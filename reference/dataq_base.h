#ifndef DATAQ_BASE_H
#define DATAQ_BASE_H

/*
 *   DATAQ_BASE class, used as Protocol Base Class
 *   to encapsulate main protocol operations, generic for all compatible devices
 *
 *   version: 1.0.1
 *
 *   Created by Reyan Valdes (ITG)
 *
 *   email: rvaldes@itgtec.com
 *   date: 4/21/2021
 *
 */

// For the communication protocol was used two documents as reference from DATAQ:
// - DI-2108-P manual.pdf
// - Data Acquisition Communication Protocol.pdf
// -

#include <iostream>
#include <stdio.h>
#include <string.h>
#include <sstream>
#include <unistd.h>
#include <vector>
#include </usr/include/libusb-1.0/libusb.h>  // handle communcation with the device
#include <INIReader.h> // for handling INIT file configuration (used for cyclicRecording)
#include <dataq_base.h> // for the Abstract class (Base) to handle DATAQ Instruments


using namespace std;


// Note: Only the following models are fully supported in this version when configuring or parsing the data
//
// FULLY SUPPORTED IN THIS VERSION: *********    2108, 2108P, 4108, 4208    **********
//
// TODO: Complete configuration & parsing for rest of models: 1100, 1111, 1120, 2008, 4718B
// - bool DATAQ_BASE::setChannelConfig
// - bool DATAQ_BASE::parsingData

// Define all DI-DATAQ models, its PID & VID and min/max for main config parameters
#define DI_TOTAL_MODELS 9

const uint32_t MI = 1000000; // constant to make it easy enter dividend

const string MODEL_NAME [DI_TOTAL_MODELS] = {"DI-1100", "DI-1110", "DI-1120", "DI-2008", "DI-2108", "DI-2108P", "DI-4108", "DI-4208", "DI-4718B"};

const uint16_t PID_LibUSB [DI_TOTAL_MODELS] = {0x1100,    0x1110,    0x1120,    0x2008,    0x2108,    0x2109,     0x4108,    0x4208,    0x4718};

const uint32_t SRATE_MIN [DI_TOTAL_MODELS]  = { 1500,     375,       375,       4,         375,       375,        375,       375,       375   };

const uint32_t SRATE_MAX [DI_TOTAL_MODELS]  = { 65535,    65535,     65535,     2232,      65535,     65535,      65535,     65535,     65535 };

const uint32_t DEC_MIN [DI_TOTAL_MODELS]    = { 1,        1,         1,         1,         1,         1,          1,         1,         1     };

const uint32_t DEC_MAX [DI_TOTAL_MODELS]    = { 1,        1,         512,       32767,     512,       512,        512,       512,       512   };

const uint32_t DECA_MIN [DI_TOTAL_MODELS]   = { 1,        1,         1,         1,         1,         1,          1,         1,         1     };

const uint32_t DECA_MAX [DI_TOTAL_MODELS]   = { 40000,    40000,     40000,     1,         40000,     1,          40000,     40000,     40000 };

const uint16_t AI_MAX  [DI_TOTAL_MODELS]    = { 4,        4,         4,         8,         8,         8,          8,         8,         8     };

const uint32_t SAMPLE_MAX [DI_TOTAL_MODELS] = {40000,     160000,    160000,    2000,      160000,    160000,     160000,    160000,    160000};

const uint32_t DIVIDEND [DI_TOTAL_MODELS] =   {60*MI,     60*MI,     60*MI,     8000,      60*MI,     60*MI,      60*MI,     60*MI,     60*MI };

const uint16_t VID = 0x0683;


// main parameters that describe each model
struct tModelConfig
{
   // General configuration based on model
   string   modelName;
   uint16_t modelID;
   uint16_t pidLibUSB;
   uint16_t vidLibUSB;
   uint32_t srateMin;
   uint32_t srateMax;
   uint32_t decMin;
   uint32_t decMax;
   uint32_t decaMin;
   uint32_t decaMax;
   uint16_t aiMax;
   uint32_t sampleRateMax;

   // custom based on device and setSampleRate
   uint32_t sampleRate;
   uint32_t dividend;
   uint32_t srate;
   uint32_t dec;
   uint32_t deca;
};


