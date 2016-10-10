"""
@file       tc_sdk_wsmp.py
@brief      Testsuite for testing sdk wsmp layer module
@author    	Shai Shochat
@version	1.0
@date		Nov 2013
\link		http://marge/trac/wavesys/wiki/ate/sdk-link-test
"""

# import global and general setup var
from lib import station_setup
from uuts import common
from tests import common, dsrc_definitions
from lib import instruments_manager
from lib import packet_analyzer


from lib.instruments import spectracom_gsg_6
from uuts.craton.cli import navigation
from pynmea.streamer import NMEAStream

from collections import defaultdict


# from lib import setup
# import lib
from lib import globals


# import geopy pacakge for calculations
from geopy.point import Point
from geopy import distance

# from sdk20 import setup

import sys, os
import time
from datetime import datetime
import logging
import tempfile
import decimal

from tests.sdk3_0 import tx_sdk_link


class TC_SDK_WSMP(tx_sdk_link.TC_SDK_LINK):
    """
    @class TC_SDK_WSMP
    @brief Implementation of sdk wsmp layer implementation, over link test
    @author Shai Shochat
    @version 0.1
    @date	03/09/2013
    """

    def runTest(self):
        pass

    def tearDown(self):
        for pair in self._uuts:
            for dir in ['tx', 'rx']:
                uut_id, rf_if = pair[dir]
                # close link session
                self._uut[uut_id].qa_cli(dir).link_close()
                # close general session
                self._uut[uut_id].qa_cli(dir).session_close()
                # Close sdk Link
                self._uut[uut_id].close_qa_cli(dir)

    def packet_handler(self, packet):
        log = logging.getLogger(__name__)
        self.stats.total_sniffer_frames_processed += 1
        
        #int(packet["llc.type"],0) == self._proto_id:
        
        #packet["data.data"]
        # raw data is "61:62:61:62:61:62:61:62:61:62:61:62:61:62:61 ....", means ascii char in hex value.
        packet_data = (''.join([chr(int('0x' + i,0)) for i in packet["data.data"].split(':') ])).rstrip('\x00')

        # Compare data with transmited Data
        if packet_data != self.tx_data:
            self.stats.sniffer_data_fail += 1

        if not(self._wlan_da is None):
            if self._wlan_da != packet["wlan.da"]:
                self.stats.wlan_da_mismatch += 1

        if not(self._user_prio is None):
            if self._user_prio != packet["NA YET"]:
                self.stats.user_prio_mismatch += 1


        if not(self._data_rate is None):
            if self._data_rate != packet["radiotap.datarate"]:
                self.stats.data_rate_mismatch += 1
 

    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.stats = Statistics()

        return super(TC_SDK_LINK, self).__init__(methodName, param)

   
    def test_link_tx_rx(self):
        """ Test link layer Tx and Rx
            @fn         test_link_tx_rx
            @brief      Verify tx nd rx abilites
            @details    Test ID	    : TC_SDK3.0_LINK_01
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx\n
        """
        log = logging.getLogger(__name__)

        # unit configuration 


        #Additional scenario details:
        #HDOP < 5

        #Get position data that described in table below via NAV API.
        
        self._gps_scenario = self.param.get('gps_scenario', "" )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        self._gps_lock_timeout_sec = self.param.get('gps_lock_timeout_sec', 600 )



        self._frame_type = self.param.get('frame_type', 'data' )
        self._proto_id = self.param.get('proto_id', 0x1234 )
        
        self._frames_to_send = self.param.get('frames', 100 )
        self._frame_rate_hz = self.param.get('frame_rate_hz', 10 )

        self._tx_data_len = self.param.get('tx_data_len', 30 )
        self._tx_data_val = self.param.get('tx_data_val', 'a' )

        self._wlan_da = self.param.get('dest_addr', None )
        self._user_prio  = self.param.get('user_priority', None )
        self._data_rate  = self.param.get('data_rate', None )
        self._power_dbm8  = self.param.get('power_dbm8', None )
 


        self._tx_pwr_chnl = self.param.get('tx_power', 0 )
        self._freq = self.param.get('freq', 5880)

        
        # uuts = dict( dict( tx = (0,1), rx = (0,2) ) , dict( tx = (3,2), rx = (4,1) ) )
        self._uuts = self.param.get('uuts', None )
        if self._uuts is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uuts = dict( tx = ( (0,1), (0,2) ), rx = ( (1,1), (1,2) ) )")

        # Retreive all uuts 
        g = list()
        for pair in self._uuts:
            for dir in pair:
                uut = pair[dir]
                g.append(uut[0])
        # ignore duplicate uuts ids
        self._uut_list = set(g)

        self._uut = {}
        # Verify uut idx exits and get uut object
        for uut_idx in self._uut_list:
            try:
                self._uut[uut_idx] = globals.setup.units.unit(uut_idx)
            except KeyError as e:
                raise globals.Error("uut index and interface input is missing or currpted, usage : _uut_id_tx=(0,1)")

  
        def test_initilization(self):
  
            # Get sniffer handle from setup
            log.info("Getting Sniffer info")
            if globals.setup.instruments.sniffer is None:
                raise globals.Error("Sniffer is not initilize or define in setup, please check your configuration")
            else:
                # Get pointer to object
                self.sniffer = globals.setup.instruments.sniffer

            # initlize sniffer
            self.sniffer.initialize()

            # Only if GPS scenraio is valid
            if bool(len(self._gps_scenario)):
                log.info("Getting GPS simulator in config")
                if globals.setup.instruments.gps_simulator is None:
                    raise globals.Error("gps simulator is not initilize, please check your configuration")
                else:
                    # Get pointer to object
                    self.gps_sim = globals.setup.instruments.gps_simulator

                # set general tx power
                self.gps_sim.tx_power( self._gps_tx_power )  
                #load scenario
                self.gps_sim.load( self._gps_scenario )



            dir_name = tempfile.gettempdir()
            timestr = time.strftime("%Y%m%d-%H%M%S")
            self.test_file_name = 'tc_sdk_link'
            self.gps_file = os.path.join( tempfile.gettempdir(), self.test_file_name + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')
            self.sniffer_file = os.path.join( common.SNIFFER_DRIVE , self.test_file_name + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap')


        # Main test action
        def test_main(self):
           
            # Start gps scenario without recording
            if bool(len(self._gps_scenario)):
                self.gps_sim.start_scenario()
 
                log.info("Start loop waiting GPS Lock, max time {}.format(self.gps_lock_timeout_sec) )")
                start_time = time.time()
                while ( (time.time() - start_time) < self.gps_lock_timeout_sec ):
                    if (self.uut.managment.get_nav_fix_available() == 1):
                        self.gps_lock = True 
                        log.info("GPS locked O.K.")
                        break
                    time.sleep(0.2)
 
        
                # Add Gps lock limit     
                self.add_limit( "GPS Locked" , 1 , int(self.gps_lock), None , 'EQ')
        
                if self.gps_lock == False:
                    log.info("GPS Lock failed")
                    return 

                # Start recording gps simulator scenraio data
                self.gps_sim.start_recording( gps_file )

            # start recording 
            self.sniffer.start_capture( file_name = self.sniffer_file )


            # Config rx uut
            for pair in self._uuts:
                uut_id, rf_if = pair['rx']
                  
                self._uut[uut_id].create_qa_cli('rx')
                # Open general session
                self._uut[uut_id].qa_cli('rx').session_open()
                # Open sdk Link
                self._uut[uut_id].qa_cli('rx').link_open(rf_if, self._frame_type, self._proto_id)
                self._uut[uut_id].qa_cli('rx').link_rx( self._frames_to_send )
                # Get start counters
                self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )
                self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )
                # Set Rf Frequenct
                self._uut[uut_id].managment.set_rf_frequency( self._freq  , rf_if )

            
            self.tx_data = self._tx_data_len *  self._tx_data_val 
            # Config tx uut
            for pair in self._uuts:
                uut_id, rf_if = pair['tx']
                # Configure the Tx power 
                self._uut[uut_id].managment.set_tx_power( self._tx_pwr_chnl, rf_if )

                # Get start counters
                self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )
                self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )

                self._uut[uut_id].create_qa_cli('tx')
                self._uut[uut_id].qa_cli('tx').session_open()
                self._uut[uut_id].qa_cli('tx').link_open(rf_if, self._frame_type, self._proto_id)
                self._uut[uut_id].qa_cli('tx').link_tx(self.tx_data , frames = self._frames_to_send, rate_hz = self._frame_rate_hz)
                # Set Rf Frequenct
                self._uut[uut_id].managment.set_rf_frequency( self._freq  , rf_if )

            
                
            transmit_time  = int(float( 1.0 / self._frame_rate_hz) *  self._frames_to_send)
            start_time = int(time.clock())
            frm_cnt = 0
            while True:
                # Start Reading from RX unit
                data = self._uut[uut_id].qa_cli('rx').interface().read_until('\r\n', timeout = 1)
                if 'Frame' in data:
                    frm_cnt += 1
                    self.stats.total_frames_processed += 1
             
                    frame = data.split(',')
                    frame_id = int(frame[0].split(':')[1])
                    if frame_id != frm_cnt:
                        self.stats.frame_seq_err += 1

                    if self.tx_data.strip() != frame[2].strip():
                         self.stats.data_mismatch += 1


                if frm_cnt >= self._frames_to_send:
                    break
                
                # Timeout
                if ( int(time.clock()) - start_time ) > (transmit_time + int(transmit_time * 0.1)):
                    break

                    

            # Get Counter at the End of transmition           
            for pair in self._uuts:
                for dir in ['tx', 'rx']:
                    uut_id, rf_if = pair[dir]
                    self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = int(self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )) - int(self.stats.uut_counters[uut_id][rf_if]['rx_cnt'])
                    self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = int(self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )) - int(self.stats.uut_counters[uut_id][rf_if]['tx_cnt'])





            #stop and clean
            if bool(len(self._gps_scenario)):
                self.gps_sim.stop_scenario()
                self.gps_sim.stop_recording()

            self.sniffer.stop_capture()

        def test_debug_overide(self):


            # DEBUG ONLY !!!!!!!   override for tests !!!!!
            #nav_file_recorder = "C:\\Users\\shochats\\AppData\\Local\\Temp\\nav_data_20130702-150427.txt"
            self.gps_file = "C:\\Users\\shochats\\AppData\\Local\\Temp\\gps_rec_20130702-150427.txt"
            self.sniffer_file = "I:\\hbe.pcap"


            print "GPS log file : %s\n\r" % self.gps_file
            print "NAV_FIX log file : %s\n\r" % self.sniffer_file

        # Start analyzer


        def test_analyze_results(self):


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

            # Start analyze the counters



        test_initilization(self)
        test_main(self)
        # test_debug_overide(self)
        test_analyze_results(self)

        self.add_limit( "Total Frames Sent" , self._frames_to_send , self._frames_to_send, None , 'GT')    
        self.add_limit( "Frame Rate (hz)" , self._frame_rate_hz , self._frame_rate_hz, None , 'EQ')    
        self.add_limit( "Total Frames Proceesed" , self._frames_to_send, self.stats.total_frames_processed, None , 'EQ')    
        self.add_limit( "Total Frames on RX data errors" ,0, self.stats.data_mismatch, None , 'EQ')    

        for pair in self._uuts:
            for dir in ['rx']:
                uut_id, rf_if = pair[dir]
                self.add_limit( "uut %d, rf if %d, %s counter" % ( uut_id, rf_if, dir)  ,self._frames_to_send, self.stats.uut_counters[uut_id][rf_if]['rx_cnt'], None , 'EQ')

        
        self.add_limit( "Total Frames Prccessed on Sniffer" , self._frames_to_send , self.stats.total_sniffer_frames_processed, None , 'EQ')    

        if self.stats.sniffer_data_fail:
            self.add_limit( "Total Frames on Data error" ,0, self.stats.sniffer_data_fail, None , 'EQ')    

        if self.stats.wlan_da_mismatch:
            self.add_limit( "Total Frames on DA error" ,0, self.stats.wlan_da_mismatch, None , 'EQ')    
        if self.stats.user_prio_mismatch:
            self.add_limit( "Total Frames on Priority error" ,0, self.stats.user_prio_mismatch, None , 'EQ')    
        if self.stats.data_rate_mismatch:
            self.add_limit( "Total Frames on Rate error" ,0, self.stats.data_rate_mismatch, None , 'EQ')    
        
        
        print "test_completed"
  
def tree(): return defaultdict(tree)
       
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
        self.data_rate_mismatch =0 
