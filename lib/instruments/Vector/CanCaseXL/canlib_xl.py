# To change this template, choose Tools | Templates
# and open the template in the editor.

import ctypes
import time

XLuint64=ctypes.c_ulonglong
XLaccess=XLuint64
XLstatus=ctypes.c_short
XLporthandle=ctypes.c_long
XLeventtag=ctypes.c_ubyte



XL_DEFAULT_APP_NAME = "QA-ATE"


MAX_MSG_LEN             =   8

# Hardware types
XL_HWTYPE_NONE          =   0
XL_ACTIVATE_RESET_CLOCK =   8
XL_HWTYPE_CANCARDXL     =   15
XL_HWTYPE_CANCASEXL     =   21
XL_HWTYPE_VN1630        =   57
XL_HWTYPE_VN1640        =   59

XL_DEFUALT_HWTYPE       =   XL_HWTYPE_VN1630

# Hardware bus suport
XL_BUS_TYPE_NONE            = 0x00000000
XL_BUS_TYPE_CAN             = 0x00000001
XL_BUS_TYPE_LIN             = 0x00000002
XL_BUS_TYPE_FLEXRAY         = 0x00000004
XL_BUS_TYPE_AFDX            = 0x00000008 # former BUS_TYPE_BEAN
XL_BUS_TYPE_MOST            = 0x00000010
XL_BUS_TYPE_DAIO            = 0x00000040 # IO cab/piggy
XL_BUS_TYPE_J1708           = 0x00000100
XL_BUS_TYPE_ETHERNET        = 0x00001000

# interface version for our events
XL_INTERFACE_VERSION_V2 =   2                                                                             
XL_INTERFACE_VERSION_V3 =   3 
XL_INTERFACE_VERSION_V4 =   4           
# current version
XL_INTERFACE_VERSION    =   XL_INTERFACE_VERSION_V3

XL_INVALID_PORTHANDLE   =   -1

XL_ACTIVATE_NONE        =   0
XL_ACTIVATE_RESET_CLOCK =   8

# ------------------------------------------------------------------------------
# Transceiver types
# ------------------------------------------------------------------------------
# CAN Cab

XL_TRANSCEIVER_TYPE_NONE                = 0x0000
XL_TRANSCEIVER_TYPE_CAN_251             = 0x0001 # Low Speed
XL_TRANSCEIVER_TYPE_CAN_252             = 0x0002 # Low Speed
XL_TRANSCEIVER_TYPE_CAN_SWC             = 0x0006 # Single wire
XL_TRANSCEIVER_TYPE_CAN_1041            = 0x0010 # hi speed
XL_TRANSCEIVER_TYPE_PB_CAN_1051_CAP     = 0x013F # TJA 1051, capacitive isolated
XL_TRANSCEIVER_TYPE_DEFAULT             = XL_TRANSCEIVER_TYPE_PB_CAN_1051_CAP


# ------------------------------------------------------------------------------
# Transceiver Operation Modes
# ------------------------------------------------------------------------------
XL_TRANSCEIVER_LINEMODE_NA               = 0x0000
XL_TRANSCEIVER_LINEMODE_TWO_LINE         = 0x0001
XL_TRANSCEIVER_LINEMODE_CAN_H            = 0x0002
XL_TRANSCEIVER_LINEMODE_CAN_L            = 0x0003
XL_TRANSCEIVER_LINEMODE_SWC_SLEEP        = 0x0004  #  SWC Sleep Mode.
XL_TRANSCEIVER_LINEMODE_SWC_NORMAL       = 0x0005  #  SWC Normal Mode.
XL_TRANSCEIVER_LINEMODE_SWC_FAST         = 0x0006  #  SWC High-Speed Mode.
XL_TRANSCEIVER_LINEMODE_SWC_WAKEUP       = 0x0007  #  SWC Wakeup Mode.
XL_TRANSCEIVER_LINEMODE_SLEEP            = 0x0008
XL_TRANSCEIVER_LINEMODE_NORMAL           = 0x0009
XL_TRANSCEIVER_LINEMODE_STDBY            = 0x000a  #  Standby for those who support it
XL_TRANSCEIVER_LINEMODE_TT_CAN_H         = 0x000b  #  truck & trailer: operating mode single wire using CAN high
XL_TRANSCEIVER_LINEMODE_TT_CAN_L         = 0x000c  #  truck & trailer: operating mode single wire using CAN low
XL_TRANSCEIVER_LINEMODE_EVA_00           = 0x000d  #  CANcab Eva 
XL_TRANSCEIVER_LINEMODE_EVA_01           = 0x000e  #  CANcab Eva 
XL_TRANSCEIVER_LINEMODE_EVA_10           = 0x000f  #  CANcab Eva 
XL_TRANSCEIVER_LINEMODE_EVA_11           = 0x0010  #  CANcab Eva 




