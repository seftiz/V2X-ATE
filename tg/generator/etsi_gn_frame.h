#ifndef _EFG_GN_H
#define _EFG_GN_H


/* Max supported payload length (not per standard) */
#define GN_PAYLOAD_LEN_MAX 1400

/* Generic Sock Core set/getsockopt optname's */
enum {
  GN_OPT_RCVTIMEO = CORE_OPT_RCVTIMEO,
  GN_OPT_SKB_CB = CORE_OPT_SKB_CB,
  GN_OPT_SKB_HWCB_TX = CORE_OPT_SKB_HWCB_TX,
  GN_OPT_SKB_HWCB_RX = CORE_OPT_SKB_HWCB_RX,
  GN_OPT_RX_DISABLE = CORE_OPT_RX_DISABLE,
};

#define GN_CURRENT_VERSION 0


/** GN address configuration type: automatic or manual  */
#define GN_ADDR_PARAM_M_BIT_OFFSET 15
enum gn_addr_m {
  GN_ADDR_M_AUTO  = 0,
  GN_ADDR_M_MANUALLY  =  1,
};


/** GN station type */
#define GN_ADDR_PARAM_ST_BIT_OFFSET 11
enum gn_addr_st {
  GN_ADDR_ST_BIKE = 0,
  GN_ADDR_ST_MOTOR_BIKE = 1,
  GN_ADDR_ST_CAR = 2,
  GN_ADDR_ST_TRUCK = 3,
  GN_ADDR_ST_BUS = 4,
  GN_ADDR_ST_TRAFFIC_LIGHT = 8,
  GN_ADDR_ST_ORDINARY_RSU = 9,
};

/** GN station sub type */
#define GN_ADDR_PARAM_SST_BIT_OFFSET 10
enum gn_addr_sst {
  GN_ADDR_SST_PUBLIC = 0,
  GN_ADDR_SST_PRIVATE = 1,
};

/** GN country code */
#define GN_ADDR_PARAM_SCC_HIGH_BIT_OFFSET 8
#define GN_ADDR_PARAM_SCC_LOW_BIT_OFFSET 0

/* traffic class enable to prioritize packets,
   defined in ETSI 102.637.04 section 4 */
enum gn_tc {
  GN_TC_AR_SAFETY_DIRECT = 0,
  GN_TC_AR_SAFETY_WARNING  = 1,
  GN_TC_PR_SAFETY  = 2,
  GN_TC_AR_SAFETY_INFO = 3,
  GN_TC_MULTIPLE_EXCHANGE  = 10,
  GN_TC_CONVERSATIONAL = 11,
  GN_TC_STREAMING  = 12,
  GN_TC_BACKGROUND = 13
};

/* GN data passed via CMSG to/from sk_buff->hwcb at TX */
struct gn_skb_hwcb_tx {
  struct core_skb_hwcb_tx core;
};

/* GN sk_buff->hwcb TX struct initializer */
#define GN_SKB_HWCB_TX_INIT {         \
  .core = CORE_SKB_HWCB_TX_INIT,        \
}

/* GN data passed via CMSG to/from sk_buff->hwcb at RX */
struct gn_skb_hwcb_rx {
  struct core_skb_hwcb_rx core;
};

/* GN sk_buff->hwcb RX struct initializer */
#define GN_SKB_HWCB_RX_INIT {         \
  .core = CORE_SKB_HWCB_RX_INIT,        \
}

struct gn_long_pv {
  /** The network address for the GeoAdhoc router entity in the ITS station. */
  v2x_gn_addr_t gn_addr;
  /** Expresses the time in milliseconds at which the latitude and longitude
	 	 	 of the ITS station were acquired by the GeoAdhoc router */
  uint32_t tst;
  /** WGS-84 latitude of the GeoAdhoc router expressed in 1/10 micro degree. */
  int32_t lat;
  /** WGS84 longitude of the GeoAdhoc router expressed in 1/10 micro degree.*/
  int32_t longitude;
  /** Speed of the GeoAdhoc router expressed in signed units of 0,01 meters per second. */
  uint16_t speed;
  /** Heading of the GeoAdhoc router from which the Network Header originates,
       expressed in unsigned units of 0,1 degrees from North */
  uint16_t heading;
  /** Altitude of the GeoAdhoc router expressed in signed units of 1 meter. */
  uint16_t altitude;

  /** 4 bits t_acc: Accuracy indicator for the value expressed in the field TST
   4 bits pos_acc : Encoded accuracy indicator for the value of the position POS.
   3 bits s_acc Encoded accuracy indicator for the value expressed in the field Speed S.
   3 bits h_acc Encoded accuracy indicator for the value of the field Heading H.
   2 bits alt_acc Encoded accuracy indicator for the value in the field Altitude (Alt). */

