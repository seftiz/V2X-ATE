"""Common DSRC definitions"""

import sys
from lib import utilities


DSRC_MSG_TYPE = utilities.Enum([ 
    'DSRC_MSG_ID_RES',                    #reserved                           (0),  
    'DSRC_MSG_ID_ACM',                    #alaCarteMessage                    (1), --ACM 
    'DSRC_MSG_ID_BSM',                    #basicSafetyMessage                 (2), --BSM
    'DSRC_MSG_ID_BSM_VERBOSE',            #basicSafetyMessageVerbos           (3), -- used for testing only
    'DSRC_MSG_ID_CSR',                    #commonSafetyRequest                (4), --CSR 
    'DSRC_MSG_ID_EVA',                    #emergencyVehicleAlert              (5), --EVA
    'DSRC_MSG_ID_ICA',                    #intersectionCollisionAlert         (6), --ICA
    'DSRC_MSG_ID_MAP',                    #mapData                            (7), --MAP,GID, intersections
    'DSRC_MSG_ID_NMEA',                   #nmeaCorrections                    (8), --NMEA
    'DSRC_MSG_ID_PDM',                    #probeDataManagment                 (9), --PDM 
    'DSRC_MSG_ID_PVD',                    #probVehicleData                    (10),--PVD
    'DSRC_MSG_ID_RSA',                    #roadSideAlert                      (11),--RSA
    'DSRC_MSG_ID_RTCM',                   #rtcmCorrections                    (12),--RTCM
    'DSRC_MSG_ID_SPAT',                   #signalPhaseAndtimingMessage        (13),--SPAT
    'DSRC_MSG_ID_SRM',                    #signalRequestMessage               (14),--SRM
    'DSRC_MSG_ID_SSM',                    #signalStatusMessage                (15),--SSM
    ])

DSRC_TRANMISSION_STATE = utilities.Enum([ 
    'DSRC_TRANMISSION_STATE_NEUTRAL', # neutral (0), -- Neutral, speed relative to the vehicle alignment
    'DSRC_TRANMISSION_STATE_PARK',    #park (1), -- Park, speed relative the to vehicle alignment
    'DSRC_TRANMISSION_STATE_FORWARDGEARS', #forwardGears (2), -- Forward gears, speed relative the to vehicle alignment
    'DSRC_TRANMISSION_STATE_REVERSEGEARS', #reverseGears (3), -- Reverse gears, speed relative the to vehicle alignment
    'DSRC_TRANMISSION_STATE_RESERVED1', #RESERVED (4),
    'DSRC_TRANMISSION_STATE_RESERVED2', #RESERVED (5),
    'DSRC_TRANMISSION_STATE_RESERVED3', #RESERVED1 (6),
    'DSRC_TRANMISSION_STATE_UNAVAILABLE', #unavailable (7), -- not-equipped or unavailable value,
    ])


class DSRCbasicSafetyMessageLimitsAndNa(object): 

    #TODO
    # |4bits|1bit|1bit = 0|2bit|2bit|2bit|2bit|2bit|
    def brakeSystemStatusGetkMax(self):
        # returns the max possible value
        max = 0
        max = (8 << 12) | (1 << 11) | (3 << 8) | (3 << 6) | (2 << 4) | (2 << 2) | 2
        return max

    def brakeSystemStatusCheckNa(self, value):
        # return true if all fields are n/a otherwise return false
        # wheelBrakes field (4 first bits) has no unavailable value therfore its not tested
        # for unavailable all other fields should equall 0 except wheelBrakesUnavailable that should equal 1
        if (value & ~(int("f000", 16))) == int("800", 16):
            return True
        else:
            return False


    # (min, max, n/a value, tupple of all supported version)
    values = {  'j2735.msgCount'        : (0, 127, None, ("GM1.0.0A2")),
                'j2735.temporaryid'  : (0, 4294967295, None, ("GM1.0.0A2")),
                'j2735.uniqueid'     : (0, 65535, None, ("GM1.0.0A2")),
                'j2735.dsecond'      : (0, 65535, None, ("GM1.0.0A2")),
                'j2735.pos3D.lat'    : (-900000000, 900000000, 900000001, ("GM1.0.0A2")),
                'j2735.pos3D.long'   : (-1800000000, 1800000000, 1800000001, ("GM1.0.0A2")),
                'j2735.pos3Delevation' : (0, int("0xEFFF", 16), int("0xF000", 16), ("GM1.0.0A2")), 
                # the DSRC srtandard uses accuracy sub fields but the pdml shows it as one field 
                'j2735.accuracy'     : (0, int("0xFEFEFFFE", 16), int("0xFFFFFFFF", 16), ("GM1.0.0A2")), 
                # the DSRC srtandard uses speed sub fields but the pdml shows it as one field 
                # max = DSRC_TRANMISSION_STATE_REVERSEGEARS (0x3) << 13 | 8190 = 0x7ffe
                # unavailable = DSRC_TRANMISSION_STATE_UNAVAILABLE (0x7) << 13 | 8191 = 0xffff
                'j2735.speed'        : (0, int("0xfffe", 16), int("0xffff",16), ("GM1.0.0A2")),
                'j2735.heading'      : (0, 28799 ,28800, ("GM1.0.0A2")),
                'j2735.steeringAngle': (0, 126, 127, ("GM1.0.0A2")),
                'j2735.accelSet4Way.lon'     : (-2000, 2000, 2001, ("GM1.0.0A2")),
                'j2735.accelSet4Way.lat'     : (-2000, 2000, 2001, ("GM1.0.0A2")),
                'j2735.accelSet4Way.vert'    : (-126, 127, -127, ("GM1.0.0A2")),
                'j2735.accelSet4Way.yaw'     : (-32767, 32767, None, ("GM1.0.0A2")),
                # the DSRC srtandard uses brakeSystemStatus sub fields but the pdml shows it as one field 
                'j2735.brakeSystemStatus'    : (0, brakeSystemStatusGetkMax, brakeSystemStatusCheckNa, ("GM1.0.0A2")), # 0xffff = 65535,
                'j2735.width'        : (1, 1023, 0, ("GM1.0.0A2")),
                'j2735.length'       : (1, 16383, 0, ("GM1.0.0A2"))       
            }
    def min(self, field):
        return self.values[field][0]
    def max(self, field):
        return self.values[field][1]
    def na(self, field):
        return self.values[field][2]
    def is_version_supported(self, ver, field):
        if ver in self.values[field][3]:
            return True
        return False

