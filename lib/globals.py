
setup = None

# Used to print to screen in the unittest enviroment
screen = None


GPS_SIMULATOR_OVERIDE = 1

EXIT_OK = 0
EXIT_ERROR = -1

LOCAL = 0
REMOTE = 1

START = 0
STOP = 1


UDP_SERVER_PORT = 5454

class Error(StandardError):
	pass

#For CHS TC added:
CHS_RX_SNIF = 0
CHS_TX_SNIF = 1

# CAN Definitions
CAN_ID_RTR_BIT          = 30
CAN_ID_IDE_BIT          = 31
STANDARD_CAN_ID_LEN     = 11
EXTENDED_CAN_ID_LEN     = 29

CAN_ID_RTR_MASK         = 0x1 << CAN_ID_RTR_BIT
CAN_ID_RTR_FLAG         = CAN_ID_RTR_MASK
CAN_ID_IDE_MASK         = 0x1 << CAN_ID_IDE_BIT
CAN_ID_IDE_FLAG         = CAN_ID_IDE_MASK
STANDARD_CAN_ID_MASK    = (0x1 << STANDARD_CAN_ID_LEN)-1 # = 0x000007ff (First 11 bits)
EXTENDED_CAN_ID_MASK    = (0x1 << EXTENDED_CAN_ID_LEN)-1 # = 0x1fffffff (First 29 bits)
EXTENDED_CAN_ID_FLAG    = EXTENDED_CAN_ID_MASK

class canBusFrame(object):
    """
    @class CanFrame
    @brief Contains frame attributes: can_id, ide_f (extended), rtr_f (remote), dlc and data
    @author Neta-ly Rahamim
    @version 0.1
    @date	13/01/2015
    """
    def __init__(self, can_id, dlc, data, flags = None):
        self.can_id = can_id
        self.can_id_and_flags = can_id
        self.dlc = dlc
        self.data = data

        if not flags is None:

            self.ide_f = bool(flags & CAN_ID_IDE_FLAG)
            self.rtr_f = bool(flags & CAN_ID_RTR_FLAG)
            
            # Update can id 
            self.can_id = (self.can_id | (self.ide_f << CAN_ID_IDE_BIT) )

            self.can_id_and_flags = (self.can_id | (self.ide_f << CAN_ID_IDE_BIT)  | (self.rtr_f << CAN_ID_RTR_BIT) ) & 0xFFFFFFFF

        else:
            self.ide_f = bool(can_id & CAN_ID_IDE_FLAG)
            self.rtr_f = bool(can_id & CAN_ID_RTR_FLAG)


    def __eq__(self, can_frame):
        if can_frame is None:
            return False

        if (self.can_id_and_flags != can_frame.can_id_and_flags) or \
           (self.dlc != can_frame.dlc) or \
           (self.ide_f != can_frame.ide_f) or \
           (self.rtr_f != can_frame.rtr_f):
            return False

        # Make sure data is 8 bytes and complete it if needed
        data1 = self.data +  [0]*(8 - len(self.data))
        data2 = can_frame.data +  [0]*(8 - len(can_frame.data))

        for idx in range(0,8):
            if data1[idx] != data2[idx]:
                return False

        return True


    def __ne__(self, can_frame):
        return not self.__eq__(can_frame)


    def __str__(self):
        return "can_id = {0}, ide = {1}, rtr = {2}, dlc = {3}, data = {4}".format(hex(self.can_id), int(self.ide_f), int(self.rtr_f), self.dlc, ["0x%0.2X" % x for x in self.data])

