#include <stdio.h>
#include <time.h>

#include <CAM.h>
#include <DENM.h>

#include <atlk/nav_service.h>
#include <nxd_bsd.h>
#include "etsi_frames_generator.h"

#define EINVAL          22  /* Invalid argument */
#define ENOBUFS         105 /* No buffer space available */


static uint8_t 							buf[400];
static uint8_t 							denm_buf[400];

static uint8_t              cntr = 0;


static inline ssize_t bits_to_bytes(size_t bits)
{
  return (bits + 7) / 8;
}

ssize_t cam_decode(const void *buf, size_t size, CAM_t *pdu)
{
  ssize_t rc = 0;
  asn_dec_rval_t rval =
    uper_decode_complete(NULL, &asn_DEF_CAM, (void **)&pdu, buf, size);

  switch (rval.code) {
  case RC_OK:
    rc = bits_to_bytes(rval.consumed);
    break;
  case RC_FAIL:
    rc = -EINVAL;
    break;
  case RC_WMORE:
    rc = -ENOBUFS;
    break;
  default:
    assert(!(1));
  }

  return rc;
}

ssize_t cam_encode(CAM_t *pdu, void *buf, size_t size)
{
  ssize_t rc;
	
  asn_enc_rval_t rval = uper_encode_to_buffer(&asn_DEF_CAM, pdu, buf, size);

  if ( rval.encoded < 0) {
    rc = -EINVAL;
    fprintf(stderr, "Failed to encode type %s\n", rval.failed_type->name);
  }
  else {
    rc = bits_to_bytes((size_t)rval.encoded);
  }
  return rc;
}



int create_cam_layer(  nav_fix_t nav_fix, uint32_t station_id, uint8_t **buffer , size_t *pdu_size )
{

	int	i =0;

  uint8_t exteriorLights[] = {
    1 <<ExteriorLights_lowBeamHeadlightsOn
  };

  ExteriorLights_t exteriorLights_bitstr = {
    .buf = exteriorLights,
    .size = sizeof(exteriorLights),
    .bits_unused = 1
  };
    
  
  struct LowFrequencyContainer lowFrequencyContainer = {
    .present = LowFrequencyContainer_PR_basicVehicleContainerLowFrequency,
    .choice = {
      .basicVehicleContainerLowFrequency = {
        .vehicleRole = 0,
        .exteriorLights = exteriorLights_bitstr,
        .pathHistory = NULL,
      },
    }
  };
 
  uint8_t accelerationControl[] = {
    1 << AccelerationControl_gasPedalEngaged
  };
  AccelerationControl_t accelerationControl_bitstr = {
    .buf = accelerationControl,
    .size = sizeof(accelerationControl),
    .bits_unused = 1
    /*
      NOTE: MSB of accelerationControl is 6. Perhaps bits_unused can be
      (8 - <index of most significant set bit>)?
    */
  };

	uint32_t	latitude = 900000001, longtitude = 1800000001, altitude = 800001, heading = 3600;
	uint16_t tst = 0xFFFF, speed = 16383;
	
	cntr ++;
	if ( !isnan( nav_fix.position_latitude_deg ) ) {
	
		latitude = CONVERT_LAT_LNG(nav_fix.position_latitude_deg);
		longtitude = CONVERT_LAT_LNG(nav_fix.position_longitude_deg) ;
		altitude = CONVERT_ALT(nav_fix.position_altitude_m);
		tst = (uint16_t) ( (uint64_t) (nav_fix.time.tai_seconds_since_2004 * 1000.0) % 65536);
		
		heading =  (int16_t) (nav_fix.movement_horizontal_direction_deg);
		speed =  (int16_t) (nav_fix.movement_horizontal_speed_mps * 100.0);
		
		//printf( "latitude : %x, longtitude %x, heading %x\n", latitude, longtitude, heading );
	}
	
  CAM_t input_pdu = {
    .header = {
      .protocolVersion = ItsPduHeader__protocolVersion_currentVersion,
      .messageID = ItsPduHeader__messageID_cam,
      .stationID = station_id
    },
    .cam = {
      // .generationDeltaTime = GenerationDeltaTime_oneMilliSec * tst,
      .generationDeltaTime = (uint16_t) tst,
      .camParameters = {
        .basicContainer = {
          .stationType = 12, //StationType_unknown,
          .referencePosition = {
            .latitude = latitude,
            .longitude = longtitude,
            .positionConfidenceEllipse = {
              .semiMajorConfidence = 0xF,
              .semiMinorConfidence = 0xF,
              .semiMajorOrientation = heading
            },
            .altitude = {
              .altitudeValue = AltitudeValue_oneCentimeter * altitude,
              .altitudeConfidence = AltitudeConfidence_alt_001_00

            }
          }
        },
        .highFrequencyContainer = {
          .present = HighFrequencyContainer_PR_basicVehicleContainerHighFrequency,
          .choice = {
            .basicVehicleContainerHighFrequency = {
              .heading = {
                .headingValue = heading,
                .headingConfidence = HeadingConfidence_equalOrWithinOneDegree * 7
              },
              .speed = {
                .speedValue = speed,
                .speedConfidence = SpeedConfidence_equalOrWithinOneCentimeterPerSec * 5
              },
              .driveDirection = DriveDirection_forward,
              .longitudinalAcceleration = {
                .longitudinalAccelerationValue = LongitudinalAccelerationValue_pointOneMeterPerSecSquaredForward * 3,
                .longitudinalAccelerationConfidence = AccelerationConfidence_pointOneMeterPerSecSquared * 1
              },
              .accelerationControl = &accelerationControl_bitstr,
              .vehicleLength = {
                .vehicleLengthValue = VehicleLengthValue_unavailable, 
                .vehicleLengthConfidenceIndication = VehicleLengthConfidenceIndication_noTrailerPresent 
              },             
              .vehicleWidth = VehicleWidth_tenCentimeters * 43,

              .curvature = {
                .curvatureValue = CurvatureValue_reciprocalOf1MeterRadiusToRight,
                .curvatureConfidence = CurvatureConfidence_onePerMeter_0_0001
              },
              .curvatureCalculationMode = CurvatureCalculationMode_yawRateNotUsed,
              .lanePosition = NULL,

              .steeringWheelAngle = NULL,
              .lateralAcceleration = NULL,
              .verticalAcceleration = NULL
            }
          }

        },
        .lowFrequencyContainer = NULL,
        .specialVehicleContainer = NULL
      }
    }
  };

  ssize_t rc;


  CAM_t output_pdu;

  /*
    NOTE: output PDU descriptor must be zeroed because optional elements
    are represented as pointers and will not be assigned to if element is
    not present in PDU, resulting in a trash pointer.
  */



  if ( (rc = cam_encode(&input_pdu, buf, sizeof(buf))) < 0) {
    fprintf(stderr, "cam_encode failed, rc=%d\n", rc);
    return -1;
  }
	/*
	asn_fprint(stdout, &asn_DEF_CAM, &input_pdu);
	for (i = 0; i < *pdu_size; i++) {
    printf("%02x, ", buf[i]);
  }
	*/
	
  *pdu_size = rc;
	*buffer = buf;
	i++;

	
	memset(&output_pdu, 0, sizeof(output_pdu));
	/*
  if (FAILED(rc = cam_decode(buf, *pdu_size, &output_pdu))) {
    fprintf(stderr, "cam_decode failed, rc=%d\n", rc);
    return (-1);
  }
	asn_fprint(stdout, &asn_DEF_CAM, &output_pdu);

  for (i = 0; i < *pdu_size; i++) {
    printf("%02x, ", buf[i]);
  }
	*/
	

  return (rc < 0);
}



