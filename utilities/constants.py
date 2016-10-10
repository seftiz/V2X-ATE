DATA_FREQUENCY_LIST = [5860,5890,5900,5910]
#DATA_FREQUENCY_LIST = [5900]
DATA_RATE_LIST = [3,4.5,6,9,12,18,24,27]
#DATA_RATE_LIST = [6]
DATA_TX_POWER_LIST = [10,20,23]
DATA_LENGH = [1000,360]
#DATA_LENGH = [1000]
DSRC_CHANNEL_MODELS_ENABLE = 0  # 0 - disable for LitePoint, 1 - enable for MXG
TEMPERATURE_RANGE = [25,85]
TEMPERATURE_DEFAULT = 25
PACKET_INTERVAL_USEC = 32


TELNET_PORT1 = 23
TELNET_PORT2 = 1123
TS_PORT = 2039
TERMINAL_SERVER_IP = "trs01"
PLUG_ID = "nps01/6"
DO_RESET = "True"

snmp = dict(
                    Freq_Set = [('wlanFrequency', 1),('wlanFrequency', 2)],
                    TxPower = [('wlanDefaultTxPower', 1),('wlanDefaultTxPower', 2)],
                    DataRate = [('wlanDefaultTxDataRate', 1),('wlanDefaultTxDataRate', 2)],
                    RxMacCounter = [('wlanFrameRxCnt',1),('wlanFrameRxCnt',2)],
                    TxMacCounter = [('wlanFrameTxCnt',1),('wlanFrameTxCnt',2)],
                    DCOCstatus = [('wlanDcocStatus',1), ('wlanDcocStatus',2)],
                    DC_Status_descrp = ['NotStarted','InProgress','Success','Failure'],
                    Rfindex = [('wlanRfindex',1),('wlanRfindex',2)],
                    RfEnabled = [('wlanRfEnabled',1),('wlanRfEnabled',2)],
                    RfFrontEndConnected = [('wlanRfFrontEndConnected',1),('wlanRfFrontEndConnected',2)],
                    RfFrontEndOffset = [('wlanRfFrontEndOffset',1),('wlanRfFrontEndOffset',2)],
                    TssiPintercept = [('wlanTssiPintercept',1), ('wlanTssiPintercept',2)],
                    TssiPslope = [('wlanTssiPslope',1), ('wlanTssiPslope',2)],
                    TssiInterval = [('wlanTssiInterval',1), ('wlanTssiInterval',2)],
                    RandomBackoffEnabled = [('wlanRandomBackoffEnabled',1),('wlanRandomBackoffEnabled',2)],
                    MacAddress = [('wlanMacAddress',1), ('wlanMacAddress',2)],
                    TxDiversityEnabled = ['wlanTxDiversityEnabled'],
                    TxCsd = ['wlanTxCsd'],
                    RxDiversityEnabled = ['wlanRxDiversityEnabled'],
                    RxDiversityCnt = ['wlanRxDiversityCnt'],
                    LogMode = ['vcaLogMode'],
                    TxPeriod = [('vcaTxPeriod',1),('vcaTxPeriod',2)],
                    FrameLen = [('vcaFrameLen',1),('vcaFrameLen',2)],
                    TxEnabled = [('vcaTxEnabled',1),('vcaTxEnabled',2)],
                    navFixAvailable = ['navFixAvailable'],
                    wlanPantLut = [('wlanPantLut',1),('wlanPantLut',2),('wlanPantLut',3),('wlanPantLut',4)]
                    #wlanMib_Mac_list = [DataRate, TxPower, RandomBackoffEnabled, MacAddress, RxMacCounter, TxMacCounter],
                    #wlanMib_Phy_list = [TxDiversityEnabled, TxCsd, RxDiversityEnabled, RxDiversityCnt],
                    #wlanMib_Rf_list = [Rfindex, Freq_Set, RfFrontEndConnected, RfFrontEndOffset],
                    #vcaMib_list = [LogMode, TxPeriod, FrameLen, TxEnabled],
                    #navMib_list = [navFixAvailable]
                    )

