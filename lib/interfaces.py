"""
This file includes the BaseInterface class and all interfaces inheritance from it:
TelnetInterface
SerialInterface
"""
import logging
import telnetlib
# import serial

log = logging.getLogger(__name__)


class BaseInterface(object):
    """
    All interfaces should be inheritance from this class
    and implement the following functions.
    Otherwise an exception will be raised.
    """

    def __init__(self, cnn_info):
        for key, value in cnn_info.items():
            setattr(self, key, value)

    def __del__(self):
        raise Exception("Missing implementaion for function __del__ in the interface.")

    def open(self):
        raise Exception("Missing implementaion for function open in the interface.")

    def close(self):
        raise Exception("Missing implementaion for function close in the interface.")

    def write(self, command, check_echo = True):
        raise Exception("Missing implementaion for function write in the interface.")

    def read_line(self):
        self.read_until( until = '\r\n' )

    def read(self, until, timeout):
        self.read_until( until, timeout )

    def read_until(self, until, timeout):
        raise Exception("Missing implementaion for function read_until in the interface.")

    def flush_buffer(self):
        raise Exception("Missing implementaion for function flush_buffer in the interface.")



class TelnetInterface(BaseInterface):
    """
    Implements basic operations in Telnet interface
    by using telnetlib module.
    cnn_info should conatins: 
    host - for host name
    port - for port id
    timeout_sec - for timeout value in seconds (default 10 sec.)
    """

    def __init__(self, cnn_info):
        self.host = ''
        self.port = 0
        self.timeout_sec = 10
        super(TelnetInterface, self).__init__(cnn_info)
        self.handle = None

    def __del__(self):
        self.close()

    def open(self):
        try:
            self.handle = telnetlib.Telnet(self.host, self.port, self.timeout_sec)
        except Exception, e:
            raise e

        log.info( "Connected to {} on port {} with timeout {}".format(self.host, self.port, self.timeout_sec) )

    def close(self):
        if not self.handle is None:
            self.handle.close()
            self.handle = None


    def write(self, command, check_echo = True):
        self.handle.write(command + '\r\n')
        log.info("Tx@{}: {}".format(self.host, command.replace('\r\n', '') ) )

        if check_echo:
            return self.handle.read_until(command,3)
 
    def read(self, until = '\r\n', timeout_sec = 10):
        return self.read_until( until, timeout_sec)
 
    def read_until(self, until = '\r\n', timeout_sec = 10):
        data = self.handle.read_until(until,timeout_sec)

        log.info("Rx@{}: {}".format(self.host, data.replace('\r\n', '') ) )
        return data

    def flush_buffer(self):
        data = self.handle.read_very_eager()
        log.info("Rx flush@{}: {}".format(self.host, data.replace('\r\n', '') ) )
        return data 




#  TBD - The SerialInterface is still not finished and cannot be used
class SerialInterface(BaseInterface): 
    """
    Implements basic operations in Serial interface
    by using pySerial module.
    cnn_info should conatins: 
    port - for port name or id
    timeout_sec - for timeout value in seconds (default 10 sec.) 
    baudrate - for baudrate value (default 115,200).
    It may also contains other serial parameters like: bytesize, parity, 
    stopbits and more. See documentation of pySerial API.
    """

    def __init__(self, cnn_info):

        # Raise exception, cause the serial not supported
        raise Exception("Serial interface is still not supported.")

        self.port = 0;
        self.timeout_sec = 10
        self.baudrate = 115200
        super(SerialInterface, self).__init__(cnn_info)
        self.handle = None

    def __del__(self):
        self.close()

    def open(self):
        try:
            self.handle = serial.Serial(port = self.port, 
                                        baudrate = self.baudrate, 
                                        timeout = self.timeout_sec)

        except Exception, e:
            raise Exception("Unable to connet %s via Serial port.\nError: %s" % (str(self.port), str(e)))

    def close(self):
        if not self.handle is None:
            self.handle.close()
            self.handle = None

    def write(self, command, check_echo = True):
        self.handle.write(command)

        if check_echo:
            return self.handle.read() #  TBD
    
    def read(self, until = '\r\n', timeout_sec = 10):
        return self.handle.read() #  TBD


#  Dictionary of existing interfaces and their class name.
INTERFACES = {'TELNET': TelnetInterface, 'SERIAL': SerialInterface}


if __name__ == "__main__":
    pass 

    #def test():
    
    #    try:
    #        interface_type = 'TELNET'
    #        cnn_info = { 'host':'trs01', 'port':2056, 'timeout_sec': 10 }
    #        interface = INTERFACES[interface_type](cnn_info)

    #        interface.open()