  uint16_t accuracy;

} __attribute__ ((packed));

struct gn_common_hdr {
  /** 4 bits Identifies the version of the GeoNetworking protocol.
     4 bits  Identifies the type of header immediately following the GeoNetworking header -> nh */
  uint8_t ver_nh;

  /** 4 bits Identifies the type of the GeoAdhoc header -> ht
     4 bits Identifies the sub-type of the GeoAdhoc -> hst */
  uint8_t ht_hst;
  /** 8 bits reserved for future */
  uint8_t reserved;
  uint8_t flags;
  /** Length of the Network Header payload, i.e. the rest of the packet
	 	 	 following the whole GeoNetworking header in octets. */
  uint16_t pl;
  /** Traffic class */
  uint8_t tc;
  /** Decremented by 1 by each GeoAdhoc router that forwards the packet.
	 	 	 The packet must not be forwarded if Hop Limit is decremented to zero. */
  uint8_t hl;
  /** Long position vector of the sender. */
  struct gn_long_pv se_pv;
} __attribute__ ((packed));

struct gn_ext_bc {
    /** sequence number used to detect duplicate packet */
    uint16_t seq_num;
    /** life time indicate the maximum tolerable time a packet can be buffered */
    uint8_t life_time;
    /** alignment */
    uint8_t reserved1;
    /** the packet source position vector */
    struct gn_long_pv src_long_pv;
    /** WGS-84 latitude for the center position of
       the geometric shape in 1/10 micro degree.*/
    uint32_t area_latitude;
    /** WGS-84 longitude for the center position of
        the geometric shape in 1/10 micro degree.*/
    uint32_t area_longitude;
    /** Distance a of the geometric shape in meters. */
    uint16_t distance_a;
    /** Distance b of the geometric shape in meters. */
    uint16_t distance_b;
    /** Angle of the geometric shape in degrees from North.*/
    uint16_t angle;
    /** alignment */
    uint16_t reserved2;
} __attribute__ ((packed));

struct gn_extended_hdr {
    union {
        /** the geo-broadcast extended header */
        struct gn_ext_bc ext_bc;
    };
};

struct gn_header {
  /** common header contain all attributes that relvant to all packet types */
  struct gn_common_hdr common_hdr;
  /** Add packets unique attributes */
  struct gn_extended_hdr extend_hdr;
};

enum next_hdr {
  NH_ANY,		/**< Unspecified */
  NH_BTP_A,		/**< Transport protocol (BTP-A for interactive packet transport) as defined in TS 102 636-5-1 [5]*/
  NH_BTP_B,		/**< Transport protocol (BTP-B for non-interactive packet transport) as defined in TS 102 636-5-1 [5]*/
  NH_IPV6		/**< IPv6 header as defined in TS 102 636-6-1 [6] */
};


/** Cluster 8.5.4 : Encoding of the HT(Header type) and HST(Header sub type) fields */
enum ht_hdr_type {
  HT_ANY,		/**<	Unspecified */
  HT_BEACON,		/**<	Beacon */
  HT_GEOUNICAST, 	/**< 	GeoUnicast */
  HT_GEOANYCAST, 	/**<	Geographically-Scoped Anycast (GAC) */
  HT_GEOBROADCAST,      /**<   	Geographically-Scoped broadcast */
  HT_TSB,		/**<	Topologically-scoped broadcast (TSB) */
  HT_LS			/**<	Location service (LS) */
};


enum hst_tsb {
  HST_NOT_IN_USE,                       /**< relevant to all packets that are not SHB/TSB */
  HST_TSB_SINGLE_HOP = HST_NOT_IN_USE,	/**< Single-hop broadcast (SHB) */
  HST_TSB_MULTI_HOP	                /**< Multi-hop TSB */

};

enum hst_area {
  HST_AREA_CIRCLE,        /**< Geobroadcast/Anycast packet sub type circle  */
  HST_AREA_RECT,          /**< Geobroadcast/Anycast packet sub type rectengular */  
  HST_AREA_ELIP           /**< GeoBroadcast/Anycast packet sub type elliptical */  
};

/** set GN version and next header fields  */
static inline uint8_t gn_set_version_next_hdr_field(enum next_hdr next_hdr)
{
    return ((GN_CURRENT_VERSION << 4) | (next_hdr & 0xF));
}

/** return next header field */
static inline enum next_hdr gn_get_next_hdr(uint8_t ver_next_hdr)
{
    return (ver_next_hdr & 0xF);
}

