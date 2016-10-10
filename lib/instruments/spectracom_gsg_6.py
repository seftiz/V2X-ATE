

import os, sys
import visa
import logging
import time
import threading
from uuts import common
from lib import utilities
from lib import globals


log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 5

class SPECTRACOM_GSG_6(object):

    def __init__(self, ip_addr, local_nic_id = 0 ):
        """
        * @fn  constructor
        * @brief initilize class and connect to unit over VISA, 
        * @param[in] ip_addr ate ip address
        * @param[in] local_nic_id local machine nic interface idx in case of more then one interface
        *
        * @return None
        *
        """
        visa_conn_str = "TCPIP{}::{}::inst0::INSTR".format( local_nic_id, ip_addr )
        self.hwd = visa.instrument(visa_conn_str)
        self.hwd.ask("*IDN?")

    def __del__(self):
        """
        * @fn destroctur
        * @brief terminate  terminate class 
        *
        * @return None
        *
        """
        self.hwd.close()
        self.hwd = None

    def get_idntification( self ):
        """
        @fn Gets device information 
        
        @return device innformation as '<Manufacturer>, <Model>, <Serial Number>, <Firmware Level>, <Options>'
        
        """
        return self.hwd.ask("*IDN?")

    def _get_esr( self ):
        """
        @fn     Gets event status register status 
        @brief  Read the contents of the standard event status register. Reading the standard event status register clears the register.

        @return esr status as boolean, true for ok, false for all the rest 
        
        """

        esr = int(self.hwd.ask("*ESR?"))
        if esr == 1:
            return True
        else:
            log.error("_get_event_status_register return {}".format( esr) )
            return False
        
    def  _set_operation_complete( self ):
        """
        @fn     _set_operation_complete
        @brief  Set and clear operation copmlete flag 

        @return esr status as boolean, true for ok, false for all the rest 
        
        """
        self.hwd.write("*OPC")

    def  _get_operation_complete( self ):
        return int(self.hwd.ask("*OPC?"))

    def _wait_operation_complete( self, timeout_sec = DEFAULT_TIMEOUT ):

        if (timeout_sec != DEFAULT_TIMEOUT ):
            self.hwd.timeout = timeout_sec

        try:
            if ( self._get_operation_complete() == 1 ):
                return True
        except Exception as e:
            raise globals.Error( e.message )      
        else: 
            return False     
        finally:
            self.hwd.timeout = DEFAULT_TIMEOUT
  
    def _read_err_status(self):
        rc = self.hwd.ask('SYST:ERR:NEXT?')
        if ( int(rc.split(',')[0]) != 0 ):
            raise globals.Error( "Opreation failed, error : {}, Description : {}".format( rc.split(',')[0], rc.split(',')[1] ) )

    def _check_err(self):
        if ( self._get_esr() != 0 ):
            self._read_err_status()
   
    @property
    def tx_power(self):
        """ """
        return self.hwd.write("SOURce:POWer?")

    @tx_power.setter
    def tx_power(self, value):
        if ( (value >= -165.0) and (value <= -65.0) ): 
            self.hwd.write("SOURce:POWer {}".format( value ) )
        else:
            raise globals.Error("value : {} is out of range [-165.0, -65.0]".format( value)  )
    
    def get_current_scenario(self):
        return self.hwd.write("SOURce:SCENario:LOAD?")

    def load_scenario(self, scenario_name):
        self.hwd.write("SOUR:SCEN:LOAD {}.scen".format( scenario_name ) )
        if ( self._wait_operation_complete() != True):
            raise globals.Error( "Faild to load scenario")
        self._check_err()

    def _wait_for_scenario_state ( self, state, time_out = 120):
        start_time = time.time()
        str = ''
        while (time.time() - start_time) < 120.0:
            try:
                str = self.hwd.ask("SOURce:SCENario:CONTrol?")
            except:
                pass
            if str == state:
                return True
            time.sleep(0.2)

        return False

    def start_scenario( self ):
        # Stop any current scenatio 
        str = self.hwd.ask("SOURce:SCENario:CONTrol?")
        if ( str != 'STOP' ):
            self.stop_scenario()

        self._wait_for_scenario_state( 'STOP' , 20 )

        self.hwd.write("SOURce:SCENario:CONTrol {}".format( 'START' ) )
        if ( self._wait_for_scenario_state( 'START' ) == False ):
            raise globals.Error("Failed to start GPS simulator scenario")

    def get_scenario_state (self):
        return self.hwd.ask("SOURce:SCENario:CONTrol?")
        #START, STOP, HOLD, WAIT, ARMED or ARMING


    def stop_scenario( self ):
        self.hwd.write("SOURce:SCENario:CONTrol {}".format( 'STOP' ) )
        time.sleep(0.1)
        if ( self._wait_for_scenario_state( 'STOP' ) == False ):
            raise globals.Error("Failed to stop GPS simulator scenario")

    def hold_scenario( self ):
        self.hwd.write("SOURce:SCENario:CONTrol {}".format( 'HOLD' ) )
        if ( self._wait_operation_complete() != True):
            raise globals.Error( "Faild to stop scenario")
        self._check_err()

    def get_current_position(self):
        return self.hwd.ask("SOURce:SCENario:LOG?")

    def _log_to_file( self ):
        pass

    def start_record( self, file_path ):
        """ Start main GPS simulator recording thread """
        self._fh = open( file_path, 'w' )
        self._recorder = Recorder( self.hwd, self._fh )
        try:		
            self._recorder.start()
            while not self._recorder.isAlive():
                common.usleep(1000)
        except:
            raise globals.Error("Faild to active the gps thread")

    def stop_record( self ):
        """ Stop recording session """
        
        
        try:
            self._recorder.shutdown()
            self._recorder.terminate()
        except:
            pass
        while not self._recorder.isAlive():
            time.sleep(0.1)
        self._recorder.join()
        self._fh.close()

    def _calc_checksum(self,s):
        sum = 0
        for c in s:
            sum += ord(c)
        sum &= 0xff
        sum = -sum
        return sum

    def create_scenario(self):
        s = "SOURce:FILe:TYPe SCEN"
        s = "SOURce:FILe:NAMe {}".format( scen_name )
        s = "SOURce:FILe:LENgth {}".foramt ( data_length )
        s = "SOURce:FILe:CHECKsum %d" % ( self._calc_checksum(s) )
        s = "SOURce:FILe:DATA"
        s = "#800000335StartTime 01/06/2009 00:00:00" + \
            "Duration 31 3 46 0" + \
            "NavigationData Default" + \
            "EventData None" + \
            "NumSignals 14" + \
            "Startpos 60.00000000 degN 24.00000000 degE 10.0000 m" + \
            "UserTrajectory Circle" + \
            "TrajectoryParameters 300 10 -1" + \
            "AntennaModel Zero model" + \
            "IonoModel 1" + \
            "TropoModel Saastamoinen" + \
            "Temperature 15" + \
            "Pressure 1100" + \
            "Humidity 50" + \
            "MinElev 0" + \
            "NrSBASChannels 2"


