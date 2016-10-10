"""
@file v2x_cli.py
@brief V2X CLI API for python
@author    	Shai Shochat
@version	1.0
@date		18/01/2013
"""
import logging
from uuts import interface
from uuts import common
from uuts.craton.cli import gps
from uuts.craton.cli import navigation
import os
from lib import globals
from lib import utilities

log = logging.getLogger(__name__)


class QaCli(object):
    """
    @class QaCli
    @brief V2X CLI Implementation for python.
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """

    def __init__(self, version = ""):
        self._if = interface.QaCliInterface()
        self.timeout = common.DEFAULT_TIMEOUT # set default timeout 
        self._buffer = "" # history buffer for telnet
        self.port = common.DEFAULT_PORT
        self.server = ""
        self.cli_addr = ""
        self.version = version
        self.is_connected = False
        self.uut = None
        

    def __del__(self):
        self.gps = None
        
    def set_interface(self, If = common.DEFUALT_INTERFACE):
        """ Set interface connection for the V2X CLI
        @param[in] if set interface name, telnet or serial
        """
        # self._if = interface.QaCliInterface()
        pass
    
    def interface(self):
        """ Get interface connection for the V2X CLI
        @retval return interface object 
        """
        return self._if.interface()

    def connect(self, server, port = common.DEFAULT_PORT, timeout = common.DEFAULT_TIMEOUT):
        """ Connect to unit via interface in new connection
        @param[in] server unit address as telnet ip or serial port (TBD)
        @param[in] port port for telnet connection
        @param[in] timeout timeout for telnet connection
        """
        self.port = port
        self.server = server
        self.timeout = timeout
        # Store the current main cli session address for external host
        self.cli_session = 0 
        log.info('Connect to CLI Server IP %s Port %s', server , port)
        self._if.connect( server, port, timeout )
        self._if.login()
        self.is_connected = True

        # clean any buffer
        self._if.timeout = 1
        data = self._if.read_until_prompt()
        self._if.send_command('\r\n')
        data = self._if.read_until_prompt()
        self._if.timeout = 3

    def disconnect(self):
        """ Disconnect from V2X CLI """
        self._if.disconnect()
        self.is_connected = False

    def session_open(self, type = globals.LOCAL, server_addr = None):
        """ Open Session, refer V2X SDK/API """
        cmd = "session open"
        if len(self.uut.external_host):
            if ( len(self.uut.external_host_session) == 0 ):
                cmd += (" -type %s"  % 'remote')
                cmd += (" -server_addr %s"  % self.uut.ip)
                self._if.send_command( cmd.encode('ascii','ignore'), True )

                # Read current session for more clis due to limitation of VTP
                self.uut.external_host_session = self.session_get_address()
            else:
                self.session_set_address ( self.uut.external_host_session )

        else:
            self._if.send_command( cmd.encode('ascii','ignore') )
                
    def session_get_address( self ):
        rc = self._if.send_command("session get", True)
        # Make sure data echo exists
        if not 'session get' in rc:
            rc = self._if.read_until_prompt()

        if ( int(rc.split('\r\n')[1].split(':')[1].strip(),16) <= 0 ):
            raise Exception( "Session address is wrong")

        return ('0x' + rc.split('\r\n')[1].split(':')[1].strip())

    def session_set_address ( self, address ):
        """ Set already active session to a new connection """
        self._if.send_command("session set -addr {}".format( address ) )

    def get_user_context(self):
        # v2x >> uc get
        # Context : 50ad3a78
        cmd = 'uc get'
        rc = self._if.send_command(cmd, True)
        # Make sure data echo exists
        if not cmd in rc:
            rc = self._if.read_until_prompt()

        if ( int(rc.split('\r\n')[1].split(':')[1].strip(),16) <= 0 ):
            raise Exception( "Context address is wrong")

        return ('0x' + rc.split('\r\n')[1].split(':')[1].strip())

    def set_user_contesxt ( self, address ):
        """ Set already active context to a new connection """
        self._if.send_command("uc set -addr {}".format( address ) )

    def session_close(self):
        """ Close Session, refer V2X SDK/API """
        self._if.send_command("session close")

    def wsmp_open(self):
        """ open WSMP socket, refer V2X SDK/API """
        self._if.send_command("wsmp open") 

    def wsmp_close(self):
        """ close WSMP socket, refer V2X SDK/API """
        self._if.send_command("wsmp close")

    def wsmp_send_frames(self, frames = 1, rate_hz = 1):
        """ send WSM frame via WSMP socket, refer V2X SDK/API
        @param[in] num_frames Number of frames to send
        @param[in] rate Frmes rate
        """
        cmd = "wsmp tx -frames %d -rate-hz %d" % (frames, rate_hz)
        self._if.send_command(cmd)

    def nav_init( self, type, server_addr = None ):
        self.nav  = navigation.NavigationRecorder( self._if )
        self.nav.init( type, server_addr )
        
    def nav_start( self, output = None ):
        if not output == None:
            type, destination = output
            self.nav.set_output( type , destination )
        self.nav.start()

    def nav_stop( self ):
        self.nav.stop()
    
    def gps_start(self, nmea_data_file, gps_mode = 0, gps_handler_func = None ):
        """ Start Gps class and GpsReaderThread for reading gps data from unit
	        @param[in] gps_mode set handler mode\n
		        0 - simulator  No data retrive\n
		        1 - queue		Retrieve data from GPS
	        @param[in] gps_handler_func Callback for handling and manipulating data
        """

        # nmea_data_file = "c:\\temp\\nmea_data_1.txt"
        if not os.path.exists(nmea_data_file):
            Error('nmea data file %s is missing' % nmea_data_file )

        self.gps = Gps( nmea_data_file , gps_handler_func )
        self.gps.connect( self.ip, common.DEFAULT_PORT, common.DEFAULT_TIMEOUT )
        self.gps.start()

    def gps_stop( self ):
        self.gps.stop()

    def link_open(self, if_idx, frame_type, proto_id):
        
        cmd = "link open -if_idx %d -frame_type %s -proto_id 0x%x" % (if_idx, frame_type, proto_id)
        data = self._if.send_command(cmd)
        #data = self._if.read_until_prompt()
        
    def link_close(self):
        cmd = "link close"
        self._if.send_command(cmd)
 
    def link_tx(self, payload_len = None, tx_data = None, dest_addr = None, frames = 1, rate_hz = 1, user_priority = None, data_rate = None, power_dbm8 = None):

        cmd = "link tx"
        cmd += (" -frames %d"  % frames)
        cmd += (" -rate_hz %d"  % rate_hz)
        if tx_data == None and payload_len == None:
            payload_len = 50
        cmd += (" -payload_len %s"  % payload_len) if not payload_len is None else ""
        cmd += (" -tx_data %s"  % tx_data) if not tx_data is None else ""
 
        cmd += (" -dest_addr %s"  % dest_addr) if not dest_addr is None else ""
        cmd += (" -user_priority %d"  % user_priority) if not user_priority is None else ""
        cmd += (" -data_rate %d"  % data_rate) if not data_rate is None else ""
        cmd += (" -power_dbm8 %d"  % power_dbm8) if not power_dbm8 is None else ""
 
        self._if.send_command(cmd)

    def link_reset_counter(self):
        cmd = "link reset_cntrs"
        self._if.send_command(cmd)
        return self._if.read_until_prompt()
              
    def link_get_counters(self):
        cnts = dict()
        cmd = "link print_cntrs"
        data = self._if.send_command(cmd)
        while not cmd in data :
            data = self._if.read_until_prompt()
            if not len(data):
                return cnts

        data = data.split('\r\n')
        """
        TX : module 400, session 0
        RX : module 400, session 0
        """

        cnts['tx'] = list()
        cnts['rx'] = list()

        for line in data:
            if line.find('TX') >= 0:
                cnts['tx'].append( int(line.split(',')[0].split('=')[1].strip()))
                cnts['tx'].append( int(line.split(',')[1].split('=')[1].strip()))

            if line.find('RX') >= 0:
                cnts['rx'].append( int(line.split(',')[0].split('=')[1].strip()))
                cnts['rx'].append( int(line.split(',')[1].split('=')[1].strip()))

        return cnts

    def link_rx(self, frames, timeout = None, print_frame = None):
        cmd = "link rx -frames %s" % frames
        cmd += (" -print %d"  % print_frame) if not print_frame is None else ""
        cmd += (" -timeout_ms %d"  % timeout) if not timeout is None else ""

        self._if.send_command(cmd)

    def prof(self, reset = False):
        # Uses uut cli commmand line
        cmd = "prof"
        cmd += " reset" if reset is True else ""
        a = self._if.send_command(cmd)
        b = a.split('\r\n')
        data = {}
        for item in b:
            # Search only lines with % of cpu load
            if '%' in item:
                thread_name = item[9:34].strip() 
                cpu_data = [s for s in item[35:].split(' ') if len(s)]
                # k = { 'thread_id' : item[0:8], 'thread_name' : thread_name, 'cycles' : cpu_data[0], 'Load' : cpu_data[1] }
                k = { 'thread_id' : item[0:8], 'cycles' : cpu_data[0], 'Load' : cpu_data[1] }
                data[ thread_name ] = k

        return data

    def cpu_load(self, avg_load, timeout):
        # timeout = 0 cancel the timeout
        cmd = "set cpu-load -timeout %d -load %d" % ( timeout, avg_load )
        #  cpu-load -timeout_ms 60000 -num_iter 80000 -sleep_ticks 1
        self._if.send_command(cmd, False)

    def set_cli_thread_name(self, name ):
        cmd = "set context-name -name %s" % name
        #  cpu-load -timeout_ms 60000 -num_iter 80000 -sleep_ticks 1
        addr = self._if.send_command(cmd)
        # thread addr :0x%x
        for s in addr.split('\r\n'):
            if 'addr' in s:
                self.cli_addr  = s.split(':')[1]
                break

    def thread_kill( self, thread_addr ):
        cmd = "thread kill -addr %s" %  (thread_addr if '0x' in thread_addr else '0x' + thread_addr)
        addr = self._if.send_command(cmd)
        self.cli_addr = ''

 
  






