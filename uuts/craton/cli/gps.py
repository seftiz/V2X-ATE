"""
@file gps.py
@brief Handle unit GPS software simulator manipulation
@author    	Shai Shochat
@version	1.0
@date		18/01/2013
"""


import os, time, sys
import thread, threading
import logging
from uuts import interface
from uuts import common
import Queue
from lib import globals

log = logging.getLogger(__name__)

class TimerTaskThread(threading.Thread):
    """Thread that executes a task every N seconds"""
    
    def __init__(self):
        threading.Thread.__init__(self)
        self._finished = threading.Event()
        self._interval = 1.0
    
    def setInterval(self, interval):
        """Set the number of seconds we sleep between executing our task"""
        self._interval = interval
    
    def shutdown(self):
        """Stop this thread"""
        self._finished.set()
    
    def run(self):
        while 1:
			try:
				if self._finished.is_set(): return
				self.task()
				# sleep for interval or until shutdown
				self._finished.wait(self._interval)
			except (KeyboardInterrupt, SystemExit):
				return
	
	def task(self):
		"""The task done by this thread - override in subclasses"""
		pass	


class NmeaDataHandler(object):

    def __init__(self, out_queue, nmea_data_file , data_modifier_func = None):
        
        self.w_q = out_queue
        self.data_modifier_func = data_modifier_func
        self._pause = True
        self.nmea_log_line = None
        # define data queue
        self.nmea_q = Queue.Queue()
        # Load data
        self.load_data_file( nmea_data_file )

    def __del__(self):
        self.data_modifier_func = None
        self.nmea_q = None
        self.w_q = None

    def load_data_file(self, file_name):
        # set pos for cyclic reading 
        self.data_file = file_name

        try:
            file_hwd = open(self.data_file, 'r')
        except:
            file_hwd = None
            raise Error("Faild to open %s nmea log file" % self.data_file)

        file_hwd.seek(0, 0);
        for line in file_hwd:
            self.nmea_q.put(line)

        file_hwd.close()

    def get_last_nmea_data(self):
        return self.nmea_log_line

    def add_data_to_buffer(self, data_line):
        self.nmea_q.put(data_line)

    def pause(self):
        self._pause = True

    def resume(self):
        self._pause = False

    def gps_data_handler(self, data):
        """ GPS data handler for @link GpsReaderThread"""

        if data[0:6] != '$GPGGA':
             return

        self.nmea_log_line = data

        # Load same data in case of empty buffer cyclic
        if self.nmea_q.empty():
            self.load_data_file(self.data_file)

        # get data from data file
        if not self._pause and not self.nmea_log_line is None:
            self.nmea_log_line = self.nmea_q.get()
         

        # manipulation
        if self.data_modifier_func is None:
            processed_data = self._modify_nmea(self.nmea_log_line)
        else:
            processed_data = self.data_modifier_func(self.nmea_log_line)

        # update writer queue
        log.info("gps_data_handler :loading %s to W_Q :<-->: %s" % ( processed_data , time.strftime("%H:%M:%S") ) )
        self.w_q.put(processed_data)

    def _modify_nmea(self, data):
        # strip the header of GPS : and the Newline
        return data.rstrip('\r\n')

class GpsWriter(TimerTaskThread):
	"""
	@class GpsWriter
	@brief GPS position and paramter updater via timer
	@author Shai Shochat
	@version 0.1
	@date	28/01/2013
	"""
	
	def __init__(self, cli_interface, data_queue, event_timer = 0.1 ):
		""" Initilze class with interface """
		self._if = cli_interface
		self._event_timer = event_timer
		self.nmea_data = ""
		self.queue = data_queue
		TimerTaskThread.__init__(self)
		
	def __del__(self):
		self.queue = None
		
	def gps_data_writer(self):	

		if not self.queue.empty():
			self.nmea_data = self.queue.get()
		
		if self.nmea_data != '':
			log.info( "gps_data_writer : injecting %s :<-->: %s" % (self.nmea_data, time.strftime("%H:%M:%S") ) )
			rc = self._if.send_command( 'gps inject -nmea ' + self.nmea_data , False )
		
	def task(self):
		self.gps_data_writer()

