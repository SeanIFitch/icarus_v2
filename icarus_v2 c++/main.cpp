// main.cpp
#include "Di4108.h"
#include "DeviceConfiguration.h"
#include "DataBuffer.h"
#include "GUI.h"
#include "ControlClass.h"

int main() {
    // Create instances of necessary classes
    DeviceConfiguration deviceConfig;
    DeviceCommunication deviceComm(deviceConfig);
    DataBuffer dataBuffer(BufferSize);  // Provide an appropriate buffer size
    GUI gui;                             // Create only if needed
    ControlClass control(deviceComm, dataBuffer, gui);  // Adjust parameters as needed

    // Additional initialization code as required

    // Run the application
    control.startDataAcquisition();

    // Additional code for handling user interactions or running analysis modules

    // Cleanup and exit
    return 0;
}