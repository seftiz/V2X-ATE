import sys
import unittest
import inspect
import os
import time
from time import ctime
import re
import argparse
import socket
import math
import numpy
import subprocess
import win32gui
import win32con
import csv
import ConfigParser
import logging
import telnetlib
from os.path import isfile, join
from os import listdir
import pandas as pd

sys.path.append(r"C:/sysHW")

from utilities import constants as c

from utilities.rx_iq_imbalance_cal import IQImbalance
from utilities.CreateLabReport_Internal import ReportInternal
from utilities.CreateLabReport_External import ReportExternal
from utilities import hw_tools
from utilities import rf_vector_signal

from lib.instruments import RFswitch_drv
from lib.instruments.TempChamberControl import TempChamberControl
from lib.instruments.SignalGeneratorMXG import SignalGeneratorMXGdriver
from lib import globals
#from uuts import common
#from uuts import interface

pysdk_version = c.common['QA_SDK_VERSION']  # get updated sdk version
pysdk = r'\\fs01\docs\SW\qa-sdk' + '\\' + pysdk_version + r'\python'
print "\n\npysdk: ", pysdk
sys.path.append(pysdk)

from atlk import hwregs
from atlk import rxoobsampler
from utilities import tssi

import numpy as np
from PIL import ImageGrab

from atlk.uboot import uboot
from atlk import mibs

# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)

class GlobalState(object):
    pass

global_state = GlobalState()
global_state.do_reset = True

def uut_py_sdk_connect(ip,telnet_port1,telnet_port2):
    rssi_evm = rxoobsampler.open("telnet://"+ip+":"+str(telnet_port1))
    regs = hwregs.open("telnet://"+ip+":"+str(telnet_port2))   # Telnet connection

    time.sleep(2)
    if (rssi_evm and regs):
        print "Connected to board"
    else:
        print "Telnet Connection failed.."
        sys.exit()
    return rssi_evm, regs

class CreateLogFile(object):
    def Destination(self,destination_path):
        self.log_dest = os.path.dirname(destination_path)
    def Logger(self,log_name):
        # create logger
        logger = logging.getLogger(log_name)

        # create console handler and set level to debug
        LogFile = logging.FileHandler(self.log_dest+"/"+log_name+".log")
        logger.setLevel(logging.INFO)

        # create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # add formatter to LogFile
        LogFile.setFormatter(formatter)
        
        # remove prints to output window
        for h in logger.handlers:
            logger.removeHandler(h)

        # add LogFile to logger
        logger.addHandler(LogFile)
        
        return logger

class ParametrizedTestCase(unittest.TestCase):
    """ TestCase classes that want to be parametrized should inherit from this class. """
    def __init__(self, methodName='runTest', param={}):
        super(ParametrizedTestCase, self).__init__(methodName)
        self.param = param

    @staticmethod
    def parametrize(testcase_class, param={}):
        """ Create a suite containing all tests taken from the given
            subclass, passing them the parameter 'param'.
        """
        testloader = unittest.TestLoader()
        testnames = testloader.getTestCaseNames(testcase_class)
        suite = unittest.TestSuite()
        for name in testnames:
            suite.addTest(testcase_class(name, param=param))
        return suite
 
    def setUp(self):
        #hw_tools.wait_until_awake(evk_ip)
        self.start_test = time.clock()
        UUT.connect(evk_ip)
        return super(ParametrizedTestCase, self).setUp()

    def tearDown(self):
        TesterDevice.transmit_rf("OFF")
        #UUT.reset_board( self.plug_id)
        self.end_test = time.clock()
        print "Test duration: %.2gs\n" % (self.end_test-self.start_test)
        Logger[self.param['macIf']].info ("Test duration: %.2gs\n" % (self.end_test-self.start_test))
        return super(ParametrizedTestCase, self).tearDown()

