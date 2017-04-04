import os, sys
from datetime import datetime
import unittest, logging, socket, json, json2html
from lib import globals, station_setup, HTMLTestRunner
from tests import common
from tests.common import tParam
import json2html
import webbrowser
import signal
import argparse
import time

# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)

def gm_v2x_tests( suite, cpu_type = 'arm', total_frames = 10000, tx_pow = -5 ):

    frames_verification_active = False

    # tx_pow = -5
    # test_frames = 10000
    from tests.sdk3_0 import tc_link_api

    """ CONFORMENCE TEST : This test case will check frame structure of wlan & llc """
    # 1. Broadcast
    frame_verification = { 'active' : False, 'ratio' : 10 }
    test_links = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0x1234, frames = total_frames, frame_rate_hz = 10, payload_len = 800, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), proto_id = 0x5678, frames = total_frames, frame_rate_hz = 10, payload_len = 800, tx_power = tx_pow ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    # 2. Unitcast
    test_links = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0x1234, frames = total_frames, frame_rate_hz = 10, payload_len = 800, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                   tParam( tx = (1,1), rx = (0,1), proto_id = 0x5678, frames = total_frames, frame_rate_hz = 10, payload_len = 800, dest_addr = globals.setup.units.unit(0).rf_interfaces[0].mac_addr, tx_power = tx_pow ) ]
    #suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    # 3. VSA unicast
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    frame_verification = { 'active' : True, 'ratio' : 10 }
    test_links = [ tParam( tx = (0,1), rx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a44, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr,  tx_power = tx_pow )]

    #suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    # 4. VSA broadcast
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    test_links = [ tParam( tx = (0,1), rx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a44, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow )]

    #suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    """ System Throughput as minimum requirment for varios of sizes , as well as test stability, total 9 tests """
    # 5-13
    for frame_size in xrange(300, 2100, 217):

        test_links = [ tParam( tx = (0,1), rx = (1,1), proto_id = 0x2123, frames = total_frames, frame_rate_hz = 10, payload_len = frame_size, tx_power = tx_pow ), 
                        tParam( rx = (0,1), tx = (1,1), proto_id = 0x4123, frames = total_frames, frame_rate_hz = 400, payload_len = frame_size, tx_power = tx_pow ) ]

        suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type ) ) )

    #14. VSA 
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    """ VSA unicast frames """
    test_links = [  tParam( tx = (0,1), rx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a44, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr,  tx_power = tx_pow ) ] 

    #suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    """ VSA broadcast frames """
    # 15.
    test_links = [  tParam( tx = (0,1), rx = (1,1), frame_type= 'vsa', proto_id = 0x0151c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0151c24a44, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow ) ] 

    #suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, verify_frames = frame_verification ) ) )


    # 16. Stress test, 6 session TX + RX         
    cpu_load = {0: {'load': 30, 'timeout': 0}, 1: {'load': 30, 'timeout': 0} }
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    test_links = [ tParam( tx = (0,1), rx = (1,1), frame_type= 'data', proto_id = 0x13e2, frames = total_frames, frame_rate_hz = 20, tx_data = tx_data,  tx_power = tx_pow ), 
                   tParam( tx = (1,1), rx = (0,1), frame_type= 'data', proto_id = 0x13b3, frames = total_frames*10, frame_rate_hz = 300, tx_data = tx_data,  tx_power = tx_pow ) ]

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, sniffer_test = 0, cpu_load_info = cpu_load ) ) )


    cpu_load = {0: {'load': 30, 'timeout': 0}, 1: {'load': 30, 'timeout': 0} }
    test_links = [  tParam( tx = (0,1), rx = (1,1), proto_id = 0x2163, frames = total_frames, frame_rate_hz = 10, payload_len = frame_size, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), proto_id = 0x4163, frames = (total_frames * 40), frame_rate_hz = 400, payload_len = frame_size, tx_power = tx_pow ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, cpu_load_info = cpu_load ) ) )

