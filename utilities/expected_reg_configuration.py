#dictionary: {NAME,TYPE,REG_ADDR,BITMASK,(VALUES_RANGE),COMMENTS}

#System Parameters
AGC_MAXIMUM_VGA_GAIN_REGISTER = {'name':'AGC Maximum VGA Gain Register','type':'reg','location':{'subsys':'phy','reg_addr':0x23,'bitmask':0xff},'valuesRange':(0x13,),'comment':"The setting of BB gain during AGC WFP state"}
BPF_MIN_TH_REG3_VGA_BIAS0  = {'name':'VGA Bias LNA=00','type':'reg','location':{'subsys':'phy','reg_addr':0x196,'bitmask':0xf0000000},'valuesRange':(0x0,),'comment':"VGA bias add for LNA=0"}
BACKOFF_UPSCALE = {'name':'BACKOFF UPSCALE','type':'reg','location':{'subsys':'phy','reg_addr':0x155,'bitmask':0x00000003},'valuesRange':(0x2,),'comment':"Upscale the Reciever by this factor"} 

#Parameters Sets
AGC_SETTINGS = (AGC_MAXIMUM_VGA_GAIN_REGISTER,BPF_MIN_TH_REG3_VGA_BIAS0)
BACKOFF_COMPENSATION = (BACKOFF_UPSCALE,) 