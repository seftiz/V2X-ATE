"""
@file       tc_navapi.py
@brief      Testsuite for testing Navigation api 
@author    	Shai Shochat
@version	0.1
@date		May 2013
\link		\\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx \endlink
"""

# import global and general setup var
from lib import station_setup
from uuts import common
from tests import common
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

log = logging.getLogger(__name__)


# @topology('CF01')
class TC_NAV_1(common.V2X_SDKBaseTest):

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
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )
        try:
            self.uut.close_qa_cli("nav_api")
        except Exception:
            pass

    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.cli_name = 'nav_api'
        return super(TC_NAV_1, self).__init__(methodName, param)


    def nav_lock_handler(self, data):
        
        self._last_msg_timestamp = time.time()
        nav_fix = data.split(",")
        if nav_fix[0] == "$ATLK":
            try:
                # make sure a compllete sentence arrived
                if ((len(nav_fix) > 5) and (nav_fix[3] != "Nan") and (nav_fix[4] != "Nan")):
                    self.gps_lock = True
            except IndexError:
                pass

    def get_test_parameters( self ):
        super(TC_NAV_1, self).get_test_parameters()
        self._start_speed_mps = self.param.get('start_speed_mps', 20 )
        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )
        self._point_distance_err_max = self.param.get('point_distance_err_max', 1.5 )
        self._altitude_distance_err_max_meter = self.param.get('altitude_distance_err_max_meter', 3 )
        self._max_hdop = self.param.get('max_hdop', 5 )
        self.target_cpu = self.param.get('target_cpu', 'arm') 

    def instruments_initilization(self):
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

        self.gps_file = os.path.join( tempfile.gettempdir(),  self._testMethodName + "_gps_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')
        self.nav_file_recorder = os.path.join( tempfile.gettempdir(),  self._testMethodName + "_nav_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'txt')


    def unit_configuration(self):

        gps_lock = True
        # start gps scenario
        if self.is_gps_active():
            self.gps_sim.start_scenario()
            gps_lock = self.wait_for_gps_lock( self.uut, self._gps_lock_timeout_sec )

            # Add Gps lock limit     
            self.add_limit( "GPS Locked" , int(True) , int(gps_lock), None , 'EQ')
            if gps_lock == False:
                log.info("GPS Lock failed")

            return gps_lock
        else:
            raise globals.Error( " GPS simulator is not active " ) 


    def main(self):

        self.uut.create_qa_cli(self.cli_name, target_cpu = self.target_cpu)

        # start nav session in evk
        self.uut.qa_cli(self.cli_name).nav.init( type = globals.LOCAL )

        self.uut.qa_cli(self.cli_name).nav.start( ('file', self.nav_file_recorder) )
        # Start recording gps simulator scenraio data

        self.gps_sim.start_recording( self.gps_file )

        # run scenrio for a period of time
        # print "NOTE : test will sleep for {} for gps data".format(self._scenario_time_sec) 
        start_time = time.time()
        while ( (time.time() - start_time) < self._scenario_time_sec ):
            time.sleep(0.5)
        
        # Stop and clean gps 
        self.gps_sim.stop_recording()
        # Stop nav stop        
        self.uut.qa_cli(self.cli_name).nav.stop()
        self.uut.qa_cli(self.cli_name).nav.terminate()
        self.gps_sim.stop_scenario()

    
    def debug_override( self, base_dir = None ):
        file_date_time = '20151118-151744'

        # DEBUG ONLY !!!!!!!   override for tests !!!!!
        self.gps_file = os.path.join( tempfile.gettempdir(),  'test_nav_api_gps_' + file_date_time + "." + 'txt')
        self.nav_file_recorder = os.path.join( tempfile.gettempdir(),  'test_nav_api_nav_' + file_date_time + "." + 'txt')

        #self.nav_file_recorder = "C:\\Temp\\test_nav_api_nav_{}.txt".format( file_date_time )
        #self.gps_file = "C:\\Temp\\test_nav_api_gps_{}.txt".format( file_date_time )

        print >> self.result._original_stdout, "DEBUG Override is active "
        print >> self.result._original_stdout, "GPS log file : {}".format(  self.gps_file )
        print >> self.result._original_stdout, "NAV_FIX log file : {}".format(  self.nav_file_recorder )


    def analyze_results(self):

        # Analyze any results
        gps_data = self.load_data_file( self.gps_file )
        uut_data = self.load_data_file( self.nav_file_recorder , type = 'navfix' )

        # uut receive 10 unit
        msg_ratio_uut_to_sim = 10
        max_offset_in_sec_allowed = 10
        cnt  = 0
                
        found_first_aligned_point = -1
        i = 0
        k = 0

        # Find first gps data in nav data
        # Define counters
        self.gps_stats = Statistics()
        self.nav_stats = Statistics()
        dist_calc = distance.distance

        # Start Search and compare algoririthm.
        for gps_sentence in gps_data:
            k += 1
            if gps_sentence.sen_type == 'GPRMC':
                # find nmea in uut
                self.gps_stats.total_frames_processed += 1
                try:
                    gps_time = datetime.strptime(gps_sentence.datestamp + gps_sentence.timestamp , '%d%m%y%H%M%S.%f')
                except:
                    self.gps_stats.total_frames_misparsed += 1
                    continue

                if ( gps_sentence.data_validity != 'A' ):
                    continue
                
                #if gps_sentence.validity
                self.convert_nmea_to_dec( gps_sentence )

                # If simulator Add this messe                
                if ( gps_data[k].sen_type == 'GPVTG' ):
                    k += 1

                if (len(gps_data) >= k) and (gps_data[k].sen_type == 'GPGGA'):
                    gps_sen_gpgga = gps_data[k]
                    self.convert_nmea_to_dec( gps_sen_gpgga )

                if float(gps_sen_gpgga.horizontal_dil) >= self._max_hdop:
                    self.gps_stats.total_frames_hdop_fail += 1
                    continue
                
                # Convert Knots Speed to mps
                while ( i < len(uut_data) ):
                    # Make sure field parsed 
                    try:
                        nav_time = datetime.utcfromtimestamp(float(uut_data[i].nav_time))
                    except:
                        self.nav_stats.total_frames_misparsed += 1
                        i += 1
                        continue

                    # Check to verify if nav time is not 0
                    if nav_time == 0:
                        self.nav_stats.total_frames_misparsed += 1
                        i += 1
                        continue


                    # The comparison is not made for Zero due to some bit lost in converting time stamp from double to uint32 in the evk, so results of 13.0 might be 13.099999
                    if ( abs((gps_time - nav_time).total_seconds()) < 0.01):
                        self.gps_stats.total_frames_found += 1
                        self.nav_stats.total_frames_found += 1
                        self.nav_stats.total_frames_processed += 1

                        found_first_aligned_point = 1
                        # start compare all other fields

                        # We processed the GPRMC message, get next message which shuold be with same time stamp and shuold be GPGGA for altitude
                        gps_gpgga_time = datetime.strptime(gps_sentence.datestamp + gps_sen_gpgga.timestamp , '%d%m%y%H%M%S.%f')

                       
                        if ( abs((gps_time - gps_gpgga_time).total_seconds()) == 0):
                            try: # make sure field exists
                                gps_point = Point( gps_sentence.lat, gps_sentence.lon, gps_sen_gpgga.antenna_altitude)
                                nav_point = Point( uut_data[i].position_latitude_deg, uut_data[i].position_longitude_deg, uut_data[i].position_altitude_m )
                                frame_with_altitude = 1
                            except:
                                pass

                        else:
                            gps_point = Point( gps_sentence.lat, gps_sentence.lon, 0)
                            nav_point = Point( uut_data[i].position_latitude_deg, uut_data[i].position_longitude_deg, 0 )
                            self.nav_stats.total_frames_wo_altitude += 1
                            frame_with_altitude = 0


                        # Check altitude and longtitude 
                        points_distance = dist_calc(gps_point, nav_point).meters
                        # Make sure in range of 1.5 meters
                        if 0 < abs(points_distance) < self._point_distance_err_max:
                            self.nav_stats.total_frames_passed_lat_lon += 1
                        else:
                            self.nav_stats.total_frames_failed_lat_lon += 1
                            log.info( "GPS point time {} delta {} lat{} long {} alt {}".format(gps_gpgga_time , points_distance , gps_point.latitude,gps_point.longitude,gps_point.altitude) + "!= Nav point  lat : {} long {} alt {}".format(nav_point.latitude,nav_point.longitude,nav_point.altitude) )
                            # limit_desc =  "Point@time {},  lat:{} long:{}, alt:{} Distance".format( gps_sentence.timestamp, gps_point.latitude, gps_point.longitude, gps_point.altitude) 
                            # self.add_limit( limit_desc, 0.0 , points_distance , self._point_distance_err_max , 'GELE')

                        # Check if altitude exists ??
                        if frame_with_altitude == 1:
                            self.nav_stats.total_frames_with_altitude += 1
                            alt_distance = abs(float(gps_sen_gpgga.antenna_altitude) - float(uut_data[i].position_altitude_m))
                            if 0 < alt_distance < self._altitude_distance_err_max_meter:
                                self.nav_stats.total_frames_passed_alt += 1
                            else:
                                self.nav_stats.total_frames_failed_alt += 1
                                log.info( "GPS point time {} altitude failed, Delta : {} alt {}".format(gps_gpgga_time , alt_distance , gps_point.altitude) + "!= Nav point alt {}".format(nav_point.altitude) )



                        
                        try:
                            speed_ground_mps = float(gps_sentence.spd_over_grnd) * 0.514444 
                        except Exception:
                            speed_ground_mps = 0

                        try:
                            gps_heading = float(gps_sentence.true_course)
                        except Exception:
                            gps_heading = 0

                        # current  heading  (<  2?)  when  moving between 0.56 m/s and 12.5 m/s? 
                        if 0.56 < speed_ground_mps < 12.5:
                            self.nav_stats.count_heading_low_speed += 1
                            if ( gps_heading - float(uut_data[i].movement_horizontal_direction_deg) ) > 2:
                                log.info( "Heading Fail (LS d<2) @ GPS time {}, Nav Heading {}, Gps Heading {}, Gps Speend {} m/s, nav speed {}".format(gps_time, uut_data[i].movement_horizontal_direction_deg, gps_heading, speed_ground_mps, uut_data[i].movement_horizontal_speed_mps) )
                                self.nav_stats.fail_heading_low_speed += 1
                            else:
                                self.nav_stats.pass_heading_low_speed += 1
                                
                            
                            pass
                        # current  vehicle  speed  (+/0.35  m/s)  and heading (+/- 3?) when moving > 12.5 m/s
                        elif  speed_ground_mps > 12.5:
                            self.nav_stats.count_heading_high_speed += 1
                            if ( gps_heading - float(uut_data[i].movement_horizontal_direction_deg) ) > 2:
                                log.info( "Heading Fail (HS d>2) @ GPS time {}, Nav Heading {}, Gps Heading {}, Gps Speend {} m/s, nav speed {}".format(gps_time, uut_data[i].movement_horizontal_direction_deg, gps_heading, speed_ground_mps, uut_data[i].movement_horizontal_speed_mps) )
                                self.nav_stats.fail_heading_high_speed += 1
                            else:
                                self.nav_stats.pass_heading_high_speed += 1
                            
                            if ( speed_ground_mps - float(uut_data[i].movement_horizontal_speed_mps) ) > 0.35:
                                log.info( "Speed Fail (HS > 0.35) @ GPS time {}, Nav Heading {}, Gps Heading {}, Gps Speend {} m/s, nav speed {}".format(gps_time, uut_data[i].movement_horizontal_direction_deg, gps_heading, speed_ground_mps, uut_data[i].movement_horizontal_speed_mps) )
                        else:
                            pass


                    # If the gps data is behind the nav fix time, move gps data forward
                    elif gps_time < nav_time: 
                        break
                    else:
                        i += 1
                        continue
                     
                    i += 1
                
                    
                if found_first_aligned_point != 1:
                    self.gps_stats.total_frames_not_found += 1
                    # reset search index for next point
                    i = 0

                    
        gps_sim = None

    def print_results(self):
        # Start Handling limit
        self.add_limit( "Total GPS Points processed" , self.gps_stats.total_frames_processed , self.gps_stats.total_frames_processed, None , 'EQ')
        self.add_limit( "Total GPS Misparsed" , 0, self.nav_stats.total_frames_misparsed, 5 , 'LT')
        self.add_limit( "Total Fixes Matched" , 0 , self.nav_stats.total_frames_found, self.gps_stats.total_frames_processed , 'GTLE')


        # Set Max Allowed not found
        not_fnd_max = (float(self.gps_stats.total_frames_not_found) / float(self.gps_stats.total_frames_processed)) * 100
        self.add_limit( "Total GPS points not found (%)" , 0, round(not_fnd_max,1), 10.0 , 'GELE')

        
        
        self.add_limit( "Total Lon-Lat Fixes failed ( > {}m )".format (self._point_distance_err_max) , 0 , self.nav_stats.total_frames_failed_lat_lon, self.nav_stats.total_frames_found , 'GELE')
        self.add_limit( "Total Lon-Lat Fixes Passed ( < {}m )".format (self._point_distance_err_max) , 1 , self.nav_stats.total_frames_passed_lat_lon, (self.nav_stats.total_frames_found -  self.nav_stats.total_frames_failed_lat_lon), 'GELE')

        # Longitude, Latitude	Accurate Radius 1.5m from actual position at fix time under 1 sigma error (probability of being outside the limit is < 39.4%)
        try: 
            fail_ratio = (float(self.nav_stats.total_frames_failed_lat_lon) / float(self.nav_stats.total_frames_processed) ) * 100.0
        except ZeroDivisionError:
            self.add_limit( "Total Lon-Alt fix failes (N/A)" , -1 , 0, None , 'EQ')
        else:
            self.add_limit( "Total Lon-Alt fix failes (%)" , 0 , fail_ratio, 39 , 'GELE')

        try:
            fail_ratio = (float(self.nav_stats.total_frames_failed_alt) / float(self.nav_stats.total_frames_with_altitude)) * 100.0
        except ZeroDivisionError:
            self.add_limit( "Total Alt fix failes (N/A)" , -1 , 0, None , 'EQ')
        else:
            self.add_limit( "Total Alt fix failes (%)" , 0 , fail_ratio, 39 , 'GELE')

        #self.add_limit( "Total GPS points not found" , self.gps_stats.total_frames_not_found , 0, None , 'EQ')
        #self.add_limit( "Total GPS points failed" , self.gps_stats.total_frames_failed , 0, None , 'EQ')
        #self.add_limit( "Total GPS points passed" , self.gps_stats.total_frames_passed ,  self.gps_stats.total_frames_processed, None , 'EQ')
        #self.add_limit( "Total NAV points passed " , self.gps_stats.total_frames_passed , 0, None , 'EQ')


        self.add_limit( "Total GPS HDOP fails" , None , self.gps_stats.total_frames_hdop_fail, 10, 'LT')

    def test_nav_api(self):
        """ Test nav api correctness
            @fn         test_nav_api_1
            @brief      Verify nav api data and accurecy correctness 
            @details    Test ID	: TC_SDK2.1_NAV_01\n
                        Test Name 	: NAV API\n
                        Objective 	: Validate correct positioning data reported by NAV API\n
                        Reference	: REQ_SDK2.1_NAVAPI_01\n
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx\n
        """
        

        # unit configuration 
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )


        #Test scenario shall include the following driving segments (derived from SafetyPilot test scenario), played by GNSS simulator:
        #Each test case should be executed at least 5 minutes.
        #Segment	Detail
        #Straight line	Straight line, driving speed 50kph ? 100kph.
        #Elliptic track course	50, 100,150 kph driving speed
        #Figure ? 8	50, 100,150 kph driving speed

        #Additional scenario details:
        #HDOP < 5

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

        # self.debug_override()


        self.instruments_initilization()

        rv = self.unit_configuration()
        # Check if unit is locked
        if rv == True:
            self.main()
    
        self.analyze_results()

        self.print_results()
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )




class Statistics(object):

    def __init__(self):
        self.total_frames_processed = 0
        self.total_frames_found = 0
        self.total_frames_passed_lat_lon = 0
        self.total_frames_passed_alt = 0
        self.total_frames_failed_lat_lon = 0
        self.total_frames_failed_alt = 0
        self.total_frames_not_found = 0
        self.total_frames_misparsed = 0
        self.total_frames_wo_altitude = 0
        self.total_frames_with_altitude = 0
        self.total_frames_hdop_fail = 0
        self.count_heading_high_speed = 0
        self.fail_heading_high_speed = 0
        self.pass_heading_high_speed = 0
        self.count_heading_low_speed = 0
        self.pass_heading_low_speed = 0
        self.fail_heading_low_speed = 0
