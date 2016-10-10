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

#pysdk_version = r'qa-sdk-3.3.2-rc2'

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

pysdk_version = c.common['QA_SDK_VERSION']  # get updated sdk version

pysdk = r'\\fs01\docs\SW\qa-sdk' + '\\' + pysdk_version + r'\python'
print "\n\npysdk: ", pysdk
sys.path.append(pysdk)

from atlk import hwregs
from atlk import rxoobsampler
from utilities import tssi

import numpy as np
from atlk import powerswitch
#powerswitch.reboot_plugs(['nps01/6'])
from PIL import ImageGrab

from atlk.uboot import uboot
from atlk import mibs

rep_expected = ["<"+str("{0:.2f}".format(c.expected['EXPECTED_HI_TX_EVM'])),"<"+str("{0:.2f}".format(c.expected['EXPECTED_TX_EVM'])),str("{0:.2f}".format(c.expected['EXPECTED_TX_HI_POWER_LOW']+1))+u"\u00B11",str("{0:.2f}".format(c.expected['EXPECTED_TX_POWER_LOW']+1))+u"\u00B11","<"+str("{0:.2f}".format(c.expected['EXPECTED_LO_LEAKAGE'])),u"\u00B1"+str("{0:.2f}".format(c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH'])),u"\u00B1"+str("{0:.2f}".format(c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH'])),u"\u00B1"+str("{0:.2f}".format(c.expected['EXPECTED_TX_FREQ_ERROR_HIGH'])),u"\u00B1"+str("{0:.2f}".format(c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH'])),"<"+str(c.expected['EXPECTED_RX_EVM_LIMIT'])]
status_list = [["Fail"]*len(c.expected['rep_list_name']),["Fail"]*len(c.expected['rep_list_name'])]
#status_list = [["Pass","Pass","Fail","Fail","Pass","Pass","Pass","Pass","Pass","Pass","Fail"],["Pass","Pass","Fail","Fail","Pass","Pass","Pass","Pass","Pass","Pass","Fail"]] # For Fitax board


# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)

end_results_int = []
end_results_ext = []
lo_leakage_results = []
sample_gain_results = []

            
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
        
        # Get Configuration file
        try:
            self.ConfigFileHandler = ConfigParser.RawConfigParser() 
            self.ConfigFileHandler.read(cfg_file)   # Read file mode 

            self.telnet_port1 = self.ConfigFileHandler.getint("Defaults","TelnetPort1")
            self.telnet_port2 = self.ConfigFileHandler.getint("Defaults","TelnetPort2")
            self.ts_port = self.ConfigFileHandler.get("Defaults","ts_port")
            self.terminal_server_IP = self.ConfigFileHandler.get("Defaults","terminal_server_IP")
            self.plug_id = self.ConfigFileHandler.get("Defaults","plug_id")
            plug_id = self.plug_id
        except IOError:
            print "Loading configuration file failed.."
            sys.exit()

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
        UUT.connect(evk_ip)
        return super(ParametrizedTestCase, self).setUp()

    def tearDown(self):
        TesterDevice.transmit_rf("OFF")
        UUT.reset_board( self.plug_id)
        return super(ParametrizedTestCase, self).tearDown()

class CalibrationTestsDCOCcheck(ParametrizedTestCase):
    def test_DCOC_status(self):
        # Get DCOC status 
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
        
        Logger[self.param['macIf']].info("----------- Start DCOC test ------------------------")
        
        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        UUT.set_mib( c.snmp['Freq_Set'][abs(self.param['macIf']-1)], self.param['ch_freq']-30)

        ResFileName = open(final_res_file,'r+')
        ResultsFileHandler.read(final_res_file)

        #DAC DCOC measurements
        if self.param['macIf'] == 0:
            dc_iq_list = [c.register['RX1_DC_IQ_0'],c.register['RX1_DC_IQ_1'],c.register['RX1_DC_IQ_4'],c.register['RX1_DC_IQ_6']]
        else:
            dc_iq_list = [c.register['RX2_DC_IQ_0'],c.register['RX2_DC_IQ_1'],c.register['RX2_DC_IQ_4'],c.register['RX2_DC_IQ_6']]

        for i in range(0,len(dc_iq_list)):
            rf_reg = regs.get(('rf'+str(self.param['macIf']), dc_iq_list[i]))
            reg_I = str(hex(rf_reg&hw_tools.bit_mask(8)<<8)).split('00')
            reg_Q = hex(rf_reg&hw_tools.bit_mask(8))
            
            DC_I = int(reg_I[0],16)
            DC_Q = int(str(reg_Q),16)
            dc_status = "Fail"
            if (DC_I in range(c.register['DC_RANGE_START_REG'],c.register['DC_RANGE_STOP_REG'])) or (DC_Q in range(c.register['DC_RANGE_START_REG'],c.register['DC_RANGE_STOP_REG'])):
                print "DC fail ",(str(hex(dc_iq_list[i])), str(hex(rf_reg)))            
                Logger[self.param['macIf']].info('DCOC test fail, DAC register %s, value %s'%(str(hex(dc_iq_list[i])), str(hex(rf_reg))))
                dc_status = "Fail"
                ResultsFileHandler.set("DCOC DAC registers",str(hex(dc_iq_list[i])), dc_status)
                print "reg_I %s, reg_Q %s "%(str(reg_I[0]),str(reg_Q))
                print "DC_I,DC_Q (hex): ", hex(DC_I),hex(DC_Q)
            else:
                print "DC pass  (register %s, value %s)" %(str(hex(dc_iq_list[i])), str(hex(rf_reg)))
                dc_status = "Pass"
                Logger[self.param['macIf']].info('DCOC test pass, DAC register %s, value %s'%(str(hex(dc_iq_list[i])), str(hex(rf_reg))))
                ResultsFileHandler.set("DCOC DAC registers",str(hex(dc_iq_list[i])), dc_status)

        print "Creating CLI instance"
        cli_ate = cli.V2xCli()
        print "Setting interface"
        cli_ate.set_interface("telnet")
        print "Connecting to telnet server"
        cli_ate.connect( str(evk_ip) , self.telnet_port1 )
        cli_ate.dcoc_wfp_timer( self.param['macIf'] + 1 , '0' )   #1/2  #asher add
        cli_ate.dcoc_calibrate( self.param['macIf'] + 1 )   #1/2
        time.sleep(2)
        """
        # Read the DC values for the wfp gain
        data_string = cli_ate.dcoc_read_wfp(self.param['macIf'] + 1)
        dc_values_wfp = [s.strip() for s in data_string.splitlines()][1]
        Logger[self.param['macIf']].info( 'DC values wfp:' + str(dc_values_wfp))
        """
        # Read the DC values for [ medium, low, free agc ]
        dc_values = ''

        #gain_levels =  ['9b01','1b01','1']
        #for i in gain_levels[:2]:
        #gain_levels =  { 'high' : 'd301', 'medium' : '9b01', 'low' : '1b01'}
        gain_levels =  { 'high' : '01', 'medium' : '9b01', 'low' : '1b01'}
        for key,value in gain_levels.iteritems():
            cli_ate.enter_to_registers
            cli_ate.change_phy_num( self.param['macIf'] )  #asher add
            cli_ate.write_to_register( '10d', value ) 
            cli_ate.quit_from_registers
            time.sleep(1)  #asher add
            data_string = cli_ate.dcoc_read_wfp(self.param['macIf'] + 1)
            dc_values = [s.strip() for s in data_string.splitlines()][1]
            print "DC values for " + key + " gains " + dc_values
            Logger[self.param['macIf']].info( 'DC values ' + key + ': ' + dc_values )
            ResultsFileHandler.set("DC gain levels",channel_name + "_" + key, dc_values.replace('WFP: ',''))
        # Free AGC
        cli_ate.enter_to_registers
        cli_ate.write_to_register( '10d', '1' ) 
        cli_ate.quit_from_registers
        cli_ate.disconnect()
        
        try:
            with ResFileName as f:
                ResultsFileHandler.write(f)
        except IOError:
            print "Can't read file..Please check the file"
        ResFileName.close()
        
        del rssi_evm
        del regs
        Logger[self.param['macIf']].info('----------------- Test finished --------------------------------------')
        Logger[self.param['macIf']].info('||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||')

class CalibrationTestsRX_sample_gain(ParametrizedTestCase):
    def test_rx_sample_gain_IQNXN_VSGen(self):        
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name
        '''
        if self.param['macIf'] == 0:
            channel_name = 'chA'
            channel_name_co = 'chB'
        else:
            channel_name = 'chB'
            channel_name_co = 'chA'
        '''
        # VSG select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',2) # Switch B to com 2    
    
        print ('\n================== Sample Gain START ===============================')
        Logger[self.param['macIf']].info('----------------- Start Sample Gain test  -------------------------')
        print "Channel frequency:", str(self.param['ch_freq'])
        
        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)

        tx_power_low = c.common['STRONG_PACKETS_AREA'] + c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype] # LNA off Mixer off
        tx_power_med = c.common['MID_PACKETS_AREA'] + c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]  # LNA off Mixer on
        tx_power_high = c.common['WEAK_PACKETS_AREA'] + c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype] # LNA on Mixer on
        
        full_res = []
        
        #Setting to default values
        regs.set(('phy' + str(self.param['macIf']), c.register['RX_SAMPLE_GAIN_REG_LOW_PART']), 0x0)
        regs.set(('phy' + str(self.param['macIf']), c.register['RX_SAMPLE_GAIN_REG_HIGHMID_PART']), 0x0)
        
        #Read Backoff compensation configuration
        backoff_index = hex(regs.get(('phy'+str(self.param['macIf']), c.register['BACKOFF_COMP_REG'])))
        print "backoff_index = ", backoff_index
        BackoffComp = int(backoff_index,16)*6   # Backoff compensation index*6 = attenuation compensation in dB
        print "Backoff compensation = ", BackoffComp
        

        print "Start transmitting.."
        tx_power_list = [tx_power_low,tx_power_med,tx_power_high]

        for tx_power_val in tx_power_list:
            # Start transmission
            TesterDevice.signal_generator_settings(self.param['ch_freq'],tx_power_val) 
            TesterDevice.transmit_rf("ON")
            print "Expected RSSI (dBm) = ", str(tx_power_val-float(c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]))

            # Get DUT Pin(RSSI)     
            dictionaryRes = rssi_evm.get(self.param['macIf']+1,c.common['EVM_AVERAGE_CNT'], timeout=10)
            print("RSSI and EVM statistics : %s" %  dictionaryRes)
            rssi_average = dictionaryRes.get('rssi')[1]     # Average RSSI
            evm_average = dictionaryRes.get('evm')[1]       # Average EVM
            print("Average RSSI = %sdBm, EVM = %sdB") %(rssi_average,evm_average)
            
            # Sample gain calculation
            sample_gain = float(rssi_average) - (tx_power_val - float(c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]))
            full_res.append(sample_gain)
            
        #Stop transmission
        TesterDevice.transmit_rf("OFF")

        SampleGainLow, SampleGainMid, SampleGainHigh = full_res
        low_hex = str(hex(hw_tools.dB_to_11_3(SampleGainLow)))    
        mid_hex = str(hex(hw_tools.dB_to_11_3(SampleGainMid)))
        high_hex = str(hex(hw_tools.dB_to_11_3(SampleGainHigh)))
        
        #Update results in calibration file
        self.sample_gain_hi = high_hex
        self.sample_gain_mid = mid_hex
        self.sample_gain_low = low_hex

        print '\nSampleGainLow = %s SampleGainMid = %s SampleGainHigh = %s' %(SampleGainLow, SampleGainMid, SampleGainHigh)
        
        #Logging
        Logger[self.param['macIf']].info ('Measured SampleGainLow(hex): '+low_hex)
        Logger[self.param['macIf']].info ('Measured SampleGainMid(hex): '+mid_hex)
        Logger[self.param['macIf']].info ('Measured SampleGainHigh(hex): '+high_hex)

        # Status Sample gain range checking
        if (c.expected['START_RANGE'] <= (SampleGainLow or SampleGainMid or SampleGainHigh) <= c.expected['END_RANGE']):
            Logger[self.param['macIf']].info('Status: PASS')
        else:
            print "Sample Gain value range fail!! "
            Logger[self.param['macIf']].info('Status: FAIL')
        del rssi_evm
        del regs
        
        # -------------Set and save Uboot params-----------------------
        uboot_sample_gain_high = "ch_"+str(self.param['macIf'])+"_sample_gain_high"
        uboot_sample_gain_mid = "ch_"+str(self.param['macIf'])+"_sample_gain_mid"
        uboot_sample_gain_low = "ch_"+str(self.param['macIf'])+"_sample_gain_low"
        
        # Reading results file, needs for accsess to sample gain section
        SampleGainLow = format(float(SampleGainLow),'0.2f')
        SampleGainMid = format(float(SampleGainMid),'0.2f')
        SampleGainHigh = format(float(SampleGainHigh),'0.2f')
        #res_dict["rate"] = format(float(rate),'0.2f')
        SampleGainLow = float(SampleGainLow)
        SampleGainMid = float(SampleGainMid)
        SampleGainHigh = float(SampleGainHigh)

        ResFileName = open(final_res_file,'r+')
        ResultsFileHandler.read(final_res_file)
        ResultsFileHandler.set("Sample_Gain",channel_name+"_(hex,dB)",[self.sample_gain_low,SampleGainLow,self.sample_gain_mid,SampleGainMid,self.sample_gain_hi,SampleGainHigh])

        
        try:
            with ResFileName as f:
                ResultsFileHandler.write(f)
        except IOError:
            print "Can't read file..Please check the file"
        ResFileName.close()

        print "\nRebooting board and save parameters"
        """
        try:
            telnetlib.Telnet(self.terminal_server_IP, self.ts_port, timeout=5).close()
        except:
            pass
        """
        u = uboot(self.terminal_server_IP, self.ts_port, self.plug_id)
        u.enter_uboot()
        d = u.get_dict()
        
        try :
            u.set_dict({uboot_sample_gain_high : self.sample_gain_hi, uboot_sample_gain_mid : self.sample_gain_mid, uboot_sample_gain_low : self.sample_gain_low})
        except:
            print "Tx IQ imbalance as default"
        del u
        
        Logger[self.param['macIf']].info("----------------- Test finished --------------------------------------")
        Logger[self.param['macIf']].info("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

class CalibrationTestsRX_iq_imbalance(ParametrizedTestCase):
    def test_rx_iq_imbalance(self):
        print "\n..............Start RX IQ imbalance calibration test --------------"
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)

        # MXG/VSG select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',2) # Switch B to com 2    
        
        print "Channel frequency: ", str(self.param['ch_freq'])
        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)

        # Calcilate Initial power (Pin) for the test, Pin should be -60dBm during the calibration
        init_tx_power = c.common['RX_IQ_IMBALANCE_INIT_PIN_POWER'] + c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]

        # Configure transmitter settings and start tranmission
        TesterDevice.signal_generator_settings(self.param['ch_freq'],init_tx_power) 
        TesterDevice.transmit_rf("ON")

        Logger[self.param['macIf']].info('----------------- Start RX IQ imbalance test -------------------------')
        # Excecute RX IQ imbalance script, is based on mathematical calculations and measurements values of dedicated registers
        # Before the calculations, we need configure the phase and amplitude registers to default values
        # EVM measurement serves us as an indicator for calibration correction, for this purpose we need to measure initial EVM 
        # The function Run() returns 3 values with calibration values (valA,valB,valC)
        # Finally we measure final EVM after the calibration
        iq = IQImbalance() # create object
        try:
            iq.Open(regs, self.param['macIf'])
            if (self.param['macIf']==1) and btype == "_ATK22027":
                regs.set(('phy' + str(self.param['macIf']), c.register['RX_IQ_IMBALANCE_AMPL_REG']), 0x300)       # set to default value
            else:
                regs.set(('phy' + str(self.param['macIf']), c.register['RX_IQ_IMBALANCE_AMPL_REG']), c.register['RX_IQ_IMBALANCE_AMPL_REG_VALUE'])       # set to default value
            regs.set(('phy' + str(self.param['macIf']), c.register['RX_IQ_IMBALANCE_PHASE_REG']), c.register['RX_IQ_IMBALANCE_PHASE_REG_VALUE']) # set to default value
            valA,valB_valC = hex(regs.get(("phy"+str(self.param['macIf']), c.register['RX_IQ_IMBALANCE_AMPL_REG']))),hex(regs.get(("phy"+str(self.param['macIf']), c.register['RX_IQ_IMBALANCE_PHASE_REG'])))
            print "Initial RX IQ imbalance registers settings (0x14c and 0x14d) = ", valA,valB_valC
            print "macIf = ", self.param['macIf']   
            Logger[self.param['macIf']].info('MAC Interface: '+str(self.param['macIf']))
            try:
                dictionaryRes = rssi_evm.get(self.param['macIf']+1,c.common['EVM_AVERAGE_CNT'], timeout=10)
            except RuntimeError:
                raise
                sys.exit()
            rssi_average = dictionaryRes.get('rssi')[1]     # Average RSSI
            evm_average = dictionaryRes.get('evm')[1]       # Average EVM
            print("Average RSSI = %sdBm, EVM = %sdB\n") %(rssi_average,evm_average)
            Logger[self.param['macIf']].info('Initial RX EVM: '+evm_average)
            
            valA,valB,valC = iq.Run(10,2)

            dictionaryRes = rssi_evm.get(self.param['macIf']+1,c.common['EVM_AVERAGE_CNT'])
            rssi_average = dictionaryRes.get('rssi')[1]     # Average RSSI
            evm_average = dictionaryRes.get('evm')[1]       # Average EVM

            if (valA and valB and valC) and float(evm_average) < c.expected['EXPECTED_RX_EVM_LIMIT']:
                Logger[self.param['macIf']].info ('Status: PASS')
            else:
                Logger[self.param['macIf']].info ('Status: FAIL')
            print("Final EVM: %s\n" % evm_average)
        except:
            print "Test failed..\n"
            Logger[self.param['macIf']].info ('Measurements failed, Status: FAIL')

        Logger[self.param['macIf']].info('Final RX EVM: '+evm_average)


        #Stop transmission
        TesterDevice.transmit_rf("OFF")
              
        #Update results in calibration file
        self.rx_balance_phase = str(hex(valB<<16 | valC))
        self.rx_balance_gain = str(hex(valA))
        del rssi_evm
        del regs
        del iq
        # -------------Set and save Uboot params-----------------------
        uboot_rx_balance_phase = "rx_" + str(self.param['macIf']) + "_balance_phase"
        uboot_rx_balance_gain = "rx_" + str(self.param['macIf']) + "_balance_gain"
        
        print "Rebooting board and save parameters"
        
        u = uboot(self.terminal_server_IP, self.ts_port, self.plug_id)
        u.enter_uboot()
        d = u.get_dict()
        
        try :
            u.set_dict({uboot_rx_balance_phase : self.rx_balance_phase, uboot_rx_balance_gain : self.rx_balance_gain})
        except:
            print "Rx IQ imbalance settings register failed"
        del u
        
        # Write results to Calibration File                    
        Logger[self.param['macIf']].info('Phy Register 0x14d: '+str(self.rx_balance_phase))
        Logger[self.param['macIf']].info('Phy Register 0x14c: '+str(self.rx_balance_gain))
        
        Logger[self.param['macIf']].info('----------------- Test finished --------------------------------------')
        Logger[self.param['macIf']].info('||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||')

