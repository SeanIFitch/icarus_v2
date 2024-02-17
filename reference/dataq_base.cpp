#include "dataq_base.h"

/*
 *   DATAQ_BASE class, used as Protocol Base Class
 *   to encapsulate main protocol operations, generic for all compatible devices
 *
 *   Created by Reyan Valdes (ITG)
 *
 *   email: rvaldes@itgtec.com
 *   date: 4/21/2021
 */

// For the communication protocol was used two documents as reference from DATAQ:
// - DI-2108-P manual.pdf
// - Data Acquisition Communication Protocol.pdf
//

#include <iostream>
#include <stdio.h>
#include <string.h>
#include <sstream>
#include <unistd.h>
#include <vector>
#include <iomanip>
#include <chrono> // for timer control
#include <bitset> // for bits operation
#include <dataq_base.h> // for DATAQ_BASE Class
#include <fstream> // to write on file
#include <iomanip> // for set precision


using namespace std;

//default constructor
DATAQ_BASE::DATAQ_BASE()
{
   // Init scan list
  initScanList();

  timeoutms = 2000; // default timeout

  initModelConfig(config);

  //set status booleans to false
  isRun=false;
  isRead=false;
  isInit=false;

}

//***********************************************************************************************************************

//constructor with basic parameters
// Device Model Name, timeout(ms)
//
DATAQ_BASE::DATAQ_BASE(string dev_model, uint32_t timeout_ms, string serialNumber)
{

  setModel (dev_model, timeout_ms);

  serialNum = serialNumber;

  //set status booleans to false
  isRun=false;
  isRead=false;
  isInit=false;
}

//***********************************************************************************************************************

// Set model and timeout, in case the empty constructor was called
// This function is useful when working with cyclic recording to make it easy

bool DATAQ_BASE::setModel(string dev_model, uint32_t timeout_ms)
{
    initModelConfig(config);

    config.modelName = dev_model;

    timeoutms = timeout_ms;

     // Init scan list
    initScanList();

    // Set the Product ID (PID) and Vendor ID (VID) based on the Device Model name
    return detDeviceConfig();
}

//***********************************************************************************************************************

// Set the Acquisition mode for one channel (1-8) or all channels (DI_ALL_AI_CHANNELS), acqMode: 0-Last point, 1- Average, 2-Maximum, 3-Minimum
// based on DI-2108-protocol.pdf, page 10.
// filter arg0 arg1
bool DATAQ_BASE::setAcqMode ()
{
   if ((!isInit)) return false; //don't do it if the device isn't initialized

   bool error = false;

   for (uint16_t i=0; i < scanList.size(); i++)
   {
    if (scanList[i].type == DI_CHANNEL_TYPE_AI)
    {
     string arg0 = to_string(scanList[i].number);
     string arg1 = to_string(scanList[i].acqMode);

     string resp = sendMessage("filter " + arg0 + " "+ arg1);  //Set filter (Acquisition Mode) for each analog channel defined in the scan list

     if (resp == "error") error = true;
    }
   }

   return !error;
}

//***********************************************************************************************************************

// Init model configuration parameters
void DATAQ_BASE::initModelConfig(tModelConfig &model)
 {
   model.modelName = "";
   model.modelID   = DI_MODEL_DI_NONE;
   model.pidLibUSB = 0;
   model.vidLibUSB = 0;
   model.srateMin  = 0;
   model.srateMax  = 0;
   model.decMin    = 0;
   model.decMax    = 0;
   model.decaMin   = 0;
   model.decaMax   = 0;
   model.aiMax     = 0;
   model.sampleRateMax =0;

   // init custom
   model.sampleRate =0;
   model.srate     = 0;
   model.dividend  = 0;
   model.dec       = 0;
   model.deca      = 0;
}

//***********************************************************************************************************************

// Get Model configuration parameters
void DATAQ_BASE::getModelConfig(tModelConfig &model)
{
  model = config;
}

//***********************************************************************************************************************

// Set the work mode: binary, ASCII, binary with date number (For future models, the DI-2108-P doesnt support )
// Doc: Data Acquisition Communication Protocol.pdf, page:37

bool DATAQ_BASE::setWorkMode (uint16_t outMode)
{
  if(!isInit) return false; //don't do it if the device isn't initialized

  if (! ((outMode==0) || (outMode==1) || (outMode ==129))) return false;

  string arg0 = to_string(outMode);

  string resp = sendMessage("encode " + arg0);

  return (resp != "error");
}


//***********************************************************************************************************************

// set the scan list defined with addScanList
 bool DATAQ_BASE::setScanList()
 {
     /*
     *  To activate a channel, need to sent this message to the device:
     *
     *    slist num1 num2
     *
     *  num1 is the 'offset', num2 is a 16bit number which includes the channel and range setting, example for DI-2108P:
     *
     *          range        chan
     *    0000  0000   0000  0000
     *
     *  so for channel 2 at 0-10V scale, send
     *
     *    0000 0011 0000 0010 = 770
     *
     */

    bool error = false;

    for (uint16_t i=0; i< scanList.size(); i++)
    {
        string cmdslist = "slist "+ to_string(i) + " " + to_string(scanList[i].config);
        string respond = sendMessage(cmdslist);  //send the slist command
        if (respond == "error") error = true;
    }

    sleep(0.5); // give little time after setup channels

    return !error;
 }