# ------------------------------------------------------------------------------
# s_xl_event tag flags option 
# ------------------------------------------------------------------------------

XL_CAN_MSG_FLAG_ERROR_FRAME     = 0x01      # The event is an error frame (rx*). 
XL_CAN_MSG_FLAG_OVERRUN         = 0x02      # Overrun in Driver or CAN Controller, An overrun occurred, events have been lost (rx, tx*). 
XL_CAN_MSG_FLAG_REMOTE_FRAME    = 0x10      # Message Transmitted, The event is a remote frame (rx, tx*). 
XL_CAN_MSG_FLAG_TX_COMPLETED    = 0x40      # Notification for successful message transmission (rx*). 
XL_CAN_MSG_FLAG_TX_REQUEST      = 0x80      # Request notification for message transmission (rx*). 
XL_CAN_MSG_FLAG_NERR            = 0x04      # Line Error on Lowspeed, The transceiver reported an error while the message was received (rx*). 
XL_CAN_MSG_FLAG_WAKEUP          = 0x08      # High Voltage Message on Single Wire CAN, High voltage message for Single Wire (rx, tx*). To flush the queue
                                            # and transmit a high voltage message combine the flags XL_CAN_MSG_FLAG_WAKEUP and XL_CAN_MSG_FLAG_OVERRUN by a binary OR. 
XL_CAN_MSG_FLAG_SRR_BIT_DOM     = 0x0200    # SRR bit in CAN message is dominant, SSR (Substitute Remote Request) bit in CAN message is set (rx, tx*).  



XL_NO_COMMAND               = 0
XL_RECEIVE_MSG              = 1
XL_CHIP_STATE               = 4
XL_TRANSCEIVER              = 6
XL_TIMER                    = 8
XL_TRANSMIT_MSG             =10
XL_SYNC_PULSE               =11
XL_APPLICATION_NOTIFICATION =15

#//for LIN we have special events
XL_LIN_MSG                  =20
XL_LIN_ERRMSG               =21
XL_LIN_SYNCERR              =22
XL_LIN_NOANS                =23
XL_LIN_WAKEUP               =24
XL_LIN_SLEEP                =25
XL_LIN_CRCINFO              =26

#// for D/A IO bus
XL_RECEIVE_DAIO_DATA        = 32
XL_SUCCESS                  = 0

XL_CANBUS_DEFAULT_BITRATE_500KHZ = 500000


class s_xl_can_msg(ctypes.Structure):
    _fields_ = [("id", ctypes.c_ulong),
                ("flags", ctypes.c_ushort),
                ("dlc", ctypes.c_ushort),
                ("res1", XLuint64),
                ("data", ctypes.c_ubyte*MAX_MSG_LEN)]

class s_xl_chip_state(ctypes.Structure):
    _fields_ = [("busStatus", ctypes.c_ubyte),
                ("txErrorCounter", ctypes.c_ubyte),
                ("rxErrorCounter", ctypes.c_ubyte),
                ("chipStatte", ctypes.c_ubyte),
                ("flags", ctypes.c_uint)]

class s_xl_lin_crc_info(ctypes.Structure):
    _fields_ = [("id", ctypes.c_ubyte),
                ("flags", ctypes.c_ubyte)]

class s_xl_lin_wake_up(ctypes.Structure):
    _fields_ = [("flag", ctypes.c_ubyte)]

class s_xl_lin_no_ans(ctypes.Structure):
    _fields_ = [("id", ctypes.c_ubyte)]    #

class s_xl_lin_sleep(ctypes.Structure):
    _fields_ = [("flag", ctypes.c_ubyte)]

