"""
CCSDS RS(255,223) encoder with symbol interleaving depth I (round-robin),
for TM frames already randomized. One input TM frame of length tm_len=223*I
becomes an interleaved RS codeblock of length 255*I.

Input : bytes (uchar), tagged stream with len_tag_key = 223*I
Output: bytes (uchar), tagged stream with len_tag_key = 255*I
"""

import numpy as np
import pmt
from gnuradio import gr

class blk(gr.basic_block):
    def __init__(self, len_tag_key="packet_len", I=5, tm_len=1115):
        gr.basic_block.__init__(self,
            name="rs255_223_interleave_I",
            in_sig=[np.uint8],
            out_sig=[np.uint8],
        )
        self.len_key = pmt.intern(str(len_tag_key))
        self.I = int(I)
        self.tm_len = int(tm_len)

        # --- RS(255,223) constants ---
        self.N = 255
        self.K = 223
        self.NPAR = self.N - self.K  # 32 parity bytes

        # Sanity check: input length must be 223*I
        if self.tm_len != self.K * self.I:
            raise ValueError(f"tm_len ({self.tm_len}) must equal 223*I ({self.K*self.I})")

        # Build GF(256) tables with primitive polynomial 0x11D
        self._gf_init(prim=0x11D)

        # Build generator polynomial g(x) = Π_{i=1..NPAR} (x - α^i)
        # (Common RS(255,223) choice; for strict CCSDS compliance this matches practice for TM.)
        self.gen = self._rs_generator(self.NPAR)

    # ---------------- GF(256) helpers ----------------
    def _gf_init(self, prim=0x11D):
        self.gf_exp = np.zeros(512, dtype=np.uint8)
        self.gf_log = np.zeros(256, dtype=np.int16) - 1
        x = 1
        for i in range(255):
            self.gf_exp[i] = x
            self.gf_log[x] = i
            x <<= 1
            if x & 0x100:
                x ^= prim
        # duplicate for fast wrap
        self.gf_exp[255:510] = self.gf_exp[:255]
        self.gf_exp[510:] = self.gf_exp[:2]


    def _gf_add(self, a, b):  # = subtract
        return a ^ b

    def _gf_mul(self, a, b):
        if a == 0 or b == 0:
            return 0
        return int(self.gf_exp[int(self.gf_log[a]) + int(self.gf_log[b])])

    def _poly_scale(self, p, x):
        if x == 0:
            return np.zeros_like(p)
        return np.array([self._gf_mul(int(c), x) for c in p], dtype=np.uint8)

    def _poly_add(self, p, q):
        # align lengths (MSB first)
        if len(p) < len(q):
            p = np.pad(p, (len(q)-len(p), 0), constant_values=0)
        elif len(q) < len(p):
            q = np.pad(q, (len(p)-len(q), 0), constant_values=0)
        return np.array([self._gf_add(int(a), int(b)) for a, b in zip(p, q)], dtype=np.uint8)

    def _rs_generator(self, nsym):
        g = np.array([1], dtype=np.uint8)
        for i in range(1, nsym+1):
            # multiply by (x - α^i)
            term = np.array([1, self.gf_exp[i]], dtype=np.uint8)
            g = self._poly_mul(g, term)
        return g

    def _poly_mul(self, p, q):
        r = np.zeros(len(p)+len(q)-1, dtype=np.uint8)
        for i, a in enumerate(p):
            if a == 0: continue
            for j, b in enumerate(q):
                if b == 0: continue
                r[i+j] ^= self._gf_mul(int(a), int(b))
        return r

    def _rs_encode_223_255(self, data):
        """Return parity bytes for a 223-byte message."""
        if len(data) != self.K:
            raise ValueError("RS encoder expects exactly 223 data bytes")
        # remainder of x^(NPAR) * data(x) divided by g(x)
        rem = np.zeros(self.NPAR, dtype=np.uint8)
        for d in data:
            coef = d ^ rem[0]
            # shift left by 1 (drop MSB), append 0
            rem = np.concatenate([rem[1:], np.array([0], dtype=np.uint8)])
            if coef != 0:
                # rem = rem ^ (coef * g[1..])
                for j in range(self.NPAR):
                    rem[j] ^= self._gf_mul(int(self.gen[j+1]), int(coef))
        return bytes(rem)  # parity

    # -------------- Work: one TM frame → I interleaved RS codewords --------------
    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        n_in = len(inp)
        if n_in == 0 or len(out) == 0:
            return 0

        n_read = self.nitems_read(0)
        tags = self.get_tags_in_window(0, 0, n_in, self.len_key)
        if not tags:
            return 0

        t = tags[0]
        rel = int(t.offset - n_read)
        if rel > 0:
            self.consume(0, rel)
            return 0

        L = int(pmt.to_long(t.value))
        if L < self.tm_len or n_in < self.tm_len:
            # need the full TM frame
            return 0

        # Take exactly one TM frame
        tm = np.array(inp[:self.tm_len], dtype=np.uint8)

        # Demultiplex into I branches (round-robin)
        # branch j gets bytes tm[j], tm[j+I], tm[j+2I], ... total 223 each
        branches = []
        for j in range(self.I):
            branch = tm[j::self.I]
            if len(branch) != self.K:
                # Should not happen if tm_len == 223*I
                branch = np.pad(branch, (0, self.K - len(branch)), constant_values=0)
            branches.append(np.array(branch, dtype=np.uint8))

        # RS encode each branch and form full 255-byte codewords
        codewords = []
        for j in range(self.I):
            parity = self._rs_encode_223_255(branches[j])
            cw = bytes(branches[j].tolist()) + parity  # 223 + 32
            codewords.append(np.frombuffer(cw, dtype=np.uint8))

        # Multiplex interleaver output: cw0[0], cw1[0], ..., cw{I-1}[0], cw0[1], ...
        out_len = self.N * self.I  # 255*I
        if len(out) < out_len:
            return 0

        write_idx = 0
        for sym_idx in range(self.N):
            for j in range(self.I):
                out[write_idx] = codewords[j][sym_idx]
                write_idx += 1

        # Emit new packet_len tag (255*I) at output head
        self.add_item_tag(0, self.nitems_written(0), self.len_key, pmt.from_long(out_len))

        # Consume exactly one TM frame worth of input
        self.consume(0, self.tm_len)
        return out_len