class GpsReader(threading.Thread):
    """
    @class GpsReaderThread
    @brief Main V2X thread handler for Gps class
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """

    def __init__(self, cli_interface, handler = None):
        """ Initilze class with interface and handler callback """
        threading.Thread.__init__(self)
        self._if = cli_interface
        self._finished = threading.Event()
        self.handler = handler


    def __del__( self ):
        self._if = None

    def run(self):
        """ Thread start point """
        self.read_gps_data()

    def shutdown(self):
        """Stop this thread"""
        self._finished.set()

    def read_gps_data(self):	
        """ Main thread loop function retreive data from target """
        start_time = time.time()
        while 1:
            if self._finished.is_set(): return
            str = ''
            try:
                str = self._if.read_until('\r\n')
            except:
                pass

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
                # Remove 'GPS : ' from message
                if str[0:6] == 'GPS : ':
                    a = str[6:]
                    self.handler(a)
                else:
                    log.info("Received data not from gps : %s" % str)
            # Sleep and release resources for 1 mSec
            common.usleep(1000)

 
class Gps(object):
    """
    @class Gps
    @brief Main V2X handler for GPS retreive from unit
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """
	
    def __init__(self, nmea_data_file = "", cli_interface = common.DEFUALT_INTERFACE, nmea_handler_func = None):
        """ Initilize interface for unit connection """
        self.if_reader = interface.QaCliInterface()
        self.if_writer = interface.QaCliInterface()
        self.handler = None
        self.feed_q = Queue.Queue()
        self._handler_func = nmea_handler_func
        self._nmea_data_file = nmea_data_file
        self.reader = None
        self.writer = None

    def __del__( self ):
        self.reader = None
        self.writer = None
        self.if_reader = None
        self.if_writer = None
        self.handler = None

    def set_data_file(self, nmea_data_file ):
        """ Set simulation file name and path"""
        self._nmea_data_file = nmea_data_file
        	
    def interface( self ):
        """ Get interface connection """
        return self.if_reader
    
    def connect(self, server, port = common.DEFAULT_PORT , timeout = common.DEFAULT_TIMEOUT):
        """ Connect to unit via interface in new connection
        @param[in] server unit address as telnet ip or serial port (TBD)
        @param[in] port port for telnet connection
        @param[in] timeout timeout for telnet connection
        """
        # open channel for reader
        self.if_reader.connect( server, port, timeout )
        self.if_reader.login()
        self.if_reader.send_command("gps stop")
        time.sleep(0.5)
        self.if_reader.send_command("gps start -mode override")
        # init channel for writer
        self.if_writer.connect( server, port, timeout )
        self.if_writer.login()


    def _reader(self):
        """ Start main GPS data retreive thread """
        self.reader = GpsReader( self.if_reader.interface(), self.nmea_data_h.gps_data_handler )
        try:		
            self.reader.start()
            while not self.reader.isAlive():
                common.usleep(1000)
        except:
            raise Error("Faild to active the gps thread")

    def _writer(self):
        self.writer = GpsWriter( self.if_writer, self.feed_q )
        self.writer.setInterval(0.1)
        self.writer.start()

    def start(self):
        # Configure Data handler
        if not os.path.exists( self._nmea_data_file ):
            raise Error("configuration file \'%s\' is missing." % (self._nmea_data_file) )
        
        self.nmea_data_h = NmeaDataHandler( self.feed_q, self._nmea_data_file, self._handler_func ) 
        log.info("Starting GPS reader thread")
        self._reader()
        log.info("Starting GPS writer thread")
        self._writer()

    def stop(self):
        """ Start main GPS data retreive thread """
        self.reader.shutdown()
        while not self.reader.isAlive():
            pass
        self.writer.shutdown()
        while not self.writer.isAlive():
            pass

    def pause(self, input = False, output = False):
        self.input_flow = input
        self.output_flow = output


def usage_example():
    # EXMAPLE : Usage
    import cli

    #nmea_data_file = "c:\\temp\\nmea_data_1.txt"
    nmea_data_file = "c:\\temp\\neter2eilat.nmea"

    gps = Gps( nmea_data_file )
    gps.connect( "10.10.0.60", 8000, 10 )
    gps.start()


    loop = 1
    while loop:
        try:
            time.sleep(0.05)
        except (KeyboardInterrupt, SystemExit):
            log.info ( "Exiting" )
            loop = 0;
            gps.stop()
    
    gps = None

def print_data( data ):
    print data

if __name__ == '__main__':
    log_file = 'c:\\temp\\gps_log.txt'
    print "NOTE : log file created, all messages will redirect to : \n%s" % log_file
    logging.basicConfig(filename=log_file, filemode='w', level=logging.NOTSET)
    log = logging.getLogger(__name__)
    
    usage_example()

