"""
@file       v2x_api_test.py
@brief        
@author    	Chani Rubinstain
@version	0.1
@date		December 2016
"""
import os, sys, socket
from test.test_threading_local import target


# Get current main file path and add to all searchings
if __name__ == "__main__":

    dirname, filename = os.path.split(os.path.abspath(__file__))
    sys.path.append("c:\\temp\\qa")


import unittest, logging, socket, json, json2html
from datetime import datetime
import time, threading, random
from lib import globals, station_setup, HTMLTestRunner
from lib import instruments_manager, packet_analyzer
#from lib import canbus_manager as canbus
from tests import common
import webbrowser, re
import Queue
from lib import HTMLTestRunner

log = logging.getLogger(__name__)

V2X_DATA_FILE_NAME = "c:\\temp\v2x_data_file.txt"


class V2X_API_TEST(common.V2X_SDKBaseTest):
    """
    @class V2X_API_TEST
    @brief Test the V2X_API 
    @author chani rubinstain
    @version 0.1
    @date	15/12/2016
    """ 

    def __init__(self, methodName = 'runTest', param = None,scen = None):
        self.v2x_cli = None
        self.v2x_cli2 = None
        self.v2x_sim = None
        self.v2x_func_param = []
        self._v2x_frames_list  = None
        self.Error_type  = None
        self.Failures = []
        self.uut_v2x_if = []
        self._uut = {}
        self.error_count = 0
        self.pass_count = 0
        self.if_index = 1
        super(V2X_API_TEST, self).__init__(methodName, param)

    def get_test_parameters( self ):
        super(V2X_API_TEST, self).get_test_parameters()
        self._test_desc = self.param.get('test_desc', '')

        # Get uut index and V2X interface index
        self.uut_id1 = self.param.get('uut_id1', None )
        self.uut_id2 = self.param.get('uut_id2', None )
        if self.uut_id1 is None:
            raise globals.Error("uut index and v2x interface id input is missing or corrupted, usage : uut_id1=0")
        if self.uut_id2 is None:
            raise globals.Error("uut index and v2x interface id input is missing or corrupted, usage : uut_id2=1")

        print "Test parameters for %s :" % self.__class__.__name__
        
        print "{} = {}".format ("uut_id1", self.uut_id1)
        print "{} = {}".format ("uut_id2", self.uut_id2)
        
    def setUp(self):
        super(V2X_API_TEST, self).setUp()

    def tearDown(self):
        super(V2X_API_TEST, self).tearDown()

    def test_v2x(self):

        self.log = logging.getLogger(__name__)
  
        print >> self.result._original_stdout, "Starting : {}".format(self._testMethodName)

        self.setUp()

        self.get_test_parameters()
        self.unit_configuration()

        self.main()

        self.analyze_results()
        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format(self._testMethodName)


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

        self.v2x_cli = self.uut1.create_qa_cli("v2x_cli", target_cpu = self.target_cpu )
        if self.uut1.external_host != "":
            self._rc = self.v2x_cli.link.service_create("remote")
        else:
            self._rc = self.v2x_cli.link.service_create("hw") 
        self._rc = self.v2x_cli.link.socket_create(self.if_index - 1, "data", 1234 )
 
        self.v2x_cli2 = self.uut2.create_qa_cli("v2x_cli", target_cpu = self.target_cpu )
        if self.uut2.external_host != "":
            self._rc = self.v2x_cli2.link.service_create("remote")
        else:
            self._rc = self.v2x_cli2.link.service_create("hw") 
        self._rc = self.v2x_cli2.link.socket_create(self.if_index -1, "data", 1234 )
        
    def instruments_initilization(self):
        
        # Receving and start v2x bus simulator
        self.v2x_sim = globals.setup.instruments.v2x_bus

        if self.v2x_sim is None:
            raise globals.Error("v2x bus simulator is not initailize, please check your configuration")                         
        
    def main(self):

        self.scen = self.param.get('scen', None )

        if self.scen.find("basic") is not -1:
            self._generate_basic_scenario()           # run the v2x function with valid data prameters
        

        if self.scen.find("send_receive") is not -1 or self.scen.find("send_all") is not -1 :      
            self._send_receive_scenario()             # run send and receive functions with valid data prameters 
        if self.scen.find("send_random") is not -1 or self.scen.find("send_all") is not -1 :
            self._send_random_scenario()              # run send function with random
        if self.scen.find("send_invalid") is not -1 or self.scen.find("send_all") is not -1 :
            self._send_invalid_scenario()             # run send function with invalid data prameters
        if self.scen.find("send_edge_cases")is not -1 or self.scen.find("send_all") is not -1:
            self._send_edge_cases()                   # run send function in edge cases
        
        if self.scen.find("dot4_valid") is not -1 or self.scen.find("dot4_all") is not -1 :
            self._dot4_valid_scenario()
        if self.scen.find("dot4_invalid") is not -1 or self.scen.find("dot4_all") is not -1:
            self._dot4_invalid_scenario()             # run the dot4_channel functions with invalid data parameters
        if self.scen.find("dot4_edge_cases") is not -1 or self.scen.find("dot4_all") is not -1:
            self._dot4_edge_cases()                   # run the dot4_channel functions in edge cases 
        if self.scen.find("dot4_specific") is not -1 or self.scen.find("dot4_all") is not -1:
            self._dot4_specific_scenario()            # run the dot4_channel functions in the state machine

        if self.scen.find("socket") is not -1:
            self._socket_scenario()                   # run creat and deleat socket in stress
        if self.scen.find("socket") is not -1:
            self._socket_invalid_scenario()           # run creat and deleat socket with invalid parameters

        if self.scen.find("service_get") is not -1:        
            self._service_get_delete()                # get default service and delete service in stress
        

    def analyze_results(self):
        pass

    def print_results(self):
        self.error_count
        self.pass_count
        self.add_limit( "number of saccessed functions"  , 0 ,self.pass_count , 0 , 'GE')
        self.add_limit( "number of failed functions"  , 0 ,self.error_count , 0 , 'LE')
        pass 
 
    def _generate_basic_scenario(self):

        self._prms = V2X_API_TEST_v_generator()

        self._request = self._prms.request_start_random()
        self._wait = self._prms.wait_random()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc) 
        
        self._request = self._prms.request_end_random()
        self._wait = self._prms.wait_random()
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc)
        
        self._indication = self._prms.indication_random()
        self._wait = self._prms.wait_random()
        self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait)
        self.info_linit("dot4_channel_end_receive",self._rc)
        
        self._rc = self.v2x_cli.link.socket_delete()
        self.info_linit("socket_delete",self._rc)

        self._config = self._prms.socket_config()
        self._rc = self.v2x_cli.link.socket_create_api_test(self._config[0],self._config[1],self._config[2])
        self.info_linit("socket_create",self._rc)
       
    def _send_receive_scenario(self) :
        
        self._send_receive(frames = 1,timeout = 5000 ,print_frame = 1)

        self._send_receive(frames = 20,timeout = 5000 ,print_frame = 1) 

        self._send_receive(frames = 20,timeout = 0 ,print_frame = 1)

        self._send_receive(frames = 150 ,timeout = 486 ,print_frame = 1)

        self._send_receive(frames = 0,timeout = 500 ,print_frame = 1,v_or_inv = 1) 

        self._send_receive(frames = 0,timeout = 0 ,print_frame = 1,v_or_inv = 1) 

        self._send_receive(frames = 20,timeout = 5000 ,print_frame = 0)
            

    def _send_receive(self,frames, timeout, print_frame,v_or_inv = 0):
        thread_list = []

        self.Rx_count_start = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index) 

        #self.add_limit( "receive - Rx count : " + str(self.Rx_count_start) , 0 , 0, None , 'EQ') 
               
        self.receive_thread = threading.Thread(target = self.v2x_cli2.link.receive, args = (frames,timeout,print_frame))
        thread_list.append(self.receive_thread)
        self.send_thread = threading.Thread(target = self._some_sends, args = (frames,))
        thread_list.append(self.send_thread)
        #self.send_thread = threading.Thread(target = self.v2x_cli.link.transmit, args = (None,None,None,frames))
        

        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()     
          
        self.Rx_count = self.uut2.managment.get_wlan_frame_rx_cnt(self.if_index)

        if  v_or_inv :
            if(self.Rx_count == self.Rx_count_start) :
                self.add_limit('function name : receive \nPASS : the Rx not get the Tx frames, Rx_count : ' + str(self.Rx_count) , 0 , 0, None , 'EQ')
            else :
                self.add_limit('function name : receive \nERROR : unknown state, Rx_count : ' + str(self.Rx_count) , 0 , 1, None , 'EQ')
        else :
            if(self.Rx_count == (self.Rx_count_start + frames)) :
                self.add_limit('function name : receive \nPASS : the Rx function get Tx frame, Rx_count : ' + str(self.Rx_count) , 0 , 0, None , 'EQ')
            else :
                self.add_limit('function name : receive \nERROR : the Rx function not get Tx frame, Rx_count : ' + str(self.Rx_count) , 0 , 1, None , 'EQ')

    def _some_sends(self, num_frames):
        for x in range (0,num_frames) :
            self._rc = self.v2x_cli.link.send()    
                           
    def _send_random_scenario(self) :
        self._prms = V2X_API_TEST_v_generator()
        for x in range (0,20) :
            self._send_params = self._prms.send_param_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
            self.info_linit("send",self._rc)
              
    def _send_invalid_scenario(self) :
        self._prms = V2X_API_TEST_inv_generator()
        for x in range (0,20) :
            self._send_params = self._prms.send_param_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
            self.info_linit("send",self._rc,1)

    def _send_edge_cases(self):
        self._prms = V2X_API_TEST_Extreme_cases_generator()
        
        self._send_params = self._prms.send_param(source_address = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(source_address = 0xFFFFFFFFFFFF)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(dest_address = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(dest_address = 0xFFFFFFFFFFFF)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(user_priority = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(user_priority = 0xFF)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(op_class = 1)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(op_class = 4)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(channel_num= 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(channel_num = 0xff)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(datarate_ran = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(datarate_ran = 0xb)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(power_dbm8 = 0xFFFF)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(power_dbm8 = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(expiry_time_ms = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param(expiry_time_ms = 0x7fff)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param()
        self._wait = self._prms.wait(wait = 0)
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param()
        self._wait = self._prms.wait(wait = 1)
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param()
        self._wait = self._prms.wait(wait_usec = 0)
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

        self._send_params = self._prms.send_param()
        self._wait = self._prms.wait(wait_usec = 0xffffffff)
        self._rc = self.v2x_cli.link.send(self._send_params,self._wait)
        self.info_linit("send",self._rc)

    def _socket_scenario(self):
        self._prms = V2X_API_TEST_v_generator()
        self._config = self._prms.socket_config();
        for x in range(0,20) :
            self._config[2] += 1
            self._rc = self.v2x_cli.link.socket_create(self._config[0],self._config[1],self._config[2])
            self.info_linit("socket_create",self._rc)
            self._rc = self.v2x_cli.link.socket_delete()
            self.info_linit("socket_delete",self._rc)

    def _socket_invalid_scenario(self):
        self._prms = V2X_API_TEST_inv_generator()
        for x in range(0,20) :
            self._config = self._prms.socket_config();
            self._rc = self.v2x_cli.link.socket_create(self._config[0],self._config[1],self._config[2])
            self.info_linit("socket_create",self._rc,1)
            self._rc = self.v2x_cli.link.socket_delete()
            self.info_linit("socket_delete",self._rc,1)

    def _dot4_specific_scenario(self) :
        self._prms = V2X_API_TEST_Extreme_cases_generator()
# 1:
        self._request = self._prms.request_start(channel_num = 1,immediate_access = 255)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(channel_num = 1,time_slot = 1,immediate_access = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(channel_num = 1,immediate_access = random.randint(1,254))
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc,1)
        

# 2:
        self._request = self._prms.request_end(channel_num = 1)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc)  
        
        self._request = self._prms.request_start(channel_num = 2,immediate_access = 255)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
       
        self._request = self._prms.request_start(channel_num = 2,time_slot = 1,immediate_access =  random.randint(1,254))
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(channel_num = 2,time_slot = 1,immediate_access = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
# 3:
        self._request = self._prms.request_end(channel_num = 2)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)  
        self.info_linit("dot4_channel_end",self._rc)
        
        self._request = self._prms.request_start(channel_num = 3,immediate_access = 255)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
       
        self._request = self._prms.request_start(channel_num = 3,time_slot = 1,immediate_access = random.randint(1,254))
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(channel_num = 3,time_slot = 1,immediate_access = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(channel_num = 3,time_slot = 0,immediate_access = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
# 4:
        self._request = self._prms.request_end(channel_num = 2)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)  
        self.info_linit("dot4_channel_end",self._rc) 
           
        self._indication = self._prms.indication(channel_num = 2)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait)
        self.info_linit("dot4_channel_end_receive",self._rc)
        
        self._request = self._prms.request_start(channel_num = 3,immediate_access = 255)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(channel_num = 3,time_slot = 1,immediate_access = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(channel_num = 3,time_slot = 1,immediate_access = random.randint(1,254))
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
# 5:
        self._request = self._prms.request_end(channel_num = 2)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc,1)
        
        self._request = self._prms.request_end(channel_num = 2)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc,1)
        
        self._request = self._prms.request_start(channel_num = 2,immediate_access = random.randint(1,254))
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc,1)
        
        self._request = self._prms.request_start(channel_num = 2,time_slot = 1,immediate_access = random.randint(1,254))
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc,1)
        
        self._request = self._prms.request_start(channel_num = 2,time_slot = random.randint(0,1),immediate_access = 255)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc,1)
  
    def _dot4_valid_scenario(self) :
        self._prms = V2X_API_TEST_v_generator()
        for x in range(0,20):
            self._request = self._prms.request_start_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
            self.info_linit("dot4_channel_start",self._rc)
            
            self._request = self._prms.request_end_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
            self.info_linit("dot4_channel_end",self._rc)
            
            self._indication = self._prms.indication_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait) 
            self.info_linit("dot4_channel_end_receive",self._rc) 
      
    def _dot4_invalid_scenario(self):
        self._prms = V2X_API_TEST_inv_generator()
        for x in range(0,20):
            self._request = self._prms.request_start_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
            self.info_linit("dot4_channel_start",self._rc,1)
            
            self._request = self._prms.request_end_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
            self.info_linit("dot4_channel_end",self._rc,1)
            
            self._indication = self._prms.indication_random()
            self._wait = self._prms.wait_random()
            self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait) 
            self.info_linit("dot4_channel_end_receive",self._rc,1)            

    def _dot4_edge_cases(self):
        self._prms = V2X_API_TEST_Extreme_cases_generator()

        self._request = self._prms.request_start(immediate_access = 0)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start(immediate_access = 255)
        self._wait = self._prms.wait()
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start()
        self._wait = self._prms.wait(wait = 0)
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start()
        self._wait = self._prms.wait(wait = 1)
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)

        self._request = self._prms.request_start()
        self._wait = self._prms.wait(wait_usec = 0)
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_start()
        self._wait = self._prms.wait(wait_usec = 0xffffffff)
        self._rc = self.v2x_cli.link.dot4_channel_start(self._request,self._wait)
        self.info_linit("dot4_channel_start",self._rc)
        
        self._request = self._prms.request_end()
        self._wait = self._prms.wait(wait = 0)
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc)
        
        self._request = self._prms.request_end()
        self._wait = self._prms.wait(wait = 1)
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc)

        self._request = self._prms.request_end()
        self._wait = self._prms.wait(wait_usec = 0)
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc)
        
        self._request = self._prms.request_end()
        self._wait = self._prms.wait(wait_usec = 0xffffffff)
        self._rc = self.v2x_cli.link.dot4_channel_end(self._request,self._wait)
        self.info_linit("dot4_channel_end",self._rc)
       
        self._indication = self._prms.indication()
        self._wait = self._prms.wait(wait = 0)
        self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait) 
        self.info_linit("dot4_channel_end_receive",self._rc)
        
        self._indication = self._prms.indication()
        self._wait = self._prms.wait(wait = 1)
        self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait) 
        self.info_linit("dot4_channel_end_receive",self._rc)

        self._indication = self._prms.indication()
        self._wait = self._prms.wait(wait_usec = 0)
        self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait) 
        self.info_linit("dot4_channel_end_receive",self._rc)
        
        self._indication = self._prms.indication()
        self._wait = self._prms.wait(wait_usec = 0xffffffff)
        self._rc = self.v2x_cli.link.dot4_channel_end_receive(self._indication,self._wait) 
        self.info_linit("dot4_channel_end_receive",self._rc)
       
    def _service_get_delete(self) :
        for x in (0,20) :
            self._rc = self.v2x_cli.link.default_service_get()
            self.info_linit("default_service_get",self._rc)
            self._rc = self.v2x_cli.link.service_delete_api_test()
            self.info_linit("service_delete",self._rc)

    def info_linit(self,func_name, rc, pass_or_fail = 0 ) :
        self.html = HTMLTestRunner._TestResult()
        if pass_or_fail :
            if 'PASS' in rc:
                self.add_limit( "function name : " + func_name + " ERROR - the function run with invalid argoment"   , 0 , 1, None , 'EQ') 
                self.error_count += 1                
            elif 'ERROR' in rc:
                self.err1 = rc.split("ERROR")
                self.err2 = self.err1[1]
                self.err3 = self.err2.split("\r")
                self.add_limit( "function name : " + func_name + " PASS : the error message - " + self.err3[0]  , 0 , 0, None , 'EQ')
                self.pass_count += 1                               
            else :
                self.add_limit( "function name : " + func_name + " unknown state"   , 0 , 1, None , 'EQ')
                self.error_count += 1                
        else :
            if 'ERROR' in rc:
                self.err1 = rc.split("ERROR")
                self.err2 = self.err1[1]
                self.err3 = self.err2.split("\r")
                self.add_limit( "function name : " + func_name + " ERROR" + self.err3[0]  , 0 , 1, None , 'EQ') 
                self.error_count += 1                
            elif 'PASS' in rc:
                self.err1 = rc.split("PASS")
                self.err2 = self.err1[1]
                self.err3 = self.err2.split("\r")
                self.add_limit( "function name : " + func_name + " PASS" + self.err3[0] , 0 , 0, None , 'EQ') 
                self.pass_count += 1                
            else :
                self.add_limit( "function name : " + func_name + " unknown state"   , 0 , 1, None , 'EQ')
                self.error_count += 1                


