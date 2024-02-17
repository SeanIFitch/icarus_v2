#include <QCoreApplication>
#include <dataq_usb.h>
#include <bitset>
//***********************************************************************************************************************
// Read example using the recordTime for Batch recording
// Save in a recording file

void ReadExample1()
{
  cout << "Start Example 1- Using simple recordTime for batch processing (DI-2108P)" << endl;

  DATAQ_USB  dev("DI-2108P", 1000, "6059A55E"); // Configure to work with DI-2108P, use timeout of 1 sec

  dev.setDebugMode(true); // set debug mode

  dev.connect();  // Discovery, connect and setup default communication parameters

  dev.setSampleRate(160000);  // Set the sample rate throughput

  // Configure the channels for scan list
  dev.addScanList(DI_CHANNEL_TYPE_AI, 1, DI_AI_RANGE_BIPOL_5VDC); // 1st-Channel 1- +/- 5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 2, DI_AI_RANGE_BIPOL_10VDC); // 2nd- Channel 2- +/- 10 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 3, DI_AI_RANGE_BIPOL_2_5VDC); // 3rd- Channel 3- +/- 2.5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 4, DI_AI_RANGE_UNIPOL_5VDC); // 4th- Channel 4- 0-5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 5, DI_AI_RANGE_UNIPOL_5VDC); // 5th- Channel 5- 0-5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_DIG, 9); // Digital Inputs Status
  dev.addScanList(DI_CHANNEL_TYPE_RATE, 10); // Rate Status
  dev.addScanList(DI_CHANNEL_TYPE_COUNT, 11); // Counter Status

  cout << "Serial Number: " << dev.getSerialNum() << endl;

  tDataChannels data;

  dev.recordTime(data, 1); // record for few seconds

  dev.disconnect(); // close communication

//  dev.showData(data); // Print all the data based on scan list channel

  // Save records in a file
  dev.writeDataFile(data, "test1.txt"); // write all data using same format as showData but in a text file

  cout << "End Example 1..." << endl;
}


//***********************************************************************************************************************

// Simple read example using the startScan, readData, stopScan for realtime monitoring

void ReadExample2()
{
  cout << "Start Example 2- Using startScan/stopScan  (DI-2108P)" << endl;

  DATAQ_USB  dev("DI-2108P", 2000);

  dev.connect();  // Discovery the device, connect and setup default communication parameters

  dev.setSampleRate(8000);  // Set the sample rate throughput

  // Configure the channels for scan list
  dev.addScanList(DI_CHANNEL_TYPE_AI, 1, DI_AI_RANGE_BIPOL_5VDC); // 1st-Channel 1- +/- 5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 2, DI_AI_RANGE_BIPOL_10VDC); // 2nd- Channel 2- +/- 10 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 3, DI_AI_RANGE_BIPOL_2_5VDC); // 3rd- Channel 2- +/- 2.5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 4, DI_AI_RANGE_UNIPOL_5VDC); // 4th- Channel 2- 0-5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_DIG, 9); // Digital Inputs Status
  dev.addScanList(DI_CHANNEL_TYPE_RATE, 10); // Rate Status
  dev.addScanList(DI_CHANNEL_TYPE_COUNT, 11); // Counter Status

  tDataChannels data;

  dev.startScan(); // start scanning and broadcasting the realtime data

  // if place initData outside the reading loop, all data read will be added into the vectors
 //  dev.initData(data);

  for (uint16_t i=0; i< 10; i++) // reading loop
  {
    cout << " ****  Reading Loop: " << i+1 << endl;

    // if place initData just before readData, the data read starting at index 0
     dev.initData(data);

    // read and parsing the data
    // It is important to do this step very quickly to remove bytes from usb input buffer
    // otherwise the device can get an error if its iternal buffer get full

    if (!dev.readData(data))
    {
      cout << "[ERROR] No data was read" << endl;
      break;
    }

    // Do something with the data
    // Show the data
    dev.showData(data);

  } // reading loop

  dev.stopScan(); // stop the scan

  dev.disconnect(); // close communication

  cout << "End Example 2..." << endl;
}

//***********************************************************************************************************************

// Read example using the startScan, readData, stopScan for realtime monitoring and set different parameters

