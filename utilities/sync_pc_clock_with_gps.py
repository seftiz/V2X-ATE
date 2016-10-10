

"""
This utility shuld run on the host computer and connect to a referaence GPS signal.
The Data shold then be used for time synce



"""
import sys
import serial
from pynmea.streamer import NMEAStream
import win32api
import datetime
import time
import operator
import socket
from threading import Thread
import zmq


"""
    $GPRMC,100500.200,A,2935.1829,N,03458.3629,E,29.1,29.6,030814,0.0,W*7E
    $GPGGA,100500.200,2935.1829,N,03458.3629,E,1,10,0.9,015.34,M,14.5,M,,*6A
    $GNGSA,A,3,19,32,22,06,03,14,16,18,11,21,,,1.4,0.9,1.1*24
    $GNGSA,A,3,,,,,,,,,,,,,1.4,0.9,1.1*20
    $GNGSA,A,3,,,,,,,,,,,,,1.4,0.9,1.1*20
    $GPGSV,3,1,12,03,66,227,51,06,65,196,51,10,14,316,,11,16,307,47*77
    $GPGSV,3,2,12,14,59,124,51,16,15,216,48,18,17,050,48,19,53,310,51*75
    $GPGSV,3,3,12,21,16,097,48,22,55,027,51,24,29,246,,32,21,246,48*7E
    $GPGLL,2935.1829,N,03458.3629,E,100500.200,A*39
"""


UDP_SERVER_IP = socket.gethostbyname(socket.gethostname())
UDP_SERVER_PORT = 5454

class SerialServer( object ):
 
    def __init__(self, source_serial, dest_serial ):
        self.src_data = source_serial
        self.dest_data =  dest_serial
        self.source_port = None
        self.dest_port = None

    def open_ports ( self ):
        try:
            if not self.src_data is None:
                self.source_port = serial.Serial(    port='COM%d' % self.src_data['port'],
                                                    baudrate=self.src_data['baud'],
                                                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                                                    timeout=1)

            if not self.dest_port is None:
                print "configurign dest port"															
                self.dest_port = serial.Serial(  port='COM%d' % self.dest_data['port'],
                                                baudrate=self.dest_data['baud'],
                                                parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                                                timeout=1)
        except Exception as e:
            pass


 

class SerialLoopBack( SerialServer ):

    def __init__(self, source_serial, dest_serial ):
        super(SerialLoopBack, self).__init__(source_serial, dest_serial)
 
    def start( self ):

        self.open_ports()
        while True:
            data = self.source_port.readline()
            if len(data) > 0:
                self.source_port.write(data)
                print data




 
 
class NMEA_Modifier( SerialServer ):
       
    def __init__(self, source_serial, dest_serial ):
        super(NMEA_Modifier, self).__init__(source_serial, dest_serial)
        self.nav_data = "$GPRMC,100500.200,A,2935.1829,N,03458.3629,E,29.1,29.6,030814,0.0,W*7E\n$GPGGA,100500.200,2935.1829,N,03458.3629,E,1,10,0.9,015.34,M,14.5,M,,*6A\n$GNGSA,A,3,19,32,22,06,03,14,16,18,11,21,,,1.4,0.9,1.1*24\n$GNGSA,A,3,,,,,,,,,,,,,1.4,0.9,1.1*20\n$GNGSA,A,3,,,,,,,,,,,,,1.4,0.9,1.1*20\n$GPGSV,3,1,12,03,66,227,51,06,65,196,51,10,14,316,,11,16,307,47*77\n$GPGSV,3,2,12,14,59,124,51,16,15,216,48,18,17,050,48,19,53,310,51*75\n$GPGSV,3,3,12,21,16,097,48,22,55,027,51,24,29,246,,32,21,246,48*7E\n$GPGLL,2935.1829,N,03458.3629,E,100500.200,A*39\n"


    def checksum(self, sentence):
        sentence = sentence.strip('\n')
        nmeadata,cksum = sentence.split('*', 1)
        calc_cksum = reduce(operator.xor, (ord(s) for s in nmeadata), 0)
        print hex(calc_cksum)
        return nmeadata,int(cksum,16),calc_cksum

    def start_server(self):
	
        gps_parser = NMEAStream()
        while True:
            try:
                if not(self.src_data is None):
                    gps_info = source_port.readline()
                else:
                    print "Loading static nav data"
                gps_info = self.nav_data.split('\n')
                for line in gps_info:
                    gps_sentence = gps_parser._get_type(line)()
                    gps_sentence.parse(gps_feed)
                    if gps_sentence.sen_type == 'GPRMC' or gps_sentence.sen_type == 'GPGGA':
                        time = datetime.strptime('%s' % gps_sentence.timestamp, '%H%M%S.%f')
                        time += datetime.timedelta(microseconds=1000)
                    #GPGGA
                    print line
                    dest_port.writeline( line )
                time.sleep(1)
			
            except Exception as e:
                pass
				
        dest_port.close()

