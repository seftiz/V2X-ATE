"""
@file       tc_wlanMib.py
@brief      Test suite for testing wlan mib api implementation  
@author    	Nomi Rozenkruntz
@version	1.0
@date		December 2016
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
from tests import common
import webbrowser, re

log = logging.getLogger(__name__)

WLAN_MIB_DATA_FILE_NAME = "c:\\temp\WlanMib_data_file.txt"

class TC_WlanMib_API(common.V2X_SDKBaseTest):
    """
    @class TC_WlanMib_API
    @brief Test the WlanMib API
    @author Nomi Rozenkruntz
    @version 0.1
    @date	12/15/2016
    """

    def __init__(self, methodName = 'runTest', param = None):
        self.wlanMib_cli = None
        self.stats = Statistics()
        self.uut_wlanMib_if = []

        self.t_property = str()  
        self.n_variables = str() 
        self.inspectionType = str()
        
        self.remoteFlag = str()  
        super(TC_WlanMib_API, self).__init__(methodName, param)

    def test_wlanMib(self):
        self.log = logging.getLogger(__name__)
  
        print >> self.result._original_stdout, "Starting : {}".format( self._testMethodName )

        self.get_test_parameters()
        self.unit_configuration()

        self.main()

        self.analyze_results()
        self.print_results()
        
        print >> self.result._original_stdout, "test, {} completed".format( self._testMethodName )

    def get_test_parameters( self ):
        super(TC_WlanMib_API, self).get_test_parameters()

        self.t_property = self.param.get('property',None)
                
        self.inspectionType = self.param.get('inspectionType',None)
       
        print "Test parameters for %s :" % self.__class__.__name__
       
    def runTest(self):
        pass
    
    def setUp(self):
        super(TC_WlanMib_API, self).setUp()

    def tearDown(self):
        super(TC_WlanMib_API, self).tearDown()

        # Close unit mib service
        if not self.wlanMib_cli is None:
            #self.wlanMib_cli.wlanMib.service_delete()
            self.uut.close_qa_cli("wlanMib_cli")
            self.wlanMib_cli = None

    def unit_configuration(self):

        self.uut_index = 0

        # Verify uut idx exits
        try:
            self.uut = globals.setup.units.unit(self.uut_index)
        except KeyError as e:
            raise globals.Error("uut index and interface input is missing or corrupted, usage : uut_id=(0,1)")

        # Open new v2x-cli
        self.wlanMib_cli = self.uut.create_qa_cli("wlanMib_cli", target_cpu = self.target_cpu )
        
        if self.remoteFlag.count == 0: 
            self.remoteFlag = self.wlanMib_cli.wlanMib.transport_create()
        self.wlanMib_cli.wlanMib.service_create()
        
        self.wlanMib_cli.link.reset_counters()

    def main(self):
        try:
            erroneous = TC_WlanMib_ERRONEOUS()
                     
            #get/set test
            prop = self.t_property
            if prop == "get":
                for i in ("one","two"):
                    valAndType=erroneous._generate_basic_scenario_data(prop,self.inspectionType,i)
                    self._test_extreme_points("Get",self.inspectionType,valAndType,i)
            else:
                for i in ("one","two"):
                    valAndType=erroneous._generate_basic_scenario_data(prop,self.inspectionType,i)
                    self._test_extreme_points("Set",self.inspectionType,valAndType,i)    

        except Exception as e:
            raise e

    def _test_extreme_points(self,property,inspectionType,valAndType,num_of_variables):
        self.inspectionType = inspectionType
        #key- func name
        #value- type and his value
        func_name = []
        
        #WlanMib CLI transmit
        if inspectionType == "incorrect":
            ret = self.wlanMib_cli.wlanMib.transmit(property,valAndType,True)
        else:
            ret = self.wlanMib_cli.wlanMib.transmit(property,valAndType,False)

        string = ret.split("func")
        
        for i in range(1,len(string)-1):
            return_code = string[i].split("rc ")
            save_str = return_code[1].split("for")
            if return_code[1].find("0") == 0:
                if inspectionType == "correct":
                    self.stats.testCorrectSuccess += 1
                elif inspectionType == "exact":
                    self.stats.testExactSuccess += 1
                else:
                    temp = save_str[1].split("\r")
                    values = [int(s) for s in temp[0].split() if s.isdigit()]
                    if len(values) > 1:
                        self.stats.testIncorrectFailed.append(return_code[0] + "for values " + hex(int(values[0])) + hex(int(values[1])))
                    else:
                        self.stats.testIncorrectFailed.append(return_code[0] + "for value " + hex(int(values[0])))
            else:
                if inspectionType == "correct" or inspectionType == "exact":
                    self.stats.functionFailed.append(return_code[0] + "rc " + save_str[0])
                else:
                    self.stats.testIncorrectSuccess += 1
                    
    def analyze_results(self):
        pass

    def print_results(self):
        n_inspectionType = str()
        
        if self.inspectionType.find("correct") ==0 :
            n_inspectionType = "valid values"
        elif self.inspectionType.find("incorrect") ==0 :
            n_inspectionType = "invalid values"
        else:
            n_inspectionType = "extrrme values"

        if n_inspectionType == "invalid values":
            self.add_limit("Mib %s functions %s" % (self.t_property.swapcase(), n_inspectionType), 1 , 59 - len(self.stats.testIncorrectFailed) , 59, 'GE')
        else:
            self.add_limit("Mib %s functions %s" % (self.t_property.swapcase(), n_inspectionType), 1 , 59 - len(self.stats.functionFailed) , 59, 'GE')
        
        #function name , sent values
        for i in self.stats.testIncorrectFailed:
            self.add_limit("%s" % i , 0 , 1 , 1, 'EQ')
        #function name , return code
        for i in self.stats.functionFailed:
            self.add_limit("%s" % i , 0 , 1 , 1, 'EQ')
        
############ END Class TC_WlanMib_API ############

class TC_WlanMib_ERRONEOUS(TC_WlanMib_API):
    """
    @class TC_WlanMib_ERRONEOUS
    @brief Test the WlanMib API
    @author Nomi Rozenkruntz
    @version 0.1
    @date   12/21/2016
    """
    def __init__(self, methodName = 'runTest', param = None):
        super(TC_WlanMib_ERRONEOUS, self).__init__(methodName, param)
        self.extentFlag=True
        self.exactInstance = Generate_ExactValues()
        self.correctInstance = Generate_CorrectValues()
        self.inCorrectInstance = Generate_InCorrectValues()
        self._one_arg_func_dict=dict(enum="mib_configSaveStatus_t",regular=("int","int32","uint32"))
        self._two_arg_func_list=dict(fIndex=dict(regular=("int32","int","uint32"),eui48="eui48",enum=("mib_antennaStatus_t","mib_wlanDcocStatus_t",
                                             "mib_wlanPhyOFDM","mib_wlanRfTestMode_t")),
                                     int32=dict(regular=("int32","uint8")))
        self._three_arg_func_dict=dict(fIndex="fIndex",regular="char",size_t="size_t")
    
    def _generate_basic_scenario_data(self,property,inspectionType,num):
        valuesAndTypes=list()
        funcName="get_"+num+"_var_functions"
        func=getattr(self,funcName,property+" "+inspectionType)
        valuesAndTypes = func(property+" "+inspectionType)
        return valuesAndTypes

    def get_one_var_functions(self,_property_inspectionType):
       property_inspectionType=_property_inspectionType.split(" ")
       funcName="test_"+property_inspectionType[1]+"_values"    
       valAndType=list()
       func=None
       #running on the types
       for i in self._one_arg_func_dict.keys():
           if i == "enum":
               j = self._one_arg_func_dict.get(i)
               valAndType.append(i)
               func=(getattr(self,funcName,i+" "+j))
               valAndType.append(func(i+" "+j))
               continue
           #running on the values
           for j in self._one_arg_func_dict.get(i):
               valAndType.append(j)             
               func=(getattr(self,funcName,i+" "+j))
               valAndType.append(func(i+" "+j))
       return valAndType

    def get_two_var_functions(self,_property_inspectionType):

        property_inspectionType=_property_inspectionType.split(" ")
        funcName = "test_"+property_inspectionType[1]+"_values"    
        valAndType = list()
        
        #running on the first variables types
        for i in self._two_arg_func_list:
            if i == "fIndex":
                    valAndType.append(i)
                    func=getattr(self,funcName,i+" "+i)
                    valAndType.append(func(i+" "+i))
            else:
                    valAndType.append(i)
                    func=getattr(self,funcName,"regular"+" "+i)
                    valAndType.append(func("regular"+" "+i))
            #running on the types
            for k in self._two_arg_func_list.get(i):
                #running on the values
                if not k=="eui48":
                    for j in self._two_arg_func_list.get(i).get(k):
                        #this common parameters exist only for get functions
                        if property_inspectionType[0] == "set" and i == "fIndex" and (j == "mib_AntennaStatus_t" or j == "mib_wlanDcocStatus_t"):
                            continue
                        valAndType.append(j)
                        func=getattr(self,funcName,k+" "+j)
                        valAndType.append(func(k+" "+j))
            valAndType.append("eui48")
            func=getattr(self,funcName,"eui48"+" "+"eui48")
            valAndType.append(func("eui48"+" "+"eui48"))
        return valAndType

    def get_three_var_functions(self,_property_inspectionType):

       property_inspectionType=_property_inspectionType.split(" ")
       funcName="test_"+property_inspectionType[1]+"_values"    
       valAndType=list()
       #running on the types
       for i in self._three_arg_func_dict:
           #running on the values
           j= self._three_arg_func_dict.get(i)
           valAndType.append(j)
           if i == "size_t":
               i= "regular"
           func=getattr(self,funcName,i+" "+j)
           valAndType.append(func(i+" "+j))
       return valAndType

    def test_correct_values(self,typeid):
        """Test functions by sending the correct values"""
        
        _typeid=typeid.split(" ")
        funcName= "get_" + _typeid[0] + "_type"

        if _typeid[1] == "eui48" or _typeid[1] == "fIndex":
            func=getattr(self.correctInstance,funcName)
            value = func()
        elif _typeid[0] == "regular": 
            func = getattr(self.correctInstance,funcName,_typeid[0])          
            value = func(_typeid[1])
        else:
            func = getattr(self.correctInstance,funcName,_typeid[0])
            value = func(_typeid[1])
        return value

    def test_incorrect_values(self,typeid):
        """Test functions by sending incorrect entries"""
        _typeid=typeid.split(" ")
        funcName= "get_" + _typeid[0] + "_type"
        if _typeid[1] == "eui48" or _typeid[0] == "fIndex":
            func = getattr(self.inCorrectInstance,funcName)
            value = func()
        else:  
            func =  getattr(self.inCorrectInstance,funcName,_typeid[1])                         
            value = func(_typeid[1])
        return value

    def test_exact_values(self,typeid):
        """Test functions by sending precise values"""
        _typeid=typeid.split(" ")
        funcName= "get_" + _typeid[0] + "_type"        
        if self.extentFlag:
            funcName= "get_min" + "_" + _typeid[0] + "_type"
            self.extentFlag=False
        else:
            funcName= "get_max" + "_" + _typeid[0] + "_type"
            self.extentFlag=True
        if _typeid[0] == "eui48" or _typeid[0] == "fIndex":
            func = getattr(self.exactInstance,funcName)
            value = func()
        else:     
            func = getattr(self.exactInstance,funcName)                
            value = func(_typeid[1])
        return value
     
############ END Class TC_WlanMib_ERRONEOUS ############

class Generate_CorrectValues():
    """
    @class Generate_CorrectValues
    @brief Generrate Correct Values 
    @author Nomi Rozenkruntz
    @version 0.1
    @date	12/20/2016
    """
        
    def __init__(self, methodName = 'runTest', param = None):
        self._findexFlag=False
        self.regular_var_list = (dict(char=127,uint8=255,int=100,int32=100,uint32=100,size_t=65535)
                 ,dict(char=-128,uint8=0,int=0,int32=0,uint32=0,size_t=0))
    
    def create_random(self,max,min):
        value=random.randint(min,max)
        return value

    def get_regular_type(self,var_id):
        return self.create_random(self.regular_var_list[0].get(var_id),self.regular_var_list[1].get(var_id))

    def get_enum_type(self,id):
        exactInstanse = Generate_ExactValues()
        a = exactInstanse.get_min_enum_type(id)
        b = exactInstanse.get_max_enum_type(id)
        return self.create_random(b,a)

    def get_eui48_type(self):
        a = self.regular_var_list[0].get("uint8") * 8
        b = self.regular_var_list[1].get("uint8") * 8
        return self.create_random(a,b)

    def get_fIndex_type(self):
        if self._findexFlag:
            self._findexFlag = False
            return 1
        self._findexFlag = True
        return 2

############ END Class Generate_CorrectValues ############

class Generate_InCorrectValues():
    """
    @class Generate_InCorrectValues
    @brief Generate InCorrect Values
    @author Nomi Rozenkruntz
    @version 0.1
    @date	12/20/2016
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.flags=[False,False,False]
        self.exactInstance = Generate_ExactValues()
        self.regular_var_list = (dict(char=127,uint8=255,int=32767,int32=2147483646,uint32=4294967295,size_t=65535)
                 ,dict(char=-128,uint8=0,int=-32555,int32=-2147483647,uint32=0,size_t=0))
    
    def create_random(self,min,max):
        value=random.randint(min,max)
        return value

    def get_regular_type(self,var_id):
        if(self.flags[0]):
            self.flags[0]=False
            value=self.regular_var_list[1].get(var_id)
            return self.create_random(value-100,value)

        self.flags[0]=True
        value=self.regular_var_list[0].get(var_id)
        return self.create_random(value,value+100)
        
    def get_enum_type(self,id):
        if(self.flags[1]):
            self.flags[1]=False
            value=self.exactInstance.get_min_enum_type(id)
            return self.create_random(value-10,value)

        self.flags[1]=True
        value=self.exactInstance.get_max_enum_type(id)
        return self.create_random(value,value+10)

    def get_fIndex_type(self):
        if(self.flags[2]):
            self.flags[2]=False
            return self.create_random(-9,1)

        self.flags[2]=True
        return self.create_random(2,10)
    
    def get_eui48_type(self):
        return self.get_regular_type("uint8") * 8
      
