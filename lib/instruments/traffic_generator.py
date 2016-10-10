"""
@file traffic_generator.py
@brief Traffic generator and sniffer instruments handler

controler
@author    	Shai Shochat
@version	1.0
@date		18/01/2016
"""


if __name__ == "__main__":
    import sys
    sys.path.append('C:\\ATLK - Zohar\\work\\qa')


from ctypes import *
from datetime import datetime
from uuts import common
import os, sys, subprocess, time, logging, socket
from lib import globals, interfaces
import threading
from uuts.craton import managment
from lib.instruments import packet_sniffer


log = logging.getLogger(__name__) 

TG_CLI_PROMPT = 'ate>'
IF_IDX_RANGE = [1,2,3]
BASE_HOST_PORT = 8030


# packet_sniffer.SnifferTypes['panagea4'] = TrafficGeneratorPanagea4

# def sniffer_types():
#    return packet_sniffer.SnifferTypes



class pcap_hdr_t(Structure):
    _pack_ = 1
    _fields_ = [
        (u'magic_number', c_uint32),
        (u'version_major', c_uint16),
        (u'version_minor', c_uint16),
        (u'thiszone', c_int32),
        (u'sigfigs', c_uint32),
        (u'snaplen', c_uint32),
        (u'network', c_uint32)
    ]
class pcaprec_hdr_t(Structure):
    _pack_ = 1
    _fields_ = [
        (u'ts_sec', c_uint32),
        (u'ts_usec', c_uint32),
        (u'incl_len', c_uint32),
        (u'orig_len', c_uint32)
    ]


class TGEmbeddedSniffer(object):
        
    def __init__(self, index, interface):
        self._if = interface
        self._module_name = 'sniffer'
        self._interfaces_active = {1 : False, 2 : False, 3 : False }


        data = self._if.write('\n')
        self.__set_id( index )

    def __del__(self):
        try:
            for if_idx, state in self._interfaces_active:
                if state:
                    self.stop( if_idx )
        except Exception:
            pass


    def __set_id(self, index):
        """
        usage : sniffer setting -id 1..4
        """
        assert( 1 <= index <= 4 )

        self.sniffer_id = index

        cmd = "%s setting -id %d" % (self._module_name, index )
        res = self._if.write( cmd.encode('ascii') + "\r\n" )
        res = self._if.read_until('ate>');
        if ('ERROR' in res) :
            raise Exception("Error setting sniffer settings")


    def start(self, if_idx, server_ip = None, server_port = None):
        """
        usage : sniffer start -if_idx 1|2|3 (3 - both 1 and 2 simultanously) -server_ip 10.10.1.131 [-server_port 8030] (in any case all rf_idx frames will be redirect to the first configured port...)
        """
        assert( if_idx in IF_IDX_RANGE )

        assert ( self._interfaces_active[if_idx] == False )

        cmd = "%s start -if_idx %d" % (self._module_name, if_idx)
        cmd += " -server_ip %s"  % (server_ip if not server_ip is None else socket.gethostbyname(socket.gethostname()) )
        cmd += (" -server_port %s"  % server_port) if not server_port is None else ""
        res = self._if.write( cmd.encode('ascii') + "\r\n" )
        
                
        self._interfaces_active[if_idx] = True
        res = self._if.read_until('ate>');        
        if ('ERROR' in res):
            raise Exception("Error in starting tg session")

    def stop(self, if_idx):
        """
            usage : sniffer stop -if_idx 1|2|3
        """
        assert( if_idx in IF_IDX_RANGE )
        assert ( self._interfaces_active[if_idx] == True )

        cmd = "%s stop -if_idx %d" % (self._module_name, if_idx)
        res = self._if.write( cmd.encode('ascii') + "\r\n" )
        res = self._if.read_until('ate>');
        if ('ERROR' in res) :
            raise Exception("Error in starting tg session")

        self._interfaces_active[if_idx] = False

    def get_counters( self, if_idx ):

        """
            sniffer counters print -if_idx 1
            DEBUG : Processed parameter -if_idx, value "1"
            Interface : 1
            RX : 0
            ate>
        """

        assert( if_idx in [1,2] )
        assert ( (self._interfaces_active[if_idx] == True) or (self._interfaces_active[3] == True) )

        cmd = "%s counters print -if_idx %d" % (self._module_name, if_idx)
        res = self._if.write( cmd.encode('ascii') + "\r\n" )
        
        res = self._if.read_until('ate>');
        if ('ERROR' in res) :
            raise Exception("Error in starting tg session")

        counter = None

        lines = res.split('\r\n')
        for line in lines:
            if 'RX' in line:
                counter = line.split(':')[1].replace('\r', '').strip()

        if counter is None:
            raise SyntaxError("Unable to parse uut counters")

        return { 'RX' : counter, 'TX' : None }



    def reset_counters(self, if_idx):
        """
        usage : sniffer reset -if_idx 1|2
        """
            
        assert( if_idx in [1,2] )
        cmd = "%s counters reset -if_idx %d" % (self._module_name, if_idx)
        res = self._if.write( cmd.encode('ascii') + "\r\n" )
        res = self._if.read_until('ate>');
        if ('ERROR' in res) :
            raise Exception("Error in starting tg session")

