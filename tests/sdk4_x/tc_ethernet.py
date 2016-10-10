"""
    @file  
    Implement ethernet port testing 

    This test is based on audi-marben version.

    TP :  @link \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx @endlink 
"""

import sys, os, time, tempfile
import logging
from lib import station_setup
from uuts import common
from tests import common
from lib import instruments_manager, packet_analyzer, globals, gps_simulator

import threading
from datetime import datetime
import socket
import binascii
import pyshark

import ctypes
from lib import winpcapy


LOOPBACK_UDP_PORT = 8020
LOOPBACK_RAW_PORT = 8021
ETH_HDR_LEN = 14

header = ctypes.POINTER(winpcapy.pcap_pkthdr)()
pkt_data = ctypes.POINTER(ctypes.c_ubyte)()



class TC_ETHERNET_UDP(common.V2X_SDKBaseTest):
    """
    @class TC_ETHERNET_UDP
    """
 
    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.stats = Statistics()
        super(TC_ETHERNET_UDP, self).__init__(methodName, param)
    
    def get_test_parameters( self ):
        super(TC_ETHERNET_UDP, self).get_test_parameters()
        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )
        self._udp_port = self.param.get('udp_port', LOOPBACK_UDP_PORT )
        self.total_frames_to_send = self.param.get('total_frames_to_send', 100 )
        self.max_rrt_msec = self.param.get('max_rtt_msec', 2 )
         
   
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

        self.instruments_initilization()
        self.unit_configuration()
        self.main()

        #self.debug_override()

        if len(self._cpu_load_info):
            for uut_id in self._cpu_load_info:
                self.uut.set_cpu_load( 0 )

        self.analyze_results()

        self.print_results()
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def instruments_initilization(self):
        pass

    def unit_configuration(self):
        self.cli_name = 'loopback'
        self.uut.create_qa_cli( self.cli_name )
        # Activate loopback 
        evk_addr = ( socket.gethostbyname(socket.gethostname()),  self._udp_port)
        self.uut.qa_cli( self.cli_name ).cmd_loopback('udp', evk_addr, print_frames = 0 )


    def main(self):

        self.evk_ip = self.uut.ip
        evk_addr = (self.uut.ip, self._udp_port)

        # Open udp socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
        sock.bind( ('', self._udp_port ) )
        sock.settimeout(1.0)
        loss_frm_seq = 0

        msg_size = 38 # Min Packet size is 64, L2 size is 12, IP hdr is 16 and UDP hdr is 4 --> 64 - 32
        try:
            for i in range(self.total_frames_to_send):
            
                frame = self._build_frame( msg_size, i)
                sock.sendto( frame , evk_addr)
                self.stats.total_frames_tx += 1

                try:
                    data, addr = sock.recvfrom(2048)
                except Exception as e:
                    self.stats.total_frame_loss += 1
                    self.log.error("Frame size %d dropprd", msg_size )
                    loss_frm_seq += 1
                    if loss_frm_seq > 60:
                        raise GeneratorExit("Frame loss is very high please check system and configuration")
                else:
                    loss_frm_seq = 0
                    delta_ts = self.time_stamp_msec() - int(data[3:19], 16)

                    self.stats.total_frames_rx += 1
                    if ( delta_ts > self.max_rrt_msec ):
                        self.log.error("Latecny error on frame size %d", msg_size )
                        self.stats.frame_latency_error += 1
                
                    if len(data) != msg_size:
                        self.log.error("Error size error on frame size %d rcv %d", msg_size, len(data) )
                        self.stats.frame_size_error +=1
 
                msg_size += 1
                if msg_size > 1472:
                    msg_size = 38

        except Exception:
            raise e
        finally:
            # Send exit to the loop back 
            sock.sendto( "!EXIT", evk_addr )
            sock.close()


    def time_stamp_msec(self):
        return int((datetime.utcnow() - datetime(1970, 1, 1)).total_seconds() * 1000)	

    def verify_frame(self, sequence_id):
        pass

    def _build_frame(self, payload_len, sequence_id ):
          
        c_time_stamp   = '%016X' % self.time_stamp_msec()
        c_sequence_id =  '%08x' % (sequence_id & 0xffffffff)
        c_crc32 = '%08X' % (binascii.crc32('%s%s' % (c_time_stamp , c_sequence_id) ) & 0xffffffff)
        c_data = '{}{}{}'.format( c_time_stamp, c_sequence_id,  c_crc32 )

        truncate_len = payload_len - len(c_data) - 6 
        if truncate_len < 0:
            truncate_len = 0

        msg = 'SOF{}{}EOF'.format( c_data, ('A' * truncate_len) )
        return msg.encode("utf-8")
         
    def debug_override( self, base_dir = None ):
        pass
    def analyze_results(self):
        pass
    def print_results(self):

        self.add_limit( "Total frames sent" , self.total_frames_to_send, self.stats.total_frames_tx, None , 'EQ')
        self.add_limit( "Total frames received" , self.total_frames_to_send, self.stats.total_frames_rx, None , 'EQ')
        self.add_limit( "Total frames loss" , 0, self.stats.total_frame_loss, None , 'EQ')
        self.add_limit( "RTT error > %d " % self.max_rrt_msec , 0, self.stats.frame_latency_error, None , 'EQ')
        self.add_limit( "Frame size error ", 0, self.stats.frame_size_error, None , 'EQ')




