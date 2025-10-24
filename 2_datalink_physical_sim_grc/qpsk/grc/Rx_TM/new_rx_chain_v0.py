#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: new_rx_chain_v0
# Author: Joshua Wille
# GNU Radio version: 3.10.7.0

from packaging.version import Version as StrictVersion
from PyQt5 import Qt
from gnuradio import qtgui
from gnuradio import blocks
import pmt
from gnuradio import digital
from gnuradio import filter
from gnuradio.filter import firdes
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
import new_rx_chain_v0_epy_block_0 as epy_block_0  # embedded python block
import sip



class new_rx_chain_v0(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "new_rx_chain_v0", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("new_rx_chain_v0")
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

        self.settings = Qt.QSettings("GNU Radio", "new_rx_chain_v0")

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
        self.RS_BYTES = RS_BYTES = 255 * I_RS
        self.RSYM = RSYM = samp_rate/sps
        self.ASM_BYTES = ASM_BYTES = len(ASM_MARKER)
        self.trans_width = trans_width = 0.005 * samp_rate
        self.soft_flip = soft_flip = 1
        self.rrc_taps = rrc_taps = firdes.root_raised_cosine(1.0, samp_rate, RSYM, alpha, span_symbols*sps*filter_size)
        self.qpsk = qpsk = digital.constellation_rect([0.707+0.707j, -0.707+0.707j, -0.707-0.707j, 0.707-0.707j], [0, 1, 2, 3],
        4, 2, 2, 1, 1).base()
        self.loop_bw = loop_bw = 0.005
        self.cuttoff_freq = cuttoff_freq = 0.6 * (1 + alpha) * RSYM
        self.costas_order = costas_order = 4
        self.costas_bw = costas_bw = 2e-3
        self.RS_info_bytes = RS_info_bytes = 223
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES = RS_BYTES + ASM_BYTES
        self.BYTES_PER_FRAME = BYTES_PER_FRAME = 1115

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            "", #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "red", "red", "red",
            "red", "red", "red", "red", "red"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.top_layout.addWidget(self._qtgui_const_sink_x_0_win)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            1,
            firdes.low_pass(
                1,
                samp_rate,
                cuttoff_freq,
                trans_width,
                window.WIN_HAMMING,
                6.76))
        self.epy_block_0 = epy_block_0.blk(len_tag_key=, K=, gen0=, gen1=, reset_each_frame=, soft_mode=)
        self.digital_pfb_clock_sync_xxx_0 = digital.pfb_clock_sync_ccf(sps, loop_bw, rrc_taps, filter_size, 16, 1.5, 1)
        self.digital_costas_loop_cc_0 = digital.costas_loop_cc(costas_bw, costas_order, False)
        self.digital_constellation_soft_decoder_cf_0 = digital.constellation_soft_decoder_cf(qpsk)
        self.blocks_stream_to_tagged_stream_1 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, CADU_RS_ASM_BYTES, "packet_len")
        self.blocks_repack_bits_bb_0 = blocks.repack_bits_bb(1, 8, "", False, gr.GR_MSB_FIRST)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_ff(soft_flip)
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_gr_complex*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/Rx_data/tx_out.cfile', True, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_sink_1_1 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/Rx_data/viterbi_out.bin', False)
        self.blocks_file_sink_1_1.set_unbuffered(False)
        self.blocks_file_sink_1_0 = blocks.file_sink(gr.sizeof_gr_complex*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/Rx_data/source_check.cfile', False)
        self.blocks_file_sink_1_0.set_unbuffered(False)
        self.blocks_file_sink_1 = blocks.file_sink(gr.sizeof_gr_complex*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/Rx_data/ppcs_out.cfile', False)
        self.blocks_file_sink_1.set_unbuffered(False)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/Rx_data/unwrapped.bin', False)
        self.blocks_file_sink_0.set_unbuffered(False)
        self.blocks_delay_0 = blocks.delay(gr.sizeof_float*1, (int(sps//2)))
        self.blocks_complex_to_float_0 = blocks.complex_to_float(1)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_complex_to_float_0, 1), (self.blocks_delay_0, 0))
        self.connect((self.blocks_complex_to_float_0, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.blocks_delay_0, 0), (self.blocks_float_to_complex_0, 1))
        self.connect((self.blocks_file_source_0, 0), (self.blocks_file_sink_1_0, 0))
        self.connect((self.blocks_file_source_0, 0), (self.low_pass_filter_0, 0))
        self.connect((self.blocks_float_to_complex_0, 0), (self.digital_costas_loop_cc_0, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.epy_block_0, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.blocks_file_sink_1_1, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.blocks_stream_to_tagged_stream_1, 0))
        self.connect((self.blocks_stream_to_tagged_stream_1, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.digital_constellation_soft_decoder_cf_0, 0), (self.blocks_multiply_const_vxx_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.digital_constellation_soft_decoder_cf_0, 0))
        self.connect((self.digital_costas_loop_cc_0, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0), (self.blocks_complex_to_float_0, 0))
        self.connect((self.digital_pfb_clock_sync_xxx_0, 0), (self.blocks_file_sink_1, 0))
        self.connect((self.epy_block_0, 0), (self.blocks_repack_bits_bb_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.digital_pfb_clock_sync_xxx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "new_rx_chain_v0")
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
        self.blocks_delay_0.set_dly(int((int(self.sps//2))))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.set_RSYM(self.samp_rate/self.sps)
        self.set_rrc_taps(firdes.root_raised_cosine(1.0, self.samp_rate, self.RSYM, self.alpha, self.span_symbols*self.sps*self.filter_size))
        self.set_trans_width(0.005 * self.samp_rate)
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.cuttoff_freq, self.trans_width, window.WIN_HAMMING, 6.76))

    def get_I_RS(self):
        return self.I_RS

    def set_I_RS(self, I_RS):
        self.I_RS = I_RS
        self.set_RS_BYTES(255 * self.I_RS)

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

    def get_ASM_BYTES(self):
        return self.ASM_BYTES

    def set_ASM_BYTES(self, ASM_BYTES):
        self.ASM_BYTES = ASM_BYTES
        self.set_CADU_RS_ASM_BYTES(self.RS_BYTES + self.ASM_BYTES)

    def get_trans_width(self):
        return self.trans_width

    def set_trans_width(self, trans_width):
        self.trans_width = trans_width
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.cuttoff_freq, self.trans_width, window.WIN_HAMMING, 6.76))

    def get_soft_flip(self):
        return self.soft_flip

    def set_soft_flip(self, soft_flip):
        self.soft_flip = soft_flip
        self.blocks_multiply_const_vxx_0.set_k(self.soft_flip)

    def get_rrc_taps(self):
        return self.rrc_taps

    def set_rrc_taps(self, rrc_taps):
        self.rrc_taps = rrc_taps
        self.digital_pfb_clock_sync_xxx_0.update_taps(self.rrc_taps)

    def get_qpsk(self):
        return self.qpsk

    def set_qpsk(self, qpsk):
        self.qpsk = qpsk
        self.digital_constellation_soft_decoder_cf_0.set_constellation(self.qpsk)

    def get_loop_bw(self):
        return self.loop_bw

    def set_loop_bw(self, loop_bw):
        self.loop_bw = loop_bw
        self.digital_pfb_clock_sync_xxx_0.set_loop_bandwidth(self.loop_bw)

    def get_cuttoff_freq(self):
        return self.cuttoff_freq

    def set_cuttoff_freq(self, cuttoff_freq):
        self.cuttoff_freq = cuttoff_freq
        self.low_pass_filter_0.set_taps(firdes.low_pass(1, self.samp_rate, self.cuttoff_freq, self.trans_width, window.WIN_HAMMING, 6.76))

    def get_costas_order(self):
        return self.costas_order

    def set_costas_order(self, costas_order):
        self.costas_order = costas_order

    def get_costas_bw(self):
        return self.costas_bw

    def set_costas_bw(self, costas_bw):
        self.costas_bw = costas_bw
        self.digital_costas_loop_cc_0.set_loop_bandwidth(self.costas_bw)

    def get_RS_info_bytes(self):
        return self.RS_info_bytes

    def set_RS_info_bytes(self, RS_info_bytes):
        self.RS_info_bytes = RS_info_bytes

    def get_CADU_RS_ASM_BYTES(self):
        return self.CADU_RS_ASM_BYTES

    def set_CADU_RS_ASM_BYTES(self, CADU_RS_ASM_BYTES):
        self.CADU_RS_ASM_BYTES = CADU_RS_ASM_BYTES
        self.blocks_stream_to_tagged_stream_1.set_packet_len(self.CADU_RS_ASM_BYTES)
        self.blocks_stream_to_tagged_stream_1.set_packet_len_pmt(self.CADU_RS_ASM_BYTES)

    def get_BYTES_PER_FRAME(self):
        return self.BYTES_PER_FRAME

    def set_BYTES_PER_FRAME(self, BYTES_PER_FRAME):
        self.BYTES_PER_FRAME = BYTES_PER_FRAME




def main(top_block_cls=new_rx_chain_v0, options=None):

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
