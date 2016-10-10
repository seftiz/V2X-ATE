import sys
import os
import socket, time
from os.path import isfile, join

'''
sys.path.append(r'C:/sysHW/lib/instruments/Vector_Signal')
import litepoint_iq2010
import rf_vector_signal
import sig_generator_mxg
'''
from lib.instruments.Vector_Signal import litepoint_iq2010

from lib.instruments.Vector_Signal import sig_generator_mxg


class IQ2010_Base(object):
    def __init__(self, ip_addr): 
        self.ip = ip_addr
        # create new instance for IQ2010
        self.iq2010 = litepoint_iq2010.IQ2010()

    def connect(self):
        try: 
            socket.inet_aton(self.ip)
            # connect to server via ip
            rc = self.iq2010.connect(self.ip)
            if rc != 0:
                raise Exception("VSG IQ2010 connection fail.")
            return rc
        except socket.error:
            raise IOError("Connection SocketError: Not legal IP address !!!") 

    def disconnect(self):
        self.iq2010.disconnect()


class VSA_Incubator(object):
    pass


class LP_IQ2010_VSA(IQ2010_Base):
    
    def __init__(self, ip_addr): 
        super(LP_IQ2010_VSA, self).__init__(ip_addr)

    def vsa_settings(self, rf_freq_hz, rf_ampl_db, port, ext_atten_db, trigger_level_db, capture_window ):
        self.iq2010.vsa.set_config(rf_freq_hz*1e6, rf_ampl_db, port, ext_atten_db, trigger_level_db, capture_window )

    def prepare_vsa_measurements(self , capture_lenght = 2000e-6):
        self.iq2010.vsa.set_agc()
        self.iq2010.vsa.capture_data( capture_lenght )
        #time.sleep(0.3)
        self.iq2010.vsa.analyze_802_11p()
        #time.sleep(0.3)

    def get_tx_vsa_measure(self,key):
        return self.iq2010.vsa.get_scalar_meas(key)
    
    def vsa_get_measure(self, key):
        self.vsa_capture_data(2000e-6)
        self.vsa_analyze_802_11p()
        time.sleep(0.3)
        self.get_tx_vsa_measure(key)

    def vsa_set_agc(self):
        return self.iq2010.vsa.set_agc()

    def vsa_capture_data( self, capture_lenght_sec = 2000e-6 ):
        self.iq2010.vsa.capture_data( capture_lenght_sec )
        #time.sleep(0.5)

    def vsa_analyze_802_11p( self ):
        self.iq2010.vsa.analyze_802_11p()
        time.sleep(0.3)

    def get_version(self):
        return self.iq2010.get_version()

class LP_IQ2010_VSG(IQ2010_Base):  
    def __init__(self, ip_addr): 
        super(LP_IQ2010_VSG, self).__init__(ip_addr)

    def vsg_settings(self, freq_hz = 5900, power_dbm_set = -60):
        self.iq2010.vsg.set( freq_hz*1e6, power_dbm_set, 3, True, 0.0)
        #self.iq2010.vsg.transmit_frame_count(frames_to_send) # 0 - free run, number - number of frames to send

    def vsg_frames_to_send(self, frames_to_send = 0):
        self.iq2010.vsg.transmit_frame_count(frames_to_send) # 0 - free run, number - number of frames to send

    def load_file(self, file_path, data_file, bandwidth_mhz = 10):
        try:
            if os.path.exists(file_path + str(bandwidth_mhz) + "Mhz\\" + data_file + ".mod"):
                self.iq2010.vsg.load(file_path + str(bandwidth_mhz) + "Mhz\\" + data_file + ".mod")          
            else:
                raise Exception("Data file {} is not exists..".format(file_path + str(bandwidth_mhz) + "Mhz\\" + data_file))
        except:
            raise Exception("Data file {} is not loaded..".format(file_path + str(bandwidth_mhz) + "Mhz\\" + data_file))

    # Trigger parameter is for mxg compability
    def rf_enable(self, enable = False, trigger = 0):
        self.iq2010.vsg.rf_state(enable)

    def get_version(self):
        return self.iq2010.get_version()


class AG_MXG(object):

    def __init__(self, ip): 
        self.ip = ip

    def connect(self):
        
        try: 
            print "Connecting to MXG, IP ",self.ip
            self.mxg = sig_generator_mxg.MXG_N5182X(self.ip, port = 5025, timeout = 3)
            self.mxg.set_arb_trig_type("CONT")
            self.status_conn = True
        except IOError:
            raise Exception("IOError: connection to MXG failed !!!")

    def disconnect(self):
        del self.mxg

    def vsg_settings(self, freq_hz = 5900, power_dbm = -60):
        #self.mxg.set_arb_sample_clk(arb_sample_clk_mhz)     #40MHertz - Bandwidth 10Mhz,80MHertz - Bandwidth 20Mhz
        self.mxg.set_frequency( str(freq_hz) )
        self.mxg.set_amplitude( str(power_dbm) )

    def load_file(self, file_path, data_file, bandwidth_mhz = 10, usb_drive = 0):
        file_path = file_path
        # Configure OFDM bandwitdh
        arb_sample_clk_mhz = { 10 : 40, 20 : 80 }    #40MHertz - Bandwidth 10Mhz,80MHertz - Bandwidth 20Mhz
        self.mxg.set_arb_sample_clk(arb_sample_clk_mhz[bandwidth_mhz])     

        if usb_drive == 1:
            self.mxg.load_file_from_external_drive(data_file)
            self.mxg.set_sequence_repetition(seq_name = data_file, waveform_name = data_file, reps = 1000, type = "BIN")
        else:
            # Copy waveform from Internal memory to BBG1
            self.mxg.set_sequence_repetition(seq_name = data_file, waveform_name = data_file, reps = 1000)
    
    def vsg_frames_to_send(self, frames_to_send = 0):
        self.mxg.set_arb_trig_type("CONT" if frames_to_send > 0 else "SING")

    def rf_enable(self, enable = False, trigger = 0):
        self.mxg.set_rf_enable(enable)
        time.sleep(0.5)
        if trigger == 1:
            self.mxg.set_trigger("BUS")

    def get_version(self):
        return self.mxg.get_version()


