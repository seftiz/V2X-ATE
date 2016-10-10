from lib import globals, setup_consts, interfaces
from tests import common
from utilities import utils
from lib.instruments import power_control
import time, logging, traceback
from time import ctime
import numpy as np
import pandas as pd
import os

log = logging.getLogger(__name__)


class AnalyzeTestsResults(common.ParametrizedTestCase):
    """
    Class: AnalyzeTestsResults
    Brief: Get tests results and analyze tests statistics, build statistic tables, output: report file
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """

    def __init__(self, methodName = 'runTest', param = None):
        super(AnalyzeTestsResults, self).__init__(methodName, param)

    def setUp(self):
        # Verify uut input exists and active
        self._uut_id = self.param.get('uut_id', None )
        if self._uut_id is None:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")

    def tearDown(self):
        self.uut.close_fw_cli()

    def initialization(self):
        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self._uut_id[0])
            self.uut.create_fw_cli()                                # create cli connection for (23,1123,terminal)
            self.fw_cli = self.uut.fw_cli('23')                     # get cli from telnet port 23
            self.uboot = self.uut.fw_cli('terminal').u_boot
            self.consts = setup_consts.CONSTS[globals.setup.station_parameters.station_name]
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or currpted, usage : uut_id=(0,1)")


    def test_results_analyze(self):
        log.info("Start analysing")

        # Test initialization
        self.initialization()              

        results_collect = {} # report results dictionary
        print >> self.result._original_stdout, "\nAnalysing for .."

        # Sorting groups by parameter key dictionary, extracted from the collected results
        """
        parameter_sort_group = { "TxPower_dBm" : self.param["tx_results"],
                                 "TxEvm_dB" : self.param["tx_results"],
                                 "Tx_IqImb_Ampl_dB" : self.param["tx_results"],
                                 "Tx_IqImb_Phase_Deg" : self.param["tx_results"],
                                 "Tx_Freq_Err_kHz" : self.param["tx_results"],
                                 "Tx_Symb_Clk_Err_ppm" : self.param["tx_results"],
                                 "Sensitivity_dB" : self.param["sens_results"] }
        """
        parameter_sort_group = { "TxEvm_dB" : self.param["tx_results"] }
        
        # Agregate and parse by max.min.mean value
        
        for key_param, file_name in parameter_sort_group.iteritems():
            if os.path.exists(file_name):
                data_to_analyze = pd.read_csv(file_name)

                #grouped_measured_param = data_to_analyze.groupby( ["Temperature", "Channel", "Rate_Mbps"] )[ key_param ]
                grouped_measured_param = data_to_analyze.groupby( ["Channel"] )[ key_param ]
                data_to_out = grouped_measured_param.aggregate( { 'min': np.min,
                                                                   'max': np.max,
                                                                   'average': np.mean } )

                out = os.path.dirname( os.path.abspath( file_name ) ) + '\out_results_analyze.csv'
                # Write the aggregated results to csv file
                with open(out, 'a') as out_file:
                    utils.print_and_log(out_file, "Grouped by: " + key_param)
                    data_to_out.to_csv(out_file)
        
        log.info("Test finished ")