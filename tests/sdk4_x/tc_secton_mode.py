"""
    @file  
    Implement secton mode tests
    This test is based on the v2x link test and adding some features to stress the remote infrastrcuture

    TP :  @link \\fs01\docs\ATE\Test Plans\SECTON mode.docx @endlink 
"""

import sys, os, time, tempfile, logging
from lib import station_setup, instruments_manager, packet_analyzer, globals, gps_simulator

from uuts import common
from tests import common

import threading
from datetime import datetime

from tests.sdk3_0 import tc_link_api


log = logging.getLogger(__name__)
# class TC_LINK_API(common.V2X_SDKBaseTest):

class TC_SECTON(tc_link_api.TC_LINK_API):


    def __init__(self, methodName = 'runTest', param = None):
        
        super(TC_SECTON, self).__init__(methodName, param)

        # Add verification stat to stats
        setattr( self.stats, 'verification_stat', {'total' : 0, 'failure' : 0, 'success' : 0, 'errors' : 0 } )


    def ecc_verify_signuature(self):
        pass

    def unit_configuration(self):
        super(TC_SECTON, self).unit_configuration()

        # Add cli for e
        #for uut_id in self._uut_list:
        for uut_id in self._uut_list:
            if self._uut[uut_id].external_host:
                self.uut_id = uut_id
                break

    
        self.cli_name = "ecc_cli_%d" % 0
        self._uut[self.uut_id].create_qa_cli(self.cli_name, target_cpu = self.target_cpu)

        self._uut[self.uut_id].qa_cli(self.cli_name).ecc.service_create( type = 'remote' if self._uut[self.uut_id].external_host else 'hw')
            
        self._uut[self.uut_id].qa_cli(self.cli_name).ecc.verification.socket_create()
        self._uut[self.uut_id].qa_cli(self.cli_name).ecc.verification.set_curve( 256 )
        self._uut[self.uut_id].qa_cli(self.cli_name).ecc.verification.set_public_key( 
                        'bc3fdd5d620d0a145d867d8b286867ec92c47d908a772d4344eb389526f3751e' ,
                        '96fc56f1f79baeaaff5b3542b7ffb678c22d9ddb3dc0cb4df0e24af51606db3b')

        self._uut[self.uut_id].qa_cli(self.cli_name).ecc.verification.set_signuture( 
                        '4e3a775c71a5c259fad57a8ed1e45591030fbb6594d2300b7ceccd7dbc70ad36' ,
                        'bc05d39cd2c5f32bf10502c6b91de10c8599d0890873e8ae7b137225d51dd454')

    def do_while_transmit(self, transmit_time):

        start_time = int(time.time())
        i = 0
        while ( (int(time.time()) - start_time) < transmit_time ):

            self._uut[self.uut_id].qa_cli(self.cli_name).ecc.verification.set_request ( i , 'b93d12b2c6027b0ba4d4d8c2bc20da888be2422f089be3243a6c44e50ddef0cb')
            verification_state = self._uut[self.uut_id].qa_cli(self.cli_name).ecc.verification.get_response ()

            if verification_state is None:
                self.stats.verification_stat['errors'] += 1
                log.error(" ERROR : verification failed" )
            elif verification_state == '0':
                self.stats.verification_stat['success'] += 1
            else:
                self.stats.verification_stat['failure'] += 1
            i = i + 1

            self.stats.verification_stat['total'] += 1

    def print_results(self):
        super(TC_SECTON, self).print_results()
        self.add_limit( "Total verifications" , 0 , self.stats.verification_stat['total'], None , 'GT')    
        self.add_limit( "Succcessful verifications" , 0 , self.stats.verification_stat['success'], None , 'GT')    
        self.add_limit( "Failed verifications" , 0 , self.stats.verification_stat['failure'], None , 'EQ')    
        self.add_limit( "Errors verifications" , 0 , self.stats.verification_stat['errors'], None , 'EQ')    



class Statistics(tc_link_api.Statistics):

    def __init__(self):
        super(Statistics, self).__init__()
        self.verification_stat = {'total' : 0, 'failure' : 0, 'success' : 0, 'errors' : 0 }