#VsignalTypes = { 'vsa' : { 'litepoint': LP_IQ2010_VSA }, 'vsg' : { 'agilent': AG_MXG, 'litepoint': LP_IQ2010_VSG } }
VsignalTypes = { 'litepoint': { 'vsa' : LP_IQ2010_VSA,  'vsg': LP_IQ2010_VSG }, 'agilent' : {'vsg': AG_MXG} }

# Tester selection by type 1 - vsa, 2 - mxg
def vectorSignal( maker, type, ip_address):
    return VsignalTypes[ maker ][ type ](ip_address)
    '''
    if get_available( ip ):
        return VsignalTypes[ type ][ maker ]( str( ip ) )
    else:
        return "N/A"
    '''
def get_available( host_ip ):
    status = ( os.system("ping " + host_ip) == 0 )
    return status


if __name__ == "__main__":
    '''
    # VSG example
    # create new instance for vector signal
    litepoint2010 = rf_vector_signal.vectorSignal('litepoint2010','10.10.1.129')
    
    # connect to server via ip
    litepoint2010.connect()

    print "\n\n\nWorking with IQ2010 version %s\n\n\n" % litepoint2010.get_version()
    
    print "Setting VSG to (5900e6, -60, 3, True, 0.0), vsg will be on port 3 "
    litepoint2010.vsg_settings()
    print "Loading file"
    litepoint2010.load_file( "\\\\fs01\\docs\\system\\Integration\\Signals_sample\\10MHz\\qpsk_6MHz_434Bytes.mod" )
    litepoint2010.rf_enable( False )


    # Clear unit stats now
    
    print "Transmit 1000 packets"
    litepoint2010.vsg_frames_to_send(1000)
    #return

    # Cont transmit
    litepoint2010.rf_enable( True )
    time.sleep(10)
    litepoint2010.rf_enable( False )
    time.sleep(1)
    '''
    """
    VSA example
    """
    #return 
    # create new instance for vector signal
    #litepoint2010 = rf_vector_signal.vectorSignal('litepoint2010','10.10.1.129')
    litepoint2010 = vectorSignal('vsa', 'litepoint', '10.10.1.129')
    litepoint2010.connect()

    print "Setting VSA to requency of 5.860Mhz, max ampl to 5, vsa will be on left port 2"
    litepoint2010.vsa_settings( 5880, 25, 2, 0, -30, 20e-6 )
    #agc_data = litepoint2010.vsa_set_agc()
    #print "\nReceived agc : %f\n" % agc_data.value
    #litepoint2010.vsa_settings( 5880, 25, 2, 0, -30, 20e-6 )
    #litepoint2010.vsa_set_agc()
    
    litepoint2010.prepare_vsa_measurements()
    #litepoint2010.vsa_capture_data(2000e-6) #sec
    #litepoint2010.vsa_analyze_802_11p()

    #time.sleep(2)
    print "Capture data for 2000uSec and Activate 802.11P analysis on data"
    #litepoint2010.prepare_vsa_measurements()
    litepoint2010.vsa_capture_data(2000e-6) #sec
    litepoint2010.vsa_analyze_802_11p()


    """
    Measurments exapmles
    """
    print "start mesurments"
    measurment_analysis_80211ag_vals = [ "evmAll", "evmData", "evmPilot", "codingRate",  "freqErr", "clockErr", "ampErr", "ampErrDb", "phaseErr", "rmsPhaseNoise", "rmsPowerNoGap", "rmsPower",
                                        "pkPower", "rmsMaxAvgPower", "psduCrcFail", "plcpCrcPass", "dataRate", "numSymbols", "numPsduBytes", "SUBCARRIER_LO_B_VSA1", "VALUE_DB_LO_B_VSA1", 
                                        "SUBCARRIER_LO_A_VSA1", "VALUE_DB_LO_A_VSA1", "SUBCARRIER_UP_A_VSA1",  "VALUE_DB_UP_A_VSA1", "SUBCARRIER_UP_B_VSA1", "VALUE_DB_UP_B_VSA1", "LO_LEAKAGE_DBR_VSA1" ]

    for measure in measurment_analysis_80211ag_vals:
        try: 
            val = litepoint2010.get_tx_vsa_measure(measure)
            print "get var %s : %f" % ( measure, val )
        except:
            pass

    
    """

    #MXG Example
    mxg = rf_vector_signal.vectorSignal('mxg','10.10.0.8')

    # connect to server via ip
    mxg.connect()

    print "Setting MXG to (freq_hz = 5900, power_dbm = -60, arb_sample_clk_mhz = 40, frames_to_send = 0) "
    mxg.vsg_settings()
    print "Loading file"
    try:
        mxg.load_file( "6MBPS" )
        #mxg.rf_enable( False )
    
        # Clear unit stats now
    
        print "Transmit 1000 packets configured by sequence"
        mxg.vsg_frames_to_send(0)

        # Sing trigger transmit
        mxg.rf_enable( True, 1 )
        time.sleep(10)
        mxg.rf_enable( False )
        time.sleep(1)
    except IOError:
        raise Exception("Loading file failed" )    
    """