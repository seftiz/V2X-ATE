"""
@file cli_5.py
@brief V2X CLI API for SDK 5
@author    	Shai Shochat
@version	1.0
@date		13/05/2014

"""
import logging, re
from uuts import interface
from uuts import common
from uuts.craton.cli import gps
from uuts.craton.cli import navigation
import os
from lib import globals
from lib import utilities
import time

log = logging.getLogger(__name__)

class qaCliManagment(object):

    def __init__(self):
        self.__qa_cli = {}

    def __del__(self):
        for cli in self.__qa_cli:
            try:
                self.close(cli)
            except Exception as e:
                log.error("qaCli destructor: close cli {} received exception".format(cli))

    def create(self, name):
        user_cli = v2x_cli.qaCliApi()
        user_cli.uut = self
        self.__qa_cli[name] = user_cli
        return self.__qa_cli[name] 

    def close( self, name):
        try:
            self.__v2x_cli[cli_name].disconnect()
        except Exception as e:
            log.error("close cli {} received exception in cli disconnect".format(cli))
        finally:
            self.__v2x_cli[cli_name] = None
            del self.__v2x_cli[cli_name]

    def kill( self, name, name_to_kill ):
        try:
            # verify cli address is exists
            if len(self.__qa_cli[name_to_kill].cli_addr):
                self.__qa_cli[name].thread_kill( self.__qa_cli[name_to_kill].cli_addr )
            else:
                raise Exception('Missing cli addr to kill')
        except Exception as e:
            log.error("kill cli {} received exception in cli thread kill".format(cli))

    def cli(self, name):
        return self.__qa_cli[name]

    def count( self ):
        """ Get Number of active cli """
        try: 
            return len(self.__qa_cli)
        except Exception:
            return 0

class Register(object) :

    def __init__(self, interface):
        self._if = interface
        self._name = "register"

    def device_register(self, type = "hw", embedded_ip = None ,device_type = 0, i_f = None):
        
        cmd = "%s device" % self._name
        cmd += (" -hw_addr %s"  % embedded_ip)
        cmd += (" -device_type %d"  % device_type) 
        cmd += (" -if %s"  % i_f)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data;
        #if 'ERROR' in data:
        #    raise Exception( data )
        
    def service_register(self,service_name,service_type,device_name):
        cmd = "%s service" % self._name
        cmd += (" -service_name %s"  % service_name)
        cmd += (" -service_type %d"  % service_type) 
        cmd += (" -device_name %s"  % device_name)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data;
        #if 'ERROR' in data:
        #    raise Exception( data )


