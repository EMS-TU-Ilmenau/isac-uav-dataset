# dataset-demo

Demo repository for sharing of a dataset.

## Getting started

This depository is used to download and demonstrate the dataset and two steps is needed.

**Step 1: Download**  
You can go with:
```
python downloader.py
```
which will bring you into default mode. In this case, all scenarios will be downloaded.  

Or you can also specify scenarios with:  
```
python downloader.py -s SCENARIO [SCENARIO_1, SCENARIO_2, ...]
```
in this way you need to pass a list of desired scenarios.  

Before it starts to download, you need to enter a password, then the files will be downloaded, decrypted, and unzipped in the main folder automatically.
For the password please contact anyone below:  
steffen.schieler@tu-ilmenau.de  
carsten.smeenk@tu-ilmenau.de  
zhixiang.zhao@tu-ilmenau.de  

**Step 2: Plot**  
You need to specify the name of '.h5' data files, which should be placed in the main folder, namely channel dataset and target dataset.  
```
python postprocessing.py -c channel.h5 -t target.h5
```

# License
This dataset (and all remote files associated with it) is licensed under the [Creative Commons Attribution Share Alike 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/) License.

To use this dataset and/or scripts or any modified part of them, cite:
```
@Article{FancyDataset2022,
author = {Contributor 1, Contributor 2, ...},
title = {Our Fancy Dataset},
journal={See you on Scihub or Arxiv},
year = {2022},
url = {https://www.tu-ilmenau.de/ems},}
```
