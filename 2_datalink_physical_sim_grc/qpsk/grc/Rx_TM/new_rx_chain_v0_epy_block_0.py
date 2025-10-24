import numpy as np
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    """
    CCSDS Viterbi decoder (K=7, r=1/2, 171/133) — SOFT decision (float inputs).

    Input : float32 per coded bit (one float per bit), framed by 'packet_len' tags
            whose value is the NUMBER OF CODED BITS in the frame (not bytes).
            For a pre-FEC frame of L bytes, packet_len_in = 16*L.
            'soft_mode' controls interpretation of floats:
              - 'pm1' (default): +A ≈ bit 0, -A ≈ bit 1
              - 'llr'         : +LLR favors 0, -LLR favors 1
    Output: uint8 bytes with 'packet_len' tag = L (decoded bytes), tag emitted
            at the FIRST output byte of each frame (mirrors your TX scheduling).

    Notes:
      - Assumes reset_each_frame=True at encoder (trellis start state = 0).
      - If your upstream produces different scaling, no problem; pm1 mode
        uses Euclidean branch metrics, scale-invariant up to a constant.
    """
    def __init__(self,
                 len_tag_key="packet_len",
                 K=7,
                 gen0=0o171,
                 gen1=0o133,
                 reset_each_frame=True,
                 soft_mode="pm1"):  # 'pm1' or 'llr'
        gr.sync_block.__init__(
            self,
            name="ccsds_viterbi_k7_r12_soft_epy",
            in_sig=[np.float32],
            out_sig=[np.uint8],
        )
        self.len_tag_key = str(len_tag_key)
        self.len_key_sym = pmt.intern(self.len_tag_key)
        self.K = int(K)
        self.gen0 = int(gen0)
        self.gen1 = int(gen1)
        self.reset_each_frame = bool(reset_each_frame)
        self.soft_mode = str(soft_mode).lower()

        # Trellis
        self.NSTATES = 1 << (self.K - 1)  # 64
        self._trellis_ns   = np.zeros((self.NSTATES, 2), dtype=np.uint8)
        self._trellis_obit = np.zeros((self.NSTATES, 2, 2), dtype=np.uint8)  # expected 2 bits
        self._build_trellis()

        # Buffers & frame bookkeeping
        self._inbuf  = np.empty(0, dtype=np.float32)  # soft bits buffer
        self._outbuf = bytearray()
        self._frame_queue_bits = []   # input frame sizes in *bits* (coded)
        self._pending_out_frames = [] # decoded frame sizes in *bytes*
        self._head_remaining = 0

        self.set_tag_propagation_policy(gr.TPP_DONT)

    # ---------- trellis ----------
    @staticmethod
    def _parity_u32(x: int) -> int:
        # fast parity (like your TX)
        v = x
        v ^= v >> 16; v ^= v >> 8; v ^= v >> 4
        v &= 0xF
        return (0x6996 >> v) & 1

    def _build_trellis(self):
        maskK = (1 << self.K) - 1
        maskS = (1 << (self.K - 1)) - 1
        for s in range(self.NSTATES):
            for u in (0, 1):
                full = ((s << 1) | u) & maskK
                ns = (full >> 1) & maskS
                b0 = self._parity_u32(full & self.gen0)
                b1 = self._parity_u32(full & self.gen1)
                self._trellis_ns[s, u] = ns
                self._trellis_obit[s, u, 0] = b0
                self._trellis_obit[s, u, 1] = b1

    # ---------- branch metrics ----------
    @staticmethod
    def _euclid_pair(r0, r1, e0, e1):
        """
        Euclidean metric for 'pm1' softs:
        map expected bit 0 -> +1, bit 1 -> -1, then sum squared error.
        """
        t0 = 1.0 if e0 == 0 else -1.0
        t1 = 1.0 if e1 == 0 else -1.0
        d0 = r0 - t0
        d1 = r1 - t1
        return d0*d0 + d1*d1

    @staticmethod
    def _llr_pair(r0, r1, e0, e1):
        """
        LLR metric (additive, smaller=better):
          if expected=0, cost += -LLR; if expected=1, cost += +LLR
        """
        m0 = (-r0) if e0 == 0 else (+r0)
        m1 = (-r1) if e1 == 0 else (+r1)
        # ensure non-negative by offset (optional); not required for DP
        return m0 + m1

    # ---------- Viterbi core (soft) ----------
    def _viterbi_soft_decode(self, soft_bits: np.ndarray) -> bytes:
        # Expect pairs of soft bits per input bit
        nsoft = soft_bits.size
        if nsoft & 1:
            soft_bits = soft_bits[:-1]
            nsoft -= 1
        nsym = nsoft // 2  # number of input bits to recover

        # Path metrics
        BIG = 1e12
        pm = np.full(self.NSTATES, BIG, dtype=np.float64)
        pm_new = np.full(self.NSTATES, BIG, dtype=np.float64)
        if self.reset_each_frame:
            pm[:] = BIG; pm[0] = 0.0
        else:
            pm[:] = 0.0

        prev_state  = np.zeros((nsym, self.NSTATES), dtype=np.uint8)
        decided_bit = np.zeros((nsym, self.NSTATES), dtype=np.uint8)

        use_llr = (self.soft_mode == "llr")

        # iterate symbol pairs
        for t in range(nsym):
            r0 = float(soft_bits[2*t + 0])
            r1 = float(soft_bits[2*t + 1])
            pm_new[:] = BIG
            for s in range(self.NSTATES):
                cost_s = pm[s]
                if cost_s >= BIG:  # unreachable
                    continue

                # branch u=0
                ns0 = self._trellis_ns[s, 0]
                e00 = int(self._trellis_obit[s, 0, 0])
                e01 = int(self._trellis_obit[s, 0, 1])
                bm0 = (self._llr_pair(r0, r1, e00, e01) if use_llr
                       else self._euclid_pair(r0, r1, e00, e01))
                c0 = cost_s + bm0
                if c0 < pm_new[ns0]:
                    pm_new[ns0] = c0
                    prev_state[t, ns0]  = s
                    decided_bit[t, ns0] = 0

                # branch u=1
                ns1 = self._trellis_ns[s, 1]
                e10 = int(self._trellis_obit[s, 1, 0])
                e11 = int(self._trellis_obit[s, 1, 1])
                bm1 = (self._llr_pair(r0, r1, e10, e11) if use_llr
                       else self._euclid_pair(r0, r1, e10, e11))
                c1 = cost_s + bm1
                if c1 < pm_new[ns1]:
                    pm_new[ns1] = c1
                    prev_state[t, ns1]  = s
                    decided_bit[t, ns1] = 1

            pm, pm_new = pm_new, pm

        # traceback
        end_state = int(np.argmin(pm))
        bits_dec = np.zeros(nsym, dtype=np.uint8)
        s = end_state
        for t in range(nsym-1, -1, -1):
            b = decided_bit[t, s]
            bits_dec[t] = b
            s = prev_state[t, s]

        # pack to bytes (MSB-first inside each byte)
        pad = (8 - (nsym % 8)) % 8
        if pad:
            bits_dec = np.concatenate([bits_dec, np.zeros(pad, dtype=np.uint8)])
        bits_dec = bits_dec.reshape(-1, 8)
        shifts = np.arange(7, -1, -1, dtype=np.uint8)
        packed = (bits_dec * (1 << shifts)).sum(axis=1).astype(np.uint8)
        return bytes(packed)

    # ---------- tag parsing ----------
    def _enqueue_len_tags(self, ninput_items):
        # collect tags in current window
        tags = self.get_tags_in_window(0, 0, ninput_items)
        for t in tags:
            try:
                key_str = pmt.symbol_to_string(t.key)
            except Exception:
                continue
            if key_str == self.len_tag_key and pmt.is_integer(t.value):
                L_soft_bits = int(pmt.to_long(t.value))
                if L_soft_bits > 0:
                    self._frame_queue_bits.append(L_soft_bits)

    def _process_frames_to_outbuf(self):
        # Consume frames as soon as enough soft bits are buffered
        while self._frame_queue_bits:
            need_bits = self._frame_queue_bits[0]
            if self._inbuf.size < need_bits:
                break
            soft = self._inbuf[:need_bits].astype(np.float32, copy=False)
            self._inbuf = self._inbuf[need_bits:]
            self._frame_queue_bits.pop(0)

            # Decode
            dec_bytes = self._viterbi_soft_decode(soft)
            self._outbuf += dec_bytes

            # Output length in BYTES = need_bits / 16
            L_out = need_bits // 16
            self._pending_out_frames.append(L_out)

    # ---------- work ----------
    def work(self, input_items, output_items):
        in0 = input_items[0]  # float32
        out0 = output_items[0]

        n_in = len(in0)
        if n_in:
            # append softs
            if self._inbuf.size == 0:
                self._inbuf = np.array(in0, dtype=np.float32, copy=True)
            else:
                self._inbuf = np.concatenate([self._inbuf, np.array(in0, dtype=np.float32, copy=True)])
            # discover frame tags and try to decode
            self._enqueue_len_tags(n_in)
            self._process_frames_to_outbuf()

        if not self._outbuf:
            self.consume_each(n_in)
            return 0

        ow = self.nitems_written(0)
        space = len(out0)
        produced = 0

        # Emit output tag at the first byte of each decoded frame
        while space > 0 and self._outbuf:
            if self._head_remaining == 0:
                if not self._pending_out_frames:
                    break
                self._head_remaining = self._pending_out_frames[0]
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

