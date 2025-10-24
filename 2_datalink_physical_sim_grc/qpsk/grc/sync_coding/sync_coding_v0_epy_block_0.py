# tm_framer_ccsds_epy.py
import numpy as np
import pmt
from gnuradio import gr

class blk(gr.basic_block):
    """
    CCSDS TM Transfer Frame framer (packetized mode, SyncFlag=0).
    In : uchar stream, tagged per Space Packet (len_tag_key = SPP length in BYTES)
    Out: uchar stream, fixed-length TM frames (len_tag_key = frame_len)

    • 6B Primary Header: TFVN/SCID/VCID/OCF + MC/VC counters + Data Field Status
    • Data Field Status (packetized): SyncFlag=0, FHP computed per frame
      - FHP = 0..TFDF_len-1 if a packet header starts in this TFDF
      - FHP = 0x7FF if the frame contains only packet continuation bytes
      - (Optional) 0x7FE if Only-Idle-Data (if emit_idle_when_empty=True and no SPPs)
    • Packs multiple SPPs if they fit; segments across frames when needed
    • Optional FECF (CRC-16-IBM) appended after TFDF when include_fecf=True
    • Maintains Master/Virtual Channel frame counters (mod-256)

    Parameters
      scid: 0..1023 (10b)
      vcid: 0..7    (3b)
      ocf_present: bool (sets OCF flag in header only; no OCF bytes are added)
      frame_len: total TM frame length in bytes (header + TFDF [+ FECF])
      len_tag_key: tag name for lengths (default "packet_len")
      include_fecf: append CRC-16 FECF (True/False)
      idle_fill: byte used for idle padding if emit_idle_when_empty=True
      emit_idle_when_empty: when True and no SPP available, send OID frames (FHP=0x7FE)
    """
    def __init__(self,
                 scid=0, vcid=0, ocf_present=False,
                 frame_len=1115,
                 len_tag_key="packet_len",
                 include_fecf=False,
                 idle_fill=0x55,
                 emit_idle_when_empty=False):
        gr.basic_block.__init__(self,
            name="tm_framer_ccsds",
            in_sig=[np.uint8],
            out_sig=[np.uint8],
        )
        # ---- config ----
        self.scid  = int(scid) & 0x3FF
        self.vcid  = int(vcid) & 0x7
        self.ocf_present = bool(ocf_present)
        self.len_key_str = str(len_tag_key)
        self.len_key = pmt.intern(self.len_key_str)
        self.include_fecf = bool(include_fecf)
        self.emit_idle = bool(emit_idle_when_empty)
        self.idle_fill = int(idle_fill) & 0xFF

        # lengths
        self.header_len = 6
        self.fecf_len   = 2 if self.include_fecf else 0
        self.frame_len  = int(frame_len)
        assert self.frame_len >= self.header_len + self.fecf_len + 1, "frame_len too small"
        self.tfdf_len   = self.frame_len - self.header_len - self.fecf_len

        # counters
        self.mc_cnt = 0
        self.vc_cnt = 0

        # input buffering / queues
        self._inbuf = bytearray()
        self._pending_tags = []  # (rel_offset, spp_len)
        self._spp_queue = []     # dicts: { 'data': bytearray, 'pos': 0, 'len': L }
        self._cur_pkt = None     # currently-being-segmented packet

        # we re-emit only our own frame length tags
        self.set_tag_propagation_policy(gr.TPP_DONT)

    # --------------- CRC-16-IBM (FECF) ----------------
    @staticmethod
    def _crc16_ibm(data, init=0xFFFF):
        crc = init
        for b in data:
            crc ^= (b << 8) & 0xFFFF
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ 0x1021) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF
        return crc & 0xFFFF

    # --------------- Primary Header packer ---------------
    def _pack_primary_header(self, fhp, sync_flag=0, sec_hdr_flag=0,
                             pkt_order_flag=0, seg_len_id=0):
        """
        16 bits: TFVN(2)=0, SCID(10), VCID(3), OCF(1)
        8  bits: MC frame count
        8  bits: VC frame count
        16 bits: Data Field Status: [SecHdr(1) Sync(1) PktOrd(1) SegLen(2) FHP(11)]
        """
        tfvn = 0
        word0 = ((tfvn & 0x3) << 14) | ((self.scid & 0x3FF) << 4) | ((self.vcid & 0x7) << 1) | (1 if self.ocf_present else 0)
        b0 = (word0 >> 8) & 0xFF
        b1 = (word0 >> 0) & 0xFF

        dfs = ((sec_hdr_flag & 1) << 15) \
            | ((sync_flag   & 1) << 14) \
            | ((pkt_order_flag & 1) << 13) \
            | ((seg_len_id & 0x3) << 11) \
            | (fhp & 0x7FF)
        b4 = (dfs >> 8) & 0xFF
        b5 = (dfs >> 0) & 0xFF

        hdr = bytearray(6)
        hdr[0] = b0; hdr[1] = b1
        hdr[2] = self.mc_cnt & 0xFF
        hdr[3] = self.vc_cnt & 0xFF
        hdr[4] = b4; hdr[5] = b5
        return bytes(hdr)

    def _advance_counters(self):
        self.mc_cnt = (self.mc_cnt + 1) & 0xFF
        self.vc_cnt = (self.vc_cnt + 1) & 0xFF

    # --------------- Input tag handling ---------------
    def _collect_spp_tags(self, n_input):
        in0 = 0
        nread = self.nitems_read(in0)
        tags = self.get_tags_in_range(in0, nread, nread + n_input, self.len_key)
        if not tags:
            return
        tags = sorted(tags, key=lambda t: int(t.offset))
        for t in tags:
            if not pmt.is_integer(t.value): continue
            L = int(pmt.to_long(t.value))
            if L <= 0: continue
            rel = int(t.offset - nread)
            self._pending_tags.append((rel, L))

    # --------------- Work ---------------
    def general_work(self, input_items, output_items):
        inp = input_items[0]
        out = output_items[0]
        n_in, n_out = len(inp), len(out)
        if n_out < self.frame_len:
            return 0

        produced = 0

        # Ingest bytes and discover new SPP starts in this call
        if n_in:
            self._inbuf += bytes(inp)
            self._collect_spp_tags(n_in)

        # Carve complete SPPs out of _inbuf into _spp_queue
        while self._pending_tags:
            rel_off, L = self._pending_tags[0]
            if rel_off < 0:
                # tag before buffer head; drop it (shouldn't happen with sane upstream)
                self._pending_tags.pop(0)
                continue
            if len(self._inbuf) < rel_off + L:
                break  # wait for more bytes
            pkt = bytes(self._inbuf[rel_off:rel_off+L])
            # remove everything up to end-of-packet to keep indices simple
            del self._inbuf[:rel_off+L]
            # adjust remaining tags
            self._pending_tags = [(off - (rel_off+L), l) for (off, l) in self._pending_tags[1:]]
            # queue SPP
            self._spp_queue.append({'data': bytearray(pkt), 'pos': 0, 'len': L})

        # Assemble as many full frames as we have space for
        while n_out - produced >= self.frame_len:
            tfdf = bytearray(self.tfdf_len)
            cursor = 0
            header_starts = []  # offsets of SPP header starts within this TFDF

            # 1) If continuing a split packet, place its continuation first
            if self._cur_pkt is not None:
                pkt = self._cur_pkt
                rem = pkt['len'] - pkt['pos']
                take = min(rem, self.tfdf_len - cursor)
                if take > 0:
                    tfdf[cursor:cursor+take] = pkt['data'][pkt['pos']:pkt['pos']+take]
                    pkt['pos'] += take
                    cursor += take
                if pkt['pos'] >= pkt['len']:
                    self._cur_pkt = None  # finished this packet

            # 2) Place as many *new* SPPs as fit; record each header start
            while cursor < self.tfdf_len and self._spp_queue:
                pkt = self._spp_queue[0]
                header_starts.append(cursor)  # a new packet header starts here
                L = pkt['len']
                room = self.tfdf_len - cursor
                if L <= room:
                    tfdf[cursor:cursor+L] = pkt['data']
                    cursor += L
                    self._spp_queue.pop(0)
                else:
                    # split across frames
                    take = room
                    if take > 0:
                        tfdf[cursor:cursor+take] = pkt['data'][:take]
                        pkt['pos'] = take
                        self._cur_pkt = pkt
                        self._spp_queue.pop(0)
                    cursor = self.tfdf_len
                    break

            # 3) If there is still space and no data, optionally emit Only-Idle-Data
            only_idle = False
            if cursor < self.tfdf_len:
                if self.emit_idle and not header_starts and self._cur_pkt is None and not self._spp_queue:
                    tfdf[cursor:self.tfdf_len] = bytes([self.idle_fill]) * (self.tfdf_len - cursor)
                    only_idle = True
                else:
                    # leave zeros (lab mode); production systems should prefer idle
                    pass

            # 4) Compute FHP
            if only_idle:
                fhp = 0x7FE
            else:
                fhp = header_starts[0] if header_starts else 0x7FF

            # 5) Build frame (header + TFDF [+ FECF])
            hdr = self._pack_primary_header(fhp=fhp, sync_flag=0, sec_hdr_flag=0, pkt_order_flag=0, seg_len_id=0)
            frame_wo_fecf = hdr + bytes(tfdf)
            if self.include_fecf:
                crc = self._crc16_ibm(frame_wo_fecf)
                fecf = bytes([(crc >> 8) & 0xFF, crc & 0xFF])
                frame = frame_wo_fecf + fecf
            else:
                frame = frame_wo_fecf

            # 6) Output and tag
            out[produced:produced+len(frame)] = np.frombuffer(frame, dtype=np.uint8)
            self.add_item_tag(0, self.nitems_written(0) + produced, self.len_key, pmt.from_long(len(frame)))

            # 7) advance counters and produced
            self._advance_counters()
            produced += len(frame)

            # If we didn't actually place any data and also didn't permit idle,
            # break to avoid emitting empty frames.
            if cursor == 0 and not self.emit_idle:
                break

        # Consume all input provided this call (we manage our own buffers)
        self.consume(0, n_in)
        return produced

