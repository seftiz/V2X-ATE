"""
@file v2x_managment.py
@brief V2X Managment over SNMP
@author    	Shai Shochat
@version	1.0
@date		24/01/2013
"""
from uuts import common
from uuts.craton.snmp import snmp 


class snmpManagmentBase(object):
    # define boolean to 1/2 value for snmp settings
    snmp_bool = { True:1, False:2}
    def snmp_bool(self, value):
        return 1 if value == True else 2

    # Convertion board rf interface 0/1 to 1/2, due to snmp adaptability
    def snmp_rf_if(self, rf_if):
        return rf_if+1


class wlanCnt(snmpManagmentBase):
    """        ?atlk rc t mib get wlanFrameTxCnt (mib service t service, int32 t ifIndex, uint32 t value)
    atlk rc t mib get wlanFrameRxCnt (mib service t service, int32 t ifIndex, uint32 t value)
    atlk rc t mib get wlanTxFailCnt (mib service t service, int32 t ifIndex, uint32 t value)
    atlk rc t mib get wlanTxAllocFailCnt (mib service t service, int32 t ifIndex, uint32 t value)
    atlk rc t mib get wlanTxQueueFailCnt (mib service t service, int32 t ifIndex, uint32 t value)
    atlk rc t mib get wlanRxFailCnt (mib service t service, int32 t ifIndex, uint32 t value)
    atlk rc t mib get wlanRxAllocFailCnt (mib service t service, int32 t ifIndex, uint32 t value)
    atlk rc t mib get wlanRxQueueFailCnt (mib service t service, int32 t ifIndex, uint32 t value)
    """


    def __init__(self, mng):
        self._mng = mng

    def tx_frames(self, channel):
        mib = ( 'wlanFrameTxCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def rx_frames(self, channel):
        mib = ( 'wlanFrameRxCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def tx_fail(self, channel):
        mib = ( 'wlanTxFailCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def rx_fail(self, channel):
        mib = ( 'wlanRxFailCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def tx_alloc_fail(self, channel):
        mib = ( 'wlanTxAllocFailCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def rx_alloc_fail(self, channel):
        mib = ( 'wlanRxAllocFailCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def tx_queue_fail(self, channel):
        mib = ( 'wlanTxQueueFailCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def rx_queue_fail(self, channel):
        mib = ( 'wlanRxQueueFailCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)



class V2xManagment(snmpManagmentBase):
    """
    @class V2xManagment
    @brief V2X SNMP manamgent Implementation for python.
    @author Shai Shochat
    @version 0.1
    @date	10/01/2013
    """

    def __init__(self, ip, mng_type = 'snmpv1', unit_version = None):
        self._ip = ip
        self._mng_type = mng_type
        self.unit_version = unit_version
        self._init_managment()
        self.counters = self.snmpCounters( self._mng )

    class snmpCounters(object):

        def __init__(self, mng):
            self._mng = mng
            self.wlan = wlanCnt( self._mng)
        


    def _init_managment(self): 
        self._mng = snmp.Manager(self._ip, self.unit_version ) 
        #self._mng = create_manager(self._ip, self._mng_type, unit_version)

    def set_tx_power(self, tx_power, channel):
        """ Set Tx Power Transmit from RF channel from WLAN-MIB via SNMP """
        mib = ('wlanDefaultTxPower', self.snmp_rf_if(channel))
        self._mng.set(mib, tx_power)

    def get_tx_power(self,  channel):
        """ Get Tx Power Transmit from RF channel from WLAN-MIB via SNMP """
        mib = ( 'wlanDefaultTxPower', self.snmp_rf_if(channel))
        return self._mng.get(mib)
    
    def set_rf_frequency(self, freq , channel):
        """ Set RF frequency for channel from WLAN-MIB via SNMP """
        mib = ('wlanFrequency', self.snmp_rf_if(channel))
        self._mng.set(mib, freq)

    def get_rf_frequency(self, channel):
        """ Get RF frequency for channel from WLAN-MIB via SNMP """	
        mib = ('wlanFrequency', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def set_rf_rate(self, rate , channel):
        """ Set RF rate for channel from WLAN-MIB via SNMP """
        mib = ('wlanDefaultTxDataRate', self.snmp_rf_if(channel))
        self._mng.set(mib, rate)

    def get_rf_rate(self, channel):
        """ Get RF rate for channel from WLAN-MIB via SNMP """
        mib = ('wlanDefaultTxDataRate', self.snmp_rf_if(channel))
        return self._mng.get(mib)
    

    def set_rf_enable(self, enabled , channel):
        """ Set RF enable for channel from WLAN-MIB via SNMP """
        mib = ('wlanRfEnabled', self.snmp_rf_if(channel))
        self._mng.set(mib, self.snmp_bool(enabled))

    def set_rf_frontend_enable(self, enabled , channel):
        """ Set RF Front end enable for channel from WLAN-MIB via SNMP """
        mib = ('wlanRfFrontEndConnected' ,self.snmp_rf_if(channel))
        self._mng.set(mib, self.snmp_bool(enabled))

    def set_rf_frontend_offset(self, enabled , channel):
        """ Set RF Front end for offset channel from WLAN-MIB via SNMP """
        mib = ('wlanRfFrontEndOffset', self.snmp_rf_if(channel))
        self._mng.set(mib, enabled)

    def set_rf_ofdm_chan_bandwidth(self, bw, channel):
        """ Set RF OFDM channel bandwidth via SNMP """
        bandwidth_mhz = { 10 : 1, 20 : 2}
        mib = ('wlanPhyOFDMChannelWidth', self.snmp_rf_if(channel))
        self._mng.set(mib, bandwidth_mhz[bw])

    def set_tssi_pintercept(self, pintercept , channel):
        """ Set RF Front end for offset channel from WLAN-MIB via SNMP """
        mib = ('wlanTssiPintercept', self.snmp_rf_if(channel))
        self._mng.set(mib, pintercept)

    def set_tssi_pslope(self, pslope , channel):
        """ Set RF Front end for offset channel from WLAN-MIB via SNMP """
        mib = ('wlanTssiPslope', self.snmp_rf_if(channel))
        self._mng.set(mib, pslope)

    def get_tssi_pintercept(self, pintercept , channel):
        """ Get Tssi pintercept for channel from WLAN-MIB via SNMP """
        mib = ('wlanTssiPintercept', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def get_tssi_pslope(self, channel):
        """ Get Tssi pslope for channel from WLAN-MIB via SNMP """
        mib = ('wlanTssiPslope', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def get_tssi_interval(self, channel):
        """ Get Tssi interval for channel from WLAN-MIB via SNMP """
        mib = ('wlanTssiInterval', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def set_tssi_interval(self, interval_sec, channel):
        """ Set Tssi interval for channel from WLAN-MIB via SNMP, 0 - TSSI is OFF """
        mib = ('wlanTssiInterval', self.snmp_rf_if(channel))
        self._mng.set(mib, interval_sec)

    def set_random_backoff_enabled(self, enabled , channel):
        """ Set Random backoff enabled for channel from WLAN-MIB via SNMP """
        mib = ('wlanRandomBackoffEnabled', self.snmp_rf_if(channel))
        self._mng.set(mib, self.snmp_bool(enabled))

    def get_random_backoff_enabled(self, channel):
        """ Get Random backoff enabled for channel from WLAN-MIB via SNMP """
        mib = ('wlanRandomBackoffEnabled', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def get_mac_addr(self, channel):
        """ Get Mac address for channel from WLAN-MIB via SNMP """
        mib = ('wlanMacAddress', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def set_tx_diversity_enabled(self, enabled):
        """ Set Tx diversity enabled from WLAN-MIB via SNMP """
        mib = ('wlanTxDiversityEnabled')
        self._mng.set(mib, self.snmp_bool(enabled))

    def set_rx_diversity_enabled(self, enabled):
        """ Set Rx diversity enabled from WLAN-MIB via SNMP """
        mib = ('wlanRxDiversityEnabled')
        self._mng.set(mib, self.snmp_bool(enabled))

    def set_tx_csd(self, tx_csd):
        """ Set CSD index from WLAN-MIB via SNMP """
        mib = ('TX_CSD')
        self._mng.set(mib, tx_csd)

    def get_rx_diversity_cntr(self):
        """ Get Rx diversity for channel from WLAN-MIB via SNMP """
        mib = ('wlanRxDiversityCnt')
        return self._mng.get(mib)

    def get_rx_rssi(self, channel):
        """ Get Rx RSSI for channel from WLAN-MIB via SNMP """
        mib = ('wlanRssiLatestFrame', self.snmp_rf_if(channel))
        return self._mng.get(mib)


    # AUTOTALKS-J2735-MIB          
    def set_bsm_tx_period(self, tx_period_ms ):
        """ Set the Period in ms between sequential Basic Safety Messages from AUTOTALKS-J2735-MIB via SNMP """	
        mib = 'j2735BsmTxPeriod'
        self._mng.set(mib, tx_period_ms)
    
    def get_bsm_tx_period(self):
        """ Set the Period in ms between sequential Basic Safety Messages from AUTOTALKS-J2735-MIB via SNMP """	
        mib = 'j2735BsmTxPeriod'
        return self._mng.get(mib)

    def set_bsm_tx_interface(self, if_id ):
        """ Set MAC interface used for BSM Tx """
        mib = 'j2735BsmTxIf'
        self._mng.set(mib, if_id)
    
    def get_bsm_tx_interface(self):
        """ Get MAC interface used for BSM Tx """	
        mib = 'j2735BsmTxIf'
        return self._mng.get(mib)

    def set_bsm_tx_enabled(self, enable ):
        """ Set bsm tx enabled """
        mib = 'j2735BsmTxEnabled'
        self._mng.set(mib, enable)
    
    def get_bsm_tx_enabled(self):
        """ Get bsm tx enabled """	
        mib = 'j2735BsmTxEnabled'
        return self._mng.get(mib)

    def set_bsm_p2_ext_ratio(self, value ):
        """ Set bsm tx enabled """
        mib = 'j2735BsmSafetyExtTxRatio'
        self._mng.set(mib, value)

    def get_nav_fix_available(self):
        """ Get bsm tx enabled """	
        mib = 'navFixAvailable'
        return self._mng.get(mib)

    #AUTOTALKS-VCA-MIB
    def set_vca_tx_period(self, value, channel ):
        """ Set vca tx period """
        mib = ('vcaTxPeriod', self.snmp_rf_if(channel))
        self._mng.set(mib, value)

    def set_vca_tx_enabled(self, enabled, channel ):
        """ Set vca tx enable """
        mib = ('vcaTxEnabled', self.snmp_rf_if(channel))
        self._mng.set(mib, self.snmp_bool(enabled))

    def set_vca_log_mode(self, mode):
        """ Set vca log mode """
        mib = ('vcaLogMode')
        self._mng.set(mib, mode)

    def set_vca_frame_len(self, value, channel ):
        """ Set vca frame lenght """
        mib = ('vcaFrameLen', self.snmp_rf_if(channel))
        self._mng.set(mib, value)


    #AUTOTALKS-WLAN-MIB
    def get_wlan_frame_rx_cnt(self, channel):
        """ Gets the number of rx frame sent by HW via SNMP """	
        mib = ('wlanFrameRxCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def get_wlan_frame_tx_cnt(self, channel):
        """ Gets the number of tx frame sent by HW via SNMP """	
        mib = ('wlanFrameTxCnt', self.snmp_rf_if(channel))
        return self._mng.get(mib)

    def set_bsm_security_enable(self, enable):
        """ Set bsm security enabled """	
        mib = 'j2735BsmSecEnabled'
        self._mng.set(mib, enable)