class Panagea4SnifferAppEmbedded( TGEmbeddedSniffer ):

    def __init__(self, interface):
        self._module_name = 'apps sniffer'
        self._if = interface
        self._interfaces_active = {1 : False, 2 : False, 3 : False }
        data = self._if.write('\n')

class TGHostSniffer(object):

    class PcapFile(object):

        PCAP_MAGIC = 0xa1b2c3d4
        PCAP_MAJOR_VERSION = 2
        PCAP_MINOR_VERSION = 4

        def __init__(self, filename, overwrite = False):
            self._f = open(filename, u'wb' if overwrite == False else 'w+b')
            # write the hdr
            self._f.write(pcap_hdr_t(
                self.PCAP_MAGIC,
                self.PCAP_MAJOR_VERSION,
                self.PCAP_MINOR_VERSION,
                0,
                0,
                65535, # XXX update this if we ever get a bigger packet
                127 # LINKTYPE_IEEE802_11_RADIOTAP
            ))
        

        def __del__(self):
            self.close()

        def close(self):
            self._f.close()

        def write_packet(self, packetdata):
            now = datetime.now()
            self._f.write(pcaprec_hdr_t(
                now.second,
                now.microsecond,
                len(packetdata),
                len(packetdata)
            ))
            self._f.write(packetdata)
        
        
    """   Main TGHostSniffer Class   """
        
        
    def __init__(self, index):

        self.threads_loop_flag = {}
        self.id = index
        self.sock_timeout = 1
        self.sock_retries = 100

    def start_capture_thread(self, port, capture_file):

        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_addr = ('', port )
        sock.bind(listen_addr)

        pcap = self.PcapFile( capture_file.decode(u'utf-8'))

        self.threads_loop_flag[port] = True
            
        sock.settimeout(self.sock_timeout)
        counter = 0
        retries = 0
        while ( self.threads_loop_flag[port] == True ):
                    
            try:
                data,addr = sock.recvfrom(1518)
                pcap.write_packet( data )
                    
            except Exception as e:

                if ( type(e) == socket.timeout ):
                    retries += 1
                    continue

                if (retries > self.sock_retries ):
                    self.threads_loop_flag[port] = False

                print "ERROR : {} , {}, {} ".format( type(e), inst.args, e )
            counter+=1
        
        print counter

        pcap.close()
        sock.close()

    def start(self, if_idx, port, capture_file):

        # check if this if_idx was initialized...
        t = threading.Thread( target = self.start_capture_thread, args= [port,capture_file] )
        t.start()

    def stop(self, port):
        self.threads_loop_flag[port] = False


