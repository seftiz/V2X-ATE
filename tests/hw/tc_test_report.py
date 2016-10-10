

#from utilities import constants as c
from utilities import consts
from hw import hw_setup_config
from tests import common

from utilities.CreateLabReport_Internal import ReportInternal
from utilities.CreateLabReport_External import ReportExternal
from utilities import hw_tools
from utilities import rf_vector_signal

from lib.instruments import RFswitch_drv
from lib.instruments.TempChamberControl import TempChamberControl
from lib.instruments.SignalGeneratorMXG import SignalGeneratorMXGdriver
from lib import globals


from atlk import hwregs
from atlk import rxoobsampler
from utilities import tssi

import numpy as np
from atlk import powerswitch
from PIL import ImageGrab

from atlk.uboot import uboot
from atlk import mibs

rep_expected = ["<"+str("{0:.2f}".format(consts.expected['EXPECTED_HI_TX_EVM_DB'])),"<"+str("{0:.2f}".format(consts.expected['EXPECTED_TX_EVM_DB'])),str("{0:.2f}".format(consts.expected['EXPECTED_TX_HI_POWER_LOW_DBM']+1))+u"\u00B11",str("{0:.2f}".format(consts.expected['EXPECTED_TX_POWER_LOW_DBM']+1))+u"\u00B11","<"+str("{0:.2f}".format(consts.expected['EXPECTED_LO_LEAKAGE_DBC'])),u"\u00B1"+str("{0:.2f}".format(consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH_DB'])),u"\u00B1"+str("{0:.2f}".format(consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH_DEG'])),u"\u00B1"+str("{0:.2f}".format(consts.expected['EXPECTED_TX_FREQ_ERROR_HIGH_KHZ'])),u"\u00B1"+str("{0:.2f}".format(consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH_PPM'])),"<"+str(consts.expected['EXPECTED_RX_EVM_LIMIT_DB'])]
status_list = [["Fail"]*len(consts.expected['REPORT_LIST_ROWS']),["Fail"]*len(consts.expected['REPORT_LIST_ROWS'])]



end_results_int = []
end_results_ext = []
lo_leakage_results = []
sample_gain_results = []


class TestsReport_Measurements_and_Creation(common.ParametrizedTestCase):   
    """
    Class: TestsReport_Measurements_and_Creation
    Brief: Calibration validation and report creation, output: report txt/pdf
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """

    def setUp(self):
        self.UUT = hw_tools.Unit()   #UUT constructor
        self.UUT.connect(self.param['evk_ip'])     #Snmp connection
        self.rssi_evm, self.regs = self.UUT.py_sdk_tools_telnet_connect(self.param['evk_ip'], cfg_file['RSSI_EVM_PORT'], cfg_file['REGS_PORT'])
        self.ResultsFileHandler = ConfigParser.RawConfigParser()

    def tearDown(self):
        del self.rssi_evm, self.regs
        TesterDevice.transmit_rf("OFF")
        self.UUT.reset_board( hw_setup_config['PLUG_ID'])

    def test_report_meas(self):
        print "\n..............Start verifying test .............."    
        print "\n Configuration parameters: "
        for key,value in self.param.iteritems():
            if key == 'rate':
                value = value/2
            print "%s: %d " %(key,value)
        
        # Init values
        self.res_tx_evm , self.res_tx_Hievm, self.res_power, self.res_Hipower, self.res_LO_leakage, self.res_tx_amp, self.res_tx_phase, self.res_freq_err, self.res_symb_clk_err, self.res_rx_evm , self.res_sens_point = [],[],[],[],[],[],[],[],[],[],[]
        
        #rssi_evm, regs = UUT.py_sdk_tools_telnet_connect(evk_ip, cfg_file['RSSI_EVM_PORT'], cfg_file['REGS_PORT'])
        
        print "Channel frequency:", str(self.param['ch_freq'])

        self.UUT.set_mib( consts.snmp['FREQ_SET'][self.param['macIf']], self.param['ch_freq'])
        # Set additional channel to off
        self.UUT.set_mib( consts.snmp['RF_ENABLED'][abs(self.param['macIf']-1)], 2)
        
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name


        ResFileName = open(final_res_file,'r+')    
        ResultsFileHandler.read(final_res_file)
        
        # -----------------  TX PATH --------------------------------------
        # VSA select switch
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',1) # Switch B to com 1 
        Freq = (self.param['ch_freq'])*1e6
        Port = 2 # left port
        Atten = consts.common['TX_PATH_SETUP_ATTENUATION_DB'+"_"+str(self.param['macIf'])+btype]
        
        #self.UUT.set_mib( consts.snmp['TSSI_INTERVAL'][self.param['macIf']], 0)    # Turn OFF TSSI for a Fitax boards

        # EVK settings
        self.UUT.set_mib( consts.snmp['DATA_RATE'][self.param['macIf']], self.param['rate'])
        self.UUT.set_mib( consts.snmp['TX_POWER'][self.param['macIf']], self.param['tx_power'])
        self.UUT.set_mib( consts.snmp['FRAME_LEN'][self.param['macIf']], self.param['pad'])
        self.UUT.set_mib( consts.snmp['TX_PERIOD'][self.param['macIf']], self.param['interval_usec'])

        print 'Start transmiting from channel %s' %str(self.param['macIf'])
        self.UUT.set_mib( consts.snmp['TX_ENABLED'][self.param['macIf']], 1)   # Transmit ON

        TesterDevice.vsa_settings(Freq, consts.common['VSA_MAX_SIGNAL_LEVEL_DBM'], Port, Atten, consts.common['VSA_TRIGGER_LEVEL_DB'], consts.common['VSA_CAPTURE_WINDOW'] )
        #TesterDevice.vsa_set_agc()
        #time.sleep(1)
        #TesterDevice.prepare_vsa_measurements()
        
        print "\nStart TX path.."
        print "Perform measurements.."
        
        ch_power_list = [10,20,23]    #dBm
                                                         
        # VSA measurements loop
        rep = 20
        for pow in ch_power_list:
            self.UUT.set_mib(consts.snmp['TX_POWER'][self.param['macIf']], pow)    #Set tx power
            time.sleep(0.2)
            TesterDevice.vsa_settings(Freq, consts.common['VSA_MAX_SIGNAL_LEVEL_DBM'], Port, Atten, consts.common['VSA_TRIGGER_LEVEL_DB'], consts.common['VSA_CAPTURE_WINDOW'] )
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
                    #TesterDevice.vsa_settings(Freq, consts.common['VSA_MAX_SIGNAL_LEVEL_DBM'], Port, Atten, consts.common['VSA_TRIGGER_LEVEL_DB'], consts.common['VSA_CAPTURE_WINDOW'] )
                    time.sleep(1)
                    #print win32gui.GetWindowText (win32gui.GetForegroundWindow())
                    #hwnd = win32gui.GetForegroundWindow()
                    #win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
                    #time.sleep(0.5)
                    '''
                    TesterDevice.vsa_settings(Freq, consts.common['VSA_MAX_SIGNAL_LEVEL_DBM']+1, Port, Atten, consts.common['VSA_TRIGGER_LEVEL_DB'], consts.common['VSA_CAPTURE_WINDOW'] )
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
        lo_leak_power_list = consts.common['LO_LEAKAGE_POW_LIST_DBM']    # [23,20,15,12,10,8,5] dBm
        for p in lo_leak_power_list:
            self.UUT.set_mib(consts.snmp['TX_POWER'][self.param['macIf']], p)    #Set tx power
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
        
        results_list = [ self.res_tx_evm[2], self.res_tx_evm[1], self.res_power[2], self.res_power[1], self.res_LO_leakage[1], self.res_tx_amp[1], self.res_tx_phase[1],self.res_freq_err[1],self.res_symb_clk_err[1]]
        status = "Fail"

        # Compare results with expected results and get status
        if (abs(consts.expected['EXPECTED_HI_TX_EVM_DB']) <= abs(float(results_list[0])) ):
            status_list[self.param['macIf']][0] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (abs(consts.expected['EXPECTED_TX_EVM_DB']) <= abs(float(results_list[1]))):
            status_list[self.param['macIf']][1] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (consts.expected['EXPECTED_TX_HI_POWER_LOW_DBM'] <= float(results_list[2]) <= consts.expected['EXPECTED_TX_HI_POWER_HIGH_DBM']):
            status_list[self.param['macIf']][2] = 'Pass'
        else:
            status_list[self.param['macIf']][2] = 'Fail'
        if (consts.expected['EXPECTED_TX_POWER_LOW_DBM'] <= float(results_list[3]) <= consts.expected['EXPECTED_TX_POWER_HIGH_DBM']):
            status_list[self.param['macIf']][3] = 'Pass'
        else:
            status_list[self.param['macIf']][3] = 'Fail'    
        if (consts.expected['EXPECTED_LO_LEAKAGE_DBC']>= results_list[4]):
            status_list[self.param['macIf']][4] = 'Pass'
        else:
            status_list[self.param['macIf']][4] = 'Fail'
        if (consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW_DB']<=float(results_list[5]) <=consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH_DB']):
            status_list[self.param['macIf']][5] = 'Pass'
        else:
            status_list[self.param['macIf']][5] = 'Fail'           
        if (consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW_DEG']<=float(results_list[6]) <=consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH_DEG']):
            status_list[self.param['macIf']][6] = 'Pass'
        else:
            status_list[self.param['macIf']][6] = 'Fail' 
        if (consts.expected['EXPECTED_TX_FREQ_ERROR_LOW_KHZ']<=float(results_list[7]) <=consts.expected['EXPECTED_TX_FREQ_ERROR_HIGH_KHZ']):
            status_list[self.param['macIf']][7] = 'Pass'
        else:
            status_list[self.param['macIf']][7] = 'Fail' 
        if (consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW_PPM']<=float(results_list[8]) <=consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH_PPM']):
            status_list[self.param['macIf']][8] = 'Pass'
        else:
            status_list[self.param['macIf']][8] = 'Fail' 
        
        #print "\n\n status_list : ",status_list        

        index = 0
        for z in consts.expected['REPORT_LIST_ROWS'][:(len(consts.expected['REPORT_LIST_ROWS']))-1]:
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
        self.UUT.set_mib(consts.snmp['TX_ENABLED'][self.param['macIf']], 2)   # Transmit OFF
        
        # ---------------------------- RX PATH -----------------------------------------

        print "\nStart RX path.."
        RFswitch.set_switch('A',self.param['macIf']+1) # setup RF Switch A to com 1/2   (com1 selection for chA,com2 selection for chB)
        RFswitch.set_switch('B',2) # Switch B to com 2 
        ###ResFileName = open(final_res_file,'r')
        ###ResultsFileHandler.read(final_res_file)
        
        # Calculate initial Pin for RX EVM test, should be -60dBm
        tx_power_val = consts.common['RX_IQ_IMBALANCE_INIT_PIN_POWER_DBM'] + consts.common['RX_PATH_SETUP_ATTENUATION_DB'+"_"+str(self.param['macIf'])+btype]
        
        #Start transmission and measurements
        TesterDevice.signal_generator_settings(self.param['ch_freq'],tx_power_val)     
        TesterDevice.transmit_rf("ON")

        #Get RX EVM
        dictionaryRes = self.rssi_evm.get(self.param['macIf']+1,consts.common['EVM_AVERAGE_CNT'], timeout=10)

        rssi_average = dictionaryRes.get('rssi')[1]     # Average RSSI
        resRxEVM = dictionaryRes.get('evm')[1]       # Average EVM
        print("Average RSSI : %s" %  rssi_average)
        print("Average EVM : %s" %  resRxEVM)

        self.res_rx_evm.append(float(resRxEVM))
                
        if (float(self.res_rx_evm[0]) <= consts.expected['EXPECTED_RX_EVM_LIMIT_DB']):
            print "RX Evm = ",self.res_rx_evm[0]
            status_list[self.param['macIf']][9] = 'Pass'
        else:     
            print "Rx Evm = ", self.res_rx_evm[0]
            status_list[self.param['macIf']][9] = "Fail"  
        ResultsFileHandler.set('Final results',channel_name+" Rx EVM@-55dBm","{0:.2f}".format(self.res_rx_evm[0]))
        ###ResFileName.close()
        #del rssi_evm
        #del regs

        #Stop transmission
        TesterDevice.transmit_rf("OFF")

         # *****************************************************    Build results    ********************************
        
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name

        # Open results file         
        ##ResFileName = open(final_res_file,'r+')
        ##ResultsFileHandler.read(final_res_file)

        status_sens = "Fail"
        if len(active_ch)<2:   
            pass
            index = 0
            for z in consts.expected['REPORT_LIST_ROWS']:
                if (self.param['macIf'] == 0):
                    end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),"N/A",rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),ResultsFileHandler.get('Final results',channel_name_co+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards
                else:
                    end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],"N/A",ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards    
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
            
            #if (abs(float(self.res_sens_point))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])) and (abs(float(self.res_sens_point_co))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])):
            if (abs(float(self.res_sens_point)) > abs(consts.expected['EXPECTED_SENSITIVITY_DB'])):
                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(consts.expected['EXPECTED_SENSITIVITY_DB'])), "dB", status_sens])

        elif self.param['macIf']==0:
            pass 
        else:  
            self.res_sens_point = ResultsFileHandler.get("Sensitivity test","Sensitivity_chA")
            self.res_sens_point_co = ResultsFileHandler.get("Sensitivity test","Sensitivity_chB")

            print "Sensitivity point = %s dB" %(self.res_sens_point)        
            
            if (abs(float(self.res_sens_point))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])) and (abs(float(self.res_sens_point_co))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])):
                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)


            index = 0
            
            for z in consts.expected['REPORT_LIST_ROWS']:
                if (status_list[0][index] == status_list[1][index]) and (status_list[0][index] == "Pass"):
                    status = "Pass"
                else:
                    status = "Fail"
                end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status])
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
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(consts.expected['EXPECTED_SENSITIVITY_DB'])), "dB", status_sens])
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chA"))
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chB"))
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name_co+"_(hex,dB)"))[1:-1])
            sample_gain_results.append((ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))[1:-1])
        
        # Get sdk version        
        try:
            tn = telnetlib.Telnet( hw_setup_config['TERMINAL_SERVER_IP'] , hw_setup_config['TERMINAL_SERVER_PORT'])
            tn.read_until("ate> ",2)
            tn.write("version\n\r")
            sdk_version = tn.read_until("ate> ",2)
            #print "sw_version = ", sdk_version.split()[1]
            ResultsFileHandler.set('Report details',"sdk version",sdk_version.split()[1])
            tn.close()
        except:
            ResultsFileHandler.set('Report details',"sdk version","N\A")

        # Enter to uboot mode and get ethernet address, uboot version
        uboot_mode = uboot(hw_setup_config['TERMINAL_SERVER_IP'], hw_setup_config['TERMINAL_SERVER_PORT'], hw_setup_config['PLUG_ID'])
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


    def test_report_creation(self):        
        # *****************************************************    Build results    ********************************
        channel_name = 'chA'
        channel_name_co = 'chB'
        
        if self.param['macIf'] == 1:
            channel_name,channel_name_co = channel_name_co,channel_name

        status = "Fail"

        # Open results file         
        ResFileName = open(final_res_file,'r+')
        ResultsFileHandler.read(final_res_file)

        # Compare results with expected results and get status
        if (abs(consts.expected['EXPECTED_HI_TX_EVM_DB']) <= abs(float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][0])))):
            status_list[self.param['macIf']][0] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (abs(consts.expected['EXPECTED_TX_EVM_DB']) <= abs(float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][1])))):
            status_list[self.param['macIf']][1] = 'Pass'
        else:     
            status_list[self.param['macIf']][1] = 'Fail'
        if (consts.expected['EXPECTED_TX_HI_POWER_LOW_DBM'] <= float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][2]))<= consts.expected['EXPECTED_TX_HI_POWER_HIGH_DBM']):
            status_list[self.param['macIf']][2] = 'Pass'
        else:
            status_list[self.param['macIf']][2] = 'Fail'
        if (consts.expected['EXPECTED_TX_POWER_LOW_DBM'] <= float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][3])) <= consts.expected['EXPECTED_TX_POWER_HIGH_DBM']):
            status_list[self.param['macIf']][3] = 'Pass'
        else:
            status_list[self.param['macIf']][3] = 'Fail'    
        if (consts.expected['EXPECTED_LO_LEAKAGE_DBC']>= float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][4]))):
            status_list[self.param['macIf']][4] = 'Pass'
        else:
            status_list[self.param['macIf']][4] = 'Fail'
        if (consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_LOW_DB']<=float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][5])) <=consts.expected['EXPECTED_TX_IQIMBALANCE_GAIN_HIGH_DB']):
            status_list[self.param['macIf']][5] = 'Pass'
        else:
            status_list[self.param['macIf']][5] = 'Fail'           
        if (consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_LOW_DEG']<=float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][6])) <=consts.expected['EXPECTED_TX_IQIMBALANCE_PHASE_HIGH_DEG']):
            status_list[self.param['macIf']][6] = 'Pass'
        else:
            status_list[self.param['macIf']][6] = 'Fail' 
        if (consts.expected['EXPECTED_TX_FREQ_ERROR_LOW_KHZ']<=float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][7])) <=consts.expected['EXPECTED_TX_FREQ_ERROR_HIGH_KHZ']):
            status_list[self.param['macIf']][7] = 'Pass'
        else:
            status_list[self.param['macIf']][7] = 'Fail' 
        if (consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_LOW_PPM']<=float(ResultsFileHandler.get('Final results',channel_name+" "+consts.expected['REPORT_LIST_ROWS'][8])) <=consts.expected['EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH_PPM']):
            status_list[self.param['macIf']][8] = 'Pass'
        else:
            status_list[self.param['macIf']][8] = 'Fail'
        if (float(ResultsFileHandler.get('Final results',channel_name+" Rx EVM@-55dBm")) <= consts.expected['EXPECTED_RX_EVM_LIMIT_DB']):
            status_list[self.param['macIf']][9] = 'Pass'
        else:     
            status_list[self.param['macIf']][9] = "Fail"               


        status_sens = "Fail"
        if len(active_ch)<2:   
            pass
            index = 0
            for z in consts.expected['REPORT_LIST_ROWS']:
                if (self.param['macIf'] == 0):
                    end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),"N/A",rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name+" "+z),ResultsFileHandler.get('Final results',channel_name_co+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards
                else:
                    end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],"N/A",ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])
                    #end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status_list[self.param['macIf']][index]])  # Setting for Fitax boards    
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
            
            if (abs(float(self.res_sens_point))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])) and (abs(float(self.res_sens_point_co))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])):                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(consts.expected['EXPECTED_SENSITIVITY_DB'])), "dB", status_sens])

        elif self.param['macIf']==0:
            pass 
        else:  
            self.res_sens_point = ResultsFileHandler.get("Sensitivity test","Sensitivity_chA")
            self.res_sens_point_co = ResultsFileHandler.get("Sensitivity test","Sensitivity_chB")

            print "Sensitivity point = %s dB" %(self.res_sens_point)        
            
            if (abs(float(self.res_sens_point))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])) and (abs(float(self.res_sens_point_co))> abs(consts.expected['EXPECTED_SENSITIVITY_DB'])):
                status_sens = 'Pass'
            else:
                status_sens = 'Fail'
            print "Sensitivity point status: %s" %(status_sens)


            index = 0
            
            for z in consts.expected['REPORT_LIST_ROWS']:
                if (status_list[0][index] == status_list[1][index]) and (status_list[0][index] == "Pass"):
                    status = "Pass"
                else:
                    status = "Fail"
                end_results_int.append([consts.expected['REPORT_LIST_ROWS'][index],ResultsFileHandler.get('Final results',channel_name_co+" "+z),ResultsFileHandler.get('Final results',channel_name+" "+z),rep_expected[index], consts.expected['REPORT_UNITS'][index], status])
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
            end_results_int.append(["Sensitivity test",self.res_sens_point,self.res_sens_point_co,"<"+str("{0:.2f}".format(consts.expected['EXPECTED_SENSITIVITY_DB'])), "dB", status_sens])
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chA"))
            lo_leakage_results.append(ResultsFileHandler.get('LO leakage results',"LO_leak_chB"))
            sample_gain_results.append(ResultsFileHandler.get('Sample_Gain',channel_name_co+"_(hex,dB)"))
            sample_gain_results.append(ResultsFileHandler.get('Sample_Gain',channel_name+"_(hex,dB)"))
            
            

        
        # Get sdk version        
        tn = telnetlib.Telnet( hw_setup_config['TERMINAL_SERVER_IP'] , hw_setup_config['TERMINAL_SERVER_PORT'])
        tn.read_until("ate> ",2)
        tn.write("version\n\r")
        sdk_version = tn.read_until("ate> ",2)
        #print "sw_version = ", sdk_version.split()[1]
        ResultsFileHandler.set('Report details',"sdk version",sdk_version.split()[1])
        tn.close()

        # Enter to uboot mode and get ethernet address, uboot version
        uboot_mode = uboot(hw_setup_config['TERMINAL_SERVER_IP'], hw_setup_config['TERMINAL_SERVER_PORT'], hw_setup_config['PLUG_ID'])
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

        # Close results file
        ResFileName.close()
        print "----------------------------------- End verifying test --------------------------------\n" 
