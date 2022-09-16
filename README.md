# dataset-demo

Demo repository for sharing of a dataset.

## Getting started

This depository is used to download and demonstrate the dataset and two steps is needed.

Step 1: Download
You can go with:
'''
python downloader.py
'''
which will bring you into default mode. In this case, all scenarios will be downloaded.

Or you can also specify scenarios with:
'''
python downloader.py -s SCENARIO [SCENARIO_1, SCENARIO_2, ...]
'''
this way you will pass a list of desired scenarios.

After downloading you need to enter a password, the files will be decrypted and unzipped in main folder automatically. 
For the password please contact:
steffen.schieler@tu-ilmenau.de
carsten.smeenk@tu-ilmenau.de
zhixiang.zhao@tu-ilmenau.de

Step 2: Plot
You need to specify the name of data files,which should be placed in the main folder, namely channel dataset and target dataset.
'''
python postprocessing.py -c channel.h5 -t target.h5
'''