//***********************************************************************************************************************
 // Set the Package Size

 bool DATAQ_BASE::setPackSize( uint32_t packSize)
 {
    if(!isInit) return false; //don't do it if the device isn't initialized

    string arg = to_string(packSize);

    string respond = sendMessage("ps " + arg);

    return (respond == "ps " + arg+"\r");
 }



 //***********************************************************************************************************************

 // Set the Sample Rate in hertz throughput (for all channels) by setting scan rate and dec
 // The sample rate defined how many data points is sampling per second (throughput)
 // Usually good estimation based on max frequency of interest (MFI):
 //  - For only the FFT is enough: 2 x MFI
 //
 // Need calling first the getDividend, which is calling from SetupCommParam

 bool DATAQ_BASE::setSampleRate (uint32_t sampleRateHz)
 {
   if(!isInit) return false; //don't do it if the device isn't initialized

   if  ((sampleRateHz ==0))
    return false;

   // clamp to max limit allow by this device
   if (sampleRateHz > config.sampleRateMax)
   {
     sampleRateHz = config.sampleRateMax;
   }

   config.sampleRate = sampleRateHz; // update last Sample Rate Hz

   // Determine the scan rate, dec & deca parameters based on Sample Rate
   // Sample Rate = dividend / (srate * dec * deca)

   config.dec = 1; config.deca =1;
   config.srate = config.dividend / sampleRateHz; // try to max out srate

   // Check limit for srate
   if (config.srate > config.sampleRateMax)
   {
      config.srate = config.sampleRateMax;
      config.dec = config.dividend / (config.srate * sampleRateHz); // try to max out dec
   };

   // Check limit for dec and adjust using deca
   if (config.dec > config.decMax)
   {
      config.dec = config.decMax;
      config.deca = config.dividend / (config.srate * config.dec * sampleRateHz); // adjust anything else with deca
   }

   // Check limit for deca
   if (config.deca > config.decaMax)
   {
      config.deca =  config.decaMax;
   }

   string resp1 = sendMessage("srate " + to_string(config.srate)); // Set up the device for scan rate

   string resp2 = sendMessage("dec "+ to_string(config.dec)); // Defines the decimation factor applied to the specified mode

   string resp3 = sendMessage("deca "+ to_string(config.deca)); // Defines the deca factor applied to the specified mode

   return ((resp1 != "error") && (resp2 !="error") && (resp3 != "error"));
 }

//***********************************************************************************************************************

// Record data for time (seconds) or fraction of it
// Start scan, get reading for some time and reach limit minimum of records, stop scan
// if limitMin ==0, only will do based on time only, which not all the time produce same amount of records
// if limitMin > 0, will do for both based on time and also reach amount of records minimum
//

void DATAQ_BASE::recordTime(tDataChannels & data, double timesec,  uint32_t limitMin)
{
  initData (data); // Initialize the data structure

  startScan(); // start scan

  auto start = chrono::system_clock::now(); // get the timestamp for starting

  uint16_t errorCount =0;

  while (true)
  {
    if (readData(data))  // get data records reading
     errorCount = 0;
    else
    { // this is handling recovery errors
      errorCount++;
      if (errorCount > 10)
      {
        cout << "[ERROR] Critical Error, too many consecutive errors reading, aborted" << endl;

        return;
      }
    }

    auto end = chrono::system_clock::now();

    chrono::duration<double> elapsed_seconds = end - start; // check duration
    if ((elapsed_seconds.count() >= timesec) && (data.totalRecords > limitMin))
        break;

  }

  stopScan();  // stop the scan
}

//***********************************************************************************************************************

// Read the recording configuration from .ini file
/* Example of .ini file
; Configuration file for cyclic recording

[config]
model = DI-2108P       ; Model
serial =               ; Serial Number
timeout = 1000         ; timeout (ms)
nchannels = 4          ; Total of Analog Input Channels
ai_range = 1           ; Analog input range: 0= +/- 10 VDC, 1= +/- 5 vdc, 2= +- 2.5 vdc, 3= 0-10 vdc, 4= 0-5 vdc
sample_rate= 160000    ; throughtput sample rate (for all channels together)
debug = true           ; Debug mode active

[recording]
every = 900            ; trigger time for recording (sec)
duration = 3           ; how long will record (sec)
count = 10             ; count limit recording, use 0 for endless loop
file_name= data.txt    ; recording file name and path as text file
overwrite = true       ; when recording overwrite same file or create a new file with date&time
precision = 10;        ; decimal precision to store decimal values
min_records = 80000    ; Need to reach minimum records on each cycle, if set to 0, will be based on time only

*/

