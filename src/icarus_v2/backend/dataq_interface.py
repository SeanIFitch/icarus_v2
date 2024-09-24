import usb.core
from array import array
from threading import Lock


# Device information
DI_4108_VENDOR_ID = 0x0683
DI_4108_PRODUCT_ID = 0x4108


# Interface to the Di4108 USB device, capable of reading from its DIO and Analog channels and sending instructions.
class DataqInterface:
    def __init__(self) -> None:
        """
        Initializes a DataqInterface object and sets up device for reading.
        """
        self.stop_lock = Lock()  # Used to make sure you do not stop the device while reading

        self.device = None
        self.endpoint_out = None
        self.endpoint_in = None
        self.usb_buff = None
        self.sample_rate = None
        self.points_to_read = None
        self.channels_to_read = None
        self.bytes_to_read = None
        self.current_dio = None
        self.acquiring = None

        self.find_device()
        self.setup_device()

    def find_device(self):
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
                intf = cfg[(0, 0)]
                ep = usb.util.find_descriptor(
                    intf,
                    custom_match=lambda err: usb.util.endpoint_direction(err.bEndpointAddress) == usb.util.ENDPOINT_IN
                )                
                assert ep is not None
                # If no exception was raised, assume permissions are adequate
                return True
        except usb.core.USBError as e:
            if e.errno == 13:
                raise RuntimeError("Insufficient permissions to access the USB device. " +
                                   "Please set up udev rules by running setup/install_udev_rules.sh.")
            else:
                raise RuntimeError(e)

    def setup_device(self):
        # Reinitialize device
        self.device.reset()
        # Set the first configuration as active
        self.device.set_configuration()

        # Get and setup endpoints
        cfg = self.device.get_active_configuration()
        intf = cfg[(0, 0)]
        def match_out(e): return usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        def match_in(e): return usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN
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
        self.send_cmd("endo 127")
        # Define binary output mode
        self.send_cmd("encode 0")
        # Set packet size = 1024 bytes
        self.send_cmd("ps 6")
        # Set all channels to CIC filtering
        self.send_cmd("filter * 1")

        # Set slist which is order of channels to sample. See device protocol for more info.
        # This is A0-A6 at +-10V, Digital
        slist = ["0 0", "1 1", "2 2", "3 3", "4 4", "5 5", "6 6", "7 8"]
        for i in slist:
            self.send_cmd("slist " + i)

        # Sample rate (Hz) = 60,000,000 / (srate * dec * deca)
        # Device reports 1 value per (dec * deca) readings. (default is by CIC filtering)
        srate = 3000
        dec = 5
        self.sample_rate = 60000000 / (srate * dec)
        self.send_cmd('srate ' + str(srate))
        self.send_cmd('dec ' + str(dec))

        # Calculate number of bytes to read
        self.points_to_read = 64
        self.channels_to_read = len(slist)
        # 2 bytes per channel
        self.bytes_to_read = self.channels_to_read * 2 * self.points_to_read

    def send_cmd(self, command, check_echo=True):
        """
        Sends a command to the USB device.

        :param command: The command to be sent.
        :param check_echo: Whether to compare the return of the device. Do not use while acquiring data.
        """
        self.device.write(self.endpoint_out, (command+'\r').encode('utf-8'))

        # Expect a response unless the device is currently reading
        # Not reading a response can leave the response in the buffer which can cause data processing issues or overflow
        if not self.acquiring:
            response = self.read()
            if response is not None:
                response = bytes(response).decode('utf-8', errors='ignore').strip('\0')
            expected_response = command+'\r'
            if check_echo and response != expected_response:
                print(f"Error sending command: Response \"{expected_response.strip()}\"" +
                      f"expected but \"{response.strip()}\" received.")

    # Default value - pump off, valves closed, not logging
    def set_dio(self, value=0b1111111, check_echo=True):
        """
        Sets digital input/output state.

        :param value: States to set.
        :param check_echo: Whether to compare the return of the device. Do not use while acquiring data.
        """
        self.current_dio = int(value)
        self.send_cmd("dout " + str(int(value)), check_echo=check_echo)

    def read(self, size=None, timeout=2000):
        if size is None:
            size = self.usb_buff
        data = self.device.read(self.endpoint_in, size, timeout=timeout)
        return data

    def start_scan(self):
        # Prevent stopping device while reading
        self.stop_lock.acquire()
        # Start reading
        self.acquiring = True

        self.send_cmd('start', check_echo=False)

    def end_scan(self):
        if self.stop_lock.locked():
            self.stop_lock.release()

    def read_data(self):
        data = self.read(self.bytes_to_read)
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
            self.send_cmd("stop", check_echo=False)
        # Turn all valves off
        self.set_dio(0b1111111, check_echo=False)

    def get_current_dio(self):
        return self.current_dio