class CalibrationTestsTSSI(ParametrizedTestCase):
    def test_tssi_calibration(self):
        print "\n----------------------------------- Start TSSI calibration test --------------------------------"
        Logger[self.param['macIf']].info("----------------- Start TSSI calibration test ------------------------")
        
        Logger[self.param['macIf']].info('TSSI calibration test start : ')

        # VSA select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',1) # Switch B to com 1 
        
        # VSA settings
        print "Channel frequency:", str(self.param['ch_freq'])
        Freq = self.param['ch_freq']*1e6
        Port = 2 # left port VSA mode
        Atten = c.common['TX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]

        TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
        TesterDevice.prepare_vsa_measurements()
            
        delta20 = 2
        delta10 = 2
        tssi_timeout = 0
        ch_power10 = 10
        ch_power20 = 20    

        iter_num = 4    # Number of temps for TSSI calibrations
        ch_power_list = [ch_power10,ch_power20] 

        while ((abs(delta20) > c.expected['EXPECTED_TSSI_DIFF']) or (abs(delta10) > c.expected['EXPECTED_TSSI_DIFF'])) and (tssi_timeout<iter_num):
            UUT.connect(evk_ip)
            rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
            
            UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
            # Set additional channel to off
            UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)
            print 'Start transmiting from channel ch%s' %str(self.param['macIf'])
            #UUT.set_to_rx_mode(self.param['macIf'],c.register['RF_SYNTHESIZER_REG'][self.param['macIf']],regs)  # Set additional channel to rx mode 
            time.sleep(0.1)
            UUT.set_mib(c.snmp['TxEnabled'][self.param['macIf']], 1)   # Transmit ON

            #for TX_EVM
            TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
            time.sleep(0.3)
            TesterDevice.prepare_vsa_measurements()
        
            SUMresTxPower10 = 0
            SUMresTxPower20 = 0
            SUMresTxEVM20 = 0
            SUMresTxEVM10 = 0
                                    
            for iter_power in ch_power_list:
                UUT.set_mib(c.snmp['TxPower'][self.param['macIf']], iter_power)    #Set tx power
                time.sleep(6)
                #tssi_timeout+=1
            
                SUM = 0
                SUMresTxEVM = 0
                SAMPLES = 20
                
                for i in range (0,SAMPLES):          
                    TesterDevice.prepare_vsa_measurements()
                    SUM += TesterDevice.get_tx_vsa_measure('rmsPowerNoGap')
                    SUMresTxEVM += TesterDevice.get_tx_vsa_measure('evmAll')
          
                if iter_power == ch_power_list[0]:
                    SUMresTxPower10 = SUM
                    SUMresTxEVM10 = SUMresTxEVM
                elif iter_power == ch_power_list[1]:
                    SUMresTxPower20 = SUM
                    SUMresTxEVM20 = SUMresTxEVM
                                
                # Calculate average value
                resTxPower10 = SUMresTxPower10/SAMPLES    
                resTxPower20 = SUMresTxPower20/SAMPLES
                resTxEVM = SUMresTxEVM20/SAMPLES
                                   
            tssi_timeout+=1

            delta20 = c.expected['EXPECTED_POWER_20'] - resTxPower20
            delta10 = c.expected['EXPECTED_POWER_10'] - resTxPower10

            print "TX power10 = %f \n" %resTxPower10
            print "TX power20 = %f \n" %resTxPower20
            print "TX EVM@20dBm = %f \n" %resTxEVM        
            Logger[self.param['macIf']].info('Tx power10 : '+ str(resTxPower10))
            Logger[self.param['macIf']].info('Tx power20 : '+ str(resTxPower20))
            Logger[self.param['macIf']].info('TX EVM@20dBm : '+str(resTxEVM))
            
            if ((abs(delta20) > 0.45) or (abs(delta10) > 0.45)):            
                print "Serial port:", self.ts_port
                Pslope,Pintercept = tssi.adjust_tssi_calibration(self.terminal_server_IP, self.ts_port, self.plug_id, self.param['macIf'], resTxPower10, resTxPower20)
            else:
                Pintercept = UUT.get_mib( c.snmp['TssiPintercept'][self.param['macIf']])
                Pslope = UUT.get_mib( c.snmp['TssiPslope'][self.param['macIf']])
                break                
            print "New Pslope,Pintercept = ", Pslope,Pintercept
            del rssi_evm
            del regs
            UUT.reset_board( self.plug_id)
            
        # Final Pslope and Pintercept
        Logger[self.param['macIf']].info("Pslope = " + str(Pslope))
        Logger[self.param['macIf']].info("Pintercept = " + str(Pintercept))
        try:
            del rssi_evm
            del regs
        except:
            pass
        UUT.set_mib(c.snmp['TxEnabled'][self.param['macIf']], 2)   # Transmit OFF
        print "----------------------------------- Stop TSSI calibration test --------------------------------"    
        Logger[self.param['macIf']].info("----------------- Test finished --------------------------------------")
        Logger[self.param['macIf']].info("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")

