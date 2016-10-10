
import logging
from array import array


CAN_MSG_ID_CHASSIS          = 0x1E9
CAN_MSG_ID_BRAKE_APPLY      = 0x0F1
CAN_MSG_ID_TRANS            = 0x1F5
CAN_MSG_ID_BODY_INFO        = 0x12A
CAN_MSG_ID_SPEED_DIST       = 0x3E9
CAN_MSG_ID_PLATFORM         = 0x1F1
CAN_MSG_ID_LIGHTS           = 0x140
CAN_MSG_ID_ABS_TC_STAT      = 0x17D
CAN_MSG_ID_ETEI_ENGINE_ST   = 0x1A1
CAN_MSG_ID_PPEI_ENGINE_ST1  = 0x0C9
CAN_MSG_ID_PPEI_ENGINE_ST2  = 0x3D1
CAN_MSG_ID_ODOMETER         = 0x120
CAN_MSG_ID_STEERING_ANGLE   = 0x1E5

log = logging.getLogger(__name__)

class GmCanMessages(object):

    def __init__(self,  can_bus_sim , can_interface ):
        self._can_bus_sim = can_bus_sim
        self._can_if = can_interface
        
    def _send_msg(self, msg_id, msg_data ):
        self._can_bus_sim.send_frame( self._can_if, msg_id, msg_data )
        log.info("Sending can msg {}, data : {}".format(msg_id, msg_data))


    def chassis_msg( self, pedal_pressure_detected , lateral_acceleration, abs_active, \
                                    traction_control_active, stability_system_active, dynamic_yaw_rate, data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):


        """
        PPEI_Chassis_General_Status_1,$1E9,20,
                                                            Start Byte, Start Bit, Len,Data, Range,                       Conversion
        Brake Pedal Driver Applied Pressure Detected,              0,    6,      1,       BLN,N/A,$1=True; $0=False
        Vehicle Stability Enhancement Lateral Acceleration,        0,    3,      12,      SNM,-32 - 31.984375 m/s^2,    E = N * 0.015625
        Antilock Brake System Active,                              3,    6,      1,       BLN,N/A,$1=True; $0=False
        Traction Control System Active,                            3,    4,      1,       BLN,N/A,$1=True; $0=False
        Vehicle Stability Enhancement System Active,               3,    0,      1,       BLN,N/A,$1=True; $0=False
        Vehicle Dynamics Yaw Rate,                                 4,    3,      12,      SNM,-128 - 127.9375 deg/sec,  E = N * 0.0625
        """

        # data = [0x93, 0xFD, 0x07, 0xD0, 0x90, 0x2C, 0xDF, 0x40]
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] 
     
        data[0] = ( ( pedal_pressure_detected & 0x01 ) << 6) | data[0]

        lateral_accel_repr = int(lateral_acceleration / 0.015625)
        data[0] = ( ((lateral_accel_repr & 0x0F00) >> 8 ) | data[0] )
        data[1] = (lateral_accel_repr & 0xFF)

        # Antilock Brake System Active
        data[3] = ( (abs_active & 0x1) << 6) | data[3]
        # Traction Control System Active
        data[3] = ( (traction_control_active & 0x1) << 4) | data[3]

        # Vehicle Stability Enhancement System Active
        data[3] = (stability_system_active & 0x1) | data[3]
    
        dynamic_yaw_rate_repr = int( dynamic_yaw_rate / 0.0625)
        data[4] = ( ((dynamic_yaw_rate_repr & 0x0F00) >> 8 ) | data[4] )
        data[5] = (dynamic_yaw_rate_repr & 0xFF)
    
        self._send_msg( CAN_MSG_ID_CHASSIS,data )


    def break_apply_msg(self, pedal_moderate_travel, pedal_initial_tavel, pedal_postition, data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):
        """
        PPEI_Brake_Apply_Status,    $0F1,10,
                                                        Start Byte, Start Bit, Len,Data, Range,                       Conversion
        Brake Pedal Moderate Travel Achieved,                  0,   6,          1,BLN,N/A,$1=True; $0=False
        Brake Pedal Initial Travel Achieved Status,            0,   1,          1,BLN,N/A,$1=True; $0=False
        Brake Pedal Position,                                  1,   7,          8,UNM,0 - 100.000035 % full,    E = N * 0.392157
        """
        # Message example 
        # can_id = 0x0f1, dlc = 6, data = [0x1C, 0x00, 0x00, 0x40, 0x00, 0x00], wait = 1)
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        # Brake Pedal Moderate Travel Achieved
        data[0] = ( ( ( pedal_moderate_travel & 0x01 ) << 6) | data[0]) & 0xFF
        # Brake Pedal Initial Travel Achieved Status
        data[0] = ( ( pedal_initial_tavel & 0x01 )  | data[0] ) & 0xFF

        # Brake Pedal Position

        pedal_pos_repr = int(pedal_postition / 0.392157)
        data[1] = pedal_pos_repr & 0xFF
    
        self._send_msg(CAN_MSG_ID_BRAKE_APPLY,data )

    def generate_trans_message( self, transmission_gear, data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):
        """
                                                        Start Byte, Start Bit, Len,Data, Range,                       Conversion

        PPEI_Trans_General_Status_2,$1F5,25,
        Transmission Estimated Gear,                            0,          3, 4,   ENM,N/A,                        $0=Not Supported
                                                                                                                    $1=First Gear
                                                                                                                    $2=Second Gear
                                                                                                                    $3=Third Gear
                                                                                                                    $4=Fourth Gear
                                                                                                                    $5=Fifth Gear
                                                                                                                    $6=Sixth Gear
                                                                                                                    $7=Seventh Gear
                                                                                                                    $8=Eighth Gear
                                                                                                                    $A=EVT Mode 1
                                                                                                                    $B=EVT Mode 2
                                                                                                                    $C=CVT Forward Gear
                                                                                                                    $D=Neutral Gear
                                                                                                                    $E=Reverse Gear
                                                                                                                    $F=Park Gear
        """
        # Message example 
        # can_id = 0x1f5, dlc = 8, data = [0x0F, 0x0F, 0x00, 0x01, 0x00, 0x00, 0x08, 0x00], wait = 1)
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        # Transmission Estimated Gear
        data[0]  = (transmission_gear & 0x0F) & 0xFF
        self._send_msg(CAN_MSG_ID_TRANS,data )


    def generate_body_info_msg ( self, battery_voltage, data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]):
        """
        Body_Information_HS,$12A,100,
                                                        Start Byte, Start Bit, Len,Data, Range,                       Conversion
            Battery Voltage,                                    3,          7, 8,   UNM,    3 - 28.5 volts,         E = N * 0.1 + 3

        """

        # Message example 
        # can_id = 0x12a, dlc = 8, data = [0x00, 0xE2, 0x60, 0x74, 0x00, 0x00, 0x00, 0x80], wait = 1)
    

        # Transmission Estimated Gear
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        battery_voltage_repr = (battery_voltage / 0.1) - 3
        data[3]  = (battery_voltage_repr & 0xFF) & 0xFF

        self._send_msg(CAN_MSG_ID_BODY_INFO,data )

 

    def generate_vehicle_speed_and_distance( self, speed_avg_kh, data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):
    
        """
        PPEI_Vehicle_Speed_and_Distance, $3E9, 100,
                                                        Start Byte, Start Bit, Len,  Data, Range,                       Conversion
            Vehicle Speed Average Non Driven,                   4,         6,   15, UNM,    0 - 511.984375 km / h,      E = N * 0.015625

        """

        # Message example 
        # can_id = 0x3e9, dlc = 8, data = [0x00, 0x00, 0x04, 0x12, 0x00, 0x00, 0x03, 0xFC], wait = 1)
    
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        # Vehicle Speed Average Non Driven
        speed_avg_repr = int(speed_avg_kh / 0.015625) & 0x7FFF

        data[4] = ( (speed_avg_repr & 0x3F00) >> 8) | data[4]
        data[5] = (speed_avg_repr & 0xFF) & 0xFF

        self._send_msg(CAN_MSG_ID_SPEED_DIST,data )


    def generate_platform_msg( self, airbag_deployed, data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):

        """
        PPEI_Platform_General_Status,$1F1,100,
                                                    Start Byte, Start Bit, Len,  Data, Range,                       Conversion
            Airbag Deployed,                                7,          2,   1,   BLN,    N/A,$1=True; $0=False
        """

        # Message example 
        # can_id = 0x1f1, dlc = 8, data = [0xAE, 0x12, 0x00, 0x00, 0x08, 0x00, 0x32, 0x7A], wait = 1)
    

        # Vehicle Speed Average Non Driven
        data[7] = (((airbag_deployed & 0x1)  << 2) & 0xFF) | data[7] 
        self._send_msg(CAN_MSG_ID_PLATFORM,data )


    def generate_lights_msg( self, brake_light_active , headligh_beam, data = [0x00, 0x00, 0x00] ):

        """
        Exterior_Lighting_HS,$140,1000,
                                                    Start Byte, Start Bit, Len,  Data, Range,                       Conversion
        Brake Lights Active,                                0,          6, 1,   BLN,    N/A,$1=True; $0=False
        Headlamp Beam Select Status,                        1,          2, 2,   ENM,    N/A,$0=Unknown
        """

        # Message example 
        # can_id = 0x140, dlc = 3, data = [0x00, 0x02, 0x02], wait = 1)

        # Brake Lights Active,    
        data[0] = (((brake_light_active & 0x1)  << 6) & 0xFF) | data[0] 

        # Headlamp Beam Select Status
        #data[1] = headligh_beam 
        self._send_msg(CAN_MSG_ID_LIGHTS,data )


    def generate_antilock_brake_and_tc_msg( self,  vehicle_acc, data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):

        """
        Antilock_Brake_and_TC_Status_HS,$17D,100,
                                                    Start Byte, Start Bit, Len,  Data, Range,                       Conversion
     
        Actual Vehicle Acceleration,                         4,         3, 12,  SNM,    -20.48 - 20.47 m/s^2,E = N * 0.01

        """

        # Message example 
        # can_id = 0x17d, dlc = 6, data = [0x22, 0x24, 0x42, 0x96, 0x00, 0x00], wait = 1)
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        #  Actual Vehicle Acceleration,
        vehicle_acc_repr = int(vehicle_acc / 0.01)

        data[4] = ( ( (vehicle_acc_repr & 0xF00) >> 8) & 0xFF ) | data[4]
        data[5] = ( ( vehicle_acc_repr & 0xFF) & 0xFF ) | data[5]

        self._send_msg(CAN_MSG_ID_ABS_TC_STAT,data )



    def generate_engine_stat_1_msg( self, cruise_control_active , driver_throttle_override,  data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):

        """
        PPEI_Engine_General_Status_1,$0C9,12,
                                                    Start Byte, Start Bit, Len,  Data, Range,                       Conversion
        Cruise Control Active,                              3,          6, 1,   BLN,    N/A,$1=True; $0=False
        Driver Throttle Override Detected,                  3,          4, 1,   BLN,    N/A,$1=True; $0=False
        """

        # Message example 
        # can_id = 0x0c9, dlc = 8, data = [0x84, 0x0C, 0x38, 0x0A, 0x00, 0x10, 0x10, 0xFF], wait = 1)


        #  Cruise Control Active,
        data[3] = ( ( (cruise_control_active & 0x1) << 6) & 0xFF ) | data[3]
        # Driver Throttle Override Detected
        data[5] = ( vehicle_acc_repr & 0xFF) & 0xFF

        self._send_msg(CAN_MSG_ID_PPEI_ENGINE_ST1,data )


    def generate_engine_stat_1_msg( self, acc_pedal_pos,  data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):

        """

        ETEI_Engine_General_Status,$1A1,25,
                                                            Start Byte, Start Bit, Len,  Data, Range,                  Conversion
        Accelerator Pedal Position Percent Full Range,               6,         7,   8,  UNM    ,0 - 100.000035 %,     E = N * 0.392157

        """

        # Message example 
        # can_id = 0x1a1, dlc = 7, data = [0x00, 0x20, 0x01, 0x40, 0x61, 0x57, 0x00], wait = 1)


        #  Cruise Control Active,

        acc_pedal_pos_repr = int(acc_pedal_pos / 0.392157)

        # Accelerator Pedal Position Percent Full Range,
        data[6] = (acc_pedal_pos_repr & 0xFF)

        self._send_msg(CAN_MSG_ID_ETEI_ENGINE_ST,data )



    def generate_engine_stat_2_msg( self, cruise_speed_limiter,  data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):

        """
        PPEI_Engine_General_Status_2,$3D1,100,
 
                                                            Start Byte, Start Bit, Len,  Data, Range,                  Conversion
        Cruise and Speed Limiter Driver Selected Speed,              2,         3,  12,   UNM,  0 - 255.9375 km / h,    E = N * 0.0625
        """

        # Message example 
        # can_id = 0x3d1, dlc = 8, data = [0x01, 0x23, 0x00, 0x00, 0x20, 0x1F, 0x00, 0x7F], wait = 1)



        # Cruise and Speed Limiter Driver Selected Speed,
        cruise_speed_limiter_repr = int(cruise_speed_limiter / 0.0625)

        data[2] = ( ( (cruise_speed_limiter_repr & 0xF00) >> 8) & 0xFF ) | data[4]
        data[3] = ( ( cruise_speed_limiter_repr & 0xFF) & 0xFF ) | data[5]

        self._send_msg(CAN_MSG_ID_PPEI_ENGINE_ST2,data )

       


    def vehicle_odometer_msg( self, odometer,  data = [0x00, 0x00, 0x00, 0x00, 0x00] ):

        """
        Vehicle_Odometer_HS,$120,5000,
    
                                                            Start Byte, Start Bit, Len,  Data, Range,                  Conversion
        Vehicle Odometer,                                            0,         7,  32,  UNM,   0 - 67108863.984375 km,E = N * 0.015625

        """

        # Message example 
        # can_id = 0x120, dlc = 5, data = [0x00, 0x00, 0x07, 0xFE, 0x00], wait = 1)



        # Vehicle Odometer
        odometer_repr = int(cruise_speed_limiter / 0.015625)

        data[0] = ( ( (odometer_repr & 0xFF000000) >> 24) & 0xFF ) | data[0]
        data[1] = ( ( (odometer_repr & 0x00FF0000) >> 16) & 0xFF ) | data[1]
        data[2] = ( ( (odometer_repr & 0x0000FF00) >> 8) & 0xFF ) | data[2]
        data[3] = ( (odometer_repr & 0xFF) & 0xFF ) | data[3]

        self._send_msg(CAN_MSG_ID_ODOMETER,data )

       

    def steering_wheel_angle_msg( self, steering_wheel_angle,  data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] ):

        """
        PPEI_Steering_Wheel_Angle,$1E5,10,
                                                            Start Byte, Start Bit, Len,  Data, Range,                  Conversion
        Steering Wheel Angle,                                        1,         7, 16,  SNM,  -2048 - 2047.9375 deg,    E = N * 0.0625

        """

        # Message example 
        # can_id = 0x1e5, dlc = 8, data = [0x44, 0xFB, 0xB8, 0x50, 0x00, 0x00, 0x02, 0x83], wait = 1)

        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        # Cruise and Speed Limiter Driver Selected Speed,
        steering_wheel_angle_repr = int(steering_wheel_angle / 0.0625)

        data[1] = ( ( (steering_wheel_angle_repr & 0xFF00) >> 8) & 0xFF ) | data[1]
        data[1] = ( (steering_wheel_angle_repr & 0xFF) & 0xFF ) | data[1]
 
        self._send_msg(CAN_MSG_ID_STEERING_ANGLE,data )

       


