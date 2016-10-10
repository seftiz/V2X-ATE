"""
@file tc_bsm_1.py
@brief Testsuite for testing BSM Messages
@author    	Shai Shochat
@version	1.0
@date		20/02/2012
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

# @topology('CF01')
class TC_BSM_1(common.V2X_SDKBaseTest):
    """
    @class AtlkUnit
    @brief ATLK base unit Implementation 
    @author Shai Shochat
    @version 0.1
    @date	27/01/2013
    """

    def runTest(self):
        pass
    def tearDown(self):        
        # kill gps        
        if globals.setup.instruments.gps_simulator != None:
            gps_sim.stop_scenario()
            gps_sim.stop_recording()

    def check_bsm_ranges(self, pckt, gps_on):
        status = True
        """ validate all bsm fields are in limits min to max or n/a according to GPS state"""        
        limits = dsrc_definitions.DSRCbasicSafetyMessageLimitsAndNa()
        for field in limits.values:
            str_value = pckt.get_items(field)[-1].get_show()
            if str(str_value).find('0x') == (-1):
                value = long(str_value, 10)
            else:
                value = long(str_value, 16)
            if gps_on == True and limits.is_version_supported(self.uut.version, field) == True:
                """ gps is on - check that values are in range """                
                min = limits.min(field)
                max = limits.max(field)

                # if min/max are function type. retreive the value they represent
                if type(min) != int:
                    min = min(limits)
                if type(max) != int and type(max) != long:
                    max = max(limits)

                if self.check_limit( min, value, max, 'GELE') == False:   
                    self.log.error("bsm field: %s is %d not in [%d, %d] range" % (field, value, min, max)) 
                    self.stats.bsm.range_err[field] += 1
                    status = False
                           
            else: 
                """ gps is off - check that value equals n/a value"""
                na_val = limits.na(field)
                if na_val == None:
                    continue
                elif type(na_val) == int:
                    if self.check_limit( na_val, value, None, 'EQ') == False:             
                        self.log.error("bsm field: %s is %d not n/a value %d" % (field, value, na_val)) 
                        self.stats.bsm.range_err[field] += 1
                        status = False
                else:
                    if na_val.na(limits, value) == Flase:
                        self.log.error("bsm field: %s is %d not n/a value" % (field, value)) 
                        self.stats.bsm.range_err[field] += 1
                        status = False

        return status
  
    def check_msg_count( self, value):
        #validate msg cnt is greater by 1 from previous & 0 follows 127
        rc = True
        limits = dsrc_definitions.DSRCbasicSafetyMessageLimitsAndNa()       
        if self.msg_cnt == limits.max('j2735.msgCount'):
            if self.check_limit( limits.min('j2735.msgCount'), value, None, 'EQ' ) == False:
                rc = False
        elif self.check_limit( self.msg_cnt+1, value, None, 'EQ' ) == False:
            rc = False
        else:
            rc = True
        self.msg_cnt = value 
        return rc

    
    def check_dsecond( self, value, utc):
        """validate sec mark is valid. handels only positive leap seconds (no neg leap seconds according to wiki)""" 
        #self.stats.sec_mark_range_err += 1
        #TODO compare to UTC time
        #TODO check leap second

    def check_wsmp( self, pckt ):
        if int(pckt.get_items('wsmpv2.version')[-1].get_show(), 16) != dsrc_definitions.DSRCwsmp['version']:
            self.log.error("wsmp version is %d insted of %d" % (int(pckt.get_items('wsmpv2.version')[-1].get_show()), dsrc_definitions.DSRCwsmp.version))
            self.stats.wsmp.version_err += 1         

    def check_llc_snap( self, pckt ):    
        if int(pckt.get_items('llc.dsap')[-1].get_show(), 16) != dsrc_definitions.DSRCllcSnap['dsap']:
            self.log.error("llc.dsap is 0x%x insted of 0x%x" % (hex(int(pckt.get_items('llc.dsap')[-1].get_show())), dsrc_definitions.DSRCllcSnap.dsap))
            self.stats.llc.dsap_err += 1
        if int(pckt.get_items('llc.ssap')[-1].get_show(), 16) != dsrc_definitions.DSRCllcSnap['ssap']:
            self.log.error("llc.ssap is 0x%x insted of 0x%x" % (hex(int(pckt.get_items('llc.ssap')[-1].get_show())), dsrc_definitions.DSRCllcSnap.ssap))
            self.stats.llc.ssap_err += 1
        if int(pckt.get_items('llc.control')[-1].get_show(), 16) != dsrc_definitions.DSRCllcSnap['control']:
            self.log.error("llc.control is %d insted of %d" % (int(pckt.get_items('llc.control')[-1].get_show()), dsrc_definitions.DSRCllcSnap.control))
            self.stats.llc.control_err += 1
        if int(pckt.get_items('llc.oui')[-1].get_show(), 16) != dsrc_definitions.DSRCllcSnap['oui']:
            self.log.error("llc.oui is %d insted of %d" % (int(pckt.get_items('llc.oui')[-1].get_show()), dsrc_definitions.DSRCllcSnap.oui))
            self.stats.llc.oui_err += 1
        if int(pckt.get_items('llc.type')[-1].get_show(), 16) != dsrc_definitions.DSRCllcSnap['type']:
            self.log.error("llc.type is 0x%x insted of 0x%x" % (hex(int(pckt.get_items('llc.type')[-1].get_show())), dsrc_definitions.DSRCllcSnap.type))
            self.stats.llc.type_err += 1

    
    def _check_transmission_state( self, str ): 
        transmission = ((int(str) & 0xE000) >> 13)
        if transmission == dsrc_definitions.DSRC_TRANMISSION_STATE.DSRC_TRANMISSION_STATE_RESERVED1:
            return False  
        elif transmission == dsrc_definitions.DSRC_TRANMISSION_STATE.DSRC_TRANMISSION_STATE_RESERVED2:
            return False
        elif transmission == dsrc_definitions.DSRC_TRANMISSION_STATE.DSRC_TRANMISSION_STATE_RESERVED3:
            return False
        else:
            return True

  
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
                self.add_limit( ("Frame %d delta time" % frame_id) , frame_delta_time , self._tx_frames, None , 'GTLT')


        # Verify wsmp protocol exists
        if 'wsmp' in packet["frame.protocols"]:
            self.wsmp_packets += 1
            


    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.analyzed_packet_count = 0
        self.wsmp_packets = 0
        return super(TC_BSM_1, self).__init__(methodName, param)

   
    def test_wsmp_tc_1(self):
        """ Test wsmp protocol base on\nsomething else\nif there is
            @fn wsmp_tc_1
            @brief wsmp testing 
            @details Test ID		: TC_SDK2_01\n	
            Test Name 	: BSM Part I Structure\n
            Objective 	: Validate correct field population for Part I of BSM Message\n
            Reference	: REQ_SDK20_BSM_02\n
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.0\SDK2_0_Test_Plan_v2.docx\n
        """
        self.log = logging.getLogger(__name__)
        self.stats = Statistics()

        # unit configuration 

        # expect dictionary as parameter for exapmle  uut_id = (0,1), bsm_tx_period_ms = 100, frames = 1000, gps_scenario="c:\\temp\\nmea_data_1.txt") )
        self._tx_frames = self.param.get('frames', 1000 )
        self._bsm_tx_period_ms = self.param.get('bsm_tx_period_ms', 100 )
        self._tx_power = self.param.get('tx_power', None)
        self._power_dbm8 = self.param.get('power_dbm8', None)
        self._psid = self.param.get('psid', None)
        self._gps_scenario = self.param.get('gps_scenario', None )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        
        if self._gps_scenario == None:
            globals.Error("Gps scenario not exists, please make sure to pass parameters")

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
            # DBG raise globals.Error("GPS simulator is not initilize, please check your configuration")
            pass
        else:
            # Get pointer to object
            gps_sim = globals.setup.instruments.gps_simulator

            # set general tx power
            gps_sim.tx_power( self._gps_tx_power )  
            #load scenario
            gps_sim.load( self._gps_scenario )
            gps_file = "c:\\temp\\gps_rec_tc_bsm_1.txt"

            # Start gps scenario without recording
            gps_sim.start_scenario()        

            self.log.info("Start loop waiting GPS Lock, max time {}.format(self.gps_lock_timeout_sec) )")
            start_time = time.time()
            while ( (time.time() - start_time) < 600):#self.gps_lock_timeout_sec ):
                if (self.uut.managment.get_nav_fix_available() == 1):
                    self.gps_lock = True 
                    self.log.info("GPS locked O.K.")
                    break
                time.sleep(0.2)
 
        
            # Add Gps lock limit     
            self.add_limit( "GPS Locked" , 1 , int(self.gps_lock), None , 'EQ')
        
            if self.gps_lock == False:
                self.log.info("GPS Lock failed")

            else:
                # Start recording gps simulator scenraio data
                gps_sim.start_recording( gps_file )

        self.log.info("Setting sniffer configuration and start capture")
        if globals.setup.instruments.sniffer is None:
            #raise globals.Error("Sniffer is not initilize, please check your configuration")
            pdml_data_file = "test_sdk2_0_tc_bsm_1_gps_on.pdml" #"tests_sdk2_0_tc_bsm_1_151013_114625.pdml"
            full_pdml_file_name = "i:\\%s" % pdml_data_file
            sniffer = None
            self.gps_lock = True
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

        test_expected_time = self._tx_frames * ( self._bsm_tx_period_ms / 1000.0)

        if sniffer != None:
            sniffer.start_capture( capture_data_file )
            
            # Configure BSM values via snmp managment        
            self.uut.managment.set_bsm_tx_period(  self._bsm_tx_period_ms)
            self.uut.managment.set_bsm_tx_interface( self.uut_channel )
            self.uut.managment.set_bsm_tx_enabled( 1 )

            #wait till all frames of first batch are Tx
            time.sleep(((self._bsm_tx_period_ms * self._tx_frames) / 1000) + 10) 
       
            self.uut.managment.set_bsm_tx_interface( self.uut_channel )
            self.uut.managment.set_bsm_tx_enabled( 2 )

            # wait time for all frames to capture
            self.log.info( " Waiting for all frames to be capture, waiting %d" % test_expected_time )
            sniffer.stop_capture()
        
            full_pcap_file_name = "i:\\%s" % capture_data_file
            full_xml_file_name = "i:\\%s" % xml_data_file           
            full_pdml_file_name = "i:\\%s" % pdml_data_file 
            pcap_pdml_conv.export_pcap( full_pcap_file_name, full_pdml_file_name )

        pdml_parser = packet_analyzer.PcapHandler()
        pdml_parser.parse_file( full_pdml_file_name , self._check_bsm )

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
            if self.stats.llc.get_total_err() != 0:
                self.add_limit( "Number of dsap_Errors", 0, self.stats.llc.dsap_err, None, 'EQ')
                self.add_limit( "Number of ssap_Errors", 0, self.stats.llc.ssap_err, None, 'EQ')
                self.add_limit( "Number of control_Errors", 0, self.stats.llc.control_err, None, 'EQ')
                self.add_limit( "Number of oui_Errors", 0, self.stats.llc.oui_err, None, 'EQ')
                self.add_limit( "Number of type_Errors", 0, self.stats.llc.type_err, None, 'EQ')
            elif self.stats.wsmp.get_total_err() != 0:
                self.add_limit( "Number of version_Errors", 0, self.stats.wsmp.version_err, None, 'EQ')
            else:
                self.add_limit( "Number of Initial_value_Errors", 0, self.stats.bsm_init_value_err,
                                    None , 'EQ')
                self.add_limit( "Number of Frames contaning Range Errors", 0, self.stats.bsm_frames_with_range_err,
                                None , 'EQ')
                self.add_limit( "Number of msgCount Errors", 0, self.stats.bsm_msg_cnt_err,
                                None , 'EQ')
                self.add_limit( "Number of DSecond Errors", 0, self.stats.bsm_dsecond_err,
                                None , 'EQ')
                self.add_limit( "Number of speed Errors", 0, self.stats.bsm_speed_err,
                                None , 'EQ')
                if self.stats.bsm_frames_with_range_err != 0:
                    for field in self.stats.bsm.range_err:
                        self.add_limit( "Number of %s range Errors" % (field), 0, self.stats.bsm.range_err[field], None , 'EQ')

        if self.stats.validate == False:
            print "Test validation error"                
        print "test_completed" 

    def _check_bsm(self, pckt):       
        a = wiresharkXML.Template()
        pckt.build_packet( pckt, a)
      
        self.stats.total_frames_processed += 1
        
        # its a BSM 
        if int(pckt.get_items('j2735.msgID')[-1].get_show()) == dsrc_definitions.DSRC_MSG_TYPE.DSRC_MSG_ID_BSM:
            self.stats.bsm_frames_processed +=1 
        else:
            return
            
        self.check_llc_snap( pckt )

        # Verify wsmp protocol exists & check its fields
        if 'wsmp' in pckt.get_items('frame.protocols')[-1].get_show():
            #self.wsmp_packets += 1
            self.check_wsmp( pckt )
            
            
        # tempId should be constant through out this test   
        if self.stats.bsm_frames_processed == 1:
            self.tempId = pckt.get_items('j2735.temporaryid')[-1].get_show()
            self.width  = int(pckt.get_items('j2735.width')[-1].get_show())
            self.length = int(pckt.get_items('j2735.length')[-1].get_show())
            self.brakeSystemStatus = pckt.get_items('j2735.brakeSystemStatus')[-1].get_show()
            self.msg_cnt = long(pckt.get_items('j2735.msgCount')[-1].get_show())

        else:  
            if self.tempId != pckt.get_items('j2735.temporaryid')[-1].get_show():
                self.log.error("BSM temp Id has changed illigaly during the test")
                self.stats.bsm_init_value_err += 1
            if self.width != int(pckt.get_items('j2735.width')[-1].get_show()):
                self.log.error("BSM size width has changed illigaly during the test")
                self.stats.bsm_init_value_err += 1
            if self.length != int(pckt.get_items('j2735.length')[-1].get_show()):
                self.log.error("BSM Size length has changed illigaly during the test")
                self.stats.bsm_init_value_err += 1
            if self.brakeSystemStatus != pckt.get_items('j2735.brakeSystemStatus')[-1].get_show():
                self.log.error("BSM brakeSystemStatus has changed illigaly during the test")
                self.stats.bsm_init_value_err += 1                
            if self.check_msg_count(long(pckt.get_items('j2735.msgCount')[-1].get_show())) == False:
                self.log.error("BSM msg count is out of sequence")
                self.stats.bsm_msg_cnt_err += 1
                    

        if self.check_bsm_ranges(pckt, self.gps_lock) == False:
            self.stats.bsm_frames_with_range_err += 1
        #elif self.check_dsecond(analyzer.get_items('j2735.dsecond'), UTC) == False:
        #    self.stats.bsm_dsecond_err += 1      
        elif self._check_transmission_state(pckt.get_items('j2735.speed')[-1].get_show()) == False:
            self.stats.bsm_speed_err += 1


class Statistics(object):
    
    class LLC(object):

        def __init__(self):
            self.dsap_err = 0
            self.ssap_err = 0
            self.control_err = 0
            self.oui_err  = 0
            self.type_err = 0

        def get_total_err(self):
            err = (self.dsap_err, self.ssap_err, self.control_err, self.oui_err, self.type_err)
            return sum(err)
    
    class WSMP(object):
        def __init__(self):
            self.verion_err = 0

        def get_total_err(self):
            err = (self.verion_err,)
            return sum(err)

    class BSM(object):
        def __init__(self):
            self.range_err = {'j2735.msgCount'        : 0,
                        'j2735.temporaryid'  : 0,
                        'j2735.uniqueid'     : 0,
                        'j2735.dsecond'      : 0,
                        'j2735.pos3D.lat'    : 0,
                        'j2735.pos3D.long'   : 0,
                        'j2735.pos3Delevation' : 0,                        
                        'j2735.accuracy'     : 0,                     
                        'j2735.speed'        : 0,
                        'j2735.heading'      : 0,
                        'j2735.steeringAngle': 0,
                        'j2735.accelSet4Way.lon'     : 0,
                        'j2735.accelSet4Way.lat'     : 0,
                        'j2735.accelSet4Way.vert'    : 0,
                        'j2735.accelSet4Way.yaw'     : 0,
                        'j2735.brakeSystemStatus'    : 0,
                        'j2735.width'        : 0,
                        'j2735.length'       : 0
                        }      
            
    def __init__(self):
        self.total_frames_processed = 0
        self.bsm_frames_processed = 0
        self.bsm_frames_with_range_err = 0
        self.bsm_msg_cnt_err = 0
        self.bsm_dsecond_err = 0
        self.bsm_speed_err = 0
        self.bsm_init_value_err = 0
        self.llc = self.LLC()
        self.wsmp = self.WSMP()
        self.bsm = self.BSM()

    def get_total_err(self):
        err = (self.bsm_msg_cnt_err, self.bsm_frames_with_range_err, self.bsm_dsecond_err, 
               self.bsm_speed_err, self.bsm_init_value_err, self.llc.get_total_err(), self.wsmp.get_total_err())
        return sum(err)

    def validate(self):      
        return 0 == (self.stats.total_frames_processed - self.get_total_err())
            
#if __name__ == "__main__":
#  tc_bsm_1 = TC_BSM_1(param =  dict( uut_id = (0,1), bsm_tx_period_ms = 100, frames = 1000, gps_scenario="Neter2Eilat") ))                        
                        