class linkApi(object):

    def __init__(self, interface):
        self._if = interface
        self._name = "link"

    def service_create(self, type = "hw", server_ip = None ):
        
        cmd = "%s service create" % self._name
        cmd += (" -type %s"  % type)
        cmd += (" -server_addr %s"  % server_ip) if not server_ip is None else ""
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )

                 

    def service_delete(self):
        cmd = "%s service delete" % self._name
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )




    def socket_create(self, if_idx, frame_type, proto_id):
        cmd = "%s socket create " % self._name
        cmd += "-if_idx %d -frame_type %s -protocol_id 0x%x" % ( (if_idx+1), frame_type, proto_id)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data
        #if 'ERROR' in data:
        #    raise Exception( data )


    def socket_delete(self):
        cmd = "%s socket delete" % self._name
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data
        #if 'ERROR' in data:
         #   raise Exception( data )


    def transmit(self, payload_len = None, tx_data = None, dest_addr = None, frames = 1, rate_hz = 1, user_priority = None, data_rate = None, power_dbm8 = None,op_class = None):
        
        cmd = "%s socket tx" % self._name
        cmd += (" -frames %d"  % frames)
        cmd += (" -rate_hz %d"  % rate_hz)
        if tx_data == None and payload_len == None:
            payload_len = 50
        cmd += (" -payload_len %s"  % payload_len) if not payload_len is None else ""
        cmd += (" -tx_data %s"  % tx_data) if not tx_data is None else ""

        #if not tx_data is None and not data_file is None:
        #    try:
        #        data_file.write(tx_data + "\n") 
        #    except Exception as e:
        #        return "error";
        
        cmd += (" -dest_addr %s"  % dest_addr) if not dest_addr is None else ""
        cmd += (" -user_priority %d"  % user_priority) if not user_priority is None else ""
        cmd += (" -data_rate %d"  % data_rate) if not data_rate is None else ""
        cmd += (" -power_dbm8 %d"  % power_dbm8) if not power_dbm8 is None else ""
        cmd += (" -op_class %s"  % op_class) if not op_class is None else ""
        self._if.send_command(cmd, False)
        #time.sleep((frames / rate_hz) +10)
        #data = self._if.read_until_prompt( timeout  = (frames / rate_hz) +10)        
        #return data;
        #if 'ERROR' in data:
         #   raise Exception( data )

        # No response till end of transmission 

    def receive(self, frames, timeout = None, print_frame = None,out_queue = None):
        cmd = "link socket rx -frames %s" % frames
        cmd += (" -print %s"  % print_frame) if not print_frame is None else ""
        cmd += (" -timeout_ms %s"  % timeout) if not timeout is None else ""
        self._if.send_command(cmd)
        #data = self._if.read_until_prompt( timeout  = 5000) 
        #if out_queue is not None : 
        #    out_queue.put(data)  
        #return data
        #if 'ERROR' in data:
        #    raise Ebxception( data )

    def reset_counters(self):
        cmd = "%s counters reset" % self._name
        return self._if.send_command(cmd)
    
    def read_counters(self):

        cnts = dict()
        cmd = "%s counters print" % self._name
        data1 = self._if.send_command(cmd)
        
        data = self._if.read_until_prompt(timeout  = 3)
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

    def get_socket(self):
        cmd = "link socket get" % self._name
        rc = self._if.send_command(cmd, True)
        # Make sure data echo exists
        if not cmd in rc:
            rc = self._if.read_until_prompt()

        if ( int(rc.split('\r\n')[1].split(':')[1].strip(),16) <= 0 ):
            raise Exception( "Session address is wrong")

        return ('0x' + rc.split('\r\n')[1].split(':')[1].strip())

    def set_socket( self, address ):
        """ Set already active session to a new connection """
        cmd = "{} socket set -addr {}".format( self._name, address )
        self._if.send_command(cmd)

    def netif_profile_set(self,  netif_index, profile ):
        cmd = "%s netif_profile set " % self._name        
        cmd += (" -datarate %s"  % profile[3]) #datarate
        cmd += (" -power_dbm8 %s"  % profile[4]) #power_dbm8
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )


    # chani added : 

    def socket_create_api_test(self, if_idx, frame_type, proto_id):
        cmd = "%s api_test socket_create " % self._name
        cmd += "-if_idx %d -frame_type %s -protocol_id 0x%x" % ( (if_idx+1), frame_type, proto_id)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data

    def default_service_get(self):
        
        cmd = "%s api_test service_get" % self._name        
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data         
  
    def service_delete_api_test(self ) :
        cmd = "%s service delete" % self._name
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data 

    def dot4_channel_start(self, request, wait ):
        cmd = "%s api_test dot4_channel_start" % self._name
        cmd += (" -if_index %s" % request[0]) #if_index
        cmd += (" -op_class %s" % request[1]) #op_class
        cmd += (" -channel_num %s" % request[2]) #channel_num
        cmd += (" -time_slot %s" % request[3]) #time_slot
        cmd += (" -immediate_access %s" % request[4]) #immediate_access
        cmd += (" -wait_type %s" % wait[0])
        cmd += (" -wait_usec %s" % wait[1])
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data       

    def dot4_channel_end(self, request, wait ):
        cmd = "%s api_test dot4_channel_end" % self._name
        cmd += (" -if_index %s" % request[0]) #if_index
        cmd += (" -op_class %s" % request[1]) #op_class
        cmd += (" -channel_num %s" % request[2]) #channel_num
        cmd += (" -wait_type %s" % wait[0])
        cmd += (" -wait_usec %s" % wait[1])
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data       

    def dot4_channel_end_receive(self, indication, wait):
        cmd = "%s api_test dot4_channel_end_receive" % self._name
        cmd += (" -if_index %s"  % indication[0]) #if_index
        cmd += (" -op_class %s"  % indication[1]) #op_class
        cmd += (" -channel_num %s"  % indication[2]) #channel_num
        cmd += (" -reason %s"  % indication[3]) #reason
        cmd += (" -wait_type %s" % wait[0])
        cmd += (" -wait_usec %s" % wait[1])
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data       

 #   def netif_profile_set(self,  netif_index, profile ):
 #       cmd = "%s api_test netif_profile set " % self._name        
 #       cmd += (" -netif_index %s"  % netif_index)
 #       cmd += (" -if_index %s"  % profile[0]) #if_index
 #       cmd += (" -op_class %s"  % profile[1]) #op_class
 #       cmd += (" -channel_num %s"  % profile[2]) #channel_num
 #       cmd += (" -datarate %s"  % profile[3]) #datarate
 #       cmd += (" -power_dbm8 %s"  % profile[4]) #power_dbm8
 #       self._if.send_command(cmd)
  #      data = self._if.read_until_prompt( timeout  = 1)
 #       if 'ERROR' in data:
 #           raise Exception( data )

    def send(self ,params = None ,wait = None ):
        cmd = "%s api_test send" % self._name        
        #cmd += (" -source_address %s"  % params[0]) #source_address
        cmd += (" -dest_addr %s"  % params[1])if not params is None else "" 
        cmd += (" -uset_priority %s"  % params[2])if not params is None else "" 
        cmd += (" -op_class %s"  % params[3])if not params is None else "" 
        cmd += (" -channel_num %s"  % params[4])if not params is None else "" 
        cmd += (" -datarate %s"  % params[5])if not params is None else "" 
        cmd += (" -power_dbm8 %s"  % params[6])if not params is None else "" 
        cmd += (" -wait_type %s" % wait[0])if not params is None else ""
        cmd += (" -wait_usec %s" % wait[1])if not params is None else ""
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data
    """ 
    def receive(self, data_size, wait ):
        cmd = "%s api_test receive" % self._name        
        cmd += (" -data_size %s"  % data_size)        
        cmd += (" -wait_type %s" % wait[0])
        cmd += (" -wait_usec %s" % wait[1])
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data       
    """

    def sample_subscriber_create(self, config ):
        cmd = "%s api_test sample_subscriber_create " % self._name
        cmd += (" -if_index %s"  % config[0] ) #if_index
        cmd += (" -type %s"  % config[1]) #type
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data       

    def sample_subscriber_delete(self, subscriber ):
        cmd = "%s api_test sample_subscriber_delete " % self._name
        cmd += (" -pointer %s"  % subscriber)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data        

    def sample_int32_receive(self, subscriber, value_ptr, wait):
        cmd = "%s api_test sample_int32_receive " % self._name
        cmd += (" -subscriber %s"  % subscriber)
        cmd += (" -value_ptr %s"  % value_ptr)
        cmd += (" -wait %s"  % wait)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data
        
