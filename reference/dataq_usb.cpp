/*
 *   DATAQ_USB class, used for communicating with DATAQ Models like DI-2108P High
 *   Speed DAQ on a linux machine. Tested on ubuntu 18.04
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
#include <iomanip>
#include <chrono> // for timer control
#include <dataq_usb.h> // for DATAQ_USB Class
//#include <mutex> // for interlock multiple devices when open
#include <QSystemSemaphore> // for interlock between process, the instance Number in the attributes determine which is responsible to create it or not

using namespace std;


//default constructor
DATAQ_USB::DATAQ_USB() : DATAQ_BASE() // Calling Base first to initialize all variables
{
    ctx = NULL;
    dev_handle = NULL;
}

//***********************************************************************************************************************

//constructor with basic parameters
// number of channels, range of operation (applied to all channels), acquisition Mode, timeout(ms)
//
DATAQ_USB::DATAQ_USB(string dev_model, uint32_t timeout_ms, string serialNumber) :
  DATAQ_BASE (dev_model, timeout_ms, serialNumber) // Calling Base first to initialize all variables
{
   ctx = NULL;
   dev_handle = NULL;

}

//***********************************************************************************************************************
// Discovery, connect and initialize to the DI-DATAQ device by USB
bool DATAQ_USB::connect()
{
  libusb_device **devs; //pointer to pointer of device, used to retrieve a list of devices

  ctx = NULL; //a libusb session

  dev_handle = NULL; // connection handle

  int r; //for return values

  r = libusb_init(&ctx); //initialize the library for the session we just declared
  if(r < 0) {
    cout<<"[ERROR] Init LibUSB Error "<<r<<endl; //there was an error
     return false;
  }
  libusb_set_debug(ctx, 3); //set verbosity level to 3, as suggested in the documentation
  
   ssize_t  cnt = libusb_get_device_list(ctx, &devs); //get the list of devices
  if(cnt < 0) {
    cout<<"[ERROR] LibUSB Get Device Error"<<endl; //there was an error
    return false;
  }
  if (isDebugging())
   cout<<"[INFO] Devices listed: "<< cnt << endl;
  
  // Added global SystemSemaphore as interlock to avoid conflict when multiple devices attempted to open at same time
  // The System Semaphore 'discovery' it is used for sync all process, where only one can do discovery at a time
  QSystemSemaphore *sem;

  // open the semaphore, if it is not created it will and sync with other process in First In First Out
  // open the semaphore

  sem = new QSystemSemaphore ("discovery", 1, QSystemSemaphore::Open); // Only enable 1 resource

  // Global inter-process mutex with acquire()
  sem->acquire();

  // Show devices list
  for (int idx =0; idx < cnt; idx++)
  {
     libusb_device *device = devs[idx];
     libusb_device_descriptor desc ={0};


     int rc = libusb_get_device_descriptor(device, &desc);
     if (rc ==0)
     {
//       cout << "[ERROR] Error getting description" << endl;
     }

     cout << "[INFO] Vendor: " << desc.idVendor << " Device: " << desc.idProduct << endl;

     if ( (desc.idVendor ==  config.vidLibUSB) && (desc.idProduct == config.pidLibUSB))
     {
       if (isDebugging())
       {
        cout << "[INFO] Found model " << config.modelName << endl;
        cout << "[INFO] Vendor ID: " << std::hex << desc.idVendor << " Product ID: " << std::hex << desc.idProduct << " Address " <<  std::dec << (int) libusb_get_device_address(device)
             << " Serial Index: " << (int) desc.iSerialNumber << endl;
        cout << std::dec << endl;
       }

       if (!serialNum.empty()) // Checking by Serial number also
       {
         // Check the Serial Number, this is only available if it is not collecting
         libusb_device_handle *handle;

         int error = libusb_open (device, &handle);

            if (error != 0)
             cout << "[ERROR] Failed when attempt to open for checking serial, maybe it is used already" << endl;
            else
             {
                dev_handle = handle; //used for the following commands stopScan and getSerialNum

                isInit=true; //initialization successful to be able use the commands

                stopScan(); // make sure it stop first just in case was scaning before and interrupted, it will clear also any previous communication

                string serial = getSerialNum();

                cout << "Discovery Serial Number: " << serial << endl; // change in 1-8

                if (serial == serialNum)
                {
                  cout << "[INFO] Found Serial Number " << serial << endl;
                  break;
                }
                else
                 {
                    isInit=false; // reset initialization flag

                   libusb_close(handle);
                   cout << "[WARN] Device with serial " << serial << "dropped, didn't match" << endl;
                 }
               } // no error opening handle

         } // checking serial number
       } // if device matched

    } // loop for all devices

  sem->release(); // Release the interlock

  delete sem; // release memory

  if (serialNum.empty())
    dev_handle = libusb_open_device_with_vid_pid(ctx, config.vidLibUSB, config.pidLibUSB);

  if(dev_handle == NULL){
    cout<<"[ERROR] Cannot find device "<< config.modelName << endl;
     return false;
  }
  else
    if (isDebugging())
     cout<<"[INFO] Device " << config.modelName << " Opened"<<endl;

  libusb_free_device_list(devs, 1); //free the list, unref the devices in it
  
  if(libusb_kernel_driver_active(dev_handle, 0) == 1) { //find out if kernel driver is attached
    cout<<"[WARN] Kernel Driver Active"<<endl;
    if(libusb_detach_kernel_driver(dev_handle, 0) == 0) //detach it
      cout<<"[WARN] Kernel Driver Detached!"<<endl;
  }
  r = libusb_claim_interface(dev_handle, 0); //claim interface 0
  if(r < 0) {
    cout<<"[ERROR] Cannot Claim Interface"<<endl;
    return false;
  }

  if (isDebugging())
   cout<<"[INFO] Claimed USB Interface"<<endl;
  
 isInit=true; //initialization successful

 // See DI-2108-P protocol document
 stopScan(); // make sure it stop first just in case was scaning before and interrupted, it will clear also any previous communication

 setupCommParam(); // setup main communication parameters

 if (isDebugging())
  cout<<"[INFO] Initialization USB Interface Done"<<endl;

 return true;
}

//***********************************************************************************************************************

void DATAQ_USB::disconnect()
{
  if(!isInit) return; //don't close if the device isn't initialized
  int r;

  r = libusb_release_interface(dev_handle, 0); //release the claimed interface
  if(r!=0) {
    cout<<"[ERROR] Cannot Release Interface"<<endl;
    return;
  }

  if (isDebugging())
   cout<<"[INFO] Released Interface"<<endl;

  libusb_close(dev_handle); //close the device we opened
  libusb_exit(ctx); //needs to be called to end the session
  isInit=false;

}

//***********************************************************************************************************************

void DATAQ_USB::reset()
{
  if(!isInit) return;  //don't try to reset if the device isn't initialized
  libusb_reset_device(dev_handle);

  sleep(1);

  isRun=false;
  isInit=false;
}

//***********************************************************************************************************************

string DATAQ_USB::sendMessage(string message)
{
  if(!isInit){
    //can't send a message if the device isn't initialized
    cout << "[ERROR] Cannot Send Message " << message << " not initialized yet " << endl;
    return "error";
  }

  if (isDebugging())
   cout << "[INFO] Send Message: " << message << endl;

  int r; //for return values

  string error = "error";

  message = message+"\r";
  

  unsigned char sent[50];
  strcpy((char*) sent, message.c_str());  //convert the message to a char*
  memset (received, 0, sizeof(received));

  int actual; //used to find out how many bytes were written

  //send the message
  // Doesn't like a very short timeout
  r = libusb_bulk_transfer(dev_handle, (1 | LIBUSB_ENDPOINT_OUT), sent, sizeof(sent), &actual, timeoutms); // (1 | LIBUSB_ENDPOINT_OUT)

  if(r == 0 && actual == sizeof(sent)){
    sleep(0.1);

    if (isDebugging())
     cout << "[INFO] Sent message Ok" << endl;

    //receive the message
    if (message == "start 0\r")  // the start 0 command doesn't has response, doesn't need read response after
     return "ok";
    else
     {
//       cout << "[INFO] Read feedback message" << endl;
       r = libusb_bulk_transfer(dev_handle, (1 | LIBUSB_ENDPOINT_IN), received, sizeof(received), &actual, timeoutms); // (1 | LIBUSB_ENDPOINT_IN)
     }
    
  }else {
    cout<<"[ERROR] Send Error"<<endl;
    return error;
  } 
  std::string sName(reinterpret_cast<char*>(received));  //convert recieved message into a string

//  cout << "[INFO] Respond message: " << sName << endl;

  return sName;


}

//***********************************************************************************************************************
 // Read raw data from device and put into the received
int DATAQ_USB::readBuffer ( unsigned char *buffer, uint32_t limit, uint32_t timeoutms)
{
    //read data from the device
    //the buffer received size define the limit for the packages out from the device, has to be as quickly as possible depend on sample rate
    //If the sample rate is too fast this process need to be done very fast also, otherwise we can get an error from the device
    // When the device got an error, it is better power cycle to reset because after the reading could be off

    // The limit has to be a multiple of nChannels to make sure can read the completed set for all channels available
    // This is to avoid offset or shift in the channel reading for next

    int actual =0;

     if (isDebugging())
      cout << "[WARN] Reading Buffer, limit: " << limit << endl;
    int r = libusb_bulk_transfer(dev_handle, (1 | LIBUSB_ENDPOINT_IN), buffer, limit, &actual, timeoutms); //

    if (isDebugging())
     cout << "[WARN] Read- Total Bytes: " << actual << endl;

    return actual;
}

//***********************************************************************************************************************

 // Clear Input from Device to ensure there is no data buffered from previous commands
void DATAQ_USB::clearInput()
{
   if (isDebugging())
    cout << "[WARN] Clearing Buffer.." << endl;

    int actual, r; //used to find out how many bytes were read

    //send the message
    do
    {
       r = libusb_bulk_transfer(dev_handle, (1 | LIBUSB_ENDPOINT_IN), received, sizeof(received), &actual, timeoutms);
    }
    while ( (r==0) && (actual >0));
}