ssize_t denm_encode( DENM_t *pdu, void *buf, size_t size )
{
  ssize_t rc;
	
  asn_enc_rval_t rval = uper_encode_to_buffer(&asn_DEF_DENM, pdu, buf, size);

  if (rval.encoded < 0) {
    rc = -EINVAL;
    fprintf(stderr, "Failed to encode type %s\n", rval.failed_type->name);
  }
  else {
    rc = bits_to_bytes((size_t)rval.encoded);
  }
  return rc;
}


int create_denm_layer ( nav_fix_t nav_fix, uint32_t station_id, uint8_t **buffer , size_t *pdu_size )
{
  static uint32_t seqNumber = 0;
  ssize_t         rc;
  uint32_t	latitude = 900000001, longtitude = 1800000001, altitude = 800001, heading = 3600; ;
  uint64_t tst = 0;
  
	if ( !isnan( nav_fix.position_latitude_deg ) ) {
	
		latitude = CONVERT_LAT_LNG(nav_fix.position_latitude_deg);
		longtitude = CONVERT_LAT_LNG(nav_fix.position_longitude_deg) ;
		altitude = CONVERT_ALT(nav_fix.position_altitude_m);
		heading =  (int16_t) (nav_fix.movement_horizontal_direction_deg);
    tst = (uint64_t) ( (uint64_t) (nav_fix.time.tai_seconds_since_2004 / 1000.0) );
	}

  seqNumber++;
  DENM_t input_pdu = {
  
    .header = {
      .protocolVersion = ItsPduHeader__protocolVersion_currentVersion,
      .messageID = ItsPduHeader__messageID_denm,
      .stationID = station_id
    },
    .denm = {
    
      .management = {
        .actionID = {
            .sequenceNumber = seqNumber
        },

        .eventPosition = {
          .latitude = latitude,
          .longitude = longtitude,
          .positionConfidenceEllipse = {
            .semiMajorConfidence = 0xF,
            .semiMinorConfidence = 0xF,
            .semiMajorOrientation = heading
          },
          .altitude = {
            .altitudeValue = AltitudeValue_oneCentimeter * altitude,
            .altitudeConfidence = AltitudeConfidence_alt_001_00
          }
        },
        
        .relevanceDistance = RelevanceDistance_lessThan50m, 
        .relevanceTrafficDirection = RelevanceTrafficDirection_allTrafficDirections, 
        .validityDuration	= ValidityDuration_timeOfDetection * 5,
        .transmissionInterval	= NULL,
      },
      .situation = NULL,
      .location	= NULL, 
      .alacarte	= NULL

    }
  };

	







 /* 	TimestampIts ::= BIT STRING(SIZE(42))  -- units of milliseconds, 7 byte*/
  TimestampIts_t time_stamp_bitstr = {
      .buf = tst,
      .size = 6,
      .bits_unused = 6
  };

	memcpy( &input_pdu.denm.management.detectionTime, &time_stamp_bitstr, sizeof(time_stamp_bitstr) );
	memcpy( &input_pdu.denm.management.referenceTime, &time_stamp_bitstr, sizeof(time_stamp_bitstr) );
	




	rc = denm_encode(&input_pdu, buf, sizeof(buf) );
  if ( rc < 0) {
    fprintf(stderr, "ERROR : denm_encode failed, rc=%d\n", rc);
    return -1;
  }
	
	/*
	int i = 0;
	asn_fprint(stdout, &asn_DEF_DENM, &input_pdu);
	for (i = 0; i < rc; i++) {
    printf("%02x, ", denm_buf[i]);
  }
	*/
	
  *pdu_size = rc;
	*buffer = denm_buf;
  
  return 0;
}