register = dict(
                    RF_SYNTHESIZER_REG = [0x1340,0x1040],                                       # 0x1340 - interface 1, 0x1040 - interface 0
                    LNA_VGA_LOCK_reg = 0x19d,                                                   # register VGA+LNA value on AGC lock
                    EVM_OUT = 0x14E,
                    CONST_POWER_BIN_COUNT = 0x14F,
                    RSSI_PART1 = 0x78,
                    RSSI_PART2 = 0x79,
                    TSSI_FIFO =  [0x31810, 0x31814],                                            #TSSI FIFO registers 0x31810 (chA) and 0x31814 (chB) 

                    BACKOFF_COMP_REG = 0x155,                                                   # PHY register

                    DC_RANGE_START_REG = int('0x68',16),                                        # low limit
                    DC_RANGE_STOP_REG = int('0x99',16),                                         # high limit
                    RX1_DC_IQ_0 = 0x1070,                                                       # rx1_ch0_dc_iq_config_0  rf register
                    RX1_DC_IQ_1 = 0x1071,                                                       # rx1_ch0_dc_iq_config_1  rf register
                    RX1_DC_IQ_4 = 0x1074,                                                       # rx1_ch0_dc_iq_config_4  rf register      
                    RX1_DC_IQ_6 = 0x1076,                                                       # rx1_ch0_dc_iq_config_6  rf register
                            
                    RX2_DC_IQ_0 = 0x1370,                                                       # rx2_ch0_dc_iq_config_0  rf register
                    RX2_DC_IQ_1 = 0x1371,                                                       # rx2_ch0_dc_iq_config_1  rf register
                    RX2_DC_IQ_4 = 0x1374,                                                       # rx2_ch0_dc_iq_config_4  rf register     
                    RX2_DC_IQ_6 = 0x1376,                                                       # rx2_ch0_dc_iq_config_6  rf register

                    TX_IQ_IMBALANCE_AMPL_REG = 0x14a,                                           # TX IQ imbalance amplitude PHY register
                    TX_IQ_IMBALANCE_PHASE_REG = 0x14b,                                          # TX IQ imbalance phase PHY register
                    RX_IQ_IMBALANCE_AMPL_REG = 0x14c,                                           # PHY register
                    RX_IQ_IMBALANCE_PHASE_REG = 0x14d,                                          # PHY register
                    RX_IQ_IMBALANCE_AMPL_REG_VALUE = 0x100,                                     # Default value                
                    RX_IQ_IMBALANCE_PHASE_REG_VALUE = 0x20000000,                               # Default value
                    RX_SAMPLE_GAIN_REG_LOW_PART = 0x15a,                                        # PHY register
                    RX_SAMPLE_GAIN_REG_HIGHMID_PART = 0x15b,
                    REG_PHASE_LIST = [0x1fe03BC,0x1fe03C1,0x1fe03C5,0x1fe03CA,0x1fe03CE,0x1fe03D3,0x1fe03D8,0x1fe03DC,0x1fe03D3,0x1fe03D8,0x1ff03DC,0x1ff03E1,0x1ff03E5,0x1ff03EA,0x1ff03EE,0x1ff03F3,0x1ff03F7,0x1ff03FC,0x1ff0000,0x1ff0004,0x1ff0009,0x1ff000D,0x1ff0012,0x1ff0016,0x1ff001B,0x1ff001F,0x1ff0024,0x1fe0028,0x1fe002D,0x1fe0031,0x1fe0035,0x1fe003A,0x1fe003E,0x1fe0043,0x1fe0047,0x1fe004C,0x1fe0050],
                    REG_AMPLITUDE_LIST = [0x100,0x101,0x102,0x103,0x104,0x105,0x106,0x107,0x108,0x109,0x10A,0x10B,0x10C,0x10D,0x10E,0x10F,0x110,0x111,0x112,0x113,0x114,0x115,0x116,0x117,0x118,0x119,0x11a,0xf8,0xf9,0xfa,0xfb,0xfc,0xfd,0xfe,0xff]
                    )


