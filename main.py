
import os, sys, socket
from datetime import datetime
import unittest
import logging 
import json, signal
from lib import station_setup, HTMLTestRunner
from tests import common
from tests.common import tParam
from lib import globals, winpcapy
import json2html
import webbrowser


from ctypes import *
import string
import time
import socket as sk
import platform

# import scapy
# from scapy.utils import wrpcap


# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)


class TC_EXAMPLE(common.V2X_SDKBaseTest):

 
    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.stats = Statistics()
        super(TC_EXAMPLE, self).__init__(methodName, param)
    
    def get_test_parameters( self ):
        super(TC_EXAMPLE, self).get_test_parameters()
        self.debug = self.param.get('debug', false)
         
   
    def test_start(self):
        self.log = logging.getLogger(__name__)
        # unit configuration 
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )
        # Get position data that described in table below via NAV API.
        self.get_test_parameters()
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self._uut_id[0])
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")
        
        self.uut_channel = self._uut_id[1]

        if self.debug:
            self.debug_override()
        else:

            self.instruments_initilization()
            self.unit_configuration()
            self.main()

        if len(self._cpu_load_info):
            for uut_id in self._cpu_load_info:
                self.uut.set_cpu_load( 0 )

        self.analyze_results()

        self.print_results()
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def instruments_initilization(self):
        pass

    def unit_configuration(self):
        pass

    def main(self):
        # Main test logic
        pass

    def debug_override( self, base_dir = None ):
        pass

    def analyze_results(self):
        # Analyze any results
        pass

    def print_results(self):
        # print resuls to report
        pass

