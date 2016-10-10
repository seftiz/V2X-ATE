


        
class generic_setup(object):

    def generate_instance_list(self, name, max_length_instance):
        for i in range(1, max_length_instance):
            return [ (name, 1), (name, 2) ]

    def __init__(self):
        self.snmp = dict(
                            FREQ_SET = self.generate_instance_list('wlanFrequency', 2),
                            TX_POWER = self.generate_instance_list('wlanDefaultTxPower', 2),
                            DATA_RATE = self.generate_instance_list('wlanDefaultTxDataRate', 2),
                            RX_MAC_COUNTER = self.generate_instance_list('wlanFrameRxCnt', 2),
                            TX_MAC_COUNTER = self.generate_instance_list('wlanFrameTxCnt', 2),
                            RX_RSSI = self.generate_instance_list('wlanRssiLatestFrame', 2),
                            DCOC_STATUS = self.generate_instance_list('wlanDcocStatus', 2),
                            DC_STATUS_DESCRPT = [ 'NotStarted', 'InProgress', 'Success', 'Failure' ],
                            RF_INDEX = self.generate_instance_list('wlanRfindex', 2),
                            RF_ENABLED = self.generate_instance_list('wlanRfEnabled', 2),
                            RF_FRONT_END_CONNECTED = self.generate_instance_list('wlanRfFrontEndConnected', 2),
                            RF_FRONT_END_OFFSET = self.generate_instance_list('wlanRfFrontEndOffset', 2),
                            TSSI_PINTERCEPT = self.generate_instance_list('wlanTssiPintercept', 2),
                            TSSI_PSLOPE = self.generate_instance_list('wlanTssiPslope', 2),
                            TSSI_INTERVAL = self.generate_instance_list('wlanTssiInterval', 2),
                            RANDOM_BACKOFF_ENABLED = self.generate_instance_list('wlanRandomBackoffEnabled', 2),
                            MAC_ADDRESS = self.generate_instance_list('wlanMacAddress', 2),
                            TX_DIVERSITY_ENABLED = [ 'wlanTxDiversityEnabled' ],
                            TX_CSD = [ 'wlanTxCsd' ],
                            RX_DIVERSITY_ENABLED = [ 'wlanRxDiversityEnabled' ],
                            RX_DIVERSITY_CNT = [ 'wlanRxDiversityCnt' ],
                            LOG_MODE = ['vcaLogMode'],
                            TX_PERIOD = self.generate_instance_list('vcaTxPeriod', 2),
                            FRAME_LEN = self.generate_instance_list('vcaFrameLen', 2),
                            TX_ENABLED = self.generate_instance_list('vcaTxEnabled', 2),
                            NAV_FIX_AVAILABLE = [ 'navFixAvailable' ],
                            WLAN_PANT_LUT = [ ('wlanPantLut', 1), ('wlanPantLut', 2), ('wlanPantLut', 3), ('wlanPantLut', 4) ]
                            #wlanMib_Mac_list = [DataRate, TxPower, RandomBackoffEnabled, MacAddress, RxMacCounter, TxMacCounter],
                            #wlanMib_Phy_list = [TxDiversityEnabled, TxCsd, RxDiversityEnabled, RxDiversityCnt],
                            #wlanMib_Rf_list = [Rfindex, Freq_Set, RfFrontEndConnected, RfFrontEndOffset],
                            #vcaMib_list = [LogMode, TxPeriod, FrameLen, TxEnabled],
                            #navMib_list = [navFixAvailable]
                            )

        self.register = dict(
                            RF_SYNTHESIZER_REG_HEX = [ 0x1340, 0x1040 ],                                    # 0x1340 - interface 1, 0x1040 - interface 0
                            LNA_VGA_LOCK_REG_HEX = 0x19d,                                                   # register VGA+LNA value on AGC lock
                            EVM_OUT_HEX = 0x14E,
                            CONST_POWER_BIN_COUNT_HEX = 0x14F,
                            RSSI_PART1_HEX = 0x78,
                            RSSI_PART2_HEX = 0x79,
                            TSSI_FIFO_HEX =  [ 0x31810, 0x31814 ],                                          #TSSI FIFO registers 0x31810 (chA) and 0x31814 (chB) 

                            BACKOFF_COMP_REG_HEX = 0x155,                                                   # PHY register

                            DC_RANGE_START_REG_HEX = int( '0x68', 16 ),                                     # low limit
                            DC_RANGE_STOP_REG_HEX = int( '0x99', 16 ),                                      # high limit
                            RX1_DC_IQ_0_HEX = 0x1070,                                                       # rx1_ch0_dc_iq_config_0  rf register  (i-bits [15:8], q-bits[7:0]) 
                            RX1_DC_IQ_1_HEX = 0x1071,                                                       # rx1_ch0_dc_iq_config_1  rf register
                            RX1_DC_IQ_4_HEX = 0x1074,                                                       # rx1_ch0_dc_iq_config_4  rf register      
                            RX1_DC_IQ_6_HEX = 0x1076,                                                       # rx1_ch0_dc_iq_config_6  rf register
                            #RX1_DC_IQ_REGS_HEX = [ 0x1070, 0x1071, 0x1074, 0x1076 ],                       # rx1_ch0_dc_iq_config_0/1/4/6  rf register        

                            RX2_DC_IQ_0_HEX = 0x1370,                                                       # rx2_ch0_dc_iq_config_0  rf register
                            RX2_DC_IQ_1_HEX = 0x1371,                                                       # rx2_ch0_dc_iq_config_1  rf register
                            RX2_DC_IQ_4_HEX = 0x1374,                                                       # rx2_ch0_dc_iq_config_4  rf register     
                            RX2_DC_IQ_6_HEX = 0x1376,                                                       # rx2_ch0_dc_iq_config_6  rf register
                            #RX2_DC_IQ_REGS_HEX = [ 0x1370, 0x1371, 0x1374, 0x1376 ],                       # rx2_ch0_dc_iq_config_0/1/4/6  rf register

                            RX_DC_IQ_REGS_HEX = [[ 0x1070, 0x1071, 0x1074, 0x1076 ], [ 0x1370, 0x1371, 0x1374, 0x1376 ]],         # rx[index]_ch0_dc_iq_config_0/1/4/6  rf register  ,index = 1/2      

                            TX_IQ_IMBALANCE_AMPL_REG_HEX = 0x14a,                                           # TX IQ imbalance amplitude PHY register
                            TX_IQ_IMBALANCE_PHASE_REG_HEX = 0x14b,                                          # TX IQ imbalance phase PHY register
                            RX_IQ_IMBALANCE_AMPL_REG_HEX = 0x14c,                                           # PHY register
                            RX_IQ_IMBALANCE_PHASE_REG_HEX = 0x14d,                                          # PHY register
                            RX_IQ_IMBALANCE_AMPL_REG_VALUE_HEX = 0x100,                                     # Default value                
                            RX_IQ_IMBALANCE_PHASE_REG_VALUE_HEX = 0x20000000,                               # Default value
                            RX_SAMPLE_GAIN_REG_LOW_PART_HEX = 0x15a,                                        # PHY register
                            RX_SAMPLE_GAIN_REG_HIGHMID_PART_HEX = 0x15b,
                            REG_PHASE_LIST = [ 0x1fe03BC, 0x1fe03C1, 0x1fe03C5, 0x1fe03CA, 0x1fe03CE, 0x1fe03D3, 0x1fe03D8, 0x1fe03DC, 0x1fe03D3, 0x1fe03D8, 0x1ff03DC, 0x1ff03E1, 0x1ff03E5, 0x1ff03EA, 0x1ff03EE, 0x1ff03F3, 0x1ff03F7, 0x1ff03FC, 0x1ff0000, 0x1ff0004, 0x1ff0009, 0x1ff000D, 0x1ff0012, 0x1ff0016, 0x1ff001B, 0x1ff001F, 0x1ff0024, 0x1fe0028, 0x1fe002D, 0x1fe0031, 0x1fe0035, 0x1fe003A, 0x1fe003E, 0x1fe0043, 0x1fe0047, 0x1fe004C, 0x1fe0050 ],
                            REG_AMPLITUDE_LIST = [ 0x100, 0x101, 0x102, 0x103, 0x104, 0x105, 0x106, 0x107, 0x108, 0x109, 0x10A, 0x10B, 0x10C, 0x10D, 0x10E, 0x10F, 0x110, 0x111, 0x112, 0x113, 0x114 ,0x115, 0x116, 0x117, 0x118, 0x119, 0x11a, 0xf8, 0xf9, 0xfa, 0xfb, 0xfc, 0xfd, 0xfe, 0xff ]
                            )


        self.common = dict(                    
                            QA_SDK_VERSION = r'qa-sdk-4.3-alpha6',
                            #QA_SDK_VERSION = r'qa-sdk-4.3-alpha3',
                            #QA_SDK_VERSION = r'qa-sdk-4.2-rc14',
                            #QA_SDK_VERSION = r'qa-sdk-4.2-rc6',
                            #QA_SDK_VERSION = r'qa-sdk-3.3.5',
                            #LO_LEAKAGE_POW_LIST = [ 20, 15, 12, 10, 8, 5 ],                                # dBm
                            LO_LEAKAGE_POW_LIST_DBM = [ 23, 20, 15, 12, 10, 8, 5 ],                         # dBm

                            EVM_AVERAGE_CNT = 10,                                                           # wait for 10 packets
                            BACKOFF_COMP_DB = 12,                                                           # dB Default

                            VSA_MAX_SIGNAL_LEVEL_DBM = 16,                                                  # dBm
                            VSA_TRIGGER_LEVEL_DB = -38,                                                     # dB
                            VSA_CAPTURE_WINDOW = 20e-6,                                                     # previous value 10e-6

                            #TX_CAL_RANGE_DBM  = range(24,9,-1),                                            # Down direction: TX calibration tx power 24,23,22,21,...10 dBm
                            TX_CAL_RANGE_DBM  = range(10, 25, 1),                                           # Up direction: TX calibration tx power 10,11,12,13,...24 dBm

                            RX_IQ_IMBALANCE_INIT_PIN_POWER_DBM = -55,                                       # dBm
                            EXPECTED_RX_EVM_LIMIT_DB = -22,                                                 # dB

                            SENSITIVITY_TEST_RANGE_RATE = { 3 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1),
                                                            6 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1),
                                                            9 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1),
                                                            12 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1),
                                                            18 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1),
                                                            24 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1),
                                                            36 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1),
                                                            54 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1)},

                            #In case of setup atten = 8dB
                            STRONG_PACKETS_AREA_DBM = -37,                                                  # LNA off Mixer off
                            MID_PACKETS_AREA_DBM = -56,                                                     # LNA off Mixer on
                            WEAK_PACKETS_AREA_DBM = -78,                                                    # LNA on Mixer on
                            VGA_RANGE_HEX = { "LOW" : 0xC0, "MID" : 0x80, "HIGH" : 0x0 },                                             # VGA ranges gain

                            BOARD_TYPE = { 1:"ATK22016", 2:"ATK22022", 3:"ATK22027", 4:"ATK23010", 5:"ATK22017" },
                            BOARD_TYPE_MENU = { 1:'ATK22016 (EVK4/Pangaea4)', 2:'ATK22022 (Audi)', 3:'ATK22027 (Laird)', 4:'ATK23010 (Fitax)', 5:'ATK22017 (EVK4S/Pangaea4S)'},
                            #GPS_VERSION_TYPE = { "version1":"TELIT SW Version: SL869 v3.1.5.1", "version2":"sta8088-3.1.14-atk-1.0.0-rel" },
                            GPS_VERSION_TYPE = { 1: "TELIT SW Version: SL869 v3.1.5.1", 2: "sta8088-3.1.14-atk-1.0.0-rel", 3: "sta8088-3.1.14-atk-1.0.0-rel", 4: "sta8088-3.1.14-atk-1.0.0-rel", 5: "sta8088-3.1.14-atk-1.0.0-rel" },
                            SERIAL_NUMBER_DICT = { 1: 13100000, 2: 13300000, 3: 13400000, 4: 13500000, 5: 13200000 },

                            # Default Attenuation Value (dB)
                            TX_PATH_SETUP_ATTENUATION_DB_0_ATK22016 = 34,   
                            RX_PATH_SETUP_ATTENUATION_DB_0_ATK22016 = 8,    
                            TX_PATH_SETUP_ATTENUATION_DB_1_ATK22016 = 34,   
                            RX_PATH_SETUP_ATTENUATION_DB_1_ATK22016 = 8,    
                    
                            # Fitax Board Attenuation Value (dB)
                            TX_PATH_SETUP_ATTENUATION_DB_0_ATK23010 = 36,   
                            RX_PATH_SETUP_ATTENUATION_DB_0_ATK23010 = 10,
                            TX_PATH_SETUP_ATTENUATION_DB_1_ATK23010 = 36,   
                            RX_PATH_SETUP_ATTENUATION_DB_1_ATK23010 = 10,   
                    
                            # Audi Board Attenuation Value (dB)
                            TX_PATH_SETUP_ATTENUATION_DB_0_ATK22022 = 35,   
                            RX_PATH_SETUP_ATTENUATION_DB_0_ATK22022 = 9,   
                            TX_PATH_SETUP_ATTENUATION_DB_1_ATK22022 = 34,   
                            RX_PATH_SETUP_ATTENUATION_DB_1_ATK22022 = 8,

                            # Laird Board Attenuation Value (dB)
                            TX_PATH_SETUP_ATTENUATION_DB_0_ATK22027 = 36,   
                            RX_PATH_SETUP_ATTENUATION_DB_0_ATK22027 = 10,   
                            TX_PATH_SETUP_ATTENUATION_DB_1_ATK22027 = 36,   
                            RX_PATH_SETUP_ATTENUATION_DB_1_ATK22027 = 10,

                            # 4S Board Attenuation Value (dB)
                            TX_PATH_SETUP_ATTENUATION_DB_0_ATK22017 = 34,   
                            RX_PATH_SETUP_ATTENUATION_DB_0_ATK22017 = 8,    
                            TX_PATH_SETUP_ATTENUATION_DB_1_ATK22017 = 34,   
                            RX_PATH_SETUP_ATTENUATION_DB_1_ATK22017 = 8, 
                    
                            #RX_PATH_SETUP_ATTENUATION_DB = 9,   # for WNC board

                            TX_POW_DELTA_LIMIT_DB = 6,               # limit for delta between expected and measured tx power adjustment

                            MIN_SENSITIVITY_BY_RATE_DB = { '3':-85, '4.5':-84, '6':-82, '9':-77, '12':-73, '18':-70, '24':-69, '27':-68 },                     #dB
                    
                            DC_GAIN_LEVELS = { 'high' : 0x01, 'medium' : 0x9b01, 'low' : 0x1b01 },

                            TESTER_DEVICE = {'IQ2010':1,'MXG':2},
                            #DSRC_CHANNEL_SIM_MODELS_LIST = ['AWGN10MHZ','V2V50KMH','V2V100KMH','V2V200KMH','NLOS']
                            #DSRC_CHANNEL_SIM_MODELS_LIST = ['AWGN10MHZ','0ONCOMMING_V2V_EXT','0APPROACH_LOS','0HIGHWAY_LOS','0HIGHWAY_NLOS','0RURAL_LOS','0WALL_V2V_NLOS']
                            DSRC_CHANNEL_SIM_MODELS_LIST = ['1AWGN10MHZ','1ONCOMMING_V2V_EXT','1APPROACH_LOS','1HIGHWAY_LOS','1HIGHWAY_NLOS','1RURAL_LOS','1WALL_V2V_NLOS']
                            #DSRC_CHANNEL_SIM_MODELS_LIST = ['0APPROACH_LOS','0HIGHWAY_LOS','0HIGHWAY_NLOS','0RURAL_LOS','0WALL_V2V_NLOS']

                    )
                    
        self.expected = dict(                    
                            EXPECTED_POWER_20_DBM = 20,
                            EXPECTED_POWER_10_DBM = 10,
                            EXPECTED_TSSI_DIFF_DB = 0.45,
                            START_RANGE_DB = -8,                                                            #Sample gain limit low
                            END_RANGE_DB = 8,                                                               #Sample gain limit high

                            EXPECTED_TX_EVM_DB = -23.00,                                                    #dB
                            EXPECTED_HI_TX_EVM_DB = -23.00,                                                 #dB
                            EXPECTED_LO_LEAKAGE_DBC = -22.00,                                               #dBc
                            EXPECTED_TX_IQIMBALANCE_GAIN_LOW_DB = -0.20,                                    #dB
                            EXPECTED_TX_IQIMBALANCE_GAIN_HIGH_DB = 0.20,                                    #dB  
                            EXPECTED_TX_IQIMBALANCE_PHASE_LOW_DEG = -0.50,                                  #deg
                            EXPECTED_TX_IQIMBALANCE_PHASE_HIGH_DEG = 0.50,                                  #deg 
                            EXPECTED_TX_POWER_HIGH_DBM = 21.00,
                            EXPECTED_TX_POWER_LOW_DBM = 19.00,
                            #EXPECTED_TX_POWER = [EXPECTED_TX_POWER_LOW,EXPECTED_TX_POWER_HIGH],
                            EXPECTED_TX_HI_POWER_LOW_DBM = 22,
                            EXPECTED_TX_HI_POWER_HIGH_DBM = 24,
                            EXPECTED_TX_LOW_POWER_LOW_DBM = 9,
                            EXPECTED_TX_LOW_POWER_HIGH_DBM = 11,
                            #EXPECTED_TX_HI_POWER = [EXPECTED_TX_HI_POWER_LOW,EXPECTED_TX_HI_POWER_HIGH],
                            EXPECTED_TX_FREQ_ERROR_LOW_KHZ = -117,                                           #kHz
                            EXPECTED_TX_FREQ_ERROR_HIGH_KHZ = 117,                                           #kHz
                            EXPECTED_TX_SYMBOL_CLK_ERROR_LOW_PPM = -20,                                      #ppm
                            EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH_PPM = 20,                                      #ppm

                            EXPECTED_PER_HIGH_PERCENT = 10.0,                                                #%
                            EXPECTED_PER_LOW_PERCENT = 9.0 ,
                            EXPECTED_DC_RANGE = 50,                                                          #mv, (+-)       

                            EXPECTED_RX_EVM_LIMIT_DB = -22.00,                                               #dB
                            EXPECTED_SENSITIVITY_DB = -91.00,                                                #dB
                            REPORT_LIST_ROWS = [ "Tx EVM @23dBm", "Tx EVM @20dBm", "Tx High Power (23dBm)", "Tx Power (20dBm)", "LO leakage @20dBm", "Tx IQ imbalance ampl", "Tx IQ imbalance phase", "Tx Frequency error", "Tx Symbol clock error", "Rx EVM@-55dbm" ],
                            REPORT_UNITS = [ "dB", "dB", "dBm", "dBm", "dBc", "dB", "deg", "kHz", "ppm", "dB" ]
                        )


