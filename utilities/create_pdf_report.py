from reportlab.lib.pagesizes import letter, A4, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, SimpleDocTemplate, Spacer,Table, TableStyle, Image
from reportlab.rl_config import defaultPageSize
#from reportlab.platypus import *
from reportlab.lib import colors
import time
from time import ctime 
import csv
import os
import sys
import ast
from lib import globals, setup_consts

# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)

title = "<font size=16><b>Calibration tests report<b></font>"
header = [  "<b>Report No.:<b>",
            "<b>P/N:<b>",
            "<b>SDK version:<b>",
            "<b>S/N:<b>",
            "<b>GPS ver.:<b>",
            "<b>Calibration date:<b>",
            "<b>Temperature conditions:<b>",
            "<b>IP address:<b>"]
            #"<b>MAC address:<b>"]
#Description = """Calibration test report description ..."""

sub1 = "General" 
sub2 = "System tests" 
sub3 = "GPS/Tablet connection" 

res_titles = ["Test name", "Measured result chA", "Measured result chB", "Expected result", "Units", "Status"]   
connections_titles = ["Function", "Status", "Details"]
gps_status = ["GPS lock", "Pass", "Pass"]
wifi_pairing = ["WiFi pairing", "Pass", "Pass"]


results_template = [ ['Tx EVM @20dBm', 'N/A', 'N/A', '<-23.00', 'dB', 'Fail'],
                     ['Tx Power @20dBm', 'N/A', 'N/A', u'20.00\xb11', 'dBm', 'Fail'],
                     ['LO leakage @20dBm', 'N/A', 'N/A', '<-22.00', 'dBc', 'Fail'],
                     ['Tx IQ imbalance ampl', 'N/A', 'N/A', u'\xb10.20', 'dB', 'Fail'],
                     ['Tx IQ imbalance phase', 'N/A', 'N/A', u'\xb10.50', 'deg', 'Fail'],
                     ['Tx Frequency error', 'N/A', 'N/A', u'\xb1117.00', 'kHz', 'Fail'],
                     ['Tx Symbol clock error', 'N/A', 'N/A', u'\xb120.00', 'ppm', 'Fail'],
                     ['Rx EVM@-55dbm', 'N/A', 'N/A', '<-22.0', 'dB', 'Fail'],
                     ['Sensitivity (6,12)Mbps', "['N/A', 'N/A']", "['N/A', 'N/A']", '<(-91.00,-85.00)', 'dB', 'Fail'] ]



localtime = time.asctime(time.localtime(time.time()))

details = ['N/A','N/A','N/A', 'N/A', 'N/A', 'N/A', str(localtime),'N/A', 'N/A', 'N/A'] 
 
