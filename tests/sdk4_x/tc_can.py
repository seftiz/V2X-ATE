"""
@file       tc_can.py
@brief      Test suite for testing can bus transmitting and receiving frames  
@author    	Neta-ly Rahamim
@version	1.0
@date		December 2014
"""
import os, sys, socket


# Get current main file path and add to all searchings
if __name__ == "__main__":

    dirname, filename = os.path.split(os.path.abspath(__file__))
    sys.path.append("c:\\temp\\qa")


import unittest, logging, socket, json, json2html
from datetime import datetime
import time, threading, random
from lib import globals, station_setup, HTMLTestRunner
from lib import instruments_manager, packet_analyzer
from lib import canbus_manager as canbus
from tests import common
# import lib.instruments.Komodo.komodo_if as komodo_if
import webbrowser, re

log = logging.getLogger(__name__)

CAN_DATA_FILE_NAME = "c:\\temp\can_data_file.txt"


class TC_CAN_API(common.V2X_SDKBaseTest):
    """
    @class TC_CAN_API
    @brief Test the CAN API
    @author Neta-ly Rahamim
    @version 0.2
    @date	09/02/2015
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.can_cli = None
        self.can_sim = None
        self.stats = Statistics()
        self._can_frames_list = []
        self._frames_num = 0
        self.uut_can_if = []

        super(TC_CAN_API, self).__init__(methodName, param)
        

    def get_test_parameters( self ):
        super(TC_CAN_API, self).get_test_parameters()
        
        # Get uut index and CAN interface index
        self.uut_id = self.param.get('uut_id', None )
        if self.uut_id is None:
            raise globals.Error("uut index and can interface id input is missing or corrupted, usage : uut_id=(0,1)")

        print "Test parameters for %s :" % self.__class__.__name__

        if len(self.uut_id) == 2:
            print "{} = {}\t\t{} = {}".format ("uut_id", self.uut_id[0], "can device_id", self.uut_id[1])
        else:
            print "{} = {}\t\t{} = {}\t\t{} = {}".format ("uut_id", self.uut_id[0], "can device_id", self.uut_id[1], "can device2_id", self.uut_id[2])


 
    def runTest(self):
        pass


    def setUp(self):
        super(TC_CAN_API, self).setUp()


    def tearDown(self):
        super(TC_CAN_API, self).tearDown()

        # Close unit can service
        if not self.can_cli is None:
            self.can_cli.can.socket_delete()
            self.can_cli.can.service_delete()
            self.uut.close_qa_cli("can_cli")
            self.can_cli = None

        # Close can simulator
        if not self.can_sim is None:
            #self.can_sim.power_down(self.uut_can_if[0].sim_port)
            #self.can_sim.close_port(self.uut_can_if[0].sim_port)
            self.can_sim.channel_close( self.uut_can_if[0].sim_port )

    def test_can(self):

        self.log = logging.getLogger(__name__)
  
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )

        self.get_test_parameters()

        self.unit_configuration()
        self.instruments_initilization()
        self.main()

        #self.debug_override()
        self.analyze_results()
        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )


    def unit_configuration(self):
        self.uut_index = self.uut_id[0]

        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self.uut_index)
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or corrupted, usage : uut_id=(0,1)")

        self.uut_can_if.append(self.uut.can_interfaces[self.uut_id[1]])
        if not self.uut_can_if[0].active:
            raise globals.Error("CAN device {} is not active.".format(self.uut_can_if[0].device_id))

        # Open new v2x-cli
        self.can_cli = self.uut.create_qa_cli("can_cli", target_cpu = self.target_cpu )
        self.can_cli.can.service_create()
        ret = self.can_cli.can.socket_create(self.uut_can_if[0].device_id, {} )
        if "ERROR :" in ret:
            raise globals.Error("Can socket create received error {}".format(ret))

        self.can_cli.can.reset_counters()


    def instruments_initilization(self):
        
        # Receving and start Can bus simulator
        self.can_sim = globals.setup.instruments.can_bus

        if self.can_sim is None:
            raise globals.Error("Can bus simulator is not initailize, please check your configuration")
                           
        #self.can_sim.find_devices() 
        #self.can_sim.configure_port(self.uut_can_if[0].sim_port)
        #self.can_sim.set_timeout(self.uut_can_if[0].sim_port) # set timeout to read can frames
        #self.can_sim.power_up(self.uut_can_if[0].sim_port)

        self.can_sim.channel_open( self.uut_can_if[0].sim_port )


    def main(self):
    
        try:
    
            self._generate_basic_scenario_data()

            for idx, can_frame in enumerate(self._can_frames_list):
                self._test_can_frame(can_frame, can_frame, can_frame, self.can_cli, self.uut_can_if[0].sim_port)

        except Exception as e:
            raise e


    def analyze_results(self):
        pass


    def print_results(self):
        can_counters = self.can_cli.can.read_counters()

        if len(can_counters) == 0:
            can_counters = self.can_cli.can.read_counters()

        print >> self.result._original_stdout, "CAN CLI Counters : {}".format(can_counters)

        if len(can_counters) :
            self.add_limit("CAN CLI Tx to Sim Rx", can_counters['tx'][1], self.stats.can_sim_rx[self.uut_can_if[0].sim_port], self._frames_num, 'EQ')
            self.add_limit("CAN CLI to Sim - Not equal", 0, self.stats.failed_can_cli2sim[self.uut_can_if[0].sim_port], 0 , 'EQ')
            self.add_limit("CAN Sim Tx to CLI Rx", self.stats.can_sim_tx[self.uut_can_if[0].sim_port], can_counters['rx'][1], self._frames_num, 'EQ')
            self.add_limit("CAN Sim 2 CLI - Not equal", 0, self.stats.failed_can_sim2cli[self.uut_can_if[0].sim_port], 0 , 'EQ')


    # Transmit and receive the frame and compare it to expected result
    def _test_can_frame(self, can_frame, expected_frame1, expected_frame2, cli, sim_port):
        
        self._frames_num += 1 
        sim_rx_frame = None

        # CAN CLI transmit
        data_str = "".join(("%0.2x" % x) for x in can_frame.data)
        log.info("TC_CAN_API: Can tx frame - {}".format(can_frame))
        ret = cli.can.transmit(can_id = can_frame.can_id_and_flags , can_data = data_str, data_size = can_frame.dlc)

        if "ERROR : can_send:" in ret:
            log.debug("TC_CAM_API: Can tx frame received error")
            sim_rx_frame = globals.canBusFrame( 0, 0, [] )

        else:
            # CAN simulator receive
            try :
                # sim_rx_frame = self.can_sim.get_frame(sim_port, 10)
                sim_rx_frame = self.can_sim.receive( sim_port )
            except Exception as e:
                log.error("TC_CAN_API: Simulator rx failed, {}".format(e))

            self.stats.can_sim_rx[sim_port] += 1

            if ( (sim_rx_frame is None)  or (isinstance(sim_rx_frame, str)) ):
                # sim_rx_frame = CanFrameAT((sim_rx_frame["can_id"], sim_rx_frame["ide_f"], sim_rx_frame["rtr_f"]), sim_rx_frame["dlc"], sim_rx_frame["data"])
                sim_rx_frame = globals.canBusFrame( 0, 0, [] )

            log.debug("TC_CAN_API: Simulator received - {}".format(sim_rx_frame) )

        try:
            is_equal = (expected_frame1 == sim_rx_frame)
        except Exception as e:
            is_equal = False

        log.info("TC_CAN_API: canbus tx == simulator rx - {}".format(is_equal) )
        if not is_equal:
            log.error('Failed can cli tx --> simulator rx: id={0} dlc={1}'.format(sim_rx_frame.can_id, sim_rx_frame.dlc) )
            self.stats.failed_can_cli2sim[sim_port] += 1


        # CAN Simulator transmit
        #self.can_sim.send_frame(sim_port, can_frame)
        self.can_sim.transmit(sim_port, can_frame )

        log.info("Can Simulator transmit frame : {}".format(can_frame))
        self.stats.can_sim_tx[sim_port] += 1

        # CAN CLI receive
        rx_id, rx_dlc, rx_data = cli.can.receive(frames = 1, print_frame = 1)
        can_frame_rx = globals.canBusFrame( rx_id, rx_dlc, rx_data )
        #CanFrameAT(rx_id, rx_dlc, rx_data)
        log.debug("TC_CAN_API: Canbus received - {}".format(can_frame_rx))

        is_equal = (expected_frame2 == can_frame_rx)

        log.info("TC_CAN_API: simulator tx == canbus rx - {}".format( is_equal) )
        if not is_equal:
            log.error('Failed simulator tx --> can cli rx: id={0} dlc={1}'.format( can_frame_rx.can_id, can_frame_rx.dlc))
            self.stats.failed_can_sim2cli[sim_port] += 1


    def _create_random_can_data(self, can_data_len):
        return [  random.randint(1,0xFF)  for i in xrange(can_data_len) ] 


    def _create_random_can_id(self, extended):

        if extended:
            can_id = ( random.randint( 0, (pow(2, globals.EXTENDED_CAN_ID_LEN-2) ) ) | globals.CAN_ID_IDE_FLAG )
        else:
            can_id = random.randint(0 , pow(2, globals.STANDARD_CAN_ID_LEN) )
            
        return can_id


    def _generate_basic_scenario_data(self):
        # can_id = 0x0c1, ide = 0, rtr = 0, dlc = 8, data = [0x93, 0xFD, 0x07, 0xD0, 0x90, 0x2C, 0xDF, 0x40])
        self._can_frames_list[:] = []

        # Generate standard and extended data frames with different length of data
        for is_extended in [False, True]:
            for dlc in range(9):
                # Generate random frame id and data
                can_id = self._create_random_can_id( is_extended )
                can_data = self._create_random_can_data( dlc )
                self._can_frames_list.append( globals.canBusFrame( can_id, dlc, can_data ) )

        # Generate extended data frame with CAN ID less than 11 bits.
        can_id = self._create_random_can_id(False)
        can_data = self._create_random_can_data(8)
        self._can_frames_list.append( globals.canBusFrame(can_id, 8, can_data, flags = globals.CAN_ID_IDE_FLAG ) )

        # Generate Remote frames
        can_id = self._create_random_can_id( False )
        self._can_frames_list.append( globals.canBusFrame( can_id, 8, [0]*8, flags = globals.CAN_ID_RTR_FLAG) )

        can_id = self._create_random_can_id( True )
        self._can_frames_list.append( globals.canBusFrame( can_id, 0, [], flags = (globals.CAN_ID_RTR_FLAG | globals.CAN_ID_IDE_FLAG) ) )

############ END Class TC_CAN_API ############


class TC_CAN_2DEVICES(TC_CAN_API):
    """
    @class TC_CAN_2DEVICES
    @brief Basic tests for CAN API
    @author Neta-ly Rahamim
    @version 0.1
    @date	09/02/2015
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.can_cli2 = None

        super(TC_CAN_2DEVICES, self).__init__(methodName, param)

    
    def tearDown(self):
        # Close unit can socket (service will be closed in the TC_CAN_API tearDown)
        if not self.can_cli2 is None:
            self.can_cli2.can.socket_delete()
            self.uut.close_qa_cli("can_cli2")
            self.can_cli2 = None
                

        # Close can simulator
        if not self.can_sim is None:
            self.can_sim.channel_close( self.uut.can_interfaces[1].sim_port )
            #self.can_sim.power_down(self.uut.can_interfaces[1].sim_port)
            #self.can_sim.close_port(self.uut.can_interfaces[1].sim_port)
 
        super(TC_CAN_2DEVICES, self).tearDown()

    def unit_configuration(self):
        super(TC_CAN_2DEVICES, self).unit_configuration()

        self.uut_can_if.append(self.uut.can_interfaces[self.uut_id[2]])
        if not self.uut_can_if[1].active:
            raise globals.Error("CAN device {} is not active.".format(self.uut_can_if[1].device_id))

        self.can_cli2 = self.uut.create_qa_cli("can_cli2",  target_cpu = self.target_cpu )
        ret = self.can_cli2.can.socket_create(self.uut_can_if[1].device_id, {} )
        if "ERROR :" in ret:
            raise globals.Error("Can socket create received error {}".format(ret))

        self.can_cli2.can.reset_counters()


    def instruments_initilization(self):
        super(TC_CAN_2DEVICES, self).instruments_initilization()
        
        #self.can_sim.configure_port(self.uut_can_if[1].sim_port)
        #self.can_sim.set_timeout(self.uut_can_if[1].sim_port) # set timeout to read can frames
        #self.can_sim.power_up(self.uut_can_if[1].sim_port)
        self.can_sim.channel_open( self.uut_can_if[1].sim_port )

    def main(self):
        try:
            self._errors = []

            self._generate_basic_scenario_data()

            for can_frame in self._can_frames_list:
                self._test_can_frame(can_frame, can_frame, can_frame, self.can_cli, self.uut_can_if[0].sim_port)
                self._test_can_frame(can_frame, can_frame, can_frame, self.can_cli2, self.uut_can_if[1].sim_port)

            if len(self._errors):
                log.debug("TC_CAN_API - Test errors :")
                for error in self._errors:
                    log.debug(error)

        except Exception as e:
            raise e


    def print_results(self):
        can_counters = self.can_cli.can.read_counters()
        can2_counters = self.can_cli2.can.read_counters()

        if len(can_counters) :
            self.add_limit("CAN CLI Tx to Sim Rx", can_counters['tx'][1], self.stats.can_sim_rx[self.uut_can_if[0].sim_port], self._frames_num, 'EQ')
            self.add_limit("CAN CLI to Sim - Not equal", 0, self.stats.failed_can_cli2sim[self.uut_can_if[0].sim_port], 0 , 'EQ')
            self.add_limit("CAN Sim Tx to CLI Rx", self.stats.can_sim_tx[self.uut_can_if[0].sim_port], can_counters['rx'][1], self._frames_num, 'EQ')
            self.add_limit("CAN Sim 2 CLI - Not equal", 0, self.stats.failed_can_sim2cli[self.uut_can_if[0].sim_port], 0 , 'EQ')

        if len(can2_counters) :
            self.add_limit("Second CAN CLI Tx to Sim Rx", can2_counters['tx'][1], self.stats.can_sim_rx[self.uut_can_if[1].sim_port], self._frames_num, 'EQ')
            self.add_limit("Second CAN CLI to Sim - Not equal", 0, self.stats.failed_can_cli2sim[self.uut_can_if[1].sim_port], 0 , 'EQ')
            self.add_limit("Second CAN Sim Tx to CLI Rx", self.stats.can_sim_tx[self.uut_can_if[1].sim_port], can2_counters['rx'][1], self._frames_num, 'EQ')
            self.add_limit("Second CAN Sim 2 CLI - Not equal", 0, self.stats.failed_can_sim2cli[self.uut_can_if[1].sim_port], 0 , 'EQ')


