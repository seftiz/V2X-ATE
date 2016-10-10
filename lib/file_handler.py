import sys, os
#from utilities import consts
import ConfigParser



class File_Handler(object): 
    """ 
    Class: File_Handler
    Brief: File handler is based on ConfigParser module, provides structured file for an easy customization of test results. Configuration by sections header followed by names 
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """

    def initialize(self, final_res_file):
        # Initialaze Results file
        ResultsFileHandler = ConfigParser.RawConfigParser()
    
        if (os.path.exists(final_res_file)):            
            print "Note: File exist....the results will be added to the existing file"
            #ResFileName = open(final_res_file,"r+")  # open for reading and writing
        else:

            # Open results file for adding sections
            ResFileName = open(final_res_file,"a+") 
            ResultsFileHandler.read(final_res_file)
            sections_list = ["DCOC DAC registers","Sample_Gain","LO leakage results","Sensitivity test","Report details","Final results"]
            for i in sections_list:
                if ResultsFileHandler.has_section(i) == False:
                    ResultsFileHandler.add_section(i)
           
            # Preparing results section 
            index = 0
            for z in consts.expected['REPORT_LIST_ROWS'][:(len(consts.expected['REPORT_LIST_ROWS']))-1]:
                ResultsFileHandler.set('Final results',"chA "+z,"N/A")
                ResultsFileHandler.set('Final results',"chB "+z,"N/A")
                index +=1 

            ResultsFileHandler.set('Sample_Gain', "chA_(hex,dB)", "N/A")
            ResultsFileHandler.set('Sample_Gain', "chB_(hex,dB)", "N/A")
            ResultsFileHandler.set('LO leakage results', "LO_leak_chA", "N/A")
            ResultsFileHandler.set('LO leakage results', "LO_leak_chB", "N/A")
            ResultsFileHandler.set('Report details', "ethernet address", "N/A")
            ResultsFileHandler.set('Sensitivity test', "sensitivity_cha", "N/A")
            ResultsFileHandler.set('Sensitivity test', "sensitivity_chb", "N/A")
            ResultsFileHandler.set('Report details', "sdk version", "N/A")
            ResultsFileHandler.set('Report details', "uboot version", "N/A")

            dc_iq_reg_list = [consts.register['RX1_DC_IQ_0_HEX'],consts.register['RX1_DC_IQ_1_HEX'],consts.register['RX1_DC_IQ_4_HEX'],consts.register['RX1_DC_IQ_6_HEX'],consts.register['RX2_DC_IQ_0_HEX'],consts.register['RX2_DC_IQ_1_HEX'],consts.register['RX2_DC_IQ_4_HEX'],consts.register['RX2_DC_IQ_6_HEX']]
            for i in range(0,len(dc_iq_reg_list)):
                ResultsFileHandler.set("DCOC DAC registers",str(hex(dc_iq_reg_list[i])), "N/A")

            #Write added sections to file
            try:
                print "Preparing results file.."
                with ResFileName as file:
                    ResultsFileHandler.write(file)
            except IOError:
                print "Can't open file..Please check the file"
            ResFileName.close()