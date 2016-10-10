#include <stdio.h>
#include <time.h>

#include <asn1/etsi/CAM.h>
#include <atlk/common.h>


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
    BUG();
  }

  return rc;
}

ssize_t cam_encode(CAM_t *pdu, void *buf, size_t size)
{
  ssize_t rc;
  asn_enc_rval_t rval = uper_encode_to_buffer(&asn_DEF_CAM, pdu, buf, size);

  if (unlikely(rval.encoded < 0)) {
    rc = -EINVAL;
    fprintf(stderr, "Failed to encode type %s\n", rval.failed_type->name);
  }
  else {
    rc = bits_to_bytes((size_t)rval.encoded);
  }
  return rc;
}

int main(void)
{
  static const uint32_t num_iter = 15000;
  static const clockid_t clk_id = CLOCK_THREAD_CPUTIME_ID;

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
  
  CAM_t input_pdu = {
    .header = {
      .protocolVersion = ItsPduHeader__protocolVersion_currentVersion,
      .messageID = ItsPduHeader__messageID_cam,
      .stationID = 1234567890
    },
    .cam = {
      .generationDeltaTime = GenerationDeltaTime_oneMilliSec * 100,
      .camParameters = {
        .basicContainer = {
          .stationType = 5, //StationType_passengerCar,
          .referencePosition = {
            .latitude = Latitude_oneMicrodegreeNorth * 32285183,
            .longitude = Longitude_oneMicrodegreeEast * 34871582,
            .positionConfidenceEllipse = {
              .semiMajorConfidence = SemiAxisLength_oneCentimeter * 157,
              .semiMinorConfidence = SemiAxisLength_oneCentimeter * 236,
              .semiMajorOrientation = {
                .headingValue = HeadingValue_wgs84North,
                .headingConfidence = HeadingConfidence_withinOneDegree * 5
              },
            },
            .altitude = {
              .altitudeValue = AltitudeValue_oneCentimeter * 1700,
              .altitudeConfidence = AltitudeConfidence_alt_001_00
            }
          }
        },
        .highFrequencyContainer = {
          .present = HighFrequencyContainer_PR_basicVehicleContainerHighFrequency,
          .choice = {
            .basicVehicleContainerHighFrequency = {
              .heading = {
                .headingValue = HeadingValue_wgs84West,
                .headingConfidence = HeadingConfidence_withinOneDegree * 7
              },
              .speed = {
                .speedValue = SpeedValue_oneCentimeterPerSec * 1000,
                .speedConfidence = SpeedConfidence_withinOneCentimeterPerSec * 5
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
              .laneNumber = NULL,
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
  uint8_t buf[64];
  size_t pdu_size;
  struct timespec start;
  struct timespec finish;
  uint64_t elapsed_ns;
  uint32_t i;
  CAM_t output_pdu;

  /*
    NOTE: output PDU descriptor must be zeroed because optional elements
    are represented as pointers and will not be assigned to if element is
    not present in PDU, resulting in a trash pointer.
  */
  memset(&output_pdu, 0, sizeof(output_pdu));

  if (FAILED(rc = cam_encode(&input_pdu, buf, sizeof(buf)))) {
    fprintf(stderr, "cam_encode failed, rc=%d\n", rc);
    goto exit;
  }
  pdu_size = rc;
  if (FAILED(rc = cam_decode(buf, pdu_size, &output_pdu))) {
    fprintf(stderr, "cam_decode failed, rc=%d\n", rc);
    goto exit;
  }
  asn_fprint(stdout, &asn_DEF_CAM, &output_pdu);
  for (i = 0; i < pdu_size; i++) {
    printf("%02x, ", buf[i]);
  }
  printf("\nDoing %" PRIu32 " iterations of decoding ... ", num_iter);
  fflush(stdout);

  if (FAILED(clock_gettime(clk_id, &start))) {
    rc = -errno;
    perror("clock_gettime");
    goto exit;
  }
  for (i = 0; i < num_iter; i++) {
    memset(&output_pdu, 0, sizeof(output_pdu));
    rc = cam_decode(buf, pdu_size, &output_pdu);
    if (FAILED(rc)) {
      fprintf(stderr, "cam_decode failed, rc=%d\n", rc);
      goto exit;
    }
  }
  if (FAILED(clock_gettime(clk_id, &finish))) {
    rc = -errno;
    perror("clock_gettime");
    goto exit;
  }

  elapsed_ns =
    ((uint64_t)finish.tv_sec * NANO_PER_UNIT + finish.tv_nsec) -
    ((uint64_t)start.tv_sec * NANO_PER_UNIT + start.tv_nsec);
  printf("done.\nRate was %.2f Hz\n",
         (double)NANO_PER_UNIT * num_iter / elapsed_ns);

 exit:
  return FAILED(rc);
}
