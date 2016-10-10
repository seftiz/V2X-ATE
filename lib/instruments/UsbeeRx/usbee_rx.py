"""
// USBeeRXToolbuilderExampleC.cpp : Defines the entry point for the console application.
//

CWAV_IMPORT unsigned long CWAV_API InitializeRX( void );
CWAV_IMPORT unsigned long CWAV_API GetSignalsRX( unsigned char *digital0to7, unsigned char *digital8toF, unsigned char *analog1, unsigned char *analog2, unsigned char *CandT  );
CWAV_IMPORT unsigned long CWAV_API SetSignalsRX( unsigned long mask, unsigned long value  );
CWAV_IMPORT unsigned long CWAV_API GenerateAnalogWaveformRX( unsigned long SamplesPerSecond, unsigned char SamplesPerCycle, unsigned char *samples );
CWAV_IMPORT unsigned long CWAV_API GeneratePWMWaveformRX( unsigned char channel,  unsigned long samplespersecond, unsigned char dutycycle  );
CWAV_IMPORT unsigned long CWAV_API LoadDigitalWaveformRX( unsigned long numberofsamples, unsigned char *samples  );
CWAV_IMPORT unsigned long CWAV_API GenerateDigitalWaveformRX( unsigned char channelmask,unsigned char GenerateOn, unsigned char loop,  unsigned char waitT,  unsigned char Trising,  unsigned char externalclock,  unsigned char Crising, unsigned long samplespersecond);
CWAV_IMPORT unsigned long CWAV_API GetFrequencyAndCountsRX( unsigned long *edgecounts0, unsigned long *edgecounts1, unsigned long *edgecounts2, unsigned long *edgecounts3, unsigned long *freq4, unsigned long *freq5, unsigned long *freq6, unsigned long *freq7    );
CWAV_IMPORT unsigned long CWAV_API ClearCountsRX( void );
CWAV_IMPORT unsigned long CWAV_API EnableCountsRX( void );
CWAV_IMPORT unsigned long CWAV_API DisableCountsRX( void );
CWAV_IMPORT unsigned long CWAV_API SetLogicThresholdRX( float Thresh  );
CWAV_IMPORT unsigned long CWAV_API StartCaptureRX( unsigned long buffersize, unsigned char TriggerPosition, float SampleRate, unsigned long channelmask, unsigned char ExternalClockingOn, unsigned char CompressionOn  );
CWAV_IMPORT unsigned long CWAV_API CaptureStatusRX( unsigned char *Full, unsigned char *Triggered, unsigned char *Running );
CWAV_IMPORT unsigned long CWAV_API StopCaptureRX( void );
CWAV_IMPORT unsigned long CWAV_API TriggerNowRX( void );
CWAV_IMPORT unsigned long CWAV_API EndCaptureRX( __int64 *ActualNumberOfSamples, __int64 *TriggerPosition);
CWAV_IMPORT unsigned long CWAV_API SampleData( __int64 index ); 
CWAV_IMPORT __int64 CWAV_API FindNextEdge( __int64 UCSample, unsigned long channelmask, unsigned long direction ); 
CWAV_IMPORT unsigned long CWAV_API SetTriggersRX( int TrigXEnabled, int TrigYEnabled, int TrigXorYEnabled, int TrigXandYEnabled, int TrigXthenYEnabled, int TrigYthenXEnabled,
				
	int TrigX_DigitalEdgeEnabled, int TrigX_AnalogEdgeEnabled, int TrigX_QualifyDigitalEnabled, int TrigX_QualifyAnalogEnabled, int TrigX_QualifyTimeEnabled, 
	int TrigX_InvertDigitalQualifierEnabled, int TrigX_InvertAnalogQualifierEnabled, int TrigX_InvertTimeQualifierEnabled, int TrigX_DigitalEdgeChannel, 
	int TrigX_DigitalEdgeRising,  int TrigX_AnalogEdgeChannel, int TrigX_AnalogEdgeRising, int TrigX_AnalogQualifierChannel, int TrigX_AnalogQualifierFrom, 
	int TrigX_AnalogQualifierTo, int TrigX_AnalogTriggerLevel, long TrigX_DigitalQualifierChannelMask, long TrigX_DigitalQualifierFrom, long TrigX_DigitalQualifierTo,

	int TrigY_DigitalEdgeEnabled, int TrigY_AnalogEdgeEnabled, int TrigY_QualifyDigitalEnabled, int TrigY_QualifyAnalogEnabled, int TrigY_QualifyTimeEnabled, 
	int TrigY_InvertDigitalQualifierEnabled, int TrigY_InvertAnalogQualifierEnabled, int TrigY_InvertTimeQualifierEnabled, int TrigY_DigitalEdgeChannel, 
	int TrigY_DigitalEdgeRising,  int TrigY_AnalogEdgeChannel, int TrigY_AnalogEdgeRising, int TrigY_AnalogQualifierChannel, int TrigY_AnalogQualifierFrom, 
	int TrigY_AnalogQualifierTo, int TrigY_AnalogTriggerLevel, long TrigY_DigitalQualifierChannelMask, long TrigY_DigitalQualifierFrom, long TrigY_DigitalQualifierTo
	
	);

// Protocol Decoders
CWAV_IMPORT int CWAV_API DecodeSerial (unsigned long *reserved1, unsigned char *OutFilename, unsigned char *InlineFilename, 
								   __int64 StartSample, __int64 EndSample, unsigned long Rate, 
								   unsigned long Channel,unsigned long AlignValue, unsigned long AlignEdge,
								   unsigned long AlignChannel,unsigned long UseAlignChannel,
								   unsigned long ClockChannel,unsigned long ClockEdge,
								   unsigned long BitsPerValue, unsigned long MSBFirst,
								   unsigned long delimiter,unsigned long hex, long BytesPerLine,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API Decode1Wire (unsigned long *reserved1, unsigned char *OutFilename, unsigned char *InlineFilename, 
								   _int64 StartSample, __int64 EndSample, long Rate, unsigned long Signal,
								   long delimiter, long showall, 
								   long hex,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeI2S (unsigned long *reserved1, unsigned char *OutFilename, unsigned char *InlineFilename,
								   __int64 StartSample, __int64 EndSample, unsigned long Rate, 
								   unsigned long Channel, long BitOffset, unsigned long AlignValue, unsigned long AlignEdge,
								   unsigned long AlignChannel,unsigned long UseAlignChannel,
								   unsigned long ClockChannel,unsigned long ClockEdge,
								   unsigned long BitsPerValue, unsigned long MSBFirst,
								   unsigned long delimiter,unsigned long hex, long BytesPerLine,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeASYNC (unsigned long *reserved1, unsigned char *OutFilename,unsigned char *OutTxFilename,unsigned char *OutRxFilename, 
								   __int64 StartSample, __int64 EndSample, long Rate, unsigned long TxChannel, unsigned long RxChannel,
								   unsigned long BaudRate, unsigned long Parity, unsigned long DataBits, unsigned long Invert,
								   unsigned long delimiter,unsigned long hex,unsigned long ascii, long BytesPerLine,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodePS2 (unsigned long *reserved1, unsigned char *OutFilename, unsigned char *HostFilename, unsigned char *DeviceFilename, 
								   __int64 StartSample, __int64 EndSample, long Rate,
								   unsigned long DataChannel, unsigned long ClockChannel,
								   unsigned long MSBFirst, long hex,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeUSB (unsigned long *reserved1, unsigned char *OutFilename,unsigned char *InlineFilename, 
								   __int64 StartSample, __int64 EndSample, 
								   long ShowEndpoint, long ShowAddress, long DPlus, long DMinus,
								   long Speed, long Rate, long SOF, long delimiter, long showall, 
								   long hex,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeSPIVariable (unsigned long *reserved1, unsigned char *OutFilename,unsigned char *InlineMOSIFilename,unsigned char *InlineMISOFilename, 
								   __int64 StartSample, __int64 EndSample, long Rate,
								   unsigned long SS,unsigned long SCK,unsigned long tMOSI,unsigned long tMISO,
								   unsigned long MISOEdge,unsigned long MOSIEdge,
								   unsigned long delimiter,unsigned long hex,unsigned long UseSS, unsigned long SSLevel, long BytesPerLine, long BitsPerByte,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeI2C (unsigned long *reserved1, unsigned char *OutFilename, unsigned char *InlineSDAFilename,
								   __int64 StartSample, __int64 EndSample, long Rate, unsigned long SDA,
								   unsigned long SCL, 
								   long showack, 
								   long delimiter, long showall, 
								   long hex,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeCAN (unsigned long *InputDecodeBuffer, unsigned char *OutFilename, unsigned char *InlineFilename, 
								   __int64 StartSample, __int64 EndSample, unsigned long Rate,
								   unsigned long Channel, unsigned long BitRate, 
								   unsigned long maxID, unsigned long minID, 
								   long delimiter, long showall, 
								   long Phex,
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeParallel (unsigned long *reserved1, unsigned char *OutFilename, unsigned char *InlineFilename, 
								   __int64 StartSample, __int64 EndSample,
								   long Rate, unsigned long Channels,unsigned long Clock, 
								   unsigned long UseCLK, long CLKEdge,
								   unsigned long delimiter,unsigned long hex, long BytesPerLine, 
								   char *ProtocolDefinitionFilename, char *ProtocolOutputFilename, char *ErrorString);

CWAV_IMPORT int CWAV_API DecodeSetName (char *name);


Function Real name

?AppendBetweenSampleData@@YGHPADKKK@Z
?AppendSampleData@@YGHPADK@Z
?BulkIn@@YGHEIPAE@Z
?BulkOut@@YGHEIPAE@Z
?CalibrateScope@@YGHKKKK@Z
?CaptureStatus@@YGHPAD00PAJ110@Z
?CaptureStatusRX@@YGKPAE00@Z
?CaptureStreamingRXStatus@@YGHXZ
?ChangeBufferLength@@YGHK@Z
?ClearCountsRX@@YGKXZ
?ClearScopeData@@YGJXZ
?CloseBootloader@@YGHXZ
?ClosePacketPresenter@@YGHXZ
?ClosePod@@YGHXZ
?CombineAndSort@@YGHPAE@Z
?CombineAndSortPP@@YGHPAE@Z
?ControlIn@@YGHPAVCCyUSBDevice@@EIIIPAE@Z
?ControlOut@@YGHEIIIPAE@Z
?Copy@@YGHPADJJ@Z
?CountEdges@@YGJPAEI@Z
?CountEdgesInBuffer@@YGJPAJ000000000000000@Z
?CreateSpectrum@@YGHJJJQAM@Z
?CreateVectors@@YGXPAEPAKK@Z
?DLLTest@@YGKK@Z
?Decode1Wire@@YGHPAKPAE1_J2JKJJJPAD33@Z
?DecodeASYNC@@YGHPAKPAE11_J2JKKKKKKKKKKJPAD33@Z
?DecodeCAN@@YGHPAKPAE1_J2KKKKKJJJPAD33@Z
?DecodeI2C@@YGHPAKPAE1_J2JKKJJJJPAD33@Z
?DecodeI2S@@YGHPAKPAE1_J2KKJKKKKKKKKKKJPAD33@Z
?DecodePS2@@YGHPAKPAE11_J2JKKKJPAD33@Z
?DecodeParallel@@YGHPAKPAE1_J2JKKKJKKJPAD33@Z
?DecodeSDIO@@YGHPAKPAE11_J2JKKKKKKKKKJPAD333@Z
?DecodeSPIVariable@@YGHPAKPAE11_J2JKKKKKKKKKKJJPAD33@Z
?DecodeSPIVariableExternal@@YGHPAKPAE11_J2JKKKKKKKKKKJJPAD33@Z
?DecodeSerial@@YGHPAKPAE1_J2KKKKKKKKKKKKJPAD33@Z
?DecodeSetName@@YGHPAD@Z
?DecodeUSB@@YGHPAKPAE1_J2JJJJJJJJJJPAD33@Z
?DeleteBuffer@@YGHPAK@Z
?DemoData16@@YGJXZ
?DemoData16Old@@YGJXZ
?DemoData@@YGJXZ
?DisableCountsRX@@YGKXZ
?DownloadFile@@YGHPAVCCyUSBDevice@@PAD@Z
?DownloadImage@@YGHPAVCCyUSBDevice@@PAE@Z
?DownloadQXImage@@YGHPAVCCyUSBDevice@@PAE@Z
?EnableCountsRX@@YGKXZ
?EndCaptureRX@@YGKPA_J0@Z
?EnumerateALLPods@@YGHXZ
?EnumerateAXPods@@YGHPAI@Z
?EnumerateBusBeePods@@YGHPAI@Z
?EnumerateDXPods@@YGHPAI@Z
?EnumerateQXPods@@YGHPAI@Z
?EnumerateSXPods@@YGHPAI@Z
?EnumerateZXPods@@YGHPAI@Z
?ExtractBufferFromFile@@YGHPADK@Z
?FindNextActualSample@@YG_J_J@Z
?FindNextEdge@@YG_J_JKK@Z
?FindTrigger@@YG_JXZ
?FlushRXData@@YGHXZ
?GenerateAnalogWaveformRX@@YGKKEPAE@Z
?GenerateDigitalWaveformRX@@YGKEEEEEEEK@Z
?GeneratePWMWaveformRX@@YGKEKE@Z
?GenerateStatus@@YGHPAD000@Z
?GetActualCaptureLength@@YGJXZ
?GetFileBufferSize@@YGJPAKPBD@Z
?GetFrequencyAndCountsRX@@YGKPAK0000000@Z
?GetGain@@YGHXZ
?GetMaxBufferSize@@YGKXZ
?GetMaxBufferSizeOld@@YGKXZ
?GetMaxBufferSizeSG@@YGKXZ
?GetNextStreamBuffer@@YGEPAE@Z
?GetPixelLine@@YGHPAEKK@Z
?GetPixelMap@@YGHKK@Z
?GetPulseCount@@YGJPAJ000000000000000@Z
?GetRXData@@YGHXZ
?GetSampleRate@@YGKI@Z
?GetSignals@@YGHKIPAK@Z
?GetSignalsRX@@YGKPAE0000@Z
?GetTotalUncompressedSamples@@YG_JXZ
?InitBootloader@@YGHXZ
?InitCompression@@YG_JJK@Z
?InitCompressionOverClock@@YG_JJKK@Z
?InitQXCapture@@YGHXZ
?InitQXPassthru@@YGHK@Z
?InitializeAXPod@@YGHI@Z
?InitializeBusBeePod@@YGHI@Z
?InitializeDXExtractor@@YGHII@Z
?InitializeDXPod@@YGHI@Z
?InitializePacketPresenter@@YGHPAD00@Z
?InitializeQXPod@@YGHI@Z
?InitializeRX@@YGKXZ
?InitializeRXExtractor@@YGHIIK@Z
?InitializeSXPod@@YGHI@Z
?InitializeZXPod@@YGHI@Z
?LoadDigitalWaveformRX@@YGKKPAE@Z
?LoadPackets@@YGHDPAD@Z
?LoggedData@@YGJ_J@Z
?LoggedDataCH1@@YGJ_J@Z
?LoggedDataCH2@@YGJ_J@Z
?LoggedDataSG@@YGJK@Z
?LookupLabel@@YGHDPADJJ@Z
?LookupValue@@YGHDPADJJ@Z
?MakeBuffer@@YGPAKK@Z
?MakeBufferSG@@YGPAKK@Z
?OpenAXPod@@YGHI@Z
?OpenAnyAXPod@@YGHXZ
?OpenBusBeePod@@YGHI@Z
?OpenDXPod@@YGHI@Z
?OpenFileData@@YGJPAD0000000PAEPBD@Z
?OpenFileDataAndConfig16@@YGJPAD0000000PAEPAK1111111111111111111111111111111111122222222222221PBD@Z
?OpenFileDataAndConfig@@YGJPAD0000000PAEPAK1111111111111111111111111111111111122222222PBD@Z
?OpenQXPod@@YGHI@Z
?OpenSXPod@@YGHI@Z
?OpenZXPod@@YGHI@Z
?OutputBinarySampleData@@YGHPAD_J1@Z
?OutputSampleData@@YGHPAD_J1KKK1@Z
?Paste@@YGJPADJ@Z
?ReadEEPROM@@YGHIIPAE@Z
?ReadQXReg@@YGHE@Z
?ReadRXReg@@YGHE@Z
?Reset8051@@YGHPAVCCyUSBDevice@@D@Z
?ResetHFReject@@YGKXZ
?SampleData@@YGK_J@Z
?SaveFileData@@YGHPAD0000000PAEPBD@Z
?SaveFileDataAndConfig16@@YGHPAD0000000PAEPAK1111111111111111111111111111111111122222222222221PBD@Z
?SaveFileDataAndConfig@@YGHPAD0000000PAEPAK1111111111111111111111111111111111122222222PBD@Z
?SaveUndo@@YGHPADJJ@Z
?ScaleDataToScreen@@YGXPAKPAE111111111111111JKKK@Z
?ScaleDataToScreenNew@@YGXPAKPAE111111111111111JKK@Z
?ScaleDataToScreenNewSG@@YGXPAKPAE111111111111111JKK@Z
?ScaleDataToScreenRX@@YGKPAKPAE1111111111111110000_JKNK@Z
?ScaleDataToScreenSG@@YGXPAKPAE111111111111111JKKK@Z
?ScaleScopeDataToScreenNew@@YGXPAKK00JKK@Z
?ScaleScopeDataToScreenVeryNew@@YGXPAKKK00JKKPAJJ@Z
?ScopeData@@YGJJK@Z
?SearchForTrigger@@YGJPAKKKK@Z
?SendDataStream@@YGHH_JEDDDJ@Z
?SendDataToPacketPresenter@@YGHPAD_JJJJJ@Z
?SendEventToPacketPresenter@@YGHPAD_JJJJ@Z
?SetBlockData@@YGJJJEE@Z
?SetBlockDataSG@@YGJJJEE@Z
?SetData@@YGJKK@Z
?SetDataSG@@YGJKK@Z
?SetHFReject@@YGKXZ
?SetLogicThresholdRX@@YGKM@Z
?SetMode@@YGHH@Z
?SetSignals@@YGHKIPAK@Z
?SetSignalsRX@@YGKKK@Z
?SetTriggersRX@@YGKHHHHHHHHHHHHHHHHHHHHHHJJJHHHHHHHHHHHHHHHHJJJ@Z
?SingleCaptureStatus@@YGHXZ
?StartCapture16Bit@@YGHIIIIIPAKH0KK@Z
?StartCaptureRX@@YGKKEMKEE@Z
?StartGenerate@@YGHKIEPAKK@Z
?StartGenerateSG@@YGHKIEPAKK@Z
?StartLoopGenerate@@YGHKIEPAKKE@Z
?StartLoopGenerateSG@@YGHKIEPAKKE@Z
?StartPulseCount@@YGHEIKK@Z
?StartStreamingCapture@@YGHIIPAEH0KK@Z
?StartTimestamp@@YGHD@Z
?StartVariableLoopGenerate@@YGHIEPAKKE@Z
?StillThere@@YGHXZ
?StopCapture16@@YGHXZ
?StopCapture@@YGHXZ
?StopCaptureMSO@@YGHXZ
?StopCaptureRX@@YGKXZ
?StopGenerate@@YGHXZ
?StopPulseCount@@YGHXZ
?StopStream@@YGHXZ
?StreamBufferCount@@YGKXZ
?StreamBufferOverflow@@YGDXZ
?StreamBuffersLeft@@YGKXZ
?TerminateProgram@@YGHXZ
?TestDXPod@@YGHPAI@Z
?TriggerNowRX@@YGKXZ
?USBDecode@@YGHPAEJJJ0JJJJJJJJ@Z
?UnLoadPackets@@YGHD@Z
?Undo@@YGJPAD@Z
?VendorControlIn@@YGHPAVCCyUSBDevice@@IIIPAE@Z
?VendorControlOut@@YGHPAVCCyUSBDevice@@IIIPAE@Z
?WriteEEPROM@@YGHIIPAE@Z
?WriteI2C@@YGHEEE@Z
?WriteQXReg@@YGHEE@Z
?WriteRXReg@@YGHEE@Z



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



class USBEE(object):

    def __init__( self ):

        # os.chdir( dll_lib )
        
        self.dll_lib = dll_lib

        self.hwd = ctypes.windll.usbeerxste
        
        # Set Function return value for python 
        self.get_error_string = self.hwd.LP_GetErrorString
        self.get_error_string.restype = ctypes.c_char_p
        self.get_error_string.argtypes = [ ctypes.c_int ]

    def InitilizeRX(self):
        """
                CWAV_IMPORT unsigned long CWAV_API InitializeRX( void );
        """
        func = getattr( self.hwd, '?InitializeRX@@YGKXZ')
        func.restype = ctypes.c_ulong

        rc = func()
        return rc 

        
    def GetSignalsRX(self, digital0to7, digital8toF, analog1, analog2, CandT ):
        """
        CWAV_IMPORT unsigned long CWAV_API GetSignalsRX( unsigned char *digital0to7, unsigned char *digital8toF,
                                                         unsigned char *analog1, unsigned char *analog2, unsigned char *CandT  ); 
        ?  After this call, the variable pointed to by digital0to7 will hold the digital logic value read on 
           the input signals 0 through 7.   
        ?  After this call, the variable pointed to by digital8toF will hold the digital logic value read on 
           the input signals 8 through F.   
        ?  After this call, the variable pointed to by analog1 will hold the 8 MSbits of the CH1 ADC.  
           To convert the digital value to voltage, V =  ((128 - analog1) * 0.046875  
        ?  After this call, the variable pointed to by analog2 will hold the 8 MSbits of the CH2 ADC.  
           To convert the digital value to voltage, V =  ((128 ? analog2) * 0.046875 
        ?  After this call, the variable pointed to by CandT will hold the digital logic value read on the 
           input signals C and T.   
        Return Value:   
        ?  1 = Successful 
        ?  0 = Failure 

        ?GetSignalsRX@@YGKPAE0000@Z
        """
        func = getattr( hwd, '?GetSignalsRX@@YGKPAE0000@Z')
        func.restype = ctypes.c_ulong
        func.argtypes = [ ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p ]
        rc =  func(digital0to7, digital8toF, analog1, analog2, CandT)

        return rc

    def SetSignalsRX(self , mask, value):
        """
        CWAV_IMPORT unsigned long CWAV_API SetSignalsRX( unsigned long mask, unsigned long value  ); 
        ?  mask is the mask for setting each of the 8 USBee digital Output signals (0 through 7).  A 
           signal is not changed if the corresponding bit is a 0.  A signal is changed if the 
           corresponding bit is a 1. Channel D0 is bit 0 (lsb) and D7 is bit 7. 
        ?  value is the digital level driven on the output signals.  A signal is driven high (3.3V) if the 
           corresponding bit is a 1.  A signal is driven low (0V) if the corresponding bit is a 0. Channel 
           D0 is bit 0 (lsb) and D7 is bit 7. 
        Return Value:   
        ?  1 = Successful 
        ?  0 = Failure 


        """
        func = getattr( hwd, '?SetSignalsRX@@YGKKK@Z')
        func.restype = ctypes.c_ulong
        func.argtypes = [ ctypes.c_ulong , ctypes.c_ulong]
        rc =  func(mask, value)
        return rc

    def GenerateAnalogWaveformRX(self, SamplesPerSecond, SamplesPerCycle ):
        """
        CWAV_IMPORT unsigned long CWAV_API GenerateAnalogWaveformRX( unsigned long SamplesPerSecond, 
                                                                     unsigned char SamplesPerCycle, unsigned char *samples ); 
        ?  SamplesPerSecond is the sample rate of the output samples and ranges from 1 to 300,000.   
        ?  SamplesPerCycle is the number of samples that make up a complete cycle in the analog waveform and ranges from 1 to 128 samples. 
        ?  samples points to a buffer of samples.  Each sample is a digital value representing the 
           analog output voltage using the formula Vout = samples  / 61.429.  Vout range is from 0 to 3.0V. 
        Return Value:   
        ?  1 = Successful 
        ?  0 = Failure 


        """
        func = getattr( hwd, '?GenerateAnalogWaveformRX@@YGKKEPAE@Z')
        func.restype = ctypes.c_ulong
        func.argtypes = [ ctypes.c_ulong , ctypes.c_char,  ctypes.c_char_p]
        rc =  func(SamplesPerSecond, SamplesPerCycle)
        return rc






    def __del__(self):
        pass

   




if __name__ == "__main__":
    import time
    
    iq2010 = IQ2010()
    
    iq2010.connect("10.10.0.7")

    print iq2010.get_version()
    print "\n\n\nWorking with IQ2010 version %s\n\n\n" % iq2010.get_version()

    