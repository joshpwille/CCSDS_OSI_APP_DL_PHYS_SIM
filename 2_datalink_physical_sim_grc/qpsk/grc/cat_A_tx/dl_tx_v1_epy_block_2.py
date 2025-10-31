#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ASM Inserter with Monitor Tap (CCSDS CADU builder)

In  : uint8 bytes (RS-coded frames, default 1275 B), arbitrarily chunked.
Out0: uint8 bytes  -> CADU stream (ASM 4B + RS 1275B = 1279B)  [to conv encoder]
Out1: float32      -> Mirror of Out0 converted to floats        [to Len Meter -> Number Sink]

Behavior:
- Drops ALL upstream tags (TPP_DONT).
- Emits exactly one length tag per CADU on BOTH outputs (default key "packet_len" = 1279).
- Buffers partial input and outputs CADUs as soon as RS_LEN bytes are available.

Params:
- len_tag_key : downstream length tag key (default "packet_len")
- rs_len      : RS-coded length per frame (default 1275; for I=5 interleave)
- asm_hex     : 8 hex chars, big-endian ASM (default "1ACFFC1D")
- enable_sanity : if True, prints a one-liner when dropping upstream tags
"""

import sys
import numpy as np
import pmt
from gnuradio import gr

class blk(gr.sync_block):
    def __init__(self,
                 len_tag_key="packet_len",
                 rs_len=1275,
                 asm_hex="1ACFFC1D",
                 enable_sanity=True):
        gr.sync_block.__init__(
            self,
            name="ccsds_asm_inserter_tapped",
            in_sig=[np.uint8],
            out_sig=[np.uint8, np.float32],   # Out[0]=bytes (main), Out[1]=float (monitor)
        )

        # --- Params ---
        self.len_tag_key = str(len_tag_key)
        self.len_key_sym = pmt.intern(self.len_tag_key)
        self.RS_LEN = int(rs_len)
        self.enable_sanity = bool(enable_sanity)

        if not (isinstance(asm_hex, str) and len(asm_hex) == 8):
            raise ValueError("asm_hex must be 8 hex chars, e.g., '1ACFFC1D'")
        try:
            asm_val = int(asm_hex, 16)
        except ValueError:
            raise ValueError("asm_hex must be valid hex, e.g., '1ACFFC1D'")
        self.ASM = asm_val.to_bytes(4, byteorder="big")
        self.CADU_LEN = 4 + self.RS_LEN  # 1279 by default

        # --- State ---
        self._inbuf = bytearray()
        self._outbuf = bytearray()
        self._pending = []          # queue of CADU sizes waiting to tag/emit
        self._head_remaining = 0    # bytes remaining in current CADU emission

        # Do NOT forward upstream tags; we add our own clean frame tags.
        self.set_tag_propagation_policy(gr.TPP_DONT)

    # Optional: observe & drop upstream tags (never forwarded)
    def _maybe_warn_upstream_tags(self, ninput_items):
        if not self.enable_sanity:
            return
        tags = self.get_tags_in_window(0, 0, ninput_items)
        if tags:
            try:
                sys.stderr.write("[asm_inserter] Dropping {} upstream tags (by design).\n".format(len(tags)))
            except Exception:
                pass

    # Build as many CADUs as possible
    def _consume_to_cadus(self):
        while len(self._inbuf) >= self.RS_LEN:
            payload = bytes(self._inbuf[:self.RS_LEN])
            del self._inbuf[:self.RS_LEN]
            cadu = self.ASM + payload
            self._outbuf += cadu
            self._pending.append(self.CADU_LEN)

    def work(self, input_items, output_items):
        x = input_items[0]
        y0 = output_items[0]  # bytes (main path)
        y1 = output_items[1]  # float (monitor tap)

        n_in = len(x)
        if n_in:
            self._inbuf += bytes(x)
            self._maybe_warn_upstream_tags(n_in)
            self._consume_to_cadus()

        if not self._outbuf:
            self.consume_each(n_in)
            return 0  # nothing ready yet

        space0 = len(y0)
        space1 = len(y1)
        space = min(space0, space1)  # sync_block must produce same on all outs
        if space == 0:
            self.consume_each(n_in)
            return 0

        produced = 0
        ow0 = self.nitems_written(0)
        ow1 = self.nitems_written(1)

        while space > 0 and self._outbuf:
            # Start-of-frame: set remaining and emit tags on BOTH outputs
            if self._head_remaining == 0:
                if not self._pending:
                    break
                self._head_remaining = self._pending[0]
                # tag at current write offset on both outputs
                self.add_item_tag(0, ow0 + produced, self.len_key_sym, pmt.from_long(self.CADU_LEN))
                self.add_item_tag(1, ow1 + produced, self.len_key_sym, pmt.from_long(self.CADU_LEN))

            # Max chunk we can emit now
            chunk = min(space, self._head_remaining, len(self._outbuf))
            if chunk <= 0:
                break

            # Copy bytes to out0
            y0[produced:produced+chunk] = np.frombuffer(self._outbuf[:chunk], dtype=np.uint8)
            # Convert to float for out1 (0..255 as float)
            # Avoid extra allocation: simple vectorized cast
            y1[produced:produced+chunk] = np.frombuffer(self._outbuf[:chunk], dtype=np.uint8).astype(np.float32)

            del self._outbuf[:chunk]
            produced += chunk
            space -= chunk
            self._head_remaining -= chunk

            if self._head_remaining == 0 and self._pending:
                self._pending.pop(0)

        self.consume_each(n_in)
        return produced

