"""
@file tc_vca_1.py
@brief Testsuite for testing VCA loging 
@author    	Ayelet
@version	1.0
@date		27/10/2013
\link		\\fs01\docs\system\Integration\Test_Plans\SW_Releases\???.docx \endlink
"""

from lib import station_setup
from uuts import common
from lib import instruments_manager
from lib import packet_analyzer
from lib import globals
from lib import ssh
import subprocess

from tests import sdk2_0
from tests import common

import sys
import os
import time
import logging
import commands

# @topology('CF01')
class TC_VCA_1(common.V2X_SDKBaseTest):
    """
    @class AtlkUnit
    @brief ATLK base unit Implementation 
    @author Ayelet
    @version 0.1
    @date	27/10/2013
    @param test_links - a list of 2 tPrams each has the following format
        tParam( tx = (0,1), rx = (1,1), proto_id = 0x2123, frame_rate_hz = 10, tx_data_len = 0, tx_power = 10, freq = 5880)
    @param test_duration - test duration is seconds. at this time both links will both tx & rx.
    Important notes: 
    1. currently this test supports only windows OS 
    2. cleaning the log fiels at the end of each run leaves the VCAD in an undefined state which prevents ferther loggings
    3. there is a memory issue of tx & rx seq list - we choose to leave it implemented in lists untill we decide there is a true memory
    issue. if such an issue aroses we will split the log files to rx file & tx file. so that memory is not execisly consumed 
    """
    class Rf_if_basic_params(object):
        def __init__(self, uut_idx, rf_if):
            self.uut = globals.setup.units.unit(uut_idx)
            self.uut_idx = uut_idx
            self.rf_if = rf_if
            self.freq = self.uut.rf_interfaces[self.rf_if].frequency
            
    class Rf_if_tx_params(Rf_if_basic_params):
        def __init__(self, uut_idx, rf_if, tx_power, frame_rate_hz):
            TC_VCA_1.Rf_if_basic_params.__init__(self, uut_idx, rf_if)
            self.tx_period = int(float( 1000 / frame_rate_hz))
            self.freq = self.uut.rf_interfaces[self.rf_if].frequency
            self.tx_power = tx_power


    class Statistics(object):

        class Unit_Statistics(object):
            def __init__(self):
                self.src_addr_err = 0
                self.rx_seq_err = 0
                self.tx_seq_err = 0

        def __init__(self):
            self.unit = []
            self.unit.append(self.Unit_Statistics())
            self.unit.append(self.Unit_Statistics())
            self.cross_seq_err = [0,0]
        

        def get_total_err(self):
            err = ()
            return sum(err)
                
    def runTest(self):
        pass

    def tearDown(self):        
        # kill gps        
        if globals.setup.instruments.gps_simulator != None:
            self.gps_sim.stop_scenario()
            self.gps_sim.stop_recording()

    def __init__(self, methodName = 'runTest', param = None):        
        return super(TC_VCA_1, self).__init__(methodName, param)

    def _clean_logs(self):
        """ clean all previos logs & reboot otherwise the vcad will not continue logging"""
        
        from lib.instruments import power_control
        #switch = power_control.NetworkPowerControl('10.10.0.2')
               
        for uut in self.uuts:
            #uut = globals.setup.units.unit(uut_idx)
            if "SDK3." in uut.version:
                uut.cli.vca_clean_logs()
                globals.setup.instruments.power_control[ uut.pwr_cntrl.id ].reboot( uut.pwr_cntrl.port )
            else:        
                self._if = ssh.SSHSession( uut.ip , "root", "123" )
                command = 'rm -rf ../vca/2013'
                rc = self._if.exec_command( command )
                self._if.status_ready()
                command = 'reboot'
                rc = self._if.exec_command( command )
                self._if.status_ready()
                rc = self._if.exit_status()     
         
        """for idx, obj in enumerate(self._uut):   
            if self._uut[idx].version == "SDK3.0.0":    
                self._uut[idx].cli.vca_clean_logs()
                switch.reboot(self._uut[idx].pc["port"])
            else:        
                self._if = ssh.SSHSession( self._uut[idx].ip , "root", "123" )
                command = 'rm -rf ../vca/2013'
                rc = self._if.exec_command( command )
                self._if.status_ready()
                command = 'reboot'
                rc = self._if.exec_command( command )
                self._if.status_ready()
                rc = self._if.exit_status()
                #if ( rc != 0 ):
                #    raise globals.Error("%s failed !" % command )"""
        
    def _test_units(self):
        """ Test items:
        1. that RX src address is constant through out the test
        2. that rx & tx logging are in sequential order (i.e. no sequence is missing)
        3. the amount of logged rx of cross units is equall to the amount of logged tx  
        4. the sequence of the logged tx equalls those of rx
        """
        #vca_reader = []
        src_addr_list = []
        for tx_params in self.rf_if_tx_params_list:
            src_addr_list.append((tx_params.uut,tx_params.uut.rf_interfaces[tx_params.rf_if].mac_addr))
        rx_seq_list = [[],[]]
        tx_seq_list = [[],[]]
        len_err = 0
        
        # both log files have the same timestamp
        timestr = time.strftime("%Y%m%d-%H%M%S")
        for uut in self.uuts:
            # we need the peer src addr 
            for addr in src_addr_list:
                if uut != addr[0]:
                    peer_src_addr = addr[1]
                     
        #for idx, obj in enumerate(src_addr):  
            if globals.setup.instruments.gps_simulator != None:           
                output_dir = None
                output_file = os.path.join(globals.setup.station_parameters.reports_dir, "vca_log_%s_%s.txt" % (repr(uut.idx), timestr) ) 
                
                # call the import_vca.exe                          
                try:
                    exe_path = self._vca_lib_path + "\\vca_import.exe"
                    cmd = [exe_path,  uut.ip, "--output", output_file]
                    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
                    proc.communicate(input="y\r\n")
                except:
                    raise
            else:
                # used for debug only
                output_file = None
                output_dir = "T:\\vca"
            if proc.returncode != 0:
                self.add_limit( "vca_import_error", None, 1, None , 'EQ')
                return 
       
            # start analyzing frames    
            vca_reader = sdk2_0.vca_reader.VcaReader(vca_log_dir_path = output_dir, vca_log_single_file_path = output_file)
            

            #for packet in vca_reader[idx].get_frames() :
            for packet in vca_reader.get_frames():
                 if packet[0] == "RxPkt":
                    # make sure src address is constant
                    if peer_src_addr != packet[1]['srcAddr']:
                        self.log.error("inconsistant src address %s instead of %s" % (packet[1]['srcAddr'], peer_src_addr)) 
                        self.stats.unit[uut.idx].src_addr_err += 1
                    # add rx seq to seq list
                    rx_seq_list[uut.idx].append(packet[1]["seqNum"])                                                                                  
                 if packet[0] == "TxPkt":
                    # add tx seq to seq list
                    tx_seq_list[uut.idx].append(packet[1]["seqNum"])
                                                
            tx_seq_list[uut.idx].sort
            rx_seq_list[uut.idx].sort

            # check that there are no missing tx loggs (by seq number)
            for index in xrange(1, len(tx_seq_list[uut.idx])):                                
                if tx_seq_list[uut.idx][index-1] + 1 != tx_seq_list[uut.idx][index]:
                    self.stats.unit[uut.idx].tx_seq_err += 1
                    self.log.info("tx_seq of unit %d prev=%d cur=%d" % (uut.idx, tx_seq_list[uut.idx][index-1], tx_seq_list[uut.idx][index]))

            # check that there are no missing rx loggs (by seq number)
            for index in xrange(1, len(rx_seq_list[uut.idx])):                                
                if rx_seq_list[uut.idx][index-1] + 1 != rx_seq_list[uut.idx][index]:
                    self.stats.unit[uut.idx].rx_seq_err += 1
                    self.log.info("rx_seq of unit %d prev=%d cur=%d" % (uut.idx, rx_seq_list[uut.idx][index-1], rx_seq_list[uut.idx][index]))
        
        # check rx & tx seq number accorss units 
        if len(tx_seq_list[0]) == len(rx_seq_list[1]) and tx_seq_list[0] != rx_seq_list[1]:
            self.stats.cross_seq_err[0] += 1
        if len(tx_seq_list[1]) == len(rx_seq_list[0]) and tx_seq_list[1] != rx_seq_list[0]:
            self.stats.cross_seq_err[1] += 1
        
        return ([len(tx_seq_list[0]), len(tx_seq_list[1])], [len(rx_seq_list[0]), len(rx_seq_list[1])])
     
    def get_test_parameters( self ):
        self._test_duration = self.param.get('test_duration', 5*60 )
        self._vca_lib_path = self.param.get('vca_lib_path', "tc_vca")
        self._gps_scenario = self.param.get('gps_scenario', "Neter2Eilat" )
        self._gps_tx_power = self.param.get('gps_tx_power', -68.0 )   
        self._gps_lock_timeout_sec = self.param.get('gps_lock_timeout_sec', 600 )
        
    def initilization(self): 
        # Initilize GPS 
        self.gps_sim = None
        if self._gps_scenario == None:
            globals.Error("Gps scenario not exists, please make sure to pass parameters")

        self.log.info("Getting GPS simulator in config")
        if globals.setup.instruments.gps_simulator is None:
            raise globals.Error("GPS simulator is not initilize, please check your configuration")
            #pass
        else:
            # Get pointer to object
            self.gps_sim = globals.setup.instruments.gps_simulator

            # set general tx power
            self.gps_sim.tx_power( self._gps_tx_power )  
            #load scenario
            self.gps_sim.load( self._gps_scenario )            


    def main_test(self):
        """ since GPS lock can take up to 10min first lock both gps & only then run the test.
            so tx & rx are in sync """
        if self.is_gps_active():
            self.gps_sim.start_scenario()        

        lock = 0
        for uut in self.uuts:
            if self.wait_for_gps_lock(uut, self._gps_lock_timeout_sec ) == False: 
                self.log.info("GPS Lock failed unit(%d)" % (uut.idx))
            else:
                lock += 1 

        if lock != len(self.uuts):
            raise globals.Error("GPS is not Locked for both units")
  
        #gps lock succeeded 4 both boards
        rx_hw_cnt = [0,0]
        tx_hw_cnt = [0,0]
        tx_vca_cnt = [0,0]
        rx_vca_cnt = [0,0]

        for rf_if_params in self.rf_if_rx_params_list:  
            rx_hw_cnt[rf_if_params.uut_idx] = rf_if_params.uut.managment.get_wlan_frame_rx_cnt(rf_if_params.rf_if)

        for rf_if_params in self.rf_if_tx_params_list:  
            tx_hw_cnt[rf_if_params.uut_idx] = rf_if_params.uut.managment.get_wlan_frame_tx_cnt(rf_if_params.rf_if)
            rf_if_params.uut.managment.set_vca_log_mode(1)
            rf_if_params.uut.managment.set_vca_tx_period(rf_if_params.rf_if, rf_if_params.tx_period)                
            rf_if_params.uut.managment.set_vca_tx_enabled(rf_if_params.rf_if, 1)                

        time.sleep(self._test_duration)
        
        for rf_if_params in self.rf_if_rx_params_list:
             rx_hw_cnt[rf_if_params.uut_idx] = rf_if_params.uut.managment.get_wlan_frame_rx_cnt(rf_if_params.rf_if) - rx_hw_cnt[rf_if_params.uut_idx]
              
        for rf_if_params in self.rf_if_tx_params_list:  
            rf_if_params.uut.managment.set_vca_tx_enabled(rf_if_params.rf_if, 2)
            tx_hw_cnt[rf_if_params.uut_idx] = rf_if_params.uut.managment.get_wlan_frame_tx_cnt(rf_if_params.rf_if)  - tx_hw_cnt[rf_if_params.uut_idx]
               
        # sleep untill all packets are logged in the vca            
        time.sleep(100)

        (tx_vca_cnt, rx_vca_cnt) = self._test_units()
        return (tx_vca_cnt, rx_vca_cnt, tx_hw_cnt, rx_hw_cnt)

    def print_report(self, tx_vca_cnt, rx_vca_cnt, tx_hw_cnt, rx_hw_cnt):
        for idx, obj in enumerate(rx_hw_cnt):
            self.add_limit( "INFO: unit %d: ip %s: TX Mac frames" % (idx, globals.setup.units.unit(idx).ip), tx_hw_cnt[idx], tx_hw_cnt[idx], None , 'EQ') 
            self.add_limit( "INFO: unit %d: ip %s: RX Mac frames" % (idx, globals.setup.units.unit(idx).ip), rx_hw_cnt[idx], rx_hw_cnt[idx], None , 'EQ') 
            self.add_limit( "unit %d: TX Mac frames vs. TX logged frames" % (idx), tx_hw_cnt[idx], tx_vca_cnt[idx], None , 'EQ') 
            self.add_limit( "unit %d: RX Mac frames vs. RX logged frames" % (idx), rx_hw_cnt[idx], rx_vca_cnt[idx], None , 'EQ') 
        
        self.add_limit( "Number of TX Mac frames by unit 0 vs. number of Rx Mac frames by unit 1", 
                            tx_hw_cnt[0], rx_hw_cnt[1], None , 'EQ') 
        self.add_limit( "Number of TX Mac frames by unit 1 vs. number of Rx Mac frames by unit 0", 
                            tx_hw_cnt[1], rx_hw_cnt[0], None , 'EQ') 
                        
        self.add_limit( "Number of TX logged packets of unit 0 vs. number of Rx logged packets of unit 1", 
                            tx_vca_cnt[0], rx_vca_cnt[1], None , 'EQ') 
        self.add_limit( "Number of TX logged packets of unit 1 vs. number of Rx logged packets of unit 0", 
                            tx_vca_cnt[1], rx_vca_cnt[0], None , 'EQ') 
        
        self.add_limit( "unit 0 TX to unit 1 RX Number of sequence mismatches", 0, self.stats.cross_seq_err[0], None, 'EQ') 
        self.add_limit( "unit 1 TX to unit 0 RX Number of sequence mismatches", 0, self.stats.cross_seq_err[1], None, 'EQ')  
        
        for idx, obj in enumerate(rx_hw_cnt):
            self.add_limit( "unit %d: logged Tx sequnce errors" % (idx), 0, self.stats.unit[idx].tx_seq_err, 0 , 'EQ') 
            self.add_limit( "unit %d: logged Rx sequnce errors" % (idx), 0, self.stats.unit[idx].rx_seq_err, 0 , 'EQ')  
            self.add_limit( "unit %d: received Rx packets from several inputs" % (idx), 0, self.stats.unit[idx].src_addr_err, 0 , 'EQ') 

    def test_vca_1(self):
        # Parse test parameters        
        # params = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data_val = 'ab', tx_power = -5 ) ]
        self._test_params = self.param.get('params', None )
        if self._test_params is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : params = tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data_val = 'ab', tx_power = -5 )")
                
        # Get & parse test parameters
        self.get_test_parameters()    
       
        # Verify uut input exists and active
        self.rf_if_tx_params_list = []        
        self.rf_if_rx_params_list = [] 
        for t_params in self._test_params:
            self.rf_if_rx_params_list.append(self.Rf_if_basic_params(t_params.rx[0], t_params.rx[1]))
            if t_params.tx_power == None or t_params.frame_rate_hz == None:
                raise globals.Error("Missing tx_power or frame_rate_hz from input params")               
            self.rf_if_tx_params_list.append(self.Rf_if_tx_params(t_params.tx[0], t_params.tx[1], t_params.tx_power, t_params.frame_rate_hz))

        self.uuts = []
        for rf_if in self.rf_if_tx_params_list + self.rf_if_rx_params_list:       
            self.uuts.append(globals.setup.units.unit(rf_if.uut_idx))
        self.uuts = set(self.uuts)

        #self._clean_logs()
        
        self.log = logging.getLogger(__name__)
        self.stats = self.Statistics()

        self.initilization()
       
        # Set Rf Frequenct & tx_power
        for rf_if_params in  self.rf_if_tx_params_list:  
            rf_if_params.uut.managment.set_rf_frequency(rf_if_params.freq , rf_if_params.rf_if)
            rf_if_params.uut.managment.set_tx_power(rf_if_params.tx_power, rf_if_params.rf_if)

        for rf_if_params in  self.rf_if_rx_params_list:  
            rf_if_params.uut.managment.set_rf_frequency(rf_if_params.freq , rf_if_params.rf_if)
        
        (tx_vca_cnt, rx_vca_cnt, tx_hw_cnt, rx_hw_cnt) = self.main_test()
        
        self.print_report( tx_vca_cnt, rx_vca_cnt, tx_hw_cnt, rx_hw_cnt )   
       
           
        

  
                            
                        
        

