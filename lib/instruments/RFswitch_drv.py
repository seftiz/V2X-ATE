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




class RFswitch_driver:
    def __init__(self):
        self.sw = win32com.client.Dispatch("MCL_RF_Switch_Controller.USB_RF_Switch")
        Connection_Status = self.ConnectRF()
        
        if Connection_Status:
            print "Connection to RF switch was successful"
        else:
            print "Connection to RF switch was NOT successful"
            exit()
            
    def ConnectRF(self, SN = "11205150010"):
        try:                
            Connection_Status = self.sw.Connect(SN)
            SN == self.sw.Read_SN()
            print "\nThe serial number of RF switch: %s" %SN
            return Connection_Status
        except:
            print "\nConnection error.. Not connected to RF switch, please check the ON/OFF button.."
            return 
        
    def GetTemperature(self):        
        TemperatureSW = self.sw.GetDeviceTemperature()
        print "\nTemperature of RF switch is ", TemperatureSW
        
    
    def SetSwitch(self, NameSwitch, State):        
        """ Setting Switch funciton description """
        """ SwitchName - parameter for the required switch."""
        """ State - parameter can be 0 for DE-ENERGIZED (COM port 1) or can be 1 for ENERGIZED (COM port 2)."""
        
        assert NameSwitch in ['A','B','C','D']
        assert State in [1,2]
        
        if State == 1:
            swState = 0  # connected to switch port COM 1
        else:
            swState = 1  # connected to switch port COM 2
        self.sw.Set_Switch(NameSwitch,swState)

        return self.Get_SW_Status()
    
    def Get_SW_Status(self):        
        self.Status = self.sw.GetSwitchesStatus()
        if self.Status == False:
            print "Error...RF switches status is unavailable, please check the device.."        
        else:
            #print "Each bit in the Value represent one switch. LSB bit represent Switch A, MSB bit represent Switch D", self.Status
             print "Status RF switch: ", self.Status, '\n'   
        return self.Status

    def RFswDisconnect(self):        
        self.sw.Disconnect()                
        print "\nRF switch was disconnected "


    
#cn = sw.Connect()
#cn=sw.Set_SwitchesPort(1)
#cn=sw.Set_SwitchesPort(0)

#new = RFswitch_driver()
#new.GetSwitchesStatus()
