from PySide6.QtCore import QThread
from time import sleep, time


# DIGITAL
# CH0: high pressure pump
# CH1: depressurize valve
# CH2: pressurize valve
# CH3: spare
# CH4: log
# CH5: spare
# CH6: spare

class PulseGenerator(QThread):
    PUMP = 0
    DEPRESSURIZE = 1
    PRESSURIZE = 2
    LOG = 4

    def __init__(self, config_manager) -> None:
        super().__init__()

        self.device = None
        self.config_manager = config_manager

        # dictionary containing pressurize_width, depressurize_width, period_width, delay_width
        self.settings = config_manager.get_settings('timing_settings')
        self.config_manager.settings_updated.connect(self.update_settings)

        # Whether the device should be currently generating pulses
        self.pulsing = False

    def set_device(self, device):
        self.device = device

    # Pressurizes and depressurizes at regular intervals
    def run(self):
        self.pulsing = True
        while self.pulsing:
            # Make sure widths are not edited in the middle of a period.
            # Otherwise, this could cause sleeping for negative times.
            pressurize_width = self.settings["pressurize_width"]
            depressurize_width = self.settings["depressurize_width"]
            period_width = self.settings["period_width"]
            delay_width = self.settings["delay_width"]
            # Get time before setting DIO for more precise timing
            begin_time = time()

            self._pulse_low(self.DEPRESSURIZE, depressurize_width)
            if not self.no_hang_sleep(begin_time + delay_width):
                break

            self._pulse_low(self.PRESSURIZE, pressurize_width)
            if not self.no_hang_sleep(begin_time + period_width):
                break

    # Sleep until end_time, checking for self.pulsing frequently
    # Returns False if self.pulsing becomes false, true otherwise
    def no_hang_sleep(self, end_time, running_check_hz=10):
        remaining_time = end_time - time()
        while remaining_time >= 0:
            sleep_time = min(1 / running_check_hz, remaining_time)
            sleep(sleep_time)
            remaining_time = end_time - time()

            if not self.pulsing:
                return False
        return True

    def set_pressurize_low(self):
        self._set_low(self.PRESSURIZE)

    def set_pressurize_high(self):
        self._set_high(self.PRESSURIZE)

    def set_depressurize_low(self):
        self._set_low(self.DEPRESSURIZE)

    def set_depressurize_high(self):
        self._set_high(self.DEPRESSURIZE)

    def set_pump_low(self):
        self._set_low(self.PUMP)

    def set_pump_high(self):
        self._set_high(self.PUMP)

    def update_settings(self, key = 'timing_settings'):
        if key == 'timing_settings':
            self.settings = self.config_manager.get_settings(key)

    # Sets channel low for duration milliseconds
    # Raises RuntimeError if channel is already low
    def _pulse_low(self, channel, duration):
        if self.device is None:
            raise RuntimeError("Running PulseGenerator when device is not initialized")
        # int representing the current state of dio
        current_dio = self.device.get_current_dio()
        # binary representation of channel to pulse
        channel_bit = 2 ** channel

        # Make sure the channel we are pulsing starts high.
        if not current_dio & channel_bit: # bitwise AND
            raise RuntimeError(f"Error: pulsing low digital channel {channel} which is already low.")

        # Get time before setting DIO for more precise timing
        current_time = time()

        # Set specified channel low
        self.device.set_dio(current_dio ^ channel_bit) # bitwise XOR

        # Sleep for remaining time
        duration_sec = float(duration) / 1000
        time_elapsed = time() - current_time
        remaining_time = max(0, duration_sec - time_elapsed)
        sleep(remaining_time)

        # Reset to original DIO
        self.device.set_dio(current_dio)

    # Sets channel low
    # Raises RuntimeError if channel is already low
    def _set_low(self, channel):
        if self.device is None:
            raise RuntimeError("Running PulseGenerator when device is not initialized")
        # int representing the current state of dio
        current_dio = self.device.get_current_dio()
        # binary representation of channel to pulse
        channel_bit = 2 ** channel

        # Make sure the channel we are setting starts high.
        if not current_dio & channel_bit:  # bitwise AND
            raise RuntimeError(f"Error: setting low digital channel {channel} which is already low.")

        # set low
        self.device.set_dio(current_dio ^ channel_bit)  # bitwise XOR

    # Sets channel high
    # Raises RuntimeError if channel is already high
    def _set_high(self, channel):
        if self.device is None:
            raise RuntimeError("Running PulseGenerator when device is not initialized")
        # int representing the current state of dio
        current_dio = self.device.get_current_dio()
        # binary representation of channel to pulse
        channel_bit = 2 ** channel

        # Make sure the channel we are setting starts low.
        if current_dio & channel_bit:  # bitwise AND
            raise RuntimeError(f"Error: setting high digital channel {channel} which is already high.")

        # set high
        self.device.set_dio(current_dio | channel_bit)  # bitwise OR

    def quit(self):
        self.pulsing = False
