import sys
import socket
from threading import Thread



class SerialToUdp( object ):
    
    def __init__(self, ip = UDP_SERVER_IP, ip_port = 5454, serial_port = 0, serial_baud = 115200, serial_timeout = 2, print_data = 0 ):
        self.ser_port = serial_port
        self.ser_baud = serial_baud
        self.ser_timeout = serial_timeout
        self.ip = ip
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

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to the port
        self.server_address = ( self.ip , self.ip_port)
        print >>sys.stderr, 'starting up on %s port %s' % self.server_address
        # sock.bind(self.server_address)
        # sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # sock.setblocking( False )
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        # sock.connect( self.server_address )
        return sock


    def start_bridge(self):
        serial_if = self.open_serial_connection()
        socket_if = self.open_udp_server()

        while (1):
            line = serial_if.readline()

            if (line != ''):
                if (self.printing):
                    print line[:-1]
                #socket_if.send( line )
                socket_if.sendto(line,  ( '<broadcast>' , 9090) )
                # self.send_data( line )

            else:
                if (self.printing):
                    print "."

        serial_if.close()



if __name__ == "__main__":

    import os, sys, time
    import win32api

    if ( len(sys.argv) == 1 ):
            print "GPS-to-UDP"
            print "Syntax: " + sys.argv[0] + " serial_port udp_ip(= 127.0.0.1) udp_port(= 5454)"
            print "Example: " + sys.argv[0] + " 20 127.0.0.1 5000"
            # quit()

    # serial_port = int(sys.argv[1])
    serial_port = 15

    if ( len(sys.argv) >= 3 ):
        udp_ip = sys.argv[2]
    else:
        udp_ip = UDP_SERVER_IP

    if ( len(sys.argv) >= 4 ):
        udp_port = sys.argv[3]
    else:
        udp_port = str(UDP_SERVER_PORT)

    if ( len(sys.argv) >= 5):
        printing = 1
    else:
        printing = 0

    print "Reading from serial port: %d" % serial_port
    print "Sending to " + udp_ip + ":" + udp_port

    udp_port = int(udp_port)

    gps_info = { 'port':serial_port, 'baud':230400, 'timeout':2 }

    Ser2ip = SerialToUdp( ip = udp_ip, ip_port = udp_port, serial_port = gps_info['port'], serial_baud = gps_info['baud'] , serial_timeout = gps_info['timeout'] )
    
    sync = pcTimeSyncGps( **gps_info )
    # sync.start_gps_reader()

    # src_info = { 'port':13, 'baud':230400, 'timeout':1 }
    # dst_info = { 'port':4, 'baud':230400, 'timeout':1 }

    # server = SerialLoopBack ( src_info, None )
    # server.start()

    # server = SerialServer ( None , dst_info )