class SystemTestsSDK_snmp(ParametrizedTestCase):        
    def test_sdk_snmp(self):
        print "------------ Start SNMP browser validation test -------------------"
        Logger[self.param['macIf']].info("------------ Start SNMP browser validation test -------------------")
        print "\n Configuration parameters : "
        for key,value in self.param.iteritems():
            if key == 'rate':
                value = value/2
            print "%s: %s " %(str(key),str(value))
            Logger[self.param['macIf']].info (str(key) +': '+ str(value))
        
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,c.TELNET_PORT1,c.TELNET_PORT2)
        # VSA select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',1) # Switch B to com 1 
    
        print "Channel frequency:", str(self.param['ch_freq'])

        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)

        Freq = self.param['ch_freq']*1e6
        Port = 2 # left port
        Atten = c.common['TX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]
        LO_leakage_list = []

        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        UUT.set_mib( c.snmp['DataRate'][self.param['macIf']], self.param['rate'])
        UUT.set_mib( c.snmp['TxPower'][self.param['macIf']], self.param['tx_power'])
        UUT.set_mib( c.snmp['FrameLen'][self.param['macIf']], self.param['pad'])
        UUT.set_mib( c.snmp['TxEnabled'][self.param['macIf']], 1)  # Start transmission
        
        # Configure test parameters
        TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
        TesterDevice.prepare_vsa_measurements()
        time.sleep(0.2)

        data_rate = 0
        PSDU_CRC = '0.0'
        packet_len = None
        # Get Measurements 
        try:
            TesterDevice.prepare_vsa_measurements()
            data_rate = TesterDevice.get_vsa_measure('dataRate')
            PSDU_CRC = TesterDevice.get_vsa_measure('psduCrcFail')
            tx_power = TesterDevice.get_vsa_measure('rmsPowerNoGap')
            packet_len = TesterDevice.get_vsa_measure('numPsduBytes')
        except:
            pass
        print "Measured data_rate, PSDU_CRC, tx_power, packet_len:  ",data_rate, PSDU_CRC, tx_power, packet_len
        Logger[self.param['macIf']].info("Expected data rate "+str(self.param['rate']/2)+", Measured: "+str(data_rate))
        Logger[self.param['macIf']].info("Expected frequency "+str(self.param['ch_freq'])+", status "+str(PSDU_CRC))
        Logger[self.param['macIf']].info("Expected Tx power: "+str(self.param['tx_power'])+", Measured: "+str(tx_power))
        Logger[self.param['macIf']].info("Expected packet lengh: "+str(self.param['pad'])+", Measured: "+str(packet_len))

        
        """
        # TX RX diversity settings
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
        UUT.connect(evk_ip)
                
        CSD_list = [0,1,2,3,4]
        div_register_set_0 = [0x3f0,0x1031,0x2071,0x3071,0x40f1]
        div_register_set_1 = [0x2070,0x2073,0x2073,0x2073,0x2073]
        #diversity_reg = 0x0
        i = 0
        for a in CSD_list:
            snmp_manager_master(evk_ip, 'wlanTxCsd', a, macIf_SNMP, False, True)
            diversity_reg = regs.get(("phy"+str(macIf), 0x18c))
            if self.param['macIf'] == 0:
                print "Expected register settings: "+str(hex(div_register_set_0[i]))+", Measured: "+str(hex(diversity_reg))
                Logger[self.param['macIf']].info("Expected register settings: "+str(hex(div_register_set_0[i]))+", Measured: "+str(hex(diversity_reg)))
            else:
                print "Expected register settings: "+str(hex(div_register_set_1[i]))+", Measured: "+str(hex(diversity_reg))
                Logger[self.param['macIf']].info("Expected register settings: "+str(hex(div_register_set_1[i]))+", Measured: "+str(hex(diversity_reg)))
            i+=1   
                
        snmp_manager(evk_ip, self.ch, self.ch_power, self.rate, transmit=False)
        self.ch_power = 20
        """
        UUT.set_mib( c.snmp['TxEnabled'][self.param['macIf']], 2)  # Stop transmission
        Logger[self.param['macIf']].info("----------------- Test finished --------------------------------------")
        Logger[self.param['macIf']].info("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

class SystemTestsSensitivity(ParametrizedTestCase):
    def test_sensitivity(self):
        
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if (self.param['macIf'] == 1):
            channel_name,channel_name_co = channel_name_co,channel_name
        '''
        if self.param['macIf'] == 0:
            channel_name = 'chA'
            channel_name_co = 'chB'
        else:
            channel_name = 'chB'
            channel_name_co = 'chA'        
        '''
        print "\nConfiguration parameters: "
        for key,value in self.param.iteritems():
            if key == 'rate':
                value = value/2
            print "%s: %s " %(str(key),str(value))
            Logger[self.param['macIf']].info (str(key) +': '+ str(value))

        rssi_evm, regs = uut_py_sdk_connect(evk_ip,c.TELNET_PORT1,c.TELNET_PORT2)
        print "Channel frequency:", str(self.param['ch_freq'])

        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)

        print "\n-------------- Start sensitivity test -------------------"
        Logger[self.param['macIf']].info ('------------------- Start Sensitivity test -------------------------')

        # VSA select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',2) # Switch B to com 2    
        
        full_res = []
        
        ch = self.param['ch_freq']
        rate = (self.param['rate'])/2
        num_pckt2send = self.param['num_pckt2send']
        pad = self.param['pad']

        # Reading results file, needs for accsess to sensitivity section
        #ResultsFileHandler.read(final_res_file)
        
        firstString = True
            
        # AGC cross-over points  (-67dBm,-49dBm)
        pow_range = c.common['SENSITIVITY_TEST_RANGE']
        #pow_range = range(-88, -78, 1)
            
        #TesterDevice.signal_generator_load_file(utilities_dir+ "qpsk_6MHz_1034Bytes.mod")
        if self.param['dsrc_channel_models_enable'] == 0:
            channel_loop = 1
        else:
            channel_loop = len(c.common['dsrc_channel_models_list'])

        # The test measurements loop
        for i in range(channel_loop):
            res_fname = logs_path + "sensitivity_logs/sensitivity_test_res_" + str(Number) +"_"+str(ch)+"_"+str(rate)+ "_" +str(self.param['macIf']) +"_" +str(self.param['temperature']) +".txt"
            try:
                if self.param[tester_type] == 1:
                    #TesterDevice.signal_generator_load_file(utilities_dir+ "autotalks_1000bytes_10mhz_"+str(rate)+".mod")
                    TesterDevice.signal_generator_load_file(utilities_dir+ "32u_1000bytes_10mhz_"+str(rate)+".mod")
                else:
                    if self.param['dsrc_channel_models_enable'] == 0:
                        if str(rate) == '4.5':
                            TesterDevice.signal_generator_load_file("4_5MBPS") 
                        else:
                            TesterDevice.signal_generator_load_file(str(rate)+"MBPS")
                    elif self.param['dsrc_channel_models_enable'] == 1:                        
                        res_fname = logs_path + "sensitivity_logs/"+c.common['dsrc_channel_models_list'][i]+"_sensitivity_test_res_" + str(Number) +"_"+str(ch)+"_"+str(rate)+ "_" +str(self.param['macIf']) +"_" +str(self.param['temperature']) +".txt"
                        TesterDevice.signal_generator_load_file(c.common['dsrc_channel_models_list'][i],1)
                    else:
                        print "File not found.."
                        sys.exit()
            except:
                print "Loading file failed"
            
            TesterDevice.transmit_rf("OFF",1)
            print "Sensitivity result file name = ",res_fname

            # Check if result file exists
            if (os.path.exists(res_fname)):            
                print "Note: File exists....the results will be added to the existing file"
                try:
                    res_file = open(res_fname,"a")
                except:
                    print "File %s not accesible "%res_fname
            else:
                res_file = open(res_fname,"w")                
            
            # Logging
            Logger[self.param['macIf']].info('Created results file = '+res_fname)

            # Execute test
            point = True
            sens_point = 0    
            for pow in pow_range:                
                # Set pow and Trigger
                #start_test = time.clock()
                
                if self.param[tester_type] == 1:
                    # When using IQ2010 tester we must transmit 1 packet for clean RF output 
                    #TesterDevice.transmit_rf("ON",1)
                    TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,1)     # Transmit 1 packet with Single trigger mode 
                
                #end_test = time.clock()
                #print "LitePoint VSG time for transmit 1 packet: %.2gs\n" % (end_test-start_test)        
                # Get initial RX counter value 
                init_value = UUT.get_mib(c.snmp['RxMacCounter'][self.param['macIf']])
                #print "init_value = ",init_value 
                TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,self.param['num_pckt2send'])     #Transmit n packets with Single trigger mode 
                #start_test = time.clock()
                TesterDevice.transmit_rf("ON",1)
                #end_test = time.clock()
                #print "LitePoint VSG time for 1000 packets transmition: %.2gs\n" % (end_test-start_test)                
                #init_value_debug = UUT.get_mib(c.snmp['RxMacCounter'][self.param['macIf']])
                #print "init_value_debug = ",init_value_debug 
                
                # Get DUT EVM
                start_test = time.clock()
                
                try:
                    dictionaryRes = rssi_evm.get(self.param['macIf']+1,1, timeout=1)
                    evm_average = dictionaryRes.get('evm')[1]       # Average EVM
                except:
                    evm_average = "0"
                """
                    end_test = time.clock()
                    print "LitePoint VSG time for EVM calc hwregs: %.2gs\n" % (end_test-start_test)                
                    start_test = time.clock()
                
                    try:
                        evm_average = hw_tools.evm_calc(str(hex(regs.get(('phy'+str(self.param['macIf'])), c.register['EVM_OUT']))),str(hex(regs.get(('phy'+str(self.param['macIf'])), c.register['CONST_POWER_BIN_COUNT']))))
                    except:
                        evm_average = "0"
                        pass
                    end_test = time.clock()
                    print "LitePoint VSG time for EVM calc local function: %.2gs\n" % (end_test-start_test)                
                """
                print("Average EVM : %s" %  evm_average)


                # Wait 8 seconds to complete transmission
                #time.sleep(8)   # to do calculate exact time for transmission, Packet transmission time = Packet size / Bit rate
                
                cur_powPin = pow - float(c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype])
                #print "Pin signal power: "+str(cur_powPin)+" dBm"
                
                # Logging
                Logger[self.param['macIf']].info('Pin signal power: '+str(cur_powPin)+' dBm')

                # Get RX counter value after transmission of n packets      
                next_rx_cnt = UUT.get_mib(c.snmp['RxMacCounter'][self.param['macIf']])
            
                # Calculate recieved packets
                recieved_cnt = next_rx_cnt - init_value

                # PER calculation
                per = float(num_pckt2send - recieved_cnt)/num_pckt2send    
                print "Pin signal power: "+str(cur_powPin)+" dBm, " + "PER: "+str(per*100) + "%"

                Logger[self.param['macIf']].info('PER : '+str(per*100)+' %')
                res_dict = {}
                res_dict["channel"] = ch
                res_dict["rate"] = format(float(rate),'0.2f')
                res_dict["interval_usec"] = self.param['interval_usec']
                #res_dict["interval_usec"] = 32
                res_dict["packets_to_send"] = num_pckt2send
                res_dict["packet_size"] = pad 
                res_dict["rx_ip"] = evk_ip
                res_dict["PER_ch"] = per*100
                res_dict["EVM"] = format(float(evm_average),'0.2f')
                res_dict["macIF"] = self.param['macIf']
                res_dict["macIF_counter_val"] = recieved_cnt
                                                           
                full_res.append( (cur_powPin,res_dict) )
                
                # Print results to integrative file
                for item in full_res:
                    res2 = item[1]
                    if firstString == True:
                        header = "%20s" %("cur_powPin")
                        for key2 in res2.keys():
                            header += ",%20s" %(key2)
                        header += "\n"
                        res_file.write(header)
                    firstString = False
                    
                    st = "%20s" %(item[0])
                    for key2 in res2.keys():
                        st +=  ",%20s" %(str(res2[key2]))
                    st += "\n"
                    res_file.write(st)
                full_res = []
                
                #Sensitivity point trap
            
                if (per*100<= c.expected['EXPECTED_PER_HIGH']) and (cur_powPin<c.common['MIN_SENSITIVITY_BY_RATE'][str(rate)]) and (per!=0) and point:
                    sens_point = cur_powPin
                    Logger[self.param['macIf']].info ('________________________________Sensitivity point =' + str(cur_powPin))
                    print "_______________________________>>>Sensitivity point =" + str(cur_powPin)
                    point = False
                else:
                    pass               

            res_file.close()

            # Compare measured vs excpected    
            if sens_point <c.common['MIN_SENSITIVITY_BY_RATE'][str(rate)]:
                status_s = "Pass"
            else:
                status_s = "Fail"
            
            # Write sensitivity results to file
            with open(sens_fname, "a+") as out_file:
                hw_tools.print_and_log(out_file, "{:s}, {:s}, {:s}, {:s}, {:s}, {:s}, {:s},".format(time.strftime("%d/%m/%Y"),str(c.common['dsrc_channel_models_list'][i]),str(channel_name),str(rate),str(ch),str(sens_point),status_s))
            out_file.close()

            #Stop transmission
            TesterDevice.transmit_rf("OFF")
            UUT.set_to_txrx_mode(self.param['macIf'],c.register['RF_SYNTHESIZER_REG'][self.param['macIf']],regs)  # Set additional channel to txrx mode
        try:
            sensitivity_res_loader_ = np.loadtxt(sens_fname, delimiter=',', skiprows=1, usecols=(3,4))
            rate, max_sens_by_rate = sensitivity_res_loader.max(axis=0)
            rate, min_sens_by_rate = sensitivity_res_loader.min(axis=0)
            print "Maximum sensitivity %s by rate %s"% (str(rate),str(max_sens_by_rate))
            print "Minimum sensitivity %s by rate %s"% (str(rate),str(min_sens_by_rate))
            # Add min,max sensitivity by rate 
            with open(sens_fname, "a+") as out_file:
                hw_tools.print_and_log(out_file, "%s, Maximum sensitivity %s, rate %s,"% (str(channel_name),str(rate),str(max_sens_by_rate)))
                hw_tools.print_and_log(out_file, "%s, Minimum sensitivity %s, rate %s,"% (str(channel_name),str(rate),str(min_sens_by_rate)))
            out_file.close()
        except:
            print "Failed to get min, max value"


        """
        # Replace waveform to default waveform 6mbps
        try:
            if self.param[tester_type] == 1:
                TesterDevice.signal_generator_load_file(utilities_dir+ "autotalks_1000bytes_10mhz_6.mod")
            else:
                TesterDevice.signal_generator_load_file("6MBPS") 
        except:
            print "Loading file failed"
        """
        del rssi_evm
        del regs 
        
        TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,0) # continious mode
        Logger[self.param['macIf']].info('----------------- Test finished --------------------------------------')
        Logger[self.param['macIf']].info('||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||')

