from lib import globals, setup_consts, interfaces
from tests import common
from utilities import utils
from lib.instruments import power_control
import time, logging, traceback
from time import ctime
import numpy as np

log = logging.getLogger(__name__)


class TXpathTests(common.ParametrizedTestCase):
    """
    Class: TXpathTests
    Brief: TX path parameters - power, tx evm, freq error, lo leakage measurements, output: results of measured values
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """

    def __init__(self, methodName = 'runTest', param = None):
        super(TXpathTests, self).__init__(methodName, param)
        self.rf_if = self.param['rf_if']

    def setUp(self):
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

    def tearDown(self):
        self.uut.close_fw_cli()

    def initialization(self):

        self.status_tx_power = False
        self.status_tx_evm = False
        self.status_tx_iq_ampl_imbalance = False
        self.status_tx_iq_phase_imbalance = False
        self.status_dc_lo_leakage = False
        self.status_freq_error = False
        self.status_sym_clock_error = False


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

        # Set rate
        self.uut.managment.set_rf_rate( self.param['snmp_rate'], self.rf_if )
        
        # Compensator connected/disconnected
        self.uut.managment.set_rf_frontend_enable( self.param['rf_front_end_compensator'], self.rf_if )

        # Set tx power
        self.uut.managment.set_tx_power( self.param['tx_power'], self.rf_if )    #Set tx power to 20dBm

        # Set RF OFDM channel bandwidth
        self.uut.managment.set_rf_ofdm_chan_bandwidth( self.param["bandwidth"], self.rf_if )

        # Get Signal tester VSG/MXG handle from setup
        log.info("Signal tester VSA/VSG/MXG configuration")
        if globals.setup.instruments.rf_vector_signal is None:
            raise globals.Error("Signal tester is not initilized, please check your configuration")

        self.vsa = globals.setup.instruments.rf_vector_signal['vsa']

        # VSA settings
        port = 2 # left port VSA mode
        atten = self.consts.common[ 'TX_PATH_SETUP_ATTENUATION_DB' + "_" + str( self.rf_if ) + "_" + self.param['board_type'] ] 
        self.vsa.vsa_settings(self.param['ch_freq'], self.consts.common['VSA_MAX_SIGNAL_LEVEL_DBM'], port, atten, self.consts.common['VSA_TRIGGER_LEVEL_DB'], self.consts.common['VSA_CAPTURE_WINDOW'] )
        time.sleep(0.5)

    def test_tx_path(self):
        log.info("Start TX path test, measurements for ch_{}, rate {}, temp {}..".format( self.rf_if, self.param["rate"], self.param['temperature'] ) )

        # Test initialization
        self.initialization()
               
        # Start transmiting packets from evk
        self.uut.managment.set_vca_tx_enabled( True, self.rf_if )
        time.sleep(5)

        
        # Update dict
        results_collect = {} # report results dictionary
        results_collect.update(utils.file_to_dict( self.param['final_report_file'] ))
       
        print >> self.result._original_stdout, "\nStart measurements for ch_{}, rate {}, temp {}..".format( self.rf_if, self.param["rate"], self.param['temperature'] )

        # Tx path parameters measurements
        print >> self.result._original_stdout, "\nPerforming Tx path parameters measurements.."

        # Initiate dictionary of sums to zeros
        SAMPLES = 10     # number of iteration for addition delta calculation loop
        measurement = { "rmsPowerNoGap" : [], "evmAll" : [], "ampErrDb" : [], "phaseErr" : [], "dcLeakageDbc" : [] , "freqErr" : [], "clockErr" : [] }
        self.vsa.prepare_vsa_measurements()

        # Measure params
        for iteration in range(0, SAMPLES): 
            for item, val in measurement.items():
                try:
                    self.vsa.vsa_capture_data(2000e-6) #sec
                    self.vsa.vsa_analyze_802_11p()
                    measurement[ item ] = np.append( measurement[ item ], self.vsa.get_tx_vsa_measure( item ) )
                except:
                    measurement[ item ] = np.append( measurement[ item ], np.nan )
                
        # Stop transmission packets
        self.uut.managment.set_vca_tx_enabled( False, self.rf_if )

        # Calculate mean of valid measurements and update the dictionary
        for k, v in measurement.items():
            measurement.update( { k : float( format(np.mean(v), '0.2f') ) } )
        
     # Add measurements to report
        fails_list = []
        self.add_limit( "temp {}C, freq {}MHz, ch_{}, rate {}[Mbps]".format( self.param['temperature'], self.param['ch_freq'], self.rf_if, self.param['rate'] ), 0, 0, 0 , 'GELE')
        self.status_tx_power = self.add_limit( "ch_{} tx power [dBm]".format(self.rf_if), self.param['tx_power'] - 1  , measurement ["rmsPowerNoGap"], self.param['tx_power'] + 1, 'GELE')
        self.status_tx_evm = self.add_limit( "ch_{} tx evm [dB]".format(self.rf_if), self.consts.expected['EXPECTED_TX_EVM_DB'], measurement[ "evmAll" ], np.nan, 'LE')
        self.status_tx_iq_ampl_imbalance = self.add_limit( "ch_{} iq imbalance amplitude error [dB]".format(self.rf_if), self.consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW_DB'], measurement[ "ampErrDb" ], self.consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH_DB'] , 'GELE')
        self.status_tx_iq_phase_imbalance = self.add_limit( "ch_{} iq imbalance phase error [deg]".format(self.rf_if), self.consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW_DEG'], measurement[ "phaseErr" ], self.consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH_DEG'] , 'GELE')
        self.status_dc_lo_leakage = self.add_limit( "ch_{} dc lo leakage [dBc]".format(self.rf_if), self.consts.expected['EXPECTED_LO_LEAKAGE_DBC'], measurement[ "dcLeakageDbc" ], np.nan, 'LE')
        self.status_freq_error = self.add_limit( "ch_{} frequency error [kHz]".format(self.rf_if), self.consts.expected['EXPECTED_TX_FREQ_ERROR_LOW_KHZ'] , (measurement[ "freqErr" ])/1e3, self.consts.expected['EXPECTED_TX_FREQ_ERROR_HIGH_KHZ'] , 'GELE')
        self.status_sym_clock_error = self.add_limit( "ch_{} symbol clock error [ppm]".format(self.rf_if), self.consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW_PPM'], measurement[ "clockErr" ], self.consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH_PPM'] , 'GELE')

        fails_list.append("tx_power = {}".format( measurement ["rmsPowerNoGap"] )) if not self.status_tx_power else log.info("status_tx_power {}".format( self.status_tx_power ))
        fails_list.append("tx evm = {}".format( measurement ["evmAll"] ) ) if not self.status_tx_evm else log.info("status_tx_evm {}".format( self.status_tx_evm ))
        fails_list.append("iq imbalance amplitude error = {}".format( measurement ["ampErrDb"] ) ) if not self.status_tx_iq_ampl_imbalance else log.info("status_tx_iq_ampl_imbalance {}".format(self.status_tx_iq_ampl_imbalance ))
        fails_list.append("iq imbalance phase error = {}".format( measurement ["phaseErr"] ) ) if not self.status_tx_iq_phase_imbalance else log.info("status_tx_iq_phase_imbalance {}".format(self.status_tx_iq_phase_imbalance ))
        fails_list.append("dc lo leakage = {}".format( measurement ["dcLeakageDbc"] ) ) if not self.status_dc_lo_leakage else log.info("status_dc_lo_leakage {}".format(self.status_dc_lo_leakage ))
        fails_list.append("frequency error = {}".format( measurement ["freqErr"] ) ) if not self.status_freq_error else log.info("status_freq_error {}".format(self.status_freq_error ))
        fails_list.append("symbol clock error = {}".format( measurement ["clockErr"] ) ) if not self.status_sym_clock_error else log.info("status_sym_clock_error {}".format(self.status_sym_clock_error ))
        
        # Collect tx meas results to file
        with open(self.param["tx_results"], "a+") as out_file:
            utils.print_and_log(out_file, "{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},".format(
                                ctime(),
                                str((self.param['temperature'])),
                                ("ch_{}").format(self.rf_if),
                                str((self.param['rate'])),
                                str(self.param['pad']),
                                str(self.param['ch_freq']),
                                str(self.param['tx_power']),
                                str(measurement ["rmsPowerNoGap"]),
                                "<"+str(self.consts.expected['EXPECTED_LO_LEAKAGE_DBC']),
                                str(measurement[ "dcLeakageDbc" ]),
                                "<"+str(self.consts.expected['EXPECTED_TX_EVM_DB']),
                                str(measurement[ "evmAll" ]),
                                str(self.consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW_DB']),
                                str(measurement[ "ampErrDb" ]),
                                str(self.consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH_DB']),
                                str(self.consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW_DEG']),
                                str(measurement[ "phaseErr" ]),
                                str(self.consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH_DEG']),
                                str(self.consts.expected['EXPECTED_TX_FREQ_ERROR_LOW_KHZ']),
                                str((measurement[ "freqErr" ])/1e3),
                                str(self.consts.expected['EXPECTED_TX_FREQ_ERROR_HIGH_KHZ']),
                                str(self.consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW_PPM']),
                                str(measurement[ "clockErr" ]),
                                str(self.consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH_PPM']),
                                str(fails_list).replace(",",";")))
        
        if self.param["calibration_enable"]:
            results_collect.update( { "ch_{} tx power@{}dBm".format(self.rf_if, self.param['tx_power']): [ measurement ["rmsPowerNoGap"], self.status_tx_power ] } )
            results_collect.update( { "ch_{} tx evm@{}dBm".format(self.rf_if, self.param['tx_power']): [ measurement[ "evmAll" ], self.status_tx_evm ] } )
            results_collect.update( { "ch_{} iq imbalance amplitude error".format(self.rf_if): [ measurement ["ampErrDb"], self.status_tx_iq_ampl_imbalance ] } )
            results_collect.update( { "ch_{} iq imbalance phase error".format(self.rf_if): [ measurement ["phaseErr"], self.status_tx_iq_phase_imbalance ] } )
            results_collect.update( { "ch_{} dc lo leakage".format(self.rf_if): [ measurement ["dcLeakageDbc"] , self.status_dc_lo_leakage ] } )
            results_collect.update( { "ch_{} frequency error".format(self.rf_if): [ (measurement ["freqErr"])/1e3 , self.status_freq_error ] } )
            results_collect.update( { "ch_{} symbol clock error".format(self.rf_if): [ measurement ["clockErr"], self.status_sym_clock_error ] } )

            utils.dict_to_file( results_collect, self.param['final_report_file'] )
        else:
            pass
        log.info("Test finished ")