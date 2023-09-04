# ISAC UAV Dataset

Contains scripts and code demo to work with the ISAC UAV Dataset from the EMS Group at TU Ilmenau.
Please note that due to large filesizes of the dataset, this repository does not contain the actual dataset.
Instead, the files are downloaded by the code in this repository. 
Below, we outline the download process and provide a simple demo for the dataset.

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

Calling for help is always an option when something is not clear.   
```
python downloader.py --help
```

Before downloading, you need to enter a password, then the files will be downloading, decrypted, and unzipped in the main folder automatically.  
For the password please contact anyone below:  
steffen.schieler@tu-ilmenau.de  
carsten.smeenk@tu-ilmenau.de  
zhixiang.zhao@tu-ilmenau.de  

**Step 2: Plot**  
You need to use '-p' and specify the '.h5' data files, namely channel dataset and target dataset, which should be placed in the main folder.    
```
python postprocessing.py -c channel.h5 -t target.h5 -p
```

**Optional: Slice the channel**  
You can also slice the channel using '-s' by giving three idx: idx_snapshot idx_Tx idx_Rx
```
python postprocessing.py -c channel.h5 -t target.h5 -s idx_snapshot idx_Tx idx_Rx

```
# License
This dataset (and all remote files associated with it) is licensed under the [Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International](https://creativecommons.org/licenses/by-nc-nd/4.0/legalcode) License.

To use this dataset and/or scripts or any modified part of them, cite:
```
@INPROCEEDINGS{10133118,
  author={Beuster, Julia and Andrich, Carsten and Döbereiner, Michael and Schieler, Steffen and Engelhardt, Maximilian and Schneider, Christian and Thomä, Reiner},
  booktitle={2023 17th European Conference on Antennas and Propagation (EuCAP)}, 
  title={Measurement Testbed for Radar and Emitter Localization of UAV at 3.75 GHz}, 
  year={2023},
  pages={1-5},
  doi={10.23919/EuCAP57121.2023.10133118}
}
```

The paper is available on [IEEEXplore](https://ieeexplore.ieee.org/document/10133118) and [Arxiv](https://arxiv.org/abs/2210.07168).

Please cite the IEEEXplore paper if you use the dataset for your publication.
