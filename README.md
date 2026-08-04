# BannerClick

BannerClick is a web privacy measurement tool that is built on top of [OpenWPM](https://github.com/openwpm/OpenWPM).
It is designed to detect and interact with cookie banners.
For more details on how BannerClick works please read [our papers](https://bannerclick.github.io/).

## Installation

We implemented BannerClick as a [custom command](https://github.com/openwpm/OpenWPM/blob/master/custom_command.py) in OpenWPM. Therefore, to run BannerClick first you need to install OpenWPM as follows.

The main pre-requisite for OpenWPM is conda. it is an open-source cross-platform package management tool, and can be installed from https://docs.conda.io/en/latest/miniconda.html.


Next, the `install.sh` script will install all the prerequisites in a separate conda environment named openwpm. 

. To run the install script, run

```bash
./install.sh
```

After running the install script, activate your conda environment by running:

```bash
conda activate openwpm
```
## Firefox Setup

1. Extract the Firefox binary archive:
```bash
tar -xvjf firefox-bin.tar.bz2
```
2. Set the `FIREFOX_BINARY` environment variable to point to the extracted Firefox binary:
```bash
export FIREFOX_BINARY=/path/to/ShadowMap/firefox-bin/firefox-bin
```
> **Note:** Replace `/path/to/ShadowMap` with the absolute path to your project directory.

3. To make this environment variable persistent across terminal sessions, append it to your `~/.bashrc` file and reload your shell:
```bash
echo 'export FIREFOX_BINARY=/path/to/ShadowMap/firefox-bin/firefox-bin' >> ~/.bashrc
source ~/.bashrc
```

## Instruction to start the script :

As an example the following command will run the bannerclick custom command using 8 headless browsers with 5 repetitions for each domain in the `Tranco5Nov.csv` file.

```bash
python run.py --bannerclick --headless --num-browsers 1 --num-repetitions 1 
```
By Default it crawls the domains mentioned at give filepath :
./bannerclick/input-files/Tranco5Nov.csv

## Configuration

Aside from the [configuration](https://github.com/openwpm/OpenWPM/blob/master/docs/Configuration.md) for OpenWPM, there are other parameters that can be modified in [`config.py`](https://github.com/bannerclick/bannerclick/blob/bannerclick_v0.18.0/bannerclick/config.py) to configure BannerClick. Each parameter is documented in the file directly. 

## Fingerprinting Instrumentation :
All modified fingerprinting instrumentaion is defined as : [_'fingerprinting.json'_](https://github.com/Xclusive-Ishan/ShadowMap/blob/main/openwpm/js_instrumentation_collections/fingerprinting.json) 

## References:

DuckDuckGo Tracker Radar : [Github Repo](https://github.com/duckduckgo/tracker-radar.git)

## Attribution

If you use our tool in your research, please reference it with the following citations:

```bibtex
@inproceedings{rasaii2023exploring,
    title = {Exploring the Cookieverse: A Multi-Perspective Analysis of Web Cookies},
    author = {Ali Rasaii and Shivani Singh and Devashish Gosain and Oliver Gasser},
    booktitle = {Proceedings of the 2023 Passive and Active Measurement Conference},
    year = {2023},
    month = mar
}
```

```bibtex
@inproceedings{rasaii2023cookiewall,
    title = {Thou Shalt Not Reject: Analyzing Accept-Or-Pay Cookie Banners on the Web},
    author = {Ali Rasaii and Devashish Gosain and Oliver Gasser},
    booktitle = {Proceedings of the 23rd ACM Internet Measurement Conference},
    year = {2023},
    month = oct
}
```
