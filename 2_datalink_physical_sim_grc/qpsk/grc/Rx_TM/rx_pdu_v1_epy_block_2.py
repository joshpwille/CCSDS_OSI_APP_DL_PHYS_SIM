#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCSDS TM de-randomizer (multiplicative scrambler), frame-synced — with float tap.

In  : BYTES (uint8), continuous stream with 'packet_len' tags per frame
Out0: BYTES (uint8), de-randomized (main path)
Out1: FLOAT32       mirror of Out0 for GUI taps (Number Sink / Len Meter)

Behavior:
- Restarts 8-bit LFSR at each frame start (seen via length-tag).
- Optionally skips the first 'skip_bytes_at_frame_start' bytes per frame (e.g., ASM).
- XOR with PN bytes is symmetric; set enabled=False for pass-through.
- Tag propagation: TPP_ALL (all input tags, including 'packet_len', propagate to BOTH outputs).
"""

import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    def __init__(self,
                 len_tag_key="packet_len",
                 seed=0xFF,
                 taps=(8,7,5,3),         # CCSDS default polynomial taps (excluding x^8 which is implicit)
                 skip_bytes_at_frame_start=0,
                 enabled=True):
        gr.basic_block.__init__(self,
            name="ccsds_tm_derandomizer_tapped",
            in_sig=[np.uint8],
            out_sig=[np.uint8, np.float32],  # Out0 bytes, Out1 float tap
        )

        # ---- Config ----
        self.len_tag_key_str = str(len_tag_key)
        self.len_tag_key     = pmt.intern(self.len_tag_key_str)
        self.enabled         = bool(enabled)
        self.skip_bytes      = int(skip_bytes_at_frame_start)

        # 8-bit LFSR state and taps
        self.seed            = int(seed) & 0xFF
        self._lfsr           = self.seed
        self._taps           = tuple(sorted(set(int(t) for t in taps if 1 <= int(t) <= 7), reverse=True))

        # Frame state
        self._in_frame       = False
        self._frame_left     = 0
        self._skip_left      = 0

        # Forward all upstream tags to BOTH outputs (we also add none ourselves)
        try:
            self.set_tag_propagation_policy(gr.block.TPP_ALL)
        except AttributeError:
            try:
                self.set_tag_propagation_policy(gr.TPP_ALL)
            except AttributeError:
                pass

    # -------- LFSR core --------
    def _reset_lfsr(self):
        self._lfsr = self.seed & 0xFF
        if self._lfsr == 0:
            self._lfsr = 0xFF  # avoid zero lock

    def _next_pn_byte(self):
        out_byte = 0
        for _ in range(8):
            msb = (self._lfsr >> 7) & 0x1
            out_byte = ((out_byte << 1) | msb) & 0xFF

            fb = msb
            s = self._lfsr
            for t in self._taps:
                fb ^= (s >> (t - 1)) & 0x1

            self._lfsr = ((self._lfsr << 1) & 0xFF) | fb
        return out_byte

    # -------- Helpers --------
    def _frame_start(self, frame_len):
        self._reset_lfsr()
        self._in_frame   = True
        self._frame_left = int(frame_len)
        self._skip_left  = min(self.skip_bytes, self._frame_left)

    def _apply_derand_into(self, src, dst, n):
        # byte-wise XOR with PN; src,dst are numpy uint8 views
        for i in range(n):
            dst[i] = src[i] ^ self._next_pn_byte()

    def _find_starts(self, n_input):
        """Return sorted list of (rel_offset, frame_len) for all length-tag starts in this window."""
        in0 = 0
        nread = self.nitems_read(in0)
        tags = self.get_tags_in_range(in0, nread, nread + n_input, self.len_tag_key)
        starts = []
        for t in tags:
            try:
                L = int(pmt.to_long(t.value))
            except Exception:
                continue
            if L > 0:
                rel = int(t.offset - nread)
                starts.append((rel, L))
        starts.sort(key=lambda x: x[0])
        return starts

    # -------- Work --------
    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out_b = output_items[0]  # bytes
        out_f = output_items[1]  # float tap

        n_in  = len(inp)
        n_out = min(len(out_b), len(out_f))  # produce same count on both outs
        if n_in == 0 or n_out == 0:
            return 0

        produced = 0
        consumed = 0
        cursor   = 0

        # Discover all frame-starts within this window
        starts = self._find_starts(n_in)
        starts_idx = 0

        def emit_chunk(src_start, n_bytes, do_derand, skip_first):
            """Process n_bytes from inp[src_start:src_start+n_bytes] into both outputs."""
            nonlocal produced, consumed

            n = min(n_bytes, n_out - produced)
            if n <= 0:
                return

            src = inp[src_start:src_start+n].view(np.uint8)
            dst_b = out_b[produced:produced+n].view(np.uint8)

            if (not self.enabled) or (not do_derand):
                # passthrough
                dst_b[:] = src
            else:
                # optional leading passthrough (skip_first), then derand the rest
                k = min(skip_first, n)
                if k > 0:
                    dst_b[:k] = src[:k]
                    skip_first -= k
                    if k == n:
                        # nothing left to derand in this call
                        out_f[produced:produced+n] = dst_b.astype(np.float32)
                        produced += n
                        consumed += n
                        return
                    # fallthrough to derand the remainder
                    src = src[k:]
                    dst_b = dst_b[k:]
                    n -= k
                # derandomize remaining bytes into dst_b
                self._apply_derand_into(src, dst_b, n)

            # mirror to float tap
            out_f[produced:produced + (len(dst_b) if isinstance(dst_b, np.ndarray) else n)] = \
                out_b[produced:produced+n].astype(np.float32)

            produced += (len(dst_b) if isinstance(dst_b, np.ndarray) else n)
            consumed += (len(dst_b) if isinstance(dst_b, np.ndarray) else n)

            return

        # Walk the window, starting new frames where tags say so
        while cursor < n_in and produced < n_out:
            next_rel = starts[starts_idx][0] if starts_idx < len(starts) else None
            if next_rel is None or next_rel <= cursor:
                if starts_idx < len(starts) and next_rel == cursor:
                    # Start of a new frame right here
                    _, L = starts[starts_idx]
                    self._frame_start(L)
                    starts_idx += 1

                # How many bytes can we emit this call?
                # If in a frame, we may need to honor skip + derand budget.
                if self._in_frame:
                    # We can emit up to what's left in frame OR output space OR remaining input
                    n_possible = min(n_in - cursor, n_out - produced)
                    # First chunk may include skip portion
                    emit_chunk(cursor, n_possible, do_derand=True, skip_first=self._skip_left)
                    # Update skip/frame counters based on how many actually produced
                    advanced = min(n_possible, n_out - produced)  # already accounted
                    # Update frame accounting
                    use = min(advanced, self._skip_left)
                    self._skip_left -= use
                    self._frame_left -= advanced
                    cursor += advanced
                    if self._frame_left <= 0:
                        self._in_frame = False
                else:
                    # Not in a frame: straight passthrough until next start or output full
                    span = min(n_in - cursor, n_out - produced)
                    emit_chunk(cursor, span, do_derand=False, skip_first=0)
                    cursor += span
            else:
                # bytes until next frame start
                span = min(next_rel - cursor, n_in - cursor, n_out - produced)
                # Outside of a frame -> passthrough
                emit_chunk(cursor, span, do_derand=False, skip_first=0)
                cursor += span

        self.consume(0, consumed)
        return produced