"""chani added - end """

class canApi(linkApi):

    def __init__(self, interface):
        super(canApi, self).__init__(interface)
        self._name = "can"

    def socket_create(self, device_id, can_filter):
        """"can socket create [ -device_id 0|1|0xFFU ] -filter_count 0|N [can_id_1 0x1 can_id_mask_1 0xFFFFFFFFU .... can_id_N 0x1 can_id_mask_N 0xFFFFFFFFU]"""

        cmd = "%s socket create " % self._name
        if ( not type(can_filter) is dict ):
            raise Exception("can_filter must be dict as  { 0x123 : 0xFFBCCdd, 0xFF : 0xFFBBCCAA } ")

        cmd += " -device_id %s"  % hex(device_id)

        cmd += " -filter_count %d"  % len(can_filter) 
        for i, can in enumerate(can_filter):
            cmd += "-can_id_%d 0x%x -can_id_mask_%d 0x%x" % (i, can, i, can_filter[can] )

        data = self._if.send_command(cmd)
        data = self._if.read_until_prompt()

        return data

    def socket_delete(self):
        cmd = "%s socket delete" % self._name
        data = self._if.send_command(cmd)

    def transmit(self, frames = 1, rate_hz = 1, can_id = None, can_data = None, data_size = None):
        """can socket tx [-frames 1- ...] [-rate_hz 1 - ...] [-can_id 0x1 -can_data '000102030405' | -data_size 8]"""

        cmd = "%s socket tx" % self._name
        cmd += (" -frames %d"  % frames)
        cmd += (" -rate_hz %d"  % rate_hz)

        cmd += (" -can_id %s"  % hex(can_id)) if not can_id is None else ""
        if not (can_data is None or len(can_data) == 0):
            cmd += (" -can_data \'%s\'"  % can_data)

        if not data_size is None:
            cmd += (" -data_size %d"  % data_size)

        data = self._if.send_command(cmd)
        data = self._if.read_until_prompt()

        return data

    def transmit_load(self, frames = 10000, rate_hz = 0, err_part = 0):
        """can socket tx-load [-frames 10000- ...] [-rate_hz 0 - ...]"""

        cmd = "%s socket tx-load" % self._name
        cmd += (" -frames %d"  % frames)
        cmd += (" -rate_hz %d"  % rate_hz)
        cmd += (" -err_part %d"  % err_part)

        data = self._if.send_command(cmd)
        data = self._if.read_until_prompt()

        return data

    def receive(self, frames, timeout = None, print_frame = None):
        """ can socket rx [-frames 1- ...] [-print (0|1)] [-timeout_ms (0-1e6)]" """

        cmd = "%s socket rx -frames %s" % (self._name, frames)
        cmd += (" -print %d"  % print_frame) if not print_frame is None else ""
        cmd += (" -timeout_ms %d"  % timeout) if not timeout is None else ""
        data = self._if.send_command(cmd)

        if frames == 1 and print_frame:
