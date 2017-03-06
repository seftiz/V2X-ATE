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
        self.dot4_cli = 0
        self.dot4_cli2 = 1
        self.stats = Statistics()

        super(TC_Dot4, self).__init__(methodName, param)

    def test_dot4(self):
        self.log = logging.getLogger(__name__)
  
        #print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )

        #self.get_test_parameters()
        self.unit_configuration()

        self.main()

        self.analyze_results()
        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def get_test_parameters( self ):
        super(TC_Dot4, self).get_test_parameters()
                
    def runTest(self):
        pass
    
    def setUp(self):
        super(TC_Dot4, self).setUp()

    def tearDown(self):
        super(TC_Dot4, self).tearDown()

    def unit_configuration(self):
    
        # Verify uut idx exits
        try:
            self.uut1 = globals.setup.units.unit(self.uut_id1)
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or corrupted, usage : uut_id1=0")

        try:
            self.uut2 = globals.setup.units.unit(self.uut_id2)
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or corrupted, usage : uut_id=1")

        # Open new v2x-cli

        self.dot4_cli = self.uut1.create_qa_cli("dot4_cli", target_cpu = self.target_cpu )
        if self.uut1.external_host != "":
            self._rc = self.dot4_cli.link.device_register("00:02:cc:f0:00:07",0,"eth1")
            self._rc = self.dot4_cli.link.service_register("v2x",0)
            self._rc = self.dot4_cli.link.socket_create(self.if_index - 1, "data", 1234 )
            self._rc = self.dot4_cli.link.socket_tx(1000, 10 )

        #self.dot4_cli2 = self.uut2.create_qa_cli("dot4_cli", target_cpu = self.target_cpu )
        #if self.uut2.external_host != "":
        #    self._rc = self.v2x_cli2.link.service_create("remote")
        #else:
        #    self._rc = self.dot4_cli2.link.service_create("hw") 
        #self._rc = self.dot4_cli2.link.socket_create(self.if_index -1, "data", 1234 )

    def main(self):
        try:
            err_req = TC_Dot4_ERRONEOUS_Request()
            err_req.main()
        except Exception as e:
            raise e
                   
    def analyze_results(self):
        pass

    def print_results(self):
        #function name , sent values
        for i in self.stats.testIncorrectFailed:
            self.add_limit("%s" % i , 0 , 1 , 1, 'EQ')
        #function name , return code
        for i in self.stats.functionFailed:
            self.add_limit("%s" % i , 0 , 1 , 1, 'EQ')
        
############ END Class TC_Dot4 ############
             
class TC_Dot4_ERRONEOUS_Request(TC_Dot4):
    """
    @class TC_Dot4_ERRONEOUS
    @brief Test 
    @author Nomi Rozenkruntz
    @version 0.1
    @date   2/22/2017
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.state_instance = TC_Dot4_State()
        self.error_list = list()
        self.state = None
        self.if_index = 1
        self.time_slots = 0       
        self.channel_id = dict(channel_num = None, op_class = 0)
        self.immediate_access = 0
    
    def main(self):
        self.get_test_parameters()
        self.errouneuos_request()
        
    def get_test_parameters( self ):
        super(TC_Dot4, self).get_test_parameters()
        self.state = self.param.get('state',None)
        self.test_param = self.param.get('params',None)

    def errouneuos_request(self):
        for req in self.test_param:
            rc = self.start_request(req.get(channel_num),
                               req.get(time_slot),
                               req.get(op_class),
                               req.get(immediate_access))
            if rc != -3:
                self.error_list.append("Start request failed for: ..")
            self.end_channel(channel_num)
    
    def start_request(self,ch_num,t_slot,op_class,imm_access):
        request = list()
        request.extend(0,ch_num,t_slot,op_class,imm_access)
        self.dot4_cli.dot4.dot4_channel_start(request)

    def end_channel(self,ch_num): 
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        if rc != 0:
            self.error_list.append("End request failed for: ..")
            
############ END Class TC_Dot4_ERRONEOUS_Request ############

class TC_Dot4_ERRONEOUS_Send(TC_Dot4):
    """
    @class TC_Dot4_ERRONEOUS_Send
    @brief Test 
    @author Nomi Rozenkruntz
    @version 0.1
    @date   2/22/2017
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.send_instance = Generate_Dot4_Send()
        self.state_instance = TC_Dot4_State()
        self.state = None
        
        self.if_index = 1
        self.time_slots = 0       
        self.channel_id = dict(channel_num = 0, op_class = 0)
        self.immediate_access = 0
    
    def main(self):
        self.get_test_parameters()
        self.errouneuos_send()
        
    def get_test_parameters( self ):
        super(TC_Dot4, self).get_test_parameters()
        self.state = self.param.get('state',None)
        self.test_param = self.param.get('params',None)

    def errouneuos_send(self):
        self.state_instance.start_continuous(172)
        for send_p in self.test_param:
            self.start_send(   send_p.get(channel_num),
                               send_p.get(time_slot),
                               send_p.get(op_class),
                               send_p.get(immediate_access))
            
        self.end_channel(channel_num)
     
    def end_channel(self,ch_num):          
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        if rc != 0:
            self.error_list.append("End request failed for: ..")    