########################################################################
class Report(object):
    """ 
    Class: Report
    Brief: Creating report pdf type from test results, input: list test results and setup details, output: pdf file
    Author: Daniel Shiper
    Version: 0.1
    Date: 10.2014
    """
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        #self.width, self.height = letter
        self.width, self.height = A4
        self.styles = getSampleStyleSheet()
 
    #----------------------------------------------------------------------
    def coord(self, x, y, unit=1):
        x, y = x * unit, self.height -  y * unit
        return x, y
 
    #----------------------------------------------------------------------
    #def run(self, newpath, general, results, sn, details, lo_leakage_res, dc_dac_res, sample_gain_res, rep_internal = False):
    #def run(self, logpath, results_dict, sn, details, lo_leakage_res, dc_dac_res, sample_gain_res, rep_internal = False):
    def run(self, logpath, test_data_dir, results, ver_info, serial_number, rep_internal = True):
        """
        Run the report
        """
        """
        self.gen_data = general
        #self.results = results 
        self.results = []
        #self.conn_data = conn
        self.sn = sn
        self.path = logpath
        self.story =[]
        self.details = details
        self.additional_res_lo = lo_leakage_res
        self.additional_res_dc = dc_dac_res
        self.sample_gain_res = sample_gain_res
        """
        self.internal = rep_internal
        self.path = logpath
        self.test_data_dir = test_data_dir
        #self.results = results
        self.rn = results['board_number']
        self.ver_info = ver_info
        self.serial_number = serial_number
        self.details = [ results['board_number'],
                         results['board_number'],
                        self.ver_info,
                        self.serial_number,
                        results['gps_version'],
                        ctime(),
                        '25C',
                        results['board_IP']]
        self.connections = []
        self.connections.append(connections_titles)
        self.connections.append(gps_status)
        self.connections.append(wifi_pairing)


        self.results = [ ['Tx EVM @20dBm', ast.literal_eval(results['ch_0 tx evm@20dBm'])[0] if 'ch_0 tx evm@20dBm' in results else 'N/A', ast.literal_eval(results['ch_1 tx evm@20dBm'])[0] if 'ch_1 tx evm@20dBm' in results else 'N/A', '<-23.00', 'dB', 'Pass' if ast.literal_eval(results['ch_0 tx evm@20dBm'])[1] & ast.literal_eval(results['ch_1 tx evm@20dBm'])[1] else 'Fail' ],
                             ['Tx Power @20dBm', ast.literal_eval(results['ch_0 tx power@20dBm'])[0] if 'ch_0 tx power@20dBm' in results else 'N/A', ast.literal_eval(results['ch_1 tx power@20dBm'])[0] if 'ch_1 tx power@20dBm' in results else 'N/A', u'20.00\xb11', 'dBm', 'Pass' if ast.literal_eval(results['ch_0 tx power@20dBm'])[1] & ast.literal_eval(results['ch_1 tx power@20dBm'])[1] else 'Fail'],
                             ['LO leakage @20dBm', ast.literal_eval(results['ch_0 dc lo leakage'])[0] if 'ch_0 dc lo leakage' in results else 'N/A', ast.literal_eval(results['ch_1 dc lo leakage'])[0] if 'ch_1 dc lo leakage' in results else 'N/A', '<-22.00', 'dBc', 'Pass' if ast.literal_eval(results['ch_0 dc lo leakage'])[1] & ast.literal_eval(results['ch_1 dc lo leakage'])[1] else 'Fail'],
                             ['Tx IQ imbalance ampl', ast.literal_eval(results['ch_0 iq imbalance amplitude error'])[0] if 'ch_0 iq imbalance amplitude error' in results else 'N/A', ast.literal_eval(results['ch_1 iq imbalance amplitude error'])[0] if 'ch_1 iq imbalance amplitude error' in results else 'N/A', u'\xb10.20', 'dB', 'Pass' if ast.literal_eval(results['ch_0 iq imbalance amplitude error'])[1] & ast.literal_eval(results['ch_1 iq imbalance amplitude error'])[1] else 'Fail'],
                             ['Tx IQ imbalance phase', ast.literal_eval(results['ch_0 iq imbalance phase error'])[0] if 'ch_0 iq imbalance phase error' in results else 'N/A', ast.literal_eval(results['ch_1 iq imbalance phase error'])[0] if 'ch_1 iq imbalance phase error' in results else 'N/A', u'\xb10.50', 'deg', 'Pass' if ast.literal_eval(results['ch_0 iq imbalance phase error'])[1] & ast.literal_eval(results['ch_1 iq imbalance phase error'])[1] else 'Fail'],
                             ['Tx Frequency error', ast.literal_eval(results['ch_0 frequency error'])[0] if 'ch_0 frequency error' in results else 'N/A', ast.literal_eval(results['ch_1 frequency error'])[0] if 'ch_1 frequency error' in results else 'N/A', u'\xb1117.00', 'kHz', 'Pass' if ast.literal_eval(results['ch_0 frequency error'])[1] & ast.literal_eval(results['ch_1 frequency error'])[1] else 'Fail'],
                             ['Tx Symbol clock error', ast.literal_eval(results['ch_0 symbol clock error'])[0] if 'ch_0 symbol clock error' in results else 'N/A', ast.literal_eval(results['ch_1 symbol clock error'])[0] if 'ch_1 symbol clock error' in results else 'N/A', u'\xb120.00', 'ppm', 'Pass' if ast.literal_eval(results['ch_0 symbol clock error'])[1] & ast.literal_eval(results['ch_1 symbol clock error'])[1] else 'Fail'],
                             ['Rx EVM@-55dbm', ast.literal_eval(results['ch_0 rx evm@-55dBm'])[0] if 'ch_0 rx evm@-55dBm' in results else 'N/A', ast.literal_eval(results['ch_1 rx evm@-55dBm'])[0] if 'ch_1 rx evm@-55dBm' in results else 'N/A', '<-22.0', 'dB', 'Pass' if ast.literal_eval(results['ch_0 rx evm@-55dBm'])[1] & ast.literal_eval(results['ch_1 rx evm@-55dBm'])[1] else 'Fail'],
                             ['Sensitivity (6,12)Mbps', str([ast.literal_eval(results['ch_0 rate 6Mbps sensitivity point'])[0] if 'ch_0 rate 6Mbps sensitivity point' in results else 'N/A', ast.literal_eval(results['ch_0 rate 12Mbps sensitivity point'])[0] if 'ch_0 rate 12Mbps sensitivity point' in results else 'N/A']), str([ast.literal_eval(results['ch_1 rate 6Mbps sensitivity point'])[0] if 'ch_1 rate 6Mbps sensitivity point' in results else 'N/A', ast.literal_eval(results['ch_1 rate 12Mbps sensitivity point'])[0] if 'ch_1 rate 12Mbps sensitivity point' in results else 'N/A']), '<(-91.00,-85.00)', 'dB', 'Pass' if ast.literal_eval(results['ch_0 rate 6Mbps sensitivity point'])[1] & ast.literal_eval(results['ch_0 rate 12Mbps sensitivity point'])[1] & ast.literal_eval(results['ch_1 rate 6Mbps sensitivity point'])[1] & ast.literal_eval(results['ch_1 rate 12Mbps sensitivity point'])[1] else 'Fail'] ]

        if self.internal:
            pass
        else:
            # Remove not relevant fields from internal report
            self.results.remove(self.results[3])
            self.results.remove(self.results[3])
            self.results.remove(self.results[3])
            self.results.remove(self.results[3])
        
        try:
            if not (os.path.exists(self.path)):
                os.makedirs(self.path)
                print "Created new directory : ", self.path           
        except:
            print "Can't create the directoty :", self.path        

        report_name_file = '{}\LabReport_{}' .format( self.path, self.rn)
        self.doc = SimpleDocTemplate(report_name_file + '_internal.pdf') if self.internal else SimpleDocTemplate(report_name_file + '.pdf')
        self.story = [Spacer(1, 2.5*inch)]
        
        self.doc.build(self.story, onFirstPage=self.create_document)
        print "..Finished!\n"
 
    #----------------------------------------------------------------------
    def create_document(self, canvas, doc):
        """
        Create the document
        """
        self.c = canvas
        normal = self.styles["Normal"]

        # Load logo file
        logo_name = self.test_data_dir + "firm_logo.jpg"

        logo_file = os.path.join(self.test_data_dir, logo_name)
        im = Image(logo_file, width=2.0*inch, height=0.9*inch)
        #im.hAlign = 'RIGHT'
        
        im.wrapOn(self.c, self.width, self.height)
        im.drawOn(self.c, *self.coord(15.7, 2.3, cm))
        #self.story.append(im)

        p = Paragraph(title, normal)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, *self.coord(8, 2.5, cm))
        #self.c.line(128,121,328,121)
        

        #Create header
        i = 40
        j = 0
        for field in header:
            p = Paragraph(field, normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(10, i, mm))
            p = Paragraph(str(self.details[j]), normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(60, i, mm))
            i=i+5   # Adding 5 mm between header lines
            j=j+1


        font_size = 12

        # List of report subtitles sections
        sub_titles = [sub2, sub3]
        
        point = 0
        # Set table y coordinates
        if self.internal:
            shift = 11
            table2_coordinate_cm = 16
            table3_coordinate_cm = 22.6
        else:
            shift = 9
            table2_coordinate_cm = 13.5
            table3_coordinate_cm = 20.6

        for item in sub_titles:
            text = "<font size=%s><b>%s</b></font>" % (font_size,item)
            p = Paragraph(text, style=normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(1, point+9.5, cm))
            point = point + shift

        '''
        # General Table 1 - Not used
        #self.results = [["Test name", "Measured result", "Expected result", "Units", "Status"], ["TX output power", "20", "20", "dBm", "Pass"],["TX EVM", "-23", "-20", "dBm", "Pass"]]
        tableONE = Table(self.gen_data, colWidths=[4.55 * cm, 3 * cm, 3 * cm, 3* cm, 3 * cm])
        
        tableONE.setStyle(TableStyle([
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black)
                       ]))
        
        tableONE.wrapOn(self.c, self.width, self.height)
        tableONE.drawOn(self.c, *self.coord(1.8, 13.5, cm))
        '''

        
        # System tests Table 2
        #tableTWO = Table(self.results.insert(0,res_titles), colWidths=[4.15 * cm, 3.7 * cm, 3.7 * cm, 2.9 * cm, 1.7* cm, 1.7 * cm])
        self.results.insert(0,res_titles)
        tableTWO = Table(self.results, colWidths=[4.15 * cm, 3.7 * cm, 3.7 * cm, 2.9 * cm, 1.7* cm, 1.7 * cm])

        tableTWO.setStyle(TableStyle([
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black)
                       ]))
        
        tableTWO.wrapOn(self.c, self.width, self.height)
        tableTWO.drawOn(self.c, *self.coord(1.7, table2_coordinate_cm, cm))

        # GPS/WiFi pairing tests Table 3
        tableTHREE = Table(self.connections, colWidths=[4.25 * cm, 3 * cm, 3 * cm, 3 * cm, 1.7* cm, 1.7 * cm])
        
        tableTHREE.setStyle(TableStyle([
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black)
                       ]))
        
        tableTHREE.wrapOn(self.c, self.width, self.height)
        tableTHREE.drawOn(self.c, *self.coord(1.7, table3_coordinate_cm, cm))

        """
        # Additional measurements results for internal use
        if self.internal:
            # Add text lines - LO leakage results
            point = 0
            #text_line = "<font size=%s><b>%s</b></font>" % (font_size-2,self.additional_res)
            text_LO_0 = " * LO leakage at TX output power " + str(consts.common['LO_LEAKAGE_POW_LIST_DBM']) + "dBm chA"
            text_LO_1 = " * LO leakage at TX output power " + str(consts.common['LO_LEAKAGE_POW_LIST_DBM']) + "dBm chB"
            text_line_0 = "<font size=%s>%s:  %s</font>" % (font_size-4,text_LO_0,self.additional_res_lo[0])
            text_line_1 = "<font size=%s>%s:  %s</font>" % (font_size-4,text_LO_1,self.additional_res_lo[1])       
            p = Paragraph(text_line_0, style=normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(1.7, 17.8, cm))

            p = Paragraph(text_line_1, style=normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(1.7, 18.3, cm))

            # Add text lines - DC DAC results
            text_DC = " * DC DAC regs " + str(consts.common['RX1_DC_IQ_REGS_HEX'] + consts.common['RX2_DC_IQ_REGS_HEX']) + " status"
            text_line = "<font size=%s>%s:  %s</font>" % (font_size-4,text_DC,self.additional_res_dc)       
            p = Paragraph(text_line, style=normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(1.7, 18.8, cm))

            # Add text lines - Sample gain results
            text_sg = " * Sample gain results [chA,chB]"
            text_line = "<font size=%s>%s:  %s</font>" % (font_size-4,text_sg,str(self.sample_gain_res))       
            p = Paragraph(text_line, style=normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(1.7, 19.3, cm))
        else:
            pass
        """
    #----------------------------------------------------------------------
    # Not in use
    def createLineItems(self):
        """
        Create the line items
        """
        text_data = ["Test name", "Measured result", "Expected",
                     "Units", "Status"]

        d = []
        font_size = 9
        
        centered = ParagraphStyle(name="centered", alignment=TA_CENTER)
        
        for text in text_data:
            ptext = "<font size=%s><b>%s</b></font>" % (font_size, text)
            p = Paragraph(ptext, centered)
            d.append(p)
        
        data = [d]
 
        line_num = 1
 
        formatted_line_data = []
 
        for x in range(10):
            line_data = ["TX output power", "20", 
                         "20", "dBm", "Pass"]
 
            for item in line_data:
                ptext = "<font size=%s>%s</font>" % (font_size-1, item)
                p = Paragraph(ptext, centered)
                formatted_line_data.append(p)
            data.append(formatted_line_data)
            formatted_line_data = []
            line_num += 1
 
        table = Table(data, colWidths=[200, 100, 100, 100, 60])
 
        self.story.append(table)
 
'''
#----------------------------------------------------------------------
if __name__ == "__main__":
    results =[["Test name", "Measured result", "Expected result", "Units", "Status"], ["TX output power", "20", "20", "dBm", "Pass"],["TX EVM", "-23", "-20", "dBm", "Pass"]]
    t = ReportInternal()
    t.run(results)
'''