#       pattern = 'ID = (\S+), DLC = (\d+), data[0:7] = (\S+)'
            data = self._if.read_until_prompt()
            lines = data.splitlines()
            if len(lines) != 5  or "ID =" not in lines[3] :
                raise Exception( "Can receive : got wrong data")

            sp = lines[3].split(',',3)[1:]
            can_id = int(sp[0].split('=')[1].strip(),16)
            dlc = int(sp[1].split('=')[1].strip())
            can_data = [int(x.strip(),16) for x in sp[2].split('=')[1].split(',')]
            return can_id, dlc, can_data

    def read_rx_rate(self):
        """ can rx rate """
        cmd = "can rx rate"
        data = self._if.send_command(cmd)
        
        data = self._if.read_until_prompt()
        if 'rate' not in data:
            return 0

        """
        RX average frames rate = %u
        """
        data = data.split('\r\n')
        rate = int(data[1].split('=')[1].strip())

        return rate

class navApi(object):
    
    def __init__(self, interface):
        self._if = interface
        self._name = "link"

    def __del__(self):
        self.nav = None

    def init( self, type, server_addr = None ):
        self.nav = navigation.NavigationRecorder( self._if )
        self.nav.init( type, server_addr )
        
    def start( self, output = None ):
        if not output == None:
            type, destination = output
            self.nav.set_output( type , destination )
        self.nav.start()

    def stop( self ):
        self.nav.stop()

    def terminate(self):
        self.nav.terminate()
        del self.nav


class Crypto(object):

    def __init__(self, interface, socket_type):
        self.socket_type = socket_type
        self._if = interface
        self._name = 'ecc'

    def socket_create(self):
        cmd = "%s socket create " % 'ecc'
        cmd += "-action %s" % ( self.socket_type )
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )
    
    def socket_delete(self):
        cmd = "%s socket delete " % 'ecc'
        cmd += "-action %s" % ( self.socket_type )
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )

  
    def get_curve( self ):
        """usage : ecc curve set -action sign|verify"""
        cmd = "%s curve " % 'ecc'
        cmd += "-action %s" % ( self.socket_type )
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )
        elif 'ECC sign curve type' in data:
            return data.split('ECC sign curve type', 1)[1]
    
    def set_curve( self, val ):
        """usage : ecc curve set -action sign|verify|all -curve 224|256"""
        cmd = "%s curve set " % 'ecc'
        cmd += "-action {} -curve {}".format( self.socket_type , val)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )

class eccApi(linkApi):

    class Verification(Crypto):
        
        def __init__(self, interface):
            self._if = interface
            Crypto.__init__( self, self._if, 'verify')
            self._name = "ecc verification"
            

        def set_public_key(self, x, y):
            """usage : ecc verification public-key -x 360c3a... -y 360c3a...."""
            cmd = "%s public-key " % self._name
            cmd += "-x {} -y {}".format( x , y)
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )

        def get_public_key(self):
            """usage : ecc verification public-key"""
            cmd = "%s public-key" % self._name
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )
            return data

        def set_request(self, id,  hash):
            """ecc verification request -id N -hash 360c..."""
            cmd = "%s request " % self._name
            cmd += "-id {} -hash {}".format( id, hash)
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )

        def get_response(self):
            """ecc verification get-response"""
            cmd = "%s get-response" % self._name
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )

            # ECC request 0 is 0
            r = re.compile('ECC request (\d+) is (\d+)')
            a = r.split(data)
            
            return a[2] if len(a) > 2 else None

        def set_signuture(self, r, s):
            """usage : ecc verification signature -r 360c3a... -s 360c3a...."""
            cmd = "%s signature " % self._name
            cmd += "-r {} -s {}".format( r, s )
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )
             
            """usage : ecc verification signature -r 360c3a... -s 360c3a...."""
            cmd = "%s signature " % self._name
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )

            # TBD : Parse it in the future
            return data

    class Sign(Crypto):

        def __init__(self, interface):
            self._if = interface
            self._name = "ecc sign"
            Crypto.__init__( self, self._if, 'verify')


        def key(self, private_key):
            "usage : ecc sign key -private_key 360c3ae1cc12dd1f43fa4286827e9848d8eb6093ab98c5a8b23000c9dd1d3489"
            cmd = "%s key " % self._name
            cmd += "-private_key {}".format( private_key )
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )

        def request(self, id, hash):
            """usage : ecc sign request -id 1-N -hash 6e43d9322536c7535efbc81edc214974780fe2f78bd0b2a2c93126c68495a379"""
            cmd = "%s request " % self._name
            cmd += "-id {} -hash {}".format( id, hash)
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )

        def get_response(self, timeout_ms = None ):
            """usage : ecc sign get-response [-timeout_ms n]"""
            cmd = "%s get-response " % self._name
            cmd += "-timeout {}".format( timeout ) if not timeout_ms is None else ""
            self._if.send_command(cmd)
            data = self._if.read_until_prompt( timeout  = 1)
            if 'ERROR' in data:
                raise Exception( data )


    def __init__(self, interface):
        
        self._if = interface
        self.verification = self.Verification( self._if )
        self.sign = self.Sign( self._if )
        self._name = "ecc"

class wlanMibApi(linkApi):

    def __init__(self, interface):
        super(wlanMibApi, self).__init__(interface)
        self._name = "wlanMib"
    
    def transport_create(self, type = "remote", server_ip = None):
        cmd = "remote transport create"
        cmd += (" -ip_addr 192.168.120.220")
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )

    def service_create(self, type = "remote", server_ip = None ):     
        cmd = "mng create"
        cmd += (" -type %s"  % type)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )

                 

    '''def service_delete(self):
        cmd = "%s service delete" % self._name
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        if 'ERROR' in data:
            raise Exception( data )
    '''

    def transmit(self,property,valAndType,sleepFlag):
        #mib service-(common to all)
        cmd = 'mng mibApi test'
        #get or set
        cmd += ("%s" % property)
        #the specific variables
        size = len(valAndType)
                
        if valAndType[0]=="regular" and size==2:
            cmd += (" -type%d " % i ) 
            cmd += ("%s " % valAndType[i] )
            cmd += ("%s" % valAndType[i+1] )
            cmd += ("%s" % valAndType[i+2] )
            cmd += (" -value%d " %i) 
            data = self._if.send_command(cmd)
            data = self._if.read_until_prompt()
            return data
        index = 0 
        for i in range(0,size,2):
            index += 1
            cmd += (" -type%d " % index) 
            cmd += ("%s " % valAndType[i])
            cmd += (" -value%d " % index) 
            cmd += ("%s" % valAndType[i+1])
        data = self._if.send_command(cmd)
        if sleepFlag and property == "Get":
            time.sleep(60)
        data = self._if.read_until_prompt()
        
        return data

    def read_counters(self):

        cnts = dict()
        cmd = "%s counters print" % self._name
        data1 = self._if.send_command(cmd)
        
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
 
