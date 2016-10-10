

from ctypes import *
from datetime import datetime
import socket
import argparse
import signal



class pcap_hdr_t(Structure):
    _pack_ = 1
    _fields_ = [
        (u'magic_number', c_uint32),
        (u'version_major', c_uint16),
        (u'version_minor', c_uint16),
        (u'thiszone', c_int32),
        (u'sigfigs', c_uint32),
        (u'snaplen', c_uint32),
        (u'network', c_uint32)
    ]


class pcaprec_hdr_t(Structure):
    _pack_ = 1
    _fields_ = [
        (u'ts_sec', c_uint32),
        (u'ts_usec', c_uint32),
        (u'incl_len', c_uint32),
        (u'orig_len', c_uint32)
    ]


class PcapFile(object):

    PCAP_MAGIC = 0xa1b2c3d4
    PCAP_MAJOR_VERSION = 2
    PCAP_MINOR_VERSION = 4

    def __init__(self, filename, overwrite = False):

        self._f = open(filename, u'wb' if overwrite == False else 'w+b')
        # write the hdr
        self._f.write(pcap_hdr_t(
            PcapFile.PCAP_MAGIC,
            PcapFile.PCAP_MAJOR_VERSION,
            PcapFile.PCAP_MINOR_VERSION,
            0,
            0,
            65535, # XXX update this if we ever get a bigger packet
            127 # LINKTYPE_IEEE802_11_RADIOTAP
        ))

    def __del__(self):
        self.close()

    def close(self):
        self._f.close()

    def write_packet(self, packetdata):
        now = datetime.now()
        self._f.write(pcaprec_hdr_t(
            now.second,
            now.microsecond,
            len(packetdata),
            len(packetdata)
        ))
        self._f.write(packetdata)


    

if __name__ == "__main__":

    import argparse

    def cmd_pcap(args):

        def close():
            pcap.close()
            sock.close()


        def handler(signum, frame):
            close()



        sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        listen_addr = ("", args.port )
        sock.bind(listen_addr)


        pcap = PcapFile( args.file.decode(u'utf-8'), args.overwrite )

        signal.signal(signal.SIGINT, handler)
        print "Starting Capture on port {}, to file {}".format( args.port, args.file.decode(u'utf-8') )
        try:
            while True:
                data,addr = sock.recvfrom(1518)
                pcap.write_packet( data )

        except:
            pass


    parser = argparse.ArgumentParser( description='Panagea sniffer' )
    parser.add_argument( '-f', '--file', type=str, required=True, help='Pcap file name to create')
    parser.add_argument( '-o', '--overwrite', action="store_true", help='Overwrite pcap file')
    parser.add_argument( '-p', '--port', type=int, default=8030 , help='Port ')
    parser.add_argument( '-l', '--limit', type=int, default=-1, help='Limit number of frames in packet')
    args = parser.parse_args()
    # args = parser.parse_args( ['-f', 'c:/temp/testfile.pcap'] )
    

    cmd_pcap( args )
    # pcapcmd.set_defaults(func=cmd_pcap)