class CalibrationTestsTxPowerAdjustment(ParametrizedTestCase):
    def test_tx_power_calibration(self):
        print "\n----------------------------------- Start TSSI calibration test --------------------------------"
        Logger[self.param['macIf']].info("----------------- Start TSSI calibration test ------------------------")
        
        Logger[self.param['macIf']].info('TSSI calibration test start : ')

        # VSA select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',1) # Switch B to com 1 
        
        # VSA settings
        print "Channel frequency:", str(self.param['ch_freq'])
        Freq = self.param['ch_freq']*1e6
        Port = 2 # left port VSA mode
        Atten = c.common['TX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]

        TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
        TesterDevice.prepare_vsa_measurements()
            
        delta20 = 2
        delta10 = 2
        tssi_timeout = 0
        ch_power10 = 10
        ch_power20 = 20    
        delta = 0
        
        #Define TX power range
        ch_power =  c.common['TX_CAL_RANGE']    # tx power 10,11,12,.....,24
        tx_power_list, detector_meas_list =[],[]
        
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
            
        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        UUT.set_mib( c.snmp['FrameLen'][self.param['macIf']], self.param['pad'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)
        print 'Start transmiting from channel ch%s' %str(self.param['macIf'])
        time.sleep(0.1)
        UUT.set_mib( c.snmp['TssiInterval'][self.param['macIf']], 0)    # Turn OFF TSSI before the calibration
        UUT.set_mib(c.snmp['TxEnabled'][self.param['macIf']], 1)   # Transmit ON

        #for TX_EVM
        TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
        #time.sleep(0.3)
        #TesterDevice.prepare_vsa_measurements()
        
        #Settings initial values to zeros
        SUMresTxPower10 = 0
        SUMresTxPower20 = 0
        SUMresTxEVM20 = 0
        SUMresTxEVM10 = 0
        
        resTxEVM_all = []
        fifo_meas_status = True
                                    
        for iter_power in ch_power:
            UUT.set_mib(c.snmp['TxPower'][self.param['macIf']], iter_power)    #Set tx power
            time.sleep(0.5)
            TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
            time.sleep(0.5)
            TesterDevice.vsa_set_agc() #Asher add
            TesterDevice.prepare_vsa_measurements()

            delta_sum = 0
            iter_indx = 3 #for delta calc
            for i in range (0,iter_indx):
                TesterDevice.prepare_vsa_measurements()
                delta_sum += TesterDevice.get_tx_vsa_measure('rmsPowerNoGap')
                #print "Iteration = %s, delta_sum = %s" % (str(i),str(delta_sum))
            delta = iter_power - delta_sum/iter_indx
            #print "delta = ", delta
            #print "Expected = {}, Measured = {} ,delta = {}".format(iter_power,delta_sum/iter_indx, delta)
            #UUT.set_mib(c.snmp['TxPower'][self.param['macIf']], iter_power+delta)    #Set tx power
            
            if abs(delta) < 6 :
                print "Expected = {}, Measured = {} ,delta = {}".format(iter_power,delta_sum/iter_indx, delta)
                rounded_power = round(iter_power+delta)
                print "rounded_power(dBm) = ",rounded_power
                UUT.set_mib(c.snmp['TxPower'][self.param['macIf']], rounded_power)    #Set tx power
            else:
                print "Expected = {}, Measured = {} ,delta_out_of_range = {}".format(iter_power,delta_sum/iter_indx, delta)
                UUT.set_mib(c.snmp['TxPower'][self.param['macIf']], round(iter_power+delta/2))    #Set tx power
            
            time.sleep(1)
            # to read 10 first bits (0 to 9) also you need to verify bit 31 is 0 (when 1 the FIFO value is not valid)
            #fifo_meas_status = bool(regs.get(("mac"+str(self.param['macIf']),c.register['TSSI_FIFO'][self.param['macIf']]))&(0x80000000))
            fifo_meas_status = bool(regs.get(("mac0",c.register['TSSI_FIFO'][self.param['macIf']]))&(0x80000000))
            #print "TSSI_FIFO valid status ",fifo_meas_status
            
            # Start measurement loop
            if (fifo_meas_status == False):
                SUM = 0
                SUMresTxEVM = 0
                SAMPLES = 10 #after addition delta
                resTxEVM = 0
                SUMdetector_meas = 0
                SUMtssi_fifo_val = 0
                TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
                #time.sleep(3)
                TesterDevice.vsa_set_agc() #Asher add
                TesterDevice.prepare_vsa_measurements()
                                
                for i in range (0,SAMPLES):          
                    TesterDevice.prepare_vsa_measurements()
                    #TesterDevice.vsa_set_agc() #Asher add
                    SUM += TesterDevice.get_tx_vsa_measure('rmsPowerNoGap')
                    #print "Samples = %s, SUM = %s" % (str(i),str(SUM)) #Asher add
                    SUMresTxEVM += TesterDevice.get_tx_vsa_measure('evmAll')
                    ######SUMdetector_meas += int(regs.get(("mac"+str(self.param['macIf']),c.register['TSSI_FIFO'][self.param['macIf']]))&hw_tools.bit_mask(10))
                    tssi_fifo_val_hex = regs.get(("mac0",c.register['TSSI_FIFO'][self.param['macIf']]))
                    SUMdetector_meas += int(tssi_fifo_val_hex) & hw_tools.bit_mask(10)
                    print "TSSI_FIFO register value = {}".format(tssi_fifo_val_hex)
                    SUMtssi_fifo_val += int(tssi_fifo_val_hex)
                # Collect the measurements
                tx_power_meas = (SUM/SAMPLES)                
                tx_power_list.append(tx_power_meas)
                print "TX_Power_meas_value = ",tx_power_meas
                #detector_meas_list_not_rounded.append(float(SUMdetector_meas)/SAMPLES)
                
                # Append rounded values to final measurement detector list 
                #for i in detector_meas_list_not_rounded: detector_meas_list.append(round(i))
                #print "Average TSSI_FIFO rounded register value = ",detector_meas_list
                avg_tssi_fifo_val = round((float(SUMtssi_fifo_val)/SAMPLES))
                print "Average TSSI_FIFO rounded register value = {}".format(avg_tssi_fifo_val)
                avg_detector_meas = round((float(SUMdetector_meas)/SAMPLES))
                detector_meas_list.append(avg_detector_meas)
                print "Average detector_meas rounded value = ",avg_detector_meas
                
                resTxEVM_all.append(SUMresTxEVM/SAMPLES)
                #print tx_power_list
                #print detector_meas_list
                # Calculate average value for 10dBm and 20dBm
                #resTxPower10 = SUMresTxPower10/SAMPLES    
                #resTxPower20 = SUMresTxPower20/SAMPLES
                #resTxEVM = SUMresTxEVM20/SAMPLES #Asher add
                fifo_meas_status = True                       
            else:
                print "TSSI FIFO not valid!"


        # reverse list 
        tx_power_list = tx_power_list[::-1]     
        detector_meas_list = detector_meas_list[::-1]
        resTxEVM_all = resTxEVM_all[::-1] #Asher add
        # TX power adjustment function, returns the final vector for an antenna power LUT
        calib_pant_lut_vector_list = tssi.adjust_tx_power(self.terminal_server_IP, self.ts_port, self.plug_id, self.param['macIf'], detector_meas_list, tx_power_list)    
        
        Logger[self.param['macIf']].info("Final vector_list: {:s}".format(str(calib_pant_lut_vector_list).replace(" ","")))
        Logger[self.param['macIf']].info("tx_power_list): {:s}".format(str(tx_power_list)))
        Logger[self.param['macIf']].info("detector_meas_list: {:s}".format(str(detector_meas_list)))
        
        # Set calculated final vector on the board
        #UUT.set_mib(c.snmp['wlanPantLut'][self.param['macIf']], calib_pant_lut_vector_list)
        
        print "\n\ntx_power_list ",tx_power_list
        print "\n\ndetector_meas_list ",detector_meas_list
        print "\n\nresTxEVM_all ",resTxEVM_all  #Asher add
        print "\n\ncalib_pant_lut_vector_list ",calib_pant_lut_vector_list
        tssi_meas_fname = logs_path + "tssi_measurements_results_{}.csv".format(str(self.param['macIf']))
        if not os.path.exists(tssi_meas_fname):
            with open(tssi_meas_fname, "w") as out_file:
                hw_tools.print_and_log(out_file, "tx_power_list, " +str(tx_power_list))
                hw_tools.print_and_log(out_file, "detector_meas_list, "+str(detector_meas_list))
                hw_tools.print_and_log(out_file, "final_vector_list, {:s}".format(str(calib_pant_lut_vector_list).replace(" ","")))
            out_file.close()        

        del rssi_evm
        del regs
        
        #print "Frequency = ",UUT.get_mib(c.snmp['Freq_Set'][self.param['macIf']])
        #UUT.set_mib(c.snmp['TxEnabled'][self.param['macIf']], 2)   # Transmit OFF

        print "----------------------------------- Stop TSSI calibration test --------------------------------"    
        Logger[self.param['macIf']].info("----------------- Test finished --------------------------------------")
        Logger[self.param['macIf']].info("||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||")


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
        
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
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
        print "\nConfiguration parameters: "
        for key,value in self.param.iteritems():
            if key == 'rate':
                value = value/2
            print "%s: %s " %(str(key),str(value))
            Logger[self.param['macIf']].info (str(key) +': '+ str(value))

        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name
        '''
        if self.param['macIf'] == 0:
            channel_name = 'chA'
            channel_name_co = 'chB'
        else:
            channel_name = 'chB'
            channel_name_co = 'chA'
        '''
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
        
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

        # Check if result file exists
        res_fname = logs_path + "sensitivity_test_res_" + str(Number) +"_"+str(ch)+"_"+str(rate)+ "_" +str(self.param['macIf']) +"_" +str(self.param['temperature']) +".txt"
        print "Sensitivity result file name = ",res_fname

        # Check if result file exists
        if (os.path.exists(res_fname)):            
            print "Note: File exists....the results will be added to the existing file"
            res_file = file(res_fname,"w+")
        else:
            res_file = open(res_fname,"w")

        
        # Logging
        Logger[self.param['macIf']].info('Created results file = '+res_fname)
        
        # Reading results file, needs for accsess to sensitivity section
        ResultsFileHandler.read(final_res_file)
        
        firstString = True
            
        # AGC cross-over points  (-67dBm,-49dBm)
        pow_range = c.common['SENSITIVITY_TEST_RANGE']        
        #pow_range = range(-88, -70, 2)
            
        if self.param['dsrc_channel_models_enable'] == 0:
            channel_loop = 1
        else:
            channel_loop = len(c.common['dsrc_channel_models_list'])

        for i in range(channel_loop):
            try:
                if self.param[tester_type] == 1:
                    TesterDevice.signal_generator_load_file(utilities_dir+ "autotalks_1000bytes_10mhz_"+str(rate)+".mod")
                    print "File in use: " +utilities_dir+ "autotalks_1000bytes_10mhz_"+str(rate)+".mod"
                else:
                    if self.param['dsrc_channel_models_enable'] == 0:
                        if str(rate) == '4.5':
                            TesterDevice.signal_generator_load_file("4_5MBPS") 
                        else:
                            TesterDevice.signal_generator_load_file(str(rate)+"MBPS")
                    else:
                        print "File not found.."
                        sys.exit()
                    #elif self.param['dsrc_channel_models_enable'] == 1:                        
                    #    TesterDevice.signal_generator_load_file(utilities_dir+ c.common['dsrc_channel_models_list'][i]+str(rate))
                    
            except:
                print "Loading file failed"
            TesterDevice.transmit_rf("OFF",1)

            # Execute test
            point = True
            sens_point = ''    
            for pow in pow_range:                
                # Set pow and Trigger

                if self.param[tester_type] == 1:
                    # When using IQ2010 tester we must transmit 1 packet for clean RF output 
                    TesterDevice.transmit_rf("ON",1)
                    TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,1)     # Transmit 1 packet with Single trigger mode 
                        
                # Get initial RX counter value 
                init_value = UUT.get_mib(c.snmp['RxMacCounter'][self.param['macIf']])
                TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,self.param['num_pckt2send'])     #Transmit n packets with Single trigger mode 
                TesterDevice.transmit_rf("ON",1)
                """
                # Get DUT EVM
                try:
                    dictionaryRes = rssi_evm.get(self.param['macIf']+1,3, timeout=10)
                    evm_average = dictionaryRes.get('evm')[1]       # Average EVM
                except:
                    try:
                        evm_average = hw_tools.evm_calc(str(hex(regs.get(('phy'+str(self.param['macIf'])), c.register['EVM_OUT']))),str(hex(regs.get(('phy'+str(self.param['macIf'])), c.register['CONST_POWER_BIN_COUNT']))))
                    except:
                        evm_average = "0"
                        pass
                print("Average EVM : %s" %  evm_average)
                """
                # Wait 5 seconds to complete transmission (for MXG only)
                #time.sleep(5)   # to do calculate exact time for transmission, Packet transmission time = Packet size / Bit rate
                
                cur_powPin = pow - float(c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype])
                #print "Pin signal power: "+str(cur_powPin)+" dBm"
                
                # Logging
                Logger[self.param['macIf']].info('Pin signal power: '+str(cur_powPin)+' dBm')

                # Get RX counter value after transmission of n packets      
                next_rx_cnt = UUT.get_mib(c.snmp['RxMacCounter'][self.param['macIf']])
            
                # Calculate recieved packets
                recieved_cnt = next_rx_cnt - init_value
                #print "init_value = ", init_value
                #print "next_rx_cnt = ", next_rx_cnt
                #print "recieved_cnt = ", recieved_cnt

                # PER calculation
                per = float(num_pckt2send - recieved_cnt)/num_pckt2send    
                print "Pin signal power: "+str(cur_powPin)+" dBm, " + "PER: "+str(per*100) + "%"

                Logger[self.param['macIf']].info('PER : '+str(per*100)+' %')
                res_dict = {}
                res_dict["channel"] = ch
                res_dict["rate"] = format(float(rate),'0.2f')
                res_dict["interval_usec"] = 5000
                res_dict["packets_to_send"] = num_pckt2send
                res_dict["packet_size"] = pad 
                res_dict["rx_ip"] = evk_ip
                res_dict["PER_ch"] = per*100
                #res_dict["EVM"] = format(float(evm_average),'0.2f')
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
                    sens_point = str(cur_powPin)
                    ResultsFileHandler.set("Sensitivity test","Sensitivity_"+channel_name,str(cur_powPin))
                    Logger[self.param['macIf']].info ('________________________________Sensitivity point =' + str(cur_powPin))
                    print "_______________________________>>>Sensitivity point =" + str(cur_powPin)
                    point = False
                else:
                    pass               

            res_file.close()
        

            #Stop transmission
            TesterDevice.transmit_rf("OFF")
            UUT.set_to_txrx_mode(self.param['macIf'],c.register['RF_SYNTHESIZER_REG'][self.param['macIf']],regs)  # Set additional channel to txrx mode
            del rssi_evm
            del regs 
            ResFileName = open(final_res_file,'r+')
            try:
                with ResFileName as f:
                    ResultsFileHandler.write(f)
            except IOError:
                print "Can't read file..Please check the file"
            ResFileName.close()

        # Replace waveform to default waveform 6mbps
        try:
            if self.param[tester_type] == 1:
                TesterDevice.signal_generator_load_file(utilities_dir+ "autotalks_1000bytes_10mhz_6.mod")
            else:
                TesterDevice.signal_generator_load_file("6MBPS") 
        except:
            print "Loading file failed"
        
        
        TesterDevice.signal_generator_settings(self.param['ch_freq'],pow,0) # continious mode
        Logger[self.param['macIf']].info('----------------- Test finished --------------------------------------')
        Logger[self.param['macIf']].info('||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||')