bool DATAQ_BASE::loadRecordConfig (string fileName,  tRecordConfig &recConfig)
{
   INIReader iniFile (fileName);

   if (iniFile.ParseError() < 0)
   {
       cout << "Can't load " << fileName << endl;
       return false;
   }
   recConfig.model = iniFile.Get("config", "model", "DI-2108P");
   recConfig.serial = iniFile.Get("config", "serial", "");
   recConfig.timeout   = iniFile.GetInteger ("config", "timeout", 1000);
   recConfig.nchannels = iniFile.GetInteger ("config", "nchannels", 1);
   recConfig.ai_range  = iniFile.GetInteger ("config", "ai_range", 1);
   recConfig.sample_rate  = iniFile.GetInteger ("config", "sample_rate", 1000);
   recConfig.debug  =  iniFile.GetBoolean("config", "debug", false);
   recConfig.record_every  = iniFile.GetInteger ("recording", "every", 900);
   recConfig.record_duration  = iniFile.GetInteger ("recording", "duration", 3);
   recConfig.count  = iniFile.GetInteger ("recording", "count", 0);
   recConfig.file_name = iniFile.Get("recording", "file_name", "record.txt");
   recConfig.overwrite = iniFile.GetBoolean("recording", "overwrite", true);
   recConfig.precision = iniFile.GetInteger("recording", "precision", SET_DEC_PRECISION);
   recConfig.min_records = iniFile.GetInteger("recording", "min_records", 0);

   cout << "Config loaded from " << fileName << endl;
   cout << " model = " << recConfig.model << endl;
   cout << " serial = " << recConfig.serial << endl;
   cout << " timeout = " << recConfig.timeout << endl;
   cout << " nchannels = " << recConfig.nchannels << endl;
   cout << " ai_range = " <<  recConfig.ai_range << endl;
   cout << " sample_rate = " <<  recConfig.sample_rate << endl;
   cout << " debug = " << recConfig.debug  << endl;
   cout << " every = " << recConfig.record_every  << endl;
   cout << " duration = " << recConfig.record_duration  << endl;
   cout << " count = " << recConfig.count  << endl;
   cout << " file_name = " << recConfig.file_name  << endl;
   cout << " overwrite = " << recConfig.overwrite  << endl;
   cout << " precision = " << recConfig.precision  << endl;
   cout << " min_records = " << recConfig.min_records  << endl;


   return true;
}

//***********************************************************************************************************************

 // cyclic recording in a file based on the recording configuration for the entire elapsed time (min) and reach minimum records

void DATAQ_BASE::cyclicRecord ( const tRecordConfig &recConfig)
{
   uint32_t count =0;

   cout << "[INFO] Start Cyclic Recording " << endl;

   if (!setModel(recConfig.model, recConfig.timeout)) // Set Model Name & init scanlist and config
   {
      cout << "[ERROR] Recording aborted, the device " << recConfig.model << " not found" << endl;

      return;
   };

   serialNum = recConfig.serial; // Set serial number

   setDebugMode(recConfig.debug); // set debug mode

   if (connect())  // Discovery, connect and setup default communication parameters
   {
     setSampleRate(recConfig.sample_rate);  // Set the sample rate throughput

     initScanList();

     // Configure the channels for scan list
     for (uint16_t i=0; i< recConfig.nchannels; i++)
     {
        addScanList(DI_CHANNEL_TYPE_AI, i+1, recConfig.ai_range); // 1st-Channel
     }
   }
   else
    {
       cout << "[ERROR] Recording aborted, the device " << recConfig.model << " not found" << endl;
       return;
    }

   while (1)
   {
       // On every record it will start all over again, in case loss the connection or somebody disconnect cable
       // to be able recover

       auto start = chrono::system_clock::now(); // get the timestamp for starting

       // Delete the lock file when start recording new file
       // At the beginning delete if any the lock file
       // This will be used for other process that there is no new data written or it is in the process of writing new data
       // When finish the lock file will be created again indicating there is new data ready to be read

        deleteLockFile(recConfig.file_name);

         tDataChannels data;

         recordTime(data, recConfig.record_duration, recConfig.min_records); // record for few seconds but limit to minimum amount of records, if =0, only do it by time

         // Detect if there is a problem with record data and abort to allow a watchdog activate the process again
         // This could happened if for some reason the USB cable is disconnected or turn off
         if (data.totalRecords < recConfig.min_records)
         {
            cout << "[ERROR] Recording aborted, the device " << recConfig.model << " has error reading" << endl;
            return;
         }

         // Save records in a file
         writeDataFile(data, recConfig.file_name, recConfig.overwrite, recConfig.precision); // write all data using same format as showData but in a text file

         count ++;
         cout << "[INFO] Recorded count " << count << " timestamp " << data.timestamp << " records " << data.totalRecords << endl;

         // When finish creating file indicate for other process that there is a new data available
         // the other process is responsible to delete this file to avoid read old data again

         createLockFile(recConfig.file_name);

         // Check if reach count, if count ==0, means endless loop
         if (recConfig.count >0)
         {
            if (count >= recConfig.count) break; // break while loop
         }


       // check next trigger time

       while (1)
       {
           auto end = chrono::system_clock::now();

           chrono::duration<double> elapsed_seconds = end - start; // check next trigger

           if (elapsed_seconds.count() >= recConfig.record_every)
               break;

           sleep(1); // wait one second tick
       }

   }// while

   disconnect(); // close communication

  cout << "[WARN] End Cyclic Recording " << endl;
}

//***********************************************************************************************************************

 // Load the configuration from file and starting cyclic record
bool DATAQ_BASE::loadConfigCyclicRecord (string fileName)
{
    tRecordConfig config;

    if (!loadRecordConfig(fileName, config)) // Load configuration file
    {
       cout << "[ERROR] Could not load record config file 'config.ini' record operation aborted" << endl;
       return false;
    }

    cyclicRecord(config); // perform cyclic recording as per configuration file with minimum records

    return true;
}

//***********************************************************************************************************************

