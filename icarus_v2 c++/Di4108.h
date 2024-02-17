#ifndef DI4108
#define DI4108

#include <iostream>
#include <libusb-1.0/libusb.h>
#include <vector>
#include <cstring>

class Di4108 {
public:
    Di4108();
    ~Di4108();

    void acquire();
    void setDIO(uint8_t value = 0b1111111);

private:
    bool findDevice();
    void setupDevice();
    void sendCommand(const std::string& command, bool checkEcho = true);
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

    static const uint16_t DI_4108_VENDOR_ID = 0x0683;
    static const uint16_t DI_4108_PRODUCT_ID = 0x4108;
};

// For testing purposes
int main() {
    Di4108 device;

    device.acquire();

    return 0;
}

#endif
