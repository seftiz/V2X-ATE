"""
@file      uart_handler.py
@brief     Handles incoming UART packets and interprete them accordingly
@author    Moosa Baransi
@version   1.0
@date      09/07/2013
"""

import threading
import serial
import sys
import Queue
import logging
import hdlc
from uart_monitor import UartMonitor
from gm_common import *
import logging

class UartHandler():
    def __init__(self, uart, read_timeout):
        self.logger = logging.getLogger(__name__)
        try:
            self.ser = serial.Serial(   port=uart,
                                        baudrate=115200,
                                        parity=serial.PARITY_NONE,
                                        stopbits=serial.STOPBITS_ONE,
                                        bytesize=serial.EIGHTBITS,
                                        timeout = 1)
        except Exception as e:
            raise e
            return

        self._rx_queue = Queue.Queue(10)
        self.uart_stop_event = threading.Event()
        self.read_timeout = read_timeout
        # Create a UART monitor
        self.monitor = UartMonitor()
        # Start serial port interpreter
        self._interpreter = UartRxInterpreter(2, "Interpreter Thread", self._rx_queue, self.monitor)
        self._interpreter.start()

    def stop_uart(self):
        self.uart_stop_event.set()
        self._interpreter.join()
        self._listener.join()
        self.ser.close()

    def startListen(self):
        # Both UartListener and UartRxInterpreter share the same queue for
        # Rx UART packets IPC
        
        self.uart_stop_event.clear()
        # Start listening on serial port
        self._listener = UartListener(1, "Uart Listener", self.ser, self._rx_queue, self.uart_stop_event)
        self._listener.set_packet_timeout(self.read_timeout)
        self._listener.start()

    def sniff_can_id(self, can_id_str):
        self._interpreter.sniff_can_id(can_id_str)

    def get_sniffed_list(self):
        return self._interpreter.sniffed_frames

    def get_message_counters(self):
        return self.monitor.message_counter.copy()

    def send_direct_comand(self, cmd_id, cmd_data):
        command_to_encode = cmd_id + cmd_data
        encoded = hdlc.hdlc_encode(command_to_encode)
        self.logger.info("Direct send: " + ':'.join(x.encode('hex') for x in encoded))
        self.ser.write(encoded)

    def send_uart_command(self, cmd_id, cmd_data):
        command_to_encode = cmd_id + cmd_data

        if cmd_id == UART_CMD_ENABLE_CAN_ID:
            self.monitor.add_expected_response(UART_RSP_ENABLE_CAN_ID + cmd_data)

        elif cmd_id == UART_CMD_MONITOR_HS_ID or cmd_id == UART_CMD_MONITOR_SW_ID:
            is_sw_port = True if cmd_id == UART_CMD_MONITOR_SW_ID else False
            stream_name = "SW" if is_sw_port else "HS"
            if not self.monitor.is_can_stream_enabled(is_sw_port):
                self.logger.warning("stream " + stream_name + " disabled. Send has no effect")
                return False
            isValidReq = False
            canIdLen = 4 if is_sw_port else 2    
            rsp = UART_RSP_MONITOR_SW if is_sw_port else UART_RSP_MONITOR_HS
            rsp += cmd_data[0]
            # check if the argument is valid
            if (cmd_data[0] in UART_OPT_MONITOR_VALID):
                # check if the CAN ID is valid
                canIdStr = cmd_data[1 : 1 + canIdLen]
                if (canIdStr in CAN_AVAILABLE_HS_MESSAGES):
                    self.monitor.add_pending_can_id(canIdStr)
                    isValidReq = True
                else:
                    self.logger.warning("Unknown message ID!: " + ':'.join(x.encode('hex') for x in canIdStr) + str(can_id))
            
            rsp += "\x00" if isValidReq else "\x01"
            self.monitor.add_expected_response(rsp)
        
        encoded = hdlc.hdlc_encode(command_to_encode)
        self.logger.info("Sending: " + ':'.join(x.encode('hex') for x in encoded))
        self.ser.write(encoded)
        return True