// Setup main communication parameters by default values
// Work Mode: BINARY, Sample Rate: 160 Khz (Max), Package Size: 64 Bytes
void DATAQ_BASE::setupCommParam()
{
    if(!isInit) return; //don't do it if the device isn't initialized

    // get the Device Info => DATAQ
    if (getDeviceInfo() =="error")
    {
      cout << "[ERROR] Setup communication parameters failed, couldn't get Device Info" << endl;
      return;
    }

    setWorkMode(DI_WORK_MODE_BINARY); // // Set up the device for binary mode- The Model DI-2108-P doesn't support ASCII, this is to be compatible with other devices

    readDividend (); // Returns the sample rate divisor value of 60,000,000 for the DI-2108-P (see the srate command for details)

    setSampleRate(DI_MAX_SAMPLE_RATE); // By default set Sample rate as 160 Khz

    setPackSize(DI_PACK_SIZE_64_BYTES);  //request 0-16 byte package size, 1- 32 bytes, 2- 64 bytes, 3- 128 bytes, 4- 256 bytes, 5- 512, 6- 1024 bytes, 7- 2048 bytes, has to be accordingly the sample rate
}


//***********************************************************************************************************************

//start scanning
void DATAQ_BASE::startScan(){
  if(!isInit) return; //don't start if the device isn't initialized

  if (isDebugging())
   cout << "[WARN] Start Scan" << endl;

  // check if there is no scan list defined
  if (scanList.empty())
  {
    if (isDebugging())
     cout << "[ERROR] Cannot Start Scan, scanlist is not defined, please use addScanList to setup the channels to scan" << endl;

    return;
  }

  setScanList(); // Set the scan list

  setAcqMode(); // Set filters for Acquisition Mode for all Analog Input channels

  sendMessage("start 0");  //start scanning, start doesn't has echo

  sleep(0.5); // wait to allow starting the scanning

  isRun=true;   //set run boolean to true
  scanIndex =0; // Start index for parsing in the first channel when reading & parsing data
}

//***********************************************************************************************************************

//stop scanning
void DATAQ_BASE::stopScan(){
  if(!isInit) return;   //don't do anything if it's not initialized

  if (isDebugging())
   cout << "[WARN] Stop Scan" << endl;

  isRun=false;          //set run boolean to false
  sendMessage("stop");

  clearInput(); // clear any additional data that was sent in buffer
}

//***********************************************************************************************************************

// Get the Firmware from device

string DATAQ_BASE::getFirmware()
{
  string result = sendMessage("info 2");

  return getParamFromResp(result, "info 2");
}

//***********************************************************************************************************************

// Get the serial number from device
string DATAQ_BASE::getSerialNum()
{
  string result = sendMessage("info 6");

  string serial = getParamFromResp(result, "info 6");

  return serial.substr(1,8);
}

//***********************************************************************************************************************
// Get the device Info DATAQ
 string  DATAQ_BASE::getDeviceInfo()
 {
   if(!isInit) return "error"; //don't do it if the device isn't initialized

   string respond = sendMessage("info 0"); // get the Device Info => DATAQ

   return getParamFromResp(respond, "info 0");
 }

 //***********************************************************************************************************************
 // Get the dividend number used for sample rate
 // Doc: di-2108-p protocol.pdf, page 3

 bool DATAQ_BASE::readDividend ()
 {
     if(!isInit) return false; //don't do it if the device isn't initialized

     string result = sendMessage("info 9"); // Returns the sample rate divisor value of 60,000,000 for the DI-2108-P (see the srate command for details)
     // respond can be: info 9 60000000

     string arg = getParamFromResp( result, "info 9"); // get the parameter from response

     if (!arg.empty())
     {
       uint32_t number = stoul(arg); // convert to unsigned long number

        if (number >0)
        {
         config.dividend = number;
         if (isDebugging())
          cout << "[WARN] Read Dividend =" << config.dividend  << endl; // This is a factor using for

         return true;
        };
        // if number =0, will keep whatever has based on model number

     }

     return false;
 }


 //***********************************************************************************************************************

 // Set debug mode (enable or not)
 // if false will not show up the tracking messages
 void DATAQ_BASE::setDebugMode (bool debugMode)
 {
   isdebug = debugMode;
 }

 //***********************************************************************************************************************

 // Show device models listed
  void DATAQ_BASE::showDeviceModels()
  {
    cout << "[INFO] Models Expected" << endl;
    for (uint16_t i=0; i < DI_TOTAL_MODELS; i++)
    {
      cout << " " << MODEL_NAME[i];
    };

    cout << endl;
  }

  //***********************************************************************************************************************

  // Reset the Counter to 0, although start/stop scan will reset counter also
  // Looks that during the scan cycle the device DI-2108P cannot take reset command, so actually it is useless

  bool DATAQ_BASE::resetCounter()
  {
     string resp = sendMessage("reset 1");

     return (resp != "error");
  }

  //***********************************************************************************************************************

  // Write digital input bits defined as switch (Output)
  // where 1- turn on, 0- turn off
  bool DATAQ_BASE::writeDigBits (uint16_t digBits)
  {
     string resp = sendMessage("dout " + to_string(digBits));

     return (resp != "error");
  }


  //***********************************************************************************************************************

  // Read current digital input bits status
  bool DATAQ_BASE::readDigBits (uint16_t &digBits)
  {
      digBits = 0;

      string resp = sendMessage("din"); // read the digital input status

      string strBits = getParamFromResp(resp, "din ");

      if ((strBits == "error") || (strBits.empty())) return false;

      digBits = stoul(strBits); // convert to unsigned long number

      return true;
  }



 //***********************************************************************************************************************

  // Init scan list of channels configuration
  void DATAQ_BASE::initScanList()
  {
    scanList.clear();
  }

 //***********************************************************************************************************************

 // Add the channel configuration to the Scan List, need to call setScanList after
  bool DATAQ_BASE::addScanList (uint16_t channelType, uint16_t channelNumber,  uint16_t channelRange, uint16_t acqMode)
  {
    tChannelConfig channel;
    bool result = setChannelConfig (channel, config.modelID, channelType, channelNumber, channelRange,  acqMode);  // call for setting chanel configuration

    if (result)
      scanList.push_back(channel);
    else
    {
      if (isDebugging())
      {
        cout << "[ERROR] Cannot set the channel << " << channelNumber << endl;
      }
    }
    return result;
  }


