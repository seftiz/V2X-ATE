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

from collections import defaultdict
import collections
def tree(): return defaultdict(tree)

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
        self.expected_frames = 0

    def test_dot4(self):
        """Testsuite for testing channel switching
        @class TC_Dot4
        @main class Test the dot4 functionality and api
        """
        self.stats = Statistics()
        self.state_instance = TC_Dot4_State()
        self.err_req = TC_Dot4_ERRONEOUS_Request()
        self.err_send = TC_Dot4_ERRONEOUS_Send()
        self.tx_instance = TC_Dot4_Tx()
        self.rx_instance = TC_Dot4_Rx()
        self.full_test = TC_Dot4_Full_CS()
    
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )

        self.get_test_parameters()
        self.initilization()
        self.main()
        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def get_test_parameters( self ):
        super(TC_Dot4, self).get_test_parameters()
        g = []
        self._testParams = self.param.get('tx_dict', None )
        if self._testParams is None:
            self._testParams = self.param.get('link_dict', None )
            if self._testParams is None:
                self._testParams = self.param.get('rx_dict', None )
            if self._testParams is None:
                self._testParams = self.param.get('rxtx_dict', None )
        for i, t_param in enumerate(self._testParams):
            print "Param {} : {}".format ( i, ', '.join( "%s=%r" % (t,self.cap(str(v),10)) for t,v in t_param.__dict__.iteritems()) )
            if 'tx' in vars(t_param):
                g.append(t_param.tx[0])
            if 'rx' in vars(t_param) and not t_param.rx is None:
                g.append(t_param.rx[0])
        self.tx_list = set(g)
 
    def runTest(self):
        pass
    
    def setUp(self):
        super(TC_Dot4, self).setUp()

    def unit_configuration(self):
        # Config rx uut
        for rx_ in self._testParams:
            rx_list = [rx_.rx] if type(rx_.rx) == tuple else rx_.rx
            for rx in rx_list:
                uut_id, rf_if = rx
                #set cli name base on rx + proto_id + if
                cli_name = "rx_%d_%x" % ( rf_if, rx_.proto_id )
                self.active_cli_list.append( (uut_id, rf_if, cli_name) )
                #ref unit:
                if self._uut[uut_id].external_host is u'':
                    self.dot4_cli_sniffer = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    self.rx_list.append( (uut_id, rf_if, cli_name, rx_.frames, rx_.proto_id, rx_) )
                    
                    self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                #dut:
                else:
                    self.rx_list.append( (uut_id, rf_if, cli_name, rx_.frames, rx_.proto_id,rx_.ch_idx,rx_.op_class,rx_.time_slot, rx_.tx_power, rx_.print_, rx_) )
                    self.expected_frames += rx_.frames
                    self.dot4_cli = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    if self.register_flag is False:
                        self.register_flag = True
                        self._uut[uut_id].qa_cli(cli_name).register.device_register("hw",self._uut[uut_id].mac_addr,1,"eth1")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("v2x",0,"Secton")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("wdm",3,"Secton")
                self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if, "data", rx_.proto_id)

        # Config tx uut
        for tx_ in self._testParams:
            tx_list = [tx_.tx] if type(tx_.tx) == tuple else tx_.tx
            for tx in tx_list:
                uut_id, rf_if = tx
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
                    #ref unit:
                    if self._uut[uut_id].external_host is u'':
                        self.tx_list_.append( (uut_id, rf_if, cli_name,tx_.frames ,tx_.proto_id,tx_.frame_rate_hz ,tx_) )
                        self.dot4_cli_sniffer1 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        # Open general session
                        self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                    #dut:
                    else:
                        self.tx_list_.append( (uut_id, rf_if, cli_name, tx_.frames , tx_.proto_id, tx_.frame_type, tx_.frame_rate_hz, tx_.ch_idx, tx_.time_slot, tx_.op_class, tx_.tx_power, tx_) )
                        self.expected_frames += tx_.frames
                        self.dot4_cli1 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        if self.register_flag is False:
                            self.register_flag = True
                            self._uut[uut_id].qa_cli(cli_name).register.device_register("hw",self._uut[uut_id].mac_addr,1,"eth1")
                            self._uut[uut_id].qa_cli(cli_name).register.service_register("v2x",0,"Secton")
                            self._uut[uut_id].qa_cli(cli_name).register.service_register("wdm",3,"Secton")
                    self._uut[uut_id].qa_cli(cli_name).link.socket_create(rf_if, "data", tx_.proto_id)
                     
    def main(self):
        try:
            result = None

            test_type = self.param.get('link_dict', None )
            if test_type is None:
                test_type = self.param.get('params', None )
                if test_type is None:
                    test_type = self.param.get('send_dict', None )
                    if test_type is None:
                        test_type = self.param.get('tx_dict', None )
                        if test_type is None:
                            test_type = self.param.get('rx_dict', None )
                            if test_type is None:
                                test_type = self.param.get('rxtx_dict',None)
                                if test_type is None:
                                    raise globals.Error("input is missing or corrupted")
                                else:
                                    #Full channel Switching Tests:
                                    result = self.full_test.main(self)
                                    self.stats.results_dic["full_test"].extend(result["Tx"])
                                    self.stats.results_dic["full_test"].extend(result["Rx"])
                            else:
                                #Channel Switch Rx Tests:
                                self.stats.results_dic["rx_test"] = self.rx_instance.main(self)
                        else:
                            #Channel Switch Tx Tests:
                            self.stats.results_dic["tx_test"] = self.tx_instance.main(self)
                    else:
                        #Erroneuos Send Tests:
                        result = self.err_send.main(self,self.param)
                        self.stats.results_dic["erroneuous_send"].append(result["success"])
                        self.stats.results_dic["erroneuous_send"].extend(result["fail"])
                else:
                    #Erroneuos Start Tests:
                    for i in ("alternate","immediate"):
                        result = self.err_req.main(i, self.param,self.dot4_cli1)
                        self.stats.results_dic["erroneuous_request_%s" % i].append(result["success"])
                        self.stats.results_dic["erroneuous_request_%s" % i].extend(result["fail"])
                    result = self.err_req.main("continuous",self.param,self.dot4_cli1) #continuous
                    self.stats.results_dic["erroneuous_request_continuous"].append(result["success"])
                    self.stats.results_dic["erroneuous_request_continuous"].extend(result["fail"])
            else:
                #State Tests:
                result = self.state_instance.main(self,self.dot4_cli1,self.dot4_cli_sniffer)
                self.stats.results_dic["state_tests"].extend(result["success"])
                #to know from where start the indication of the failures
                self.stats.results_dic["state_tests"].append("fail:")
                self.stats.results_dic["state_tests"].extend(result["fail"])

        except Exception as e:
            raise e

    def print_results(self):
        #function name , sent values
        for i in self.stats.results_dic:
            item = self.stats.results_dic.get(i)
            l = len(item)
            if l == 0:
                continue
            if "erroneuous_request" in i:
                if item[0] is not 0:
                    if not "continuous" in i:
                        self.add_limit("Dot4 start invalid request %s" % i.split("erroneuous_request_")[1] ,1 ,int(item[0]) ,4 , 'GE')
                    else:
                        self.add_limit("Dot4 start invalid request %s" % i.split("erroneuous_request_")[1] ,1 ,int(item[0]) ,3 , 'GE')
                for j in item[1:l]:
                    self.add_limit("Dot4 start %s invalid request" % j , 0 , 1 , 1, 'EQ')
            elif "erroneuous_send" in i:
                if item[0] is not 0:
                    self.add_limit("Dot4 send- invalid values" ,0 ,int(item[0]) ,5 , 'GE')
                if item[0] < 5:
                    for j in item[1:l]:
                        self.add_limit("Dot4 start %s invalid request" % j , 0 , 1 , 1, 'EQ')
            elif "state_tests" in i:
                flag = False
                for j in item:
                    if "fail" in j and flag == False:
                        flag = True
                        continue
                    elif flag == False:
                        if 'fail' not in j:
                            self.add_limit("Dot4 State %s" % j , 1 , 1 , 1 , 'EQ')
                            continue
                        else:
                            self.add_limit("%s %d" % (string[0] ,int(string[1])) ,0 ,string[1] ,None ,'EQ')
                    else:
                        self.add_limit("Dot4 State %s" % j , 0 , 1 , 1 , 'EQ' )
            else:
                for j in item:
                    string = j
                    if 'fail' not in j:
                        values = [int(s) for s in string.split() if s.isdigit()]
                        self.add_limit("%s %s %s on chan%d" %(string.split()[0] ,string.split()[1] ,string.split()[2] ,values[0]) ,values[1] ,values[2] ,None ,'EQ')
                    else:
                        self.add_limit("%s" % string.split(",fail")[0], 0, int(string.split(",fail")[1]),None ,'EQ')
                                    
    def initilization(self):
        rc = 0
        # initilize uut
        self._uut[0] = globals.setup.units.unit(globals.CHS_DUT_ID)
        self._uut[1] = globals.setup.units.unit(globals.CHS_DUT_ID + 1)
        self.unit_configuration()
       
    def tearDown(self):
        super(TC_Dot4, self).tearDown()
        #for cli in self.active_cli_list:
        #    try:
        #        uut_id, rf_if, cli_name = cli
        #        # close link session
        #        self._uut[uut_id].qa_cli(cli_name).link.socket_delete()
        #    except Exception as e:
        #        print >> self.result._original_stdout, "ERROR in tearDown,  Failed to delete socket on uut {} for cli {}".format( uut_id, cli_name )
        #        log.error( "ERROR in tearDown,  Failed to clean uut {} for cli {}".format(uut_id, cli_name) )
        #    finally:
        #        self._uut[uut_id].close_qa_cli(cli_name)
        