class UartListener (threading.Thread):
    def __init__(self, threadID, name, ser, rx_queue, uart_stop_event):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.ser = ser        
        self._rx_queue = rx_queue
        self.logger = logging.getLogger(__name__)
        self._stop_event = uart_stop_event

    def set_packet_timeout(self, timeout):
        self.packet_timeout = timeout

    def run(self):
        self.logger.debug("Starting " + self.name)
        # make sure serial is opened
        if (self.ser.isOpen() == False):
            self.ser.open()
        total_time_out = 0
        # packet_buffer holds a valid packet from serial
        packet_buffer = ""
        # get the time out of single characters
        serial_timeout = self.ser.getSettingsDict()['timeout']
        # loop on the packets
        while not self._stop_event.is_set():
            part, is_packet_completed = self._receive_single_packet()
            packet_buffer += part
            # if we received the whole packet, send it for interpreting
            if is_packet_completed:
                self._rx_queue.put(packet_buffer)
                total_time_out = 0
                packet_buffer = ""
            # in part is empty then we had a time out
            elif len(part) == 0:
                total_time_out += serial_timeout
                if total_time_out > self.packet_timeout:
                    self.logger.info("No Rx detected for {0} seconds".format(self.packet_timeout))
                    break
        # special character to inform the interpreter that we're done
        self._rx_queue.put("\xFF")
        self.logger.info("Listener ended")

    def _receive_single_packet(self):
        # loop on received bytes
        buff = ""
        while True:
            more = self.ser.read()
            if len(more) == 0:
                return buff, False
            buff += more
            # if we received the last character of the packet
            if (ord(buff[-1]) == hdlc.HDLC_EOT):
                return buff, True


class UartRxInterpreter (threading.Thread):
    def __init__(self, threadID, name, rx_queue, monitor):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self._rx_queue = rx_queue
        self.logger = logging.getLogger(__name__)
        self.monitor = monitor
        self.sniffed_frames = []
        self._sniff_frame_id = None

    def run(self):
        self.logger.debug("Starting " + self.name)
        self.packetListener()

    def sniff_can_id(self, can_id_str):
        self._sniff_frame_id = can_id_str

    def packetListener(self):
        while True:
            packet = self._rx_queue.get()
            # special character informing that we're done
            if packet == "\xFF":
                break
            res = self.handlePacket(packet)
            if (not res):
                self.logger.warning("Packet handling failed")
            self._rx_queue.task_done()
        self.logger.info(" Interpreter ended")

    def handlePacket(self, packet):
        # Decode packet, strip the HDLC protocol
        decoded = hdlc.hdlc_decode(packet)
        if decoded == None:
            self.logger.warning("decoding failed for: " + ':'.join(x.encode('hex') for x in packet))
            return False
        self.logger.debug("Incoming packet: " + ':'.join(x.encode('hex') for x in decoded))

        cmd_id = decoded[0]

        if cmd_id == UART_RCV_HS_ID or cmd_id == UART_RCV_SW_ID:
            is_sw_port = True if cmd_id == UART_RCV_SW_ID else False
            canIdLen = 4 if is_sw_port else 2
            canIdStr = decoded[1 : 1 + canIdLen]
            # check if the incoming is a monitored message
            if self.monitor.is_monitored_can_id(canIdStr, is_sw_port):
                if self._sniff_frame_id is not None:
                    if self._sniff_frame_id == canIdStr:
                        # append to sniffed packets, take the actual data
                        self.sniffed_frames.append(decoded[1 + canIdLen:])
                if self.monitor.message_counter.has_key(canIdStr):
                    self.monitor.message_counter[canIdStr] += 1
                else:
                    # first time message arrives
                    self.monitor.message_counter[canIdStr] = 1
                return True
            self.logger.warning("unexpected CAN message: " + ':'.join(x.encode('hex') for x in decoded))
            return False

        isExpected = self.monitor.is_expected_response(decoded)
        if not isExpected:
            self.logger.warning("Unexpected response packet: " + ':'.join(x.encode('hex') for x in decoded))
            return False
        
        if cmd_id == UART_RSP_ENABLE_CAN_ID:
            is_hs_enabled = False
            is_sw_enabled = False  
            # Enable the relevant interface(s)
            if decoded[1] == UART_OPT_ENABLE_CAN_BOTH:
                is_hs_enabled = True
                is_sw_enabled = True
            elif decoded[1] == UART_OPT_ENABLE_CAN_HS:
                is_hs_enabled = True
            elif decoded[1] == UART_OPT_ENABLE_CAN_SW:
                is_sw_enabled = True
            # apply the rules
            self.monitor.configCanStrean(is_hs_enabled, is_sw_enabled)

        elif cmd_id == UART_RSP_MONITOR_HS or cmd_id == UART_RSP_MONITOR_SW:
            is_sw_port = True if cmd_id == UART_RSP_MONITOR_SW else False
            if decoded[2] != "\x00":
                return True # in case of invalid command, nothing shall be changed
            can_id = self.monitor.pop_pending_can_id()
            if decoded[1] == UART_OPT_MONITOR_ADD:
                self.monitor.add_can_id_to_monitor(can_id, is_sw_port)
            elif decoded[1] == UART_OPT_MONITOR_DEL:
                self.monitor.remove_can_id_from_monitor(can_id, is_sw_port)
            elif decoded[1] == UART_OPT_MONITOR_DEL_ALL:
                self.monitor.clear_can_monitor_list(is_sw_port)
            else:
                self.logger.warning("Unknows response option for CAN monitoring: 0x" + decoded[1].encode('hex'))
        return True