//***********************************************************************************************************************

// Set digital mode for all digital channels using command endo <bits in switch>
// for example: 3 means D0 and D1 will set as output, while the others will be set as inputs
 bool DATAQ_BASE::setDigBitsMode(uint16_t digBitsMode)
 {
     if ((!isInit) || (digBitsMode > 127)) return false; //don't do it if the device isn't initialized

     bool error = false;

     string arg0 = to_string(digBitsMode);

     string resp = sendMessage("endo " + arg0);  //Set digital mode for all digitals channels, where bits: 0- input, 1- output (switch)

     if (resp == "error") error = true;

     return !error;
 }

  //***********************************************************************************************************************

  // Init data records
  void DATAQ_BASE::initData (tDataChannels & data)
  {
     data.timestamp = 0;
     data.totalRecords = 0;
     for (uint16_t i=0; i < MAX_AI_CHANNELS; i++)
      {
        data.analog[i].clear();
      }
     data.dig.clear();
     data.rate.clear();
     data.count.clear();
  }

  //***********************************************************************************************************************

  //get the voltage measurements from the device and do parsing to convert to voltage
  // It is important to do this step very quickly to remove bytes from usb input buffer
  // otherwise the device can get an error

  bool DATAQ_BASE::readData( tDataChannels &data)
  {
    if(!isInit) return false; //don't do it if the device isn't initialized

    isRead=true;  //set recording boolean to true for the duration of this method

    if ((!isInit) || (scanList.empty())){   //if device is not initialized, send a vector with only 0 entries
       isRead=false;
      return false;
    }


    initRecBuffer(); // init Receiving buffer

    // check first if time put the start timestamp (ms) for the data set
    if (data.timestamp ==0)
    {
        data.timestamp = getTimestamp(); // get timestamp in ms (time since epoch)
    }

    uint32_t limit = sizeof(received); // limit to even bytes quantity config.sampleRate; //

    int actual = readBuffer(received, limit, timeoutms); // get how many bytes were read in the received buffer

    if (actual ==0)
    {
        if (isDebugging())
         cout << "[ERROR] Read Failed- No Bytes" << endl;
        sleep(0.01);
        return false;
    }

    bool parsed =parsingData (data, scanIndex, received, actual);

    isRead=false;  //recording is finished

    return true;  //return success
  }

  //***********************************************************************************************************************

  // show data records based on channels scan list
 void DATAQ_BASE::showData (const tDataChannels &data)
 {
   cout << "timestamp: " << data.timestamp << " samplerate: " << config.sampleRate << " nchannels: " << scanList.size() <<endl;

   for (uint32_t i=0; i<data.totalRecords; i++ )
   {
      cout << i +1 << ":";
      for (int16_t s=0; s< scanList.size(); s++) // scan channel loop
      {
        cout << " ";
        tChannelConfig channel = scanList[s];
        switch (channel.type)
        {
         case DI_CHANNEL_TYPE_AI:
            cout <<"CH" << channel.number+1 << " " <<  std::fixed << std::setprecision(SET_DEC_PRECISION) << data.analog[channel.number][i];
            break;
         case DI_CHANNEL_TYPE_DIG:
            cout << "DIG:" << data.dig[i];
            break;
         case DI_CHANNEL_TYPE_RATE:
            cout <<"RATE:" << data.rate[i];
            break;
         case DI_CHANNEL_TYPE_COUNT:
            cout << "COUNT:" << data.count[i];
            break;
        } // switch

      } // for loop for record

     cout << endl; // change of line
   }
 }

 //***********************************************************************************************************************

 // Get current timestamp in ms (time since epoch)
  uint64_t DATAQ_BASE::getTimestamp()
  {
      auto current = chrono::system_clock::now(); // get the current timestamp

     return std::chrono::duration_cast<std::chrono::milliseconds> (current.time_since_epoch()).count(); // milliseconds
  }

 //***********************************************************************************************************************
 // Write in text file the data, the file will be overwritten if exist
 bool DATAQ_BASE::writeDataFile (const tDataChannels &data, string fileName, bool overwrite,  uint16_t precision )
 {

    // determine the file name based on overwrite
    // if it is not overwritting, a new file name will be created adding timestamp at the end: <timestamp ms>_<file name>
    if (!overwrite)
         fileName = to_string( data.timestamp) + "_" + fileName;

    // open the record file
    ofstream file;
    file.open(fileName);

    if (isDebugging())
     cout << "[INFO] Writing in file " << fileName << endl;

    if (!file.is_open())
    {
      cout << "[ERROR] Unable to open file " << fileName << endl;
      return false;
    }

    // First row will be: timestart <time since epoch>    samplerate: <sample rate>  nchannels: <total channels defined>
    file << "timestamp: " << data.timestamp << " samplerate: " << config.sampleRate << " nchannels: " << scanList.size() <<endl;

     for (uint32_t i=0; i<data.totalRecords; i++ )
     {
        file << i +1 << ":";
        for (int16_t s=0; s< scanList.size(); s++) // scan channel loop
        {
          file << " ";
          tChannelConfig channel = scanList[s];
          switch (channel.type)
          {
           case DI_CHANNEL_TYPE_AI:
              file <<"CH" << channel.number+1 << " " << std::fixed << std::setprecision(precision) << data.analog[channel.number][i];
              break;
           case DI_CHANNEL_TYPE_DIG:
              file << "DIG:" << data.dig[i];
              break;
           case DI_CHANNEL_TYPE_RATE:
              file <<"RATE:" << data.rate[i];
              break;
           case DI_CHANNEL_TYPE_COUNT:
              file << "COUNT:" << data.count[i];
              break;
          } // switch

        } // for loop for record

       file << endl; // change of line
     }  // for loop for all data

     file.close();

     if (isDebugging())
      cout << "[INFO] Finished writing in file " << fileName << endl;

    return true;
 }

 //***********************************************************************************************************************
 // Create an empty file with the lck at the end as signal for other process want to read the file was done
 // the file name could not include the lck mark, this will be added at the end

 bool DATAQ_BASE::createLockFile (string fileName)
 {
     ofstream file;

     fileName += "_lck";

     file.open(fileName);

     if (isDebugging())
      cout << "[INFO] Creating Lock file " << fileName << endl;

     if (!file.is_open())
     {
       cout << "[ERROR] Unable to open file " << fileName << endl;
       return false;
     }

     file.close();

     return true;
 }

 //***********************************************************************************************************************