class debug_setup(generic_setup):

    def __init__(self):
        super(debug_setup, self).__init__()
        self.common[ 'TX_PATH_SETUP_ATTENUATION_DB_0_ATK22017' ] = 8
        self.common[ 'RX_PATH_SETUP_ATTENUATION_DB_0_ATK22017' ] = 1.5



CONSTS = { "debug_setup" : debug_setup(), "generic_setup" : generic_setup() }

DEFAULT_TEMP = 25
CHAMBER_TEMP_OVER_LIMIT = 90

DATA_FREQUENCY_LIST = [5860,5890,5900,5910]
#DATA_RATE_LIST = [3,4.5,6,9,12,18,24,27]
DATA_RATE_LIST = [3,6,12,27]
DATA_TX_POWER_LIST = [10,20,23]
DATA_LENGH = [1000,360]
DSRC_CHANNEL_MODELS_ENABLE = 0  # 0 - disable for LitePoint, 1 - enable for MXG
TEMPERATURE_RANGE = [25,85,-10]
PACKET_INTERVAL_USEC = 32
CHAMBER_TEST = False

#Calibration settings
CALIBRATION_ENABLE = False
DATA_FREQUENCY_LIST_CAL = [5900]
DATA_RATE_LIST_CAL = [6,12]
DATA_TX_POWER_LIST_CAL = [20]
DATA_LENGH_CAL = [1000]
DSRC_CHANNEL_MODELS_ENABLE_CAL = 0  # 0 - disable for LitePoint, 1 - enable for MXG
PACKET_INTERVAL_USEC_CAL = 32
CHANNEL_BW_CAL = 10 # OFDM channel bandwith 10Mhz/20Mhz