class dot4(object):

    def __init__(self, interface):
        super(dot4, self).__init__()
        self._if = interface
        self._name = "dot4"
    
    def dot4_channel_start(self, request):
        cmd = "link dot4 start_ch" 
        cmd += (" -if_index %s" % request[0]) 
        cmd += (" -ch_id %s" % request[1])
        cmd += (" -slot_id %s" % request[2]) 
        cmd += (" -op_class %s" % request[3]) 
        cmd += (" -imm_acc %s" % request[4]) 
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data

    def dot4_channel_end(self,if_index, ch_num):
        #link dot4 end_ch -if_index 1 -ch_id 172
        cmd = "link dot4 end_ch"
        cmd += (" -if_index %s" % if_index)
        cmd += (" -ch_id %s" % ch_num)
        self._if.send_command(cmd)
        data = self._if.read_until_prompt( timeout  = 1)
        return data

    def transmit(self, frames = 1, rate_hz = 1,payload_len = None, tx_data = None, 
                 dest_addr = None,  user_priority = None, data_rate = None, power_dbm8 = None, op_class = None, channel_num = None, time_slot = None):
        cmd = "link socket tx"
        cmd += (" -frames %d"  % frames)
        cmd += (" -rate_hz %d"  % rate_hz) if not rate_hz is None else ""
        if tx_data == None and payload_len == None:
            payload_len = 50
        cmd += (" -payload_len %s"  % payload_len) if not payload_len is None else ""
        cmd += (" -tx_data %s"  % tx_data) if not tx_data is None else ""
 
        cmd += (" -user_priority %d"  % user_priority) if not user_priority is None else ""
        cmd += (" -data_rate %d"  % data_rate) if not data_rate is None else ""
        cmd += (" -power_dbm8 %d"  % power_dbm8) if not power_dbm8 is None else ""
        cmd += (" -op_class %s"  % op_class) if not op_class is None else ""
        cmd += (" -ch_idx %d"  % channel_num) if not channel_num is None else ""
        
        cmd += (" -time_slot %s"  % time_slot) if not time_slot is None else ""
        self._if.send_command(cmd, False)
        
    def receive(self, frames, timeout = None, print_frame = None, channel_num= None,op_class = None,
                time_slot = None,power_dbm8 = None):
        cmd = "link socket rx -frames %s" % frames
        cmd += (" -print %s"  % print_frame) if not print_frame is None else ""
        cmd += (" -ch_idx %d"  % channel_num) if not channel_num is None else 0
        cmd += (" -op_class %d"  % op_class) if not op_class is None else 0
        cmd += (" -power_dbm8 %d"  % power_dbm8) if not power_dbm8 is None else 0
        cmd += (" -time_slot %s"  % time_slot) if not time_slot is None else ""
        cmd += (" -timeout_ms %s"  % timeout) if not timeout is None else ""
        self._if.send_command(cmd)
        return cmd

    def erroneous_transmit(self, frames = 1, rate_hz = 1,payload_len = None, tx_data = None, 
                 dest_addr = None,  user_priority = None, data_rate = None, power_dbm8 = None, op_class = None, channel_num = None, time_slot = None):
        cmd = "link socket tx"
        cmd += (" -frames %d"  % frames)
        cmd += (" -rate_hz %d"  % rate_hz) if not rate_hz is None else ""
        if tx_data == None and payload_len == None:
            payload_len = 50
        cmd += (" -payload_len %s"  % payload_len) if not payload_len is None else ""
        cmd += (" -tx_data %s"  % tx_data) if not tx_data is None else ""
 
        cmd += (" -user_priority %d"  % user_priority) if not user_priority is None else ""
        cmd += (" -data_rate %d"  % data_rate) if not data_rate is None else ""
        cmd += (" -power_dbm8 %d"  % power_dbm8) if not power_dbm8 is None else ""
        cmd += (" -op_class %s"  % op_class) if not op_class is None else ""
        cmd += (" -ch_idx %d"  % channel_num) if not channel_num is None else ""
        
        cmd += (" -time_slot %s"  % time_slot) if not time_slot is None else ""
        self._if.send_command(cmd, False)
        data = self._if.read_until_prompt( timeout  = 1)
        return cmd + data








       

