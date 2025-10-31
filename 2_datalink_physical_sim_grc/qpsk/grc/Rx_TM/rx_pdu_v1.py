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
import rx_pdu_v1_epy_block_0 as epy_block_0  # embedded python block
import rx_pdu_v1_epy_block_1 as epy_block_1  # embedded python block
import rx_pdu_v1_epy_block_2 as epy_block_2  # embedded python block
import rx_pdu_v1_epy_block_3 as epy_block_3  # embedded python block
import rx_pdu_v1_epy_block_4 as epy_block_4  # embedded python block
import rx_pdu_v1_epy_block_5_1 as epy_block_5_1  # embedded python block
import rx_pdu_v1_epy_block_5_1_0 as epy_block_5_1_0  # embedded python block
import rx_pdu_v1_epy_block_5_1_1 as epy_block_5_1_1  # embedded python block
import rx_pdu_v1_epy_block_5_1_2 as epy_block_5_1_2  # embedded python block
import rx_pdu_v1_epy_block_5_1_3 as epy_block_5_1_3  # embedded python block
import sip



class rx_pdu_v1(gr.top_block, Qt.QWidget):

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

        self.settings = Qt.QSettings("GNU Radio", "rx_pdu_v1")

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
        self.sps = sps = 8
        self.samp_rate = samp_rate = 2e6
        self.I_RS = I_RS = 5
        self.ASM_MARKER = ASM_MARKER = (0x1A, 0xCF, 0xFC, 0x1D)
        self.span_symbols = span_symbols = 8
        self.filter_size = filter_size = 32
        self.alpha = alpha = 0.35
        self.TM_HDR_LEN = TM_HDR_LEN = 6
        self.RS_BYTES = RS_BYTES = 255 * I_RS
        self.RSYM = RSYM = samp_rate/sps
        self.BYTES_PER_TM_FRAME = BYTES_PER_TM_FRAME = 223 * I_RS
        self.ASM_BYTES = ASM_BYTES = len(ASM_MARKER)
        self.trans_width = trans_width = 0.005 * samp_rate
        self.soft_flip = soft_flip = 1
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(1.0, samp_rate, RSYM, alpha, span_symbols*sps*filter_size)
        self.loop_bw = loop_bw = 0.005
        self.cuttoff_freq = cuttoff_freq = 0.6 * (1 + alpha) * RSYM
        self.costas_order = costas_order = 4
        self.costas_bw = costas_bw = 2e-3
        self.TM_BODY_LEN = TM_BODY_LEN = BYTES_PER_TM_FRAME - TM_HDR_LEN
        self.RS_info_bytes = RS_info_bytes = 223
        self.RAND_SEED_ALL_ONES = RAND_SEED_ALL_ONES = 0x7FFF
        self.K = K = 7
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES = RS_BYTES + ASM_BYTES
        self.BYTES_PER_FRAME = BYTES_PER_FRAME = 1115

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_number_sink_80 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_80.set_update_time(0.10)
        self.qtgui_number_sink_80.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_80.set_min(i, 0)
            self.qtgui_number_sink_80.set_max(i, 2000)
            self.qtgui_number_sink_80.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_80.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_80.set_label(i, labels[i])
            self.qtgui_number_sink_80.set_unit(i, units[i])
            self.qtgui_number_sink_80.set_factor(i, factor[i])

        self.qtgui_number_sink_80.enable_autoscale(True)
        self._qtgui_number_sink_80_win = sip.wrapinstance(self.qtgui_number_sink_80.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_80_win)
        self.qtgui_number_sink_80.set_block_alias("ns_tm_rx")
        self.qtgui_number_sink_0_1_81 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_1_81.set_update_time(0.10)
        self.qtgui_number_sink_0_1_81.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_1_81.set_min(i, -1)
            self.qtgui_number_sink_0_1_81.set_max(i, 1)
            self.qtgui_number_sink_0_1_81.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_1_81.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_1_81.set_label(i, labels[i])
            self.qtgui_number_sink_0_1_81.set_unit(i, units[i])
            self.qtgui_number_sink_0_1_81.set_factor(i, factor[i])

        self.qtgui_number_sink_0_1_81.enable_autoscale(False)
        self._qtgui_number_sink_0_1_81_win = sip.wrapinstance(self.qtgui_number_sink_0_1_81.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_1_81_win)
        self.qtgui_number_sink_0_1_81.set_block_alias("ns_rs_rx")
        self.qtgui_number_sink_0_1_1_84 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_1_1_84.set_update_time(0.10)
        self.qtgui_number_sink_0_1_1_84.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_1_1_84.set_min(i, -1)
            self.qtgui_number_sink_0_1_1_84.set_max(i, 1)
            self.qtgui_number_sink_0_1_1_84.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_1_1_84.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_1_1_84.set_label(i, labels[i])
            self.qtgui_number_sink_0_1_1_84.set_unit(i, units[i])
            self.qtgui_number_sink_0_1_1_84.set_factor(i, factor[i])

        self.qtgui_number_sink_0_1_1_84.enable_autoscale(False)
        self._qtgui_number_sink_0_1_1_84_win = sip.wrapinstance(self.qtgui_number_sink_0_1_1_84.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_1_1_84_win)
        self.qtgui_number_sink_0_1_1_84.set_block_alias("ns_conv_rx")
        self.qtgui_number_sink_0_0_83 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_0_83.set_update_time(0.10)
        self.qtgui_number_sink_0_0_83.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_0_83.set_min(i, 0)
            self.qtgui_number_sink_0_0_83.set_max(i, 2000)
            self.qtgui_number_sink_0_0_83.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_0_83.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_0_83.set_label(i, labels[i])
            self.qtgui_number_sink_0_0_83.set_unit(i, units[i])
            self.qtgui_number_sink_0_0_83.set_factor(i, factor[i])

        self.qtgui_number_sink_0_0_83.enable_autoscale(True)
        self._qtgui_number_sink_0_0_83_win = sip.wrapinstance(self.qtgui_number_sink_0_0_83.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_0_83_win)
        self.qtgui_number_sink_0_0_83.set_block_alias("ns_rand_rx")
        self.qtgui_number_sink_0_0_0_82 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_0_0_82.set_update_time(0.10)
        self.qtgui_number_sink_0_0_0_82.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_0_0_82.set_min(i, 0)
            self.qtgui_number_sink_0_0_0_82.set_max(i, 2000)
            self.qtgui_number_sink_0_0_0_82.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_0_0_82.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_0_0_82.set_label(i, labels[i])
            self.qtgui_number_sink_0_0_0_82.set_unit(i, units[i])
            self.qtgui_number_sink_0_0_0_82.set_factor(i, factor[i])

        self.qtgui_number_sink_0_0_0_82.enable_autoscale(True)
        self._qtgui_number_sink_0_0_0_82_win = sip.wrapinstance(self.qtgui_number_sink_0_0_0_82.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_0_0_82_win)
        self.qtgui_number_sink_0_0_0_82.set_block_alias("ns_randy_rx")
        self.pdu_tagged_stream_to_pdu_0 = pdu.tagged_stream_to_pdu(gr.types.byte_t, 'packet_len')
        self.pdu_pdu_to_tagged_stream_0 = pdu.pdu_to_tagged_stream(gr.types.byte_t, 'packet_len')
        self.network_socket_pdu_1 = network.socket_pdu('UDP_CLIENT', '127.0.0.1', '52003', 4096, False)
        self.network_socket_pdu_0 = network.socket_pdu('UDP_SERVER', '0.0.0.0', '52002', 4096, False)
        self.epy_block_5_1_3 = epy_block_5_1_3.blk(len_tag_key="packet_len")
        self.epy_block_5_1_3.set_block_alias("len_rs_rx")
        self.epy_block_5_1_2 = epy_block_5_1_2.blk(len_tag_key="packet_len")
        self.epy_block_5_1_2.set_block_alias("len_conv_rx")
        self.epy_block_5_1_1 = epy_block_5_1_1.blk(len_tag_key="packet_len")
        self.epy_block_5_1_1.set_block_alias("len_rand_rx")
        self.epy_block_5_1_0 = epy_block_5_1_0.blk(len_tag_key="packet_len")
        self.epy_block_5_1_0.set_block_alias("len_asm_rx")
        self.epy_block_5_1 = epy_block_5_1.blk(len_tag_key="packet_len")
        self.epy_block_5_1.set_block_alias("len_reed_sol_rx")
        self.epy_block_4 = epy_block_4.blk(tm_hdr_len=TM_HDR_LEN, tm_body_len=TM_BODY_LEN, len_tag_key="packet_len", mode="trim_zeros", len_field_offset=6, len_field_big_endian=True, forward_other_tags=True)
        self.epy_block_3 = epy_block_3.blk(len_tag_key="packet_len", asm_word=ASM_MARKER, cadu_len_bytes=1279, strip_len_bytes=ASM_BYTES, msb_first=True, max_hamming=4, lock_confirm=2, loss_threshold=3, verify_guard_bits=24, trust_tags=True)
        self.epy_block_2 = epy_block_2.blk(len_tag_key="packet_len", seed=RAND_SEED_ALL_ONES, taps=(8,7), skip_bytes_at_frame_start=0, enabled=True)
        self.epy_block_1 = epy_block_1.blk(len_tag_key="packet_len", I=I_RS, expect_len=1275, forward_other_tags=True)
        self.epy_block_0 = epy_block_0.blk(len_tag_key="packet_len", K=K, gen0=0o171, gen1=0o133, msb_first=True, reset_each_frame=True, g2_inverted=False, c1c2_order=True, coded_len_in=2558, decoded_len_out=1279)
        self.blocks_tagged_stream_align_0 = blocks.tagged_stream_align(gr.sizeof_char*1, 'packet_len')
        self.blocks_tag_debug_1 = blocks.tag_debug(gr.sizeof_float*1, '', "")
        self.blocks_tag_debug_1.set_display(True)
        self.blocks_file_sink_0_0_0_2_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/Rx_data/into_rx.bin', False)
        self.blocks_file_sink_0_0_0_2_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_2_0.set_block_alias("into_rx")
        self.blocks_file_sink_0_0_0_2 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/Rx_data/conv_rx_out.bin', False)
        self.blocks_file_sink_0_0_0_2.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_2.set_block_alias("conv_out_rx")
        self.blocks_file_sink_0_0_0_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/Rx_data/rand_rx_out.bin', False)
        self.blocks_file_sink_0_0_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_0_0.set_block_alias("randy_out_rx")
        self.blocks_file_sink_0_0_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/Rx_data/asm_rx_out.bin', False)
        self.blocks_file_sink_0_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_0.set_block_alias("asm_out_rx")
        self.blocks_file_sink_0_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/Rx_data/rs_rx_out.bin', False)
        self.blocks_file_sink_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0.set_block_alias("rs_out_rx")
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Projects/CCSDS_OSI_APP_DL_PHYS_SIM/2_datalink_physical_sim_grc/qpsk/data/Rx_data/tm_rx_out.bin', False)
        self.blocks_file_sink_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0.set_block_alias("tm_out_rx")


        ##################################################
        # Connections
        ##################################################
        self.msg_connect((self.network_socket_pdu_0, 'pdus'), (self.pdu_pdu_to_tagged_stream_0, 'pdus'))
        self.msg_connect((self.pdu_tagged_stream_to_pdu_0, 'pdus'), (self.network_socket_pdu_1, 'pdus'))
        self.connect((self.blocks_tagged_stream_align_0, 0), (self.pdu_tagged_stream_to_pdu_0, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_file_sink_0_0_0_2, 0))
        self.connect((self.epy_block_0, 0), (self.epy_block_2, 0))
        self.connect((self.epy_block_0, 1), (self.epy_block_5_1_2, 0))
        self.connect((self.epy_block_1, 0), (self.blocks_file_sink_0_0_0, 0))
        self.connect((self.epy_block_1, 1), (self.blocks_tag_debug_1, 0))
        self.connect((self.epy_block_1, 0), (self.epy_block_4, 0))
        self.connect((self.epy_block_1, 1), (self.epy_block_5_1, 0))
        self.connect((self.epy_block_2, 0), (self.blocks_file_sink_0_0_0_0_0, 0))
        self.connect((self.epy_block_2, 0), (self.epy_block_3, 0))
        self.connect((self.epy_block_2, 1), (self.epy_block_5_1_1, 0))
        self.connect((self.epy_block_3, 0), (self.blocks_file_sink_0_0_0_0, 0))
        self.connect((self.epy_block_3, 0), (self.epy_block_1, 0))
        self.connect((self.epy_block_3, 1), (self.epy_block_5_1_0, 0))
        self.connect((self.epy_block_4, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.epy_block_4, 0), (self.blocks_tagged_stream_align_0, 0))
        self.connect((self.epy_block_4, 1), (self.epy_block_5_1_3, 0))
        self.connect((self.epy_block_5_1, 0), (self.qtgui_number_sink_0_1_81, 0))
        self.connect((self.epy_block_5_1_0, 0), (self.qtgui_number_sink_0_0_83, 0))
        self.connect((self.epy_block_5_1_1, 0), (self.qtgui_number_sink_0_0_0_82, 0))
        self.connect((self.epy_block_5_1_2, 0), (self.qtgui_number_sink_0_1_1_84, 0))
        self.connect((self.epy_block_5_1_3, 0), (self.qtgui_number_sink_80, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.blocks_file_sink_0_0_0_2_0, 0))
        self.connect((self.pdu_pdu_to_tagged_stream_0, 0), (self.epy_block_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "rx_pdu_v1")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_RSYM(self.samp_rate/self.sps)
        self.set_rrc_taps(firdes.root_raised_cosine(1.0, self.samp_rate, self.RSYM, self.alpha, self.span_symbols*self.sps*self.filter_size))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_RSYM(self.samp_rate/self.sps)
        self.set_rrc_taps(firdes.root_raised_cosine(1.0, self.samp_rate, self.RSYM, self.alpha, self.span_symbols*self.sps*self.filter_size))
        self.set_trans_width(0.005 * self.samp_rate)

    def get_I_RS(self):
        return self.I_RS

    def set_I_RS(self, I_RS):
        self.I_RS = I_RS
        self.set_BYTES_PER_TM_FRAME(223 * self.I_RS)
        self.set_RS_BYTES(255 * self.I_RS)
        self.epy_block_1.I = self.I_RS

    def get_ASM_MARKER(self):
        return self.ASM_MARKER

    def set_ASM_MARKER(self, ASM_MARKER):
        self.ASM_MARKER = ASM_MARKER
        self.set_ASM_BYTES(len(self.ASM_MARKER))

    def get_span_symbols(self):
        return self.span_symbols

    def set_span_symbols(self, span_symbols):
        self.span_symbols = span_symbols
        self.set_rrc_taps(firdes.root_raised_cosine(1.0, self.samp_rate, self.RSYM, self.alpha, self.span_symbols*self.sps*self.filter_size))

    def get_filter_size(self):
        return self.filter_size

    def set_filter_size(self, filter_size):
        self.filter_size = filter_size
        self.set_rrc_taps(firdes.root_raised_cosine(1.0, self.samp_rate, self.RSYM, self.alpha, self.span_symbols*self.sps*self.filter_size))

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.set_cuttoff_freq(0.6 * (1 + self.alpha) * self.RSYM)
        self.set_rrc_taps(firdes.root_raised_cosine(1.0, self.samp_rate, self.RSYM, self.alpha, self.span_symbols*self.sps*self.filter_size))

    def get_TM_HDR_LEN(self):
        return self.TM_HDR_LEN

    def set_TM_HDR_LEN(self, TM_HDR_LEN):
        self.TM_HDR_LEN = TM_HDR_LEN
        self.set_TM_BODY_LEN(self.BYTES_PER_TM_FRAME - self.TM_HDR_LEN)
        self.epy_block_4.tm_hdr_len = self.TM_HDR_LEN

    def get_RS_BYTES(self):
        return self.RS_BYTES

    def set_RS_BYTES(self, RS_BYTES):
        self.RS_BYTES = RS_BYTES
        self.set_CADU_RS_ASM_BYTES(self.RS_BYTES + self.ASM_BYTES)

    def get_RSYM(self):
        return self.RSYM

    def set_RSYM(self, RSYM):
        self.RSYM = RSYM
        self.set_cuttoff_freq(0.6 * (1 + self.alpha) * self.RSYM)
        self.set_rrc_taps(firdes.root_raised_cosine(1.0, self.samp_rate, self.RSYM, self.alpha, self.span_symbols*self.sps*self.filter_size))

    def get_BYTES_PER_TM_FRAME(self):
        return self.BYTES_PER_TM_FRAME

    def set_BYTES_PER_TM_FRAME(self, BYTES_PER_TM_FRAME):
        self.BYTES_PER_TM_FRAME = BYTES_PER_TM_FRAME
        self.set_TM_BODY_LEN(self.BYTES_PER_TM_FRAME - self.TM_HDR_LEN)

    def get_ASM_BYTES(self):
        return self.ASM_BYTES

    def set_ASM_BYTES(self, ASM_BYTES):
        self.ASM_BYTES = ASM_BYTES
        self.set_CADU_RS_ASM_BYTES(self.RS_BYTES + self.ASM_BYTES)

    def get_trans_width(self):
        return self.trans_width

    def set_trans_width(self, trans_width):
        self.trans_width = trans_width

    def get_soft_flip(self):
        return self.soft_flip

    def set_soft_flip(self, soft_flip):
        self.soft_flip = soft_flip

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps

    def get_loop_bw(self):
        return self.loop_bw

    def set_loop_bw(self, loop_bw):
        self.loop_bw = loop_bw

    def get_cuttoff_freq(self):
        return self.cuttoff_freq

    def set_cuttoff_freq(self, cuttoff_freq):
        self.cuttoff_freq = cuttoff_freq

    def get_costas_order(self):
        return self.costas_order

    def set_costas_order(self, costas_order):
        self.costas_order = costas_order

    def get_costas_bw(self):
        return self.costas_bw

    def set_costas_bw(self, costas_bw):
        self.costas_bw = costas_bw

    def get_TM_BODY_LEN(self):
        return self.TM_BODY_LEN

    def set_TM_BODY_LEN(self, TM_BODY_LEN):
        self.TM_BODY_LEN = TM_BODY_LEN
        self.epy_block_4.tm_body_len = self.TM_BODY_LEN

    def get_RS_info_bytes(self):
        return self.RS_info_bytes

    def set_RS_info_bytes(self, RS_info_bytes):
        self.RS_info_bytes = RS_info_bytes

    def get_RAND_SEED_ALL_ONES(self):
        return self.RAND_SEED_ALL_ONES

    def set_RAND_SEED_ALL_ONES(self, RAND_SEED_ALL_ONES):
        self.RAND_SEED_ALL_ONES = RAND_SEED_ALL_ONES
        self.epy_block_2.seed = self.RAND_SEED_ALL_ONES

    def get_K(self):
        return self.K

    def set_K(self, K):
        self.K = K
        self.epy_block_0.K = self.K

    def get_CADU_RS_ASM_BYTES(self):
        return self.CADU_RS_ASM_BYTES

    def set_CADU_RS_ASM_BYTES(self, CADU_RS_ASM_BYTES):
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES

    def get_BYTES_PER_FRAME(self):
        return self.BYTES_PER_FRAME

    def set_BYTES_PER_FRAME(self, BYTES_PER_FRAME):
        self.BYTES_PER_FRAME = BYTES_PER_FRAME




def main(top_block_cls=rx_pdu_v1, options=None):

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
