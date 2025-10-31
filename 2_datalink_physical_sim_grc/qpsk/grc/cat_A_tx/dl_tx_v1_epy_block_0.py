import numpy as np, time
from collections import deque
from gnuradio import gr
import pmt

class blk(gr.sync_block):
    """
    CCSDS TM Framer (Primary+optional 12B Secondary Header, Segmentation, FHP).
      In : bytes (uchar) tagged stream, 'packet_len' = SPP length
      Out: bytes (uchar) fixed-size TM frames: H(6) + B(TM_BODY_LEN)
           Each frame tagged with 'packet_len' = 6 + TM_BODY_LEN
    Notes:
      - TM_BODY_LEN is the ENTIRE data field length (what RS sees).
      - If Sec_Hdr_Flag=1, the first S bytes of the data field are the Secondary Header.
      - FHP counts from the start of the Packet Zone (immediately after the SecHdr).
    """

    def __init__(self,
                 len_tag_key="packet_len",
                 tm_hdr_len=6,
                 tm_body_len=1115,      # full data field length (SecHdr + Packet Zone)
                 scid=0x042, vcid=0,
                 sec_hdr_flag=0,
                 sec_hdr_len=12,        # 12-byte secondary header
                 ocf_present=0,
                 sync_flag=0,
                 pkt_order_flag=0,
                 sl_id=1,               # 01b => Packet TM with FHP
                 fill_byte=0x00):
        gr.sync_block.__init__(self,
            name="tm_framer_seg",
            in_sig=[np.uint8],
            out_sig=[np.uint8])

        # lengths
        self.H  = int(tm_hdr_len)
        assert self.H == 6, "This emits a 6-byte primary header."
        self.B  = int(tm_body_len)          # full TM data field
        self.SF = 1 if sec_hdr_flag else 0
        self.S  = int(sec_hdr_len) if self.SF else 0   # secondary header size
        assert self.B > self.S, "TM_BODY_LEN must exceed Secondary Header length"
        self.PZ = self.B - self.S           # bytes available for Space Packets
        self.F  = self.H + self.B           # total bytes per frame
        self.set_output_multiple(self.F)    # only produce whole frames

        # fields / flags
        self.scid  = int(scid)   & 0x3FF
        self.vcid  = int(vcid)   & 0x7
        self.sec   = self.SF     # primary-header SecHdrFlag reflects reality
        self.ocf   = 1 if ocf_present else 0
        self.sync  = 1 if sync_flag else 0
        self.pord  = 1 if pkt_order_flag else 0
        self.sl_id = int(sl_id) & 0x3

        # counters (roll at 256)
        self.mcfc  = 0
        self.vcfc  = 0

        # plumbing
        self.len_key   = pmt.intern(str(len_tag_key))
        self.fill_byte = int(fill_byte) & 0xFF

        # SPP assembly state
        self._open_chunk = None
        self.spp_q = deque()
        self._carry = None  # continuation across frames: {'data': bytes, 'pos': int}

    # ---------- helpers ----------
    def _build_tm_primary(self, fhp):
        # Word 1: ver(2)=00, SCID(10), VCID(3), OCF(1)
        w1 = (0 << 14) | (self.scid << 4) | (self.vcid << 1) | (self.ocf & 0x1)
        # Word 2: MCFC(8) VCFC(8)
        w2 = ((self.mcfc & 0xFF) << 8) | (self.vcfc & 0xFF)
        # Word 3: SecHdr(1) Sync(1) PktOrd(1) SLID(2) FHP(11)
        fhp &= 0x7FF
        w3 = ((self.sec & 1) << 15) | ((self.sync & 1) << 14) | ((self.pord & 1) << 13) \
             | ((self.sl_id & 0x3) << 11) | fhp
        hdr = bytearray(6)
        hdr[0]=(w1>>8)&0xFF; hdr[1]=w1&0xFF
        hdr[2]=(w2>>8)&0xFF; hdr[3]=w2&0xFF
        hdr[4]=(w3>>8)&0xFF; hdr[5]=w3&0xFF
        return hdr

    def _build_secondary_header(self):
        """
        12-byte Secondary Header:
          [0]  SH_Version(2b)=00 | SH_ID(6b)=0x00
          [1]  Flags (spare for now, set 0)
          [2..8]  CUC time: coarse(4 bytes, seconds since UNIX epoch), fine(3 bytes, 1/2^24 s)
          [9..11] User bytes (0 for now)
        """
        sh = bytearray(self.S if self.S else 0)
        if not self.S: return sh
        # Byte 0: version+id (both zero for now)
        sh[0] = 0x00
        sh[1] = 0x00
        # Time
        now = time.time()
        coarse = int(now) & 0xFFFFFFFF
        fine   = int((now - int(now)) * (1<<24)) & 0xFFFFFF  # 3 bytes
        sh[2] = (coarse >> 24) & 0xFF
        sh[3] = (coarse >> 16) & 0xFF
        sh[4] = (coarse >> 8)  & 0xFF
        sh[5] = coarse & 0xFF
        sh[6] = (fine >> 16) & 0xFF
        sh[7] = (fine >> 8)  & 0xFF
        sh[8] = fine & 0xFF
        # user bytes
        for i in range(9, 12):
            sh[i] = 0x00
        return sh

    def _emit_frame(self, out, out_off, fhp, payload_bytes, sec_hdr_bytes=None):
        # Primary
        ph = self._build_tm_primary(fhp)
        out[out_off:out_off+self.H] = np.frombuffer(ph, dtype=np.uint8)
        # Secondary (if present) goes at the head of the data field
        pos = out_off + self.H
        if self.S:
            sh = sec_hdr_bytes if sec_hdr_bytes is not None else self._build_secondary_header()
            out[pos:pos+self.S] = np.frombuffer(sh, dtype=np.uint8)
            pos += self.S
        # Packet Zone payload (length self.PZ) follows
        out[pos:pos+self.PZ] = np.frombuffer(payload_bytes, dtype=np.uint8)

        # counters
        self.mcfc = (self.mcfc + 1) & 0xFF
        self.vcfc = (self.vcfc + 1) & 0xFF

        # length tag at frame start (whole frame length)
        self.add_item_tag(0, self.nitems_written(0) + out_off, self.len_key, pmt.from_long(self.F))

    # ---------- work ----------
    def work(self, input_items, output_items):
        inn, out = input_items[0], output_items[0]
        n_in, n_out = len(inn), len(out)

        # 1) Ingest SPPs via packet_len tags
        if n_in:
            start = self.nitems_read(0); end = start + n_in
            tags = self.get_tags_in_range(0, start, end, self.len_key)
            tags.sort(key=lambda t: int(t.offset))
            abs_pos = start; consumed = 0; ti = 0

            def copy_span(a, b):
                nonlocal consumed
                if b <= a: return
                chunk = bytes(inn[(a-start):(b-start)])
                if self._open_chunk is not None:
                    self._open_chunk['data'] += chunk
                    self._open_chunk['need'] -= (b - a)
                    if self._open_chunk['need'] <= 0:
                        self.spp_q.append(self._open_chunk['data'])
                        self._open_chunk = None
                consumed += (b - a)

            while abs_pos < end:
                if self._open_chunk is None:
                    if ti >= len(tags):
                        consumed += (end - abs_pos); abs_pos = end; break
                    tag = tags[ti]; tag_off = int(tag.offset)
                    tag_len = int(pmt.to_long(tag.value))
                    if tag_off > abs_pos:
                        copy_span(abs_pos, tag_off); abs_pos = tag_off; continue
                    self._open_chunk = {'start': tag_off, 'need': tag_len, 'data': bytearray()}
                    ti += 1
                # fill current chunk
                need = self._open_chunk['need']
                avail = end - abs_pos
                take = min(avail, need)
                copy_span(abs_pos, abs_pos + take)
                abs_pos += take

            self.consume(0, consumed)

        # 2) Build frames (only in whole-frame multiples)
        produced = 0; out_off = 0
        while (n_out - out_off) >= self.F:
            # Prepare Packet Zone buffer (size self.PZ)
            pz = bytearray([self.fill_byte] * self.PZ)

            fhp = 0x7FF
            idx = 0

            # 2a) Continue previous SPP if any
            if self._carry is not None:
                tail = self._carry
                take = min(self.PZ - idx, len(tail['data']) - tail['pos'])
                pz[idx:idx+take] = tail['data'][tail['pos']:tail['pos']+take]
                tail['pos'] += take; idx += take
                if tail['pos'] >= len(tail['data']):
                    self._carry = None
                    if idx < self.PZ and len(self.spp_q) > 0:
                        fhp = idx  # first new SPP header starts at this offset in the Packet Zone

            # 2b) Pull whole SPPs
            while idx < self.PZ and len(self.spp_q) > 0:
                pkt = self.spp_q[0]
                if fhp == 0x7FF:
                    fhp = 0 if (idx == 0 and self._carry is None) else idx
                if len(pkt) <= (self.PZ - idx):
                    pz[idx:idx+len(pkt)] = pkt
                    idx += len(pkt)
                    self.spp_q.popleft()
                else:
                    take = self.PZ - idx
                    pz[idx:idx+take] = pkt[:take]
                    self._carry = {'data': pkt, 'pos': take}
                    self.spp_q.popleft()
                    idx += take
                    break

            # Emit frame (Secondary Header is injected inside)
            self._emit_frame(out, out_off, fhp, pz)
            out_off += self.F; produced += self.F

        return produced