def v2x_api_tests( suite, cpu_type = 'arm', total_frames = 10000, tx_pow = -5 ):

    frames_verification_active = False

    # tx_pow = -5
    # test_frames = 10000
    from tests.sdk3_0 import tc_link_api

    """ CONFORMENCE TEST : This test case will check frame structure of wlan & llc """
    # 1. Broadcast
    frame_verification = { 'active' : False, 'ratio' : 10 }
    test_links = [ tParam( tx = (0,0), rx = (1,0), proto_id = 0x1234, frames = total_frames, frame_rate_hz = 10, payload_len = 600, tx_power = tx_pow ), 
                    tParam( rx = (0,0), tx = (1,0), proto_id = 0x5678, frames = total_frames, frame_rate_hz = 10, payload_len = 600, tx_power = tx_pow ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )
    return    
    # 2. Unitcast
    test_links = [ tParam( tx = (0,0), rx = (1,0), proto_id = 0x1234, frames = total_frames, frame_rate_hz = 10, payload_len = 800, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                   tParam( tx = (1,0), rx = (0,0), proto_id = 0x5678, frames = total_frames, frame_rate_hz = 10, payload_len = 800, dest_addr = globals.setup.units.unit(0).rf_interfaces[0].mac_addr, tx_power = tx_pow ) ]

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    # 3. VSA unicast
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    frame_verification = { 'active' : False, 'ratio' : 10 }
    test_links = [ tParam( tx = (0,0), rx = (1,0), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr,  tx_power = tx_pow )]

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    # 4. VSA broadcast
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"

    test_links = [ tParam( tx = (0,0), rx = (1,0), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow )]

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    """ System Throughput as minimum requirment for varios of sizes , as well as test stability, total 9 tests """
    # 5-13
    for frame_size in xrange(300, 2100, 217):

        test_links = [ tParam( tx = (0,0), rx = (1,0), proto_id = 0x2123, frames = total_frames, frame_rate_hz = 10, payload_len = frame_size, tx_power = tx_pow ), 
                        tParam( rx = (0,1), tx = (1,1), proto_id = 0x4123, frames = total_frames, frame_rate_hz = 400, payload_len = frame_size, tx_power = tx_pow ) ]

        suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type ) ) )

    #14. VSA 
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    """ VSA unicast frames """
    test_links = [  tParam( tx = (0,0), rx = (1,0), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0050c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr,  tx_power = tx_pow ) ] 

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, verify_frames = frame_verification ) ) )

    """ VSA broadcast frames """
    # 15.
    test_links = [  tParam( tx = (0,0), rx = (1,0), frame_type= 'vsa', proto_id = 0x0151c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), frame_type= 'vsa', proto_id = 0x0151c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, tx_power = tx_pow ) ] 

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, verify_frames = frame_verification ) ) )


    # 16. Stress test, 6 session TX + RX         
    cpu_load = {0: {'load': 30, 'timeout': 0}, 1: {'load': 30, 'timeout': 0} }
    tx_data = "01020b045a0304017cfa71feb712698b01000113231f0080031f00bfe01f00bfe11f00bff01f0001118cc6c8c53896b200fa139709de1082a8de000000010308f12c42d4b36996d2cf668769ea87badf56ae3ae4808ec2344d2eb232bcb6f601010e808107040114060f118cc7fec538970c090666ffffffff07055553444f5401231f01080453434d53091020011890110ea777000000000000f2340a023edc0211b6010c1a150101030708262000140000300200000000000000004026200014000030020000000000000001200148708000000300000000000000050e06000b6b236ca30001064bd41c26fd0e0001064bd7afadfd118cc77cc538968209390359fa54b6dfce9753c2d8d407e4ce022a9122ed4b4f48e13a00f01261919cc14f7816613be146785f4a599a73c2ec0b96dcf44e2972efb2a8502577e474b0af7e"
    test_links = [  tParam( tx = (0,0), rx = (1,0), frame_type= 'vsa', proto_id = 0x0052c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'vsa', proto_id = 0x0052c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr,  tx_power = tx_pow ),  
                    tParam( tx = (1,0), rx = (0,0), frame_type= 'data', proto_id = 0x13a1, frames = total_frames*5, frame_rate_hz = 20, tx_data = tx_data,  dest_addr = globals.setup.units.unit(0).rf_interfaces[0].mac_addr, tx_power = tx_pow ),
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'data', proto_id = 0x13d1, frames = total_frames*10, frame_rate_hz = 50, tx_data = tx_data,  dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr, tx_power = tx_pow ),
                    tParam( tx = (0,0), rx = (1,0), frame_type= 'data', proto_id = 0x13e2, frames = total_frames, frame_rate_hz = 20, tx_data = tx_data,  tx_power = tx_pow ), 
                    tParam( tx = (1,0), rx = (0,0), frame_type= 'data', proto_id = 0x13b3, frames = total_frames*10, frame_rate_hz = 200, tx_data = tx_data,  tx_power = tx_pow ) ]

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links,  target_cpu = cpu_type, sniffer_test = 0, cpu_load_info = cpu_load ) ) )


    cpu_load = {0: {'load': 30, 'timeout': 0}, 1: {'load': 30, 'timeout': 0} }
    test_links = [  tParam( tx = (0,0), rx = (1,0), proto_id = 0x2163, frames = total_frames, frame_rate_hz = 10, payload_len = frame_size, tx_power = tx_pow ), 
                    tParam( rx = (0,1), tx = (1,1), proto_id = 0x4163, frames = (total_frames * 40), frame_rate_hz = 400, payload_len = frame_size, tx_power = tx_pow ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, cpu_load_info = cpu_load ) ) )