class TestsReport_Measurements_and_Creation(ParametrizedTestCase):   
    def test_report_meas(self):
        
        print "\n Configuration parameters: "
        for key,value in self.param.iteritems():
            if key == 'rate':
                value = value/2
            print "%s: %d " %(key,value)

        self.res_tx_evm , self.res_tx_Hievm, self.res_power, self.res_Hipower, self.res_LO_leakage, self.res_tx_amp, self.res_tx_phase, self.res_freq_err, self.res_symb_clk_err, self.res_rx_evm , self.res_sens_point = [],[],[],[],[],[],[],[],[],[],[]
        print "\n..............Start verifying test .............."    
        rssi_evm, regs = uut_py_sdk_connect(evk_ip,self.telnet_port1,self.telnet_port2)
        
        print "Channel frequency:", str(self.param['ch_freq'])

        UUT.set_mib( c.snmp['Freq_Set'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        UUT.set_mib( c.snmp['RfEnabled'][abs(self.param['macIf']-1)], 2)
        
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name
        '''
        if self.param['macIf'] == 0:
            channel_name = 'chA'
            channel_name_co = 'chB'
        else:
            channel_name = 'chB'
            channel_name_co = 'chA'
        '''


        ResFileName = open(final_res_file,'r+')    
        ResultsFileHandler.read(final_res_file)
        
        # -----------------  TX PATH --------------------------------------
        # VSA select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',1) # Switch B to com 1 
        Freq = (self.param['ch_freq'])*1e6
        Port = 2 # left port
        Atten = c.common['TX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]
        
        #UUT.set_mib( c.snmp['TssiInterval'][self.param['macIf']], 0)    # Turn OFF TSSI for a Fitax boards

        print 'Start transmiting from channel %s' %str(self.param['macIf'])
        UUT.set_mib( c.snmp['DataRate'][self.param['macIf']], self.param['rate'])
        UUT.set_mib( c.snmp['TxPower'][self.param['macIf']], self.param['tx_power'])
        UUT.set_mib( c.snmp['FrameLen'][self.param['macIf']], self.param['pad'])
        UUT.set_mib( c.snmp['TxPeriod'][self.param['macIf']], self.param['interval_usec'])

        UUT.set_mib( c.snmp['TxEnabled'][self.param['macIf']], 1)   # Transmit ON

        TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
        #TesterDevice.vsa_set_agc()
        #time.sleep(1)
        #TesterDevice.prepare_vsa_measurements()
        
        print "\nStart TX path.."
        print "Perform measurements.."
        
        ch_power_list = [10,20,23]    #dBm
                                                         
        # VSA measurements loop
        rep = 20
        for pow in ch_power_list:
            UUT.set_mib(c.snmp['TxPower'][self.param['macIf']], pow)    #Set tx power
            time.sleep(0.2)
            TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
            time.sleep(0.2)
            TesterDevice.vsa_set_agc()
            TesterDevice.prepare_vsa_measurements()

            SUMresTxEVM = 0
            #SUMresLOleakage = 0
            SUMresTxAmplImbl = 0
            SUMresTxPhaseImbl = 0
            SUMresTxPower = 0
            SUMresTxFreqErr = 0
            SUMresTxSymbClk = 0

            for i in range (0,rep):          
                TesterDevice.prepare_vsa_measurements()
                time.sleep(0.2)
                try:
                    SUMresTxEVM += TesterDevice.get_tx_vsa_measure('evmAll')
                    #SUMresLOleakage += TesterDevice.get_tx_vsa_measure('dcLeakageDbc')
                    SUMresTxAmplImbl += TesterDevice.get_tx_vsa_measure('ampErrDb')
                    SUMresTxPhaseImbl += TesterDevice.get_tx_vsa_measure('phaseErr')
                    SUMresTxPower += TesterDevice.get_tx_vsa_measure('rmsPowerNoGap')
                    SUMresTxFreqErr += TesterDevice.get_tx_vsa_measure('freqErr')
                    SUMresTxSymbClk += TesterDevice.get_tx_vsa_measure('clockErr')
                except:
                    print "VSA measurement iteration %s failed" %str(i)
                    continue 
                            
            self.res_tx_evm.append(float("{0:.2f}".format(SUMresTxEVM/rep)))
            #self.res_LO_leakage.append(float("{0:.2f}".format(SUMresLOleakage/rep)))
            self.res_tx_amp.append(float("{0:.2f}".format(SUMresTxAmplImbl/rep)))
            self.res_tx_phase.append(float("{0:.2f}".format(SUMresTxPhaseImbl/rep)))
            self.res_power.append(float("{0:.2f}".format(SUMresTxPower/rep)))
            self.res_freq_err.append(float("{0:.2f}".format(SUMresTxFreqErr/rep/1e3)))  #kHz
            self.res_symb_clk_err.append(float("{0:.2f}".format(SUMresTxSymbClk/rep)))
            """
            # Save screen shot - Spectrum mask
            if pow == 20:
                try:
                    '''
                    #handle = win32gui.FindWindow(None,"LitePoint IQsignal 1.2.9")
                    #print win32gui.GetWindowText(win32gui.GetForegroundWindow())
                    handle = win32gui.FindWindow(None,"LitePoint IQsignal 1.2.7")
                    win32gui.IsWindowVisible(handle)
                    time.sleep(2)
                    if (handle):
                        win32gui.SetForegroundWindow(handle)
                        win32gui.ShowWindow(handle,win32con.SW_MAXIMIZE)
                        hwnd = win32gui.GetForegroundWindow()
                        win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    #TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL'], Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
                    time.sleep(1)
                    #print win32gui.GetWindowText (win32gui.GetForegroundWindow())
                    #hwnd = win32gui.GetForegroundWindow()
                    #win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    #time.sleep(0.5)
                    '''
                    TesterDevice.vsa_settings(Freq, c.common['VSA_MAX_SIGNAL_LEVEL']+1, Port, Atten, c.common['VSA_TRIGGER_LEVEL'], c.common['VSA_CAPTURE_WINDOW'] )
                    TesterDevice.vsa_set_agc()
                    time.sleep(3)
                    title_name = u'LitePoint IQsignal 1.2.7'
                    hw_tools.make_window_active(title_name)
                    time.sleep(0.5)
                    
                    im = ImageGrab.grab()
                    im.save(logs_path+"\Spectrum_mask_"+str(self.param['macIf'])+".jpg")
                except:
                    print "Can't save the spectrum mask.."
                    pass
            """
        #LO leakage measurements
        lo_leak_power_list = [23,20,15,12,10,8,5]    #dBm
        for p in lo_leak_power_list:
            UUT.set_mib(c.snmp['TxPower'][self.param['macIf']], p)    #Set tx power
            time.sleep(0.2)
            SUMresLOleakage = 0
            iter = 3
            for x in range (0,iter):          
                TesterDevice.prepare_vsa_measurements()
                time.sleep(0.3)
                try:
                    SUMresLOleakage += TesterDevice.get_vsa_measure('dcLeakageDbc')
                except:
                    print "VSA measurement iteration %s failed" %str(x)
                    continue
            self.res_LO_leakage.append(float("{0:.2f}".format(SUMresLOleakage/iter)))

        print "Meausrements points(dBm):" ,ch_power_list
        print "TX EVM :                 " ,self.res_tx_evm
        print "TX power :               " ,self.res_power
        print "TX LO leakage :          " ,self.res_LO_leakage
        print "TX IQ ampl imbalance :   " ,self.res_tx_amp
        print "TX IQ phase imbalance :  " ,self.res_tx_phase
        print "TX Frequency error    :  " ,self.res_freq_err
        print "TX Symbol clock error :  " ,self.res_symb_clk_err
        
        #results_list = [ self.res_tx_evm[0], self.res_tx_evm[1], self.res_power[0], self.res_power[1], self.res_LO_leakage[1], self.res_tx_amp[1], self.res_tx_phase[1],self.res_freq_err[1],self.res_symb_clk_err[1]]
        results_list = [ self.res_tx_evm[2], self.res_tx_evm[1], self.res_power[2], self.res_power[1], self.res_LO_leakage[1], self.res_tx_amp[1], self.res_tx_phase[1],self.res_freq_err[1],self.res_symb_clk_err[1]]
        status = "Fail"

        # Compare results with expected results and get status
        if (abs(c.expected['EXPECTED_HI_TX_EVM']) <= abs(float(results_list[0])) ):
            status_list[self.param['macIf']][0] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (abs(c.expected['EXPECTED_TX_EVM']) <= abs(float(results_list[1]))):
            status_list[self.param['macIf']][1] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (c.expected['EXPECTED_TX_HI_POWER_LOW'] <= float(results_list[2]) <= c.expected['EXPECTED_TX_HI_POWER_HIGH']):
            status_list[self.param['macIf']][2] = 'Pass'
        else:
            status_list[self.param['macIf']][2] = 'Fail'
        if (c.expected['EXPECTED_TX_POWER_LOW'] <= float(results_list[3]) <= c.expected['EXPECTED_TX_POWER_HIGH']):
            status_list[self.param['macIf']][3] = 'Pass'
        else:
            status_list[self.param['macIf']][3] = 'Fail'    
        if (c.expected['EXPECTED_LO_LEAKAGE']>= results_list[4]):
            status_list[self.param['macIf']][4] = 'Pass'
        else:
            status_list[self.param['macIf']][4] = 'Fail'
        if (c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW']<=float(results_list[5]) <=c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH']):
            status_list[self.param['macIf']][5] = 'Pass'
        else:
            status_list[self.param['macIf']][5] = 'Fail'           
        if (c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW']<=float(results_list[6]) <=c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH']):
            status_list[self.param['macIf']][6] = 'Pass'
        else:
            status_list[self.param['macIf']][6] = 'Fail' 
        if (c.expected['EXPECTED_TX_FREQ_ERROR_LOW']<=float(results_list[7]) <=c.expected['EXPECTED_TX_FREQ_ERROR_HIGH']):
            status_list[self.param['macIf']][7] = 'Pass'
        else:
            status_list[self.param['macIf']][7] = 'Fail' 
        if (c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW']<=float(results_list[8]) <=c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH']):
            status_list[self.param['macIf']][8] = 'Pass'
        else:
            status_list[self.param['macIf']][8] = 'Fail' 
        
        #print "\n\n status_list : ",status_list        

        index = 0
        for z in c.expected['rep_list_name'][:(len(c.expected['rep_list_name']))-1]:
            if len(active_ch)>1 and (self.param['macIf'] >0):
                ResultsFileHandler.set('Final results',channel_name+" "+z,results_list[index])
            else:
                ResultsFileHandler.set('Final results',channel_name+" "+z,results_list[index])
                #ResultsFileHandler.set('Final results',channel_name_co+" "+z,"N/A")    # For Fitax board
            index +=1

        # Set LO leakage measurements to file
        ResultsFileHandler.set('LO leakage results',"LO_leak_"+channel_name, self.res_LO_leakage)
        
        '''
        try:
            print "Writing to results file.."
            with ResFileName as f:
                ResultsFileHandler.write(f)
        except IOError:
            print "Can't read file..Please check the file"
        ResFileName.close()
        '''
        UUT.set_mib(c.snmp['TxEnabled'][self.param['macIf']], 2)   # Transmit OFF
        
        # ---------------------------- RX PATH -----------------------------------------

        print "\nStart RX path.."
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',2) # Switch B to com 2 
        ###ResFileName = open(final_res_file,'r')
        ###ResultsFileHandler.read(final_res_file)
        
        # Calculate initial Pin for RX EVM test, should be -60dBm
        tx_power_val = c.common['RX_IQ_IMBALANCE_INIT_PIN_POWER'] + c.common['RX_PATH_SETUP_ATTENUATION'+"_"+str(self.param['macIf'])+btype]
        
        #Start transmission and measurements
        TesterDevice.signal_generator_settings(self.param['ch_freq'],tx_power_val)     
        TesterDevice.transmit_rf("ON")

        #Get RX EVM
        dictionaryRes = rssi_evm.get(self.param['macIf']+1,c.common['EVM_AVERAGE_CNT'], timeout=10)

        rssi_average = dictionaryRes.get('rssi')[1]     # Average RSSI
        resRxEVM = dictionaryRes.get('evm')[1]       # Average EVM
        print("Average RSSI : %s" %  rssi_average)
        print("Average EVM : %s" %  resRxEVM)

        self.res_rx_evm.append(float(resRxEVM))
                
        if (float(self.res_rx_evm[0]) <= c.expected['EXPECTED_RX_EVM_LIMIT']):
            print "RX Evm = ",self.res_rx_evm[0]
            status_list[self.param['macIf']][9] = 'Pass'
        else:     
            print "Rx Evm = ", self.res_rx_evm[0]
            status_list[self.param['macIf']][9] = "Fail"  
        ResultsFileHandler.set('Final results',channel_name+" Rx EVM@-55dBm","{0:.2f}".format(self.res_rx_evm[0]))
        ###ResFileName.close()
        del rssi_evm
        del regs

        #Stop transmission
        TesterDevice.transmit_rf("OFF")

         # *****************************************************    Build results    ********************************
        
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name
        '''
        if self.param['macIf'] == 0:
            channel_name = 'chA'
            channel_name_co = 'chB'
        else:
            channel_name = 'chB'
            channel_name_co = 'chA'
        '''
        # Open results file         
        ##ResFileName = open(final_res_file,'r+')
        ##ResultsFileHandler.read(final_res_file)

        status_sens = "Fail"
        if len(active_ch)<2:   
            pass
            index = 0
            for z in c.expected['rep_list_name']:
                if (self.param['macIf'] == 0):
                    end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),"N/A",rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),ResultsFileHandler.get('Final results',channel_name_co+" "+z),rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards
                else:
                    end_results_int.append([c.expected['rep_list_name'][index],"N/A",ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards    
                index +=1
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_"+channel_name))
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_"+channel_name_co))
            #sample_gain_results.append(ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))[1:-1])
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name_co+"_(hex,dB)"))[1:-1])
            

            # Add DCOC results
            for section in ResultsFileHandler.sections():
                for name, value in ResultsFileHandler.items(section):
                    if section == "DCOC DAC registers":
                        DCOC_DAC_reg_results.append(str(value))
                        print "DC value ", value
                    else:
                        pass
            self.res_sens_point = ResultsFileHandler.get("Sensitivity test","Sensitivity_chA")
            self.res_sens_point_co = ResultsFileHandler.get("Sensitivity test","Sensitivity_chB")

            print "Sensitivity point = %s dB" %(self.res_sens_point)        
            
            #if (abs(float(self.res_sens_point))> abs(c.expected['EXPECTED_SENSITIVITY'])) and (abs(float(self.res_sens_point_co))> abs(c.expected['EXPECTED_SENSITIVITY'])):
            if (abs(float(self.res_sens_point)) > abs(c.expected['EXPECTED_SENSITIVITY'])):
                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(c.expected['EXPECTED_SENSITIVITY'])), "dB", status_sens])

        elif self.param['macIf']==0:
            pass 
        else:  
            self.res_sens_point = ResultsFileHandler.get("Sensitivity test","Sensitivity_chA")
            self.res_sens_point_co = ResultsFileHandler.get("Sensitivity test","Sensitivity_chB")

            print "Sensitivity point = %s dB" %(self.res_sens_point)        
            
            if (abs(float(self.res_sens_point))> abs(c.expected['EXPECTED_SENSITIVITY'])) and (abs(float(self.res_sens_point_co))> abs(c.expected['EXPECTED_SENSITIVITY'])):
                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)


            index = 0
            
            for z in c.expected['rep_list_name']:
                if (status_list[0][index] == status_list[1][index]) and (status_list[0][index] == "Pass"):
                    status = "Pass"
                else:
                    status = "Fail"
                end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], c.expected['rep_units'][index], status])
                index +=1
            
            # Add DCOC results
            for section in ResultsFileHandler.sections():
                for name, value in ResultsFileHandler.items(section):
                    if section == "DCOC DAC registers":
                        DCOC_DAC_reg_results.append(str(value))
                        print "DC value ", value
                    else:
                        pass

            # Internal report results
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(c.expected['EXPECTED_SENSITIVITY'])), "dB", status_sens])
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chA"))
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chB"))
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name_co+"_(hex,dB)"))[1:-1])
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))[1:-1])
            
            

        
        # Get sdk version        
        try:
            tn = telnetlib.Telnet( self.terminal_server_IP , self.ts_port)
            tn.read_until("ate> ",2)
            tn.write("version\n\r")
            sdk_version = tn.read_until("ate> ",2)
            #print "sw_version = ", sdk_version.split()[1]
            ResultsFileHandler.set('Report details',"sdk version",sdk_version.split()[1])
            tn.close()
        except:
            ResultsFileHandler.set('Report details',"sdk version","N\A")

        # Enter to uboot mode and get ethernet address, uboot version
        uboot_mode = uboot(self.terminal_server_IP, self.ts_port, self.plug_id)
        uboot_mode.enter_uboot()
        uboot_params = uboot_mode.get_dict()
        try:
            uboot_version = uboot_mode.execute("version")
            ethaddr = uboot_params['ethaddr']
            print "uboot_version: ",uboot_version
            print "ethaddr: ",ethaddr 
            ResultsFileHandler.set('Report details',"ethernet address",ethaddr)

            # Save uboot params to text file
            uboot_params_file = logs_path + "/uboot_params.txt"
            sdcard_file = open(uboot_params_file,"w")
            sorted = uboot_params.items()
            sorted.sort()
            for k, v in sorted:
                print k, v
                sdcard_file.write(k+'='+v)
                sdcard_file.write('\n')

            sdcard_file.close()
        except:
            uboot_version = "N/A"

        del uboot_mode

        ### Write to resilts file
        try:
            print "Writing to results file.."
            with ResFileName as f:
                ResultsFileHandler.write(f)
        except IOError:
            print "Can't read file..Please check the file"
        #ResFileName.close()                                        

        #Close results file
        ResFileName.close()
        print "----------------------------------- End verifying test --------------------------------\n" 
               
