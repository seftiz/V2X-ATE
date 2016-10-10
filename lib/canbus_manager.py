
import logging
import os, time, sys
import thread, threading
import logging
from lib import globals


log = logging.getLogger(__name__)


import lib.instruments.Komodo.komodo_if as Komodo
import lib.instruments.Vector.vector as Vector


canBusDevicesTypes = {'komodo': Komodo.komodoCanDevice , 'vector': Vector.vectorCanDevice }
#canBusDevicesTypes = {'komodo': Komodo.Komodo , 'vector': Vector.vectorCanDevice }

class CanFrame(object):
    """
    @class CanFrame
    @brief Contains frame attributes: can_id, ide_f (extended), rtr_f (remote), dlc and data
    @author Neta-ly Rahamim
    @version 0.1
    @date	13/01/2015
    """
    def __init__(self, can_id, ide_f, rtr_f, dlc, data):
        self.can_id = can_id
        self.ide_f = ide_f
        self.rtr_f = rtr_f
        self.dlc = dlc
        self.data = data[:]

    def __eq__(self, can_frame):
        if can_frame is None:
            return False

        if (self.can_id  != can_frame.can_id) or (self.dlc != can_frame.dlc):
            return False

        if (self.ide_f != can_frame.ide_f) or (self.rtr_f != can_frame.rtr_f):
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


if __name__ == "__main__":
    pass