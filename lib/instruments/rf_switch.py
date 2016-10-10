#           Mini Circuits RF switch driver 12.07.2012
#------------------- Install instruction: ------------------------------------------
#
#1. copy MCL_RF_Switch_Controller.dll  to c:\windows\system32 folder
#2. from command line run regsvr32 C:\WINDOWS\system32\MCL_RF_Switch_Controller.dll
#3. install http://sourceforge.net/projects/pywin32/files/pywin32/ last updated module for your system 32/64 bit
#----------------------------------------------------------------------------------- 

# wrap RF switch dll amd expose the API into Python

import win32com.client
import pythoncom
import logging

log = logging.getLogger(__name__)

class MiniCircuitsUsbRfSwDriver(object):
    def __init__(self):
        self.sw = win32com.client.Dispatch("MCL_RF_Switch_Controller.USB_RF_Switch")
        connection_Status = self.connect_rf()
        
        if connection_Status:
            #print "RF switch connection OK"
            pass
        else:
            log.info("Connection to RF switch failed {}".format( connection_Status ) )
            raise IOError("Connection to RF switch failed..\n")
            
    def connect_rf(self, SN = "11205150010"):
        try:                
            connection_status = self.sw.Connect(SN)
            SN == self.sw.Read_SN()
            #print "\nThe serial number of RF switch: %s" %SN
            return connection_status
        except:
            log.info( "\nConnection error.. Not connected to RF switch, please check the ON/OFF button.." )
            raise IOError("Connection to RF switch failed..\n") 
        
    def get_temperature(self):
        # Not supported command         
        temperature_sw = self.sw.GetDeviceTemperature()
        print "\nTemperature of RF switch is ", temperature_sw
        
    
    def set_switch(self, spdt_switch_name, state):        
        """ Setting Switch funciton description """
        """ SwitchName - parameter for the required switch."""
        """ State - parameter can be 0 for DE-ENERGIZED (COM port 1) or can be 1 for ENERGIZED (COM port 2)."""
        """ Set all switches:  
            Handles all switches in one command 
            Transmit Array
            ? Byte[0]=9 
            ? Byte[1]= Set Switches state(Switch A- is LSB)  
            ? Bytes[2] through [63] are NC - Not Care 
            Bits used in Byte[1]: 
            The USB-1SPDT-A18 contains one Switch ? bit LSB (0) 
            The USB-2SPDT-A18 contains two Switches ? Bits: LSB (0) =A, 1=B 
            The USB-3SPDT-A18 contains three Switches ? Bits: LSB (0) =A, 1=B, 2=C 
            The USB-4SPDT-A18 contains four Switches ? Bits: LSB (0) =A, 1=B, 2=C, 3=D 
        """
        assert spdt_switch_name in ['A','B','C','D']
        assert state in [1,2]
        
        # Each SPDT switch only has a single input (COM) and can connect to and switch between 2 outputs
        sw_state = state - 1  # connected to switch port COM 1/COM 2
        self.sw.Set_Switch(spdt_switch_name, sw_state)

        return self.get_switch_status()
    
    def get_switch_status(self):        
        self.status = self.sw.GetSwitchesStatus()
        if self.status:
            #"Each bit in the Value represent one switch. LSB bit represent Switch A, MSB bit represent Switch D", self.Status
            log.info( "Status RF switch: %s" % str( self.status ) )   
            pass
        else:
            log.info( " Error...RF switches status is unavailable, please check the device.." )
            raise Exception(" Status for RF switch unknown")
        return self.status

    def disconnect(self):        
        self.sw.Disconnect()                
        print "\nRF switch was disconnected "

rfSwitchTypes = {'usb_rf_sw_box': MiniCircuitsUsbRfSwDriver }

def select_type(type):
    return rfSwitchTypes[type]()
    
#cn = sw.Connect()
#cn=sw.Set_SwitchesPort(1)
#cn=sw.Set_SwitchesPort(0)

#new = RFswitch_driver()
#new.GetSwitchesStatus()

if __name__ == "__main__":
    rf_sw = select_type('usb_rf_sw_box')
    rf_sw.connect_rf()
    #rf_sw.get_temperature()
    print "Connection status: ", rf_sw.get_switch_status()

    rf_sw.disconnect()

