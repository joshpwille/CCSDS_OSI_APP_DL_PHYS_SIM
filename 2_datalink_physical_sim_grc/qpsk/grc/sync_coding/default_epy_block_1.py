import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    """
    CCSDS TM byte-wise randomizer / de-randomizer.

    - LFSR: x^15 + x^14 + 1 (CCSDS PN), 15-bit, seed default 0x7FFF (all ones)
    - Restarts PN at each frame, where frame boundaries are indicated by a
      length tag (e.g., "packet_len") whose value is the byte length of the frame.
    - Forwards all tags with correct relative offsets.
    - XOR is symmetric, so this works as both randomizer and de-randomizer.

    Parameters
    ----------
    len_tag_key : str
        Length tag key used throughout your flowgraph (usually "packet_len").
    seed : int
        15-bit seed for the LFSR (default 0x7FFF per CCSDS).
    restart_per_frame : bool
        If True, re-seed LFSR at the start of each frame (default True).
    enabled : bool
        If False, pass-through with tag forwarding (default True).
    """

    def __init__(self, len_tag_key="packet_len", seed=0x7FFF,
                 restart_per_frame=True, enabled=True):
        gr.basic_block.__init__(self,
            name="ccsds_tm_randomizer",
            in_sig=[np.uint8],
            out_sig=[np.uint8])

        # Params
        self.len_tag_key_str = str(len_tag_key)
        self.len_tag_key = pmt.intern(self.len_tag_key_str)
        self.seed = int(seed) & 0x7FFF  # 15-bit
        self.restart_per_frame = bool(restart_per_frame)
        self.enabled = bool(enabled)

        # State
        self._lfsr = self.seed
        self._frame_bytes_left = 0  # counts down within a frame
        self._abs_out = 0  # absolute output index for tag forwarding

    # ---- PN generator (CCSDS 15-bit LFSR) ----
    @staticmethod
    def _step_lfsr(state):
        """
        One bit step for polynomial x^15 + x^14 + 1 (feedback from bit14 ^ bit13).
        Shift left; output bit taken as previous MSB (bit14) if needed.
        Returns new state (15-bit).
        """
        # taps at 14 and 13 (0-based indexing for 15-bit register [14..0])
        new_bit = ((state >> 14) ^ (state >> 13)) & 0x1
        state = ((state << 1) & 0x7FFF) | new_bit
        return state

    def _next_pn_byte(self):
        """
        Generate 8 PN bits from the current LFSR, MSB-first into a byte.
        """
        out_byte = 0
        for _ in range(8):
            # Use current MSB as the next PN bit (before stepping)
            pn_bit = (self._lfsr >> 14) & 0x1
            out_byte = ((out_byte << 1) | pn_bit) & 0xFF
            self._lfsr = self._step_lfsr(self._lfsr)
        return out_byte

    def _reset_pn(self):
        self._lfsr = self.seed

    # ---- Tag forwarding helper ----
    def _forward_tags(self, n_input, produced):
        """
        Forward all input tags into the output at the correct offsets.
        """
        in0 = 0
        nread = self.nitems_read(in0)
        nwrite = self.nitems_written(in0)

        tags = []
        self.get_tags_in_range(tags, in0, nread, nread + n_input)
        for t in tags:
            # preserve key/value/srcid; shift offset by the amount already produced in this call
            rel = t.offset - nread  # 0..n_input-1
            out_off = nwrite + produced + rel
            self.add_item_tag(in0, out_off, t.key, t.value, t.srcid)

    # ---- Handle incoming length tags (frame boundaries) ----
    def _consume_length_tags(self, n_input):
        """
        Look for new length tags within the current input window and, if found,
        initiate a new frame (optionally restarting the PN).
        Returns a list of (rel_offset, frame_len) found in this window.
        """
        in0 = 0
        nread = self.nitems_read(in0)

        tags = []
        self.get_tags_in_range(tags, in0, nread, nread + n_input)

        found = []
        for t in tags:
            if pmt.equal(t.key, self.len_tag_key):
                # tag.value should be an integer length
                try:
                    L = int(pmt.to_long(t.value))
                except Exception:
                    # ignore malformed values
                    continue
                rel = t.offset - nread  # where in the current input window the frame starts
                if L > 0:
                    found.append((rel, L))
        # sort by relative offset in case there are multiple in-window
        found.sort(key=lambda x: x[0])
        return found

    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        n_in = len(inp)
        n_out = len(out)
        if n_in == 0 or n_out == 0:
            return 0

        produced = 0
        consumed = 0

        # 1) Forward tags (all of them) so sinks/downstream see lengths, etc.
        #    We forward upfront, then write bytes. Offsets are corrected by "produced".
        self._forward_tags(n_in, produced=0)

        # 2) Gather any new frame-start tags inside this window.
        starts = self._consume_length_tags(n_in)
        # We'll walk through the input, possibly hitting multiple new-frame starts.

        cursor = 0  # how many input bytes we've already handled in this call

        def process_chunk(chunk_len):
            """
            Process 'chunk_len' bytes from inp[cursor:cursor+chunk_len] into out[produced:...].
            Applies PN only while self._frame_bytes_left > 0.
            """
            nonlocal produced, consumed, cursor

            if chunk_len <= 0:
                return

            n = min(chunk_len, n_out - produced)
            if n <= 0:
                return  # no output space; let scheduler call again

            if not self.enabled or self._frame_bytes_left <= 0:
                # pass-through
                out[produced:produced+n] = inp[cursor:cursor+n]
            else:
                # we may have less than n bytes left in this frame; handle that first
                to_rand = min(n, self._frame_bytes_left)

                # XOR the part within the frame
                if to_rand > 0:
                    # generate PN bytes for to_rand bytes
                    # do it in small chunks to avoid Python loop overhead
                    # but we need per-byte PN; loop is acceptable at this scale
                    for i in range(to_rand):
                        out[produced+i] = inp[cursor+i] ^ self._next_pn_byte()

                # copy any trailing bytes that fall *after* the frame (unlikely unless tags overlap weirdly)
                if n > to_rand:
                    out[produced+to_rand:produced+n] = inp[cursor+to_rand:cursor+n]

                self._frame_bytes_left -= to_rand

            produced += n
            consumed += n
            cursor += n

        # Walk through input, respecting any new frame starts we see.
        for rel_off, frame_len in starts:
            # First, process bytes *before* this frame starts (pass-through)
            pre = rel_off - cursor
            if pre > 0:
                process_chunk(pre)
                if produced >= n_out:
                    break  # no more room

            # Start a new frame at this point
            if self.restart_per_frame:
                self._reset_pn()
            self._frame_bytes_left = frame_len

            # From here on, loop continues; the next process_chunk() call will randomize bytes.

        # After handling all in-window frame starts, process whatever remains
        if produced < n_out and cursor < n_in:
            process_chunk(n_in - cursor)

        # Update absolute output index for any external bookkeeping
        self._abs_out += produced

        self.consume(0, consumed)
        return produced