class SystemTestsLNA_VGA_status(ParametrizedTestCase):
    def test_LNA_VGA_status(self):
        fname = logs_path + "LNA_VGA_values_{}.csv".format(self.param['macIf'])
        
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,c.TELNET_PORT1,c.TELNET_PORT2)

        # VSG select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',2) # Switch B to com 2    
    
        print ('\n================== LNA VGA test START ===============================')
        Logger[self.param['macIf']].info('----------------- Start LNA VGA test  -------------------------')
        print "Channel frequency:", str(self.param['ch_freq'])

        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)

        rate = (self.param['rate'])/2
        
        # Loading waveform
        try:
            if self.param[tester_type] == 1:
                TesterDevice.signal_generator_load_file(utilities_dir+ "autotalks_1000bytes_10mhz_"+str(rate)+".mod")
            else:
                if str(rate) == '4.5':
                    TesterDevice.signal_generator_load_file("4_5MBPS") 
                else:
                    TesterDevice.signal_generator_load_file(str(rate)+"MBPS") 
        except:
            print "Loading file failed"
        TesterDevice.transmit_rf("OFF",1)

        # Start tranmission
        print "Start transmitting.."
        pow_range = range(-80,-30)
        rep = 5
        RSSI_sum = 0
        resRxEVM_sum = 0
        with open(fname, "w") as out_file:
            hw_tools.print_and_log(out_file, "RSSI, EVM, LNA_VGA_value, MIN_DIST_VGA_OFF_dB,PACKET_CNT,")
            for pow in pow_range:
                RSSI_sum = 0
                resRxEVM_sum = 0
                #LNA_VGA_value = 0
                #INIT_LNA_VGA_value = regs.get(('phy'+str(self.param['macIf']), c.register['LNA_VGA_LOCK_reg']))
                for i in range (0,rep):        
                    if self.param[tester_type] == 1:         
                        # When using IQ2010 tester we must transmit 1 packet for clean RF output 
                        TesterDevice.transmit_rf("ON",1)
                        TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,1)     # Transmit 1 packet with Single trigger mode 
            
                    # Get initial RX counter value 
                    init_value = UUT.get_mib(c.snmp['RxMacCounter'][self.param['macIf']])
                    TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,1)     #Transmit 1 packet with Single trigger mode 
                    TesterDevice.transmit_rf("ON",1)

                    cur_powPin = pow - float(c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype])
                    print "Pin signal power: "+str(cur_powPin)+" dBm"
                
                    # Logging
                    Logger[self.param['macIf']].info('Pin signal power: '+str(cur_powPin)+' dBm')
                    #LNA_VGA_value += regs.get(('phy'+str(self.param['macIf']), c.register['LNA_VGA_LOCK_reg']))
                    LNA_VGA_value = regs.get(('phy'+str(self.param['macIf']), c.register['LNA_VGA_LOCK_reg']))
                    
                    next_rx_cnt = UUT.get_mib(c.snmp['RxMacCounter'][self.param['macIf']])
                
                    # Packet counter status recieved/not recived
                    recieved_cnt = next_rx_cnt - init_value
                    """
                    #Get RX EVM
                    dictionaryRes = rssi_evm.get(self.param['macIf']+1, 1, timeout=10)

                    RSSI = dictionaryRes.get('rssi')[1]     # Average RSSI
                    resRxEVM = dictionaryRes.get('evm')[1]       # Average EVM
                    print("Average RSSI : %sdBm" %  RSSI)
                    print("Average EVM : %sdB" %  resRxEVM)
                    """
                    # RSSI and EVM calculations extracted from registers 
                    p1 = regs.get(('phy'+str(self.param['macIf']), c.register['RSSI_PART1']))
                    p2 = regs.get(('phy'+str(self.param['macIf']), c.register['RSSI_PART2']))
                    evm_out = regs.get(('phy'+str(self.param['macIf']), c.register['EVM_OUT']))
                    const_power_bin_count = regs.get(('phy'+str(self.param['macIf']), c.register['CONST_POWER_BIN_COUNT']))
                    print "reg {:s} = {:s},reg {:s} = {:s}".format(str(hex(c.register['EVM_OUT'])),str(hex(evm_out)),str(hex(c.register['CONST_POWER_BIN_COUNT'])),str(hex(const_power_bin_count)))
                    RSSI_sum += float((p1<<3|p2)-math.pow(2, 11))/math.pow(2, 3) - c.common['BACKOFF_COMP']  # Final Pin in dB    
                    resRxEVM_sum += hw_tools.evm_calc(str(hex(evm_out)),str(hex(const_power_bin_count)))

                    if recieved_cnt == 1:
                        print "Packet recieved"
                    else:
                        print "Not recieved"
                RSSI = RSSI_sum/rep 
                resRxEVM = resRxEVM_sum/rep
                #LNA_VGA_value = LNA_VGA_value/rep
                print "EVM : ",str(resRxEVM)
                # LNA register 2 msb bits check and VGA minimum distance (VGA min points 0xC0,0x80,0x00)
                #delta = abs(INIT_LNA_VGA_value-LNA_VGA_value)
                #print "delta ",delta
                VGA_RANGE = [0xC0,0x80,0x0]
                LNA_status = LNA_VGA_value>>6   # 2 msb bits reg 0x19d
                print "LNA_status ", str(hex(LNA_status))
                #print "hex(LNA_VGA_value) =  ",str(hex(LNA_VGA_value))
                vga_min_dist = None
                prev_vga_min_dist = None
                if (LNA_status)==3:
                    vga_min_dist = abs(LNA_VGA_value - int(0xC0))*2   # each VGA step = 2db
                elif (LNA_status)==2:
                    vga_min_dist = abs(LNA_VGA_value - int(0x80))*2   # each VGA step = 2db
                elif (LNA_status)==0:
                    vga_min_dist = abs(LNA_VGA_value - int(0x0))*2   # each VGA step = 2db
                else:
                    prev_vga_min_dist = vga_min_dist
                hw_tools.print_and_log(out_file, "{:s},{:s},{:s},{:s},{:d},".format(str(RSSI),str(format(float(resRxEVM),'0.2f')),str(hex(LNA_VGA_value)),str(vga_min_dist),recieved_cnt))

        UUT.set_to_txrx_mode(self.param['macIf'],c.register['RF_SYNTHESIZER_REG'][self.param['macIf']],regs)  # Set additional channel to txrx mode
        del rssi_evm
        del regs
        out_file.close()

        #Stop transmission
        TesterDevice.transmit_rf("OFF")

        Logger[self.param['macIf']].info("----------------- Test finished --------------------------------------")
        Logger[self.param['macIf']].info("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")
        

