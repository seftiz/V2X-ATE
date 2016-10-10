
# convert all pcap file to pdml 
# tshark -r TML000.pcap -T pdml >tml_test_1.xml

# Export only on frame at a time
# tshark -r TML000.pcap -T pdml -R frame.number==3 >tml_test_1.xml

# Export range of frames
# tshark -r TML000.pcap -T pdml -R "frame.number>=0 && frame.number<=3" >tml_test_1.xml

import os, sys
import subprocess, logging
from uuts import common
from lib import utilities, globals, wiresharkXML
import xmlrpclib


log = logging.getLogger(__name__)

ExportFormatTypes = utilities.Enum(['pdml', 'psml'])

FILE_DEFAULT_FORMAT = 'pdml'


# These paraemters are option
def PcapConvertor(ip = None , port = None):
    ip = ip if not(ip is None) else globals.setup.PcapConvertServer.ip
    port = port if not(port is None) else globals.setup.PcapConvertServer.port

    print "Connecting to server %s on port %d" % ( ip, port )
    server_addr =  'http://%s:%d' % ( ip, port )
    return xmlrpclib.ServerProxy(server_addr)
 

class Packet(object):

    def __init__(self, wireshark_packet):
        self.wireshark_packet = wireshark_packet
    
    @property
    def packet_xml(self):
        return self.wireshark_packet
        #.dump()

    @property
    def number(self):
        return self["frame.number"]
    
    @property
    def len(self):
        return self.field("frame.len")
    
    @property
    def time_delta(self):
        return self.field("frame.time_delta")

    @property
    def protocols(self):
        return self.field("frame.protocols").split(':')
    
    def __getitem__(self, field):
        return self.wireshark_packet.get_items(field)[-1].get_show()


class PcapHandler(object):

    def __init__(self):
        # Store handler for function
        self.pckt_handler = None
        self.num_packets = 0
        # Set Max recursion limit for parse_file
        # sys.setrecursionlimit(10)

        # Process os 
        if 'win32' in sys.platform:
            import win32process
            if win32process.IsWow64Process () == True:
                self.capinfos_file = 'c:\\Program Files (x86)\\Wireshark\\capinfos.exe'
                self.tsharks_file = 'c:\\Program Files (x86)\\Wireshark\\tshark.exe'
            else:
                self.capinfos_file = 'c:\\Program Files\\Wireshark\\capinfos.exe'
                self.tsharks_file = 'c:\\Program Files\\Wireshark\\tshark.exe'
 
        elif 'linux' in sys.platform:
            self.capinfos_file = "./capinfos"
            self.tsharks_file = "./tshark"
        else:
            raise globals.Error("Unknown os type, where is capinfos.exe")
        
        if not( os.path.exists(self.capinfos_file) or os.path.exists(self.tsharks_file) ):
            raise globals.Error("Tshark or capinfos file not found, please make sure you have a full WireShark full installtion")

    def get_num_packets(self, pcap_file):
        """
        TBD : consider use of pypcapfile lbrary for this actions
        """
        try:
            data =  subprocess.check_output([self.capinfos_file,self.pcap_file])
        except WindowsError as e:
            raise globals.Error("FAILED : Please make sure the path are correct")
        except subprocess.CalledProcessError as e:
            raise globals.Error("FAILD : Process failed with return value diffrent from 0")

        data = data.split('\r\n')
        # Get numner of packet in file
        self.num_packets = int(data[4].split(':')[1].strip())
        return self.num_packets


    def export_pcap( self, source_file, dest_file , format = FILE_DEFAULT_FORMAT, frames_to_export = -1):
        
        frames_range = ''

        if  not(os.path.exists(source_file)):
            globals.Error("File not exists")

        if type(frames_to_export) == int:
            if frames_to_export == '-1':
                frame_range = ""
            elif frames_to_export > 0:
                frames_range = '-R frame.number == %d' % frames_to_export
        elif type(frams_to_export) == string:
            if len(frames_to_export.split('-'))>1:
                frames_range = "-R \"frame.number>=%s && frame.number<=%s\"" % ( frames_to_export.split('-')[0].strip(),  frames_to_export.split('-')[1].strip() )
            else:
                Error("frames_to_export value is mismatch, either number or range etc: 1 or 1-5")

        file_args =  ' -r %s -T %s %s >%s' % ( source_file, format, frames_range, dest_file ) 

        cmd = "\"" + self.tsharks_file + "\"" + file_args
        try:
            data =  subprocess.check_output(cmd, shell = True)
        except WindowsError as e:
            raise globals.Error("FAILED : Please make sure the path are correct")
        except subprocess.CalledProcessError as e:
            raise globals.Error("FAILD : Process failed with return value diffrent from 0")

        return globals.EXIT_OK

    
    def _packet_analyzer(self, packet_pdml):

        # Collect statistics
        self.num_packets += 1
        if not self.pckt_handler is None:
            self.pckt_handler( packet_pdml )
            #self.pckt_handler( Packet(packet_pdml) )
            
    def parse_file( self, pdml_file_name, pckt_handler ):
         
        # pdml_filename = self.pcap_file.split('.')[0] + '.' + FILE_DEFAULT_FORMAT
        if  not(os.path.exists(pdml_file_name)):
            raise globals.Error("File not exists")

        file_hwd = open(pdml_file_name, "r")

        i = 0;
        
        #while file_hwd.readline() != '<?xml version="1.0"?>\n':
        while ('xml version' not in file_hwd.readline()) and (i < 20):
            i += 1
            
            
        if ( i >= 20 ):
            raise globals.Error("Start of PDML file not found")

        if ( i == 0 ): file_hwd.seek(0)

        self.pckt_handler = pckt_handler
        wiresharkXML.parse_fh(file_hwd, self._packet_analyzer) 
     
   
        


