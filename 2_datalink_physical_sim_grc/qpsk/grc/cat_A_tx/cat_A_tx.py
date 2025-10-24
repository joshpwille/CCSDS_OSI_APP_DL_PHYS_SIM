#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: cat_A_tx
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



class cat_A_tx(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "cat_A_tx", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("cat_A_tx")
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

        self.settings = Qt.QSettings("GNU Radio", "cat_A_tx")

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
        self.beta = beta = 0.3
        self.Rs = Rs = 250000
        self.BYTES_PER_PKT = BYTES_PER_PKT = 1115
        self.samp_rate = samp_rate = Rs*sps
        self.rf_bw = rf_bw = Rs*(1+beta)
        self.rcc_taps = rcc_taps = 0
        self.qpsk = qpsk = digital.constellation_rect([0.707+0.707j, -0.707+0.707j, -0.707-0.707j, 0.707-0.707j], [0, 1, 2, 3],
        4, 2, 2, 1, 1).base()
        self.lo_offset = lo_offset = 1000000
        self.gain = gain = 0
        self.alpha = alpha = beta
        self.Fc = Fc = 2200000000
        self.BITS_PER_PKT = BITS_PER_PKT = BYTES_PER_PKT*8

        ##################################################
        # Blocks
        ##################################################

        self.root_raised_cosine_filter_0 = filter.interp_fir_filter_ccf(
            sps,
            firdes.root_raised_cosine(
                1,
                samp_rate,
                Rs,
                alpha,
                (11*sps)))
        self.root_raised_cosine_filter_0.set_block_alias("rrc_c")
        self.mmse_resampler_xx_0_0 = filter.mmse_resampler_ff(0.5, 1)
        self.digital_chunks_to_symbols_xx_0_0 = digital.chunks_to_symbols_bf([-1.0, 1.0], 1)
        self.digital_chunks_to_symbols_xx_0_0.set_block_alias("sym_I")
        self.digital_chunks_to_symbols_xx_0 = digital.chunks_to_symbols_bf([-1.0, 1.0], 1)
        self.digital_chunks_to_symbols_xx_0.set_block_alias("sym_Q")
        self.blocks_tagged_stream_align_0 = blocks.tagged_stream_align(gr.sizeof_gr_complex*1, 'packet_len')
        self.blocks_tag_debug_0_0_0 = blocks.tag_debug(gr.sizeof_gr_complex*1, 'Q_bits', "packet_len")
        self.blocks_tag_debug_0_0_0.set_display(True)
        self.blocks_tag_debug_0_0 = blocks.tag_debug(gr.sizeof_char*1, 'Q_bits', "packet_len")
        self.blocks_tag_debug_0_0.set_display(True)
        self.blocks_tag_debug_0 = blocks.tag_debug(gr.sizeof_char*1, 'I_bits', "packet_len")
        self.blocks_tag_debug_0.set_display(True)
        self.blocks_stream_to_tagged_stream_3 = blocks.stream_to_tagged_stream(gr.sizeof_gr_complex, 1, (int(BITS_PER_PKT/2) * sps), "packet_len")
        self.blocks_stream_to_tagged_stream_2 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, (int(BITS_PER_PKT/2)), "packet_len")
        self.blocks_stream_to_tagged_stream_2.set_block_alias("STTS_Q")
        self.blocks_stream_to_tagged_stream_1 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, (int(BITS_PER_PKT/2)), "packet_len")
        self.blocks_stream_to_tagged_stream_1.set_block_alias("STTS_I")
        self.blocks_stream_to_tagged_stream_0 = blocks.stream_to_tagged_stream(gr.sizeof_char, 1, BYTES_PER_PKT, "packet_len")
        self.blocks_repack_bits_bb_0 = blocks.repack_bits_bb(8, 1, "packet_len", False, gr.GR_MSB_FIRST)
        self.blocks_multiply_const_vxx_0 = blocks.multiply_const_cc(0.7)
        self.blocks_keep_m_in_n_1 = blocks.keep_m_in_n(gr.sizeof_char, 1, 2, 1)
        self.blocks_keep_m_in_n_1.set_block_alias("keep_old")
        self.blocks_keep_m_in_n_0 = blocks.keep_m_in_n(gr.sizeof_char, 1, 2, 0)
        self.blocks_keep_m_in_n_0.set_block_alias("keep_even")
        self.blocks_float_to_complex_0 = blocks.float_to_complex(1)
        self.blocks_file_source_0 = blocks.file_source(gr.sizeof_char*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/cadu_v0.bin', True, 0, 0)
        self.blocks_file_source_0.set_begin_tag(pmt.PMT_NIL)
        self.blocks_file_sink_0 = blocks.file_sink(gr.sizeof_gr_complex*1, '/home/dogg/Downloads/tm_stagin_grc/qpsk/data/art/tx_out.cfile', False)
        self.blocks_file_sink_0.set_unbuffered(False)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.blocks_file_source_0, 0), (self.blocks_stream_to_tagged_stream_0, 0))
        self.connect((self.blocks_float_to_complex_0, 0), (self.root_raised_cosine_filter_0, 0))
        self.connect((self.blocks_keep_m_in_n_0, 0), (self.blocks_stream_to_tagged_stream_1, 0))
        self.connect((self.blocks_keep_m_in_n_1, 0), (self.blocks_stream_to_tagged_stream_2, 0))
        self.connect((self.blocks_multiply_const_vxx_0, 0), (self.blocks_stream_to_tagged_stream_3, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.blocks_keep_m_in_n_0, 0))
        self.connect((self.blocks_repack_bits_bb_0, 0), (self.blocks_keep_m_in_n_1, 0))
        self.connect((self.blocks_stream_to_tagged_stream_0, 0), (self.blocks_repack_bits_bb_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_1, 0), (self.blocks_tag_debug_0_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_1, 0), (self.digital_chunks_to_symbols_xx_0_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_2, 0), (self.blocks_tag_debug_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_2, 0), (self.digital_chunks_to_symbols_xx_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_3, 0), (self.blocks_tag_debug_0_0_0, 0))
        self.connect((self.blocks_stream_to_tagged_stream_3, 0), (self.blocks_tagged_stream_align_0, 0))
        self.connect((self.blocks_tagged_stream_align_0, 0), (self.blocks_file_sink_0, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0, 0), (self.mmse_resampler_xx_0_0, 0))
        self.connect((self.digital_chunks_to_symbols_xx_0_0, 0), (self.blocks_float_to_complex_0, 0))
        self.connect((self.mmse_resampler_xx_0_0, 0), (self.blocks_float_to_complex_0, 1))
        self.connect((self.root_raised_cosine_filter_0, 0), (self.blocks_multiply_const_vxx_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "cat_A_tx")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_sps(self):
        return self.sps

    def set_sps(self, sps):
        self.sps = sps
        self.set_samp_rate(self.Rs*self.sps)
        self.blocks_stream_to_tagged_stream_3.set_packet_len((int(self.BITS_PER_PKT/2) * self.sps))
        self.blocks_stream_to_tagged_stream_3.set_packet_len_pmt((int(self.BITS_PER_PKT/2) * self.sps))
        self.root_raised_cosine_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, self.Rs, self.alpha, (11*self.sps)))

    def get_beta(self):
        return self.beta

    def set_beta(self, beta):
        self.beta = beta
        self.set_alpha(self.beta)
        self.set_rf_bw(self.Rs*(1+self.beta))

    def get_Rs(self):
        return self.Rs

    def set_Rs(self, Rs):
        self.Rs = Rs
        self.set_rf_bw(self.Rs*(1+self.beta))
        self.set_samp_rate(self.Rs*self.sps)
        self.root_raised_cosine_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, self.Rs, self.alpha, (11*self.sps)))

    def get_BYTES_PER_PKT(self):
        return self.BYTES_PER_PKT

    def set_BYTES_PER_PKT(self, BYTES_PER_PKT):
        self.BYTES_PER_PKT = BYTES_PER_PKT
        self.set_BITS_PER_PKT(self.BYTES_PER_PKT*8)
        self.blocks_stream_to_tagged_stream_0.set_packet_len(self.BYTES_PER_PKT)
        self.blocks_stream_to_tagged_stream_0.set_packet_len_pmt(self.BYTES_PER_PKT)

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.root_raised_cosine_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, self.Rs, self.alpha, (11*self.sps)))

    def get_rf_bw(self):
        return self.rf_bw

    def set_rf_bw(self, rf_bw):
        self.rf_bw = rf_bw

    def get_rcc_taps(self):
        return self.rcc_taps

    def set_rcc_taps(self, rcc_taps):
        self.rcc_taps = rcc_taps

    def get_qpsk(self):
        return self.qpsk

    def set_qpsk(self, qpsk):
        self.qpsk = qpsk

    def get_lo_offset(self):
        return self.lo_offset

    def set_lo_offset(self, lo_offset):
        self.lo_offset = lo_offset

    def get_gain(self):
        return self.gain

    def set_gain(self, gain):
        self.gain = gain

    def get_alpha(self):
        return self.alpha

    def set_alpha(self, alpha):
        self.alpha = alpha
        self.root_raised_cosine_filter_0.set_taps(firdes.root_raised_cosine(1, self.samp_rate, self.Rs, self.alpha, (11*self.sps)))

    def get_Fc(self):
        return self.Fc

    def set_Fc(self, Fc):
        self.Fc = Fc

    def get_BITS_PER_PKT(self):
        return self.BITS_PER_PKT

    def set_BITS_PER_PKT(self, BITS_PER_PKT):
        self.BITS_PER_PKT = BITS_PER_PKT
        self.blocks_stream_to_tagged_stream_1.set_packet_len((int(self.BITS_PER_PKT/2)))
        self.blocks_stream_to_tagged_stream_1.set_packet_len_pmt((int(self.BITS_PER_PKT/2)))
        self.blocks_stream_to_tagged_stream_2.set_packet_len((int(self.BITS_PER_PKT/2)))
        self.blocks_stream_to_tagged_stream_2.set_packet_len_pmt((int(self.BITS_PER_PKT/2)))
        self.blocks_stream_to_tagged_stream_3.set_packet_len((int(self.BITS_PER_PKT/2) * self.sps))
        self.blocks_stream_to_tagged_stream_3.set_packet_len_pmt((int(self.BITS_PER_PKT/2) * self.sps))




def main(top_block_cls=cat_A_tx, options=None):
    if gr.enable_realtime_scheduling() != gr.RT_OK:
        gr.logger("realtime").warning("Error: failed to enable real-time scheduling.")

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