""" GENERATOR : """
"""-------------"""

class V2X_API_TEST_v_generator():
    """
    @class TC_V2X_v_generator
    @generate valid prameters  
    @author chani rubinstain
    @version 0.1
    @date	15/12/2016
    """ 

    def __init__(self):
        self._if_index = 0 #(0-2)
        self._op_class = 0 #1,2,3,4
        self._channel_num = 0 #(0-255)
        self._time_slot = 0
        self._immediate_access = 0
        self._reason = 0 #0,1
        self._datarate = 0 #0,6,9,12,18,24,36,48,54,72,96,108
        self._power_dbm8 = 0 #(0-0xffff)
        self._wait = 0
        self._netif_index = 0 #integer

    def request_start_random (self):
        self._if_index = random.randint(1,2)
        self._op_class = random.randint(0,4)
        self._channel_num = random.randint(0,0xFF)
        self._time_slot = random.randint(0,1)
        self._immediate_access = random.randint(0,0xFF)
        return [self._if_index,self._op_class,self._channel_num,self._time_slot,self._immediate_access]

    def request_end_random (self):
        self._if_index = random.randint(1,2)
        self._op_class = random.randint(0,4)
        self._channel_num = random.randint(0,0xFF)
        return [self._if_index,self._op_class,self._channel_num]

    def indication_random (self):
        self._if_index = random.randint(1,2)
        self._op_class = random.randint(0,4)
        self._channel_num = random.randint(0,0xFF)
        self._reason = random.randint(0,1)
        return [self._if_index,self._op_class,self._channel_num,self._reason]

    def profile_random(self):
        self._if_index = random.randint(0,2)
        self._op_class = random.randint(0,4)
        self._channel_num = random.randint(0,0xFF) 
        self._datarate_ran =  random.randint(0,0xb) 
        if self._datarate_ran == 0 :
            self._datarate = 0  
        if self._datarate_ran == 1 :
            self._datarate = 6
        if self._datarate_ran == 2 :
            self._datarate = 9
        if self._datarate_ran == 3 :
            self._datarate = 12
        if self._datarate_ran == 4 :
            self._datarate = 18
        if self._datarate_ran == 5 :
            self._datarate = 24
        if self._datarate_ran == 6 :
            self._datarate = 36
        if self._datarate_ran == 7 :
            self._datarate = 48 
        if self._datarate_ran == 8 :
            self._datarate = 54 
        if self._datarate_ran == 9 :
            self._datarate = 72 
        if self._datarate_ran == 10 :
            self._datarate = 96 
        if self._datarate_ran == 11 :
            self._datarate = 108   
        self._power_dbm8 = random.randint(-20,20)
        return [self._if_index,self._op_class,self._channel_num,self._datarate,self._power_dbm8]

    def send_param_random(self):
        self._source_address = random.randint(0, 0xFFFFFFFFFFFF)
        self._dest_address = random.randint(0, 0xFFFFFFFFFFFF)
        self._user_priority = random.randint(0,7)
        self._op_class = random.randint(1,4)
        self._channel_num = random.randint(0,0xFF)
        self._datarate_ran =  random.randint(0,0xb) 
        if self._datarate_ran == 0 :
            self._datarate = 0  
        if self._datarate_ran == 1 :
            self._datarate = 6
        if self._datarate_ran == 2 :
            self._datarate = 9
        if self._datarate_ran == 3 :
            self._datarate = 12
        if self._datarate_ran == 4 :
            self._datarate = 18
        if self._datarate_ran == 5 :
            self._datarate = 24
        if self._datarate_ran == 6 :
            self._datarate = 36
        if self._datarate_ran == 7 :
            self._datarate = 48 
        if self._datarate_ran == 8 :
            self._datarate = 54 
        if self._datarate_ran == 9 :
            self._datarate = 72 
        if self._datarate_ran == 10 :
            self._datarate = 96 
        if self._datarate_ran == 11 :
            self._datarate = 108   
        self._power_dbm8 = random.randint(-20,20)
        self._expiry_time_ms = random.randint(0,0x7FFF)
        return [self._source_address,self._dest_address,self._user_priority,self._op_class,self._channel_num,self._datarate,self._power_dbm8,self._expiry_time_ms]

    def receive_param_random(self):
        self.data_size = random.randint(0,1)
        return self.data_size

    def wait_random (self):
        self._wait_type = random.randint(0,1)
        self._wait_usec = random.randint(0,0xffffffff)
        return [self._wait_type,self._wait_usec]

    def netif_index_random(self):
        self._netif_index = random.randint(0,0xFFFF);
        return self._netif_index

    def subscriber_config_random(self):
        self._if_index = random.randint(0,2)
        self._type = random.randint(0,1)
        return [self._if_index,self._type]

    def socket_config(self):
        self._if_index = random.randint(0,1) 
        self._frame_type = "data" #random.randint(0,1)
        self._pritocol_id = 4660 #random.randint(0,0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)     
        return [self._if_index,self._frame_type,self._pritocol_id] 