############ END Class TC_CAN_2DEVICES ############


class TC_CAN_ERRONEOUS(TC_CAN_API):
    """
    @class TC_CAN_ERRONEOUS
    @brief Test the CAN API
    @author Neta-ly Rahamim
    @version 0.1
    @date	09/02/2015
    """

    def main(self):
        try:
            self._errors = []

            # Generate CAN ID more than 11 bits and extended format bit off
            can_id = self._create_random_can_id( True )
            can_data = self._create_random_can_data( 8 )

            can_frame = globals.canBusFrame( can_id, 8, can_data)
            can_frame.ide_f = False
            can_frame.can_id_and_flags = can_id & globals.STANDARD_CAN_ID_MASK
            expected_frame = globals.canBusFrame( can_id & globals.STANDARD_CAN_ID_MASK, 8, can_data)
            self._test_can_frame( can_frame, None, expected_frame, self.can_cli, self.uut_can_if[0].sim_port)


            # Generate Data frame with data not empty and remote bit on
            can_id = self._create_random_can_id( False )
            can_data = self._create_random_can_data( 8 )

            can_frame = globals.canBusFrame( can_id, 8, can_data, flags = globals.CAN_ID_RTR_FLAG )
            expected_frame = globals.canBusFrame( can_id, 8,[] , flags = globals.CAN_ID_RTR_FLAG )
            self._test_can_frame(can_frame, expected_frame, expected_frame, self.can_cli, self.uut_can_if[0].sim_port)

            # Generate frame with data length code and actual data size not equal
            can_id = self._create_random_can_id(False)
            can_data = self._create_random_can_data(8)
            can_frame = globals.canBusFrame( can_id, 4, can_data)
            expected_frame = globals.canBusFrame( can_id, 4, can_data[0:4] )

            self._test_can_frame(can_frame, expected_frame, expected_frame, self.can_cli, self.uut_can_if[0].sim_port)

            can_id = self._create_random_can_id(False)
            can_data = self._create_random_can_data(4)
            can_frame = globals.canBusFrame( can_id, 8, can_data)
            komodo_expected_frame = globals.canBusFrame( can_id, 4, can_data[0:4] )
            ################ TO CHECK ###############
            self._test_can_frame(can_frame, can_frame, komodo_expected_frame, self.can_cli, self.uut_can_if[0].sim_port)


            # This Test is useless in vector mode, since vector is not allowing this status.
            # Generate Data frame with data length code < 0
            # can_id = self._create_random_can_id(False)
            # can_frame = globals.canBusFrame( can_id, -2, [] )
            # komodo_expected_frame = globals.canBusFrame( can_id, 0, [])
            # self._test_can_frame(can_frame, None, komodo_expected_frame, self.can_cli, self.uut_can_if[0].sim_port)

            # Generate Data frame with data and data length code > 8
            can_id = self._create_random_can_id( False )
            can_data = self._create_random_can_data(10)
            can_frame = globals.canBusFrame( can_id, 10, can_data)
            expected_frame = globals.canBusFrame( can_id, 8, can_data[0:8] )
            self._test_can_frame(can_frame, None, expected_frame, self.can_cli, self.uut_can_if[0].sim_port)

            if len(self._errors):
                log.debug("TC_CAN_API - Test errors :")
                for error in self._errors:
                    log.debug(error)

        except Exception as e:
            raise e


