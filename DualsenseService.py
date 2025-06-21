import datetime
from dualsense_controller import DualSenseController

from SunflowerEnums import TrackerStates, TrackingMode


class DualsenseService:
    def __init__(self):
        self.stop_program = False
        self.controller_is_connected = False
        self.controller = None
        self.is_L1_pressed = False
        self.left_target = 0
        self.right_target = 0
        self.safety_trigger_callback = None
        self.safety_release_callback = None
        self.homing_callback = None
        self.last_triangle_time = None

    def start_controller(self):
        print(DualSenseController.enumerate_devices())
        self.controller = DualSenseController()
        self.controller.activate()
        self.color = "red"

        if not self.controller.is_active:
            return

        self.controller_is_connected = True
        self.controller.left_stick.on_change(self.on_stick_change)

        self.controller.btn_ps.on_down(self.on_ps_btn_pressed)
        self.controller.btn_cross.on_down(self.on_cross_btn_pressed)
        self.controller.btn_circle.on_down(self.on_circle_btn_pressed)
        self.controller.btn_triangle.on_down(self.on_triangle_button_pressed)
        self.controller.btn_triangle.on_up(self.on_triangle_button_release)

    # input handlers #

    def on_cross_btn_pressed(self):
        if self.safety_trigger_callback:
            self.safety_trigger_callback()

    def on_circle_btn_pressed(self):
        """
        Calls release safety, but only when r2 is pressed simultaneously
        """
        if self.controller.right_trigger.value >= 0.9:
            if self.safety_release_callback:
                self.safety_release_callback()
        else:
            print(
                f"safety not released, R2 not pressed. Value: {self.controller.right_trigger.value}"
            )

    def on_triangle_button_pressed(self):
        self.last_triangle_time = datetime.now()

    def on_triangle_button_release(self):
        if self.last_triangle_time:
            delta = datetime.now() - self.last_triangle_time

            if delta > datetime.timedelta(seconds=3) and self.homing_callback:
                self.homing_callback()
            
            self.last_triangle_time = None


    def on_ps_btn_pressed(self):
        print("PS button pressed, setting flag")
        self.stop_program = True

    def on_stick_change(self, JoyStick):
        """
        Calculates L and R values based on stick X and Y positions.
        """
        self.left_target, self.right_target = self.calculate_motor_speeds(
            JoyStick.x, JoyStick.y
        )
        print(f"Target R: {self.right_target} Target L: {self.left_target}, {JoyStick}")

    def on_error(self, error):
        print(f"Got DualSense error: {error}, returning")
        self.stop_program = True

    def calculate_motor_speeds(self, x, y, deadzone_width):
        """
        Using joystick X and Y values, calculates motor speeds

        Args:
            x: float value from -1 to 1
            y: float value from -1 to 1
        Returns:
            (left_motor_speed, right_motor_speed): float values in range -1:1
        """
        # ensure value is within <-1, 1> range
        left_motor_speed = max(-1, min(y + x, 1))
        right_motor_speed = max(-1, min(y - x, 1))

        # apply deadzone
        left_motor_speed = self.apply_deadzone(left_motor_speed, 0.4)
        right_motor_speed = self.apply_deadzone(right_motor_speed, 0.4)

        return left_motor_speed, right_motor_speed

    @classmethod
    def apply_deadzone(cls, value: float, deadzone_width: float) -> float:
        half_deadzone = abs(deadzone_width) / 2
        
        if -1*half_deadzone < deadzone_width < half_deadzone:
            return 0
        
        return value

    # output handlers #

    state_color_map = {
        TrackerStates.IDLE: (0, 0, 0),
        TrackerStates.WARNING: (255, 255, 0),
        TrackerStates.ERROR: (255, 0, 0),
        TrackerStates.TRACKING: (0, 255, 0),
        TrackerStates.STOP: (0, 0, 255),
    }

    def display_state(self, state: TrackerStates):
        """
        Sets the most important states as DualSense lightbar colors
        """
        if state in self.state_color_map:
            self.controller.lightbar.set_color(*self.state_color_map[state])

        else:
            self.controller.lightbar.set_color_white()

    def display_mode(self, state: TrackingMode):
        """
        Sets the most important states as DualSense lightbar colors
        """
        match state:
            case TrackingMode.UART_TRACKING:
                self.controller.player_leds.set_center()
            case TrackingMode.FULL_SENSOR_TRACKING:
                self.controller.player_leds.set_inner()
            case TrackingMode.TIMED_TRACKING:
                self.controller.player_leds.set_outer()
            case TrackingMode.HYBRID_TRACKING:
                self.controller.player_leds.set_center_and_outer()
            case TrackingMode.AI_TRACKING:
                self.controller.player_leds.set_off()

    def start_rumble(self):
        self.controller.left_rumble.set(200)
        self.controller.right_rumble.set(200)

    def stop_rumble(self):
        self.controller.left_rumble.set(0)
        self.controller.right_rumble.set(0)