############ END Class TC_Dot4 ############
             
class TC_Dot4_ERRONEOUS_Request():
    """
    @class TC_Dot4_ERRONEOUS
    @brief Test - TC_CHS_09, TC_CHS_10 ,TC_CHS_12 ,TC_CHS_14 ,TC_CHS_15
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
        try:
            self.res_dic["success"] = 0
            self.res_dic["fail"] = []
            self.dot4_cli = cli
            self.get_test_parameters(param)
            self.erroneous_request(state)
            return self.res_dic
        except Exception as e:
            raise globals.Error(e.message)
        
    def get_test_parameters( self, param ):
        self.param = param
        self.test_param = self.param.get('params',None)
        self.state = self.param.get('state',None)
        
    def erroneous_request(self,state):
        for req in self.test_param:
            rc = self.start_request(req.get("channel_num"),
                               req.get("time_slot"),
                               req.get("op_class"),
                               req.get("immediate_access"))
            if "ERROR" and "Invalid" not in rc :
                self.res_dic["fail"].append(state.upper() + " state: channel: %d time slot: %d operation class: %d immediate access: %d" %(req.get("channel_num"),req.get("time_slot"),req.get("op_class"),req.get("immediate_access")))
                self.end_channel(req.get("channel_num"))
            else:
                self.res_dic["success"] += 1

        if state is not "continuous":
            rc = self.start_request(180,1,1,None)
            if "ERROR" or "Invalid " not in rc :
                self.res_dic["fail"].append(state.upper() + " state: channel: %d time slot: %d operation class: %d immediate access: %d" %(req.get("channel_num"),req.get("time_slot"),req.get("op_class"),req.get("immediate_access")))
                self.end_channel(180)
            else:
                self.res_dic["success"] += 1

    def start_request(self,ch_num,t_slot,op_class,imm_access):
        request = 0,ch_num,t_slot,op_class,imm_access
        return self.dot4_cli.dot4.dot4_channel_start(request)

    def end_channel(self,ch_num): 
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        if rc != 0:
            self.error_list.append("End request failed for: ..")
            
############ END Class TC_Dot4_ERRONEOUS_Request ############

class TC_Dot4_ERRONEOUS_Send():
    """
    @class TC_Dot4_ERRONEOUS_Send
    @brief Test TC_CHS_11, TC_CHS_13 ,TC_CHS_16
    @author Nomi Rozenkruntz
    @version 0.1
    @date   3/6/2017
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.state_instance = TC_Dot4_State()
        self.res_dic = dict(success = int(), fail = list())
        self.state = None
        self.dot4_cli = None
        self.if_index = 1
        self.time_slots = 0       
        self.channel_id = dict(channel_num = 0, op_class = 0)
        self.immediate_access = 0
    
    def main(self,tc_dot4,param):
        try:
            self.tc_dot4 = tc_dot4
            self.get_test_parameters(param)
            self.erroneous_send()
            return self.res_dic
        except Exception as e:
            raise globals.Error(e.message)        

    def get_test_parameters( self,param ):
        self.state = param.get('state',None)
        self.test_param = param.get('send_dict',None)

    def erroneous_send(self):
        uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = self.tc_dot4.tx_list_[0]
        self.state_instance.start_alternate(182,self.tc_dot4._uut[uut_id].qa_cli(cli_name))
        for send_p in self.test_param:
            rc = self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.erroneous_transmit(tx_data = "4560" ,frames = frames, 
                                                             rate_hz = frame_rate_hz ,channel_num = send_p.get("channel_num"),
                                                             time_slot = send_p.get("time_slot"), 
                                                             op_class = send_p.get("op_class"), 
                                                             power_dbm8 = tx_power)
            if "ERROR" and "Invalid" not in rc :
                self.res_dic["fail"].append("Alternate state: channel %d time slot %d operation class %d" %(send_p.get("channel_num"),send_p.get("time_slot"),send_p.get("op_class")))
                self.end_channels()
            else:
                self.res_dic["success"] += 1
    
    def end_channels(self):
        rc = ''
        for tx in self.tc_dot4.tx_list_:
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            rc += self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.dot4_channel_end(rf_if+1,ch_idx) 
        return rc