############ END Class Generate_InCorrectValues ############

class Generate_ExactValues():
    """
    @class Generate_ExactValues
    @brief Generate Exact Values
    @author Nomi Rozenkruntz
    @version 0.1
    @date	12/19/2016
    """
    def __init__(self, methodName = 'runTest', param = None):
        self.regular_var_list = (dict(char=127,uint8=255,int=100,int32=100,uint32=100,size_t=65535)
                 ,dict(char=-128,uint8=0,int=0,int32=0,uint32=0,size_t=0))
   
    def get_min_eui48_type(self):
        return self.regular_var_list[0].get("uint8") * 8

    def get_max_eui48_type(self):
        return self.regular_var_list[1].get("uint8") * 8

    def get_min_fIndex_type(self):
        return 1

    def get_max_fIndex_type(self):
        return 2

    def get_min_enum_type(self,enum_name):
        if enum_name=="mib_wlanPhyOFDM":
            return 1
        else:
            return 0

    def get_max_enum_type(self,enum_name):
        if enum_name=="mib_configSaveStatus_t":
            return 5
        elif enum_name=="mib_antennaStatus_t":
            return 4
        elif enum_name=="mib_wlanDcocStatus_t":
            return 3
        elif enum_name=="mib_wlanPhyOFDM": 
            return 2
        elif enum_name=="mib_wlanRfTestMode_t":
            return 1

    def get_min_regular_type(self,key):
        return self.regular_var_list[0].get(key)

    def get_max_regular_type(self,key):
        return self.regular_var_list[1].get(key)
         