############ END Class TC_Dot4_ERRONEOUS_Send ############

class TC_Dot4_Tx(TC_Dot4):
    """
    @class Generate_Dot4_Transmission
    @brief Test transmision while channel switching 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	2/23/2017
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self.send_instance = Generate_Dot4_Send()
        self.request = TC_Dot4_State()
        self.thread_list = []
        self.if_index = 1
    
    def main(self):
        #create_service - uut is configure to rx
        self.socket_create(5678)
        self.create_rx_thread(frames = 5000,timeout = 5000 ,print_frame = 1)
        self.socket_create(5678)
        self.create_tx_thread(frames = 5000,timeout = 5000 ,print_frame = 1)
        for thread in self.thread_list:
            thread.start()
        for thread in self.thread_list:
            thread.join() 
        self.request.start_continuous(172)
        self.request.start_continuous(176)
        
    def create_rx_thread(self,frames, timeout, print_frame):
        self.Rx_count_start = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index) 
                        
        self.receive_thread = threading.Thread(target = self.dot4_cli.link.receive, args = (frames,timeout,print_frame))
        self.thread_list.append(self.receive_thread)
            
        self.Rx_count = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index)

        if(self.Rx_count == self.Rx_count_start) :                
            self.pass_count[1] += 1
        else :          
            self.error_count[1] += 1

    def create_tx_thread(self,frames, timeout, print_frame):
       
        self.Rx_count_start = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index) 
                        
        self.send_thread = threading.Thread(target = self.send_instance.set_send(172), args = (frames,))
        thread_list.append(self.send_thread) 
          
        self.Rx_count = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index)

        if(self.Rx_count == self.Rx_count_start) :                
            self.pass_count[1] += 1
        else :              
            self.error_count[1] += 1

    def socket_create(self,protocol_id):
        self._rc = self.dot4.link.socket_create(self.if_index - 1, "V2X_FRAME_TYPE_DATA_LPD_ETHERTYPE", protocol_id )
    
    def guard_transmit(self):
        """
        change the frames num
        """

    def guard_receive(self):
        """
        change the frames num
        """

############ END Class Generate_Dot4_Transmission ############

class TC_Dot4_Rx(TC_Dot4):
    """
    @class Generate_Dot4_Reception
    @brief Test reception while channel switching 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	2/23/2017
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self.send_instance = Generate_Dot4_Send()
        self.request = TC_Dot4_State()
        self.thread_list = []
        self.if_index = 1
    
    def main(self):
        #create_service - uut is configure to rx
        self.socket_create(1234)
        self.create_rx_thread(frames = 5000,timeout = 5000 ,print_frame = 1)
        self.socket_create(1234)
        self.create_tx_thread(frames = 5000,timeout = 5000 ,print_frame = 1)
        for thread in self.thread_list:
            thread.start()
        for thread in self.thread_list:
            thread.join() 
        self.request.start_continuous(172)
        self.request.start_continuous(176)
        
    def create_rx_thread(self,frames, timeout, print_frame):
        self.Rx_count_start = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index) 
                        
        self.receive_thread = threading.Thread(target = self.v2x_cli2.link.receive, args = (frames,timeout,print_frame))
        self.thread_list.append(self.receive_thread)
            
        self.Rx_count = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index)

        if(self.Rx_count == self.Rx_count_start) :                
            self.pass_count[1] += 1
        else :          
            self.error_count[1] += 1

    def create_tx_thread(self,frames, timeout, print_frame):
       
        self.Rx_count_start = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index) 
                        
        self.send_thread = threading.Thread(target = self._some_sends, args = (frames,))
        thread_list.append(self.send_thread) 
          
        self.Rx_count = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index)

        if(self.Rx_count == self.Rx_count_start) :                
            self.pass_count[1] += 1
        else :              
            self.error_count[1] += 1

    def socket_create(self,protocol_id):
        self._rc = self.dot4.link.socket_create(self.if_index - 1, "V2X_FRAME_TYPE_DATA_LPD_ETHERTYPE", protocol_id )
      
