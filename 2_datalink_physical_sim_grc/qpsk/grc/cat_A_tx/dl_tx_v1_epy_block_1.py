import numpy as np
from gnuradio import gr
import pmt

class blk(gr.basic_block):
    """
    CCSDS TM Randomizer / De-randomizer (robust, frame-tag driven).

    - PN polynomial: x^15 + x^14 + 1 (CCSDS)
    - Seed: 0x7FFF (all ones), reseeded at each frame start (by default)
    - Frame boundaries are given by a length tag (e.g., "packet_len"), whose value is the *byte length* of the frame
      produced by your TM framer (i.e., TM primary header + TM data field).
    - Tag-safe: forwards all input tags to output with corrected offsets.

    Parameters
    ----------
    len_tag_key : str
        Name of the length tag carrying the frame length (default: "packet_len").
    seed : int
        15-bit initial seed (default 0x7FFF per CCSDS).
    restart_per_frame : bool
        If True, reseed PN at each frame start (default True).
    enabled : bool
        If False, pass-through (still forwards tags; default True).
    mode : str
        One of {"frame","data_field","packet_zone"}:
          - "frame"       : randomize entire TM frame (header + data field).
          - "data_field"  : skip 6-byte TM primary header; randomize only TM data field.
          - "packet_zone" : skip 6-byte TM primary header + 'sec_hdr_len' bytes; randomize only packet zone.
    sec_hdr_len : int
        Length of TM Secondary Header (bytes) if using "packet_zone" mode (default 0).
        Ignored in other modes.
    pri_hdr_len : int
        Primary header length (bytes). For CCSDS TM this is 6. (Default 6)
    max_tag_per_window : int
        Guardrail to avoid pathological cases (default 1024).

    Notes
    -----
    - XOR randomization is symmetric; the same block de-randomizes.
    - This block assumes that *each* frame is tagged exactly once at its *first byte* with len_tag_key.
    - If multiple frames appear within one scheduler call, all are handled.
    """

    def __init__(self,
                 len_tag_key="packet_len",
                 seed=0x7FFF,
                 restart_per_frame=True,
                 enabled=True,
                 mode="frame",
                 sec_hdr_len=0,
                 pri_hdr_len=6,
                 max_tag_per_window=1024):

        gr.basic_block.__init__(self,
            name="ccsds_tm_randomizer_v2",
            in_sig=[np.uint8],
            out_sig=[np.uint8]
        )

        # ---- Params
        self.len_tag_key_str = str(len_tag_key)
        self.len_tag_key = pmt.intern(self.len_tag_key_str)

        self.seed = int(seed) & 0x7FFF
        if self.seed == 0:
            # 15-bit LFSR cannot be zero; force to CCSDS default
            self.seed = 0x7FFF

        self.restart_per_frame = bool(restart_per_frame)
        self.enabled = bool(enabled)

        self.mode = str(mode).lower()
        if self.mode not in ("frame", "data_field", "packet_zone"):
            raise ValueError("mode must be 'frame', 'data_field', or 'packet_zone'.")

        self.sec_hdr_len = max(0, int(sec_hdr_len))
        self.pri_hdr_len = max(0, int(pri_hdr_len))
        self.max_tag_per_window = int(max_tag_per_window)

        # ---- State
        self._lfsr = self.seed
        self._frame_bytes_left = 0   # remaining bytes to randomize in *this frame*
        self._skip_left = 0          # per-frame leading bytes to skip (per mode)
        self._abs_out = 0            # optional counter

        # Stats (optional)
        self.frames_seen = 0
        self.frames_rand = 0
        self.frames_skipped = 0

    # ---- PN generator (CCSDS 15-bit LFSR)
    @staticmethod
    def _step_lfsr(state):
        # feedback from bit14 ^ bit13 (1-indexed x^15 + x^14 + 1)
        new_bit = ((state >> 14) ^ (state >> 13)) & 0x1
        return ((state << 1) & 0x7FFF) | new_bit

    def _pn_bytes(self, n):
        """
        Generate 'n' PN bytes from current LFSR state (MSB-first).
        Vectorized for fewer Python-level loops.
        """
        out = np.empty(n, dtype=np.uint8)
        s = self._lfsr
        for i in range(n):
            b = 0
            # Unroll 8 bit-steps into one byte
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            b = (b << 1) | ((s >> 14) & 1); s = self._step_lfsr(s)
            out[i] = b
        self._lfsr = s
        return out

    def _reset_pn(self):
        self._lfsr = self.seed

    # ---- Tag forwarding (preserve all tags, not just length)
    def _forward_tags(self, n_input, produced):
        in0 = 0
        nread = self.nitems_read(in0)
        nwrite = self.nitems_written(in0)

        abs_start = nread
        abs_end   = nread + n_input

        tags = self.get_tags_in_range(in0, abs_start, abs_end)
        # guard against pathological cases
        if len(tags) > self.max_tag_per_window:
            tags = tags[:self.max_tag_per_window]

        for t in tags:
            rel = int(t.offset - nread)  # 0..n_input-1
            if rel < 0 or rel >= n_input:
                continue
            out_off = nwrite + produced + rel
            try:
                self.add_item_tag(in0, out_off, t.key, t.value, t.srcid)
            except TypeError:
                self.add_item_tag(in0, out_off, t.key, t.value)

    # ---- Consume only (start_offset, frame_len) for our length-tag key
    def _find_frame_starts(self, n_input):
        in0 = 0
        nread = self.nitems_read(in0)
        abs_start = nread
        abs_end   = nread + n_input

        tags = self.get_tags_in_range(in0, abs_start, abs_end, self.len_tag_key)
        if not tags:
            return []

        items = []
        for t in tags:
            try:
                L = int(pmt.to_long(t.value))
            except Exception:
                continue
            if L <= 0:
                continue
            rel = int(t.offset - nread)
            if rel < 0 or rel >= n_input:
                continue
            items.append((rel, L))

        if not items:
            return []

        # sort and dedup by rel offset (ignore any overlapping/duplicate starts)
        items.sort(key=lambda x: x[0])
        dedup = []
        last_rel = None
        for rel, L in items:
            if rel != last_rel:
                dedup.append((rel, L))
                last_rel = rel

        return dedup[:self.max_tag_per_window]

    # ---- Compute per-frame skip (based on mode)
    def _compute_skip(self):
        if self.mode == "frame":
            return 0
        elif self.mode == "data_field":
            return self.pri_hdr_len
        elif self.mode == "packet_zone":
            return self.pri_hdr_len + self.sec_hdr_len
        else:
            return 0

    # ---- Core
    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]

        n_in  = len(inp)
        n_out = len(out)
        if n_in == 0 or n_out == 0:
            return 0

        produced = 0
        consumed = 0
        cursor   = 0

        # Forward *all* input tags seen in this window
        self._forward_tags(n_in, produced=0)

        # Find any frame starts in this window for our len_tag_key
        starts = self._find_frame_starts(n_in)
        si = 0

        # Local helper: process N input bytes from current cursor
        def process_bytes(nbytes):
            nonlocal produced, consumed, cursor

            if nbytes <= 0:
                return
            n = min(nbytes, n_out - produced)
            if n <= 0:
                return

            if not self.enabled:
                # bypass
                out[produced:produced+n] = inp[cursor:cursor+n]
                produced += n
                consumed += n
                cursor   += n
                return

            # Apply per-frame skip first
            if self._skip_left > 0:
                s = min(self._skip_left, n)
                # pass-through the skipped leading bytes
                out[produced:produced+s] = inp[cursor:cursor+s]
                self._skip_left -= s
                produced += s
                consumed += s
                cursor   += s
                n -= s
                if n == 0:
                    return  # all consumed from this call

            if self._frame_bytes_left > 0 and n > 0:
                to_rand = min(n, self._frame_bytes_left)
                # XOR with PN
                pn = self._pn_bytes(to_rand)
                out[produced:produced+to_rand] = np.bitwise_xor(inp[cursor:cursor+to_rand], pn)

                produced += to_rand
                consumed += to_rand
                cursor   += to_rand
                self._frame_bytes_left -= to_rand
                n -= to_rand

            # Any trailing bytes beyond frame boundary are pass-through
            if n > 0:
                out[produced:produced+n] = inp[cursor:cursor+n]
                produced += n
                consumed += n
                cursor   += n

        # Walk frames that start within this scheduler window
        while si < len(starts):
            rel_off, frame_len = starts[si]
            # bytes before the frame start (from current cursor)
            pre = rel_off - cursor
            if pre > 0:
                process_bytes(pre)
                if produced >= n_out:
                    break

            # Start of a new frame at current cursor
            if self.restart_per_frame:
                self._reset_pn()
            self._frame_bytes_left = int(frame_len)
            self._skip_left = self._compute_skip()

            self.frames_seen += 1
            if self._frame_bytes_left > 0:
                self.frames_rand += 1

            si += 1

        # After walking all starts, process whatever input remains in this window
        if produced < n_out and cursor < n_in:
            process_bytes(n_in - cursor)

        self._abs_out += produced
        self.consume(0, consumed)
        return produced

