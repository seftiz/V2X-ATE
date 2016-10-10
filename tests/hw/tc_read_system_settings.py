from lib import globals, setup_consts, interfaces
import time
import re
from utilities import utils
from tests import common
import logging


log = logging.getLogger(__name__)

class ReadSystemRegistersSettings(common.ParametrizedTestCase):
    """
    Class: ReadSystemRegistersSettings
    Brief: Registers setttings validation test, output: status of registers settings
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """
    def __init__(self, methodName = 'runTest', param = None):
        super(ReadSystemRegistersSettings, self).__init__(methodName, param)
        self.rf_if = self.param['rf_if']

    def setUp(self):
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self._uut_id[0])
            self.uut.create_fw_cli()                                # create cli connection for (23,1123,terminal)
            self.fw_cli = self.uut.fw_cli('23')                     # get cli from telnet port 23
            self.consts = setup_consts.CONSTS[globals.setup.station_parameters.station_name]
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

    def tearDown(self):
        self.uut.close_fw_cli()

    def initialization(self):
        self.subsystems_to_pull = ( setup_consts.AGC_SETTINGS, setup_consts.BACKOFF_COMPENSATION, )
        self.display_full_report = True
        self.fix_enable = False

    def test_check_parameter(self):
        
        self.initialization()
        
        for subsystem in self.subsystems_to_pull:
            for parameter in subsystem:
                name = parameter['name']
                list = []
                if parameter['type'] == 'reg':
                    subsys = parameter['location']['subsys']
                    reg_addr = parameter['location']['reg_addr']
                    bitmask = parameter['location']['bitmask']
                    comment = parameter['comment']

                    reg_val = self.fw_cli.get_reg( ( subsys + str(self.rf_if), reg_addr ) )
                    valuesRange = parameter['valuesRange']
                    actualValue = reg_val & bitmask

                    notInRange = (actualValue not in valuesRange)
                    if notInRange:
                        print >> self.result._original_stdout, "Unexpected Parameter: "+name+": expected values: "+str([hex(i) for i in valuesRange])+" configured: "+hex(actualValue)
                        if self.fix_enable:
                            self.fix_parameter(parameter, fix_value)
                        else:
                            print >> self.result._original_stdout, "No change"
                    else:
                        self.display_warning(actualValue, valuesRange, name, comment)
                else:
                    log.info( "Unknown parameter type in parameter: {}".format( name ) )

    def fix_parameter(self, parameter, fix_value):
        # Not completed code
        name = parameter['name']
        list = []
        if parameter['type'] == 'reg':
            subsys = parameter['location']['subsys']
            reg_addr = parameter['location']['reg_addr']
            bitmask = parameter['location']['bitmask']
            comment = parameter['comment']

            reg_val = self.fw_cli.get_reg( ( subsys + str(self.rf_if), reg_addr ) )
            valuesRange = parameter['valuesRange']
            actualValue = reg_val & bitmask
            print >> self.result._original_stdout, "Fixing Unexpected Parameter.."
            #dut_regs.set( (subsys+'0', reg_addr), fix_value )
            self.fw_cli.set_reg( (subsys + str(self.rf_if), reg_addr), fix_value )

            reg_val = self.fw_cli.get_reg( ( subsys + str(self.rf_if), reg_addr ) )
            valuesRange = parameter['valuesRange']
            fixed_actualValue = reg_val & bitmask
            
            notInRange = (fixed_actualValue not in valuesRange)
            if notInRange:
                #log.info( "Unexpected Parameter: "+name+": expected values: "+str([hex(i) for i in valuesRange])+" configured: "+hex(fixed_actualValue) )
                log.info( "Unexpected Parameter: {}, expected value {}, configured {}".format(name, str([hex(i) for i in valuesRange]), hex(fixed_actualValue) ) )
            else:
                display_warning(fixed_actualValue, valuesRange, name, comment)
        else:
            log.info( "Unknown parameter type in parameter: {}".format( name ))
            return None

    def display_warning(self, actual_value, values_range, name, comment):
        log.info( "Parameter: {}, expected values: {}, configured: {}".format( name, str([hex(i) for i in values_range]), hex(actual_value)) )
        print >> self.result._original_stdout, "Parameter: {}, expected values: {}, configured: {}".format( name, str([hex(i) for i in values_range]), hex(actual_value))

    def readSubsystem(self,dut_regs,subsystem):
        for parameter in subsystem:
            self.checkParameter(dut_regs,parameter)



"""

if __name__ == '__main__':
    # Load configuration file
    cfg_file_name = "hw_setup_config.ini"
    current_dir = os.getcwd() # returns current working directory
    print "Tests directory: %s"  %current_dir
    cfg_dir_name = "%s\\configuration\\" % current_dir 
    utilities_dir = "%s\\utilities\\" % current_dir 
    cfg_file = os.path.join(cfg_dir_name, cfg_file_name)

    if not os.path.exists( cfg_file ):
        raise globals.Error("configuration file \'%s\' is missing." % (cfg_file) )    

    # Import telnet port from the default init file
    ConfigFileHandler = ConfigParser.RawConfigParser()
    ConfigFileHandler.read(cfg_file)   # Read file mode 
    telnet_port = ConfigFileHandler.getint("Defaults","TelnetPort2")

    ipAddr = raw_input("Enter IP addr: ")
    #ipAddr = "10.10.0.188"
    module_read = CompareParam()
    dut_regs = hwregs.open("telnet://"+ipAddr+":"+str(telnet_port))   # Telnet connection
    #dut = SSHReg(ipAddr)
    #print "SUBSYTEMS_TO_POLL: "+str(SUBSYTEMS_TO_POLL)
"""    
    
    