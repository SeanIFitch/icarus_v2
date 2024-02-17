/*
 *   DATAQ_USB class, used for communicating with DATAQ Model DI-2108-P High
 *   Speed DAQ on a linux machine by USB (LibUSB mode). Tested on ubuntu 18.04
 *
 *   The C++ 11 or higher should be enable
 *
 *   Uses libusb to communicate with device.
 *
 *   Adapted from Sam de Jong
 *   Updated and improved by Reyan Valdes (ITG)
 *
 *   email: rvaldes@itgtec.com
 *   date: 4/21/2021
 */

// Ubuntu versions like 18.08 LTS include the libusb library
// but in case need install libusb-1.0-dev, just execute the following command:
// sudo apt-get install libusb-1.0-dev


// For the communication protocol was used two documents as reference from DATAQ:
// - Data Acquisition Communication Protocol.pdf
// - DI-2108-P manual.pdf
//

#include <iostream>
#include <stdio.h>
#include <string.h>
#include <sstream>
#include <unistd.h>
#include <vector>
#include </usr/include/libusb-1.0/libusb.h>  // handle communcation with the device
#include <dataq_base.h> // for the Abstract class (Base) to handle DATAQ Instruments

#ifndef DATAQ_USB_h
#define DATAQ_USB_h

using namespace std;

class DATAQ_USB: public DATAQ_BASE  // Inherited from DATAQ_BASE that implement the generic communication protocol
{
  
 public:

  DATAQ_USB();                   //empty constructor
  DATAQ_USB(string dev_model, uint32_t timeout_ms=2000, string serialNumber="");      //constructor with number of channels and measurement range (default: +/- 5VDC

  bool connect() override;     //initialize and connect to the DI-DATAQ device by USB
  void disconnect() override;          //close the interface to the DI_DATAQ

  void reset() override;  //reset the interface
  string sendMessage(string message) override;  //send a message to the DI-2108-P, return the response
  int readBuffer ( unsigned char *received, uint32_t limit, uint32_t timeoutms) override; // Read raw data from device and put into the received
  void clearInput() override;       // Clear Input Buffer from device to ensure it is new starting

 private:
  
  //libusb session
  libusb_context *ctx;
  
  //device handle
  libusb_device_handle *dev_handle;
  
};

#endif
