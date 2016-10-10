// No doxygen 'group' header because this file is included by both user & kernel implmentations
 
//------------------------------------------------------------------------------ 
// Copyright (c) 2010 Cohda Wireless Pty Ltd 
//------------------------------------------------------------------------------

#ifndef __LINUX__IEEE1609__DOT4__MK2REMOTE_API_TYPES_H__
#define __LINUX__IEEE1609__DOT4__MK2REMOTE_API_TYPES_H__

// Based on: CWD-MK2-0007, CohdaMobility MK2 Radio API Specification

//------------------------------------------------------------------------------ 
// Included headers 
//------------------------------------------------------------------------------ 

#ifdef __KERNEL__
#include <linux/types.h>
#else
#include <stdint.h>
#include <stdbool.h>
#endif

//------------------------------------------------------------------------------ 
// Type definitions  
//------------------------------------------------------------------------------ 

/**
 * MK2 MLME interface return codes
 */
typedef enum MK2Status
{
    MK2STATUS_SUCCESS = 0,
    MK2STATUS_OPERATION_IN_PROGRESS,
    MK2STATUS_FAILURE_INVALID_HANDLE,
    MK2STATUS_FAILURE_INVALID_BANDWIDTH,
    MK2STATUS_FAILURE_INVALID_CHANNEL,
    MK2STATUS_FAILURE_INVALID_CHANNELNUMBER,
    MK2STATUS_FAILURE_INVALID_CMD,
    MK2STATUS_FAILURE_INVALID_DEFAULTMCS,
    MK2STATUS_FAILURE_INVALID_DEFAULTTPC,
    MK2STATUS_FAILURE_INVALID_DEFAULTTRC,
    MK2STATUS_FAILURE_INVALID_DEFAULTTXPOWER,
    MK2STATUS_FAILURE_INVALID_EDCAPARAMETERSET,
    MK2STATUS_FAILURE_INVALID_OPERATIONRATESET,
    MK2STATUS_FAILURE_INVALID_PRIORITY,
    MK2STATUS_FAILURE_INVALID_TABLE,
    MK2STATUS_FAILURE_CCH_NOT_SET,
    MK2STATUS_FAILURE_NOCONFIG_SCH,
    MK2STATUS_FAILURE_SCH_NOT_SET,
    MK2STATUS_FAILURE_SCH_NOT_STARTED,
    MK2STATUS_FAILURE_DESCRIPTOR_NOBUFFER,
    MK2STATUS_FAILURE_NO_RADIO_PRESENT,
    MK2STATUS_FAILURE_NO_REPEATS,
    MK2STATUS_FAILURE_NOT_OPEN,
    MK2STATUS_FAILURE_NOT_SET,
    MK2STATUS_FAILURE_NOT_STARTED,
    MK2STATUS_FAILURE_NULL_PARAMETER,
    MK2STATUS_FAILURE_TX_INVALID_MCS,
    MK2STATUS_FAILURE_TX_INVALID_PERIOD,
    MK2STATUS_FAILURE_TX_INVALID_POWER
} eMK2Status;
/// @copydoc eMK2Status
typedef int tMK2Status;

/**
 * This type is a pointer to an opaque structure which is used by the MLME_IF access library
 * functions to store data required to maintain communication with the WAVE MAC driver
 * IOCTL interface. This type is returned by a call to MK2_mlme_if_open(), and is required by
 * all calls to the MLME_IF access layer functions.
 */
typedef void *tMK2MLMEIFHandle;

/// The 802.11 channel number, per 802.11-2007
typedef uint8_t tMK2ChannelNumber;

/**
 * Channel type
 * Indicates CCH or SCH
 */