class Recorder(threading.Thread):
    """
    @class NavReader
    @brief Data recorder for gps scenario
    @author Shai Shochat
    @version 1.0
    @date	07/05/2013
    """

    def __init__(self, interface, file_hwd = None):
        """ Initilze class with interface and handler callback """
        threading.Thread.__init__(self)
        self._if = interface
        self._finished = threading.Event()
        self._file_hwd = file_hwd
 
    def __del__( self ):
        self._if = None

    def run(self):
        """ Thread start point """
        self.read_data_loop()

    def shutdown(self):
        """Stop this thread"""
        self._finished.set()

    def read_data_loop(self):	
        """ Main thread loop function retreive data from target """
        start_time = time.time()
        # verify session has started first
        while 1:
            # silent any exceptions
            if self._finished.is_set(): return
            try:
                str = self._if.ask("SOURce:SCENario:CONTrol?")
            except:
                pass
            if str == 'START':
                break
            # Wait max 60 Sec till session will start, otherwise exit with error
            if (time.time() - start_time) > 60.0:
                return (-1) 
            time.sleep(0.5)
        
            
        start_time = time.time()
        self._last_msg = ''
        while 1:
            if self._finished.is_set(): return
            str = ''
            try:
                str = self._if.ask("SOURce:SCENario:LOG?")
            except:
                str = ''

            if str == '':
                continue

            # data arrived, start new clock       
            start_time = time.time()
            #print "data arrived : %s" % str
            if not self._file_hwd is None:
                if not (self._last_msg == str):
                    #new_data = str.split(',')
                    #new_data.insert(1, utilities.timestamp() )
                    #self._file_hwd.write( ','.join(new_data) )

                    # This is some spectracom issue which is concat to messeges
                    self._file_hwd.write( str + '\n') 
                 
                self._last_msg = str
            # Sleep and release resources for 1 mSec
            time.sleep(0.5)

def usage_example():
    # Create simulator instance 
    gps_sim = SPECTRACOM_GSG_6( "10.10.1.50" )
    # set general tx power
    #gps_sim.tx_power = -91.5
    # load scenario
    #gps_sim.load_scenario('Neter2Eilat')

   
    gps_sim.start_scenario()
   
    #gps_sim.start_record( 'c:\\temp\\neter2eilat_recording.txt') 

    start_time = time.time()
    while ( (time.time() - start_time) < 60.0):
        pass
    #for i in range(0,100):
    #    print gps_sim.get_current_position()
    gps_sim.stop_record()

    gps_sim.stop_scenario()
    gps_sim = None
            
                
if __name__ == "__main__":
    usage_example()


 



