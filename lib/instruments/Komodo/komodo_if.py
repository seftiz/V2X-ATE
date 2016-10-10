"""
@file      komodo_if.py
@brief     Interface for komodo testing equipment
@author    Moosa Baransi
@version   1.0
@date      09/07/2013
"""

from __future__ import division
from lib.instruments.Komodo import komodo_py as komodo_drv 
import logging
import time
from array import array
from lib import globals
import threading

 
KOMODO_IF_BIT_RATE_500KHZ = 500000
KOMODO_IF_PORT = 0
KOMODO_IF_CAN_A = komodo_drv.KM_CAN_CH_A
KOMODO_IF_CAN_B = komodo_drv.KM_CAN_CH_B


log = logging.getLogger(__name__)



class Komodo(object):
    
    def __init__(self, bit_rate = KOMODO_IF_BIT_RATE_500KHZ):
        self._bit_rate = bit_rate
        self._is_power_up = False
        self._port = [None, None]

    def _check_interface_range(self, interface):
        assert interface in [KOMODO_IF_CAN_A, KOMODO_IF_CAN_B], "Wrong interface number: {0}".format(interface)

    def get_avaliable_port():
        try:
            port = self._port.index(None)
        except ValueError as e:
            raise (" Can device has no avaliable port")

        return port

    def find_devices(self):
        max_ports_to_search = 5
        try:
            rc = komodo_drv.km_find_devices(max_ports_to_search)
            self.num_ports, self.ports = rc
            
        except Exception as e:
            raise e

    def configure_port(self, interface):
        self._check_interface_range(interface)
        local_port = komodo_drv.km_open(interface)
        if local_port < 0:
            raise Exception("Could not open port {0}, error {1}".format(interface, local_port))
        log.info("Powering up port {0}".format(local_port))
        # configure port A for write & read
        if interface == KOMODO_IF_CAN_A:
            features = komodo_drv.KM_FEATURE_CAN_A_CONFIG | komodo_drv.KM_FEATURE_CAN_A_CONTROL | komodo_drv.KM_FEATURE_CAN_A_LISTEN
        else:
            features = komodo_drv.KM_FEATURE_CAN_B_CONFIG | komodo_drv.KM_FEATURE_CAN_B_CONTROL | komodo_drv.KM_FEATURE_CAN_B_LISTEN

        komodo_drv.km_acquire(local_port, features)
        rate = komodo_drv.km_can_bitrate(local_port, interface, self._bit_rate)
        if rate != self._bit_rate:
            raise Exception("Could not set bit rate to {0} KHz, instead it is {1} KHz".format(self._bit_rate // 1000, rate // 1000))

        self._port[interface] = local_port

    def set_timeout (self, interface, timeout_ms=100):
        self._check_interface_range(interface)
        komodo_drv.km_timeout (self._port[interface], timeout_ms)

    def close_port( self, interface ):

        if self._port[interface] is None:
            raise Exception("Port number {0} is not configured".format(interface))
        
        komodo_drv.km_close(self._port[interface])
        self._port[interface] = None

    def power_up(self, interface):
        self._check_interface_range(interface)
        # power up the port
        if self._port[interface] is None:
            raise Exception("Port number {0} is not configured".format(interface))
        ret = komodo_drv.km_can_target_power(self._port[interface], interface, komodo_drv.KM_TARGET_POWER_ON)
        if ret != komodo_drv.KM_OK:
            raise Exception("Could not power on channel A, error {0}".format(ret))
        # enable the port
        ret = komodo_drv.km_enable(self._port[interface])
        if ret != komodo_drv.KM_OK:
            raise Exception("Could not enable CAN port, error {0}".format(ret))
        self._is_power_up = True

    def power_down(self, interface):
        self._check_interface_range(interface)

        # disable the port
        if self._port[interface] is None:
            raise Exception("Port number {0} is not configured".format(interface))
        ret = komodo_drv.km_disable(self._port[interface])
        if ret != komodo_drv.KM_OK:
            raise Exception("Could not disable CAN port, error {0}".format(ret))        
        # power off the port
        ret = komodo_drv.km_can_target_power(self._port[interface], interface, komodo_drv.KM_TARGET_POWER_OFF)
        if ret != komodo_drv.KM_OK:
            raise Exception("Could not power off channel A, error {0}".format(ret))
        self._is_power_up = False

    def send_frame(self, interface, can_frame):

        self._check_interface_range(interface)
        if not self._is_power_up:
            raise Exception("Could not send frame - CAN Port is not powered up")

        if self._port[interface] is None:
            raise Exception("Could not send frame - Port number {0} is not configured".format(interface))

        pkt       = komodo_drv.km_can_packet_t()
        pkt.id    = can_frame.can_id
        pkt.dlc   = can_frame.dlc
        pkt.extend_addr = can_frame.ide_f
        pkt.remote_req  = can_frame.rtr_f

        # Convert data of type list to array for the komodo driver
        data = array('B', can_frame.data)

        ret, bytes = komodo_drv.km_can_write(self._port[interface], interface, 0, pkt, data)
        if ret < 0:
            raise Exception("Could not send frame, error {0}".format(ret))

    def get_frame(self, interface, timeout_sec=60):
        self._check_interface_range(interface)
        if not self._is_power_up:
            raise Exception("Could not get frame - CAN Port is not powered up")

        if self._port[interface] is None:
            raise Exception("Could not get frame - Port number {0} is not configured".format(interface))

        info = komodo_drv.km_can_info_t()
        pkt = komodo_drv.km_can_packet_t()
        ret = 0
        data_in   = array('B', '\0' * 8) 

        start_time = time.time()

        # When a frame is received info.status changes to 0 and info.events should be 0.
        while ((info.status != 0) or (info.events != 0)):
            ret, info, pkt, data_in = komodo_drv.km_can_read(self._port[interface], data_in)
#            log.debug("Inside Komodo read loop - status={0}, events={1}, id={2}, dlc={3}".format(info.status, info.events, pkt.id, pkt.dlc))
            if (time.time() - start_time > timeout_sec):
                raise Exception("Get frame didn't receive any frame for {} seconds".format(timeout_sec))
    
        # can_frame = globals.CanFrame(pkt.id, pkt.extend_addr, pkt.remote_req, pkt.dlc, data_in.tolist())
        return can_frame




class Can_fw_pkt_t:
    def __init__ (self):
        self.dlc         = 0
        self.id          = 0
        self.data     = array('B', '\0' * 8)

""" Kommodo FW Update Adaptation Class """
class komodoCanDevice(object):
    def __init__(self):
        self.komodo_interface = KOMODO_IF_CAN_A
        self.bit_rate = KOMODO_IF_BIT_RATE_500KHZ
        self.port = [None, None]
        self.lock = threading.Lock()
        self.is_power_up = False

    def check_interface_range(self, interface):
        """ 
        check_interface_range -
        validate CAN port 
        """
        if (interface < KOMODO_IF_CAN_A) or (interface > KOMODO_IF_CAN_B):
            raise Exception("Wrong interface number: {0}".format(interface))

    def open_device(self, interface):
        """ 
        open_device -
        configure CAN port 
        """
        self.check_interface_range(interface)
        local_port = komodo_drv.km_open(interface)
        if local_port < 0:
          raise Exception( "Could not open port {0}, error {1}".format(interface, local_port) )
        
        if interface == KOMODO_IF_CAN_A:
            """ configure port A for write & read """
            komodo_drv.km_acquire(local_port, komodo_drv.KM_FEATURE_CAN_A_CONFIG | komodo_drv.KM_FEATURE_CAN_A_CONTROL | komodo_drv.KM_FEATURE_CAN_A_LISTEN)
            rate = komodo_drv.km_can_bitrate(local_port, komodo_drv.KM_CAN_CH_A, self.bit_rate)
        else:
            komodo_drv.km_acquire(local_port, komodo_drv.KM_FEATURE_CAN_B_CONFIG | komodo_drv.KM_FEATURE_CAN_B_CONTROL | komodo_drv.KM_FEATURE_CAN_B_LISTEN)
            rate = komodo_drv.km_can_bitrate(local_port, komodo_drv.KM_CAN_CH_B, self.bit_rate)
         
        if rate != self.bit_rate:
            raise Exception("Could'nt set bitrate to {0}, instead it's {1} KHz".format(self.bit_rate // 1000, rate // 1000))
    
        self.port[interface] = local_port
      
    def channel_open(self, interface):
      """ 
      channel_open - 
      power up CAN port 
      """
      self.check_interface_range(interface)
      if interface == KOMODO_IF_CAN_A:
          channel = komodo_drv.KM_CAN_CH_A
      else:
          channel = komodo_drv.KM_CAN_CH_B
      if self.port[interface] is None:
          raise Exception( "Port number {0} is not configured".format(interface))
      ret = komodo_drv.km_can_target_power(self.port[interface], channel, komodo_drv.KM_TARGET_POWER_ON)
      if ret != komodo_drv.KM_OK:
          raise Exception( "Could not power on channel A, error {0}".format(ret))

      ret = komodo_drv.km_enable(self.port[interface])
      if ret != komodo_drv.KM_OK:
          raise Exception("Could not enable CAN port, error {0}".format(ret))
      self.is_power_up = True
  
    def channel_close(self, interface):
        """ 
        channel_close - 
        power down CAN port 
        """
        self.check_interface_range(interface)
        if self.port[interface] is None:
            raise Exception("Port number {0} is not configured".format(interface))
        ret = komodo_drv.km_disable(self.port[interface])
        if ret != komodo_drv.KM_OK:
            raise Exception("Could not disable CAN port, error {0}"
                            .format(ret))        
        channel = komodo_drv.KM_CAN_CH_A if interface == KOMODO_IF_CAN_A else komodo_drv.KM_CAN_CH_B
        ret = komodo_drv.km_can_target_power(self.port[interface], channel, komodo_drv.KM_TARGET_POWER_OFF)
        if ret != komodo_drv.KM_OK:
            raise Exception("Could not power off channel A, error {0}".format(ret))
        self.is_power_up = False
  
    def transmit_obselete(self, interface, data, id):
        """ 
        transmit - 
        send CAN frame 
        """
        self.check_interface_range(interface)
        if not self.is_power_up:
            try:
                self.power_up(self.port[interface])
            except Exception:
                raise

            self.is_power_up = True
    
        pkt = km_can_packet_t()
        pkt.dlc   = len(data)
        pkt.id    = id
        """ Check if CAN address is extended (29 bits instead of 11 bits) """
        if id & 0x3FFFF800:
            pkt.extend_addr = True
    
        if self.port[interface] is None:
            raise Exception("Port number {0} is not configured".format(interface))

        channel = komodo_drv.KM_CAN_CH_A if interface == KOMODO_IF_CAN_A else komodo_drv.KM_CAN_CH_B

        ret, bytes = komodo_drv.km_can_write(self.port[interface], channel, 0, pkt, data)
        if ret < 0:
            raise Exception("Could not send packet, error {0}".format(ret))
        
    def transmit( self, interface, can_frame ):       

        self.check_interface_range(interface)
        if not self.is_power_up:
            raise Exception("Could not send frame - CAN Port is not powered up")

        if self.port[interface] is None:
            raise Exception("Could not send frame - Port number {0} is not configured".format(interface))

        pkt       = komodo_drv.km_can_packet_t()
        pkt.id    = can_frame.can_id
        pkt.dlc   = can_frame.dlc
        pkt.extend_addr = can_frame.ide_f
        pkt.remote_req  = can_frame.rtr_f

        # Convert data of type list to array for the komodo driver
        data = array('B', can_frame.data)

        self.lock.acquire()
        ret, bytes = komodo_drv.km_can_write(self.port[interface], interface, 0, pkt, data)
        self.lock.release()
        if ret < 0:
            raise Exception("Could not send frame, error {0}".format(ret))

    def receive(self, interface):
        """
        receive - 
        receive CAN frame
        """
        self.check_interface_range(interface)
        if self.port[interface] is None:
            raise Exception("Port number {0} is not configured".format(interface))
        
        info = komodo_drv.km_can_info_t()
        komodo_pkt = komodo_drv.km_can_packet_t()
        data_in = array('B', '\0' * 8) 
        komodo_rc = 0
        rc = 1
        self.lock.acquire()
        komodo_rc, info, komodo_pkt, data_in = komodo_drv.km_can_read( self.port[interface], data_in)
        self.lock.release()
        if komodo_rc:
            # pkt.can_id = komodo_pkt.id
            # pkt.dlc = komodo_pkt.dlc
            # pkt.data = data_in
            # flags = (pkt.extend_addr << EXTENDED_CAN_ID_LEN) | (pkt.remote_req << CAN_ID_RTR_BIT)
            # pkt.is_extended = pkt.extend_addr
            # pkt.rtr_f =  pkt.remote_req
            # rc = 0
            return globals.canBusFrame( komodo_pkt.id , komodo_pkt.dlc, data_in, (komodo_pkt.extend_addr << globals.EXTENDED_CAN_ID_LEN) | (komodo_pkt.remote_req << globals.CAN_ID_RTR_BIT) ) 
          
        return str(rc)    
    
    def get_frame(self, interface, timeout_sec=60):
        self._check_interface_range(interface)
        if not self._is_power_up:
            raise Exception("Could not get frame - CAN Port is not powered up")

        if self._port[interface] is None:
            raise Exception("Could not get frame - Port number {0} is not configured".format(interface))

        info = komodo_drv.km_can_info_t()
        pkt = komodo_drv.km_can_packet_t()
        ret = 0
        data_in   = array('B', '\0' * 8) 

        start_time = time.time()

        # When a frame is received info.status changes to 0 and info.events should be 0.
        while ((info.status != 0) or (info.events != 0)):
            ret, info, pkt, data_in = komodo_drv.km_can_read(self._port[interface], data_in)
#            log.debug("Inside Komodo read loop - status={0}, events={1}, id={2}, dlc={3}".format(info.status, info.events, pkt.id, pkt.dlc))
            if (time.time() - start_time > timeout_sec):
                raise Exception("Get frame didn't receive any frame for {} seconds".format(timeout_sec))
    
        

        # can_frame = canbus_manager.CanFrame(pkt.id, pkt.extend_addr, pkt.remote_req, pkt.dlc, data_in.tolist())
        return can_frame

  


if __name__ == "__main__":
    KomodoServer()