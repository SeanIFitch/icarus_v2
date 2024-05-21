<a name="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/SeanIFitch/icarus_v2">
    <img src="images/wing.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">Icarus v2</h3>

  <p align="center">
    Monitoring software for the Icarus NMR pressure jump apparatus
    <br />
    <a href="https://pubmed.ncbi.nlm.nih.gov/29666248/">Pressure Jump Apparatus</a>
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

![Product Name Screen Shot](product-screenshot)


<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Next][Next.js]][Next-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Prerequisites

#### System Requirements
These instructions are tailored for Ubuntu 24, which is the only operating system tested and supported for this setup.

#### Installing Python
Ensure you have Python 3.10 installed on your system. If you do not have Python 3.10 installed, you can install it using the following commands:
```sh
sudo apt update
sudo apt install python3.10
```
#### Cloning the Repository
Before you can start setting up your environment, you'll need to clone the repository containing the project. Open your terminal and execute the following command:
```sh
git clone https://github.com/SeanIFitch/Icarus_v2
cd Icarus_v2
```

This is an example of how to list things you need to use the software and how to install them.
* npm
  ```sh
  npm install npm@latest -g
  ```

### Installation

#### Setting Up Your Environment
1. Create a Virtual Environment:
Use a virtual environment to manage dependencies effectively and avoid conflicts between package versions. Run the following command in your project directory to create a virtual environment:
   ```sh
   python3.10 -m venv venv
   ```
2. Activate the Virtual Environment:
Once the virtual environment is created, activate it with:
   ```sh
   source venv/bin/activate
   ```
#### Installing Dependencies
With the virtual environment activated, you can now install all required packages from required-packages.txt. Install these packages by running:
   ```sh
   pip install -r required-packages.txt
   ```


<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

To run the application, use:
   ```sh
   python3 src/main.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

See the [open issues](https://github.com/SeanIFitch/Icarus_v2/issues) for a full list of proposed features (and known issues).

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

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Sean Fitch - seanifitch@gmail.com

Project Link: [https://github.com/SeanIFitch/Icarus_v2](https://github.com/SeanIFitch/Icarus_v2)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* Dr. Philip Anfinrud - Software design
* [icarus-nmr](https://github.com/vstadnytskyi/icarus-nmr) by Valentyn Stadnytskyi

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[product-screenshot]: images/example-log-screen.png
[Next.js]: https://img.shields.io/badge/next.js-000000?style=for-the-badge&logo=nextdotjs&logoColor=white
[Next-url]: https://nextjs.org/