// Device Model ID - Need to correspond in order with the MODEL_NAME string array (+1)
// In this version only are supported: 2108, 2108P, 4108, 4208, 4718B

#define DI_MODEL_DI_NONE  0
#define DI_MODEL_DI_1100  1
#define DI_MODEL_DI_1110  2
#define DI_MODEL_DI_1120  3
#define DI_MODEL_DI_2008  4
#define DI_MODEL_DI_2108  5
#define DI_MODEL_DI_2108P 6
#define DI_MODEL_DI_4108  7
#define DI_MODEL_DI_4208  8
#define DI_MODEL_DI_47188 9


// Define all channel types

#define DI_CHANNEL_TYPE_AI    0    // Analog Input
#define DI_CHANNEL_TYPE_DIG   1    // Digital
#define DI_CHANNEL_TYPE_RATE  2    // Rate
#define DI_CHANNEL_TYPE_COUNT 3    // Count


// Analog Input Rage

#define DI_AI_RANGE_BIPOL_10VDC  0 // +/- 10 VDC
#define DI_AI_RANGE_BIPOL_5VDC   1 // +/- 5 VDC
#define DI_AI_RANGE_BIPOL_2_5VDC 2 // +/- 2.5 VDC
#define DI_AI_RANGE_UNIPOL_10VDC 3 // 0-10 VDC
#define DI_AI_RANGE_UNIPOL_5VDC  4 // 0-5 VDC
#define DI_AI_RANGE_BIPOL_100VDC 5 // +/- 100 VDC
#define DI_AI_RANGE_BIPOL_50VDC  6 // +/- 50 VDC
#define DI_AI_RANGE_BIPOL_20VDC  7 // +/- 20 VDC
#define DI_AI_RANGE_BIPOL_2VDC   8 // +/- 2 VDC
#define DI_AI_RANGE_BIPOL_1VDC   9 // +/- 1 VDC
#define DI_AI_RANGE_BIPOL_0_5VDC  10 // +/- 0.5 VDC
#define DI_AI_RANGE_BIPOL_0_2VDC  11 // +/- 0.2 VDC

#define DI_AI_RANGE_NOT_DEFINED 0xFFFF

// Digital Mode: Input / Switch
#define DI_DIG_INPUT  0
#define DI_DIG_SWITCH 1

// Acquisition Modes

#define DI_ACQ_MODE_LAST_POINT 0
#define DI_ACQ_MODE_AVERAGE    1
#define DI_ACQ_MODE_MAXIMUM    2
#define DI_ACQ_MODE_MINIMUM    3


// Output Working Mode

// This for compatibility of other models (for future reference)
// For now we focus on Binary

#define DI_WORK_MODE_BINARY   0
#define DI_WORK_MODE_ASCII    1
#define DI_WORK_MODE_BINARY_2 129


// Define package size

#define DI_PACK_SIZE_16_BYTES   0
#define DI_PACK_SIZE_32_BYTES   1
#define DI_PACK_SIZE_64_BYTES   2
#define DI_PACK_SIZE_128_BYTES  3
#define DI_PACK_SIZE_256_BYTES  4
#define DI_PACK_SIZE_512_BYTES  5
#define DI_PACK_SIZE_1024_BYTES 6
#define DI_PACK_SIZE_2048_BYTES 7

// Define Max Sample rate Hz

#define DI_MAX_SAMPLE_RATE  160000

// Define the structure for reading data channels

#define MAX_AI_CHANNELS 8

// Channel configuration
struct tChannelConfig
{
   uint16_t type;   // AI, DIG, RATE, COUNT
   uint16_t number; // 0-7 (starting from 0)
   uint16_t range;  // +/- 10 VDC, +/-5 VDC,...
   uint16_t acqMode; // Acquisition Mode: Last Point, Average, Maximum, Minimum
   uint16_t config; // Based on the configuration table and device model
   double   scalingFactor;   // Scaling factor for parsing the buffer
   double   scalingOffset;   // Scaling offset for parsing the buffer
};

typedef vector<tChannelConfig> tScanList; // Scan List of channels

// Data for channels
struct tDataChannels
{
   uint64_t timestamp;
   uint32_t totalRecords;
   vector<double>   analog [MAX_AI_CHANNELS];
   vector<uint16_t> dig;
   vector<double>   rate;
   vector<uint16_t> count;
};



