"""
@file      uart_monitor.py
@brief     Monitoring and statistics for UART incoming messages
@author    Moosa Baransi
@version   1.0
@date      09/07/2013
"""

import logging
import threading

from gm_common import *

CAN_HS_IDX = 0
CAN_SW_IDX = 1

# Monitoring UART Tx/Rx
class UartMonitor:
    def __init__(self):
        # monitoring lists
        self.expected_uart_responses = []       # stores expected UART responses when sending data from UART to DUT
        self.expected_hs_can_ids = []           # expected High Speed CAN IDs to be monitored
        self.expected_sw_can_ids = []           # expected Single Wire CAN IDs to be monitored
        self.pending_can_ids = []               # pending CAN IDs to be monitored/filtered
        self.message_counter = {}               # holds each message type with its corresponding number of Rx messages
        self.is_can_enabled = [False, False]    # determines if HS/SW CAN streaming is enabled/disabled
        self.logger = logging.getLogger(UART_LOGGER_NAME)
        # lockers
        self.expected_uart_lock = threading.Lock()
        self.can_enable_lock = threading.Lock()
        self.can_monitor_lock = threading.Lock()
        self.can_pending_lock = threading.Lock()

    def is_expected_response(self, response):
        self.expected_uart_lock.acquire()
        res = True if response in self.expected_uart_responses else False
        self.expected_uart_lock.release()
        return res

    def add_expected_response(self, result):
        self.expected_uart_lock.acquire()
        self.expected_uart_responses.append(result)
        self.expected_uart_lock.release()

    def add_can_id_to_monitor(self, can_id, is_sw_port):
        self.can_monitor_lock.acquire()
        if (is_sw_port):
            self.expected_sw_can_ids.append(can_id)
        else:
            self.expected_hs_can_ids.append(can_id)
        self.can_monitor_lock.release()

    def remove_can_id_from_monitor(self, can_id, is_sw_port):
        self.can_monitor_lock.acquire()
        if (is_sw_port):
            self.expected_sw_can_ids.remove(can_id)
        else:
            self.expected_hs_can_ids.remove(can_id)
        self.can_monitor_lock.release()

    def clear_can_monitor_list(self, is_sw_port):
        self.can_monitor_lock.acquire()
        if (is_sw_port):
            del self.expected_sw_can_ids[:]
        else:
            del self.expected_hs_can_ids[:]
        self.can_monitor_lock.release()

    def is_monitored_can_id(self, can_id, is_sw_port):
        self.can_monitor_lock.acquire()
        res = False
        if (is_sw_port):
            res = True if can_id in self.expected_sw_can_ids else False
        else:
            res = True if can_id in self.expected_hs_can_ids else False
        self.can_monitor_lock.release()
        return res

    def add_pending_can_id(self, can_id):
        self.can_pending_lock.acquire()
        self.pending_can_ids.append(can_id)
        self.can_pending_lock.release()

    def pop_pending_can_id(self):
        self.can_pending_lock.acquire()
        res = self.pending_can_ids.pop(0)
        self.can_pending_lock.release()
        return res

    def is_can_stream_enabled(self, is_sw_port):
        res = False
        self.can_enable_lock.acquire()
        if is_sw_port:
            res = self.is_can_enabled[CAN_SW_IDX]
        else:
            res = self.is_can_enabled[CAN_HS_IDX]

        self.can_enable_lock.release()
        return res

    def configCanStrean(self, is_hs_enabled, is_sw_enabled):
        self.can_enable_lock.acquire()
        self.is_can_enabled[CAN_HS_IDX] = is_hs_enabled
        self.is_can_enabled[CAN_SW_IDX] = is_sw_enabled
        self.can_enable_lock.release()