// Delete lock file, return true if the file was deleted, otherwise return false
 bool DATAQ_BASE::deleteLockFile (string fileName)
 {
    fileName += "_lck";

    if (isDebugging())
     cout << "[INFO] Deleting Lock file " << fileName << endl;

    int res = remove(fileName.c_str());

    return res==0;
 }


//***********************************************************************************************************************
// Parsing the raw data read from buffer, scaling and put into the data structure
// The count and rate channels are only working during the scanning.

bool DATAQ_BASE::parsingData (tDataChannels & data, uint16_t &scanInd, unsigned char *buffer, int bufferSize)
{
    /*
     *  The device returns a 16 bit value for each channel. libusb converts this whole message
     *  into a char* array. Each char is 8 bits, so the measurement in each channel is composed
     *  of two chars: the one at 2n and the one at 2n+1.
     */
  bool error = false;

  uint32_t index =0;

  while (index < bufferSize)
  {
    tChannelConfig channel = scanList[scanInd];

    switch ( config.modelID)
    {
     // TODO parsing of other models

     case DI_MODEL_DI_2108:
     case DI_MODEL_DI_2108P:
     case DI_MODEL_DI_4108:
     case DI_MODEL_DI_4208:
     case DI_MODEL_DI_47188:
      {
        int16_t rawValue;

        memmove(&rawValue, &buffer[index], 2); // This is equivalent like doing this: buffer[index+1] << 8) | (buffer[index]

        switch (channel.type)
        {
           case DI_CHANNEL_TYPE_AI: // Parsing Analog Input
               {
                 double value = rawValue * channel.scalingFactor + channel.scalingOffset; // see page 44- Data Acquisition Communication Protocol
                 data.analog[channel.number].push_back(value);

                 break;
               }

           case DI_CHANNEL_TYPE_DIG:
               {
                 uint16_t digStatus = buffer[index+1]; // The digital are in the second byte index-  // see page 44- Data Acquisition Communication Protocol
                 data.dig.push_back(digStatus);

                 break;
               }

           case DI_CHANNEL_TYPE_RATE: // only works if the scan channels is actived
               {
                  double rate = 50000 * (rawValue + 32768.0)/65535.0; // see page 46- Data Acquisition Communication Protocol
                  data.rate.push_back(rate);

                  break;
               }

           case DI_CHANNEL_TYPE_COUNT: // only works if the scan channels is actived
               {
                  uint32_t count = rawValue + 32768;
                  data.count.push_back(count);

                  break;
               }

        } // channel type

//        cout << "index " << index << "chanel " << channel.number << " value " << rawValue  << " word " << (uint16_t) rawValue  << " scaled " << channel.scalingFactor * rawValue + channel.scalingOffset << endl;

       break;
      }

      default:
       { cout << "[ERROR] Parsing not implemented yet for this model" << endl;
        return false;
       }

    } // Device model

    index += 2;

    scanInd++;

    if (scanInd >= scanList.size()) // check if already completed all channels
    {
       scanIndex = 0; // start over again
       data.totalRecords++; // already complete all channels, so increment the general counter
    }

  } // while buffer size
}

//***********************************************************************************************************************
// Set the channel configuration value based on configuration table,  Device Model, Range, channel number (1-8), Acquisition Mode
// Doc: Data Acquisition Communication Protocol.pdf, page 39
// return false if there is an error

