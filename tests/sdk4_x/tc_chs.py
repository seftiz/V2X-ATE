"""
@file       tc_chs.py
@brief      Testsuite for testing channel switching
@author    	zohar
@version	1.0
@date		Dec 2015
\link		
"""

# import global and general setup var
import signal, os
from lib import globals, station_setup, instruments_manager, packet_analyzer
from uuts import common
from tests import common, dsrc_definitions
from uuts.craton.snmp import snmp 
from utilities import panagea4_sniffer
from array import array
from uuts.craton.snmp import snmp 
import pyshark
from lib.instruments import traffic_generator

# Define tree for 3 layer array
from collections import defaultdict
def tree(): return defaultdict(tree)

import threading

import sys, os, time
from datetime import datetime
import logging
import tempfile
import decimal

BASE_HOST_PORT = 8030


log = logging.getLogger(__name__)


class TC_CHS_01(common.V2X_SDKBaseTest):
    """
    @file       tc_chs.py
    @brief      Testsuite for testing channel switching
    @author    	zohar
    @version	1.0
    @date		Dec 2015
    """
    
    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self.active_cli_list = []
        self._uut = []
        self.sniffer_file = []
        self._last_frame_info = {'last_rfif' : 0, 'last_rfif_first_frame_ts' : 0, 'last_rfif_frame_id' : 0, 'last_rfif_last_frame_ts' : 0, 'last_rfif_sa' : 0, 'last_rfif_first_frame_id' : 0}
        self.sniffers = []
        self._not_use_gps_time_sync = False
        self.uut = None
        self.cs_tg_link = None
        self.bsm_tg_link = None
        self.cs_sniffer = None
        self.bsm_sniffer = None
        self.tgs = []
        self._first_frame_if_idx = None
        return super(TC_CHS_01, self).__init__(methodName, param)

    def runTest(self):
        pass

    def setUp(self):
        super(TC_CHS_01, self).setUp()
        pass

    def tearDown(self):
        super(TC_CHS_01, self).tearDown()

        for cli in self.active_cli_list:
            try:
                uut_id, rf_if, cli_name = cli
                # close link session
                self.uut.qa_cli(cli_name).link.socket_delete()
                self.uut.qa_cli(cli_name).link.service_delete()
            except Exception as e:
                print >> self.result._original_stdout, "ERROR in tearDown,  Failed to delete socket on uut {} for cli {}".format( uut_id, cli_name )
                log.error( "ERROR in tearDown,  Failed to clean uut {} for cli {}".format(uut_id, cli_name) )
            finally:
                self.uut.close_qa_cli(cli_name)
    
    def extract_frame_common_params(self, rf_if, sniffer_id):

        if rf_if == globals.RF_IF_2_PHYSICAL and sniffer_id == globals.CHS_SNIF_CS_ID:
            proto_id = self._sch_proto_id
            freq = self._sch_band
            interval = self._cs_interval
        elif rf_if == globals.RF_IF_1_PHYSICAL and sniffer_id == globals.CHS_SNIF_CS_ID:
            proto_id = self._cch_proto_id
            freq = self._cch_band
            interval = self._cs_interval
        elif rf_if == globals.RF_IF_1_PHYSICAL and sniffer_id == globals.CHS_SNIF_BSM_ID:
            proto_id = self._bsm_proto_id
            freq = self._bsm_band
            interval = self._cs_interval
        else:
            return ()
        return (interval, freq, proto_id)

    def handle_chs_event(self, interval, sniffer_id, rf_if, packet):

                #check if actual Tx frames equales to expected...
        if (((self._last_frame_info['last_rfif_frame_id'] - self._last_frame_info['last_rfif_first_frame_id']) + 1) != self._chs_interval_max_expected_frames * 2):
             self.stats.counters[sniffer_id][rf_if]['chs_interval_expected_frames_fail_count'] +=1
               #check CHS interval
        if ((((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) > (int(interval) - globals.CHS_GI_MS)) and
           ((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) <= self._cs_interval)) or ((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) < (int(interval) - globals.CHS_GI_MS)) or
            ((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) > self._cs_interval)):
                 self.stats.counters[sniffer_id][rf_if]['chs_interval_expected_to_fail_count'] +=1
            #check activity during GI 
        if not((int(packet.radiotap.mactime) / 1000) - self._last_frame_info['last_rfif_last_frame_ts'] >= globals.CHS_GI_MS):
                  self.stats.counters[sniffer_id][rf_if]['chs_tx_during_gi_fail_count'] +=1


        
        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "chs_new_freq_tx_to_interval", ((int(packet.radiotap.mactime) / 1000) - self._last_frame_info['last_rfif_last_frame_ts']))
        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "last frame id", self._last_frame_info['last_rfif_frame_id'])
        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "chs_interval_frames", ((self._last_frame_info['last_rfif_frame_id'] - self._last_frame_info['last_rfif_first_frame_id']) + 1))
        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "chs_to_interval_between_first_and_last", self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts'])

    def check_is_wlan_ack_frame( self, packet ):
        try:
            fc_type = int(packet.wlan.fc_type)
            fc_subtype = int(packet.wlan.fc_subtype)

            if ( fc_type == 1 and fc_subtype == 13 ):
                return True
        except Exception:
            pass

        return False

    def packet_handler(self, packet):

        if self.check_is_wlan_ack_frame(packet):
            self.stats.total_unicast_ack_frames += 1
            return

        self.stats.total_sniffer_frames_processed += 1

        packet_if_id = int(packet.radiotap.antenna) & 0x0F
        packet_if_id +=1
        id = (int(packet.radiotap.antenna) & 0xF0)>>4 
        for tg in self.tgs:
            if tg.sniffer.id == id:
                break
        # Test packet data
        try:
            packet_data = ''.join(packet.data.data.split(':')).encode('ascii','ignore').upper()
        except Exception as e:
            self.stats.counters[tg.sniffer.id][packet_if_id]['sniffer_data_read_fail'] +=1
            #count total frames and data (amount in bytes)
            self.stats.counters[tg.sniffer.id][packet_if_id]['total_frames'] += 1
            self.stats.counters[tg.sniffer.id][packet_if_id]['total_data'] += int(packet.data.len)
        else:
            # Compare data with transmited Data after extracting crc and extracting Tx buffer 
            if len(packet_data[:8]) != self._payload_len:
                self.stats.counters[tg.sniffer.id][packet_if_id]['sniffer_data_payload_len_fail'] += 1
                #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", tg.sniffer.id, "rf_id", packet_if_id, "packet_data len", len(packet_data[:-8]))
            a = []
            a = interval, freq, proto_id = self.extract_frame_common_params(packet_if_id, tg.sniffer.id)
            if not (bool(len(a))):
                self.stats.counters[sniffer_id][rf_if]['chs_setup_failure'] += 1
                return
            #test protocol id
            if int(packet.llc.type, 16) != int(proto_id):
                self.stats.counters[tg.sniffer.id][packet_if_id]['sniffer_proto_fail'] += 1
                print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", tg.sniffer.id, "rf_id", packet_if_id, "proto_id", packet.llc.type)

            #handle channel switching packet
            if tg.sniffer.id == globals.CHS_SNIF_CS_ID:
                
                #handle first frame in the test - save its if idx and skip testing since tx start vs CS interval start period are not synchronized... 
                if int(packet.frame_info.number) == 1:
                    self._first_frame_if_idx = packet_if_id
               
                
                #while first if idx skip testing but continue taking counters...
                if packet_if_id == self._first_frame_if_idx:
                    self.stats.counters[tg.sniffer.id][packet_if_id]['total_frames'] += 1
                    self.stats.counters[tg.sniffer.id][packet_if_id]['total_data'] += int(packet.data.len)
                    return

                if  self._first_frame_if_idx != None:
                    #reset the first frame if idx flag
                    self._first_frame_if_idx = None   
                    self._last_frame_info['last_rfif_first_frame_ts'] = int(packet.radiotap.mactime) / 1000
                    self._last_frame_info['last_rfif'] = packet_if_id
                    self._last_frame_info['last_rfif_last_frame_ts'] = self._last_frame_info['last_rfif_first_frame_ts']
                    self._last_frame_info['last_rfif_frame_id'] = int(packet.frame_info.number) 
                    self._last_frame_info['last_rfif_first_frame_id'] = int(packet.frame_info.number)

                #if CS occured - start testing last interval parameters and gi between inter freq HO    
                if self._last_frame_info['last_rfif'] != packet_if_id:
                   
                   #handle channel switching tests according to TP
                   self.handle_chs_event(interval, tg.sniffer.id, packet_if_id, packet)

                   #cs - update next freq interval first frame ts...
                   self._last_frame_info['last_rfif_first_frame_ts'] = int(packet.radiotap.mactime) / 1000 
                   #self._last_frame_info['last_rfif_first_frame_ts'] = int(float(packet.frame_info.time_epoch) * 1000)
                   self._last_frame_info['last_rfif_first_frame_id'] = int(packet.frame_info.number)
                #update last frame info
                self._last_frame_info['last_rfif'] = packet_if_id
                self._last_frame_info['last_rfif_last_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
                #self._last_frame_info['last_rfif_last_frame_ts'] = int(float(packet.frame_info.time_epoch) * 1000)
                self._last_frame_info['last_rfif_frame_id'] = int(packet.frame_info.number)
                
            #count total frames and data (amount in bytes)
            self.stats.counters[tg.sniffer.id][packet_if_id]['total_frames'] += 1
            self.stats.counters[tg.sniffer.id][packet_if_id]['total_data'] += int(packet.data.len)

    def get_test_parameters( self ):
      
        super(TC_CHS_01, self).get_test_parameters()
      
        # Set Some test defaults 
        self._bsm_band       = self.param.get('bsm_band', 5890 )
        self._cch_band      = self.param.get('cch_band', 5920 )
        self._sch_band      = self.param.get('sch_band', 5900 )
        self._sch2_band      = self.param.get('sch2_band', 5870 )
        self._sch_proto_id   = self.param.get('sch_proto_id', 0x1234 )
        self._cch_proto_id   = self.param.get('cch_proto_id', 0x5678 )
        self._frame_rate_hz  = self.param.get('frame_rate_hz', 2000 )
        self._expected_frames         = self.param.get('expected_frames', 500 )
        self._cs_interval  = self.param.get('cs_interval', 50 )
        self._payload_len         = self.param.get('payload_len', 330 )
        self._chs_interval_max_expected_frames = self.param.get('chs_interval_max_expected_frames', 100 )
        self._bsm_proto_id = self.param.get('bsm_proto_id', 0x9abc )
        self._sync_tolerance = self.param.get('sync_tolerance', 2 )
        self._gps_lock_timeout_sec = self.param.get('gps_to', 2 )
        self._cs_interval = self.param.get('cs_interval', 50 )

    def test_chs(self):
        """ Test CHS Tx and Rx
            @fn         test_chs
            @brief      Verify CHS works
            @details    Test ID	: TC_SDK4.x_CHS_01
            @see Test Plan	: TBD
        """
        # Get & parse test parameters
        
        self.get_test_parameters()

        # Call Test scenarios blocks
        chs_status = self.initilization()
        if chs_status != globals.CHS_ACTIVE:
            return

        self.main()
        self.analyze_results()
        self.print_results()

    def get_mib_cs_mode(self):
       return self.uut.managment.get_cs_mode(globals.RF_IF_2_PHYSICAL)
   
    def initilization(self):
       
        rc = 0
        # initilize uut
        self.uut = globals.setup.units.unit(globals.CHS_DUT_ID)
        self.unit_configuration()

        self.set_cs_mib_table()

        ## Initilize GPS
        #if self._not_use_gps_time_sync == False:
             
        #    self.gps_sim = self.gps_init(  self._gps_scenario, self._gps_tx_power )
        #    self.gps_file = os.path.join( tempfile.gettempdir(),  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')

        
        self.activate_sniffers()
        self.init_link_tx()
        rc = self.check_chs_activation_status()
        
        return rc

    def _init_sniffers_counters(self, sniffer_id, rf_if):

        self.stats.counters[sniffer_id][rf_if]['chs_interval_expected_frames_fail_count'] = 0
        self.stats.counters[sniffer_id][rf_if]['chs_interval_expected_to_fail_count'] = 0
        self.stats.counters[sniffer_id][rf_if]['chs_tx_during_gi_fail_count'] = 0
        self.stats.counters[sniffer_id][rf_if]['chs_setup_failure'] = 0
        self.stats.counters[sniffer_id][rf_if]['sniffer_data_read_fail'] = 0
        self.stats.counters[sniffer_id][rf_if]['sniffer_data_cmp_fail'] = 0
        self.stats.counters[sniffer_id][rf_if]['total_frames'] = 0
        self.stats.counters[sniffer_id][rf_if]['total_data'] = 0
        self.stats.counters[sniffer_id][rf_if]['sniffer_proto_fail'] = 0
        self.stats.counters[sniffer_id][rf_if]['sniffer_data_payload_len_fail'] = 0
    
    def init_link_tx(self):
        tgs = []
        tgs = globals.setup.instruments.traffic_generators
        for tg in tgs:
            if tg.link.index == globals.CS_TG_ID:
                self.cs_tg_link = tg.link
            elif tg.link.index == globals.BSM_TG_ID: 
                self.bsm_tg_link = tg.link
            tg.link.init()

    def generate_link_tx(self, tg_link, session_id, if_idx, proto_id):
        tg_link.start(session_id, if_idx, proto_id, self._expected_frames, self._frame_rate_hz, self._payload_len, 'data')

    def activate_sniffers(self):

        log.info("Getting Sniffer info")

        self.tgs = globals.setup.instruments.traffic_generators

        for tg in self.tgs:
           
            tg.sniffer.init(tg.sniffer._target_ip, version = "SDK4.x")
            #init and start sniffer for channel switching rf interface (2)
            if tg.sniffer.id == globals.CHS_SNIF_CS_ID:
                self.cs_sniffer = tg.sniffer
                self.cs_sniffer.managment.set_rf_frequency(self._cch_band , 0)
                self.cs_sniffer.managment.set_rf_frequency(self._sch_band , 1)
                self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
                self.cs_sniffer.start(3,  self.sniffer_file[0])
            #init and start sniffer for bsm rf interface (1)
            elif tg.sniffer.id == globals.CHS_SNIF_BSM_ID: 
                self.bsm_sniffer = tg.sniffer
                self.bsm_sniffer.managment.set_rf_frequency(self._bsm_band , 0)
                self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
                self.bsm_sniffer.start(1,  self.sniffer_file[1])
            #reset counters of cs and bsm sniffers
            if tg.sniffer.id in [globals.CHS_SNIF_BSM_ID, globals.CHS_SNIF_CS_ID]:
                for rf_if in [globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL]:
                    self._init_sniffers_counters(tg.sniffer.id, rf_if)
                    tg.sniffer.reset_counters(rf_if);
                 
    def check_chs_activation_status(self):
        return self.get_mib_cs_mode()

    def unit_configuration(self):

        gps_lock = True
        # start gps scenario
        #if self.is_gps_active() and self._not_use_gps_time_sync == False:
        #    self.gps_sim.start_scenario()
        gps_lock &= self.wait_for_gps_lock( self.uut, self._gps_lock_timeout_sec )
        # Add Gps lock limit     
        self.add_limit( "GPS Locked" , int(True) , int(gps_lock), None , 'EQ')
        if gps_lock == False:
            log.info("GPS Lock failed")
        #else:
        #     #Start recording gps simulator scenraio data
        #     self.gps_sim.start_recording( gps_file )

        for rf_if in [globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL, globals.RF_IF_2_VIRTUAL]:

            #dut and sniffers bands and protocol id settings
            if rf_if == globals.RF_IF_1_PHYSICAL:
               proto_id = self._bsm_proto_id
               self.uut.managment.set_rf_frequency( self._bsm_band,  rf_if - 1 )

            elif rf_if == globals.RF_IF_2_PHYSICAL:
               proto_id = self._cch_proto_id
               self.uut.managment.set_rf_frequency( self._cch_band, rf_if - 1 )
 
            elif rf_if == globals.RF_IF_2_VIRTUAL:
               proto_id = self._sch_proto_id

            cli_name = "uut_%d_if_%d_proto_%x" % ( self.uut.idx, rf_if, proto_id )
                
            self.active_cli_list.append( (self.uut.idx, rf_if, cli_name ))

            self.uut.create_qa_cli(cli_name, target_cpu = self.target_cpu)
            # Open general session
            self.uut.qa_cli(cli_name).link.service_create( type = 'remote' if self.uut.external_host else 'hw')
            # Open sdk Link
            self.uut.qa_cli(cli_name).link.socket_create(rf_if - 1, 'data', proto_id)
    
    def start_unit_tx_session(self):

        for cli in self.active_cli_list:
           
            uut_id, rf_if, cli_name = cli

            self.uut.qa_cli(cli_name).link.transmit(tx_data = "CHS", payload_len = self._payload_len, frames = self._expected_frames, rate_hz = self._frame_rate_hz, dest_addr = None)  

    def start_unit_rx_session(self,  time_out):

       for cli in self.active_cli_list:
            uut_id, rf_if, cli_name = cli
            self.uut.qa_cli( cli_name).link.receive( self._expected_frames, print_frame = True, timeout = time_out )

    def stop_refference_sniffers(self):

        if self.cs_sniffer != None:
            #stop both 1 and 2 rf_ifs of CS sniffer (3)
            self.cs_sniffer.stop(3)
        if self.bsm_sniffer != None:
            #stop rf_if 1 of BSM sniffer (1)
            self.bsm_sniffer.stop(1)

    def main(self):


        transmit_time = 0

        # frame_rate_hz = 2000 and frames = 500 we get  250ms this leaves us with 100 frame in 50ms time CS interval per CS frequency
        expected_transmit_time = int(float( 1.0 / self._frame_rate_hz) *  self._expected_frames) + 5

        rx_timeout = ( expected_transmit_time + int(expected_transmit_time * 0.25) ) * 1000
        
        self.start_unit_tx_session()

        time.sleep(expected_transmit_time * 2.5)

        self.stop_refference_sniffers()
        print 'Hault pcap file recording and embedded sniffer client'
    
    def analyze_results(self):
        
        self._test_frm_data = self.get_test_frm_data()

        for sniffer_file in self.sniffer_file:
            cap = pyshark.FileCapture(sniffer_file)
            for frame_idx,frame in  enumerate(cap):
                self.packet_handler(frame)
    def print_results(self):
        self.print_ref_results()

    def print_ref_results(self):
        
        for tg in self.tgs:
            if tg.sniffer.id in [globals.CHS_SNIF_BSM_ID, globals.CHS_SNIF_CS_ID]:
                for rf_if in [globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL]:

                    print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", tg.sniffer.id, "rf_id", rf_if, "total frames", self.stats.counters[tg.sniffer.id][rf_if]['total_frames'])
                    print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", tg.sniffer.id, "rf_id", rf_if, "total data", self.stats.counters[tg.sniffer.id][rf_if]['total_data'])
            
                    self.add_limit( "(sniffer_id#%d, rf_if#%d), protocol id check " % ( tg.sniffer.id, rf_if), 0, self.stats.counters[tg.sniffer.id][rf_if]['sniffer_proto_fail'], None , 'EQ') 
                    self.add_limit( "(sniffer_id#%d, rf_if#%d), data compare check " % ( tg.sniffer.id, rf_if), 0, self.stats.counters[tg.sniffer.id][rf_if]['sniffer_data_cmp_fail'], None , 'EQ')
                    self.add_limit( "(sniffer_id#%d, rf_if#%d), Total Frames Prccessed on Sniffer " % ( tg.sniffer.id, rf_if), self._expected_frames, self.stats.counters[tg.sniffer.id][rf_if]['total_frames'], None , 'EQ') 

                    if tg.sniffer.id == globals.CHS_SNIF_CS_ID:
                        self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx after sync tolerance " % ( tg.sniffer.id, rf_if), 0, self.stats.counters[tg.sniffer.id][rf_if]['chs_setup_failure'], None , 'EQ')
                        self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx interval expected frames " % ( tg.sniffer.id, rf_if), 0, self.stats.counters[tg.sniffer.id][rf_if]['chs_interval_expected_frames_fail_count'] , None , 'EQ') 
                        self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx interval equals to 46-50 ms " % ( tg.sniffer.id, rf_if), 0, self.stats.counters[tg.sniffer.id][rf_if]['chs_interval_expected_to_fail_count'] , None , 'EQ') 
                        self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx during GI " % ( tg.sniffer.id, rf_if), 0, self.stats.counters[tg.sniffer.id][rf_if]['chs_tx_during_gi_fail_count'] , None , 'EQ')
                        self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx data read fail " % ( tg.sniffer.id, rf_if), 0, self.stats.counters[tg.sniffer.id][rf_if]['sniffer_data_read_fail'], None , 'EQ')

    def set_cs_mib_table(self):
        
        # 'wlanCsRowStatus' - set CHS active to 'notInService' before CS MIB configuration
        self.uut.managment.set_cs_mode(globals.CHS_NOT_IN_SERVICE, globals.RF_IF_2_PHYSICAL)

        # 'wlanCsFrequencyA' - Channel A frequency to be used in channel switching.
        self.uut.managment.set_cs_freq_a(globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL, self._bsm_band, self._cch_band)
        self.uut.managment.set_rf_frequency(self._cch_band , 1)
        self.uut.managment.set_rf_frequency(self._bsm_band , 0)


        # 'wlanCsFrequencyB' - Channel B frequency to be used in channel switching.
        self.uut.managment.set_cs_freq_b(globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL, self._bsm_band, self._sch_band)

        # 'wlanCsIntervalA' - Channel A interval
        self.uut.managment.set_cs_interval_a(globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL, self._cs_interval, self._cs_interval)

        # 'wlanCsIntervalB' - Channel B interval
        self.uut.managment.set_cs_interval_b(globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL, self._cs_interval, self._cs_interval)

        # 'wlanCsSyncTolerance' - set CHS inter frequency HO tolerance
        self.uut.managment.set_cs_sync_tolerance(globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL, self._sync_tolerance, self._sync_tolerance)
           
        # 'wlanCsRowStatus' - set CHS active to 'notInService' before CS MIB configuration
        self.uut.managment.set_cs_mode(globals.CHS_ACTIVE, globals.RF_IF_2_PHYSICAL)

    def get_test_frm_data(self):
        
        frm_tx_data = ""
        for chr in range(self._payload_len):
            frm_tx_data += "".join('{:02x}'.format((chr % 0xFF) + 1))

        return frm_tx_data
  
class TC_CHS_02(TC_CHS_01):

    def __init__(self, methodName = 'runTest', param = None):

        self.uut_qa_cli_handle = None
        self.dut_sniffer = None
        self.dut_host_sniffer = None
        self.sniffers_ports = []
        self._first_proto_id = None
        self._first_if_sa = None
        #self._last_if_sa = None
        self._if_dict = {}
        self._current_milli_time = None
        self._current_milli_time = lambda: int(round(time.time() * 1000))
        return super(TC_CHS_02, self).__init__(methodName, param)


    def start_dut_sniffer(self):
      
        self.uut_qa_cli_handle = self.uut.create_qa_cli("sniffer_cli", target_cpu = self.target_cpu)
        #init 'apps' embedded sniffer for DUT rx analysis
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferAppEmbedded(self.uut_qa_cli_handle.interface())
        #add to sniffer list
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(self.uut.idx)
        for rf_if in [globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL]:
            
            sniffer_port = BASE_HOST_PORT + ( self.uut.idx * 17 ) + rf_if
            self.sniffers_ports.append(sniffer_port)
            self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + "DUT_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
            time.sleep(2)
            self.dut_embd_sniffer.start( if_idx = rf_if, server_ip = None, server_port = sniffer_port)
            #use the last appended sniffer  file...
            self.dut_host_sniffer.start( if_idx = rf_if, port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
            self._init_sniffers_counters(self.uut.idx, rf_if)

    def start_tg_link(self):

        if self.bsm_tg_link != None:
            #start TG Tx from BSM TG and from CS TG
            self.bsm_tg_link.start(session_id = 1, if_idx = globals.RF_IF_1_PHYSICAL, protocol_id = self._bsm_proto_id, 
                                   frames = self._expected_frames, rate_hz = self._frame_rate_hz, payload_length = self._payload_len)
        if self.cs_tg_link != None:
            self.cs_tg_link.start(session_id = 2, if_idx = globals.RF_IF_1_PHYSICAL, protocol_id = self._cch_proto_id, 
                                   frames = self._expected_frames, rate_hz = self._frame_rate_hz, payload_length = self._payload_len)

            self.cs_tg_link.start(session_id = 3, if_idx = globals.RF_IF_2_PHYSICAL, protocol_id = self._sch_proto_id, 
                                   frames = self._expected_frames, rate_hz = self._frame_rate_hz, payload_length = self._payload_len)

    def stop_tg_link(self):
        #stop TG Tx from BSM TG and from CS TG

        if self.bsm_tg_link != None:
            self.bsm_tg_link.stop(session_id = 1)
        if self.cs_tg_link != None:
            self.cs_tg_link.stop(session_id = 2)
            self.cs_tg_link.stop(session_id = 3)

    def stop_dut_sniffer(self):

        for rf_if in [globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL]:
            
            self.dut_embd_sniffer.stop(if_idx = rf_if)
            self.dut_host_sniffer.stop(port = self.sniffers_ports[rf_if - 1])

    def main(self):


        transmit_time = 0
        thread_list = []
        tx_hexstr = ""
        # frame_rate_hz = 2000 and frames = 500 we get  250ms this leaves us with 100 frame in 50ms time CS interval per CS frequency
        expected_transmit_time = int(float( 1.0 / self._frame_rate_hz) *  self._expected_frames) + 5

        rx_timeout = ( expected_transmit_time + int(expected_transmit_time * 0.25) ) * 1000

        #start Rx for both CS channels and BSM channel
        self.start_unit_rx_session(rx_timeout)
                        
        #Start DUT sniffer
        self.start_dut_sniffer()
        
        #start tg link
        self.start_tg_link()
        
        time.sleep(expected_transmit_time * 2)

        self.stop_tg_link()
        self.stop_dut_sniffer()
        self.stop_refference_sniffers()

    def extract_dut_rx_frame_common_params(self, rf_if):

        if rf_if == globals.RF_IF_2_PHYSICAL:
            proto_id = self._sch_proto_id
            freq = self._sch_band
            interval = self._cs_interval
        elif rf_if == globals.RF_IF_2_VIRTUAL:
            proto_id = self._cch_proto_id
            freq = self._cch_band
            interval = self._cs_interval
        else:
            proto_id = -1
            freq = -1
            interval = -1
        return (interval, freq, proto_id)

    def handle_dut_rx_chs_event(self, packet, sniffer_id, rf_if):

        # check if actual Tx frames equales to expected...
        if (((self._last_frame_info['last_rfif_frame_id'] - self._last_frame_info['last_rfif_first_frame_id']) + 1) != self._chs_interval_max_expected_frames):
             self.stats.counters[sniffer_id][rf_if]['chs_interval_expected_frames_fail_count'] +=1

        ## check CHS interval
        #if ((((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) > (self._cs_interval - globals.CHS_GI_MS)) and ((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) <= self._cs_interval)) or
        #    ((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) < (self._cs_interval - globals.CHS_GI_MS)) or
        #    ((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) > self._cs_interval)):
        #         self.stats.counters[sniffer_id][rf_if]['chs_interval_expected_to_fail_count'] +=1

        if not(((int(packet.radiotap.mactime) / 1000) - self._last_frame_info['last_rfif_last_frame_ts'] <= (self._sync_tolerance / 2)) or
               (((int(packet.radiotap.mactime) / 1000) - self._last_frame_info['last_rfif_last_frame_ts']) >= (self._sync_tolerance / 2) + globals.CHS_MAX_SWITCH_TIME)):
                  self.stats.counters[sniffer_id][rf_if]['chs_tx_during_gi_fail_count'] +=1

        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "chs_new_freq_tx_to_interval", ((int(packet.radiotap.mactime) / 1000) - self._last_frame_info['last_rfif_last_frame_ts']))
        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "last frame id", self._last_frame_info['last_rfif_frame_id'])
        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "chs_interval_frames", ((self._last_frame_info['last_rfif_frame_id'] - self._last_frame_info['last_rfif_first_frame_id']) + 1))
        #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id", sniffer_id, "rf_id", rf_if, "chs_to_interval_between_first_and_last", self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts'])




    def dut_rx_packet_handler(self, packet):

        if self.check_is_wlan_ack_frame(packet):
            self.stats.total_unicast_ack_frames += 1
            return

        self.stats.total_sniffer_frames_processed += 1

        packet_if_id = int(packet.radiotap.antenna) & 0x0F
        packet_if_id +=1

        #handle first frame in the test
        if int(packet.frame_info.number) == 1:
            self._first_if_sa = packet.wlan.sa
            self._last_frame_info['last_rfif_sa'] = packet.wlan.sa
            #all frames comes on the same physical rf interface - '2' need to destinguish between them...
            self._if_dict[packet.wlan.sa] = 1
        #we do not know where in the time sequence of the Rx CS interval the transmission started so we skipp first protocol id testing and starting from the second
        if packet.wlan.sa == self._first_if_sa:
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_data'] += int(packet.data.len)
            return
        #check if this is the first if sa change and set the second interface for test
        if self._first_if_sa  != None:
            self._if_dict[packet.wlan.sa] = 2

        # Test packet data
        try:
            packet_data = ''.join(packet.data.data.split(':')).encode('ascii','ignore').upper()
        except Exception as e:
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['sniffer_data_read_fail'] +=1
            #count total frames and data (amount in bytes)
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_data'] += int(packet.data.len)
        else:
            # Compare data with transmited Data after extracting crc and extracting Tx buffer (sequence_id, frame_size, frame_options)...
            if packet_data[16:-8] != self._test_frm_data.upper():
                self.stats.counters[self.uut.idx][self._if_dict[packet.wlan.sa]]['sniffer_data_cmp_fail'] += 1
            if len(packet_data[:8]) != self._payload_len:
                self.stats.counters[self.uut.idx][self._if_dict[packet.wlan.sa]]['sniffer_data_payload_len_fail'] += 1
                #print "{} = {}\t\t{} = {}\t\t{} = {}".format ("sniffer_id",  self.uut.idx, "rf_id", self._if_dict[packet.wlan.sa], "packet_data len", len(packet_data[:-8]))


            #if  packet.wlan.sa !=  self._last_if_sa:
            if  packet.wlan.sa !=  self._last_frame_info['last_rfif_sa']:
                # handle first CS - this is the testing starting point...
                if self._first_if_sa  != None:
                    self._first_if_sa  = None
                    #arrival time of last frame
                    #self._last_frame_info['last_rfif_last_frame_ts'] = int(float(packet.frame_info.time_epoch) * 1000)
                    self._last_frame_info['last_rfif_last_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
                    #frame id of last frame
                    self._last_frame_info['last_rfif_frame_id'] = int(packet.frame_info.number)
                    self._last_frame_info['last_rfif_first_frame_id'] = int(packet.frame_info.number)

                    #self._last_frame_info['last_rfif_first_frame_ts']  = int(float(packet.frame_info.time_epoch) * 1000)
                    self._last_frame_info['last_rfif_first_frame_ts']  = (int(packet.radiotap.mactime) / 1000)
                    self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
                    self._last_frame_info['last_rfif_sa'] = packet.wlan.sa
                    #self._last_if_sa = packet.wlan.sa
                    return
        
                #if self._last_frame_info['last_rfif_first_frame_ts'] > 0:
                self.handle_dut_rx_chs_event(packet,  self.uut.idx, self._if_dict[packet.wlan.sa])

                #arrival time of first frame of the interval
                #self._last_frame_info['last_rfif_first_frame_ts'] = int(float(packet.frame_info.time_epoch) * 1000)
                self._last_frame_info['last_rfif_first_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
                self._last_frame_info['last_rfif_first_frame_id'] = int(packet.frame_info.number)
            #arrival time of last frame
            #self._last_frame_info['last_rfif_last_frame_ts'] = int(float(packet.frame_info.time_epoch) * 1000)
            self._last_frame_info['last_rfif_last_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
            #frame id of last frame
            self._last_frame_info['last_rfif_frame_id'] = int(packet.frame_info.number)
            self._last_frame_info['last_rfif_sa'] = packet.wlan.sa
            #self._last_if_sa = packet.wlan.sa 
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_data'] += int(packet.data.len)

    def analyze_results(self):
        
        self._test_frm_data = self.get_test_frm_data()
        # analyze last file only - DUT rf_if 2 (CS)
        cap = pyshark.FileCapture(self.sniffer_file[len(self.sniffer_file) - 1])
        for frame_idx,frame in  enumerate(cap):
            self.dut_rx_packet_handler(frame)

    def print_results(self):
        self.print_dut_results()

    def print_dut_results(self):
        for rf_if in [globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL]:

            print "{} = {}\t\t{} = {}\t\t{} = {}".format ("dut_sniffer_id", self.uut.idx, "rf_id", rf_if, "total frames", self.stats.counters[self.uut.idx][rf_if]['total_frames'])
            print "{} = {}\t\t{} = {}\t\t{} = {}".format ("dut_sniffer_id", self.uut.idx, "rf_id", rf_if, "total data", self.stats.counters[self.uut.idx][rf_if]['total_data'])
            
            self.add_limit( "(DUT Rx, rf_if#%d), Rx interval expected frames " % ( rf_if), 0, self.stats.counters[self.uut.idx][rf_if]['chs_interval_expected_frames_fail_count'] , None , 'EQ') 
            #self.add_limit( "(DUT Rx, rf_if#%d), data compare check " % ( rf_if), 0, self.stats.counters[self.uut.idx][rf_if]['sniffer_data_cmp_fail'], None , 'EQ')
            self.add_limit( "(DUT Rx, rf_if#%d), Total Rx Frames " % ( rf_if), (int(self._expected_frames / 2)), self.stats.counters[self.uut.idx][rf_if]['total_frames'], None , 'EQ') 
            self.add_limit( "(DUT Rx, rf_if#%d), Rx during CS Switch Time " % ( rf_if), 0, self.stats.counters[self.uut.idx][rf_if]['chs_tx_during_gi_fail_count'] , None , 'EQ')
            self.add_limit( "(DUT Rx, rf_if#%d), Rx data read fail " % ( rf_if), 0, self.stats.counters[self.uut.idx][rf_if]['sniffer_data_read_fail'], None , 'EQ')


class TC_CHS_08(TC_CHS_02):

    def __init__(self, methodName = 'runTest', param = None):
        return super(TC_CHS_08, self).__init__(methodName, param)

    def main(self):

        # frame_rate_hz = 2000 and frames = 500 we get  250ms this leaves us with 100 frame in 50ms time CS interval per CS frequency
        expected_transmit_time = int(float( 1.0 / self._frame_rate_hz) *  self._expected_frames) + 5

        rx_timeout = ( expected_transmit_time + int(expected_transmit_time * 0.25) ) * 1000
        
        self.start_unit_tx_session()

        time.sleep(1)
        #start Rx for both CS channels and BSM channel
        self.start_unit_rx_session(rx_timeout)

        #Start DUT sniffer
        self.start_dut_sniffer()
        
        time.sleep(1)
        #start tg link
        self.start_tg_link()
        
        time.sleep(expected_transmit_time * 2)

        self.stop_tg_link()
        self.stop_dut_sniffer()
        self.stop_refference_sniffers()

    def analyze_results(self):
        
        self._test_frm_data = self.get_test_frm_data()

        for sniffer_file in self.sniffer_file:
            cap = pyshark.FileCapture(sniffer_file)
            for frame_idx,frame in  enumerate(cap):
                if sniffer_file.find("DUT") == -1:
                    self.packet_handler(frame)
                else:
                    self.dut_rx_packet_handler(frame)

    def print_results(self):
        self.print_ref_results()
        self.print_dut_results()


class TC_CHS_09(TC_CHS_08):

    def __init__(self, methodName = 'runTest', param = None):
        return super(TC_CHS_09, self).__init__(methodName, param)

    def main(self):

        # frame_rate_hz = 2000 and frames = 500 we get  250ms this leaves us with 100 frame in 50ms time CS interval per CS frequency
        expected_transmit_time = int(float( 1.0 / self._frame_rate_hz) *  self._expected_frames) + 5

        rx_timeout = ( expected_transmit_time + int(expected_transmit_time * 0.25) ) * 1000

        t = threading.Thread( target = self.change_cs_freqB_each_100ms, args = (expected_transmit_time,))
        t.start()

        self.start_unit_tx_session()

        time.sleep(1)
        #start Rx for both CS channels and BSM channel
        self.start_unit_rx_session(rx_timeout)

        #Start DUT sniffer
        self.start_dut_sniffer()
        
        time.sleep(1)
        #start tg link
        self.start_tg_link()
        
        time.sleep(expected_transmit_time * 2)

        t.join()
        self.stop_tg_link()
        self.stop_dut_sniffer()
        self.stop_refference_sniffers()

    def change_cs_freqB_each_100ms(self, expected_transmit_time):
       thread_start_ts = datetime.now()
       sch_band = [self._sch_band, self._sch2_band]
       i = 1
       while(1):
           start_interval = datetime.now()
           i %= 2
           thread_elapsed_time = start_interval - thread_start_ts
           #stop thread when thread elapsed time reaches expected transmit time
           if thread_elapsed_time.seconds >= expected_transmit_time:
              break
           while(1):
               end_interval = datetime.now()
               interval = end_interval - start_interval
               #each 100ms change CS rf interface frequency and TG transmitter rf interface 2 to the same frequency
               if ((interval.microseconds)/1000) >= 100:
                   # 'wlanCsFrequencyB' - Channel B frequency to be used in channel switching.
                   print "change SCH freq {}".format(i)
                   self.uut.managment.set_cs_freq_b(globals.RF_IF_1_PHYSICAL, globals.RF_IF_2_PHYSICAL, self._bsm_band, sch_band[i])
                   self.cs_tg_link.managment.set_rf_frequency(sch_band[i], globals.RF_IF_2_PHYSICAL)
                   i += 1
                   break

class TC_CHS_10(TC_CHS_08):

    def __init__(self, methodName = 'runTest', param = None):
        return super(TC_CHS_10, self).__init__(methodName, param)

    def main(self):

        # frame_rate_hz = 2000 and frames = 500 we get  250ms this leaves us with 100 frame in 50ms time CS interval per CS frequency
        expected_transmit_time = int(float( 1.0 / self._frame_rate_hz) *  self._expected_frames) + 5

        rx_timeout = ( expected_transmit_time + int(expected_transmit_time * 0.25) ) * 1000

        t = threading.Thread( target = self.change_channels_rate_100ms, args = (expected_transmit_time,))
        t.start()

        self.start_unit_tx_session()

        time.sleep(1)
        #start Rx for both CS channels and BSM channel
        self.start_unit_rx_session(rx_timeout)

        #Start DUT sniffer
        self.start_dut_sniffer()
        
        time.sleep(1)
        #start tg link
        self.start_tg_link()
        
        time.sleep(expected_transmit_time * 2)

        t.join()
        self.stop_tg_link()
        self.stop_dut_sniffer()
        self.stop_refference_sniffers()

    def change_channels_rate_100ms(self, expected_transmit_time):
       thread_start_ts = datetime.now()
       rate = [12, 6]
       i = 1
       while(1):
           start_interval = datetime.now()
           i %= 2
           thread_elapsed_time = start_interval - thread_start_ts
           #stop thread when thread elapsed time reaches expected transmit time
           if thread_elapsed_time.seconds >= expected_transmit_time:
               break
           while(1):
               end_interval = datetime.now()
               interval = end_interval - start_interval
               #each 100ms change CS rf interface frequency and TG transmitter rf interface 2 to the same frequency
               if ((interval.microseconds)/1000) >= 100:
                   # 'wlanCsFrequencyB' - Channel B frequency to be used in channel switching.
                   self.uut.managment.set_rf_rate(rate[i], globals.RF_IF_2_PHYSICAL) 
                   self.cs_tg_link.managment.set_rf_rate(rate[i], globals.RF_IF_2_PHYSICAL)
                   self.cs_tg_link.managment.set_rf_rate(rate[i], globals.RF_IF_1_PHYSICAL)
                   i += 1
                   break



class frameStatistics(object):
    pass

class Statistics(object):

 
    def __init__(self):
        # Total frame process in the wireshark file
        self.total_frames_processed = 0
        self.frame_seq_err = 0
        self.data_mismatch = tree()
        self.counters = tree()
        self.bad_ch_type = tree()
        self.total_sniffer_frames_processed = 0
        self.total_unicast_ack_frames = 0
        self.sniffer_data_fail = 0
        self.wlan_da_mismatch = 0
        self.user_prio_mismatch = 0
        self.data_band_mismatch = tree()
        self.total_tx_expected = 0
        self.tx_count = 0
        self.sniffer_proto_fail = 0
        self.total_frames_processed = tree()
        self.frame_fields = frameStatistics()
        self.total_tx_time_exceed = tree()
        self.total_frame_cnt_exceed = tree()
