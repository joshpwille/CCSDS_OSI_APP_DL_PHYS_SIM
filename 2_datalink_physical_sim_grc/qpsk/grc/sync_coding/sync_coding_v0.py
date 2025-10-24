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
import pmt
from gnuradio import gr
from gnuradio.filter import firdes
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import sip
import sync_coding_v0_epy_block_0 as epy_block_0  # embedded python block
import sync_coding_v0_epy_block_1 as epy_block_1  # embedded python block
import sync_coding_v0_epy_block_2 as epy_block_2  # embedded python block
import sync_coding_v0_epy_block_3 as epy_block_3  # embedded python block
import sync_coding_v0_epy_block_4 as epy_block_4  # embedded python block
import sync_coding_v0_epy_block_5 as epy_block_5  # embedded python block
import sync_coding_v0_epy_block_5_0 as epy_block_5_0  # embedded python block
import sync_coding_v0_epy_block_5_1 as epy_block_5_1  # embedded python block
import sync_coding_v0_epy_block_5_2 as epy_block_5_2  # embedded python block
import sync_coding_v0_epy_block_5_3 as epy_block_5_3  # embedded python block
import sync_coding_v0_epy_block_5_4 as epy_block_5_4  # embedded python block
import sync_coding_v0_epy_block_6 as epy_block_6  # embedded python block