bool DATAQ_BASE::setChannelConfig (tChannelConfig &channel, uint16_t deviceModel, uint16_t channelType, uint16_t channelNumber, uint16_t channelRange,  uint16_t acqMode)
{
  // validation of some input parameters
    if (channelNumber >12)
    {
       return false;
    };

   // Channel initialization
  channel.type   = channelType;
  channel.number = channelNumber - 1; // 0- 7
  channel.range  = channelRange;
  channel.acqMode = acqMode;
  channel.config = 0; // default 0
  channel.scalingFactor = 1.0; // default values for scaling
  channel.scalingOffset = 0.0;

  // check if there is any error in parameters
  bool error = false;

   switch (deviceModel)
   {
    case DI_MODEL_DI_NONE:
       error = true;
      break;

    case DI_MODEL_DI_1100: // TODO
       break;

    case DI_MODEL_DI_1110: // TODO
       break;

    case DI_MODEL_DI_1120: // TODO
       break;

    case DI_MODEL_DI_2008: // TODO
       break;

    case DI_MODEL_DI_2108:
       if (channelType == DI_CHANNEL_TYPE_AI)
       {
           bitset<16> bits (channel.number); // 0- 7

           switch (channelRange)
           {
             case DI_AI_RANGE_BIPOL_10VDC:  // +/- 10 VDC
                channel.scalingFactor = 10.0 / 32768.0;  // full scale * count / 32768
               break;

             default:
               error = true;
               break;
           };
           channel.config = bits.to_ulong(); // convert bits to number
       } ;
       if (channelType == DI_CHANNEL_TYPE_DIG) channel.config = 8;

       if (channelType==DI_CHANNEL_TYPE_RATE)
       {
          bitset<16> bits (9);
          bits[8] = 1;  // 50 Khz
          channel.config = bits.to_ulong();
          // TODO- scaling Rate
           channel.scalingFactor = 50000.0 / 65535.0;
       }

       break;

    case DI_MODEL_DI_2108P:
        if (channelType == DI_CHANNEL_TYPE_AI)
        {
            bitset<16> bits (channel.number); // 0- 7

            switch (channelRange)
            {
              case DI_AI_RANGE_BIPOL_10VDC:  // +/- 10 VDC
                 channel.scalingFactor = 10.0 / 32768.0;  // full scale * count / 32768
                break;

              case DI_AI_RANGE_BIPOL_5VDC: // +/- 5 VDC
                bits[8] = 1;
                 channel.scalingFactor = 5.0 / 32768.0;  // full scale * count / 32768
                break;

              case DI_AI_RANGE_BIPOL_2_5VDC: // +/- 2.5 VDC
                bits[9] = 1;
                 channel.scalingFactor = 2.5 / 32768.0;  // full scale * count / 32768
                break;

              case DI_AI_RANGE_UNIPOL_10VDC: // 0-10 VDC
                bits[8] = 1; bits [9] =1;
                 channel.scalingFactor = 10.0 / 65536.0; channel.scalingOffset = 10.0/2.0; // Full scale * (count + 32768)/ 65536
                break;

              case DI_AI_RANGE_UNIPOL_5VDC: // 0-5 VDC
                bits [10] = 1;
                  channel.scalingFactor = 5.0 / 65536.0; channel.scalingOffset = 5.0/2.0; // Full scale * (count + 32768)/ 65536
                break;

              default:
                error = true;
                break;
            };
            channel.config = bits.to_ulong(); // convert bits to number
        } ;
        if (channelType == DI_CHANNEL_TYPE_DIG) channel.config = 8;

        if (channelType==DI_CHANNEL_TYPE_RATE)
        {
           bitset<16> bits (9);
           bits[8] = 1;  // 50 Khz
           channel.config = bits.to_ulong();
           // TODO- scaling Rate
            channel.scalingFactor = 50000.0 / 65535.0;
        }

        if (channelType == DI_CHANNEL_TYPE_COUNT) channel.config = 10;

       break;

    case DI_MODEL_DI_4108:
       if (channelType == DI_CHANNEL_TYPE_AI)
       {
           bitset<16> bits (channel.number); // 0- 7

           switch (channelRange)
           {
             case DI_AI_RANGE_BIPOL_10VDC:  // +/- 10 VDC
                channel.scalingFactor = 10.0 / 32768.0;  // full scale * count / 32768
               break;

             case DI_AI_RANGE_BIPOL_5VDC: // +/- 5 VDC
               bits[8] = 1;
                channel.scalingFactor = 5.0 / 32768.0;  // full scale * count / 32768
               break;

             case DI_AI_RANGE_BIPOL_2VDC: // +/- 2VDC
               bits[9] = 1;
                channel.scalingFactor = 2.5 / 32768.0;  // full scale * count / 32768
               break;

            case DI_AI_RANGE_BIPOL_1VDC: // +/- 1VDC
              bits[8] = 1; bits[9] = 1;
              channel.scalingFactor = 1.0 / 32768.0;  // full scale * count / 32768
             break;


           case DI_AI_RANGE_BIPOL_0_5VDC: // +/- 0.5VDC
             bits[10] = 1;
              channel.scalingFactor = 0.5 / 32768.0;  // full scale * count / 32768
             break;

           case DI_AI_RANGE_BIPOL_0_2VDC: // +/- 0.2VDC
             bits[8] = 1; bits[10] = 1;
              channel.scalingFactor = 0.2 / 32768.0;  // full scale * count / 32768
             break;

             default:
               error = true;
               break;
           };
           channel.config = bits.to_ulong(); // convert bits to number
       } ;
       if (channelType == DI_CHANNEL_TYPE_DIG) channel.config = 8;

       if (channelType==DI_CHANNEL_TYPE_RATE)
       {
          bitset<16> bits (9);
          bits[8] = 1;  // 50 Khz
          channel.config = bits.to_ulong();
          // TODO- scaling Rate
           channel.scalingFactor = 50000.0 / 65535.0;
       }

       if (channelType == DI_CHANNEL_TYPE_COUNT) channel.config = 10;
       break;

    case DI_MODEL_DI_4208:
       if (channelType == DI_CHANNEL_TYPE_AI)
       {
           bitset<16> bits (channel.number); // 0- 7

           switch (channelRange)
           {
             case DI_AI_RANGE_BIPOL_100VDC:  // +/- 100 VDC
                channel.scalingFactor = 100.0 / 32768.0;  // full scale * count / 32768
               break;

             case DI_AI_RANGE_BIPOL_50VDC: // +/- 50 VDC
               bits[8] = 1;
                channel.scalingFactor = 50.0 / 32768.0;  // full scale * count / 32768
               break;

             case DI_AI_RANGE_BIPOL_20VDC: // +/- 20VDC
               bits[9] = 1;
                channel.scalingFactor = 20.0 / 32768.0;  // full scale * count / 32768
               break;

            case DI_AI_RANGE_BIPOL_10VDC: // +/- 10 VDC
              bits[8] = 1; bits[9] = 1;
              channel.scalingFactor = 10.0 / 32768.0;  // full scale * count / 32768
             break;


           case DI_AI_RANGE_BIPOL_5VDC: // +/- 5VDC
             bits[10] = 1;
              channel.scalingFactor = 5.0 / 32768.0;  // full scale * count / 32768
             break;

           case DI_AI_RANGE_BIPOL_2VDC: // +/- 2 VDC
             bits[8] = 1; bits[10] = 1;
              channel.scalingFactor = 2 / 32768.0;  // full scale * count / 32768
             break;

             default:
               error = true;
               break;
           };
           channel.config = bits.to_ulong(); // convert bits to number
       } ;
       if (channelType == DI_CHANNEL_TYPE_DIG) channel.config = 8;

       if (channelType==DI_CHANNEL_TYPE_RATE)
       {
          bitset<16> bits (9);
          bits[8] = 1;  // 50 Khz
          channel.config = bits.to_ulong();
          // TODO- scaling Rate
           channel.scalingFactor = 50000.0 / 65535.0;
       }

       if (channelType == DI_CHANNEL_TYPE_COUNT) channel.config = 10;
       break;

    case DI_MODEL_DI_47188: // TODO- HAs to include all cards and ranges

      break;

    default:
       error = true;
       break;
   }

  if (isDebugging())
  {
     cout << "[INFO] Set Channel Type " <<  channel.type  << " Number " << channel.number  << " Range " << channel.range
          << " Config " <<  channel.config << " Acq Mode " <<  channel.acqMode << endl;
  }
  return !error;
}