class s_xl_lin_msg(ctypes.Structure):
    _fields_ = [("id", ctypes.c_ubyte),
                ("dlc", ctypes.c_ubyte),
                ("flags", ctypes.c_ushort),
                ("data", ctypes.c_ubyte*8),
                ("crc", ctypes.c_ubyte)]

class s_xl_lin_msg_api(ctypes.Union):
    _fields_ = [("s_xl_lin_msg", s_xl_lin_msg),
                ("s_xl_lin_no_ans", s_xl_lin_no_ans),
                ("s_xl_lin_wake_up", s_xl_lin_wake_up),
                ("s_xl_lin_sleep", s_xl_lin_sleep),
                ("s_xl_lin_crc_info", s_xl_lin_crc_info)]

class s_xl_sync_pulse(ctypes.Structure):
    _fields_ = [("pulseCode", ctypes.c_ubyte),
                ("time", XLuint64)]

class s_xl_daio_data(ctypes.Structure):
    _fields_ = [("flags", ctypes.c_ubyte),
                ("timestamp_correction", ctypes.c_uint),
                ("mask_digital", ctypes.c_ubyte),
                ("value_digital", ctypes.c_ubyte),
                ("mask_analog", ctypes.c_ubyte),
                ("reserved", ctypes.c_ubyte),
                ("value_analog", ctypes.c_ubyte*4),
                ("pwm_frequency", ctypes.c_uint),
                ("pwm_value", ctypes.c_ubyte),
                ("reserved1", ctypes.c_uint),
                ("reserved2", ctypes.c_uint)]

class s_xl_transceiver(ctypes.Structure):
    _fields_ = [("event_reason", ctypes.c_ubyte),
                ("is_present", ctypes.c_ubyte)]

class s_xl_tag_data(ctypes.Union):
    _fields_ = [("msg", s_xl_can_msg),
                ("chipState", s_xl_chip_state),
                ("linMsgApi", s_xl_lin_msg_api),
                ("syncPulse", s_xl_sync_pulse),
                ("daioData", s_xl_daio_data),
                ("transceiver", s_xl_transceiver)]

class s_xl_event(ctypes.Structure):
    _fields_ =[ ("tag", XLeventtag),
                ("chanIndex", ctypes.c_ubyte),
                ("transId", ctypes.c_ushort),
                ("portHandle", ctypes.c_ushort),
                ("reserved", ctypes.c_ushort),
                ("timeStamp", XLuint64),
                ("tagData", s_xl_tag_data)]

XLevent=s_xl_event



#/////////////////////////////////////////////////////////////////////////////////////////////////////////
#// IO XL API
#/////////////////////////////////////////////////////////////////////////////////////////////////////////


class s_xl_io_digital_data(ctypes.Structure): 
    _fields_ =[ ("digitalInputData", ctypes.c_int32) ]

XL_IO_DIGITAL_DATA = s_xl_io_digital_data


class s_xl_io_analog_data(ctypes.Structure):
    _fields_ =[ ("measuredAnalogData0", ctypes.c_int32),
                ("measuredAnalogData0", ctypes.c_int32),
                ("measuredAnalogData0", ctypes.c_int32),
                ("measuredAnalogData0", ctypes.c_int32) ]

XL_IO_ANALOG_DATA = s_xl_io_analog_data

class s_xl_daio_piggy_data_union(ctypes.Union):
        _fields_ =[ ("digital", XL_IO_DIGITAL_DATA),
                    ("analog", XL_IO_ANALOG_DATA) ]



class s_xl_daio_piggy_data(ctypes.Structure): 
    _fields_ =[ ("daioEvtTag", ctypes.c_uint32),
                ("triggerType", ctypes.c_uint32),
                ("data", s_xl_daio_piggy_data_union)]

class s_xl_digital_data(ctypes.Structure): 
    _fields_ =[ ("portMask", ctypes.c_int32),
                ("type", ctypes.c_int32)        # Use defines XL_DAIO_TRIGGER_TYPE_xxx from below
               ]


class s_xl_trigger_type_params(ctypes.Union):
    _fields_ =[ ("cycleTime", ctypes.c_int32), # specify time in microseconds
                ("digital", s_xl_digital_data) ]

 