class V2X_API_TEST_inv_generator():
    """
    @class TC_V2X_inv_generator
    @generate invalid prameters 
    @author chani rubinstain
    @version 0.1
    @date	15/12/2016
    """ 
    def __init__(self):
        self._if_index = 0 #(0-2)
        self._op_class = 0 #1,2,3,4
        self._channel_num = 0 #(0-255)
        self._reason = 0 #0,1
        self._datarate = 0 #0,6,9,12,18,24,36,48,54,72,96,108
        self._power_dbm8 = 0 #(0-0xffff)
        self._wait = 0

    def request_start_random (self):
        self._if_index = random.randint(3,0xff)
        self._op_class = random.randint(5,10)
        self._channel_num = random.randint(0x100,0xfff)
        self._time_slot = random.randint(4,255)
        self._immediate_access = random.randint(0x100,0xfff)
        return [self._if_index,self._op_class,self._channel_num,self._time_slot,self._immediate_access]

    def request_end_random (self):
        self._if_index = random.randint(3,0xff)
        self._op_class = random.randint(5,10)
        self._channel_num = random.randint(0x100,0xfff)
        return [self._if_index,self._op_class,self._channel_num]

    def indication_random (self):
        self._if_index = random.randint(3,0xff)
        self._op_class = random.randint(5,10)
        self._channel_num = random.randint(0x100,0xfff)
        self._reason = random.randint(3,10)
        return [self._if_index,self._op_class,self._channel_num,self._reason]

    def profile_random(self):
        self._if_index = random.randint(3,0xff)
        self._op_class = random.randint(5,10)
        self._channel_num = random.randint(1,0xFF) 
        self._datarate_ran =  random.ranint(0,0xb) 
        if self._datarate_ran == 0 :
            self._datarate = random.randint()  
        if self._datarate_ran == 1 :
            self._datarate = random.randint(1,5)
        if self._datarate_ran == 2 :
            self._datarate = random.randint(7,8)
        if self._datarate_ran == 3 :
            self._datarate = random.randint(10,11)
        if self._datarate_ran == 4 :
            self._datarate = random.randint(13,17)
        if self._datarate_ran == 5 :
            self._datarate = random.randint(19,23)
        if self._datarate_ran == 6 :
            self._datarate = random.randint(25,35)
        if self._datarate_ran == 7 :
            self._datarate = random.randint(37,47) 
        if self._datarate_ran == 8 :
            self._datarate = random.randint(39,53) 
        if self._datarate_ran == 9 :
            self._datarate = random.randint(55,71) 
        if self._datarate_ran == 10 :
            self._datarate = random.randint(73,95)
        if self._datarate_ran == 11 :
            self._datarate = random.randint(97,107)  
        self._power_dbm8 = random.randint(21,0xFFFF)
        return [_if_index,_op_class,_channel_num,self._datarate,_power_dbm8]

    def send_param_random(self):
        self._source_address = random.randint(0, 0xFFFFFFFFFFFF)
        self._dest_address = random.randint(0, 0xFFFFFFFFFFFF)
        self._user_priority = random.randint(8,0xFF)
        self._op_class = random.randint(5,0xFF)
        self._channel_num = random.randint(0x100,0xFFF)
        self._datarate_ran =  random.randint(0,0xb) 
        if self._datarate_ran == 0 :
            self._datarate = random.randint(1,5)  
        if self._datarate_ran == 1 :
            self._datarate = random.randint(1,5)
        if self._datarate_ran == 2 :
            self._datarate = random.randint(7,8)
        if self._datarate_ran == 3 :
            self._datarate = random.randint(10,11)
        if self._datarate_ran == 4 :
            self._datarate = random.randint(13,17)
        if self._datarate_ran == 5 :
            self._datarate = random.randint(19,23)
        if self._datarate_ran == 6 :
            self._datarate = random.randint(25,35)
        if self._datarate_ran == 7 :
            self._datarate = random.randint(37,47) 
        if self._datarate_ran == 8 :
            self._datarate = random.randint(39,53) 
        if self._datarate_ran == 9 :
            self._datarate = random.randint(55,71) 
        if self._datarate_ran == 10 :
            self._datarate = random.randint(73,95)
        if self._datarate_ran == 11 :
            self._datarate = random.randint(97,107)  
        self._power_dbm8 = random.randint(21,0xFFFF)
        self._expiry_time_ms = random.randint(0,0x7FFF)
        return [self._source_address,self._dest_address,self._user_priority,self._op_class,self._channel_num,self._datarate,self._power_dbm8,self._expiry_time_ms]

    def receive_param_random(self):
        self.data_size = random.randint(2,0xFF)
        return self.data_size

    def wait_random (self):
        self._wait_type = random.randint(2,255)
        self._wait_usec = random.randint(0x100000000,0xfffffffff)
        return [self._wait_type,self._wait_usec]

    def socket_config(self):
        self._if_index = random.randint(3,0xFF) 
        self._frame_type = random.randint(2,0xFF)
        self._pritocol_id =  random.randint(0,0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)     
        return [self._if_index,self._frame_type,self._pritocol_id]

    
        
 