common = dict(                    
                    QA_SDK_VERSION = r'qa-sdk-4.3-alpha6',
                    #QA_SDK_VERSION = r'qa-sdk-4.3-alpha3',
                    #QA_SDK_VERSION = r'qa-sdk-4.2-rc14',
                    #QA_SDK_VERSION = r'qa-sdk-4.2-rc6',
                    #QA_SDK_VERSION = r'qa-sdk-3.3.5',
                    LO_LEAKAGE_POW_LIST = [20, 15, 12, 10, 8, 5],                               # dBm

                    EVM_AVERAGE_CNT = 8,
                    BACKOFF_COMP = 12,                                                          # dB Default

                    VSA_MAX_SIGNAL_LEVEL = -2,  #defult=-8
                    VSA_TRIGGER_LEVEL = -38,
                    VSA_CAPTURE_WINDOW = 20e-6,  #defult=10e-6

                    #TX_CAL_RANGE  = range(24,9,-1),                                            # TX calibration tx power 23,22,21,...10,9 dBm
                    TX_CAL_RANGE  = range(10,25,1),                                              # TX calibration tx power 10,11,12,13,...24 dBm

                    RX_IQ_IMBALANCE_INIT_PIN_POWER = -55,                                       # dBm
                    EXPECTED_RX_EVM_LIMIT = -22,                                                # dB

                    #SENSITIVITY_TEST_RANGE = range(-88, -78, 1),
                    #SENSITIVITY_TEST_RANGE_RATE_12MBPS = range(-88, -72, 1) +range(-72, -63, 2)+range(-63, -55, 1)+range(-55, -45, 2)+range(-45, -38, 1)+range(-38, -22, 2)+range(-22, -8, 1),  #Sensitivity range+(-RX_PATH_SETUP_ATTENUATION)
                    #SENSITIVITY_TEST_RANGE_RATE_6MBPS = range(-88, -78, 1),
                    SENSITIVITY_TEST_RANGE_RATE = { 6 : range(-88, -78, 1),
                                                   12 : range(-88, -72, 1) +range(-72, -63, 2) + range(-63, -55, 1) + range(-55, -45, 2) + range(-45, -38, 1) + range(-38, -22, 2) + range(-22, -8, 1)},

                    #In case of setup atten = 8dB
                    STRONG_PACKETS_AREA = -37,                                                  # LNA off Mixer off
                    MID_PACKETS_AREA = -56,                                                     # LNA off Mixer on
                    WEAK_PACKETS_AREA = -78,                                                    # LNA on Mixer on

                    type_dict = {'1':"ATK22016",'2':"ATK22022",'3':"ATK22027",'4':"ATK23010","5":"ATK22017"},
                    gps_version_dict = {'1':"TELIT SW Version: SL869 v3.1.5.1",'2':"sta8088-3.1.14-atk-1.0.0-rel",'3':"sta8088-3.1.14-atk-1.0.0-rel",'4':"sta8088-3.1.14-atk-1.0.0-rel","5":"sta8088-3.1.14-atk-1.0.0-rel"},
                    serial_number_dict = {'1':13100000,'2':13300000,'3':13400000,'4':13500000,'5':13200000},

                    # Default Attenuation Value (dB)
                    TX_PATH_SETUP_ATTENUATION_0_ATK22016 = 34,   
                    RX_PATH_SETUP_ATTENUATION_0_ATK22016 = 8,    
                    TX_PATH_SETUP_ATTENUATION_1_ATK22016 = 34,   
                    RX_PATH_SETUP_ATTENUATION_1_ATK22016 = 8,    
                    
                    # Fitax Board Attenuation Value (dB)
                    TX_PATH_SETUP_ATTENUATION_0_ATK23010 = 36,   
                    RX_PATH_SETUP_ATTENUATION_0_ATK23010 = 10,
                    TX_PATH_SETUP_ATTENUATION_1_ATK23010 = 36,   
                    RX_PATH_SETUP_ATTENUATION_1_ATK23010 = 10,   
                    
                    # Audi Board Attenuation Value (dB)
                    TX_PATH_SETUP_ATTENUATION_0_ATK22022 = 35,   
                    RX_PATH_SETUP_ATTENUATION_0_ATK22022 = 9,   
                    TX_PATH_SETUP_ATTENUATION_1_ATK22022 = 34,   
                    RX_PATH_SETUP_ATTENUATION_1_ATK22022 = 8,

                    # Laird Board Attenuation Value (dB)
                    TX_PATH_SETUP_ATTENUATION_0_ATK22027 = 36,   
                    RX_PATH_SETUP_ATTENUATION_0_ATK22027 = 10,   
                    TX_PATH_SETUP_ATTENUATION_1_ATK22027 = 36,   
                    RX_PATH_SETUP_ATTENUATION_1_ATK22027 = 10,

                    # 4S Board Attenuation Value (dB)
                    TX_PATH_SETUP_ATTENUATION_0_ATK22017 = 34,   
                    RX_PATH_SETUP_ATTENUATION_0_ATK22017 = 8,    
                    TX_PATH_SETUP_ATTENUATION_1_ATK22017 = 34,   
                    RX_PATH_SETUP_ATTENUATION_1_ATK22017 = 8, 
                    
                    #RX_PATH_SETUP_ATTENUATION = 9,   # for WNC board

                    #setup_attenuation = 48.8   #  oven test
                    MIN_SENSITIVITY_BY_RATE = {'3':-85,'4.5':-84,'6':-82,'9':-77,'12':-73,'18':-70,'24':-69,'27':-68},                     #dB
                    PLUG_ID = 'nps01/6',

                    tester_device = {'IQ2010':1,'MXG':2},
                    #dsrc_channel_models_list = ['AWGN10MHZ','V2V50KMH','V2V100KMH','V2V200KMH','NLOS']
                    #dsrc_channel_models_list = ['AWGN10MHZ','0ONCOMMING_V2V_EXT','0APPROACH_LOS','0HIGHWAY_LOS','0HIGHWAY_NLOS','0RURAL_LOS','0WALL_V2V_NLOS']
                    dsrc_channel_models_list = ['1AWGN10MHZ','1ONCOMMING_V2V_EXT','1APPROACH_LOS','1HIGHWAY_LOS','1HIGHWAY_NLOS','1RURAL_LOS','1WALL_V2V_NLOS']
                    #dsrc_channel_models_list = ['0APPROACH_LOS','0HIGHWAY_LOS','0HIGHWAY_NLOS','0RURAL_LOS','0WALL_V2V_NLOS']

            )
                    
