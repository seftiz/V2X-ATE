"""
@file       tc_dot4.py
@brief      Test suite for testing dot4 functionality and api implementation  
@author    	Nomi Rozenkruntz
@version	1.0
@date		February 2017
"""
import os, sys, socket

import unittest, logging, socket, json, json2html
from datetime import datetime
import time, threading, random
from lib import globals, station_setup, HTMLTestRunner
from lib import instruments_manager, packet_analyzer
from tests import common
import webbrowser, re
import pyshark, threading
from lib.instruments import traffic_generator
from utilities import panagea4_sniffer

log = logging.getLogger(__name__)

class TC_Dot4(common.V2X_SDKBaseTest):
    """
    @class TC_Dot4
    @brief Test the dot4 functionality and api
    @author Nomi Rozenkruntz
    @version 0.1
    @date	20/2/2017
    """

    def __init__(self, methodName = 'runTest', param = None):
        super(TC_Dot4, self).__init__(methodName, param)
        self.send_instance = Generate_Dot4_Send()
        self.sniffers_ports = list()
        self.sniffer_file = list()
        self.dot4_cli = None
        self.dot4_cli_sniffer = None
        self.dot4_cli1 = None
        self.dot4_cli_sniffer1 = None
        self.register_flag = False
        self.rx_list = []
        self.tx_list = []
        self.tx_list_ = []
        self.active_cli_list = []
        self._uut = {}
        self.stats = None
        self.state_instance = None
        self.err_req = None
        self.err_send = None
        self.tx_instance = None
        self.rx_instance = None
        self.full_test = None
        
    def test_dot4(self):
        self.stats = Statistics()
        self.state_instance = TC_Dot4_State()
        self.err_req = TC_Dot4_ERRONEOUS_Request()
        self.err_send = TC_Dot4_ERRONEOUS_Send()
        self.tx_instance = TC_Dot4_Tx()
        self.rx_instance = TC_Dot4_Rx()
        self.full_test = TC_Dot4_Full_CS()
        self.log = logging.getLogger(__name__)
  
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )

        self.get_test_parameters()
        self.unit_configuration()

        self.main()

        self.analyze_results()
        #self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def get_test_parameters( self ):
        super(TC_Dot4, self).get_test_parameters()
        g = []
        self._testParams = self.param.get('tx_dict', None )
        for i, t_param in enumerate(self._testParams):
            if 'tx' in vars(t_param):
                g.append(t_param.tx[0])
            if 'rx' in vars(t_param) and not t_param.rx is None:
                g.append(t_param.rx[0])
         
        self.tx_list = set(g)
                        
    def runTest(self):
        pass
    
    def setUp(self):
        super(TC_Dot4, self).setUp()

    def tearDown(self):
        super(TC_Dot4, self).tearDown()

    def unit_configuration(self):
        self._uut[0] = globals.setup.units.unit(0)
        self._uut[1] = globals.setup.units.unit(1)
        # Config rx uut
        for rx_ in self._testParams:
            rx_list = [rx_.rx] if type(rx_.rx) == tuple else rx_.rx
            for rx in rx_list:
                uut_id, rf_if = rx
                #set cli name base on rx + proto_id + if
                cli_name = "rx_%d_%x" % ( rf_if, rx_.proto_id )
                self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                self.rx_list.append( (uut_id, rf_if, cli_name, rx_.frames, rx_) )
                if self._uut[uut_id].external_host is u'':
                    self.dot4_cli_sniffer = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    # Open general session
                    self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                    self.start_dut_sniffer(self.dot4_cli_sniffer.interface(),1,globals.CHS_RX_SNIF) 
                else: 
                    self.dot4_cli = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    if self.register_flag is False:
                        self.register_flag = True
                        #self._rc = self.dot4_cli.link.device_register("00:02:cc:f0:00:07",0,"eth1")
                        #self._rc = self.dot4_cli.link.service_register("v2x",0)
                        self._rc = self.dot4_cli.link.socket_create(0, "data", 0x1234 )
                        self._rc = self.dot4_cli.link.transmit(1000, 10)

        # Config tx uut
        for tx_ in self._testParams:
            tx_list = [tx_.tx] if type(tx_.tx) == tuple else tx_.tx
            for rx in rx_list:
                uut_id, rf_if = self.tx_list
                #set cli name base on tx + proto_id + if
                cli_name = "tx_{}_{}_{}".format( rf_if, tx_.frame_type, tx_.proto_id )
                # Check if cli exists
                try:
                    current_context = self._uut[uut_id].qa_cli(cli_name).get_socket_addr()
                    create_new_cli = False
                except Exception as e:
                    create_new_cli = True
                    if ( create_new_cli == False):
                        cli_name = cli + '_' + '1'
                    self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                    self.tx_list_.append( (uut_id, rf_if, cli_name, tx_.frames, tx_.frame_rate_hz, tx_) )
                    if self._uut[uut_id].external_host is u'':
                        self.dot4_cli_sniffer1 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        # Open general session
                        self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                    else: 
                        self.dot4_cli1 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        if self.register_flag is False:
                            self.register_flag = True
                            self._rc = self.dot4_cli.link.device_register("00:02:cc:f0:00:07",0,"eth1")
                            self._rc = self.dot4_cli.link.service_register("v2x",0)
                 
    def main(self):
        try:
            result = None
                      
            #State Tests:
            #self.stats.results_dic["state_tests"] = self.state_instance.main(self.dot4_cli_sniffer)
            #Erroneuos Start Tests:
            #for i in ("alternate","immediate"):
            #    result = self.err_req.main(i, self.param,self.dot4_cli)
            #    self.stats.results_dic["erroneuous_request_%s" % i].append(result["success"])
            #    self.stats.results_dic["erroneuous_request_%s" % i].extend(result["fail"])
            #result = self.err_req.main("continuous",self.param,self.dot4_cli) #continuous
            #self.stats.results_dic["erroneuous_request_continuous"].append(result["success"])
            #self.stats.results_dic["erroneuous_request_continuous"].extend(result["fail"])
            ##Erroneuos Send Tests:
            #self.stats.results_dic["erroneuous_send"] = self.err_send.main(self.dot4_cli_sniffer,self.param)
            ##Channel Switch Tx Tests:
            #self.stats.results_dic["tx_test"] = self.tx_instance.main()
            ##Channel Switch Rx Tests:
            #self.stats.results_dic["rx_test"] = self.rx_instance.main()
            ##Channel Switch Full Test:
            #self.stats.results_dic["full_test"] = self.full_test.main()
            
        except Exception as e:
            raise e
                   
    def analyze_results(self):
        pass

    def print_results(self):
        #function name , sent values
        for i in self.stats.results_dic:
            if "erroneuous_request" in i:
                if not "continuous" in i:
                    self.add_limit("Dot4 start %s invalid request" % i.split("erroneuous_request_")[1] ,1 ,int(self.stats.results_dic.get(i)[0]) ,4 , 'GE')
                else:
                    self.add_limit("Dot4 start %s invalid request" % i.split("erroneuous_request_")[1] ,1 ,int(self.stats.results_dic.get(i)[0]) ,3 , 'GE')
                for j in self.stats.results_dic.get(i)[1:len(self.stats.results_dic.get(i))]:
                    self.add_limit("Dot4 start %s invalid request" % j.split("state")[0] , 0 , 1 , 1, 'EQ')
    
    def start_dut_sniffer(self, cli_interface, idx, type):
        
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(idx)
        #add to sniffer list
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferAppEmbedded(cli_interface)
                    
        sniffer_port = traffic_generator.BASE_HOST_PORT + ( idx * 17 ) + (1 if type is globals.CHS_TX_SNIF else 0)

        #save for sniffer close...
        self.sniffers_ports.append(sniffer_port)
        self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + "dut" + str(idx) + "_" + str(type) + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
        time.sleep(2)
        #use the last appended sniffer  file...
        self.dut_host_sniffer.start( if_idx = idx, port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
        time.sleep(1)
        self.dut_embd_sniffer.start( if_idx = idx, server_ip = None, server_port = sniffer_port, sniffer_type = type)
        #self._init_sniffers_counters(idx, type)
        """
        if type == globals.CHS_RX_SNIF:
            self._protocol_id_last_seesion_last_frame[idx][self._sch_proto_id]['last_frame_num'] = 0
            self._protocol_id_last_seesion_last_frame[idx][self._cch_proto_id]['last_frame_num'] = 0
            self._protocol_id_last_seesion_last_frame[idx][self._sch_proto_id]['pending_chs_interval_expected_to_fail_count'] = 0
            self._protocol_id_last_seesion_last_frame[idx][self._cch_proto_id]['pending_chs_interval_expected_to_fail_count'] = 0
        """
                
############ END Class TC_Dot4 ############
             
class TC_Dot4_ERRONEOUS_Request():
    """
    @class TC_Dot4_ERRONEOUS
    @brief Test 
    @author Nomi Rozenkruntz
    @version 0.1
    @date   3/6/2017
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.res_dic = dict(success = int(), fail = list())
        self.error_list = list()
        self.dot4_cli = None
        self.not_continuous_flag = None
        self.test_param = None
        self.if_index = 1
        self.time_slots = 0       
        self.channel_id = dict(channel_num = None, op_class = 0)
        self.immediate_access = 0
    
    def main(self,state,param,cli):
        self.res_dic["success"] = 0
        self.res_dic["fail"] = []
        self.dot4_cli = cli
        self.get_test_parameters(param)
        self.erroneous_request(state)
        return self.res_dic
        
    def get_test_parameters( self, param ):
        self.param = param
        self.state = self.param.get('state',None)
        self.test_param = self.param.get('params',None)
        
    def erroneous_request(self,state):
        for req in self.test_param:
            rc = self.start_request(req.get("channel_num"),
                               req.get("time_slot"),
                               req.get("op_class"),
                               req.get("immediate_access"))
            if rc == None:
                self.res_dic["success"] += 1
            else:
                self.res_dic["fail"].append(state.upper() + " state"+  "---to print the parameters????")
                self.end_channel("channel_num")

        if state is not "continuous":
            rc = self.start_request(180,1,1,None)
            if rc == None:
                self.res_dic["success"] += 1
            else:
                self.res_dic["fail"].append(state.upper() + " state"+  "---to print the parameters????")
                self.end_channel("channel_num")

    def start_request(self,ch_num,t_slot,op_class,imm_access):
        request = 0,ch_num,t_slot,op_class,imm_access
        self.dot4_cli.dot4.dot4_channel_start(request)

    def end_channel(self,ch_num): 
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        if rc != 0:
            self.error_list.append("End request failed for: ..")
            
############ END Class TC_Dot4_ERRONEOUS_Request ############

class TC_Dot4_ERRONEOUS_Send():
    """
    @class TC_Dot4_ERRONEOUS_Send
    @brief Test 
    @author Nomi Rozenkruntz
    @version 0.1
    @date   3/6/2017
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.send_instance = Generate_Dot4_Send()
        self.state_instance = TC_Dot4_State()
        self.state = None
        self.dot4_cli = None
        self.if_index = 1
        self.time_slots = 0       
        self.channel_id = dict(channel_num = 0, op_class = 0)
        self.immediate_access = 0
    
    def main(self,dot4_cli,param):
        self.dot4_cli = dot4_cli
        self.get_test_parameters(param)
        self.erroneous_send()
        
    def get_test_parameters( self,param ):
        self.state = param.get('state',None)
        self.test_param = param.get('params',None)

    def erroneous_send(self):
        self.state_instance.start_continuous(172,self.dot4_cli)
        for send_p in self.test_param:
            self.send_instance.send(self.dot4_cli,"D4",send_p.get("channel_num"),
                                    False,
                                    send_p.get("time_slot"),
                                    send_p.get("op_class"))
        self.end_channel(172)
    
    def end_channel(self,ch_num):
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        #if rc != 0:
        #    self.error_list.append("End request failed for: ..")    

############ END Class TC_Dot4_ERRONEOUS_Send ############

class TC_Dot4_Tx(TC_Dot4):
    """
    @class TC_Dot4_Tx
    @brief Test transmision while channel switching 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	3/7/2017
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self.request = TC_Dot4_State()
        self.thread_list = []
        self.if_index = 1
        self.active_cli_list = []
        self.interface = None
        self._sch_proto_id = hex(1234)
        self._cch_proto_id = hex(5678)
            
    def main(self):
        #config tx and rx parameters
        self.unit_configuration()
        self.request.start_continuous(172)
        self.send_instance.send(self.dot4_cli ,"Dot4 Tx",172)
        self.request.start_continuous(176)
        self.send_instance.send(self.dot4_cli ,"Dot4 Tx",172)

    def guard_transmit(self):
        """
        change the frames num
        """

    def guard_receive(self):
        """
        change the frames num
        """
        
    def get_test_frm_data(self):
        frm_tx_data = ""
        for chr in range(self._payload_len):
            frm_tx_data += "".join('{:02x}'.format((chr % 0xFF) + 1))
        return frm_tx_data

    def dut_rx_packet_handler(self, packet):

        if self.check_is_wlan_ack_frame(packet):
            self.stats.total_unicast_ack_frames += 1
            return

        self.stats.total_sniffer_frames_processed += 1

        packet_if_id = int(packet.radiotap.antenna) & 0x0F
        packet_if_id +=1

        #handle first frame in the test
        if int(packet.frame_info.number) == 1:
            self._first_if_sa = packet.wlan.sa
            self._last_frame_info['last_rfif_sa'] = packet.wlan.sa
            #all frames comes on the same physical rf interface - '2' need to destinguish between them...
            self._if_dict[packet.wlan.sa] = 1
        #we do not know where in the time sequence of the Rx CS interval the transmission started so we skipp first protocol id testing and starting from the second
        if packet.wlan.sa == self._first_if_sa:
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_data'] += int(packet.data.len)
            return
        #check if this is the first if sa change and set the second interface for test
        if self._first_if_sa  != None:
            self._if_dict[packet.wlan.sa] = 2
        # Test packet data
        try:
            packet_data = ''.join(packet.data.data.split(':')).encode('ascii','ignore').upper()
        except Exception as e:
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['sniffer_data_read_fail'] +=1
            #count total frames and data (amount in bytes)
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_data'] += int(packet.data.len)
        else:
            # Compare data with transmited Data after extracting crc and extracting Tx buffer (sequence_id, frame_size, frame_options)...
            if packet_data[16:-8] != self._test_frm_data.upper():
                self.stats.counters[self.uut.idx][self._if_dict[packet.wlan.sa]]['sniffer_data_cmp_fail'] += 1
            if len(packet_data[:8]) != self._payload_len:
                self.stats.counters[self.uut.idx][self._if_dict[packet.wlan.sa]]['sniffer_data_payload_len_fail'] += 1
           
            if  packet.wlan.sa !=  self._last_frame_info['last_rfif_sa']:
                # handle first CS - this is the testing starting point...
                if self._first_if_sa  != None:
                    self._first_if_sa  = None
                    #arrival time of last frame
                    #self._last_frame_info['last_rfif_last_frame_ts'] = int(float(packet.frame_info.time_epoch) * 1000)
                    self._last_frame_info['last_rfif_last_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
                    #frame id of last frame
                    self._last_frame_info['last_rfif_frame_id'] = int(packet.frame_info.number)
                    self._last_frame_info['last_rfif_first_frame_id'] = int(packet.frame_info.number)

                    #self._last_frame_info['last_rfif_first_frame_ts']  = int(float(packet.frame_info.time_epoch) * 1000)
                    self._last_frame_info['last_rfif_first_frame_ts']  = (int(packet.radiotap.mactime) / 1000)
                    self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
                    self._last_frame_info['last_rfif_sa'] = packet.wlan.sa
                    #self._last_if_sa = packet.wlan.sa
                    return
           
                #if self._last_frame_info['last_rfif_first_frame_ts'] > 0:
                self.handle_dut_rx_chs_event(packet,  self.uut.idx, self._if_dict[packet.wlan.sa])

                #arrival time of first frame of the interval
                #self._last_frame_info['last_rfif_first_frame_ts'] = int(float(packet.frame_info.time_epoch) * 1000)
                self._last_frame_info['last_rfif_first_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
                self._last_frame_info['last_rfif_first_frame_id'] = int(packet.frame_info.number)
            #arrival time of last frame
            self._last_frame_info['last_rfif_last_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
            #frame id of last frame
            self._last_frame_info['last_rfif_frame_id'] = int(packet.frame_info.number)
            self._last_frame_info['last_rfif_sa'] = packet.wlan.sa
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_frames'] += 1
            self.stats.counters[ self.uut.idx][self._if_dict[packet.wlan.sa]]['total_data'] += int(packet.data.len)
    
    def get_test_frm_data(self):
        frm_tx_data = ""
        for chr in range(self._payload_len):
            frm_tx_data += "".join('{:02x}'.format((chr % 0xFF) + 1))
        return frm_tx_data

    def analyze_results(self):
        self._test_frm_data = self.get_test_frm_data()
        # analyze last file only - DUT rf_if 2 (CS)
        cap = pyshark.FileCapture(self.sniffer_file[len(self.sniffer_file) - 1])
        for frame_idx,frame in  enumerate(cap):
            self.dut_rx_packet_handler(frame)        

############ END Class TC_Dot4_Tx ############

class TC_Dot4_Rx(TC_Dot4):
    """
    @class TC_Dot4_Rx
    @brief Test reception while channel switching 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	3/7/2017
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self.request = TC_Dot4_State()
        self.tx_instance = TC_Dot4_Tx()
        self.thread_list = []
        self.if_index = 1
    
    def main(self):
        #create_service - uut is configure to rx
        self.create_rx_thread(frames = 5000,timeout = 5000 ,print_frame = 1)
        self.socket_create(1234)
        self.create_tx_thread(frames = 5000,timeout = 5000 ,print_frame = 1)
        for thread in self.thread_list:
            thread.start()
        for thread in self.thread_list:
            thread.join() 
        self.request.start_continuous(172)
        self.request.start_continuous(176)
        
    def create_rx_thread(self):
        # Config rx uut
        for t_param in self._testParams:
            if t_param.rx is None:
                continue
            rx_list = [t_param.rx] if type(t_param.rx) == tuple else t_param.rx
            for rx in rx_list:
                uut_id, ch_num = rx
                #set cli name base on rx + proto_id + if
                cli_name = "dut%d_rx_%d_%x" % ( uut_id, ch_num, t_param.proto_id )
                # Get start counters
                self.stats.uut_counters[uut_id][ch_num]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt( ch_num )
                self.stats.uut_counters[uut_id][ch_num]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt( ch_num )
                #Initialization interface to work with     
                interface = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                self.active_cli_list.append( (interface, uut_id, ch_num, cli_name) )
                self.rx_list.append( (interface, uut_id, ch_num, cli_name, t_param.frames, t_param.frame_rate_hz, t_param) )
                t_param.rx_cli = cli_name
                # Open general session
                self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                # Open sdk Link
                self._uut[uut_id].qa_cli(cli_name).link.socket_create(self.if_index,"data", t_param.proto_id)
                self.request.start_continuous(t_param.ch_id)                  

    def create_tx_thread(self):
        for t_param in self._testParams:
            # For Multiple RX convert to list is not list
            tx_list = [t_param.tx] if type(t_param.tx) == tuple else t_param.tx
            # Config tx uut
            for tx in tx_list:
                self.stats.tx_count += 1
                uut_id, ch_num = tx
                # Set start rate
                if self.stats.tx_count == 1:
                    self._frame_rate_hz = t_param.frame_rate_hz
                #set cli name base on tx + proto_id + if
                cli_name = "dut%d_tx_%d_%x" % ( uut_id, ch_num, t_param.proto_id )
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
                    # Get start counters
                    self.stats.uut_counters[uut_id][ch_num]['rx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_rx_cnt(ch_num )
                    self.stats.uut_counters[uut_id][ch_num]['tx_cnt'] = self._uut[uut_id].managment.get_wlan_frame_tx_cnt(ch_num )
                    interface = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    if (create_new_cli == False):
                        self._uut[uut_id].qa_cli(cli_name).set_socket_addr( current_context )
                    else:
                        self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                        self._uut[uut_id].qa_cli(cli_name).link.socket_create(self.if_index - 1, "data", protocol_id)
                    self._uut[uut_id].qa_cli(cli_name).link.dot4_channel_start(rf_if = CHS_TEST_RF_IF, op_class = 1, ch_id = t_param.ch_id, slot_id = t_param.slot_id, im_acc = 0)
                    self.active_cli_list.append( (interface, uut_id, ch_num, cli_name) )
                    self.tx_list.append( (interface, uut_id, ch_num, cli_name, t_param.frames, t_param.frame_rate_hz, t_param) )
                    self.stats.total_tx_expected += t_param.frames
                    # Verify lowest rate
                    if self._frame_rate_hz < t_param.frame_rate_hz: 
                        self._frame_rate_hz = t_param.frame_rate_hz

    def socket_create(self,protocol_id):
        self._rc = self.dot4.link.socket_create( )
      
############ END Class TC_Dot4_Rx ############

class TC_Dot4_Full_CS():
    """
    @class TC_Dot4_Full_CS
    @brief Test transmit and recieve while channel switching 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	2/23/2017
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self.transmit_instance = TC_Dot4_Tx()
        self.receive_instance = TC_Dot4_Rx()
        self.thread_list = []
        self.if_index = 1

    def main(self):
        gps_lock = True
        gps_lock &= self.wait_for_gps_lock( uut, self._gps_lock_timeout_sec )
        if gps_lock == False:
          log.info("GPS Lock failed")
          return 
        #create_service - 2 uuts is configure to dot4 one to rx, one to tx
        #uut1
        self.receive_instance.socket_create(1234)
        self.receive_instance.create_rx_thread(5000,5000,1)
        self.receive_instance.socket_create(1234)
        self.receive_instance.create_tx_thread(5000,5000,1)
        #uut2
        for i in range(1235,1335):
            self.transmit_instance.socket_create(i)
            self.transmit_instance.create_rx_thread(5000,5000,1)
            self.transmit_instance.socket_create(i)
            self.transmit_instance.create_rx_thread(5000,5000,1)
        for thread in self.thread_list:
            thread.start()
        for thread in self.thread_list:
            thread.join() 
        self.request.start_continuous(172)
        self.request.start_continuous(176)

############ END Class TC_Dot4_Full_CS ############

class TC_Dot4_State():
    """
    @class TC_Dot4_State
    @brief Test dot4 start request with all modes 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	3/5/2017
    """
    
    def __init__(self, methodName = 'runTest', param = None):
        self.dot4_cli = None
        self.send_times = dict()
        self.if_index = 1
        self.time_slots = 0       
        self.channel_id = dict(channel_num = 0, op_class = 0)
        self.immediate_access = 0
        self.send_instance = Generate_Dot4_Send()
    
    def main(self,dot4_cli):
        self.dot4_cli = dot4_cli
        self.continuous_scenario()
        self.continuous_2_continuous_scenario()
        self.alternate_scenario_1()
        self.alternate_scenario_2()
        self.immediate_scenario_1()
        self.immediate_scenario_2()
        self.immediate_scenario_3()
        return self.analyze_results()        

    def start_continuous(self,ch_num,cli = None):
        if self.dot4_cli is None:
            self.dot4_cli = cli
        self.time_slots = 3
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 255
        self.start_request()

    def start_alternate(self,ch_num):
        self.time_slots = 2
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 0
        self.start_request()

    def start_immediate(self,ch_num):
        self.time_slots = 3
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 10
        self.start_request()

    def continuous_scenario(self):
        self.start_continuous(172)
        self.send_instance.send(self.dot4_cli ,"Dot4 continuous",172) #expected: success
        self.end_channel(172)

    def continuous_end_scenario(self):
        self.start_continuous(172)
        self.end_channel(172)
        self.send_instance.send(self.dot4_cli ,"Dot4 end",0,True) #expected: success
        self.end_channel(176)

    def continuous_2_continuous_scenario(self):
        self.start_continuous(172)
        self.start_continuous(176)
        self.send_instance.send(self.dot4_cli ,"Dot4 continuous to continuous",176) #expected: success
        self.end_channel(172)
        self.send_instance.send(self.dot4_cli ,"Dot4 continuous to continuous",172) #expected: success
        self.end_channel(176)

    def immediate_scenario_1(self):
        self.start_alternate(172)
        self.start_immediate(176)
        self.send_instance.send(self.dot4_cli ,"Dot4 immediate1",176) #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4",172) #expected: success
        self.end_channel(172)
        self.end_channel(176)
    
    def immediate_scenario_2(self):
        self.start_alternate(172)
        self.start_alternate(176)
        self.start_immediate(180)
        self.send_instance.send(self.dot4_cli ,"Dot4 immediate2",180) #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4 immediate2",172) #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4 immediate2",176) #expected: success
        self.end_channel(172)
        self.end_channel(176)
        self.end_channel(180)

    def immediate_scenario_3(self):
        self.start_immediate(172) #expected: fail

    def alternate_scenario_1(self):
        self.start_alternate(172)
        self.start_alternate(176)
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate1",176) #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate1",172) #expected: success
        self.end_channel(176)                                         #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate1",176) #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate1",172) #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate1",0,True) #expected: success
        self.end_channel(172)

    def alternate_scenario_2(self):
        self.start_continuous(172)
        self.start_immediate(176)
        self.start_alternate(184)
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate2",176) #expected: success
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate2",184) #expected: success
        self.end_channel(172)
        self.end_channel(176)
        self.end_channel(184)

    def alternate_scenario_2(self):
        self.start_continuous(172)
        self.start_alternate(184)
        self.send_instance.send(self.dot4_cli ,"Dot4 alternate2",184) #expected: success, to check: durring not define channel time - there is no transmission
        self.end_channel(172)
        self.end_channel(184)

    def start_request(self):
        request = []
        request.append(self.if_index)
        request.append(self.channel_id.get("op_class"))
        request.append(self.channel_id.get("channel_num"))
        request.append(self.time_slots)
        request.append(self.immediate_access)
        self.dot4_cli.dot4.dot4_channel_start(request)

    def end_channel(self,ch_num):
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        #if rc != 0:
        #    self.error_list.append("End request failed for: ..")

    def analyze_results(self):
        """to be done!!!"""

############ END Class TC_Dot4_State ############

class Generate_Dot4_Send():
    """
    @class Generate_Dot4_Send
    @brief Generate parameters for send request
    @author Nomi Rozenkruntz
    @version 0.1
    @date	2/21/2017
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.dot4_cli = None
        self.sniffers_ports = list()
        self.sniffer_file = list()
        self.frames = 0
        self.rate_hz = 0
        self.payloud_len = None
        self.user_priority = 0
        self.data_rate = None
        self.powerdbm8 = 160
        self.dest_addr = None
        self.op_class = 0
        self.channel_num = 0
        self.time_slot = -1
        self.tx_data = None
        
    def send(self ,dot4_cli ,tx_data ,ch_num ,flag = False ,frames = 5000 ,rate_hz = 100 ,time_slot = 0):
        self.dot4_cli = dot4_cli
        self._testMethodName = "test_dot4"
        if self.dot4_cli.uut.external_host == u'':
            self.start_dut_sniffer(self.dot4_cli.interface(),1,globals.CHS_RX_SNIF,self._testMethodName)
        if flag == False:
            self.channel_num = ch_num
            self.frames = frames
            self.tx_data = tx_data
            self.data_rate = 12
            self.user_priority = 7
            self.dot4_cli.dot4.transmit(self.frames,
                                        self.rate_hz,
                                        self.payloud_len,
                                        self.tx_data,
                                        self.dest_addr,
                                        self.user_priority,
                                        self.data_rate,
                                        self.powerdbm8,
                                        self.op_class,
                                        self.channel_num,
                                        self.time_slot)
        else:
            self.dot4_cli.dot4.transmit_empty()
    
    def start_dut_sniffer(self, cli_interface, idx, type, testMethodName):
        
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(idx)
        #add to sniffer list
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferAppEmbedded(cli_interface)
                    
        sniffer_port = traffic_generator.BASE_HOST_PORT + ( idx * 17 ) + (1 if type is globals.CHS_TX_SNIF else 0)

        #save for sniffer close...
        self.sniffers_ports.append(sniffer_port)
        self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + "dut" + str(idx) + "_" + str(type) + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
        time.sleep(2)
        #use the last appended sniffer  file...
        self.dut_host_sniffer.start( if_idx = idx, port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
        time.sleep(1)
        self.dut_embd_sniffer.start( if_idx = idx, server_ip = None, server_port = sniffer_port, sniffer_type = type)
        #self._init_sniffers_counters(idx, type)
        """
        if type == globals.CHS_RX_SNIF:
            self._protocol_id_last_seesion_last_frame[idx][self._sch_proto_id]['last_frame_num'] = 0
            self._protocol_id_last_seesion_last_frame[idx][self._cch_proto_id]['last_frame_num'] = 0
            self._protocol_id_last_seesion_last_frame[idx][self._sch_proto_id]['pending_chs_interval_expected_to_fail_count'] = 0
            self._protocol_id_last_seesion_last_frame[idx][self._cch_proto_id]['pending_chs_interval_expected_to_fail_count'] = 0
        """  
                
############ END Class Generate_Dot4_Send ############

class Statistics(object):
    def __init__(self):
        #reset counters
        self.results_dic = dict()
        self.results_dic["state_tests"] = list()
        self.results_dic["erroneuous_request_alternate"]  = list()
        self.results_dic["erroneuous_request_continuous"] = list()
        self.results_dic["erroneuous_request_immediate"] = list()
        self.results_dic["erroneuous_send"] = list()
        self.results_dic["tx_test"] = list()
        self.results_dic["rx_test"] = list()
        self.results_dic["full_test"] = list()