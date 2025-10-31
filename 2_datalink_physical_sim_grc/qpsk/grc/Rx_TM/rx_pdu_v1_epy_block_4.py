#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tm_deframer_stub_floattap — TM Deframer with a float mirror tap.

Input : BYTES (uint8), tagged stream, one 'packet_len' tag per TM frame
        frame_len = tm_hdr_len + tm_body_len (e.g., 6 + 1109 = 1115).
Out[0]: BYTES (uint8) — SPP payload bytes, tagged with 'packet_len' = spp_len
Out[1]: FLOATS (float32) — SPP payload mirrored as floats (for Number Sink/Tag Debug)

Modes for determining SPP length:
  - mode="len_field"   : read uint16 length at 'len_field_offset' in header (big-endian).
  - mode="trim_zeros"  : trim trailing 0x00 from body (default).
  - mode="fixed"       : always emit tm_body_len bytes.

Notes:
- Stub deframer that inverts a simple TX "tm_framer_stub" (fixed body + zero padding).
- Adds a float tap so you can visualize values and tags easily in QT Number Sink.
"""

import numpy as np, pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self,
                 tm_hdr_len=6,
                 tm_body_len=1109,
                 len_tag_key="packet_len",
                 mode="trim_zeros",          # "len_field" | "trim_zeros" | "fixed"
                 len_field_offset=6,         # where a 2B length would live (if you add it)
                 len_field_big_endian=True,  # endianness for length field
                 forward_other_tags=False    # remap non-length tags into SPP offsets
                 ):
        gr.basic_block.__init__(self,
            name="tm_deframer_stub_floattap",
            in_sig=[np.uint8],
            out_sig=[np.uint8, np.float32],   # <-- byte output + float tap
        )

        self.tm_hdr_len  = int(tm_hdr_len)
        self.tm_body_len = int(tm_body_len)
        self.frame_len   = self.tm_hdr_len + self.tm_body_len

        self.len_key_str = str(len_tag_key)
        self.len_key     = pmt.intern(self.len_key_str)

        self.mode                 = str(mode)
        self.len_field_offset     = int(len_field_offset)
        self.len_field_big_endian = bool(len_field_big_endian)
        self.forward_other_tags   = bool(forward_other_tags)

        try:
            self.set_tag_propagation_policy(gr.block.TPP_DONT)
        except Exception:
            pass

    # ---------------- helpers ----------------
    def _first_len_tag_here(self, n_in):
        nread = self.nitems_read(0)
        tags  = self.get_tags_in_window(0, 0, n_in)
        tags.sort(key=lambda t: int(t.offset))
        for t in tags:
            if pmt.equal(t.key, self.len_key):
                return t
        return None

    def _get_other_tags(self, n_bytes):
        nread = self.nitems_read(0)
        tags  = self.get_tags_in_window(0, 0, n_bytes)
        return nread, [t for t in tags if not pmt.equal(t.key, self.len_key)]

    def _spp_len_from_header(self, hdr: bytes) -> int:
        off = self.len_field_offset
        if off + 2 <= len(hdr):
            b0, b1 = hdr[off], hdr[off+1]
            if self.len_field_big_endian:
                L = (b0 << 8) | b1
            else:
                L = (b1 << 8) | b0
            return int(L)
        return -1

    def _spp_len_from_trim(self, body: bytes) -> int:
        idx = len(body) - 1
        while idx >= 0 and body[idx] == 0:
            idx -= 1
        return idx + 1

    # ---------------- work ----------------
    def general_work(self, input_items, output_items):
        inp  = input_items[0]
        outB = output_items[0]     # bytes out
        outF = output_items[1]     # float tap out

        n_in  = len(inp)
        n_oB  = len(outB)
        n_oF  = len(outF)
        if n_in == 0 or n_oB == 0 or n_oF == 0:
            return 0

        t = self._first_len_tag_here(n_in)
        if t is None:
            return 0

        nread = self.nitems_read(0)
        rel   = int(t.offset - nread)
        if rel > 0:
            self.consume(0, rel)
            return 0

        # Expect and wait for a full TM frame
        try:
            L = int(pmt.to_long(t.value))
        except Exception:
            return 0

        if L < self.frame_len or n_in < self.frame_len:
            return 0

        frame = bytes(inp[:self.frame_len])
        hdr   = frame[:self.tm_hdr_len]
        body  = frame[self.tm_hdr_len:]

        # Determine SPP length
        if self.mode == "len_field":
            spp_len = self._spp_len_from_header(hdr)
            if spp_len < 0:
                spp_len = min(self.tm_body_len, self._spp_len_from_trim(body))
            else:
                spp_len = max(0, min(spp_len, self.tm_body_len))
        elif self.mode == "fixed":
            spp_len = self.tm_body_len
        else:  # "trim_zeros"
            spp_len = min(self.tm_body_len, self._spp_len_from_trim(body))

        if spp_len < 0:
            self.consume(0, self.frame_len)
            return 0

        # Ensure output space on both outputs
        if n_oB < spp_len or n_oF < spp_len:
            return 0

        # Write bytes to out0
        if spp_len > 0:
            outB[:spp_len] = np.frombuffer(body[:spp_len], dtype=np.uint8)

            # Mirror to float32 on out1 (byte value → float value)
            # Avoid Python loops: vectorized cast
            outF[:spp_len] = np.frombuffer(body[:spp_len], dtype=np.uint8).astype(np.float32)

        # Tag both outputs at their respective write cursors
        w0 = self.nitems_written(0)
        w1 = self.nitems_written(1)
        self.add_item_tag(0, w0, self.len_key, pmt.from_long(spp_len))
        self.add_item_tag(1, w1, self.len_key, pmt.from_long(spp_len))

        # Optionally forward non-length tags into SPP offsets (both outs)
        if self.forward_other_tags and spp_len > 0:
            nread0, others = self._get_other_tags(self.frame_len)
            for tt in others:
                k = int(tt.offset - nread0) - self.tm_hdr_len
                if 0 <= k < spp_len:
                    try:
                        self.add_item_tag(0, w0 + k, tt.key, tt.value, tt.srcid)
                        self.add_item_tag(1, w1 + k, tt.key, tt.value, tt.srcid)
                    except TypeError:
                        self.add_item_tag(0, w0 + k, tt.key, tt.value)
                        self.add_item_tag(1, w1 + k, tt.key, tt.value)

        # Consume exactly one TM frame
        self.consume(0, self.frame_len)
        # We produced spp_len items on BOTH outputs
        return spp_len

