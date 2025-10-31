#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ccsds_conv_k7_r12_epy_sync — Convolutional encoder (K=7, r=1/2) matched to Viterbi

Input : uint8 BYTES (packed; 8 bits/byte), framed by 'packet_len' = input BYTES (e.g., 1279)
Output: uint8 BYTES (packed), framed by 'packet_len' = 2*input BYTES (e.g., 2558)

Toggles (must agree with Viterbi):
- g2_inverted   : invert the G2 output bit (False to match your current RX; True for CCSDS base flavor)
- c1c2_order    : multiplex order of encoder outputs; True => C1 then C2, False => C2 then C1
- msb_first     : bit packing inside each byte
- reset_each_frame : reset state to 0 for each tagged frame (set False for continuous trellis)
- strict_frame_len_in : if >0, force this input frame length; ignore incoming tag values

Notes:
- No tail bits are added; pure streaming per frame.
- Emits exactly one clean length tag at the first output byte of each encoded frame.
"""

import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    def __init__(self,
                 len_tag_key="packet_len",
                 K=7,
                 gen0=0o171,            # C1
                 gen1=0o133,            # C2
                 msb_first=True,
                 reset_each_frame=True,
                 g2_inverted=False,
                 c1c2_order=True,
                 strict_frame_len_in=1279):
        gr.sync_block.__init__(
            self,
            name="ccsds_conv_k7_r12_epy_sync",
            in_sig=[np.uint8],
            out_sig=[np.uint8],
        )
        # Params
        self.len_tag_key = str(len_tag_key)
        self.len_key_sym = pmt.intern(self.len_tag_key)
        self.K = int(K)
        self.gen0 = np.uint32(int(gen0))
        self.gen1 = np.uint32(int(gen1))
        self._mask = np.uint32((1 << self.K) - 1)
        self.msb_first = bool(msb_first)
        self.reset_each_frame = bool(reset_each_frame)
        self.g2_inverted = bool(g2_inverted)
        self.c1c2_order = bool(c1c2_order)
        self.strict_frame_len_in = int(strict_frame_len_in)

        # State
        self._inbuf = bytearray()
        self._frame_queue = []       # pending input frame lengths (bytes)
        self._state = np.uint32(0)   # shift register

        self._outbuf = bytearray()
        self._pending_out_frames = []  # encoded frame lengths to tag
        self._head_remaining = 0

        # We emit our own clean length tags
        self.set_tag_propagation_policy(gr.TPP_DONT)

    # ---------- helpers ----------
    @staticmethod
    def _parity_u32(x: int) -> int:
        # bit-parity (XOR popcount)
        v = x
        v ^= (v >> 16)
        v ^= (v >> 8)
        v ^= (v >> 4)
        v &= 0xF
        # 0x6996 parity lookup for 4 bits
        return (0x6996 >> v) & 1

    def _bytes_to_bits(self, b: bytes) -> np.ndarray:
        a = np.frombuffer(b, dtype=np.uint8)
        if self.msb_first:
            shifts = np.array([7,6,5,4,3,2,1,0], dtype=np.uint8)
        else:
            shifts = np.array([0,1,2,3,4,5,6,7], dtype=np.uint8)
        return ((a[:, None] >> shifts[None, :]) & 1).astype(np.uint8).reshape(-1)

    def _bits_to_bytes(self, bits: np.ndarray) -> bytes:
        n = bits.size
        pad = (8 - (n % 8)) % 8
        if pad:
            bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
        bits = bits.reshape(-1, 8)
        if self.msb_first:
            weights = (1 << np.array([7,6,5,4,3,2,1,0], dtype=np.uint8)).astype(np.uint16)
        else:
            weights = (1 << np.array([0,1,2,3,4,5,6,7], dtype=np.uint8)).astype(np.uint16)
        packed = (bits * weights).sum(axis=1).astype(np.uint8)
        return bytes(packed)

    def _encode_bits(self, in_bits: np.ndarray) -> np.ndarray:
        n = in_bits.size
        out = np.empty(n * 2, dtype=np.uint8)
        state = self._state
        mask = self._mask
        g0 = self.gen0
        g1 = self.gen1

        idx = 0
        if self.c1c2_order:
            # C1 then C2
            for b in in_bits:
                state = ((state << np.uint32(1)) | np.uint32(int(b & 1))) & mask
                c1 = self._parity_u32(int(state & g0))
                c2 = self._parity_u32(int(state & g1)) ^ (1 if self.g2_inverted else 0)
                out[idx]   = c1
                out[idx+1] = c2
                idx += 2
        else:
            # C2 then C1
            for b in in_bits:
                state = ((state << np.uint32(1)) | np.uint32(int(b & 1))) & mask
                c1 = self._parity_u32(int(state & g0))
                c2 = self._parity_u32(int(state & g1)) ^ (1 if self.g2_inverted else 0)
                out[idx]   = c2
                out[idx+1] = c1
                idx += 2

        # update/clear state
        if self.reset_each_frame:
            self._state = np.uint32(0)
        else:
            self._state = state
        return out

    # ---------- input frame parsing ----------
    def _enqueue_len_tags(self, ninput_items: int):
        tags = self.get_tags_in_window(0, 0, ninput_items)
        for t in tags:
            try:
                key_str = pmt.symbol_to_string(t.key)
            except Exception:
                continue
            if key_str == self.len_tag_key and pmt.is_integer(t.value):
                L = int(pmt.to_long(t.value))
                if self.strict_frame_len_in > 0:
                    L = self.strict_frame_len_in
                if L > 0:
                    self._frame_queue.append(L)

    def _process_frames_to_outbuf(self):
        # Convert as many full input frames as are currently buffered
        while self._frame_queue:
            need = self._frame_queue[0]
            if len(self._inbuf) < need:
                break
            inp = bytes(self._inbuf[:need])
            del self._inbuf[:need]
            self._frame_queue.pop(0)

            bits_in  = self._bytes_to_bits(inp)
            bits_out = self._encode_bits(bits_in)
            enc      = self._bits_to_bytes(bits_out)  # exactly 2*need bytes

            self._outbuf += enc
            self._pending_out_frames.append(len(enc))  # schedule tag on write

    # ---------- work ----------
    def work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]

        n_in = len(in0)
        if n_in:
            self._inbuf += bytes(in0)
            self._enqueue_len_tags(n_in)
            self._process_frames_to_outbuf()

        if not self._outbuf:
            self.consume_each(n_in)
            return 0

        ow = self.nitems_written(0)
        space = len(out0)
        produced = 0

        while space > 0 and self._outbuf:
            if self._head_remaining == 0:
                if not self._pending_out_frames:
                    break
                self._head_remaining = self._pending_out_frames[0]
                # tag *start* of this encoded frame on output
                self.add_item_tag(0, ow + produced, self.len_key_sym, pmt.from_long(self._head_remaining))

            chunk = min(space, self._head_remaining, len(self._outbuf))
            if chunk <= 0:
                break

            out0[produced:produced+chunk] = np.frombuffer(self._outbuf[:chunk], dtype=np.uint8)
            del self._outbuf[:chunk]

            produced += chunk
            space    -= chunk
            self._head_remaining -= chunk

            if self._head_remaining == 0 and self._pending_out_frames:
                self._pending_out_frames.pop(0)

        self.consume_each(n_in)
        return produced

