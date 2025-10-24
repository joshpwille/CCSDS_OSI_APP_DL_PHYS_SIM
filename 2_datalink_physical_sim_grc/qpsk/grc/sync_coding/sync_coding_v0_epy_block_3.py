import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    """
    CCSDS convolutional encoder (K=7, r=1/2, generators 171/133 octal).
    Input : BYTES with per-frame 'packet_len' tag (pre-FEC CADU: TM+ASM)
    Output: BYTES with updated 'packet_len' tag (post-FEC CADU bytes)
    Emits the output length tag exactly at the first encoded byte of each frame.
    """
    def __init__(self,
                 len_tag_key="packet_len",
                 K=7,
                 gen0=0o171,
                 gen1=0o133,
                 msb_first=True,
                 reset_each_frame=True):
        gr.sync_block.__init__(
            self,
            name="ccsds_conv_k7_r12_epy",
            in_sig=[np.uint8],
            out_sig=[np.uint8],
        )
        # Params
        self.len_tag_key = str(len_tag_key)
        self.len_key_sym = pmt.intern(self.len_tag_key)
        self.K = int(K)
        self.gen0 = np.uint32(gen0)
        self.gen1 = np.uint32(gen1)
        self._mask = np.uint32((1 << self.K) - 1)
        self.msb_first = bool(msb_first)
        self.reset_each_frame = bool(reset_each_frame)

        # Internal
        self._inbuf = bytearray()
        self._outbuf = bytearray()
        self._frame_queue = []     # pending input frame lengths (bytes)
        self._state = np.uint32(0)

        # Tag scheduling for output
        self._pending_out_frames = []  # list of encoded frame lengths (bytes)
        self._head_remaining = 0       # bytes remaining to write in current head frame

        # We will re-emit only our packet_len; do not propagate all tags blindly
        self.set_tag_propagation_policy(gr.TPP_DONT)

    # ---------- helpers ----------
    @staticmethod
    def _parity_u32(x):
        cnt = 0
        while x:
            x &= (x - 1)
            cnt ^= 1
        return cnt & 1

    def _bytes_to_bits(self, b):
        arr = np.frombuffer(bytes(b), dtype=np.uint8)
        if self.msb_first:
            shifts = np.arange(7, -1, -1, dtype=np.uint8)
        else:
            shifts = np.arange(0, 8, 1, dtype=np.uint8)
        bits = ((arr[:, None] >> shifts[None, :]) & 1).astype(np.uint8)
        return bits.reshape(-1)

    def _bits_to_bytes(self, bits):
        n = bits.size
        pad = (8 - (n % 8)) % 8
        if pad:
            bits = np.concatenate([bits, np.zeros(pad, dtype=np.uint8)])
        bits = bits.reshape(-1, 8)
        if self.msb_first:
            shifts = np.arange(7, -1, -1, dtype=np.uint8)
        else:
            shifts = np.arange(0, 8, 1, dtype=np.uint8)
        packed = (bits * (1 << shifts)).sum(axis=1).astype(np.uint8)
        return bytes(packed)

    def _conv_encode_bits(self, in_bits):
        out = np.empty(in_bits.size * 2, dtype=np.uint8)
        state = self._state
        mask = self._mask
        g0 = self.gen0
        g1 = self.gen1
        idx = 0
        for b in in_bits:
            state = ((state << np.uint32(1)) | np.uint32(int(b & 1))) & mask
            out[idx]   = self._parity_u32(int(state & g0))
            out[idx+1] = self._parity_u32(int(state & g1))
            idx += 2
        if self.reset_each_frame:
            self._state = np.uint32(0)
        else:
            self._state = state
        return out

    # ---------- input frame parsing ----------
    def _enqueue_len_tags(self, ninput_items):
        tags = self.get_tags_in_window(0, 0, ninput_items)
        for t in tags:
            try:
                key_str = pmt.symbol_to_string(t.key)
            except Exception:
                continue
            if key_str == self.len_tag_key and pmt.is_integer(t.value):
                L = int(pmt.to_long(t.value))
                if L > 0:
                    self._frame_queue.append(L)

    def _process_frames_to_outbuf(self):
        # Convert as many full frames as are available in _inbuf
        while self._frame_queue:
            need = self._frame_queue[0]
            if len(self._inbuf) < need:
                break
            # consume one input frame
            frame = self._inbuf[:need]
            del self._inbuf[:need]
            self._frame_queue.pop(0)

            # bytes -> bits -> encode -> bytes
            bits_in  = self._bytes_to_bits(frame)
            bits_out = self._conv_encode_bits(bits_in)
            enc      = self._bits_to_bytes(bits_out)  # exactly 2*need bytes

            # append to output buffer
            start_new_frame = (self._head_remaining == 0 and len(self._pending_out_frames) == 0 and len(self._outbuf) == 0)
            self._outbuf += enc

            # queue this encoded frame length for tag scheduling
            self._pending_out_frames.append(len(enc))
            # Note: we don't emit the tag yet; we emit it when the first byte of this frame is written.

    # ---------- work ----------
    def work(self, input_items, output_items):
        in0 = input_items[0]
        out0 = output_items[0]

        n_in = len(in0)
        if n_in:
            # ingest bytes and discover new frame tags
            self._inbuf += bytes(in0)
            self._enqueue_len_tags(n_in)
            self._process_frames_to_outbuf()

        # nothing to output?
        if not self._outbuf:
            self.consume_each(n_in)
            return 0

        ow = self.nitems_written(0)
        space = len(out0)
        produced = 0

        # Before writing any bytes in this call, if we are at a frame boundary,
        # emit the length tag at the current write head.
        while space > 0 and self._outbuf:
            if self._head_remaining == 0:
                # Starting a new encoded frame on the output stream
                if not self._pending_out_frames:
                    # Shouldn't happen, but guard anyway
                    break
                self._head_remaining = self._pending_out_frames[0]
                # Emit the tag RIGHT HERE at the start boundary
                self.add_item_tag(0, ow + produced, self.len_key_sym, pmt.from_long(self._head_remaining))

            # write up to the remainder of this frame (or available space)
            chunk = min(space, self._head_remaining, len(self._outbuf))
            if chunk <= 0:
                break

            out0[produced:produced+chunk] = np.frombuffer(self._outbuf[:chunk], dtype=np.uint8)
            del self._outbuf[:chunk]

            produced += chunk
            space    -= chunk
            self._head_remaining -= chunk

            if self._head_remaining == 0:
                # finished a frame; pop it
                if self._pending_out_frames:
                    self._pending_out_frames.pop(0)
                # loop continues; if there's still space and more frames queued,
                # the next iteration will emit the next tag at the new boundary.

        self.consume_each(n_in)
        return produced
