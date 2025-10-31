#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
len_meter_ts_f32 — emits one float sample per frame equal to the length tag.

Input : FLOATS (np.float32), tagged stream with 'packet_len' per frame.
Output: FLOATS (np.float32), 1 sample per frame = float(packet_len).

Typical use:
[float-tap] → len_meter_ts_f32 → QT GUI Number Sink
"""

import numpy as np
import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, len_tag_key="packet_len"):
        gr.basic_block.__init__(self,
            name="len_meter_ts_f32",
            in_sig=[np.float32],
            out_sig=[np.float32],
        )
        self.len_key_str = str(len_tag_key)
        self.len_key     = pmt.intern(self.len_key_str)

        # We produce our own outputs; don't auto-forward tags.
        try:
            self.set_tag_propagation_policy(gr.block.TPP_DONT)
        except Exception:
            pass

    def _first_len_tag_here(self, n_in):
        """Return first length tag at/after current read index within window."""
        tags = self.get_tags_in_window(0, 0, n_in)
        if not tags:
            return None
        tags.sort(key=lambda t: int(t.offset))
        for t in tags:
            if pmt.equal(t.key, self.len_key):
                return t
        return None

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        n_in  = len(inp)
        n_out = len(out)
        if n_in == 0 or n_out == 0:
            return 0

        # Find the first length tag at/after the current read pointer
        t = self._first_len_tag_here(n_in)
        if t is None:
            return 0

        nread = self.nitems_read(0)
        rel   = int(t.offset - nread)

        # If the tag starts later in this window, advance to it
        if rel > 0:
            self.consume(0, rel)
            return 0

        # Tag is at current cursor; parse length
        try:
            L = int(pmt.to_long(t.value))
        except Exception:
            # If the tag value isn't a PMT integer, try to coerce
            try:
                L = int(str(t.value))
            except Exception:
                # Can't parse; drop one item to avoid deadlock
                self.consume(0, 1)
                return 0

        # Wait until the full frame is present
        if n_in < L:
            return 0

        # Emit one float with the length and consume exactly one frame
        out[0] = float(L)
        self.consume(0, L)
        return 1