class TESTING(object):

    def read_from_named_pipe_3M():

        import win32pipe, win32file
        import win32file
        fileHandle = win32file.CreateFile("\\\\.\\pipe\\EmbdPipe0",
                                      win32file.GENERIC_READ | win32file.GENERIC_WRITE,
                                      0, None,
                                      win32file.OPEN_EXISTING,
                                      0, None)

        while 1:
            try:
                data = win32file.ReadFile(fileHandle, 4096)
                print data
            except Exception:
                pass


    def getTests(prefix='test'):
        """ Finds all tests in all loaded modules, except for certain predefined modules """
        tests = []
        for mod_name in sys.modules:
            if not mod_name in ['unittest', 'testermatic', 'clr', 'unittest.case']:
    #            print 'mod_name = %s' % mod_name
                testsuites = unittest.findTestCases(sys.modules[mod_name], prefix)
                if testsuites:
                    for testsuite in testsuites:
                        for test in testsuite:
                            tests.append(test)	
        return tests
 
    def runTests(test_list, complete_func=None):
        suite = unittest.TestSuite()
        for test in test_list:
            print test
            if complete_func:
                test = TestermaticTestCase(test)
                test.addListener(complete_func)			
            suite.addTest(test)	
    
        return unittest.TextTestRunner().run(suite)

    def test_can():

        import lib.instruments.Komodo.komodo_if as Komodo
        from  lib import canbus_manager as can
        import time
         
        if globals.setup.instruments.can_bus is None:
            raise globals.Error("Can bus server is not initilize, please check your configuration")

        try:
            can_mod = can.TM_CanBus( globals.setup.instruments.can_bus , 0 )
            #self._can_bus_sim = Komodo.Komodo()

            can_mod.init( True )

            can_mod.start()
            while True:
                time.sleep(0.2)

        except Exception as e:
            can_mod = None
            raise e
 

    def test_komodo_can():
        from lib.instruments.Komodo import komodo_if as Komodo
        from  lib import canbus_manager as can

        try:
    #        can_bus = can.komodo( '10.10.1.119' , 8010 )
            port = Komodo.KOMODO_IF_CAN_A
            can_bus = Komodo.Komodo()
        
            can_bus.find_devices()

            can_bus.configure_port(port)
            can_bus.power_up(port)

            #for i in xrange( 0, 10000 ):

            #    # AUDI msg = [0x00, 0x00, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00]
            #    msg = [0x12, 0x13, 0x13, 0x14, 0x15, 0x00, 0x00, 0x00]
            #    can_bus.send_frame(port, 0x3BE, msg )
  
            while True:
                cmd = raw_input('Hit : tx - for transmit, rx - for receive and x for exit\n')

                if cmd == 'tx':
                    id = 0
                    dlc = 5
                    data = [0x12, 0x13, 0x13, 0x14, 0x15, 0x00, 0x00, 0x00]
                    is_extended = False
                    is_remote = False
                    data = [12, 13, 13, 14, 15, 0, 0, 0]
                    cmd  = raw_input('Insert can id, extended(0,1), remote(0,1), len(0-8) and data:\n')
                    lst = cmd.split()
                    if len(lst) != 0:
                        id = int(lst[0],16)
                        is_extended = bool(int(lst[1]))
                        is_remote = bool(int(lst[2]))
                        dlc = int(lst[3])
                        data = [int(str,16) for str in lst[4:]]
      
                
                    can_frame = can.CanFrame(id, is_extended, is_remote, dlc, data)
                    print can_frame
                    can_bus.send_frame(port, can_frame)

                elif cmd == 'rx':
                    can_frame = can_bus.get_frame(port)
                    if isinstance(can_frame,dict):
                        can_frame = can.CanFrame(can_frame["can_id"], can_frame["ide_f"], can_frame["rtr_f"], can_frame["dlc"], can_frame["data"])

                    print can_frame

                elif cmd == 'x':
                    break

                else:
                    print 'Unknown command !'

        except Exception as e:
            raise e
        finally:
            can_bus.power_down(port)
            can_bus.close_port(port)


    def loopback_udp_test():

        import socket
        import binascii

        UDP_IP = '10.10.2.4'

        def time_stamp_msec():
            import datetime
            return int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds() * 1000)	

        def _build_frame( payload_len, sequence_id ):
          
            c_time_stamp   = '%016X' % time_stamp_msec()
            c_sequence_id =  '%08x' % (sequence_id & 0xffffffff)
            c_crc32 = '%08X' % (binascii.crc32('%s%s' % (c_time_stamp , c_sequence_id) ) & 0xffffffff)
            c_data = '{}{}{}'.format( c_time_stamp, c_sequence_id,  c_crc32 )

            truncate_len = payload_len - len(c_data) - 6 
            if truncate_len < 0:
                truncate_len = 0

            msg = 'SOF{}{}EOF'.format( c_data, ('A' * truncate_len) )
            return msg.encode("utf-8")


        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.bind( ('', 8020 ) )
        sock.settimeout(2.0)

        msg_size = 32 # Min Packet size is 64, L2 size is 12, IP hdr is 16 and UDP hdr is 4 --> 64 - 32


        for i in range(50000):

            if msg_size > 1472:
                msg_size = 32

            frame = _build_frame( msg_size, i)
            sock.sendto( frame , (UDP_IP, 8020))
            try:
                data, addr = sock.recvfrom(2048)
                print "{} : c_ts {}, c_sqid {} len : {} ".format( '%08X' % time_stamp_msec(), data[3:19], data[20:28],  len(data) )
            except Exception as e:
                print "ERROR : frame size %d not received" % msg_size
                print e

            msg_size += 1

        sock.sendto( "!EXIT" , (UDP_IP, 8020))
        sock.close()

    def loopback_raw_test():
        pass

 

    def test_uboot():
        uut = globals.setup.units.unit(0)
    
        uboot = uut.fw_cli('terminal').u_boot
        uboot.reboot()
        a =uboot.print_env()
        print a

        uboot.set_value( 'bootcmd' , "'tftp v2x-cli.img; bootm'")
        uboot.save()

        uboot.close()
 
    def test_pyshark():
        import pyshark
        #display_filter = str('wlan.sa==92:56:92:01:00:e1 and cam')
        display_filter = 'wlan.sa=={} and cam'.format('92:56:92:01:00:e1')
        #display_filter = str('cam')
        #bpf_filter = str('source 92:56:92:01:00:e1')
        capture = pyshark.LiveCapture( interface = '\\\\.\\pipe\\EmbdPipe0' , bpf_filter = None , display_filter = display_filter, only_summaries = False)
        capture.sniff( packet_count = 20, timeout = 60 )
        print capture


    def find_device(self):
            import ctypes


            if platform.python_version()[0] == "3":
                raw_input=input
            #
            # Basic structures and data definitions for AF_INET family
            #
            class S_un_b(Structure):
                _fields_ = [("s_b1",c_ubyte),
                            ("s_b2",c_ubyte),
                            ("s_b3",c_ubyte),
                            ("s_b4",c_ubyte)]

            class S_un_w(Structure):
                _fields_ = [("s_wl",c_ushort),
                            ("s_w2",c_ushort)]

            class S_un(Union):
                _fields_ = [("S_un_b",S_un_b),
                            ("S_un_w",S_un_w),
                            ("S_addr",c_ulong)]

            class in_addr(Structure):
                _fields_ = [("S_un",S_un)]



            class sockaddr_in(Structure):
                _fields_ = [("sin_family", c_ushort),
                            ("sin_port", c_ushort),
                            ("sin_addr", in_addr),
                            ("sin_zero", c_char * 8)]

            #
            # Basic structures and data definitions for AF_INET6 family
            #
            class _S6_un(Union):
                _fields_=[("_S6_u8",c_ubyte *16),
                          ("_S6_u16",c_ushort *8),
                          ("_S6_u32",c_ulong *4)]

            class in6_addr(Structure):
                _fields_=[("_S6_un",_S6_un)]

            s6_addr=_S6_un._S6_u8
            s6_addr16=_S6_un._S6_u16
            s6_addr32=_S6_un._S6_u32

            IN6_ADDR=in6_addr
            PIN6_ADDR=POINTER(in6_addr)
            LPIN6_ADDR=POINTER(in6_addr)

            class sockaddr_in6(Structure):
                _fields_=[("sin6_family",c_short),
                          ("sin6_port",c_ushort),
                          ("sin6_flowinfo",c_ulong),
                          ("sin6_addr",in6_addr),
                          ("sin6_scope_id",c_ulong)]

            SOCKADDR_IN6=sockaddr_in6
            PSOCKADDR_IN6=POINTER(sockaddr_in6)
            LPSOCKADDR_IN6=POINTER(sockaddr_in6)


            def iptos(in_):
               return "%d.%d.%d.%d" % (in_.s_b1,in_.s_b2 , in_.s_b3, in_.s_b4)
            def ip6tos(in_):
                addr=in_.contents.sin6_addr._S6_un._S6_u16
                vals=[]
                for x in range(0,8):
                    vals.append(sk.ntohs(addr[x]))
                host= ("%x:%x:%x:%x:%x:%x:%x:%x" % tuple(vals))
                port=0
                flowinfo=in_.contents.sin6_flowinfo
                scopeid=in_.contents.sin6_scope_id
                flags=sk.NI_NUMERICHOST | sk.NI_NUMERICSERV
                retAddr,retPort=sk.getnameinfo((host, port, flowinfo, scopeid), flags)
                return retAddr
            def ifprint(d):
                a=POINTER(pcap_addr_t)
                ip6str=c_char * 128
                ## Name
                print("%s\n" % d.name)
                ## Description
                if (d.description):
                    print ("\tDescription: %s\n" % d.description)
                ## Loopback Address
                if (d.flags & PCAP_IF_LOOPBACK):
                    print ("\tLoopback: %s\n" % "yes")
                else:
                    print ("\tLoopback: %s\n" % "no")
                ## IP addresses
                if d.addresses:
                    a=d.addresses.contents
                else:
                    a=False
                while a:
                    print ("\tAddress Family: #%d\n" % a.addr.contents.sa_family)
                    if a.addr.contents.sa_family == sk.AF_INET:
                        mysockaddr_in=sockaddr_in
                        print ("\tAddress Family Name: AF_INET\n")
                        if (a.addr):
                            aTmp=cast(a.addr,POINTER(mysockaddr_in))
                            print ("\tAddress: %s\n" % iptos(aTmp.contents.sin_addr.S_un.S_un_b))
                        if a.netmask:
                            aTmp=cast(a.netmask,POINTER(mysockaddr_in))
                            print ("\tNetmask: %s\n" % iptos(aTmp.contents.sin_addr.S_un.S_un_b))
                        if a.broadaddr:
                            aTmp=cast(a.broadaddr,POINTER(mysockaddr_in))
                            print ("\tBroadcast Address: %s\n" % iptos(aTmp.contents.sin_addr.S_un.S_un_b))
                        if a.dstaddr:
                            aTmp=cast(a.dstaddr,POINTER(mysockaddr_in))
                            print ("\tDestination Address: %s\n" % iptos(aTmp.contents.sin_addr.S_un.S_un_b))
                    elif a.addr.contents.sa_family == sk.AF_INET6:
                        mysockaddr_in6=sockaddr_in6
                        print ("\tAddress Family Name: AF_INET6\n")
                        if (a.addr):
                            aTmp=cast(a.addr,POINTER(mysockaddr_in6))
                            print ("\tAddress: %s\n" % ip6tos(aTmp))
                    else:
                        print ("\tAddress Family Name: Unknown\n")
                    if a.next:
                        a=a.next.contents
                    else:
                        a=False
                print ("\n")


            alldevs=POINTER(winpcapy.pcap_if_t)()
            d=POINTER(winpcapy.pcap_if_t)
            errbuf= winpcapy.create_string_buffer(winpcapy.PCAP_ERRBUF_SIZE)

            ## Retrieve the device list
            if (winpcapy.pcap_findalldevs(byref(alldevs), errbuf) == -1):
                print ("Error in pcap_findalldevs: %s\n" % errbuf.value)
                sys.exit(1)

            d=alldevs.contents
            while d:
                # ifprint(d)
                if (d.description):
                    print ("\tDescription: %s\n" % d.description)

                if d.next:
                    d=d.next.contents
                else:
                    d=False
                ## Free the device list
            winpcapy.pcap_freealldevs(alldevs)

    def test_can():
        my_uut = globals.setup.units.unit(0)

        cli_name = 'can_bus_test'
        my_uut.create_qa_cli(cli_name)
        # Open general session
        my_uut.qa_cli(cli_name).can.service_create()

    def test_nav_on_arc( cpu = 'arm' ):

            uut = globals.setup.units.unit(0)

            cli_name = 'nav_api'
            uut.create_qa_cli(cli_name, target_cpu = cpu )

            # Open general session
            uut.qa_cli(cli_name).nav.init( type = globals.LOCAL )
            nav_file_recorder = "c:\\temp\\nav_file_testing_{}_{}.log".format( cpu, time.time() )
            uut.qa_cli(cli_name).nav.start( ('file', nav_file_recorder) )
            start_time = time.time()
            while ( (time.time() - start_time) < 15 ):
                time.sleep(1)
        
            uut.qa_cli(cli_name).nav.stop()
        
            uut.qa_cli(cli_name).nav.terminate()

            uut.close_qa_cli( cli_name )

