from lib import globals, setup_consts, interfaces
from tests import common
from utilities import utils
from lib.instruments import power_control
import time, logging, traceback
import numpy as np

log = logging.getLogger(__name__)

class CalibrationTestsRxSampleGain(common.ParametrizedTestCase):
    """
    Class: CalibrationTestsRX_sample_gain
    Brief: RX sample gain calibration, output: 3 values in dB converted to hex and prepared for relevant registers settings (phy 0x15a/15b registers)
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """
    def __init__(self, methodName = 'runTest', param = None):
        super(CalibrationTestsRxSampleGain, self).__init__(methodName, param)
        self.rf_if = self.param['rf_if']

    def setUp(self):
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

    def tearDown(self):
        self.uut.close_fw_cli()

    def initialization(self):
        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self._uut_id[0])
            self.uut.create_fw_cli()                                # create cli connection for (23,1123,terminal)
            self.fw_cli = self.uut.fw_cli('23')                     # get cli from telnet port 23
            self.uboot = self.uut.fw_cli('terminal').u_boot
            self.consts = setup_consts.CONSTS[globals.setup.station_parameters.station_name]
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

        # Get Signal tester VSG/MXG handle from setup
        log.info("Signal tester VSA/VSG/MXG configuration")
        if globals.setup.instruments.rf_vector_signal is None:
            raise globals.Error("Signal tester is not initilized, please check your configuration")

        self.vsg = globals.setup.instruments.rf_vector_signal['vsg']

        # Get RF switch handle from setup
        log.info("RF switch configuration")
        if globals.setup.instruments.rf_switch_box is None:
           raise globals.Error("RF switch is not initilized, please check your configuration")
        
        # Get pointer to object
        self.rf_switch_box = globals.setup.instruments.rf_switch_box

        # MXG/VSG select switch
        self.rf_switch_box.set_switch('A', self.param['rf_if']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        self.rf_switch_box.set_switch('B', 2) # Switch B to com 2 

        if globals.setup.instruments.power_control is None:
            raise globals.Error("Power control is not initilized, please check your configuration")

        self.power_control = globals.setup.instruments.power_control

        # Set frequency
        self.uut.managment.set_rf_frequency( self.param['ch_freq'], self.rf_if )

        # Compensator connected/disconnected
        self.uut.managment.set_rf_frontend_enable( self.param['rf_front_end_compensator'], self.rf_if )
       
        print >> self.result._original_stdout, "\nWaiting for loading file to vsg.. "
        self.vsg.load_file( self.param['test_data_dir'], self.param['data_waveform'], self.param['bandwidth'] )
        self.vsg.rf_enable( True )

    def test_rx_sample_gain(self):        
        #self.skipTest("Skip over the rest of the routine")
        self.initialization()
           
        log.info('Start Sample Gain test')
        log.info( "Channel frequency:" + str( self.param['ch_freq'] ) )
        
        # Calculate transmission tx power for a measurements areas, depends on setup attenuation by board type
        selected_btype_attenuation = self.consts.common[ 'RX_PATH_SETUP_ATTENUATION_DB' + "_" + str( self.rf_if ) + "_" + self.param['board_type'] ]
        select_meas_area_tx_power = { "STRONG": None, "MID": None, "WEAK": None }      # LNA off Mixer off, LNA off Mixer on, LNA on Mixer on
        for area, power in select_meas_area_tx_power.iteritems():
            power = self.consts.common[ area + '_PACKETS_AREA_DBM' ] + selected_btype_attenuation   # actual setup
            select_meas_area_tx_power[ area ] = power
        
        
        #Settings phy registers to default values
        self.fw_cli.set_reg(('phy' + str(self.rf_if), self.consts.register['RX_SAMPLE_GAIN_REG_LOW_PART_HEX']), 0x0)
        self.fw_cli.set_reg(('phy' + str(self.rf_if), self.consts.register['RX_SAMPLE_GAIN_REG_HIGHMID_PART_HEX']), 0x0)
        
        #Read Backoff compensation configuration
        backoff_index = hex( self.fw_cli.get_reg( ( 'phy' + str( self.rf_if ), self.consts.register[ 'BACKOFF_COMP_REG_HEX' ] ) ) )
        backoff_comp = int( backoff_index, 16 )*6   # Backoff compensation index*6 = attenuation compensation in dB
        log.info( "Backoff compensation = {}".format(backoff_comp ))
        

        # Start transmitting packets and measure RSSI
        sg_dict = {}    # the dictionary will collect measured deltas
        results_collect = {} # report results dictionary

        for area, power in select_meas_area_tx_power.iteritems():
            # Start transmission
            self.vsg.vsg_settings( self.param['ch_freq'], power )
            expected_rssi = power - float( selected_btype_attenuation )
            log.info( "Expected RSSI (dBm) = {}".format( expected_rssi ) )

            # Get measured DUT Pin(RSSI, EVM)     
            results_dict = self.fw_cli.get_rssi( self.rf_if + 1, self.consts.common['EVM_AVERAGE_CNT'], 10 )     # timeout = 10sec
            rssi_average = results_dict.get('rssi')[1]     # Get Average RSSI from statistics
            evm_average = results_dict.get('evm')[1]       # Get Average EVM from statistics
            log.info( "Average RSSI = %sdBm, EVM = %sdB"  % (rssi_average,evm_average))
            
            # Sample gain calculation dB
            sample_gain = float(rssi_average) - expected_rssi  # sample gain delta = measured - expected
            sg_dict.update( { area: sample_gain } )            # updating measurements in dictonary 

        #Stop transmission
        self.vsg.rf_enable( False )

        # Convert measured diff deltas in dB to (11,3) format
        sg_converted_dict = {}
        for key, value in sg_dict.iteritems():
            sg_converted_dict.update({ key : hex(utils.dB_to_11_3(value))})
      
        #Logging
        log.info ('Measured SampleGain low: {}, mid: {}, high :{}'.format(sg_dict["STRONG"], sg_dict["MID"], sg_dict["WEAK"]))
        log.info ('Measured SampleGain (11,3) format low: {}, mid: {}, high :{}'.format(sg_converted_dict["STRONG"], sg_converted_dict["MID"], sg_converted_dict["WEAK"]))

        # Checking status Sample gain range 
        if (self.consts.expected['START_RANGE_DB'] <= (sg_dict["STRONG"] or sg_dict["MID"] or sg_dict["WEAK"]) <= self.consts.expected['END_RANGE_DB']):
            log.info('Status: PASS')
        else:
            log.info('Sample Gain value range fail.Status: FAIL')
        
        # Update dict
        results_collect.update(utils.file_to_dict( self.param['final_report_file'] ))

        # Add measurements to report
        for key in sg_dict:
            self.add_limit( "ch_"+str(self.rf_if) + " " + key + " sample Gain value [dB]" , self.consts.expected['START_RANGE_DB'] , sg_dict[key], self.consts.expected['END_RANGE_DB'] , 'GELE')
            results_collect.update( { "ch_"+str(self.rf_if) + " "+ key + " sample Gain value [dB, hex]" : [ format(float(sg_dict[key]),'0.2f'), sg_converted_dict[key] ] } )
            #utils.update_dict_in_file( self.param['final_report_file'], key + " sample Gain [dB, hex]", [ format(float(sg_dict[key]),'0.2f'), sg_converted_dict[key] ] )
            
        utils.dict_to_file( results_collect, self.param['final_report_file'] )

        # -------------Set and save Uboot params-----------------------
        uboot_sample_gain_high = "ch_"+str(self.rf_if)+"_sample_gain_high"
        uboot_sample_gain_mid = "ch_"+str(self.rf_if)+"_sample_gain_mid"
        uboot_sample_gain_low = "ch_"+str(self.rf_if)+"_sample_gain_low"
        
        # Rebooting board and save parameters
        log.info("Rebooting board and save parameters")

        try:
            self.uboot.reboot()
            d = { uboot_sample_gain_high : sg_converted_dict["STRONG"], uboot_sample_gain_mid : sg_converted_dict["MID"], uboot_sample_gain_low : sg_converted_dict["WEAK"] }
            for k, v in d.iteritems():
                self.uboot.set_value( str(k), str(v) )
            self.uboot.save()

        except Exception as e:
            raise Exception("{}, failed to save uboot parameters".format( e ))
        finally:
            try:
                # Reset board
                self.uboot.reset()
            except Exception as err:
                #traceback.print_exc()
                raise Exception("{}, failed to reset board".format( err ))

        log.info("Test finished ")
