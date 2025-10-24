import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    """
    Reads CCSDS Space Packets from a raw byte stream and adds a 'packet_len' tag
    at the start of each packet. Assumes packets are concatenated back-to-back.
    CCSDS primary header: 6 bytes total; bytes [4:6] is Packet Length (big-endian)
    meaning: total bytes in the Data Field minus 1. So total packet bytes =
    6 + (PacketLength + 1).
    """
    def __init__(self, len_tag_key="packet_len"):
        gr.basic_block.__init__(self,
            name="spp_len_tagger",
            in_sig=[np.uint8],
            out_sig=[np.uint8])
        self.len_tag_key = pmt.intern(len_tag_key)
        self._buf = bytearray()
        self._abs_out = 0  # absolute output item index

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        # append new input to buffer
        self._buf += bytes(inp.tobytes())

        produced = 0
        consumed = len(inp)

        # process complete packets from buffer
        while True:
            if len(self._buf) < 6:
                break  # need full primary header

            # CCSDS is big-endian
            pkt_len_field = (self._buf[4] << 8) | self._buf[5]
            total_len = 6 + (pkt_len_field + 1)  # primary hdr + data field

            if len(self._buf) < total_len:
                break  # wait for full packet

            # emit a packet_len tag at the *current* output absolute index
            self.add_item_tag(0, self._abs_out, self.len_tag_key, pmt.from_long(total_len))

            # copy this packet to output
            n = min(len(out) - produced, total_len)
            if n < total_len:
                # not enough output space this call
                break

            out[produced:produced+total_len] = np.frombuffer(self._buf[:total_len], dtype=np.uint8)
            produced += total_len
            self._abs_out += total_len

            # drop packet from buffer
            del self._buf[:total_len]

        # if there's leftover room in out, copy whatever we can (no tags)
        spill = min(len(out) - produced, len(self._buf))
        if spill:
            out[produced:produced+spill] = np.frombuffer(self._buf[:spill], dtype=np.uint8)
            produced += spill
            self._abs_out += spill
            del self._buf[:spill]

        self.consume(0, consumed)
        return produced

