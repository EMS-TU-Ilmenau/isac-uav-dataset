---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: page
permalink: /gettingstarted/
title: Getting started
nav_order: 1
---

# Getting Started
Hello and welcome to the ISAC UAV Dataset from Technische Universität Ilmenau. 
This page will help you get started with the dataset and provide you with some useful information.

Before downloading the dataset, we want to familiarize you with the structure of the dataset and the provided files.

{: .important}
Please read this section carefully to avoid wasting your costly time in premature self-exploratory efforts.

## Dataset organization
The dataset is organized in `scenarios`.
Each scenario contains a series of complex-baseband, time-variant channel transfer functions $$H(f,t)$$ recorded at three receivers (Rx). 
Files that contain sampled transfer-functions use the `_channel.h5` suffix.

In addition to the channel transfer functions, the groundtruth position of the UAV is provided in an additional file. 
Files that contain sampled transfer-functions use the `_target.h5` suffix.
Hence, each scenario consists of six files:
- 1 file for each Rx (3 in total)
- 3 identical target files (1 for each Rx)

{: .note}
The redundant copies of the target files are provided in case only a single Rx is studied.  

{: .important} 
For security purposes, the dataset is currently encrypted.  

To obtain the password required for the encryption, pleas [drop us a short email](mailto:steffen.schieler@tu-ilmenau.de) and state where you are from and how you want to make use of the dataset.
A really brief explanation is sufficient :)

# Preparations

In its current state, the dataset contains 60 different scenarios in 360 files. 
The total required disk space is about 200 GB.
As Git is not suitable (at least not without extensions) to store such large datasets, the dataset is stored on a different server at TU Ilmenau [1].
The repository provides a script `downloader.py` to download the dataset from the server. 

![Repository Structure](../assets/repository_structure.png)

We tried to keep the requirements minimal, but in case you experience any issues please check the `requirements.txt` file in the repository.

{: .note}
You can run `python -m pip install -r requirements.txt` from the repository root to install the required packages.

# Downloading the dataset

Clone this repository using the following command:
```
git clone https://github.com/EMS-TU-Ilmenau/isac-uav-dataset.git
```

![Cloning the repository](../assets/demo_clone.gif)

The `downloader.py` script provides a command-line interface to download the dataset.
It takes care of the download, decryption, unpacking, and verification of files.
Shasum hashes for the files in the `scenarions.shasums` also provide a way to track changes of the provided dataset files for the users (via the history of `scenarions.shasums`).

To download all available files, simply run the `downloader.py` script without any arguments:
```
python downloader.py
```
which will bring you into default mode.
In this case, all available scenarios will be downloaded.

{: .warning}
The full dataset consumes about 200 GB of disk space. Correspondingly, the time required to download all scenarios will depend on your internet connection. When working with a remote machine, we recommend a `screen` or `tmux` session.


![Cloning the repository](../assets/demo_downloader.gif)

Alternatively, you can also specify scenarios with:  
```
python downloader.py --scenario SCENARIO_1 SCENARIO_2 ... SCENARIO_N
```
Pass the desired scenarios separated by spaces, e.g.,
```
python downloader.py --scenario 1to2_H15_V11 2to3_H15_V11
```

To see all available options run:
```
python downloader.py --help
```

{: .note}
If you entered a wrong password `downloader.py`, just re-run the script. In this case, it will not re-download the file and instead access the previously downloaded version stored in the `.tmp` folder.


{: .fs-3}  
**Footnote**

{: .fs-2}
[1] - We want to thank Henning Schwanbeck from the Technische Universität Ilmenau Rechenzentrum for his continuous support with the provisioning of the measurement files.