//***********************************************************************************************************************
// Determine the Device PID & VID based on Product Model

// General configuration based on model

bool DATAQ_BASE::detDeviceConfig()
{
  for (uint16_t i=0; i < DI_TOTAL_MODELS; i++)
  {
    if (MODEL_NAME[i] == config.modelName)
    {
      // Determine the Device Model Numeric Identifier (+1)
      config.modelID = i+1;  // add 1 because starting in 1, while the array starting in 0

      // Determine the Product ID and Vendor ID
      config.pidLibUSB = PID_LibUSB[i]; // Product ID based on the model name
      config.vidLibUSB = VID; // Vendor ID is commom for all products

      // Determine the Min/Max for scan rate, Decimal, Decimal Factor
      config.srateMin = SRATE_MIN[i]; config.srateMax = SRATE_MAX[i];
      config.decMin   = DEC_MIN[i];   config.decMax   = DEC_MAX[i];
      config.decaMin  = DECA_MIN[i];  config.decaMax  = DECA_MAX[i];
      config.aiMax    = AI_MAX[i];
      config.sampleRateMax =SAMPLE_MAX[i];

      // The custom parameters are set when calling setSampleRate
      config.dividend = DIVIDEND[i]; // this is just tentative, in case there is an error when calling readDividend

      return true;
    }
  };

 if (config.pidLibUSB ==0)
  {
    cout << "[ERROR] Could not determine the Product/Vendor ID for " << config.modelName << " Please check name " << endl;
    showDeviceModels();
  }

 return false;
}

//***********************************************************************************************************************

 // Initialize the receiving buffer
 void DATAQ_BASE::initRecBuffer()
 {
     memset (received, 0, sizeof(received));
 }

//***********************************************************************************************************************

// Get the parameter from the respond to the command
string DATAQ_BASE::getParamFromResp (string response, string cmd)
{
    int pos = response.find(cmd);
    if (pos != std::string::npos) // if got the echo of same command after is the arguments
    {
       string arg = response.erase(0, cmd.length()); // delete from the response the cmd to get only the arguments
       return arg;
    }

    return response;
}
