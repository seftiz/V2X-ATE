"""

Ver 3.0
========================
1) Adding vsg frame count support 



Ver 2.0
==================
1) Add support to VSG
2) Moved get_scalar_meas from VSA class to general class

Ver 1.0
==================
1) IQ2010 Support 
2) VSA driver




"""
import os, sys
import ctypes
import time
import logging

log = logging.getLogger(__name__)

class IQ2010_Instrument(object):

    def __init__(self, hwd):
        self.hwd = hwd

        # Set Function return value for python 
        self.get_error_string = self.hwd.LP_GetErrorString
        self.get_error_string.restype = ctypes.c_char_p
        self.get_error_string.argtypes = [ ctypes.c_int ]


class IQ2010_VSG(IQ2010_Instrument):
    
    def __init__(self, hwd):

        IQ2010_Instrument.__init__(self,hwd)


    def set(self , rf_freq_hz, rf_pwr_lvl_dbm, port, set_gap_pwr_off, freq_shift_hz = 0.0):
        """//! Sets up VSG
            /*!
            * \param[in] rfFreqHz The center frequency of VSG (Hz)
            * \param[in] rfGainDb The output power level of VSG (dBm)
            * \param[in] port The port to which the VSG connects, with the following options:
            *				- =1: OFF
            *				- =2: Left RF port (RF1)
            *				- =3: Right RF port (RF2) (Default)
            *				- =4: Baseband
            * \param[in] setGapPowerOff
            *              - =true: Turn off RF power in the gap between packets
            *              - =false: Does not turn off RF power in the gap between packets
            * \param[in] dFreqShiftHz Frequency Shit
            * \return ERR_OK if no errors; otherwise call LP_GetErrorString() for detailed error message.
            */
            IQMEASURE_API int		LP_SetVsg(double rfFreqHz, double rfPowerLeveldBm, int port, bool setGapPowerOff = true, double dFreqShiftHz = 0.0);
        """
        # Define function prototype for python
        set_vsg_cfg = self.hwd.LP_SetVsg
        set_vsg_cfg.restype = ctypes.c_int
        set_vsg_cfg.argtypes = [ ctypes.c_double, ctypes.c_double, ctypes.c_int ,ctypes.c_int , ctypes.c_double ]
        
        
        #print "rf_freq_hz {}, rf_pwr_lvl_dbm {}, port {}, set_gap_pwr_off {}, freq_shift_hz {}".format( rf_freq_hz, rf_pwr_lvl_dbm, port, set_gap_pwr_off, freq_shift_hz )
        retry = 0
        while ( retry < 3 ):
            rc = set_vsg_cfg( rf_freq_hz, rf_pwr_lvl_dbm, port, set_gap_pwr_off, freq_shift_hz)
            if rc != 0:
                 retry += 1
                 time.sleep(1)
            else:
                retry = 10

        if retry == 3:
             raise Exception( " Failed to configure set config" )

             

        
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )

    def load(self, mod_file_name, load_internal_wave_form = 0):
        """
        //! Loads the modulation file (waveform) to VSG and performs auto transmit of the loaded VSG mod file in free run mode
        /*!
        * \param[in] modFileName The .mod file to be loaded
        * \param[in] Choose whether to load modFile from internal tester (1) or upload from file (0) default is (0).
        *            This option is only valid with IQxel tester other wise it is ignored.
        *
        * \return ERR_OK if successful; otherwise call LP_GetErrorString() for detailed error message.
        */
        IQMEASURE_API int		LP_SetVsgModulation(char *modFileName, int loadInternalWaveform = 0);
        """
        # Define function prototype for python
        load_vsg_file_cfg = self.hwd.LP_SetVsgModulation
        load_vsg_file_cfg.restype = ctypes.c_int
        load_vsg_file_cfg.argtypes = [ ctypes.c_char_p, ctypes.c_int ]

        rc = load_vsg_file_cfg( mod_file_name , load_internal_wave_form )
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )

    def rf_state(self, active):
        """
        //! Turn ON/OFF the first VSG RF
        /*!
         * \param[in] enabled 1 to turn on the first VSG RF; 0 to turn off the first VSG RF
         *
         * \return ERR_OK if the first VSG RF is turned on or off; otherwise call LP_GetErrorString() for detailed error message.
         */
        IQMEASURE_API int		LP_EnableVsgRF(int enabled);
        """
        vsg_rf_state = self.hwd.LP_EnableVsgRF
        vsg_rf_state.restype = ctypes.c_int
        vsg_rf_state.argtypes = [ ctypes.c_int ]

        state = 0
        if active == True:
            state = 1
        
        rc = vsg_rf_state( state )
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )

    def set_frame_count(self, frames_to_send ):
        """
        //! Sets up the number of frames for VSG to transmit
        /*!
        * \param[in] frameCnt The number of frames to be transmitted between 0 and 65534, where "0" indicates continuous transmission
        *
        * \return ERR_OK if number of frames accepted; otherwise call LP_GetErrorString() for detailed error message.
        */
        IQMEASURE_API int		LP_SetFrameCnt(int frameCnt);
        """
        vsg_frame_cnt = self.hwd.LP_SetFrameCnt
        vsg_frame_cnt.restype = ctypes.c_int
        vsg_frame_cnt.argtypes = [ ctypes.c_int ]

        rc = vsg_frame_cnt( frames_to_send )
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )

    def _tx_done(self):
        """
        //! Check if TX is done
        /*!
         * \return ERR_OK if TX is done; otherwise call LP_GetErrorString() for detailed error message.
         */
        IQMEASURE_API int		LP_TxDone(void);
        """
        vsg_tx_done = self.hwd.LP_TxDone
        vsg_tx_done.restype = ctypes.c_int
        
        rc = vsg_tx_done()
        return rc
        

            
    def transmit_frame_count(self, frame_to_send, time_out_sec = 60):
        """
        Set and Transmit number of frames and wait for end of transmision)
        """
        self.rf_state(False)
        self.set_frame_count(1)
        #time.sleep(1)
        self.rf_state(True)
        time.sleep( 0.2 )
        self.set_frame_count(frame_to_send)

        start_time = time.time()
        while (self._tx_done() != 0):
            # Sleep for 50 mSec
            time.sleep( 50.0 / 1000.0 )
            if (time.time() - start_time) > time_out_sec:
                log.info("time out")
                return (-1)

        return 0

    def trigger_type(self, trigger_type = 0):
        """
        //! Sets up VSG triggerType
        /*!
        * \param[in] triggerType Select VSG trigger Type. 0 = IQV_VSG_TRIG_FREE_RUN; 1 = IQV_VSG_TRIG_EXT_1; 2 = IQV_VSG_TRIG_EXT_2
        * \return ERR_OK if no errors; otherwise call LP_GetErrorString() for detailed error message.
        */
        IQMEASURE_API int		LP_SetVsgTriggerType(int trigger);
        """
        vsg_rf_state = self.hwd.LP_SetVsgTriggerType
        vsg_rf_state.restype = ctypes.c_int
        vsg_rf_state.argtypes = [ ctypes.c_int ]
   
        rc = vsg_rf_state( trigger_type )
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )




