"""
@file navigation.py
@brief Handle unit Navigation API manipulation
@author    	Shai Shochat
@version	1.0
@date		18/01/2013
"""


import os, time, sys
import thread, threading
import logging
from uuts import interface
from uuts import common
from lib import globals
from lib import utilities


# Import NMEA parsers
from pynmea.streamer import NMEAStream
from pynmea.nmea import NMEASentence


log = logging.getLogger(__name__)


class NavigationRecorder(object):
    """
    @class Navigation
    @brief handle NAV API data retreive
    @author Shai Shochat
    @version 0.1
    @date	07/05/2013
    """
	
    def __init__(self, active_if, timeout = common.DEFAULT_TIMEOUT):
        """ Initilize interface for unit connection """
        self.if_reader = interface.QaCliInterface()
        self._connect( active_if.server_addr, active_if.port, timeout) 

    def __del__( self ):
        self.terminate()

    def interface( self ):
        """ Get interface connection """
        return self.if_reader
    
    def _connect(self, server, port = common.DEFAULT_PORT , timeout = common.DEFAULT_TIMEOUT):
        """ Connect to unit via interface in new connection
        @param[in] server unit address as telnet ip or serial port (TBD)
        @param[in] port port for telnet connection
        @param[in] timeout timeout for telnet connection
        """
        # open channel for reader
        self.if_reader.connect( server, port, timeout )
        self.if_reader.login()
    
    def terminate(self):
        self.reader = None
        self.output.close()
        try:
            self.if_reader.send_command("exit", False)
            self.if_reader.disconnect()
            self.if_reader.close()
        except Exception:
            pass

        self.if_reader = None
        del self.if_reader


    def set_output( self, type, destination):
        """ Sets output direction """
        self.type = type
        if type == 'file':
            self.output = open(destination,'w')
        elif type == "handler":
            self.output = destination
        elif type == 'stdout':
            self.output = sys.stdout
        else:
            raise globals.Error("Type is not known")

    def nav_data_handler(self, data):
        """ NAV API data handler for @link NavReader"""
        # Add "$ATLK," to each sentence for using with pynema classes
        #line = "$ATLK," + utilities.timestamp() + "," + data 
        line = "$ATLK," + data + '\n'
        if self.type == 'handler':
             self.output( line )
        else:
            try:
                self.output.write( line )
            except Exception as e:
                log.error( e )



    def _reader(self):
        """ Start main NAV data retreive thread """
        self.reader = NavReader( self.if_reader.interface(), self.nav_data_handler )
        try:
            self.reader.start()
            while not self.reader.isAlive():
                common.usleep(1000)
        except:
            raise Error("Faild to active the gps thread")
    
    def init( self, type = globals.LOCAL, server_addr = None ):
        """ Initilize unit CLI Nav """
        """ Open Session, refer V2X SDK/API """
        cmd = "nav init"
        cmd += (" -type %s"  % 'local' if type == globals.LOCAL else 'remote')
        cmd += (" -server_addr %s"  % server_addr) if ( (not server_addr is None) and (type == globals.LOCAL) ) else ""
        self.if_reader.send_command(cmd)

    def start(self):
        self.if_reader.send_command("nav start")
        log.info("Starting NAV reader thread")
        self._reader()


    def stop(self):
        """ Stop main GPS data retreive thread """
        self.reader.shutdown()
        while not self.reader.isAlive():
            common.usleep(1000)
        self.if_reader.send_command("nav stop" , False)


class NavReader(threading.Thread):
    """
    @class NavReader
    @brief Nav api reader over V2X interface
    @author Shai Shochat
    @version 1.0
    @date	07/05/2013
    """

    def __init__(self, cli_interface, handler = None):
        """ Initilze class with interface and handler callback """
        threading.Thread.__init__(self)
        self._if = cli_interface
        self._finished = threading.Event()
        self.handler = handler

    def __del__( self ):
        self.handler = None
        pass
        # self._if = None

    def run(self):
        """ Thread start point """
        self.read_nav_data()

    def shutdown(self):
        """Stop this thread"""
        self._finished.set()

    def read_nav_data(self):	
        """ Main thread loop function retreive data from target """
        start_time = time.time()

        while not self._finished.isSet():
            str = ''
            try:
                str = self._if.read_until('\r\n')
            except:
                pass

            str = str.replace('\r\n', '')

            if str == '':
                if (time.time() - start_time) > 10.0:
                    log.info( "NOTE : no data arrived for 10 sec")
                    start_time = time.time()
                    continue
                else:
                    continue

            # data arrived, start new clock       
            start_time = time.time()
            #print "data arrived : %s" % str
            if not self.handler is None:
                # log.debug("Nav data : %s" % (str) )
                self.handler(str)
            # Sleep and release resources for 1 mSec
            common.usleep(1000)

class NavigationDataAnalyzer(NMEAStream):


    def __init__(self, stream_obj):
         super(NavigationDataAnalyzer, self).__init__(stream_obj)

    def _get_type(self, sentence):
        """ Get the NMEA type and return the appropriate object. Returns
            None if no such object was found.

            TODO: raise error instead of None. Failing silently is a Bad Thing.
            We can always catch the error later if the user wishes to supress
            errors.
        """
        sen_type = sentence.split(',')[0].lstrip('$')
        #sen_mod = __import__('pynmea.nmea', fromlist=[sen_type])
        sen_mod = sys.modules['uuts.craton.cli.navigation']
        sen_obj = getattr(sen_mod, sen_type, None)
        return sen_obj