############ END Class TC_Dot4_ERRONEOUS_Send ############

class TC_Dot4_Tx(TC_Dot4):
    """Transmission test
    @class TC_Dot4_Tx
    @brief Test transmision while channel switching- TC_CHS_17, TC_CHS_18
    @author Nomi Rozenkruntz
    @version 0.1
    @date	3/7/2017
    """
    #A reminder - todo the high rate test! 
    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self.res_list = list()
        self.chs_flag = False
        self.first_proto = None
        self.sniffer_file = list()
        self.interface = None
        self._expected_frames = 0
        self._frame_rate = 0
                    
    def main(self,tc_dot4):
        try:
            self.tc_dot4 = tc_dot4
            self._init_sniffers_counters()
            #test start:
            self.session_start()
            self.end_channels()
            self.analyze_results()
            return self.print_results()

        except Exception as e:
            raise globals.Error(e.message)

    def link_tx(self,rx_timeout):
        #recieve:
        for rx in self.tc_dot4.rx_list:
            uut_id, rf_if, cli_name, frames, proto_id,  _ = rx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = 0, timeout = rx_timeout )

        ind = 0
        #transmit:
        for tx in self.tc_dot4.tx_list_:
            ind += 1
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.transmit(tx_data = "4752" ,frames = frames, rate_hz = frame_rate_hz ,channel_num = ch_idx,time_slot = time_slot, op_class = op_class, power_dbm8 = tx_power)             
            self.stats.total_frames_expected[ind % 2 + 1] += frames 
            self.stats.total_data_expected[ind % 2 + 1] += frames

    def session_start(self):
        
        transmit_time = 0
        # get the max waiting time, 
        for tx in self.tc_dot4.tx_list_:
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self._frame_rate = frame_rate_hz
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        for rx in self.tc_dot4.rx_list: 
            uut_id, rf_if, cli_name, frames, proto_id,  _ = rx 
        
        #open sniffer for the two interfaces in craton1
        port = self.start_sniffer(self.tc_dot4._uut[uut_id].qa_cli(cli_name).interface(),rf_if ,"RX")

        request = [1,182,1,1,0]  
        for tx in self.tc_dot4.tx_list_:
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.dot4_channel_start(request) 
            request = [1,184,2,1,0]

        self.link_tx(rx_timeout)

        time.sleep(int(float(rx_timeout / 1000))+100)

        self.stop_sniffer(port)
     
    def _init_sniffers_counters(self):
        for i in (1,2):
            self.stats.total_frames_expected[i] = 0
            self.stats.total_data_expected[i] = 0

        self.stats.counters['total_frames_rf1'] = 0
        self.stats.counters['total_frames_rf2'] = 0
        self.stats.counters['total_data_rf1'] = 0
        self.stats.counters['total_data_rf2'] = 0
        self.stats.counters['chs_setup_failure_ch1'] = 0
        self.stats.counters['chs_setup_failure_ch2'] = 0
        self.stats.counters['chs_tx_during_gi_fail_count_ch1'] = 0
        self.stats.counters['chs_tx_during_gi_fail_count_ch2'] = 0
        self.stats.counters['chs_interval_expected_to_fail_count'] = 0
        
    def dut_tx_packet_handler(self, packet):
        #a)	Frames are associated with the right channel. 
        #b)	All frames have been transmitted (continues frames numbers). 
        #c)	Frames data was not corrupted.
        #d)	The number of frames sent equals the number of frames arrived.
               
        current_active_ch_proto = int(packet.llc.type, 16)
        num = int(packet.radiotap.mactime) / 1000
        #powerDbm8 (transmit power):
        if packet.radiotap.txpower != 160:
            pass
        #save first frame protocol
        if int(packet.frame_info.number) == 1:
            self.top = current_active_ch_proto
            self.first_proto = current_active_ch_proto
            self.last_proto = self.top
            
        #channel switch occurred
        if self.last_proto != current_active_ch_proto: 
            #first channel switch
            if self.chs_flag == False:
                self.chs_flag = True
                if self.top == current_active_ch_proto:
                    self.stats.counters['total_frames_rf1'] += 1
                    self.stats.counters['total_data_rf1'] += 1
                else:
                    self.stats.counters['total_frames_rf2'] += 1
                    self.stats.counters['total_data_rf2'] += 1
                #to know if there was already a channel switch
                self.first_proto = None
                self.last_timestamp = num
                self.last_proto = current_active_ch_proto
                return

        #not yet CHS:
        if not self.chs_flag:
            self.first_timestamp = num
            self.last_proto = current_active_ch_proto
            if self.top == current_active_ch_proto:
                self.stats.counters['total_frames_rf1'] += 1
                self.stats.counters['total_data_rf1'] += 1
            else:
                self.stats.counters['total_frames_rf2'] += 1
                self.stats.counters['total_data_rf2'] += 1
            return

        #there was already a channel switch
        if self.first_proto == None:
            #continues to arrive in the same channel, check if time slot is match
            if self.last_proto == current_active_ch_proto:
                #the previous frames was on slot_0
                if self.last_timestamp % 100 < 54 and self.last_timestamp % 100 > 4:
                    if num % 100 <= 54:
                        if self.top == current_active_ch_proto:
                            self.stats.counters['chs_setup_failure_ch1'] += 1
                        else:
                            self.stats.counters['chs_setup_failure_ch2'] += 1
                        
                #the previous frames was on slot_1
                else:
                    if num - self.last_timestamp > 54:
                        if self.top == current_active_ch_proto:
                            self.stats.counters['chs_setup_failure_ch1'] += 1
                        else:
                            self.stats.counters['chs_setup_failure_ch2'] += 1
                        
                self.last_timestamp = num
            #again there is CHS, TEST!
            else:
                self.first_proto = current_active_ch_proto
                #timestamp test:
                if self.last_timestamp - self.first_timestamp > 50:
                    if self.top == current_active_ch_proto:
                        self.stats.counters['chs_tx_during_gi_fail_count_ch1'] += 1 
                    else:
                        self.stats.counters['chs_tx_during_gi_fail_count_ch2'] += 1
                    
                #the previous frames was on slot_0
                if self.last_timestamp % 100 < 54 and self.last_timestamp % 100 > 4:
                    if num % 100 <= 54:
                        if self.top == current_active_ch_proto:
                            self.stats.counters['chs_setup_failure_ch1'] += 1
                        else:
                            self.stats.counters['chs_setup_failure_ch2'] += 1
                        
                #the previous frames was on slot_1
                else:
                    if num - self.last_timestamp > 54:
                        if self.top == current_active_ch_proto:
                            self.stats.counters['chs_setup_failure_ch1'] += 1
                        else:
                            self.stats.counters['chs_setup_failure_ch2'] += 1
                        
                #when high transmit power - more than one frame per 50 ms:
                '''Now - 10 frames in time slot, or 40 - 2 frames in timeslot?'''
                if self._frame_rate >= 40:     
                    #check time sync and last frame in interval boumdries (2ms in GI are RX OK!)
                    if num % 100 > 4 and num % 100 < 54:
                        if self.last_timestamp < 37:
                            self.stats.counters['chs_interval_expected_to_fail_count'] += 1

        #There was not yet CHS
        else:
            self.first_proto = None
            self.last_proto = current_active_ch_proto
            self.last_timestamp = num
        #for testing all frames arrived and data was not corrupted
        if self.top == current_active_ch_proto:
            self.stats.counters['total_frames_rf1'] += 1
            self.stats.counters['total_data_rf1'] += 1
        else:
            self.stats.counters['total_frames_rf2'] += 1
            self.stats.counters['total_data_rf2'] += 1

    def analyze_results(self):
        
        for sniffer_file in self.sniffer_file:
            try:
                cap = pyshark.FileCapture(sniffer_file)
            except Exception as e:
                raise globals.Error("pcap file not exist")
            
            for frame_idx,frame in enumerate(cap):
                self.dut_tx_packet_handler(frame)
                
    def end_channels(self):
        rc = ''
        for tx in self.tc_dot4.tx_list_:
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            rc += self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.dot4_channel_end(rf_if+1,ch_idx) 
        return rc

    def start_sniffer(self, cli_interface, idx, type):
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(idx)
        time.sleep(2)
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferLinkEmbedded(cli_interface)
        sniffer_port = traffic_generator.BASE_HOST_PORT + ( idx * 17 ) + 1 
        #save for sniffer close...
        self.sniffer_file.append ( os.path.join( common.SNIFFER_DRIVE , "test_mode_dut" + str(idx) + "_" + str(type) + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))
        try:
            time.sleep(2)
            #use the last appended sniffer  file...
            self.dut_host_sniffer.start( if_idx = idx , port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
            time.sleep(1)
            self.dut_embd_sniffer.start( if_idx = idx , server_ip = "192.168.120.1" , server_port = sniffer_port, sniffer_type = type)
            time.sleep(1)
            self.dut_embd_sniffer.start( if_idx = idx + 1 , server_ip = "192.168.120.1" , server_port = sniffer_port, sniffer_type = type)
            time.sleep( 30 )
        except Exception as e:
            time.sleep( 300 )
            pass
        return sniffer_port

    def stop_sniffer(self,sniffer_port):
        self.dut_host_sniffer.stop(sniffer_port)
        time.sleep(2)
        #self.dut_embd_sniffer.stop(1)
        #time.sleep(2)
        #self.dut_embd_sniffer.stop(2)

    def print_results(self):
        self.res_list.append("Total Tx Frames %d %d %d" %(1,self.stats.total_frames_expected[1],self.stats.counters['total_frames_rf1']))
        self.res_list.append("Total Tx Frames %d %d %d" %(2,self.stats.total_frames_expected[2],self.stats.counters['total_frames_rf2']))
        self.res_list.append("Dropped Tx frames %d %d %d" %(1,self.stats.total_data_expected[1],self.stats.counters['total_data_rf1']))
        self.res_list.append("Dropped Tx frames %d %d %d" %(2,self.stats.total_data_expected[2],self.stats.counters['total_data_rf2']))
        if self._frame_rate >= 40:
            self.res_list.append("Tx interval equals to 46-50 ms ,fail %d" %self.stats.counters['chs_interval_expected_to_fail_count'])
        self.res_list.append("Tx during GI on time_slot0 ,fail %d" %self.stats.counters['chs_tx_during_gi_fail_count_ch1'])
        self.res_list.append("Tx during GI on time_slot1 ,fail %d" %self.stats.counters['chs_tx_during_gi_fail_count_ch2'])        
        self.res_list.append("Tx chan1 During chan2 ,fail %d" %self.stats.counters['chs_setup_failure_ch1'])
        self.res_list.append("Tx chan2 During chan1 ,fail %d" %self.stats.counters['chs_setup_failure_ch2'])
        return self.res_list

############ END Class TC_Dot4_Tx ############

class TC_Dot4_Rx(TC_Dot4):
    """
    @class TC_Dot4_Rx
    @brief Test reception while channel switching- TC_CHS_19, TC_CHS_20 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	3/7/2017
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self.res_list = list()
        self.frames_headers = list()
        self.last_timestamp = 0
        self._expected_frames = 0
        self.chs_flag = False
        self._frame_rate = 0
    
    def _init_counters(self):
        for i in (1,2):
            self.stats.total_frames_expected[i] = 0
            self.stats.total_data_expected[i] = 0

        self.stats.counters['total_frames_chan1'] = 0
        self.stats.counters['total_frames_chan2'] = 0
        self.stats.counters['chs_setup_failure_ch1'] = 0
        self.stats.counters['chs_setup_failure_ch2'] = 0
        self.stats.counters['chs_rx_during_gi_fail_count_ch1'] = 0
        self.stats.counters['chs_rx_during_gi_fail_count_ch2'] = 0
        self.stats.counters['chs_interval_expected_to_fail_count'] = 0

    def main(self,tc_dot4):
        try:
            self.tc_dot4 = tc_dot4
            #test start:
            self._init_counters()
            self.session_start()
            self.analyze_results(self.frames_headers)
            return self.print_results()
            
        except Exception as e:
            raise globals.Error(e.message)

    def session_start(self):
        thread_list = []
        transmit_time = 0
        # get the max waiting time
        for tx in self.tc_dot4.tx_list_:
            uut_id, rf_if, cli_name, frames, proto_id, frame_rate_hz,  _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time
            self._expected_frames += frames
        #Need for waiting time calculation
        self._frame_rate = frame_rate_hz

        request = [1,182,1,1,0] 
        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        for rx in self.tc_dot4.rx_list: 
            uut_id, rf_if, cli_name, frames, proto_id, ch_idx, op_class,time_slot, tx_power , print_ , _ = rx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.dot4_channel_start(request) 
            request = [1,184,2,1,0]               
        
        self.link_rx(rx_timeout)
        
        for rx in self.tc_dot4.rx_list:
            t = threading.Thread( target = self.get_frames_from_cli_thread, args = (rx,) )
            thread_list.append(t)

        # Starts threads
        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()

        time.sleep(int(float(rx_timeout / 1000))+100)

        #Read from ref, how many frames had been transmited:
        for tx in self.tc_dot4.tx_list_:
            uut_id, rf_if, cli_name, frames, proto_id, frame_rate_hz,  _ = tx
            self.read_cnt = self.tc_dot4._uut[uut_id].qa_cli(cli_name).link.read_counters() 
            time.sleep(2)
            if bool(self.read_cnt) :
                self.stats.total_frames_expected[rf_if + 1] += self.read_cnt['tx'][1]

        self.end_channels()
        
    def link_rx(self,rx_timeout):
        #recieve:
        for rx in self.tc_dot4.rx_list:
            uut_id, rf_if, cli_name, frames, proto_id, ch_idx, op_class,time_slot, tx_power , print_ , _ = rx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.receive( frames, print_frame = print_, timeout = rx_timeout, channel_num = ch_idx ,op_class = op_class,time_slot = time_slot, power_dbm8 = tx_power)
            
        ind = 0
        #transmit:
        for tx in self.tc_dot4.tx_list_:
            ind += 1
            uut_id, rf_if, cli_name, frames, proto_id, frame_rate_hz,  _ = tx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = "4560" ,frames = frames, rate_hz = frame_rate_hz)    
        
    def get_frames_from_cli_thread(self, rx):
        
        log = logging.getLogger(__name__)
        uut_id, rf_if, cli_name, frames, proto_id, ch_idx, op_class,time_slot, tx_power ,print_ ,  _ = rx
        
        frm_cnt = 0
        transmit_time  = int(float( 1.0 / self._frame_rate) *  frames * 2) + 5  
        start_time = int(time.clock())
  
        # Start Reading from RX unit
        while True:
            try:
                data = self.tc_dot4._uut[uut_id].qa_cli(cli_name).interface().read_until('\r\n', 2)
                if 'Frame' in data:
                    frm_cnt += 1
                    self.stats.total_frames_processed += 1
                    self.frames_headers.append(data)
            except Exception as e:
                break
            
            if 'ERROR' in data:
                log.debug( "ERROR Found in RX, {}".format( data) )
                              
            # Timeout
            if ( int(time.clock()) - start_time ) > (transmit_time + int(transmit_time * 0.1)):
                log.debug( "exit rx thread {} loop due to time out".format (rx) )
                break

            # frame count
            if frm_cnt >= self._expected_frames:
                log.debug( "exit rx thread {} loop due to frame count".format(rx) )
                break

    def analyze_results(self,frames_headers):
        #a)	Frames are associated with the right channel. 
        #b)	All frames have been transmitted (continues frames numbers). 
        #c)	Frames data was not corrupted.
        #d)	The number of frames sent equals the number of frames arrived.
        if frames_headers == []:
            return
        ind = 0
        values = [int(s) for s in frames_headers[0].split() if s.isdigit()]
        current_active_ch = int(frames_headers[0].split("ch_num:")[1].split(',')[0])
        self.last_timestamp = values[1]
        self.top = current_active_ch
        self.first_chan = current_active_ch
        self.last_chan = self.top
        frames_headers.pop(0)
        for packet in frames_headers:
            ind += 1
            values = [int(s) for s in packet.split() if s.isdigit()]
            self.last_timestamp = values[1]
            
            current_active_ch = int(packet.split("ch_num:")[1].split(',')[0])
            num = values[1]
            #powerDbm8 (transmit power):
            if int(packet.split("power_dbm8")[1].split(',')[0]) != 160:
                pass
            #save first frame channel num
            if int(packet.split('Frame:')[1].split(',')[0]) == 1:
                self.top = current_active_ch
                self.first_chan = current_active_ch
                self.last_chan = self.top
                
            #channel switch occurred
            if self.last_chan != current_active_ch: 
                #first channel switch
                if self.chs_flag == False:
                    self.chs_flag = True
                    if self.top == current_active_ch:
                        self.stats.counters['total_frames_chan1'] += 1
                    else:
                        self.stats.counters['total_frames_chan2'] += 1
                    #to know if there was already a channel switch
                    self.first_chan = None
                    self.last_timestamp = num
                    self.last_chan = current_active_ch
                    continue

            #not yet CHS:
            if not self.chs_flag:
                self.first_timestamp = num
                self.last_chan = current_active_ch
                if self.top == current_active_ch:
                    self.stats.counters['total_frames_chan1'] += 1
                else:
                    self.stats.counters['total_frames_chan2'] += 1
                continue

            #there was already a channel switch
            if self.first_chan == None:
                #continues to arrive in the same channel, check if time slot is match
                if self.last_chan == current_active_ch:
                    #the previous frames was on slot_0
                    if self.last_timestamp % 100 < 54 and self.last_timestamp % 100 > 4:
                        if num % 100 <= 54:
                            if self.top == current_active_ch:
                                self.stats.counters['chs_setup_failure_ch1'] += 1
                            else:
                                self.stats.counters['chs_setup_failure_ch2'] += 1
                            
                    #the previous frames was on slot_1
                    else:
                        if num - self.last_timestamp > 54:
                            if self.top == current_active_ch:
                                self.stats.counters['chs_setup_failure_ch1'] += 1
                            else:
                                self.stats.counters['chs_setup_failure_ch2'] += 1
                            
                    self.last_timestamp = num
                #again there is CHS, TEST!
                else:
                    self.first_chan = current_active_ch
                    #timestamp test:
                    if self.last_timestamp - self.first_timestamp > 50:
                        if self.top == current_active_ch:
                            self.stats.counters['chs_rx_during_gi_fail_count_ch1'] += 1
                        else:
                            self.stats.counters['chs_rx_during_gi_fail_count_ch2'] += 1
                        
                    #the previous frames was on slot_0
                    if self.last_timestamp % 100 < 54 and self.last_timestamp % 100 > 4:
                        if num % 100 <= 54:
                            if self.top == current_active_ch:
                                self.stats.counters['chs_setup_failure_ch1'] += 1
                            else:
                                self.stats.counters['chs_setup_failure_ch2'] += 1
                            
                    #the previous frames was on slot_1
                    else:
                        if num - self.last_timestamp > 54:
                            if self.top == current_active_ch:
                                self.stats.counters['chs_setup_failure_ch1'] += 1
                            else:
                                self.stats.counters['chs_setup_failure_ch2'] += 1
                            
                    #when high transmit power - more than one frame per 50 ms:
                    '''Now - 10 frames in time slot, or 40 - 2 frames in timeslot?'''
                    if self._frame_rate >= 40:     
                        #check time sync and last frame in interval boumdries (2ms in GI are RX OK!)
                        if num % 100 > 4 and num % 100 < 54:
                            if self.last_timestamp < 37:
                                self.stats.counters['chs_interval_expected_to_fail_count'] += 1

            #There was not yet CHS
            else:
                self.first_chan = None
                self.last_chan = current_active_ch
                self.last_timestamp = num
            #for testing all frames arrived and data was not corrupted
            if self.top == current_active_ch:
                self.stats.counters['total_frames_chan1'] += 1
            else:
                self.stats.counters['total_frames_chan2'] += 1
                        
    def end_channels(self):
        for rx in self.tc_dot4.rx_list: 
            uut_id, rf_if, cli_name, frames, proto_id, ch_idx, op_class,time_slot, print_ ,tx_power ,  _ = rx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.dot4_channel_end(rf_if + 1,ch_idx) 

    def print_results(self):
        self.res_list.append("Total Rx Frames %d %d %d" %(1,self.stats.total_frames_expected[1],self.stats.counters['total_frames_chan1']))
        self.res_list.append("Total Rx Frames %d %d %d" %(2,self.stats.total_frames_expected[2],self.stats.counters['total_frames_chan2']))
        if self._frame_rate >= 40:
            self.res_list.append("Rx interval equals to 46-50 ms ,fail %d" %self.stats.counters['chs_interval_expected_to_fail_count'])
        self.res_list.append("Rx during GI on time_slot0 ,fail %d" %self.stats.counters['chs_rx_during_gi_fail_count_ch1']) 
        self.res_list.append("Rx during GI on time_slot1 ,fail %d" %self.stats.counters['chs_rx_during_gi_fail_count_ch2'])
        self.res_list.append("Rx chan1 During chan2 ,fail %d" %self.stats.counters['chs_setup_failure_ch1'])
        self.res_list.append("Rx chan2 During chan1 ,fail %d" %self.stats.counters['chs_setup_failure_ch2'])
        return self.res_list

############ END Class TC_Dot4_Rx ############

class TC_Dot4_Full_CS():
    """
    @class TC_Dot4_Full_CS
    @brief Test transmit and recieve while channel switching - TC_CHS_23
    @author Nomi Rozenkruntz
    @version 0.1
    @date	2/23/2017
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self.stats = Statistics()
        self.frames_headers = list()
        self.results_dic = dict(Tx = list(), Rx = list())
        self.tx_instance = TC_Dot4_Tx()
        self.rx_instance = TC_Dot4_Rx()
        self._expected_frames = 0

    def main(self,tc_dot4):
        try:
            self.tc_dot4 = tc_dot4
            self._init_counters()
            #test start:
            results = self.session_start()
            self.end_channels()
            self.analyze_results()
            return self.results_dic
            
        except Exception as e:
            raise globals.Error(e.message)

    def _init_counters(self):
        self.tx_instance._init_sniffers_counters()
        self.rx_instance._init_counters()

    def link_tx_rx(self,rx_timeout):

        #recieve, ref unit:
        for i in range(0,len(self.tc_dot4.rx_list)/2):
            rx = self.tc_dot4.rx_list[i]
            uut_id, rf_if, cli_name, frames, proto_id,  _ = rx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = 0, timeout = rx_timeout )
        #recieve, dut:
        for j in range(i+1,len(self.tc_dot4.rx_list)):
            rx = self.tc_dot4.rx_list[j]
            uut_id, rf_if, cli_name, frames, proto_id, ch_idx, op_class,time_slot, tx_power , print_ , _ = rx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.receive( frames, print_frame = print_, timeout = rx_timeout, channel_num = ch_idx ,op_class = op_class,time_slot = time_slot, power_dbm8 = tx_power)
        ind = 0
        #transmit, dut:
        for i in range(0,len(self.tc_dot4.tx_list_)/2):
            tx = self.tc_dot4.tx_list_[i]
            ind += 1
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.transmit(tx_data = "4752" ,frames = frames, rate_hz = frame_rate_hz ,channel_num = ch_idx,time_slot = time_slot, op_class = op_class, power_dbm8 = tx_power)             
            self.tx_instance.stats.total_frames_expected[ind % 2 + 1] += frames 
            self.tx_instance.stats.total_data_expected[ind % 2 + 1] += frames
        ind = 0
        #transmit, ref unit:
        for j in range(i + 1,len(self.tc_dot4.tx_list_)):
            tx = self.tc_dot4.tx_list_[j]
            ind += 1
            uut_id, rf_if, cli_name, frames, proto_id, frame_rate_hz,  _ = tx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).link.transmit(tx_data = "4560" ,frames = frames, rate_hz = frame_rate_hz)             
             
            self.rx_instance.stats.total_data_expected[ind % 2 + 1] += frames

    def session_start(self):
        thread_list = []
        transmit_time = 0
        # get the max waiting time, 
        for i in range(0,len(self.tc_dot4.tx_list_)/2):
            tx = self.tc_dot4.tx_list_[i]
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self._frame_rate = frame_rate_hz
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        for j in range(i + 1,len(self.tc_dot4.tx_list_)):
            tx = self.tc_dot4.tx_list_[j]
            uut_id, rf_if, cli_name, frames, proto_id, frame_rate_hz,  _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time
            self._expected_frames += frames

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        rx = self.tc_dot4.rx_list[1]
        uut_id, rf_if, cli_name, frames, proto_id,  _ = rx  
        
        #open sniffer for the two interfaces in craton1
        port = self.tx_instance.start_sniffer(self.tc_dot4._uut[uut_id].qa_cli(cli_name).interface(),rf_if ,"RX")

        request = [1,182,1,1,0]  
        for i in range(0,len(self.tc_dot4.tx_list_)/2):
            tx = self.tc_dot4.tx_list_[i]
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.dot4_channel_start(request) 
            request = [1,184,2,1,0]

        self.link_tx_rx(rx_timeout)

        for j in range(i + 1,len(self.tc_dot4.rx_list)):
            rx = self.tc_dot4.rx_list[j]
            t = threading.Thread( target = self.get_frames_from_cli_thread, args = (rx,) )
            thread_list.append(t)

        # Starts threads
        for thread in thread_list:
            thread.start()

        for thread in thread_list:
            thread.join()

        time.sleep(int(float(rx_timeout / 1000))+100)

        #Read from ref, how many frames had been transmited:
        for j in range(i + 1,len(self.tc_dot4.tx_list_)):
            tx = self.tc_dot4.tx_list_[j]
            uut_id, rf_if, cli_name, frames, proto_id, frame_rate_hz,  _ = tx
            self.read_cnt = self.tc_dot4._uut[uut_id].qa_cli(cli_name).link.read_counters() 
            time.sleep(2)
            if bool(self.read_cnt) :
                self.rx_instance.stats.total_frames_expected[rf_if + 1] += self.read_cnt['tx'][1]

        self.tx_instance.stop_sniffer(port) 

    def get_frames_from_cli_thread(self, rx):
        
        log = logging.getLogger(__name__)
        uut_id, rf_if, cli_name, frames, proto_id, ch_idx, op_class,time_slot, tx_power ,print_ ,  _ = rx
        
        frm_cnt = 0
        transmit_time  = int(float( 1.0 / self._frame_rate) *  frames * 2) + 5  
        start_time = int(time.clock())
  
        # Start Reading from RX unit
        while True:
            try:
                data = self.tc_dot4._uut[uut_id].qa_cli(cli_name).interface().read_until('\r\n', 2)
                if 'Frame' in data:
                    frm_cnt += 1
                    self.stats.total_frames_processed += 1
                    self.frames_headers.append(data)
            except Exception as e:
                break
            
            if 'ERROR' in data:
                log.debug( "ERROR Found in RX, {}".format( data) )
                              
            # Timeout
            if ( int(time.clock()) - start_time ) > (transmit_time + int(transmit_time * 0.1)):
                log.debug( "exit rx thread {} loop due to time out".format (rx) )
                break

            # frame count
            if frm_cnt >= self._expected_frames:
                log.debug( "exit rx thread {} loop due to frame count".format(rx) )
                break        

    def analyze_results(self):
        #Tx analyze:
        self.tx_instance.analyze_results()
        self.results_dic["Tx"] = self.tx_instance.print_results()
        #Rx analyze:
        self.rx_instance.analyze_results(self.frames_headers)
        self.results_dic["Rx"] = self.rx_instance.print_results()

    def end_channels(self):
        for i in range(0,len(self.tc_dot4.tx_list_)/2):
            tx = self.tc_dot4.tx_list_[i]
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self.tc_dot4._uut[uut_id].qa_cli(cli_name).dot4.dot4_channel_end(rf_if,ch_idx) 
            
