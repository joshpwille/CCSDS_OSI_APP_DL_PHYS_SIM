import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    """
    TM body packer: accumulates incoming bytes and emits fixed-size bodies.

    - Input:  bytes, may arrive as smaller tagged SPP chunks (e.g., 144B).
              Tags are not required; stream can be continuous.
    - Output: bytes in exact chunks of `body_len` (default 1109).
              At the start of each chunk, emits tag {len_tag_key: body_len}.
    - Tag policy: TPP_DONT (we re-tag only the length tag at output boundaries).
    - Padding: if `flush` message is received and a partial body remains,
               pads with `pad_byte` and emits one final body.

    Parameters:
      body_len:      int   (default 1109)
      len_tag_key:   str   (default "packet_len")
      pad_byte:      int   (default 0x00)
    """

    def __init__(self, body_len=1109, len_tag_key="packet_len", pad_byte=0):
        gr.basic_block.__init__(self,
            name="tm_body_packer",
            in_sig=[np.uint8],
            out_sig=[np.uint8])
        self.body_len = int(body_len)
        self.len_tag_key_str = str(len_tag_key)
        self.len_tag_key = pmt.intern(self.len_tag_key_str)
        self.pad_byte = int(pad_byte) & 0xFF

        self.set_tag_propagation_policy(gr.TPP_DONT)

        # internal state
        self._buf = bytearray()
        self._pending_flush = False  # set true when 'flush' message arrives

        # message port for explicit flush/pad of final partial body
        self.message_port_register_in(pmt.intern("flush"))
        self.set_msg_handler(pmt.intern("flush"), self._on_flush)

    def _on_flush(self, msg):
        # any message triggers a flush of the last partial body (with padding)
        self._pending_flush = True

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        n_in = len(inp)
        n_out = len(out)

        if n_in == 0 and n_out == 0:
            return 0

        # 1) Ingest everything available from input into our buffer
        if n_in:
            self._buf.extend(bytes(inp))
            self.consume(0, n_in)

        produced = 0
        out_room = n_out

        # 2) Emit as many full bodies as will fit
        while out_room >= self.body_len and len(self._buf) >= self.body_len:
            # add length tag at this output frame boundary
            self.add_item_tag(0,
                              self.nitems_written(0) + produced,
                              self.len_tag_key,
                              pmt.from_long(self.body_len))
            # copy one body
            out[produced:produced+self.body_len] = np.frombuffer(
                self._buf[:self.body_len], dtype=np.uint8
            )
            # drop from buffer
            del self._buf[:self.body_len]

            produced += self.body_len
            out_room -= self.body_len

        # 3) If a flush was requested and we have a partial leftover, pad & emit one final
        if self._pending_flush and out_room >= self.body_len and 0 < len(self._buf) < self.body_len:
            need = self.body_len - len(self._buf)
            self._buf.extend(bytes([self.pad_byte]) * need)

            # tag and write the padded frame
            self.add_item_tag(0,
                              self.nitems_written(0) + produced,
                              self.len_tag_key,
                              pmt.from_long(self.body_len))
            out[produced:produced+self.body_len] = np.frombuffer(
                self._buf[:self.body_len], dtype=np.uint8
            )
            del self._buf[:self.body_len]
            produced += self.body_len
            out_room -= self.body_len
            # flush handled
            self._pending_flush = False

        return produced