/** set header type and sub type fields */
static inline uint8_t gn_set_hdr_type_sub_type_field(enum ht_hdr_type ht, enum hst_tsb hst)
{
    return (((ht & 0xF) << 4) | (hst & 0xF));
}

/** return header type field */
static inline enum ht_hdr_type gn_get_hdr_type(uint8_t ht_hst)
{
    return ((ht_hst >> 4) & 0xF);
}

/** return header sub type field */
static inline uint8_t gn_get_sub_type(uint8_t ht_hst)
{
    return (ht_hst & 0xF);
}

/** return GN header size according to header type */
static inline int gn_get_hdr_size(enum ht_hdr_type ht)
{
    switch (ht) {
        case HT_TSB:
            return sizeof(struct gn_common_hdr);
        case HT_GEOBROADCAST:
            return sizeof(struct gn_common_hdr) + sizeof(struct gn_ext_bc);
        default:
            return -1;
    }
}
static inline 
const eui48_t *gn_get_ll_addr(const v2x_gn_addr_t *addr)
{
  return (eui48_t *)&addr->octets[2];
}

enum gn_action {
    GN_ACT_FORWARD,     /**< forward the packet to the next ITS */
    GN_ACT_APPLICATION, /**< send the packet to application layer */
    GN_ACT_FWD_APP,     /**< forward and send to application layer */
    GN_ACT_DISCARD      /**< discard the packet */
};

enum gnl_msg_send {
    GNL_C_UNSPEC,
    GNL_C_BIND,
    GNL_C_RX_RESP,
    GNL_C_TX_RESP,
    GNL_C_RX_SEND, /**< rx send message */
    GNL_C_TX_SEND, /**< tx send message */
    __GNL_C_MAX,
};
#define GNL_C_MAX (__GNL_C_MAX - 1)

struct gn_nl_rx_msg {
    /** skb to send */
    struct sk_buff *skb;
    /** device that recieve this packet */
    struct net_device *dev;
    /** local latitude */
    uint32_t local_lat;
    /** local longitude */
    uint32_t local_long;
    /** gn header information */
    struct gn_header gn_header;
};

struct gn_nl_rx_resp {
    /** type of action to be done on packet */ 
    enum gn_action action;
    /** skb to send */
    struct sk_buff *skb;
    /** device that received this packet */
    struct net_device *dev;
    /** broadcast flag */
    uint32_t  broadcast;
    /** gn addr to forward or transmit */
    v2x_gn_addr_t gn_addr;
};

typedef struct {
  uint8_t octets[V2X_GN_ADDR_LEN];
} v2x_gn_addr_t;

/**
   GN_ADDR with all fields zero except MID

   @param[in] mid eui48_t value representing the MID
*/
#define V2X_GN_ADDR_MID_INIT(mid) {               \
  .octets = { 0, 0,                               \
    (mid).octets[0], (mid).octets[1],             \
    (mid).octets[2], (mid).octets[3],             \
    (mid).octets[4], (mid).octets[5] }            \
  }

/** Initializer that represents an invalid GN_ADDR */
#define V2X_GN_ADDR_ZERO_INIT { .octets = { 0 } }

/**
   GN packet delivery method

   See @ref v2x_gn_ref_1 "[1]" clause 8.5.4, H.2.
*/
typedef enum {
  /** GeoUnicast */
  V2X_GN_PKT_GEOUNICAST = 0,

  /** GeoAnycast */
  V2X_GN_PKT_GEOANYCAST = 1,

  /** GeoBroadcast */
  V2X_GN_PKT_GEOBROADCAST = 2,

  /** Single-hop broadcast */
  V2X_GN_PKT_SHB = 3,

  /** Topologically scoped broadcast */
  V2X_GN_PKT_TSB = 4

} v2x_gn_pkt_type_t;

/** Geographic area shape type

    See @ref v2x_gn_ref_1 "[1]" 8.5.4.
*/
typedef enum {
  /** Circular area */
  V2X_GN_AREA_CIRCLE = 0,

  /** Rectangular area */
  V2X_GN_AREA_RECT = 1,

  /** Ellipsodial area */
  V2X_GN_AREA_ELLIPSE = 2

} v2x_gn_area_shape_t;

