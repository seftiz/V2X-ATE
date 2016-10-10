"""
@file       tc_frame_struct.py
@brief      Testsuite for testing sdk link frame structure correctness 
@author    	Shai Shochat
@version	1.0
@date		Jan 2014
\link		http://marge/trac/wavesys/wiki/ate/tp/sdk3.0/frame_struct
"""

# import global and general setup var
from lib import station_setup
from uuts import common
from tests import common, dsrc_definitions
from lib import instruments_manager
from lib import packet_analyzer

from lib.instruments import spectracom_gsg_6
from uuts.craton.cli import navigation
# Define tree for 3 layer array
from collections import defaultdict
def tree(): return defaultdict(tree)

import threading
from lib import globals

import sys, os
import time
from datetime import datetime
import logging
import tempfile
import decimal


log = logging.getLogger(__name__)



class TC_FRAME_STRUCT_CONFORMENCE(common.V2X_SDKBaseTest):
    """
    @class TC_FRAME_STRUCT_CONFORMENCE
    @brief Implementation of sdk link layer implementation  
    @author Shai Shochat
    @version 0.1
    @date	03/09/2013
    """

    def runTest(self):
        pass

    def tearDown(self):
        try:
            for cli in self.active_cli_list:
                uut_id, rf_if, cli_name = cli
                # close link session
                self._uut[uut_id].qa_cli(cli_name).link_close()
                # close general session
                self._uut[uut_id].qa_cli(cli_name).session_close()
                # Close sdk Link
                self._uut[uut_id].close_qa_cli(cli_name)
        except Exception as e:
            pass

    def compare_field( field, type, value ):
        if type == int:
            field_ok = ( int(field) == value )
        elif type(value) == string:
            field_ok =  ( field == value )

    def frame_strcut_wlan(self, packet):
       
        for field, value in dsrc_definitions.wlanStructureFixed.items():
            # print >> self.result._original_stdout, "wlan.{}".format(field), " :", value, type(value), type(value) == int
            try:
                field_name = "wlan.{}".format(field)
            except Exception as e:
                pass
            else:
                if type(value) == int:
                    field_ok = ( int(packet[field_name],0) == value )
                elif type(value) == str:
                    if '!ref:' in value:

                        field_ok =  ( packet[field_name] == value )
                    else:
                        field_ok =  ( packet[field_name] == value )
                else:
                    uut_idx = 0
                    rf_id =  int(packet["frame.interface_id"],0) + 1
                    try:
                        field_ok =  ( packet[field_name] ==  eval(field) )
                    except Exception as e:
                        pass

                if not field_ok:
                    setattr ( self.stats.frame_fields, field_name.replace('.', '_') , ( getattr(self.stats.frame_fields, field_name.replace('.', '_') ) + 1 ) )
                    # eval( "self.stats.frame_fields.{} += 1".format( field_name.replace('.', '_') )  )

    def packet_handler(self, packet):

        log = logging.getLogger(__name__)
        self.stats.total_sniffer_frames_processed += 1

        self.frame_strcut_wlan( packet )

        if_id = int(packet["frame.interface_id"],0) + 1


        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
            for rx in rx_list:

                uut_id, rf_if = rx
                # Verify rx if
                if rf_if == if_id :
                    if 'tx_data_len' in vars(t_param):
                        tx_data = t_param.tx_data_len * t_param.tx_data_val 
                    elif 'payload_len' in vars(t_param):
                        tx_data = 'A' * t_param.payload_len
                    else:
                        raise Exception


                    try:
                        # raw data is "61:62:61:62:61:62:61:62:61:62:61:62:61:62:61 ....", means ascii char in hex value.
                        packet_data = (''.join([chr(int('0x' + i,0)) for i in packet["data.data"].split(':') ])).rstrip('\x00')
                    except Exception as e:
                        self.stats.sniffer_data_fail += 1
                        continue 
                    else:
                        # Compare data with transmited Data
                        if packet_data != tx_data:
                            self.stats.sniffer_data_fail += 1

                        if packet["llc.type"] != t_param.proto_id:
                            self.stats.sniffer_proto_fail += 1

    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self._tx_src_count = 0
        # Initlize all frame counters
        for field, value in dsrc_definitions.wlanStructureFixed.items(): 
            field_name = "wlan.{}".format(field)  
            setattr( self.stats.frame_fields ,  field_name.replace('.', '_'), 0)

        return super(TC_FRAME_STRUCT_CONFORMENCE, self).__init__(methodName, param)

    def get_test_parameters( self ):
        # Set Some test defaults 
        self._gps_scenario = self.param.get('gps_scenario', "" )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        self._gps_lock_timeout_sec = self.param.get('gps_lock_timeout_sec', 600 )
        self._capture_frames = self.param.get('capture_frames', 0)
        self._sniffer_test = self.param.get('sniffer_test', 0)


        self._testParams = self.param.get('params', None )
        if self._testParams is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : params = tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data_val = 'ab', tx_power = -5 )")

        g = list()
        i = 0
        for t_param in self._testParams:
            print "Tparam {} : {}".format ( i, t_param.__dict__)

            if 'tx' in vars(t_param):
                g.append(t_param.tx[0])
            if 'rx' in vars(t_param):
                g.append(t_param.rx[0])

            i += 1
         
        self._uut_list = set(g)
        self._uut = {}
    
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
                # log.debug( "RX {}, Data {}".format( rx, data) )
            except Exception as e:
                break

            if 'ERROR' in data:
                log.debug( "ERROR Found in RX, {}".format( data) )
                #break;
                #data = ERROR : rx time out


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
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )



        # Get & parse test parameters
        # params = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data_val = 'ab', tx_power = -5 ) ]
        self.get_test_parameters()

        # Verify uut idx exits and get uut object
        for uut_idx in self._uut_list:
            try:
                self._uut[uut_idx] = globals.setup.units.unit(uut_idx)
                # globals.setup.instruments.power_control[ self._uut[uut_idx].pwr_cntrl.id ].reboot( self._uut[uut_idx].pwr_cntrl.port )
            except KeyError as e:
                raise globals.Error("uut index and interface input is missing or currpted, usage : _uut_id_tx=(0,1)")

        # Start Test scenarios 
        
        self.initilization()
        self.unit_configuration()

        self.main()
        # self.debug_overides()
        if ( self._sniffer_test == 1 ):
            self.analyze_results()

        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def initilization(self):
  
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
        self.sniffer.start_capture( file_name = self.sniffer_file )

        self.rx_list = []
        self.tx_list = []
        self.active_cli_list = []

        # Config rx uut
        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx

            for rx in rx_list:
                uut_id, rf_if = rx
                #set cli name base on rx + proto_id + if
                cli_name = "rx_{}_{}".format( rf_if, t_param.proto_id )
                    
                self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                self.rx_list.append( (uut_id, rf_if, cli_name, t_param.frames) )

                if not 'frame_type' in vars(t_param):
                    self._frame_type = 'data'

                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency( t_param.freq  , rf_if )

                # Get start counters
                self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt( rf_if )
                self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt( rf_if )
                                        
                self._uut[uut_id].create_qa_cli(cli_name)
                # Open general session
                self._uut[uut_id].qa_cli(cli_name).session_open()
                # Open sdk Link
                self._uut[uut_id].qa_cli(cli_name).link_open(rf_if, self._frame_type, t_param.proto_id)
                #self._uut[uut_id].qa_cli(cli_name).link_rx( t_param.frames, print_frame = 1, timeout = 10000 )
                    # Set Rf Frequenct

        # Config tx test parameters
        for t_param in self._testParams:

            if ( 'tx_data_len' in vars(t_param) and 'tx_data_val' in vars(t_param) ):
                self.tx_data = t_param.tx_data_len * t_param.tx_data_val
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
  
                #set cli name base on tx + proto_id + if
                cli_name = "tx_{}_{}".format( rf_if, t_param.proto_id )
                self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                self.tx_list.append( (uut_id, rf_if, cli_name, self.tx_data ,t_param.frames, t_param.frame_rate_hz) )

                self.stats.total_tx_expected += t_param.frames

                # Configure the Tx power 
                if 'tx_power' in vars(t_param):
                    self._uut[uut_id].managment.set_tx_power( t_param.tx_power, rf_if )
                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency(  t_param.freq  , rf_if )
    
                # Get start counters
                self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )
                self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )

                self._uut[uut_id].create_qa_cli(cli_name)
                self._uut[uut_id].qa_cli(cli_name).session_open()
                self._uut[uut_id].qa_cli(cli_name).link_open(rf_if, self._frame_type, t_param.proto_id)
                # self._uut[uut_id].qa_cli(cli_name).link_tx(self.tx_data , frames = t_param.frames, rate_hz = t_param.frame_rate_hz)
                # Verify lowest rate
                if self._frame_rate_hz < t_param.frame_rate_hz: 
                    self._frame_rate_hz = t_param.frame_rate_hz 
            
    def main(self):

        thread_list = []
        transmit_time = 0

        # get the max waiting time
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

 
        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        for rx in  self.rx_list: 
            uut_id, rf_if, cli_name, frames = rx
            self._uut[uut_id].qa_cli(cli_name).link_rx( frames, print_frame = self._capture_frames, timeout = rx_timeout )

        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz = tx
            if ( type(self.tx_data) is int ):
                self._uut[uut_id].qa_cli(cli_name).link_tx(payload_len = tx_data , frames = frames, rate_hz = frame_rate_hz)
            if ( type(self.tx_data) is str ):
                self._uut[uut_id].qa_cli(cli_name).link_tx(tx_data = tx_data , frames = frames, rate_hz = frame_rate_hz)
            
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
            time.sleep( transmit_time + int(transmit_time * 0.3) )

                    
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

        self.sniffer.stop_capture()

    def debug_overides(self):
        # DEBUG ONLY !!!!!!!   override for tests !!!!!
        #nav_file_recorder = "C:\\Users\\shochats\\AppData\\Local\\Temp\\nav_data_20130702-150427.txt"
        self.gps_file = "C:\\Users\\shochats\\AppData\\Local\\Temp\\gps_rec_20130702-150427.txt"
        self.sniffer_file = "c:\\capture\\test_link_20140202-162129.pcap"
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
            self.add_limit( "Total Frames Proceesed" , total_frames_sent, self.stats.total_frames_processed, None , 'EQ')    

        self.add_limit( "Total Frames on RX data errors" ,0, self.stats.data_mismatch, None , 'EQ')    

        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx

            for rx in rx_list:
                uut_id, rf_if = rx
                self.add_limit( "uut %d, rf if %d, RX counter" % ( uut_id, rf_if)  ,t_param.frames, self.stats.uut_counters[uut_id][rf_if]['rx_cnt'], None , 'EQ')

        if ( self._sniffer_test == 1 ):
            self.add_limit( "Total Frames Prccessed on Sniffer" , self.stats.total_tx_expected , self.stats.total_sniffer_frames_processed, None , 'EQ')    

        if self.stats.sniffer_data_fail:
            self.add_limit( "Total Frames on Data error" ,0, self.stats.sniffer_data_fail, None , 'EQ')    

        if self.stats.wlan_da_mismatch:
            self.add_limit( "Total Frames on DA error" ,0, self.stats.wlan_da_mismatch, None , 'EQ')    
        if self.stats.user_prio_mismatch:
            self.add_limit( "Total Frames on Priority error" ,0, self.stats.user_prio_mismatch, None , 'EQ')    
        if self.stats.data_rate_mismatch:
            self.add_limit( "Total Frames on Rate error" ,0, self.stats.data_rate_mismatch, None , 'EQ')    

        field_val = 0
        for field, value in dsrc_definitions.wlanStructureFixed.items(): 
            field_name = "wlan.{}".format(field)   
            field_val = getattr( self.stats.frame_fields, field_name.replace('.', '_') )
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
        self.sniffer_data_fail = 0
        self.wlan_da_mismatch = 0
        self.user_prio_mismatch = 0
        self.data_rate_mismatch = 0
        self.total_tx_expected = 0
        self.tx_count = 0
        self.sniffer_proto_fail = 0
        self.frame_fields = frameStatistics()
        
