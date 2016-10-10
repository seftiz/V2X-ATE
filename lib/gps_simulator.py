


if __name__ == "__main__":
    import sys
    sys.path.append('c:/qa_reg/')


from lib.instruments import spectracom_gsg_6
#import . from .
from pynmea.streamer import NMEAStream
import time
import socket, logging
from lib import globals
from lib import ssh
from lib import interfaces
import threading
import re, os, sys


log = logging.getLogger(__name__)

class gpsBaseClass(object):

    def __init__(self):
        pass
    def __del__(self):
        pass
    def tx_power(self, value):
        pass
    def load_scenario(self, scenario_name):
        pass
    def get_current_scenario(self):
        pass
    def start_scenario(self, scenario_name):
        pass
    def start_record(self , file_path ):
        pass
    def stop_record( self ):
        pass
    def stop_scenario(self):
        pass
    def hold_scenario(self):
        pass
    def start_scenario(self):
        pass
    def lock( self, uut ):
        pass
    def terminate(self):
        pass


class gpsdServer( gpsBaseClass ):

    def __init__(self, ip , user = 'user', pwd = '123' ):
        self._if = ssh.SSHSession( ip, user, pwd )

    def tx_power(self, value):
        pass

    def get_current_scenario(self):
       return self.scenario_name
 
    def load_scenario(self, scenario_name):
        self.scenario_name = scenario_name
        
    def start_scenario( self ):
        cmd = 'gpsfake -blc{} -o "-G" {}'.format( 0.5, self.scenario_name )
        rc = self._if.exec_command(cmd)
        # Stop any current scenatio 

    def stop_scenario( self ):
        cmd = '\x003'
        rc = self._if.exec_command(cmd)

class GpsSimulator(object):

    def __init__(self, type, address):
        self.gps = SimulatorsTypes[type](address)
        self.ref_gps = ExternalGpsRecorder()
        self._record = False
        if self.gps == None:
            raise qa.globals.Error("GPS type %s is unknown",  SimulatorsTypes[type] )

    def __del__(self):
        self.gps = None
                
    def tx_power( self, value ):
        self.gps.tx_power = value

    def load(self, scenario_name):
        self.gps.load_scenario(scenario_name)

    def get_current_scenario(self):
        return self.gps.get_current_scenario()

    def start_scenario( self ):
       self.gps.start_scenario()
 
    def start_recording( self, recorder_file = None ):
        if not recorder_file is None:
            self._record = True
            self.gps.start_record( recorder_file )
        else:   
            raise globals.Error("Recorder file is missing")

    def stop_scenario( self ):
         self.gps.stop_scenario()

    def stop_recording( self ):
        if self._record:
            self.gps.stop_record()
            self._record = False
    
    def pause( self ):
        self.gps.hold_scenario()

    def resume( self ):
        return self.gps.start_scenario()

    def terminate( self ):
        return self.gps.terminate()

    
    # returns true if gps is locked otherwise false   
    def lock( self, uut ):
        start_time = time.time()
        while ( (time.time() - start_time) < 600):
            if (uut.managment.get_nav_fix_available() == 1):
                return True 
            time.sleep(0.2)
        return False     

class nmea_parser(object):
        
    def __init__(self):
        pass

    def __del__(self):
        pass


    def load_nmea_data(self):

        with open('example_data_file.txt', 'r') as data_file:
            streamer = NMEAStreamer(data_file)
            next_data = streamer.get_objects()
            data = []
            while next_data:
                data += next_data
                next_data = streamer(read)

class ExternalGpsRecorder(object):

    def __init__(self):
        import zmq
        self.read_data_flag = False

    def open_connection(self):
        #self.sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #self.sock.bind( ('', globals.UDP_SERVER_PORT) )

        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.SUB)
        self.sock.setsockopt(zmq.SUBSCRIBE, '')

        self.sock.connect('tcp://localhost:%d' % globals.UDP_SERVER_PORT )


    def start_recording( self, gps_file ):
        self._file_hwd = open( gps_file, 'w' )
        self.read_data_flag = True
        self.open_connection()	
        self._thread_hwd = threading.Thread(target = self.read_data_loop, args = ())
        self._thread_hwd.start()
        #thread.join()
 
    def stop_recording( self ):
        self.read_data_flag = False
        self._thread_hwd.join()
        self._file_hwd.close()

    def read_data_loop(self):
        
        self._last_msg = ''
        while self.read_data_flag:
            try:
                gps_feed = self.sock.recv()
            except:
                gps_feed = ''
                print "no data"

            if gps_feed == '' or gps_feed[0] != '$':
                continue

            #print "data arrived : %s" % str
            if not self._file_hwd is None:
                self._file_hwd.write( gps_feed.replace('\r\n','') + '\n' ) 

