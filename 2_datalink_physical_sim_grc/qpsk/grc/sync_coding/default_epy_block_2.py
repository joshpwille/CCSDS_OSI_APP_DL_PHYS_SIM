"""
ASM inserter for CCSDS CADU.

Input : bytes (uchar), tagged stream with one length tag per frame (len_tag_key)
Output: bytes (uchar), same frame with ASM prepended; packet_len increased by len(ASM)
"""

import numpy as np
import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, len_tag_key="packet_len", asm_word=(0x1A, 0xCF, 0xFC, 0x1D)):
        gr.basic_block.__init__(self,
            name="asm_inserter",
            in_sig=[np.uint8],
            out_sig=[np.uint8],
        )
        self.len_key  = pmt.intern(str(len_tag_key))
        # use your canvas variable; GRC will pass ASM_MARKER here
        self.asm      = bytes(asm_word) if asm_word is not None else b""
        self.asm_len  = len(self.asm)

        # We do not create headers or bodies here; we just insert ASM.

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        n_in = len(inp)
        if n_in == 0:
            return 0

        n_read = self.nitems_read(0)

        # Look for the first length tag in the current window
        tags = self.get_tags_in_window(0, 0, n_in, self.len_key)
        if not tags:
            return 0

        t = tags[0]
        rel = int(t.offset - n_read)
        if rel > 0:
            # Align to the tag (start of frame)
            self.consume(0, rel)
            return 0

        # Length of the incoming frame payload (pre-ASM)
        L_in = int(pmt.to_long(t.value))
        if n_in < L_in:
            # wait for the whole frame to arrive
            return 0

        L_out = L_in + self.asm_len  # <— THIS is the “+4” (or +len(ASM_MARKER))

        if len(out) < L_out:
            # need more output buffer
            return 0

        # write ASM then the original frame bytes
        if self.asm_len:
            out[:self.asm_len] = np.frombuffer(self.asm, dtype=np.uint8)
        out[self.asm_len:self.asm_len+L_in] = inp[:L_in]

        # Re-tag output with the new length
        self.add_item_tag(0, self.nitems_written(0), self.len_key, pmt.from_long(L_out))

        # Consume exactly the input frame
        self.consume(0, L_in)
        return L_out
