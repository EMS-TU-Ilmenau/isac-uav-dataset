import h5py
import numpy as np
from dataclasses import dataclass, field
import torch
from torch.utils.data import Dataset, DataLoader

__author__ = "steffen.schieler@tu-ilmenau.de, FG EMS"
__credits__ = "Zhixiang Zhao, Carsten Smeenk"
__all__ = ["UAVDataset", "TorchDataset"]

# For an explanation of the following, see the PDF description in the repository
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
        self.channel = np.array(h5_channel[H5_CDATA]).view(np.complex64).squeeze()
        self.groundtruth = np.concatenate(
            (
                np.array(h5_channel[H5_TARGET_DELAY]),
                np.array(h5_channel[H5_TARGET_DOPPLER]),
            ),
            axis=1,
        )
        self.tx = np.array(h5_channel[H5_TXANTENNA]).view(np.float64).squeeze()
        self.rx = np.array(h5_channel[H5_RXANTENNA]).view(np.float64).squeeze()
        
        if self.targetfile is not None:
            h5_target = h5py.File(self.targetfile, "r")
            self.uav = np.array(h5_target[H5_UAVPOSITIONS]).view(np.float64).squeeze()
        
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

class TorchDataset(Dataset):
    def __init__(self, dataset: UAVDataset, t_window: int = 100, return_uavpos: bool = False):
        """Torch Dataset for UAV Channel Data

        Args:
            dataset (UAVDataset): An instance of `UAVDataset`
            t_window (int, optional): The length of the slow-time window. Defaults to 100.
            return_uavpos (bool, optional): Whether to return the RTK UAV position. Defaults to False.

        """        
        self.dataset = dataset
        self.t_window = t_window
        self.return_uavpos = return_uavpos
        
        if return_uavpos and self.dataset.uav is None:
            raise ValueError("UAV Positions not loaded!")
        
        return
    
    def __getitem__(self, idx: int) -> [torch.Tensor, torch.Tensor]:
        if self.return_uavpos:
            return (
                torch.from_numpy(self.dataset.channel[idx: idx + self.t_window]), 
                torch.from_numpy(self.dataset.groundtruth[idx + self.t_window // 2]),
                torch.from_numpy(self.dataset.uav[idx + self.t_window // 2])
            )
        else:
            return (
                torch.from_numpy(self.dataset.channel[idx: idx + self.t_window]), 
                torch.from_numpy(self.dataset.groundtruth[idx + self.t_window // 2]),
            )
    
    def __len__(self) -> int:
        return len(self.dataset)- self.t_window//2
    
    def __str__(self) -> str:
        return str(self.dataset)
    

if __name__ == "__main__":
    channel_file = "1to2_H15_V11_VGH0_channel.h5"
    
    # Example 1: Dataloader with complex baseband and delay-doppler groundtruth
    dataset = UAVDataset(channel_file)
    dataloader = DataLoader(TorchDataset(dataset), batch_size=16, shuffle=True)
    
    X, Y = next(iter(dataloader))
    
    print(f"""
            ---- Dataloader with complex baseband and delay-doppler groundtruth ----
            Number of samples in Dataloader: {len(dataloader)}
            Data shape: {tuple(X.shape)} (bs x t_bins x f_bins)
            Delay-Doppler-Groundtruth shape: {tuple(Y.shape)} (bs x 2)
    """)
    
    # Example 2: Dataloader with complex baseband, delay-doppler groundtruth, and UAV positions
    target_file = "1to2_H15_V11_VGH0_target.h5"
    dataset = UAVDataset(channel_file, target_file)
    dataloader = DataLoader(TorchDataset(dataset, return_uavpos=True), batch_size=16, shuffle=True)
    
    X, Y, Z = next(iter(dataloader))
    
    print(f"""
            ---- Dataloader with complex baseband and delay-doppler groundtruth ----
            Number of samples in Dataloader: {len(dataloader)}
            Data shape: {tuple(X.shape)} (bs x t_bins x f_bins)
            Delay-Doppler-Groundtruth shape: {tuple(Y.shape)} (bs x 2)
            UAV-Position shape: {tuple(Z.shape)} (bs x 3)
    """)