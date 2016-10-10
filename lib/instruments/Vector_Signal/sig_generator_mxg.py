#!/usr/bin/env python

""" Telnetlib is a package for Telnet comunication. This script will handle the MXG Signal generator by remote connection """
# HOST = '10.10.1.114'
# PORT = 5025
# LOOP = 3

import telnetlib
import time

class BaseVSG(object):
    """
    All devices drivers should be inheritance from this class
    and implement the following functions.
    Otherwise an exception will be raised.
    """

    def __init__(self, ip):
        self.ip = None

    def __del__(self):
        raise Exception("Missing implementaion for function __del__ in the vsg driver.")

    def __open(self):
        raise Exception("Missing implementaion for function open in the vsg driver.")

    def __close(self):
        raise Exception("Missing implementaion for function close in the vsg driver.")

    def __send_command(self, command, check_echo = True):
        raise Exception("Missing implementaion for function write in the vsg driver.")

    def __read_until(self, until, timeout):
        self.read_until( until, timeout )

    def __wait_for_promt(self, until, timeout):
        self.read_until( until, timeout )
        raise Exception("Missing implementaion for function read_until in the vsg driver.")



class MXG_N5182X(BaseVSG):
    def __init__(self, host, port, loop, enable_prints = False):

        """ host = ip | port = port | loop = how many times run the command if failure """
        
        self.__host = host
        self.__port = port
        self.__loop = loop
        self.__enable_prints = enable_prints
        
        #Connect to the Signal Generator
        self.tn = telnetlib.Telnet(host=self.__host, port=self.__port)

        #Reset the Signal Generator
        self.__send_command("*RST")
        #self.__measMode = "OFF"   ## possible values CHANPOWER - measure channel power, OCCBW - occupied bandwidth mode. Default = off
        

    def __del__(self):
        """ close connection:
        1st go to 'clean' prompt
        2nd send Ctrl+] (chr = 29) in order to close agilent session
        3rd close telnet connection """

        self.tn.write("\r\n")
        self.__wait_for_promt()
        self.tn.write("%c"%chr(29))
        self.tn.close()

    def __send_command(self, command):
        """ sending command to signal generator by using telnet write"""
        for i in range(self.__loop):
            if self.__enable_prints: print "Sending command: "+command
            self.tn.write(command+"\r\n")
            time.sleep(0.1)
            try:
                self.__wait_for_promt()
            except EOFError or '': # raised by self.rawq_getchar()
                self.tn.write("\r\n")
                 #if no error - continue and return True
                 #if error repeat transimt n time, if still error return False
                continue
            return True
        return False

    def __read_string(self,timeout = 2):
        """ read the string result from the telnet port"""
        res_str = self.tn.read_eager()
        #resStr = self.tn.read_until("\r\n",timeout)
        #resStr = self.tn.read_until('SCPI>',timeout)
        #resStr = self.tn.read_very_eager()
        return res_str

    def __wait_for_promt(self, promt = 'SCPI>', timeout = 2):
        """waiting for prompt"""
        read = self.tn.read_until(promt, timeout)
        if self.__enable_prints: print read
        return read
        
    def set_rf_enable(self, mode = False):
        #"Turns signal generator RF state %s" %(str(mode))
        self.__send_command(":OUTPut:STATe " + ("ON" if mode else "OFF"))
        time.sleep(1)
        return
    
    def set_frequency(self, freqVal):
        """ config the frequency for signal generator,  input freqVal given in MHz, output sendOk True if successful"""
        sendOk = self.__send_command("FREQ "+str(freqVal) + " MHz")
        return sendOk

    def set_amplitude(self, amplVal):
        """ config the amplitude for signal generator,  input amplVal given in dBm, output sendOk True if successful"""
        sendOk = self.__send_command("POW:AMPL "+str(amplVal) + " dBm")
        return sendOk    

    def recall_state(self, state_num):
        """ recall saved state in signal generator internal memmory"""
        sendOk = self.__send_command("*RCL " +str(state_num))   # TBD state 0 description
        stat = self.__send_command("*OPC?")                            # Checks for operation complete
        #print stat
        while (stat==0):
            print "Waiting for operation complete.."
        return sendOk
    
    # Function description: Play the waveform and use it to modulate the RF carrier
    def select_waveform(self, file_name, mem_type = "Volatile"):
        """ select the waveform from the list"""
        #self.__send_command(":MEM:CAT? WFM1:")
        #self.__send_command(":MMEM:DATA? /USER/"+file_name) :MEM:COPY "IQ_DATA@SNVWFM","Test_DATA@WFM1"
        #self.__send_command(":MEM:COPY "+ "/USER/"+file_name,"/USER/BBG1/"+file_name)
        """
        #-----------Volatile memory to Non-volatile memory
        #:MEMory:COPY "WFM1:file_name","NVWFM:file_name"
        #:MEMory:COPY "file_name@WFM1","file_name@NVWFM"
        #:MEMory:COPY "/user/bbg1/waveform/file_name","/user/waveform/file_name"
        #-----------Non-volatile memory to Volatile memory
        #:MEMory:COPY "NVWFM:file_name","WFM1:file_name"
        #:MEMory:COPY "file_name@NVWFM","file_name@WFM1"
        #:MEMory:COPY "/user/waveform/file_name","/user/bbg1/waveform/file_name"
        """
        if mem_type == "Volatile":
            self.__send_command('SOURce:RADio:ARB:WAVeform "WFM1:'+file_name+'.WFM"')  #Select the waveform from the volatile memory waveform list
        elif mem_type == "Non-Volatile":   
            #self.__send_command(':MEM:COPY "NVWFM:'+file_name+'.WFM"'+',"WFM1:'+file_name+'.WFM"') #copy file from Non-volatile memory to Volatile memory
            self.__send_command(':MEM:COPY '+'"/user/waveform/waveform_modulations/'+file_name+'.WFM"'+"," + '"WFM1:'+file_name+'.WFM"') #copy file from Non-volatile memory to Volatile memory
            self.__send_command('SOURce:RADio:ARB:WAVeform "WFM1:'+file_name+'.WFM"')  #Select the waveform from BBG1 memory waveform list
        # Play the wafeform
        #self.__send_command("SOUR:RAD:ARB:STAT ON")
        #self.__send_command("OUTP:MOD:STAT ON")
        return

    def set_modulation_enable(self, mode = False):
        """ config the signal generator modulation mode - Enable/Disable"""
        sendOk = self.__send_command(":OUTP:MOD " + ("ON" if mode else "OFF"))
        return senOk

       
    def set_sweep_mode_enable(self,mode = False):
        #Begins/Stops the step sweep operation
        self.__send_command("INIT:CONT " + ("ON" if mode else "OFF"))


    def set_arb_trig_type(self,type = "SINGle"):
        """ SING - enables Single triggering,  CONT - enables Continiuos triggering"""
        self.__send_command(":SOURce:RADio:ARB:TRIGger:TYPE "+ type)         # This choice enables selected type

    def set_arb_trig_mode(self,mode = "IMM"):
        """ Modes: "IMM" - enables Restart on triger, "ON"  - enables Buffered trigger, "OFF" - enables No retrigger"""
        self.__send_command(":SOURce:RADio:ARB:RETRigger " + mode)         # This choice enables selected mode

    def set_arb_sample_clk(self,clkRate):
        """ config the Arb sample clock rate for signal generator,  input clkRate given in MHz, output sendOk True if successful"""
        sendOk = self.__send_command(":SOURce:RADio:ARB:SCLock:RATE "+str(clkRate*1e6))
        return sendOk
            
    def set_trigger(self, mode = "BUS"):
        """Modes: ["BUS", "KEY", "EXT"]"""
        self.__send_command(":SOUR:RAD:ARB:TRIG:SOUR " + mode)
        self.__send_command("*TRG")
            
    def delete_arb_memory(self, file_name):
        # "Delete %s modulation file waveform from USER/BBG1/WAVEFORM" %file_name
        sendOk = self.__send_command(":MMEMory:DELete[:NAME] " + file_name,[" WFM1:"])
        return sendOk
    
    def set_sequence_repetition(self, seq_name, waveform_name, reps, type = "WFM"):
        '''
        try:
            self.__send_command(":SYST:FIL:STOR:TYPE:AUTO ON")
            path = self.__send_command(":SYSTem:FILesystem:STORage:EXTernal:PATH?")
            self.__send_command(":SYSTem:FILesystem:STORage:EXTernal:PATH"+' "/waveform_modulations"')
            self.select_waveform(waveform_name, "Non-Volatile")
        except Exception as e:
            raise Exception('Error...{}'.format(e))
        '''
        self.__send_command('SOURce:RADio:ARB:WAVeform "WFM1:' + waveform_name + '.' + type + '"')
        sendOk = self.__send_command(':SOURce:RADio:ARB:SEQuence "SEQ:'+ seq_name + '",' + '"WFM1:'+ waveform_name +'.' + type + '",' + str(reps) + ',' + "ALL")
        #sendOk = self.__send_command(':SOUR:RAD:ARB:SEQ "SEQ:'+ seq_name + '",' + '"WFM1:'+ waveform_name +'.WFM",' + str(reps))
        #sendOk = self.__send_command(':SOURce:RADio:ARB:SEQuence "SEQ:'+ seq_name + '",' + '"WFM1:'+ waveform_name +'.WFM",' + str(reps) + ",M1|M2|M3|M4|")
        #self.__send_command(':MMEMory:CATalog? "SEQ:"')
        #sendOk = self.__send_command(':SOUR:RAD:ARB:SEQ "SEQ:'+ seq_name + '",' + '"WFM1:'+ waveform_name +'.WFM",' + str(reps) + ',' + "M1M2M3M4")
        self.__send_command('SOURce:RADio:ARB:WAVeform "SEQ:'+ seq_name + '"')
        
        # Play the sequence
        self.__send_command("SOUR:RAD:ARB:STAT ON")
        self.__send_command("OUTP:MOD:STAT ON")
        return sendOk

    def load_arb_memory(self):
        self.__send_command(":MMEMory:LOAD:ARB:ALL")

    def load_file_from_external_drive(self, file_name = "AWGN10MHZ"):
        usb_drive_status = self.__send_command(":SYSTem:FILesystem:STORage:EXTernal?")
        if usb_drive_status == 1:
            print "External USB connected\n"
            self.__send_command(":SYST:FIL:STOR:TYPE:AUTO ON")
            #self.__send_command(":SYSTem:FILesystem:STORage:EXTernal:PATH"+" /")
            #self.__send_command(":SYST:FIL:STOR:TYPE EXT")
            #self.__send_command(":MEMory:COPY:NAME "+'"NVWFM:'+file_name+'.bin"'+',"WFM1:'+file_name+'.bin"') #closed 22.09.2014 debug
            #self.__send_command(":MEMory:COPY:NAME "+'"NVMKR:'+file_name+'.bin"'+',"MKR1:'+file_name+'.bin"')
            #self.__send_command(":MEMory:COPY:NAME "+'"NVHDR:'+file_name+'.bin"'+',"HDR:'+file_name+'.bin"')
            self.__send_command(":SOURce:RADio:ARB:SCLock:RATE 80MHz")
            self.__send_command(":SOURce:RADio:ARB:WAVeform "+'"WFM1:'+file_name+'.bin"')
        else:
            print "External USB media drive is not connected!"
    def get_version(self):
        return self.__send_command(":SYSTem:VERSion?")
        #return self.__send_command(":SYSTem:IDN")
 

"""sys.path.append(r"C:\Local\wavesys\trunk\lab_utils\Test_Environment\Tools")
from SignalGeneratorMXG import SignalGeneratorMXGdriver
new = SignalGeneratorMXGdriver('10.10.1.114',5025,3)
SOURce:RADio:ARB:WAVeform "WFM1:TEST1.WFM"
"""
     
        