class TC_ETHERNET_RAW(TC_ETHERNET_UDP):

    def __init__(self, methodName = 'runTest', param = None):
        super(TC_ETHERNET_RAW, self).__init__(methodName, param)
        self.fp = winpcapy.pcap_t
        self.thread_loop = True
        self._thread_start = False

    def tearDown(self):
        super(TC_ETHERNET_RAW, self).tearDown()
        try:
            winpcapy.pcap_close(self.fp)
        except Exception:
            pass

    def getMacAddress(self, adapter = "Local Area Connection"): 
        eth = False
        if sys.platform == 'win32':
            for line in os.popen("ipconfig /all"): 
                if adapter in line:
                    eth = True

                if eth and line.lstrip().startswith('Physical Address'): 
                    mac = line.split(':')[1].strip().replace('-',':') 
                    break 
        else: 
            for line in os.popen("/sbin/ifconfig"): 
                if line.find('Ether') > -1: 
                    mac = line.split()[4] 
                    break 
        return mac  

    def unit_configuration(self):
        self.cli_name = 'loopback_raw'
        self.uut.create_qa_cli( self.cli_name )
        # Activate loopback 
        host_addr = ( self.getMacAddress() )
        self.uut.qa_cli( self.cli_name ).cmd_loopback('raw', host_addr, print_frames = 0 )

    def capture_frames(self, interface, total_frames, start_seq_id = 0, bpf_filter = str('ether proto 0xdccd'), display_filter = None ):
        # display_filter = 'wlan.sa=={} and cam'.format('92:56:92:01:00:e1')
        #bpf_filter = str('ether proto 0xcdcd')
        netmask = 0xffffffff

        seq_id = start_seq_id

        bpf_program = winpcapy.bpf_program()
        res = winpcapy.pcap_compile(self.fp, ctypes.byref(bpf_program), bpf_filter, 1, netmask)  
        if res != 0:
            raise Exception("Error compile BPF")     
        res = winpcapy.pcap_setfilter(self.fp, ctypes.byref(bpf_program) )
        if res != 0:
            raise Exception("Error compile BPF")
        
        self._thread_start = True

        while ( (self.thread_loop) and (self.stats.total_frames_rx < total_frames) ):
            res = winpcapy.pcap_next_ex( self.fp, ctypes.byref(header), ctypes.byref(pkt_data) )
            if (res > 0):
                ts = self.time_stamp_msec()

                self.stats.total_frames_rx += 1
                frame_seq = int(''.join(['%02x' % b for b in pkt_data[23:26]]), 16)
                frame_ts = int(''.join(['%02x' % b for b in pkt_data[14:22]]), 16)
                if ( frame_seq != seq_id):
                    self.stats.sequence_error += 1

                delta_ts = ts - frame_ts
                if (delta_ts  > self.max_rrt_msec ):
                    self.log.info( "Ts Delta %u" % delta_ts )
                    self.stats.frame_latency_error += 1

                seq_id += 1
                # print ("%ld:%ld (%ld)\n" % (header.contents.ts.tv_sec,header.contents.ts.tv_usec, header.contents.len))
                # print >> self.result._original_stdout, "%02x%02x" % (pkt_data[22] , pkt_data[23],  )
                # if pkt_data[11] == 0xdc:
            else:
                pass

     
    def _build_frame(self, da,sa,ether_type, payload_len, sequence_id ):

        if payload_len < 46:
            payload_len = 46

        packet = (ctypes.c_ubyte * (payload_len + ETH_HDR_LEN ) )()
            
        ts = self.time_stamp_msec()
        c_time_stamp   = map( ord, ('%016X' % ts).decode("hex") ) 
        c_sequence_id =  map( ord, ('%08x' % (sequence_id & 0xffffffff)).decode("hex") )
        c_crc32 = '%08X' % (binascii.crc32('%s%s' % ('%016X' % ts , '%08x' % (sequence_id & 0xffffffff)) ) & 0xffffffff)

        c_data = c_time_stamp + c_sequence_id + map( ord, c_crc32.decode("hex") )
        payload = [int(0xab)] * ( payload_len - len(c_data) )
        
        eth_type = ether_type
        if type(ether_type) is int:
            eth_type = map( ord, ('%04x' % ether_type).decode("hex"))

        frame = da + sa + eth_type + c_data + payload
        for i in range(len(frame)):
            packet[i] = frame[i]

        return packet

    def _build_exit_frame(self,  da, sa):
        PKT_LEN = 64
        packet = (ctypes.c_ubyte * ( PKT_LEN ) )()

        frame = da + sa + map( ord, ('%04x' % 0xdccd).decode("hex")) + [int(0x00)] * ( PKT_LEN - 14 )
        for i in range(len(frame)):
            packet[i] = frame[i]

        return packet

    ## Send down the packet

    def main(self):
        
        header = ctypes.POINTER(winpcapy.pcap_pkthdr)()
        pkt_data = ctypes.POINTER(ctypes.c_ubyte)()

        interface = "\\Device\\NPF_{01C5CC27-5D2E-469D-B2EC-0B38D8FAAEE9}" # Shai LT
        interface = "\\Device\\NPF_{5649CE3A-0A6F-4C1D-B605-0222EC75BEE0}" # Server 10.10.1.119


        errbuf= winpcapy.create_string_buffer(winpcapy.PCAP_ERRBUF_SIZE)
        ## Check the validity of the command line
        
        ## Open the adapter
        self.fp = winpcapy.pcap_open_live(interface, 65536, winpcapy.PCAP_OPENFLAG_PROMISCUOUS, 1000, errbuf)
        if not bool(self.fp):
            raise Exception("\nUnable to open the adapter. %s is not supported by WinPcap\n")

        da = map( ord, (self.uut.mac_addr.replace(':','')).decode("hex") )
        sa =  map( ord, ( (self.getMacAddress()).replace(':','')).decode("hex") ) 
        
        ether_type = 0xcdcd
        msg_size = 46
        seq_id = 0

        rcvThread = threading.Thread(target=self.capture_frames, args=( interface, self.total_frames_to_send, seq_id, ) )
        rcvThread.start()
        time.sleep(1)
        while not self._thread_start:
            time.sleep( 0.01 ) # sleep until thread started
        
            

        for i in range(0, self.total_frames_to_send):

            if msg_size > 1518:
                msg_size = 46

            if seq_id == 0xffffffff:
                seq_id = 0

            packet = self._build_frame( da,sa,ether_type, msg_size, i)
            if (winpcapy.pcap_sendpacket(self.fp, packet, len(packet) ) != 0):
                self.stats.total_frames_tx_fail += 1
            self.stats.total_frames_tx += 1

            seq_id +=1
            msg_size += 1

        rcvThread.join(timeout = 600)  # Wait Max 10 Min

        # Send exit frame
        # packet = self._build_exit_frame( da,sa)
        # winpcapy.pcap_sendpacket(self.fp, packet, len(packet)



    def print_results(self):

        self.add_limit( "Total frames sent" , self.total_frames_to_send, self.stats.total_frames_tx, None , 'EQ')
        self.add_limit( "Total frames received" , self.stats.total_frames_tx, self.stats.total_frames_rx, None , 'EQ')
        # self.add_limit( "Total frames loss" , 0, self.stats.total_frame_loss, None , 'EQ')
        self.add_limit( "RTT error > %d " % self.max_rrt_msec , 0, self.stats.frame_latency_error, None , 'EQ')
        self.add_limit( "Sequence Error", 0, self.stats.sequence_error, None , 'EQ')



class Statistics(object):

    def __init__(self):
        self.total_frames_tx = 0
        self.total_frames_tx_fail = 0
        self.total_frames_rx = 0
        self.total_frame_loss = 0
        self.sequence_error = 0
        self.frame_latency_error = 0
        self.frame_size_error = 0



  



