#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASM correlate+strip with optional 'trust_tags' bypass + float tap.

In  : uint8 stream after Viterbi (CADUs, e.g., 1279B), no tags required unless trust_tags=True
Out0: uint8 payload bytes (ASM stripped)
Out1: float32 mirror for GUI (with same 'packet_len' tags)

Modes:
- trust_tags=False (default): correlate 0x1ACFFC1D across bit phases, lock/track.
- trust_tags=True : ignore correlation; use upstream 'packet_len' (=cadu_len_bytes) as frame starts,
                    strip 'strip_len_bytes' and emit immediately.

Accepts asm_word as: int / "0x..." string / bytes / bytearray / tuple(list of 4 bytes).
"""

import numpy as np
import pmt
from collections import deque
from gnuradio import gr

# ---------- helpers ----------
def _asm_to_int(val, msb_first=True) -> int:
    if isinstance(val, (tuple, list)):
        b = bytes(val)
        return int.from_bytes(b, 'big' if msb_first else 'little') & 0xFFFFFFFF
    if isinstance(val, (bytes, bytearray)):
        return int.from_bytes(val, 'big' if msb_first else 'little') & 0xFFFFFFFF
    if isinstance(val, str):
        return int(val, 0) & 0xFFFFFFFF
    return int(val) & 0xFFFFFFFF

def _bytes_to_bits(arr: bytes, msb_first: bool = True) -> np.ndarray:
    a = np.frombuffer(arr, dtype=np.uint8)
    shifts = np.arange(7, -1, -1, dtype=np.uint8) if msb_first else np.arange(0, 8, 1, dtype=np.uint8)
    return ((a[:, None] >> shifts[None, :]) & 1).astype(np.uint8).reshape(-1)

class blk(gr.basic_block):
    def __init__(self,
                 len_tag_key="packet_len",
                 asm_word=0x1ACFFC1D,
                 cadu_len_bytes=1279,
                 strip_len_bytes=4,
                 msb_first=True,
                 max_hamming=4,
                 lock_confirm=2,
                 loss_threshold=3,
                 verify_guard_bits=24,
                 trust_tags=False):
        gr.basic_block.__init__(self,
            name="ccsds_asm_correlator_strip_tapped",
            in_sig=[np.uint8],
            out_sig=[np.uint8, np.float32],
        )
        # params
        self.len_key_str  = str(len_tag_key)
        self.len_key_sym  = pmt.intern(self.len_key_str)
        self.cadu_B       = int(cadu_len_bytes)
        self.strip_B      = int(strip_len_bytes)
        self.post_B       = self.cadu_B - self.strip_B
        self.msb_first    = bool(msb_first)
        self.max_ham      = int(max_hamming)
        self.lock_confirm = int(lock_confirm)
        self.loss_thresh  = int(loss_threshold)
        self.guard_bits   = int(verify_guard_bits)
        self.trust_tags   = bool(trust_tags)

        # normalize ASM to int, precompute bits
        asm_u32 = _asm_to_int(asm_word, self.msb_first)
        asm_bytes = np.array([(asm_u32 >> 24) & 0xFF,
                              (asm_u32 >> 16) & 0xFF,
                              (asm_u32 >>  8) & 0xFF,
                               asm_u32        & 0xFF], dtype=np.uint8)
        self.asm_bits = np.unpackbits(asm_bytes)  # big-endian within each byte

        # state
        self._bitbuf  = deque()
        self._locked  = False
        self._consec_hits = 0
        self._consec_miss = 0
        self._need_bits_for_search = 32 + 8*4
        self._cadu_bits  = self.cadu_B * 8
        self._strip_bits = self.strip_B * 8

        # NOTE: no tag-propagation constants used; block handles tags manually.

    # ---- correlator helpers ----
    def _ham32(self, win):
        return int(np.count_nonzero(win ^ self.asm_bits))

    def _scan(self, bits):
        n = len(bits)
        if n < 32: return -1, 999
        best_d, best_i = 999, -1
        for i in range(0, n - 32 + 1):
            d = self._ham32(bits[i:i+32])
            if d < best_d:
                best_d, best_i = d, i
                if d == 0: break
        return best_i, best_d

    # ---------- TRUST TAGS PATH ----------
    def _general_work_trust_tags(self, inpB, outB, outF):
        n_in = len(inpB)
        if n_in == 0:
            return 0

        nread = self.nitems_read(0)
        tags = self.get_tags_in_range(0, nread, nread + n_in, pmt.intern(self.len_key_str))
        tags.sort(key=lambda t: int(t.offset))

        produced = 0
        consumed = 0
        cursor   = 0
        cap = min(len(outB), len(outF))

        for t in tags:
            off = int(t.offset) - nread
            L   = int(pmt.to_long(t.value))

            # ignore stuff before the CADU start (optional passthrough to keep outputs aligned)
            pre = off - cursor
            if pre > 0:
                take = min(pre, cap - produced)
                if take <= 0:
                    break
                seg = inpB[cursor:cursor+take]
                outB[produced:produced+take] = seg
                outF[produced:produced+take] = seg.astype(np.float32)
                produced += take; consumed += take; cursor += take
                if take < pre:
                    self.consume(0, consumed)
                    return produced

            # Need full CADU at cursor
            if L != self.cadu_B or cursor + L > len(inpB):
                break  # wait for more input

            payload = inpB[cursor + self.strip_B : cursor + L]
            need = len(payload)
            if produced + need > cap:
                break

            outB[produced:produced+need] = payload
            outF[produced:produced+need] = payload.astype(np.float32)

            # tag both outputs with payload length
            base0 = self.nitems_written(0) + produced
            base1 = self.nitems_written(1) + produced
            self.add_item_tag(0, base0, self.len_key_sym, pmt.from_long(self.post_B))
            self.add_item_tag(1, base1, self.len_key_sym, pmt.from_long(self.post_B))

            produced += need
            consumed += L
            cursor   += L

        self.consume(0, consumed if consumed else n_in)
        return produced

    # ---------- CORRELATOR PATH ----------
    def _general_work_correlate(self, inpB, outB, outF):
        produced = 0
        cap = min(len(outB), len(outF))

        # append bits
        if len(inpB):
            self._bitbuf.extend(_bytes_to_bits(inpB.tobytes(), self.msb_first).tolist())

        progressed = True
        while progressed:
            progressed = False

            if not self._locked:
                if len(self._bitbuf) < self._need_bits_for_search:
                    break
                arr = np.frombuffer(bytes(self._bitbuf), dtype=np.uint8)
                idx, dist = self._scan(arr)
                if idx >= 0 and dist <= self.max_ham:
                    for _ in range(idx): self._bitbuf.popleft()   # align to ASM
                    self._consec_hits += 1; self._consec_miss = 0
                    if self._consec_hits >= self.lock_confirm:
                        self._locked = True
                    progressed = True
                else:
                    drop = min(len(self._bitbuf) - 31, 8)
                    if drop > 0:
                        for _ in range(drop): self._bitbuf.popleft()
                        progressed = True
                continue

            if len(self._bitbuf) < self._cadu_bits:
                break

            arr = np.frombuffer(bytes(self._bitbuf), dtype=np.uint8)

            # verify near head
            head_d = self._ham32(arr[:32])
            if head_d > self.max_ham:
                best_d, best_i = 999, -1
                hi = min(self.guard_bits, len(arr)-32)
                for i in range(0, hi+1):
                    d = self._ham32(arr[i:i+32])
                    if d < best_d:
                        best_d, best_i = d, i
                        if d == 0: break
                if best_d <= self.max_ham:
                    for _ in range(best_i): self._bitbuf.popleft()
                else:
                    self._consec_miss += 1; self._consec_hits = 0
                    if self._consec_miss >= self.loss_thresh:
                        keep = min(64, len(self._bitbuf))
                        drop = len(self._bitbuf) - keep
                        for _ in range(drop): self._bitbuf.popleft()
                        self._locked = False
                    else:
                        slide = min(8, len(self._bitbuf))
                        for _ in range(slide): self._bitbuf.popleft()
                    progressed = True
                    continue

            if len(self._bitbuf) < self._cadu_bits:
                break

            # extract payload bytes
            buf = np.frombuffer(bytes(self._bitbuf), dtype=np.uint8)
            payload_bits = buf[self._strip_bits:self._cadu_bits]
            pb = payload_bits.reshape(-1, 8)
            shifts = (np.arange(7, -1, -1, dtype=np.uint8)
                      if self.msb_first else
                      np.arange(0, 8, 1, dtype=np.uint8))
            out_bytes = (pb * (1 << shifts)).sum(axis=1).astype(np.uint8)

            if produced + self.post_B > cap:
                break

            outB[produced:produced+self.post_B] = out_bytes
            outF[produced:produced+self.post_B] = out_bytes.astype(np.float32)

            # emit tags on both outputs
            base0 = self.nitems_written(0) + produced
            base1 = self.nitems_written(1) + produced
            self.add_item_tag(0, base0, self.len_key_sym, pmt.from_long(self.post_B))
            self.add_item_tag(1, base1, self.len_key_sym, pmt.from_long(self.post_B))

            produced += self.post_B

            # drop the CADU we just consumed
            for _ in range(self._cadu_bits): self._bitbuf.popleft()
            self._consec_hits += 1; self._consec_miss = 0
            progressed = True

        self.consume(0, len(inpB))
        return produced

    def general_work(self, input_items, output_items):
        inpB = input_items[0]
        outB = output_items[0]
        outF = output_items[1]
        if self.trust_tags:
            return self._general_work_trust_tags(inpB, outB, outF)
        else:
            return self._general_work_correlate(inpB, outB, outF)

