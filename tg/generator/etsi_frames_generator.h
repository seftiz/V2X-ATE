

#ifndef _ETSI_FRAME_GENERATOR_
#define _ETSI_FRAME_GENERATOR_

#include <atlk/ecdsa.h>

#define CONVERT_LAT_LNG(_val_) ( (uint32_t) (_val_ * 1e7) )
#define CONVERT_ALT(_val_) ( (uint32_t) (_val_ * 100) )


#define RF_FREQ_1		5890
#define RF_FREQ_2		5920
#define RF_POWER		5



/* Format string for ECC scalar */
#define ECC_SCALAR_FMT \
  "0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx,0x%08lx"

/* Format argument list for ecc_scalar_t */
#define ECC_SCALAR_FMT_ARGS(x)                    \
  x.value[0], x.value[1], x.value[2], x.value[3], \
  x.value[4], x.value[5], x.value[6], x.value[7]

/* Format string for SHA digest */

#define SHA_DIGEST_FMT \
  "%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x"

/* Format argument list for SHA digest */
#define SHA_DIGEST_FMT_ARGS(x)                          \
  x.value[0], x.value[1], x.value[2], x.value[3],       \
  x.value[4], x.value[5], x.value[6], x.value[7],       \
  x.value[8], x.value[9], x.value[10], x.value[11],     \
  x.value[12], x.value[13], x.value[14], x.value[15],   \
  x.value[16], x.value[17], x.value[18], x.value[19],   \
  x.value[20], x.value[21], x.value[22], x.value[23],   \
  x.value[24], x.value[25], x.value[26], x.value[27],   \
  x.value[28], x.value[29], x.value[30], x.value[31]
 
#define packed __attribute__((packed))

typedef struct packed {

	uint8_t 	reserved:4;
	uint8_t 	next_header:4;
	uint8_t 	hst:4;
	uint8_t 	header_type:4;
	uint8_t 	traffic_class;
	uint8_t 	flags;
	uint16_t 	payload_length;
	uint8_t 	maximum_hop_limit;
	uint8_t 	reserved1;
	
} common_header_t;

typedef union packed {
  uint64_t  value;
  uint8_t   octets[8];
} value64_t;


#define HASH_ID8_SIZE   8


/* Not used yet */  
typedef enum header_fields {

  HDR_GENERATION_TIME       = 0x0,
  HDR_GENERATION_LOCATION   = 0x3, 
  HDR_MESSAGE_TYPE          = 0x5, 
  HDR_SIGNER_INFO           = 0x80

} header_field_type_t;

/* Not used yet */  
typedef struct packed _hdr_fld {

  uint8_t		type;
  uint8_t   length;
  uint8_t   *value;
  struct _hdr_fld *next;

} header_field_t;



typedef struct packed {

  uint8_t   header;
 	int32_t		latitude;
	int32_t 	longitude;
	uint16_t	elevation;
  
} generation_loc_t;

typedef struct packed {
  uint8_t		        signer_info;
  uint8_t		        sign_info_type;
  uint8_t           *certificate;
  uint8_t           hdr_generation_time;
  value64_t         generation_time;
  generation_loc_t  *generation_location;
  uint8_t		        header_field;
  uint16_t	        message_type;
	
} header_fields_t;


/* Remove pointer size, user musr add real size */
#define HDR_FIELDS_SIZE_CAM sizeof(header_fields_t) - sizeof(uint8_t*) - sizeof(generation_loc_t*)
#define SECURE_HDR_SIZE_CAM sizeof(secure_header_t) - sizeof(header_fields_t) + HDR_FIELDS_SIZE


#define HDR_FIELDS_SIZE  HDR_FIELDS_SIZE_CAM
#define SECURE_HDR_SIZE  SECURE_HDR_SIZE_CAM



typedef struct packed {
	uint8_t					   version;
  uint8_t					   profile;
	uint8_t 				   header_length;
	header_fields_t    header_fields;
	uint8_t					   payload_length;
	uint8_t					   payload_type;
	uint8_t					   payload_data_length;

} secure_header_t;


