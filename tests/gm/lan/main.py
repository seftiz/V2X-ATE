from __future__ import division

import serial
import sys

from gm_common import *

import time
import logging
import gmlan_tester
from array import array

################################################################
# Logging stuff, TBD: changedto the system testing log mechanism
################################################################
uart_logger = logging.getLogger(UART_LOGGER_NAME)
uart_logger.setLevel(logging.DEBUG)
# create file handler which logs even debug messages
fh = logging.FileHandler(UART_LOGGER_FILE)
fh.setLevel(logging.DEBUG)
# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
fh.setFormatter(formatter)
# add the handlers to logger
uart_logger.addHandler(ch)
uart_logger.addHandler(fh)

def main():
    try:
        lan_tester = gmlan_tester.GmLanTester(test_type = GM_FUNCTIONAL_TEST,
                                              max_monitored_messages = 3,
                                              com_port = "COM3",
                                              sanity_test_duration = 50,
                                              uart_rx_timeout = 30)
        lan_tester.start_gmlan_test()
    except Exception as e:
        uart_logger.error("GMLAN Tester error: {0}".format(e))

main()