############ END Class Generate_Dot4_Reception ############

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
        #create_service - 2 uuts is configure one to rx, one to tx
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
        self.if_index = 1
        self.time_slots = 0       
        self.channel_id = dict(channel_num = 0, op_class = 0)
        self.immediate_access = 0
        self.send_instance = Generate_Dot4_Send()
    
    def main(self):
        self.continuous_scenario()
        self.continuous_2_continuous_scenario()
        self.alternate_scenario_1()
        self.alternate_scenario_2()
        self.immediate_scenario_1()
        self.immediate_scenario_2()
        self.immediate_scenario_3()        

    def start_continuous(self,ch_num):
        self.time_slots = 3
        self.channel_id[channel_num] = ch_num
        self.channel_id[op_class] = 1 
        self.immediate_access = 255
        self.start_request()

    def start_alternate(self):
        self.time_slots = 2
        self.channel_id[channel_num] = 172
        self.channel_id[op_class] = 1 
        self.immediate_access = 0
        self.start_request()

    def start_immediate(self,ch_num):
        self.time_slots = 3
        self.channel_id[channel_num] = ch_num
        self.channel_id[op_class] = 1 
        self.immediate_access = 10
        self.start_request()

    def continuous_scenario(self):
        self.start_continuous(172)
        self.send_instance.set_send(172)
        """
        start sniffer to verify the sends arrived correctly
        """
        self.end_channel(172)

    def continuous_end_scenario(self):
        self.start_continuous(172)
        self.end_channel(172)
        self.send_instance.set_send("default",True)
        self.end_channel(176)

    def continuous_2_continuous_scenario(self):
        self.start_continuous(172)
        self.start_continuous(176)
        self.send_instance.set_send(176)
        self.end_channel(172)
        self.send_instance.set_send(172)
        self.end_channel(176)

    def immediate_scenario_1(self):
        self.start_alternate(172)
        self.start_immediate(176)
        self.send_instance.set_send(176)
        self.send_instance.set_send(172)
        self.end_channel(172)
        self.end_channel(176)
    
    def immediate_scenario_2(self):
        self.start_alternate(172)
        self.start_alternate(176)
        self.start_immediate(180)
        self.send_instance.set_send(180)
        self.send_instance.set_send(172)
        self.send_instance.set_send(176)
        self.end_channel(172)
        self.end_channel(176)
        self.end_channel(180)

    def immediate_scenario_3(self):
        self.start_immediate(172)

    def alternate_scenario_1(self):
        self.start_alternate(172)
        self.start_alternate(176)
        self.send_instance.set_send(176)
        self.send_instance.set_send(172)
        self.end_channel(176)
        self.send_instance.set_send(176)
        self.send_instance.set_send(172)
        self.send_instance.set_send("default",True)
        self.end_channel(172)

    def alternate_scenario_2(self):
        self.start_continuous(172)
        self.start_immediate(176)
        self.start_alternate(184)
        self.send_instance.set_send(176)
        self.send_instance.set_send(184)
        self.end_channel(172)
        self.end_channel(176)
        self.end_channel(176)

    def start_request(self):
        request = []
        request.append(self.if_index)
        request.append(self.channel_id.get(op_class))
        request.append(self.channel_id.get(channel_num))
        request.append(self.time_slots)
        request.append(self.immediate_access)
        self.dot4_cli.dot4.dot4_channel_start(request)

    def end_channel(self,ch_num):
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        if rc != 0:
            self.error_list.append("End request failed for: ..")

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
        self.frames = 0
        self.rate_hz = 0
        self.payloud_len = None
        self.user_priority = 0
        self.data_rate = None
        self.powerdbm8 = 160
        self.dest_addr = None
        self.op_class = 0
        self.channel_num = 0
        self.tx_data = None
        self.send_param = None
                
    def set_send(self,ch_num,flag = False,frames = 5000 ,rate_hz = 100):
        if flag == False:
            self.channel_num = ch_num
            self.frames = frames
            self.data_rate = 12
            self.user_priority = 7
            self.dot4_cli.dot4.transmit(self.frames,
                                        self.rate_hz,
                                        self.payloud_len,
                                        self.user_priority,
                                        self.data_rate,
                                        self.powerdbm8,
                                        self.dest_addr,
                                        self.op_class,
                                        self.channel_num,
                                        self.tx_data)
        else:
            self.dot4_cli.dot4.transmit_empty()
            
############ END Class Generate_Dot4_Send ############

class Statistics(object):
    def __init__(self):
        #reset counters
        self.testCorrectSuccess = 0
        self.testExactSuccess = 0 
        self.testIncorrectSuccess = 0
        self.testIncorrectFailed = list()
        self.functionFailed = list()
     