expected = dict(                    
                    #EXPECTED_POWER_20 = 23,
                    EXPECTED_POWER_20 = 20,
                    EXPECTED_POWER_10 = 10,
                    EXPECTED_TSSI_DIFF = 0.45,
                    START_RANGE = -8,                                                           #Sample gain limit low
                    END_RANGE = 8,                                                              #Sample gain limit high


                    EXPECTED_TX_EVM = -23.00,                                                    #dBm
                    EXPECTED_HI_TX_EVM = -23.00,                                                 #dBm
                    EXPECTED_LO_LEAKAGE = -22.00,                                                #dBc
                    EXPECTED_TX_IQIMBALANCE_GAIN_LOW = -0.20,                                    #dB
                    EXPECTED_TX_IQIMBALANCE_GAIN_HIGH = 0.20,                                    #dB  
                    EXPECTED_TX_IQIMBALANCE_PHASE_LOW = -0.50,                                   #deg
                    EXPECTED_TX_IQIMBALANCE_PHASE_HIGH = 0.50,                                   #deg 
                    EXPECTED_TX_POWER_HIGH = 21.00,
                    EXPECTED_TX_POWER_LOW = 19.00,
                    #EXPECTED_TX_POWER = [EXPECTED_TX_POWER_LOW,EXPECTED_TX_POWER_HIGH],
                    EXPECTED_TX_HI_POWER_LOW = 22,
                    EXPECTED_TX_HI_POWER_HIGH = 24,
                    EXPECTED_TX_LOW_POWER_LOW = 9,
                    EXPECTED_TX_LOW_POWER_HIGH = 11,
                    #EXPECTED_TX_HI_POWER = [EXPECTED_TX_HI_POWER_LOW,EXPECTED_TX_HI_POWER_HIGH],
                    EXPECTED_TX_FREQ_ERROR_LOW = -117,                                           #kHz
                    EXPECTED_TX_FREQ_ERROR_HIGH = 117,                                           #kHz
                    EXPECTED_TX_SYMBOL_CLK_ERROR_LOW = -20,                                      #ppm
                    EXPECTED_TX_SYMBOL_CLK_ERROR_HIGH = 20,                                      #ppm

                    EXPECTED_PER_HIGH = 10.0,                                                    #%
                    EXPECTED_PER_LOW = 9.0 ,       

                    EXPECTED_RX_EVM_LIMIT = -22.00,                                              #dBm
                    EXPECTED_SENSITIVITY = -91.00,                                                #dBm
                    rep_list_name = ["Tx EVM @23dBm","Tx EVM @20dBm","Tx High Power (23dBm)","Tx Power (20dBm)","LO leakage @20dBm","Tx IQ imbalance ampl","Tx IQ imbalance phase","Tx Frequency error","Tx Symbol clock error","Rx EVM@-55dbm"],
                    rep_units = ["dB","dB","dBm","dBm","dBc","dB","deg","kHz","ppm","dB"]
                )
