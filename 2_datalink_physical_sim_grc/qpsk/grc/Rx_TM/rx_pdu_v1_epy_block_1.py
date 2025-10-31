#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CCSDS RS(255,223) I-depth deinterleaver (round-robin), RX side, with float tap.

Input : BYTES (uint8), tagged stream with one length tag per CADU body:
        len_tag_key = 255*I (e.g., 1275 for I=5) -- ASM already stripped.
        Layout is interleaved: s = [cw0[0], cw1[0], ..., cw{I-1}[0], cw0[1], ...]
Output0: BYTES (uint8), tagged stream of length 255*I, deinterleaved & concatenated:
         out = [cw0[0..254], cw1[0..254], ..., cw{I-1}[0..254]]
Output1: FLOAT32 mirror of Output0 (0..255), same 'packet_len' tags (for GUI taps).

Place before your RS(255,223) decoder. The decoder can then consume the output
in contiguous 255-byte chunks (cw0, cw1, ..., cw{I-1}).
"""

import numpy as np, pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, len_tag_key="packet_len", I=5, expect_len=0, forward_other_tags=True):
        gr.basic_block.__init__(self,
            name="rs255_223_deinterleave_I_tapped",
            in_sig=[np.uint8],
            out_sig=[np.uint8, np.float32],   # Out0 bytes, Out1 float tap
        )
        self.len_key_str = str(len_tag_key)
        self.len_key     = pmt.intern(self.len_key_str)
        self.I           = int(I)
        if self.I <= 0:
            raise ValueError("I must be >= 1")
        self.expect_len  = int(expect_len)   # if 0 -> will use 255*I
        self.forward_other_tags = bool(forward_other_tags)

        # Emit only our own length tags; forward others manually
        try:
            self.set_tag_propagation_policy(gr.block.TPP_DONT)
        except Exception:
            try:
                self.set_tag_propagation_policy(gr.TPP_DONT)
            except Exception:
                pass

    # ---- tag helpers ----
    def _first_len_tag_here(self, n_in):
        """Return the first length tag at/after current read index within window."""
        tags  = self.get_tags_in_window(0, 0, n_in)
        tags.sort(key=lambda t: int(t.offset))
        for t in tags:
            if pmt.equal(t.key, self.len_key):
                return t
        return None

    def _get_other_tags(self, n_in):
        nread = self.nitems_read(0)
        tags  = self.get_tags_in_window(0, 0, n_in)
        others = [t for t in tags if not pmt.equal(t.key, self.len_key)]
        return nread, others

    # ---- work ----
    def general_work(self, input_items, output_items):
        inp = input_items[0]
        outB = output_items[0]   # bytes
        outF = output_items[1]   # float32 tap

        n_in = len(inp)
        if n_in == 0 or len(outB) == 0 or len(outF) == 0:
            return 0

        t = self._first_len_tag_here(n_in)
        if t is None:
            return 0

        nread = self.nitems_read(0)
        rel   = int(t.offset - nread)
        if rel > 0:
            # align to the frame start
            self.consume(0, rel)
            return 0

        try:
            L = int(pmt.to_long(t.value))
        except Exception:
            return 0

        expected = (255 * self.I) if self.expect_len <= 0 else self.expect_len
        if L < expected or n_in < L:
            # wait for full frame
            return 0

        frame = np.array(inp[:L], dtype=np.uint8)

        # Robustness: length must be a multiple of I
        if (L % self.I) != 0:
            self.consume(0, L)
            return 0

        symbols_per_cw = L // self.I
        if symbols_per_cw < 255:
            # malformed; not enough for a full RS codeword
            self.consume(0, L)
            return 0

        N = 255
        needed = N * self.I
        cap = min(len(outB), len(outF))
        if cap < needed:
            return 0

        # Deinterleave: for each branch j, take frame[j::I][:N] and place contiguously
        write_idx = 0
        for j in range(self.I):
            cw = frame[j::self.I][:N]
            outB[write_idx:write_idx+N] = cw
            # float tap mirror
            outF[write_idx:write_idx+N] = cw.astype(np.float32)
            write_idx += N

        # Emit output length tag (still 255*I) on BOTH outputs
        base0 = self.nitems_written(0)
        base1 = self.nitems_written(1)
        tag_val = pmt.from_long(needed)
        self.add_item_tag(0, base0, self.len_key, tag_val)
        self.add_item_tag(1, base1, self.len_key, tag_val)

        # Optionally forward non-length tags with offset mapping to BOTH outputs
        if self.forward_other_tags:
            nread0, others = self._get_other_tags(L)
            nwrite0_B = self.nitems_written(0)
            nwrite0_F = self.nitems_written(1)
            for t2 in others:
                k = int(t2.offset - nread0)  # input index within this frame
                if 0 <= k < L:
                    branch = k % self.I
                    sym    = k // self.I
                    if sym < N:
                        out_off = branch*255 + sym
                        # bytes output
                        try:
                            self.add_item_tag(0, nwrite0_B + out_off, t2.key, t2.value, t2.srcid)
                        except TypeError:
                            self.add_item_tag(0, nwrite0_B + out_off, t2.key, t2.value)
                        # float tap output
                        try:
                            self.add_item_tag(1, nwrite0_F + out_off, t2.key, t2.value, t2.srcid)
                        except TypeError:
                            self.add_item_tag(1, nwrite0_F + out_off, t2.key, t2.value)

        # Consume exactly one (interleaved) frame
        self.consume(0, L)
        # Produce exactly 'needed' on BOTH outputs
        return needed