def nav_api_tests( suite, cpu_type = 'arm', sampling_time_sec = 60*10 ):

    from tests.sdk2_1 import tc_navapi
    suite.addTest(common.ParametrizedTestCase.parametrize(  tc_navapi.TC_NAV_1,
                                                            param =  dict( uut_id = (1,0),  target_cpu = cpu_type,
                                                            gps_scenario="Autotalks\\netter2beersheva", scenario_time_sec = sampling_time_sec,
                                                            test_desc = 'Verify NAV module' ) ))

def can_api_tests( suite, is_sc = True, cpu_type = 'arm' ):

    from tests.sdk4_x import tc_can

    UUT_ID = (0,0)

    if os.path.isfile(tc_can.CAN_DATA_FILE_NAME) :
        os.remove(tc_can.CAN_DATA_FILE_NAME)

   # CAN tests
    from tests.sdk4_x import tc_can
    test_param = dict( uut_id = (0,0)) # (unit ID, CAN ID)
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_can.TC_CAN_API, param = test_param ))

    test_param = dict( uut_id = UUT_ID )
    # Removed
    # suite.addTest(common.ParametrizedTestCase.parametrize(tc_can.TC_CAN_ERRONEOUS, param = test_param ))

    test_param = dict( uut_id = UUT_ID, frames_rate = 500, frames_num = 100000, err_part = 0)
    test_type = tc_can.TC_CAN_LOAD if is_sc else tc_can.TC_CAN_LOAD_MC 
    suite.addTest(common.ParametrizedTestCase.parametrize(test_type, param = test_param ))

    # Check if any unit support 2 can or board type ATK17
    CAN_2devices = -1
    for uut in globals.setup.units:
        if len(uut.can_interfaces) == 2:
            CAN_2devices = uut.idx
            break

    if CAN_2devices >= 0:
        test_param = dict( uut_id = (CAN_2devices,0,1)) # (unit ID, CAN ID, second CAN ID)
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_can.TC_CAN_2DEVICES, param = test_param ))

        test_param = dict( uut_id = ( CAN_2devices,0,1), frames_rate = 500, frames_num = 100000, err_part = 0)
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_can.TC_CAN_LOAD_2DEVICES, param = test_param ))

