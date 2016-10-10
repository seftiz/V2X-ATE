$(eval $(call def_asn1c,ITS-Container.asn CAM.asn,etsi,-gen-PER -fnative-types))

obj-y += AccelerationConfidence.o
obj-y += AccelerationControl.o
obj-y += AccidentSubCauseCode.o
obj-y += AdverseWeatherCondition-AdhesionSubCauseCode.o
obj-y += AdverseWeatherCondition-ExtremeWeatherConditionSubCauseCode.o
obj-y += AdverseWeatherCondition-PrecipitationSubCauseCode.o
obj-y += AdverseWeatherCondition-VisibilitySubCauseCode.o
obj-y += Altitude.o
obj-y += AltitudeConfidence.o
obj-y += AltitudeValue.o
obj-y += asn_codecs_prim.o
obj-y += asn_SEQUENCE_OF.o
obj-y += asn_SET_OF.o
obj-y += BasicContainer.o
obj-y += BasicVehicleContainerHighFrequency.o
obj-y += BasicVehicleContainerLowFrequency.o
obj-y += ber_decoder.o
obj-y += ber_tlv_length.o
obj-y += ber_tlv_tag.o
obj-y += BIT_STRING.o
obj-y += BOOLEAN.o
obj-y += CAM.o
obj-y += CamParameters.o
obj-y += CauseCode.o
obj-y += CauseCodeType.o
obj-y += ClosedLanes.o
obj-y += CollisionRiskSubCauseCode.o
obj-y += constraints.o
obj-y += constr_CHOICE.o
obj-y += constr_SEQUENCE.o
obj-y += constr_SEQUENCE_OF.o
obj-y += constr_SET_OF.o
obj-y += constr_TYPE.o
obj-y += CoopAwareness.o
obj-y += Curvature.o
obj-y += CurvatureCalculationMode.o
obj-y += CurvatureConfidence.o
obj-y += CurvatureValue.o
obj-y += DangerousEndOfQueueSubCauseCode.o
obj-y += DangerousGoodsBasic.o
obj-y += DangerousGoodsContainer.o
obj-y += DangerousGoodsExtended.o
obj-y += DangerousSituationSubCauseCode.o
obj-y += DeltaAltitude.o
obj-y += DeltaLatitude.o
obj-y += DeltaLongitude.o
obj-y += DeltaReferencePosition.o
obj-y += der_encoder.o
obj-y += DriveDirection.o
obj-y += DrivingLaneStatus.o
obj-y += EmbarkationStatus.o
obj-y += EmergencyContainer.o
obj-y += EmergencyPriority.o
obj-y += EmergencyVehicleApproachingSubCauseCode.o
obj-y += EmptyRSUContainerHighFrequency.o
obj-y += EnergyStorageType.o
obj-y += ExteriorLights.o
obj-y += GenerationDeltaTime.o
obj-y += HardShoulderStatus.o
obj-y += HazardousLocation-AnimalOnTheRoadSubCauseCode.o
obj-y += HazardousLocation-DangerousCurveSubCauseCode.o
obj-y += HazardousLocation-ObstacleOnTheRoadSubCauseCode.o
obj-y += HazardousLocation-SurfaceConditionSubCauseCode.o
obj-y += Heading.o
obj-y += HeadingConfidence.o
obj-y += HeadingValue.o
obj-y += HeightLonCarr.o
obj-y += HighFrequencyContainer.o
obj-y += HumanPresenceOnTheRoadSubCauseCode.o
obj-y += HumanProblemSubCauseCode.o
obj-y += IA5String.o
obj-y += InformationQuality.o
obj-y += INTEGER.o
obj-y += ItsPduHeader.o
obj-y += LaneNumber.o
obj-y += LateralAcceleration.o
obj-y += LateralAccelerationValue.o
obj-y += Latitude.o
obj-y += LightBarSirenInUse.o
obj-y += Longitude.o
obj-y += LongitudinalAcceleration.o
obj-y += LongitudinalAccelerationValue.o
obj-y += LowFrequencyContainer.o
obj-y += NativeEnumerated.o
obj-y += NativeInteger.o
obj-y += NULL.o
obj-y += OCTET_STRING.o
obj-y += PathDeltaTime.o
obj-y += PathHistory.o
obj-y += PathPoint.o
obj-y += per_decoder.o
obj-y += per_encoder.o
obj-y += PerformanceClass.o
obj-y += per_opentype.o
obj-y += per_support.o
obj-y += PosCentMass.o
obj-y += PosConfidenceEllipse.o
obj-y += PosFrontAx.o
obj-y += PositioningSolutionType.o
obj-y += PositionOfOccupants.o
obj-y += PosLonCarr.o
obj-y += PosPillar.o
obj-y += PostCrashSubCauseCode.o
obj-y += PtActivation.o
obj-y += PtActivationData.o
obj-y += PtActivationType.o
obj-y += PublicTransportContainer.o
obj-y += ReferencePosition.o
obj-y += RequestResponseIndication.o
obj-y += RescueAndRecoveryWorkInProgressSubCauseCode.o
obj-y += RescueContainer.o
obj-y += RoadType.o
obj-y += RoadWorksContainerBasic.o
obj-y += RoadworksSubCauseCode.o
obj-y += SafetyCarContainer.o
obj-y += SemiAxisLength.o
obj-y += SignalViolationSubCauseCode.o
obj-y += SlowVehicleSubCauseCode.o
obj-y += SpecialTransportContainer.o
obj-y += SpecialTransportType.o
obj-y += SpecialVehicleContainer.o
obj-y += Speed.o
obj-y += SpeedConfidence.o
obj-y += SpeedLimit.o
obj-y += SpeedValue.o
obj-y += StationarySince.o
obj-y += StationaryVehicleSubCauseCode.o
obj-y += StationID.o
obj-y += StationType.o
obj-y += SteeringWheelAngle.o
obj-y += SteeringWheelAngleValue.o
obj-y += SteeringWheelConfidence.o
obj-y += SubCauseCodeType.o
obj-y += Temperature.o
obj-y += TimestampIts.o
obj-y += TrafficConditionSubCauseCode.o
obj-y += TrafficRule.o
obj-y += TurningRadius.o
obj-y += UTF8String.o
obj-y += VDS.o
obj-y += VehicleBreakdownSubCauseCode.o
obj-y += VehicleIdentification.o
obj-y += VehicleLength.o
obj-y += VehicleLengthConfidenceIndication.o
obj-y += VehicleLengthValue.o
obj-y += VehicleMass.o
obj-y += VehicleRole.o
obj-y += VehicleWidth.o
obj-y += VerticalAcceleration.o
obj-y += VerticalAccelerationValue.o
obj-y += WheelBaseVehicle.o
obj-y += WMInumber.o
obj-y += WrongWayDrivingSubCauseCode.o
obj-y += xer_decoder.o
obj-y += xer_encoder.o
obj-y += xer_support.o
obj-y += YawRate.o
obj-y += YawRateConfidence.o
obj-y += YawRateValue.o

x := $(TARGET)/lib/libasn1-etsi.a
$x-obj-y := $(obj-y)
$x-cflags-y := -w -O2
build-y += $x

x := $(HOST)/lib/libasn1-etsi.a
$x-obj-y := $(obj-y)
$x-cflags-y := -w -O2
build-y += $x
