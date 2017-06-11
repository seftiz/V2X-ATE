"Common constants and functionality for SDK tests"

import unittest
import sys
from lib import utilities
from datetime import datetime, timedelta
import logging
import time
from tests import dsrc_definitions
from lib import globals


LEAP_SECONDS_TAI_START = 34


GPS_LATITUDE_UNAVAILABLE = 900000001 
GPS_LONGITUDE_UNAVAILABLE = 1800000001 


#SNIFFER_DRIVE = "\\\\ate-lab\\capture\\"
#SNIFFER_DRIVE = "Z:\pcapLogs\link"
SNIFFER_DRIVE = 'C:\\temp\\pcapLogs\\'
#DATA_FILES = "Z:\pcapLogs\link\\tx_data\\"
DATA_FILES = r"C:\\temp\\tx_file\\"
rc = utilities.Enum(['EXIT_OK', 'EXIT_ERROR', 'EXIT_BAD_PARAMETER'])
rs = utilities.Enum(['LOCAL', 'REMOTE'])
actions = utilities.Enum(['START', 'STOP'])



def verify_in_range( value, expected, error_in_prec ):
        high_limit = expected + ( expected * (error_in_prec/100.0) )
        low_limit = expected + ( expected * (error_in_prec/100.0) ) 

        if low_limit <= value <= high_limit:
            return True
        else:
            return False


class SystemTestCase(unittest.TestCase):

    def run(self, result=None):
        self.result = result
        self._num_expectations = 0
        self.limit_count = 0
        self.limits = []
        self.test_status = None
        self.report_header = ""
        super(SystemTestCase, self).run(result)
        
    def results(self):
        return self._result

    def check_limit( self, low_limit, value, high_limit, comparison ):

        limit_status = False
        if type(low_limit) is str:
            limit_status = (low_limit == value)
        elif (type(low_limit) is int) or (type(low_limit) is long) or (type(low_limit) is float):
            try:
                comp = comparison.upper()
                if comp == "EQ":
                    limit_status = ( value == low_limit )
                elif comp == "NE":
                    limit_status = ( value != low_limit )
                elif comp == "GT":
                    limit_status = ( value > low_limit )
                elif comp == "LT":
                    limit_status = ( value < high_limit )
                elif comp == "GE":
                    limit_status = (  value >= low_limit )
                elif comp == "LE":
                    limit_status = ( value <= low_limit )
                elif comp == "GTLT":
                    limit_status = ( low_limit < value < high_limit )
                elif comp == "GELE":
                    limit_status = ( low_limit <= value <= high_limit )
                elif comp == "GELT":
                    limit_status = ( low_limit <= value < high_limit )
                elif comp == "GTLE":
                    limit_status = ( low_limit < value <= high_limit )
                elif comp == "LTGT":
                    limit_status = ( low_limit > value > high_limit )
                elif comp == "LEGE":
                    limit_status = ( low_limit >= value >= high_limit )
                elif comp == "LEGT":
                    limit_status = ( low_limit >= value > high_limit )
                elif comp == "LTGE":
                    limit_status = ( low_limit > value >= high_limit )
                elif comp == "NIR":
                    limit_status = value not in range ( low_limit, high_limit )
            except:
                return False
                   
        return limit_status

    def add_limit( self, limit_name, low_limit, value, high_limit, comparison, limit_desc = '' ):
        test_name = self._testMethodName
        limit_status = self.check_limit ( low_limit, value, high_limit, comparison )
        if limit_status == True: 
            pass
            #self.result.success_count += 1
            #self.result.addSuccess( ('ff','f') )
        elif limit_status == None or limit_status == False:
            pass
            #self.result.failure_count += 1
           

        self.limits.append( (test_name, limit_name, low_limit, value, high_limit, comparison , limit_status) )
        self.limit_count += 1

        # Configure test result
        if self.test_status == None:
            self.test_status = limit_status
        else:
            self.test_status = self.test_status and limit_status

        return limit_status

    def _fail(self, failure):
        try:
            raise failure
        except failure.__class__:
            self.result.addFailure(self, sys.exc_info())

    def expect_true(self, a, msg):
        if not a:
            self._fail(self.failureException(msg))
        self._num_expectations += 1

    def expect_equal(self, a, b, msg=''):
        if a != b:
            msg = '({}) Expected} to equal {}. '.format(self._num_expectations, a, b) + msg
            #org_limit_name = self._testMethodName
            #self._testMethodName = limit_name
            self._fail(self.failureException(msg))
            # self._testMethodName = org_limit_name
        self._num_expectations += 1
    
        # make override
    def doCleanups(self):
        #for limit in self.limits:
        #    row = "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>" % limit
        #    print row
        dd = self
        if self.test_status == True:
            self.result.addSuccess(self)
        else:
            self.result.addFailure(self, sys.exc_info())
        
        super(SystemTestCase, self).doCleanups()