def connect_telnet( host, port ):
    #!/usr/bin/python
    telnets = []

    import telnetlib
    for i in range(100):
        tel = telnetlib.Telnet(host, port)
        tel.write("root\n\r")
        print tel.read_until("password :", 1)
        tel.write("root\n\r")
        telnets.append( tel )

def test_gpdsServer_sim ( ):
    from lib import gps_simulator as sim

    gpsd = sim.gpsdServer( '10.10.1.127' )
    gpsd.load_scenario( '/media/sf_Z_DRIVE/users/shochats/test.nmea' )

    gpsd.start_scenario()
    time.sleep(2)

    gpsd.stop_scenario()
    gpsd._if.close()








port = 9600

message =  ('01 01 00 08'   #Foo Base Header
            '01 02 00 00'   #Foo Message (31 Bytes)
            '00 00 12 30'   
            '00 00 12 31'
            '00 00 12 32' 
            '00 00 12 33' 
            '00 00 12 34' 
            'D7 CD EF'      #Foo flags
            '00 00 12 35')     


"""----------------------------------------------------------------"""
""" Do not edit below this line unless you know what you are doing """
"""----------------------------------------------------------------"""

import sys
import binascii

#Global header for pcap 2.4
pcap_global_header =   ('D4 C3 B2 A1'   
                        '02 00'         #File format major revision (i.e. pcap <2>.4)  
                        '04 00'         #File format minor revision (i.e. pcap 2.<4>)   
                        '00 00 00 00'     
                        '00 00 00 00'     
                        'FF FF 00 00'     
                        '7F 00 00 00')

