from lib import globals, setup_consts
from tests import common
from utilities import utils
from lib.instruments import power_control

from lib import globals, interfaces
import time, logging, traceback
from time import ctime
import numpy as np

log = logging.getLogger(__name__)



class SdkSnmpTests(common.ParametrizedTestCase):
    """
    Class: SdkSnmpTests
    Brief: SNMP Mibs fields validation, output: status
    Author: Daniel Shiper
    Version: 0.1
    Date: 02.2015
    """

    def __init__(self, methodName = 'runTest', param = None):
        super(SdkSnmpTests, self).__init__(methodName, param)
        self.rf_if = self.param['rf_if']

    def setUp(self):
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

    def tearDown(self):
        self.uut.close_fw_cli() #self.uut.self.uut.fw_cli('23')

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

        # Set rate
        self.uut.managment.set_rf_rate( self.param['snmp_rate'], self.rf_if )

        # Set packet lenght
        self.uut.managment.set_vca_frame_len( self.param['pad'], self.rf_if )
        
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
        atten = self.consts.common[ 'TX_PATH_SETUP_ATTENUATION_DB' + "_" + str( self.rf_if ) + "_" + self.param['board_type'] ] # actual setup
        self.vsa.vsa_settings(self.param['ch_freq'], self.consts.common['VSA_MAX_SIGNAL_LEVEL_DBM'], port, atten, self.consts.common['VSA_TRIGGER_LEVEL_DB'], self.consts.common['VSA_CAPTURE_WINDOW'] )
        time.sleep(0.5)

    def test_sdk_snmp_validation(self):
        log.info("Start sdk snmp valiadtion test")

        # Test initialization
        self.initialization()
               
        # Start transmiting packets from evk
        self.uut.managment.set_vca_tx_enabled( True, self.rf_if )
        time.sleep(5)

        results_collect = {} # report results dictionary
        
        print >> self.result._original_stdout, "\nStart measurements for ch_{}..".format( self.rf_if )

        # Tx path parameters measurements
        print >> self.result._original_stdout, "\nPerforming sdk snmp mibs field validation.."
        
        # Initiate dictionary of sums to zeros
        SAMPLES = 5     # number of iteration for addition delta calculation loop
        measurement = { "rmsPowerNoGap" : [], "psduCrcFail" : [], "dataRate" : [], "numPsduBytes" : [] }
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
        
        fails_list = []
        # Add measurements to report
        if self.add_limit( "ch_{} wlanMib.wlanMac.wlanMacTable wlanDefaultTxPower [dBm]".format(self.rf_if), self.param['tx_power'] - 1  , measurement ["rmsPowerNoGap"], self.param['tx_power'] + 1, 'GELE'):
            pass
        else:
            log.info( "tx_power = {}".format( measurement ["rmsPowerNoGap"] ) )
        if self.add_limit( "ch_{} wlanMib.wlanMac.wlanMacTable wlanDefaultTxDataRate [mbps]".format(self.rf_if), self.param["rate"], measurement[ "dataRate" ], self.param["rate"], 'EQ'):
            pass
        else:
            log.info( "rate = {}".format( measurement ["dataRate"] ) )
        if self.add_limit( "ch_{} iwlanMib.wlanRf.wlanRfTable wlanFrequency [MHz]".format(self.rf_if), self.param["ch_freq"], measurement[ "psduCrcFail" ], self.param["ch_freq"] , 'EQ'):
            pass    
        else:
            log.info( "channel frequency = {}".format( measurement ["psduCrcFail"] ) )
        if self.add_limit( "ch_{} vcaMib.vcaIfTable. vcaFrameLen [Bytes]".format(self.rf_if), self.param["pad"], measurement[ "numPsduBytes" ], self.param["pad"]+50 , 'GELE'):
            pass    
        else:
            log.info( "packet lengh = {}".format( measurement ["numPsduBytes"] ) )
       

        log.info("Test finished ")