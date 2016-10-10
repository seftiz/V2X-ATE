"""
@file       tc_can2bsm.py
@brief      Testsuite for testing can bus updates to bsm messages  
@author    	Shai Shochat
@version	1.0
@date		Sep 2013
"""

# import global and general setup var
from lib import station_setup
from uuts import common
from tests import common, dsrc_definitions
from lib import instruments_manager
from lib import packet_analyzer
from tests.gm import gm_can_definitions

from lib import komodo_if 

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
class TC_CAN_2_BSM(common.V2X_SDKBaseTest):
    """
    @class TC_CAN_2_BSM
    @brief Implementation can bus messagaes to bsm messages
    @author Shai Shochat
    @version 0.1
    @date	03/09/2013
    """

    def runTest(self):
        pass

    def tearDown(self):

        # Close can bus server
        if not self._can_bus_sim is None:
            self._can_bus_sim.power_down(self._can_inferface)
            self._can_bus_sim.close_port(self._can_inferface)

    def packet_handler(self, packet):
        pass

    def transmit_can_file(self, file_name):
        file_hwd = open( file_name, "r")
        for line in file_hwd:
            
            # examples of can data
            # can_id = 0x0c1, dlc = 8, data = [0x93, 0xFD, 0x07, 0xD0, 0x90, 0x2C, 0xDF, 0x40])
            # can_id = 0x0c5, dlc = 8, data = [0x93, 0xB4, 0x1E, 0xE0, 0x53, 0xEC, 0xF0, 0x3C], wait = 1)

            # split to 3 blocks
            base = line.split(',',2)

            #cam_msg = base[0].split('=')[1].strip()
            
            # extract can_id messages value
            cam_msg = int(base[0].split('=')[1].strip(),16)

            # extract cam data length
            cam_data_len = int(base[1].split('=')[1].strip())

            # Create regular expression
            regex = re.compile("0x[0-9,A-F][0-9,A-F]")
            data = regex.findall(base[2])

            # convert each ascii hex into its binary value
            cam_data = [int(x, 16) for x in ascii_hex_values]

            if cam_data_len != len(hex_values):
                continue

        file_hwd.close()


    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.packet_stack = []
        self.frame_idx = 0
        self.stats = Statistics()

        return super(TC_CAN_2_BSM, self).__init__(methodName, param)

   
    def test_can_messages(self):
        """ Test can data that upload to bsm messages
            @fn         test_can_messages
            @brief      Verify hard brakeing event
        """

        log = logging.getLogger(__name__)

        # unit configuration 
        self._gps_scenario = self.param.get('gps_scenario', "strait_line_hard_brake" )
        self._gps_lock_timeout_sec = self.param.get('gps_lock_timeout_sec', 600 )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )

        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )

        self._can_bus_data_file = self.param.get('can_data_file', '' )

        self._bsm_tx_period_ms = self.param.get('bsm_tx_period_ms', 100 )
        
        # Get can bus simulator interface
        self._can_inferface = self.param.get('can_inferface', komodo_if.KOMODO_IF_CAN_A )


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
                #raise globals.Error("gps simulator is not initilize, please check your configuration")
                gps_sim = None
            else:
                # Get pointer to object
                gps_sim = globals.setup.instruments.gps_simulator
            
            if globals.setup.instruments.can_bus is None:
                raise globals.Error("Can bus server is not initilize, please check your configuration")
            else:
                # Get pointer to object
                self._can_bus_sim = globals.setup.instruments.can_bus

            #self._komodo = Komodo.Komodo()
            self._can_bus_sim.configure_port(self._can_inferface)
            self._can_bus_sim.power_up(self._can_inferface)
            #self._can_bus_sim.power_down(self._can_inferface)
            #self._komodo.power_down(self._komodo_interface)

            self.gm_can_msgs = gm_can_definitions.GmCanMessages( self._can_bus_sim, self._can_inferface )

            # set general tx power
            if not gps_sim is None:
                gps_sim.tx_power( self._gps_tx_power )  
            #load scenario
            if not gps_sim is None:
                gps_sim.load( self._gps_scenario )

            dir_name = tempfile.gettempdir()
            timestr = time.strftime("%Y%m%d-%H%M%S")
            self.test_file_name = 'tc_can_2_bsm_rec'
            self.gps_file = os.path.join( tempfile.gettempdir(), self.test_file_name + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')
            self.sniffer_file = os.path.join( common.SNIFFER_DRIVE , self.test_file_name + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap')


        # Main test action
        def test_main(self):
            
            # Start gps scenario without recording
            if not gps_sim is None:
                gps_sim.start_scenario()
        
            if not gps_sim is None:
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
                # During wait change some of the fields in the bsm
                time.sleep(0.1)

            #stop and clean
            if not gps_sim is None:
                gps_sim.stop_scenario()
                gps_sim.stop_recording()

            sniffer.stop_capture()

        def test_debug_overide(self):


            # DEBUG ONLY !!!!!!!   override for tests !!!!!
            #nav_file_recorder = "C:\\Users\\shochats\\AppData\\Local\\Temp\\nav_data_20130702-150427.txt"
            self.gps_file = "C:\\Users\\shochats\\AppData\\Local\\Temp\\gps_rec_20130702-150427.txt"
            self.sniffer_file = "I:\\hbe.pcap"
            
            self.uut.managment.set_rf_frequency(  5880 , 2 )
            self.uut.managment.set_bsm_tx_period( 1000 )
            self.uut.managment.set_bsm_tx_interface(1)
            self.uut.managment.set_bsm_tx_enabled( True )
            self.uut.managment.set_bsm_p2_ext_ratio( 10 )


            val  = False
            while ( True ):

                self.gm_can_msgs.chassis_msg( val , 20, val , val, val, 30)
                self.gm_can_msgs.generate_antilock_brake_and_tc_msg( -3 )
                self.gm_can_msgs.steering_wheel_angle_msg( 80 )
                self.gm_can_msgs.generate_vehicle_speed_and_distance( 100 )
                self.gm_can_msgs.generate_trans_message( 3 )
                self.gm_can_msgs.break_apply_msg( val, val, 80 )
                val = not val
                

            

            self.gm_can_msgs.generate_trans_message( 0 )
            val = False
            for i in range(80,90):
                self.gm_can_msgs.generate_vehicle_speed_and_distance( i )
                
            for i in range(0,0x10):
                self.gm_can_msgs.generate_trans_message( i )



            for i in range(1,1):
                val = not val
                self.gm_can_msgs.chassis_msg( val, i, val, val, val, i)
                log.info("Sending chassis_msg : pedal_pressure_detected {}, lateral_acceleration {}, abs_active {}, traction_control_active {}, stability_system_active {}, dynamic_yaw_rate {} ".format(val, i, val, val, val, i))

            time.sleep(1)

            self.gm_can_msgs.chassis_msg( True, 10, False, True, False, 20)
            
            

           


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

        test_initilization(self)
        #test_main(self)
        test_debug_overide(self)
        #test_analyze_results(self)

        
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