typedef enum Mk2Channel
{
    /// CCH
    MK2CHAN_CCH = 0x01,
    /// SCH
    MK2CHAN_SCH = 0x80,
    
    /// CCH on radio A
    MK2CHAN_CCH_A = 0x01,
    /// SCH on radio A
    MK2CHAN_SCH_A = 0x08,

    /// CCH on radio B
    MK2CHAN_CCH_B = 0x10,
    /// SCH on radio B
    MK2CHAN_SCH_B = 0x80,
    
    /// CCH (interval 1) on radio A
    MK2CHAN_CCH_A1 = 0x01,
    /// CCH (interval 2) on radio A
    MK2CHAN_CCH_A2 = 0x02,
    /// SCH (interval 1) on radio A
    MK2CHAN_SCH_A1 = 0x08,
    /// SCH (interval 2) on radio A
    MK2CHAN_SCH_A2 = 0x04
    
} eMK2Channel;
/// @copydoc eMK2Channel
typedef uint8_t tMK2Channel;

/**
 * MK2 Bandwidth
 * Indicates 10 MHz or 20 MHz
 */
typedef enum MK2Bandwidth
{
    /// Indicates 10 MHz
    MK2BW_10MHz,
    /// Indicates 20 MHz
    MK2BW_20MHz
} eMK2Bandwidth;
/// @copydoc eMK2Bandwidth
typedef uint8_t tMK2Bandwidth;

/**
 * MK2 dual radio transmit control
 * Controls transmit behaviour according to activity on the
 * other radio (inactive in single radio configurations)
 */
typedef enum MK2DualTxControl
{
    /// Do not constrain transmissions
    MK2TXC_NONE,
    /// Prevent transmissions when other radio is transmitting
    MK2TXC_TX,
    /// Prevent transmissions when other radio is receiving
    MK2TXC_RX,
    /// Prevent transmissions when other radio is transmitting or receiving
    MK2TXC_TXRX, 
    /// Default behaviour
    MK2TXC_DEFAULT = MK2TXC_TX
    
} eMK2DualTxControl;
/// @copydoc eMK2DualTxControl
typedef uint8_t tMK2DualTxControl;

/**
 * MK2 Modulation and Coding scheme
 */
typedef enum MK2MCS
{
    /// Rate 1/2 BPSK
    MK2MCS_R12BPSK  = 0xB,
    /// Rate 3/4 BPSK
    MK2MCS_R34BPSK  = 0xF,
    /// Rate 1/2 QPSK
    MK2MCS_R12QPSK  = 0xA,
    /// Rate 3/4 QPSK
    MK2MCS_R34QPSK  = 0xE,
    /// Rate 1/2 16QAM
    MK2MCS_R12QAM16 = 0x9,
    /// Rate 3/4 16QAM
    MK2MCS_R34QAM16 = 0xD,
    /// Rate 2/3 64QAM
    MK2MCS_R23QAM64 = 0x8,
    /// Rate 3/4 64QAM
    MK2MCS_R34QAM64 = 0xC,
    /// Use default data rate
    MK2MCS_DEFAULT  = 0x0,
    /// Use transmit rate control
    MK2MCS_TRC      = 0x1
} eMK2MCS;
/// @copydoc eMK2MCS
typedef uint8_t tMK2MCS;

/**
 * MK2 Power
 * Indicates the power in 0.5 dBm steps (signed to indicate Rx power too)
 */
typedef int16_t tMK2Power;

/// Indicate manual, default or TPC
typedef enum MK2TxPwrCtl
{
    /// Manually specified
    MK2TPC_MANUAL,
    /// Default values
    MK2TPC_DEFAULT,
    /// Utilize dynamic TPC
    MK2TPC_TPC
} eMK2TxPwrCtl;
/// @copydoc eMK2TxPwrCtl
typedef uint8_t tMK2TxPwrCtl;

/**
 * MK2 Transmit Power
 * Indicates if manual, default or TPC is to be used, and manual power
 * setting if needed. If the power specified is lower than the minimum power supported by the
 * hardware, the minimum will be used. If the power specified is higher than the maximum power
 * supported by the hardware, the maximum will be used.
 */
typedef struct MK2TxPower
{
    /// Indicate manual, default or TPC
    tMK2TxPwrCtl PowerSetting;
    /// The manual power setting (if used)
    tMK2Power ManualPower;
} __attribute__ ((packed)) tMK2TxPower;