/** Security trailer signature structure */
typedef struct packed {

	uint8_t 	          pka;
	uint8_t		          ecc_point_type;
	ecdsa_signature_t   	ecdsa_sign;

} st_signature_t;

typedef struct packed {

	uint8_t						length;
	uint8_t						type;
	st_signature_t 		signature;

} signature_trailer_t;


typedef struct packed {
		uint8_t d1;
		uint8_t d2;
		uint8_t link_addr[6];
} gn_addr_t;


typedef struct packed {
	
	gn_addr_t		gn_addr;
	uint32_t 		time_stamp;
	int32_t			latitude;
	int32_t 		longitude;
	int16_t 		speed:15;
	int16_t			pai:1;
	int16_t 		heading;
	
} source_position_vector_t, spv_t;


typedef struct packed {
  
  spv_t             spv;
  int32_t 	        resreved;
  
} topology_scoped_broadcast_t, tsb_t;


typedef struct packed {

	uint8_t		next_hdr:4;
	uint8_t		version:4;
	uint8_t		reserved;
	uint8_t 	lifetime;
	uint8_t		hop_limit;
	
} basic_header_t, gn_basic_header_t;


typedef struct packed {
	
	basic_header_t 		basic_hdr;
	secure_header_t		secure_header;
	common_header_t 	common_header;
	tsb_t 						tsb;

} gn_secured_t;



typedef struct packed{
  
  basic_header_t 		basic_header;
  common_header_t   common_header;
	tsb_t 						tsb;
  
} gn_t;

 	
typedef struct packed {

	uint16_t	sequence_number;
	uint8_t		life_time;
	uint8_t		tbd_1;
	spv_t			spv;
	int32_t		latitude;
	int32_t 	longitude;
	uint16_t	distance_a;
	uint16_t	distance_b;
	uint16_t	angle;
	uint16_t	tbd_2;
} geo_broadcat_t, gbc_t;

				
typedef struct DENM_GEO_FRAME{
		uint8_t	data[56];
		struct {
			uint8_t 					basic_hdr[4];
			common_header_t		common_header;
			gbc_t							gbc;
		} geo_bc;
		
} gn_denm;


typedef struct packed{
  
  basic_header_t 		basic_header;
  common_header_t   common_header;
  union {
    gbc_t							*gbc;
	  tsb_t 						*tsb;
  } types;
  
} gn_all_t;


typedef enum station_type {

	STATION_ID_STATIC = 0, 
	STATION_ID_RANDOM	,
	STATION_ID_SEQUENCE,
	
} station_id_mod_t;


enum counters_name {
	RX_COUNTER = 0, 
	TX_COUNTER,
	CAM_TX_COUNTER,
	CAM_RX_COUNTER,
	DENM_RX_COUNTER,
	DENM_TX_COUNTER,
	LAST_COUNTER
};


#define SET_BIT_VAL(_val_) (1<<_val_)

typedef enum signing_option {

  SIGN_DISABLE      = 0x0,
  SIGN_DIGEST       = 0x1,
  SIGN_CERTIFICATE  = 0x2,
  SIGN_WITH_CHAIN   = 0x4,
  
  SIGN_WITH_ERROR   = 0x100

} signing_opt_t;


typedef enum frame_type {
  
  CAM_FRAME             = 0x0, 
  DENM_FRAME            = 0x1,
  NOT_SIGNED_FRAME      = 0x2,
  BAD_SIGNED_FRAME      = 0x3

} frame_type_t;

typedef frame_type_t sh_profile_t;



#define TG_THREAD_PRIORITY 								            	20
#define TG_THREAD_STACK_SIZE                            0x10000
#define TG_STAT_THREAD_STACK_SIZE                       0x1000

#define ntohll(x) (((uint64_t)(ntohl((int)((x << 32) >> 32))) << 32) | (unsigned int)ntohl(((int)(x >> 32))))
#define htonll(x) ntohll(x)



int create_cam_layer(  nav_fix_t nav_fix, uint32_t station_id, uint8_t **buffer , size_t *pdu_size );
int create_denm_layer(  nav_fix_t nav_fix, uint32_t station_id, uint8_t **buffer , size_t *pdu_size );







#endif


