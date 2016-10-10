
import sys

if __name__ == "__main__":
    sys.path.append('c:/qa')

import logging, os, time, sys
from lib import globals
import ctypes, re
from lib.instruments.Vector.CanCaseXL import canlib_xl
import threading

log = logging.getLogger(__name__)

class vectorCanDevice():

    def __init__(self):
        self.driver=canlib_xl.vxlapi()
        self.chan_mask = {}
        self.bus_type = canlib_xl.XL_BUS_TYPE_CAN
        self.lock = threading.Lock()

        self.rx_queue_size = 256

    def open_device( self , ports ):
        
        self.driver.open_driver()
        if type(ports) is list:
            for prt in ports:
                self.chan_mask[prt] = self.driver.get_channel_mask( hwchannel = prt )
        elif type(ports) is int:
            self.chan_mask[ports] = self.driver.get_channel_mask( hwchannel = port_idx )

        # build mask from all required channels
        self.mask = canlib_xl.XLaccess(sum([x.value for x in self.chan_mask.itervalues()]))

        # Set the option to send to all channels
        self.chan_mask[0xff] = self.mask

        ok, self.phandle, self.pmask = self.driver.open_port( access_mask = self.mask, permission_mask = self.mask, rx_queue_size = self.rx_queue_size, bus_type = self.bus_type )
        if ok  != canlib_xl.XL_SUCCESS:
            raise Exception(" Open port raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

    def channel_open(self, port, bit_rate  = 500000 ):

        ok = self.driver.can_set_channel_bitrate(self.phandle, self.chan_mask[port], bit_rate)
        if ok  != canlib_xl.XL_SUCCESS:
            raise Exception("can_set_channel_bitrate raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

        ok = self.driver.set_channel_mode ( self.phandle,  self.chan_mask[port], 0, 0)
        if ok  != canlib_xl.XL_SUCCESS:
            raise Exception("can_set_channel_bitrate raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )


        ok = self.driver.activate_channel(self.phandle , access_mask = self.chan_mask[port], bustype = self.bus_type )
        if ok  != canlib_xl.XL_SUCCESS:
            raise Exception("activate_channel raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

    def channel_close( self, port ):
        ok = self.driver.deactivate_channel( self.phandle, self.chan_mask[port] )
        if ok  != canlib_xl.XL_SUCCESS:
            raise Exception("activate_channel raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

    def device_close( self ):
        self.driver.close_port(self.phandle)
        self.driver.close_driver()

    #def transmit (self, port, data, id):
    def transmit (self, port, can_frame):

        event_count = ctypes.c_uint(1)

        event_msg = canlib_xl.XLevent(0)
        event_msg.tag = canlib_xl.XL_TRANSMIT_MSG
        event_msg.tagData.msg.id = can_frame.can_id
        event_msg.tagData.msg.flags = canlib_xl.XL_CAN_MSG_FLAG_REMOTE_FRAME if (can_frame.rtr_f) else 0 
        dlc = len(can_frame.data)
        for i, n in enumerate(can_frame.data):
            event_msg.tagData.msg.data[i] = n

        event_msg.tagData.msg.dlc = can_frame.dlc

        # clear all api flags
        if not(can_frame.ide_f):
            event_msg.tagData.msg.id = can_frame.can_id & 0x7FF

        # event_msg.tagData.msg.id = can_frame.can_id & 0x3FFFFFFF
        self.lock.acquire()
        ok = self.driver.can_transmit(self.phandle, self.chan_mask[port], event_count, event_msg)
        self.lock.release()
        if ok  != canlib_xl.XL_SUCCESS:
            raise Exception("can_transmit raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )
    
    def transmit_ex( self, port, msgs ):

        total_msg = 1
        if isinstance(msgs, list):
            total_msg = len( msgs )
        # event_msg = (total_msg * XLevent)()

        events = (XLevent * total_msg)()
        event_msg = ctypes.cast(events, ctypes.POINTER(XLevent) )

        for id, msg in enumerate(msgs):
            event_msg[id].tag = canlib_xl.XL_TRANSMIT_MSG
            event_msg[id].tagData.msg.id= msg[0]
            event_msg[id].tagData.msg.flags=0
            dlc=len(msg)
            #for n in range(0, dlc):
            #    event_msg[id].tagData.msg.data[n]=msg[1][n]
            event_msg[id].tagData.msg.data = msg
            event_msg[id].tagData.msg.dlc=dlc

        event_count = ctypes.c_uint(total_msg)

        ok = self.driver.can_transmit(self.phandle, self.chan_mask[port] , event_count, events)
        if ok  != canlib_xl.XL_SUCCESS:
            raise Exception("can_transmit raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

    def receive(self, port = None):

        event_count = ctypes.c_uint(1)
        #print phandle, event_count
        event_list=canlib_xl.XLevent()

        self.lock.acquire()
        ok = self.driver.receive(self.phandle, event_count, event_list)
        self.lock.release()

        if ok:
            rec_string=self.driver.get_error_string(ok)
        else:
            rec_string=self.driver.get_event_string(event_list)

            dlc = event_list.tagData.msg.dlc
            data = []
            for i in range(0, dlc):
                data.append( event_list.tagData.msg.data[i] )

            flags = 0
            # Verify Remote
            if event_list.tagData.msg.flags & canlib_xl.XL_CAN_MSG_FLAG_REMOTE_FRAME:
                flags = flags | globals.CAN_ID_RTR_FLAG

            # Verify Extednded flags
            if (event_list.tagData.msg.id & globals.CAN_ID_IDE_FLAG):
                flags = flags | globals.CAN_ID_IDE_FLAG


            # initileize for default
            if flags == 0:
                flags = None

            return globals.canBusFrame( event_list.tagData.msg.id , dlc, data, flags ) 

        return rec_string
    

class vectorDaioDevice(vectorCanDevice):

    def __init__(self):
        self.driver=vxlapi()
        self.chan_mask = {}
        self.bus_type = XL_BUS_TYPE_DAIO
        self.rx_queue_size = 1024

    def channel_open(self, port ):

        trigMode = XLdaioTriggerMode()

        # XLstatus            xlStatus = XL_ERROR;

        # Set Trigger mode for IO-Piggy

        trigMode.portTypeMask = XL_DAIO_PORT_TYPE_MASK_ANALOG;

        if g_ioPiggyDigitalTriggerCyclic:
            trigMode.portTypeMask |= XL_DAIO_PORT_TYPE_MASK_DIGITAL

        trigMode.triggerType = XL_DAIO_TRIGGER_TYPE_CYCLIC;
        trigMode.param.cycleTime = g_frequency * 1000;

        ok = self.driver.set_channel_mode(self.phandle , self.chan_mask[port], 0, 0)
        if ok  != XL_SUCCESS:
            raise Exception("set_channel_mode raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )


        ok = self.driver.activate_channel(self.phandle , access_mask = self.chan_mask[port], bustype = self.bus_type )
        if ok  != XL_SUCCESS:
            raise Exception("activate_channel raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

    def channel_close( self, port ):
        ok = self.driver.deactivate_channel( self.phandle, self.chan_mask[port] )
        if ok  != XL_SUCCESS:
            raise Exception("activate_channel raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

    def device_close( self ):
        self.driver.close_port(self.phandle)
        self.driver.close_driver()

    def transmit (self, port, data, id):

        event_msg=XLevent(0)
        event_msg.tag=XL_TRANSMIT_MSG
        event_msg.tagData.msg.id=id
        event_msg.tagData.msg.flags=0
        dlc=len(data)
        for n in range(0, dlc):
            event_msg.tagData.msg.data[n]=data[n]
        event_msg.tagData.msg.dlc=dlc
        event_count=ctypes.c_uint(1)

        ok = self.driver.can_transmit(self.phandle, self.chan_mask[port], event_count, event_msg)
        if ok  != XL_SUCCESS:
            raise Exception("activate_channel raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )
    
    def transmit_ex( self, port, msgs ):

        total_msg = len( msgs )
        # event_msg = (total_msg * XLevent)()

        events = (XLevent * total_msg)()
        event_msg = ctypes.cast(events, ctypes.POINTER(XLevent) )

        for id, msg in enumerate(msgs):
            event_msg[id].tag = XL_TRANSMIT_MSG
            event_msg[id].tagData.msg.id= msg[0]
            event_msg[id].tagData.msg.flags=0
            dlc=len(msg[1])
            for n in range(0, dlc):
                event_msg[id].tagData.msg.data[n]=msg[1][n]
            event_msg[id].tagData.msg.dlc=dlc

        event_count=ctypes.c_uint(total_msg)

        ok = self.driver.can_transmit(self.phandle, self.mask, event_count, events)
        if ok  != XL_SUCCESS:
            raise Exception("activate_channel raised error : {}, {}".format( ok, self.driver.get_error_string(ok) ) )

    def receive(self):
        event_count=ctypes.c_uint(1)
        #print phandle, event_count
        event_list=XLevent(0)
        ok = self.driver.receive(self.phandle, event_count, event_list)
        if ok:
            rec_string=self.driver.get_error_string(ok)
        else:
            rec_string=self.driver.get_event_string(event_list)
        return rec_string
    



if __name__ == "__main__":

    # import canlib_xl 
    import ctypes
    import msvcrt
    import time

    def test_can_device():
        

        can = vectorCanDevice()

        can.open_device( [1,2] )

        can.channel_open( 1 )
        can.channel_open( 2 )
        
        can_frame = globals.canBusFrame( 0x402, 8 , [0]*8, flags = globals.CAN_ID_RTR_FLAG )

        i= 0
        while 1:
            
            can.transmit(1  , can_frame )
            ddd = can.receive()
            if type(ddd) is globals.canBusFrame:
                i += 1
                print "Recevied frame {}, can_id {}, dlc {}".format(i, ddd.can_id, ddd.dlc )




        # can_frame = globals.canBusFrame( 0x1C01, 8 , [0]*8 )
        # can.transmit(2  , can_frame ) 
        rate = 500
        rate_fps_ms = 500 / ( 60.0 * 1000.0 )


        """
        try:
            ddd = can.receive()
        except Exception as e:
            pass
        """

        frames = 100000
        for i in xrange(frames):

            start = time.time()
            if i % 2 == 0:
                can_frame = globals.canBusFrame( 0x402, 8 , [0]*8, flags = globals.CAN_ID_RTR_FLAG )
            else:
                can_frame = globals.canBusFrame( 0x401, 8 , [0]*8, flags = (globals.CAN_ID_RTR_FLAG | globals.CAN_ID_IDE_FLAG) )

            can.transmit(1  , can_frame )

            sleep_time = rate_fps_ms - (time.time() - start)
            time.sleep( sleep_time if sleep_time > 0 else 0 )



        print "Total frames {}, time {}".format( frames , time.time() - start )


        try:

            can.transmit(2  , can_frame )
            time.sleep(0.5)
            ddd = can.receive()

        except Exception as e:
            raise e
        finally:
            can.channel_close(1)
            can.channel_close(2)
            can.device_close()

    test_can_device()
    # raise Exception("Exit")