# // defines for xlIoSetTriggerMode
class s_xl_daio_trigger_mode(ctypes.Structure):

    _fields_ =[ ("portTypeMask", ctypes.c_int32),   # Use defines XL_DAIO_PORT_TYPE_MASK_xxx. Unused for VN1630/VN1640.
                ("triggerType", ctypes.c_int32),   # Use defines XL_DAIO_TRIGGER_TYPE_xxx from above
                ("triggerTypeParams", s_xl_trigger_type_params)]

XLdaioTriggerMode = s_xl_daio_trigger_mode



# // defines for xlIoConfigurePorts 
class xl_daio_set_port(ctypes.Structure):

    _fields_ =[ ("portType", ctypes.c_int32),   # Only one signal group is allowed. One of the defines XL_DAIO_PORT_TYPE_MASK_*
                ("portMask", ctypes.c_int32),   # Mask of affected ports.
                ("portFunction", ctypes.c_int32 * 8), # Special function of port. One of the defines XL_DAIO_PORT_DIGITAL_* or XL_DAIO_PORT_ANALOG_*
                ("reserved", ctypes.c_int32 * 8) ] # Set this parameters to zero!
                
XLdaioSetPort = xl_daio_set_port


# global IO defines
# type defines for XLdaioTriggerMode.portTypeMask 
XL_DAIO_PORT_TYPE_MASK_DIGITAL          = 0x01
XL_DAIO_PORT_TYPE_MASK_ANALOG           = 0x02

# type defines for XLdaioTriggerMode.triggerType 
XL_DAIO_TRIGGER_TYPE_CYCLIC             = 0x01
XL_DAIO_TRIGGER_TYPE_PORT               = 0x02

XL_DAIO_TRIGGER_TYPE_RISING          = 0x01
XL_DAIO_TRIGGER_TYPE_FALLING         = 0x02
XL_DAIO_TRIGGER_TYPE_BOTH            = 0x03

# for digital ports:
XL_DAIO_PORT_DIGITAL_IN              = 0x00
XL_DAIO_PORT_DIGITAL_PUSHPULL        = 0x01
XL_DAIO_PORT_DIGITAL_OPENDRAIN       = 0x02
# for analog ports:
XL_DAIO_PORT_ANALOG_IN               = 0x00
XL_DAIO_PORT_ANALOG_OUT              = 0x01
XL_DAIO_PORT_ANALOG_DIFF             = 0x02
XL_DAIO_PORT_ANALOG_OFF              = 0x03

# defines for xlIoSetDigOutLevel
XL_DAIO_DO_LEVEL_0V                  = 0
XL_DAIO_DO_LEVEL_5V                  = 5
XL_DAIO_DO_LEVEL_12V                 = 12

# defines for portMask
XL_DAIO_PORT_MASK_DIGITAL_D0         = 0x01
XL_DAIO_PORT_MASK_DIGITAL_D1         = 0x02
XL_DAIO_PORT_MASK_DIGITAL_D2         = 0x04
XL_DAIO_PORT_MASK_DIGITAL_D3         = 0x08
XL_DAIO_PORT_MASK_DIGITAL_D4         = 0x10
XL_DAIO_PORT_MASK_DIGITAL_D5         = 0x20
XL_DAIO_PORT_MASK_DIGITAL_D6         = 0x40
XL_DAIO_PORT_MASK_DIGITAL_D7         = 0x80

#// defines for XLdaioAnalogParams::portMask
XL_DAIO_PORT_MASK_ANALOG_A0          = 0x01
XL_DAIO_PORT_MASK_ANALOG_A1          = 0x02
XL_DAIO_PORT_MASK_ANALOG_A2          = 0x04
XL_DAIO_PORT_MASK_ANALOG_A3          = 0x08

# event ids
XL_DAIO_EVT_ID_DIGITAL               = XL_DAIO_PORT_TYPE_MASK_DIGITAL
XL_DAIO_EVT_ID_ANALOG                = XL_DAIO_PORT_TYPE_MASK_ANALOG