/**
 * MK2 Transmit Antenna
 * Indicates if manual, or automatic antenna control is to
 * be used, and a manual antenna setting if needed.
 */
typedef enum MK2TxAntenna
{
    /// Transmit packet using automatic/default transmit antenna selection.
    MK2_TXANT_DEFAULT = 0,
    /// Transmit packet on antenna 1
    MK2_TXANT_ANTENNA1 = 1,
    /// Transmit packet on antenna 2 (when available).
    MK2_TXANT_ANTENNA2 = 2,
    /// Transmit packet on both antenna
    MK2_TXANT_ANTENNA1AND2 = 3
} eMK2TxAntenna;
/// @copydoc eMK2TxAntenna
typedef uint8_t tMK2TxAntenna;

/**
 * MK2 Receive Antenna
 * Indicates if manual, or automatic antenna control is to
 * be used, and manual antenna setting if needed.
 */
typedef enum MK2RxAntenna
{
    /// Receive using default antenna selection (default is MRC)
    MK2_RXANT_DEFAULT = 0,
    /// Receive only on antenna 1
    MK2_RXANT_ANTENNA1 = 1,
    /// Receive only on antenna 2 (when available).
    MK2_RXANT_ANTENNA2 = 2,
    /// Receive on both antennas (MRC)
    MK2_RXANT_ANTENNA1AND2 = 3
} eMK2RxAntenna;
/// @copydoc eMK2RxAntenna
typedef uint8_t tMK2RxAntenna;

/**
 * MK2 TSF
 * Indicates absolute 802.11 MAC time in micro seconds
 */
typedef uint64_t tMK2TSF;

/**
 * MK2 Expiry time
 * Indicates absolute 802.11 MAC time in micro seconds
 */
typedef uint64_t tMK2Time;

/**
 * MK2 MAC Address
 */
typedef uint8_t tMK2MACAddr[6];

/**
 * MK2 Rate sets
 * Each bit indicates if corresponding MCS rate is supported
 */
typedef enum MK2Rate
{
    /// Rate 1/2 BPSK rate mask
    MK2_RATE12BPSK_MASK = 0x01,
    /// Rate 3/4 BPSK rate mask
    MK2_RATE34BPSK_MASK = 0x02,
    /// Rate 1/2 QPSK rate mask
    MK2_RATE12QPSK_MASK = 0x04,
    /// Rate 3/4 QPSK rate mask
    MK2_RATE34QPSK_MASK = 0x08,
    /// Rate 1/2 16QAM rate mask
    MK2_RATE12QAM16_MASK = 0x10,
    /// Rate 2/3 64QAM rate mask
    MK2_RATE23QAM64_MASK = 0x20,
    /// Rate 3/4 16QAM rate mask
    MK2_RATE34QAM16_MASK = 0x40
} eMK2Rate;
/// @copydoc eMK2Rate
typedef uint8_t tMK2Rate;

/**
 * MK2 Priority
 */
typedef enum MK2Priority
{
    /// Priority level 0
    MK2_PRIO_0 = 0,
    /// Priority level 1
    MK2_PRIO_1 = 1,
    /// Priority level 2
    MK2_PRIO_2 = 2,
    /// Priority level 3
    MK2_PRIO_3 = 3,
    /// Priority level 4
    MK2_PRIO_4 = 4,
    /// Priority level 5
    MK2_PRIO_5 = 5,
    /// Priority level 6
    MK2_PRIO_6 = 6,
    /// Priority level 7
    MK2_PRIO_7 = 7
} eMK2Priority;
/// @copydoc eMK2Priority
typedef uint8_t tMK2Priority;

/**
 * MK2 802.11 service class specification.
 */
typedef enum MK2Service
{
    /// Packet should be (was) transmitted using normal ACK policy
    MK2_QOS_ACK = 0,
    /// Packet should be (was) transmitted without Acknowledgement.
    MK2_QOS_NOACK = 1
} eMK2Service;
/// @copydoc eMK2Service
typedef uint8_t tMK2Service;