class LabSat3(gpsBaseClass):

    def __init__(self, ip_addr):
        self._ip = ip_addr
        info = { 'host':ip_addr, 'port':23, 'timeout_sec': 1 }
        self._if = interfaces.INTERFACES['TELNET'](info)
        self._if.open()
        self._prompt = 'LABSATV3 >'
        self.default_path = ''        # 'LabSat 3 Scenario Library\SatGen'
        self.scenario_name = None
        self.scenario_path = None


        status  = self._check_connection()

           

    def __del__(self):
        self.terminate()
    
    def _check_connection(self):
        self._if.write("\n", False)
        str = self.clean_ansi_escape( self._if.read_until( self._prompt, 2) )

        if self._prompt in str:
            return True
        if 'Connection is already in use by' in str:
            raise globals.Error("Unable to connect to LABSAT, connection is busy")

        raise globals.Error("Unable to connect to LABSAT, unknown reason")



    def terminate(self):
        try:
            self.change_directory('/')
            self._if.write("quit")
        except Exception as e:
            pass
        finally:
            self._if.close()


    def initilize(self):
        self.change_directory('\\')


    def clean_ansi_escape(self, str):
        ansi_escape = re.compile(r'\x1b[^m]*m')
        return ansi_escape.sub('', str)

    def verify_ack(self, timout_sec = 2):

        data = self.clean_ansi_escape( self._if.read_until( self._prompt, timout_sec ) )
        if 'OK' in data:
            return True
        elif 'ERR' in data:
            raise globals.Error("Error in Command" ) 
        else:
            raise globals.Error("No ack" )

    def get_nmea_data_thread(self):
        
        self._if.write("MON:NMEA:ON", False)
        try:
            self.verify_ack()
        except Exception as e:
            pass

        self._if.write("MON:NMEA:ON", False)

        while (self._mon_active):
            try:
                gps_feed = self._if.handle.read_until('\r\n', 0.1) # read_very_eager() # read_lazy()
            except Exception as e:
                continue

            if gps_feed == '' or gps_feed[0] != '$':
                continue

            if not self._fh is None:
                self._fh.write( gps_feed.replace('\r\n', '') + '\n' ) 


    def tx_power(self, value):

        # Support Labast range 
        if value > -83.0:
            value = -83.0
        elif value < -115.0:
            value = -115.0

        #self._if.write("ATTN:{}".format( value ) )
        #self.verify_ack()

    def load_scenario(self, scenario_name):

        self._current_scenario = scenario_name
        head, tail = os.path.split(scenario_name)
        self.scenario_name = tail
        self.scenario_path = head
        if head is '': # Goto default dir 
            self.change_directory( self.default_path )
        else:
            self.change_directory(head)

    def get_current_scenario(self):
        return self._current_scenario

    def start_scenario(self):
        if ( self.scenario_name is None):
            raise Exception("ERROR : scenario not loaded, please load scenario  first")

        self._if.write("PLAY:FILE:{}".format(self.scenario_name ) , False)
        self.verify_ack()

    def stop_scenario(self):
        self._if.write("PLAY:STOP")
        #self.verify_ack()

    def start_record(self , file_path ):
        self._fh = open( file_path, 'w' )
        self._mon_active = True
        self._rec_thread = threading.Thread(target = self.get_nmea_data_thread, args = ())
        self._rec_thread.start()

    def stop_record( self ):
        self._mon_active = False
        self._rec_thread.join( timeout = 10 )
        self._if.write("MON:NMEA:OFF")
        # self.verify_ack()
        self._fh.close()

    def _select_media_source( self, source = 'USB' ):

        self._if.write("MEDIA:?", False)
        str = self.clean_ansi_escape( self._if.read_until( self._prompt, 2) )
        if not ('MEDIA:{}'.format( source ) in str):
            raise IOError("External device not conncted to LABSAT")
        
        self._if.write("MEDIA:SELECT:{}".format(source), False)
        self.verify_ack()


    def change_directory( self, dir ):
        
        self._select_media_source()
        
        # Recursive call for chagne directory.
 
        if (dir == '\\' or dir == '/'):
            self._if.write('MEDIA:CHDIR:\\', False)
            self.verify_ack()
            return

        self._if.write('MEDIA:CHDIR:\\', False)
        self.verify_ack()
        time.sleep(1)

        path_list = dir.split(os.sep)
        for dir_name in path_list:
            self._if.write('MEDIA:CHDIR:{}'.format(dir_name), False)
            time.sleep(1)
            self.verify_ack()
            time.sleep(1)

    def get_file_list( self ):
        
        self._select_media_source()
        
        # Goto to home directory
        self._if.write('MEDIA:CHDIR:\\', False)
        self.verify_ack()

        self._if.write('MEDIA:LIST', False)
        str = self.clean_ansi_escape( self._if.read_until( self._prompt, 2) )
        dir_list = [file for file in str.split('\r\n') if ( (len(file) > 0) and not(self._prompt in file)) ]

    def hold_scenario(self):
        pass

    def lock( self, uut ):
        pass


SimulatorsTypes = {'internal': None, 'spectracom_gsg_6': spectracom_gsg_6.SPECTRACOM_GSG_6, 'gpsd' : gpsdServer, 'LabSat3' : LabSat3 }


if __name__ == "__main__":
    try:

        labsat = LabSat3('10.10.1.49')
        # file_list = labsat.get_file_list()

        labsat.change_directory('/')
        time.sleep(1)

        labsat.load_scenario('netter2eilat')

        labsat.start_scenario()

        time.sleep(5)

        labsat.start_record('c:\\temp\\gps_recoreding.txt')

        time.sleep(60)

        labsat.stop_record()

        time.sleep(1)

        labsat.stop_scenario()

    except Exception as e:
        raise e
    finally:
        labsat.terminate()

    labsat = None



    # labsat.load_scenario('some scenario')


