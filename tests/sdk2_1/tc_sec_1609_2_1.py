"""
@file       tc_sec_1609_2_1.py
@brief      Testsuite for security 1609.2 vad format 
@author    	Shai Shochat
@version	0.1
@date		August 2013
\link		\\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx \endlink
"""

import sys, os
import time
from datetime import datetime
import logging
import tempfile
import decimal

from lib import station_setup
from uuts.craton import common
from tests import common
from lib import instruments_manager
from lib import packet_analyzer

from lib.instruments import spectracom_gsg_6
from uuts.craton.cli import navigation
from pynmea.streamer import NMEAStream
from lib import globals


# @topology('CF01')
class TC_SEC_1609_2_1(common.V2X_SDKBaseTest):
    """
    @class TC_SEC_1609_2_1
    @brief Security 1609.2 standard for certificate testing 
    @author Shai Shochat
    @version 0.1
    @date	12/08/2013
    """

    def runTest(self):
        pass

    def tearDown(self):
        pass


    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        return super(TC_SEC_1609_2_1, self).__init__(methodName, param)
   
    def test_certificate_changes(self):
        """ Test nav api correctness
            @fn         test_nav_api_1
            @brief      Validate correct certificate loading and usage 
            @details    Test ID	: TC_SDK2.1_SEC_01\n
                        Test Name 	: Certificate load \n
                        Objective 	: Validate correct certificate loading and usage
                        Reference	: REQ_SDK2.1_SEC_02\n
            @see Test Plan	: \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx\n
        """
        log = logging.getLogger(__name__)

        # Get Test parameters
        self._gps_scenario = self.param.get('gps_scenario', None )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )

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

        # handle gps scenario
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

        
        # Load Certificates to unit, this test assume pre certificates exists in directory
        
        # Load VAD certificates to evk.
        self.uut.cli.start_certs( source_dir, targer_dir)
        # certld vad-legacy /storage/certs




        dir_name = tempfile.gettempdir()
        timestr = time.strftime("%Y%m%d-%H%M%S")
        nav_file_name = 'nav_data'
        gps_file_name = 'gps_rec'
        nav_file_recorder = os.path.join(dir_name, nav_file_name + "_" + timestr + "." + 'txt')
        gps_file = os.path.join(dir_name, gps_file_name + "_" + timestr + "." + 'txt')



        # Load certificates to unit is not exists


        log.info("test will search nav lock up to {}".format(self._max_nav_fix_lock_time_sec) )
        # Start gps scenario without recording
        gps_sim.start_scenario()
        use_lock_by_data = 0
        if ( use_lock_by_data == 1 ):
            # start nav session in evk
            self.uut.cli.nav_init( 'local' )

            self._last_msg_timestamp = time.time()
            self.uut.cli.nav_start( ('handler', self.nav_lock_handler) )

            start_time = time.time()
            log.info("  Start loop waiting GPS Lock")

            while ( self.gps_lock == False ):
                if  ( (time.time() - start_time) > self._max_nav_fix_lock_time_sec ):
                    log.error("GPS lock failed to find for 5 Mins ?")
                    break

                # Make sure messages arrive from unit
                if ( (time.time() - self._last_msg_timestamp) > 10.0 ):
                    log.error("NAV fix not arrvied for 10 seconds")
                    break

                time.sleep(0.2)
 
            time.sleep(1)
            self.uut.cli.nav_stop()

        else:
            log.info("  Start loop waiting GPS Lock")
            start_time = time.time()
            while ( (time.time() - start_time) < self._max_nav_fix_lock_time_sec ):
                if (self.uut.managment.get_nav_fix_available() == 1):
                    self.gps_lock = True 
                    log.error("GPS locked O.K.")
                    break

                time.sleep(0.2)
 
        if self.gps_lock == False:
            self.add_limit( "GPS Locked" , 1 , 0, None , 'EQ')
            log.info("GPS Lock failed")
            return 
        else:
            self.add_limit( "GPS Locked" , 1 , 1, None , 'EQ')

        # start nav session in evk
        self.uut.cli.nav_init( 'local' )

        self.uut.cli.nav_start( ('file', nav_file_recorder) )
        gps_sim.start_recording( gps_file )

        # run scenrio for a period of time
        print "NOTE : test will sleep for {} for gps data".format(self._scenario_time_sec) 
        start_time = time.time()
        while ( (time.time() - start_time) < self._scenario_time_sec ):
            time.sleep(0.2)

        
        #stop and clean
        gps_sim.stop_scenario()
        gps_sim.stop_recording()
        self.uut.cli.nav_stop()

        # DEBUG ONLY !!!!!!!   override for tests !!!!!
        #nav_file_recorder = "C:\\Users\\shochats\\AppData\\Local\\Temp\\nav_data_20130702-150427.txt"
        #gps_file = "C:\\Users\\shochats\\AppData\\Local\\Temp\\gps_rec_20130702-150427.txt"
        
        print "GPS log file : %s\n\r" % gps_file
        print "NAV_FIX log file : %s\n\r" % nav_file_recorder

        gps_data = self.load_data_file( gps_file )
        uut_data = self.load_data_file( nav_file_recorder , type = 'navfix' )


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
        nav_stats = Statistics()
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
                
                self.convert_nmea_to_dec( gps_sentence )

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
                        nav_stats.total_frames_misparsed += 1
                        i += 1
                        continue
                    # The comparison is not made for Zero due to some bit lost in converting time stamp from double to uint32 in the evk, so results of 13.0 might be 13.099999
                    if ( abs((gps_time - nav_time).total_seconds()) < 0.01):
                        self.gps_stats.total_frames_found += 1
                        nav_stats.total_frames_found += 1
                        nav_stats.total_frames_processed += 1

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
                            nav_stats.total_frames_wo_altitude += 1
                            frame_with_altitude = 0


                        # Check altitude and longtitude 
                        points_distance = dist_calc(gps_point, nav_point).meters
                        # Make sure in range of 1.5 meters
                        if 0 < abs(points_distance) < self._point_distance_err_max:
                            nav_stats.total_frames_passed_lat_lon += 1
                        else:
                            nav_stats.total_frames_failed_lat_lon += 1
                            log.info( "GPS point lat : {} long {} alt {}".format(gps_point.latitude,gps_point.longitude,gps_point.altitude) + "!= Nav point  lat : {} long {} alt {}".format(nav_point.latitude,nav_point.longitude,nav_point.altitude) )
                            # limit_desc =  "Point@time {},  lat:{} long:{}, alt:{} Distance".format( gps_sentence.timestamp, gps_point.latitude, gps_point.longitude, gps_point.altitude) 
                            # self.add_limit( limit_desc, 0.0 , points_distance , self._point_distance_err_max , 'GELE')

                        # Check if altitude exists ??
                        if frame_with_altitude == 1:
                            nav_stats.total_frames_with_altitude += 1
                            alt_distance = abs(float(gps_sen_gpgga.antenna_altitude) - float(uut_data[i].position_altitude_m))
                            if 0 < alt_distance < self._altitude_distance_err_max_meter:
                                nav_stats.total_frames_passed_alt += 1
                            else:
                                nav_stats.total_frames_failed_alt += 1


                        
                        
                        speed_ground_mps = float(gps_sentence.spd_over_grnd) * 0.514444 
                        gps_heading = float(gps_sentence.true_course)

                        # current  heading  (<  2?)  when  moving between 0.56 m/s and 12.5 m/s? 
                        if 0.56 < speed_ground_mps < 12.5:
                            nav_stats.count_heading_low_speed += 1
                            if ( gps_heading - float(uut_data[i].movement_horizontal_direction_deg) ) > 2:
                                log.info( "Heading Fail (LS) @ GPS time {}, Nav Heading {}, Gps Heading {}, Gps Speend {} m/s, nav speed {}".format(gps_time, uut_data[i].movement_horizontal_direction_deg, gps_heading, speed_ground_mps, uut_data[i].movement_horizontal_speed_mps) )
                                nav_stats.fail_heading_low_speed += 1
                            else:
                                nav_stats.pass_heading_low_speed += 1
                                
                            
                            pass
                        # current  vehicle  speed  (+/0.35  m/s)  and heading (+/- 3?) when moving > 12.5 m/s
                        elif  speed_ground_mps > 12.5:
                            nav_stats.count_heading_high_speed += 1
                            if ( gps_heading - float(uut_data[i].movement_horizontal_direction_deg) ) > 2:
                                log.info( "Heading Fail (HS) @ GPS time {}, Nav Heading {}, Gps Heading {}, Gps Speend {} m/s, nav speed {}".format(gps_time, uut_data[i].movement_horizontal_direction_deg, gps_heading, speed_ground_mps, uut_data[i].movement_horizontal_speed_mps) )
                                nav_stats.fail_heading_high_speed += 1
                            else:
                                nav_stats.pass_heading_high_speed += 1
                            
                            if ( speed_ground_mps - float(uut_data[i].movement_horizontal_speed_mps) ) > 0.35:
                                log.info( "Speed Fail (HS) @ GPS time {}, Nav Heading {}, Gps Heading {}, Gps Speend {} m/s, nav speed {}".format(gps_time, uut_data[i].movement_horizontal_direction_deg, gps_heading, speed_ground_mps, uut_data[i].movement_horizontal_speed_mps) )
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


        # Start Handling limit
        self.add_limit( "Total GPS Points processed" , self.gps_stats.total_frames_processed , self.gps_stats.total_frames_processed, None , 'EQ')
        self.add_limit( "Total GPS Misparsed" , 0, nav_stats.total_frames_misparsed, None , 'GT')
        self.add_limit( "Total Fixes Matched" , 0 , nav_stats.total_frames_found, self.gps_stats.total_frames_processed , 'GTLE')


        # Set Max Allowed not found
        not_fnd_max = (float(self.gps_stats.total_frames_not_found) / float(self.gps_stats.total_frames_processed)) * 100
        self.add_limit( "Total GPS points not found (%)" , 0, round(not_fnd_max,1), 10.0 , 'GELE')

        
        
        self.add_limit( "Total Lon-Lat Fixes failed" , 0 , nav_stats.total_frames_failed_lat_lon, self.gps_stats.total_frames_processed , 'GELE')
        self.add_limit( "Total Lon-Lat Fixes Passed" , 0 , nav_stats.total_frames_passed_lat_lon, (self.gps_stats.total_frames_processed -  nav_stats.total_frames_failed_lat_lon), 'GELE')

        # Longitude, Latitude	Accurate Radius 1.5m from actual position at fix time under 1 sigma error (probability of being outside the limit is < 39.4%)
        fail_ratio = (float(nav_stats.total_frames_failed_lat_lon) / float(nav_stats.total_frames_processed)) * 100.0
        self.add_limit( "Total Lon-Alt fix failes" , 0 , fail_ratio, 39 , 'GELE')

        fail_ratio = (float(nav_stats.total_frames_failed_alt) / float(nav_stats.total_frames_with_altitude)) * 100.0
        self.add_limit( "Total Alt fix failes" , 0 , fail_ratio, 39 , 'GELE')


        self.add_limit( "Total GPS HDOP fails" , None , self.gps_stats.total_frames_hdop_fail, 10 , 'LE')

        #self.add_limit( "Total GPS points not found" , self.gps_stats.total_frames_not_found , 0, None , 'EQ')
        #self.add_limit( "Total GPS points failed" , self.gps_stats.total_frames_failed , 0, None , 'EQ')
        #self.add_limit( "Total GPS points passed" , self.gps_stats.total_frames_passed ,  self.gps_stats.total_frames_processed, None , 'EQ')
        #self.add_limit( "Total NAV points passed " , self.gps_stats.total_frames_passed , 0, None , 'EQ')

          
        print "test_completed"
        


