from lib import globals, setup_consts, interfaces
from tests import common
from utilities import utils
from lib.instruments import power_control
import time, logging, traceback
from time import ctime
import numpy as np

log = logging.getLogger(__name__)


class SystemTestsLnaVgaStatus(common.ParametrizedTestCase):
    """
    Class: SystemTestsLnaVgaStatus
    Brief: LNA/VGA maximum distance status measurement test, output: distance value
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """
    def __init__(self, methodName = 'runTest', param = None):
        super(SystemTestsLnaVgaStatus, self).__init__(methodName, param)

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
        self.range_by_rate = self.param.get('range_by_rate')

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
            self.uut.create_fw_cli()                                # create cli connection for (23,1123,terminal)
            self.fw_cli = self.uut.fw_cli('23')                     # get cli from telnet port 23
            self.consts = setup_consts.CONSTS[globals.setup.station_parameters.station_name]
        except KeyError as e:
            traceback.print_exc()
            raise globals.Error("{}, uut index and interface input is missing or currpted, usage : uut_id=(0,1)".format ( e ))

        # Get Signal tester VSG/MXG handle from setup
        log.info("Signal tester VSA/VSG/MXG configuration")
        if globals.setup.instruments.rf_vector_signal is None:
            raise globals.Error("Signal tester is not initilized, please check your configuration")

        self.vsg = globals.setup.instruments.rf_vector_signal['vsg']

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
        
        print >> self.result._original_stdout, "\nWaiting for loading file to vsg.. "
        self.vsg.load_file( self.param['test_data_dir'], self.param['data_waveform'], self.bandwidth )


    def test_lna_vga_status(self):

        log.info('Start LNA/VGA status test')

        self.get_test_parameters()
        self.initialization()
       
        full_res = []
        results_collect = {} # report results dictionary      
       
        # Logging
        log.info( "LNA_VGA status test parameters: rf_if {}, freq {}Mhz, rate {}Mbps, temperature {}".format( self.rf_if, self.ch_freq, self.rate, self.temperature ) )
               
        firstString = True
            
        # AGC cross-over points  default(-67dBm,-49dBm)
        pwr_range = self.range_by_rate   # dictionary of ranges  

        # Execute test
        point = True
        sens_point = np.nan  
        fail_details = ''  

        print >> self.result._original_stdout, "\nStart LNA/VGA status test measurements loop .. "
        self.add_limit( "temp {}C, freq {}MHz, ch_{}, rate {}[Mbps]".format( self.param['temperature'], self.param['ch_freq'], self.rf_if, self.param['rate'] ), 0, 0, 0 , 'GELE')

        
        for pwr in pwr_range[self.rate]:                
            # When using IQ2010 tester we must transmit 1 packet for clean RF output
            self.vsg.vsg_settings( self.ch_freq, pwr )       # Transmit 1 packet with Single trigger mode 
            self.vsg.vsg_frames_to_send( 1 )
            self.vsg.rf_enable( True )

            # Get initial RX counter value 
            init_value = self.uut.managment.get_wlan_frame_rx_cnt( self.rf_if ) # Get Rx counter, initial reference
            self.vsg.vsg_settings( self.ch_freq, pwr )       # Transmit n packets with Single trigger mode
            self.vsg.vsg_frames_to_send( 1 )   #  Transmit 1 packet with Single trigger mode
            self.vsg.rf_enable( True )

            # Wait 1 seconds to complete transmission
            #time.sleep(1)   # to do calculate exact time for transmission, Packet transmission time = Packet size / Bit rate
                
            current_rssi = pwr - float( self.consts.common['RX_PATH_SETUP_ATTENUATION_DB_' + str( self.rf_if ) + "_" + self.param['board_type']] ) 
                
            lna_vga_value = self.fw_cli.get_reg( ( "phy"+str( self.rf_if ), self.consts.register[ 'LNA_VGA_LOCK_REG_HEX' ] ) )

            # Logging
            log.info( 'Pin signal power: {}dBm, lna_vga_value: {}'.format( str( current_rssi ), lna_vga_value ) )

            # Get RX counter value after transmission of n packets      
            frame_rx_cnt = self.uut.managment.get_wlan_frame_rx_cnt( self.rf_if ) 

            # Calculate number of recieved packets
            recieved_cnt = frame_rx_cnt - init_value

            # PER calculation
            per = 1 - float( recieved_cnt )/1

            # Get RSSI of last packet - read 10 times and calulate average RSSI
            rssi_value = self.uut.managment.get_rx_rssi( self.rf_if )

            # Logging
            log.debug( 'RSSI measurements values: ' + str( rssi_value ) + " dBm" )

            log.info( 'PER (%) : ' + str( per*100 ) + ' %' )
            res_dict = {}
                
            # LNA/VGA status checking
            SHIFT = 6
            lna_status = lna_vga_value >> SHIFT   # 2 msb bits reg 0x19d (self.consts.register[ 'LNA_VGA_LOCK_REG_HEX' ])
            log.info( "LNA status {}".format( str(hex( lna_status )) ) )
            vga_range = self.consts.common[ "VGA_RANGE_HEX" ] # dict
            vga_min_dist = None
            prev_vga_min_dist = None

            lna_status_dict = {"LOW": 3, "MID": 2, "HIGH": 0}   
            for key, item in lna_status_dict.iteritems():
                if lna_status == item:
                    vga_min_dist = abs(lna_vga_value - int(vga_range[key]))*2   # vga values {0xC0, 0x80, 0x0 } each VGA step = 2db
                else:
                    prev_vga_min_dist = vga_min_dist
                

            log.info( "RSSI = {:s}, LNA_VGA_VALUE= {:s}, MIN_DIST_VGA_OFF_dB = {:s}, PACKET_CNT = {:d},".format(str(rssi_value), str(hex(lna_vga_value)), str(vga_min_dist), recieved_cnt) )
            print >> self.result._original_stdout, "ch_{}, rate {}[Mbps], RSSI {}[dBm], PER {}[%]".format( self.rf_if, self.rate, str(format(float(current_rssi),'0.2f')), per*100)
            self.add_limit( "ch_{} rate {}, freq {}, temp {}, RSSI {}, MIN_DIST [dB]".format( self.rf_if, self.rate, self.ch_freq, self.temperature, format(float(current_rssi),'0.2f')), 0, vga_min_dist, 0 , 'GELE')
        #Stop transmission
        self.vsg.rf_enable( False )
        log.info('LNA_VGA status test finished')
