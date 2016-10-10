import sys, os, re, time, datetime, subprocess
import unittest
import inspect
import argparse
import socket, telnetlib
import math
import win32gui, win32con
import csv, ConfigParser
import logging, traceback
from os.path import isfile, join
from os import listdir
import json, signal
import webbrowser

from lib import globals, setup_consts, interfaces
from tests import common

from lib.file_handler import File_Handler
from utilities import utils, create_pdf_report, analyze_tests_results

from lib.instruments.TempChamberControl import temperature_chamber
from lib import globals, station_setup, HTMLTestRunner

import numpy as np
import pandas as pd
#powerswitch.reboot_plugs(['nps01/6'])
from PIL import ImageGrab

# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)


def main(evk_ip):
    localtime = time.asctime(time.localtime(time.time()))


if __name__ == "__main__":

    # Load configuration file
    cfg_file_name = "hw_setup_cfg.json"
    current_dir = os.getcwd() # returns current working directory
    print "Tests directory: %s"  %current_dir
    cfg_dir_name = "%s\\configuration\\" % current_dir 
    utilities_dir = "%s\\utilities\\" % current_dir 
    test_data_dir = "%s\\tests\\hw\\test_data\\" % current_dir
    input_conf_file = test_data_dir + "\input_parameters.csv"


    cfg_file = os.path.join(cfg_dir_name, cfg_file_name)

    if not os.path.exists( cfg_file ):
        raise globals.Error("configuration file \'%s\' is missing." % (cfg_file) )

    json_file = open(cfg_file)
    try:
        json_data = json.load(json_file)
    except Exception as err:
        traceback.print_exc()
        raise globals.Error("Failed to parse json data %s" % cfg_file, err)


    board_name_dict = {1:'ATK22016 (EVK4/Pangaea4)',2:'ATK22022 (Audi)',3:'ATK22027 (Laird)',4:'ATK23010 (Fitax)',5:'ATK22017 (EVK4S/Pangaea4S)'}
    print "\nBoard type selection:"
    for key,value in board_name_dict.iteritems():
        print "type %s:      %s" %(str(key),str(value))
    
    # Read and apply input user configuration
    try:
        if os.path.exists(input_conf_file):
            data_configuration = pd.read_csv(input_conf_file, index_col=0, delimiter = ',' )
        # Check if legal ip
        socket.inet_aton(str(data_configuration.IP[0]))

        # Update IP in json data file
        json_data['units'][0]['ip'] = str(data_configuration.IP[0])

        #json_data['units'][0]['rf_interfaces'][0]['freq'] = 5880
        selected_type = int(data_configuration.BoardType[0])
        board_number = int(data_configuration.BoardNumber[0])
        
    except Exception as err:
        raise globals.Error("Failed to parse input parameters data %s" % input_conf_file, err)


    globals.setup = station_setup.Setup( json_data )
    consts = setup_consts.CONSTS[globals.setup.station_parameters.station_name]
    
    board_type = consts.common['BOARD_TYPE'].get(int(selected_type),'unknown_type')
    serial_number = consts.common['SERIAL_NUMBER_DICT'].get(int(selected_type)) + int(board_number)
    gps_version = consts.common['GPS_VERSION_TYPE'][int(selected_type)]
    logs_path = r'C:/automation_setup_logs/' + board_type + "_"+ str(board_number) + "/"    #to do: Change to generic location
    sens_results = logs_path + "/sensitivity_collected_results_{}.csv".format(str(board_number)) # sensitivity logs
    tx_results = logs_path + "/tx_path_collected_results_{}.csv".format(str(board_number)) # tx path measurements logs
    final_report_file = logs_path + "/final_report_results_" + str(board_number) + ".txt"

    # create results folder
    d = os.path.dirname(logs_path)
    if not os.path.exists(d):
        os.makedirs(d)

    # create final results txt file
    if not os.path.exists(final_report_file):
        with open(final_report_file, "w") as out_file:
            pass

    # Create Rx Sensitivity results columns
    if not os.path.exists(sens_results):
        with open(sens_results, "w") as out_file:
            utils.print_and_log(out_file, "Date,Test,Temperature,Channel,Rate_Mbps,Frequency_MHz,Sensitivity_dB,Passed,Details,")
    
    # Create TX measurements results columns
    if not os.path.exists(tx_results):
        with open(tx_results, "w") as out_file:
            utils.print_and_log(out_file, "Date,Temperature,Channel,Rate_Mbps,PacketLengh,Frequency_MHz,Exp_TxPower_dBm,TxPower_dBm,Exp_LO_leakage_dBc,LO_leakage_dBc,Exp_TxEvm_dB,TxEvm_dB,Min_Tx_IqImb_Ampl_dB,Tx_IqImb_Ampl_dB,Max_Tx_IqImb_Ampl_dB,Min_Tx_IqImb_Phase_Deg,Tx_IqImb_Phase_Deg,Max_Tx_IqImb_Phase_Deg,Min_Tx_Freq_Err_kHz,Tx_Freq_Err_kHz,Max_Tx_Freq_Err_kHz,Min_Tx_Symb_Clk_Err_ppm,Tx_Symb_Clk_Err_ppm,Max_Tx_Symb_Clk_Err_ppm,Fails,")

    # Create timestamp for log and report file
    scn_time = "%s" % (datetime.datetime.now().strftime("%d%m%Y_%H%M%S"))   
    """ @var logger handle for loging library """
    log_file = os.path.join(globals.setup.station_parameters.log_dir, "st_log_%s.txt" % (scn_time) )
    print "note : log file created, all messages will redirect to : \n%s" % log_file
    logging.basicConfig(filename=log_file, filemode='w', level=logging.NOTSET)
    log = logging.getLogger(__name__)



    # load all system 
    globals.setup.load_setup_configuration_file()

    CHAMBER_TEMP_OVER_LIMIT = setup_consts.CHAMBER_TEMP_OVER_LIMIT   #90 deg
    DEFAULT_TEMP = setup_consts.DEFAULT_TEMP  #25 deg
    chamber_test = data_configuration.ChamberTest[0]   #True/False 
    if chamber_test:
        temperature_range = []
        for x in data_configuration.Temperature.dropna():
            temperature_range.append( int(x) )         # [25, 85, -10]

        # Get temperature chamber handle from setup
        if globals.setup.instruments.temperature_chamber is None:
            raise globals.Error("Temperature chamber is not initilized, please check your configuration")
        temperature_chamber = globals.setup.instruments.temperature_chamber
    else:
        temperature_range = [ DEFAULT_TEMP ]
        
    from tests.hw import tc_rx_iq_imbalance
    from tests.hw import tc_dcoc
    from tests.hw import tc_sample_gain
    from tests.hw import tc_rx_sensitivity
    from tests.hw import tc_tx_power
    from tests.hw import tc_rx_lna_vga_status
    from tests.hw import tc_tx_path
    from tests.hw import tc_read_system_settings
    from tests.hw import tc_sdk_snmp
    
    active_tests = data_configuration[data_configuration['TestActive'] == True].index.tolist()
    cal_tests_dict = {  'tc_rx_iq_imbalance' : tc_rx_iq_imbalance.CalibrationTestsRX_iq_imbalance,
                        'tc_dcoc' : tc_dcoc.CalibrationTestsDCOCcheck,
                        'tc_sample_gain' : tc_sample_gain.CalibrationTestsRxSampleGain,
                        'tc_tx_power' : tc_tx_power.CalibrationTestsTxPowerAdjustment  }

    sys_tests_dict = {  'tc_tx_path' : tc_tx_path.TXpathTests,
                        'tc_rx_sensitivity' : tc_rx_sensitivity.SystemTestsSensitivity,
                        'tc_rx_lna_vga_status' : tc_rx_lna_vga_status.SystemTestsLnaVgaStatus,
                        'tc_sdk_snmp' : tc_sdk_snmp.SdkSnmpTests   }

    common_tests_dict = {   'tc_read_system_settings' : tc_read_system_settings.ReadSystemRegistersSettings,
                            'analyze_tests_results' : analyze_tests_results.AnalyzeTestsResults }


    for t in temperature_range:
        if chamber_test:
            print "Setting temperature to ",t
            chamber_temp = int(temperature_chamber.get_temp())
            print "\n The Chamber Temperature is ",chamber_temp
            # Setting temperature
            temperature_chamber.set_temp(t)
            time.sleep(0.2)
            if (chamber_temp in range(23,27)) and (t == DEFAULT_TEMP) :
                pass
            else:
                # Temperature point stabilization (accuracy of 3 degree while loop)
                while abs(t-chamber_temp) >= 3:
                    chamber_temp = int(temperature_chamber.get_temp())
                    if (chamber_temp < t  and CHAMBER_TEMP_OVER_LIMIT > chamber_temp):
                        print "\n The current temperature is", chamber_temp, "less then", t
                        print 'Waiting..'
                    if chamber_temp > t:
                        print "\n The current temperature is", chamber_temp, "more then", t
                    time.sleep(20)
                print "Waiting 20 minutes for temperature absorbtion..\n"
                time.sleep(60*20)   # 60 sec * 20 = 20 minuts
            print "\n The current temperature stabilized on ", chamber_temp
        else:
            print "chamber not in use" 
        print "\n Start testing .. "

        suite = unittest.TestSuite()

        
        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        # Setup parameters configuration

        # Parameters block:
        calibration_enable = data_configuration.Calibration[0]   #True/False
        rf_interface_list = []
        for rf_index in data_configuration.RfInterface.dropna():
            rf_interface_list.append( int( rf_index ) )

        if calibration_enable and (not chamber_test):
            packet_interval = []
            frequency_list = setup_consts.DATA_FREQUENCY_LIST_CAL 
            rate_list = setup_consts.DATA_RATE_LIST_CAL
            power_list = setup_consts.DATA_TX_POWER_LIST_CAL
            data_lengh = setup_consts.DATA_LENGH_CAL
            packet_interval.append( setup_consts.PACKET_INTERVAL_USEC_CAL )
            dsrc_channel_models_enable = setup_consts.DSRC_CHANNEL_MODELS_ENABLE_CAL  # 0 - disable, 1 - enable
            ch_bw = setup_consts.CHANNEL_BW_CAL # OFDM channel bandwith 1 for 10Mhz, 2 for 20Mhz
        else:
            frequency_list, rate_list, power_list, data_lengh, packet_interval = [],[],[],[],[]
            for fr in data_configuration.Frequency.dropna():
                frequency_list.append( int(fr) )
            for r in data_configuration.Rate.dropna():
                rate_list.append( float(r) )
            for pwr in data_configuration.TxPower.dropna():
                power_list.append( float(pwr) )
            for dlen in data_configuration.PacketLength.dropna():
                data_lengh.append( int(dlen) )
            for interval in data_configuration.PacketInterval.dropna():
                packet_interval.append( int(interval) )
            for ch_m in data_configuration.ChannelModels.dropna():
                dsrc_channel_models_enable = ( int(ch_m) )   # 0 - disable, 1 - enable
            for bandw in data_configuration.Bandwidth.dropna():
                ch_bw = int(bandw)  # OFDM channel bandwith 1 for 10Mhz, 2 for 20Mhz

        #@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
        
        for freq in frequency_list:
            for rate in rate_list:
                for pad in data_lengh:
                    for tx_power in power_list:
                        test_param = [ {  'uut_id': (0,1),
                                        'evk_ip': str(globals.setup.units.unit(0).ip),
                                        'board_type': board_type,
                                        'board_number': board_number,
                                        'gps_version': gps_version,
                                        'test_data_dir': test_data_dir,
                                        'data_waveform': str(rate) + "MBPS",
                                        'final_report_file': final_report_file,
                                        'sens_results': sens_results,
                                        'tx_results': tx_results,
                                        'rf_if': 0,
                                        'ch_freq': freq,
                                        'rate': rate,
                                        'snmp_rate': rate*2,
                                        'tx_power': tx_power,
                                        'pad': pad,
                                        'num_pckt2send': 1000,
                                        'interval_usec': packet_interval[0],
                                        'temperature': t,
                                        'dsrc_channel_models_enable': dsrc_channel_models_enable,
                                        'rf_front_end_compensator' : data_configuration.RfFrontEnd[0],
                                        'bandwidth': ch_bw,
                                        'calibration_enable': calibration_enable },

                                        {  'uut_id': (0,2),
                                        'evk_ip': str(globals.setup.units.unit(0).ip),
                                        'board_type': board_type,
                                        'board_number': board_number,
                                        'gps_version': gps_version,
                                        'test_data_dir': test_data_dir,
                                        'data_waveform': str(rate) + "MBPS",
                                        'final_report_file': final_report_file,
                                        'sens_results': sens_results,
                                        'tx_results': tx_results,
                                        'rf_if': 1,
                                        'ch_freq': freq,
                                        'rate': rate,
                                        'snmp_rate': rate*2,
                                        'tx_power': tx_power,
                                        'pad': pad,
                                        'num_pckt2send': 1000,
                                        'interval_usec': packet_interval[0],
                                        'temperature': t,
                                        'dsrc_channel_models_enable': dsrc_channel_models_enable,
                                        'rf_front_end_compensator' : data_configuration.RfFrontEnd[0],
                                        'bandwidth': ch_bw,
                                        'calibration_enable': calibration_enable } ]



                        #for i in range(len(test_param)-1):
                        for i in rf_interface_list:
                            if calibration_enable:
                                if rate == 6:
                                    for cal_key in cal_tests_dict.iterkeys():
                                        if cal_key in active_tests:
                                            suite.addTest(common.ParametrizedTestCase.parametrize(cal_tests_dict[ cal_key ], param = test_param[i] ) )
                                             
                                    for sys_key in sys_tests_dict.iterkeys():
                                        if sys_key in active_tests:
                                            suite.addTest(common.ParametrizedTestCase.parametrize(sys_tests_dict[ sys_key ], param = test_param[i] ) )
                                else:
                                    for sys_key in sys_tests_dict.iterkeys():
                                        if sys_key in active_tests:
                                            suite.addTest(common.ParametrizedTestCase.parametrize(sys_tests_dict[ 'tc_rx_sensitivity' ], param = test_param[i] ) )
                            else:
                                for skey in sys_tests_dict.iterkeys():
                                    if skey in active_tests:
                                        suite.addTest(common.ParametrizedTestCase.parametrize(sys_tests_dict[ skey ], param = test_param[i] ) )
                                            
                                
        # Read system settings
        if 'tc_read_system_settings' in active_tests:
            suite.addTest(common.ParametrizedTestCase.parametrize(common_tests_dict[ 'tc_read_system_settings' ], param = test_param[rf_interface_list[0]] ) )

        # Analyze tests results
        if 'analyze_tests_results' in active_tests:
            suite.addTest(common.ParametrizedTestCase.parametrize(common_tests_dict[ 'analyze_tests_results' ], param = test_param[rf_interface_list[0]] ) )

        # define report file
        report_file = os.path.join(globals.setup.station_parameters.reports_dir, "report_%s.html" % (scn_time) ) 
        fp = file(report_file, 'wb')



        # Create unit information table
        uut_info = []
        for uut in globals.setup.units:
            #ver_info = uut.get_uut_info()
            ver_info = { 'sdk_ver': "sdk-4.3" }
            uut_info.append( { uut.ip, ver_info['sdk_ver']} )

        # use html atlk test runner
        runner = HTMLTestRunner.HTMLTestRunner(
                                                stream=fp,
                                                verbosity=2,
                                                title='auto-talks system testing',
                                                description = 'System tests and calibrations',
                                                uut_info = uut_info
                                                )

        try:
            result = runner.run(suite)
        except (KeyboardInterrupt, SystemExit):       
            pass
        finally:
            # close report file
            fp.close()

            print "test sequence completed, please review report file %s" % report_file
            # open an HTML file on my own (Windows) computer
            url = "file://" + report_file
            webbrowser.open(url,new=2)

    # Graceful return to room temperature
    if chamber_test:
        try:
            chamber_temp = int(temperature_chamber.get_temp())
            if ( DEFAULT_TEMP - 3 ) <= chamber_temp <= ( DEFAULT_TEMP + 3 ):
                print "\n The current temperature is {}".format( chamber_temp )
                pass
            else:    
                try:
                    print "Return to room temperature"   # 60-->25 degree Celcius
                    for back_to_room in [60, DEFAULT_TEMP]:
                        temperature_chamber.set_temp( back_to_room )   
                        time.sleep(60*5)
                        chamber_temp = int( temperature_chamber.get_temp() )
                        print "\n The current temperature is {}".format( chamber_temp )
                        print "Returning to room temperature, wait.."
                        if ( DEFAULT_TEMP - 3 ) <= chamber_temp <= ( DEFAULT_TEMP + 3 ):
                            pass
                        else:
                            time.sleep(60*30)
                    
                    chamber_temp = int( temperature_chamber.get_temp() )
                    print "\n The current temperature is {}".format( chamber_temp )
                    print "Temperature loop is finished!!"
                except:
                    print "The chamber not in use"
        except:
            log.info("Unable to set chamber")
            pass
    


    # Create pdf report True/False
    pdf_report = data_configuration.PdfReport[0]
    if pdf_report:
        results_collect = {} # report results dictionary   
        # Read collected results file and update dict 
        results_collect.update( utils.file_to_dict( final_report_file ) ) 
        pdf_report = create_pdf_report.Report()
        pdf_report.run(logs_path, test_data_dir, results_collect, ver_info, serial_number, False)
        pass



