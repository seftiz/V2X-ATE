"""
@file instruments_manager.py
@brief pcap to pdml client convertor 
@author    	Shai Shochat
@version	1.0
@date		04/04/2013
"""
import sys, types, socket
import json, logging, traceback
from lib.instruments import packet_sniffer
from lib.instruments import power_control
from lib import packet_analyzer
from lib import globals



#  from atlk import ssh
from lib import uut
# global variables
# from atlk.v2x.common import instruments
from uuts import common

log = logging.getLogger(__name__)

class Serial2Ip(object):

    def __init__(self, id, type, name, ip):
        self.id = id
        self.type = type
        self.name = name
        self.ip = ip


class Instruments(object):

    def __init__(self):
        # initilize all instruments 
        self.sniffer = None
        self.serial_ip = None
        self.power_control = {}
        self.gps_simulator = None
        self.can_bus = None
        self.rf_switch_box = None
        self.rf_vector_signal = {}
        self.temperature_chamber = None
        self.__instruments = { 'Sniffer': self.sniffer, 'PcapConvertServer' : None,
                             'Serial2Ip' : self.serial_ip, 'PowerControl': self.power_control, 'GpsSimulator':self.gps_simulator,
                             'CanBusServer': self.can_bus, 'CanBus' : self.can_bus, 'RfSwitch' : self.rf_switch_box, 'RfVectorSignal' : self.rf_vector_signal, self.temperature_chamber : 'TemperatureChamber' } 

    def __del(self):
        self.sniffer = None
        self.serial_ip = None
        self.power_control = None
        self.can_bus = None
        self.rf_switch_box = None
        self.rf_vector_signal = {}
        self.temperature_chamber = None

    def terminate(self):
        if not self.gps_simulator is None:
            self.gps_simulator.terminate()
            self.gps_simulator = None



    def get_instrument_by_name( self, instrument_name ):
        try:
            return self.__instruments[instrument_name]
        except KeyError:
            return None

        
    def load_instruments_from_cfg_file(self, cfg_data ):
        """ Load all setup configuration from JSON configuration file """

        local_ip = socket.gethostbyname(socket.gethostname())
        try:    
            instruments = cfg_data["Instruments"]
        except Nameglobals.Error, err:
            raise Exception("Failed to retrieve instruments from configuration file")
        
        for instrument in instruments:
            print "instrument is %s" % instrument
            if instrument in 'Sniffer':
                # sniffer = str_to_class("packet_sniffer", instrument + instruments[instrument]['type'])( instruments[instrument]['ip'] )
                if  instruments[instrument]['active'] == 1:
                    try:
                        print "Please wait, Loading Sniffer %s, user %s and pwd %s" % ( instruments[instrument]['ip'], instruments[instrument]['user'], instruments[instrument]['pwd'] ) 
                        self.sniffer = packet_sniffer.Sniffer( instruments[instrument]['type'], instruments[instrument]['ip'],instruments[instrument]['interface'], instruments[instrument]['user'], instruments[instrument]['pwd'] )
                        # self.sniffer.initialize()
                    except Exception as e:
                         raise globals.Error("Unable to Connect %s at %s, user %s and pwd %s" % (instrument, instruments[instrument]['ip'], instruments[instrument]['user'], instruments[instrument]['pwd']))
                
            elif instrument in 'Serial2Ip':
                if  instruments[instrument]['active'] == 1:
                    self.serial_ip = Serial2Ip( instruments[instrument]['id'] , instruments[instrument]['type'],
                                                instruments[instrument]['name'], instruments[instrument]['ip'] )

            elif instrument in 'PowerControl':

                if  instruments[instrument]['active'] == 1:
                    try:
                        self.power_control[ instruments[instrument]['id'] ] = power_control.powerSwitch( instruments[instrument]['name'], instruments[instrument]['ip'], instruments[instrument]['user'], instruments[instrument]['pwd'], instruments[instrument]['prompt'])
                        # self.power_control.initilize()
                    except Exception as e:
                        raise globals.Error("Unable to Connect %s at %s, user %s and pwd %s" % (instrument, instruments[instrument]['ip'], instruments[instrument]['user'], instruments[instrument]['pwd']))

            elif instrument in 'GpsSimulator':
                if  instruments[instrument]['active'] == 1:
                    from lib import gps_simulator
                    try:
                        self.gps_simulator = gps_simulator.GpsSimulator( instruments[instrument]['type'], instruments[instrument]['addr'] )
                    except Exception as e:
                        raise globals.Error("Unable to Connect gps type {} at {}\r\n{}".format( instruments[instrument]['type'], instruments[instrument]['addr'], e ) )

            elif instrument in 'PcapConvertServer':
                if  instruments[instrument]['active'] == 1:
                    try:
                        # Check if Packet analyzer server located in local computer if yes then run local server
                        ins_ip = instruments[instrument]['ip'].encode()                                         
                        self.pcap_convertor = packet_analyzer.PcapConvertor( ins_ip, instruments[instrument]['port'] )

                    except Exception as e:
                        raise globals.Error("Unable to Connect %s at %s" % (instrument,ins_ip ) )

            elif instrument in 'RfSwitch':
                # Connect to rf switches
                if  instruments[instrument]['active'] == 1:
                    from lib.instruments import rf_switch

                    try:
                        self.rf_switch_box = rf_switch.select_type( instruments[instrument]['type'] )
                    except Exception as e:
                        raise globals.Error("Unable to Connect RF switch")

            elif instrument in 'RfVectorSignal':
                for i in range(0, len(instruments[instrument])):

                    from lib.instruments.Vector_Signal import rf_vector_signal

                    if  instruments[instrument][i]['active'] != 1:
                        continue
                    try:
                        ins_id = instruments[instrument][i]['id']
                        ins_maker = instruments[instrument][i]['maker']
                        ins_ip = instruments[instrument][i]['ip']
                        for type in instruments[instrument][i]['type'].itervalues():
                            self.rf_vector_signal.update({ str(type): rf_vector_signal.vectorSignal( str(ins_maker), str(type), str(ins_ip) ) })
                        # Access first element in dictionary of instuments types
                        self.rf_vector_signal.itervalues().next().connect()      
                    except Exception as e:
                        traceback.print_exc()
                        raise globals.Error("Unable to Connect %s at %s" % (instrument,ins_ip ) )

            elif instrument in 'TemperatureChamber':
                # Connect to Temperature chamber
                if  instruments[instrument]['active'] == 1:
                    from lib.instruments.TempChamberControl import temperature_chamber
                    try:
                        self.temperature_chamber = temperature_chamber.select_type( instruments[instrument]['type'], instruments[instrument]['port'] )
                    except Exception as e:
                        raise globals.Error("Unable to Connect RF switch")

            elif instrument in 'CanBusServer':
                if  instruments[instrument]['active'] == 1:
                    raise globals.Error("CanbusServer parameter in configuration file changed, please consult admin")
            elif instrument in 'CanBusSimulator':
                if  instruments[instrument]['active'] == 1:
                    try:

                        from lib import canbus_manager
                                                                          
                        self.can_bus = canbus_manager.canBusDevicesTypes[instruments[instrument]['type']]()
                        # Convert port list string to python list
                        port_list = eval(instruments[instrument]['port'])
                        # Prepare device
                        self.can_bus.open_device( port_list )

                    except Exception as e:
                        raise globals.Error("Failed to set can bus server device, please review configuraiton\r\n{}".format(e) )

            else:
                raise globals.Error("Instrument %s type %s is unknown for system" % (instrument, instruments[instrument]['type']))


    def terminate_intstruments():

        if not self.can_bus is None:
            self.can_bus.device_close()
