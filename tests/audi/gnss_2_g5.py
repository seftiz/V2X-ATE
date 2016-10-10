"""
    @file  
    Implement audi test case for gnss to its-g5 path 

    TP :  @link \\fs01\docs\system\Integration\Test_Plans\SW_Releases\SDK2.1\SDK2_1_Test_Plan_v2.docx @endlink 
"""


import logging
from lib import station_setup
from uuts import common
from tests import common
from lib import instruments_manager, packet_analyzer, globals, gps_simulator

from lib.instruments import spectracom_gsg_6
from uuts.craton.cli import navigation
from pynmea.streamer import NMEAStream
import pyshark


# import geopy pacakge for calculations
from geopy.point import Point
from geopy import distance

# from sdk20 import setup

import sys, os, time
from datetime import datetime
import tempfile
import decimal

class TC_GNSS_2_G5(common.V2X_SDKBaseTest):
    """
    @class TC_GNSS_2_G5
    """
 
    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        self.stats = Statistics()
        super(TC_GNSS_2_G5, self).__init__(methodName, param)
        
    def get_test_parameters( self ):
        # Call father class
        super(TC_GNSS_2_G5, self).get_test_parameters()

        self._scenario_time_sec = self.param.get('scenario_time_sec', 300 )
   
    def test_gnss(self):
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

        #self.instruments_initilization()
        #self.unit_configuration()
        #self.main()

        self.debug_override()

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
        self.log.info("Getting Sniffer info")
        if globals.setup.instruments.sniffer is None:
            raise globals.Error("Sniffer is not initilize or define in setup, please check your configuration")
        else:
            # Get pointer to object
            self.sniffer = globals.setup.instruments.sniffer

        # initlize sniffer
        self.sniffer.initialize()
        self.sniffer.set_interface([0,1])
        # tshark app used for capturing frames must verify license of sirit and it take time ~ 15 seconds 
        time.sleep(20)

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

    def main(self):
            

        # Start capture frames from sirit.
        dir, file = os.path.split(os.path.abspath(self.sniffer_file))

        if self.sniffer.type == 'sirit':
            self.sniffer.configure_dsrc_tool()

        # Start recording gps simulator scenraio data
        # self.gps_sim.start_recording( self.gps_file )

        ref_gps = gps_simulator.ExternalGpsRecorder()
        ref_gps.start_recording( self.gps_file )

        self.sniffer.start_capture( file, dir )

        # run scenrio for a period of time
        # print "NOTE : test will sleep for {} for gps data".format(self._scenario_time_sec) 
        start_time = time.time()
        while ( (time.time() - start_time) < self._scenario_time_sec ):
            time.sleep(0.5)

        # Stop and clean gps 
        ref_gps.stop_recording()

        # self.gps_sim.stop_recording()
        # Stop sniffer capture file
        self.sniffer.stop_capture()
        
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

        dist_calc = distance.distance

        gps_data = self.load_data_file( self.gps_file )
        cam_data = pyshark.FileCapture( self.sniffer_file )
        
        current_gps_file_pos = 0
        for frame_idx,frame in  enumerate(cam_data._packets):

            self.stats.total_frames += 1
            try:
                self.stats.layers_cntr[frame.layers[-1].layer_name] += 1
            except Exception:
                self.log.error("Layer is not defined in stats %s" % frame.layers[-1].layer_name )
                self.stats.layers_cntr['unkown'] += 1

            if frame.layers[-1].layer_name != 'cam':
                continue

            self.stats.total_cam_frames += 1
            #get GN Source position vector location

            gn_gnss = Point( float( int('0x' + frame.gn.get_field('sopv_lat').value , 0) / 1e7) ,float( int('0x' + frame.gn.get_field('sopv_long').value , 0) / 1e7) , 0)

            # TIME_DIFF_MS_1970_2004_MSEC =  1072915200000.0
            # tai_time_ms = time.mktime( (datetime(2004, 1, 1, 0, 0)).timetuple() ) * 1000.0
            # gn_timestamp_utc =  datetime.utcfromtimestamp( ( (float(frame.gn.sopv_tst)  + tai_time_ms) / 1000.0) )
            #gn_tst_calc_sec =  ( (float(frame.gn.sopv_tst)  + tai_time_ms) / 1000.0 )
            gn_timestamp =  float(frame.gn.sopv_tst)

            #get CAM location
            cam_gnss = Point( float(int(frame.cam.latitude, 0) /1e7) , float( int(frame.cam.longitude,0) / 1e7) , 0 ) # frame.cam.altitud
            cam_tst = int(frame.cam.generationDeltaTime, 0)

            #calc time diffrence between CAM and geo 
            gn_tst_to_cam_time = ( int(frame.gn.sopv_tst, 0) % pow(2,16) )
            time_diff_between_gn_cam = abs(gn_tst_to_cam_time - cam_tst) # if gn_tst > cam_tst else (cam_tst + (pow(2,16) - gn_tst))

            if ( time_diff_between_gn_cam > 100 ):
                self.log.warning( "CAM-GN time limit is over > 100mSec, %d at frame %d" % ( time_diff_between_gn_cam, frame_idx) )
                self.stats.time_diff_gn_cam_fail += 1

            
            unit_speed_ms = int(frame.cam.speedValue,0) / 1e2 # Units convert
            # Calc the distance between CAM and GN generation on current speed value
            s = unit_speed_ms * ( float(time_diff_between_gn_cam) / 1e3)
            # Calculate diffrence between the points
            points_distance = dist_calc(cam_gnss, gn_gnss).meters
            if abs( s - points_distance ) > 1.5:
                self.log.warning( "CAM-GN gnss location is over 1.5, %d at frame %d" % ( abs( s - points_distance ), frame_idx) )
                self.stats.gnss_cam_gn_mismatch +=1

            #Search pos in the gps
            for i in xrange( current_gps_file_pos, len(gps_data) ):
                gprmc_sentences = 0
                gps_sentence = gps_data[i]
                if gps_sentence.sen_type == 'GPRMC':
                    try:
                        gps_time = datetime.strptime(gps_sentence.datestamp + gps_sentence.timestamp , '%d%m%y%H%M%S.%f')
                        # convert current time to geo timestamp 
                        current_time = ( gps_time - datetime(2004, 1, 1, 0, 0) ).total_seconds() + 3 # Add 3 leap seconds from 2004.
                        current_time_tst = ( current_time * 1000 ) % pow(2, 32)

                    except:
                        self.log.warning( "Failed to parse gps sentence ")
                        self.stats.total_frames_misparsed += 1
                        continue
                    
                    gprmc_sentences +=1

                    # Data is applica
                    delta_time_ms = abs(current_time_tst - gn_timestamp)

                    if ( delta_time_ms <= 5 ):
                        
                        self.stats.total_cam_frames_match_gps_data += 1

                        # Check continuity in gps data in frames, and not the first sample
                        if gprmc_sentences > 1 and current_gps_file_pos > 0 :
                            self.log.warning( "Continuity problem in GPS refrence data found , gprmc_sentences: %d :current_gps_file_pos %d" % ( gprmc_sentences, current_gps_file_pos) )
                            self.stat.latency_error_data += 1

                        current_gps_file_pos = i # Set current file position

                        # get next sentence in refrence gps data
                        try:
                            next_gps_sen = gps_data[i+1]
                        except IndexError:
                            next_gps_sen = None

                        if not(next_gps_sen is None) and next_gps_sen.sen_type == 'GPGGA':

                            try:
                                #Get the gpgga
                                gps_sen_gpgga = next_gps_sen
                                self.convert_nmea_to_dec( gps_sen_gpgga )
                                gps_point = Point( gps_sen_gpgga.latitude, gps_sen_gpgga.longitude, gps_sen_gpgga.antenna_altitude)
                            except Exception as e:
                               gps_point = Point( gps_sen_gpgga.latitude, gps_sen_gpgga.longitude, 0)
                        
                            cam_gps_points_distance = dist_calc(cam_gnss, gps_point).meters
                            if ( cam_gps_points_distance < 3 ): # Distance between points shuold be no more then 3 Meters
                                self.stats.total_frames_passed_lat_lon += 1
                            else:
                                self.stats.total_frames_failed_lat_lon += 1
                        else:
                            self.log.error( "Unexcpected information in refrence GPS data at line %d" % i )
                            self.stats.gps_reference_unexpected_sen +=1

                        # Check arrivel jitter Check verified gps location of the current CAM frame is found and use tst to calc jitter in data
                        try:
                            delta_time_arrive = abs( (gps_time - frame.sniff_time).total_seconds() )
                            if delta_time_arrive > 5.0:
                                self.stats.cam_jitter_error += 1 
                        except Exception:
                            pass

                        # Go to next frame
                        break


    def print_results(self):

        # Handle totol frames handles
        self.add_limit( "Total frames procces" , self.stats.total_frames , self.stats.total_frames, None , 'EQ')
        # print counter of 
        for key, value in self.stats.layers_cntr.iteritems():
            self.add_limit( "Frame Layer %s, total packets" % key.upper() , 0, value, None , 'GE')

        # Check generation time of Geo layer and Cam layer not exceeding 100
        self.add_limit( "CAM-GN generation time (>100mSec)" , 0 , self.stats.time_diff_gn_cam_fail, None , 'EQ')

        # Check location of Geo layer and CAM layer, take into considiration time diff and speed
        self.add_limit( "CAM-GN gnss pos (> 1.5m)" , 0 , self.stats.gnss_cam_gn_mismatch, None , 'EQ')
        
        # Total CAM frames found in GPS refrence data 
        self.add_limit( "Total frames match CAM to GPS ref" , self.stats.layers_cntr['cam'] , self.stats.total_cam_frames_match_gps_data, None , 'EQ')

        # Total GPS refrence data of GPRMC failed to parse
        if ( self.stats.total_frames_misparsed > 0 ):
            self.add_limit( "Total GPS ref misparsed" , 0 , self.stats.total_frames_misparsed, None , 'EQ')

        # Verify continuity in CAM - GPS ref data from first point
        self.add_limit( "CAM continuity data errors" , 0 , self.stats.latency_error_data, None , 'EQ')


        # Total CAM frames lat lon testing passed
        self.add_limit( "CAM position info correction ok" , self.stats.layers_cntr['cam'] , self.stats.total_frames_passed_lat_lon, None , 'EQ')
        # Total CAM frames lat lon testing failed
        self.add_limit( "CAM position info correction failed" , 0 , self.stats.total_frames_failed_lat_lon, None , 'EQ')

        # Total CAM frames failed to be received up to 5 sec from generation time
        if ( self.stats.cam_jitter_error > 0 ):
            self.add_limit( "CAM position info correction failed" , 0 , self.stats.cam_jitter_error, None , 'EQ')

        if ( self.stats.gps_reference_unexpected_sen > 0 ):
            self.add_limit( "GPS reference unexpected sentences" , 0 , self.stats.gps_reference_unexpected_sen, None , 'EQ')


class Statistics(object):

    def __init__(self):
        self.total_frames = 0
        self.total_cam_frames = 0

        self.layers_cntr = {'unkown':0, 'llc':0, 'gn':0, 'btp':0, 'cam':0, 'denm':0}
        
        self.time_diff_gn_cam_fail = 0

        self.latency_error_data = 0
        self.gps_reference_unexpected_sen = 0
        self.total_frames_found = 0
        self.total_frames_passed_lat_lon = 0
        self.total_frames_passed_alt = 0
        self.total_frames_failed_lat_lon = 0
        self.total_frames_failed_alt = 0
        self.gnss_cam_gn_mismatch = 0
        self.cam_jitter_error = 0
        self.total_cam_frames_match_gps_data = 0
        self.total_frames_not_found = 0
        self.total_frames_misparsed = 0
        self.total_frames_wo_altitude = 0
        self.total_frames_with_altitude = 0
        self.total_frames_hdop_fail = 0
        self.count_heading_high_speed = 0
        self.fail_heading_high_speed = 0
        self.pass_heading_high_speed = 0




