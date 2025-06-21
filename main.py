from time import sleep


from DualsenseService import DualsenseService
from SerialService import SerialService, SunflowerFrame
from SunflowerEnums import TrackerStates, TrackingMode, FrameCommand


class ProgramMain:
    def __init__(self):
        self.dualsense_service = None
        self.dualsense_service = DualsenseService()
        self.dualsense_service.start_controller()

        self.serial_service = SerialService()

    def user_configure(self) -> bool:
        print("Please select one of the COM ports")

        ports_list = self.serial_service.get_ports()

        for idx, port in enumerate(ports_list):
            print(f"[{idx}] {port}")

        port_num = int(input("Port: "))

        if port_num < 0 or port_num >= len(ports_list):
            print("Selected number is out of range")
            return False

        self.serial_service.start_serial(ports_list[port_num].name, 115200)
        
        self.dualsense_service.safety_trigger_callback = self.send_safety_stop
        self.dualsense_service.safety_release_callback = self.send_safety_release

        return True

    def loop(self):
        """
        Runs main loop that handles state updates from the device
        """
        positions = {
            FrameCommand.SET_MOTOR_L: 0,
            FrameCommand.SET_MOTOR_R: 0,
            FrameCommand.HALT_TRACKING: 0,
            FrameCommand.START_TRACKING: 0,
        }
        multiplier = 50

        try:
            while (
                not self.dualsense_service.stop_program
                and self.dualsense_service.controller_is_connected
            ):
                # get state and set the dualsense output accordingly
                frame = SunflowerFrame()
                frame.command = FrameCommand.GET_STATE.value

                response = self.serial_service.send_frame(frame)

                if FrameCommand(response.command) != FrameCommand.OK:
                    print(f"Yikes! Frame: {response}")
                    continue

                # print(f"Got frame: {response}")
                current_state = TrackerStates(response.data)
                self.dualsense_service.display_state(current_state)

                if current_state == TrackerStates.IDLE:
                    positions[FrameCommand.SET_MOTOR_L] += int(
                        multiplier * self.dualsense_service.left_target
                    )
                    positions[FrameCommand.SET_MOTOR_R] += int(
                        multiplier * self.dualsense_service.right_target
                    )

                    # trim values
                    for position in positions:
                        if positions[position] > 500:
                            positions[position] = 500
                        elif positions[position] < 0:
                            positions[position] = 0

                    for command in [
                        FrameCommand.HALT_TRACKING,
                        FrameCommand.SET_MOTOR_L,
                        FrameCommand.SET_MOTOR_R,
                        FrameCommand.START_TRACKING,
                    ]:

                        frame = SunflowerFrame()
                        frame.command = command.value
                        frame.data = positions[command]

                        response = self.serial_service.send_frame(frame)
                        if FrameCommand(response.command) != FrameCommand.OK:
                            self.dualsense_service.start_rumble()
                            sleep(2)
                            self.dualsense_service.stop_rumble()
                            break

                # sleep for 250 ms, may need changes
                sleep(0.25)
        except KeyboardInterrupt:
            pass
        self.serial_service.close_serial()

    def send_safety_stop(self):
        self.send_frame(FrameCommand.STOP)

    def send_safety_release(self):
        self.send_frame(FrameCommand.RESET_STOP, True)

    def send_homing(self):
        self.send_frame(FrameCommand.HOME, True)

    def send_frame(self, frame_command: FrameCommand, rumble_on_error) -> bool:
        frame = SunflowerFrame()
        frame.command = frame_command.value

        # response is not analyzed
        response = self.serial_service.send_frame(frame)
        bool_result = FrameCommand(response.command) == FrameCommand.OK 

        if rumble_on_error and not bool_result:
            self.dualsense_service.start_rumble()
            sleep(2)
            self.dualsense_service.stop_rumble()

        return bool_result

if __name__ == "__main__":
    main = ProgramMain()
    if main.user_configure():
        main.loop()