class sync_coding_v0(gr.top_block, Qt.QWidget):

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

        self.settings = Qt.QSettings("GNU Radio", "sync_coding_v0")

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
        self.FILE_PATH = FILE_PATH = "/home/dogg/Downloads/tm_stagin_grc/qpsk/data/SPPencaps_CFDP_metadata_tx.bin"
        self.ASM_MARKER = ASM_MARKER = (0x1A, 0xCF, 0xFC, 0x1D)
        self.RS_BYTES = RS_BYTES = 255 * I_RS
        self.FILE_BYTES = FILE_BYTES = __import__('os').path.getsize(FILE_PATH)
        self.ASM_BYTES = ASM_BYTES = len(ASM_MARKER)
        self.r = r = 1/2
        self.SPP_LEN = SPP_LEN = FILE_BYTES
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES = RS_BYTES + ASM_BYTES
        self.k = k = 2
        self.TM_HDR_LEN = TM_HDR_LEN = 6
        self.Rs = Rs = 250000
        self.POST_CONV_BITS = POST_CONV_BITS = CADU_RS_ASM_BYTES *8*(1/r)
        self.N_FRAMES = N_FRAMES = (FILE_BYTES + SPP_LEN - 1) // SPP_LEN
        self.BYTES_PER_TM_FRAME = BYTES_PER_TM_FRAME = 223 * I_RS
        self.TM_BODY_LEN = TM_BODY_LEN = BYTES_PER_TM_FRAME - TM_HDR_LEN
        self.RAND_SEED_ALL_ONES = RAND_SEED_ALL_ONES = 0x7FFF
        self.POST_CONV_BYTES = POST_CONV_BYTES = POST_CONV_BITS/8
        self.K = K = 7
        self.HEAD_SPACING = HEAD_SPACING = BYTES_PER_TM_FRAME * N_FRAMES
        self.DATA_RATE_BPS = DATA_RATE_BPS = (Rs*k*(1/r))

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_number_sink_0_4 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_4.set_update_time(0.10)
        self.qtgui_number_sink_0_4.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_4.set_min(i, -1)
            self.qtgui_number_sink_0_4.set_max(i, 1)
            self.qtgui_number_sink_0_4.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_4.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_4.set_label(i, labels[i])
            self.qtgui_number_sink_0_4.set_unit(i, units[i])
            self.qtgui_number_sink_0_4.set_factor(i, factor[i])

        self.qtgui_number_sink_0_4.enable_autoscale(True)
        self._qtgui_number_sink_0_4_win = sip.wrapinstance(self.qtgui_number_sink_0_4.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_4_win)
        self.qtgui_number_sink_0_3 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_3.set_update_time(0.10)
        self.qtgui_number_sink_0_3.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_3.set_min(i, -1)
            self.qtgui_number_sink_0_3.set_max(i, 1)
            self.qtgui_number_sink_0_3.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_3.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_3.set_label(i, labels[i])
            self.qtgui_number_sink_0_3.set_unit(i, units[i])
            self.qtgui_number_sink_0_3.set_factor(i, factor[i])

        self.qtgui_number_sink_0_3.enable_autoscale(True)
        self._qtgui_number_sink_0_3_win = sip.wrapinstance(self.qtgui_number_sink_0_3.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_3_win)
        self.qtgui_number_sink_0_2 = qtgui.number_sink(
            gr.sizeof_float,
            0,
            qtgui.NUM_GRAPH_HORIZ,
            1,
            None # parent
        )
        self.qtgui_number_sink_0_2.set_update_time(0.10)
        self.qtgui_number_sink_0_2.set_title("")

        labels = ['', '', '', '', '',
            '', '', '', '', '']
        units = ['', '', '', '', '',
            '', '', '', '', '']
        colors = [("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"),
            ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black"), ("black", "black")]
        factor = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]

        for i in range(1):
            self.qtgui_number_sink_0_2.set_min(i, -1)
            self.qtgui_number_sink_0_2.set_max(i, 1)
            self.qtgui_number_sink_0_2.set_color(i, colors[i][0], colors[i][1])
            if len(labels[i]) == 0:
                self.qtgui_number_sink_0_2.set_label(i, "Data {0}".format(i))
            else:
                self.qtgui_number_sink_0_2.set_label(i, labels[i])
            self.qtgui_number_sink_0_2.set_unit(i, units[i])
            self.qtgui_number_sink_0_2.set_factor(i, factor[i])

        self.qtgui_number_sink_0_2.enable_autoscale(True)
        self._qtgui_number_sink_0_2_win = sip.wrapinstance(self.qtgui_number_sink_0_2.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_2_win)
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

        self.qtgui_number_sink_0_1.enable_autoscale(True)
        self._qtgui_number_sink_0_1_win = sip.wrapinstance(self.qtgui_number_sink_0_1.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_number_sink_0_1_win)
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
            self.qtgui_number_sink_0_0.set_min(i, -1)
            self.qtgui_number_sink_0_0.set_max(i, 1)
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
            self.qtgui_number_sink_0.set_min(i, -1)
            self.qtgui_number_sink_0.set_max(i, 1)
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
        self.epy_block_6 = epy_block_6.blk(len_tag_key="packet_len")
        self.epy_block_5_4 = epy_block_5_4.blk(len_tag_key="packet_len")
        self.epy_block_5_4.set_block_alias("len_tagger")
        self.epy_block_5_3 = epy_block_5_3.blk(len_tag_key="packet_len")
        self.epy_block_5_3.set_block_alias("len_conv")
        self.epy_block_5_2 = epy_block_5_2.blk(len_tag_key="packet_len")
        self.epy_block_5_2.set_block_alias("len_asm")
        self.epy_block_5_1 = epy_block_5_1.blk(len_tag_key="packet_len")
        self.epy_block_5_1.set_block_alias("len_rs")
        self.epy_block_5_0 = epy_block_5_0.blk(len_tag_key="packet_len")
        self.epy_block_5_0.set_block_alias("len_rand")
        self.epy_block_5 = epy_block_5.blk(len_tag_key="packet_len")
        self.epy_block_5.set_block_alias("len_tm")
        self.epy_block_4 = epy_block_4.blk(len_tag_key="packet_len", I=I_RS, tm_len=BYTES_PER_TM_FRAME)
        self.epy_block_4.set_block_alias("rs_I")
        self.epy_block_3 = epy_block_3.blk(len_tag_key="packet_len", K=K, gen0=0o171, gen1=0o133, msb_first=True, reset_each_frame=True)
        self.epy_block_3.set_block_alias("conv_k7r12")
        self.epy_block_2 = epy_block_2.blk(len_tag_key="packet_len", asm_word=ASM_MARKER)
        self.epy_block_2.set_block_alias("asm_ins")
        self.epy_block_1 = epy_block_1.blk(len_tag_key="packet_len", seed=RAND_SEED_ALL_ONES, restart_per_frame=True, enabled=True)
        self.epy_block_1.set_block_alias("tm_rand")
        self.epy_block_0 = epy_block_0.blk(scid=, vcid=, ocf_present=, frame_len=, len_tag_key="packet_len", include_fecf=, idle_fill=, emit_idle_when_empty=)
        self.epy_block_0.set_block_alias("tm_framer")
        self.blocks_throttle2_0 = blocks.throttle( gr.sizeof_char*1, DATA_RATE_BPS, True, 0 if "auto" == "auto" else max( int(float(0.1) * DATA_RATE_BPS) if "auto" == "time" else int(0.1), 1) )
        self.blocks_throttle2_0.set_block_alias("throttle_datalink")
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/SPPencaps_CFDP_metadata_tx.bin', True, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_sink_0_1 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/asm_out.bin', False)
        self.blocks_file_sink_0_1.set_unbuffered(False)
        self.blocks_file_sink_0_1.set_block_alias("asm_out")
        self.blocks_file_sink_0_0_1 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/tag_out.bin', False)
        self.blocks_file_sink_0_0_1.set_unbuffered(False)
        self.blocks_file_sink_0_0_1.set_block_alias("tag_out")
        self.blocks_file_sink_0_0_0_2 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/conv_out.bin', False)
        self.blocks_file_sink_0_0_0_2.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_2.set_block_alias("conv_out")
        self.blocks_file_sink_0_0_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/rand_out.bin', False)
        self.blocks_file_sink_0_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0_0.set_block_alias("rand_out")
        self.blocks_file_sink_0_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/rs_out.bin', False)
        self.blocks_file_sink_0_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0_0.set_block_alias("rs_out")
        self.blocks_file_sink_0_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/tm_out.bin', False)
        self.blocks_file_sink_0_0.set_unbuffered(False)
        self.blocks_file_sink_0_0.set_block_alias("tm_out")
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/cadu_v0.bin', False)
        self.blocks_file_sink_0.set_unbuffered(False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.epy_block_6, 0))
        self.connect((self.blocks_throttle2_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_file_sink_0_0, 0))
        self.connect((self.epy_block_0, 0), (self.epy_block_1, 0))
        self.connect((self.epy_block_0, 0), (self.epy_block_5, 0))
        self.connect((self.epy_block_1, 0), (self.blocks_file_sink_0_0_0_0, 0))
        self.connect((self.epy_block_1, 0), (self.epy_block_4, 0))
        self.connect((self.epy_block_1, 0), (self.epy_block_5_0, 0))
        self.connect((self.epy_block_2, 0), (self.blocks_file_sink_0_1, 0))
        self.connect((self.epy_block_2, 0), (self.epy_block_3, 0))
        self.connect((self.epy_block_2, 0), (self.epy_block_5_2, 0))
        self.connect((self.epy_block_3, 0), (self.blocks_file_sink_0_0_0_2, 0))
        self.connect((self.epy_block_3, 0), (self.blocks_throttle2_0, 0))
        self.connect((self.epy_block_3, 0), (self.epy_block_5_3, 0))
        self.connect((self.epy_block_4, 0), (self.blocks_file_sink_0_0_0, 0))
        self.connect((self.epy_block_4, 0), (self.epy_block_2, 0))
        self.connect((self.epy_block_4, 0), (self.epy_block_5_1, 0))
        self.connect((self.epy_block_5, 0), (self.qtgui_number_sink_0_0, 0))
        self.connect((self.epy_block_5_0, 0), (self.qtgui_number_sink_0_1, 0))
        self.connect((self.epy_block_5_1, 0), (self.qtgui_number_sink_0_2, 0))
        self.connect((self.epy_block_5_2, 0), (self.qtgui_number_sink_0_3, 0))
        self.connect((self.epy_block_5_3, 0), (self.qtgui_number_sink_0_4, 0))
        self.connect((self.epy_block_5_4, 0), (self.qtgui_number_sink_0, 0))
        self.connect((self.epy_block_6, 0), (self.blocks_file_sink_0_0_1, 0))
        self.connect((self.epy_block_6, 0), (self.epy_block_0, 0))
        self.connect((self.epy_block_6, 0), (self.epy_block_5_4, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "sync_coding_v0")
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

    def get_FILE_PATH(self):
        return self.FILE_PATH

    def set_FILE_PATH(self, FILE_PATH):
        self.FILE_PATH = FILE_PATH
        self.set_FILE_BYTES(__import__('os').path.getsize(self.FILE_PATH))

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

    def get_FILE_BYTES(self):
        return self.FILE_BYTES

    def set_FILE_BYTES(self, FILE_BYTES):
        self.FILE_BYTES = FILE_BYTES
        self.set_N_FRAMES((self.FILE_BYTES + self.SPP_LEN - 1) // self.SPP_LEN)
        self.set_SPP_LEN(self.FILE_BYTES)

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

    def get_SPP_LEN(self):
        return self.SPP_LEN

    def set_SPP_LEN(self, SPP_LEN):
        self.SPP_LEN = SPP_LEN
        self.set_N_FRAMES((self.FILE_BYTES + self.SPP_LEN - 1) // self.SPP_LEN)

    def get_CADU_RS_ASM_BYTES(self):
        return self.CADU_RS_ASM_BYTES

    def set_CADU_RS_ASM_BYTES(self, CADU_RS_ASM_BYTES):
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES
        self.set_POST_CONV_BITS(self.CADU_RS_ASM_BYTES *8*(1/self.r))

    def get_k(self):
        return self.k

    def set_k(self, k):
        self.k = k
        self.set_DATA_RATE_BPS((self.Rs*self.k*(1/self.r)))

    def get_TM_HDR_LEN(self):
        return self.TM_HDR_LEN

    def set_TM_HDR_LEN(self, TM_HDR_LEN):
        self.TM_HDR_LEN = TM_HDR_LEN
        self.set_TM_BODY_LEN(self.BYTES_PER_TM_FRAME - self.TM_HDR_LEN)

    def get_Rs(self):
        return self.Rs

    def set_Rs(self, Rs):
        self.Rs = Rs
        self.set_DATA_RATE_BPS((self.Rs*self.k*(1/self.r)))

    def get_POST_CONV_BITS(self):
        return self.POST_CONV_BITS

    def set_POST_CONV_BITS(self, POST_CONV_BITS):
        self.POST_CONV_BITS = POST_CONV_BITS
        self.set_POST_CONV_BYTES(self.POST_CONV_BITS/8)

    def get_N_FRAMES(self):
        return self.N_FRAMES

    def set_N_FRAMES(self, N_FRAMES):
        self.N_FRAMES = N_FRAMES
        self.set_HEAD_SPACING(self.BYTES_PER_TM_FRAME * self.N_FRAMES)

    def get_BYTES_PER_TM_FRAME(self):
        return self.BYTES_PER_TM_FRAME

    def set_BYTES_PER_TM_FRAME(self, BYTES_PER_TM_FRAME):
        self.BYTES_PER_TM_FRAME = BYTES_PER_TM_FRAME
        self.set_HEAD_SPACING(self.BYTES_PER_TM_FRAME * self.N_FRAMES)
        self.set_TM_BODY_LEN(self.BYTES_PER_TM_FRAME - self.TM_HDR_LEN)
        self.epy_block_4.tm_len = self.BYTES_PER_TM_FRAME

    def get_TM_BODY_LEN(self):
        return self.TM_BODY_LEN

    def set_TM_BODY_LEN(self, TM_BODY_LEN):
        self.TM_BODY_LEN = TM_BODY_LEN

    def get_RAND_SEED_ALL_ONES(self):
        return self.RAND_SEED_ALL_ONES

    def set_RAND_SEED_ALL_ONES(self, RAND_SEED_ALL_ONES):
        self.RAND_SEED_ALL_ONES = RAND_SEED_ALL_ONES
        self.epy_block_1.seed = self.RAND_SEED_ALL_ONES

    def get_POST_CONV_BYTES(self):
        return self.POST_CONV_BYTES

    def set_POST_CONV_BYTES(self, POST_CONV_BYTES):
        self.POST_CONV_BYTES = POST_CONV_BYTES

    def get_K(self):
        return self.K

    def set_K(self, K):
        self.K = K
        self.epy_block_3.K = self.K

    def get_HEAD_SPACING(self):
        return self.HEAD_SPACING

    def set_HEAD_SPACING(self, HEAD_SPACING):
        self.HEAD_SPACING = HEAD_SPACING

    def get_DATA_RATE_BPS(self):
        return self.DATA_RATE_BPS

    def set_DATA_RATE_BPS(self, DATA_RATE_BPS):
        self.DATA_RATE_BPS = DATA_RATE_BPS
        self.blocks_throttle2_0.set_sample_rate(self.DATA_RATE_BPS)




def main(top_block_cls=sync_coding_v0, options=None):

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