/**
 * MK2 General Command type.
 */
typedef enum MK2BasicCommand
{
    /// Get command
    MK2_CMD_GET = 0,
    /// Set command
    MK2_CMD_SET = 1,
    /// Add command
    MK2_CMD_ADD = 2,
    /// Delete command
    MK2_CMD_DELETE = 3
} eMK2BasicCommand;
/// @copydoc eMK2BasicCommand
typedef uint8_t tMK2BasicCommand;

/**
 * MK2 Interface Filter Specification.
 * This structure is used to specify how packets are filtered on
 * the two WAVE MAC packet data interfaces. The filter table is a list of Ethertype values which
 * will be allowed to pass via the corresponding interface (transmit and receive).
 *
 * pFiltTable should point to an array of memory of size TableLen 16 bit integers.
 *
 * After the MK2_mlme_if_filter() command returns successfully, TableLen will be set to
 * the number of valid entries in pFiltTable, and the content of pFiltTable will be updated.
 */
typedef struct MK2InterfaceFilterSpec
{
    /// Command to execute, either Get or Set
    tMK2BasicCommand Cmd;
    /// Number of items in the filter table, or size of array for Get.
    int32_t TableLen;
    /// Filter table, array of TableLen EtherType values.
    uint16_t *pFiltTable;
} __attribute__ ((packed)) tMK2InterfaceFilterSpec;


/**
 * MK2 Per-Interface Statistics
 */
typedef struct MK2InterfaceStats
{
    /// Total number of packets transmitted via the interface
    uint32_t TxCount;
    /// Total number of unicast packets transmitted via the interface
    uint32_t TxUnicastCount;
    /// Total number of broadcast packets transmitted via the interface
    uint32_t TxBroadcastCount;
    /// Total number of multicast packets transmitted via the interface
    uint32_t TxMulticastCount;
    /// Total number of failed unicast packets transmitted via the interface
    uint32_t TxFailCount;
    /// Total number of valid packets received via the interface
    uint32_t RxCount;
    /// Total number of unicast packets received via the interface
    uint32_t RxUnicastCount;
    /// Total number of broadcast packets received via the interface
    uint32_t RxBroadcastCount;
    /// Total number of multicast packets received via the interface
    uint32_t RxMulticastCount;
} __attribute__ ((packed)) tMK2InterfaceStats;

/**
 * MK2 Per-Channel Statistics
 */
typedef struct MK2ChannelStats
{
    /// Total number of packets transmitted on the channel
    uint32_t TxCount;
    /// Total number of unicast packets transmitted on the channel
    uint32_t TxUnicastCount;
    /// Total number of broadcast packets transmitted on the channel
    uint32_t TxBroadcastCount;
    /// Total number of multicast packets transmitted on the channel
    uint32_t TxMulticastCount;
    /// Total number of failed unicast packets transmitted on the channel
    uint32_t TxFailCount;
    /// Total number of valid packets received on the channel
    uint32_t RxCount;
    /// Total number of unicast packets received on the channel
    uint32_t RxUnicastCount;
    /// Total number of broadcast packets received on the channel
    uint32_t RxBroadcastCount;
    /// Total number of multicast packets received on the channel
    uint32_t RxMulticastCount;
    /// Total number of failed packets received on the channel (CRC failures)
    uint32_t RxFail;
    /// Total number of duplicate (unicast) packets received on the channel
    uint32_t RxDup;
    /// Current load on the channel (ratio of channel busy to channel idletime), measured over the last measurement period. 255 = 100%
    uint8_t ChannelUtilisation;
    /// Current channel utilisation measurement period in TU units (1 TU = 1.024 ms)
    uint16_t ChannelUtilisationPeriod;
    /// Proportion of time upon which the radio is tuned to this channel, measured over the last measurement period. 255 = 100%
    uint8_t ChannelActiveRatio;
    /// Current TSF timer value, least significant 32 bits (1 unit = 1 us)
    uint32_t CurrentTSF;
} __attribute__ ((packed)) tMK2ChannelStats;

