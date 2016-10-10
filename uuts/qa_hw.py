import os, sys
from datetime import datetime
import unittest, logging, socket, json, json2html
from lib import globals, station_setup, HTMLTestRunner
from tests import common
from tests.common import tParam
#import json2html
#import webbrowser



if __name__ == "__main__":
    
    # Load configuration file
    import socket
    com_ip = socket.gethostbyname(socket.gethostname())
    cfg_file_name = "cfg_%s.json" % com_ip
    cfg_dir_name = "%s\\configuration\\" % dirname 
    cfg_file = os.path.join(cfg_dir_name, cfg_file_name)

    if not os.path.exists( cfg_file ):
        raise globals.Error("configuration file \'%s\' is missing." % (cfg_file) )

    json_file = open(cfg_file)
    try:
        json_data = json.load(json_file)
    except Exception as err:
        raise globals.Error("Failed to parse json data %s" % cfg_file, err)

    globals.setup = station_setup.Setup( json_data )


    # Create timestamp for log and report file
    scn_time = "%s" % (datetime.now().strftime("%d%m%Y_%H%M%S"))
    """ @var logger handle for loging library """
    log_file = os.path.join(globals.setup.station_parameters.log_dir, "st_log_%s.txt" % (scn_time) )
    print "note : log file created, all messages will redirect to : \n%s" % log_file
    logging.basicConfig(filename=log_file, filemode='w', level=logging.NOTSET)
    log = logging.getLogger(__name__)

    # load all system 
    globals.setup.load_setup_configuration_file()

    suite = unittest.TestSuite()

    test_frames = 1000


    from tests.sdk3_0 import tc_link_api

    # Link conformence test 
    test_links = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0x2123, frames = 100, frame_rate_hz = 10, payload_len = 200, tx_power = -15 ), 
                   tParam( rx = (0,2), tx = (1,2), proto_id = 0x4123, frames = 100, frame_rate_hz = 10, payload_len = 200, tx_power = -15 ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, sniffer_test = 1 ) ) )

    # System Throughput minimum requirment
    for frame_size in xrange(300, 2100, 217):

        test_links = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0x2123, frames = test_frames, frame_rate_hz = 10, payload_len = frame_size, tx_power = -15 ), 
                        tParam( rx = (0,2), tx = (1,2), proto_id = 0x4123, frames = test_frames, frame_rate_hz = 400, payload_len = frame_size, tx_power = -15 ) ]

        suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links ) ) )

    
    # Stress test, 6 session TX + RX         
    cpu_load = {0: {'load': 30, 'timeout': 0}, 1: {'load': 30, 'timeout': 0} }
    sniffer_test = { 'active' : True, 'Ratio' : 10 }
    total_frames = 10000
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    test_links = [  tParam( tx = (0,1), rx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = '92:56:92:01:00:ca', tx_power = -15 ), 
                    tParam( rx = (0,2), tx = (1,2), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = '92:56:92:02:00:e1',  tx_power = -15 ),  
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'data', proto_id = 0x13a1, frames = total_frames*5, frame_rate_hz = 20, tx_data = tx_data,  dest_addr = '92:56:92:01:00:e1', tx_power = -15 ),
                    tParam( tx = (1,2), rx = (0,2), frame_type= 'data', proto_id = 0x13d1, frames = total_frames*10, frame_rate_hz = 50, tx_data = tx_data,  dest_addr = '92:56:92:02:00:e1', tx_power = -15 ),
                    tParam( tx = (0,1), rx = (1,1), frame_type= 'data', proto_id = 0x13e2, frames = total_frames, frame_rate_hz = 20, tx_data = tx_data,  tx_power = -15 ), 
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'data', proto_id = 0x13b3, frames = total_frames*10, frame_rate_hz = 200, tx_data = tx_data,  tx_power = -15 ) ]

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, sniffer_test = 0, cpu_load_info = cpu_load ) ) )



    test_links = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0x2123, frames = 100, frame_rate_hz = 10, payload_len = frame_size, tx_power = -15 ), 
                    tParam( rx = (0,2), tx = (1,2), proto_id = 0x4123, frames = (100 * 40), frame_rate_hz = 10, payload_len = frame_size, tx_power = -15 ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, sniffer_test = 1 ) ) )


    cpu_load = {'1': {'load': 30, 'timeout': 0}, '2': {'load': 30, 'timeout': 0} }
    test_links = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0x2123, frames = 5000, frame_rate_hz = 10, payload_len = frame_size, tx_power = -15 ), 
                    tParam( rx = (0,2), tx = (1,2), proto_id = 0x4123, frames = (5000 * 40), frame_rate_hz = 400, payload_len = frame_size, tx_power = -15 ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, cpu_load_info = cpu_load ) ) )

