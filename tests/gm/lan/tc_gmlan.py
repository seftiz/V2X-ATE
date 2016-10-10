"""
@file tc_gmlan.py
@brief Testsuite for testing GMLAN
@author    	Moosa Baransi
@version	1.0
@date		19/08/2012
"""

# import global setup var
# from atlk.ut import topology
from lib import station_setup
from uuts import common
from lib import instruments_manager
from lib import packet_analyzer
from lib import globals

from random import choice
from array import array
from tests import sdk2_0
from tests import common
from tests.gm.lan.gm_common import *
#from lib import komodo_if as Komodo
from tests.gm.lan.uart_handler import UartHandler as Uart

import sys
import time
import logging

# @topology('CF01')
class TC_GMLAN(common.V2X_SDKBaseTest):
    """
    @class AtlkUnit
    @brief ATLK base unit Implementation 
    @author Shai Shochat
    @version 0.1
    @date	27/01/2013
    """

    def runTest(self):
        pass

    def tearDown(self):
        pass


    def __init__(self, methodName = 'runTest', param = None):
        return super(TC_GMLAN, self).__init__(methodName, param)

    def test_functional_gmaln(self):
        """ Test GMLAN functionality
            @fn         test_functional_gmaln
            @brief      Verify functional test of GMLAN
            @details    Test ID	: TC_GM_LAN_01\n
                        Test Name 	: GM LAN\n
                        Objective 	: Test interaction between CAN interface and Bluetooth monitoring of messages
            @see Test Plan	: [TBD]
        """ 
        com_port = self.param.get('com_port', 'COM1')
        rx_packet_timeout = self.param.get('rx_packet_timeout', 30)

        # prepare UART
        uart_interface = Uart(com_port, rx_packet_timeout)

        gmlan_test = GmTestsSuite(uart_interface)
        gmlan_test.functional_test()
        # stop UART threads when test is finished
        uart_interface.stop_uart()


class GmTestsSuite():
    def __init__(self, uart_interface, komodo_interface = Komodo.KOMODO_IF_CAN_A):
        self._uart_handler = uart_interface
        self.logger = logging.getLogger(__name__)
        self._komodo_interface = komodo_interface

    def _bin_str_2_hex(self, bin):
        res = 0
        for x in bin:
            res = 256 * res + ord(x)
        return res

    def _extract_can_frames_from_file(self, captured_file, selected_can_id, returned_list):
        counter = 0
        for line in captured_file:
            if int(line[9:14], 16) == selected_can_id:
                data_len = int(line[22:23])
                returned_list.append( (selected_can_id, line[33:33 + 6 * data_len - 2]) )
                counter += 1
        return counter


    def _komodo_format_can_frames_from_file(self, captured_file, returned_list):
        counter = 0
        for line in captured_file:
            # data length is represented by 2 digits in the playback file. Offset 22
            data_len = int(line[22:23])
            # this is the data in the playback file separated by ", "
            data = line[33:33 + 6 * data_len - 2]
            # values is a list of ASCII hex
            ascii_hex_values = data.split(", ")
            # convert each ascii hex into its binary value
            hex_values = [int(x, 16) for x in ascii_hex_values]
            # the CAN ID is represented in ASCII HEX in the captured file. Offset 9, 5 digits
            returned_list.append( (int(line[9:14], 16), array('B',hex_values)) )
            counter += 1
        return counter

    # prepare playback device
    def _prepare_playback_device(self):

        if globals.setup.instruments.can_bus is None:
            raise globals.Error("Can bus server is not initilize, please check your configuration")
        else:
            # Get pointer to object
            self._komodo = globals.setup.instruments.can_bus

        #self._komodo = Komodo.Komodo()
        self._komodo.configure_port(self._komodo_interface)
        self._komodo.power_up(self._komodo_interface)

    def _shutdown_playback_device(self):
        self._komodo.power_down(self._komodo_interface)

    # start the playback sequence
    def _start_playback(self):
        self._prepare_playback_device()
        # open file and prepare the list
        try:
            capture = open("./tests/gm/lan/capture.log", "r")
        except Exception as e:
            self.logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            raise
        playback_list = []
        self._komodo_format_can_frames_from_file(capture, playback_list)
        counter = 0
        total_frames = len(playback_list)
        for frame in playback_list:
            self._komodo.send_frame(self._komodo_interface, frame[0], frame[1])
            counter += 1
            if counter % 100 == 0:
                #print "\r{0:.2f}%".format(float(counter) / total_frames * 100),
                time.sleep(0.0001)

    def _choose_can_id(self):
        # pick a random can_id from the list
        return choice(CAN_AVAILABLE_HS_MESSAGES)

    '''
    The following test monitors a single message randomly, waits for the GM replay box to finish the replay,
    and compares the data arrived with the pre-captured GM log and checks if we got the data completely in
    the right order
    '''
    def functional_test(self):
        print_counter = 0
        # open file and prepare the list
        try:
            capture = open("./tests/gm/lan/capture.log", "r")
        except Exception as e:
            self.logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
            return
        elements = []
        miss = 0
        monitored_str_id = self._choose_can_id()
        monitored_id = self._bin_str_2_hex(monitored_str_id)

        self.logger.info( "Monitoring: " + hex(monitored_id))
        self._uart_handler.sniff_can_id(monitored_str_id)

        print "Calculating monitored ID"
        counter = self._extract_can_frames_from_file(capture, monitored_id, elements)

        print "list length should be:", counter
        # Start listening to serial port
        self._uart_handler.startListen()
        time.sleep(0.5)
        # Enable streaming
        self._uart_handler.send_uart_command(UART_CMD_ENABLE_CAN_ID, UART_OPT_ENABLE_CAN_HS)
        time.sleep(0.5)
        # enable streaming for the specific message
        command_arguments = UART_OPT_MONITOR_ADD + monitored_str_id
        self._uart_handler.send_uart_command(UART_CMD_MONITOR_HS_ID, command_arguments)
        time.sleep(0.5)

        self.logger.info("Starting GM playback")
        self._start_playback()
        self._shutdown_playback_device()
        l = self._uart_handler.get_sniffed_list()

        if len(l) != counter:
            print "Expected " + str(counter) + " frames, got " + str(len(l))
        else:
            for i in range(len(l)):
                tup = elements[i]
                bin_data = ""
                # tup[1] contains the data in ASCII Hex
                capture_data = tup[1].split(", ")
                for single_hex in capture_data:
                    bin_data += chr(int(single_hex, 16))
                if l[i] != bin_data:
                    self.logger.error("Wrong data: expected " + ':'.join(x.encode('hex') for x in l[i]) + " got: " + ':'.join(x.encode('hex') for x in bin_data))
                    miss += 1
            if miss > 0:
                print "Had " + str(miss) + " mismatches"
            else:
                print "No mismatch found, Test OK"
        # Shut down
        command_arguments = UART_OPT_MONITOR_DEL_ALL + monitored_str_id
        self._uart_handler.send_uart_command(UART_CMD_MONITOR_HS_ID, command_arguments)
        time.sleep(0.1)
        self._uart_handler.send_uart_command(UART_CMD_ENABLE_CAN_ID, UART_OPT_ENABLE_CAN_NONE)
        time.sleep(0.1)

        capture.close()

        # print message counters
        dict = self._uart_handler.get_message_counters()
        for k in sorted(dict.keys()):
            strmsg = ":".join(x.encode('hex') for x in k)
            strmsg += " : " + str(dict[k])
            print strmsg