typedef bool tMK2Bool;

/**
 * MK2 Transmit Descriptor. This header is used to control how the data packet is transmitted by
 * the WAVE MAC. This is the header used on packets transmitted on the WAVE-RAW and
 * WAVE-MGMT interfaces. Note that all fields within this structure are to be packed with no
 * additional pad or alignment bytes.
 */
typedef struct MK2TxDescriptor
{
    /// Indicate the channel number that should be used (e.g. 172)
    tMK2ChannelNumber ChannelNumber;
    /// Indicate the priority to used
    tMK2Priority Priority;
    /// Indicate the 802.11 Service Class to use
    tMK2Service Service;
    /// Indicate the MCS to be used (may specify default or TRC)
    tMK2MCS MCS;
    /// Indicate the power to be used (may specify default or TPC)
    tMK2TxPower TxPower;
    /// Indicate the antenna upon which packet should be transmitted
    tMK2TxAntenna TxAntenna;
    /// Indicate the expiry time (0 means never)
    tMK2Time Expiry;
} __attribute__ ((packed)) tMK2TxDescriptor;


/**
 * MK2 Meta Data type - contains per frame receive meta-data
 *
 * The Trice is a 1/256th of microsecond resolution time stamp of the 
 * received frame.  It should be considered as an offset to the 64 bit 
 * tMK2TSF value.
 *
 * The fine frequency estimate is the carrier frequency offset.  
 * It is a signed 24 bit integer in units of normalized radians per sample 
 * (10 MHz or 20 MHz), with a Q notation of SQ23.
 */
typedef struct MK2RxMeta
{
    /// Rx Time Stamp (1/256th of a microsecond)
    uint8_t Trice;
    /// Reserved
    uint8_t Reserved1;
    /// Reserved
    uint16_t Reserved2;
    /// Reserved
    uint32_t Reserved3:8;
    /// Fine Frequency estimate (normalized radians per sample in SQ23)
    uint32_t FineFreq:24;
} __attribute__ ((packed)) tMK2RxMeta;

/**
 * MK2 Receive Descriptor.
 * This header is used to pass receive packet meta-information from
 * the WAVE-MAC to upper-layers. This header is pre-pended to all packets received on the
 * WAVE-RAW and WAVE-MGMT interfaces. If only a single receive power measure is
 * required, then simply take the maximum power of Antenna A and B. Note that all fields within
 * this structure are packed with no additional pad or alignment bytes.
 */
typedef struct MK2RxDescriptor
{
    /// Indicate the channel number that frame was received on
    tMK2ChannelNumber ChannelNumber;
    /// Indicate the priority allocated to the received packet (by Tx)
    tMK2Priority Priority;
    /// Indicate the 802.11 service class used to transmit the packet
    tMK2Service Service;
    /// Indicate the data rate that was used
    tMK2MCS MCS;
    /// Indicate the received power on Antenna A
    tMK2Power RxPowerA;
    /// Indicate the received power on Antenna B
    tMK2Power RxPowerB;
    /// Indicate the receiver noise on Antenna A
    tMK2Power RxNoiseA;
    /// Indicate the receiver noise on Antenna B
    tMK2Power RxNoiseB;
    /// Reserved (for 64 bit alignment)
    uint32_t Reserved0;
    /// MAC Rx Timestamp, local MAC TSF time at which packet was received
    tMK2TSF RxTSF;
    /// Per Frame Receive Meta Data
    tMK2RxMeta RxMeta;
} __attribute__ ((packed)) tMK2RxDescriptor;

typedef union  MK2TrxDescriptor
{
	tMK2TxDescriptor tx;
	tMK2RxDescriptor rx;
} __attribute__ ((packed)) tMK2TrxDescriptor;

/** 
 * MK2 Rate Set. See @ref eMK2Rate for bitmask for enabled rates
 */
typedef uint8_t tMK2RateSet[8];

/**
 * WSA Transmit Descriptor.
 * This is used to pass the WSA for transmission to the WAVE MAC with the MK2_mlme_wsareq function.
 */