############ END Class TC_CAN_ERRONEOUS ############


class TC_CAN_LOAD(TC_CAN_API):
    """
    @class TC_CAN_LOAD
    @brief Load tests on the CAN API
    @author Neta-ly Rahamim
    @version 0.1
    @date	08/02/2015
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.can_cli_rx = None
        # self.lock = threading.Lock()

        super(TC_CAN_LOAD, self).__init__(methodName, param)

    def get_test_parameters( self ):
        super(TC_CAN_LOAD, self).get_test_parameters()
        
        self.dut_tx_rate_hz = self.param.get('frames_rate', 500 )
        self.sim_tx_rate_hz = self.param.get('sim_frames_rate', 1000 )
        self._frames_num = self.param.get('frames_num', 100000 )
        self._err_part = self.param.get('err_part', 5 )

        print "{} = {}\t\t{} = {}\t\t{} = {}".format ("frames_rate", self.dut_tx_rate_hz, "frames_num", self._frames_num, "err_part", self._err_part)

    def tearDown(self):
        # Close unit can socket (service will be closed in the TC_CAN_API tearDown)
        if not self.can_cli_rx is None:
            self.can_cli_rx.can.socket_delete()
            self.uut.close_qa_cli("can_cli_rx")
            self.can_cli_rx = None

        super(TC_CAN_LOAD, self).tearDown()


    def unit_configuration(self):
        super(TC_CAN_LOAD, self).unit_configuration()

        self.can_cli_rx = self.uut.create_qa_cli("can_cli_rx",  target_cpu = self.target_cpu)
        ret = self.can_cli_rx.can.socket_create(self.uut_can_if[0].device_id, {} )
        if "ERROR :" in ret:
            raise globals.Error("Can socket create received error {}".format(ret))

        self.can_cli_rx.can.reset_counters()


    def main(self):
        try:
            thread_list = []

            self._load_can_data_file( CAN_DATA_FILE_NAME )

            simTxThread = threading.Thread(target=self._sim_tx_frames_thread, args=(self.uut_can_if[0].sim_port, self.sim_tx_rate_hz, ) )
            thread_list.append(simTxThread)

            simRxThread = threading.Thread( target = self._sim_rx_frames_thread, args=( self.uut_can_if[0].sim_port,) )
            thread_list.append(simRxThread)

            # CAN CLI transmit
            
            simRxThread.start()
            while not simRxThread.isAlive():
                time.sleep ( 0.0002 )

            ret = self.can_cli.can.transmit_load(frames = self._frames_num, rate_hz = self.dut_tx_rate_hz, err_part = self._err_part)

            # CAN CLI receive
            self.can_cli_rx.can.receive( frames = len(self._can_frames_list), print_frame = 0, timeout = 10000)
            simTxThread.start()

        except Exception as e:
            raise e
        # finally:
            
        # wait for threads.
        for thread in thread_list:
            thread.join()

        simTxThread.join()
        simRxThread.join()

        a = 100

    def print_results(self):

        tx_can_counters = self.can_cli.can.read_counters()
        rx_can_counters = self.can_cli_rx.can.read_counters()
        rate = self.can_cli_rx.can.read_rx_rate()

        if len(tx_can_counters) :
            limit_str = "CAN CLI Tx to Sim Rx - {}% errors".format(self._err_part)
            # self.add_limit(limit_str, tx_can_counters['tx'][1], self.stats.can_sim_rx[self.uut_can_if[0].sim_port], self._frames_num , 'EQ')
            self.add_limit(limit_str, self._frames_num, self.stats.can_sim_rx[self.uut_can_if[0].sim_port], None, 'EQ')

        if len(rx_can_counters):
            # self.add_limit("CAN Sim Tx to CLI Rx", self.stats.can_sim_tx[self.uut_can_if[0].sim_port], rx_can_counters['rx'][1], len(self._can_frames_list) , 'EQ')
            self.add_limit("CAN Sim Tx to CLI Rx", len(self._can_frames_list), rx_can_counters['rx'][1], None, 'EQ')

        self.add_limit("CAN Rx average rate", 0, rate, 4000 , 'GTLT')


    def _load_can_data_file(self, file_name):
        """ This is the example of canbus data file 
            can_id = 0x0c1, ide = 0, rtr = 0, dlc = 8, data = [0x93, 0xFD, 0x07, 0xD0, 0x90, 0x2C, 0xDF, 0x40]
            can_id = 0x0ffff0c5, ide = 1, rtr = 0, dlc = 8, data = [0x93, 0xB4, 0x1E, 0xE0, 0x53, 0xEC, 0xF0, 0x3C]
        """
        flags = 0
        if not os.path.isfile(file_name) :
            self._generate_can_data_file(file_name, self._frames_num)
            return


        self._can_frames_list[:] = []

        file_hwd = open( file_name, "r")
        for line in file_hwd:
            # split to 5 blocks
            base = line.split(',',4)

            # extract can_id messages value
            can_id = int(base[0].split('=')[1].strip(),16)

            # Extract extended flag value (=ide)
            ide = bool(int(base[1].split('=')[1].strip()))
            if ide:  flags = flags  | globals.CAN_ID_IDE_FLAG


            # Extract remote flag value (=rtr)
            rtr = bool(int(base[2].split('=')[1].strip()))
            if rtr: flags = flags  | globals.CAN_ID_RTR_FLAG

            # extract can data length (=dlc)
            dlc = int(base[3].split('=')[1].strip())

            # Create regular expression
            regex = re.compile("0x[0-9,A-F,a-f][0-9,A-F,a-f]")
            data = regex.findall(base[4])
            can_data = [int(x, 16) for x in data]

            # Remove erroneous frames - TBD
            if dlc != len(can_data):
                continue

            if flags == 0: flags = None

            self._can_frames_list.append( globals.canBusFrame( can_id, dlc, can_data, flags = flags) )

        file_hwd.close()

        
    def _generate_can_data_file(self, file_name, frames_num):
        # Save CAN data frames to a file in the following pattern
        # can_id = 0x0c1, ide = 0, rtr = 0, dlc = 8, data = [0x93, 0xFD, 0x07, 0xD0, 0x90, 0x2C, 0xDF, 0x40])

        self._can_frames_list[:] = []
        frm_cnt = 0;

        while len(self._can_frames_list) < frames_num:
            # Generate random can_id and data with different length of data
            for is_extended in [False, True]:
                for dlc in range(0,9):
                    can_id = self._create_random_can_id(is_extended)

                    # Change one extended can_id to be less than 11 bits.
                    if is_extended and dlc == 4:
                        can_id = self._create_random_can_id(False)

                    can_data = self._create_random_can_data(dlc)
                    for idx in range(0,10):
                        flags = None
                        if len(self._can_frames_list) >= frames_num:
                            break

                        self._can_frames_list.append( globals.canBusFrame ( can_id, dlc, can_data, flags = globals.CAN_ID_IDE_FLAG if is_extended else None) )

                    ## Add Remote frame - TBD
                    #self._can_frames_list.append(CanFrameAT((can_id, is_extended, True), 0, []))

        file_hwd = open( file_name, "w")
        for frame in self._can_frames_list:
            file_hwd.write( str(frame) + '\n' )

        file_hwd.close()


    def _sim_tx_frames_thread(self, sim_port, tx_rate):

        err_counter = 0
        
        if len(self._can_frames_list) == 0:
            raise Exception("ERROR : No CAN frames were loaded")

        rate_fps_ms = tx_rate / ( 60.0 * 1000.0 )

        for i, frame in enumerate(self._can_frames_list):
            start = time.time()
            try:
                self.can_sim.transmit( sim_port, frame )
                
                self.stats.can_sim_tx[sim_port] += 1
                err_counter = 0
                #log.debug( "Sim TX No. {0} : {1}".format(i, str(frame)) )
                #i += 1


            except Exception as e:
                log.error( "ERROR : failed to transmit can data - {}".format(e) )
                if 'XL_ERR_QUEUE_IS_FULL' in  e.message:
                    time.sleep(0.5)
                    err_counter += 1
            finally:

                if err_counter > 50:
                    raise Exception( "ERROR : Unable to transmit can data" )

                sleep_time = rate_fps_ms - (time.time() - start)
                if sleep_time > 0:
                    time.sleep( sleep_time )
                # raise Exception(e)
                #break



    def _sim_rx_frames_thread(self, sim_port):
        
        frm_cnt = 0
        read_empty = 0
        err_counter = 0

        num_of_sent_frame = self._frames_num - (self._frames_num * self._err_part / 100)

        while ( (frm_cnt < num_of_sent_frame) and (read_empty < 500) ):
            try:
                sim_rx_frame = self.can_sim.receive(sim_port)

                #log.debug( "Sim RX No. {0} : {1}".format(frm_cnt, str(sim_rx_frame)) )
                if type(sim_rx_frame) is globals.canBusFrame:
                    self.stats.can_sim_rx[sim_port] += 1
                    log.info ( "Receving frame {} from can sim".format(self.stats.can_sim_rx[sim_port]) )

                    frm_cnt += 1
                    read_empty = 0
                else:
                    read_empty += 1
                    time.sleep(0.001)

            except Exception as e:
                log.error( "ERROR : failed to transmit can data - {}".format(e) )
                if 'XL_ERR_QUEUE_IS_FULL' in  e.message:
                    time.sleep(0.5)
                    err_counter += 1

                log.error( "ERROT : existing simulator rx thread - frames count = {0}, error = {1}".format(frm_cnt, e) )
                raise Exception(e)
                 
            finally:
                if err_counter > 50:
                    raise Exception( "ERROR : Unable to transmit can data" )



########### END class TC_CAN_LOAD ##########

class TC_CAN_LOAD_MC(TC_CAN_LOAD):
    """
    @class TC_CAN_LOAD_MC
    @brief CAN API Load tests on Multi-core version
    @author Neta-ly Rahamim
    @version 0.1
    @date	10/03/2015
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.arc2_can_cli_rx = None

        super(TC_CAN_LOAD_MC, self).__init__(methodName, param)

    def tearDown(self):
        # Close unit can socket (service will be closed in the TC_CAN_API tearDown)
        if not self.arc2_can_cli_rx is None:
            self.arc2_can_cli_rx.can.socket_delete()
            self.uut.close_qa_cli("arc2_can_cli_rx")
            self.arc2_can_cli_rx = None

        super(TC_CAN_LOAD_MC, self).tearDown()


    def unit_configuration(self):
        super(TC_CAN_LOAD_MC, self).unit_configuration()

        self.arc2_can_cli_rx = self.uut.create_qa_cli("arc2_can_cli_rx",  target_cpu = 'arc2')
        self.arc2_can_cli_rx.can.service_create()
        ret = self.arc2_can_cli_rx.can.socket_create(self.uut_can_if[0].device_id, {} )
        if "ERROR :" in ret:
            raise globals.Error("ARC2: Can socket create received error {}".format(ret))

        self.arc2_can_cli_rx.can.reset_counters()


    def main(self):
        try:
            thread_list = []

            self._load_can_data_file(CAN_DATA_FILE_NAME)

            simTxThread = threading.Thread(target=self._sim_tx_frames_thread, args=(self.uut_can_if[0].sim_port, self.sim_tx_rate_hz,) )
            thread_list.append(simTxThread)

            simRxThread = threading.Thread(target=self._sim_rx_frames_thread, args=(self.uut_can_if[0].sim_port,) )
            thread_list.append(simRxThread)


            # CAN CLI transmit
            ret = self.can_cli.can.transmit_load(frames = self._frames_num, rate_hz = self.dut_tx_rate_hz, err_part = self._err_part)

            # CAN CLI receive
            self.can_cli_rx.can.receive(frames = len(self._can_frames_list), print_frame = 0)

            # CAN CLI receive from ARC2
            self.arc2_can_cli_rx.can.receive(frames = len(self._can_frames_list), print_frame = 0)

            # Starts simulator threads
            for thread in thread_list:
                thread.start()

            for thread in thread_list:
                thread.join()

        except Exception as e:
            raise e


    def print_results(self):
        tx_can_counters = self.can_cli.can.read_counters()
        rx_can_counters = self.can_cli_rx.can.read_counters()
        rate = self.can_cli_rx.can.read_rx_rate()

        arc2_rx_can_counters = self.arc2_can_cli_rx.can.read_counters()
        arc2_rate = self.arc2_can_cli_rx.can.read_rx_rate()

        if len(tx_can_counters) :
            limit_str = "CAN CLI Tx to Sim Rx - {}% errors".format(self._err_part)
            self.add_limit(limit_str, tx_can_counters['tx'][1], self.stats.can_sim_rx[self.uut_can_if[0].sim_port], self._frames_num , 'EQ')

        if len(rx_can_counters) :
            self.add_limit("CAN Sim Tx to CLI Rx", self.stats.can_sim_tx[self.uut_can_if[0].sim_port], rx_can_counters['rx'][1], len(self._can_frames_list) , 'EQ')

        self.add_limit("CAN Rx average rate", 0, rate, 4000 , 'GTLT')

        if len(arc2_rx_can_counters) :
            self.add_limit("CAN Sim Tx to ARC2 CLI Rx", self.stats.can_sim_tx[self.uut_can_if[0].sim_port], arc2_rx_can_counters['rx'][1], len(self._can_frames_list) , 'EQ')

        self.add_limit("ARC2 CAN Rx average rate", 0, arc2_rate, 4000 , 'GTLT')

