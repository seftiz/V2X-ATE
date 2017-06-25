"""
@file       Tc_link.py
@brief      Test suite for testing sdk link layer module  
@author    	Chani Rubinstain
@version	0.1
@date		Feb 2017
"""
# import global and general setup var
from lib import globals, station_setup, instruments_manager, packet_analyzer
from uuts import common
from tests import common, dsrc_definitions

from lib.instruments import spectracom_gsg_6

# Define tree for 3 layer array
from collections import defaultdict 
def tree(): return defaultdict(tree)

import threading

import sys, os, time
from datetime import datetime
import logging
import tempfile
import decimal
import Queue
import pyshark

from lib.instruments import traffic_generator

BASE_HOST_PORT = 8030

log = logging.getLogger(__name__)

class TC_LINK(common.V2X_SDKBaseTest):
    """
    @class TC_LINK
    @brief Implementation of sdk link layer implementation  
    @author Chani Rubinstain
    @version 0.1
    @date	20/02/2017
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self.rx_list = []
        self.tx_list = []
        self.active_cli_list = []
        self._uut = {}
        self.sniffers_ports = []
        self.sniffer_file = []                                
        self.v2x_cli_sniffer_if0 = None
        self.v2x_cli_sniffer_if1 = None
        self.dut_embd_sniffer = None
        self.num_of_frames_per_socket = dict()
        self.socket_list = [ [[],[]], [[],[]] ] # uut_id 0/1 , rf_if 0/1 , protocol_id
        self.thread_stop_tx = [[],[]]
        self.thread_stop_rx = [[],[]]
        self.RxDUT_data = []
        self.frames_NotForUnit_count = dict()
        self.rx_NotForUnit_count = 0        

        
        return super(TC_LINK, self).__init__(methodName, param)

    def runTest(self):
        pass

    def setUp(self):
        super(TC_LINK, self).setUp()
        pass

    def tearDown(self):
        super(TC_LINK, self).tearDown()
        g = []

        for cli in self.active_cli_list:
            try:
                uut_id, rf_if, cli_name = cli
                g.append(uut_id)
                # close link session
                self._uut[uut_id].qa_cli(cli_name).link.socket_delete()

            except Exception as e:
                print >> self.result._original_stdout, "ERROR in tearDown,  Failed to delete socket on uut {} for cli {}".format( uut_id, cli_name )
                log.error( "ERROR in tearDown,  Failed to clean uut {} for cli {}".format(uut_id, cli_name) )
            finally:
                self._uut[uut_id].close_qa_cli(cli_name)

    def test_link(self):
        """ Test link layer Tx and Rx
            @fn         test_link_tx_rx
            @brief      Verify tx nd rx abilites
            @details    Test ID	    : TC_SDK5.X_LINK_01
            @see Test Plan	: 
        """
        self.get_test_parameters()
        
        # Call Test scenarios blocks
        self.initilization()
        self.unit_configuration()        

        self.main()
        
        self.analyze_results()
        
    def get_test_parameters( self ):
        self.test_name = self.param.get('test_name', 0)
        print "Test name : {} \n".format(self.test_name)

        super(TC_LINK, self).get_test_parameters()

        self._capture_frames = self.param.get('capture_frames', 0) # Rx information print flag        

        self._testParams = self.param.get('params', None ) # get the test parameters dictionary from qa.py
        if self._testParams is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : params = tParam( tx = (0,1), rx = (1,1), proto_id = 0, frames = 1000, frame_rate_hz = 50, tx_data_len = 100, tx_data = 'ab', tx_power = -5 )")

        g = []
              
        print "Test parameters :\n"
        for i, t_param in enumerate(self._testParams):
            print "Param {} : {}".format ( i, ', '.join( "%s=%r" % (t,self.cap(str(v),10)) for t,v in t_param.__dict__.iteritems()) )

            if 'tx' in vars(t_param):
                g.append(t_param.tx[0])
            if 'rx' in vars(t_param) and not t_param.rx is None:
                g.append(t_param.rx[0])
         
        self._uut_list = set(g)  # list of all the units in the test

    def initilization(self):
       pass
       
    def unit_configuration(self):
    
        for uut_idx in self._uut_list:
            try:
                self._uut[uut_idx] = globals.setup.units.unit(uut_idx)
                self.stats.tx_uut_count.append(0)
                self.stats.rx_uut_count.append(0)               
            except KeyError as e:
                raise globals.Error("uut index and interface input is missing or currpted, usage : _uut_id_tx=(0,1)")

        # Config rx uut
        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            if t_param.rx is None:
                continue
            
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx

            for rx in rx_list:
                uut_id, rf_if = rx
                #set cli name base on rx + proto_id + if
                cli_name = "rx_%d_%x" % ( rf_if, t_param.proto_id )
                    
                self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                self.rx_list.append( (uut_id, rf_if, cli_name, t_param.frames, t_param) )                

                t_param.rx_cli = cli_name

                if not 'frame_type' in vars(t_param):
                    t_param.frame_type = 'data'

                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency( t_param.freq  , rf_if )

                # Get start counters
                if not self._uut[uut_id].ip is u'':  #craton2
                    self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt( rf_if )
                    self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt( rf_if )
                    
                if t_param.proto_id not in self.socket_list[uut_id][rf_if] :
                    if self._uut[uut_id].ip is u'':  #craton2                        
                        self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    else :
                        if rf_if :
                            self.v2x_cli_sniffer_if1 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        else :
                            self.v2x_cli_sniffer_if0 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    

                    # Open general session
                    if self._uut[uut_id].ip is u'':  #craton2
                        self._uut[uut_id].qa_cli(cli_name).register.device_register("hw",self._uut[uut_id].mac_addr,1,"eth1")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("v2x",0,"Secton")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("wdm",3,"Secton")
                    else :
                        self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')

                    # Open sdk Link
                    if self._uut[uut_id].ip is u'':  #craton2
                        self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if - 1, t_param.frame_type, t_param.proto_id) #rf_if - 1
                    else :
                        self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if, t_param.frame_type, t_param.proto_id) 
                        self.num_of_frames_per_socket[t_param.proto_id] = [t_param.frames,0]

                    if self._uut[uut_id].ip is u'':  #craton2 - init Rx counter 
                        self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()                       

                self.socket_list[uut_id][rf_if].append(t_param.proto_id)                


        # Config tx test parameters
        for t_param in self._testParams:

            if ( 'tx_data' in vars(t_param) ):
                self.tx_data = t_param.tx_data
                self.payload_len = None
            elif ( 'payload_len' in vars(t_param) ):
                self.tx_data = int(t_param.payload_len)
                self.payload_len = t_param.payload_len
            else :
                self.tx_data = "dddddddddddddddddddddddd"
                self.payload_len = None
             
            # For Multiple RX convert to list is not list
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx

            # Config tx uut
            for tx in tx_list:
                self.stats.tx_count += 1
                uut_id, rf_if = tx

                # Set start rate
                if self.stats.tx_count == 1:
                    self._frame_rate_hz = t_param.frame_rate_hz
  

                # Configure the Tx power 
                if 'tx_power' in vars(t_param):
                    self.tx_power = t_param.tx_power
                else :
                    self.tx_power = None                    
                if 'data_rate' in vars(t_param):
                    self.datarate = t_param.data_rate
                else :
                    self.datarate = None
                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency(  t_param.freq  , rf_if )
                # Set it to default data mode
                if not 'frame_type' in vars(t_param):
                    t_param.frame_type = 'data'

                #set cli name base on tx + proto_id + if                                
                cli_name = "tx_%d_%x" % ( rf_if, t_param.proto_id )

                if t_param.proto_id not in self.socket_list[uut_id][rf_if] :
                    t_param.tx_cli = cli_name
                else :
                    t_param.tx_cli ="rx_%d_%x" % ( rf_if, t_param.proto_id )                                

                if t_param.proto_id not in self.socket_list[uut_id][rf_if] :
                    self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                    self.tx_list.append( (uut_id, rf_if, cli_name, self.tx_data ,t_param.frames, t_param.frame_rate_hz, t_param) )
                else :
                    self.tx_list.append( (uut_id, rf_if, "rx_%d_%x" % ( rf_if, t_param.proto_id ), self.tx_data ,t_param.frames, t_param.frame_rate_hz, t_param) )
                if t_param.frames :
                    self.stats.total_tx_expected += t_param.frames
                else :
                    self.stats.total_tx_expected += 0

    
                # Get start counters
                if not self._uut[uut_id].ip is u'':  #craton2
                    self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )
                    self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )                    

                if t_param.proto_id not in self.socket_list[uut_id][rf_if] :

                    if self._uut[uut_id].ip is u'':  #craton2
                        self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()
                        time.sleep(1)                                                                        
                    else :
                        self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    

                    # Open general session
                    if self._uut[uut_id].ip is u'':  #craton2
                        self._uut[uut_id].qa_cli(cli_name).register.device_register("hw",self._uut[uut_id].mac_addr,1,"eth1")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("v2x",0,"Secton")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("wdm",3,"Secton")
                    else :
                        self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                    
                    if self._uut[uut_id].ip is u'':  #craton2
                        self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if - 1, t_param.frame_type, t_param.proto_id) #rf_if - 1
                    else :
                        self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if, t_param.frame_type, t_param.proto_id)

                    if self._uut[uut_id].ip is u'':  #craton2 - init Tx counter 
                        self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()                        

                self.socket_list[uut_id][rf_if].append(t_param.proto_id)

                # Verify lowest rate
                if self._frame_rate_hz < t_param.frame_rate_hz: 
                    self._frame_rate_hz = t_param.frame_rate_hz                                    

    def main (self):
        
        thread_list = []        
        if bool(self.v2x_cli_sniffer_if1) :
            self.start_dut_sniffer(self.v2x_cli_sniffer_if1.interface(), 2, "RX")

        self.Tx_Rx()
            
        if ( self._capture_frames == 1):
            
            for rx in self.rx_list:                                
                t = threading.Thread( target = self.get_frames_from_cli_thread, args = (rx,) )
                thread_list.append(t)

            # Starts threads
            for thread in thread_list:
                thread.start()

            for thread in thread_list:
                thread.join()
        else :
            waiting_time = self.get_max_waiting_time()       
            time.sleep(int(float(waiting_time / 1000))+100)

        # stop the threads :
        for stop in self.thread_stop_tx[0] :
            self._uut[0].qa_cli(stop).link.tx_thread_stop()
        for stop in self.thread_stop_tx[1] :
            self._uut[1].qa_cli(stop).link.tx_thread_stop()
        for stop in self.thread_stop_rx[0] :
            self._uut[0].qa_cli(stop).link.rx_thread_stop()
        for stop in self.thread_stop_rx[1] :
            self._uut[1].qa_cli(stop).link.rx_thread_stop()
        # stop the sniffers :
        if bool(self.v2x_cli_sniffer_if0) :
            self.stop_dut_sniffer(1)
        if bool(self.v2x_cli_sniffer_if1) :
            self.stop_dut_sniffer(2)
               

    def Tx_Rx(self) :

        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            cli_n = cli_name.split("_")
            self.frames_NotForUnit_count[cli_n[2]] = 0

        transmit_time = 0
        # get the max waiting time
        for tx in self.tx_list:            
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = (( transmit_time + int(transmit_time * 0.25) ) * 1000 )
       
        for rx in  self.rx_list: 
            uut_id, rf_if, cli_name, frames, _ = rx
            self.stats.rx_uut_count[uut_id] += frames 
            Rx_thread =  (self.socket_list[uut_id][rf_if].count(int("0x"+cli_name.split("_")[2],0)) > 1)
            self._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = self._capture_frames, timeout = rx_timeout , sk = "different" if Rx_thread else None)
            if Rx_thread:
                self.thread_stop_rx[uut_id].append(cli_name)                
            
                   
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            dest_addr = t_param.dest_addr if ( 'dest_addr' in vars(t_param) ) else None
 
            Tx_thread = (self.socket_list[uut_id][rf_if].count(int("0x"+cli_name.split("_")[2],0)) > 1)            
            if ( type(self.tx_data) is int ):
                data = self._uut[uut_id].qa_cli(cli_name).link.transmit(payload_len = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr,power_dbm8 = self.tx_power, data_rate = self.datarate, sk = "different" if Tx_thread else None)
            if ( type(self.tx_data) is str ):
                data = self._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr,power_dbm8 = self.tx_power, data_rate = self.datarate, sk = "different" if Tx_thread else None)
            if Tx_thread:
                self.thread_stop_tx[uut_id].append(cli_name)                   
  
            self.stats.tx_uut_count[uut_id] += frames    

            cli_n = cli_name.split("_")
            if dest_addr:
                if (dest_addr != globals.setup.units.unit(uut_id ^ 1).rf_interfaces[1].mac_addr) :
                    self.frames_NotForUnit_count[cli_n[2]] += frames
                    self.rx_NotForUnit_count += frames                        
             
 
    def analyze_results(self):

        #check the DUT Rx data :
        if ( self._capture_frames == 1 ):
            for rx_dut_data in self.RxDUT_data :
                if rx_dut_data != self.tx_data[6:len(self.tx_data)].lower() :                        
                        print "dutRx_data_mismatch %d " %self.stats.dutRx_data_mismatch                     
                        self.stats.dutRx_data_mismatch +=1
            
        # Rx ref checker :
        
        frames_recived = 0

        help = 0              

        for sniffer_file in self.sniffer_file:
            try :
                cap = pyshark.FileCapture(sniffer_file)
            except Exception as e:
                raise globals.Error("pcap file not exist")               
            for frame_idx,frame in  enumerate(cap): 
                for frames_num in self.num_of_frames_per_socket.keys() :
                    #if frames_num == int("0x"+frame.llc.type[6:10],0)  :
                    if frames_num == int(frame.llc.type,0)  :
                         inc = self.packet_handler(frame,self.num_of_frames_per_socket.get(frames_num)[1],str(self.tx_data)) 
                         frames_recived +=1
                         self.num_of_frames_per_socket.get(frames_num)[1] = inc if inc else self.num_of_frames_per_socket.get(frames_num)[1] +1 if self.num_of_frames_per_socket.get(frames_num)[1] != 65535 else 0 # 65535 = 0xffff
                         
        if frames_recived + self.rx_NotForUnit_count < self.stats.rx_uut_count[1] - 1 :
            self.stats.ref_rx_count_error += self.stats.rx_uut_count[1] - frames_recived

   #Tx counters checker :

        read = 0
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
        
        #dut tx counters :
            if not uut_id :                
                self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters() 
                time.sleep(2)
                if bool(self.read_cnt) :
                    read += self.read_cnt['tx'][1]        
        if read != self.stats.tx_uut_count[uut_id] :
            self.stats.dut_tx_count_error += self.stats.tx_uut_count[uut_id] - read
        
        
        #check the ref Tx counter :
        read = 0
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            if uut_id :                
                self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()
                time.sleep(1)
                read += self.read_cnt['tx'][1]                
        if read != self.stats.tx_uut_count[1] :
            self.stats.ref_tx_count_error +=  self.stats.tx_uut_count[1] - read

        #check the DUT Rx counter :
        read = 0
        for rx in self.rx_list:
            uut_id, rf_if, cli_name, frames, _ = rx            
            if not uut_id :
                self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()  
                time.sleep(1)  
                read += self.read_cnt['rx'][1]     
        cli_n = cli_name.split("_")      
        if read + self.rx_NotForUnit_count != self.stats.rx_uut_count[0] : 
        #if read != self.stats.rx_uut_count[0] :            
            self.stats.dut_rx_count_error += self.stats.rx_uut_count[0] - read        


        if self.stats.tx_uut_count[0] :            
            self.add_limit( "DUT Tx failed counter" , 0 , self.stats.dut_tx_count_error, None , 'EQ')
        if self.stats.rx_uut_count[0] :           
            self.add_limit( "DUT Rx failed counter" , 0 , self.stats.dut_rx_count_error, None , 'EQ')
        if self.stats.tx_uut_count[1] :
            self.add_limit( "ref Tx failed counter" , 0 , self.stats.ref_tx_count_error, None , 'EQ')
        if self.stats.rx_uut_count[1] :
            self.add_limit( "ref Rx failed counter" , 0 , self.stats.ref_rx_count_error, None , 'EQ')     
        if ( self._capture_frames == 1 ):
            self.add_limit( "data value mismatch - ref Tx to DUT Rx (sample)" , 0 ,self.stats.dutRx_data_mismatch , None ,'EQ')      
        if frames_recived :
            self.add_limit( "data value mismatch - DUT Tx to REF Rx" , 0 , self.stats.data_mismatch, None ,'EQ')#frames_recived , 'EQ')
            if self.tx_power :
                self.add_limit( "Rx ref : power mismatch" , 0 , self.stats.power_dbm_error, None ,'EQ')# frames_recived , 'EQ')
            if self.datarate :
                self.add_limit( "Rx ref : data rate mismatch" , 0 , self.stats.data_rate_error, None ,'EQ')# frames_recived , 'EQ')
            if self.payload_len:
                self.add_limit( "Rx ref : data size mismatch" , 0 , self.stats.data_size_error, None ,'EQ')# frames_recived , 'EQ')

        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx

            uut_id, rf_if = rx_list[0]
            link_rx_counters = self._uut[uut_id].qa_cli(t_param.rx_cli).link.read_counters()
            uut_id, rf_if = tx_list[0]
            link_tx_counters = self._uut[uut_id].qa_cli(t_param.tx_cli).link.read_counters()
            time.sleep(1)
            cli_n = t_param.tx_cli.split("_")
            try :
                if self.frames_NotForUnit_count.get(cli_n[2]) :
                    self.add_limit( "(%d,%d), %s 0x%x" % ( uut_id, rf_if, t_param.frame_type, t_param.proto_id), link_tx_counters['tx'][1] , link_rx_counters['rx'][1] , None , 'LE')
                else :
                    self.add_limit( "(%d,%d), %s 0x%x" % ( uut_id, rf_if, t_param.frame_type, t_param.proto_id), link_tx_counters['tx'][1] , link_rx_counters['rx'][1] , None , 'EQ')
            except Exception as e:
                pass #the limit not relevant  

        

    def packet_handler(self, packet, xp_idx, ExpData): 
        data = packet.data.data[6:len(ExpData)-1]
        ind = packet.data.data[0:6]
        if data != ExpData[6:len(ExpData)-1] :
            self.stats.data_mismatch +=1 
        if self.tx_power :
            if (int(packet.radiotap.txpower) / 8) != self.tx_power :
                self.stats.power_dbm_error += 1
        if self.datarate :       
            if packet.wlan_radio.data_rate != self.datarate :
               self.stats.data_rate_error += 1
        if self.payload_len:
            if (len(packet.data.data) - 8) != self.payload_len : 
                self.stats.data_size_error += 1
        if int(xp_idx) != int("0x"+ind,0) :
            self.stats.ref_rx_count_error +=1
            return int("0x"+ind,0) +1
        else :
            return 0
        

        
    def get_max_waiting_time(self):
        # get the max waiting time
        transmit_time = 0
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        
        return rx_timeout

    def start_dut_sniffer(self, cli_interface, idx, type):
            
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(idx)
        if self.dut_embd_sniffer is None :
            self.dut_embd_sniffer = traffic_generator.Panagea4SnifferLinkEmbedded(cli_interface)            
        #add to sniffer list
                            
        sniffer_port = BASE_HOST_PORT + ( (idx - 1) * 10 ) 

        #save for sniffer close...
        self.sniffers_ports.append(sniffer_port)
        self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + "dut" + str(idx) + "_" + type + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
        try:
            time.sleep(2)
            #use the last appended sniffer  file...
            self.dut_host_sniffer.start( if_idx = idx , port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
            time.sleep(1)
            if bool(self.v2x_cli_sniffer_if0):
                self.dut_embd_sniffer.start( if_idx = idx -1 , server_ip = "192.168.120.2" , server_port = sniffer_port, sniffer_type = type)
            time.sleep(1)
            if bool(self.v2x_cli_sniffer_if1):
                self.dut_embd_sniffer.start( if_idx = idx , server_ip = "192.168.120.2" , server_port = sniffer_port, sniffer_type = type)                   
        except  Exception as e:
            raise globals.Error("sniffer start error")
            pass        

    def stop_dut_sniffer(self, idx):

        sniffer_port = BASE_HOST_PORT + ( idx * 17 )
        self.dut_host_sniffer.stop(sniffer_port)
        time.sleep(2)
        #self.dut_embd_sniffer.stop(idx)

    def get_frames_from_cli_thread(self, rx):
        
        log = logging.getLogger(__name__)
        uut_id, rf_if, cli_name, frames, _ = rx        
        
        frm_cnt = 0
        transmit_time  = int(float( 1.0 / self._frame_rate_hz) *  frames * 2) + 5  
        start_time = int(time.clock())
 
        # Start Reading from RX unit
        while True:
            try:
                data = self._uut[uut_id].qa_cli(cli_name).interface().read_until('\r\n', 2)
                if 'RxData' in data:
                    pac1 = data.split("RxData")                    
                    pac2 = pac1[1].split("\r\r\n")
                    packet = pac2[0]    
                    self.RxDUT_data.append(packet[7:len(packet)].lower());
                    frm_cnt += 1                   
            except Exception as e:
                break
                                                      
            # Timeout
            if ( int(time.clock()) - start_time ) > (transmit_time + int(transmit_time * 0.1)):                
                break

            # frame count
            if frm_cnt >= frames:                
                break


class TC_LINK_48hours(TC_LINK):
    
    def __init__(self, methodName = 'runTest', param = None):
        self.frames = 1                
        super(TC_LINK_48hours, self).__init__(methodName, param)

    def runTest(self):
        pass

    def setUp(self):
        super(TC_LINK_48hours, self).setUp()     

    def test_link(self):
        """ Test Tx and Rx 48 hours
            @fn         test_link_tx_rx_48_hours
            @brief      Verify tx and rx abilites
            @details    Test ID	    : TC_SDK5.X_LINK_01
            @see Test Plan	: 
        """       
        super(TC_LINK_48hours, self).test_link() 

    def get_test_parameters(self):
        super(TC_LINK_48hours, self).get_test_parameters()
        for t_param in self._testParams :
            self.dataRate = t_param.frame_rate_hz 
            self.duration = t_param.duration

    def initilization(self):
       super(TC_LINK_48hours, self).initilization()
      
    def unit_configuration(self):
        super(TC_LINK_48hours, self).unit_configuration()

    def main (self):
        
        if bool(self.v2x_cli_sniffer_if1) :
            self.start_dut_sniffer(self.v2x_cli_sniffer_if1.interface(), 2, "RX")
        self.Tx_Rx()
        waiting_time = self.get_max_waiting_time()
        time.sleep(int(float(waiting_time / 1000))+100)
        if bool(self.v2x_cli_sniffer_if0) :
            self.stop_dut_sniffer(1)
        if bool(self.v2x_cli_sniffer_if1) :
            self.stop_dut_sniffer(2)        

    def Tx_Rx(self) :
        
        transmit_time = 0

        self.number_of_frames()

        # get the max waiting time
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / self.dataRate) *  self.frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        for rx in  self.rx_list: 
            uut_id, rf_if, cli_name, frames, _ = rx
            self.stats.rx_uut_count[uut_id] += self.frames
            self._uut[uut_id].qa_cli(cli_name).link.receive( self.frames, print_frame = self._capture_frames, timeout = rx_timeout )

        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            dest_addr = t_param.dest_addr if ( 'dest_addr' in vars(t_param) ) else None

            if ( type(self.tx_data) is int ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(payload_len = tx_data , frames = self.frames, rate_hz = self.dataRate, dest_addr = dest_addr)
            if ( type(self.tx_data) is str ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = tx_data , frames = self.frames, rate_hz = self.dataRate, dest_addr = dest_addr)

            self.stats.tx_uut_count[uut_id] += self.frames

    def number_of_frames (self):
        Seconds = 60 * 60 * self.duration
        self.frames = Seconds * self.dataRate
        
        self.stats.total_tx_expected = self.frames
        self.stats.total_rx_expected = self.frames
        
    def analyze_results(self):
        super(TC_LINK_48hours, self).analyze_results()    

    def get_max_waiting_time(self):
        transmit_time = 0
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / self.dataRate) *  self.frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time
        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000        
        return rx_timeout

    def start_dut_sniffer(self, cli_interface, idx, type):
        super(TC_LINK_48hours, self).start_dut_sniffer(cli_interface, idx, type)

    def stop_dut_sniffer(self, idx):
        super(TC_LINK_48hours, self).stop_dut_sniffer(idx)
 

class TC_LINK_netif_configuration(TC_LINK):

    def __init__(self, methodName = 'runTest', param = None, dataRate = 3, power = 10):
        self.dataRate = dataRate
        self.powerdBm = power
        super(TC_LINK_netif_configuration, self).__init__(methodName, param)

    def runTest(self):
        pass

    def setUp(self):
        super(TC_LINK_netif_configuration, self).setUp()

    def test_link(self):
        """ Test Tx and Rx netif configuration 
            @fn         test_link_tx_rx_netif_configuration
            @brief      Verify tx and rx abilites
            @details    Test ID	    : TC_SDK5.X_LINK_01
            @see Test Plan	: 
        """
        super(TC_LINK_netif_configuration, self).test_link()

    def get_test_parameters(self):
        super(TC_LINK_netif_configuration, self).get_test_parameters()

    def initilization(self):
       super(TC_LINK_netif_configuration, self).initilization()
       
    def unit_configuration(self):
        super(TC_LINK_netif_configuration, self).unit_configuration()

    def main (self):

        thread_list = []
        transmit_time = 0
                
        # get the max waiting time
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        for rx in  self.rx_list: 
            uut_id, rf_if, cli_name, frames, _ = rx
            self._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = self._capture_frames, timeout = rx_timeout )

        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            dest_addr = t_param.dest_addr if ( 'dest_addr' in vars(t_param) ) else None

            if ( type(self.tx_data) is int ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(payload_len = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)
            if ( type(self.tx_data) is str ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)

class Statistics(object):
 
    def __init__(self):
        
        self.uut_counters = tree()                                        
        self.total_tx_expected = 0
        self.tx_count = 0

        self.tx_uut_count = []
        self.rx_uut_count = []
        self.dut_tx_count_error = 0        
        self.dut_rx_count_error = 0        
        self.ref_tx_count_error = 0       
        self.ref_rx_count_error = 0
        self.data_mismatch = 0
        self.dutRx_data_mismatch = 0
        self.power_dbm_error = 0
        self.data_size_error = 0
        self.data_rate_error = 0

class frameStatistics(object):
    pass