logicalLinkControl = {
                'dsap'      : 0xaa,
                'ssap'      : 0xaa,
                'control'   : 3,
                'oui'       : 0x0,
                'type'      : 0x88dc
              }


wlanStructureFixed = { 
                        "fc.version"          : 0,
                        "fc.type"             : 2,
                        "fc.subtype"          : 8,
                        "flags"               : 3,
                        "fc.ds"               : 3,
                        "fc.tods"             : 0,
                        "fc.fromds"           : 0,
                        "fc.frag"             : 0,
                        "fc.retry"            : 0,
                        "fc.pwrmgt"           : 0,
                        "fc.moredata"         : 0,
                        "fc.protected"        : 0,
                        "fc.order"            : 0,

                        "duration"            : 0,
                        "da"                  : "ff:ff:ff:ff:ff:ff",
                        "sa"                  : "!ref:globals.setup.units.unit(uut_idx).rf_interfaces[rf_id].mac_addr",
                        "bssid"               : "ff:ff:ff:ff:ff:ff",
                        "frag"                : 0,
                        "fcs_good"            : 1,
                        "fcs_bad"             : 0,
                        # QoS
                        "qos.tid"             : 1,
                        "qos.priority"        : 1,
                        "qos.bit4"            : 1,
                        "qos.ack"             : 0,
                        "qos.amsdupresent"    : 0, 
                        "qos.queue_size"      : 0
    }

wlanStructureFixedVsa = { 
                        "fc.version"          : 0,
                        "fc.type"             : 0,
                        "fc.subtype"          : 0xd0,
                        "flags"               : 0,
                        "fc.ds"               : 0,
                        "fc.tods"             : 0,
                        "fc.fromds"           : 0,
                        "fc.frag"             : 0,
                        "fc.retry"            : 0,
                        "fc.pwrmgt"           : 0,
                        "fc.moredata"         : 0,
                        "fc.protected"        : 0,
                        "fc.order"            : 0,

                        "da"                  : "ff:ff:ff:ff:ff:ff",
                        "sa"                  : "unit",
                        "bssid"               : "ff:ff:ff:ff:ff:ff",
                        "frag"                : 0,
                        "seq"                : 0,
                        "fcs_good"            : 1,
                        "fcs_bad"             : 0
}


# name="wlan_mgt" showname="IEEE 802.11 wireless LAN management frame"
wlanManagementStructureFixed = {
                        'fixed.category_code'           : 0x7f,
                        'tag.oui'                       : 0x0050c2,
                        'fixed.vendor_type'             : 0x4a43,
                        'fixed.content_descriptor'      : 0x1
}
                    

frame_structure_layers = ['wlan' , 'llc', 'wlan_mgt']

EVENT_HARD_BRAKING = 0x0080
BSM_HARD_BRAKING_HYSTERESIS = 3
STANDARD_GRAVITY = 9.80665
HARD_BRAKING_ACCELERATION_THRESHOLD  = -(0.4 * STANDARD_GRAVITY)  
MAX_HBE_SYSTEM_RESPONSE_TIME_SEC = 0.200
BSM_J2375_SPEED_UNIT = 0.02


