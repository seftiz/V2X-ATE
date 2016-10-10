from lib import globals, setup_consts, interfaces
from tests import common
from utilities.rx_iq_imbalance_cal import IQImbalance
from utilities import utils
from lib.instruments import power_control
import time, logging
import numpy as np


log = logging.getLogger(__name__)

class CalibrationTestsRX_iq_imbalance(common.ParametrizedTestCase):
    """ 
    Class: CalibrationTestsRX_iq_imbalance
    Brief: RX IQ imbalance calibration, output: 2 registers values in hex
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """

    def __init__(self, methodName = 'runTest', param = None):
        super(CalibrationTestsRX_iq_imbalance, self).__init__(methodName, param)
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

        if globals.setup.instruments.power_control is None:
            raise globals.Error("Power control is not initilized, please check your configuration")

        self.power_control = globals.setup.instruments.power_control

        # Get RF switch handle from setup
        log.info("RF switch configuration")
        if globals.setup.instruments.rf_switch_box is None:
           raise globals.Error("RF switch is not initilized, please check your configuration")
        
        # Get pointer to object
        self.rf_switch_box = globals.setup.instruments.rf_switch_box

        # MXG/VSG select switch
        self.rf_switch_box.set_switch('A', self.param['rf_if']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        self.rf_switch_box.set_switch('B', 2) # Switch B to com 2    

        # Compensator connected/disconnected
        self.uut.managment.set_rf_frontend_enable( self.param['rf_front_end_compensator'], self.rf_if )

        # Set frequency
        self.uut.managment.set_rf_frequency( self.ch_freq, self.rf_if )

        # Set RF OFDM channel bandwidth 10/20MHz
        self.uut.managment.set_rf_ofdm_chan_bandwidth( self.bandwidth, self.rf_if )

        # Calcilate Initial power (Pin) for the test, Pin should be -60dBm during the calibration
        init_tx_power = self.consts.common['RX_IQ_IMBALANCE_INIT_PIN_POWER_DBM'] + self.consts.common['RX_PATH_SETUP_ATTENUATION_DB'+"_" + str( self.rf_if) + "_" + self.param['board_type']]

        # Configure transmitter settings and start tranmission
        self.vsg.vsg_settings( self.param['ch_freq'], init_tx_power ) 
        
        print >> self.result._original_stdout, "\nWaiting for loading file to vsg.. "
        self.vsg.load_file( self.param['test_data_dir'], self.param['data_waveform'], self.param['bandwidth'] )


    def test_rx_iq_imbalance(self):
        #print "\n..............Start RX IQ imbalance calibration test --------------"

        self.initialization()
        
        log.info('!^START TEST : rf_if {}, freq {}'. format( self.rf_if ,self.param['ch_freq']) )
        
        # Excecute RX IQ imbalance script, it is based on mathematical calculations and measurements values of dedicated registers
        # Before the calculations, we need configure the phase and amplitude registers to default values
        # EVM measurement serves us as an indicator for calibration correction, for this purpose we need to measure initial EVM 
        # Old implementation: The function Run() returns 3 values with calibration values (valA,valB,valC), New implementation: self.fw_cli.rx_iq_imbalance_calibrate
        # Finally we measure final EVM after the calibration
        #iq = IQImbalance() # create object
        try:
            #iq.Open(self.fw_cli,  self.rf_if)
            self.vsg.rf_enable( True )
            reg_value = self.consts.register['RX_IQ_IMBALANCE_AMPL_REG_VALUE_HEX']
            # Special case for board type
            if ( self.rf_if == 1 ) and (self.param['board_type'] == "ATK22027"):
                reg_value = 0x300

            self.fw_cli.set_reg( ('phy' + str(self.rf_if), self.consts.register['RX_IQ_IMBALANCE_AMPL_REG_HEX']), reg_value)       # set to default value
            self.fw_cli.set_reg(('phy' + str( self.rf_if), self.consts.register['RX_IQ_IMBALANCE_PHASE_REG_HEX']), self.consts.register['RX_IQ_IMBALANCE_PHASE_REG_VALUE_HEX']) # set to default value
            

            valA = self.fw_cli.get_reg( ("phy"+str( self.rf_if), self.consts.register['RX_IQ_IMBALANCE_AMPL_REG_HEX']))
            valB_C = self.fw_cli.get_reg( ("phy"+str( self.rf_if), self.consts.register['RX_IQ_IMBALANCE_PHASE_REG_HEX']))

            # Report on initilal register value
            log.info( "Initial RX IQ imbalance registers settings (0x14c, 0x14d) = ({}, {}), macIf = {}".format( hex(valA), hex(valB_C), self.rf_if ) )

            results_dict = self.fw_cli.get_rssi( self.rf_if + 1, self.consts.common['EVM_AVERAGE_CNT'], 10 )
            rssi_average = results_dict.get('rssi')[1]     # Average RSSI
            evm_average = results_dict.get('evm')[1]       # Average EVM

            #print "Average RSSI = %sdBm, EVM = %sdB\n"  % (rssi_average,evm_average)
            log.info("Initial RX EVM: {}".format( evm_average ))
            
            # Stop packet transmission
            self.vsg.rf_enable( False )

            # Return list of 3 values, for resitesrs A,B,C
            #iq_res = iq.Run(10,2)
            self.uut.close_fw_cli() 

            # Due to SDK issue http://jira.il.auto-talks.com:8080/jira/browse/AT-4465 we must reboot the board here
            # Reboot board and initialize
            #self.fw_cli.reboot()
            time.sleep(45)
            self.initialization()

            # Perform RX iq imbalance calibration
            self.fw_cli.rx_iq_imbalance_calibrate( self.rf_if + 1 )   #rf if 1/2

            # Get 0x14c and 0x14d phy registers after the callibration
            valA_after_cal = self.fw_cli.get_reg( ("phy"+str( self.rf_if), self.consts.register['RX_IQ_IMBALANCE_AMPL_REG_HEX']))
            valB_C_after_cal = self.fw_cli.get_reg( ("phy"+str( self.rf_if), self.consts.register['RX_IQ_IMBALANCE_PHASE_REG_HEX']))

            # Restart packet transmission
            self.vsg.rf_enable( True )
            
            # Read RSSI and EVM
            results_dict = self.fw_cli.get_rssi( self.rf_if,self.consts.common['EVM_AVERAGE_CNT'] )
            rssi_average = results_dict.get('rssi')[1]     # Average RSSI
            evm_average = results_dict.get('evm')[1]       # Average EVM
            
            self.add_limit( "Rx EVM (db)", self.consts.expected['EXPECTED_RX_EVM_LIMIT_DB'], float(evm_average), None , 'GE') 

            #if ( iq_res[0] and iq_res[1] and iq_res[2] ) and float(evm_average) < self.consts.expected['EXPECTED_RX_EVM_LIMIT_DB']:
            if float(evm_average) < self.consts.expected['EXPECTED_RX_EVM_LIMIT_DB']:
                log.info ('Status: PASS')
            else:
                log.info ('Status: FAIL')

            print >> self.result._original_stdout, "\nFinal RX EVM: {} ".format( evm_average )
            log.info('Test RSSI: ' + str(rssi_average))
            log.info('Final RX EVM: '+ evm_average)


        except Exception as err:
            raise Exception("Failed..%s" %err)
            log.info ('Measurements failed, Status: FAIL')
        

        # Stop packet transmission
        self.vsg.rf_enable( False )
              
        # Update results in calibration file
        #self.rx_balance_phase = str(hex( iq_res[1]<<16 | iq_res[2]) )       # connect valB and valC 
        rx_balance_phase = valB_C_after_cal       # connect valB and valC 
        self.add_limit( "Rx IQ Imbalance phase", valB_C, rx_balance_phase, None, 'NE' ) 

        #self.rx_balance_gain = str( hex(iq_res[0]) )
        rx_balance_gain = valA_after_cal
        self.add_limit( "Rx IQ Imbalance gain", valA, rx_balance_gain, None, 'NE' ) 

        # Delete iq object
        #del iq

        # Save the tests results to uboot 
        uboot_rx_balance = "rx_" + str( self.rf_if ) + '_balance_'
        uboot_rx_balance_phase = uboot_rx_balance + 'phase'
        uboot_rx_balance_gain = uboot_rx_balance + 'gain'
        try:
            self.uboot.reboot()

            d = { uboot_rx_balance_phase : hex( rx_balance_phase ), uboot_rx_balance_gain : hex( rx_balance_gain ) }
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

        # Write results to log file                    
        log.info( "Phy Registers,  0x14d: {}, 0x14c: {}".format( hex( rx_balance_phase ), hex( rx_balance_gain ) ) )
        log.info( "Test finished" )