############ END Class TC_Dot4_Full_CS ############

class TC_Dot4_State():
    """
    @class TC_Dot4_State
    @brief Test dot4 start request with all modes (TC_CHS_01 - TC_CHS_08)
    @author Nomi Rozenkruntz
    @version 0.1
    @date	3/5/2017
    """
    
    def __init__(self, methodName = 'runTest', param = None):
        self.dot4_cli = None
        self.stats = Statistics()
        self.sniffer_file = list()
        self.res_dic = dict(success = list(), fail = list())
        self.if_index = 1
        self.time_slots = 0
        self.channel_id = dict(channel_num = 0, op_class = 0)
        self.cli_names = []
        self.immediate_access = 0
        self.success_scenarios = list()
        self.fail_scenarios = list()
    
    def main(self,tc_dot4,dot4_cli,dot4_cli_sniffer):
        try:
            self.scenarios_list = ('1111','2222','3333','4444','5555','6666','7777','8888')
            self.scenarios_names= ('continuous','continuous end scenario','continuous 2 continuous scenario',
                                   'immediate scenario 1','immediate scenario 2',
                                   'alternate scenario 1','alternate scenario 2','alternate scenario 3')
            self.tc_dot4 = tc_dot4
            self._uut = self.tc_dot4._uut
            
            self.rx_timeout = self.get_max_waiting_time()
            uut_id, rf_if, cli_name, frames, proto_id,  _ = self.tc_dot4.rx_list[1]
            port = self.start_sniffer(self.tc_dot4._uut[uut_id].qa_cli(cli_name).interface(),rf_if,"RX")

            for rx in self.tc_dot4.rx_list:
                uut_id, rf_if, cli_name, frames, proto_id,  _ = rx
                self.tc_dot4._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = 0, timeout = self.rx_timeout * self.rx_timeout )

            self.frames = frames
            self.continuous_scenario()
            self.continuous_end_scenario()
            self.continuous_2_continuous_scenario()
            self.alternate_scenario_1()
            self.alternate_scenario_2()
            self.immediate_scenario_1()
            self.immediate_scenario_2()
            self.immediate_scenario_3()
            
            time.sleep(int(float(self.rx_timeout / 1000)) +20)

            self.stop_sniffer(port)
                        
            return self.analyze_results()  

        except Exception as e:
            #self.stop_sniffer(port)
            raise globals.Error(e.message)   
                   
    def get_max_waiting_time(self):
        transmit_time = 0
        # get the max waiting time
        for tx in self.tc_dot4.tx_list_:
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            self.cli_names.append(cli_name)
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time
        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        return rx_timeout

    def link_tx(self,data,ch_num):

        #transmit:
        if ch_num == 184:
            tx = self.tc_dot4.tx_list_[1]
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            rc = self._uut[uut_id].qa_cli(self.cli_names[1]).dot4.transmit(tx_data = data ,frames = frames, rate_hz = frame_rate_hz ,channel_num = ch_num,time_slot = time_slot, op_class = op_class, power_dbm8 = tx_power)
        else:
            tx = self.tc_dot4.tx_list_[0]
            uut_id, rf_if, cli_name, frames, frame_type, proto_id, frame_rate_hz, ch_idx , time_slot, op_class, tx_power,  _ = tx
            rc = self._uut[uut_id].qa_cli(self.cli_names[0]).dot4.transmit(tx_data = data ,frames = frames, rate_hz = frame_rate_hz ,channel_num = ch_num,time_slot = time_slot, op_class = op_class, power_dbm8 = tx_power)
        time.sleep(20)

    def start_continuous(self,ch_num):
        self.time_slots = 3
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 255
        return self.start_request()

    def start_alternate(self,ch_num,cli = None):
        if self.dot4_cli is None:
            self.dot4_cli = cli
        if ch_num == 182:
            self.time_slots = 1
        else:
            self.time_slots = 2
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 0
        return self.start_request()

    def start_immediate(self,ch_num):
        self.time_slots = 3
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 10
        return self.start_request()

    def continuous_scenario(self):
        rc = self.start_continuous(182)
        if not "ERROR" in rc:
            self.link_tx("11111111",182) 
            self.end_channel(182)

    def continuous_end_scenario(self):
        rc = self.start_continuous(182)
        if "ERROR" and "Invalid" not in rc:
            rc = self.end_channel(182)
            if "ERROR" and "Invalid" not in rc:
                self.link_tx("22222222",182)
            else:
                self.fail_scenarios.append("error in end channel")
        else:
            self.fail_scenarios.append("error in start continuous request")

    def continuous_2_continuous_scenario(self):
        rc = self.start_continuous(182)
        rc += self.start_continuous(184)
        if "ERROR" and "Invalid" not in rc:
            self.link_tx("33333333",182)
            self.end_channel(182)
            self.link_tx("33333333",182)
            self.end_channel(184)
        else:
            self.fail_scenarios.append("error in start continuous")

    def immediate_scenario_1(self):
        rc = self.start_continuous(182)
        rc += self.start_immediate(184)
        if "ERROR" and "Invalid" not in rc:
            self.link_tx("44444444",184)
            self.link_tx("44444444",182)
            self.end_channel(182)
            self.end_channel(184)
        else:
            self.fail_scenarios.append("error in start immediate")
            
    def immediate_scenario_2(self):
        rc = self.start_alternate(182)
        rc += self.start_alternate(184)
        rc += self.start_immediate(172)
        if "ERROR" and "Invalid" not in rc:
            #self.link_tx("55555555",184)
            #self.link_tx("55555555",182)
            self.link_tx("55555555",172)
            self.end_channel(182)
            self.end_channel(184)
            self.end_channel(172)
        else:
            self.fail_scenarios.append("error in start alternate")
        
    def immediate_scenario_3(self):
        rc = self.start_immediate(182) 
        if "ERROR" in rc:
            self.success_scenarios.append("immediate without previous mode")
        else:
            self.fail_scenarios.append("immediate without previous mode")

    def alternate_scenario_1(self):
        rc = self.start_alternate(182)
        rc += self.start_alternate(184)
        if "ERROR" and "Invalid" not in rc:
            self.link_tx("66666666",184)
            self.link_tx("66666666",182)  
            self.end_channel(184)
            self.link_tx("55555555",182)
            self.link_tx("55555555",0)
            self.end_channel(182)

    def alternate_scenario_2(self):
        rc = self.start_continuous(182)
        rc += self.start_immediate(184)
        rc += self.start_alternate(172)
        if "ERROR" and "Invalid" not in rc:
            self.link_tx("77777777",184)
            self.end_channel(182)
            self.end_channel(184)
            self.end_channel(172)

    def alternate_scenario_3(self):
        rc = self.start_continuous(182)
        rc += self.start_alternate(184)
        if "ERROR" and "Invalid" not in rc:
            self.link_tx("88888888",184)
            self.end_channel(182)
            self.end_channel(184)

    def start_request(self):
        request = []
        request.append(self.if_index)
        request.append(self.channel_id.get("channel_num"))
        request.append(self.time_slots)
        request.append(self.channel_id.get("op_class"))
        request.append(self.immediate_access)
        if self.dot4_cli != None:
             return self.dot4_cli.dot4.dot4_channel_start(request)
        if request[1] == 184:
            rc = self._uut[0].qa_cli(self.cli_names[1]).dot4.dot4_channel_start(request)
        else:
            rc = self._uut[0].qa_cli(self.cli_names[0]).dot4.dot4_channel_start(request)
        return rc

    def end_channel(self,ch_num):
        if ch_num == 182:
            rc = self._uut[0].qa_cli(self.cli_names[0]).dot4.dot4_channel_end(self.if_index, ch_num)
        elif ch_num == 184:
            rc = self._uut[0].qa_cli(self.cli_names[1]).dot4.dot4_channel_end(self.if_index, ch_num)
        else:
            rc = self._uut[0].qa_cli(self.cli_names[0]).dot4.dot4_channel_end(self.if_index, ch_num)
        return rc

    def analyze_results(self):
        for sniffer_file in self.sniffer_file:
            try:
                cap = pyshark.FileCapture(sniffer_file)
            except Exception as e:
                raise globals.Error("pcap file not exist")
            
            for frame_idx,frame in enumerate(cap):
                for i in range(0,len(self.scenarios_list)):
                    if self.scenarios_list[i] in frame.data.data and self.scenarios_names[i] not in self.success_scenarios:
                        self.success_scenarios.append("%s" %self.scenarios_names[i])
                        break
        
        [self.fail_scenarios.append("%s" %i) for i in self.scenarios_names if i not in self.success_scenarios]
            
        res_dic = dict(success = self.success_scenarios, fail = self.fail_scenarios)
        return res_dic

    def start_sniffer(self, cli_interface, idx, type):
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(idx)
        time.sleep(1)
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferLinkEmbedded(cli_interface)
        sniffer_port = traffic_generator.BASE_HOST_PORT + ( idx * 17 ) + 1 
        #save for sniffer close...
        self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE , "test_mode_dut" + str(idx) + "_" + str(type) + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
        try:
            time.sleep(2)
            #use the last appended sniffer  file...
            self.dut_host_sniffer.start( if_idx = idx , port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
            time.sleep(1)
            self.dut_embd_sniffer.start( if_idx = idx , server_ip = "192.168.120.1" , server_port = sniffer_port, sniffer_type = type)
            time.sleep(1)
            self.dut_embd_sniffer.start( if_idx = idx + 1 , server_ip = "192.168.120.1" , server_port = sniffer_port, sniffer_type = type)
            time.sleep( 30 )
        except Exception as e:
            time.sleep( 300 )
            pass
        return sniffer_port

    def stop_sniffer(self,sniffer_port):
        self.dut_host_sniffer.stop(sniffer_port)
        time.sleep(2)
        #self.dut_embd_sniffer.stop(1)
        #time.sleep(2)
        #self.dut_embd_sniffer.stop(2)

############ END Class TC_Dot4_State ############

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
        
        #tx counters
        self.total_frames_expected = dict()
        self.total_data_expected = dict()

        self.rx_uut_count = dict()

        self.total_frames_processed = 0
        self.frame_seq_err = 0
        self.counters = dict()
        self.total_tx_expected = 3
        self.proto = None
        self.total_tx_expected = None