void ReadExample3()
{
  cout << "Start Example 3- Using startScan/stopScan and set different parameters (DI-2108P)" << endl;

  DATAQ_USB  dev("DI-2108P", 2000);

  dev.setDebugMode(true); // Set debug mode for tracking: true- enable, false- disable

  dev.connect();  // Discovery the device, connect and setup default communication parameters

  // Show Device Info (DATAQ)
  cout << " Device Info: " << dev.getDeviceInfo() << endl;

  // Show Firmware version
  cout << " Firmware Version: " << dev.getFirmware() << endl;

  // Show Serial Number Version
  cout << " Serial Number: " << dev.getSerialNum() << endl;


  // Work Mode: DI_WORK_MODE_BINARY, DI_WORK_MODE_ASCII, DI_WORK_MODE_BINARY_2
  dev.setWorkMode( DI_WORK_MODE_BINARY); // Example how to set Work mode


  // By default is set to 64 bytes to cover high frequency.
  // you should adjust packet size as a function of both sampling rate and the number of enabled channels
  // to minimize latency when channel count and sample rate are low, and avoid a buffer overflow when sampling rate and channel count are high
  // Package Size: DI_PACK_SIZE_16_BYTES, DI_PACK_SIZE_32_BYTES, DI_PACK_SIZE_64_BYTES, DI_PACK_SIZE_128_BYTES, DI_PACK_SIZE_256_BYTES, DI_PACK_SIZE_512_BYTES,
  //               DI_PACK_SIZE_1024_BYTES, DI_PACK_SIZE_2048_BYTES

  dev.setPackSize(DI_PACK_SIZE_32_BYTES); // Example of how set package size to 32 bytes, each channel consume 2 bytes (Word)

  dev.setSampleRate(8000);  // Set the sample rate throughput

  // Configure the channels for scan list
  dev.addScanList(DI_CHANNEL_TYPE_AI, 1, DI_AI_RANGE_BIPOL_5VDC); // 1st-Channel 1- +/- 5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 2, DI_AI_RANGE_BIPOL_10VDC); // 2nd- Channel 2- +/- 10 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 3, DI_AI_RANGE_BIPOL_2_5VDC); // 3rd- Channel 2- +/- 2.5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_AI, 4, DI_AI_RANGE_UNIPOL_5VDC); // 4th- Channel 2- 0-5 VDC
  dev.addScanList(DI_CHANNEL_TYPE_DIG, 9); // Digital Inputs Status
  dev.addScanList(DI_CHANNEL_TYPE_RATE, 10); // Rate Status
  dev.addScanList(DI_CHANNEL_TYPE_COUNT, 11); // Counter Status

  tDataChannels data;

  dev.startScan(); // start scanning and broadcasting the realtime data

  for (uint16_t i=0; i< 10; i++) // reading loop
  {
    cout << " ****  Reading Loop: " << i+1 << endl;

    // if place initData just before readData, the data read starting at index 0
     dev.initData(data);

    // read and parsing the data
    // It is important to do this step very quickly to remove bytes from usb input buffer
    // otherwise the device can get an error

    if (!dev.readData(data))
    {
      cout << "[ERROR] No data was read" << endl;
      break;
    }

    // Do something with the data
    // Show the data
    dev.showData(data);

  } // reading loop

  dev.stopScan(); // stop the scan

  dev.disconnect(); // close communication

  cout << "End Example 3..." << endl;
}


//***********************************************************************************************************************

// Read example using load config .ini file and cyclic recording
// the config.ini should be in same place that the executable, check dataq_base.h for the structure of config.ini

void ReadExample4()
{

  cout << "Start Example 4- Read example using load config .ini file and cyclic recording (DI-2108P)" << endl;

  DATAQ_USB  dev;

  tRecordConfig config;

  if (!dev.loadRecordConfig("/opt/sdc/core/dataq/config.ini", config)) // Load configuration file
  {
     cout << "[ERROR] Could not load record config file 'config.ini' record operation aborted" << endl;
     return;
  }

  dev.cyclicRecord(config); // perform cyclic recording as per configuration file with minimum records

  cout << "End File Recording..." << endl;

  exit(-1);

};


//***********************************************************************************************************************

// Read example using load config .ini file and cyclic recording passing from command line
// the config.ini should be in same place that the executable, check dataq_base.h for the structure of config.ini

void ReadExample5(string fileName)
{

  cout << "Start Example 5- Read example using load config .ini file passing from command line and cyclic recording (DI-2108P)" << endl;

  DATAQ_USB  dev;

  dev.loadConfigCyclicRecord (fileName);

  cout << "End File Recording..." << endl;

  exit(-1);

};

int main(int argc, char *argv[])
{
    QCoreApplication a(argc, argv);

//    ReadExample1(); // Recording for some time, uses as batch processing

//    ReadExample2(); // Read data by small chunk for realtime processing

//    ReadExample3(); // Read data  for realtime processing and set different parameters

//    ReadExample4(); // Read example using load config .ini file and cyclic recording

    if (argc ==2) // the first one is the main program, and second argument is the first one
      ReadExample5(string(argv[1])); // Read example using load config .ini file passed as argument in command line and cyclic recording

    return a.exec();
}