def eth_fnc_tests( suite, cpu_type = 'arm' ):
        
    from tests.sdk4_x import tc_ethernet

    test_param = dict( uut_id = (0,0), total_frames_to_send = 50000, max_rtt_msec = 3, target_cpu = cpu_type ) 
    #test_param = dict( uut_id = (0,0), total_frames_to_send = 500, max_rtt_msec = 3, target_cpu = cpu_type ) 
     
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_ethernet.TC_ETHERNET_UDP, param = test_param ) )
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_ethernet.TC_ETHERNET_RAW, param = test_param ) )

def wlanMib_api_tests( suite , cpu_type = 'arm' ):
    from tests.sdk4_x import tc_wlanMib_api
    
    test_param = dict( property = "get" , inspectionType = "correct") 
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_wlanMib_api.TC_WlanMib_API,param=test_param) )
    test_param = dict( property = "get" , inspectionType = "exact") 
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_wlanMib_api.TC_WlanMib_API,param=test_param) )
  
    test_param = dict( property = "set" , inspectionType = "correct") 
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_wlanMib_api.TC_WlanMib_API,param=test_param) )
    test_param = dict( property = "set" , inspectionType = "exact") 
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_wlanMib_api.TC_WlanMib_API,param=test_param) )
    test_param = dict(  property = "set" , inspectionType = "incorrect") 
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_wlanMib_api.TC_WlanMib_API,param=test_param) )

    test_param = dict(  property = "get" , inspectionType = "incorrect") 
    suite.addTest(common.ParametrizedTestCase.parametrize(tc_wlanMib_api.TC_WlanMib_API,param=test_param) )

def dot4_tests(suite, cpu_type = 'arm'):
    from tests.sdk5_x import tc_dot4
    
    test_common_options = [ dict( channel_num = -1, time_slot = 0, op_class = -1, immediate_access = 0 ), 
                     dict( channel_num = 176, time_slot = 3, op_class = 1, immediate_access = 0 ),
                     dict( channel_num = 176, time_slot = 1, op_class = 1, immediate_access = 255 ) ]
    test_options = [ dict( channel_num = -1, time_slot = 0, op_class = -1), 
                     dict( channel_num = 172, time_slot = 0, op_class = -1),
                     dict( channel_num = -1, time_slot = 0, op_class = 1),
                     dict( channel_num = -1, time_slot = 1, op_class = -1),
                     dict( channel_num = -1, time_slot = 3, op_class = -1) ]
    test_links = [ tParam( tx = (0,0), rx = (1,0),frame_type= 'data', proto_id = 0x1234, frames = 20000, frame_rate_hz = 10, payload_len = 800, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = 160 ), 
                   tParam( tx = (1,0), rx = (0,0),frame_type= 'data', proto_id = 0x5678, frames = 20000, frame_rate_hz = 10, payload_len = 800, dest_addr = globals.setup.units.unit(0).rf_interfaces[0].mac_addr, tx_power = 160 ) ]

    suite.addTest(common.ParametrizedTestCase.parametrize(tc_dot4.TC_Dot4, param = dict( params = test_common_options, target_cpu = cpu_type, send_dict = test_options, tx_dict = test_links) ) )
   
def parse_params():

    parser = argparse.ArgumentParser( description='Automatic QA CLI build process script' )
    parser.add_argument( '-t', '--type', type=str, required=True, choices = ['sc', 'mc', 'all', 'gm', 'sanity'], default='all', help='Testing Firmware type, either SC or MC or sanity on SC')
    parser.add_argument( '-q', '--quick', action="store_true", help='Run short and quick scenario')
    parser.add_argument( '-p', '--prepare', action="store_true", help='Load the fw')
    parser.add_argument( '-v', '--ver', type=str, required=False, default ='',  help='Firmware tar file (e.g. sdk-4.3.0-beta1 or sdk-4.2.2-pangaea4-i686-linux-gnu)')
    parser.add_argument( '-f', '--cfg_file', type=str, required=False, default ='',  help='Configuration file of setup')
    parser.add_argument( '-sa', '--sectonm_automation', action="store_true", help='sectonm automation flage to enable target reboot before testing')
    #args = parser.parse_args( ['-v', 'sdk-4.4.0-beta14', '-t', 'sanity'] )
    #args = parser.parse_args( ['-v', 'sdk-4.4.0-beta17', '-t', 'sc', '-p'] )
    #args = parser.parse_args( ['-t', 'sc'] )
    args = parser.parse_args()
    return args

