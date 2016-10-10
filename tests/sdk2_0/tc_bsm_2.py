"""
@file tc_bsm_2.py
@brief Testsuite for testing BSM Messages
@author    	Ayelet Rubinov
@version	1.0
@date		15/10/2013
\link		\\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.0\SDK2_0_Test_Plan_v2.docx \endlink
"""

# import global setup var
# from atlk.ut import topology
from lib import station_setup
from uuts import common
from lib import instruments_manager
from lib import packet_analyzer
from lib.packet_analyzer import PcapHandler
from lib import globals
from lib import wiresharkXML


# from sdk20 import setup
from tests import sdk2_0
from tests import common
from tests import dsrc_definitions

import sys
import time
import logging
import cPickle
import tempfile

import time
from datetime import datetime

# @topology('CF01')
class TC_BSM_2(common.V2X_SDKBaseTest):
    """
    @class AtlkUnit
    @brief ATLK base unit Implementation 
    @author Ayelet Rubinov
    @version 0.1
    @date	15/10/2013
    """

    def runTest(self):
        pass

    def tearDown(self):
        # stop Tx
        self.uut.managment.set_bsm_tx_interface( self.uut_channel )
        self.uut.managment.set_bsm_tx_enabled( 2 )   
        # kill gps        
        if globals.setup.instruments.gps_simulator != None:
            gps_sim.stop_scenario()
            gps_sim.stop_recording()
               
    
    def pckt_handler(self, packet):

        # Set error limit bound in precent
        BOUND_LIMIT = ( 10 / 100 )

        self.analyzed_packet_count += 1
        frame_id = int(packet["frame.number"])

        if frame_id > 1:
            # Check delta time
            frame_delta_time = float(packet["frame.time_delta"])
            frame_expected_delta = self._bsm_tx_period_ms / 1000.0

            frm_stat = verify_in_range( frame_dalta_time, frame_expected_delta, BOUND_LIMIT)
            if not frm_stat:
                self.add_limit( ("Frame %d delta time" % frame_id) , frame_delta_time , self._frames, None , 'GTLT')


        # Verify wsmp protocol exists
        if 'wsmp' in packet["frame.protocols"]:
            self.wsmp_packets += 1


    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.analyzed_packet_count = 0
        self.wsmp_packets = 0
        return super(TC_BSM_2, self).__init__(methodName, param)

   
    def test_wsmp_tc_2(self):
        """ Test wsmp protocol base on\nsomething else\nif there is
            @fn wsmp_tc_2
            @brief wsmp testing 
            @details Test ID		: TC_SDK2_02\n	
            Test Name 	: BSM Interval\n
            Objective 	: Validate system capable of generating the BSM messages at required interval
            Reference	: REQ_SDK20_BSM_02\n
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.0\SDK2_0_Test_Plan_v2.docx\n
        """
        self.log = logging.getLogger(__name__)
        self.stats = Statistics()        

        # unit configuration 

        # expect dictionary as parameter for exapmle  uut_id = (0,1), bsm_tx_period_ms = 100, frames = 1000, gps_scenario="c:\\temp\\nmea_data_1.txt") )
        self._tx_power = self.param.get('tx_power', None)
        self._power_dbm8 = self.param.get('power_dbm8', None)
        self._psid = self.param.get('psid', None)
        self._gps_scenario = self.param.get('gps_scenario', None )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )
        self._scenario_time_sec = self.param.get('search_accelaration', 0.4*9.8 )
        self._scenario_time_sec = self.param.get('gps_lock_timeout_sec', 600 )
        self._tx_frames = self.param.get('frames', 0 )
        self._bsm_tx_period = self.param.get('bsm_tx_period_ms', 0 )
        self._bsm_tx_period_delta_factor = self.param.get('bsm_tx_period_delta_factor', 1.5)
        self._bsm_tx_period_delta = self._bsm_tx_period_delta_factor * self._bsm_tx_period
        
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


        self.log.info("Getting GPS simulator in config")
        if globals.setup.instruments.gps_simulator is None:
            #globals.Error("gps simulator is not initilize, please check your configuration")
            pass
        else:
            # Get pointer to object
            gps_sim = globals.setup.instruments.gps_simulator

            # set general tx power
            gps_sim.tx_power( self._gps_tx_power )  
            #load scenario
            gps_sim.load( self._gps_scenario )

            dir_name = tempfile.gettempdir()
            timestr = time.strftime("%Y%m%d-%H%M%S")
            gps_file_name = 'gps_rec'
            #gps_file = os.path.join(dir_name, gps_file_name + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')
            gps_file = "c:\\temp\\gps_rec.txt"

            # Start gps scenario without recording
            gps_sim.start_scenario()        

            self.log.info("Start loop waiting GPS Lock, max time {}.format(self.gps_lock_timeout_sec) )")
            self.gps_lock = gps_sim.lock(self.uut)
            
            # Add Gps lock limit     
            self.add_limit( "GPS Locked" , 1 , int(self.gps_lock), None , 'EQ')
        
            if self.gps_lock == False:
                self.log.info("GPS Lock failed")

            else:
                # Start recording gps simulator scenraio data
                gps_sim.start_recording( gps_file )

        self.log.info("Setting sniffer configuration and start capture")
        if globals.setup.instruments.sniffer is None:         
            sniffer = None
        else:           
            # Get pointer to object
            sniffer = globals.setup.instruments.sniffer
            # start sniffer with file base test name and date, for example, tc_bsm_1_140113_150202.pcap
            sniffer.stop_capture() # Kill old session if exists
            sniffer.initialize()
            file_strtime, file_localTime = __name__.replace('.', '_') ,time.strftime("%d%m%y_%H%M%S", time.localtime())
            capture_data_file = "%s_%s.pcap" % (file_strtime, file_localTime)
            xml_data_file =  "%s_%s.xml" % (file_strtime, file_localTime)
            pdml_data_file = "%s_%s.pdml" % (file_strtime, file_localTime)
        
        if globals.setup.instruments.pcap_convertor is None:
            raise globals.Error("PcapConvertor is not avaliable")
        else:
            # Get pointer to object
            pcap_pdml_conv = globals.setup.instruments.pcap_convertor

        # Set the Tx DUT to send BSMs at rate 10Hz. # Send 1000 BSM packets.
        if not self._tx_power is None:
            self.uut.managment.set_tx_power( self._tx_power,   self.uut_channel)
       
        if sniffer != None:
            """self.uut.managment.set_bsm_security_enable(1)"""

            sniffer.start_capture( capture_data_file )
            
            # Configure BSM values via snmp managment        
            self.uut.managment.set_bsm_tx_period( self._bsm_tx_period )
            self.uut.managment.set_bsm_tx_interface( self.uut_channel )
            self.uut.managment.set_bsm_tx_enabled( 1 )

            # wait time for all frames to capture
            test_expected_time = ((self._bsm_tx_period * self._tx_frames) / 1000) + 10
            self.log.info( " Waiting for all frames to be capture, waiting %d sec" % (test_expected_time) )
            #wait till all frames of first batch are Tx

            time.sleep(test_expected_time) 
       
            #stop and clean
            self.uut.managment.set_bsm_tx_interface( self.uut_channel )
            self.uut.managment.set_bsm_tx_enabled( 2 )
            sniffer.stop_capture()
            if globals.setup.instruments.gps_simulator != None:
                gps_sim.stop_scenario()
                gps_sim.stop_recording()
            
            full_pcap_file_name = "i:\\%s" % capture_data_file
            full_xml_file_name = "i:\\%s" % xml_data_file           
            full_pdml_file_name = "i:\\%s" % pdml_data_file 
            pcap_pdml_conv.export_pcap( full_pcap_file_name, full_pdml_file_name )

            pdml_parser = packet_analyzer.PcapHandler()
            pdml_parser.parse_file( full_pdml_file_name , self._check_bsm_interval )

        else:
            if self._bsm_tx_period == 100:
                full_xml_file_name = "i:\\tests_sdk2_0_tc_bsm_2_100ms.pdml"
            else:
                full_xml_file_name = "i:\\tests_sdk2_0_tc_bsm_2_1000ms.pdml"
            #"i:\\tests_sdk2_0_tc_bsm_2_161013_122007.pdml"#"i:\\tests_sdk2_0_tc_bsm_2_081013_095240.pdml"
            xml_parser = PcapHandler()
            xml_parser.parse_file( full_xml_file_name , self._check_bsm_interval)   
        
        #print test statistics
        self.add_limit( "Total frames processed" , self.stats.total_frames_processed , 
                        self.stats.total_frames_processed, None , 'EQ')
        
        self.add_limit( "Total BSM frames", self.stats.bsm_frames_processed,
                        self.stats.bsm_frames_processed, None , 'EQ')
        self.add_limit( "Total Passed frames", self.stats.bsm_frames_processed, 
                       self.stats.bsm_frames_processed - self.stats.get_total_err(), None , 'EQ')
        self.add_limit( "Number of Error frames", 0, self.stats.get_total_err(),
                        None , 'EQ')
        if self.stats.get_total_err() != 0:
            self.add_limit( "Number of inteval Errors", 0, self.stats.bsm_delta_err,
                             None , 'EQ')
            self.add_limit( "Number of 1609 time not equal to dseconds", 0, self.stats.bsm_1609_vs_dseconds_err,
                            None , 'EQ')

        if self.stats.validate == False:
            print "Test validation error"                
        print "test_completed" 

    def _check_bsm_interval(self, pckt):       
        a = wiresharkXML.Template()
        pckt.build_packet( pckt, a)
      
        self.stats.total_frames_processed += 1
        
        # its a BSM 
        if int(pckt.get_items('j2735.msgID')[-1].get_show()) == dsrc_definitions.DSRC_MSG_TYPE.DSRC_MSG_ID_BSM:
            self.stats.bsm_frames_processed +=1 
            #generation_time = common.parse_1609_2_generation_time( pckt.get_items('ieee16092.generation_time')[-1].get_show())
            # dseconds is the amount of mili second within a minute -> generation time calculation
            """if(int(pckt.get_items('j2735.dsecond')[-1].get_show()) != ((generation_time.second * 1000) + (generation_time.microsecond / 1000))):
                self.log.error("Error when comparing 1609 time to dseconds") 
                self.stats.bsm_1609_vs_dseconds_err += 1"""
            if self.stats.bsm_frames_processed > 1:
                # verify packets delta time
                # convert milisec to sec
                packet_delta_time = float(pckt.get_items('frame.time_delta')[-1].get_show()) * 1000
                if abs(self._bsm_tx_period - packet_delta_time) > self._bsm_tx_period_delta:
                        self.log.error("Error period between bsms %d exceeded its allowed delta %d" % 
                                       (int(packet_delta_time), int(self._bsm_tx_period_delta))) 
                        self.stats.bsm_delta_err += 1                 
            return

          
class Statistics(object):

    def __init__(self):
        self.total_frames_processed = 0
        self.bsm_frames_processed = 0
        self.bsm_frames_processed = 0
        self.bsm_delta_err = 0
        self.bsm_1609_vs_dseconds_err = 0
        
    def get_total_err(self):
        err = (self.bsm_delta_err, self.bsm_1609_vs_dseconds_err)
        return sum(err)

    def validate(self):      
        return 0 == (self.stats.total_frames_processed - self.get_total_err())
            
#if __name__ == "__main__":
#  tc_bsm_1 = TC_BSM_1(param =  dict( uut_id = (0,1), bsm_tx_period_ms = 100, frames = 1000, gps_scenario="Neter2Eilat") ))                        
                        
