from reportlab.lib.pagesizes import letter, A4, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle, TA_CENTER
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, SimpleDocTemplate, Spacer,Table, TableStyle, Image
from reportlab.rl_config import defaultPageSize
#from reportlab.platypus import *
from reportlab.lib import colors
import time
import csv
import os
import sys

# Get current main file path and add to all searchings
dirname, filename = os.path.split(os.path.abspath(__file__))
# add current directory
sys.path.append(dirname)

Title = "<font size=16><b>Calibration tests report<b></font>"
Header = [  "<b>Report No.:<b>",
            "<b>P/N:<b>",
            "<b>SDK version:<b>",
            "<b>S/N:<b>",
            "<b>GPS ver.:<b>",
            "<b>Calibration date:<b>",
            "<b>Temperature conditions:<b>",
            "<b>IP address:<b>",
            "<b>MAC address:<b>"]
#Description = """Calibration test report description ..."""

Sub1 = "General" 
Sub2 = "System tests" 
Sub3 = "GPS/Tablet connection" 

localtime = time.asctime(time.localtime(time.time()))

#Details = [1,'Pangaea4 (ATK22016)','3.1','0001','0.1',str(localtime),'25C','10.10.0.226','00:00:00:00:00:00']
 
 
########################################################################
class ReportInternal(object):
    """"""
 
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
    def run(self, newpath, general, results, conn, SN, Details, LO_leakage_res, DC_DAC_res, sample_gain_res):
        """
        Run the report
        """
        self.gen_data = general
        self.text_data = results 
        self.conn_data = conn
        self.SN = SN
        self.path = newpath
        self.story =[]
        self.Details = Details
        self.additional_res_LO = LO_leakage_res
        self.additional_res_DC = DC_DAC_res
        self.sample_gain_res = sample_gain_res

        try:
            if not (os.path.exists(self.path)):
                os.makedirs(self.path)
                print "Created new directory : ", self.path           
        except:
            print "Can't create the directoty :", self.path        
        
        #self.doc = SimpleDocTemplate(r'C:\Local\wavesys\trunk\lab_utils\Test_Environment\logs\LabReport_'+str(self.SN)+".pdf")
        self.doc = SimpleDocTemplate(self.path + "\LabReport_"+ str(self.SN)+'_internal'+'.pdf')
        self.story = [Spacer(1, 2.5*inch)]
        
        self.doc.build(self.story, onFirstPage=self.createDocument)
        print "..Finished!\n"
 
    #----------------------------------------------------------------------
    def createDocument(self, canvas, doc):
        """
        Create the document
        """
        self.c = canvas
        normal = self.styles["Normal"]
        
        # Load logo file
        logo_name = "firm_logo.jpg"
        #current_dir = os.getcwd() # returns current working directory of a process
        #logo_dir_name = "%s\\utilities\\" % dirname
        logo_file = os.path.join(dirname, logo_name)
        #im = Image(r'C:\Local\wavesys\trunk\lab_utils\Test_Environment\Tools\Pic1.jpg', width=2.0*inch, height=0.9*inch)
        im = Image(logo_file, width=2.0*inch, height=0.9*inch)
        #im.hAlign = 'RIGHT'
        
        im.wrapOn(self.c, self.width, self.height)
        im.drawOn(self.c, *self.coord(15.7, 2.3, cm))
        #self.story.append(im)

        p = Paragraph(Title, normal)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, *self.coord(8, 2.5, cm))
        #self.c.line(128,121,328,121)
        

        #Create header
        i = 40
        j = 0
        for field in Header:
            p = Paragraph(field, normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(10, i, mm))
            p = Paragraph(str(self.Details[j]), normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(60, i, mm))
            i=i+5
            j=j+1


        font_size = 12
        
        SubTitles = [Sub2,Sub3]
        
        point = 0
        for item in SubTitles:
            text = "<font size=%s><b>%s</b></font>" % (font_size,item)
            p = Paragraph(text, style=normal)
            p.wrapOn(self.c, self.width, self.height)
            p.drawOn(self.c, *self.coord(1, point+9, cm))
            point = point+11

        '''
        # General Table 1 - Not used
        #self.text_data = [["Test name", "Measured result", "Expected result", "Units", "Status"], ["TX output power", "20", "20", "dBm", "Pass"],["TX EVM", "-23", "-20", "dBm", "Pass"]]
        tableONE = Table(self.gen_data, colWidths=[4.55 * cm, 3 * cm, 3 * cm, 3* cm, 3 * cm])
        
        tableONE.setStyle(TableStyle([
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black)
                       ]))
        
        tableONE.wrapOn(self.c, self.width, self.height)
        tableONE.drawOn(self.c, *self.coord(1.8, 13.5, cm))
        '''
        
        # System tests Table 2
        tableTWO = Table(self.text_data, colWidths=[4.15 * cm, 3.7 * cm, 3.7 * cm, 2.9 * cm, 1.7* cm, 1.7 * cm])
        
        tableTWO.setStyle(TableStyle([
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black)
                       ]))
        
        tableTWO.wrapOn(self.c, self.width, self.height)
        tableTWO.drawOn(self.c, *self.coord(1.7, 16.9, cm))

        # GPS/WiFi pairing tests Table 3
        tableTHREE = Table(self.conn_data, colWidths=[4.25 * cm, 3 * cm, 3 * cm, 3 * cm, 1.7* cm, 1.7 * cm])
        
        tableTHREE.setStyle(TableStyle([
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black)
                       ]))
        
        tableTHREE.wrapOn(self.c, self.width, self.height)
        tableTHREE.drawOn(self.c, *self.coord(1.7, 22.6, cm))


        # Add text lines - LO leakage results
        point = 0
        #text_line = "<font size=%s><b>%s</b></font>" % (font_size-2,self.additional_res)
        text_LO_0 = " * LO leakage at TX output power [23,20,15,12,10,8,5]dBm chA"
        text_LO_1 = " * LO leakage at TX output power [23,20,15,12,10,8,5]dBm chB"
        text_line_0 = "<font size=%s>%s:  %s</font>" % (font_size-4,text_LO_0,self.additional_res_LO[0])
        text_line_1 = "<font size=%s>%s:  %s</font>" % (font_size-4,text_LO_1,self.additional_res_LO[1])       
        p = Paragraph(text_line_0, style=normal)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, *self.coord(1.7, 17.8, cm))

        p = Paragraph(text_line_1, style=normal)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, *self.coord(1.7, 18.3, cm))

        # Add text lines - DC DAC results
        text_DC = " * DC DAC regs hex[1070,1071,1074,1076,1370,1371,1374,1376] status"
        text_line = "<font size=%s>%s:  %s</font>" % (font_size-4,text_DC,self.additional_res_DC)       
        p = Paragraph(text_line, style=normal)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, *self.coord(1.7, 18.8, cm))

        # Add text lines - Sample gain results
        text_sg = " * Sample gain results [chA,chB]"
        text_line = "<font size=%s>%s:  %s</font>" % (font_size-4,text_sg,str(self.sample_gain_res))       
        p = Paragraph(text_line, style=normal)
        p.wrapOn(self.c, self.width, self.height)
        p.drawOn(self.c, *self.coord(1.7, 19.3, cm))

    #----------------------------------------------------------------------
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