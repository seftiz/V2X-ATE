
import komodo_if
from komodo_if import Komodo

import time
from array import array
import signal
import sys

DVI_KOMODO_INTERFACE = komodo_if.KOMODO_IF_CAN_B

# hard braking event response CAN ID
HBE_RESPONSE_ID = 0x10B22080
# hard braking event response CAN frame
HBE_RESPONSE_DATA = array('B', [0x00, 0x00, 0xFF])

# declaration of komodo box variable
kom_dev = komodo_if.Komodo()

# list of tuples, each tuple consists of:
#    1. CAN ID : integer
#    2. CAN data : array of bytes
hbe_list = []

# Activate display command
hbe_list.append( (0x10AC0097, array('B', [0x00, 0x04, 0x16, 0x02])) )
# Display icon command
hbe_list.append( (0x10AC0097, array('B', [0x00, 0x06, 0x16, 0x02])) )
# Deactivate display command
hbe_list.append( (0x10AC0097, array('B', [0x00, 0x0A, 0x16, 0x02])) )

# First Hard Braking Event (HBE) frame
hbe_list.append( (0x10B20097, array('B', [0x10, 0x22, 0x02, 0x01, 0x16, 0x02, 0x00, 0x42])) )
# index of first hard braking event frame
FIRST_HBE_INDEX = len(hbe_list) - 1
# Second Hard Braking Event (HBE) frame
hbe_list.append( (0x10B20097, array('B', [0x21, 0x72, 0x6F, 0x61, 0x64, 0x63, 0x61, 0x73])) )
# Third Hard Braking Event (HBE) frame
hbe_list.append( (0x10B20097, array('B', [0x22, 0x74, 0x69, 0x6E, 0x67, 0x20, 0x48, 0x61])) )
# Fourth Hard Braking Event (HBE) frame
hbe_list.append( (0x10B20097, array('B', [0x23, 0x72, 0x64, 0x20, 0x42, 0x72, 0x61, 0x6B])) )
# Fifth Hard Braking Event (HBE) frame
hbe_list.append( (0x10B20097, array('B', [0x24, 0x65, 0x20, 0x41, 0x6C, 0x65, 0x72, 0x74])) )
# index of last hard braking event frame
LAST_HBE_INDEX = len(hbe_list) - 1


# handle ctrl+c
def signal_handler(signal, frame):
    print "Powering down DVI test"   
    kom_dev.power_down(DVI_KOMODO_INTERFACE)
    sys.exit()

def start_dvi_test():
    # start with no expected packet
    expected_packet_index = None
    print "Starting test!"
    kom_dev.configure_port(DVI_KOMODO_INTERFACE)
    print "Powering up CAN"
    kom_dev.power_up(DVI_KOMODO_INTERFACE)
    print "Getting frames"
    while True:
        # get CAN frame, blocking function
        pkt, data = kom_dev.get_frame(DVI_KOMODO_INTERFACE)
        # trim the data to the actual CAN length
        data = data[:pkt.dlc]
        if expected_packet_index != None:
            # check CAN ID
            if pkt.id != hbe_list[expected_packet_index][0]:
                raise Exception("Expected ID: {0}, got {1}. Index is {2}".format(hex(hbe_list[expected_packet_index][0]),
                                                                                 hex(pkt.id),
                                                                                 expected_packet_index))
            # check CAN data
            if data != hbe_list[expected_packet_index][1]:
                raise Exception("Expected data: {0}, got {1}. Index is {2}".format(hbe_list[expected_packet_index][1],
                                                                                   data,
                                                                                   expected_packet_index))
            # increment the expected packet index
            expected_packet_index += 1
            # boundary check
            if expected_packet_index > LAST_HBE_INDEX:
                expected_packet_index = None

        # check if this is the first HBE and we need to respond
        # ID check
        hbe_id, hbe_data = hbe_list[FIRST_HBE_INDEX]
        if (hbe_id == pkt.id) and (hbe_data == data):
            # send immediate response
            kom_dev.send_frame(DVI_KOMODO_INTERFACE, HBE_RESPONSE_ID, HBE_RESPONSE_DATA)
            expected_packet_index = FIRST_HBE_INDEX + 1

signal.signal(signal.SIGINT, signal_handler)
start_dvi_test()