def v2x_api_test(suite, cpu_type = 'arm'):
    
    #scenario = "basic"
    #test_param = dict( uut_id1 = 0,uut_id2 = 1,target_cpu = cpu_type,scen = scenario)
    #from tests.sdk4_x import v2x_api_test
    #suite.addTest(common.ParametrizedTestCase.parametrize(v2x_api_test.V2X_API_TEST, param = test_param))
    
    scenario = "send and receive"
    test_param = dict( uut_id1 = 0,uut_id2 = 1,target_cpu = cpu_type,scen = scenario)
    from tests.sdk4_x import v2x_api_test
    suite.addTest(common.ParametrizedTestCase.parametrize(v2x_api_test.TC_V2X_API_TEST, param = test_param))

    scenario = "dot4_channel"
    test_param = dict( uut_id1 = 0,uut_id2 = 1,target_cpu = cpu_type,scen = scenario)
    from tests.sdk4_x import v2x_api_test
    suite.addTest(common.ParametrizedTestCase.parametrize(v2x_api_test.TC_V2X_API_TEST, param = test_param))

    scenario = "socket"
    test_param = dict( uut_id1 = 0,uut_id2 = 1,target_cpu = cpu_type,scen = scenario)
    from tests.sdk4_x import v2x_api_test
    suite.addTest(common.ParametrizedTestCase.parametrize(v2x_api_test.TC_V2X_API_TEST, param = test_param))

    scenario = "service_get and service_delete"
    test_param = dict( uut_id1 = 0,uut_id2 = 1,target_cpu = cpu_type,scen = scenario)
    from tests.sdk4_x import v2x_api_test
    suite.addTest(common.ParametrizedTestCase.parametrize(v2x_api_test.TC_V2X_API_TEST, param = test_param))

def v2x_tests ( suite, cpu_type = 'arm',total_frames = 10000):

    from tests.sdk5_x import Tc_link
   
# api tast Tx
    test_links = [ tParam( tx = (0,0), rx = (1,0), proto_id = 0x1234, frames = 10, frame_rate_hz = 10 ), 
                    tParam( rx = (0,0), tx = (1,0), proto_id = 0x5678, frames = 10, frame_rate_hz = 10 ) ]
    suite.addTest(common.ParametrizedTestCase.parametrize(Tc_link.TC_LINK, param = dict( params = test_links, target_cpu = cpu_type ) ) )

# api tast Rx
    test_links = [  tParam( tx = (0,0), rx = (1,0), frame_type= 'LPD', proto_id = 0x0052c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'LPD', proto_id = 0x0052c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr,  tx_power = tx_pow ),  
                    tParam( tx = (1,0), rx = (0,0), frame_type= 'LPD', proto_id = 0x13a1, frames = total_frames*5, frame_rate_hz = 20, tx_data = tx_data,  dest_addr = globals.setup.units.unit(0).rf_interfaces[0].mac_addr, tx_power = tx_pow ),
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'EPD', proto_id = 0x13d1, frames = total_frames*10, frame_rate_hz = 50, tx_data = tx_data,  dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr, tx_power = tx_pow ),
                    tParam( tx = (0,0), rx = (1,0), frame_type= 'data', proto_id = 0x13e2, frames = total_frames, frame_rate_hz = 20, tx_data = tx_data,  tx_power = tx_pow ), 
                    tParam( tx = (1,0), rx = (0,0), frame_type= 'data', proto_id = 0x13b3, frames = total_frames*10, frame_rate_hz = 200, tx_data = tx_data,  tx_power = tx_pow ) ]

    test_links = [  tParam( tx = (0,0), rx = (1,0), frame_type= 'vsa', proto_id = 0x0052c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(1).rf_interfaces[0].mac_addr, tx_power = tx_pow ), 
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'vsa', proto_id = 0x0052c24a43, frames = total_frames, frame_rate_hz = 10, tx_data = tx_data, dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr,  tx_power = tx_pow ),  
                    tParam( tx = (1,0), rx = (0,0), frame_type= 'data', proto_id = 0x13a1, frames = total_frames*5, frame_rate_hz = 20, tx_data = tx_data,  dest_addr = globals.setup.units.unit(0).rf_interfaces[0].mac_addr, tx_power = tx_pow ),
                    tParam( tx = (1,1), rx = (0,1), frame_type= 'data', proto_id = 0x13d1, frames = total_frames*10, frame_rate_hz = 50, tx_data = tx_data,  dest_addr = globals.setup.units.unit(0).rf_interfaces[1].mac_addr, tx_power = tx_pow ),
                    tParam( tx = (0,0), rx = (1,0), frame_type= 'data', proto_id = 0x13e2, frames = total_frames, frame_rate_hz = 20, tx_data = tx_data,  tx_power = tx_pow ), 
                    tParam( tx = (1,0), rx = (0,0), frame_type= 'data', proto_id = 0x13b3, frames = total_frames*10, frame_rate_hz = 200, tx_data = tx_data,  tx_power = tx_pow ) ]
