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
        self.craton1_if_index = 2
        self.craton2_if_index = 1
        self.sniffers_ports = []
        self.sniffer_file = []
        self.data_file = []
        self.Tx_data_list = []
        self.Tx_cnt_init = [0,0]
        self.Rx_cnt_init = [0,0]
        self.total_rx = 0
        self.Rx_ref = 0
        self.num_of_frames_per_socket = dict()
        
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

        # Verify uut idx exits and get uut object
        #for uut_idx in self._uut_list:
        #    try:
        #        self._uut[uut_idx] = globals.setup.units.unit(uut_idx)
        #    except KeyError as e:
        #        raise globals.Error("uut index and interface input is missing or currpted, usage : _uut_id_tx=(0,1)")

        # Call Test scenarios blocks
        self.initilization()
        self.unit_configuration()        

        self.main()

        #if self._verify_frames:
        self.analyze_results()

        #self.print_results()


    def get_test_parameters( self ):
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
    
        self.v2x_cli_sniffer = None

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
                if uut_id :
                    self.Rx_ref +=1

                t_param.rx_cli = cli_name

                if not 'frame_type' in vars(t_param):
                    t_param.frame_type = 'data'

                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency( t_param.freq  , rf_if )

                # Get start counters
                if not self._uut[uut_id].ip is u'':  #craton2
                    self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt( rf_if )
                    self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt( rf_if )
                    

                if self._uut[uut_id].ip is u'':  #craton2                        
                    self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                else :
                    self.v2x_cli_sniffer = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)

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
                    self.num_of_frames_per_socket[t_param.proto_id] = t_param.frames

                if self._uut[uut_id].ip is u'':  #craton2 - init Rx counter 
                        self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()
                        self.Rx_cnt_init[0] = self.read_cnt['rx'][0]
                
                # Rx frames amount :
                if not self._uut[uut_id].ip is u'':  #craton2
                    self.total_rx += t_param.frames


        # Config tx test parameters
        for t_param in self._testParams:

            if ( 'tx_data' in vars(t_param) ):
                self.tx_data = t_param.tx_data
            elif ( 'payload_len' in vars(t_param) ):
                self.tx_data = int(t_param.payload_len)
            else :
                self.tx_data = "dddddddddddddddddddddddd"
             
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
                    self._uut[uut_id].managment.set_tx_power( t_param.tx_power, rf_if )
                if 'freq' in vars(t_param):
                    self._uut[uut_id].managment.set_rf_frequency(  t_param.freq  , rf_if )
                # Set it to default data mode
                if not 'frame_type' in vars(t_param):
                    t_param.frame_type = 'data'

                #set cli name base on tx + proto_id + if
                cli_name = "tx_{}_{}_{}".format( rf_if, t_param.frame_type, t_param.proto_id )
                t_param.tx_cli = cli_name
                # Check if cli exists
                try:
                    current_context = self._uut[uut_id].qa_cli(cli_name).get_socket_addr()
                    create_new_cli = False
                except Exception as e:
                    create_new_cli = True

                    if ( create_new_cli == False):
                        cli_name = cli + '_' + '1'
                         
                    t_param.tx_cli = cli_name

                    self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                    self.tx_list.append( (uut_id, rf_if, cli_name, self.tx_data ,t_param.frames, t_param.frame_rate_hz, t_param) )
                    self.stats.total_tx_expected += t_param.frames

    
                    # Get start counters
                    if not self._uut[uut_id].ip is u'':  #craton2
                        self.stats.uut_counters[uut_id][rf_if]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt(rf_if )
                        self.stats.uut_counters[uut_id][rf_if]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if )
                        self.Tx_cnt_init[1] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if)

                    if self._uut[uut_id].ip is u'':  #craton2
                        self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()
                        time.sleep(1)
                        self.Tx_cnt_init[0] = self.read_cnt['tx'][0]                        
                        
                    else :
                        self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)

                    # Open general session
                    if self._uut[uut_id].ip is u'':  #craton2
                        self._uut[uut_id].qa_cli(cli_name).register.device_register("hw",self._uut[uut_id].mac_addr,1,"eth1")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("v2x",0,"Secton")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("wdm",3,"Secton")
                    else :
                        self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')

                    if ( create_new_cli == False):
                        self._uut[uut_id].qa_cli(cli_name).set_socket_addr( current_context )
                    else:
                        if self._uut[uut_id].ip is u'':  #craton2
                            self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if - 1, t_param.frame_type, t_param.proto_id) #rf_if - 1
                        else :
                            self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if, t_param.frame_type, t_param.proto_id)

                    if self._uut[uut_id].ip is u'':  #craton2 - init Tx counter 
                        self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()
                        self.Tx_cnt_init[0] = self.read_cnt['tx'][0]

                    # Verify lowest rate
                    if self._frame_rate_hz < t_param.frame_rate_hz: 
                        self._frame_rate_hz = t_param.frame_rate_hz 

                    # open file to Tx data
                    self.data_file.append(open(common.DATA_FILES + 'Exdata_'+ str(uut_id) +'.txt','w'))
                    

    def main (self):
        
        if bool(self.v2x_cli_sniffer) :
            self.start_dut_sniffer(self.v2x_cli_sniffer.interface(), self.craton1_if_index, "RX")
        self.Tx_Rx()
        waiting_time = self.get_max_waiting_time()
        time.sleep(int(float(waiting_time / 1000))+100)
        if bool(self.v2x_cli_sniffer) :
            self.stop_dut_sniffer(self.craton1_if_index)

        for i in self.data_file :
            i.close()

    def Tx_Rx(self) :

        transmit_time = 0
        # get the max waiting time
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
       
        for rx in  self.rx_list: 
            uut_id, rf_if, cli_name, frames, _ = rx
            self.stats.rx_uut_count[uut_id] += frames              
            self._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = self._capture_frames, timeout = rx_timeout )
                   
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            dest_addr = t_param.dest_addr if ( 'dest_addr' in vars(t_param) ) else None
 
            if ( type(self.tx_data) is int ):
                data = self._uut[uut_id].qa_cli(cli_name).link.transmit(payload_len = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)
            if ( type(self.tx_data) is str ):
                data = self._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = tx_data , frames = frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)
            
            self.stats.tx_uut_count[uut_id] += frames 
             
 
    def analyze_results(self):

        d_file = open(self.data_file[0].name,'r')
        frames_recived = 0

        help = 0

        # check Rx referenc : 
        i = 0 # to check if all the frames received according the frame index
        inc_rx_list_len = self.Rx_ref -1
        rx_list_len = inc_rx_list_len
        for sniffer_file in self.sniffer_file:
            try :
                cap = pyshark.FileCapture(sniffer_file)
            except Exception as e:
                raise globals.Error("pcap file not exist")               
            for frame_idx,frame in  enumerate(cap):               
                inc = self.packet_handler(frame,i,self.tx_data) 
                frames_recived +=1
                if not rx_list_len :
                    i = inc if inc else i+1
                    for frames in self.num_of_frames_per_socket.keys() :
                        if i == self.num_of_frames_per_socket.get(frames) :
                            inc_rx_list_len -=1
                    rx_list_len = inc_rx_list_len
                    if i == 249 :
                        help =1
                else :
                    i = inc if inc else i
                    rx_list_len -= 1
        if frames_recived < self.stats.rx_uut_count[1] - 1 :
            self.stats.ref_rx_count_error += self.stats.rx_uut_count[1] - i

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
        if read != self.stats.tx_uut_count[uut_id] :#self.Tx_cnt_init[uut_id] + self.stats.tx_uut_count[uut_id] :
            self.stats.dut_tx_count_error += self.stats.tx_uut_count[uut_id] - read
        
        
        #check the ref Tx counter :
        read = 0
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,frames, frame_rate_hz, t_param = tx
            if uut_id :
                #tx_ref_cnt = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(rf_if) 
                self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()
                time.sleep(1)
                read += self.read_cnt['tx'][1]
                #if tx_ref_cnt != self.Tx_cnt_init[1] + self.stats.tx_uut_count[uut_id] :
        if read != self.stats.tx_uut_count[uut_id] :# self.Tx_cnt_init[uut_id] + self.stats.tx_uut_count[uut_id] :
            self.stats.ref_tx_count_error +=  self.stats.tx_uut_count[uut_id] - read

        #check the DUT Rx counter :
        read = 0
        for rx in self.rx_list:
            uut_id, rf_if, cli_name, frames, _ = rx            
            if not uut_id :
                self.read_cnt = self._uut[uut_id].qa_cli(cli_name).link.read_counters()  
                time.sleep(1)  
                read += self.read_cnt['rx'][1]           
        if read != self.stats.rx_uut_count[uut_id] : #self.Rx_cnt_init[uut_id] + self.stats.rx_uut_count[uut_id]
            self.stats.dut_rx_count_error += self.stats.rx_uut_count[uut_id] - read


        if self.stats.tx_uut_count[0] :
            self.add_limit( "Tx counter DUT" , 0 , self.stats.dut_tx_count_error, self.stats.tx_uut_count[0] , 'EQ')
        if self.stats.rx_uut_count[0] :
            self.add_limit( "Rx counter DUT" , 0 , self.stats.dut_rx_count_error, self.stats.rx_uut_count[0] , 'EQ')
        if self.stats.tx_uut_count[1] :
            self.add_limit( "Tx counter ref" , 0 , self.stats.ref_tx_count_error, self.stats.tx_uut_count[1] , 'EQ')
        if self.stats.rx_uut_count[1] :
            self.add_limit( "Rx counter ref" , 0 , self.stats.ref_rx_count_error, self.stats.rx_uut_count[1] , 'EQ')
        if frames_recived :
            self.add_limit( "data mismatch - Tx DUT to REF" , 0 , self.stats.data_mismatch, frames_recived , 'EQ')

        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx

            uut_id, rf_if = rx_list[0]
            link_rx_counters = self._uut[uut_id].qa_cli(t_param.rx_cli).link.read_counters()
            uut_id, rf_if = tx_list[0]
            link_tx_counters = self._uut[uut_id].qa_cli(t_param.tx_cli).link.read_counters()
            time.sleep(1)
            try :
                self.add_limit( "(%d,%d), %s 0x%x" % ( uut_id, rf_if, t_param.frame_type, t_param.proto_id), link_tx_counters['tx'][1] , link_rx_counters['rx'][1] , None , 'EQ')
            except Exception as e:
                pass #the limit not relevant  

        

    def packet_handler(self, packet, xp_idx, ExpData): 
        data = packet.data.data[4:len(ExpData)-1]
        ind = packet.data.data[0:4]
        if data != ExpData[4:len(ExpData)-1] :
            self.stats.data_mismatch +=1 
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
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferAppEmbedded(cli_interface)
        #add to sniffer list
                            
        sniffer_port = BASE_HOST_PORT + ( idx * 17 ) #+ (1 if type is globals.CHS_TX_SNIF else 0)

        #save for sniffer close...
        self.sniffers_ports.append(sniffer_port)
        self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + "dut" + str(idx) + "_" + type + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
        try:
            time.sleep(2)
            #use the last appended sniffer  file...
            self.dut_host_sniffer.start( if_idx = idx , port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
            time.sleep(1)
            self.dut_embd_sniffer.start( if_idx = idx , server_ip = "192.168.120.2" , server_port = sniffer_port, sniffer_type = type)
            time.sleep( 120 )        
        except  Exception as e:
            time.sleep( 300 )
            pass        

    def stop_dut_sniffer(self, idx):

        sniffer_port = BASE_HOST_PORT + ( idx * 17 )
        self.dut_host_sniffer.stop(sniffer_port)
        time.sleep(2)
        self.dut_embd_sniffer.stop(idx)

class TC_LINK_48hours(TC_LINK):

    def __init__(self, dataRate, duration, frameSize, methodName = 'runTest', param = None):
        self.frames = 1
        self.dataRate = dataRate
        self.duration = duration
        self.frameSize = frameSize
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
        number_of_frames (self, rate, duration, frame_size)
        super(TC_LINK_48hours, self).test_link() 

    def get_test_parameters(self):
        super(TC_LINK_48hours, self).get_test_parameters()

    def initilization(self):
       super(TC_LINK_48hours, self).initilization()
       
    def unit_configuration(self):
        super(TC_LINK_48hours, self).unit_configuration()

    def main (self):
        thread_list = []
        transmit_time = 0

        # get the max waiting time
        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  self.frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        for rx in  self.rx_list: 
            uut_id, rf_if, cli_name, _ = rx
            self._uut[uut_id].qa_cli(cli_name).link.receive( self.frames, print_frame = self._capture_frames, timeout = rx_timeout )

        for tx in self.tx_list:
            uut_id, rf_if, cli_name, tx_data ,self.frames, frame_rate_hz, t_param = tx
            dest_addr = t_param.dest_addr if ( 'dest_addr' in vars(t_param) ) else None

            if ( type(self.tx_data) is int ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(payload_len = tx_data , frames = self.frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)
            if ( type(self.tx_data) is str ):
                self._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = tx_data , frames = self.frames, rate_hz = frame_rate_hz, dest_addr = dest_addr)

    def number_of_frames (self, rate, duration, frame_size):
        self.Seconds = 60 * 60 * duration
        self.MB = Seconds * rate
        self.frames = MB * (MB / frame_size)
 

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
        # Total frame process in the wireshark file
        self.total_frames_processed = 0
        self.frame_seq_err = 0
        
        self.uut_counters = tree()

        self.total_sniffer_frames_processed = 0
        self.total_unicast_ack_frames = 0
        self.sniffer_data_fail = 0
        self.wlan_da_mismatch = 0
        self.user_prio_mismatch = 0
        self.data_rate_mismatch = 0
        self.total_tx_expected = 0
        self.tx_count = 0
        self.sniffer_proto_fail = 0
        self.frame_fields = frameStatistics()

        self.tx_uut_count = []
        self.rx_uut_count = []
        self.dut_tx_count_error = 0        
        self.dut_rx_count_error = 0        
        self.ref_tx_count_error = 0       
        self.ref_rx_count_error = 0
        self.data_mismatch = 0

class frameStatistics(object):
    pass