class ATLK(NMEASentence):
    """ EVK CLI Data parser """
    def __init__(self):

        parse_map = (
            # fix->time_utc_s , fix->position_latitude_deg, fix->position_longitude_deg, fix->position_altitude_m, 
            ("nav_time", "nav_time"), 
            ("position_latitude_deg", "position_latitude_deg"), 
            ("position_longitude_deg", "position_longitude_deg"), 
            ("position_altitude_m", "position_altitude_m"), 
            # fix->movement_horizontal_direction_deg, fix->movement_horizontal_speed_mps, fix->movement_vertical_speed_mps, fix->time_std_s, 
            ("movement_horizontal_direction_deg", "movement_horizontal_direction_deg"), 
            ("movement_horizontal_speed_mps", "movement_horizontal_speed_mps"), 
            ("movement_vertical_speed_mps", "movement_vertical_speed_mps"), 
            ("error_time_s", "error_time_s"), 
            
            # fix->position_horizontal_std_major_axis_direction_deg, fix->position_horizontal_std_semi_major_axis_length_m, fix->position_horizontal_std_semi_minor_axis_length_m,
            ("error_position_horizontal_major_axis_direction_deg", "error_position_horizontal_major_axis_direction_deg"), 
            ("error_position_horizontal_semi_major_axis_length_m", "error_position_horizontal_semi_major_axis_length_m"), 
            ("error_position_horizontal_semi_minor_axis_length_m", "error_position_horizontal_semi_minor_axis_length_m"), 
            
            # fix->position_altitude_std_m , fix->movement_horizontal_direction_std_deg, fix->movement_horizontal_speed_std_mps, fix->movement_vertical_speed_std_mps )
            ("error_position_altitude_m", "error_position_altitude_m"), 
            ("error_movement_horizontal_direction_deg", "error_movement_horizontal_direction_deg"), 
            ("error_movement_horizontal_speed_mps", "error_movement_horizontal_speed_mps"), 
            ("error_movement_vertical_speed_mps", "error_movement_vertical_speed_mps"), 
            
            )
 
        super(ATLK, self).__init__(parse_map)

        # "1,1,1,0,235949.100,3216.3365,3452.3480, 20.0,
  
#class GPGGA(NMEASentence):
#    def __init__(self):
#        parse_map = (
#            ('log_timestamp', 'log_timestamp'),
#            ('Timestamp', 'timestamp'),
#            ('Latitude', 'latitude'),
#            ('Latitude Direction', 'lat_direction'),
#            ('Longitude', 'longitude'),
#            ('Longitude Direction', 'lon_direction'),
#            ('GPS Quality Indicator', 'gps_qual'),
#            ('Number of Satellites in use', 'num_sats'),
#            ('Horizontal Dilution of Precision', 'horizontal_dil'),
#            ('Antenna Alt above sea level (mean)', 'antenna_altitude'),
#            ('Units of altitude (meters)', 'altitude_units'),
#            ('Geoidal Separation', 'geo_sep'),
#            ('Units of Geoidal Separation (meters)', 'geo_sep_units'),
#            ('Age of Differential GPS Data (secs)', 'age_gps_data'),
#            ('Differential Reference Station ID', 'ref_station_id'))
#            #('Checksum', 'checksum'))

#        super(GPGGA, self).__init__(parse_map)

#class GPRMC(NMEASentence):
#    """ Recommended Minimum Specific GPS/TRANSIT Data
#    """
#    def __init__(self):
#        parse_map = (("log_timestamp", "log_timestamp"),
#                     ("Timestamp", "timestamp"),
#                     ("Data Validity", "data_validity"),
#                     ("Latitude", "lat"),
#                     ("Latitude Direction", "lat_dir"),
#                     ("Longitude", "lon"),
#                     ("Longitude Direction", "lon_dir"),
#                     ("Speed Over Ground", "spd_over_grnd"),
#                     ("True Course", "true_course"),
#                     ("Datestamp", "datestamp"),
#                     ("Magnetic Variation", "mag_variation"),
#                     ("Magnetic Variation Direction", "mag_var_dir"))
#                     #("Checksum", "checksum"))
#        super(GPRMC, self).__init__(parse_map)


#class GPGSV(NMEASentence):
#    def __init__(self):
#        parse_map = (
#            ('log_timestamp', 'log_timestamp'),
#            ('Number of messages of type in cycle', 'num_messages'),
#            ('Message Number', 'msg_num'),
#            ('Total number of SVs in view', 'num_sv_in_view'),
#            ('SV PRN number 1', 'sv_prn_num_1'),
#            ('Elevation in degrees 1', 'elevation_deg_1'), # 90 max
#            ('Azimuth, deg from true north 1', 'azimuth_1'), # 000 to 159
#            ('SNR 1', 'snr_1'), # 00-99 dB
#            ('SV PRN number 2', 'sv_prn_num_2'),
#            ('Elevation in degrees 2', 'elevation_deg_2'), # 90 max
#            ('Azimuth, deg from true north 2', 'azimuth_2'), # 000 to 159
#            ('SNR 2', 'snr_2'), # 00-99 dB
#            ('SV PRN number 3', 'sv_prn_num_3'),
#            ('Elevation in degrees 3', 'elevation_deg_3'), # 90 max
#            ('Azimuth, deg from true north 3', 'azimuth_3'), # 000 to 159
#            ('SNR 3', 'snr_3'), # 00-99 dB
#            ('SV PRN number 4', 'sv_prn_num_4'),
#            ('Elevation in degrees 4', 'elevation_deg_4'), # 90 max
#            ('Azimuth, deg from true north 4', 'azimuth_4'), # 000 to 159
#            ('SNR 4', 'snr_4'))  # 00-99 dB
#            #('Checksum', 'checksum'))

#        super(GPGSV, self).__init__(parse_map)
