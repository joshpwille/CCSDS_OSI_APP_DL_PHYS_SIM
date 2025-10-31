import numpy as np, pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, len_tag_key="packet_len"):
        gr.basic_block.__init__(self, name="len_meter_ts",
                                in_sig=[np.uint8], out_sig=[np.float32])
        self.len_key = pmt.intern(len_tag_key)

    def general_work(self, input_items, output_items):
        inp, out = input_items[0], output_items[0]
        n = len(inp)
        if n == 0 or len(out) == 0:
            return 0
        n_read = self.nitems_read(0)
        tags = self.get_tags_in_window(0, 0, n, self.len_key)
        if not tags:
            return 0
        t = tags[0]
        rel = int(t.offset - n_read)
        if rel > 0:
            self.consume(0, rel); 
            return 0
        L = int(pmt.to_long(t.value))
        if n < L:  # wait for full frame in this window
            return 0
        out[0] = float(L)
        self.consume(0, L)   # advance exactly one frame
        return 1
