#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ccsds_viterbi_k7_r12_hard_epy_frameless_tapped — fixed-chunk Viterbi with float tap

In  : uint8 BYTES, continuous, packed 8 bits/byte. Every 'coded_len_in' bytes = one coded frame.
Out0: uint8 BYTES (decoded bytes)
Out1: float32     (mirror of Out0 for GUI taps)
Tags: Emits 'packet_len' = decoded_len_out on BOTH outputs at each frame start.

Defaults match your TX:
- K=7, G0=171o (C1), G1=133o (C2)
- g2_inverted=False, c1c2_order=True, msb_first=True
- reset_each_frame=True (set False if encoder runs continuous trellis)
"""

import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    def __init__(self,
                 len_tag_key="packet_len",
                 K=7,
                 gen0=0o171,
                 gen1=0o133,
                 msb_first=True,
                 reset_each_frame=True,
                 g2_inverted=False,
                 c1c2_order=True,
                 coded_len_in=2558,
                 decoded_len_out=1279):
        gr.sync_block.__init__(
            self,
            name="ccsds_viterbi_k7_r12_hard_epy_frameless_tapped",
            in_sig=[np.uint8],
            out_sig=[np.uint8, np.float32],   # Out0 bytes, Out1 float tap
        )
        # params
        self.len_tag_key = str(len_tag_key)
        self.len_key_sym = pmt.intern(self.len_tag_key)
        self.K = int(K)
        self.gen0 = int(gen0)
        self.gen1 = int(gen1)
        self.msb_first = bool(msb_first)
        self.reset_each_frame = bool(reset_each_frame)
        self.g2_inverted = bool(g2_inverted)
        self.c1c2_order = bool(c1c2_order)
        self.coded_len_in = int(coded_len_in)
        self.decoded_len_out = int(decoded_len_out)

        # trellis
        self.NSTATES = 1 << (self.K - 1)
        self._trellis_ns   = np.zeros((self.NSTATES, 2), dtype=np.uint8)
        self._trellis_obit = np.zeros((self.NSTATES, 2, 2), dtype=np.uint8)
        self._build_trellis()

        # buffers/state
        self._inbuf  = bytearray()
        self._outbuf = bytearray()
        self._pending_out_frames = []  # lengths to tag (decoded_len_out per frame)
        self._head_remaining = 0

        # We add our own clean tags; ignore upstream tags completely
        self.set_tag_propagation_policy(gr.TPP_DONT)

    # -------- trellis --------
    @staticmethod
    def _parity_u32(x: int) -> int:
        v = x
        v ^= v >> 16; v ^= v >> 8; v ^= v >> 4
        v &= 0xF
        return (0x6996 >> v) & 1

    def _build_trellis(self):
        maskK = (1 << self.K) - 1
        maskS = (1 << (self.K - 1)) - 1
        for s in range(self.NSTATES):
            for u in (0, 1):
                full = ((s << 1) | u) & maskK
                ns = (full >> 1) & maskS
                b0 = self._parity_u32(full & self.gen0)  # C1
                b1 = self._parity_u32(full & self.gen1)  # C2
                if self.g2_inverted:
                    b1 ^= 1
                self._trellis_ns[s, u] = ns
                self._trellis_obit[s, u, 0] = b0
                self._trellis_obit[s, u, 1] = b1

    # -------- pack/unpack --------
    def _bytes_to_bits(self, b: bytes) -> np.ndarray:
        a = np.frombuffer(b, dtype=np.uint8)
        shifts = np.array([7,6,5,4,3,2,1,0], dtype=np.uint8) if self.msb_first \
                 else np.array([0,1,2,3,4,5,6,7], dtype=np.uint8)
        return ((a[:, None] >> shifts[None, :]) & 1).astype(np.uint8).reshape(-1)

    def _bits_to_bytes(self, bits: np.ndarray) -> bytes:
        n = bits.size
        pad = (8 - (n % 8)) % 8
        if pad:
            bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
        bits = bits.reshape(-1, 8)
        weights = (1 << np.array([7,6,5,4,3,2,1,0], dtype=np.uint8)).astype(np.uint16) \
                  if self.msb_first else (1 << np.array([0,1,2,3,4,5,6,7], dtype=np.uint8)).astype(np.uint16)
        packed = (bits * weights).sum(axis=1).astype(np.uint8)
        return bytes(packed)

    # -------- viterbi --------
    def _viterbi_hard_decode(self, rx_bits: np.ndarray) -> bytes:
        nbits = rx_bits.size
        if nbits & 1:
            rx_bits = rx_bits[:-1]
            nbits -= 1
        nsym = nbits // 2

        BIG = 1 << 30
        pm = np.full(self.NSTATES, BIG, dtype=np.int32)
        pm_new = np.full(self.NSTATES, BIG, dtype=np.int32)
        if self.reset_each_frame:
            pm[:] = BIG; pm[0] = 0
        else:
            pm[:] = 0

        prev_state  = np.zeros((nsym, self.NSTATES), dtype=np.uint8)
        decided_bit = np.zeros((nsym, self.NSTATES), dtype=np.uint8)

        for t in range(nsym):
            if self.c1c2_order:
                r0 = int(rx_bits[2*t + 0]); r1 = int(rx_bits[2*t + 1])  # C1,C2
            else:
                r1 = int(rx_bits[2*t + 0]); r0 = int(rx_bits[2*t + 1])  # C2,C1

            pm_new[:] = BIG
            for s in range(self.NSTATES):
                cost_s = pm[s]
                if cost_s >= BIG: continue

                # u = 0
                ns0 = self._trellis_ns[s, 0]
                e00 = int(self._trellis_obit[s, 0, 0]); e01 = int(self._trellis_obit[s, 0, 1])
                bm0 = (r0 ^ e00) + (r1 ^ e01)
                c0 = cost_s + bm0
                if c0 < pm_new[ns0]:
                    pm_new[ns0] = c0; prev_state[t, ns0] = s; decided_bit[t, ns0] = 0

                # u = 1
                ns1 = self._trellis_ns[s, 1]
                e10 = int(self._trellis_obit[s, 1, 0]); e11 = int(self._trellis_obit[s, 1, 1])
                bm1 = (r0 ^ e10) + (r1 ^ e11)
                c1 = cost_s + bm1
                if c1 < pm_new[ns1]:
                    pm_new[ns1] = c1; prev_state[t, ns1] = s; decided_bit[t, ns1] = 1

            pm, pm_new = pm_new, pm

        end_state = int(np.argmin(pm))
        bits_dec = np.zeros(nsym, dtype=np.uint8)
        s = end_state
        for t in range(nsym-1, -1, -1):
            b = decided_bit[t, s]; bits_dec[t] = b; s = prev_state[t, s]
        return self._bits_to_bytes(bits_dec)

    # -------- work --------
    def work(self, input_items, output_items):
        x  = input_items[0]
        y0 = output_items[0]  # bytes
        y1 = output_items[1]  # float tap

        n_in = len(x)
        if n_in:
            self._inbuf += bytes(x)

        # convert as many full coded frames as we currently have buffered
        while len(self._inbuf) >= self.coded_len_in:
            frame = bytes(self._inbuf[:self.coded_len_in])
            del self._inbuf[:self.coded_len_in]

            rx_bits = self._bytes_to_bits(frame)
            dec = self._viterbi_hard_decode(rx_bits)
            if len(dec) > self.decoded_len_out:
                dec = dec[:self.decoded_len_out]
            self._outbuf += dec
            self._pending_out_frames.append(self.decoded_len_out)

        if not self._outbuf:
            self.consume_each(n_in)
            return 0

        space = min(len(y0), len(y1))  # sync_block -> must produce equal on all outputs
        if space == 0:
            self.consume_each(n_in)
            return 0

        produced = 0
        ow0 = self.nitems_written(0)
        ow1 = self.nitems_written(1)

        while space > 0 and self._outbuf:
            # start-of-frame tagging on BOTH outputs
            if self._head_remaining == 0:
                if not self._pending_out_frames:
                    break
                self._head_remaining = self._pending_out_frames[0]
                self.add_item_tag(0, ow0 + produced, self.len_key_sym, pmt.from_long(self.decoded_len_out))
                self.add_item_tag(1, ow1 + produced, self.len_key_sym, pmt.from_long(self.decoded_len_out))

            chunk = min(space, self._head_remaining, len(self._outbuf))
            if chunk <= 0: break

            # bytes out
            y0[produced:produced+chunk] = np.frombuffer(self._outbuf[:chunk], dtype=np.uint8)
            # float tap (0..255 as float)
            y1[produced:produced+chunk] = np.frombuffer(self._outbuf[:chunk], dtype=np.uint8).astype(np.float32)

            del self._outbuf[:chunk]
            produced += chunk
            space    -= chunk
            self._head_remaining -= chunk

            if self._head_remaining == 0 and self._pending_out_frames:
                self._pending_out_frames.pop(0)

        self.consume_each(n_in)
        return produced