class vxlapi():

    def __init__(self):
        self.candll=ctypes.windll.LoadLibrary("vxlapi.dll")
        
    def open_driver(self):
        ok = self.candll.xlOpenDriver()
        return ok
    
    def get_appl_config(self, appname=XL_DEFAULT_APP_NAME, channel=0, bustype=XL_BUS_TYPE_CAN):
        app_name=ctypes.c_char_p(appname)
        app_channel=ctypes.c_uint(channel)
        p_hw_type=ctypes.pointer(ctypes.c_uint())
        p_hw_index=ctypes.pointer(ctypes.c_uint())
        p_hw_channel=ctypes.pointer(ctypes.c_uint())
        bus_type=ctypes.c_uint(bustype)
        ok=self.candll.xlGetApplConfig(app_name, app_channel, p_hw_type, p_hw_index, p_hw_channel, bus_type)
        return ok, p_hw_type.contents, p_hw_index.contents, p_hw_channel.contents

    def set_appl_config(self, appname, appchannel, hwtype, hwindex,  hwchannel, bustype):
        self.candll.xlSetApplConfig.argtypes=[ctypes.c_char_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        ok=self.candll.xlSetApplConfig(appname, appchannel, hwtype, hwindex, hwchannel, bustype)
        return ok


    def set_channel_mode(self,port_handle, access_mask =  XLaccess(1), tx = 1 , txrq = 0):
        self.candll.xlCanSetChannelMode.argtypes=[XLporthandle, XLaccess, ctypes.c_int, ctypes.c_int]
        ok=self.candll.xlCanSetChannelMode(port_handle, access_mask, tx, txrq )
        return ok

    def set_channel_transceiver(self, port_handle, access_mask =  XLaccess(1), can_type = XL_TRANSCEIVER_TYPE_DEFAULT, line_mode = XL_TRANSCEIVER_LINEMODE_NORMAL ):

        self.candll.xlCanSetChannelTransceiver.argtypes=[ctypes.POINTER(XLporthandle), XLaccess, ctypes.c_int, ctypes.c_int, ctypes.c_int]
        ok=self.candll.xlCanSetChannelTransceiver(port_handle , access_mask, can_type , line_mode, 0)
        return ok
        
    def get_channel_index(self, hw_type=XL_DEFUALT_HWTYPE, hw_index=0, hw_channel=0):
        self.candll.xlGetChannelIndex.argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int]
        channel_index=self.candll.xlGetChannelIndex(hw_type, hw_index, hw_channel)
        return channel_index

    def get_channel_mask(self, hwtype=XL_DEFUALT_HWTYPE, hwindex=0, hwchannel=0):
        self.candll.xlGetChannelMask.argtypes=[ctypes.c_int, ctypes.c_int, ctypes.c_int]
        mask=self.candll.xlGetChannelMask(hwtype, hwindex, hwchannel)
        # return ctypes.c_ulonglong(mask)
        return XLaccess(mask)
    
    def open_port(self, port_handle=XLporthandle(XL_INVALID_PORTHANDLE), user_name=XL_DEFAULT_APP_NAME, access_mask=XLaccess(1), permission_mask=XLaccess(1), rx_queue_size=256, interface_version=XL_INTERFACE_VERSION, bus_type=XL_BUS_TYPE_CAN):
        self.candll.xlOpenPort.argtypes=[ctypes.POINTER(XLporthandle), ctypes.c_char_p, XLaccess, ctypes.POINTER(XLaccess), ctypes.c_uint, ctypes.c_uint, ctypes.c_uint]
        ok=self.candll.xlOpenPort(port_handle, user_name, access_mask, permission_mask, rx_queue_size, interface_version, bus_type)
        return ok, port_handle, permission_mask

    def activate_channel(self, port_handle, access_mask=XLaccess(1), bustype=XL_BUS_TYPE_CAN, flags=XL_ACTIVATE_RESET_CLOCK):
        self.candll.xlActivateChannel.argtypes=[XLporthandle, XLaccess, ctypes.c_uint, ctypes.c_uint]
        ok=self.candll.xlActivateChannel(port_handle, access_mask, bustype, flags)
        return ok

    def close_driver(self):
        ok=self.candll.xlCloseDriver()
        return  ok

    def deactivate_channel(self, port_handle=XLporthandle(XL_INVALID_PORTHANDLE), access_mask=XLaccess(1)):
        self.candll.xlDeactivateChannel.argtypes=[XLporthandle, XLaccess]
        ok=self.candll.xlDeactivateChannel(port_handle, access_mask)
        return ok

    def close_port(self, port_handle=XLporthandle(XL_INVALID_PORTHANDLE)):
        self.candll.xlClosePort.argtypes=[XLporthandle]
        ok=self.candll.xlClosePort(port_handle)
        return ok

    def receive(self, port_handle, event_count, event_list):
        self.candll.xlReceive.argtypes=[XLporthandle, ctypes.POINTER(ctypes.c_uint), ctypes.POINTER(XLevent)]
        #ev=XLevent(0)
        #print port_handle, event_count, event_list
        ok=self.candll.xlReceive(port_handle, ctypes.byref(event_count), ctypes.byref(event_list))
        #print event_list
        return ok

    def get_event_string(self, ev):
        self.candll.xlGetEventString.argtypes=[ctypes.POINTER(XLevent)]
        self.candll.xlGetEventString.restype=ctypes.c_char_p
        rec_string=self.candll.xlGetEventString(ctypes.pointer(ev))
        return rec_string

    def can_set_channel_bitrate(self, port_handle, amask, bitrate):
        self.candll.xlCanSetChannelBitrate.argtypes=[XLporthandle, XLaccess, ctypes.c_ulong]
        ok= self.candll.xlCanSetChannelBitrate(port_handle, amask, ctypes.c_ulong(bitrate))
        return ok

    def can_transmit(self, port_handle, amask, message_count, p_messages):
        self.candll.xlCanTransmit.argtypes=[XLporthandle, XLaccess, ctypes.POINTER(ctypes.c_uint), ctypes.c_void_p]
        ok = self.candll.xlCanTransmit(port_handle, amask, ctypes.byref(message_count), ctypes.byref(p_messages))
        return ok

    def get_error_string(self, err):
        self.candll.xlGetErrorString.argtypes=[XLstatus]
        self.candll.xlGetErrorString.restype=ctypes.c_char_p
        err_string = self.candll.xlGetErrorString(err)
        return err_string


