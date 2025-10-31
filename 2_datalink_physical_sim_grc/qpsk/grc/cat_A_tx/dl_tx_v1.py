#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Not titled yet
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, pdu
from gnuradio import network
import dl_tx_v1_epy_block_0 as epy_block_0  # embedded python block
import dl_tx_v1_epy_block_1 as epy_block_1  # embedded python block
import dl_tx_v1_epy_block_2 as epy_block_2  # embedded python block
import dl_tx_v1_epy_block_3 as epy_block_3  # embedded python block
import dl_tx_v1_epy_block_4 as epy_block_4  # embedded python block
import dl_tx_v1_epy_block_5 as epy_block_5  # embedded python block
import dl_tx_v1_epy_block_5_0 as epy_block_5_0  # embedded python block
import dl_tx_v1_epy_block_5_1 as epy_block_5_1  # embedded python block
import dl_tx_v1_epy_block_5_3 as epy_block_5_3  # embedded python block
import sip



class dl_tx_v1(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Not titled yet", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Not titled yet")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "dl_tx_v1")

        try:
            if StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
                self.restoreGeometry(self.settings.value("geometry").toByteArray())
            else:
                self.restoreGeometry(self.settings.value("geometry"))
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.I_RS = I_RS = 5
        self.ASM_MARKER = ASM_MARKER = (0x1A, 0xCF, 0xFC, 0x1D)
        self.RS_BYTES = RS_BYTES = 255 * I_RS
        self.ASM_BYTES = ASM_BYTES = len(ASM_MARKER)
        self.r = r = 1/2
        self.beta = beta = 0.3
        self.TM_PRI_HDR_LEN = TM_PRI_HDR_LEN = 6
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES = RS_BYTES + ASM_BYTES
        self.BYTES_PER_TM_FRAME = BYTES_PER_TM_FRAME = 223 * I_RS
        self.sps = sps = 8
        self.span = span = 11
        self.k = k = 2
        self.alpha = alpha = beta
        self.TM_SEC_HDR_LEN = TM_SEC_HDR_LEN = 12
        self.TM_BODY_LEN = TM_BODY_LEN = BYTES_PER_TM_FRAME - TM_PRI_HDR_LEN
        self.Rs = Rs = 250000
        self.POST_CONV_BITS = POST_CONV_BITS = CADU_RS_ASM_BYTES *8*(1/r)
        self.BYTES_PER_FRAME = BYTES_PER_FRAME = 1115
        self.samp_rate = samp_rate = Rs*sps
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(1.0,    Rs*sps,     Rs,    alpha,   span*sps)
        self.rf_bw = rf_bw = Rs*(1+beta)
        self.rcc_taps = rcc_taps = 0
        self.lo_offset = lo_offset = 1000000
        self.gain = gain = 0
        self.delay_Q = delay_Q = sps/2
        self.Rs_0 = Rs_0 = 250000
        self.RAND_SEED_ALL_ONES = RAND_SEED_ALL_ONES = 0x7FFF
        self.POST_CONV_BYTES = POST_CONV_BYTES = POST_CONV_BITS/8
        self.PACKET_ZONE_LEN = PACKET_ZONE_LEN = TM_BODY_LEN - TM_SEC_HDR_LEN
        self.K = K = 7
        self.Fc = Fc = 2200000000
        self.FILE_PATH = FILE_PATH = "/home/dogg/Downloads/tm_stagin_grc/qpsk/data/SPPencaps_CFDP_metadata_tx.bin"
        self.DATA_RATE_BPS = DATA_RATE_BPS = (Rs*k*(1/r))
        self.BITS_PER_FRAME = BITS_PER_FRAME = BYTES_PER_FRAME*8

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_number_sink_0_1_1 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_1_1.set_update_time(0.10)
        self.qtgui_number_sink_0_1_1.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_1_1.set_min(i, -1)
            self.qtgui_number_sink_0_1_1.set_max(i, 1)
            self.qtgui_number_sink_0_1_1.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_1_1.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_1_1.set_label(i, labels[i])
            self.qtgui_number_sink_0_1_1.set_unit(i, units[i])
            self.qtgui_number_sink_0_1_1.set_factor(i, factor[i])

        self.qtgui_number_sink_0_1_1.enable_autoscale(False)
        self._qtgui_number_sink_0_1_1_win = sip.wrapinstance(self.qtgui_number_sink_0_1_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_1_1_win)
        self.qtgui_number_sink_0_1_1.set_block_alias("ns_conv")
        self.qtgui_number_sink_0_1_0 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_1_0.set_update_time(0.10)
        self.qtgui_number_sink_0_1_0.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_1_0.set_min(i, -1)
            self.qtgui_number_sink_0_1_0.set_max(i, 1)
            self.qtgui_number_sink_0_1_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_1_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_1_0.set_label(i, labels[i])
            self.qtgui_number_sink_0_1_0.set_unit(i, units[i])
            self.qtgui_number_sink_0_1_0.set_factor(i, factor[i])

        self.qtgui_number_sink_0_1_0.enable_autoscale(False)
        self._qtgui_number_sink_0_1_0_win = sip.wrapinstance(self.qtgui_number_sink_0_1_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_1_0_win)
        self.qtgui_number_sink_0_1_0.set_block_alias("ns_asm")
        self.qtgui_number_sink_0_1 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_1.set_update_time(0.10)
        self.qtgui_number_sink_0_1.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_1.set_min(i, -1)
            self.qtgui_number_sink_0_1.set_max(i, 1)
            self.qtgui_number_sink_0_1.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_1.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_1.set_label(i, labels[i])
            self.qtgui_number_sink_0_1.set_unit(i, units[i])
            self.qtgui_number_sink_0_1.set_factor(i, factor[i])

        self.qtgui_number_sink_0_1.enable_autoscale(False)
        self._qtgui_number_sink_0_1_win = sip.wrapinstance(self.qtgui_number_sink_0_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_1_win)
        self.qtgui_number_sink_0_1.set_block_alias("ns_rs")
        self.qtgui_number_sink_0_0 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_0.set_update_time(0.10)
        self.qtgui_number_sink_0_0.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_0.set_min(i, 0)
            self.qtgui_number_sink_0_0.set_max(i, 2000)
            self.qtgui_number_sink_0_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_0.set_label(i, labels[i])
            self.qtgui_number_sink_0_0.set_unit(i, units[i])
            self.qtgui_number_sink_0_0.set_factor(i, factor[i])

        self.qtgui_number_sink_0_0.enable_autoscale(True)
        self._qtgui_number_sink_0_0_win = sip.wrapinstance(self.qtgui_number_sink_0_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_0_win)
        self.qtgui_number_sink_0_0.set_block_alias("ns_rand")
        self.qtgui_number_sink_0 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0.set_update_time(0.10)
        self.qtgui_number_sink_0.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0.set_min(i, 0)
            self.qtgui_number_sink_0.set_max(i, 2000)
            self.qtgui_number_sink_0.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0.set_label(i, labels[i])
            self.qtgui_number_sink_0.set_unit(i, units[i])
            self.qtgui_number_sink_0.set_factor(i, factor[i])

        self.qtgui_number_sink_0.enable_autoscale(True)
        self._qtgui_number_sink_0_win = sip.wrapinstance(self.qtgui_number_sink_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_win)
        self.qtgui_number_sink_0.set_block_alias("ns_tm")
        self.pdu_tagged_stream_to_pdu_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.network_socket_pdu_1 = network.socket_pdu('UDP_CLIENT', '127.0.0.1', '52002', 4096, False)
        self.network_socket_pdu_0 = network.socket_pdu('UDP_SERVER', '0.0.0.0', '52001', 4096, False)
        self.epy_block_5_3 = epy_block_5_3.blk(len_tag_key="packet_len")
        self.epy_block_5_3.set_block_alias("len_conv")
        self.epy_block_5_1 = epy_block_5_1.blk(len_tag_key="packet_len")
        self.epy_block_5_1.set_block_alias("len_rs")
        self.epy_block_5_0 = epy_block_5_0.blk(len_tag_key="packet_len")
        self.epy_block_5_0.set_block_alias("len_rand")
        self.epy_block_5 = epy_block_5.blk(len_tag_key="packet_len")
        self.epy_block_5.set_block_alias("len_tm")
        self.epy_block_4 = epy_block_4.blk(len_tag_key="packet_len", I=I_RS, tm_len=BYTES_PER_TM_FRAME)
        self.epy_block_4.set_block_alias("rs_I")
        self.epy_block_3 = epy_block_3.blk(len_tag_key="packet_len", K=K, gen0=0o171, gen1=0o133, msb_first=True, reset_each_frame=True, g2_inverted=False, c1c2_order=True, strict_frame_len_in=1279)
        self.epy_block_3.set_block_alias("conv_k7r12")
        self.epy_block_2 = epy_block_2.blk(len_tag_key="packet_len", rs_len=1275, asm_hex="1ACFFC1D", enable_sanity=True)
        self.epy_block_2.set_block_alias("asm_ins")
        self.epy_block_1 = epy_block_1.blk(len_tag_key="packet_len", seed=RAND_SEED_ALL_ONES, restart_per_frame=True, enabled=True, mode="frame", sec_hdr_len=TM_SEC_HDR_LEN, pri_hdr_len=TM_PRI_HDR_LEN, max_tag_per_window=1024)
        self.epy_block_1.set_block_alias("tm_rand")
        self.epy_block_0 = epy_block_0.blk(len_tag_key="packet_len", tm_hdr_len=TM_PRI_HDR_LEN, tm_body_len=TM_BODY_LEN, scid=0x42, vcid=0, sec_hdr_flag=1, sec_hdr_len=TM_SEC_HDR_LEN, ocf_present=0, sync_flag=0, pkt_order_flag=0, sl_id=1, fill_byte=0x00)
        self.epy_block_0.set_block_alias("tm_framer")
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_char*1, samp_rate, True, 0 if "auto" == "auto" else max( int(float(0.1) * samp_rate) if "auto" == "time" else int(0.1), 1) )
        self.blocks_tagged_stream_align_1 = blocks.tagged_stream_align(gr.sizeof_char*1, 'packet_len')
        self.blocks_file_sink_0_1 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/art/asm_out.bin', False)
        self.blocks_file_sink_0_1.set_unbuffered(False)
        self.blocks_file_sink_0_1.set_block_alias("asm_out")
        self.blocks_file_sink_0_0_0_2 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/art/conv_out.bin', False)
        self.blocks_file_sink_0_0_0_2.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_2.set_block_alias("conv_out")
        self.blocks_file_sink_0_0_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/art/rand_out.bin', False)
        self.blocks_file_sink_0_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_0.set_block_alias("rand_out")
        self.blocks_file_sink_0_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/art/rs_out.bin', False)
        self.blocks_file_sink_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0.set_block_alias("rs_out")
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/art/tm_out.bin', False)
        self.blocks_file_sink_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0.set_block_alias("tm_out")


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.network_socket_pdu_0, 'pdus'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0, 'pdus'), (self.network_socket_pdu_1, 'pdus'))
        self.connect((self.blocks_tagged_stream_align_1, 0), (self.pdu_tagged_stream_to_pdu_0, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.epy_block_0, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.epy_block_0, 0), (self.epy_block_1, 0))
        self.connect((self.epy_block_0, 0), (self.epy_block_5, 0))
        self.connect((self.epy_block_1, 0), (self.blocks_file_sink_0_0_0_0, 0))
        self.connect((self.epy_block_1, 0), (self.epy_block_4, 0))
        self.connect((self.epy_block_1, 0), (self.epy_block_5_0, 0))
        self.connect((self.epy_block_2, 0), (self.blocks_file_sink_0_1, 0))
        self.connect((self.epy_block_2, 0), (self.epy_block_3, 0))
        self.connect((self.epy_block_2, 1), (self.qtgui_number_sink_0_1_0, 0))
        self.connect((self.epy_block_3, 0), (self.blocks_file_sink_0_0_0_2, 0))
        self.connect((self.epy_block_3, 0), (self.blocks_tagged_stream_align_1, 0))
        self.connect((self.epy_block_3, 0), (self.epy_block_5_3, 0))
        self.connect((self.epy_block_4, 0), (self.blocks_file_sink_0_0_0, 0))
        self.connect((self.epy_block_4, 0), (self.epy_block_2, 0))
        self.connect((self.epy_block_4, 0), (self.epy_block_5_1, 0))
        self.connect((self.epy_block_5, 0), (self.qtgui_number_sink_0, 0))
        self.connect((self.epy_block_5_0, 0), (self.qtgui_number_sink_0_0, 0))
        self.connect((self.epy_block_5_1, 0), (self.qtgui_number_sink_0_1, 0))
        self.connect((self.epy_block_5_3, 0), (self.qtgui_number_sink_0_1_1, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.blocks_throttle2_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "dl_tx_v1")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_I_RS(self):
        return self.I_RS

    def set_I_RS(self, I_RS):
        self.I_RS = I_RS
        self.set_BYTES_PER_TM_FRAME(223 * self.I_RS)
        self.set_RS_BYTES(255 * self.I_RS)
        self.epy_block_4.I = self.I_RS

    def get_ASM_MARKER(self):
        return self.ASM_MARKER

    def set_ASM_MARKER(self, ASM_MARKER):
        self.ASM_MARKER = ASM_MARKER
        self.set_ASM_BYTES(len(self.ASM_MARKER))

    def get_RS_BYTES(self):
        return self.RS_BYTES

    def set_RS_BYTES(self, RS_BYTES):
        self.RS_BYTES = RS_BYTES
        self.set_CADU_RS_ASM_BYTES(self.RS_BYTES + self.ASM_BYTES)

    def get_ASM_BYTES(self):
        return self.ASM_BYTES

    def set_ASM_BYTES(self, ASM_BYTES):
        self.ASM_BYTES = ASM_BYTES
        self.set_CADU_RS_ASM_BYTES(self.RS_BYTES + self.ASM_BYTES)

    def get_r(self):
        return self.r

    def set_r(self, r):
        self.r = r
        self.set_DATA_RATE_BPS((self.Rs*self.k*(1/self.r)))
        self.set_POST_CONV_BITS(self.CADU_RS_ASM_BYTES *8*(1/self.r))

    def get_beta(self):
        return self.beta

    def set_beta(self, beta):
        self.beta = beta
        self.set_alpha(self.beta)
        self.set_rf_bw(self.Rs*(1+self.beta))

    def get_TM_PRI_HDR_LEN(self):
        return self.TM_PRI_HDR_LEN

    def set_TM_PRI_HDR_LEN(self, TM_PRI_HDR_LEN):
        self.TM_PRI_HDR_LEN = TM_PRI_HDR_LEN
        self.set_TM_BODY_LEN(self.BYTES_PER_TM_FRAME - self.TM_PRI_HDR_LEN)
        self.epy_block_1.pri_hdr_len = self.TM_PRI_HDR_LEN

    def get_CADU_RS_ASM_BYTES(self):
        return self.CADU_RS_ASM_BYTES

    def set_CADU_RS_ASM_BYTES(self, CADU_RS_ASM_BYTES):
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES
        self.set_POST_CONV_BITS(self.CADU_RS_ASM_BYTES *8*(1/self.r))

    def get_BYTES_PER_TM_FRAME(self):
        return self.BYTES_PER_TM_FRAME

    def set_BYTES_PER_TM_FRAME(self, BYTES_PER_TM_FRAME):
        self.BYTES_PER_TM_FRAME = BYTES_PER_TM_FRAME
        self.set_TM_BODY_LEN(self.BYTES_PER_TM_FRAME - self.TM_PRI_HDR_LEN)
        self.epy_block_4.tm_len = self.BYTES_PER_TM_FRAME

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_delay_Q(self.sps/2)
        self.set_rrc_taps(firdes.root_raised_cosine(1.0,    self.Rs*self.sps,     self.Rs,    self.alpha,   self.span*self.sps))
        self.set_samp_rate(self.Rs*self.sps)

    def get_span(self):
        return self.span

    def set_span(self, span):
        self.span = span
        self.set_rrc_taps(firdes.root_raised_cosine(1.0,    self.Rs*self.sps,     self.Rs,    self.alpha,   self.span*self.sps))

    def get_k(self):
        return self.k

    def set_k(self, k):
        self.k = k
        self.set_DATA_RATE_BPS((self.Rs*self.k*(1/self.r)))

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.set_rrc_taps(firdes.root_raised_cosine(1.0,    self.Rs*self.sps,     self.Rs,    self.alpha,   self.span*self.sps))

    def get_TM_SEC_HDR_LEN(self):
        return self.TM_SEC_HDR_LEN

    def set_TM_SEC_HDR_LEN(self, TM_SEC_HDR_LEN):
        self.TM_SEC_HDR_LEN = TM_SEC_HDR_LEN
        self.set_PACKET_ZONE_LEN(self.TM_BODY_LEN - self.TM_SEC_HDR_LEN)
        self.epy_block_1.sec_hdr_len = self.TM_SEC_HDR_LEN

    def get_TM_BODY_LEN(self):
        return self.TM_BODY_LEN

    def set_TM_BODY_LEN(self, TM_BODY_LEN):
        self.TM_BODY_LEN = TM_BODY_LEN
        self.set_PACKET_ZONE_LEN(self.TM_BODY_LEN - self.TM_SEC_HDR_LEN)

    def get_Rs(self):
        return self.Rs

    def set_Rs(self, Rs):
        self.Rs = Rs
        self.set_DATA_RATE_BPS((self.Rs*self.k*(1/self.r)))
        self.set_rf_bw(self.Rs*(1+self.beta))
        self.set_rrc_taps(firdes.root_raised_cosine(1.0,    self.Rs*self.sps,     self.Rs,    self.alpha,   self.span*self.sps))
        self.set_samp_rate(self.Rs*self.sps)

    def get_POST_CONV_BITS(self):
        return self.POST_CONV_BITS

    def set_POST_CONV_BITS(self, POST_CONV_BITS):
        self.POST_CONV_BITS = POST_CONV_BITS
        self.set_POST_CONV_BYTES(self.POST_CONV_BITS/8)

    def get_BYTES_PER_FRAME(self):
        return self.BYTES_PER_FRAME

    def set_BYTES_PER_FRAME(self, BYTES_PER_FRAME):
        self.BYTES_PER_FRAME = BYTES_PER_FRAME
        self.set_BITS_PER_FRAME(self.BYTES_PER_FRAME*8)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.blocks_throttle2_0.set_sample_rate(self.samp_rate)

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps

    def get_rf_bw(self):
        return self.rf_bw

    def set_rf_bw(self, rf_bw):
        self.rf_bw = rf_bw

    def get_rcc_taps(self):
        return self.rcc_taps

    def set_rcc_taps(self, rcc_taps):
        self.rcc_taps = rcc_taps

    def get_lo_offset(self):
        return self.lo_offset

    def set_lo_offset(self, lo_offset):
        self.lo_offset = lo_offset

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain

    def get_delay_Q(self):
        return self.delay_Q

    def set_delay_Q(self, delay_Q):
        self.delay_Q = delay_Q

    def get_Rs_0(self):
        return self.Rs_0

    def set_Rs_0(self, Rs_0):
        self.Rs_0 = Rs_0

    def get_RAND_SEED_ALL_ONES(self):
        return self.RAND_SEED_ALL_ONES

    def set_RAND_SEED_ALL_ONES(self, RAND_SEED_ALL_ONES):
        self.RAND_SEED_ALL_ONES = RAND_SEED_ALL_ONES
        self.epy_block_1.seed = self.RAND_SEED_ALL_ONES

    def get_POST_CONV_BYTES(self):
        return self.POST_CONV_BYTES

    def set_POST_CONV_BYTES(self, POST_CONV_BYTES):
        self.POST_CONV_BYTES = POST_CONV_BYTES

    def get_PACKET_ZONE_LEN(self):
        return self.PACKET_ZONE_LEN

    def set_PACKET_ZONE_LEN(self, PACKET_ZONE_LEN):
        self.PACKET_ZONE_LEN = PACKET_ZONE_LEN

    def get_K(self):
        return self.K

    def set_K(self, K):
        self.K = K
        self.epy_block_3.K = self.K

    def get_Fc(self):
        return self.Fc

    def set_Fc(self, Fc):
        self.Fc = Fc

    def get_FILE_PATH(self):
        return self.FILE_PATH

    def set_FILE_PATH(self, FILE_PATH):
        self.FILE_PATH = FILE_PATH

    def get_DATA_RATE_BPS(self):
        return self.DATA_RATE_BPS

    def set_DATA_RATE_BPS(self, DATA_RATE_BPS):
        self.DATA_RATE_BPS = DATA_RATE_BPS

    def get_BITS_PER_FRAME(self):
        return self.BITS_PER_FRAME

    def set_BITS_PER_FRAME(self, BITS_PER_FRAME):
        self.BITS_PER_FRAME = BITS_PER_FRAME




def main(top_block_cls=dl_tx_v1, options=None):

    if StrictVersion("4.5.0") <= StrictVersion(Qt.qVersion()) < StrictVersion("5.0.0"):
        style = gr.prefs().get_string('qtgui', 'style', 'raster')
        Qt.QApplication.setGraphicsSystem(style)
    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
