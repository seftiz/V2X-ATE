import sys
import os
import socket
from os.path import isfile, join
#sys.path.append(r"\\fs01\docs\system\ate\Drivers\VSA_IQ2010")
sys.path.append(r"C:\sysHW\lib\instruments\VSA_IQ2010")
from iq2010 import *

# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)


from lib.instruments.SignalGeneratorMXG import SignalGeneratorMXGdriver


class TesterDeviceManager(object):
    def _init_(self, tester_ip, type): 
        self.type = type
        self.tester_ip = tester_ip

    def connect_to_tester(self, tester_ip = '127.0.0.1', type = None):
        if type is None:
           type = self.type
        
        self.type = type
        self.tester_ip = tester_ip
                    
        if self.type == '1':
            print "\nIQ2010 tester selected"
            """
            try: 
                #iq2010_IP = raw_input('\nEnter VSA IQ2010/NXN IP:  ')
                #iq2010_IP = '10.10.0.7'    #IQnxn device
                #iq2010_IP = '10.10.1.122'  #Remote host
                #iq2010_IP = '127.0.0.1'     #IQ2010 device, Local host
                socket.inet_aton(self.tester_ip)    
            except socket.error:
                print "Connection SocketError: Not legal IP address !!!"
                sys.exit()
            """
            # create new instance for IQ2010
            self.iq2010 = IQ2010()   
    
            # connect to server via ip
            try:
                self.iq2010.connect(self.tester_ip)
                time.sleep(0.1)
            except ValueError:
                print "VSA IQ2010 connection fail.\n"
        elif self.type == '2':   
            print "\nMXG tester selected"
            try: 
                print "Connecting to MXG, IP 10.10.0.8"
                self.tester_ip = '10.10.0.8'
                self.MXGen = SignalGeneratorMXGdriver(self.tester_ip, 5025, 3)
    
                self.MXGen.SetARBtriggerType("CONT")
                self.MXGen.SetARBsampleClock(40)     #40MHertz

                # create new instance for IQ2010 , VSA tests support
                self.iq2010 = IQ2010()   
            except IOError:
                print "IOError: connection to MXG failed !!!"
                sys.exit()
            # create new instance for IQ2010 , VSA tests support
            self.iq2010 = IQ2010()
            self.iq2010.connect("127.0.0.1")  

    def signal_generator_settings(self, freq_hz = 5900, power_dbm_set = -60, frames_to_send = 0):
        if self.type == "1":
            self.iq2010.vsg.set( freq_hz*1e6, power_dbm_set, 3, True, 0.0)
            time.sleep(0.2)
            self.iq2010.vsg.transmit_frame_count(frames_to_send) # 0 - free run, number - number of frames to send
            #self.iq2010.vsg.transmit_frame_count_raw(frames_to_send) # 0 - free run, number - number of frames to send
            time.sleep(0.1)
            
        elif self.type == "2":
            if frames_to_send == 0:
                self.MXGen.SetARBtriggerType("CONT")
            else:
                self.MXGen.SetARBtriggerType("SING")
            self.MXGen.SetFrequency(str(freq_hz))
            self.MXGen.SetAmplitude(str(power_dbm_set))

    def signal_generator_load_file(self, data_file = None, usb_drive = 0):
        if data_file == None:
            print "Data file not loaded.."
            sys.exit()
        if self.type == "1":
            self.iq2010.vsg.load(data_file)
        elif self.type == "2" and usb_drive == 1:
            self.MXGen.USBdriveLoadFile(data_file)
            self.MXGen.SetSequenceRepetition(seq_name = data_file, waveform_name = data_file, reps = 1000, type = "bin")
        else:
            # Copy waveform from Internal memory to BBG1
            self.MXGen.SetSequenceRepetition(seq_name = data_file, waveform_name = data_file, reps = 1000)
            #self.MXGen.SetSequenceRepetition(seq_name = "27MBPS", waveform_name = "27MBPS", reps = 1000)
            #self.MXGen.SetSequenceRepetition(seq_name = "12MBPS", waveform_name = "12MBPS", reps = 1000) 


    def vsa_settings(self, rf_freq_hz, rf_ampl_db, port, ext_atten_db, trigger_level_db, capture_window ):
        self.iq2010.vsa.set_config(rf_freq_hz, rf_ampl_db, port, ext_atten_db, trigger_level_db, capture_window )
        self.iq2010.vsa.set_agc()

    def prepare_vsa_measurements(self):
        #self.iq2010.vsa.set_agc()
        self.iq2010.vsa.capture_data( 2000e-6 )
        time.sleep(0.2)
        self.iq2010.vsa.analyze_802_11p()
        time.sleep(0.3)

    def get_vsa_measure(self,key):
        self.iq2010.vsa.capture_data( 2000e-6 )
        time.sleep(0.2)
        self.iq2010.vsa.analyze_802_11p()
        time.sleep(0.3)
        return self.iq2010.vsa.get_scalar_meas(key)
    
    def get_tx_vsa_measure(self,key):
        return self.iq2010.vsa.get_scalar_meas(key)

    def vsa_set_agc(self):
        self.iq2010.vsa.set_agc()

    def transmit_rf(self, state = 'OFF',trigger = 0):
        if self.type == "1":
            self.iq2010.vsg.rf_state(True if state == "ON" else False)
            #time.sleep(0.2)   
        elif self.type == "2":
            self.MXGen.SetRF_ON_OFF(state)
            #time.sleep(1)
            if trigger == 1:
                self.MXGen.SetTrigger("BUS")
            else:
                pass

signalTesterTypes = {'1': TesterDeviceManager.connect_to_tester }

# Tester selection by type 1 - vsa, 2 - mxg
def signalTester(type, ip, type_id):
    return signalTesterTypes[type](ip, type_id)