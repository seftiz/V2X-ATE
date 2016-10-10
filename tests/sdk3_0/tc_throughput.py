"""
@file       tc_sdk_link.py
@brief      Testsuite for testing sdk link layer module  
@author    	Shai Shochat
@version	1.0
@date		Nov 2013
\link		http://marge/trac/wavesys/wiki/ate/tp/sdk-link-throughput
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

from lib import globals

import sys, os
import time
import math
from datetime import datetime
import logging
import tempfile
import decimal


MAX_FRAMES_RATE = 500
# Define maximum iterations for searching
MAX_SEARCH_ITERATION = 10


class ProceesedFramesCompleted(Exception):
    pass

class TC_SDK_LINK_THROUGHPUT(common.V2X_SDKBaseTest):
    """
    @class TC_LINK_THROUGHPUT
    @brief Search best throughput for link socket
    @author Shai Shochat
    @version 0.1
    @date	03/09/2013
    """

    def runTest(self):
        pass

    def tearDown(self):

        for cli in self.active_cli_list:
            uut_id, rf_if, cli_name = cli
            # close link session
            self._uut[uut_id].qa_cli(cli_name).link_close()
            # close general session
            self._uut[uut_id].qa_cli(cli_name).session_close()
            # Close sdk Link
            self._uut[uut_id].close_qa_cli(cli_name)

 
    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self.uut_if_list = list()

        return super(TC_SDK_LINK_THROUGHPUT, self).__init__(methodName, param)
        

    def packet_handler(self, packet):

        log = logging.getLogger(__name__)
        self.stats.total_sniffer_frames_processed += 1

        if ( self.stats.total_sniffer_frames_processed > 1000 ):
            raise ProceesedFramesCompleted
        
        #int(packet["llc.type"],0) == self._proto_id:

        if_id = int(packet["frame.interface_id"],0) + 1
        if ( if_id == 1 ):
            # float(packet["frame.time_relative"])
            if ( self.stats.current_sec == int(float(packet["frame.time_relative"])) ):
                self.stats.frames_in_sec +=1
            else:
                # Moved second calc rate
                if ( self.stats.curret_sec == 0 ):
                    self.stats.capture_frame_rate = self.stats.frames_in_sec
                else:
                    self.stats.capture_frame_rate = int(float( (self.stats.capture_frame_rate + self.stats.frames_in_sec) / 2.0))
                
                self.stats.current_sec = int(float(packet["frame.time_relative"]))
        
        # verify Data len
        if (self.payload_len != None ):
            if ( int(packet["data.len"]) != self.payload_len + 1 ):
                self.stats.capture_error_length += 1
        elif ( (len(self.tx_data_val) * self.tx_data_len) == self.payload_len + 1 ):
                self.stats.capture_error_length += 1

    def round_to(self, number, res = 10):
        return int( round(math.ceil(number / float(res))) ) * int(res)

    def get_test_parameters( self ):
        # Set Some test defaults 
        self._gps_scenario = self.param.get('gps_scenario', "" )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        self._gps_lock_timeout_sec = self.param.get('gps_lock_timeout_sec', 600 )
        self._frame_rate_hz = self.param.get('frame_rate_hz', 10 )
        self.frames = self.param.get('frames', 2000 )
        self.tx_data_len = self.param.get('tx_data_len', 100 )
        self.tx_data_val = self.param.get('tx_data_val', 'ab' )
        self.main_uut = self.param.get('uut_idx', 0 )
        self.payload_len = self.param.get('payload_len', None )

        self._testParams = self.param.get('params', None )
        if self._testParams is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : params = tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data_val = 'ab', tx_power = -5 )")

        g = list()
        i = 0
        for t_param in self._testParams:
            print "Tparam {} : {}".format ( i, t_param.__dict__)

            if 'tx' in vars(t_param):
                g.append(t_param.tx[0])
                self.uut_if_list.append( t_param.tx )
            if 'rx' in vars(t_param):
                g.append(t_param.rx[0])
                self.uut_if_list.append( t_param.rx )
            i += 1
         
        self._uut_list = set(g)
        self._uut = {}
    
  
    def test_link_througput(self):
        """ Test link layer Tx and Rx
            @fn         test_link_tx_rx
            @brief      Verify tx nd rx abilites
            @details    Test ID	    : TC_SDK3.0_LINK_01
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx\n
        """
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )

        log = logging.getLogger(__name__)
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


        def initilization(self):
  
            # Get sniffer handle from setup
            log.info("Getting Sniffer info")
            if globals.setup.instruments.sniffer is None:
                raise globals.Error("Sniffer is not initilize or define in setup, please check your configuration")
            else: # Get pointer to object
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

  
            self.rx_list = []
            self.tx_list = []
            self.tx_rates = []
            self.active_cli_list = []

            # Config rx uut
            for t_param in self._testParams:
                # For Multiple RX convert to list is not list
                rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
                for rx in rx_list:
                    uut_id, rf_if = rx
                    #set cli name base on rx + proto_id + if
                    cli_name = "rx_{}_{}".format( rf_if, t_param.proto_id )
                    self.rx_list.append( (uut_id, rf_if, cli_name) )

                    self._frame_type = 'data' if not 'frame_type' in vars(t_param) else t_param.frame_type

                    if 'freq' in vars(t_param):
                        self._uut[uut_id].managment.set_rf_frequency( t_param.freq  , rf_if )

                    cli = self._uut[uut_id].create_qa_cli(cli_name)
                    self.active_cli_list.append( (uut_id, rf_if, cli_name) )

                    cli.session_open() # Open general session
                    # Open sdk Link
                    cli.link_open(rf_if, self._frame_type, t_param.proto_id)
                    #self._uut[uut_id].qa_cli(cli_name).link_rx( t_param.frames, print_frame = 1, timeout = 10000 )

            # Check which 
            if  self.payload_len != None:
                self.payload_length = self.payload_len
                self.tx_data = None
            else:
                self.tx_data = (t_param.tx_data_len if ('tx_data_len' in vars(t_param)) else self.tx_data_len ) * \
                                (t_param.tx_data_val if ('tx_data_val' in vars(t_param)) else self.tx_data_val ) 
                self.payload_length = None

            # Config tx test parameters
            for t_param in self._testParams:


                # For Multiple Tx convert to list is not list
                tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx
                # Config tx uut
                for tx in tx_list:
                    uut_id, rf_if = tx
                    #set cli name base on tx + proto_id + if
                    cli_name = "tx_{}_{}".format( rf_if, t_param.proto_id )
                    self.tx_list.append( (uut_id, rf_if, cli_name, t_param.frame_rate_hz ) )
                    self.tx_rates.append( (uut_id, t_param.frame_rate_hz) )
                    
                    # Set the main transmiter rate for test
                    if uut_id != self.main_uut:
                        self.frame_rate_hz =  t_param.frame_rate_hz

                    # Configure the Tx power 
                    if 'tx_power' in vars(t_param):
                        self._uut[uut_id].managment.set_tx_power( t_param.tx_power, rf_if )

                    # Set Rf Frequenct
                    if 'freq' in vars(t_param):
                        self._uut[uut_id].managment.set_rf_frequency(  t_param.freq, rf_if )

                    cli = self._uut[uut_id].create_qa_cli(cli_name)
                    self.active_cli_list.append( (uut_id, rf_if, cli_name) )

                    cli.session_open()
                    cli.link_open(rf_if, self._frame_type, t_param.proto_id)

            # Combine all lists
            self.active_cli_list
            # Sort rate by uut
            
        def main_test(self):

            i = 0
            transmit_time = 0
            session_counters = dict()
            search_rate = list()

            self.tx_rates = [b for a,b in sorted((tup[1], tup) for tup in self.tx_rates)]
            search_rate = [0, self.tx_rates[1][1] ] 

            log.info( "Iteration {}, tx_rates : {}".format( i, self.tx_rates ) )
            frames_ratio = int( float(self.tx_rates[1][1]) / float(self.tx_rates[0][1]) )

 
            rx_timeout_ms = 30000
            rx_timeout_sec = int( rx_timeout_ms / 1000.0)
            searching_rate = True

            self.num_search_iter = 0
            while searching_rate:
                self.num_search_iter += 1

                self.sniffer_file = os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap')
                # start sniffer recording 
                self.sniffer.start_capture( file_name = self.sniffer_file )

                frames_ratio = int( float(self.tx_rates[1][1]) / float(self.tx_rates[0][1]) )

                print >> self.result._original_stdout, "iter : {}, rate {}, ratio {}".format( self.num_search_iter,  self.tx_rates[1][1], frames_ratio )

                # Get start counters
                for uut_pair in self.uut_if_list:
                    uut_id, rf_if = uut_pair
                    self.stats.uut_counters[uut_pair]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt( rf_if )
                    self.stats.uut_counters[uut_pair]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt( rf_if )

                # Clear link v2x-cli counters                
                for uut_id in self._uut_list:
                    self._uut[uut_id].cli.link_reset_counter()
                    self.stats.total_rx_frames = 0
                    self.stats.total_tx_frames = 0

                for rx in  self.rx_list: 
                   uut_id, rf_if, cli_name = rx
                   frames = self.frames if uut_id != self.main_uut else int(self.frames * frames_ratio)
                   log.info( "Starting Rx, on {}, frames {}". format( (uut_id, rf_if), frames) )
                   self._uut[uut_id].qa_cli(cli_name).link_rx( frames, print_frame = 0, timeout = rx_timeout_ms )

                # Reset profiler 
                #for uut_id in self._uut_list:
                #    self._uut[uut_id].debug_cli.prof_reset()

                for tx in self.tx_list:
                    uut_id, rf_if, cli_name, rate = tx
                    frames = self.frames if uut_id == self.main_uut else int(self.frames * frames_ratio)
                    #frame_rate_hz = self.frame_rate_hz if uut_id != self.main_uut else rate
                    log.info( "Starting Tx, on {}, frames {}, rate {}". format( (uut_id, rf_if), frames, self.tx_rates[uut_id][1]) )
                    self._uut[uut_id].qa_cli(cli_name).link_tx(tx_data = self.tx_data, payload_len = self.payload_length , frames = frames, rate_hz = self.tx_rates[uut_id][1])
                    # Serach the larget transmit time
                    expected_transmit_time = int(float( 1.0 / self.tx_rates[uut_id][1]) *  frames) + 5
                    transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time 

                start_time = int(time.clock())
 
                # make sure to have engouh time to exit from loop
                wait_time = transmit_time if transmit_time > rx_timeout_sec else rx_timeout_sec
                time.sleep( wait_time )
                log.info( "System started to trasmit, will wait for {} sec before test".format( wait_time) ) 


                # wait some more 
                while True:
                    # TBD : Add is_transmit to v2x-cli based on counter reading.
                    if ( int(time.clock()) - start_time ) > (wait_time + int(wait_time * 0.2)):
                        break
                    time.sleep(0.500)

                #for uut_id in self._uut_list:
                #    prof[uut_id] = self._uut[uut_id].debug_cli.prof_display()

                self.stats.total_tx_frames = 0
                self.stats.total_rx_frames = 0

                # Wait for the end of transmision
                for uut_id in self._uut_list:
                    #cli_name = 'counters'
                    #cli = self._uut[uut_id].create_qa_cli(cli_name)
                    unit_counter = self._uut[uut_id].cli.link_get_counters()
                    #unit_counter = cli.link_get_counters()
                    session_counters[uut_id] =  unit_counter
                     # {'rx': [' 39998', ' 0'], 'tx': [' 2000', ' 0']}
                    self.stats.total_rx_frames += int(unit_counter['rx'][0])
                    self.stats.total_tx_frames += int(unit_counter['tx'][0])
                    log.info( "v2x-cli link counters {} ".format( unit_counter ) )
                    #self._uut[uut_id].close_qa_cli(cli_name)

                self.sniffer.stop_capture()
                frame_loss = self.stats.total_tx_frames - self.stats.total_rx_frames
                print >> self.result._original_stdout, "iter : {} ({} {}), frame loss {}, total tx  {}, total rx {}".format( self.num_search_iter,search_rate[0], search_rate[1],  frame_loss, self.stats.total_tx_frames, self.stats.total_rx_frames )

                if ( self.num_search_iter > MAX_SEARCH_ITERATION ):
                    if ( search_rate[0] > 0 ):
                        searching_rate = False
                    else:
                        raise Exception("Unable to find max throughutput")

                if ( frame_loss == 0 and self.stats.total_tx_frames > 0 and self.stats.total_rx_frames > 0  ):
                    
                    if ( self.tx_rates[1][1] >= MAX_FRAMES_RATE ) or ( search_rate[0] >= search_rate[1]) :
                        # Start data for report
                        searching_rate = False
                        break
                    else:
                        # Try to Load 
                        #self.tx_rates[1][1] = self.round_to( int(( self.tx_rates[1][1] + MAX_FRAMES_RATE ) / 2.0) )
                        # self.tx_rates[1][1] = self.round_to( int(( self.tx_rates[1][1] + MAX_FRAMES_RATE ) / 2.0) )
                        search_rate[0] = self.tx_rates[1][1]
                else:
                    search_rate[1] = self.tx_rates[1][1]
                    # We are to high Let go down 
                
                new_rate = self.round_to(sum(search_rate) / 2.0)
                uut_id = self.tx_rates[1][0]
                self.tx_rates[1] = (uut_id, new_rate)

                ## Get Counter at the End of transmition 
                #for uut_pair in self.uut_if_list:
                #    uut_id, rf_if = uut_pair
                    
                #    self.stats.uut_counters[uut_pair]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt( rf_if ) - self.stats.uut_counters[uut_pair]['rx_cnt']
                #    self.stats.total_rx_frames += self.stats.uut_counters[uut_pair]['rx_cnt']

                #    self.stats.uut_counters[uut_pair]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt( rf_if ) - self.stats.uut_counters[uut_pair]['tx_cnt']

                #    self.check_limit(self.stats.total_tx_expected , self.stats.total_rx_frames, None, 'EQ')

                #if ( self.stats.total_rx_frames == self.stats.total_tx_frames ):
                #    log.info ("FOUND Rate")
                #    break                    

            #stop and clean
            if self.is_gps_active():
                self.gps_sim.stop_scenario()
                self.gps_sim.stop_recording()

            self.sniffer.stop_capture()

        def debug_overides(self):
            # DEBUG ONLY !!!!!!!   override for tests !!!!!
            #nav_file_recorder = "C:\\Users\\shochats\\AppData\\Local\\Temp\\nav_data_20130702-150427.txt"
            self.gps_file = "C:\\Users\\shochats\\AppData\\Local\\Temp\\gps_rec_20130702-150427.txt"
            self.sniffer_file = "I:\\hbe.pcap"
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
                try:
                    pdml_parser.parse_file( self.pdml_file , self.packet_handler )
                except ProceesedFramesCompleted as e:
                    pass
                except Exception as e:
                    raise Exception(e)

        def print_results(self):
            total_frames_sent = self.stats.total_tx_expected

            self.add_limit( "Maximum RX rate found" , 0, self.tx_rates[1][1], MAX_FRAMES_RATE , 'GTLE')    
            self.add_limit( "Maximum TX rate found" , 10, self.tx_rates[0][1], None , 'EQ')    
            self.add_limit( "Number of Iterations" , 1 , self.num_search_iter, None , 'GE')    

            self.add_limit( "Total Frames Processed" , total_frames_sent, self.stats.total_frames_processed, None , 'EQ')    
            self.add_limit( "Total Frames on RX data errors" ,0, self.stats.data_mismatch, None , 'EQ')    
            
        # Start Test scenarios 
        initilization(self)
        unit_configuration(self)
        main_test(self)
        # test_debug_overide(self)
        analyze_results(self)
        print_results(self)
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    

       
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
        self.total_rx_frames = 0
        self.total_tx_frames = 0
        
        self.frames_in_sec = 0
        self.capture_frame_rate = 0
        self.capture_error_length = 0
        self.current_sec = 0