class IQ2010_VSA(IQ2010_Instrument):

    def __init__(self, hwd):
        IQ2010_Instrument.__init__(self, hwd)


    def __del__(self):
        pass

    def get_config(self, values ):
        """
        *! Return the VSA settings
        *!
        * \param[out] freqHz VSA frequency (Hz) setting
        * \param[out] ampl VSA amplitude (dBm);
        * \param[out] port VSA port: 1=PORT_OFF, 2=PORT_LEFT, 3=PORT_RIGHT, 4=PORT_BB;
        * \param[out] rfEnabled VSA RF state: 0=disalbed; 1=enabled
        * \param[out] triggerLevel VSA trigger level
        *
        * \return ERR_OK if the VSA settings are returned; otherwise call LP_GetErrorString() for detailed error message.
        */
        IQMEASURE_API int		LP_GetVsaSettings(double *freqHz, double *ampl, IQAPI_PORT_ENUM *port, int *rfEnabled, double *triggerLevel, int *triggertype=NULL);
        """
        get_vsa_config = self.hwd.LP_GetVsaSettings
        get_vsa_config.restype = ctypes.c_int
        get_vsa_config.argtypes = [ ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int) ,ctypes.POINTER(ctypes.c_int) , ctypes.POINTER(ctypes.c_double),  ctypes.POINTER(ctypes.c_int) ]

        rf_freq_hz = ctypes.c_double(0)
        ampl_dbm = ctypes.c_double(0)
        port = ctypes.c_int(0)
        rf_enabled = ctypes.c_int(0)
        trigger_level = ctypes.c_double(0)
        trigger_type = ctypes.c_int(0)

        rc = get_vsa_config( rf_freq_hz, ampl_dbm, port, port, rf_enabled, trigger_level, trigger_type)
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )

        # build new dict
        values = dict()
        values['rf_freq_hz'] = rf_freq_hz
        values['ampl_dbm'] = ampl_dbm
        values['port'] = port
        values['rf_enabled'] = rf_enabled
        values['trigger_level'] = trigger_level
        values['trigger_type'] = trigger_type



    def set_config(  self, rf_freq_hz, rf_ampl_db, port, ext_atten_db = 0, trigger_level_db = -25, trigger_pre_time=10e-6, freq_shift_hz = 0.0):
        """
        ! Sets up VSA for data capturing
        !
         \param[in] rfFreqHz The center frequency of VSA (Hz)
         \param[in] rfAmplDb The amplitude of the peak power (dBm) for VSA to work with
         \param[in] port The port to which the VSG connects, with the following options:
        				- =1: OFF
        				- =2: Left RF port (RF1) (Default)
        				- =3: Right RF port (RF2)
        				- =4: Baseband
         \param[in] extAttenDb The external attenuation (dB).  Set to 0 always.
         \param[in] triggerLevelDb The trigger level (dBm) used for signal trigger (ignored in Free-run and External Trigger Modes)
         \param[in] triggerPreTime The pre-trigger time used for signal capture
        
         \return ERR_OK if no errors; otherwise call LP_GetErrorString() for detailed error message.
         \remark For VSA to work optimally with the input signal, set rfAmplDb to the peak power of the input signal.


        IQMEASURE_API int LP_SetVsa(double rfFreqHz, double rfAmplDb, int port, double extAttenDb=0, double triggerLevelDb=-25, double triggerPreTime=10e-6);

        IQMEASURE_API int LP_SetVsa(double rfFreqHz, double rfAmplDb, int port, double extAttenDb=0, double triggerLevelDb=-25, double triggerPreTime=10e-6, double dFreqShiftHz = 0.0);

        """
        # Define function prototype for python
        # if self.set_vsa is None:
        set_vsa_config = self.hwd.LP_SetVsa
        set_vsa_config.restype = ctypes.c_int
        set_vsa_config.argtypes = [ ctypes.c_double, ctypes.c_double, ctypes.c_int ,ctypes.c_double , ctypes.c_double,  ctypes.c_double, ctypes.c_double ]

        #print "rf_freq_hz {}, rf_ampl_db {}, port {}, ext_atten_db {}, trigger_level_db {}, trigger_pre_time {}, freq_shift_hz {}".format( rf_freq_hz, rf_ampl_db, port, ext_atten_db, trigger_level_db, trigger_pre_time, freq_shift_hz )
        retry = 0
        while ( retry < 3 ):
            rc = set_vsa_config( rf_freq_hz, rf_ampl_db, port, ext_atten_db, trigger_level_db, trigger_pre_time, freq_shift_hz)
            if rc != 0:
                #raw_input("ERROR@set_vsa_config : Press Enter to continue...")
                # raise Exception( rc, self.get_error_string(rc) )
                retry += 1
                time.sleep(1)
            else:
                retry = 10

        if retry == 3:
             raise Exception( " Failed to configure set config" )

        

    def set_trigger_timeout (  self,  triggerTimeoutSec ):
        # Define function prototype for python
        # if self.set_trigger_timeout is None:
       set_trigger_timeout = iq2010_hwd.LP_SetVsaTriggerTimeout
       set_trigger_timeout.restype = ctypes.c_int
       set_trigger_timeout.argtypes = [ ctypes.POINTER(ctypes.c_double) ]

        

    
    def capture_data(  self, sampling_time_secs, trigger_type = 6, sample_freq_hz = 80e6, ht40_mode = 0 ):
        """
          ! Perform VSA data capture
         *!
         * \param[in] samplingTimeSecs Capture time in seconds
         * \param[in] triggerType Trigger type used for capturing.  Valid options are:
         *      - 1 = Free-run
         *      - 2 = External trigger
         *      - 6 = Signal Trigger
         * \param[optinal] modeHT40 Specifies if the capture is for the HT40 mask (802.11n only).  1--HT40 mask mode; 0--Normal mode
         * \param nonBlockingState = 0
            IQMEASURE_CAPTURE_NONBLOCKING_STATES
            {
	            BLOCKING,	// NONBLOCKING is off
	            ARM_TRIGGER,
	            CHECK_DATA
            };
         *
         * \return ERR_OK if the data capture is successful; otherwise call LP_GetErrorString() for detailed error message.
         * \remark modeHT40 only needs to set to 1 if the HT40 mask (120MHz) analysis is desired.  For LP_Analyze80211n(), this flag can be set to 0.
         */
        IQMEASURE_API int		LP_VsaDataCapture(double samplingTimeSecs, int triggerType=6, double sampleFreqHz=80e6,
									        int ht40Mode=OFF, IQMEASURE_CAPTURE_NONBLOCKING_STATES nonBlockingState=BLOCKING );
        """
        #if self.capture_data is None:
        capture_data = self.hwd.LP_VsaDataCapture
        capture_data.restype = ctypes.c_int
        capture_data.argtypes = [ ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_int, ctypes.c_int ]

        rc = capture_data( sampling_time_secs, trigger_type, sample_freq_hz , ht40_mode, 0 )
        if rc != 0:
            #raise Exception( rc, self.get_error_string(rc) )
            pass
            
            
    def analyze_802_11p( self, ph_corr_mode = 2, ch_estimate = 1, sym_tim_corr=2, freq_sync=2, ampl_track = 1, ofdm_mode = 2 ):
        """
        ! Perform 802.11p Analysis on current capture
        *!
        * \param[in] ph_corr_mode Phase Correction Mode with the following valid options:
        *         - 1: Phase correction off
        *         - 2: Symbol-by-symbol correction (Default)
        *         - 3: Moving avg. correction (10 symbols)
        * \param[in] ch_estimate Channel Estimate with the following options:
        *         - 1: Raw Channel Estimate (based on long trainling symbols) (Default)
        *         - 2: 2nd Order Polyfit
        *         - 3: Full packet estimate
        * \param[in] sym_tim_corr Symbol Timing Correction with the following options:
        *         - 1: Symbol Timing Correction Off
        *         - 2: Symbol Timing Correction ON (Default)
        * \param[in] freq_sync Frequency Sync. Mode with the following options:
        *         - 1: Short Training Symbol
        *         - 2: Long Training Symbol (Default)
        *         - 3: Full Data Packet
        * \param[in] ampl_track Amplitude Tracking with the following options:
        *         - 1: Amplitude tracking off (Default)
        *         - 2: Amplitude tracking on
        * \param[in] ofdm_mode Specifies OFDM mode with the following options:
        *         - 0: OFDM mode based on IEEE 802.11a or 802.11g standards specification
        *         - 1: OFDM turbo mode based on IEEE 802.11a or 802.11g standards specification
        *         - 2: ASTM DSRC standards specification (Default)
        *         - 3: OFDM quarter rate
        *
        * \return ERR_OK if the 802.11p analysis succeeded; otherwise call LP_GetErrorString() for detailed error message.
        */
        proto : IQMEASURE_API int LP_Analyze80211p(int ph_corr_mode=2, int ch_estimate=1, int sym_tim_corr=2, int freq_sync=2, int ampl_track=1, int ofdm_mode=2);
        """
    
        # if analyze_80211ag is None:
        analyze_80211p = self.hwd.LP_Analyze80211p
        analyze_80211p.restype = ctypes.c_int
        analyze_80211p.argtypes = [ ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int ]

        rc = analyze_80211p( ph_corr_mode, ch_estimate, sym_tim_corr, freq_sync, ampl_track, ofdm_mode )      
        if rc != 0:
            #raise Exception( rc, self.get_error_string(rc) )   
            pass
            

    def set_agc( self, all_testers = True):
        """
        ! Performs AGC (Automatic Gain Control) on VSA
        *!
        * \param[out] rfAmplDb The setting of rfAmplDb of VSA set by AGC
        *
        * \return ERR_OK if no errors; otherwise call LP_GetErrorString() for detailed error message.
        */
        IQMEASURE_API int		LP_Agc(double *rfAmplDb, bool allTesters = true);
        """        
        
        agc = self.hwd.LP_Agc
        agc.restype = ctypes.c_int
        agc.argtypes = [ ctypes.POINTER(ctypes.c_double), ctypes.c_bool ]
        
        rf_ampl_db = ctypes.c_double(0)

        rc = agc( ctypes.byref(rf_ampl_db), all_testers)  
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )    
       
        return rf_ampl_db 

               
    def analyze_802_11ag(  self, ph_corr_mode = 2, ch_estimate = 1, sym_tim_corr = 2, freq_sync = 2, ampl_track = 1, ofdm_mode = 0):
        """
        ! Perform 802.11 a/g Analysis on current capture
        !
         \param[in] ph_corr_mode Phase Correction Mode with the following valid options:
                         - 1: Phase correction off
                         - 2: Symbol-by-symbol correction (Default)
                         - 3: Moving avg. correction (10 symbols)
         \param[in] ch_estimate Channel Estimate with the following options:
                         - 1: Raw Channel Estimate (based on long trainling symbols) (Default)
                         - 2: 2nd Order Polyfit
                         - 3: Full packet estimate
         \param[in] sym_tim_corr Symbol Timing Correction with the following options:
                         - 1: Symbol Timing Correction Off
                         - 2: Symbol Timing Correction ON (Default)
         \param[in] freq_sync Frequency Sync. Mode with the following options:
                         - 1: Short Training Symbol
                         - 2: Long Training Symbol (Default)
                         - 3: Full Data Packet
         \param[in] ampl_track Amplitude Tracking with the following options:
                         - 1: Amplitude tracking off (Default)
                         - 2: Amplitude tracking on
        
         \return ERR_OK if the 802.11 a/g analysis succeeded; otherwise call LP_GetErrorString() for detailed error message.
        
         IQMEASURE_API int LP_Analyze80211ag(int ph_corr_mode=2, int ch_estimate=1, int sym_tim_corr=2, int freq_sync=2, int ampl_track=1, int ofdm_mode = IQV_OFDM_80211_AG);
        """
        # if analyze_80211ag is None:
        analyze_80211ag = self.hwd.LP_Analyze80211ag
        analyze_80211ag.restype = ctypes.c_int
        analyze_80211ag.argtypes = [ ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int ]

        rc = analyze_80211ag(ph_corr_mode, ch_estimate, sym_tim_corr, freq_sync, ampl_track, ofdm_mode)      
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )   



    def get_scalar_meas(  self, measurment_name ):
            
        """
        ! Get a scalar measurement result
        *!
        * \param[in] measurement The measurement name.  Please refer to \ref group_scalar_measurement "Scalar Measurements" for all available measurement names
        * \param[in] index The index of the measurement.  In most case, index would be zero.  For MIMO analysis, some measurements, such as EVM, may have more than one results
        *
        * \return The value of the measurement.  -99999.99 (a special defined negative value) will be returned if no measurement available
        *
        IQMEASURE_API double LP_GetScalarMeasurement(char *measurement, int index=0);
        """

        # if scalar_meas is None:
        scalar_meas = self.hwd.LP_GetScalarMeasurement
        scalar_meas.restype = ctypes.c_double
        scalar_meas.argtypes = [ ctypes.c_char_p, ctypes.c_int ]

        val = scalar_meas( measurment_name, 0 )
        if val == -99999.99:
            raise Exception

        log.info("Get scalar measurment from IQ2010 : %s -> %f" % ( measurment_name, val ) )
        return val 

    def DONT_USE_get_double_measure(self, measurment_name):
        """
        *! Retrieve Analysis Results [Double] in average, minimum and maximum value
        *!
        * \param[in]  measurementName          The measurement name.  Please refer to \ref group_scalar_measurement "Vector Measurements" for all available measurement names.
        * \param[out] average Average value    Average value for all the result(s). Result set can be more than one if the specified capture count is larger than one when using multi-capture function 'IQ2010EXT_VsaMultiCapture(...)'
        * \param[out] minimum Minimum value    Minimum value of all the result(s)
        * \param[out] maximum Maximum value    Maximum value of all the result(s)
        *
        * \return ERR_OK if successful; otherwise, call IQ2010EXT_GetLastErr() for detailed error message.
        */
        IQMEASURE_API int		LP_IQ2010EXT_GetDoubleMeasurements(char *measurementName, double *average, double *minimum, double *maximum);
        """

        avg_measure = self.hwd.LP_IQ2010EXT_GetDoubleMeasurements
        avg_measure.restype = ctypes.c_int
        avg_measure.argtypes = [ ctypes.c_char_p, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double) ]

        average = ctypes.c_double(0)
        minimum = ctypes.c_double(0)
        maximum = ctypes.c_double(0)
        
        rc = avg_measure(measurment_name, ctypes.byref(average), ctypes.byref(minimum), ctypes.byref(maximum) )
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )   

        results = dict()
        results['average'] = average.value
        results['minimum'] = minimum.value
        results['maximum'] = maximum.value

        return results

    def get_spectral_mask_measure (self, bandwidth_index = 0):
        """
        ! Get spectral mask result
        /*!
        * \param[in] bandwidth_index One enum value of \ref LP_SPECTRAL_MASK_ENUM.
            
            bandwidth_options = {"SPECTRAL_MASK_OFDM":0}
            IQMEASURE_API enum LP_SPECTRAL_MASK_ENUM
            {
                SPECTRAL_MASK_OFDM = 0,
                SPECTRAL_MASK_MIMO_HT20,
                SPECTRAL_MASK_MIMO_HT40,
                SPECTRAL_MASK_WiMAX_10MHz,
                SPECTRAL_MASK_WiMAX_7MHz,
                SPECTRAL_MASK_11b = 20,
                SPECTRAL_MASK_ZIGBEE,
                SPECTRAL_MASK_BT,
                SPECTRAL_MASK_BT_EDR,
                SPECTRAL_MASK_NONE = 99,
            };
    
        * \param[out] ViolationPercent The Percent of violations where the mask is below the PSD data value.
        * \param[out] length Array length of the measured result.
        * \param[out] freqs_MHz Array of the measured frequency.
        * \param[out] trace_dBm Array of the measured power.
        * \param[out] mask Array of the calculated spectral mask for measured result.
        * \return ERR_OK.
        */
        IQMEASURE_API int LP_GetResultSpectralMask(int bandwidth_index, double *ViolationPercent, int *length, double *freqs_MHz, double *trace_dBm, double *mask);
        """
        spectral_mask_measure = self.hwd.LP_GetResultSpectralMask
        spectral_mask_measure.restype = ctypes.c_int
        spectral_mask_measure.argtypes = [ ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double) ]
        
        violation_percent = ctypes.c_double(0)
        length_array = ctypes.c_int(0)
        freqs_mhz_array = ctypes.c_double(0)
        trace_dbm_array = ctypes.c_double(0)
        mask_array = ctypes.c_double(0)
        # (ctypes.POINTER(ctypes.c_double) * 1)() #
        
        # rc = spectral_mask_measure(bandwidth_index, ctypes.byref(violation_percent), ctypes.byref(length_array), ctypes.byref(freqs_mhz_array), ctypes.byref(trace_dbm_array), ctypes.byref(mask_array))
        rc = spectral_mask_measure(bandwidth_index, ctypes.byref(violation_percent), ctypes.byref(length_array), ctypes.byref(freqs_mhz_array), ctypes.byref(trace_dbm_array), ctypes.byref(mask_array) )
        if rc != 0:
            raise Exception( rc, self.get_error_string(rc) )  
            
        results = dict()
        results['violation_percent'] = violation_percent.value
        results['length_array'] = length_array.value
        results['freqs_mhz_array'] = freqs_mhz_array.value
        results['trace_dbm_array'] = trace_dbm_array.value
        results['mask_array'] = mask_array.value
        return results