class ParametrizedTestCase(SystemTestCase):
    """ TestCase classes that want to be parametrized should
        inherit from this class.
    """
    def __init__(self, methodName='runTest', param=None):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.param = param

    @staticmethod
    def parametrize(testcase_klass, param=None):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_klass)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_klass(name, param=param))
        return suite



class tParam(object):

    def __init__(self, tx, rx, **kwargs):
        self.tx = tx
        self.rx = rx
        for key, value in kwargs.items():
            setattr(self, key, value)




class V2X_SDKBaseTest(ParametrizedTestCase):
    
    def __init__(self, methodName = 'runTest', param = None):
        self.log = logging.getLogger(__name__) 
        self.can = None
        self.log_cli_active = True
        return super(V2X_SDKBaseTest, self).__init__(methodName, param)

    def setUp(self):
        self.__clock_start = time.clock()
        print >> self.result._original_stdout, "test, {} starting at {}".format( self._testMethodName, time.strftime("%H:%M:%S") )
        self.log.debug( "test, {} starting at {}".format( self._testMethodName, time.strftime("%H:%M:%S") ) )

    def tearDown(self):
        # Update test description
        if not self._test_desc is '':
            self._testMethodDoc = self._test_desc
        
        self._testMethodName  = self._testMethodName + '@' + self.target_cpu + '<BR>'

        print >> self.result._original_stdout, "test, {} completed at {}, duration {}".format( self._testMethodName, time.strftime("%H:%M:%S"), time.strftime("%H:%M:%S", time.gmtime( time.clock() - self.__clock_start)) )
        self.log.debug( "test, {} completed at {}, duration {}".format( self._testMethodName, time.strftime("%H:%M:%S"), time.strftime("%H:%M:%S", time.gmtime( time.clock() - self.__clock_start)) ) ) 

    def cap(self, s, l):
        return s if len(s)<=l else s[0:l-3]+ '...'

    def print_test_parameters(self):
        if len(self.param):
            print "Test parameters :\n"
            for i, t_param in enumerate(self.param):
                print "Param {} : {}".format( i, ''.join( "{} = {}".format( t_param, self.cap( str(self.param[t_param]),10) ) ) )

    def check_is_wlan_ack_frame( self, packet ):
        try:
            fc_type = int(packet['wlan.fc.type'],0)
            fc_subtype = int(packet['wlan.fc.subtype'],0)

            if ( fc_type == 1 and fc_subtype == 13 ):
                return True
        except Exception:
            pass

        return False

    def get_frame_reference_structure( self, packet):
        """ This function returns the reference object to compare the frame """
        frame_struct = dict()

         # Check frame type
        try:
           fc_type = int(packet['wlan.fc.type'],0)
           fc_subtype = int(packet['wlan.fc.subtype'],0)
        except Exception as e:
            self.log.error("ERROR : WLAN not found in packet, {}".format(e) )
        else:
            if fc_type == 2:
                frame_struct['wlan'] = dsrc_definitions.wlanStructureFixed
            elif fc_type == 0xd or fc_type == 0:
                frame_struct['wlan'] = dsrc_definitions.wlanStructureFixedVsa

        try:
            llc_exists = packet['llc.dsap']
        except Exception as e:
            self.log.error("ERROR : WLAN not found in packet, {}".format(e) )
        
        if not llc_exists is None:
            frame_struct['llc'] = dsrc_definitions.logicalLinkControl
        
        if fc_type == 0 and fc_subtype == 13:
            try:
                wlan_mgt_exists = packet['wlan_mgt.fixed.vendor_type']
            except Exception as e:
                self.log.error("ERROR : WLAN not found in packet, {}".format(e) )
        
            if not wlan_mgt_exists is None:
                frame_struct['wlan_mgt'] = dsrc_definitions.wlanManagementStructureFixed
 
        return frame_struct

    def verify_frame_structure(self, packet, frame_definition, field_name_prefix ):

        for field, value in frame_definition.items():
            try:
                field_name = "{}.{}".format(field_name_prefix, field)
            except Exception as e:
                pass
            else:
                if type(value) == int:
                    try:
                        field_ok = ( int(packet[field_name],0) == value )
                    except Exception as e:
                        field_ok = False
                elif type(value) == str:
                    if '!ref:' in value:
                        field_ok =  ( packet[field_name] == value )
                    else:
                        field_ok =  ( packet[field_name] == value )
                else:
                    uut_idx = 0
                    rf_id =  int(packet["frame.interface_id"],0) + 1
                    try:
                        field_ok =  ( packet[field_name] ==  eval(field) )
                    except Exception as e:
                        pass

                if not field_ok:
                    # Check if field exists
                    try: 
                        a = getattr(self.stats.frame_fields, field_name.replace('.', '_'))
                    except Exception:
                        setattr( self.stats.frame_fields ,  field_name.replace('.', '_'), 0)

                    setattr ( self.stats.frame_fields, field_name.replace('.', '_') , ( getattr(self.stats.frame_fields, field_name.replace('.', '_') ) + 1 ) )

    def get_test_parameters( self ):
        self._test_desc = self.param.get('test_desc', '')
        self.debug = self.param.get('debug', False)
        self.target_cpu = self.param.get('target_cpu', 'arm') 
        self._cpu_load_info = self.param.get('cpu_load_info', {} )
        self._profiling_info = self.param.get('prof_info', {} )
        
        # GPS configuration 
        self._gps_scenario = self.param.get('gps_scenario', "" )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )
        self._gps_lock_timeout_sec = self.param.get('gps_lock_timeout_sec', 600 )
        
        self.print_test_parameters()

    def load_data_file(self, file_name , type = 'gps'):
        from pynmea.streamer import NMEAStream
        from uuts.craton.cli import navigation
        # Start analyze recording file Vs. gps simulator file
        with open(file_name, 'r') as data_file_fd:
            if type == 'gps':
                nmea_stream = NMEAStream(stream_obj = data_file_fd)
            elif type == 'navfix':
                nmea_stream = navigation.NavigationDataAnalyzer( stream_obj = data_file_fd)
            else:
                raise globals.Error("GPS information type is mismatch")

            next_data = nmea_stream.get_objects()
            nmea_objects = []
            while next_data:
                nmea_objects += next_data
                next_data = nmea_stream.get_objects()
        
        data_file_fd.close()
        return nmea_objects

    def convert_nmea_to_dec(self , gps_sentence):
        import decimal

        if gps_sentence.sen_type == 'GPRMC':
            lat = decimal.Decimal(gps_sentence.lat)
            long = decimal.Decimal(gps_sentence.lon)
            lat = ((lat-(lat%100))/100)+(lat%100)/60
            long = ((long-(long%100))/100)+(long%100)/60
            if gps_sentence.lon_dir == 'W':
                long*=-1;
            if gps_sentence.lat_dir == 'S':
                lat*=-1

            gps_sentence.lon = '%f' % ( long )
            gps_sentence.lat = '%f' % ( lat )

        else:
            lat = decimal.Decimal(gps_sentence.latitude)
            long = decimal.Decimal(gps_sentence.longitude)
            lat = ((lat-(lat%100))/100)+(lat%100)/60
            long = ((long-(long%100))/100)+(long%100)/60
            if gps_sentence.lon_direction == 'W':
                long*=-1;
            if gps_sentence.lat_direction == 'S':
                lat*=-1

            gps_sentence.longitude = '%f' % ( long )
            gps_sentence.latitude = '%f' % ( lat )

    def gps_init( self, scenario, power, gps_require = True ):
                
        if bool(len(scenario)):
            self.log.info("Getting GPS simulator in config")
            if globals.setup.instruments.gps_simulator is None:
                if gps_require:
                    raise globals.Error("gps simulator is not initilize, please check your configuration")
            else:
                # Get pointer to object
                self.gps_sim = globals.setup.instruments.gps_simulator

            # set general tx power
            self.gps_sim.tx_power( self._gps_tx_power )  
            #load scenario
            self.gps_sim.load( self._gps_scenario )

        else:
            self.gps_sim = None

    def wait_for_gps_lock( self, uut, lock_time_out):
 
        self.log.info("Start loop waiting GPS Lock, max time {}".format(lock_time_out) )
        start_time = time.time()
        while ( (time.time() - start_time) < lock_time_out ):
            fix_status = uut.managment.get_nav_fix_available()
            if (fix_status == 1):
                self.gps_lock = True 
                self.log.info("GPS locked O.K.")
                return True
            time.sleep(0.2)

        return False
        
    def is_gps_active(self):
        if (self.gps_sim is None):
            return False
        return True

    def start_log_qa_cli(self, cli):
        
        t = threading.Thread( target = self.__read_cli_buffer_to_log, args = (cli,self.log_cli_active) )
        t.start()
        return t

    def __read_cli_buffer_to_log(self, qa_cli, loop):
        
        log = logging.getLogger(__name__)
        while loop:
            try:
                data = qa_cli.interface().read_until('\r\n', timeout = 1)
                log.info( "{}", data )
            except Exception as e:
                pass

    




def cpu_load(self, uut_idx, cpu_load_level = 50, timeout = -1):
    try:
        cpu_uut = globals.setup.units.unit(uut_idx)
    except KeyError as e:
        raise globals.Error("uut index and interface input is missing or currpted, usage : _uut_id_tx=(0,1)")

    cli_name = 'cpu_load'
    cpu_uut.create_qa_cli(cli_name)
    # Open general session
    cpu_uut.qa_cli(cli_name).cpu_load(cpu_load_level, timeout)


def profiling_info():
    pass

    


def parse_1609_2_generation_time( timestamp_usec ):
    
    pckt_time_stamp = int(timestamp_usec,16) 
    tai_ts = timedelta(microseconds = pckt_time_stamp)

    tai_start = datetime(2004,1,1,0,0, 34)
    ts = tai_start + tai_ts
    return ts 