############ END Class Generate_ExactValues ############

class TC_WlanMib_LOAD(TC_WlanMib_API):
    """
    @class TC_WlanMib_LOAD
    @brief Load tests on the Wlan Mib API
    @author Nomi Rozenkruntz
    @version 0.1
    @date	12/22/2016
    """

    def __init__(self, methodName = 'runTest', param = None):
        super(TC_WlanMib_LOAD, self).__init__(methodName, param)
        self.loudWlanMib_cli

    def get_test_parameters( self ):
        super(TC_WlanMib_LOAD, self).get_test_parameters()
        
    def tearDown(self):
        super(TC_WlanMib_LOAD, self).tearDown()

    def unit_configuration(self):
        super(TC_WlanMib_LOAD, self).unit_configuration()

        self.loudWlanMib_cli = self.uut.create_qa_cli("loudWlanMib_cli",  target_cpu = self.target_cpu)
        
        self.wlanMib_cli.link.reset_counters()


    def main(self):
        try:
            thread_list = []

            txThread = threading.Thread(target=self._tx_frames_thread,args=(self.uut_wlanMib_if[0].port,self._tx_rate_hz,))
            thread_list.append(txThread)

            rxThread = threading.Thread(target=self._rx_frames_thread,args=(self.uut_wlanMib_if[0].port,))
            thread_list.append(rxThread) 

            #transmit
            rxThread.start()

            ret = self.wlanMib_cli.transmit_loud(frames = self._frames_num,rate_hz=self.dut_tx_rate_hz,err_part=self._err_part)

        except Exception as e:
            raise e
        
        # wait for threads.
        for thread in thread_list:
            thread.join()

        txThread.join()
        rxThread.join()

    def print_results(self):
        self.add_limit("Test Correct Values Success ", 0 , self.stats.testCorrectSuccess , 0 , 'GE')
        self.add_limit("Test InCorrect values Success ", 0 , self.stats.testIncorrectSuccess , 0 , 'GE')
        self.add_limit("Test Exact Values Success ", 0 , self.stats.testExactSuccess , 0 , 'GE')
        for i in self.stats.functionFailed:
            self.add_limit("Function Failed " + i , 0 , 1 , 0, 'QE')

########### END class TC_WlanMib_LOAD ##########

class Statistics(object):

    def __init__(self):
        #reset counters
        self.testCorrectSuccess = 0
        self.testExactSuccess = 0 
        self.testIncorrectSuccess = 0
        self.testIncorrectFailed = list()
        self.functionFailed = list()
        
if __name__ == "__main__":

    # Receiving Wlan Mib API
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
    suite.addTest(common.ParametrizedTestCase.parametrize(TC_WlanMib_API, param = test_param ))

    

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
 

