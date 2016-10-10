from lib import globals, setup_consts
from tests import common

from utilities import utils
from lib.instruments.Vector_Signal import rf_vector_signal
from lib.instruments import power_control

from lib.instruments.Vector_Signal import sig_generator_mxg
from lib import globals, interfaces
import time, logging
from time import ctime
from uuts.craton import managment, fw_debug
import numpy as np
from utilities import tssi
import numpy as np

log = logging.getLogger(__name__)



class CalibrationTestsTxPowerAdjustment(common.ParametrizedTestCase):
    """
    Class: CalibrationTestsTxPowerAdjustment
    Brief: TX power adjustment and calibration, output: calibration values
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """

    def __init__(self, methodName = 'runTest', param = None):
        super(CalibrationTestsTxPowerAdjustment, self).__init__(methodName, param)
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

        # Get RF switch handle from setup
        log.info("RF switch configuration")
        if globals.setup.instruments.rf_switch_box is None:
           raise globals.Error("RF switch is not initilized, please check your configuration")
        
        # Get pointer to object
        self.rf_switch_box = globals.setup.instruments.rf_switch_box

        # VSA select switch
        self.rf_switch_box.set_switch('A',self.param['rf_if']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        self.rf_switch_box.set_switch('B',1) # Switch B to com 1 

        # Set frequency
        self.uut.managment.set_rf_frequency( self.param['ch_freq'], self.rf_if )

        # Compensator connected/disconnected
        self.uut.managment.set_rf_frontend_enable( self.param['rf_front_end_compensator'], self.rf_if )

        # Set RF OFDM channel bandwidth
        self.uut.managment.set_rf_ofdm_chan_bandwidth( self.param["bandwidth"], self.rf_if )

        # Turn OFF TSSI before the calibration
        self.uut.managment.set_tssi_interval( 0, self.rf_if)

        # Get Signal tester VSG/MXG handle from setup
        log.info("Signal tester VSA/VSG/MXG configuration")
        if globals.setup.instruments.rf_vector_signal is None:
            raise globals.Error("Signal tester is not initilized, please check your configuration")

        self.vsa = globals.setup.instruments.rf_vector_signal['vsa']

        # VSA settings
        port = 2 # left port VSA mode
        atten = self.consts.common[ 'TX_PATH_SETUP_ATTENUATION_DB' + "_" + str( self.rf_if ) + "_" + self.param['board_type'] ] # actual setup
        self.vsa.vsa_settings(self.param['ch_freq'], self.consts.common['VSA_MAX_SIGNAL_LEVEL_DBM'], port, atten, self.consts.common['VSA_TRIGGER_LEVEL_DB'], self.consts.common['VSA_CAPTURE_WINDOW'] )
        time.sleep(0.5)

    def test_tx_power_calibration(self):
        log.info("Start TSSI calibration test")

        # Test initialization
        self.initialization()
        
        tx_power_list, detector_meas_list =[],[]
        
        # Start transmiting packets from evk
        self.uut.managment.set_vca_tx_enabled( True, self.rf_if )

        #Settings initial values to zeros
        fix_delta = 0
        res_tx_evm_all = []
        fifo_meas_status = True
        results_collect = {} # report results dictionary
                
        
        print >> self.result._original_stdout, "\nStart TSSI calibration test measurements.."
        # Get measurements for set of tx powers 10,11,12,.....,24 dBm, direction in acsending order to prevent high gain measurements issue (LUT issues in high gains)
        for iter_power in self.consts.common['TX_CAL_RANGE_DBM']:
            self.uut.managment.set_tx_power( iter_power, self.rf_if )    #Set tx power
            self.vsa.prepare_vsa_measurements()

            delta_sum = 0
            iter_indx = 5 #for delta calc
            # Fixation delta measurements
            for k in range (0,iter_indx):
                #self.vsa.prepare_vsa_measurements()
                self.vsa.vsa_capture_data(2000e-6) #sec
                self.vsa.vsa_analyze_802_11p()
                delta_sum += self.vsa.get_tx_vsa_measure('rmsPowerNoGap')

            # delta between expected input power and measured average power, fixation delta
            fix_delta = iter_power - delta_sum/iter_indx    
            
            # Set fixation for tx power, if the fixation delta out of limit, set half of value
            delta_limit = self.consts.common["TX_POW_DELTA_LIMIT_DB"]    # default 6dB
            rounded_power = round( iter_power + ( fix_delta if (abs(fix_delta) < delta_limit) else fix_delta/2 ) )
            self.uut.managment.set_tx_power( rounded_power, self.rf_if )    #Set fixed tx power 
            log.info( "Expected = {}, Measured = {}, delta = {}, rounded_power(dBm) = {}".format( iter_power, delta_sum/iter_indx, fix_delta, rounded_power))
            time.sleep(4)

            # Measurement preparing, read first 10 bits (0 to 9) of TSSI FIFO register at MAC0, also need to verify bit 31 is 0 (false), when 1 (true) the FIFO value is not valid
            fifo_meas_status = bool(self.fw_cli.get_reg(( "mac0", self.consts.register['TSSI_FIFO_HEX'][self.param['rf_if']]))&(0x80000000))
            
            # Start measurement loop
            if not fifo_meas_status:
                # Initiate dictionary of sums to zeros
                sum = { "tx_pow" : 0, "tx_evm" : 0, "tx_detector_meas": 0 }
                SAMPLES = 5     # number of iteration for addition delta calculation loop
                                
                for i in range (0,SAMPLES):          
                    self.vsa.prepare_vsa_measurements()
                    sum["tx_pow"] += self.vsa.get_tx_vsa_measure('rmsPowerNoGap')
                    sum["tx_evm"] += self.vsa.get_tx_vsa_measure('evmAll')
                    sum["tx_detector_meas"] += int(self.fw_cli.get_reg(("mac0", self.consts.register['TSSI_FIFO_HEX'][self.rf_if])) & utils.bit_mask(10)) # Read first 10 bits

                # Collect the measurements                
                tx_power_list.append( sum["tx_pow"] / SAMPLES )
                detector_meas_list.append( sum["tx_detector_meas"] / SAMPLES )
                res_tx_evm_all.append( sum["tx_evm"] / SAMPLES )

                fifo_meas_status = True                       
            else:
                log.info("TSSI FIFO not valid!")

        # Reverse list for TX power adjustment function calculations
        tx_power_list = tx_power_list[::-1]     
        detector_meas_list = detector_meas_list[::-1]
        res_tx_evm_all = res_tx_evm_all[::-1]
        print >> self.result._original_stdout, "\nMeasured tx_power_list: {}".format( tx_power_list )
        print >> self.result._original_stdout, "\nMeasured detector_meas_list: {}".format( detector_meas_list )
        print >> self.result._original_stdout, "\nMeasured res_tx_evm_all: {}".format( res_tx_evm_all )

        # TX power adjustment function, returns the final vector for an antenna power LUT
        calib_pant_lut_vector_list = tssi.adjust_tx_power( self.rf_if, detector_meas_list, tx_power_list )
        print >> self.result._original_stdout, "\nMeasured pant_lut_vector: {}".format( calib_pant_lut_vector_list )

        log.info("tx_power_list): {:s}".format(str(tx_power_list)))
        log.info("detector_meas_list: {:s}".format(str(detector_meas_list)))
        log.info("Final vector_list ch{}: {}".format( self.rf_if, calib_pant_lut_vector_list ))
        results_collect.update(utils.file_to_dict( self.param['final_report_file'] ))
        results_collect.update( { "pant_lut_vector_" + str(self.rf_if+1): calib_pant_lut_vector_list } )


        # Stop transmiting packets from evk
        self.uut.managment.set_vca_tx_enabled( False, self.rf_if )

        utils.dict_to_file( results_collect, self.param['final_report_file'] )

        #Set uboot params
        assert(self.rf_if in (0, 1))
        ch_pant_lut_index = "ch_"+str(self.rf_if)+"_pant_lut_index"
        #pant_lut_vector_1 = "pant_lut_vector_1"
        #pant_lut_vector_2 = "pant_lut_vector_2"
        #pant_lut_vector_3 = "pant_lut_vector_3"
        #pant_lut_vector_4 = "pant_lut_vector_4"

        pant_lut_vector = { 1: "pant_lut_vector_1", 2: "pant_lut_vector_2", 3: "pant_lut_vector_3" , 4: "pant_lut_vector_4" }
        try:
            self.uboot.reboot()

            d = { ch_pant_lut_index : self.rf_if+1 }
            for k, v in d.iteritems():
                self.uboot.set_value( str(k), str(v) )

            if self.rf_if == 0:
                self.uboot.set_value( pant_lut_vector[1], calib_pant_lut_vector_list )
            elif self.rf_if == 1:
                self.uboot.set_value( pant_lut_vector[2], calib_pant_lut_vector_list )
        
            self.uboot.save()

        except Exception as e:
            raise Exception("{}, failed to save uboot parameters".format( e ))
        finally:
            try:
                # Reboot the board and wait for valid PROMT
                print >> self.result._original_stdout, "Rebooting.."
                self.uboot.reset()  
            except Exception as err:
                #traceback.print_exc()
                raise Exception("{}, failed to reset board".format( err ))

        # Tx power validation after the calibration
        print >> self.result._original_stdout, "\nPerforming rebooting and validation after the tx power calibration.."
        # Start transmiting packets from evk
        self.uut.managment.set_tx_power( 20, self.rf_if )    #Set tx power to 20dBm
        self.uut.managment.set_rf_frequency( self.param['ch_freq'], self.rf_if ) #Set frequency
        self.uut.managment.set_vca_tx_enabled( True, self.rf_if )
        time.sleep(5)

        SAMPLES_CHECK = 10
        SUM_CHECK = 0
        tx_power_meas_check = None
       
        for j in range (0,SAMPLES_CHECK):          
            self.vsa.prepare_vsa_measurements()
            SUM_CHECK += self.vsa.get_tx_vsa_measure('rmsPowerNoGap')
            time.sleep(0.5)
        try:
            tx_power_meas_check = float(format(( SUM_CHECK / SAMPLES_CHECK ),'0.2f'))
        except:
            raise ArithmeticError( "tx power measurements failed" )
        log.info( "Validation, TX power @20dBm = %sdBm" %str( tx_power_meas_check ) )
        print >> self.result._original_stdout, "Validation, TX power @20dBm = {}dBm".format( tx_power_meas_check ) 
        
        # Add measurements to report
        self.add_limit( "ch_"+str(self.rf_if) + " tx power @20 [dBm]", self.consts.expected['EXPECTED_TX_POWER_LOW_DBM'] , tx_power_meas_check, self.consts.expected['EXPECTED_TX_POWER_HIGH_DBM'] , 'GELE')
        log.info(" Test finished ")
