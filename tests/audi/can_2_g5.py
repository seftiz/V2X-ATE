"""
    @file  
    Implement audi test case for can to its-g5 path 

    This test is based on audi-marben version.

    TP :  @link \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx @endlink 
"""


import sys, os, time, tempfile
import logging
from lib import station_setup
from uuts import common
from tests import common
from lib import instruments_manager, packet_analyzer, globals, gps_simulator
from lib.instruments.Komodo import komodo_if

import pyshark
import threading
from datetime import datetime

class TC_CAN_2_G5(common.V2X_SDKBaseTest):
    """
    @class TC_CAN_2_G5
    """
 
    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.stats = Statistics()
        super(TC_CAN_2_G5, self).__init__(methodName, param)
    
    
    def get_test_parameters( self ):
        # Call father class
        super(TC_CAN_2_G5, self).get_test_parameters()

        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )
   
    def test_start(self):
        self.log = logging.getLogger(__name__)
        # unit configuration 
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )
        #Get position data that described in table below via NAV API.
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
         #self.unit_configuration()
        self.main()

        #self.debug_override()

        if len(self._cpu_load_info):
            for uut_id in self._cpu_load_info:
                self._uut[uut_id].set_cpu_load( 0 )

        self.analyze_results()

        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def instruments_initilization(self):
        
        # Initilize GPS 
        self.gps_init(  self._gps_scenario, self._gps_tx_power )

        # Get sniffer handle from setup
        self.sniffer = globals.setup.instruments.sniffer
        if self.sniffer is None:
            raise globals.Error("Sniffer is not initilize or define in setup, please check your configuration")

        # initlize sniffer
        self.sniffer.initialize()
        self.sniffer.set_interface([0,1])
        # tshark app used for capturing frames must verify license of sirit and it take time ~ 15 seconds 
        time.sleep(20)

        if self.sniffer.type == 'sirit':
            self.sniffer.configure_dsrc_tool()


        self.can_bus =  globals.setup.instruments.can_bus
        if self.can_bus == None:
            raise Exception("CAN BUS simulator is missing in current configuration")


        # create capture files for gps and sniffer
        self.gps_file = os.path.join( tempfile.gettempdir(),  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')
        self.sniffer_file = os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap')

    def unit_configuration(self):

        gps_lock = False
        # start gps scenario
        if self.is_gps_active():
            self.gps_sim.start_scenario()
            time.sleep(2)
            gps_lock = self.wait_for_gps_lock( self.uut, self._gps_lock_timeout_sec )

            # Add Gps lock limit     
            self.add_limit( "GPS Locked" , int(True) , int(gps_lock), None , 'EQ')
            if gps_lock == False:
                self.log.info("GPS Lock failed")
                return
        else:
            raise globals.Error( " GPS simulator is not active " ) 

    def _send_can_messeges( self, can_bus, can_port,  can_msg_id, can_data):

        while ( self.transmit_can_data ) :
            self.can_bus.send_frame( self.uut.can_bus.port, can_msg_id, can_data)
            #self.can_bus.



    def main(self):
            
        TOTAL_PKT_CNT = 10
        interfaces = 0
        # Start capture frames from sirit.
        dir, file = os.path.split(os.path.abspath(self.sniffer_file))

        self.can_bus.configure_port( self.uut.can_bus.port )
        self.can_bus.power_up( self.uut.can_bus.port )
        """
        Audi Can message for drive direction 
        Motor_14	0x3BE	958	8	100		10	Application	Cyclic		MO_Gangposition	3	4	4	OnChange 14	g?ltiger Wert   0 Gang_N
																															    1 Gang_1
																															    2 Gang_2
																															    3 Gang_3
																															    4 Gang_4
																															    5 Gang_5
																															    6 Gang_6
																															    7 Gang_7
																															    8 Gang_8
																															    9 Automat_P
																															    10 Automat_Vorwaerts_S
																															    11 Automat_Vorwaerts_D/E
																															    12 Zwischenstellung
																															    13 Gang_R
																															    14 Istgang_nicht_definiert
																															    15 Fehler

        """
        msg_id = 0x3BE
        cam_msg_reverse = [0x0 , 0x0 , 0xD0, 00, 0x0, 0x0, 0x0, 0x0]
        cam_msg_forward = [0x0 , 0x0 , 0x10, 0x0, 0x0, 0x0, 0x0, 0x0]

        test_sequence = [cam_msg_reverse, cam_msg_forward,cam_msg_reverse]

        # Send CAN command of AUDI CAN Protocol to set on CAM drive direction
        try:
            for cam_msg in test_sequence:
                cam_frame_found = False

                self.transmit_can_data = True
                # can_bus.send_frame( self.uut.can_bus.port, 0x3BE, cam_msg)
                canThread = threading.Thread(target=self._send_can_messeges, args=(can_bus, self.uut.can_bus.port, 0x3BE, cam_msg,) )
                canThread.start()

                # Create filter of sa and cam
                filter = 'wlan.sa=={} and cam'.format( self.uut.rf_interfaces[1].mac_addr )
                cam_frames = self.sniffer.start_live_capture(interfaces, total_packet_count = TOTAL_PKT_CNT, timeout_sec = 60, display_filter = filter )
                if len(cam_frames._packets) == 0:
                    pass

                # Search CAM frame in data
                for frame_idx,frame in  enumerate(cam_frames._packets):
                    if frame.layers[-1].layer_name == 'cam':
                        cam_frame_found = True
                        break

                self.transmit_can_data = False
                canThread.join()

                # Cam frames not found
                if not cam_frame_found:
                    continue

                driveDirection = int(frame.cam.driveDirection)
        
                if ( (cam_msg[2] == cam_msg_reverse[2]) and (driveDirection == 1) ):
                    self.stats.can_bus_data_ok += 1
                elif ( (cam_msg[2] == cam_msg_forward[2]) and (driveDirection == 0) ):
                    self.stats.can_bus_data_ok += 1
                
                cam_frames.clear()

        except Exception as e:
            raise e
        finally: 
            self.can_bus.power_down(self.uut.can_bus.port)
            self.can_bus.close_port(self.uut.can_bus.port)
 
    def debug_override( self, base_dir = None ):
        # DEBUG ONLY !!!!!!!   override for tests !!!!!
        if base_dir is None:
            basr_dir = tempfile.gettempdir() # "C:\\Users\\dell\\AppData\\Local\\Temp\\"

        self.gps_file = basr_dir + "\\test_gnss_20140803-100650.txt"
        self.sniffer_file = '//ate-lab/capture/test_gnss_20140803-100650.pcap'

        print >> self.result._original_stdout, "NOTE : DEBUG Override is active "
        print >> self.result._original_stdout, "GPS log file : {}".format(  self.gps_file )
        print >> self.result._original_stdout, "Sniffer file log file : {}".format(  self.sniffer_file )
        
    def analyze_results(self):
        pass

    def print_results(self):
        self.add_limit( "Can messages recevied" , 3 , self.stats.can_bus_data_ok, None , 'EQ')

class Statistics(object):

    def __init__(self):
        self.total_frames = 0
        self.total_cam_frames = 0
        self.can_bus_data_ok = 0

  