class IQ2010(object):

    def __init__( self, dll_lib = "\\\\fs01\\docs\\system\\ate\\Drivers\\VSA_IQ2010\\IQMeasure"):

        os.chdir( dll_lib )
        print "Changeing library to %s" % dll_lib
        self.dll_lib = dll_lib

        self.hwd = ctypes.cdll.LoadLibrary('IQmeasure.dll')
        # Set Function return value for python 
        self.get_error_string = self.hwd.LP_GetErrorString
        self.get_error_string.restype = ctypes.c_char_p
        self.get_error_string.argtypes = [ ctypes.c_int ]

        # Init the vsa part of the instrument
        self.vsa = IQ2010_VSA( self.hwd )
        self.vsg = IQ2010_VSG( self.hwd )


        
    
    def get_scalar_meas(  self, measurment_name ):
        """
        ! Get a scalar measurement result
        *!
        * \param[in] measurement The measurement name.  Please refer to \ref group_scalar_measurement "Scalar Measurements" for all available measurement names
        * \param[in] index The index of the measurement.  In most case, index would be zero.  For MIMO analysis, some measurements, such as EVM, may have more than one results
        *
        * \return The value of the measurement.  -99999.99 (a special defined negative value) will be returned if no measurement available
        *
        IQMEASURE_API double LP_GetScalarMeasurement(char *measurement, int index=0);
        """

        # if scalar_meas is None:
        scalar_meas = self.hwd.LP_GetScalarMeasurement
        scalar_meas.restype = ctypes.c_double
        scalar_meas.argtypes = [ ctypes.c_char_p, ctypes.c_int ]

        val = scalar_meas( measurment_name, 0 )
        if val == -99999.99:
            raise Exception

        log.info("Get scalar measurment from IQ2010 : %s -> %f" % ( measurment_name, val ) )
        return val 
        

    def __del__(self):
        pass

    def Init_2010EXT(self):
        """
        //! Initializes IQ2010 Extension
        /*!
        * \return ERR_OK if initialzation is done successfully; otherwise call IQ2010EXT_GetLastErr() for detailed error message.
        * \remark This function has to be called right after IQ2010 software has been connected to the test system
        */
        IQMEASURE_API int		LP_IQ2010EXT_Init(void);
        """
        self.hwd.LP_IQ2010EXT_Init( )
        
        
    def connect( self, device_ip ):
        """
        //! Initializes the MATLAB environment for running IQmeasure
        /*!
        * \param[in] IQtype Pointer to IQ tester type. IQXel or IQ legacy testers. It decides what dll to link.
 	        IQTYPE_2010 = 0,					
	        IQTYPE_XEL = 1

        * \param[in] testerControlMethod indicates what method is used to control LP tester: 0 = IQapi, 1 = SCPI command
        * \return 0 if MATLAB initialized OK; non-zero indicates MATLAB failed to initialize.
        * \remark This function needs to be run only once, typically at the very beginning of a program.
        */
        IQMEASURE_API int		LP_Init(int IQtype = IQTYPE_XEL,int testerControlMethod = 0);
        """
        self.hwd.LP_Init( 0 , 0)


        # self.Init_2010EXT()
        
        print "Connecting IQ2010 at %s" % device_ip
        rc = self.hwd.LP_InitTester( device_ip, 0 )
        if rc != 0:
            print self.hwd.LP_GetErrorString( rc )

   
    def get_version( self ):
        """
        @ Gets the version information
        
        @param[out] buffer The buffer that will return the version information
        @param[in] buf_size Indicates the size of the buffer
        
        IQMEASURE_API bool LP_GetVersion(char *buffer, int buf_size);
        """


        #if get_ver is None:
        get_ver = self.hwd.LP_GetVersion
        get_ver.restype = ctypes.c_int
        get_ver.argtypes = [ ctypes.c_char_p, ctypes.c_int ]

        p = ctypes.create_string_buffer(255)      # create a byte buffer, initialized to NUL bytes
        rc = get_ver( p, 254 )
        return p.value

    def get_capture(self):
        """
        //! Get memory addresses for a capture
        /*!
        * \param[in] dut
        * \param[in] captureIndex
        * \param[out] real
        * \param[out] imag
        * \param[out] length
        *
        * \return ERR_OK if successful; otherwise call LP_GetErrorString() for detailed error message.
        */
        IQMEASURE_API int LP_GetCapture(int dut, int captureIndex, double *real[], double *imag[], int length[]);
        """
        get_capture = self.hwd.LP_GetCapture
        get_capture.restype = ctypes.c_bool
        get_capture.argtypes = [ ctypes.int, ctypes.c_int ]

        p = ctypes.create_string_buffer(255)      # create a byte buffer, initialized to NUL bytes
        rc = get_ver( p, 254 )
        return p.value


