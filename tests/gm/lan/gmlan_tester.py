"""
@file      gmlan_tester.py
@brief     The tester which runs the specified GMLAN test
@author    Moosa Baransi
@version   1.0
@date      09/07/2013
"""
from tests.gm.lan import komodo_if as Komodo

from tests.gm.lan.gm_common import *
from random import choice
from random import randint
from tests.gm.lan.uart_handler import UartHandler as Uart
from array import array
import time
import threading
import logging

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
        self._komodo = Komodo.Komodo()
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
    '''
    The following test monitors a single message randomly, waits for the GM replay box to finish the replay,
    and compares the data arrived with the pre-captured GM log and checks if we got the data completely in
    the right order
    '''
    def _functional_test(self):
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

    '''
    The sanity tests perfomrs a random monitoring in real-time and checks that the incoming
    UART packets obay to the set of rules
    '''
    def _sanity_test(self, max_monitored_messages=3, sanity_test_duration=10):
        # Start listener thread
        self._uart_handler.startListen()
        time.sleep(0.5)
        # Enable HS CAN streaming
        self._uart_handler.send_uart_command(UART_CMD_ENABLE_CAN_ID, UART_OPT_ENABLE_CAN_HS)
        time.sleep(0.5)
        monitored_messages_cnt = 0
        monitored_ids = []
        start_time = time.time()
        while True:
            if (monitored_messages_cnt < max_monitored_messages):
                monitored_messages_cnt += 1

                retry_choice = 0
                while (True):
                    str_can_id = self._choose_can_id()
                    if str_can_id in monitored_ids:
                        retry_choice += 1
                        if (retry_choice == 10):
                            self.logger.error("Random function is not random!")
                            break
                        continue
                    else:
                        break

                monitored_ids.append(str_can_id)
                command_arguments = UART_OPT_MONITOR_ADD + str_can_id
                self._uart_handler.send_uart_command(UART_CMD_MONITOR_HS_ID, command_arguments)
                # Check if we passed the sanity test duration
                if (time.time() - start_time) >= sanity_test_duration:
                    self._uart_handler.send_uart_command(UART_CMD_MONITOR_HS_ID, UART_OPT_MONITOR_DEL_ALL + "\x00\xF1")
                    time.sleep(0.5)
                    self._uart_handler.send_uart_command(UART_CMD_ENABLE_CAN_ID, UART_OPT_ENABLE_CAN_NONE)
                    # print message counters
                    dict = self._uart_handler.get_message_counters()
                    for k in sorted(dict.keys()):
                        strmsg = ":".join(x.encode('hex') for x in k)
                        strmsg += " : " + str(dict[k])
                        print strmsg
                    # break the while loop
                    break
                time.sleep(randint(1, 5));
            else:
                # remove one of the monitored messages in order to be replaced by another one
                str_can_id = choice(monitored_ids)
                monitored_ids.remove(str_can_id)
                command_arguments = UART_OPT_MONITOR_DEL + str_can_id
                self._uart_handler.send_uart_command(UART_CMD_MONITOR_HS_ID, command_arguments)
                monitored_messages_cnt -= 1

    def _choose_can_id(self):
        # pick a random can_id from the list
        return choice(CAN_AVAILABLE_HS_MESSAGES)

class GmLanTester:
    def __init__(self, test_type, max_monitored_messages = 3, com_port = "COM0", sanity_test_duration=10, uart_rx_timeout=30):
        try:
            self._uart_handler = Uart(com_port, uart_rx_timeout)
        except Exception as e:
            raise e
            return
        self._gm_tester = GmTestsSuite(self._uart_handler)
        self._test_type = test_type
        self._max_monitored_messages = max_monitored_messages
        self._sanity_test_duration = sanity_test_duration

    def start_gmlan_test(self):
        # activate the desired test
        if self._test_type == GM_SANITY_TEST:
            self._gm_tester._sanity_test(self._max_monitored_messages, self._sanity_test_duration)
        elif self._test_type == GM_FUNCTIONAL_TEST:
            self._gm_tester._functional_test()
        self._uart_handler.stop_uart()
        print("GM Test ended.")
