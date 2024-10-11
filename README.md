<a name="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/SeanIFitch/icarus_v2">
	<img src="https://raw.githubusercontent.com/SeanIFitch/icarus_v2/main/src/icarus_v2/resources/wing.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">icarus v2</h3>

  <p align="center">
    Monitoring software for the <a href="https://pubmed.ncbi.nlm.nih.gov/29666248/">Icarus</a> NMR pressure jump apparatus
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

![Screen Shot](https://raw.githubusercontent.com/SeanIFitch/icarus_v2/main/src/icarus_v2/resources/app-screenshot.png)

The <a href="https://pubmed.ncbi.nlm.nih.gov/29666248/">Icarus</a> NMR Pressure Jump Apparatus is a novel device used to rapidly switch the pressure within an NMR sample cell. This enables study of the unfolded protein under native conditions and, vice versa, study of the native protein under denaturing conditions. This project is the <a href="https://github.com/vstadnytskyi/icarus-nmr">second</a> version of a monitoring software for the pressure sensors and digital controls. It is responsible for displaying device readings, controlling and testing hardware, and detecting faults. 

Once a DATAQ DI-4108 USB device is detected by the monitoring software, it establishes a connection and begins reading data from the USB device at 4000Hz. The analog and digital channels monitored are as follows:
* Analog:\
	CH0: target pressure sensor\
	CH1: depressurization valve lower sensor\
	CH2: depressurization valve upper sensor\
	CH3: pressurization valve lower sensor\
	CH4: pressurization valve upper sensor\
	CH5: high pressure sensor at the origin\
	CH6: high pressure sensor at the sample
* Digital:\
	CH0: high pressure pump control\
	CH1: depressurize valve control\
	CH2: pressurize valve control\
	CH4: log control

The data is stored in a circular buffer with a default length of 2 minutes. The data is read by many event handlers which each detect certain features in the readings. They then signal events containing their respective data which may be read by the GUI. The event handlers are as follows:
1. Depressurize: detects high to low state transitions in digital CH0
2. Pressurize: detects high to low state transitions in digital CH1
3. Period: detects consecutive high to low state transitions in digital CH1
4. Pressure: detects current pressure of analog CH5
5. Pump: detects drops in analog CH0, signifying the pump stroking
6. Log: detects state changes in digital CH4

The digital channels may be controlled by the software by sending commands to the DATAQ DI-4108. This is used for the following:
1. Toggling the high pressure pump
2. Hardware tests under manual device operation
3. Shutdowns, either manual or when a fatal error is detected by the Sentry

All events are transmitted to the GUI and are rendered in dedicated event plots, history plots, and status indicators. They are also transmitted to a Sentry module which analyzes them to detect leaks and abnormal behavior. In the event of a serious leak, the device will automatically shut down. Pressurize, depressurize, and period events are also transmitted to a logger, which generates LZMA compressed log files. These files may be opened by the GUI for later viewing.


<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* Python >=3.10, <=3.12

* PySide6

* PyQtDarkTheme

* Poetry

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

### Prerequisites

#### System Requirements
* Ubuntu 22.04 LTS or later (primary supported OS)
* Other Linux distributions with Python 3.10-3.12 support may work but are not officially supported
* macOS 11 (Big Sur) or later may work but is not officially supported
* Windows 10 or later may work but is not officially supported

#### Installing Python
Ensure you have Python 3.10-3.12 installed on your system by running the following command. 
```sh
python3 --version
```

If you do not have Python installed, you can install it using the following commands:
```sh
sudo apt update
sudo apt install python3.12
```

### Installation
The recommended method for installation is to install the application globally using pipx. First, install pipx:
```sh
sudo apt install pipx
pipx ensurepath
```
Now, you can install the icarus_v2 package:
```sh
pipx install icarus_v2
```

### Updating
To update the application to the latest version, use:
```sh
pipx upgrade icarus_v2
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- USAGE EXAMPLES -->
## Usage

To start the application, run the following command from any directory:
```sh
icarus
```
* Note: The first time the application is run with a DATAQ connected, it will attempt to install a udev rule to allow access to the USB device. This requires admin permissions. If the application fails to connect to the device after a few seconds, reboot your computer to ensure the udev rules are fully reloaded.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/SeanIFitch/icarus_v2/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Environment Setup
#### Installing Poetry
This project uses poetry to manage dependencies. Install it using:
```sh
curl -sSL https://install.python-poetry.org | python3 -
```

#### Cloning the Repository
Before you can start setting up your environment, you'll need to clone the repository containing the project. Open your terminal and execute the following command:
```sh
git clone https://github.com/YOUR-USERNAME-HERE/icarus_v2
cd icarus_v2
```
#### Installing Dependencies
Now you can initialize the poetry package:
```sh
poetry install
```
#### Run Icarus
To run the main script, you can use the following command from the directory into which you cloned the repository:
```sh
poetry run icarus
```


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Sean Fitch - seanifitch@gmail.com

Project Link: [https://github.com/SeanIFitch/icarus_v2](https://github.com/SeanIFitch/icarus_v2)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* Dr. Philip Anfinrud - Software specification
* [icarus-nmr](https://github.com/vstadnytskyi/icarus-nmr) by Valentyn Stadnytskyi

<p align="right">(<a href="#readme-top">back to top</a>)</p>