def usage_example():

    import time

    # create new instance for IQ2010
    iq2010 = IQ2010()
    
    # connect to server via ip
    iq2010.connect("127.0.0.1")

    print iq2010.get_version()
    print "\n\n\nWorking with IQ2010 version %s\n\n\n" % iq2010.get_version()
    
    print "Setting VSG to 5910e6, -20, 2, True, 0.0"
    iq2010.vsg.set( 5910e6, -20, 3, True, 0.0)
    print "Loading file"
    iq2010.vsg.load( "\\\\fs01\\docs\\system\\Integration\\Signals_sample\\10MHz\\qpsk_6MHz_434Bytes.mod" )
    iq2010.vsg.rf_state ( False )


    # Clear unit stats now
    
    print "Transmit 1000 packets"
    iq2010.vsg.transmit_frame_count(1000)
    return

    # Cont transmit
    iq2010.vsg.rf_state ( True )
    time.sleep(10)
    iq2010.vsg.rf_state ( False )
    time.sleep(1)

    """
    VSA example
    """
    #return 
    
    print "Setting VSA to requency of 5.860Mhz, max ampl to 5, vsa will be on left port"
    iq2010.vsa.set_config( 5860e6, 5, 2, 0, -25, 10e-6 )

    agc_data = iq2010.vsa.set_agc()
    print "\nReceived agc : %f\n" % agc_data.value
    
    print "Capture data for 2000uSec"
    iq2010.vsa.capture_data( 2000e-6 ) 

    print "Activate 802.11P analysis on data"
    
    iq2010.vsa.analyze_802_11p()

    
    """
    Measurments exapmles
    """
    print "start mesurments"
    measurment_analysis_80211ag_vals = [ "evmAll", "evmData", "evmPilot", "codingRate",  "freqErr", "clockErr", "ampErr", "ampErrDb", "phaseErr", "rmsPhaseNoise", "rmsPowerNoGap", "rmsPower",
                                        "pkPower", "rmsMaxAvgPower", "psduCrcFail", "plcpCrcPass", "dataRate", "numSymbols", "numPsduBytes", "SUBCARRIER_LO_B_VSA1", "VALUE_DB_LO_B_VSA1", 
                                        "SUBCARRIER_LO_A_VSA1", "VALUE_DB_LO_A_VSA1", "SUBCARRIER_UP_A_VSA1",  "VALUE_DB_UP_A_VSA1", "SUBCARRIER_UP_B_VSA1", "VALUE_DB_UP_B_VSA1", "LO_LEAKAGE_DBR_VSA1" ]

    for measure in measurment_analysis_80211ag_vals:
        try: 
            val = iq2010.vsa.get_scalar_meas(measure)
            print "get var %s : %f" % ( measure, val )
        except:
            pass

    """
    VSG Example
    """

 

        