class QaCliDebug(QaCli):
    """
    @class QaCli
    @brief V2X CLI Implementation for python.
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """

    def __init__(self, version = ""):
        #return super(QaCli, self).__init__(methodName, param)
        QaCli.__init__(self, "")
        

    def prof_reset(self):
        cmd = "prof reset"
        if ( self.is_connected == True):
            self._if.send_command(cmd)

    def prof_display(self):
        cmd = "prof display"
        if ( self.is_connected == True):
            data = self._if.send_command(cmd)
            return data 
        else:
            return ""
        #data = data.split('\r\n')
 





if __name__ == "__main__":
    
    import tempfile, time, os
    a = 1

    print "Creating CLI instance"
    cli = QaCli()
    print "Setting interface"
    cli.set_interface("telnet")
    print "Connecting to telnet server"
    cli.connect( "10.10.0.75" , 8000 )
    	
    # start nav session in evk
    cli.nav_init( 'local' )

    dir_name = tempfile.gettempdir()
    timestr = time.strftime("%Y%m%d-%H%M%S")
    nav_file_name = 'nav_data'
    gps_file_name = 'gps_rec'
    nav_file_recorder = os.path.join(dir_name, nav_file_name + "_" + timestr + "." + 'txt')
    gps_file = os.path.join(dir_name, gps_file_name + "_" + timestr + "." + 'txt')

    print "NAV File : %s" % nav_file_recorder

    cli.nav_start( ('file', nav_file_recorder) )

    while ( a == 1 ): time.sleep(0.5)

    cli.nav_stop()


    cli.disconnect()



	# """
	# import time

	# class gps_handler:
	
		# def __init__(self, interface, file_name ):
			# self._if = interface
			# try:
				# self._fhwd_nmea = open(file_name, 'r')
			# except IOError:
				# raise Error('ERROR : failed to open nmea data file')
		
		# def __del__(self):
			# close(self._fhwd_nmea)
			# pass
			
		# def gps_handler(self, data ):
			# msg = data.split(",")
			# if '$GPGGA' == msg[0]:
				# new_data = self._fhwd_nmea.readline()
				# print "HANDLER : %s\n" % data.replace("\n", "")
				
			
		
	
	# def my_gps_handler( data ):
		# print "HANDLER : %s\n" % data.replace("\n", "")
	
	
	# cli = QaCli()
	# cli.set_interface("telnet")
	# cli.connect( "10.10.0.165" , 8000 )
	
	# handler = gps_handler("c:/temp/kml_test_3.nmea")
	
	# cli.gps_start( 1, handler.gps_handler )
	
	# while 1:
		# common.usleep(50000)
		# pass
	# """	

