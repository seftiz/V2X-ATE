from lib import globals, setup_consts, interfaces
import time
import re
from utilities import utils
from tests import common
import logging


log = logging.getLogger(__name__)

class CalibrationTestsDCOCcheck(common.ParametrizedTestCase):
    """
    Class: CalibrationTestsDCOCcheck
    Brief: DCOC validation test, output: Pass/Fail if DC values not in expected range
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """
    def __init__(self, methodName = 'runTest', param = None):
        super(CalibrationTestsDCOCcheck, self).__init__(methodName, param)
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
        pass

    def test_DCOC_status(self):
        # Start DCOC status test
        
        self.initialization()

        # DAC DCOC measurements
        # DC IQ registers list selection by rf_id 0/1
        dc_iq_list = self.consts.register['RX_DC_IQ_REGS_HEX'][self.rf_if]
 
        # Description : Validation loop, get registers measurements of i and q (i-bits [15:8], q-bits[7:0]), use mask to check if value in the expected range and return status Pass/fail
        # Usage example: 
        # reg_I = (measured_register_value & 0xFF00)>>8   # extracting bits [15:8]
        # reg_Q = (measured_register_value & 0x00FF)      # extracting bits [7:0]
        
        results_collect = {}

        #Add report details to results file
        results_collect.update( { "gps_version": self.param['gps_version'] } )
        results_collect.update( { "board_IP": self.param['evk_ip'] } )
        results_collect.update( { "board_type": self.param['board_type'] } )
        results_collect.update( { "board_number": self.param['board_number'] } )
        
        for i in range(0,len(dc_iq_list)):
            # Registers measurements, returned value in hex
            rf_reg = self.fw_cli.get_reg(('rf'+str(self.rf_if), dc_iq_list[i]))

            # Mask relevant bits and extract i-bits[15:8], q-bits[7:0] using string manipulations
            DC_I = (rf_reg & 0xFF00)>>8   # extracting bits [15:8]
            DC_Q = (rf_reg & 0x00FF)      # extracting bits [7:0]

            # Checking status
            if (DC_I in range(self.consts.register['DC_RANGE_START_REG_HEX'], self.consts.register['DC_RANGE_STOP_REG_HEX'])) or (DC_Q in range(self.consts.register['DC_RANGE_START_REG_HEX'], self.consts.register['DC_RANGE_STOP_REG_HEX'])):
                dc_status_ok = Fail         
            else:
                dc_status_ok = True

            # Add results to report
            iq_name = { 'I' : DC_I, 'Q': DC_Q }
            for iq_key, reg_value in iq_name.iteritems(): 
                self.add_limit( "ch_"+str(self.rf_if) + " "+ str(hex(dc_iq_list[i])) + ", " + iq_key + " reg DC not in range" , self.consts.register['DC_RANGE_START_REG_HEX'], reg_value, self.consts.register['DC_RANGE_STOP_REG_HEX'], 'NIR')

            log.info('DCOC test, DAC register %s, value %s, status %s '%(str(hex(dc_iq_list[i])), str(hex(rf_reg)), str(dc_status_ok)))
            #print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )
            results_collect.update( { str(hex(dc_iq_list[i])):str(hex(rf_reg)) } )
            #utils.update_dict_in_file( self.param['final_report_file'], str(hex(dc_iq_list[i])), str(hex(rf_reg)))
            results_collect.update(utils.file_to_dict( self.param['final_report_file'] ))
            utils.dict_to_file( results_collect, self.param['final_report_file'] )

        # Prepare and measure DC measurements
        # Read the DC values for the wfp gain
        self.fw_cli.dcoc_wfp_timer( self.rf_if + 1, 0 ) # timeout 0
        self.fw_cli.dcoc_calibrate( self.rf_if + 1 )   #1/2
        time.sleep(5)

        # Read the DC values for [ medium, low, free agc ]
        gain_levels =  self.consts.common['DC_GAIN_LEVELS']
        for key,value in gain_levels.iteritems():
            self.fw_cli.set_reg( ('phy' + str(self.rf_if), 0x10d), value ) 
            self.fw_cli.quit_from_registers()
            time.sleep(1)
            data_string = self.fw_cli.dcoc_read_wfp(self.rf_if + 1)

            # Cleaning data string, removes all whitespaces, tabs and newlines and splitting
            dc_values = [s.strip() for s in data_string.splitlines()][0] 
            float_format = r"([-+]?\d*\.\d+|[-+]?\d+)"
            v = re.findall( float_format, dc_values )
            dc_value_real, dc_value_imag = v[0], v[1]
            log.info( 'DC values ' + key + ': ' + dc_values )
            self.add_limit( "ch_"+str(self.rf_if) + " "+ key + " gain DC value real [mV]" , -1*(self.consts.expected['EXPECTED_DC_RANGE']) , float(dc_value_real), self.consts.expected['EXPECTED_DC_RANGE'] , 'GELE')
            self.add_limit( "ch_"+str(self.rf_if) + " "+ key + " gain DC value imaginary [mV]" , -1*(self.consts.expected['EXPECTED_DC_RANGE']) , float(dc_value_imag), self.consts.expected['EXPECTED_DC_RANGE'] , 'GELE')
            results_collect.update(utils.file_to_dict( self.param['final_report_file'] ))
            results_collect.update( { "ch_"+str(self.rf_if) + " " + key + " gain [I,Q] DC value[mV]"  :[ dc_value_real, dc_value_imag ] } )
            utils.dict_to_file( results_collect, self.param['final_report_file'] )

        # Free AGC
        self.fw_cli.set_reg( ('phy' + str(self.rf_if), 0x10d), 1 )
        self.fw_cli.quit_from_registers()
        
        log.info('Test {} finished'.format( self._testMethodName ))