typedef struct MK2WSATxDescriptor
{
    /// Transmit descriptor to nominate transmit parameters for WSA
    tMK2TxDescriptor TxD;
    /// Indicate the transmission period in usecs (0 means once only)
    tMK2Time Period;
    /// The destination MAC Address
    tMK2MACAddr Destination;
    /// Basic Rate Set
    tMK2RateSet BasicRateSet;
    /// Operational Rate Set
    tMK2RateSet OperationalRateSet;
    /// The WSIE payload length
    uint16_t Length;
    /// Pointer to the WSIE payload
    uint8_t * pWSIE;
} __attribute__ ((packed)) tMK2WSATxDescriptor;


/**
 * WSA Receive Descriptor.
 * This structure is currently not used, but may be used in a future release of this interface.
 */
typedef struct MK2WSARxDescriptor
{
    /// Receive descriptor corresponding with received WSA
    tMK2RxDescriptor RxD;
    /// The transmitters time stamp for when the WSA was transmitted
    tMK2Time Timestamp;
    /// The local receiver's TSF time when the WSA was received
    tMK2Time LocalTime;
    /// The source MAC Address
    tMK2MACAddr Source;
    /// The WSA length
    uint16_t WSALength;
    /// Pointer to the WSA content
    uint8_t * WSA;
} __attribute__ ((packed)) tMK2WSARxDescriptor;

/**
 * Channel Profile
 * Indicates channel number, default data rate, default transmit power, and
 * whether transmit power control or transmit rate control should be used.
 */
typedef struct MK2ChanProfile
{
    /// Indicate the channel number that should be used (e.g. 172)
    uint8_t ChannelNumber;
    /// Indicate the default data rate that should be used (max if TRC)
    tMK2MCS DefaultMCS;
    /// Indicate the default transmit power that should be used (max if TPC)
    tMK2Power DefaultTxPower;
    /// Indicate if transmit rate control should be used by default
    tMK2Bool DefaultTRC;
    /// Indicate if transmit power control should be used by default
    tMK2Bool DefaultTPC;
    /// Indicate if channel is 10 MHz or 20 MHz
    tMK2Bandwidth Bandwidth;
    /// Dual Radio transmit control (inactive in single radio configurations)
    tMK2DualTxControl DualTxControl;
    /// Channel Utilisation measurement period (in TU units. 1 TU = 1.024 ms)
    uint16_t ChannelUtilisationPeriod;
    /// Default Tx antenna configuration 
    /// (can be overridden in @ref tMK2WSATxDescriptor and @ref tMK2TxDescriptor)
    tMK2TxAntenna TxAntenna;
    /// Receive antenna configuration
    tMK2RxAntenna RxAntenna;
    /// The MAC Address to use on this channel (overridden on wave-raw inteface)
    tMK2MACAddr MACAddr;
} __attribute__ ((packed)) tMK2ChanProfile;


/**
 * MK2 Sync Descriptor.
 * This header is used to pass channel syncronization meta-information from
 * the WAVE-MAC to upper-layers. At the start of channel each interval, this
 * descriptor is emitted by the WAVE-MAC on the wave-sync interface
 * e.g.   0ms: CCH,178,49,x
 *       50ms: SCH,172:49,x+50ms
 *      100ms: CCH,178,49,x+100ms
 */
typedef struct MK2SyncDescriptor
{
    /// Indicates the channel type of the current interval
    tMK2Channel Channel;
    /// Indicates the channel number that the radio is operating on
    tMK2ChannelNumber ChannelNumber;
    /// Channel Utilisation period (in TU units. 1 TU = 1.024 ms)
    uint16_t ChannelUtilisationPeriod;
    /// MAC Timestamp, local MAC TSF time at which the interval started
    tMK2TSF TSF;
} __attribute__ ((packed)) tMK2SyncDescriptor;


#endif // __LINUX__IEEE1609__DOT4__MK2REMOTE_API_TYPES_H__

// Close the doxygen group
/**
 * @}
 */
