#include <iostream>
#include <libusb-1.0/libusb.h>
#include <vector>
#include <cstring>

class Di4108 {
public:
    Di4108();
    ~Di4108();

    void acquire();

private:
    bool findDevice();
    void setupDevice();
    void sendCommand(const std::string& command, bool checkEcho = true);
    void setDIO(uint8_t value = 0b1111111);
    std::vector<uint8_t> read(size_t size);
    void ADCtoPressure(const std::vector<int16_t>& analogData, std::vector<double>& pressures);
    void closeDevice();
    void stop();

    bool acquiring;
    unsigned int sampleRate;
    size_t usbBuffer;
    libusb_device_handle* device;
    libusb_endpoint_descriptor endpointIn;
    libusb_endpoint_descriptor endpointOut;
    size_t pointsToRead;
    size_t channelsToRead;
    size_t bytesToRead;
    std::vector<double> pressureSensorOffset;

    static const uint16_t DI_4108_VENDOR_ID = 0x0683;
    static const uint16_t DI_4108_PRODUCT_ID = 0x4108;
};

Di4108::Di4108() : acquiring(true), sampleRate(0), usbBuffer(0), device(nullptr), pointsToRead(0), channelsToRead(0), bytesToRead(0) {
    if (!findDevice()) {
        std::cerr << "USB device not found. Please ensure the device is connected." << std::endl;
        exit(1);
    }

    setupDevice();
}

Di4108::~Di4108() {
    stop();
    closeDevice();
}

bool Di4108::findDevice() {
    libusb_device** devices;
    ssize_t count = libusb_get_device_list(nullptr, &devices);

    if (count < 0) {
        std::cerr << "Error getting device list" << std::endl;
        return false;
    }

    for (ssize_t i = 0; i < count; ++i) {
        libusb_device* dev = devices[i];
        libusb_device_descriptor desc;

        if (libusb_get_device_descriptor(dev, &desc) == 0 &&
            desc.idVendor == DI_4108_VENDOR_ID &&
            desc.idProduct == DI_4108_PRODUCT_ID) {

            int r = libusb_open(dev, &device);
            if (r == 0) {
                libusb_free_device_list(devices, 1);
                return true;
            }
        }
    }

    libusb_free_device_list(devices, 1);
    std::cerr << "USB device not found. Please ensure the device is connected." << std::endl;
    return false;
}

void Di4108::setupDevice() {
    // Implement the device setup logic here using libusb functions
    // ...

    // Example: Set configuration, claim interface, etc.
    libusb_set_configuration(device, 1);
    libusb_claim_interface(device, 0);
}

// Implement the remaining member functions...

int main() {
    Di4108 device;

    device.acquire();

    return 0;
}