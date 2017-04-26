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
        self.send_instance = Generate_Dot4_Send()
        self.sniffers_ports = list()
        self.sniffer_file = list()
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
        active_sniffer = self.initilization()
        ## Call Test scenarios blocks
        #chs_status = self.initilization()
        #if chs_status != globals.CHS_ACTIVE:
        #    return
        self.main(active_sniffer)
        #self.analyze_results()
        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def get_test_parameters( self ):
        super(TC_Dot4, self).get_test_parameters()
        g = []
        self._testParams = self.param.get('tx_dict', None )
        if self._testParams is None:
            self._testParams = self.param.get('link_dict', None )
        for i, t_param in enumerate(self._testParams):
            if 'tx' in vars(t_param):
                g.append(t_param.tx[0])
            if 'rx' in vars(t_param) and not t_param.rx is None:
                g.append(t_param.rx[0])
        self.tx_list = set(g)
        
        # Set Some test defaults 
        self._bsm_band       = self.param.get('bsm_band', 5890 )
        self._cch_band       = self.param.get('cch_band', 5920 )
        self._sch_band       = self.param.get('sch_band', 5900 )
        self._sch2_band      = self.param.get('sch2_band', 5870 )
        self._sch_proto_id   = self.param.get('sch_proto_id', 0x1234 )
        self._cch_proto_id   = self.param.get('cch_proto_id', 0x5678 )
        self._frame_rate_hz  = self.param.get('frame_rate_hz', 2000 )
        self._expected_frames         = self.param.get('expected_frames', 500 )
        self._cs_interval  = self.param.get('cs_interval', 50 )
        self._payload_len    = self.param.get('payload_len', 330 )
        self._chs_interval_max_expected_frames = self.param.get('chs_interval_max_expected_frames', 100 )
        self._bsm_proto_id = self.param.get('bsm_proto_id', 0x9abc )
        self._sync_tolerance = self.param.get('sync_tolerance', 2 )
        self._gps_lock_timeout_sec = self.param.get('gps_to', 2 )
        self._cs_interval = self.param.get('cs_interval', 50 )

    def runTest(self):
        pass
    
    def setUp(self):
        super(TC_Dot4, self).setUp()

    def unit_configuration(self):

        gps_lock = True
        gps_lock &= self.wait_for_gps_lock( self._uut[globals.CHS_DUT_ID + 1], self._gps_lock_timeout_sec )
        # Add Gps lock limit     
        self.add_limit( "GPS Locked" , int(True) , int(gps_lock), None , 'EQ')
        if gps_lock == False:
            log.info("GPS Lock failed")

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
                else: 
                    self.dot4_cli = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                    if self.register_flag is False:
                        self.register_flag = True
                        self._uut[uut_id].qa_cli(cli_name).register.device_register("hw",self._uut[uut_id].mac_addr,1,"eth1")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("v2x",0,"Secton")
                        self._uut[uut_id].qa_cli(cli_name).register.service_register("wdm",3,"Secton")

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
                    self.tx_list_.append( (uut_id, rf_if, cli_name, tx_.frames, tx_.frame_rate_hz, tx_) )
                    if self._uut[uut_id].external_host is u'':
                        self.dot4_cli_sniffer1 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        # Open general session
                        self._uut[uut_id].qa_cli(cli_name).link.service_create( type = 'remote' if self._uut[uut_id].external_host else 'hw')
                        self._uut[uut_id].qa_cli(cli_name).link.receive( tx_.frames, print_frame = 0, timeout = self.get_max_waiting_time())
                        active_sniffer = self.start_sniffer(self.dot4_cli_sniffer.interface(),1,"RX") 
                    else: 
                        self.dot4_cli1 = self._uut[uut_id].create_qa_cli(cli_name, target_cpu = self.target_cpu)
                        if self.register_flag is False:
                            self.register_flag = True
                            self._uut[uut_id].qa_cli(cli_name).register.device_register("hw",self._uut[uut_id].mac_addr,1,"eth1")
                            self._uut[uut_id].qa_cli(cli_name).register.service_register("v2x",0,"Secton")
                            self._uut[uut_id].qa_cli(cli_name).register.service_register("wdm",3,"Secton")
        return active_sniffer
             
    def main(self,active_sniffer):
        try:
            result = None
            waiting_time = self.get_max_waiting_time()
            #for rx in self.rx_list: 
            #    uut_id, rf_if, cli_name, frames, _ = rx
            #    self._uut[uut_id].qa_cli(cli_name).link.receive( frames, print_frame = 1, timeout = 12000 )

            test_type = self.param.get('link_dict', None )
            if test_type is None:
                test_type = self.param.get('params', None )
                if test_type is None:
                    test_type = self.param.get('send_dict', None )
                    if test_type is None:
                        test_type = self.param.get('tx_dict', None )
                        if test_type is None:
                            raise globals.Error("input is missing or corrupted")
                        else:
                            pass
                    else:
                        #Erroneuos Send Tests:
                        result = self.err_send.main(self.dot4_cli,self.param)
                        self.stats.results_dic["erroneuous_send"].append(result["success"])
                        self.stats.results_dic["erroneuous_send"].extend(result["fail"])
                else:
                    #Erroneuos Start Tests:
                    for i in ("alternate","immediate"):
                        result = self.err_req.main(i, self.param,self.dot4_cli)
                        self.stats.results_dic["erroneuous_request_%s" % i].append(result["success"])
                        self.stats.results_dic["erroneuous_request_%s" % i].extend(result["fail"])
                    result = self.err_req.main("continuous",self.param,self.dot4_cli) #continuous
                    self.stats.results_dic["erroneuous_request_continuous"].append(result["success"])
                    self.stats.results_dic["erroneuous_request_continuous"].extend(result["fail"])
            else:
                #State Tests:
                result = self.state_instance.main(self.dot4_cli1,self.dot4_cli_sniffer1)
                self.stats.results_dic["state_tests"].extend(result["success"])
                #to know from where start the indication of the failures
                self.stats.results_dic["state_tests"].append("fail:")
                self.stats.results_dic["state_tests"].extend(result["fail"])

            ##Channel Switch Tx Tests:
            #result = self.tx_instance.main(self.dot4_cli.uut.idx)
            #tg_sniffer_id = 0
            #rf_if = 1
            #self.add_limit( "(sniffer_id#%d, rf_if#%d), protocol id check " % ( tg_sniffer_id, rf_if), 0, result[tg_sniffer_id][rf_if]['sniffer_proto_fail'], None , 'EQ') 
            #self.add_limit( "(sniffer_id#%d, rf_if#%d), data compare check " % ( tg_sniffer_id, rf_if), 0, result[tg_sniffer_id][rf_if]['sniffer_data_cmp_fail'], None , 'EQ')
            #self.add_limit( "(sniffer_id#%d, rf_if#%d), Total Frames Prccessed on Sniffer " % ( tg_sniffer_id, rf_if), self._expected_frames, result[tg_sniffer_id][rf_if]['total_frames'], None , 'EQ') 

            #if tg_sniffer_id == globals.CHS_SNIF_CS_ID:
            #    self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx after sync tolerance " % ( tg_sniffer_id, rf_if), 0, result[tg_sniffer_id][rf_if]['chs_setup_failure'], None , 'EQ')
            #    self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx interval expected frames " % ( tg_sniffer_id, rf_if), 0, result[tg_sniffer_id][rf_if]['chs_interval_expected_frames_fail_count'] , None , 'EQ') 
            #    self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx interval equals to 46-50 ms " % ( tg_sniffer_id, rf_if), 0, result[tg_sniffer_id][rf_if]['chs_interval_expected_to_fail_count'] , None , 'EQ') 
            #    self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx during GI " % ( tg_sniffer_id, rf_if), 0, result[tg_sniffer_id][rf_if]['chs_tx_during_gi_fail_count'] , None , 'EQ')
            #    self.add_limit( "(sniffer_id#%d, rf_if#%d), Tx data read fail " % ( tg_sniffer_id, rf_if), 0, result[tg_sniffer_id][rf_if]['sniffer_data_read_fail'], None , 'EQ') 
            ##for a,b in result.iteritems():
            #    for c,d in b.iteritems():
            #        self.add_limit("Dot4 tx %s" % c , 1 , 1 , 1 , 'EQ')
            #        for e,f in d.iteritems():
            #            self.add_limit("Dot4 tx %s" % e , 1 , 1 , 1 , 'EQ')
            #            self.add_limit("Dot4 tx %d" % f , 1 , 1 , 1 , 'EQ')
            ##Channel Switch Rx Tests:
            #self.stats.results_dic["rx_test"] = self.rx_instance.main()
            ##Channel Switch Full Test:
            #self.stats.results_dic["full_test"] = self.full_test.main()
            
            self.stop_sniffer(active_sniffer[0],active_sniffer[1])
                
        except Exception as e:
            raise e
                   
    def analyze_results(self):
        self._test_frm_data = self.get_test_frm_data()
        for sniffer_file in self.sniffer_file:
            cap = pyshark.FileCapture(sniffer_file)
            for frame_idx,frame in  enumerate(cap):
                self.packet_handler(frame)

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
                    if "fail" in j:
                        flag = True
                        continue
                    if not flag:
                        self.add_limit("Dot4 State (%s) success" % j , 1 , 1 , 1 , 'EQ')
                        self.add_limit("Data proto_id 0x%x" % self.stats.proto , 1 , 1, None , 'EQ')
                        self.add_limit("Total frames sent %d" % self.stats.total_tx_expected ,self.stats.total_tx_expected, 3 , None , 'EQ')
                    else:
                        self.add_limit("Dot4 State (%s) fail" % j , 0 , 1 , 1 , 'EQ' )
            elif "tx_test" in i:
                continue
        #self.print_ref_results()

    def start_sniffer(self, cli_interface, idx, type):
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(idx)
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferAppEmbedded(cli_interface)
        sniffer_port = traffic_generator.BASE_HOST_PORT + ( idx * 17 ) #+ (1 if type is globals.CHS_TX_SNIF else 0)
        #save for sniffer close...
        self.sniffers_ports.append(sniffer_port)
        self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE ,  self._testMethodName + "_" + "dut" + str(idx) + "_" + str(type) + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
        try:
            time.sleep(2)
            #use the last appended sniffer  file...
            self.dut_host_sniffer.start( if_idx = idx , port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
            time.sleep(1)
            self.dut_embd_sniffer.start( if_idx = idx , server_ip = "192.168.120.1" , server_port = sniffer_port, sniffer_type = type)
            #time.sleep( 120 )
        except Exception as e:
            time.sleep( 300 )
            pass
        return (idx,sniffer_port)

    def stop_sniffer(self,idx,sniffer_port):
        self.dut_host_sniffer.stop(sniffer_port)
        time.sleep(2)
        self.dut_embd_sniffer.stop(idx)

    def get_max_waiting_time(self):
        # get the max waiting time
        transmit_time = 0
        for tx in self.tx_list_:
            uut_id, rf_if, cli_name, frames, frame_rate_hz, _ = tx
            expected_transmit_time = int(float( 1.0 / frame_rate_hz) *  frames) + 5
            transmit_time  = transmit_time if transmit_time > expected_transmit_time else expected_transmit_time

        rx_timeout = ( transmit_time + int(transmit_time * 0.25) ) * 1000
        
        return rx_timeout

    def packet_handler(self, packet):
        data = packet.data.data[4:len(ExpData)-1]
        ind = packet.data.data[0:4]
        if data != ExpData[4:len(ExpData)-1] :
            self.stats.data_mismatch +=1 
        if int(xp_idx) != int("0x"+ind,0) :
            self.stats.ref_rx_count_error +=1
            return int("0x" + data[:4],0) +1
        else :
            return 0
   
    def initilization(self):
        rc = 0
        # initilize uut
        self._uut[0] = globals.setup.units.unit(globals.CHS_DUT_ID)
        self._uut[1] = globals.setup.units.unit(globals.CHS_DUT_ID + 1)
        active_sniffer = self.unit_configuration()
        return active_sniffer

    def get_test_frm_data(self):
        frm_tx_data = ""
        for chr in range(self._payload_len):
            frm_tx_data += "".join('{:02x}'.format((chr % 0xFF) + 1))
        return frm_tx_data   

    def tearDown(self):
        super(TC_Dot4, self).tearDown()
        """for cli in self.active_cli_list:
            try:
                uut_id, rf_if, cli_name = cli
                # close link session
                self._uut[1].qa_cli(cli_name).link.socket_delete()
                self._uut[1].qa_cli(cli_name).link.service_delete()
            except Exception as e:
                print >> self.result._original_stdout, "ERROR in tearDown,  Failed to delete socket on uut {} for cli {}".format( uut_id, cli_name )
                log.error( "ERROR in tearDown,  Failed to clean uut {} for cli {}".format(uut_id, cli_name) )
            finally:
                self._uut[1].close_qa_cli(cli_name)
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
        self.test_param = self.param.get('params',None)
        self.state = self.param.get('state',None)
        
    def erroneous_request(self,state):
        for req in self.test_param:
            rc = self.start_request(req.get("channel_num"),
                               req.get("time_slot"),
                               req.get("op_class"),
                               req.get("immediate_access"))
            if "error" or "Invalid" not in rc :
                self.res_dic["fail"].append(state.upper() + " state: channel: %d time slot: %d operation class: %d immediate access: %d" %(req.get("channel_num"),req.get("time_slot"),req.get("op_class"),req.get("immediate_access")))
                self.end_channel("channel_num")
            else:
                self.res_dic["success"] += 1

        if state is not "continuous":
            rc = self.start_request(180,1,1,None)
            if "error" or "Invalid " not in rc :
                self.res_dic["fail"].append(state.upper() + " state: channel: %d time slot: %d operation class: %d immediate access: %d" %(req.get("channel_num"),req.get("time_slot"),req.get("op_class"),req.get("immediate_access")))
                self.end_channel("channel_num")
            else:
                self.res_dic["success"] += 1

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
        self.res_dic = dict(success = int(), fail = list())
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
        return self.res_dic
        
    def get_test_parameters( self,param ):
        self.state = param.get('state',None)
        self.test_param = param.get('send_dict',None)

    def erroneous_send(self):
        self.state_instance.start_continuous(172,self.dot4_cli)
        for send_p in self.test_param:
            rc = self.send_instance.send(self.dot4_cli,"40848",send_p.get("channel_num"),
                                    False,
                                    send_p.get("time_slot"),
                                    send_p.get("op_class"))
            if "error" or "Invalid" not in rc :
                self.res_dic["success"] += 1
            else:
                self.res_dic["fail"].append(state.upper() + " state state: channel %d time slot %d operation class %d" %(req.get("channel_num"),req.get("time_slot"),req.get("op_class")))
                self.end_channel("channel_num")
        self.end_channel(172)
    
    def end_channel(self,ch_num):
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        return rc 

############ END Class TC_Dot4_ERRONEOUS_Send ############

class TC_Dot4_Tx(TC_Dot4):
    """
    @class TC_Dot4_Tx
    @brief Test transmision while channel switching 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	3/7/2017
    """
    #A reminder - todo the high rate test! 
    def __init__(self, methodName = 'runTest', param = None):
        self.request = TC_Dot4_State()
        self.stats = Statistics()
        self.uut_id = None
        self.thread_list = []
        self.if_index = 1
        self.active_cli_list = []
        self._if_ch = {}
        self.interface = None
        self._sch_proto_id = hex(1234)
        self._cch_proto_id = hex(5678)
        self._expected_frames = 200
        self._frame_rate = 0
        self._payload_len = 330
        self._cs_interval  = 50
        self._protocol_id_last_seesion_last_frame = tree()
        self._last_frame_info = {'last_rfif' : 0, 'last_rfif_first_frame_ts' : 0, 'last_rfif_frame_id' : 0, 'last_rfif_last_frame_ts' : 0, 'last_rfif_sa' : 0, 'last_rfif_first_frame_id' : 0}
                    
    def main(self,uut_id):
        self.uut_id = uut_id
        #config tx and rx parameters
        #self.unit_configuration()
        #self.request.start_continuous(172)
        #self.send_instance.send(self.dot4_cli ,"Dot4 Tx",172)
        #self.request.start_continuous(176)
        #self.send_instance.send(self.dot4_cli ,"Dot4 Tx",172)
        self._init_sniffers_counters(1,1)
        self._init_sniffers_counters(0,2)
        return self.analyze_results()

    def guard_transmit(self):
        """
        change the frames num
        """

    def guard_receive(self):
        """
        change the frames num
        """

    def _init_sniffers_counters(self, sniffer_id, rf_if):
        self.stats.counters['chs_interval_expected_frames_fail_count'] = 0
        self.stats.counters['chs_interval_expected_to_fail_count'] = 0
        self.stats.counters['chs_tx_during_gi_fail_count'] = 0
        self.stats.counters['chs_setup_failure'] = 0
        self.stats.counters['sniffer_data_read_fail'] = 0
        self.stats.counters['sniffer_data_cmp_fail'] = 0
        self.stats.counters['total_frames'] = 0
        self.stats.counters['total_data'] = 0
        self.stats.counters['sniffer_proto_fail'] = 0
        self.stats.counters['sniffer_data_payload_len_fail'] = 0
        self._protocol_id_last_seesion_last_frame[sniffer_id][self._sch_proto_id]['last_frame_num'] = 0
        self._protocol_id_last_seesion_last_frame[sniffer_id][self._cch_proto_id]['last_frame_num'] = 0
        self._protocol_id_last_seesion_last_frame[sniffer_id][self._sch_proto_id]['pending_chs_interval_expected_to_fail_count'] = 0
        self._protocol_id_last_seesion_last_frame[sniffer_id][self._cch_proto_id]['pending_chs_interval_expected_to_fail_count'] = 0
     
    def get_test_frm_data(self):
        frm_tx_data = ""
        for chr in range(self._payload_len):
            frm_tx_data += "".join('{:02x}'.format((chr % 0xFF) + 1))
        return frm_tx_data

    def dut_tx_packet_handler(self, packet):
        self.stats.total_sniffer_frames_processed += 1
        current_active_ch_proto_id = int(packet.llc.type, 16)
        #handle first frame in the test
        if int(packet.frame_info.number) == 1:
            self._first_proto_id = current_active_ch_proto_id
            self._last_frame_info['last_rfif_proto_id'] = current_active_ch_proto_id
            self._last_frame_info['last_rfif_first_frame_id'] = int(packet.data.data[0:4],16)
            num = int(packet.radiotap.mactime) / 1000
            num = num % 100
            self._last_frame_info['last_rfif_first_frame_ts']  = (num)
            #all frames comes on the same physical rf interface - '2' need to destinguish between them...
            self._if_ch[self._first_proto_id] = 1
        #we do not know where in the time sequence of the Tx CS interval the transmission started so we skip first protocol id testing and starting from the second
        if current_active_ch_proto_id == self._first_proto_id:
            self.stats.counters['total_frames'] += 1
            self.stats.counters['total_data'] += int(packet.data.len)
            return
        #check if this is the first if channel, change and set the second channel for test
        if self._first_proto_id  != None:
            self._if_ch[current_active_ch_proto_id] = 2
        # Test packet data
        try:
            packet_data = ''.join(packet.data.data.split(':')).encode('ascii','ignore').upper()
        except Exception as e:
            self.stats.counters['sniffer_data_read_fail'] +=1
            #count total frames and data (amount in bytes)
            self.stats.counters['total_frames'] += 1
            self.stats.counters['total_data'] += int(packet.data.len)
        else:
            if current_active_ch_proto_id !=  self._last_frame_info['last_rfif_proto_id']:
                # handle first CS - this is the testing starting point...
                if self._first_proto_id  != None:
                    self._first_proto_id  = None
                    #arrival time of last frame
                    num = int(packet.radiotap.mactime) / 1000
                    num = num % 100
                    self._last_frame_info['last_rfif_last_frame_ts'] = (num)
                    #frame id of last frame
                    self._last_frame_info['last_rfif_frame_id'] = int(packet.data.data[0:4],16)
                    self.stats.counters['total_frames'] += 1
                    self._last_frame_info['last_rfif_proto_id'] = int(packet.llc.type, 16)
                    return
                if type == globals.CHS_RX_SNIF:
                  if self._protocol_id_last_seesion_last_frame[sniffer_id][int(packet.llc.type, 16)]['pending_chs_interval_expected_to_fail_count'] == 1:
                      if ((int(packet.data.data[0:4],16) - 1) == self._protocol_id_last_seesion_last_frame[sniffer_id][self._last_frame_info['last_rfif_proto_id']]['last_frame_num']):
                          self.stats.counters['chs_interval_expected_to_fail_count'] -=1

                self._protocol_id_last_seesion_last_frame[sniffer_id][self._last_frame_info['last_rfif_proto_id']]['last_frame_num'] = self._last_frame_info['last_rfif_frame_id']

                self.handle_chs_event(sniffer_id, type, self._last_frame_info['last_rfif_proto_id'])

                #arrival time of first frame of the interval
                self._last_frame_info['last_rfif_first_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
                self._last_frame_info['last_rfif_first_frame_id'] = int(packet.frame_info.number)
            #arrival time of last frame
            self._last_frame_info['last_rfif_last_frame_ts'] = (int(packet.radiotap.mactime) / 1000)
            #frame id of last frame
            self._last_frame_info['last_rfif_frame_id'] = int(packet.data.data[0:4],16)
            self._last_frame_info['last_rfif_proto_id'] = int(packet.llc.type, 16)
            self.stats.counters['total_frames'] += 1
            self.stats.counters['total_data'] += int(packet.data.len)

    def get_test_frm_data(self):
        frm_tx_data = ""
        for chr in range(self._payload_len):
            frm_tx_data += "".join('{:02x}'.format((chr % 0xFF) + 1))
        return frm_tx_data

    def analyze_results(self):
        self._test_frm_data = self.get_test_frm_data()
        # analyze last file only - DUT rf_if 2 (CS)
        cap = pyshark.FileCapture("Z:\\pcapLogs\\dot4\\dut1_tx_test_file.pcap")
        for frame_idx,frame in enumerate(cap):
            self.dut_tx_packet_handler(frame)  
        res = self.stats.counters 
        return res     

    def handle_chs_event(self, sniffer_id, type, proto_id):
        if type == globals.CHS_RX_SNIF:
            ''' check channel duration not more then defined by MIB '''
            if (((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) < self._cs_interval - globals.CHS_GI_MS - self._frame_rate) or ((self._last_frame_info['last_rfif_last_frame_ts'] - self._last_frame_info['last_rfif_first_frame_ts']) > self._cs_interval) or 
                 ''' check time sync and last frame in interval boumdries (2ms in GI are RX OK!)...'''                      ''' check time sync and first frame in interval boundries...'''
                 ((self._last_frame_info['last_rfif_last_frame_ts'] + self._frame_rate) % 10 > self._sync_tolerance / 2) or ((self._last_frame_info['last_rfif_first_frame_ts'] % 10 < globals.CHS_GI_MS - (self._sync_tolerance / 2)) or (self._last_frame_info['last_rfif_first_frame_ts'] % 10 > globals.CHS_GI_MS + 1))):
                     self.stats.counters['chs_interval_expected_to_fail_count'] +=1
                     self._protocol_id_last_seesion_last_frame[sniffer_id][proto_id]['pending_chs_interval_expected_to_fail_count'] = 1
        if type == globals.CHS_TX_SNIF:
            ''' check channel duration are alterbate from 0-50 to 50-100 '''
            if ((self._last_frame_info['last_rfif_first_frame_ts'] + self._frame_rate) % 10 > 0) or (self._last_frame_info['last_rfif_last_frame_ts'] % 10 > globals.CHS_GI_MS + 1):
                self.stats.counters['chs_interval_expected_to_fail_count'] +=1

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
    @brief Test dot4 start request with all modes (TC_CHS_01 - TC_CHS_08)
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
        self.sniffer_file = list()
        self.success_scenarios = list()
        self.fail_scenarios = list()
        self.send_instance = Generate_Dot4_Send()
    
    def main(self,dot4_cli,dot4_cli_sniffer):
        self.dot4_cli = dot4_cli
        self.frames = 100
        #Init reference unit to wait for frames on the required channels
        request = [1,172,1,1,0]
        rc = dot4_cli_sniffer.dot4.dot4_channel_start(request)
        if "error" or "Invalid" not in rc:
            request = [2,176,2,1,0]
            rc = dot4_cli_sniffer.dot4.dot4_channel_start(request)
            if "error" or "Invalid" not in rc:
                request = [1,184,3,1,0]
                rc = dot4_cli_sniffer.dot4.dot4_channel_start(request)
                if "error" or "Invalid" not in rc:
                    pass
                else:
                    raise globals.Error("error in start channel in ref unit")
            else:
                raise globals.Error("error in start channel in ref unit")
        else:
            raise globals.Error("error in start channel in ref unit")
        rc = dot4_cli_sniffer.link.socket_create(1, "data", 0x1234 )
        rc += dot4_cli_sniffer.link.socket_create(2, "data", 0x5678 )
        if "error" or "Invalid" not in rc:
            port1 = self.start_sniffer(dot4_cli_sniffer.interface(),1,"RX")
            dot4_cli_sniffer.link.receive(self.frames , print_frame = 1 , timeout = 12000)
            port2 = self.start_sniffer(dot4_cli_sniffer.interface(),2,"RX")
            self.continuous_scenario()
            self.continuous_end_scenario() 
            self.continuous_2_continuous_scenario()
            self.alternate_scenario_1()
            self.alternate_scenario_2()
            self.immediate_scenario_1()
            self.immediate_scenario_2()
            self.immediate_scenario_3()
            waiting_time = int(float( 1.0 / 10) *  self.frames) + 5
            time.sleep(int(float(waiting_time / 1000)) +20)
            #self.stop_sniffer(active_sniffer[0],active_sniffer[1])
            self.stop_sniffer(port1[0],port1[1])
            self.stop_sniffer(port2[0],port2[1])
        return self.analyze_results()        

    def start_continuous(self,ch_num,cli = None):
        if self.dot4_cli is None:
            self.dot4_cli = cli
        self.time_slots = 3
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 255
        rc = self.start_request()
        return rc

    def start_alternate(self,ch_num):
        self.time_slots = 2
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 0
        rc = self.start_request()
        return rc

    def start_immediate(self,ch_num):
        self.time_slots = 3
        self.channel_id["channel_num"] = ch_num
        self.channel_id["op_class"] = 1 
        self.immediate_access = 10
        rc = self.start_request()
        return rc

    def continuous_scenario(self):
        rc = self.start_continuous(172)
        if not "error" in rc:
            self.dot4_cli.link.socket_create(1, "data", 0x1234 )
            ex_rc = self.send_instance.send(self.dot4_cli ,"40843",172,True,self.frames) #expected: success
            if not "error" in ex_rc:
                self.success_scenarios.append("continuous data: 40843 frames_num: %d proto_id: %x" %(self.frames,0x1234))
            else:
                self.fail_scenarios.append("continuous, channel: 172")
            self.end_channel(172)

    def continuous_end_scenario(self):
        self.start_continuous(172)
        rc = self.end_channel(172)
        if "error" or "Invalid" not in rc:
            ex_rc = self.send_instance.send(self.dot4_cli ,"408431",0,True,self.frames) # expected: fail
            if not "error" in ex_rc:
                self.success_scenarios.append("continuous end")
            else:
                self.fail_scenarios.append("continuous end, channel: 172")
        else:
            raise Exception("error in start channel request")
        self.end_channel(172)

    def continuous_2_continuous_scenario(self):
        rc = ["",""]
        rc[0] = self.start_continuous(172)
        rc[1] = self.start_continuous(176)
        if ("error" or "Invalid") not in rc:
            self.dot4_cli.link.socket_create(1, "data", 0x5678 )
            ex_rc = self.send_instance.send(self.dot4_cli ,"4084323",172,True,self.frames) #expected: success
            if not "error" in ex_rc:
                self.end_channel(172)
                ex_rc = self.send_instance.send(self.dot4_cli ,"4084323",176,True,self.frames) #expected: success
                if not "error" in ex_rc:
                    self.success_scenarios.append("continuous to continuous")
                else:
                    self.fail_scenarios.append("continuous to continuous, channel: 176")
            else:
                    self.fail_scenarios.append("continuous to continuous, channel: 176")
            self.end_channel(176)
        else:
            raise Exception("error in start channel request")

    def immediate_scenario_1(self):
        rc = ["",""]
        rc[0] = self.start_continuous(172)
        rc[1] = self.start_immediate(176)
        if ("error" or "Invalid") not in rc:
            ex_rc = self.send_instance.send(self.dot4_cli ,"40843",176,True,self.frames) #expected: success
            if not "error" in ex_rc:
                ex_rc = self.send_instance.send(self.dot4_cli ,"40843",172,True,self.frames) #expected: success
                if not "error" in ex_rc:
                    self.success_scenarios.append("immediate")
                else:
                    self.fail_scenarios.append("immediate, channel: 176")
        self.end_channel(172)
        self.end_channel(176)
    
    def immediate_scenario_2(self):
        rc = ["","",""]
        rc[0] = self.start_alternate(172)
        rc[1] = self.start_alternate(176)
        rc[2] = self.start_immediate(184)
        if ("error" or "Invalid") not in rc:
            ex_rc = self.send_instance.send(self.dot4_cli ,"40847",180,True,self.frames) #expected: success
            if "error" not in ex_rc:
                ex_rc = self.send_instance.send(self.dot4_cli ,"40847",172,True,self.frames) #expected: success
                if "error" not in ex_rc:
                    ex_rc = self.send_instance.send(self.dot4_cli ,"40847",176,True,self.frames) #expected: success
                    if "error" not in ex_rc:
                        self.success_scenarios.append("immediate")
                    else:
                        self.fail_scenarios.append("immediate, channel: 176")
                else:
                    self.fail_scenarios.append("immediate, channel: 172")
            else:
                self.fail_scenarios.append("immediate, channel: 180")
        self.end_channel(172)
        self.end_channel(176)
        self.end_channel(184)

    def immediate_scenario_3(self):
        rc = self.start_immediate(172) #expected: fail
        if "error" in rc:
            self.success_scenarios.append("immediate without previous mode")
        else:
            self.fail_scenarios.append("immediate without previous mode, channel: 172")

    def alternate_scenario_1(self):
        rc = ["",""]
        rc[0] = self.start_alternate(172)
        rc[1] = self.start_alternate(176)
        if ("error" or "Invalid") not in rc:
            ex_rc = self.send_instance.send(self.dot4_cli ,"40841",176,True,self.frames) #expected: success
            if "error" not in ex_rc:
                ex_rc = self.send_instance.send(self.dot4_cli ,"40841",172,True,self.frames) #expected: success
                if "error" not in ex_rc:
                    self.success_scenarios.append("alternate")
                    self.end_channel(176)
                    ex_rc = self.send_instance.send(self.dot4_cli ,"40841",176,True,self.frames) #expected: fail
                    if "error" in ex_rc:
                        self.success_scenarios.append("alternate end")
                        ex_rc = self.send_instance.send(self.dot4_cli ,"40841",172,True,self.frames) #expected: success
                        ex_rc += self.send_instance.send(self.dot4_cli ,"40841",0,True,self.frames) #expected: success
                        if "error" in ex_rc:
                            self.fail_scenarios.append("alternate, channels: 172,default")
                    else:
                        self.success_scenarios.append("alternate end, channel: 176")
                else:
                    self.fail_scenarios.append("alternate, channel: 172")
            else:
                self.fail_scenarios.append("alternate, channel: 176")       
            self.end_channel(172)

    def alternate_scenario_2(self):
        rc = ["","",""]
        rc[0] = self.start_continuous(172)
        rc[1] = self.start_immediate(176)
        rc[2] = self.start_alternate(184)
        if ("error" or "Invalid") not in rc:
            ex_rc = self.send_instance.send(self.dot4_cli ,"408412",176,True,self.frames) #expected: success
            if "error" not in ex_rc:
                ex_rc = self.send_instance.send(self.dot4_cli ,"408412",184,True,self.frames) #expected: success
                if "error" not in ex_rc:
                    self.success_scenarios.append("immediate to alternate, channels: 172, 184")
        else:
            self.fail_scenarios.append("immediate to alternate, channel: 176")
        self.end_channel(172)
        self.end_channel(176)
        self.end_channel(184)

    def alternate_scenario_3(self):
        rc = ["",""]
        rc[0] = self.start_continuous(172)
        rc[1] = self.start_alternate(184)
        if ("error" or "Invalid") not in rc:
            ex_rc = self.send_instance.send(self.dot4_cli ,"408413",184,True,self.frames) #expected: success, to check: durring not define channel time - there is no transmission
            if "error" not in ex_rc:
                self.success_scenarios.append("continuous to alternate, channels: 172, 184")
        self.end_channel(172)
        self.end_channel(184)

    def start_request(self):
        request = []
        request.append(self.if_index)
        request.append(self.channel_id.get("op_class"))
        request.append(self.channel_id.get("channel_num"))
        request.append(self.time_slots)
        request.append(self.immediate_access)
        rc = self.dot4_cli.dot4.dot4_channel_start(request)
        return rc

    def end_channel(self,ch_num):
        rc = self.dot4_cli.dot4.dot4_channel_end(self.if_index, ch_num)
        return rc

    def analyze_results(self):
        res_dic = dict(success = self.success_scenarios, fail = self.fail_scenarios)
        return res_dic

    def start_sniffer(self, cli_interface, idx, type):
        self.dut_host_sniffer = traffic_generator.TGHostSniffer(idx)
        self.dut_embd_sniffer = traffic_generator.Panagea4SnifferAppEmbedded(cli_interface)
        sniffer_port = traffic_generator.BASE_HOST_PORT + ( idx * 17 ) + 1 
        #save for sniffer close...
        self.sniffer_file.append(os.path.join( common.SNIFFER_DRIVE , "test_mode_dut" + str(idx) + "_" + str(type) + "_" + time.strftime("%Y%m%d-%H%M%S") + "." + 'pcap'))  
        try:
            time.sleep(2)
            #use the last appended sniffer  file...
            self.dut_host_sniffer.start( if_idx = idx , port = sniffer_port, capture_file = self.sniffer_file[len(self.sniffer_file) - 1] )
            time.sleep(1)
            self.dut_embd_sniffer.start( if_idx = idx , server_ip = "192.168.120.1" , server_port = sniffer_port, sniffer_type = type)
            #time.sleep( 120 )
        except Exception as e:
            time.sleep( 300 )
            pass
        return (idx,sniffer_port)

    def stop_sniffer(self,idx,sniffer_port):
        self.dut_host_sniffer.stop(sniffer_port)
        time.sleep(2)
        self.dut_embd_sniffer.stop(idx)

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
        self.op_class = 0
        self.channel_num = 0
        self.time_slot = -1
        self.tx_data = None
        
    def send(self ,dot4_cli ,tx_data ,ch_num ,flag = False ,frames = 5000 ,rate_hz = 100 ,time_slot = 0):
        self.dot4_cli = dot4_cli
        self.channel_num = ch_num
        self._testMethodName = "test_dot4"
        if self.dot4_cli.uut.external_host == u'':
            self.start_dut_sniffer(self.dot4_cli.interface(),1,globals.CHS_RX_SNIF,self._testMethodName)
        if flag == False:
            self.frames = frames
            self.tx_data = tx_data
            self.data_rate = 12
            self.rate_hz = rate_hz
            self.user_priority = 7
            rc = self.dot4_cli.dot4.transmit(self.frames,
                                        self.rate_hz,
                                        self.payloud_len,
                                        self.tx_data,
                                        self.user_priority,
                                        self.data_rate,
                                        self.powerdbm8,
                                        self.op_class,
                                        self.channel_num,
                                        self.time_slot)
        else:
            rc = self.dot4_cli.dot4.transmit_empty(self.channel_num,self.frames)
        return rc    
    
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
        self.total_frames_processed = 0
        self.frame_seq_err = 0
        self.data_mismatch = tree()
        self.counters = dict()
        self.bad_ch_type = tree()
        self.total_sniffer_frames_processed = 0
        self.total_unicast_ack_frames = 0
        self.sniffer_data_fail = 0
        self.wlan_da_mismatch = 0
        self.user_prio_mismatch = 0
        self.data_band_mismatch = tree()
        self.total_tx_expected = 3
        self.tx_count = 0
        self.sniffer_proto_fail = 0
        self.total_frames_processed = tree()
        #self.frame_fields = frameStatistics()
        self.total_tx_time_exceed = tree()
        self.total_frame_cnt_exceed = tree()
        self.proto = None
        self.total_tx_expected = None