class TestsReportCreation(ParametrizedTestCase): 
    def test_report_creation(self):        
        # *****************************************************    Build results    ********************************
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name
        '''    
        if self.param['macIf'] == 0:
            channel_name = 'chA'
            channel_name_co = 'chB'
        else:
            channel_name = 'chB'
            channel_name_co = 'chA'
        '''
        status = "Fail"

        # Open results file         
        ResFileName = open(final_res_file,'r+')
        ResultsFileHandler.read(final_res_file)

        # Compare results with expected results and get status
        if (abs(c.expected['EXPECTED_HI_TX_EVM']) <= abs(float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][0])))):
            status_list[self.param['macIf']][0] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (abs(c.expected['EXPECTED_TX_EVM']) <= abs(float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][1])))):
            status_list[self.param['macIf']][1] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (c.expected['EXPECTED_TX_HI_POWER_LOW'] <= float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][2]))<= c.expected['EXPECTED_TX_HI_POWER_HIGH']):
            status_list[self.param['macIf']][2] = 'Pass'
        else:
            status_list[self.param['macIf']][2] = 'Fail'
        if (c.expected['EXPECTED_TX_POWER_LOW'] <= float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][3])) <= c.expected['EXPECTED_TX_POWER_HIGH']):
            status_list[self.param['macIf']][3] = 'Pass'
        else:
            status_list[self.param['macIf']][3] = 'Fail'    
        if (c.expected['EXPECTED_LO_LEAKAGE']>= float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][4]))):
            status_list[self.param['macIf']][4] = 'Pass'
        else:
            status_list[self.param['macIf']][4] = 'Fail'
        if (c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW']<=float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][5])) <=c.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH']):
            status_list[self.param['macIf']][5] = 'Pass'
        else:
            status_list[self.param['macIf']][5] = 'Fail'           
        if (c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW']<=float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][6])) <=c.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH']):
            status_list[self.param['macIf']][6] = 'Pass'
        else:
            status_list[self.param['macIf']][6] = 'Fail' 
        if (c.expected['EXPECTED_TX_FREQ_ERROR_LOW']<=float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][7])) <=c.expected['EXPECTED_TX_FREQ_ERROR_HIGH']):
            status_list[self.param['macIf']][7] = 'Pass'
        else:
            status_list[self.param['macIf']][7] = 'Fail' 
        if (c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW']<=float(ResultsFileHandler.get('Final results',channel_name+" "+c.expected['rep_list_name'][8])) <=c.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH']):
            status_list[self.param['macIf']][8] = 'Pass'
        else:
            status_list[self.param['macIf']][8] = 'Fail'
        if (float(ResultsFileHandler.get('Final results',channel_name+" Rx EVM@-55dBm")) <= c.expected['EXPECTED_RX_EVM_LIMIT']):
            status_list[self.param['macIf']][9] = 'Pass'
        else:     
            status_list[self.param['macIf']][9] = "Fail"               


        status_sens = "Fail"
        if len(active_ch)<2:   
            pass
            index = 0
            for z in c.expected['rep_list_name']:
                if (self.param['macIf'] == 0):
                    end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),"N/A",rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),ResultsFileHandler.get('Final results',channel_name_co+" "+z),rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards
                else:
                    end_results_int.append([c.expected['rep_list_name'][index],"N/A",ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], c.expected['rep_units'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards    
                index +=1
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_"+channel_name))
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_"+channel_name_co))
            #sample_gain_results.append(ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))[1:-1])
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name_co+"_(hex,dB)"))[1:-1])
            

            # Add DCOC results
            for section in ResultsFileHandler.sections():
                for name, value in ResultsFileHandler.items(section):
                    if section == "DCOC DAC registers":
                        DCOC_DAC_reg_results.append(str(value))
                        print "DC value ", value
                    else:
                        pass
            self.res_sens_point = ResultsFileHandler.get("Sensitivity test","Sensitivity_chA")
            self.res_sens_point_co = ResultsFileHandler.get("Sensitivity test","Sensitivity_chB")

            print "Sensitivity point = %s dB" %(self.res_sens_point)        
            
            if (abs(float(self.res_sens_point))> abs(c.expected['EXPECTED_SENSITIVITY'])) and (abs(float(self.res_sens_point_co))> abs(c.expected['EXPECTED_SENSITIVITY'])):                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(c.expected['EXPECTED_SENSITIVITY'])), "dB", status_sens])

        elif self.param['macIf']==0:
            pass 
        else:  
            self.res_sens_point = ResultsFileHandler.get("Sensitivity test","Sensitivity_chA")
            self.res_sens_point_co = ResultsFileHandler.get("Sensitivity test","Sensitivity_chB")

            print "Sensitivity point = %s dB" %(self.res_sens_point)        
            
            if (abs(float(self.res_sens_point))> abs(c.expected['EXPECTED_SENSITIVITY'])) and (abs(float(self.res_sens_point_co))> abs(c.expected['EXPECTED_SENSITIVITY'])):
                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)


            index = 0
            
            for z in c.expected['rep_list_name']:
                if (status_list[0][index] == status_list[1][index]) and (status_list[0][index] == "Pass"):
                    status = "Pass"
                else:
                    status = "Fail"
                end_results_int.append([c.expected['rep_list_name'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], c.expected['rep_units'][index], status])
                index +=1
            
            # Add DCOC results
            for section in ResultsFileHandler.sections():
                for name, value in ResultsFileHandler.items(section):
                    if section == "DCOC DAC registers":
                        DCOC_DAC_reg_results.append(str(value))
                        print "DC value ", value
                    else:
                        pass

            # Internal report results
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(c.expected['EXPECTED_SENSITIVITY'])), "dB", status_sens])
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chA"))
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chB"))
            sample_gain_results.append(ResultsFileHandler.get('Sample_Gain',channel_name_co+"_(hex,dB)"))
            sample_gain_results.append(ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))
            
            

        
        # Get sdk version        
        tn = telnetlib.Telnet( self.terminal_server_IP , self.ts_port)
        tn.read_until("ate> ",2)
        tn.write("version\n\r")
        sdk_version = tn.read_until("ate> ",2)
        #print "sw_version = ", sdk_version.split()[1]
        ResultsFileHandler.set('Report details',"sdk version",sdk_version.split()[1])
        tn.close()

        # Enter to uboot mode and get ethernet address, uboot version
        uboot_mode = uboot(self.terminal_server_IP, self.ts_port, self.plug_id)
        uboot_mode.enter_uboot()
        uboot_params = uboot_mode.get_dict()
        try:
            uboot_version = uboot_mode.execute("version")
            ethaddr = uboot_params['ethaddr']
            print "uboot_version: ",uboot_version
            print "ethaddr: ",ethaddr 
            match = re.compile(ur'.*?\)')
            current_uboot_version = re.search(match, uboot_version)
            ResultsFileHandler.set('Report details',"ethernet address",ethaddr)
            ResultsFileHandler.set('Report details',"uboot version",current_uboot_version) 

            # Save uboot params to text file
            uboot_params_file = logs_path + "/uboot_params.txt"
            sdcard_file = open(uboot_params_file,"w")
            sorted = uboot_params.items()
            sorted.sort()
            for k, v in sorted:
                print k, v
                sdcard_file.write(k+'='+v)
                sdcard_file.write('\n')

            sdcard_file.close()
        except:
            uboot_version = "N/A"

        del uboot_mode

        ### Write to resilts file
        try:
            print "Writing to results file.."
            with ResFileName as f:
                ResultsFileHandler.write(f)
        except IOError:
            print "Can't read file..Please check the file"
        #ResFileName.close()                                        

        # Close results file
        ResFileName.close()
        print "----------------------------------- End verifying test --------------------------------\n" 
        

