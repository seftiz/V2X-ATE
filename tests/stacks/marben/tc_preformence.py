"""
    @file  
    Implement stack preformnce 

"""

import sys, os, time, tempfile
import logging
from lib import station_setup
from uuts import common
from tests import common
from lib import instruments_manager, packet_analyzer, globals, gps_simulator

import threading
from datetime import datetime
import socket
import binascii
import re

log = logging.getLogger(__name__)


class TC_PREFORMENCE(common.V2X_SDKBaseTest):
    """
    @class TC_PREFORMENCE
    """
 
    def __init__(self, methodName = 'runTest', param = None):
        self.gps_lock = False
        # self.stats = Statistics()
        super(TC_PREFORMENCE, self).__init__(methodName, param)
    
    def get_test_parameters( self ):
        super(TC_PREFORMENCE, self).get_test_parameters()
        self.stations = self.param.get('stations', 40 )
        self.rate_fps = self.param.get('rate_fps' , 100 )
        self.security_active = self.param.get('security_active' , False )
        self.rx_fps_err = self.param.get('rx_fps_err', 0.95)
         
    def tearDown(self):
        super(TC_PREFORMENCE, self).tearDown()
        self.terminate()

    def test_start(self):
        self.log = logging.getLogger(__name__)
        # unit configuration 
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )
        # Get position data that described in table below via NAV API.
        self.get_test_parameters()
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self._uut_id[0])
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

        self.uut_channel = self._uut_id[1]


        self._tg_id = self.param.get('tg_id', None)
        if self._tg_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : tg_id=(0,1)")

        # Verify uut idx exits
        try:
            self.tg = globals.setup.units.unit(self._tg_id[0])
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or currpted, usage : tg_id=(0,1)")

        
        

        self.instruments_initilization()
        self.unit_configuration()
        self.main()

        #self.debug_override()

        if len(self._cpu_load_info):
            for uut_id in self._cpu_load_info:
                self.uut.set_cpu_load( 0 )

        self.analyze_results()

        self.print_results()
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def instruments_initilization(self):
        pass

    def unit_configuration(self):
        pass

    def get_uut_stats(self):

        while (1):
            line = self.pref_cli.interface.read_until( timeout_sec = 1 )
            if 'CAM Rx' in line:
                break

        # '250) Rx: 19672962 (287) Tx: 226917 (1)  CAM Rx: 19672962 (287)  CAM Tx: 226917 (1)      DENM Rx: 0 (0)  DENM Tx: 0 (0)'
        # stats  = filter(len, line[8:].replace('\t', ' ').split(' ') )
        log.info( "get_uut_stats process : {}".format( line ) )

        f = re.compile('\d+')
         # ['250', '19672962', '287', '226917', '1', '19672962', '287', '226917', '1', '0', '0', '0', '0']
        stats = map( int, f.findall(line) )

        stat = {}
        stat['rx_total_frames'] = stats[1]
        stat['rx_rate'] = stats[2]
        stat['tx_total_frames'] = stats[3]
        stat['tx_rate'] = stats[4]
        # Cam
        stat['rx_cam_frames'] =  stats[5] 
        stat['rx_cam_rate'] =  stats[6] 
        stat['tx_cam_frames'] = stats[7]
        stat['rx_cam_rate'] = stats[8]
        # denm
        stat['rx_denm_frames'] = stats[9]
        stat['rx_denm_rate'] = stats[10]

        stat['tx_denm_frames'] = stats[11] 
        stat['tx_denm_rate'] = stats[12]

        return stat

    def get_tg_stats(self):

        while (1):
            line = self.tg_fw.interface.read_until( timeout_sec = 1 )
            if 'STAT' in line:
                break

        # 'STATS : Tx: 139821052 (400)     Rx: 482456 (4)  CAM Tx: 139821045 (400) CAM Rx: 0       DENM Tx: 7       DENM Rx: 7'
        # stats  = filter(len, line[8:].replace('\t', ' ').split(' ') )
        log.info( "get_tg_stats process : {}".format( line ) )
        f = re.compile('\d+')
        
        stats = map( int, f.findall(line) ) # [139821052, 400, 482456, 4, 139821045, 400, 0, 7, 7]

        stat = {}
        stat['tx_total_frames'] = stats[0]
        stat['tx_rate'] = stats[1]
        stat['rx_total_frames'] = stats[2]
        stat['rx_rate'] = stats[3]
        # Cam
        stat['tx_cam_frames'] = stats[4]
        stat['tx_cam_rate'] = stats[5] 
        stat['rx_cam_frames'] = stats[6] 
        # denm
        stat['tx_denm_frames'] = stats[7]
        stat['rx_denm_frames'] = stats[8]

        return stat

    def main(self):

        self.print_test_parameters()

        # Set Traffic generator to transmit X frames
        self.tg_fw = self.tg.fw_cli('terminal')
        
        # Set number of stations
        self.tg_fw.interface.write('tg stations %d\r\n' % self.stations )
        self.tg_fw.interface.write('tg print_counters 1\r\n')
        time.sleep(1)

        self.uut_fw = self.uut.fw_cli('terminal')

        self.pref_cli = self.uut.fw_cli('23')
        self.pref_cli.interface.write('pref start\r\n')
        time.sleep(1)


        # self.tg_fw.interface.write('tg print_counters 0\r\n')
        self.tg_fw.interface.write('tg sec %d\r\n' % int(self.security_active) )

        if (self.security_active):
            self.tg_fw.interface.write('tg full %d\r\n' % 1)

        # Set rate 
        self.tg_fw.interface.write('tg rate %d\r\n' % self.rate_fps )

        # Wait for system stabilization
        time.sleep(10)

        self.pref_cli.interface.flush_buffer()


        # 
        tg_stat = self.get_tg_stats()
        expected_rate = tg_stat['tx_rate']

        received_rate = 0
        # Read tg rate
        for i in range(10):

            uut_stat = self.get_uut_stats()
            received_rate += uut_stat['rx_rate'] 
            time.sleep(1)

        avg_rate = received_rate / 10

        idle = self.uut_fw.read_cpus_profiling()

        self.add_limit( "Expected vs. Actual tx rate", (expected_rate * self.rx_fps_err) , avg_rate, expected_rate, 'GTLT')
        
        # Add idle time
        for cpu in ['arm', 'arc1', 'arc2']:
            self.add_limit( "Idle at {} cpu".format( cpu ) , 0.0 , idle['idle'][cpu], 100.0 , 'GTLT')
        

    def debug_override( self, base_dir = None ):
        pass
    def analyze_results(self):
        pass
    def print_results(self):
        pass

    def terminate(self):
        # Stop the TG
        try:
            self.tg_fw.interface.write('tg rate %d\r\n' % 0 )
            self.tg_fw.interface.write('tg stations %d\r\n' % 1 )
            self.tg_fw.interface.write('tg print_counters 0\r\n')

            # Stop profiling on unit
            self.pref_cli.interface.write('pref stop\r\n')

        except Exception:
            pass