class SerialToBcastUdp( object ):
    
    def __init__(self, ip_port = UDP_SERVER_PORT, serial_port = 0, serial_baud = 115200, serial_timeout = 2, print_data = 0 ):
        self.ser_port = serial_port
        self.ser_baud = serial_baud
        self.ser_timeout = serial_timeout
        self.ip_port = ip_port
        self.printing = print_data
        if serial_port > 0:
            thread = Thread(target = self.start_bridge, args = ())
            thread.start()
            #thread.join()
            #start_bridge()

        
    def send_data(self, msg ):
        socket(AF_INET,SOCK_DGRAM).sendto(msg,  self.server_address )

    def open_serial_connection(self):
        try:
            serial_port = serial.Serial(    port='COM%d' % self.ser_port,
                                            baudrate=self.ser_baud,
                                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                                            timeout=self.ser_timeout)

            return serial_port
        except Exception, e:
            raise e
    def open_udp_server(self):
        import zmq

        context = zmq.Context()
        sock = context.socket(zmq.PUB)
        sock.bind( 'tcp://*:%d' % UDP_SERVER_PORT )


        #sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        return sock


    def start_bridge(self):
        serial_if = self.open_serial_connection()
        socket_if = self.open_udp_server()

        while (1):
            line = serial_if.readline()

            if (line != ''):
                if (self.printing):
                    print line[:-1]

                # socket_if.sendto(line,  ( 'localhost' , UDP_SERVER_PORT) )
                #socket_if.sendto(line,  ( '<broadcast>' , UDP_SERVER_PORT) )
                socket_if.send(line)

            else:
                if (self.printing):
                    print "."

        serial_if.close()

	
    
class pcTimeSyncGps(object):
    
    def __init__(self, port, baud = 115200, timeout = 10.0):
        self.port = port
        self.baud = baud
        self.timeout = timeout
        
          
    def start_serial_connection(self):
        try:
            serial_port = serial.Serial(    port='COM%d' % self.port,
                                            baudrate=self.baud,
                                            parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS,
                                            timeout=self.timeout)

            return serial_port
        except Exception, e:
            print e
            sys.exit()
    
    def start_gps_reader(self):

        #         serial_port = self.start_serial_connection()
        #sock = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        #sock.setblocking(0)
        #sock.bind( ('', UDP_SERVER_PORT) )

        context = zmq.Context()
        sock = context.socket(zmq.SUB)
        sock.setsockopt(zmq.SUBSCRIBE, '')
        sock.connect('tcp://localhost:%d' % UDP_SERVER_PORT )

        gps_parser = NMEAStream()

        sat_lock = 0
        print "Starting reading from port"
        if sock:
            while True:
                try:
                    #gps_feed =  serial_port.readline()
                    gps_feed = sock.recv()
                    if gps_feed[0] != '$':
                        print "JUNK feed : " + gps_feed
                        continue
                    
                    # print "gps_feed : " + gps_feed
                    gps_sentence = gps_parser._get_type(gps_feed)()
                    gps_sentence.parse(gps_feed)
                    if gps_sentence.sen_type == 'GPGSA':
                        if (int(gps_sentence.mode_fix_type) > 1) and (sat_lock < 3):
                            # Set last lock state
                            sat_lock = int(gps_sentence.mode_fix_type)
                            print "Sat is locked with value of {}".format( sat_lock )
                            # Set computer clock
                            
  
                    if gps_sentence.sen_type == 'GPRMC':
                       # print "date " + gps_sentence.datestamp + " time : " + gps_sentence.timestamp
                       #date 240413 time : 201917.00
                       a = '%s %s' % (gps_sentence.datestamp, gps_sentence.timestamp)

                       time_obj = time.strptime('%s' % a, '%d%m%y %H%M%S.%f')
                       if ( (datetime.datetime.strptime('%s' % a, '%d%m%y %H%M%S.%f').microsecond) == 0 ):
                           new_time = [ time_obj.tm_year, time_obj.tm_mon, time_obj.tm_wday, time_obj.tm_mday, time_obj.tm_hour, time_obj.tm_min, time_obj.tm_sec, 0]
                           # new_time = [ time_obj.year, time_obj.month, time_obj.tm_wday, time_obj.tm_mday, time_obj.tm_hour, time_obj.tm_min, time_obj.tm_sec, 0]
                           print "Updating clock to: date " + gps_sentence.datestamp + " time : " + gps_sentence.timestamp
                           win32api.SetSystemTime (*new_time)

                except Exception, e:
                    pass 
                    # print e
        else:
            print 'Error opening serial port'
            sys.exit()






def checksum(sentence):
	import operator

	sentence = sentence.strip('\n')
	nmeadata,cksum = sentence.split('*', 1)
	calc_cksum = reduce(operator.xor, (ord(s) for s in nmeadata), 0)

	return nmeadata,int(cksum,16),calc_cksum
		
						
if __name__ == "__main__":
    import os, sys, time

    import win32api

    if ( len(sys.argv) == 1 ):
            print "GPS-to-UDP"
            print "Syntax: " + sys.argv[0] + " serial_port udp_port(= 5454)"
            print "Example: " + sys.argv[0] + " 20 5454"
            # quit()

    # serial_port = int(sys.argv[1])
    serial_port = 15

    if ( len(sys.argv) >= 3 ):
        udp_port = sys.argv[2]
    else:
        udp_port = str(UDP_SERVER_PORT)

    if ( len(sys.argv) >= 4):
        printing = 1
    else:
        printing = 0

    print "Reading from serial port: %d" % serial_port
    print "Sending to <broadcast>" + ":" + udp_port

    udp_port = int(udp_port)

    gps_info = { 'port':serial_port, 'baud':230400, 'timeout':2 }

    Ser2ip = SerialToBcastUdp( ip_port = udp_port, serial_port = gps_info['port'], serial_baud = gps_info['baud'] , serial_timeout = gps_info['timeout'] )
    
    sync = pcTimeSyncGps( **gps_info )
    sync.start_gps_reader()

    # src_info = { 'port':13, 'baud':230400, 'timeout':1 }
    # dst_info = { 'port':4, 'baud':230400, 'timeout':1 }

    # server = SerialLoopBack ( src_info, None )
    # server.start()

    # server = SerialServer ( None , dst_info )

