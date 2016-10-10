#!/usr/bin/env python
# -*- coding: utf_8 -*-
"""
 modbus_tk for the temperature chamber.
 Modbus TestKit: Implementation of Modbus protocol in python

 (C)2009 - Luc Jean - luc.jean@gmail.com
 (C)2009 - Apidev - http://www.apidev.fr

 This is distributed under GNU LGPL license, see license.txt
"""

import sys
import serial



#add logging capability , This module defines functions and classes which implement a flexible error logging system for applications
import logging 
import time
import modbus_tk
import modbus_tk.defines as cst
import modbus_tk.modbus_rtu as modbus_rtu
import numpy

logger = modbus_tk.utils.create_logger("console")
""" by chosing console the logging information/errors will display in console"""

class TempChamberControl(object):
    def __init__(self, port_num = 1, mode = "", srvIpAddra = "", srvPort = 13456):
        
        self.highLimit = 86
        self.lowLimit = -23
        self.threshold = 0
        self.__mode = mode
        self.__retries = 3
        
        if self.__mode != "REMOTE":
            
            print "Connecting to serial port number: ",port_num
            """Connect to the temperature chamber"""
            self.chamber = modbus_rtu.RtuMaster(serial.Serial(port=port_num-1, baudrate=9600, bytesize=8, parity='N', stopbits=1, xonxoff=0))
            """port = port_num-1 ,because port 1 is actually port 2 ,and thats why we need to decrement"""
            self.chamber.set_timeout(5.0)
            self.chamber.set_verbose(True)
            logger.info("connected")
        else:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((srvIpAddra, srvPort))
            
    def set_temp(self, temp):
        
        """protection check"""
        need_protection = self.temperature_limit_protection(temp)
        print ("\n\n need_protection= ",need_protection)
        if True in need_protection:
            print ("\n\n\n\n pay attention!!! - the chamber reach is limit \n\n\n\n")
            if 'over' in need_protection:
                self.__write_reg(300, (self.highLimit-self.threshold)*10) #in case the temperature is over limit -> we decrease by threshold
            elif 'under' in need_protection:
                self.__write_reg(300, (self.lowLimit+self.threshold)*10)  #in case the temperature is under limit -> we increase by threshold
        else:        
            """ set the next temperature by parameter) """
            self.__write_reg(300, (temp)*10)
            return
        
    def get_temp(self, expectedValue=0):
        """ get the current temperature """
        reg_value = 100
        self.expectedValue = expectedValue
        chamber_temp = self.__read_reg(reg_value)
        print "chamber_temp (reg_value) = ",chamber_temp
        #Converting negative numbers to valid format
        chamber_temp = numpy.int16(chamber_temp)/10.0 if chamber_temp > 6000  else chamber_temp/10.0
        return (chamber_temp)        

    def __write_reg(self,regAddress, reg_value):
        if self.__mode != "REMOTE":
            """ write single """
            self.chamber.execute(1, cst.WRITE_SINGLE_REGISTER, regAddress, output_value = reg_value )
        else:
            sent = self.socket.send(regAddress)
            if sent == 0:
                raise RuntimeError, "socket connection broken"
            sent = self.socket.send(reg_value)
            if sent == 0:
                raise RuntimeError, "socket connection broken"
        return

    def __read_reg(self,regAddress, size=1):

        if self.__mode != "REMOTE":
            """ read single thru logger in order to support errors"""
            print "address for reading temperature from chamber is- %s" %(regAddress)
            #read_value = self.chamber.execute(1, cst.READ_HOLDING_REGISTERS, regAddress, size)
            read_value = self.chamber.execute(1, cst.READ_INPUT_REGISTERS, regAddress, size)[0]
            #print "debug1"
            while self.expectedValue != 0:        
                if self.expectedValue == read_value:
                    isSuccess = True
                    print "debug2_true"
                else:
                    isSuccess = False
                    print "debug2_false"
        else:
            print "debug3"
            read_value = self.socket.recv(regAddress)
            if size > 1:
                self.socket.recv(size)
                
        return read_value #, isSuccess
        
        #send some queries
        #logger.info(self.chamber.execute(1, cst.READ_COILS, 0, 10))
        #logger.info(master.execute(1, cst.READ_DISCRETE_INPUTS, 0, 8))
        #logger.info(master.execute(1, cst.READ_INPUT_REGISTERS, 100, 3))
        #logger.info(master.execute(1, cst.READ_HOLDING_REGISTERS, 100, 12))
        #logger.info(master.execute(1, cst.WRITE_SINGLE_COIL, 7, output_value=1))
        #logger.info(master.execute(1, cst.WRITE_SINGLE_REGISTER, 100, output_value=54))
        #logger.info(master.execute(1, cst.WRITE_MULTIPLE_COILS, 0, output_value=[1, 1, 0, 1, 1, 0, 1, 1]))
        #logger.info(master.execute(1, cst.WRITE_MULTIPLE_REGISTERS, 100, output_value=xrange(12)))
        
    def __del__(self):
        """ Close the pserial port to the Temperature chamber"""
        self.chamber.close()        

    def pmc_temperature(self, evk):
        (status, dimmStartConfigDict) = evk.DimmLoggerInit()
        currTemp = dimmStartConfigDict["temperature"]
        return currTemp

    def temperature_limit_protection(self,temp):
        """ verify that the chamber does not set temperature over the limit"""
        
        chamber_temp = int(self.get_temp()) #reading the current temperature of the chamber
        chamberNextTemp = temp #the next temperature that the chamber has set to
        if chamberNextTemp>self.highLimit:
            return (True,'over')
        if chamberNextTemp<self.lowLimit:
            return (True,'under')
        return (False,None)
        
        
    
    """
    def chkTemp(self,evk):
        #EvkTemperature = evk.ChannelControl.PollDcocTemperature()
        #EvkTemperature = evk.ChannelControl.GetChannelTepmerature()
        EvkTemperature = evk.AnalysisControl.GetChannelTemperature()
        return (EvkTemperature)
    
    def SetEvkTemperature(self,evk_RX, TempVal, temperatureSteps=2):

        '''setting temperature to EVK board'''
        #tempChamberControl =  TempChamberControl(serPortNum) #selecting serial port 
        TemperatureLogFile = open('c:/Local/TempLogFile.txt','w' )
        #currentTemp = int(self.pmc_temperature(evk_RX))
        currentTemp = self.chkTemp(evk_RX)[1]
        TemperatureLogFile.write("before entering the loop - EVK current temperature is- " + str(currentTemp) +'\n')
        TemperatureLogFile.write("Chamber_curr_temp,Chamber_next_temp,EVK_req_temp,EVK_curr_temp \n")
        print "\n evk temperature is- %s" %currentTemp
        
        while abs(currentTemp-TempVal) > 1:
            if abs(currentTemp-TempVal)>5:
                temperatureSteps = 5
            if abs(currentTemp-TempVal)>10:
                temperatureSteps = 10
            #read chamber temperature
            chamber_temp = int(self.get_temp())
            print "\n Chamber Temperature is ",chamber_temp
            TemperatureLogFile.write(str(chamber_temp) +",")
            
            if currentTemp < TempVal:
                        
                #increase chamber temperature by n dgree
                self.set_temp(chamber_temp+temperatureSteps+5)
                print "\n The current temperature is", currentTemp, "less then", TempVal
                print "Raising chamber temperature to", (chamber_temp+temperatureSteps+5)
                TemperatureLogFile.write(str(chamber_temp+temperatureSteps) +",")
                                           
            if currentTemp > TempVal:
                        
                #decrease chamber temperature by n dgree
                nextTemp = self.set_temp(chamber_temp-temperatureSteps-3)
                print "\n The current temperature is", currentTemp, "more then", TempVal
                print "decreasing chamber temperature to", (chamber_temp-temperatureSteps-3)
                TemperatureLogFile.write(str(chamber_temp-temperatureSteps) +",")
                time.sleep(20)

            if temperatureSteps >5:
                time.sleep(35)
            time.sleep(25)
            currentTemp = self.chkTemp(evk_RX)[1]
            print "evk temperature is- %s \n" %currentTemp
            
            TemperatureLogFile.write(str(TempVal) +",")
            TemperatureLogFile.write(str(currentTemp) +",  \n")            
            TemperatureLogFile.flush()
        print ("EVK temperature is set as expected")
        TemperatureLogFile.write("EVK temperature is set as expected \n")
        TemperatureLogFile.close()
        return    
    """
temperatureChamberTypes = {'controller_96': TempChamberControl }

def select_type(type, port):
    return temperatureChamberTypes[type](port)