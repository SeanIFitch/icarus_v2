#include <iostream>
#include <libusb-1.0/libusb.h>
#include <vector>
#include <cstring>
#include "Di4108.h"

Di4108::Di4108() {
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