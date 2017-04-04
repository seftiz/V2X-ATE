
import os, logging
from uuts.craton.cli import cli_5 as v2x_cli
from uuts import common
from uuts.craton.cli import gps
from lib import utilities, globals, interfaces
from uuts.craton import managment, fw_debug


log = logging.getLogger(__name__)


# from atlk.v2x.common import BoardsTypes

class Units(object):
    """ class holder for Multiple Units under test """
    def __init__(self):
        self.units = dict()

    def __del__(self):
        self.units = None

    def append( self, uut ):
        if uut.ip == u'':
            print "Storing uut %d" % ( uut.idx)
        else:
            print "Storing uut %d with ip %s" % ( uut.idx , uut.ip)
        self.units[str(uut.idx)] =  uut

    def __iter__(self):
        return iter(self.units.itervalues())

    def next(self):
        if not self.units:
            raise StopIteration
        return self.units.pop()

    def unit(self, idx):
        try:
            return self.units[str(idx)]
        except NameError:
            return None

    def get_versions(self):
        uut_info = []
        for id, uut in sorted( self.units.iteritems() ):
            ver_info = uut.get_uut_info()
            uut_info.append( { 'ip' : uut.ip, 'sdk-version' : ver_info['sdk_ver'], 'uboot-version' : ver_info['uboot_ver'] } )

        return uut_info

    def prepare(self, image_name = None, uboot_parameters = None ):

        for id, uut in sorted( self.units.iteritems() ):
            uut.prepare( image_name, uboot_parameters ) 

    def init(self):
        for id, uut in sorted( self.units.iteritems() ):
            if uut.ip is u'':   # craton2 device
                craton2_flag = 1;
                uut.init(craton2_flag)
            else : 
                uut.init()


    def load_uuts_from_cfg_file (self, cfg_data ):

        try:    
            units_cfg = cfg_data["units"]
        except NameError, err:
            raise Exception("Failed to retrieve units from configuration file")

        for uut_data in units_cfg:
            # verify unit is active and connected
            try:
                is_active = int( utilities.get_value(uut_data , 'active') )
            except Exception:
                is_active = 0

            if is_active != 1:
                continue

            uut_idx = int( utilities.get_value(uut_data , 'id') )
            cli_active = int( utilities.get_value(uut_data , 'cli_active') )
            uut = None
            uut = UnitUnderTest( uut_idx , utilities.get_value(  uut_data , 'ip'), cli_active, uut_data )

            rf_interfaces = utilities.get_value( uut_data , 'rf_interfaces')
            for rf_if in rf_interfaces:
                id = utilities.get_value(rf_if , 'id')
                uut.add_rf_interface( id )
                uut.rf_interfaces[id].frequency = utilities.get_value( rf_if , 'freq')
                uut.rf_interfaces[id].tx_power = utilities.get_value( rf_if , 'power')
                uut.rf_interfaces[id].link = utilities.get_value( rf_if , 'link')
                uut.rf_interfaces[id].mac_addr = utilities.get_value( rf_if , 'mac_addr')

            uut.terminal_info = utilities.get_value(  uut_data , 'terminal')

            # Get can bus information
            can_interfaces = utilities.get_value( uut_data , 'can_interfaces')
            for can_if in can_interfaces:
                id = utilities.get_value(can_if , 'id')
                # Load only active interfaces
                if ( utilities.get_value( can_if , 'active') == 1 ):
                    uut.add_can_interface( id ) 
                    uut.can_interfaces[id].active = utilities.get_value( can_if , 'active')
                    uut.can_interfaces[id].simulator = utilities.get_value( can_if , 'simulator')
                    uut.can_interfaces[id].sim_id = utilities.get_value( can_if , 'sim_id')
                    uut.can_interfaces[id].sim_port = utilities.get_value( can_if , 'sim_port')
                    uut.can_interfaces[id].device_id = int(utilities.get_value( can_if , 'device_id'), 16)

            uut.nps.id, uut.nps.port = ( utilities.get_value(uut_data , 'pc')['device'] , utilities.get_value(uut_data , 'pc')['port']  )

            # Init basic parameters
            self.append( uut )

            

            if len(uut.external_host):
                utilities.start_v2x_cli_external_host( uut.external_host )

            # Open CLI and terminal
            # uut.initilaize()


class CanInterface(object):

    def __init__(self, idx, simulator='CanBusServer', sim_id=1, sim_port=0, device_id=0):
        self.id = idx
        self.simulator = simulator
        self.sim_id = sim_id
        self.sim_port = sim_port
        self.device_id = device_id