class TrafficGeneratorPanagea4(object):
    """
    @class TrafficGeneratorPanagea4
    @brief Panagea4 evk based traffic generator
    @author Shai Shochat
    @version 0.1
    @date	19/01/2016
    """

    class TGLink(object):

        def __init__(self, index, interface, ip = None ):
            self._if = interface
            self.index = index
            self._module_name = 'tg link'
            self._active_sessions = []
            self.managment = managment.V2xManagment(ip, unit_version = "SDK4.x")
            data = self._if.write('\n')

        def __del__(self):
            try:
                for session in self._active_sessions:
                    self.stop(session)
            except Exception:
                pass



        def init(self):
            cmd = ' '.join( [ self._module_name, 'init'] )
            self._if.write(cmd.encode('ascii') + "\r\n")
            res = self._if.read_until(TG_CLI_PROMPT)
            return res

        def start(self, session_id, if_idx, protocol_id, frames = 0, rate_hz = 1, payload_length = 200, frame_type = None):
            """
                usage : tg link start -session_id 1.. -if_idx 1|2 -protocol_id 0xXXXX|0xXXXXXXXXXX [-frames 0 - ...] 
                            [-rate_hz 1 - ...] [-tx_data 'ddddd'] [-payload_len 0 - ] [-frame_type data|vsa]
                            [-dest_address XX:XX:XX:XX:XX:XX] [-data_rate 3|4.5|6|9|12|18|24|27|36|48|108 MBPS]
                            [-user_prio 0-7] [-power_dbm8 -20-20]

            """
            cmd = "%s start -session_id %d -if_idx %d -protocol_id 0x%x" % (self._module_name, session_id, if_idx, protocol_id)
            cmd += " -rate_hz %d -payload_len %d"  % (rate_hz, payload_length ) 
            cmd += (" -frame_type %s"  % frame_type) if not frame_type is None else ""
            res = self._if.write( cmd.encode('ascii') + "\r\n" )
            res = self._if.read_until(TG_CLI_PROMPT)
            if ( ('ERROR' in res)):
                raise Exception("Error in starting tg session")
            
            self._active_sessions.append(session_id)


        def stop(self, session_id):
            """
                usage : tg link stop -session_id 1...
            """
            if not session_id in self._active_sessions:
                raise Exception("Session not exists")


            cmd = "%s stop -session_id %d" % (self._module_name, session_id)
            data = self._if.write( cmd.encode('ascii') + "\r\n" )
            if 'ERROR' in data:
                raise Exception("Error stopping tg link session")
            self._active_sessions.remove(session_id)

    class TGStack(object):
        pass

    class TGSniffer(object):

        #target ip value extracted from json configuration file, user name and password are for qa cli...
        def __init__(self, id = None, interface = None, ip = None):
            self.id = id
            self.capture_file_name = None
            self.managment = None
            self._sniffer = TGEmbeddedSniffer(id, interface)
            self._host = TGHostSniffer( id )
            self._target_ip = ip

        def init(self, tg_ip, version):
            self.managment = managment.V2xManagment(self._target_ip, unit_version = version )


        def start(self, rf_if, capture_file ):

            self.port = BASE_HOST_PORT + ( self.id * 10 ) + rf_if
            self._host.start( rf_if, self.port, capture_file )
            # send last appended rf_if in the rf interface list
            self._sniffer.start( rf_if, server_port = self.port )


        def stop(self, rf_if):
            self._sniffer.stop(rf_if)
            self._host.stop( self.port )

        def get_counters( self, rf_if ):
            # TBD : HOST Counters
            return self._sniffer.get_counters(rf_if)

        def reset_counters(self, rf_if):
            # TBD : host reset counters
            return self._sniffer.reset_counters(rf_if)


    def __init__(self, index, interface_type, connection_info):
        
        # cnn_info = { 'host':self.ip , 'port': int(port), 'timeout_sec': 10 }

        try:
            interface = interfaces.INTERFACES[interface_type]
        except Exception as e:
            raise e("Interface {} is not supported".format(interface_type) )

        self.index = index
        self._if = interfaces.INTERFACES[interface_type](connection_info)
        self._if.open()
        self.connection_info = connection_info
        self.link = self.TGLink( index,  self._if, connection_info['host'])
        self.sniffer = self.TGSniffer( index, self._if, connection_info['host'] )

    def __del__(self):
        self.link = None
        self.sniffer = None




if __name__ == "__main__":
    log_file = "c:/temp/traffic_log.txt"
    logging.basicConfig(filename=log_file, filemode='w', level=logging.INFO)
    log = logging.getLogger(__name__)


    interface_type = 'TELNET'
    #cnn_info = { 'host':'10.10.2.23', 'port': 23, 'timeout_sec': 10 }
    #tg = TrafficGeneratorPanagea4( 1, 'TELNET', cnn_info )
    #cnn_info_2 = { 'host':'10.10.0.237', 'port': 23, 'timeout_sec': 10 }
    tg2 = TGHostSniffer( 2 )
    tg3 = TGHostSniffer( 3 )
    try:
        
        #tg.sniffer.start( rf_if = 3, capture_file = "c:/temp/test_file.pcap" )
        tg2.start(if_idx = 1, port = 8051, capture_file = "c:/temp/rx_test_file.pcap" )
        tg3.start(if_idx = 1, port = 8061, capture_file = "c:/temp/tx_test_file.pcap" )
        time.sleep( 120 )
        #tg.link.start( 1, 1, 0x1234, frames = 1000, rate_hz = 50, payload_length = 100 )
        #time.sleep(1)
        #tg.link.start( 1, 2, 0x5678, frames = 1000, rate_hz = 50, payload_length = 100 )
       
        #cntr = tg.sniffer.get_counters( rf_if = 3 )
        #print cntr

        #tg.sniffer.reset_counters( rf_if = 3)

    except  Exception as e:
        pass
    finally:
        #tg.link.stop ( 1 )
        #tg.link.stop ( 2 )
        #tg.sniffer.stop( 3 )
        tg3.stop( 8061 )
        tg2.stop( 8051 )