if __name__ == "__main__":
    import time
    
    iq2010 = IQ2010()
    
    #iq2010.connect("127.0.0.1")
    iq2010.connect("10.10.0.7")

    print iq2010.get_version()
    print "\n\n\nWorking with IQ2010 version %s\n\n\n" % iq2010.get_version()

    
    rf_freq_hz  = 5880.0 * 1e6
    rf_ampl_db  = -8
    port = 3
    ext_atten_db = 8
    trigger_level_db = -38
    trigger_pre_time  = 1e-05
    freq_shift_hz = 0.0
    i = 0
    
    for i in range(0,1):
        
        iq2010.vsa.set_config( rf_freq_hz, rf_ampl_db, port, ext_atten_db, trigger_level_db, trigger_pre_time )
        iq2010.vsa.set_agc()
        iq2010.vsa.capture_data( 2000e-6 )
        time.sleep(0.1)
        iq2010.vsa.analyze_802_11p()
        time.sleep(0.5)
        
        for i in range (0,2):          
        
            iq2010.vsa.capture_data( 2000e-6 )
            time.sleep(0.2)
            iq2010.vsa.analyze_802_11p()
            time.sleep(0.5)
            try:
                a = iq2010.vsa.get_scalar_meas('evmAll')
                b = iq2010.vsa.get_scalar_meas('dcLeakageDbc')
                c = iq2010.vsa.get_scalar_meas('ampErrDb')
                d = iq2010.vsa.get_scalar_meas('phaseErr')
                e = iq2010.vsa.get_scalar_meas('rmsPowerNoGap')
            except Exception as e:
                print "ERROR : {}, ignoring".format ( e )
    
    print "Getting spectral mask"
    iq2010.vsa.get_spectral_mask_measure()
    
    # usage_example()

    
        

