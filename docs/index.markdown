---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: home
nav_order: 1
---
![](./assets/impressions/banner.jpg)

We proudly present the 
# ISAC UAV Dataset

This dataset aims to provide measurement data for the ISAC, addressing the crucial need for extensive databases to support the development and evaluation of ISAC algorithms.
It contains **RADAR-Localization measurement data** recorded during an outdoor measurement campaign by Technische Universität Ilmenau and Fraunhofer Institute for Integrated Circuits IIS.

The measurement setup targets **multi-static RADAR localization of a UAV** operating in an urban environment.
One could refer to the setup as a distributed basestation scenario, where the UAV is localized by three receivers.
It comprises of an **OFDM illuminator** and three receivers (VGH0, VGH1, VGH2) operating at a carrier frequency of **3.75 GHz** with a bandwidth of **100 MHz**.
Various trajectories for a single-target UAV are recorded, including the position of the UAV (groundtruth).
Due to the nature of the radio propagation environment, the dataset also contains reflections from other targets, such as pedestrians and cars, for which no groundtruth exists.

The dataset provides contains the time-variant Channel Transfer functions in complex-baseband.

{: .note}
The dataset, and in particulary this documentation, are still under active development. 
If you find any errors or missing information, please do not hesitate to [contact us](mailto:steffen.schieler@tu-ilmenau.de).