# The main server proxy 
def PacketAnalyzerServer():
     # Start XML RPC server
    from SimpleXMLRPCServer import SimpleXMLRPCServer

    server = SimpleXMLRPCServer(("", 8000), allow_none=True)
    server.register_function(pow)
    server.register_instance(PcapHandler())
    server.register_introspection_functions()

    print "\n\n\nAutotalks pcap to pdml convertor - server"
    print "-" * 50
    print "Server is up and running on port 8000"

    server.serve_forever()


if __name__ == "__main__":
    import sys
    import cPickle

    class test_me(object):
        @staticmethod
        def test_cb(pckt):
            a = wiresharkXML.Template()

            pckt.build_packet( pckt, a)
            #a = pckt.packet_xml()
            #b = xml2obj(a)
            print "Check object"

            file = "c:\\temp\\class_data.dump"
            a.save_to_file(file)

            b = wiresharkXML.Template()
            wiresharkXML.load_template_from_file( b , file)

            # to deserialize the object
            with open("c:\\temp\\data.dump", "rb") as input:
                obj = cPickle.load(input) # protocol version is auto detected
        
            print "Check object"
            #print "Proccessing frame %s with protocols %s"  % ( pckt["frame.number"], pckt["frame.protocols"] )

    
        def usage_sample(self):
            # Debug area

            # Connet to export server
            # m = PcapConvertor("10.10.1.119", 8000)
            # m.analyzer.export_pcap( "I:\\pdml_result.pcap", "I:\\pdml_result.xml" )

            # Define parser as local handler 
            pdml_parser = PcapHandler()
            pdml_parser.parse_file( "I:\\Honda_packet.xml" , self.test_cb )



    #m = PcapHandler()
    #m.parse_file( "I:\\pdml_result.xml" , test_cb )
    print 'Number of arguments:', len(sys.argv), 'arguments.'
    print 'Argument List:', str(sys.argv)

    if len(sys.argv) > 1:
        if str(sys.argv[1]) == 'server':
            PacketAnalyzerServer()
        else:
            print "Please start file with server parameter"
    else:
        a = test_me()
        a.usage_sample()