// For the configuration of cyclicRecording in a file
/*
; Configuration file for cyclic recording

[config]
model = DI-2108P       ; Model
serial = 6059A55E      ; Serial Number
timeout = 1000         ; timeout (ms)
nchannels = 4          ; Total of Analog Input Channels
ai_range = 1           ; Analog input range: 0= +/- 10 VDC, 1= +/- 5 vdc, 2= +- 2.5 vdc, 3= 0-10 vdc, 4= 0-5 vdc
sample_rate= 160000    ; throughtput sample rate (for all channels together)
debug = true           ; Debug mode active

[recording]
every = 900            ; trigger time for recording (sec)
duration = 3           ; how long will record (sec)
count = 10             ; count limit recording, use 0 for endless loop
file_name= data.txt    ; text file name and path for recording on a file
overwrite = true       ; when recording overwrite same file or create a new file with date&time
precision = 10         ; total of decimal digits to use for all float numbers
min_records = 80000    ; Need to reach minimum records on each cycle
*/


struct tRecordConfig
{
  string model;          // model name of DATAQ device
  string serial;         // Serial number
  uint32_t timeout;     // timeout (ms)
  uint16_t nchannels;   // Total of Analog Input Channels
  uint16_t ai_range;    //  Analog input range: 0= +/- 10 VDC, 1= +/- 5 vdc, 2= +- 2.5 vdc, 3= 0-10 vdc, 4= 0-5 vdc, ...
  uint32_t sample_rate; //  throughtput sample rate (for all channels together)
  bool debug;           // Debug mode active
  uint32_t record_every;     // record frequency (sec)
  uint32_t record_duration;  // record duration
  uint32_t count;       // count limit for recording
  string   file_name;   // record file name
  bool overwrite;       // overwrite the file or create a new one everytime
  uint16_t precision;   // how many digits want to store for the decimal analog data
  uint32_t min_records; // minimum amount od records to reach on each cycle
};


// Buffer limit used when reading

#define BUFFER_LIMIT 2*1024  // It is important this number should be multiple of 2 bytes (word), looks 2K is good for all sampling rates

#define SET_DEC_PRECISION 10 // Set to 10 decimal the precision to avoid lossing precision when reading and writing in a file to feed other process

class DATAQ_BASE
{

 public:

  DATAQ_BASE();                   //empty constructor
  DATAQ_BASE(string dev_model, uint32_t timeout_ms=2000, string serialNumber="");      //constructor with number of channels and measurement range (default: +/- 5VDC
  virtual bool setModel(string dev_model, uint32_t timeout_ms=2000); // Set model and timeout, in case the empty constructor was called

  virtual bool connect() {return false;};     // Abstract initialize and connect to the DI-DATAQ device
  virtual void disconnect() {};  // Abstract close the interface to the DI_DATAQ

  virtual bool setWorkMode (uint16_t workMode = DI_WORK_MODE_BINARY); // Set the work mode: binary, ASCII (CDC Mode), binary with date number (For future models, the DI-2108-P doesnt support )
  virtual bool addScanList (uint16_t channelType, uint16_t channelNumber=1, uint16_t channelRange= DI_AI_RANGE_NOT_DEFINED, uint16_t acqMode=DI_ACQ_MODE_LAST_POINT); // Add the channel configuration to the Scan List, need to call setScanList after
  virtual bool setDigBitsMode(uint16_t digBitsMode); // Set digital mode for all digital channels using command endo <bits in switch>
  virtual bool setPackSize( uint32_t packSize); // Set the Package Size
  virtual bool setSampleRate (uint32_t sampleRateHz); // Set the Sample Rate in Hertz by sending scan rate and dec
  virtual void reset() {};  // Abstract reset the interface
  virtual void setupCommParam();    // Setup main communication parameters, this method can be customized in child classes