class RfInterface(object):

    def __init__(self, idx, freq=5800, power=-20):
        self.id = idx
        self.frequency = freq
        self.tx_power = power
        self.link = ""

class uutPowerControl(object):

    def __init__(self, id = None, port = None):
        self.device = None
        self.id = id
        self.port = port

class CpuLoad(object):

    def __init__(self, uut ):
        self._uut = uut
        self.cpu_name = 'cpu_load'

    def start(self, load, timeout = 0):
        self.load = load

        self._load_cli = self._uut.create_qa_cli( self.cpu_name )
        self._load_cli.set_cli_thread_name(self.cpu_name )

        self._load_cli.cpu_load( load, timeout)

    def stop(self):
        try:
            self._uut.cli.thread_kill (self._load_cli.cli_addr)
            self._uut.cli.close_qa_cli(self.cpu_name)
        except Exception as e:
            pass

class Profiling(object): 

    def __init__(self, uut ):
        self._uut = uut
        self.profiling_name = 'profiling'
        self.results = dict()
        self.prof_cli = self._uut.create_qa_cli( self.profiling_name )
        self.prof_cli.set_cli_thread_name( self.profiling_name )

    def reset(self):
         prof_cli.prof( reset = True )

    def get_status(self):
        # Get current load
        self.results[time.strftime("%X")] =  self.prof_cli.prof()

    def __del__(self):
        self.results = None

