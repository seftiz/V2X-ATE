"""
@file packet_sniffer.py
@brief Packet Sniffers instruments handler

controler
@author    	Shai Shochat
@version	1.0
@date		18/01/2013
"""
import os, sys


if __name__ == "__main__":
    sys.path.append('u:\\qa\\')

from uuts import common
import os
#import paramiko
import subprocess
import time
from lib import ssh
from scp import SCPClient

# import scpclient
import logging
from lib import globals
import paramiko
import pyshark



log = logging.getLogger(__name__) 

# Sniffer constasnt
WIRESHARK_PC_SNIFFER_DEFAULT_USER	=	'root'
WIRESHARK_PC_SNIFFER_DEFAULT_PWD	=	'toor'
PANAGEA2_PC_SNIFFER_DEFAULT_PWD		=	'123'



def importName(modulename, name=None):
    """ Import identifier C{name} from module C{modulename}.

        If name is omitted, modulename must contain the name after the
        module path, delimited by a colon.

        @param modulename: Fully qualified module name, e.g. C{x.y.z}.
        @param name: Name to import from C{modulename}.
        @return: Requested object.
        @rtype: object
    """
    if name is None:
        modulename, name = modulename.split(':', 1)
    module = __import__(modulename, globals(), {}, [name])
    return getattr(module, name)