########### END class TC_CAN_LOAD_MC ##########

class TC_CAN_LOAD_2DEVICES(TC_CAN_LOAD):
    """
    @class TC_CAN_LOAD
    @brief Load tests on the CAN API
    @author Neta-ly Rahamim
    @version 0.1
    @date	08/02/2015
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.can_cli2 = None
        self.can_cli_rx2 = None

        super(TC_CAN_LOAD_2DEVICES, self).__init__(methodName, param)


    def tearDown(self):
        # Close unit can socket (service will be closed in the TC_CAN_API tearDown)
        if not self.can_cli2 is None:
            self.can_cli2.can.socket_delete()
            self.uut.close_qa_cli("can_cli2")
            self.can_cli2 = None

        if not self.can_cli_rx2 is None:
            self.can_cli_rx2.can.socket_delete()
            self.uut.close_qa_cli("can_cli_rx2")
            self.can_cli_rx = None

        # Close can simulator
        if not self.can_sim is None:
            self.can_sim.power_down(self.uut.can_interfaces[1].sim_port)
            self.can_sim.close_port(self.uut.can_interfaces[1].sim_port)

        super(TC_CAN_LOAD_2DEVICES, self).tearDown()


    def unit_configuration(self):
        super(TC_CAN_LOAD_2DEVICES, self).unit_configuration()

        self.uut_can_if.append(self.uut.can_interfaces[self.uut_id[2]])
        if not self.uut_can_if[1].active:
            raise globals.Error("CAN device {} is not active.".format(self.uut_can_if[1].device_id))

        self.can_cli2 = self.uut.create_qa_cli("can_cli2",  target_cpu = self.target_cpu)
        ret = self.can_cli2.can.socket_create(self.uut_can_if[1].device_id, {} )
        if "ERROR :" in ret:
            raise globals.Error("Can socket create received error {}".format(ret))

        self.can_cli2.can.reset_counters()

        self.can_cli_rx2 = self.uut.create_qa_cli("can_cli_rx2",  target_cpu = self.target_cpu)
        ret = self.can_cli_rx2.can.socket_create(self.uut_can_if[1].device_id, {} )
        if "ERROR :" in ret:
            raise globals.Error("Can socket create received error {}".format(ret))

        self.can_cli_rx2.can.reset_counters()


    def instruments_initilization(self):
        super(TC_CAN_LOAD_2DEVICES, self).instruments_initilization()
        self.can_sim.channel_open( self.uut_can_if[1].sim_port )
        #self.can_sim.configure_port(self.uut_can_if[1].sim_port)
        #self.can_sim.set_timeout(self.uut_can_if[1].sim_port) # set timeout to read can frames
        #self.can_sim.power_up(self.uut_can_if[1].sim_port)


    def main(self):
        try:
            thread_list = []

            self._load_can_data_file(CAN_DATA_FILE_NAME)

            simTxThread = threading.Thread(target=self._sim_tx_frames_thread, args=(self.uut_can_if[0].sim_port,) )
            thread_list.append(simTxThread)

            simTxThread2 = threading.Thread(target=self._sim_tx_frames_thread, args=(self.uut_can_if[1].sim_port, self.sim_tx_rate_hz,) )
            thread_list.append(simTxThread2)

            simRxThread = threading.Thread(target=self._sim_rx_frames_thread, args=(self.uut_can_if[0].sim_port,) )
            thread_list.append(simRxThread)

            simRxThread2 = threading.Thread(target=self._sim_rx_frames_thread, args=(self.uut_can_if[1].sim_port,) )
            thread_list.append(simRxThread2)

            # CAN CLI transmit
            ret = self.can_cli.can.transmit_load(frames = self._frames_num, rate_hz = self._frames_rate_hz, err_part = self._err_part)
            ret = self.can_cli2.can.transmit_load(frames = self._frames_num, rate_hz = self._frames_rate_hz, err_part = self._err_part)

            # CAN CLI receive
            self.can_cli_rx.can.receive(frames = len(self._can_frames_list), print_frame = 0)
            self.can_cli_rx2.can.receive(frames = len(self._can_frames_list), print_frame = 0)

            # Starts simulator threads
            for thread in thread_list:
                thread.start()

            for thread in thread_list:
                thread.join()

        except Exception as e:
            raise e


    def print_results(self):
        tx_can_counters = self.can_cli.can.read_counters()
        tx2_can_counters = self.can_cli2.can.read_counters()
        rx_can_counters = self.can_cli_rx.can.read_counters()
        rx2_can_counters = self.can_cli_rx2.can.read_counters()
        rate = self.can_cli_rx.can.read_rx_rate()
        rate2 = self.can_cli_rx2.can.read_rx_rate()

        if len(tx_can_counters) :
            limit_str = "CAN CLI Tx to Sim Rx - {}% errors".format(self._err_part)
            self.add_limit(limit_str, tx_can_counters['tx'][1], self.stats.can_sim_rx[self.uut_can_if[0].sim_port], self._frames_num , 'EQ')

        if len(rx_can_counters) :
            self.add_limit("CAN Sim Tx to CLI Rx", self.stats.can_sim_tx[self.uut_can_if[0].sim_port], rx_can_counters['rx'][1], len(self._can_frames_list) , 'EQ')

        self.add_limit("CAN Rx average rate", 0, rate, 4000 , 'GTLT')

        if len(tx2_can_counters) :
            limit_str = "Second CAN CLI Tx to Sim Rx - {}% errors".format(self._err_part)
            self.add_limit(limit_str, tx2_can_counters['tx'][1], self.stats.can_sim_rx[self.uut_can_if[1].sim_port], self._frames_num , 'EQ')

        if len(rx2_can_counters) :
            self.add_limit("Second CAN Sim Tx to CLI Rx", self.stats.can_sim_tx[self.uut_can_if[1].sim_port], rx2_can_counters['rx'][1], len(self._can_frames_list) , 'EQ')

        self.add_limit("Second CAN Rx average rate", 0, rate2, 4000 , 'GTLT')

########### END class TC_CAN_LOAD_2DEVICES ##########

class Statistics(object):

    def __init__(self):
        # Each counter is defined as dictionary to support tests with 2 simulator ports
        self.can_sim_tx = {0:0, 1:0, 2:0, 3:0, 4:0 }
        self.can_sim_rx = {0:0, 1:0, 2:0, 3:0, 4:0 }
        self.failed_can_cli2sim = {0:0, 1:0, 2:0, 3:0, 4:0 }
        self.failed_can_sim2cli = {0:0, 1:0, 2:0, 3:0, 4:0 }
  
 
if __name__ == "__main__":

    if os.path.isfile(CAN_DATA_FILE_NAME) :
        os.remove(CAN_DATA_FILE_NAME)

    # Receiving Can API
    com_ip = socket.gethostbyname(socket.gethostname())
    cfg_file_name = "cfg_%s.json" % com_ip
    cfg_dir_name = "c:\\temp\\qa\\configuration\\" 
    cfg_file = os.path.join(cfg_dir_name, cfg_file_name)

    if not os.path.exists( cfg_file ):
        raise globals.Error("configuration file \'%s\' is missing." % (cfg_file) )

    json_file = open(cfg_file)
    try:
        json_data = json.load(json_file)
    except Exception as err:
        raise globals.Error("Failed to parse json data %s, err %s" % (cfg_file, err))

    globals.setup = station_setup.Setup( json_data )
    
    # Create timestamp for log and report file
    scn_time = "%s" % (datetime.now().strftime("%d%m%Y_%H%M%S"))
    """ @var logger handle for loging library """
    log_file = os.path.join(globals.setup.station_parameters.log_dir, "st_log_%s.txt" % (scn_time) )
    print "note : log file created, all messages will redirect to : \n%s" % log_file
    logging.basicConfig(filename=log_file, filemode='w', level=logging.NOTSET)

    globals.setup.load_setup_configuration_file()

    suite = unittest.TestSuite()

    globals.screen = sys.stdout

    test_param = dict( uut_id = (0,0))
    suite.addTest(common.ParametrizedTestCase.parametrize(TC_CAN_API, param = test_param ))

    #test_param = dict( uut_id = (0,0))
    #suite.addTest(common.ParametrizedTestCase.parametrize(TC_CAN_ERRONEOUS, param = test_param ))

    #test_param = dict( uut_id = (0,0), frames_rate = 300, frames_num = 10000, err_part = 0)
    #suite.addTest(common.ParametrizedTestCase.parametrize(TC_CAN_LOAD, param = test_param ))

    #test_param = dict( uut_id = (1,0,1))
    #suite.addTest(common.ParametrizedTestCase.parametrize(TC_CAN_2DEVICES, param = test_param ))

    #test_param = dict( uut_id = (1,0,1), frames_rate = 500, frames_num = 10000, err_part = 0)
    #suite.addTest(common.ParametrizedTestCase.parametrize(TC_CAN_LOAD_2DEVICES, param = test_param ))

    test_param = dict( uut_id = (0,0), frames_rate = 300, frames_num = 10000, err_part = 0)
    suite.addTest(common.ParametrizedTestCase.parametrize(TC_CAN_LOAD_MC, param = test_param ))

    # define report file
    report_file = os.path.join(globals.setup.station_parameters.reports_dir, "report_%s.html" % (scn_time) ) 
    fp = file(report_file, 'wb')

    # use html atlk test runner
    runner = HTMLTestRunner.HTMLTestRunner(
                                            stream=fp,
                                            verbosity=2,
                                            title='auto-talks system testing',
                                            description = 'CAN tests only', 
                                            uut_info = globals.setup.units.get_versions()
                                            )

    try:
        result = runner.run(suite)

    except Exception as e:       
        print "Received Exception"
    finally:
        # close report file
        fp.close()
    
   
        print "test sequence completed, please review report file %s" % report_file
        # open an HTML file on my own (Windows) computer
        url = "file://" + report_file
        webbrowser.open(url,new=2)
 