#                        '69 00 00 00')

#pcap packet header that must preface every packet
pcap_packet_header =   ('AA 77 9F 47'     
                        '90 A2 04 00'     
                        'XX XX XX XX'   #Frame Size (little endian) 
                        'YY YY YY YY')  #Frame Size (little endian)

def generatePCAP(message,file_hwd): 

    hex_str = "%08x"% len(message)
    reverse_hex_str = hex_str[6:] + hex_str[4:6] + hex_str[2:4] + hex_str[:2]
    pcaph = pcap_packet_header.replace('XX XX XX XX',reverse_hex_str)
    pcaph = pcaph.replace('YY YY YY YY',reverse_hex_str)

    # bytestring = pcap_global_header + pcaph + eth_header + ip + udp + message
    bytestring = pcaph
    bytelist = bytestring.split()  
    bytes = ''.join(bytelist).decode('hex') + message
    # bitout = open(pcapfile, 'wb')
    # file_hwd.write(bytes)



def sniffer_server():

    pkts = []
    pcapnum = 0
    iter = 0

    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    listen_addr = ("",8030)
    sock.bind(listen_addr)

    bitout = open( 'c:/temp/file.pcap' , 'w+b')
    # Write File Header
    bitout.write( binascii.a2b_hex(''.join(pcap_global_header.split() )) )

    while True:
        data,addr = sock.recvfrom(1518)
        
        #generatePCAP( data ,bitout )
        #bytes = data[20:]
        bytes = data
        bitout.write( bytes )
        
        iter += 1
        if iter > 10:
            #bitout.close()
            # break
            pass

        # build frame from data
        # hex_data = data.encode('hex')
        # Generate all frame


