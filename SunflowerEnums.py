from enum import Enum, auto


class TrackerStates(Enum):
    IDLE = 0
    TRACKING = 1
    HOMING = 2
    NIGHT = 3
    STOP = 4
    WARNING = 5
    ERROR = 6
    UNKNOWN = 7


class TrackingMode(Enum):
    UART_TRACKING = 1
    FULL_SENSOR_TRACKING = 2
    TIMED_TRACKING = 3
    HYBRID_TRACKING = 4
    AI_TRACKING = 5


class FrameCommand(Enum):
    OK = 0  # confirmation or PING command
    STOP = auto()  # sets the device into STOP state
    RESET_STOP = (
        auto()
    )  # attempts to reset stop (valid only if physical STOP is not pressed)
    GET_STATE = auto()  # gets current device state (IDLE, STOP, ERROR itp)
    HALT_TRACKING = auto()  # halts tracking to allow full configuration of setpoint
    START_TRACKING = auto()  # starts tracking after halt
    HOME = auto()  # starts homing sequence (not implemented yet)
    SET_TRACKING_MODE = (
        auto()
    )  # sets tracking mode. Device will keep responding  to UART frames, but will not  react to motor commands
    SET_MOTOR_R = auto()  # target position for motor R
    SET_MOTOR_L = auto()  # target position for motor L
    GET_MOTOR_POS_R = auto()  # gets current position of motor R
    GET_MOTOR_POS_L = auto()  # gets current position of motor L
    GET_MOTOR_TARGET_R = auto()  # gets current target of right motor
    GET_MOTOR_TARGET_L = auto()  # gets current target of left motor
    GET_MOTORS_MOVING = auto()  # gets information if any motor is moving
    GET_IS_HOMING = auto()  # gets information if tracking controller is homing
    GET_READING_1 = auto()  # gets reading from photoresisstor 1
    GET_READING_2 = auto()  # gets reading from photoresisstor 2
    GET_READING_3 = auto()  # gets reading from photoresisstor 3
    GET_READING_4 = auto()  # gets reading from photoresisstor 4
    ERROR = 0xFF  # error - either in interpreting the CMD, execution or other


class UartOKMessages(Enum):
    OK = 0x00  # standard OK, no meaning
    MOTORS_STOPPED = 0x01  # motors stopped
    HOMING_FINISHED = 0x02  # homing stopped


class UartErrors(Enum):
    UNKNOWN = 0x00
    NOT_IMPLEMENTED = auto()
    CHECKSUM_MISMATCH = auto()
    MOTORS_OUT_OF_RAGE = auto()
    SAFETY_BUTTON_NOT_RELEASED = auto()
