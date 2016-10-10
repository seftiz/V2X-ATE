

import sys
import types
import os
import json
import logging 


from uuts import common
from lib import instruments_manager
from lib import uut
from lib import utilities

log = logging.getLogger(__name__)

class StationParameters(object):

    def __init__(self, cfg_data):
        self.log_dir = ""
        self.reports_dir = ""
        self.station_name = "" 
        self.load_params( cfg_data )

    def load_params(self, cfg_data ):

        try:    
            station_params = cfg_data["StationParamerters"]
        except NameError, err:
            raise Exception("Failed to retrieve units from configuration file")


        self.reports_dir = utilities.get_value(  station_params , 'reports_dir')
        self.log_dir = utilities.get_value(  station_params , 'log_dir')
        try:
            self.station_name =  utilities.get_value( station_params, 'station_name' )
        except Exception:
            pass



class Setup(object):

    def __init__(self, cfg_data ):
        self.instruments = instruments_manager.Instruments()
        self.units = uut.Units()
        self.json_data = cfg_data
        self.station_parameters = StationParameters( self.json_data )
        
    def __del__(self):
        self.instruments = None
        self.units = None

    def load_setup_configuration_file(self):

        # Load all instruments
        rc = self.instruments.load_instruments_from_cfg_file( self.json_data )

        self.units = uut.Units()
        self.units.load_uuts_from_cfg_file( self.json_data )

if __name__ == "__main__":
    # units = Units()
    cfg_file = "c:\\temp\\configuration.json"
    load_setup_configuration_file ( cfg_file )
    print "finised ok ????"
