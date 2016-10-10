"""
@file       tc_sdk_link.py
@brief      Testsuite for testing sdk link layer module  
@author    	Shai Shochat
@version	1.0
@date		Nov 2013
\link		http://marge/trac/wavesys/wiki/ate/tp/sdk-link-test
"""

# import global and general setup var
from lib import globals, station_setup, instruments_manager, packet_analyzer
from uuts import common
from tests import common, dsrc_definitions

from lib.instruments import spectracom_gsg_6

# Define tree for 3 layer array
from collections import defaultdict
def tree(): return defaultdict(tree)

import threading

import sys, os, time
from datetime import datetime
import logging
import tempfile
import decimal


log = logging.getLogger(__name__)


class TC_LINK_API(common.V2X_SDKBaseTest):
    """
    @class TC_LINK_API
    @brief Implementation of sdk link layer implementation  
    @author Shai Shochat
    @version 0.1
    @date	03/09/2013
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self._tx_src_count = 0
        self.rx_list = []
        self.tx_list = []
        self.active_cli_list = []
        self._uut = {}

        return super(TC_LINK_API, self).__init__(methodName, param)


    def runTest(self):
        pass

    def setUp(self):
        super(TC_LINK_API, self).setUp()
        pass

    def tearDown(self):
        super(TC_LINK_API, self).tearDown()
        g = []

        for cli in self.active_cli_list:
            try:
                uut_id, rf_if, cli_name = cli
                g.append(uut_id)
                # close link session
                self._uut[uut_id].qa_cli(cli_name).link.socket_delete()

            except Exception as e:
                print >> self.result._original_stdout, "ERROR in tearDown,  Failed to delete socket on uut {} for cli {}".format( uut_id, cli_name )
                log.error( "ERROR in tearDown,  Failed to clean uut {} for cli {}".format(uut_id, cli_name) )
            finally:
                self._uut[uut_id].close_qa_cli(cli_name)

        # close the link service
        #uuts = set(g)
        #for uut in uuts:
        #    cli_name = 'service_kill_%d' % uut
        #    try:
        #        self._uut[uut].create_qa_cli(cli_name, target_cpu = self.target_cpu)
        #        self._uut[uut].qa_cli(cli_name).link.service_delete()
        #    except Exception as e:
        #        print >> self.result._original_stdout, "tearDown->ERROR : failed to delete service on uut {}".format( uut_id, cli_name )
        #    finally:
        #        self._uut[uut].close_qa_cli(cli_name)

    def packet_handler(self, packet):

        if self.check_is_wlan_ack_frame(packet):
            self.stats.total_unicast_ack_frames += 1
            return

        self.stats.total_sniffer_frames_processed += 1

        # Verify ratio check for frames
        if (self.stats.total_sniffer_frames_processed % self._verify_frames_ratio) != 0:
            return

        # Ignore 
        if_id = int(packet["frame.interface_id"],0) + 1
        for t_param in self._testParams:
            uut_id, rf_if = t_param.rx
            
            # Verify receiving interface is as sniffer interface 
            if rf_if != if_id:
                continue 

            # Get expected information
            if 'tx_data' in vars(t_param):
                tx_data = t_param.tx_data
            elif 'payload_len' in vars(t_param):
                tx_data = 'F' * t_param.payload_len
            else:
                return
                #raise Exception("Frame payload is missing")
            
            # Get frame structure exists in 
            frm_ref_val = self.get_frame_reference_structure(packet) 
            
            # Fill dynamic fields      
            if 'dest_addr' in vars(t_param):
                frm_ref_val['wlan']['da'] = t_param.dest_addr
                
            frm_ref_val['wlan']['sa'] = globals.setup.units.unit(t_param.tx[0]).rf_interfaces[t_param.tx[1]].mac_addr

            if 'wlan_mgt' in frm_ref_val:
                if 'frame_type' in vars(t_param) and t_param.frame_type == 'vsa':
                    proto_id =  t_param.proto_id # 0x0050c24a43
                    frm_ref_val['wlan_mgt']['tag.oui'] = 0x0050c2
                    frm_ref_val['wlan_mgt']['fixed.vendor_type'] = 0x4a40 + int(hex(t_param.proto_id)[-1:])

            # Verify all layers of the packet    
            for layer in frm_ref_val:
                self.verify_frame_structure( packet, frm_ref_val[layer], layer )

            # Test packet data
            try:
                packet_data = ''.join(packet["data.data"].split(':')).encode('ascii','ignore').upper()
            except Exception as e:
                self.stats.sniffer_data_fail += 1
                continue 
            else:
                # Compare data with transmited Data
                if packet_data != tx_data:
                    self.stats.sniffer_data_fail += 1

                if packet["llc.type"] != t_param.proto_id:
                    self.stats.sniffer_proto_fail += 1
 
    def get_test_parameters( self ):
        super(TC_LINK_API, self).get_test_parameters()
        # Set Some test defaults 
        self._capture_frames = self.param.get('capture_frames', 0)

        self._verify_frames_info = self.param.get( 'verify_frames', {'active' : False, 'ratio' : 1} )
        try: 
            self._verify_frames = self._verify_frames_info['active']
            self._verify_frames_ratio = self._verify_frames_info['ratio']
        except Exception as e:
            raise globals.Error( "PARAMETER : verify_frames is mismatch expected format, EXPECTED : {'active' : False, 'ratio' : 10}" )

        self._testParams = self.param.get('params', None )
        if self._testParams is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : params = tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data = 'ab', tx_power = -5 )")

        g = []
              
        print "Test parameters :\n"
        for i, t_param in enumerate(self._testParams):
            print "Param {} : {}".format ( i, ', '.join( "%s=%r" % (t,self.cap(str(v),10)) for t,v in t_param.__dict__.iteritems()) )

            if 'tx' in vars(t_param):
                g.append(t_param.tx[0])
            if 'rx' in vars(t_param) and not t_param.rx is None:
                g.append(t_param.rx[0])
         
        self._uut_list = set(g)

    def get_frames_from_cli_thread(self, rx):
        
        log = logging.getLogger(__name__)

        uut_id, rf_if, cli_name, expected_frames = rx 

        frm_cnt = 0
        transmit_time  = int(float( 1.0 / self._frame_rate_hz) *  expected_frames) + 5  
        start_time = int(time.clock())
  
         # Start Reading from RX unit\
        while True:
            try:
                data = self._uut[uut_id].qa_cli(cli_name).interface().read_until('\r\n', timeout = 2)
            except Exception as e:
                break

            if 'ERROR' in data:
                log.debug( "ERROR Found in RX, {}".format( data) )

            if 'Frame' in data:
                frm_cnt += 1
                self.stats.total_frames_processed += 1
             
                #frame = data.split(',')
                #frame_id = int(frame[0].split(':')[1])
                #if frame_id != frm_cnt:
                #    self.stats.frame_seq_err += 1

                #if self.tx_data.strip() != frame[2].strip():
                #    self.stats.data_mismatch += 1

            # Timeout
            if ( int(time.clock()) - start_time ) > (transmit_time + int(transmit_time * 0.1)):
                log.debug( "exit rx thread {} loop due to time out".format (rx) )
                break

            # frame count
            if frm_cnt >= expected_frames:
                log.debug( "exit rx thread {} loop due to frame count".format(rx) )
                break

    def test_link(self):
        """ Test link layer Tx and Rx
            @fn         test_link_tx_rx
            @brief      Verify tx nd rx abilites
            @details    Test ID	    : TC_SDK3.0_LINK_01
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx\n
        """
        # Get & parse test parameters`
        # params = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data = 'ab', tx_power = -5 ) ]

        self.get_test_parameters()

        # Verify uut idx exits and get uut object
        for uut_idx in self._uut_list:
            try:
                self._uut[uut_idx] = globals.setup.units.unit(uut_idx)
            except KeyError as e:
                raise globals.Error("uut index and interface input is missing or currpted, usage : _uut_id_tx=(0,1)")


        if len(self._cpu_load_info):
            # cpu_load = {0: {'load': 30, 'timeout': 0}, 1: {'load': 30, 'timeout': 0} }
            for uut_idx in self._cpu_load_info:
                self._uut[uut_idx].set_cpu_load( self._cpu_load_info[uut_idx]['load'], self._cpu_load_info[uut_idx]['timeout'] )

        # Call Test scenarios blocks
        self.initilization()
        self.unit_configuration()

        self.main()
        # self.debug_overides()

        if len(self._cpu_load_info):
            for uut_id in self._cpu_load_info:
                self._uut[uut_id].set_cpu_load( 0 )

        if self._verify_frames:
            self.analyze_results()

        self.print_results()

    def initilization(self):
       
        if self._verify_frames:

            # Get sniffer handle from setup
            log.info("Getting Sniffer info")
            if globals.setup.instruments.sniffer is None:
                raise globals.Error("Sniffer is not initilize or define in setup, please check your configuration")
            else:
                # Get pointer to object
                self.sniffer = globals.setup.instruments.sniffer

            # initlize sniffer
            self.sniffer.initialize()
            self.sniffer.set_interface([0,1])
            # wait for sniffer to load
            time.sleep(20)

        # Initilize GPS 
        self.gps_sim = self.gps_init(  self._gps_scenario, self._gps_tx_power )
        self.gps_file = os.path.join( tempfile.gettempdir(),  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')
        self.sniffer_file = os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap')

    # Main test action
    def unit_configuration(self):

        gps_lock = True
        # start gps scenario
        if self.is_gps_active():
            self.gps_sim.start_scenario()
            for uut in self._uut:
                gps_lock &= self.wait_for_gps_lock( uut, self._gps_lock_timeout_sec )

            # Add Gps lock limit     
            self.add_limit( "GPS Locked" , int(True) , int(gps_lock), None , 'EQ')
            if gps_lock == False:
                log.info("GPS Lock failed")
                return 

            # Start recording gps simulator scenraio data
            self.gps_sim.start_recording( gps_file )

        # start sniffer recording 
        if self._verify_frames:
            dir, file = os.path.split(os.path.abspath(self.sniffer_file))
            self.sniffer.start_capture( file, dir )

        # Config rx uut
        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            if t_param.rx is None:
                continue
            
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx

            for rx in rx_list:
                uut_id, rf_if = rx
                #set cli name base on rx + proto_id + if
                cli_name = "rx_%d_%x" % ( rf_if, t_param.proto_id )
                    
                self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                self.rx_list.append( (uut_id, rf_if, cli_name, t_param.frames, t_param) )

                t_param.rx_cli = cli_name

                # Check frame type VSA/DATA
                if not 'frame_type' in vars(t_param):
                    t_param.frame_type = 'data'

                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency( t_param.freq  , rf_if )

                # Get start counters
                self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt( rf_if )
                self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt( rf_if )
                                        
                self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                # Open general session
                self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')

                # Open sdk Link
                self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if, t_param.frame_type, t_param.proto_id)

        # Config tx test parameters
        for t_param in self._testParams:

            if ( 'tx_data' in vars(t_param) ):
                self.tx_data = t_param.tx_data
            elif ( 'payload_len' in vars(t_param) ):
                self.tx_data = int(t_param.payload_len)
             
            # For Multiple RX convert to list is not list
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx

            # Config tx uut
            for tx in tx_list:
                self.stats.tx_count += 1
                uut_id, rf_if = tx

                # Set start rate
                if self.stats.tx_count == 1:
                    self._frame_rate_hz = t_param.frame_rate_hz
  

                # Configure the Tx power 
                if 'tx_power' in vars(t_param):
                    self._uut[uut_id].managment.set_tx_power( t_param.tx_power, rf_if )
                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency(  t_param.freq  , rf_if )
                # Set it to default data mode
                if not 'frame_type' in vars(t_param):
                    t_param.frame_type = 'data'

                #set cli name base on tx + proto_id + if
                cli_name = "tx_{}_{}_{}".format( rf_if, t_param.frame_type, t_param.proto_id )
                t_param.tx_cli = cli_name
                # Check if cli exists
                try:
                    current_context = self._uut[uut_id].qa_cli(cli_name).get_socket_addr()
                    create_new_cli = False
                except Exception as e:
                    create_new_cli = True

                    if ( create_new_cli == False):
                        cli_name = cli + '_' + '1'
                         
                    t_param.tx_cli = cli_name

                    self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                    self.tx_list.append( (uut_id, rf_if, cli_name, self.tx_data ,t_param.frames, t_param.frame_rate_hz, t_param) )
                    self.stats.total_tx_expected += t_param.frames

    
                    # Get start counters
                    self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )
                    self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )

                    self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    if ( create_new_cli == False):
                        self._uut[uut_id].qa_cli(cli_name).set_socket_addr( current_context )
                    else:
                        # self._uut[uut_id].qa_cli(cli_name).link.service_create()
                        # self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                        self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if, t_param.frame_type, t_param.proto_id)

                    # Verify lowest rate
                    if self._frame_rate_hz < t_param.frame_rate_hz: 
                        self._frame_rate_hz = t_param.frame_rate_hz 


    def do_while_transmit(self, transmit_time):
        time.sleep( transmit_time + int(transmit_time * 0.4) )


    def main(self):


        thread_list = []
        transmit_time = 0

        # get the max waiting time
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

 
        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        for rx in  self.rx_list: 
            uut_id, rf_if, cli_name, frames, _ = rx
            self._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = self._capture_frames, timeout = rx_timeout )

        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            dest_addr = t_param.dest_addr if ( 'dest_addr' in vars(t_param) ) else None

            if ( type(self.tx_data) is int ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(payload_len = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)
            if ( type(self.tx_data) is str ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)
            
        # Start search
        if ( self._capture_frames == 1 ):
            for rx in self.rx_list:
                t = threading.Thread( target = self.get_frames_from_cli_thread, args = (rx,) )
                thread_list.append(t)

            # Starts threads
            for thread in thread_list:
                thread.start()


            for thread in thread_list:
                thread.join()
        else:
            log.info( "System started to trasmit, will wait for {} sec before test".format( transmit_time ) ) 

            # This procedure is for super class in the future.
            self.do_while_transmit( transmit_time ) 
            #time.sleep( transmit_time + int(transmit_time * 0.3) )

                    
        # Get Counter at the End of transmition  
        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx

            for rx in rx_list:
                uut_id, rf_if = rx
                self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = int(self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )) - int(self.stats.uut_counters[uut_id][rf_if]['rx_cnt'])

            # For Multiple RX convert to list is not list
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx
            for tx in tx_list:
                uut_id, rf_if = tx
                self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = int(self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )) - int(self.stats.uut_counters[uut_id][rf_if]['tx_cnt'])

        #stop and clean
        if self.is_gps_active():
            self.gps_sim.stop_scenario()
            self.gps_sim.stop_recording()
        
        if self._verify_frames:
            self.sniffer.stop_capture()

    def debug_overides(self):
        # DEBUG ONLY !!!!!!!   override for tests !!!!!
        #nav_file_recorder = "C:\\Use rs\\shochats\\AppData\\Local\\Temp\\nav_data_20130702-150427.txt"
        self.gps_file = "C:\\Users\\shochats\\AppData\\Local\\Temp\\gps_rec_20130702-150427.txt"
        self.sniffer_file = "c:\\capture\\test_link_20140330-143403.pcap"
        print "GPS log file : %s\n\r" % self.gps_file
        print "NAV_FIX log file : %s\n\r" % self.sniffer_file

    def analyze_results(self):

        #gps_data = self.load_data_file( self.gps_file )
        if globals.setup.instruments.pcap_convertor is None:
            raise globals.Error("PcapConvertor is not avaliable")
        else:
            # Get pointer to object
            pcap_pdml_conv = globals.setup.instruments.pcap_convertor

        self.pdml_file = os.path.splitext(self.sniffer_file)[0] + ".pdml"
        try:
            pcap_pdml_conv.export_pcap( self.sniffer_file, self.pdml_file )
        except Exception as e:
            self.add_limit( "Sniffer File capture" , 0 , 1, None , 'EQ')   
        else:
            pdml_parser = packet_analyzer.PcapHandler()
            pdml_parser.parse_file( self.pdml_file , self.packet_handler )

    def print_results(self):
        total_frames_sent = self.stats.total_tx_expected

        self.add_limit( "Total Frames Sent" , total_frames_sent , total_frames_sent, None , 'EQ')    
        self.add_limit( "Frame Rate (hz)" , self._frame_rate_hz , self._frame_rate_hz, None , 'EQ')
        if self._capture_frames == 1:    
            self.add_limit( "Total Frames Captured (uut)" , total_frames_sent, self.stats.total_frames_processed, None , 'EQ')    

        self.add_limit( "Total Frames on RX data errors" ,0, self.stats.data_mismatch, None , 'EQ')    

        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx

            uut_id, rf_if = rx_list[0]
            link_rx_counters = self._uut[uut_id].qa_cli(t_param.rx_cli).link.read_counters()
            uut_id, rf_if = tx_list[0]
            link_tx_counters = self._uut[uut_id].qa_cli(t_param.tx_cli).link.read_counters()
            try:
                self.add_limit( "(%d,%d), %s 0x%x" % ( uut_id, rf_if, t_param.frame_type, t_param.proto_id), link_tx_counters['tx'][1], link_rx_counters['rx'][1], None , 'EQ')
            except Exception as e:
                pass 

            #for rx in rx_list:
            #    uut_id, rf_if = rx
            #    self.add_limit( "uut %d, rf if %d, RX counter" % ( uut_id, rf_if)  ,t_param.frames, self.stats.uut_counters[uut_id][rf_if]['rx_cnt'], None , 'EQ')

        if self._verify_frames:
            self.add_limit( "Total Frames Prccessed on Sniffer" , self.stats.total_tx_expected , self.stats.total_sniffer_frames_processed, None , 'EQ')    

        if self.stats.sniffer_data_fail:
            self.add_limit( "Total Frames on Data error" ,0, self.stats.sniffer_data_fail, None , 'EQ')    

        if self.stats.wlan_da_mismatch:
            self.add_limit( "Total Frames on DA error" ,0, self.stats.wlan_da_mismatch, None , 'EQ')    
        if self.stats.user_prio_mismatch:
            self.add_limit( "Total Frames on Priority error" ,0, self.stats.user_prio_mismatch, None , 'EQ')    
        if self.stats.data_rate_mismatch:
            self.add_limit( "Total Frames on Rate error" ,0, self.stats.data_rate_mismatch, None , 'EQ')    

        if self._verify_frames:
            field_val = 0
            for field_name in vars(self.stats.frame_fields): 
                field_val = getattr( self.stats.frame_fields, field_name )
                if field_val > 0:
                    self.add_limit( "Frame field {}".format( field_name ) ,0, field_val, None , 'EQ')    


class frameStatistics(object):
    pass

class Statistics(object):

 
    def __init__(self):
        # Total frame process in the wireshark file
        self.total_frames_processed = 0
        self.frame_seq_err = 0
        self.data_mismatch = 0
        self.uut_counters = tree()

        self.total_sniffer_frames_processed = 0
        self.total_unicast_ack_frames = 0
        self.sniffer_data_fail = 0
        self.wlan_da_mismatch = 0
        self.user_prio_mismatch = 0
        self.data_rate_mismatch = 0
        self.total_tx_expected = 0
        self.tx_count = 0
        self.sniffer_proto_fail = 0
        self.frame_fields = frameStatistics()
