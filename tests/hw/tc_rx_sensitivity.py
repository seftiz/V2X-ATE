from lib import globals, setup_consts, interfaces
from tests import common
from utilities import utils
from lib.instruments import power_control
import time, logging, traceback
from time import ctime
import numpy as np

log = logging.getLogger(__name__)


class SystemTestsSensitivity(common.ParametrizedTestCase):
    """
    Class: SystemTestsSensitivity
    Brief: RX sensitivity measurement test, output: sensitivity value
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """
    def __init__(self, methodName = 'runTest', param = None):
        super(SystemTestsSensitivity, self).__init__(methodName, param)


    def get_test_parameters( self ):
        #super(SystemTestsSensitivity, self).get_test_parameters()
        self.rf_if = self.param.get('rf_if', 0) 
        self.ch_freq = self.param.get('ch_freq', 5860)  # if not exists, set default freq to 5860
        self.rate = self.param.get('rate', 6)   
        self.num_pckt2send = self.param.get('num_pckt2send', 1000)
        self.pad = self.param.get('pad',1000)
        self.temperature = self.param.get('temperature', 25)
        self.evk_ip = self.param.get('evk_ip')
        self.interval_usec = self.param.get('interval_usec', 20)
        self.bandwidth = self.param.get('bandwidth', 10)
        self.rate_list = self.param.get('rate_list')
        #self.range_by_rate = self.param.get('range_by_rate')


    def setUp(self):
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

    def tearDown(self):
        self.vsg.rf_enable( False )
        self.uut.close_fw_cli()
         
        

    def initialization(self):
        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self._uut_id[0])
            self.uut.create_fw_cli()                                # create cli connection for all ports (23,1123,terminal)
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

        # Get Power control handle from setup
        if globals.setup.instruments.power_control is None:
            raise globals.Error("Power control is not initilized, please check your configuration")

        self.power_control = globals.setup.instruments.power_control

        # Get RF switch handle from setup
        if globals.setup.instruments.rf_switch_box is None:
           raise globals.Error("RF switch is not initilized, please check your configuration")
        
        # Get pointer to object
        self.rf_switch_box = globals.setup.instruments.rf_switch_box

        # MXG/VSG select switch
        self.rf_switch_box.set_switch('A', self.param['rf_if']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        self.rf_switch_box.set_switch('B', 2) # Switch B to com 2    

        # Set frequency
        self.uut.managment.set_rf_frequency( self.ch_freq, self.rf_if )

        # Set RF OFDM channel bandwidth 10/20MHz
        self.uut.managment.set_rf_ofdm_chan_bandwidth( self.bandwidth, self.rf_if )

        # Compensator connected/disconnected
        self.uut.managment.set_rf_frontend_enable( self.param['rf_front_end_compensator'], self.rf_if )

        # Loadinfg file to vsg
        print >> self.result._original_stdout, "\nWaiting for loading file to vsg.. "
        self.vsg.load_file( self.param['test_data_dir'], self.param['data_waveform'], self.bandwidth )

    def test_sensitivity(self):

        log.info('Start Sensitivity test')

        self.get_test_parameters()
        self.initialization()
       
        full_res = []
        results_collect = {} # report results dictionary   

        # Read collected results file and update dict 
        results_collect.update( utils.file_to_dict( self.param['final_report_file'] ) )   
       
        # Logging
        log.info( "Sensitivity test parameters: rf_if {}, freq {}Mhz, rate {}Mbps, temperature {}".format( self.rf_if, self.ch_freq, self.rate, self.temperature ) )
               
        firstString = True
            
        # AGC cross-over points  default (-67dBm,-49dBm)
        pwr_range = self.consts.common["SENSITIVITY_TEST_RANGE_RATE"]   # dictionary of ranges  

        # Execute test
        sens_point = np.nan  
        fail_details = 'measurement error'
        status_s = False

        print >> self.result._original_stdout, "\nSensitivity measurements loop .. "

        # Point is False when sensitivity point catched
        point = True
        # Run over selected range
        for pwr in pwr_range[self.rate]:                
            # When using IQ2010 tester we must transmit 1 packet for clean RF output
            self.vsg.vsg_settings( self.ch_freq, pwr )       # Set and Transmit 1 packet with Single trigger mode 
            self.vsg.vsg_frames_to_send( 1 )
            self.vsg.rf_enable( True )

            # Get initial RX counter value 
            init_value = self.uut.managment.get_wlan_frame_rx_cnt( self.rf_if ) # Get Rx counter, initial reference
            self.vsg.vsg_settings( self.ch_freq, pwr )       # Set and Transmit n packets with Single trigger mode
            self.vsg.vsg_frames_to_send( self.num_pckt2send )
            self.vsg.rf_enable( True )

            # Wait 8 seconds to complete transmission
            #time.sleep(8)   # to do calculate exact time for transmission, Packet transmission time = number_of_packets*(Packet size / Bit rate)
                
            current_rssi = pwr - float( self.consts.common['RX_PATH_SETUP_ATTENUATION_DB_' + str( self.rf_if ) + "_" + self.param['board_type']] ) 
                
            # Logging
            log.info( 'Pin signal power: ' + str(current_rssi) + ' dBm' )

            # Get RX counter value after transmission of n packets      
            frame_rx_cnt = self.uut.managment.get_wlan_frame_rx_cnt( self.rf_if ) 

            # Calculate number of recieved packets
            recieved_cnt = frame_rx_cnt - init_value

            # PER calculation
            per = 1 - float( recieved_cnt )/self.num_pckt2send

            # Get RSSI of last packet - read 10 times and calulate average RSSI
            rssi_values = []
            rssi_value = -1
            rssi_var = np.nan
            try:
                for i in range(10):
                    rssi_value = self.uut.managment.get_rx_rssi( self.rf_if )
                    rssi_values = np.append(rssi_values, rssi_value)

                rssi_average = np.mean(rssi_values.astype(np.float)) # calculating average RSSI
                rssi_var = np.var(rssi_values.astype(np.float)) # calculating variance of RSSI measurements
                                
                # Logging
                log.debug( 'RSSI measurements values: ' + str( rssi_values ) + " dBm" )
                log.info( 'RSSI Average: ' + str( rssi_average ) + ' dBm, ' + 'RSSI Variance: ' + str( rssi_var ) + ' dBm' )

                # Calculate delta between current RSSI - average RSSI
                average_delta = abs( current_rssi - float(rssi_average) )
            except:
                average_delta = np.nan
                pass
                
            log.info( 'PER: {} %'.format( per*100 ) )
            res_dict = {}
            res_dict["ch_freq"] = self.ch_freq
            res_dict["rate"] = self.rate
            res_dict["interval_usec"] = self.interval_usec
            #res_dict["interval_usec"] = 32
            res_dict["num_pckt2send"] = self.num_pckt2send
            res_dict["packet_size"] = self.pad 
            res_dict["evk_ip"] = self.evk_ip
            res_dict["PER_ch"] = per*100
            res_dict["rssi_average"] = format(float(rssi_average),'0.2f')
            res_dict["rssi_variance"] = format(float(rssi_var),'0.2f')
            res_dict["rssi_diff_delta"] = format(float(average_delta),'0.2f')                
            #res_dict["EVM"] = format(float(evm_average),'0.2f')
            res_dict["rf_if"] = self.param['rf_if']
            res_dict["macIF_counter_val"] = recieved_cnt
                                                           
            full_res.append( (current_rssi,res_dict) )
            log.info("sensitivity results {}".format (full_res))

            #Sensitivity point trap          
            if ( 0 <= per*100 <= self.consts.expected['EXPECTED_PER_HIGH_PERCENT'] ) and ( current_rssi < self.consts.common['MIN_SENSITIVITY_BY_RATE_DB'][str(self.rate)] ) and point:
                sens_point = current_rssi
                log.info ( '$$Sensitivity point =' + str(current_rssi) )
                status_s = self.add_limit( "temp {}, ch_{} {} rx sensitivity [dB]".format(self.temperature, self.rf_if, self.rate ) , self.consts.common['MIN_SENSITIVITY_BY_RATE_DB'][str(self.rate)], sens_point, None , 'LE')        
                point = False
            elif ( 0 <= per*100 <= self.consts.expected['EXPECTED_PER_HIGH_PERCENT'] ) and ( current_rssi > self.consts.common['MIN_SENSITIVITY_BY_RATE_DB'][str(self.rate)] ) and point:
                sens_point = current_rssi
                log.info ( '$$Sensitivity point (value exceed expected) = ' + str( current_rssi ) )
                status_s = self.add_limit( "temp {}, ch_{} {} rx sensitivity [dB]".format(self.temperature, self.rf_if, self.rate ) , self.consts.common['MIN_SENSITIVITY_BY_RATE_DB'][str(self.rate)], sens_point, None , 'LE')        
                point = False
            elif ( per*100 == 0 ) and point:
                sens_point = current_rssi
                log.info ( '$$Sensitivity point (value @PER 0%) = ' + str( current_rssi ) )
                status_s = self.add_limit( "temp {}, ch_{} {} rx sensitivity [dB]".format(self.temperature, self.rf_if, self.rate ) , self.consts.common['MIN_SENSITIVITY_BY_RATE_DB'][str(self.rate)], sens_point, None , 'LE')        
                point = False
            elif ( 0 <= per*100 <= self.consts.expected['EXPECTED_PER_HIGH_PERCENT'] ) and ( current_rssi > self.consts.common['MIN_SENSITIVITY_BY_RATE_DB'][str(self.rate)] ) and point:
                log.info ( '$$Sensitivity point did not reach the expected value, PER arround 10% at {} [dB]'.format( current_rssi ) )
                status_s = self.add_limit( "temp {}, ch_{} {} rx sensitivity [dB]".format(self.temperature, self.rf_if, self.rate ) , self.consts.common['MIN_SENSITIVITY_BY_RATE_DB'][str(self.rate)], sens_point, None , 'LE')
                point = False
                #pass               
                
            #results_collect.update( { "ch_{} rate {}Mbps sensitivity point".format( self.rf_if, self.rate ) : format(float(sens_point),'0.2f') } )
            print >> self.result._original_stdout, "ch_{}, rate {}[Mbps], RSSI {}[dBm], PER {}[%]".format( self.rf_if, self.rate, str(format(float(current_rssi),'0.2f')), per*100)
            self.add_limit( "temp {}C, ch_{}, rate {}[Mbps], RSSI {}[dBm], PER[%]".format( self.temperature, self.rf_if, self.rate, str(format(float(current_rssi),'0.2f'))), 0, per*100, float(self.consts.expected['EXPECTED_PER_HIGH_PERCENT']) if ( sens_point-3 < current_rssi < sens_point+3 ) else float(0), 'GELE')
            
            fail_details = 'sensitivity point did not reach the expected value or not in range of measurements' if point else 'status done'

        # Collect sensitivity results to file
        with open(self.param["sens_results"], "a+") as out_file:
            utils.print_and_log(out_file, "{},{},{},{},{},{},{},{},{},".format(
                                                                                    ctime(),
                                                                                    str(self.consts.common['DSRC_CHANNEL_SIM_MODELS_LIST'][0]),
                                                                                    str(self.temperature),
                                                                                    str("ch_{}".format(self.rf_if)),
                                                                                    str(self.rate),
                                                                                    str(self.ch_freq),
                                                                                    str(sens_point),
                                                                                    status_s,
                                                                                    fail_details))


        # Get measured DUT Pin(RSSI, EVM) and save results
        evm_meas_power = self.consts.common["RX_IQ_IMBALANCE_INIT_PIN_POWER_DBM"] - float( self.consts.common['RX_PATH_SETUP_ATTENUATION_DB_' + str( self.rf_if ) + "_" + self.param['board_type']] )
        self.vsg.vsg_settings( self.ch_freq, evm_meas_power ) # -55dbm
        self.vsg.vsg_frames_to_send(0) # free run
        time.sleep(1)     
        results_dict = self.fw_cli.get_rssi( self.rf_if + 1, self.consts.common['EVM_AVERAGE_CNT'], 10 )     # timeout = 10sec
        rssi_average = results_dict.get('rssi')[1]     # Get Average RSSI from statistics
        evm_average = results_dict.get('evm')[1]       # Get Average EVM from statistics
        status_evm = self.add_limit( "temp {}, ch_{} freq {} rate {} rx evm [dB]".format(self.temperature, self.rf_if, self.ch_freq, self.rate ) , self.consts.expected['EXPECTED_RX_EVM_LIMIT_DB'], float(evm_average), None , 'LE')

        log.info( "Average RSSI = %sdBm, EVM = %sdB"  % (rssi_average,evm_average))        
        if self.param["calibration_enable"]:
            results_collect.update( { "ch_{} rate {}Mbps sensitivity point".format( self.rf_if, self.rate ) : [ format(float(sens_point),'0.2f'), status_s ] } )
            results_collect.update( { "ch_{} rx evm@{}dBm".format( self.rf_if, self.consts.common["RX_IQ_IMBALANCE_INIT_PIN_POWER_DBM"]): [ evm_average, status_evm ] } )
            utils.dict_to_file( results_collect, self.param['final_report_file'] )

        # Stop transmisssion
        self.vsg.rf_enable( False )
        log.info('Sensitivity test finished')
