from time import sleep, time


# DIGITAL
# CH0: high pressure pump
# CH1: depressurize valve
# CH2: pressurize valve
# CH3: spare
# CH4: log
# CH5: spare
# CH6: spare

class PulseGenerator():
    def __init__(self, device, pressurize_width = 5, depressurize_width = 5) -> None:
        self.device = device

        # duration to hold valves open in ms
        self.pressurize_width = pressurize_width
        self.depressurize_width = depressurize_width


    def pressurize(self):
        self._pulse_low(2, self.pressurize_width)


    def depressurize(self):
        self._pulse_low(1, self.depressurize_width)


    # Sets channel low for duration milliseconds
    # Raises RuntimeError if channel is already low
    def _pulse_low(self, channel, duration):
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
        self.device.set_DIO(current_dio ^ channel_bit) # bitwise XOR

        # Sleep for remaining time
        time_elapsed = time() - current_time
        duration_sec = float(duration) / 1000
        remaining_time = duration_sec - time_elapsed
        sleep(remaining_time)

        # Reset to original DIO
        self.device.set_DIO(current_dio)


    # Sets channel low
    # Raises RuntimeError if channel is already low
    def _set_low(self, channel):
        # int representing the current state of dio
        current_dio = self.device.get_current_dio()
        # binary representation of channel to pulse
        channel_bit = 2 ** channel

        # Make sure the channel we are setting starts high.
        if not current_dio & channel_bit: # bitwise AND
            raise RuntimeError(f"Error: setting low digital channel {channel} which is already low.")

        # set low
        self.device.set_dio(current_dio ^ channel_bit) # bitwise XOR


    # Sets channel high
    # Raises RuntimeError if channel is already high
    def _set_high(self, channel):
        # int representing the current state of dio
        current_dio = self.device.get_current_dio()
        # binary representation of channel to pulse
        channel_bit = 2 ** channel

        # Make sure the channel we are setting starts low.
        if current_dio & channel_bit: # bitwise AND
            raise RuntimeError(f"Error: setting high digital channel {channel} which is already high.")

        # set high
        self.device.set_dio(current_dio | channel_bit) # bitwise OR