if __name__ == "__main__":

    # import canlib_xl 
    import ctypes
    import msvcrt
    import time

    def test_vector_driver():

        can = vxlapi()
        rc = can.open_driver()
        if rc != 0:
            raise Exception("Error initilize the driver")

        chan_mask = {}
        #mask = XLaccess(0)
        #mask = can.get_channel_mask( hwchannel = 0 )
        chan_mask[1] = can.get_channel_mask( hwchannel = 1 )
        chan_mask[2] = can.get_channel_mask( hwchannel = 2 )

        mask = XLaccess( chan_mask[1].value | chan_mask[2].value )
        # mask = XLaccess(0xf)
        print "Mask is {}".format(mask)
        ok, phandle, pmask= can.open_port( access_mask = mask, permission_mask = mask )
        if not(ok):

            ok = can.set_channel_mode( phandle , mask, 0, 0)

            ok = can.activate_channel(phandle , access_mask = mask )
            print ok
        
        ok = 0
        while not(ok):
            time.sleep(0.01)
            
            data = [1, 2, 3, 4, 5, 6]
            event_msg=XLevent(0)
            event_msg.tag=XL_TRANSMIT_MSG
            event_msg.tagData.msg.id= 4
            event_msg.tagData.msg.flags = 0
            dlc=len(data)
            for n in range(0, dlc):
                event_msg.tagData.msg.data[n]=data[n]
            event_msg.tagData.msg.dlc=dlc
            event_count=ctypes.c_uint(1)




            ok = can.can_transmit(phandle, chan_mask[1], event_count, event_msg)
            err_string = can.get_error_string(ok)


            event_count=ctypes.c_uint(1)
            #print phandle, event_count
            event_list=XLevent(0)
 
            ok = can.receive( phandle, event_count, event_list)
            if ok:
                rec_string=can.get_error_string(ok)
            else:
                rec_string=can.get_event_string(event_list)


            ok = can.can_transmit(phandle, chan_mask[2], event_count, event_msg)
            err_string = can.get_error_string(ok)

            print err_string

            #can.can_transmit(self, port_handle, amask, message_count, p_messages)

            #ok = can.send_msg([1, 2, 3, 4], 4)
            #msg = can.get_msg()



    test_vector_driver()
    #raise Exception("Error")

