import os
import math
import struct
import time
import logging
import sys

InitialValA = 1
InitialValB = 1
InitialValC = 0


#EvmAverageCnt = 5

log = logging.getLogger(__name__)

class IQImbalance:
    def __init__(self):
        #self._evkRX = None
        self._factorsDict = []
        self._est = []
        self._factorsDict.append({'Kest':1, 'Pest':math.radians(0)})
        logging.basicConfig()


    def Open(self, regs, macIf):
        self.macIf = macIf
        #self._evkRX = EvkDUT_RssiEVM
        self.regs = regs

        '''
        for analysis_control in self._evkRX.AnalysisControlList:
            analysis_control.StopRFTemperaturePolling()
        '''
        # adaptive noise threshold to 7,7
        #self._evkRX.PhyControl.WriteRegister(0x151, 0xa032812c)
        # set gain
        #self._evkRX.PhyControl.WriteRegister(0x23, 0x16)
        #self._evkRX.ChannelControl.WriteRegister(0x2, 0xd6)    

    def Destroy(self):
        '''
        self._evkRX.CloseConnection()
        self._evkRX.Destroy()
        '''
    def Run(self,N,numOfIter):    
        finalA = 0
        finalB = 0
        finalC = 0

        for i in xrange(numOfIter):
            A, B, C = self.Itteration(N)
            if A == 0 or B == 0 or C == 0:
                print "Failed at IQimbalance"
                return
            #finalA = self._ConvertToFormat(10, 8, -A)
            finalA = self._ConvertToFormat(10, 8, A)
            finalB = self._ConvertToFormat(15, 13, B)
            finalC = self._ConvertToFormat(15, 13, C)

            print "Iteration %d:  A 0x%x, B 0x%x, C 0x%x " % (
                i, finalA, finalB, finalC), finalA
            if (i == 0):
                self.regs.set_reg(("phy"+str(self.macIf), 0x14c),finalA)
                self.regs.set_reg(("phy"+str(self.macIf), 0x14d),finalB << 16 | finalC)
                Aprv = A
                Bprv = B
                Cprv = C

            else:
                finalA, finalB, finalC = self._SetFactorsDelta(A, B, C, Aprv, Bprv, Cprv)
                finalA = self._ConvertToFormat(10, 8, finalA)
                finalB = self._ConvertToFormat(15, 13, finalB)
                finalC = self._ConvertToFormat(15, 13, finalC)
                
                Aprv = A
                Bprv = B
                Cprv = C

                self.regs.set_reg(("phy"+str(self.macIf), 0x14c),finalA)
                self.regs.set_reg(("phy"+str(self.macIf), 0x14d),finalB << 16 | finalC)
            reg14c = self.regs.get_reg(("phy"+str(self.macIf), 0x14c))
            reg14d = self.regs.get_reg(("phy"+str(self.macIf), 0x14d))
            print "reg 0x14c ",str(hex(reg14c))
            print "reg 0x14d ",str(hex(reg14d))
        print "Final:  Amp 0x%x, phase 0x%x " % (finalA,( finalB<<16 | finalC))

        self.WriteCalibrationFactors2File(finalA, finalB, finalC)
        return (finalA, finalB ,finalC)

    def _SetFactorsDelta(self, A, B, C, Aprv, Bprv, Cprv):
         # iq sign issue!!!!
         Adelta = A - InitialValA + Aprv
         Bdelta = B - InitialValB + Bprv
         Cdelta = C - InitialValC + Cprv
         print "Delta A %f B %f C %f" % (Adelta, Bdelta, Cdelta)
         return Adelta, Bdelta, Cdelta
    
    def Itteration(self,N):
        Kest, Pest = self.CalcAverageKesPest(N)
        if Kest == 0 or Pest == 0:
            return 0, 0, 0
        A, B, C = self.CalcFactors(Kest, Pest)
        log.info("FACTORS: A=0x%x B=0x%x C=0x%x",
                 #self._ConvertToFormat(10, 8, -A),
                 self._ConvertToFormat(10, 8, A), 
                 self._ConvertToFormat(15, 13, B), 
                 self._ConvertToFormat(15, 13, C))
        #log.info("EVM: %f", self._evkRX.ChannelControlList[self.macIf].EvmCalc(EvmAverageCnt))

        return A, B, C
        
    def CalcFactors(self,Kest,Pest):
        A = (1 / Kest)
        B = 1 / math.sqrt(1-math.pow(Pest,2))
        #B = math.pow(Pest,2)
        C = (A * Pest) 
        print "Pre convert A B C", A, B, C
        return A, B, C


    def WriteCalibrationFactors2File(self,A,B,C):    
        calibFile = open('rf_cfg.txt', 'a')
        if calibFile == None:
            log.error("Error opening file rf_cfg.txt")
            return

        calibFile.write("#IQ imbalance calibration factors\n")
        calibFile.write("iq_imbalance_calibration_factor_A = %x\n" % (A))
        calibFile.write("iq_imbalance_calibration_factor_B = %x\n" % (B))
        calibFile.write("iq_imbalance_calibration_factor_C = %x\n" % (C))  
        calibFile.close

  
    def _ConvertFromFormat(self, domain, precision, is_signed, value):
        cvalue = value
        if is_signed:
            if (cvalue & (1 << (domain - 1)) != 0):
                cvalue = -1 * ((1 << domain) - cvalue)
        return float(cvalue) / (1 << precision)


    def _ConvertToFormat(self, domain, precision, val):
        val = int(val * (1 << precision))
        if val < 0:
            val = (1 << domain) - abs(val)
        return val

    def CalcAverageKesPest(self, iterNum):
        alphaTotal = 0 
        betaTotal = 0 
        gammaTotal = 0 
        actualIters = 0
        for i in xrange(iterNum):
            '''
            self._evkRX.ChannelControlList[self.macIf].IQImbalanceSetHwTrigger()   #Read 0x166 to clear the done bit, write 0x163  bit[0] = 1
            time.sleep(0.7)
            ret = self._evkRX.ChannelControlList[self.macIf].IQImbalanceGet()
            '''
            done_iter = 0
            while True:
                ctrl_reg = self.regs.get_reg(("phy"+str(self.macIf), 0x163))

                if ctrl_reg & 0x2 != 0:
                    break
                done_iter+=1
                if done_iter > 10000:
                    print "rPHY_IQ_CALIB_CTRL reg not ready after 10000 iterations"
                    return None


            valA = self.regs.get_reg(("phy"+str(self.macIf), 0x164))
            valB = self.regs.get_reg(("phy"+str(self.macIf), 0x165))
            valC = self.regs.get_reg(("phy"+str(self.macIf), 0x166))
            if valA == 2:
                continue
            
            print "ValA, ValB, ValC: ",valA,valB,valC
            
            self.regs.set_reg(("phy"+str(self.macIf), 0x163), 1)

            if valA == 0  and valB == 0 and valC == 0:
                print "Could not get IQ values, skip iteration"
                continue

            if (valA != None and valB != None and valC != None):
                #alpha,beta,gamma = ret
                alpha, beta, gamma = valA, valB, valC
                alphaTotal += self._ConvertFromFormat(32, 24, False, alpha)
                betaTotal += self._ConvertFromFormat(32, 24, False, beta)
                gammaTotal += self._ConvertFromFormat(32, 24, True, gamma)
                #print "Converted ",self._ConvertFrom32_24(int(alpha,16)),
                #self._ConvertFrom32_24(int(beta,16)),
                #self._ConvertFrom32_24(int(gamma,16))
                actualIters += 1
            time.sleep(0.2)    

        alphaTotal /= actualIters
        betaTotal  /= actualIters
        gammaTotal /= actualIters
        #print "debug: Total alpha,beta,gamma = ", alphaTotal, betaTotal, gammaTotal
        
        log.info("TOTAL alpha %f  beta %f gamma %f", alphaTotal, betaTotal, gammaTotal)
        if alphaTotal != 0:
            Kest = math.sqrt(betaTotal / alphaTotal)
        else:
            Kest = 0
        if betaTotal != 0:
            Pest = (gammaTotal / betaTotal) * Kest
        else:
            Pest = 0    
        print "Kest %f, Pest %f" % (Kest, Pest) 
        log.info("Kest %f, Pest %f", Kest, Pest)
        return Kest, Pest
 
'''
def main():
    print "Enter <RX board IP> <Mac IF>"
    if len(sys.argv) < 3:
        print "Command line too short...expected <192.168.30.RX IP> <0/1>"
        return
        
    ipRx = sys.argv[1]
    macIf = int(sys.argv[2]) 
    if macIf != 0 and macIf != 1:
        print "Invalid Mac IF..."
        return        
    print "RX Board", ipRx, " Mac If", macIf

    iq = None
    try:
        evk_DUT = EvkControl(ipRx, dual_mac=True)
        rc = evk_DUT.OpenConnectionToTarget()
        print "connected status:", rc
        if not rc:
            return
        iq = IQImbalance()
        iq.Open(evk_DUT, macIf)       
        iq.Run(20,2)
        print("Final EVM: %s" %  iq._evkRX.ChannelControlList[macIf].EvmCalc(EvmAverageCnt))
    finally:
        if iq is not None:
            iq.Destroy()


if __name__ == '__main__':
    main()
'''