class SystemTestsTx_Measurement(ParametrizedTestCase):
    def test_tx_measurement(self):
        
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if (self.param['macIf'] == 1):
            channel_name,channel_name_co = channel_name_co,channel_name
        '''

        if self.param['macIf'] == 0:
            channel_name = 'chA'
            channel_name_co = 'chB'
        else:
            channel_name = 'chB'
            channel_name_co = 'chA'
        '''
        Logger[self.param['macIf']].info('----------------- Start TX path test --------------------------------------')
        self.res_tx_evm, self.res_power, self.res_lo_leakage, self.res_tx_amp, self.res_tx_phase, self.res_freq_err, self.res_symb_clk_err = 0,0,0,0,0,0,0
        rate = (self.param['rate'])/2
        Logger[self.param['macIf']].info("Rate: "+str(rate))
        Logger[self.param['macIf']].info("Frequency: "+str(self.param['ch_freq']))

        if (len(mac_if_list) > 1) and (self.param['macIf'] == 1) and global_state.do_reset:
            print "\nReboot board and start testing"
            UUT.reset_board(c.PLUG_ID)
            global_state.do_reset = False
        else:
            print "do_reset = ",global_state.do_reset
        
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,c.TELNET_PORT1,c.TELNET_PORT2)
        print "Channel frequency:", str(self.param['ch_freq'])

        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)

        
        # -----------------  TX PATH --------------------------------------
        # VSA select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',1) # Switch B to com 1 
        Freq = (self.param['ch_freq'])*1e6
        Port = 2 # left port
        Atten = c.common['TX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]
        
        print 'Start transmiting from channel %s' %str(self.param['macIf'])
        UUT.set_mib( c.snmp['DataRate'][self.param['macIf']], self.param['rate'])
        UUT.set_mib( c.snmp['TxPower'][self.param['macIf']], self.param['tx_power'])
        UUT.set_mib( c.snmp['FrameLen'][self.param['macIf']], self.param['pad'])
        #UUT.set_mib( c.snmp['TxPeriod'][self.param['macIf']], self.param['interval_usec'])

        UUT.set_mib( c.snmp['TxEnabled'][self.param['macIf']], 1)   # Transmit ON

        #TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
        #TesterDevice.prepare_vsa_measurements()
        print "Perform measurements.."
                                                         
        # VSA measurements loop
        rep = 5
        TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
        time.sleep(0.2)
        #TesterDevice.vsa_set_agc()
        #TesterDevice.prepare_vsa_measurements()

        SUMresTxEVM = 0
        SUMresTxAmplImbl = 0
        SUMresTxPhaseImbl = 0
        SUMresTxPower = 0
        SUMresLOleakage = 0
        SUMresTxFreqErr = 0
        SUMresTxSymbClk = 0

        for i in range (0,rep):          
            #TesterDevice.prepare_vsa_measurements()
            #time.sleep(0.2)
            try:
                SUMresTxEVM += TesterDevice.get_tx_vsa_measure('evmAll')
                SUMresTxAmplImbl += TesterDevice.get_tx_vsa_measure('ampErrDb')
                SUMresTxPhaseImbl += TesterDevice.get_tx_vsa_measure('phaseErr')
                SUMresTxPower += TesterDevice.get_tx_vsa_measure('rmsPowerNoGap')
                SUMresLOleakage += TesterDevice.get_tx_vsa_measure('dcLeakageDbc')
                SUMresTxFreqErr += TesterDevice.get_tx_vsa_measure('freqErr')
                SUMresTxSymbClk += TesterDevice.get_tx_vsa_measure('clockErr')
            except:
                print "VSA measurement iteration %s failed" %str(i)
                continue 

                            
        self.res_tx_evm = (float("{0:.2f}".format(SUMresTxEVM/rep)))
        self.res_tx_amp = (float("{0:.2f}".format(SUMresTxAmplImbl/rep)))
        self.res_tx_phase = (float("{0:.2f}".format(SUMresTxPhaseImbl/rep)))
        self.res_power = (float("{0:.2f}".format(SUMresTxPower/rep)))
        self.res_lo_leakage = (float("{0:.2f}".format(SUMresLOleakage/rep)))
        self.res_freq_err = (float("{0:.2f}".format(SUMresTxFreqErr/rep/1e3)))  #kHz
        self.res_symb_clk_err = (float("{0:.2f}".format(SUMresTxSymbClk/rep)))
        # Add results to list
        results_list = [self.res_tx_evm, self.res_power, self.res_lo_leakage, self.res_tx_amp, self.res_tx_phase, self.res_freq_err, self.res_symb_clk_err]    
            
        print "TX EVM :                 " ,self.res_tx_evm
        print "TX power :               " ,self.res_power
        print "TX LO leakage :          " ,self.res_lo_leakage
        print "TX IQ ampl imbalance :   " ,self.res_tx_amp
        print "TX IQ phase imbalance :  " ,self.res_tx_phase
        print "TX Frequency error    :  " ,self.res_freq_err
        print "TX Symbol clock error :  " ,self.res_symb_clk_err
        
        status = []
        all_status = "Fail"
        fails_list = []
        # Compare results with expected results and get status
        if (abs(c.expected['EXPECTED_TX_EVM']) <= abs(float(self.res_tx_evm))):
            status.append('Pass')
        else:     
            status.append('Fail')
            fails_list.append('TxEvm_dB = '+str(self.res_tx_evm))
        #if ((c.expected['EXPECTED_TX_POWER_LOW'] <= float(self.res_power) <= c.expected['EXPECTED_TX_POWER_HIGH'])) or (c.expected['EXPECTED_TX_LOW_POWER_LOW'] <= float(self.res_power) <= c.expected['EXPECTED_TX_LOW_POWER_HIGH']):
        if (float(self.param['tx_power'])-1) <= float(self.res_power) <= (float(self.param['tx_power'])+1):
            status.append('Pass')
        else:
            status.append('Fail') 
            fails_list.append('TxPower_dBm = ' + str(self.res_power))
        if (c.expected['EXPECTED_LO_LEAKAGE']<=abs(self.res_lo_leakage)):
            status.append('Pass')
        else:
            status.append('Fail')
            fails_list.append('LO_leakage_dBc = '+str(self.res_lo_leakage))
        if (c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW']<=float(self.res_tx_amp) <=c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH']):
            status.append('Pass')
        else:
            status.append('Fail')
            fails_list.append('Tx_IqImb_Ampl_dB = '+str(self.res_tx_amp))
        if (c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW']<=float(self.res_tx_phase) <=c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH']):
            status.append('Pass')
        else:
            status.append('Fail')
            fails_list.append('Tx_IqImb_Phase_Deg = '+str(self.res_tx_phase))
        if (c.expected['EXPECTED_TX_FREQ_ERROR_LOW']<=float(self.res_freq_err) <=c.expected['EXPECTED_TX_FREQ_ERROR_HIGH']):
            status.append('Pass')
        else:
            status.append('Fail')
            fails_list.append('Tx_Freq_Err_kHz = '+ str(self.res_freq_err))
        if (c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW']<=float(self.res_symb_clk_err) <=c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH']):
            status.append('Pass')
        else:
            status.append('Fail')
            fails_list.append('Tx_Symb_Clk_Err_ppm = '+str(self.res_symb_clk_err))
        Logger[self.param['macIf']].info("Results list: "+'[res_tx_evm, res_power, res_lo_leakage, res_tx_amp, res_tx_phase, res_freq_err, res_symb_clk_err]')
        Logger[self.param['macIf']].info("Status list: "+str(status))
        Logger[self.param['macIf']].info("Fails list: "+str(fails_list))

        if "Fail" in status:
            all_status = "Fail"
        else:
            all_status = "Pass"
        # Write tx meas results to file
        with open(tx_meas_fname, "a+") as out_file:
            hw_tools.print_and_log(out_file, "{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},{:s},".format(
                                ctime(),
                                str(channel_name),
                                str(rate),
                                str(self.param['pad']),
                                str(self.param['ch_freq']),
                                str(self.param['tx_power']),
                                str(self.res_power),
                                "<"+str(c.expected['EXPECTED_LO_LEAKAGE']),
                                str(self.res_lo_leakage),
                                "<"+str(c.expected['EXPECTED_TX_EVM']),
                                str(self.res_tx_evm),
                                str(c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW']),
                                str(self.res_tx_amp),
                                str(c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH']),
                                str(c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW']),
                                str(self.res_tx_phase),
                                str(c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH']),
                                str(c.expected['EXPECTED_TX_FREQ_ERROR_LOW']),
                                str(self.res_freq_err),
                                str(c.expected['EXPECTED_TX_FREQ_ERROR_HIGH']),
                                str(c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW']),
                                str(self.res_symb_clk_err),
                                str(c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH']),
                                all_status,
                                str(fails_list).replace(",",";")))
        out_file.close()

        UUT.set_mib( c.snmp['TxEnabled'][self.param['macIf']], 2)   # Transmit OFF
        UUT.set_to_txrx_mode(self.param['macIf'],c.register['RF_SYNTHESIZER_REG'][self.param['macIf']],regs)  # Set additional channel to txrx mode
        Logger[self.param['macIf']].info('----------------- Test finished --------------------------------------')

class SystemTestsCongigurationCompare(ParametrizedTestCase):
    def test_subsystem_configuration_compare(self):
        print "\nConfiguration compare: "
        #Logger[self.param['macIf']].info (str(key) +': '+ str(value))

        rssi_evm, regs = uut_py_sdk_connect(evk_ip,c.TELNET_PORT1,c.TELNET_PORT2)
        
        module_subsystem_list = ["phy","mac","rf"]
        for i in module_subsystem_list:
            #value_out = regs.get((i+str(self.param['macIf']), c.register['REGISTER_1']))
            print "Code not complete. Need to add relevant registers"

class SystemTestsSummaryReport(object):
    #def generate_report(self,evk_ip,choice_num,temperature_range,total_status,file_name,test_results):
    def generate_report(self,ip,selected_test,temperature_range,total_status,file_name):
        # Initialaze Results file
        ResultsFileHandler = ConfigParser.RawConfigParser()
        var_list = ["test id","test name","date","sw version","board mac address","ip address","temperature"]

        if (os.path.exists(file_name)):            
            print "Note: File exist....the results will be added to the existing file"
            #ResFileName = open(final_res_file,"r+")  # open for reading and writing
            pass
        else:

            # Open results file for adding sections
            ResFileName = open(file_name,"w") 
            ResultsFileHandler.read(file_name)
            #sections_list = ["TestID","Test Name","Created","SW version","Board MAC address","Board IP address","Temperature","Total tests","Passed tests","Failed tests","Status"]
            sections_list = ["Tests summary","Total tests","Passed tests","Failed tests","Status"]
            for i in sections_list:
                if ResultsFileHandler.has_section(i) == False:
                    ResultsFileHandler.add_section(i)
           
            # Preparing results section 
            for i in var_list:
                ResultsFileHandler.set('Tests summary',i, "None")

            ResultsFileHandler.set('Total tests',"number of tests","None")
            ResultsFileHandler.set('Passed tests',"passed","None")
            ResultsFileHandler.set('Failed tests',"failed","None")
            #ResultsFileHandler.set('Status',"status","None")

            #Write added sections to file
            try:
                print "Preparing results file.."
                with ResFileName as file:
                    ResultsFileHandler.write(file)
            except IOError:
                print "Can't open file..Please check the file"
            ResFileName.close()
        # Tests results summary
        # Open results file for adding sections
        ResFileName = open(tests_report_file,"r+") 
        ResultsFileHandler.read(tests_report_file)
        try:
            # Get sdk version,ethaddr        
            tn = telnetlib.Telnet( c.TERMINAL_SERVER_IP , c.TS_PORT)
            tn.read_until("ate> ",2)
            tn.write("version\n\r")
            sdk_version = tn.read_until("ate> ",2)
            #print "sw_version = ", sdk_version.split()[1]
            sdk_version_str = sdk_version.split()[1]   
            tn.close()    
            # Enter to uboot mode and get ethernet address, uboot version
            uboot_mode = uboot(c.TERMINAL_SERVER_IP, c.TS_PORT, c.PLUG_ID)
            uboot_mode.enter_uboot()
            uboot_params = uboot_mode.get_dict()
            uboot_version = uboot_mode.execute("version")
            ethaddr = uboot_params['ethaddr']
            del uboot_mode
        except:
            uboot_version = "N/A"
            ethaddr = "N/A"
            sdk_version_str = "N/A"
        
        
        #var_list = ["test id","test name","date","sw version","board mac address","ip address","temperature","number of tests"]
    
        ResultsFileHandler.set('Tests summary',"test id", str(selected_test))
        ResultsFileHandler.set('Tests summary',"test name", "test_tx_measurement,test_sensitivity")
        ResultsFileHandler.set('Tests summary',"date",time.strftime("%d/%m/%Y"))
        ResultsFileHandler.set('Tests summary',"sw version",sdk_version_str)
        ResultsFileHandler.set('Tests summary',"board mac address",ethaddr)
        ResultsFileHandler.set('Tests summary',"ip address",ip)
        ResultsFileHandler.set('Tests summary',"temperature",temperature_range)
        ResultsFileHandler.set('Total tests',"number of tests",total_status)    
        pass_counter = 0
        fail_counter = 0
        # Scan tx measurements test results
        for line in open(tx_meas_fname,"r"):
            if "Pass" in line:
                pass_counter +=1
                ResultsFileHandler.set('Passed tests',"passed",pass_counter)
            elif "Fail" in line:
                fail_counter +=1
                ResultsFileHandler.set('Failed tests',"failed",fail_counter)
        if not(fail_counter == 0):
            ResultsFileHandler.set('Status',"status_test_tx_measurement","Fail")
        else:
            ResultsFileHandler.set('Status',"status_test_tx_measurement","Pass")
    
        # Scan sensitivity test results
        for line in open(sens_fname,"r"):
            if "Pass" in line:
                pass_counter +=1
                ResultsFileHandler.set('Passed tests',"passed",pass_counter)
            elif "Fail" in line:
                fail_counter +=1
                ResultsFileHandler.set('Failed tests',"failed",fail_counter)
        if not(fail_counter == 0):
            ResultsFileHandler.set('Status',"status_test_sensitivity","Fail")
        else:
            ResultsFileHandler.set('Status',"status_test_sensitivity","Pass")    

            
        
        #Write added sections to file
        try:
            print "Preparing results file.."
            with ResFileName as file:
                ResultsFileHandler.write(file)
        except IOError:
            print "Can't open file..Please check the file"
        ResFileName.close()
        
        # Agregate and parse by max.min.mean value
        data_tx_meas = pd.read_csv(tx_meas_fname)
        data_sens = pd.read_csv(sens_fname)
        grouped_measured_power = data_tx_meas.groupby(["Channel", "Rate_Mbps"])["TxPower_dBm"]
        result_tx_meas = grouped_measured_power.aggregate({'min': np.min,
                                                           'max': np.max,
                                                           'average': np.mean})
        print result_tx_meas
        
        grouped_sensitivity = data_sens.groupby(["Test","Channel","Rate_Mbps"])["Sensitivity_dB"]
        result_sens = grouped_sensitivity.aggregate({'min': np.min,
                                                     'max': np.max,
                                                     'average': np.mean})
        print result_sens
        

        grouped_evm = data_tx_meas.groupby(["Channel","Rate_Mbps"])["TxEvm_dB"]
        result_evm = grouped_evm.aggregate({'min': np.min,
                                            'max': np.max,
                                            'average': np.mean})
        print result_evm


        # Writing the aggregated results to csv file
        out = logs_path + '\out.csv'
        out_file = open(out, 'a')
        hw_tools.print_and_log(out_file, "Date,"+time.strftime("%d/%m/%Y"))
        hw_tools.print_and_log(out_file, "SW version,"+str(sdk_version_str))
        hw_tools.print_and_log(out_file, "Board mac address,"+str(ethaddr))
        hw_tools.print_and_log(out_file, "IP address,"+str(ip))
        hw_tools.print_and_log(out_file, "Temperature,"+str(temperature_range))

        hw_tools.print_and_log(out_file, "TxPower_dBm")
        result_tx_meas.to_csv(out_file)
        hw_tools.print_and_log(out_file, "Sensitivity_dB")
        result_sens.to_csv(out_file)
        hw_tools.print_and_log(out_file, "TX_EVM_dB")
        result_evm.to_csv(out_file)
        out_file.close()
        

global MXGen
global iq2010
global Logger
global evkDUT
global sens_point
global macIf        
global rssi_evm, regs
global TesterDevice
global mac_if_list

      
if __name__ == '__main__':
    
    # Load configuration file
    cfg_file_name = "hw_setup_config.ini"
    current_dir = os.getcwd() # returns current working directory
    print "Tests directory: %s"  %current_dir
    cfg_dir_name = "%s\\configuration\\" % current_dir 
    utilities_dir = "%s\\utilities\\" % current_dir 
    cfg_file = os.path.join(cfg_dir_name, cfg_file_name)

    if not os.path.exists( cfg_file ):
        raise globals.Error("configuration file \'%s\' is missing." % (cfg_file) )

    MXGen = None
    Logger = [0,0]
    evkDUT = None
    active_ch = ''

    choice_list = []
    choice_num = []

    try:
        evk_ip = raw_input('\nEnter DUT IP:  ')
        if (evk_ip == ""):
            print "\nInput error: Illegal IP"
            sys.exit()
        else:
            pass
        socket.inet_aton(evk_ip)
        # legal IP
    except socket.error:
        print "SocketError: Not legal IP address !!!"
        sys.exit()
    
    # Connections
    RFswitch = RFswitch_drv.RFswitch_driver()
    
    UUT = hw_tools.Unit()   #UUT constructor
    UUT.connect(evk_ip)     #Snmp connection

    #selected_tester = str(c.common['tester_device']['IQ2010'])
    selected_tester = raw_input('\nSelect tester (1 for IQ2010, 2 for MXG):  ')
    #tester_ip = raw_input('\nEnter tester IP (127.0.0.1) for VSA IQ2010/NXN or (10.10.0.8) for MXG:  ') 
    tester_ip = '127.0.0.1'

    TesterDevice = rf_vector_signal.TesterDeviceManager()
    TesterDevice.connect_to_tester(tester_ip, selected_tester)  # '127.0.0.1'  for IQ2010 device Local host, '10.10.0.8' - for MXG
    TesterDevice.signal_generator_settings() # Default settings loading
    
    #Loading default waveform
    try:
        if selected_tester == '1':
            TesterDevice.signal_generator_load_file(utilities_dir+ "autotalks_1000bytes_10mhz_6.mod")
        else:
            TesterDevice.signal_generator_load_file("6MBPS") 
    except:
        print "Failed to download file to IQ2010"

    localtime = time.asctime(time.localtime(time.time()))
    
        # Test selection menu
    print("\n")
    print (30 * '-')
    print ("   M A I N - M E N U")
    print (30 * '-')
    print (" 0. System configuration compare test")
    print (" 1. SDK SNMPB validation test")
    print (" 2. LNA VGA status test")
    print (" 3. TX measurement test")
    print (" 4. RX sensitivity test")
    print (" 5. Tests summary report")
    print (" 20. Exit")
    print (30 * '-')
    print("\n")
    
    
    ## Wait for valid input in while...not ###
    is_valid=0   
    while not is_valid :
        try :
            choice =(raw_input('Enter your choice [1-20] separated by commas: '))
            choice_list = choice.split(',')
            choice_num = [int(x.strip()) for x in choice_list]
            print "Selected tests: " ,choice_num
            is_valid = 1 ## set it to 1 to validate input and to terminate the while..not loop
            if 20 in choice_num:
                print "Exit."
                sys.exit()
            else:
                continue
        except ValueError, e :
            print ("'%s' is not a valid integer." % e.args[0].split(": ")[1])
            sys.exit()
    
    # Select channel 
    active_ch = raw_input('\nSelect RF test channel (a or b or ab):  ')
    
    board_name_dict = {1:'ATK22016 (EVK4/Pangaea4)',2:'ATK22022 (Audi)',3:'ATK22027 (Laird)',4:'ATK23010 (Fitax)',5:'ATK22017 (EVK4S/Pangaea4S)'}
    print "\nBoard type selection:"
    for key,value in board_name_dict.iteritems():
        print "type %s:      %s" %(str(key),str(value))
        

    type = raw_input('\nSelect type: ')        
    N = raw_input('\nEnter Board number: ')   # Enter evk/Pangaea number
    if (N.isdigit() == True):
        pass
    else:
        print "\nInputError:  Not valid Board number ", N
        print "Please enter number only"
        N = raw_input('\nEnter Board number: ')
        if (N.isdigit() == True):
            pass
        else:
            print "Invalid Board number!!"
            sys.exit()

    type_dict = {'1':"ATK22016",'2':"ATK22022",'3':"ATK22027",'4':"ATK23010","5":"ATK22017"}
    btype = "_"+type_dict.get(type)
    Number = type_dict.get(type)+'_'+ N 
    #Number = "dsrc_6mbps_"+type_dict.get(type)+'_'+ N       
    chamber_test = raw_input('\nUse chamber (y/n):  ')

    print "\nReboot board and start testing"
    UUT.reset_board(c.PLUG_ID)
   
    suite = unittest.TestSuite()

    '''
    # Select channel and run the tests
    mac_if_list = []
    mac_opts = ['a','b']    #chA, chB
    for mac in mac_opts:
        if mac in active_ch:
            print "Selected mac if " + str(mac_opts.index(mac))
            mac_if_list.append( mac_opts.index(mac) )
    '''
    # Get tester type
    for key,value in c.common['tester_device'].iteritems():
        if selected_tester == str(value):
            tester_type = key
        else:
            pass


    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    # @@@@@@@@@@@@@@@@@@@@@@   For scenarios release the parameters block    @@@@@@@@@@@@@@@@@@@@@@@@@
    # Scenario description:  Run all frequencies with all rates
    # Parameters block:
    data_frequency_list = c.DATA_FREQUENCY_LIST    
    data_rate_list = c.DATA_RATE_LIST
    data_power_list = c.DATA_TX_POWER_LIST
    data_lengh = c.DATA_LENGH
    temp_range = c.TEMPERATURE_RANGE
    packet_interval = c.PACKET_INTERVAL_USEC
    dsrc_channel_models_enable = c.DSRC_CHANNEL_MODELS_ENABLE  # 0 - disable, 1 - enable
    if dsrc_channel_models_enable == int(selected_tester):
        print "\n Error: Incompatible test!! dsrc_channel_models_enable enabled,but MXG not selected"    
        sys.exit()
    else:
        pass
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    
    #Chamber temperature  configuration
    if chamber_test == 'y':
        TEMPERATURE_STEP = 2 #   
        #serPortNum = int(raw_input("enter serial port of temperature chamber:  "))
        serPortNum = 1  # COM1 - default
        tempChamberControl =  TempChamberControl.TempChamberControl(port_num = serPortNum)
        temperature_range = temp_range
    else:
        temperature_range = [25]
    over_limit = 90
    for t in temperature_range:    
        # Select channel and run the tests
        mac_if_list = []
        mac_opts = ['a','b']    #chA, chB
        for mac in mac_opts:
            if mac in active_ch:
                print "Selected mac if " + str(mac_opts.index(mac))
                mac_if_list.append( mac_opts.index(mac) )

        if (chamber_test == 'y'):
            print "Setting temperature to ",t
            chamberTemp = int(tempChamberControl.GetTemp())
            print "\n The Chamber Temperature is ",chamberTemp
            tempChamberControl.SetTemp(t)
            time.sleep(0.5)
            # Temperature point stabilization (accuracy of 3 degree while loop)
            while abs(chamberTemp-t) >= 3:
                chamberTemp = int(tempChamberControl.GetTemp())
                if (chamberTemp < t  and over_limit > chamberTemp):
                    print "\n The current temperature is", chamberTemp, "less then", t
                    print 'Waiting..'
                if chamberTemp > t:
                    print "\n The current temperature is", chamberTemp, "more then", t
                time.sleep(20)
            print "\n The current temperature stabilized on ", chamberTemp
            if t == 25:
                pass
            else:
                print "Waiting 20 minutes for temperature absorbtion..\n"
                time.sleep(60*20)
        else:
            pass
        print "\n Start testing .. "

        # @@@@@@@@@@@@@@@@@@@@@@  Scenarious Test parameters creation
        param_dict_list = []
        param_dict_list_sens = []
        add_list = []   # Scenario collector list
        add_list_sens = []  # Sensitivity test

        for data in data_frequency_list:
            for item in data_rate_list:
                param_dict_list_sens = [{tester_type:int(selected_tester),'macIf':0,'ch_freq':data,'rate':item*2,'tx_power':20,'pad':1000,'num_pckt2send':1000,'interval_usec':packet_interval,'temperature':t,"dsrc_channel_models_enable":dsrc_channel_models_enable,"bandwidth":10},
                                            {tester_type:int(selected_tester),'macIf':1,'ch_freq':data,'rate':item*2,'tx_power':20,'pad':1000,'num_pckt2send':1000,'interval_usec':packet_interval,'temperature':t,"dsrc_channel_models_enable":dsrc_channel_models_enable,"bandwidth":10}]
                add_list_sens.append(param_dict_list_sens)
                for pad in data_lengh:
                    for tx_power in data_power_list:
                        ###########################################  Configure setup parameters  ###################################################################################################################################################################################
                        param_dict_list = [{tester_type:int(selected_tester),'macIf':0,'ch_freq':data,'rate':item*2,'tx_power':tx_power,'pad':pad,'num_pckt2send':1000,'interval_usec':100,'temperature':t,"dsrc_channel_models_enable":dsrc_channel_models_enable,"bandwidth":10},
                                            {tester_type:int(selected_tester),'macIf':1,'ch_freq':data,'rate':item*2,'tx_power':tx_power,'pad':pad,'num_pckt2send':1000,'interval_usec':100,'temperature':t,"dsrc_channel_models_enable":dsrc_channel_models_enable,"bandwidth":10}]
                        ############################################################################################################################################################################################################################################################        
                        add_list.append(param_dict_list)
    
        """ 
        # Print configured list parameters
        print "Print configured tests list parameters:\n"
        for i in add_list:
            print i
            print '\n'
        print "Print configured tests list parameters for sensitivitty test:\n"
        for i in add_list_sens:
            print i
            print '\n'
        """
        # Create Results folder
        logs_path = r'C:/Local/wavesys/trunk/lab_utils/Test_Environment/logs/'+Number+"/"    #to do: Change to generic location
        final_res_file = logs_path + "/final_results_" + Number + "_" + str(t) + ".txt"
        sens_fname = logs_path + "sensitivity_collected_results_{}_{}.csv".format(str(Number),str(t))
        tx_meas_fname = logs_path + "tx_measure_collected_results_{}_{}.csv".format(str(Number),str(t))
        tests_report_file = logs_path + "tests_report_{}.csv".format(str(Number))
        print "Log path destination : ",logs_path

        d = os.path.dirname(logs_path)
        if not os.path.exists(d):
            os.makedirs(d)
            os.makedirs(d+"/sensitivity_logs")
        
        # Create Rx Sensitivity results columns
        if not os.path.exists(sens_fname):
            with open(sens_fname, "w") as out_file:
                hw_tools.print_and_log(out_file, "Date,Test,Channel,Rate_Mbps,Frequency_MHz,Sensitivity_dB,Status")
            out_file.close()

        # Create TX measurements results columns
        if not os.path.exists(tx_meas_fname):
            with open(tx_meas_fname, "w") as out_file:
                hw_tools.print_and_log(out_file, "Date,Channel,Rate_Mbps,PacketLengh,Frequency_MHz,Exp_TxPower_dBm,TxPower_dBm,Exp_LO_leakage_dBc,LO_leakage_dBc,Exp_TxEvm_dB,TxEvm_dB,Min_Tx_IqImb_Ampl_dB,Tx_IqImb_Ampl_dB,Max_Tx_IqImb_Ampl_dB,Min_Tx_IqImb_Phase_Deg,Tx_IqImb_Phase_Deg,Max_Tx_IqImb_Phase_Deg,Min_Tx_Freq_Err_kHz,Tx_Freq_Err_kHz,Max_Tx_Freq_Err_kHz,Min_Tx_Symb_Clk_Err_ppm,Tx_Symb_Clk_Err_ppm,Max_Tx_Symb_Clk_Err_ppm,Status,Deviation,")
            out_file.close() 

        
        # ----------  Individual test cases execution --------------------------
        ### Take action as per selected menu-option ###
        for i in range(len(mac_if_list)):
            CreateLOG = CreateLogFile()
            CreateLOG.Destination(logs_path)
            log_file = 'IP_'+evk_ip+'_Log_'+str(mac_if_list[i]) + "_" + str(param_dict_list[i]['temperature'])
            Logger[mac_if_list[i]] = CreateLOG.Logger(log_file)
            
            if 0 in choice_num:
                suite.addTest(ParametrizedTestCase.parametrize(SystemTestsCongigurationCompare,param=param_dict_list[mac_if_list[i]]))
            if 1 in choice_num:
                for s in range(len(data_rate_list)):
                    suite.addTest(ParametrizedTestCase.parametrize(SystemTestsSDK_snmp, param=add_list[s][mac_if_list[i]]))                
            if 2 in choice_num:
                suite.addTest(ParametrizedTestCase.parametrize(SystemTestsLNA_VGA_status, param=param_dict_list[mac_if_list[i]]))
            if 3 in choice_num:
                for s in range(len(data_frequency_list)*len(data_rate_list)*len(data_lengh)*len(data_power_list)):
                    suite.addTest(ParametrizedTestCase.parametrize(SystemTestsTx_Measurement, param=add_list[s][mac_if_list[i]]))
            if 4 in choice_num:
                for s in range(len(data_frequency_list)*len(data_rate_list)):
                    suite.addTest(ParametrizedTestCase.parametrize(SystemTestsSensitivity, param=add_list_sens[s][mac_if_list[i]]))
            if 555 in choice_num:
                print "Missed test"
            if 6 in choice_num:
                print "Missed test"
            if 7 in choice_num:
                print "Missed test"
            unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: cmp(y, x)
        result = unittest.TextTestRunner(verbosity=0).run(suite)    
        # ----------------------------------------------------------------------
    try:
        total_status = str((str(result).split(" ")[1:4])).replace(">","")
        print "result ",
    except:
        print "result except ",result
    print "\nAdding results to tests report.. "
    

    # Graceful return to room temperature
    try:
        chamberTemp = int(tempChamberControl.GetTemp())
        if (c.TEMPERATURE_DEFAULT-3)<=chamberTemp <=(c.TEMPERATURE_DEFAULT+3):
            print "\n The current temperature is",chamberTemp
            pass
        else:    
            try:
                print "Return to room temperature"
                tempChamberControl.SetTemp(c.TEMPERATURE_DEFAULT)   #25 degree Celcius
                chamberTemp = int(tempChamberControl.GetTemp())
                print "\n The current temperature is",chamberTemp
                time.sleep(60*60)
                chamberTemp = int(tempChamberControl.GetTemp())
                print "\n The current temperature is",chamberTemp
                print "Temperature loop is finished!!"
            except:
                print "The chamber not in use"
    except:
        pass

    if 5 in choice_num:
        report = SystemTestsSummaryReport()
        report.generate_report(evk_ip,choice_num,temperature_range,total_status,tests_report_file)


    """
    with open(tests_report_file, "r+") as out_file:
        for line in out_file:
            if "Pass" in line:
                #print "Total status: ",total_status
                total_status = "True"
                pass
            else:
                total_status = "False"
                hw_tools.print_and_log(out_file, line)
        try:
            total_status = bool(total_status)&True        
            print "Total status: ",total_status
        except:
            pass
    out_file.close()
    """
'''
#if __name__ == '__main__':
#    main()
'''    
