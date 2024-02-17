import sys
import usb.core
import numpy as np
import traceback


#device information
DI_4108_VENDOR_ID = 0x0683
DI_4108_PRODUCT_ID = 0x4108


class Di4108_USB():
    def __init__(self) -> None:
        """
        Initializes a di_4108 object and sets up device for reading.
        """
        self.acquiring = True
        self.sample_rate = 0
        self.usb_buff = 0
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None
        self.points_to_read = 0
        self.channels_to_read = 0
        self.bytes_to_read = 0
        self.pressure_sensor_offset = None

        if not self._find_device():
            sys.exit(1)

        self._setup_device()


    def __enter__(self):
        """
        Enters the context. Returns the device instance.
        """
        return self
    

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exits the context. Closes the USB device.
        """
        self.stop()
        self.close_device()


    def _find_device(self):
        """
        Finds the usb device.
        
        :return: True if connection is successful, False otherwise.
        """
        try:
            # Find the USB device
            self.device = usb.core.find(idVendor=DI_4108_VENDOR_ID, idProduct=DI_4108_PRODUCT_ID)
            if self.device is None:
                print("USB device not found. Please ensure the device is connected.")
                return False
            else:
                # Attempt to read from the device as a simple permission test
                cfg = self.device.get_active_configuration()
                intf = cfg[(0,0)]
                ep = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
                )                
                assert ep is not None
                # If no exception was raised, assume permissions are adequate
                return True
        except usb.core.USBError as e:
            if e.errno == 13:
                print("Insufficient permissions to access the USB device.")
                print("Please set up udev rules by runnning ../setup/install_udev_rules.sh.")
                return False
            else:
                traceback.print_exc() 
                return False


    def _setup_device(self):
        # Reinitialize device
        self.device.reset()
        # Set the first configuration as active
        self.device.set_configuration()

        # Get and setup endpoints
        cfg = self.device.get_active_configuration()
        intf = cfg[(0,0)]
        match_out = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        match_in = lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
        self.endpoint_out = usb.util.find_descriptor(intf, custom_match=match_out)
        self.endpoint_in = usb.util.find_descriptor(intf, custom_match=match_in)
        self.endpoint_out.wMaxPacketSize = 7200000
        self.endpoint_in.wMaxPacketSize = 7200000
        self.endpoint_in.bmAttributes = 1
        self.endpoint_in.bInterval = 100
        self.usb_buff = int(self.endpoint_in.wMaxPacketSize/100)

        # Stop in case device was left running
        self.stop()
        # Set all dio ports to switches
        self._send_cmd("endo 127")
        # Define binary output mode
        self._send_cmd("encode 0")
        # Set packet size = 1024 bytes
        self._send_cmd("ps 6")
        # Set all channels to CIC filtering
        self._send_cmd("filter * 1")

        # Set slist which is order of channels to sample. See device protocol for more info.
        # Prior documentation said this was:
        #   A0 at +-5V, A1 at +-5V, A2 at +-.2V, A3 at +-.2V, A4 at +-.2V, A5 at +-.2V, A6 at +-5V, A7 at +-5V, digital input
        # This is actually A0-A7 at +-10V, Digital
        slist = ["0 0","1 1","2 2","3 3","4 4","5 5","6 6","7 7","8 8"]
        for i in slist:
            self._send_cmd("slist " + i)

        # Sample rate (Hz) = 60,000,000 / (srate * dec * deca)
        # Device reports 1 value per (dec * deca) readings. (default is by CIC filtering)
        srate = 3000
        dec = 5
        deca = 1
        self.sample_rate = 60000000 / (srate * dec * deca)
        self._send_cmd('srate ' + str(srate))
        self._send_cmd('dec ' + str(dec))
        self._send_cmd('deca ' + str(deca))

        # Calculate number of bytes to read
        self.points_to_read = 64
        self.channels_to_read = len(slist)
        # 2 bytes per channel
        self.bytes_to_read = self.channels_to_read * 2 * self.points_to_read

        #readings for pressure sensors at atmospheric pressure
        self.pressure_sensor_offset = np.asarray([69.5595, 65.562, 68.881375, 84.2195, 86.96075, 17.248, 17.322, 0])


    def _send_cmd(self, command, encoding='utf-8', check_echo = True):
        """
        Sends a command to the USB device.

        :param command: The command to be sent.
        """
        try:
            self.device.write(self.endpoint_out, (command+'\r').encode(encoding))
        except:
            traceback.print_exc()
        
        # Expect a response unless the device is currently reading
        # Not reading a response can leave the response in the buffer which can cause data processing issues or overflow
        if not self.acquiring:
            response = self._read()
            if response is not None:
                response = bytes(response).decode(encoding, errors='ignore').strip('\0')
            expected_response = command+'\r'
            if check_echo and response != expected_response:
                print(f"Error sending command: Response \"{expected_response.strip()}\" expected but \"{response.strip()}\" received.")


    def set_DIO(self, value = 0b1111111):
        """
        Sets digital input/output state.

        :param value: States to set.
        """
        self._send_cmd("dout " + str(int(value)))


    def _read(self, size = None):
        if size == None:
            size = self.usb_buff
        try:
            data = self.device.read(self.endpoint_in, size, timeout=5000)
            return data
        except:
            traceback.print_exc() 
            return None


    def acquire(self, queue):
        # Start reading
        self.set_DIO()
        self.acquiring = True
        self._send_cmd('start')
        while self.acquiring:
            data = self._read(self.bytes_to_read)
            if data is None:
                break

            analog = np.reshape(np.frombuffer(data, dtype=np.int16), (self.points_to_read, self.channels_to_read))[:, :-1]
            pressures = self._ADC_to_pressure(analog)
            print(type(pressures))
            # Digital is last channel read, and only the 2nd byte is necessary
            digital = np.reshape(np.asarray(data), (self.points_to_read, self.channels_to_read*2))[:,-1]
            print(type(digital))


    def _ADC_to_pressure(self, analog_data):
        # Convert analog data to voltage
        range = 20
        volts = range * analog_data.astype(np.float64) / 32768

        pressure = volts - self.pressure_sensor_offset
        return pressure


    def close_device(self):
        """
        Closes the USB device.
        """
        if self.device is not None:
            usb.util.dispose_resources(self.device)


    def stop(self):
        """
        Orderly stop of the device code.
        - stops data acquisiion
        - erases all data from USB buffers
        - set digital IO to all high
        - closes usb port connection
        """
        self.acquiring = False
        self._send_cmd("stop", check_echo=False)
        # Turn all valves off
        self.set_DIO(0b1111111)


# Testing
def main():
    with Di4108() as device_instance:
        device_instance.acquire(None)


if __name__ == "__main__":
    main()