class SnifferWireShark(object):
    """
    @class WireSharkSniffer
    @brief EtherReal Sniffer driver implementation
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """

    def __init__(self, target_ip, if_id = "mon0", user = WIRESHARK_PC_SNIFFER_DEFAULT_USER, pwd = WIRESHARK_PC_SNIFFER_DEFAULT_PWD):
        self._target_ip = target_ip
        self._if = ssh.SSHSession( target_ip , user, pwd )
        self._sniffer = None
        # Assume the sniffer is active and capturing
        self._initialize = True
        self._user = user
        self._pwd = pwd
        self._wireshark_name = 'tshark'
        self.sniffer_if = 'mon%d'
        self.sniffr_interface = self.sniffer_if % 0
        self.start_capture_cmd = "%s" % self._wireshark_name + " -i "+ self.sniffr_interface + " -w %s/%s"
        self.sniffer_type = 'wireshark'

    def __del__(self):
        del self._if 
        del self._sniffer

    def get_interface_name( if_id ):
            return self.sniffer_if % if_id


    def initialize(self):
        """ initialize sniffer computer, load need drivers """
        # Assume 
       
        if self._initialize:
            return 0
        command_set  = ['sudo modprobe -r ath5k', 'sudo modprobe ath5k bwmode=2',  'sudo ifconfig wlan0 up', 'airmon-ng start wlan0' ]
        for command in command_set:
            rc = self._if.exec_command( command )
            self._if.status_ready()
            rc = self._if.exit_status()
            if ( rc != 0 ):
                raise globals.Error("%s failed !" % command )

        command = "airodump-ng -c 157 mon0"
        self._if.exec_command( command )
        if self._if.exit_status() != -1:
            raise Error("%s failed !" % command)
        self._initialize = True
        
    def start_capture(self, file_name = "test.pcap", dir = "capture" ):
        """ Start capture, activate tshark
        @param[in] file_name file to save captured frames
        @param[in] dir directory of captures files
        """
        if self._sniffer is None:
            self._sniffer = ssh.SSHSession( self._target_ip, self._user, self._pwd )

        self._file_name = file_name
        self._dir = dir


        command = self.start_capture_cmd % (self._dir , self._file_name) 
        rc = self._sniffer.exec_command( command )
        if rc != -1:
            raise globals.Error("%s failed !" % command )

    def stop_capture(self):
        """ Stop capture process, deactivate tshark"""
        if not self._sniffer is None:
            kill_tshark = ssh.SSHSession( self._target_ip, self._user, self._pwd )
            rc = kill_tshark.exec_command( "killall %s" % self._wireshark_name  )
            self.kill_tshark = None

    def get_capture_file(self, src_file, dst_file):
        """ Retreive capture file from sniffer
        @param[in] src_file Source file to copy, full path
        @param[in] dst_file Destenation file, full path
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(self._target_ip , username= self._user, password=self._pwd)

        scp = SCPClient(ssh_client.get_transport())

        scp.get(src_file, dst_file)
        
        scp = None

        #with scpclient.closing(scpclient.Read(ssh_client.get_transport(), '.')) as scp:
        #    scp.receive_file(local_filename = dst_file, remote_filename = src_file)

        ssh_client = None

    def get_status(self):
        if self._sniffer is None:
            return (-1)
        else:
            return self._sniffer.exit_status()

class SnifferPanagea2(SnifferWireShark):
    
    def __init__(self, target_ip, if_id = 0, user = WIRESHARK_PC_SNIFFER_DEFAULT_USER, pwd = PANAGEA2_PC_SNIFFER_DEFAULT_PWD):
        SnifferWireShark.__init__(self, target_ip, if_id, user,pwd)
        self._if_id = if_id
        self._wireshark_name = 'tcpdump'
        self.start_capture_cmd = "/usr/sbin/%s" % self._wireshark_name + " -i wlan%d" % self._if_id + " -w %s/%s" 
        self._initialize = False
        self.type = 'panagea2'

    def set_interface(self, if_id):
        self._if_id = if_id
        self.start_capture_cmd = "/usr/sbin/tcpdump "

        # panagea2 do not support multiple intefaces on tcpdump
        self.start_capture_cmd += "-i wlan%d " % if_id[0]

        #if type(if_id) == list:
        #    for intf in if_id:
        #        self.start_capture_cmd += "-i wlan%d " % intf
        #else:
        #   raise ( "ERROR : the parameter must be list")

        self.start_capture_cmd += "-w %s/%s"


    def initialize(self):

        if self._initialize:
            return 0
        
        if self._sniffer is None:
            self._sniffer = ssh.SSHSession( self._target_ip, self._user, self._pwd )

        if not self._sniffer is None:
            self._sniffer.exec_command("cd / && cd root")

        self._initialize = True

    def stop_capture(self):
        SnifferWireShark.stop_capture(self)
        # Since the default behaiver is sirit, file must be copied to local\capture\file
        src_file = "%s/%s" % ( self._dir, self._file_name )
        dst_file = "c:/capture/" + self._file_name
        self.get_capture_file( src_file, dst_file )

    def start_capture(self, file_name = "test.pcap", dir = "capture" ):
        """ Start capture, activate tshark
        @param[in] file_name file to save captured frames
        @param[in] dir directory of captures files
        """
        if self._sniffer is None:
            self._sniffer = ssh.SSHSession( self._target_ip, self._user, self._pwd )

        self._file_name = file_name
        self._dir = '/root/capture'

        command = self.start_capture_cmd % (self._dir , self._file_name) 
        rc = self._sniffer.exec_command( command )
        if rc != -1:
            raise globals.Error("%s failed !" % command )

class SnifferSirit(SnifferWireShark):
    
    def __init__(self, target_ip, if_id = 0, user = WIRESHARK_PC_SNIFFER_DEFAULT_USER, pwd = PANAGEA2_PC_SNIFFER_DEFAULT_PWD):
        SnifferWireShark.__init__(self, target_ip, if_id, user, pwd)
        # import DSRC tool
        from lib.instruments.sirit import sirit_config_tool
        self.if_id = if_id
        self.sniffer_if = '\\\\.\pipe\EmbdPipe%d'
        self.sniffer_interfaces = "-i " + self.sniffer_if % if_id
        self.start_capture_cmd = "c:\progra~1\\wireshark\\%s" % self._wireshark_name + self.sniffer_interfaces + " -w %s"
        self.type = 'sirit'

        self.tool = sirit_config_tool.SIRIT_DSRC_TOOL()

        self._initialize = False

    def set_interface( self, if_id ):
        self.if_id = if_id
        self.sniffer_interfaces = ''
        self.start_capture_cmd = "c:\progra~1\\wireshark\\%s " % self._wireshark_name
        if type(if_id) == list:
            for intf in if_id:
                self.sniffer_interfaces += "-i " + self.sniffer_if % intf  + ' '
                self.start_capture_cmd += '-i ' + self.sniffer_if % intf
        else:
            raise ( "ERROR : the parameter must be list")

        self.start_capture_cmd += "-w %s"

    
    def start_live_capture(self, interfaces, total_packet_count = -1, timeout_sec = 300, bpf_filter = None, display_filter = None, only_summaries = False ):

        sniffer_interfaces = ''
        if type(interfaces) == list:
            for intf in interfaces:
                sniffer_interfaces += self.sniffer_if % intf + ' '
        else:
            sniffer_interfaces = self.sniffer_if % interfaces

        capture = pyshark.LiveCapture( interface = sniffer_interfaces.strip() , bpf_filter = bpf_filter , display_filter = display_filter, only_summaries = only_summaries)
        if total_packet_count > 0:
            capture.sniff( packet_count = total_packet_count, timeout = timeout_sec )
        else:
            capture.sniff( timeout = timeout_sec )

        return capture



    def start_capture(self, file_name = "test.pcap", dir = "" ):
        """ Start capture, activate tshark
        @param[in] file_name file to save captured frames
        @param[in] dir directory of captures files
        """
        if self._sniffer is None:
            self._sniffer = ssh.SSHSession( self._target_ip, self._user, self._pwd )

        command = self.start_capture_cmd % os.path.join('c:/capture/',os.path.split(file_name)[1])
        rc = self._sniffer.exec_command( command )
        if rc != -1:
            raise globals.Error("%s failed !" % command )

    def initialize(self):

        if self._initialize:
            return 0
        
        if self._sniffer is None:
            self._sniffer = ssh.SSHSession( self._target_ip, self._user, self._pwd )

        if not self._sniffer is None:
            self._sniffer.exec_command("cd\\")
            self._sniffer.exec_command("cd\\Program Files\\WireShark")

        self._initialize = True

    def configure_dsrc_tool(self):

        # make sure tool is active
        if self.tool.is_sirit_active():
            self.tool.get_app_handle()
        else:
            self.tool.start_sirit()
            self.tool.select_window()
            self.tool.configure_tool_default()
 
        gps_state = self.tool.get_gps_state()
        # print gps_state
        try:
            self.tool.start_gps_track()
            self.tool.change_gateway_time()
        except Exception as e:
            pass


SnifferTypes = {'wireshark': SnifferWireShark, 'panagea2': SnifferPanagea2, 'sirit': SnifferSirit }

def Sniffer(type, target_ip, if_id = "", user = None, pwd = None):
    return SnifferTypes[type](target_ip, if_id, user, pwd)

#class Sniffer(SnifferWireShark):
#    """
#    ##################  TBD ##################
#    @class Sniffer
#    @brief Sniffer Implementation 
#    @author Shai Shochat
#    @version 0.1
#    @date	10/01/2013
#"""

#    def __init__(self, type, target_ip, user = None, pwd = None):
#        return SnifferTypes[type](target_ip)
#        #self.sniffer.__init__(self, target_ip, user, pwd)


if __name__ == "__main__":

   
    #from scp import SCPClient
    #ssh =  ssh.SSHSession( '10.10.0.165' , 'root' , '123')
    #scp = SCPClient(ssh._client.get_transport())
    #scp.get('/root/capture/test_111222.pcap', 'c:/capture/my_test.pcap')


    sniffer = Sniffer( 'panagea2', '10.10.0.165', 0, user = 'root', pwd = '123')
    sniffer.initialize()
    sniffer.set_interface([0,1])


    sniffer.start_capture( file_name = "test_33444555.pcap" ) 
    time.sleep(5)
    sniffer.stop_capture() 


    time.sleep(5)
	#snif1 = SnifferWireShark("10.10.0.160")

 
