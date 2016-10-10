"""
@file packet_sniffer.py
@brief Packet Sniffers 

controler
@author    	Shai Shochat
@version	1.0
@date		18/01/2013
"""
from uuts import common
from uuts import interface
import os
import time
import logging
import telnetlib
import socket
import urllib


log = logging.getLogger(__name__)


class NetworkPowerSwitch(object):
    """
    ##################  TBD ##################
    @class PowerControl
    @brief PowerControl Implementation for ATE
    @author Shai Shochat
    @version 0.1
    @date	10/02/2013
    """

    def __init__(self, type = 'NPS'):
        pass
    def __del__(self):
        pass
    def power_up(self, outlet): 
        raise NotImplementedError('power_up')
    def power_down(self, outlet):
        raise NotImplementedError('power_down')
    def reboot(self, outlet):
        raise NotImplementedError('reboot')
 



class DigiPower(NetworkPowerSwitch):
    """
    @class NetworkPowerControl
    @brief Network Power Switch v3.00 
    @author Shai Shochat
    @version 0.1
    @date	06/05/2015
    """

    def __init__(self, host , user = "snmp", pwd = "1234", prompt = None):
        self._num_outlets = 8
        self._num_leds = 22
        self.host = host
        self.user = user
        self.pwd = pwd
        self.prompt = prompt
        self.user_pwd = "{}:{}".format( self.user, self.pwd)

    def _verify_outlet(self, outlet):
        if not (0 <= outlet <= self._num_outlets - 1):
            raise ValueError('Outlet number %d is not in [0, %d]' % ( outlet, self._num_outlets-1))
   

    def power_up(self, outlet): 
        
        self._verify_outlet(outlet)
        cmd = 'http://%s@%s/on.cgi?led=%s' % ( self.user_pwd, self.host, ('0' * outlet + '1').ljust( self._num_leds, '0') )
        urllib.urlopen(cmd).close()  

    def power_down(self, outlet):
        self._verify_outlet(outlet)
        cmd = 'http://%s@%s/off.cgi?led=%s' % ( self.user_pwd, self.host, ('0' * outlet + '1').ljust( self._num_leds, '0') )
        urllib.urlopen(cmd).close()  

    def reboot(self, outlet):
        self._verify_outlet(outlet)
        cmd = 'http://%s@%s/offon.cgi?led=%s' % ( self.user_pwd, self.host, ('0' * outlet + '1').ljust( self._num_leds, '0') )
        urllib.urlopen(cmd).close()  

   


class WTI(NetworkPowerSwitch):
    """
    @class NetworkPowerControl
    @brief Network Power Switch v3.00 
    @author Shai Shochat
    @version 0.1
    @date	10/02/2013
    """

    def __init__(self, ip , user = "", pwd = "", prompt = "NPS>"):
        self.ip = ip
        self._if = None
        self.user = user
        self.pwd = pwd
        self.prompt = prompt
        self._initialize = False

    def __del__(self):
        self._if = None


    def initialize(self):
        """ initialize sniffer computer, load need drivers """
        if self._initialize:
            return 0

    def _connect_and_set(self, cmd, connector):

        self._if = interface.QaCliInterface()
        self._if.prompt = self.prompt

        rc = self._if.connect( self.ip, 23 , common.DEFAULT_TIMEOUT, retries = 3 )
        # self._if.read_until_prompt()
        log.info("Setting plug %d to mode %s", str(connector) , cmd )
        self._if.send_command(  "/%s %s" % ( cmd, str(connector) )  , True )
        time.sleep(0.1)
        self._if.send_command( "/x" ,  False )
        self._if.close()
        self._if = None
        log.info('Disconnected from power switch %s',  self.ip)

        return 0

    def power_up(self, connector):
        """ Set power up on connector
        @param[in] Connector Idx as formated by device
        """
        return self._connect_and_set( "On", connector )

    def power_down(self, connector):
        """ Set power down on connector
        @param[in] Connector Idx as formated by device
        """
        return self._connect_and_set( "Off", connector )

    def reboot(self, connector):
        return self._connect_and_set( "boot", connector )



powerSwitchTypes = {'nps01': WTI, 'nps02' : DigiPower }

def powerSwitch(type, host , user = "", pwd = "", prompt = ""):
    return powerSwitchTypes[type](host, user, pwd, prompt)