class V2X_API_TEST_Extreme_cases_generator():
    """
    @class TC_V2X_inv_generator
    @generate specific prameters  
    @author chani rubinstain
    @version 0.1
    @date	15/12/2016
    """        

    def __init__(self):
        self._if_index = 0 #(0-2)
        self._op_class = 0 #1,2,3,4
        self._channel_num = 0 #(0-255)
        self._reason = 0 #0,1
        self._datarate = 0 #0,6,9,12,18,24,36,48,54,72,96,108
        self._power_dbm8 = 0 #(0-0xffff)
        self._wait = 0

    def request_start (self,if_index = random.randint(0,2),op_class = random.randint(1,4) ,channel_num = random.randint(0,0xFF),time_slot = random.randint(0,3),immediate_access = random.randint(0,0xFF)):
        self._if_index = if_index
        self._op_class = op_class
        self._channel_num = channel_num
        self._time_slot = time_slot
        self._immediate_access = immediate_access
        return [self._if_index,self._op_class,self._channel_num,self._time_slot,self._immediate_access]

    def request_end (self,if_index = random.randint(0,2),op_class = random.randint(1,4),channel_num = random.randint(0,0xFF)):
        self._if_index = if_index
        self._op_class = op_class
        self._channel_num = channel_num
        return [self._if_index,self._op_class,self._channel_num]

    def indication (self,if_index = random.randint(0,2),op_class = random.randint(1,4),channel_num = random.randint(0,0xFF),reason = random.randint(0,1)):
        self._if_index = if_index
        self._op_class = op_class
        self._channel_num = channel_num
        self._reason = reason
        return [self._if_index,self._op_class,self._channel_num,self._reason]

    def profile(self,if_index,op_class,channel_num,datarate_run,power_dbm8):
        self._if_index = if_index
        self._op_class = op_class
        self._channel_num =  channel_num
        self._datarate_run = datarate_run
        self._power_dbm8 = power_dbm8
        return [_if_index,_op_class,_channel_num,self._datarate,_power_dbm8]

    def wait (self,wait = random.randint(0,1),wait_usec = random.randint(0,0xffffffff)):
        self._wait_type = wait
        self._wait_usec = wait_usec
        return [self._wait_type,self._wait_usec]

    def send_param(self, source_address = random.randint(0, 0xFFFFFFFFFFFF), dest_address = random.randint(0, 0xFFFFFFFFFFFF), user_priority = random.randint(0,7), op_class = random.randint(1,4), channel_num = random.randint(0,0xFF), datarate_ran = random.randint(0,0xb), power_dbm8 = random.randint(-20,20), expiry_time_ms = random.randint(0,0x7FFF)):
        self._source_address = source_address
        self._dest_address = dest_address
        self._user_priority = user_priority
        self._op_class = op_class
        self._channel_num = channel_num
        self._datarate_ran = datarate_ran 
        if self._datarate_ran == 0 :
            self._datarate = 0  
        if self._datarate_ran == 1 :
            self._datarate = 6
        if self._datarate_ran == 2 :
            self._datarate = 9
        if self._datarate_ran == 3 :
            self._datarate = 12
        if self._datarate_ran == 4 :
            self._datarate = 18
        if self._datarate_ran == 5 :
            self._datarate = 24
        if self._datarate_ran == 6 :
            self._datarate = 36
        if self._datarate_ran == 7 :
            self._datarate = 48 
        if self._datarate_ran == 8 :
            self._datarate = 54 
        if self._datarate_ran == 9 :
            self._datarate = 72 
        if self._datarate_ran == 10 :
            self._datarate = 96 
        if self._datarate_ran == 11 :
            self._datarate = 108   
        self._power_dbm8 = power_dbm8
        self._expiry_time_ms = expiry_time_ms
        return [self._source_address,self._dest_address,self._user_priority,self._op_class,self._channel_num,self._datarate,self._power_dbm8,self._expiry_time_ms]