  // for recording
  void recordTime(tDataChannels & data, double timesec, uint32_t limitMin =0); // Record data for time (seconds) or fraction of it
  bool loadRecordConfig (string fileName,  tRecordConfig &recConfig); // Read the recording configuration from .ini file
  void cyclicRecord ( const tRecordConfig &recConfig); // cyclic recording based on the recording configuration
  bool loadConfigCyclicRecord (string fileName); // Load or read the configuration from file and starting cyclic record
  bool writeDataFile (const tDataChannels &data, string fileName, bool overwrite=true, uint16_t precision = SET_DEC_PRECISION); // Write in text file the data, the file will be overwritten if exist
  bool createLockFile (string fileName); // Create an empty file with the lck at the end as signal for other process want to read the file was done
  bool deleteLockFile (string fileName); // Delete lock file, return true if the file was deleted, otherwise return false

  // Read & Parsing the data
  virtual bool readData( tDataChannels & data);  //get the voltage readings, timeout=0 is blocking operation
  virtual bool parsingData ( tDataChannels & data, uint16_t &scanIndex, unsigned char *buffer, int bufferSize); // Parsing the raw data read from buffer, scaling and put into the data structure

  // start/stop
  virtual void startScan();              //start scanning
  virtual void stopScan();               //stop scanning

  // get/set parameters
  virtual string getFirmware();  // Get the Firmware from device
  virtual string getSerialNum(); // Get the serial number from device
  virtual string getDeviceInfo(); // Get the device Info DATAQ, it is used for checking if can read from the device
  virtual bool readDividend (); // Get the dividend number used for sample rate and scan rate/dec factors determination
  virtual void setDebugMode (bool debugMode); // Set debug mode
  virtual void showDeviceModels(); // Show device models listed
  virtual bool resetCounter(); // Reset the Counter

  // Digital Operations (outside of scan cycle)
  virtual bool writeDigBits (uint16_t digBits); // Write digital input bits defined as switch (Output)
  virtual bool readDigBits (uint16_t &digBits); // Read current digital input bits status

  // Set scan list
  void initScanList(); // Init scan list of channels configuration
  bool setScanList();  // set the scan list defined with addScanList
  bool setAcqMode (); // Set the Acquisition mode all Analog Input channels acqMode: 0-Last point, 1- Average, 2-Maximum, 3-Minimum
  void initModelConfig(tModelConfig &model); // Init model configuration parameters
  void getModelConfig(tModelConfig &model); // Get Model configuration parameters

  //status
  bool isRunning() { return isRun;}            //is the DI-DATAQ running?
  bool isReading(){ return isRead;}            //is it reading data?
  bool isInitialized() {return isInit;}        //is the interface initiaized?
  bool isDebugging() {return isdebug; }        // is it debugging
  uint16_t getTotalChannels() {return scanList.size();}  //Get the total channels
  uint32_t getDividend() { return config.dividend;}   //Get Dividend, this is important factor to set sample rate

  // other functions
  void initData (tDataChannels & data);  // init records
  void showData (const tDataChannels &data); // show data records based on channels scan list
  uint64_t getTimestamp(); // Get current timestamp in ms (time since epoch)

  virtual string sendMessage(string message) {return "error";};  // Abstract send a message to the DI-DATAQ, return the response
  virtual int readBuffer ( unsigned char *received, uint32_t limit, uint32_t timeoutms) {return 0;}; // Abstract Read raw data from device and put into the received
  virtual void clearInput(){};       // Clear Input Buffer from device to ensure it is new starting

  // Configuration based on Device Model
  bool setChannelConfig (tChannelConfig &channel, uint16_t deviceModel, uint16_t channelType,  uint16_t channelNumber=1, uint16_t channelRange=DI_AI_RANGE_NOT_DEFINED, uint16_t acqMode=DI_ACQ_MODE_LAST_POINT); // Return the configuration value based on configuration table & Device Model
  bool detDeviceConfig(); // Determine the Device Model main parameters configuration based on Product Model

  void initRecBuffer();    // Initialize the receiving buffer
  string getParamFromResp (string response, string cmd); // Get the parameter in the respond from a command


 protected:


  bool isRun;
  bool isRead;
  bool isInit;
  bool isdebug = false;

  tScanList scanList; // detail about channel list

  unsigned char received[BUFFER_LIMIT];
  uint16_t scanIndex =0; // scan index into the scanlist vector to keep tracking of channels already read and parse

  uint32_t timeoutms; // timeout ms

  string serialNum; // Serial Number

  tModelConfig config; // Model config some paramers are determine when calling detDeviceIDs, setSampleRate, readDividend

};

#endif // DATAQ_BASE_H
