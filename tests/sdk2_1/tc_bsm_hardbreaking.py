"""
@file       tc_navapi.py
@brief      Testsuite for testing bsm hard breaking event 
@author    	Shai Shochat
@version	1.0
@date		Sep 2013
\link		\\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx \endlink
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


# @topology('CF01')
class TC_BSM_HARD_BREAKING(common.V2X_SDKBaseTest):
    """
    @class TC_BSM_HARD_BREAKING
    @brief Implementation of hard breaking event  
    @author Shai Shochat
    @version 0.1
    @date	03/09/2013
    """

    def runTest(self):
        pass

    def tearDown(self):
        pass

    def is_hard_breaking_event(self):
        if len(self.hbe_flag) > 0:
            return True
        elif self.hbe_hysteresis > 0:
            self.hbe_hysteresis -= 1
            return True

        return False


    def packet_handler(self, packet):
        
        log = logging.getLogger(__name__)

        self.stats.total_frames_processed += 1
        self.frame_idx += 1
        
        if self.frame_idx == 1:
            # This is first frame
            self.packet_stack.append(packet)
            return
  

        # 01/01/2004 23:59
        # packet_tai_time = common.parse_1609_2_generation_time( packet["ieee16092.generation_time"] )

        # Verify bsm protocol exists
        if 'j2735' in packet["frame.protocols"]:
            # Mask the 3 MSB, since its use for transmision position
            # Each unit value is 0.02 m/s

            # Verify GPS data is avalaible
            if int(packet["j2735.pos3D.lat"]) == common.GPS_LATITUDE_UNAVAILABLE or int(packet["j2735.pos3D.long"]) == common.GPS_LONGITUDE_UNAVAILABLE:
                # add frame with no gps data or gps signal lost
                self.stats.packt_no_nav += 1
                return

            # Get packet from buffer
            prev_packet = self.packet_stack.pop()

            current_speed = (int(packet["j2735.speed"]) & 0x1FFF) * dsrc_definitions.BSM_J2375_SPEED_UNIT
            current_time = float(packet["frame.time_epoch"])

            prev_speed = (int(prev_packet["j2735.speed"]) & 0x1FFF) * dsrc_definitions.BSM_J2375_SPEED_UNIT
            prev_time = float(prev_packet["frame.time_epoch"])
            
            acceleration = (prev_speed - current_speed) / (prev_time - current_time)
            # Log test data
            log_data = "hbe info, frame %d: current_epoch_time %f current_speed %f, prev_speed %f, acceleration %f" %  ( self.frame_idx, current_time, current_speed , prev_speed, acceleration )
            log.info( log_data )

            if self.is_hard_breaking_event():

                if acceleration < dsrc_definitions.HARD_BRAKING_ACCELERATION_THRESHOLD:
                    self.stats.hbe_in_hbe += 1
                    self.hbe_hysteresis = dsrc_definitions.BSM_HARD_BRAKING_HYSTERESIS
                 
                if len(self.hbe_flag) > 0:
                    delta_time = float(packet["frame.time_epoch"]) - self.hbe_flag[1]
                    hbe_response_time_ok = (delta_time < ( dsrc_definitions.MAX_HBE_SYSTEM_RESPONSE_TIME_SEC + (dsrc_definitions.MAX_HBE_SYSTEM_RESPONSE_TIME_SEC * 0.02) ))
                else:
                    hbe_response_time_ok = False

                # Verify Frame has hbe event data
                if packet.item_exists("j2735.safetyExt"):
                    if packet.item_exists("j2735.events") and int(packet["j2735.events"]) == dsrc_definitions.EVENT_HARD_BRAKING:
                        
                        log.info("HBE flag found, verify if hystersis or first event in BSM message")
                        # count total hbe frames
                        self.stats.hbe_frames_in_file +=1
                        # Check first hbe event timeout
                        if len(self.hbe_flag) > 0:
                            # Clear hbe event
                            self.hbe_flag = ()

                            if hbe_response_time_ok:
                                # Got first hbe events
                                self.stats.hbe_expected_in_time_range += 1
                            else:
                                # This shold be hystersis flag
                                log.info("hbe_expected_out_time_range at frame %d" % self.frame_idx)
                                self.stats.hbe_expected_out_time_range += 1

                        else:
                            # Shuold be hystersis
                            if (self.hbe_hysteresis) == 0:
                                self.stats.hbe_expected_hystersis += 1
                    else:
                        # Check time from hbe event
                        if not hbe_response_time_ok:
                            # hbe events should arrive.
                            log.info("hbe_expected_out_time_range at frame %d" % self.frame_idx)
                            self.stats.hbe_expected_out_time_range += 1
                            # Clear all 
                            self.hbe_flag = ()
                            self.hbe_hysteresis = 0

                else:
                    if not hbe_response_time_ok:
                         self.stats.hbe_expected_out_time_range += 1
            else:
                # Check if expecting hard braking event
                if acceleration < dsrc_definitions.HARD_BRAKING_ACCELERATION_THRESHOLD:
                    # Raise flag for to expect hardbrake event in max 200 ms.
                    self.hbe_flag = (self.frame_idx, float(prev_packet["frame.time_epoch"]))
                    self.hbe_hysteresis = dsrc_definitions.BSM_HARD_BRAKING_HYSTERESIS
                    self.stats.total_hbe_found_in_data += 1

        else:
            self.stats.unknownframes += 1
        

        self.packet_stack.append(packet)



    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.packet_stack = []
        self.frame_idx = 0
        self.hbe_flag = ()
        self.hbe_hysteresis = 0
        self.stats = Statistics()

        return super(TC_BSM_HARD_BREAKING, self).__init__(methodName, param)

   
    def test_bsm_01(self):
        """ Test bsm hard breaking event
            @fn         test_nav_api_1
            @brief      Verify hard brakeing event
            @details    Test ID	    : TC_SDK2.1_BSM_01
                        Test Name 	: BSM-HardBreaking 
                        Objective 	: Validate correct BSM part 2 hard brake event scenario\n
                        Reference	: REQ_SDK2.1_NAVAPI_01\n
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx\n
        """
        log = logging.getLogger(__name__)

        # unit configuration 


        #Additional scenario details:
        #HDOP < 5

        #Get position data that described in table below via NAV API.
        
        self._gps_scenario = self.param.get('gps_scenario', "strait_line_hard_brake" )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )
        self._search_accelaration = self.param.get('search_accelaration', 0.4*9.8 )
        self._gps_lock_timeout_sec = self.param.get('gps_lock_timeout_sec', 600 )
        self._bsm_tx_period_ms = self.param.get('bsm_tx_period_ms', 100 )

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


        def test_initilization(self):

            # Get sniffer handle from setup
            log.info("Getting Sniffer info")
            if globals.setup.instruments.sniffer is None:
                raise globals.Error("Sniffer is not initilize or define in setup, please check your configuration")
            else:
                # Get pointer to object
                sniffer = globals.setup.instruments.sniffer

            # initlize sniffer
            sniffer.initialize()


            log.info("Getting GPS simulator in config")
            if globals.setup.instruments.gps_simulator is None:
                raise globals.Error("gps simulator is not initilize, please check your configuration")
            else:
                # Get pointer to object
                gps_sim = globals.setup.instruments.gps_simulator

            # set general tx power
            gps_sim.tx_power( self._gps_tx_power )  
            #load scenario
            gps_sim.load( self._gps_scenario )



            dir_name = tempfile.gettempdir()
            timestr = time.strftime("%Y%m%d-%H%M%S")
            self.test_file_name = 'tc_bsm_hardbake_rec'
            self.gps_file = os.path.join( tempfile.gettempdir(), self.test_file_name + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')
            self.sniffer_file = os.path.join( common.SNIFFER_DRIVE , self.test_file_name + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap')


        # Main test action
        def test_main(self):
            # Start gps scenario without recording
            gps_sim.start_scenario()
        

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
            gps_sim.start_recording( gps_file )

            # start recording 
            sniffer.start_capture( file_name = self.sniffer_file )

            # run scenrio for a period of time
            print "NOTE : test will sleep for {} for gps data".format(self._scenario_time_sec) 
            start_time = time.time()
            while ( (time.time() - start_time) < self._scenario_time_sec ):
                time.sleep(0.1)

            #stop and clean
            gps_sim.stop_scenario()
            gps_sim.stop_recording()

            sniffer.stop_capture()

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
            pcap_pdml_conv.export_pcap( self.sniffer_file, self.pdml_file )


            pdml_parser = packet_analyzer.PcapHandler()
            pdml_parser.parse_file( self.pdml_file , self.packet_handler )

            # Start analyze the counters

        #test_initilization(self)
        #test_main(self)
        test_debug_overide(self)
        test_analyze_results(self)

        self.add_limit( "Total Frames Proceesed" , 0 , self.stats.total_frames_processed, None , 'GT')    
        self.add_limit( "Total Hard Break events" , 0 , self.stats.total_hbe_found_in_data, None , 'GT')    
        
        self.add_limit( "Total HBE in time" , self.stats.hbe_expected_in_time_range , self.stats.hbe_expected_in_time_range, None, 'EQ')    
        self.add_limit( "Total HBE hystersis events" , self.stats.total_hbe_found_in_data , self.stats.hbe_expected_hystersis, None, 'EQ')    

        self.add_limit( "Total HBE out of time" , 0 , self.stats.hbe_expected_out_time_range, None, 'EQ')    

        print "test_completed"
  
        
class Statistics(object):

    def __init__(self):
        # Total frame process in the wireshark file
        self.total_frames_processed = 0

        # Count packets without gps lock or gps data which will cause to speed and acceleration errors.
        self.packt_no_nav = 0


        # Total hbe events found in file that expected without histeresis
        self.hbe_counter = 0

        self.bsm_hbe_pass = 0
        self.bsm_hbe_fail = 0
        
        # Total expected hbe frames which are missing
        self.hbe_missing = 0
        
        # Total hbe frames recieved in time frames as expected. (expected = hbe_counter)
        self.hbe_expected_in_time_range = 0
        
        # Total hbe frames recieved out time frames as expected. expected = 0
        self.hbe_expected_out_time_range = 0

        # Count number of hystersis frames arrived
        self.hbe_expected_hystersis = 0
        
        # counts total hbe events found in bsm recording file
        self.total_hbe_found_in_data = 0
  
        # count frames found with hbe event flag
        self.hbe_frames_in_file = 0

        # count how many hbe in hbe events  (new hbe while in hbe)
        self.hbe_in_hbe = 0