class UnitUnderTest(object):
	
    def __init__(self, idx, ip, cli_exists = 1, uut_data = None ):
        self.idx = idx
        self.ip = ip
        self.type = ""
        self.name = ""
        self.__uut_data = uut_data
        # Load Version parameters
        self.mac_addr = utilities.get_value(uut_data , 'mac_addr') if not(uut_data == None) else "00:00:00:00:00:00"
        self.version = utilities.get_value(uut_data , 'version') if not(uut_data == None) else ""
        self.external_host = utilities.get_value(uut_data , 'external_host') if not(uut_data == None) else ""
        self.managment = None
        self.rf_interfaces = dict()
        self.terminal_info = utilities.get_value(uut_data , 'terminal') if not(uut_data == None) else None
        self.gps = gps.Gps()
        self.nps = uutPowerControl()
        self.external_host_session = ""
        self.os = utilities.get_value(uut_data , 'os') if not(uut_data == None) else ""
        self.can_interfaces = dict()
        self.__v2x_cli = {}
        self.__fw_cli = { 'terminal': None, '23': None } # , '1123' : None}
        self.cpu_load = CpuLoad(self)
        self.cpu_ports = { 'arm' : 8000, 'arc1' : 8001, 'arc2' : 8002 }

    def __del__(self):
        self.gps_stop()

        for cli in self.__v2x_cli:
            try:
                self.close_qa_cli(cli)
            except Exception as e:
                pass

    def init_managmnet(self):
        self.managment = managment.V2xManagment( self.ip, unit_version = self.version )

    def __create_terminal_connection( self ):
        if self.terminal_info is None or 'None' in  self.terminal_info:
            return None

        if (self.terminal_info['device'].encode('ascii')).upper() == 'NONE':
            return None

        cnn_info = { 'host': self.terminal_info['id'] , 'port' : self.terminal_info['port'], 'timeout_sec': 10 }
        terminal_if = interfaces.INTERFACES[ self.terminal_info['device'] ](cnn_info)
        terminal_if.open()
        # Create terminal cli
        cli = fw_debug.DebugCli( terminal_if, True )
        try:
            cli.is_alive()
        except IOError:
            raise Exception("EVK {}, Terminal port is not avaliable for host {} port {}. Please verify connection".format( self.ip, self.terminal_info['id'], self.terminal_info['port'] ) )

        terminal_if = None
        return cli

    def fw_cli(self, name = 'terminal'):
        return self.__fw_cli[name]

    def create_fw_cli( self ):

        for port in self.__fw_cli:
            if self.__fw_cli[port] is None:
 
                if 'terminal' in port:
                    self.__fw_cli[port] = self.__create_terminal_connection()
                    continue
                
                
                # handle ports 23 1123
                cnn_info = { 'host':self.ip , 'port': int(port), 'timeout_sec': 10 }
                fw_telnet = interfaces.INTERFACES['TELNET'](cnn_info)
                user_cli = fw_debug.DebugCli( fw_telnet , False )
                user_cli.interface.open()
                self.__fw_cli[port] = user_cli

    def close_fw_cli( self, port = None ):
        if port is None:
            ports = self.__fw_cli
        else: 
            ports = { self.__fw_cli[port] }


        for id, port in enumerate(ports):
            self.__fw_cli[port].close()
            self.__fw_cli[port] = None

    def get_cli_count( self ):
        """ Get Number of active cli """
        try: 
            return len(self.__v2x_cli)
        except Exception:
            return 0

    def create_qa_cli(self, cli_name, target_cpu = 'arm'):
        user_cli = v2x_cli.qaCliApi( cpu = target_cpu )
        user_cli.uut = self
        self.connect_to_cli (user_cli)
        self.__v2x_cli[cli_name] = user_cli
        return self.__v2x_cli[cli_name] 

    def close_qa_cli( self, cli_name):
        try:
            self.__v2x_cli[cli_name].disconnect()
        except Exception as e:
            pass
        finally:
            self.__v2x_cli[cli_name] = None
            del self.__v2x_cli[cli_name]

    def connect_to_cli( self, cli ):

        cli_ip = self.ip
        cli_port = self.cpu_ports[ cli.cpu_type ]

        if len(self.external_host):
            cli_ip =  self.external_host

        cli.connect( server = cli_ip, port = cli_port )

    def kill_qa_cli( self, cli_name, cli_name_to_kill ):
        try:
            # verify cli address is exists
            if len(self.__v2x_cli[cli_name_to_kill].cli_addr):
                self.__v2x_cli[cli_name].thread_kill( self.__v2x_cli[cli_name_to_kill].cli_addr )
            else:
                raise Exception('Missing cli addr to kill')
        except Exception as e:
            pass

    def qa_cli(self, cli_name):
        return self.__v2x_cli[cli_name]

    def set_cpu_load(self, load, timeout = 0):
        if load > 0:
            self.cpu_load = CpuLoad( self )
            self.cpu_load.start( load, timeout )
        elif load == 0 and not self.cpu_load is None:
            self.cpu_load.stop()
            self.cpu_load = None

    def add_rf_interface(self, id):
        try:
            self.rf_interfaces[id] = RfInterface( id )
        except Exception as e:
            pass

    def add_can_interface(self, id):
        try:
            self.can_interfaces[id] = CanInterface( id )

        except Exception as e:
            pass

    def type(self, type):
        self._type = None
        for b in BoardsTypes:
            if type in b:
                self._type = type
                return

        raise Error("Unit type is unknown, please verfiy type")

    def prepare( self, image_name = None, uboot_params = None ):

        self.create_fw_cli()

        uut_fw = self.fw_cli('terminal')
        if uut_fw is None:
            raise Exception("Error, Unable to connect to unit terminal\n. 1. Verify in the configuration file that port is defined.\n2. Verify port is not occupied by any other application.")

        uut_fw.u_boot.reboot()

        if not image_name is None:
            uut_fw.u_boot.set_value('bootcmd', "'tftp %s; bootm'" % image_name )
        
        
        if not uboot_params is None:
            for key, val in uboot_params.iteritems():
                uut_fw.u_boot.set_value( key, val )

        uut_fw.u_boot.save()
        uut_fw.u_boot.reset()

    def get_uut_info(self):

        no_qa_cli = False
        try:
            self.create_qa_cli('version')
        except Exception:
            no_qa_cli = True
        else:
            
            try:
                version_info = self.qa_cli('version').get_version()
            except Exception as e:
                pass
            finally:

                if self.external_host:
                    try:
                        self.qa_cli('version').create_remote_transport_layer()
                    except Exception:
                        pass

                self.close_qa_cli('version')

        if no_qa_cli:
            uut_fw = self.fw_cli('terminal')
            if not uut_fw is None:
                version_info =  uut_fw.get_version()
            else:
                version_info =  { 'sdk_ver' : 'Unknown', 'uboot_ver' : 'Unknown' }
                # { 'sdk-version' : 'Unknown', 'uboot-version' : 'Unknown'}

        return version_info

    def terminate(self):
        self.close_fw_cli()
        self.managment = None

    def init(self,device_type = 0):

        if not device_type :
            self.init_managmnet()        

        # Create fw cli connection
        if not device_type :
            self.create_fw_cli()

        if not device_type :
            for rf_id in self.rf_interfaces:
                rf_if = self.rf_interfaces[rf_id]
                self.managment.set_rf_frequency(  rf_if.frequency , rf_if.id )
                self.managment.set_tx_power( rf_if.tx_power , rf_if.id )







if __name__ == "__main__":

	units = Units()
	
	for i in range(10):
		my_uut = UnitUnderTest( i , "10.10.0.%d" % ( i + 100) )
		units.append( my_uut )

	# Change some uut data
	units.unit(3).ip = "255.255.255.255"
	
	for uut in units:
		print "Stored unit is %d and ip is %s" % ( uut.idx ,  uut.ip)
	print "OK"