/**
   Geographic area descriptor

   See @ref v2x_gn_ref_1 "[1]" clause 8.6.5.2.
*/
typedef struct {
  /** 
     Area shape

     @todo Currently support is limited to ::V2X_GN_AREA_CIRCLE.
  */
  v2x_gn_area_shape_t shape;

  /** Geographic location of the center of the area */
  nav_ll_t center;

  /**
     'Distance A' in meters

     Its meaning depending on area shape (see @ref v2x_gn_ref_2 "[2]" clause 4):
     - Circle: radius of circle
     - Rectangle: half the length of the long side
     - Ellipse: half the length of the major axis
  */
  uint16_t distance_a_m;

  /**
     'Distance B' in meters

     Its meaning depending on area shape (see @ref v2x_gn_ref_2 "[2]" clause 4):
     - Circle: should be zero
     - Rectangle: half the length of the short side
     - Ellipse: half the length of the minor axis
  */
  uint16_t distance_b_m;

  /**
     Azimuth angle of area orientation in degrees

     If area shape is a circle then angle should be zero.
   */
  uint16_t angle_deg;

} v2x_gn_area_t;

/** Geographic area descriptor default initializer */
#define V2X_GN_AREA_INIT {                      \
  .shape = V2X_GN_AREA_CIRCLE,                  \
  .center = NAV_LL_INIT,                        \
  .distance_a_m = 0,                            \
  .distance_b_m = 0,                            \
  .angle_deg = 0                                \
}

/** GN packet destination descriptor */
typedef struct {
  /** 
     Packet delivery method
     
     @todo Currently support is limited to ::V2X_GN_PKT_SHB.
  */
  v2x_gn_pkt_type_t pkt_type;

  /**
     Destination GN_ADDR

     Valid only if v2x_gn_pkt_dest_t::pkt_type is ::V2X_GN_PKT_GEOUNICAST.

     @todo Currently unsupported.
  */
  v2x_gn_addr_t addr;

  /**
     Destination area

     Valid only if v2x_gn_pkt_dest_t::pkt_type is ::V2X_GN_PKT_GEOANYCAST
     or ::V2X_GN_PKT_GEOBROADCAST.

     @todo Currently unsupported.
  */
  v2x_gn_area_t area;

} v2x_gn_pkt_dest_t;

/** GN packet destination descriptor default initializer */
#define V2X_GN_PKT_DEST_INIT {                  \
  .pkt_type = V2X_GN_PKT_GEOUNICAST,            \
  .addr = V2X_GN_ADDR_ZERO_INIT,                \
  .area = V2X_GN_AREA_INIT                      \
}

/** GN packet source descriptor */
typedef struct {
  /** 
     GN_ADDR of source GN node
  
     @todo Currently unsupported.
  */
  v2x_gn_addr_t addr;

  /** 
     Position of source GN node
   
     @todo Currently unsupported.
   */
  nav_lla_t position;

  /**
     Timestamp marking the time when packet source information was captured

     Format: number of milliseconds since 1970-01-01T00:00:00Z (UTC) modulo 2^32
       (leap seconds are not counted).

     @todo Currently unsupported.
  */
  uint32_t timestamp_ms;

} v2x_gn_pkt_src_t;

/** GN packet source descriptor default initializer */
#define V2X_GN_PKT_SRC_INIT {                   \
  .addr = V2X_GN_ADDR_ZERO_INIT,                \
  .position = NAV_LLA_INIT,                     \
  .timestamp_ms = 0                             \
}

/**
   GN packet traffic class

   See @ref v2x_gn_ref_1 "[1]" clause 8.5.2.

   @todo Currently unsupported.
*/
typedef struct {
  /** Relevance: most relevant (0) to least relevant (7) */
  uint8_t relevance;

  /** Reliability: very high (0) to very low (3) */
  uint8_t reliability;

  /** Latency: very low (0) to high (3) */
  uint8_t latency;

} v2x_gn_traffic_class_t;

/** Value indicating that traffic relevance is N/A */
#define V2X_GN_RELEVANCE_NA UINT8_MAX

/** Value indicating that traffic reliability is N/A */
#define V2X_GN_RELIABILITY_NA UINT8_MAX

/** Value indicating that traffic latency is N/A */
#define V2X_GN_LATENCY_NA UINT8_MAX

/** GN packet traffic class default initializer */
#define V2X_GN_TRAFFIC_CLASS_INIT {              \
  .relevance = V2X_GN_RELEVANCE_NA,              \
  .reliability = V2X_GN_RELIABILITY_NA,          \
  .latency = V2X_GN_LATENCY_NA,                  \
}

/** BTP protocol sub-type */
typedef enum {
  /** BTP-A */
  V2X_GN_BTP_A = 0,

  /** BTP-B */
  V2X_GN_BTP_B = 1

} v2x_gn_btp_type_t;


#endif /* _ATLK_V2X_GN_H */


