import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    """
    CCSDS TM byte-wise randomizer / de-randomizer.

    - LFSR: x^15 + x^14 + 1 (15-bit), default seed 0x7FFF (all ones)
    - Restarts PN at each frame, where frame boundaries are marked by a
      length tag (e.g., "packet_len") giving the frame length in BYTES.
    - Symmetric XOR ⇒ works for randomize *and* derandomize.

    Params:
      len_tag_key="packet_len", seed=0x7FFF, restart_per_frame=True, enabled=True
    """

    def __init__(self, len_tag_key="packet_len", seed=0x7FFF,
                 restart_per_frame=True, enabled=True):
        gr.basic_block.__init__(self,
            name="ccsds_tm_randomizer",
            in_sig=[np.uint8],
            out_sig=[np.uint8])

        # --- Params
        self.len_tag_key_str = str(len_tag_key)
        self.len_tag_key = pmt.intern(self.len_tag_key_str)
        self.seed = int(seed) & 0x7FFF
        self.restart_per_frame = bool(restart_per_frame)
        self.enabled = bool(enabled)

        # --- State
        self._lfsr = self.seed
        self._frame_bytes_left = 0

        # IMPORTANT: don't auto-propagate tags; we will forward/re-emit explicitly
        self.set_tag_propagation_policy(gr.TPP_DONT)

    # ---- PN generator (CCSDS 15-bit LFSR) ----
    @staticmethod
    def _step_lfsr(state):
        # taps at bit14 and bit13 (0-based, 15-bit register [14..0])
        new_bit = ((state >> 14) ^ (state >> 13)) & 0x1
        state = ((state << 1) & 0x7FFF) | new_bit
        return state

    def _next_pn_byte(self):
        out_byte = 0
        for _ in range(8):
            pn_bit = (self._lfsr >> 14) & 0x1   # MSB before stepping
            out_byte = ((out_byte << 1) | pn_bit) & 0xFF
            self._lfsr = self._step_lfsr(self._lfsr)
        return out_byte

    def _reset_pn(self):
        self._lfsr = self.seed

    # ---- Tag forwarding helper ----
    def _forward_tags(self, n_input, produced):
        """Forward all input tags EXCEPT the length tag (we re-emit it)."""
        in0 = 0
        nread  = self.nitems_read(in0)
        out_hd = self.nitems_written(in0) + produced

        for t in self.get_tags_in_range(in0, nread, nread + n_input):
            if pmt.equal(t.key, self.len_tag_key):
                continue  # we'll re-emit a clean length tag at frame start
            rel = t.offset - nread
            self.add_item_tag(0, out_hd + rel, t.key, t.value)

    # ---- Detect incoming length tags within current window ----
    def _consume_length_tags(self, n_input):
        """Return sorted list of (rel_offset, frame_len) for new frames in-window."""
        in0 = 0
        nread = self.nitems_read(in0)
        found = []

        # Ask GNU Radio to filter by key on our behalf
        for t in self.get_tags_in_range(in0, nread, nread + n_input, self.len_tag_key):
            try:
                L = int(pmt.to_long(t.value))
            except Exception:
                continue
            if L > 0:
                rel = t.offset - nread
                found.append((rel, L))

        found.sort(key=lambda x: x[0])
        return found

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        n_in  = len(inp)
        n_out = len(out)
        if n_in == 0 or n_out == 0:
            return 0

        produced = 0
        consumed = 0

        # Forward non-length tags with corrected offsets
        self._forward_tags(n_in, produced=0)

        # Collect any new frame-start tags appearing in this call
        starts = self._consume_length_tags(n_in)
        cursor = 0  # bytes already handled from 'inp' in this call

        def process_chunk(chunk_len):
            nonlocal produced, consumed, cursor
            if chunk_len <= 0:
                return
            n = min(chunk_len, n_out - produced)
            if n <= 0:
                return

            if not self.enabled or self._frame_bytes_left <= 0:
                out[produced:produced+n] = inp[cursor:cursor+n]
            else:
                to_rand = min(n, self._frame_bytes_left)
                for i in range(to_rand):
                    out[produced+i] = inp[cursor+i] ^ self._next_pn_byte()
                if n > to_rand:
                    out[produced+to_rand:produced+n] = inp[cursor+to_rand:cursor+n]
                self._frame_bytes_left -= to_rand

            produced += n
            consumed += n
            cursor   += n

        # Walk input; when we hit a new frame start, (re)seed and re-tag
        for rel_off, frame_len in starts:
            # bytes before the frame start (pass-through or continuing prior frame)
            pre = rel_off - cursor
            if pre > 0:
                process_chunk(pre)
                if produced >= n_out:
                    break

            # Start a new frame exactly here
            if self.restart_per_frame:
                self._reset_pn()
            self._frame_bytes_left = frame_len

            # Re-emit a clean length tag at the output head for this frame
            self.add_item_tag(0,
                              self.nitems_written(0) + produced,
                              self.len_tag_key,
                              pmt.from_long(frame_len))

            # processing continues; next process_chunk() will apply PN

        # After handling all starts, process the remainder of input window
        if produced < n_out and cursor < n_in:
            process_chunk(n_in - cursor)

        self.consume(0, consumed)
        return produced

