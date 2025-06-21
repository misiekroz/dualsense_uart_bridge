import struct
import serial
import threading
from queue import Queue

import serial.tools
import serial.tools.list_ports

from SunflowerEnums import FrameCommand


class SunflowerFrame:
    def __init__(self):
        self.start_seq = [0xA5, 0xAA, 0xAA]  # example default values
        self.command = 0x00  # uint8_t
        self.data = 0x00000000  # uint32_t
        self.checksum = 0x00  # uint8_t

    def calculate_checksum(self):
        checksum = self.command
        checksum ^= self.data & 0xFF
        checksum ^= (self.data >> 8) & 0xFF
        checksum ^= (self.data >> 16) & 0xFF
        checksum ^= (self.data >> 24) & 0xFF
        return checksum & 0xFF

    def pack(self):
        self.checksum = self.calculate_checksum()
        frame_format = "<3B B I B"  # Little endian: 3 uint8, 1 uint8, 1 uint32, 1 uint8
        packed_frame = struct.pack(
            frame_format,
            self.start_seq[0],
            self.start_seq[1],
            self.start_seq[2],
            self.command,
            self.data,
            self.checksum,
        )
        return packed_frame

    @classmethod
    def unpack(cls, received_bytes):
        frame_format = "<3B B I B"
        if len(received_bytes) != struct.calcsize(frame_format):
            raise ValueError("Invalid frame size")

        unpacked_data = struct.unpack(frame_format, received_bytes)
        frame = cls()
        frame.start_seq = list(unpacked_data[0:3])
        frame.command = unpacked_data[3]
        frame.data = unpacked_data[4]
        frame.checksum = unpacked_data[5]

        if frame.checksum != frame.calculate_checksum():
            raise ValueError("Checksum mismatch")

        return frame

    def __str__(self):
        enum_command = FrameCommand(self.command)
        if enum_command == FrameCommand.ERROR:
            return f"ERROR: {UartErrors(self.data)}; checksum: {self.checksum}"
        else:
            return (
                f"Command: {enum_command}; data: {self.data}; checksum: {self.checksum}"
            )


class SerialService:
    def __init__(self):
        self.serial = None
        self.receive_thread = None
        self.running = False
        self.receive_queue = Queue()

    def start_serial(self, port_name, baudrate):
        self.serial = serial.Serial(
            port=port_name,
            baudrate=baudrate,
            timeout=1,
            parity="N",
            stopbits=1,
            bytesize=8,
        )
        if not self.serial.is_open:
            self.serial.open()
            self.serial.write(bytearray([30, 30, 30]))
        self.running = True
        self.receive_thread = threading.Thread(target=self._read_serial, daemon=True)
        self.receive_thread.start()

    def close_serial(self):
        self.running = False
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join()
        if self.serial and self.serial.is_open:
            self.serial.close()

    def send_frame(self, frame: SunflowerFrame) -> SunflowerFrame:
        """
        Sends SunflowerFrame on active serial connection and waits for a response frame.

        Args:
            frame (SunflowerFrame): frame that will be packed and sent

        Returns:
            SunflowerFrame: the received response frame
        """
        self.serial.write(frame.pack())
        # Wait and retrieve the response frame
        response = self.receive_queue.get(timeout=15)
        return response

    def _read_serial(self):
        buffer = bytearray()
        frame_size = struct.calcsize("<3B B I B")
        while self.running:
            if self.serial.in_waiting:
                # print("got byte")
                buffer.extend(self.serial.read(self.serial.in_waiting))

                while len(buffer) >= frame_size:
                    potential_frame = buffer[:frame_size]
                    try:
                        received_frame = SunflowerFrame.unpack(potential_frame)
                        self.receive_queue.put(received_frame)
                        # print(buffer[frame_size:])
                        buffer = buffer[frame_size:]  # Remove processed frame
                    except ValueError:
                        buffer.pop(0)  # Remove first byte to resync frame

    def receive(self):
        """
        Retrieves unsolicited or asynchronously received data frames.

        Returns:
            SunflowerFrame: the received frame if available, else None
        """
        if not self.receive_queue.empty():
            return self.receive_queue.get()
        return None

    @classmethod
    def get_ports(cls):
        return serial.tools.list_ports.comports(include_links=False)