PDF_REPORT = False

#Format description
#dictionary: {NAME,TYPE,REG_ADDR,BITMASK,(VALUES_RANGE),COMMENTS}

#NAME - register name
#TYPE - reg/GPIO(if supported)
#LOCATION - location of 'subsys',it may be 'phy','mac' or 'rf'
#REG_ADDR - register address 
#BITMASK - bitmask, check the state of individual bits
#VALUES_RANGE - expected value or range of values
#COMMENTS - add some comments

#System Parameters
AGC_MAXIMUM_VGA_GAIN_REGISTER = {'name':'AGC Maximum VGA Gain Register','type':'reg','location':{'subsys':'phy','reg_addr':0x23,'bitmask':0xff},'valuesRange':(0x13,),'comment':"The setting of BB gain during AGC WFP state"}
BPF_MIN_TH_REG3_VGA_BIAS0  = {'name':'VGA Bias LNA=00','type':'reg','location':{'subsys':'phy','reg_addr':0x196,'bitmask':0xf0000000},'valuesRange':(0x0,),'comment':"VGA bias add for LNA=0"}
BACKOFF_UPSCALE = {'name':'BACKOFF UPSCALE','type':'reg','location':{'subsys':'phy','reg_addr':0x155,'bitmask':0x00000003},'valuesRange':(0x2,),'comment':"Upscale the Reciever by this factor"} 

#Parameters Sets
AGC_SETTINGS = (AGC_MAXIMUM_VGA_GAIN_REGISTER,BPF_MIN_TH_REG3_VGA_BIAS0)
BACKOFF_COMPENSATION = (BACKOFF_UPSCALE,) 