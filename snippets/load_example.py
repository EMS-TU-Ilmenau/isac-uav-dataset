import h5py
import numpy as np
from dataclasses import dataclass, field

__author__ = "steffen.schieler@tu-ilmenau.de, FG EMS"
__credits__ = "Zhixiang Zhao, Carsten Smeenk"
__all__ = ["Dataset"]

H5_CDATA = "Channel/FrequencyResponses/Data"
H5_TARGET_DELAY = "TargetParameters/Delay/Data"
H5_TARGET_DOPPLER = "TargetParameters/Doppler/Data"
H5_TXANTENNA = "AntennaPositions/PositionTx/Data"
H5_RXANTENNA = "AntennaPositions/PositionRx/Data"
H5_UAVPOSITIONS = "Positions/Data"

@dataclass
class UAVDataset:
    channelfile: str
    """The path to the channel file"""
    targetfile: str = None
    """The path to the target file"""
    channel: np.ndarray = field(init=False)
    """Property to store the channel data as a numpy array"""
    groundtruth: np.ndarray = field(init=False)
    """Property to store the delay and Doppler groundtruth of the UAV as a numpy array"""
    tx: np.ndarray = field(init=False)
    """Property to store the transmitter antenna positions as a numpy array"""
    rx: np.ndarray = field(init=False)
    """Property to store the receiver antenna positions as a numpy array"""
    uav: np.ndarray = field(init=False)
    """Property to store the UAV positions as a numpy array"""
    
    def __post_init__(self) -> None:
        # load channel, positions
        h5_channel = h5py.File(self.channelfile, "r")
        self.channel = np.array(h5_channel[H5_CDATA]).squeeze()
        self.groundtruth = np.concatenate(
            (
                np.array(h5_channel[H5_TARGET_DELAY]),
                np.array(np.array(h5_channel[H5_TARGET_DOPPLER])),
            ),
            axis=1,
        )
        self.tx = np.array(h5_channel[H5_TXANTENNA]).squeeze()
        self.rx = np.array(h5_channel[H5_RXANTENNA]).squeeze()
        
        if self.targetfile is not None:
            h5_target = h5py.File(self.targetfile, "r")
            self.uav = np.array(h5_target[H5_UAVPOSITIONS]).squeeze()
        
        return

    def __str__(self) -> str:
        return f"""
           ---- Dataset Summary ----           
           Channel: \t\t{self.channel.shape}
           Groundtruth: \t{self.groundtruth.shape}
           Antenna Positions: \t{'Loaded' if self.tx is not None else 'Not Loaded'}
           UAV Positions: \t{'Loaded' if self.uav is not None else 'Not Loaded'}
           
           From Files: 
           \t - Channel: {self.channelfile}
           \t - Target: {self.targetfile}
           """

if __name__ == "__main__":
    channel_file = "1to2_H15_V11_VGH0_channel.h5"
    target_file = "1to2_H15_V11_VGH0_target.h5"
    
    dataset = UAVDataset(channel_file, target_file)
    print(dataset)