# Tx stress

# Rx stress

# brodcast

# unicast

# rate and size
    

if __name__ == "__main__":
    
    # Load configuration file
    import socket
    import sys


    args = parse_params()

    com_ip = socket.gethostbyname(socket.gethostname())
    cfg_file_name = "cfg_%s.json" % com_ip
    cfg_dir_name = "%s\\configuration\\" % dirname 
    cfg_file = os.path.join(cfg_dir_name, cfg_file_name)

    if len(args.cfg_file) > 1:
        cfg_file = args.cfg_file

    

    if not os.path.exists( cfg_file ):
        raise globals.Error("configuration file \'%s\' is missing." % (cfg_file) )

    json_file = open(cfg_file)
    try:
        json_data = json.load(json_file)
    except Exception as err:
        raise globals.Error("Failed to parse json data %s" % cfg_file, err)

    globals.setup = station_setup.Setup( json_data )

    # load all system 
    globals.setup.load_setup_configuration_file()

    def gm_suite( suite):
        #gm_v2x_tests( suite, 'arm', total_frames )
        nav_api_tests( suite, 'arm', sampling_time_sec)
        #can_api_tests( suite, True, 'arm' )
        #eth_fnc_tests( suite, 'arm' )

    def sc_suite( suite ):
        dot4_tests(suite)
        #v2x_api_test(suite)
        #v2x_tests( suite, 'arm', total_frames )
        #v2x_api_tests( suite, 'arm', total_frames )
        #wlanMib_api_tests( suite, 'arm')
        #nav_api_tests( suite, 'arm', sampling_time_sec)
  #      can_api_tests( suite, True, 'arm' )
        #eth_fnc_tests( suite, 'arm' )

    def mc_suite( suite ):
        #v2x_api_test(suite)
        v2x_api_tests( suite, 'arc1', total_frames )
        #nav_api_tests( suite, 'arm', sampling_time_sec )
        #nav_api_tests( suite, 'arc1', sampling_time_sec )
        #nav_api_tests( suite, 'arc2', sampling_time_sec )
        #can_api_tests( suite, False, 'arm' )
        #eth_fnc_tests( suite, 'arm' )

    def sanity_testing( suite ):
         
        from tests.sdk3_0 import tc_link_api
        frames_verification_active = False
        tx_pow = -5
        cpu_type = 'arm'

        """ CONFORMENCE TEST : This test case will check frame structure of wlan & llc """
        # Broadcast
        frame_verification = { 'active' : False, 'ratio' : 10 }
        test_links = [ tParam( tx = (0,0), rx = (1,0), proto_id = 0x1234, frames = 100, frame_rate_hz = 10, payload_len = 800, tx_power = tx_pow ), 
                        tParam( rx = (0,0), tx = (1,0), proto_id = 0x5678, frames = 100, frame_rate_hz = 10, payload_len = 800, tx_power = tx_pow ) ]
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_link_api.TC_LINK_API, param = dict( params = test_links, target_cpu = cpu_type, verify_frames = frame_verification ) ) )
        
        from tests.sdk2_1 import tc_navapi
        suite.addTest(common.ParametrizedTestCase.parametrize(tc_navapi.TC_NAV_1, param =  dict( uut_id = (0,0),  target_cpu = cpu_type, gps_scenario="Neter2Eilat", scenario_time_sec = 180) ))


    def run_suite( suite_function, report_scn_info = 'full' ):

        # Create timestamp for log and report file
        scn_time = "%s" % ( datetime.now().strftime("%d%m%Y_%H%M%S") )
        """ @var logger handle for loging library """
        log_file = os.path.join(globals.setup.station_parameters.log_dir, "st_log_%s.txt" % (scn_time) )
        print "note : log file created, all messages will redirect to : \n%s" % log_file
        logging.basicConfig(filename=log_file, filemode='w', level=logging.INFO)
        log = logging.getLogger(__name__)

        def close():
            fp.close()
            logging.shutdown()

        def handler(signum, frame):
            close()


        suite = unittest.TestSuite()
        suite_function( suite )

        # define report file
        report_file = os.path.join(globals.setup.station_parameters.reports_dir, "qa_%s_report_%s.html" % (suite_function.func_name, scn_time) ) 
        fp = file(report_file, 'wb')

        # use html atlk test runner
        runner = HTMLTestRunner.HTMLTestRunner(
                                                stream=fp,
                                                verbosity=2,
                                                title='auto-talks system testing',
                                                description = 'QA %s regression scenario, ver %s' % (suite_function.func_name, args.ver), 
                                                uut_info = globals.setup.units.get_versions()
                                                )
        try:
            signal.signal(signal.SIGINT, handler)
            result = runner.run(suite)

        except Exception as e:       
            print "Received Exception"
        finally:
            # close report file
            close()

 
        print "test sequence completed, please review report file %s" % report_file
        # open an HTML file on my own (Windows) computer
        url = "file://" + report_file
        webbrowser.open(url,new=2)

    # S

    evk_uboot_params = {    
                        'serverip' : com_ip,
                        'prof_enabled_arm' :  0,
                        'prof_enabled_arc1' :  0,
                        'prof_enabled_arc2' : 0,
                        'prof_interval' : 10,
                        'prof_min_load' : 5,
                        'wd_enable' : 1,
                        'syslog_level' : 7,
                        'syslog_sink' : 10
                    }

    total_frames = 100 if args.quick else 10000
    sampling_time_sec = 60 if args.quick else 600

    globals.setup.units.init()

    if args.sectonm_automation:
        for uut in globals.setup.units:
            globals.setup.instruments.power_control[ uut.nps.id ].reboot( uut.nps.port )
    time.sleep(1)
    if ('sanity' in args.type):
        print "Starting Sanity scenario"

        if args.prepare == True:
            img_name = 'qa-%s-%s.img' % ( args.ver , 'sc' if 'sc' in args.type else 'mc')
            globals.setup.units.prepare( image_name = img_name, uboot_parameters = evk_uboot_params ) 
 
        # initlize all unit for testing
        run_suite( sanity_testing, "Sanity" )
    
        
        
    if ('sc' in args.type) or ('all' in args.type):
        print "Starting Single Core scenario testing"

        if args.prepare == True:
            img_name = 'qa-%s-%s.img' % ( args.ver , 'sc')
            globals.setup.units.prepare( image_name = img_name, uboot_parameters = evk_uboot_params ) 
 
        run_suite( sc_suite )

    if ('mc' in args.type) or ('all' in args.type):
        print "Starting mc scenario testing"
        if args.prepare == True:
            img_name = 'qa-%s-%s.img' % ( args.ver , 'mc')
            globals.setup.units.prepare( image_name = img_name, uboot_parameters = evk_uboot_params ) 
 
        run_suite( mc_suite )

    elif ('gm' in args.type):
        print "Starting GM testing"
        run_suite( gm_suite )