class qaCliApi(object):
    """
    @class QaCli
    @brief QA CLI Implementation for python
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """

    def __init__(self, version = "", cpu = 'arm'):
        self._if = interface.QaCliInterface()

        self.cpu_type = cpu

        if self.cpu_type == 'arc1':
            self._if.prompt = common.DEFAULT_PROMPT_ARC % 1
        elif self.cpu_type == 'arc2':
            self._if.prompt = common.DEFAULT_PROMPT_ARC % 2

        self.timeout = common.DEFAULT_TIMEOUT # set default timeout 
        self._buffer = "" # history buffer for telnet
        self.port = common.DEFAULT_PORT
        self.server = ""
        self.cli_addr = ""
        self.version = version
        self.is_connected = False

        # declare modules
        self.link = linkApi( self._if)
        self.can = canApi( self._if)
        self.nav = navApi( self._if )
        self.ecc = eccApi( self._if )
        self.wlanMib = wlanMibApi( self._if)
        self.dot4 = dot4(self._if)
        self.register = Register(self._if)
        
    def __del__(self):
        self.link = None
        self.can = None
        self.nav = None
        self.ecc = None
        self.wlanMib = None

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
        self._if.interface().flush_buffer()
        self._if.send_command('exit')
        self._if.disconnect()
        self.is_connected = False

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

    def set_user_context ( self, address ):
        """ Set already active context to a new connection """
        self._if.send_command("uc set -addr {}".format( address ) )

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

    def cmd_loopback(self, type, lpbk_info, print_frames = 0 ):
        # loopback ip -port 8020 -server_ip 10.10.1.131 [-server_port 8020 = port as default]
        if 'udp' in type:
            ip, port = lpbk_info
            cmd = "loopback udp -port %d -server_ip %s -print %d" %  (port, ip, print_frames)

        elif 'raw' in type:
            da = lpbk_info
            cmd = "loopback raw -da %s" %  (da)
        else:
            raise TypeError("Loopback type shuld be either udp or raw")

        addr = self._if.send_command(cmd)

    def get_version(self):

        sdk_ver = ''
        uboot_ver = ''
        gnss_ver = ''

        if self.uut.external_host is u'':
            self._if.send_command('show version sdk')
            versions = {}
            rc = self._if.read_until_prompt()
            if len(rc): 
                rc = rc.replace('\r\n' ,'').split(',')
                # SDK: sdk-4.3.0-beta7-mc, U-BOOT: U-Boot 2012.04.01-atk-1.1.3-00526-g19cc217 (Nov 13 2014 - 10:13:42)
                try:
                    sdk_ver = rc[0].split(':')[1].strip()
                    uboot_ver = rc[1].split(':')[1].strip()
                    gnss_ver = rc[2].split(':')[1].strip().split(' ')[0]
                except Exception as e:
                    pass
        else:
            cmd = "link get_info about_sdk"
            self._if.send_command(cmd)
            rc = self._if.read_until_prompt()
            rc = rc.replace('\r\n' ,'').split(',')
            sdk_ver = rc[0].split("Software version:")[1].split('Device')[0]
            
        versions = {'sdk_ver': sdk_ver, 'uboot_ver' : uboot_ver, 'gnss_ver' : gnss_ver }

        return versions

    def create_remote_transport_layer(self):
        # timeout = 0 cancel the timeout
        cmd = "remote transport create -ip_addr {}".format( self.uut.ip )
        data = self._if.send_command(cmd)
        if 'ERROR' in data:
            raise Exception( data )
        





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