if __name__ == "__main__":


    a = TESTING()
    a.find_device()

    raise

    import socket

    # Load configuration file
    com_ip = socket.gethostbyname(socket.gethostname())
    # com_ip = '10.10.1.112'
    cfg_file_name = "cfg_%s.json" % com_ip
    cfg_dir_name = "%s\\configuration\\" % dirname 
    cfg_file = os.path.join(cfg_dir_name, cfg_file_name)

    if not os.path.exists( cfg_file ):
        raise globals.Error("configuration file \'%s\' is missing." % (cfg_file) )

    json_file = open(cfg_file)
    try:
        json_data = json.load(json_file)
    except Exception as err:
        raise globals.Error("Failed to parse json data %s" % cfg_file, err)

    globals.setup = station_setup.Setup( json_data )

    # Create timestamp for log and report file
    scn_time = "%s" % (datetime.now().strftime("%d%m%Y_%H%M%S"))
    """ @var logger handle for loging library """
    log_file = os.path.join(globals.setup.station_parameters.log_dir, "st_log_%s.txt" % (scn_time) )
    print "note : log file created, all messages will redirect to : \n%s" % log_file
    logging.basicConfig(filename=log_file, filemode='w', level=logging.INFO)
    log = logging.getLogger(__name__)

    # load all system 
    globals.setup.load_setup_configuration_file()

    
    uut = globals.setup.units.unit(0)

    suite = unittest.TestSuite()

    def eth_fnc_tests( cpu_type = 'arm' ):
        
        from tests.sdk4_x import tc_ethernet

        test_param = dict( uut_id = (0,0), total_frames_to_send = 30000, max_rtt_msec = 3, target_cpu = cpu_type ) 
        
        # suite.addTest(common.ParametrizedTestCase.parametrize(tc_ethernet.TC_ETHERNET_UDP, param = test_param ) )
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_ethernet.TC_ETHERNET_RAW, param = test_param ) )


    
    # Audi GNSS to g5
    def audi():
        from tests.audi import can_2_g5
        test_param = dict( uut_id = (0,1) )
        suite.addTest(common.ParametrizedTestCase.parametrize(can_2_g5.TC_CAN_2_G5, param = test_param ) )

        from tests.audi import gnss_2_g5
        test_param = dict( uut_id = (0,1) , gps_scenario = 'RoshPina2Eilat_50Ms' )
        suite.addTest(common.ParametrizedTestCase.parametrize(gnss_2_g5.TC_GNSS_2_G5, param = test_param ) )

    def link( cpu_type = 'arm' ):
    
        frames_verification_active = False
        tx_pow = -5
 
        test_frames = 10000
        from tests.sdk3_0 import tc_link_api

        """ CONFORMENCE TEST : This test case will check frame structure of wlan & llc """
        # Broadcast
        frame_verification = { 'active' : False, 'ratio' : 10 }
        test_links = [ tParam( tx = (0,0), rx = (1,0), proto_id = 0x1234, frames = 100, frame_rate_hz = 10, payload_len = 800, tx_power = tx_pow ), 
                        tParam( rx = (0,0), tx = (1,0), proto_id = 0x5678, frames = 100, frame_rate_hz = 10, payload_len = 800, tx_power = tx_pow ) ]
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )
        


        from tests.sdk3_0 import tc_link_api
         # Stress test, 6 session TX + RX         
        cpu_load = {0: {'load': 30, 'timeout': 0}, 1: {'load': 30, 'timeout': 0} }
        total_frames = 10000
        tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
        test_links = [  tParam( tx = (0,0), rx = (1,0), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = '92:56:92:01:00:ca', tx_power = tx_pow ), 
                        tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = '92:56:92:02:00:e1',  tx_power = tx_pow ),  
                        tParam( tx = (1,0), rx = (0,0), frame_type= 'data', proto_id = 0x13a1, frames = total_frames*5, frame_rate_hz = 20, tx_data = tx_data,  dest_addr = '92:56:92:01:00:e1', tx_power = tx_pow ),
                        tParam( tx = (1,1), rx = (0,1), frame_type= 'data', proto_id = 0x13d1, frames = total_frames*10, frame_rate_hz = 50, tx_data = tx_data,  dest_addr = '92:56:92:02:00:e1', tx_power = tx_pow ),
                        tParam( tx = (0,0), rx = (1,0), frame_type= 'data', proto_id = 0x13e2, frames = total_frames, frame_rate_hz = 20, tx_data = tx_data,  tx_power = tx_pow ), 
                        tParam( tx = (1,0), rx = (0,0), frame_type= 'data', proto_id = 0x13b3, frames = total_frames*10, frame_rate_hz = 200, tx_data = tx_data,  tx_power = tx_pow ) ]

        suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, sniffer_test = 0, cpu_load_info = cpu_load ) ) )


    def nav( cpu_type = 'arm' ):
        from tests.sdk2_1 import tc_navapi
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_navapi.TC_NAV_1,   param =  dict( uut_id = (0,1),
                                                                                    target_cpu = cpu_type, 
                                                                                    gps_scenario="Neter2Eilat", 
                                                                                    scenario_time_sec = 30) ) )

    # run selected tests
    def can ( cpu_type = 'arm' ):

        from tests.sdk4_x import tc_can

        if os.path.isfile(tc_can.CAN_DATA_FILE_NAME) :
            os.remove(tc_can.CAN_DATA_FILE_NAME)
    
        test_param = dict( uut_id = (0,0) , target_cpu = cpu_type ) # (unit ID, CAN ID)
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_can.TC_CAN_API, param = test_param ))

        test_param = dict( uut_id = (0,0))
        # suite.addTest(common.ParametrizedTestCase.parametrize(tc_can.TC_CAN_ERRONEOUS, param = test_param ))

        test_param = dict( uut_id = (0,0), frames_rate = 500, frames_num = 100000, err_part = 0)
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_can.TC_CAN_LOAD, param = test_param ))


    
    def marben_testing( security = False):
        from tests.stacks.marben import tc_preformence
        for i in range(100,700,100):
            test_param = dict( uut_id=(1,0), tg_id=(0,1), stations = 40, rate_fps = i, security_active = security )
            suite.addTest(common.ParametrizedTestCase.parametrize(tc_preformence.TC_PREFORMENCE, param = test_param ))


    uut = globals.setup.units.unit(0)
    
    #nps = globals.setup.instruments.power_control
    # nps[uut.nps.id].reboot( uut.nps.port )
    #globals.setup.instruments.power_control[uut.nps.id].reboot( uut.nps.port )


    # Initilzie the units
    globals.setup.units.init()

    # marben_testing( True )
    # link( 'arm' )
    # eth_fnc_tests( cpu_type = 'arm' )
    # nav( 'arc2' )
    # for i in range(10):
        # test_nav_on_arc()
       
    # raise BaseException("END")
    can()

    # define report file
    report_file = os.path.join(globals.setup.station_parameters.reports_dir, "report_%s.html" % (scn_time) ) 
    fp = file(report_file, 'wb')

        
    try:
        # use html atlk test runner
        runner = HTMLTestRunner.HTMLTestRunner(
                                                stream = fp,
                                                verbosity = 2,
                                                title = 'auto-talks system testing',
                                                description = 'Debug report only', 
                                                uut_info = globals.setup.units.get_versions()
                                                )
        result = runner.run( suite )

    except (KeyboardInterrupt, SystemExit): 
        pass
    finally:
        # close report file
        fp.close()
   
        print "test sequence completed, please review report file %s" % report_file
        # open an HTML file on my own (Windows) computer
        url = "file://" + report_file
        webbrowser.open( url, new=2 )
 
