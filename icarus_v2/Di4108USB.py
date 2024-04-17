import usb.core
from array import array
from threading import Lock


#device information
DI_4108_VENDOR_ID = 0x0683
DI_4108_PRODUCT_ID = 0x4108


class Di4108USB():
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
        self.current_dio = None

        self.stop_lock = Lock() # Used to make sure you do not stop the device while reading

        self._find_device()
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
        self.end_scan()
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
                raise RuntimeError("USB device not found. Please ensure the device is connected.")
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
                raise  RuntimeError("""Insufficient permissions to access the USB device.
                                    Please set up udev rules by runnning ../setup/install_udev_rules.sh.""")
            else:
                raise RuntimeError


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
        # This is actually A0-A6 at +-10V, Digital
        slist = ["0 0","1 1","2 2","3 3","4 4","5 5","6 6","7 8"]
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


    def _send_cmd(self, command, encoding='utf-8', check_echo = True):
        """
        Sends a command to the USB device.

        :param command: The command to be sent.
        """
        try:
            self.device.write(self.endpoint_out, (command+'\r').encode(encoding))
        except:
            raise RuntimeError("Device write failed.")
        
        # Expect a response unless the device is currently reading
        # Not reading a response can leave the response in the buffer which can cause data processing issues or overflow
        if not self.acquiring:
            response = self._read()
            if response is not None:
                response = bytes(response).decode(encoding, errors='ignore').strip('\0')
            expected_response = command+'\r'
            if check_echo and response != expected_response:
                print(f"Error sending command: Response \"{expected_response.strip()}\" expected but \"{response.strip()}\" received.")


    # Default value - pump off, valves open, not logging
    def set_DIO(self, value = 0b1111000, check_echo = True):
        """
        Sets digital input/output state.

        :param value: States to set.
        """
        self.current_dio = int(value)
        self._send_cmd("dout " + str(int(value)), check_echo=check_echo)


    def _read(self, size = None, timeout = 2000):
        if size == None:
            size = self.usb_buff
        data = self.device.read(self.endpoint_in, size, timeout=timeout)
        return data


    def start_scan(self):
        # Prevent stopping device while reading
        self.stop_lock.acquire()
        # Start reading
        self.acquiring = True

        self._send_cmd('start')


    def end_scan(self):
        if self.stop_lock.locked():
            self.stop_lock.release()


    def read_data(self):
        data = self._read(self.bytes_to_read)
        if data is None:
            return None

        # Check for buffer overflow
        # Represents a received value of "stop 01".
        stop_01_array = array('B', [115, 116, 111, 112, 32, 48, 49, 13, 0])
        if stop_01_array == data[-9:]:
            raise RuntimeError("Error: Buffer overflow on physical device. Scanning Stopped.")

        return data


    def close_device(self):
        """
        Closes the USB device.
        """
        if self.device is not None:
            usb.util.dispose_resources(self.device)


    def stop(self):
        """
        - stops data acquisiion
        - set digital IO to all high
        """
        self.acquiring = False # Signals to stop acquiring
        with self.stop_lock:
            self._send_cmd("stop", check_echo=False)
        # Turn all valves off
        self.set_DIO(0b1111000, check_echo = False)


    def get_current_dio(self):
        return self.current_dio