global MXGen
global iq2010
global Logger
global evkDUT
global sens_point
global macIf        
global ethaddr
global rssi_evm, regs
global TesterDevice
      
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
    
    ethaddr = "N/A"
    active_ch = ''

    choice_list = []
    choice_num = []
    general_results =[]
    connections = []    
    DCOC_DAC_reg_results = []

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
    print (37 * '-')
    print ("   C A L I B R A T I O N S - M E N U")
    print (37 * '-')
    print (" 1. RX IQ imbalance calibration")
    print (" 2. RX sample gain calibration")
    print (" 3. RX sensitivity calibration")
    print (" 4. DCOC status calibration")
    print (" 5. TSSI calibration")
    print (" 6. TX power calibration")    
    print (" 7. Run all calibration tests")
    print (" 8. Measurements for Report + Create Report")
    print (" 9. Create Report")
    print (" 20. Exit")
    print (37 * '-')
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
    
    res_titles = ["Test name", "Measured result chA", "Measured result chB", "Expected result", "Units", "Status"]   
    connections_titles = ["Function", "Status", "Details"]
    #GPS_status = ["GPS lock", "Pass", "Pass"]
    #WiFi_pairing = ["WiFi pairing", "Pass", "Pass"]
    GPS_status = ["GPS lock", "No", "None"]
    WiFi_pairing = ["WiFi pairing", "No", "None"]
    connections.append(connections_titles)
    connections.append(GPS_status)
    connections.append(WiFi_pairing)
    
    end_results_int.append(res_titles)
    end_results_ext.append(res_titles)
    
    
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
    #Number = 'evk4_' + N + '_debug'
    
    btype = "_"+c.common['type_dict'].get(type)
    Number = c.common['type_dict'].get(type) +'_'+ N


    print "\nReboot board and start testing"
    UUT.reset_board(c.common['PLUG_ID'])
   
    param_dict_list_cal = []
    mac_if_list = []
    suite = unittest.TestSuite()

    # Select channel and run the tests
    mac_opts = ['a','b']    #chA, chB
    for mac in mac_opts:
        if mac in active_ch:
            print "Selected mac if " + str(mac_opts.index(mac))
            mac_if_list.append( mac_opts.index(mac) )

    # Get tester type
    for key,value in c.common['tester_device'].iteritems():
        if selected_tester == str(value):
            tester_type = key
        else:
            pass

    add_list = []   # Scenario collector list
    add_list_cal = []   # Calibration list
    add_list_sens = []  # Sensitivity test

    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    data_rate_list_cal = [6]
    data_frequency_list_cal = [5900]    
    temp_range = [25]
    dsrc_channel_models_enable = 0  # 0 - disable, 1 - enable
    serial_number = c.common['serial_number_dict'].get(type)+int(N)
    #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
    

    # __  Calibration parameters creation   ___________________________________________________________________________________________________________________________________________________
    ###########################################  Configure setup parameters  ##################################################################################################################
    for data in data_frequency_list_cal:
        for item in data_rate_list_cal:
            ###########################################  Configure setup parameters  ##################################################################################################################
            param_dict_list_cal = [{tester_type:int(selected_tester),'macIf':0,'ch_freq':data,'rate':item*2,'tx_power':20,'pad':1000,'num_pckt2send':1000,'interval_usec':100,'temperature':temp_range[0],"dsrc_channel_models_enable":dsrc_channel_models_enable,"bandwidth":10},
                                        {tester_type:int(selected_tester),'macIf':1,'ch_freq':data,'rate':item*2,'tx_power':20,'pad':1000,'num_pckt2send':1000,'interval_usec':100,'temperature':temp_range[0],"dsrc_channel_models_enable":dsrc_channel_models_enable,"bandwidth":10}]
            
            #######################################################################################################################################################################################        
            add_list_cal.append(param_dict_list_cal)
        
  
    """
    # Print configured list parameters
    for i in add_list_cal:
        print i
        print '\n'
    """
    # Create Results folder
    logs_path = r'C:/Local/wavesys/trunk/lab_utils/Test_Environment/logs/'+Number+"/"    #to do: Change to generic location
    final_res_file = logs_path + "/final_results_" + Number + "_" + str(param_dict_list_cal[0]['temperature']) + ".txt"
    print "Log path destination : ",logs_path

    d = os.path.dirname(logs_path)
    if not os.path.exists(d):
        os.makedirs(d)
        os.makedirs(d+"/sensitivity_logs")
        
    # Initialaze Results file
    ResultsFileHandler = ConfigParser.RawConfigParser()
    
    if (os.path.exists(final_res_file)):            
        print "Note: File exist....the results will be added to the existing file"
        #ResFileName = open(final_res_file,"r+")  # open for reading and writing
    else:

        # Open results file for adding sections
        ResFileName = open(final_res_file,"a+") 
        ResultsFileHandler.read(final_res_file)
        sections_list = ["DCOC DAC registers","Sample_Gain","LO leakage results","Sensitivity test","Report details","Final results"]
        for i in sections_list:
            if ResultsFileHandler.has_section(i) == False:
                ResultsFileHandler.add_section(i)
           
        # Preparing results section 
        index = 0
        for z in c.expected['rep_list_name'][:(len(c.expected['rep_list_name']))-1]:
            ResultsFileHandler.set('Final results',"chA "+z,"N/A")
            ResultsFileHandler.set('Final results',"chB "+z,"N/A")
            index +=1 

        ResultsFileHandler.set('Sample_Gain',"chA_(hex,dB)", "N/A")
        ResultsFileHandler.set('Sample_Gain',"chB_(hex,dB)", "N/A")
        ResultsFileHandler.set('LO leakage results',"LO_leak_chA", "N/A")
        ResultsFileHandler.set('LO leakage results',"LO_leak_chB", "N/A")
        ResultsFileHandler.set('Report details',"ethernet address","N/A")
        ResultsFileHandler.set('Sensitivity test',"sensitivity_cha","N/A")
        ResultsFileHandler.set('Sensitivity test',"sensitivity_chb","N/A")
        ResultsFileHandler.set('Report details',"sdk version","N/A")
        ResultsFileHandler.set('Report details',"uboot version","N/A")

        dc_iq_reg_list = [c.register['RX1_DC_IQ_0'],c.register['RX1_DC_IQ_1'],c.register['RX1_DC_IQ_4'],c.register['RX1_DC_IQ_6'],c.register['RX2_DC_IQ_0'],c.register['RX2_DC_IQ_1'],c.register['RX2_DC_IQ_4'],c.register['RX2_DC_IQ_6']]
        for i in range(0,len(dc_iq_reg_list)):
            ResultsFileHandler.set("DCOC DAC registers",str(hex(dc_iq_reg_list[i])), "N/A")

        #Write added sections to file
        try:
            print "Preparing results file.."
            with ResFileName as file:
                ResultsFileHandler.write(file)
        except IOError:
            print "Can't open file..Please check the file"
        ResFileName.close()

       
    # ----------  Individual test cases execution --------------------------
    ### Take action as per selected menu-option ###
    for i in range(len(mac_if_list)):
        CreateLOG = CreateLogFile()
        CreateLOG.Destination(logs_path)
        log_file = 'IP_'+evk_ip+'_Log_'+str(mac_if_list[i]) + "_" + str(param_dict_list_cal[i]['temperature'])
        Logger[mac_if_list[i]] = CreateLOG.Logger(log_file)
    
        if 1 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsRX_iq_imbalance, param=add_list_cal[0][mac_if_list[i]]))
        if 2 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsRX_sample_gain, param=add_list_cal[0][mac_if_list[i]]))
        if 3 in choice_num:
            for s in range(len(data_frequency_list_cal)*len(data_rate_list_cal)):
                suite.addTest(ParametrizedTestCase.parametrize(SystemTestsSensitivity, param=add_list_cal[s][mac_if_list[i]]))
        if 4 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsDCOCcheck, param=add_list_cal[0][mac_if_list[i]]))
        if 5 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsTSSI, param=add_list_cal[0][mac_if_list[i]]))
        if 6 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsTxPowerAdjustment, param=add_list_cal[0][mac_if_list[i]]))
        if 7 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsRX_iq_imbalance, param=add_list_cal[0][mac_if_list[i]]))
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsRX_sample_gain, param=add_list_cal[0][mac_if_list[i]]))
            suite.addTest(ParametrizedTestCase.parametrize(SystemTestsSensitivity, param=add_list_cal[0][mac_if_list[i]]))
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsTxPowerAdjustment, param=add_list_cal[0][mac_if_list[i]]))
            suite.addTest(ParametrizedTestCase.parametrize(CalibrationTestsDCOCcheck, param=add_list_cal[0][mac_if_list[i]]))
        if 8 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(TestsReport_Measurements_and_Creation, param=param_dict_list_cal[mac_if_list[i]]))
        if 9 in choice_num:
            suite.addTest(ParametrizedTestCase.parametrize(TestsReportCreation, param=param_dict_list_cal[mac_if_list[i]]))
            
        unittest.TestLoader.sortTestMethodsUsing = lambda _, x, y: cmp(y, x)
    unittest.TextTestRunner(verbosity=0).run(suite)    
    # ----------------------------------------------------------------------

              
    # Report creation
    if (8 in choice_num) or (9 in choice_num):
        print "\nReport lab creating..."
        int_report = ReportInternal()
        ext_report = ReportExternal()

        ResFileName = open(final_res_file,'r')    
        ResultsFileHandler.read(final_res_file)
        ethaddr = ResultsFileHandler.get('Report details',"ethernet address")
        sw_version = ResultsFileHandler.get('Report details',"sdk version")
        uboot_version = ResultsFileHandler.get('Report details',"uboot version")
        ResFileName.close()

        
        # Test report details list
        #rep_details = [N,c.common['type_dict'].get(type),sw_version, serial_number, gps_version, str(localtime),'25C', evk_ip, str(ethaddr)]
        rep_details = [N,c.common['type_dict'].get(type),sw_version + uboot_version, serial_number, c.common['gps_version_dict'].get(type), str(localtime),'25C', evk_ip, str(ethaddr)]

        # Print internal report results
        try:
            for i in range(len(end_results_int)):
                print i,end_results_int[i]
        except:
            pass
        
        # Create internal report
        int_report.run(logs_path, general_results, end_results_int, connections, serial_number , rep_details, lo_leakage_results, DCOC_DAC_reg_results, sample_gain_results)
        
        # Prepare and create external report,remove not neccessary results
        end_results_int.remove(end_results_int[1])
        end_results_int.remove(end_results_int[2])
        end_results_int.remove(end_results_int[4])
        end_results_int.remove(end_results_int[4])
        end_results_int.remove(end_results_int[4])
        end_results_int.remove(end_results_int[4])
        end_results_ext = end_results_int
        
        # Print external report results
        try:
            for i in range(len(end_results_ext)):
                print i,end_results_ext[i]
        except:
            pass
        
        # Create external report
        ext_report.run(logs_path, general_results, end_results_ext, connections, serial_number, rep_details)

'''
#if __name__ == '__main__':
#    main()
'''    
