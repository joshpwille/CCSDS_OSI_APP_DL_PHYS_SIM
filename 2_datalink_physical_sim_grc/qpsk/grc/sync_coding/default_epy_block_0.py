"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
import pmt
from gnuradio import gr

class blk(gr.basic_block):
    """
    TM Framer (stub):
      Input  : SPP bytes in tagged stream (len_tag_key)
      Output : fixed-length TM frames (tm_hdr_len + tm_body_len), tagged with same key
      Strategy: copy SPP into body, pad with 0x00 if short, truncate if long; add minimal 6B header
    """
    def __init__(self, tm_hdr_len=6, tm_body_len=1109, len_tag_key="packet_len"):
        gr.basic_block.__init__(self,
            name="tm_framer_stub",
            in_sig=[np.uint8],
            out_sig=[np.uint8],
        )
        self.tm_hdr_len  = int(tm_hdr_len)
        self.tm_body_len = int(tm_body_len)
        self.frame_len   = self.tm_hdr_len + self.tm_body_len
        self.len_key     = pmt.intern(len_tag_key)

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        n_in = len(inp)
        if n_in == 0:
            return 0

        n_read = self.nitems_read(0)

        # Get first visible SPP length tag in this window (filtered by our key)
        tags = self.get_tags_in_window(0, 0, n_in, self.len_key)
        if not tags:
            # Wait until the STTS boundary is visible so we frame per SPP
            return 0

        t = tags[0]

        # If the tag isn't exactly at the start of our window, consume up to it
        rel = int(t.offset - n_read)
        if rel > 0:
            self.consume(0, rel)
            return 0

        # Tag is aligned at the start; pull the SPP payload length
        spp_len = int(pmt.to_long(t.value))
        if n_in < spp_len:
            # Need more bytes for this SPP
            return 0

        # Grab the SPP payload bytes
        spp = bytes(inp[:spp_len])

        # ---- Build a fixed-length TM frame ----
        # Minimal 6B primary header stub (customize SCID/VCID/seq later)
        hdr = bytearray(self.tm_hdr_len)
        if self.tm_hdr_len >= 6:
            hdr[0] = 0x08; hdr[1] = 0x00
            hdr[2] = 0x00; hdr[3] = 0x00
            hdr[4] = 0x00; hdr[5] = 0x00

        # Data field: copy, truncate, or pad with 0x00
        body = bytearray(self.tm_body_len)
        copy_n = min(len(spp), self.tm_body_len)
        body[:copy_n] = spp[:copy_n]

        frame = bytes(hdr + body)
        frame_len = len(frame)  # == self.frame_len

        # Ensure output buffer is large enough this call
        if len(out) < frame_len:
            return 0

        # Write the frame
        out[:frame_len] = np.frombuffer(frame, dtype=np.uint8)

        # Emit a new packet_len tag at the start of the output frame
        self.add_item_tag(0, self.nitems_written(0), self.len_key, pmt.from_long(frame_len))

        # Consume exactly the SPP bytes we just framed
        self.consume(0, spp_len)
        return frame_len
