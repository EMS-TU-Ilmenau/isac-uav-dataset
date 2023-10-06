import h5py
import numpy as np
from dataclasses import dataclass, field
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import argparse
matplotlib.use('webagg')

__author__ = "steffen.schieler@tu-ilmenau.de, FG EMS"
__credits__ = "Zhixiang Zhao, Carsten Smeenk"
__all__ = ["UAVDataset"]

H5_CDATA = "Channel/FrequencyResponses/Data"
H5_TARGET_DELAY = "TargetParameters/Delay/Data"
H5_TARGET_DOPPLER = "TargetParameters/Doppler/Data"
H5_TXANTENNA = "AntennaPositions/PositionTx/Data"
H5_RXANTENNA = "AntennaPositions/PositionRx/Data"
H5_UAVPOSITIONS = "Positions/Data"

MARKER_STYLE = dict(
    linestyle="none",
    markersize=10,
    marker="o",
    fillstyle="none",
    markeredgewidth=1.5,
    color="none",
    markerfacecolor="none",
    markerfacecoloralt="none",
    markeredgecolor="red",
)


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
        self.channel = np.array(h5_channel[H5_CDATA]).view(
            np.complex64).squeeze()
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
            self.uav = np.array(h5_target[H5_UAVPOSITIONS]).view(
                np.float64).squeeze()

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


def get_channel(x: np.ndarray, start_idx: int, window_slowtime: int) -> np.ndarray:
    if start_idx > x.shape[0] - window_slowtime:
        raise ValueError(
            "Start index must be smaller than the number of slowtime samples minus the window size.")

    x = x[start_idx:start_idx+window_slowtime, :]
    y = np.fft.fftshift(np.fft.fft(np.fft.ifft(x, axis=1), axis=0), axes=0)
    y /= np.linalg.norm(y)

    return y


def get_groundtruth(x: np.ndarray, start_idx: int, window_slowtime: int):
    if start_idx > x.shape[0] - window_slowtime:
        raise ValueError(
            "Start index must be smaller than the number of slowtime samples minus the window size.")

    delay = x[start_idx+window_slowtime//2, 0]
    doppler = x[start_idx+window_slowtime//2, 1]

    return np.array([delay, doppler])


def get_data(channel: np.ndarray, groundtruth: np.ndarray, window_slowtime: int, start_idx: int):
    channel = get_channel(channel, start_idx, window_slowtime)
    groundtruth = get_groundtruth(groundtruth, start_idx, window_slowtime)
    return channel, groundtruth


def update_fig(fig: plt.Figure, ax: plt.Axes, channel: np.ndarray, groundtruth: np.ndarray):
    ax.clear()
    ax.imshow(20*np.log10(np.abs(channel)), aspect="auto",
              cmap="inferno", vmin=-80, vmax=0, extent=[0, 16e-6, +1/(2*320e-6), -1/(2*320e-6)])
    ax.plot(groundtruth[0], groundtruth[1], **MARKER_STYLE)
    ax.set_xlabel("Delay [$\mu s$]")
    ax.set_ylabel("Doppler-Shift [Hz]")
    fig.canvas.draw_idle()
    return fig, ax


def update(fig: plt.Figure, ax: plt.Axes, channel: np.ndarray, groundtruth: np.ndarray, window_slowtime: int, start_idx: int):
    channel_window, groundtruth_window = get_data(
        channel, groundtruth, window_slowtime, start_idx)
    update_fig(fig, ax, channel_window, groundtruth_window)


def main(args):
    dataset = UAVDataset(args.channel_file, args.target_file)
    channel = dataset.channel
    groundtruth = dataset.groundtruth
    window_slowtime = args.window
    num_windows = (channel.shape[0] - window_slowtime) // window_slowtime

    fig, ax = plt.subplots(
        1, 3,
        figsize=(10, 5),
        tight_layout=True,
        gridspec_kw={"width_ratios": [0.05, 1, 0.05]}
    )
    update(fig, ax[1], channel, groundtruth, window_slowtime, 0)
    cbar = plt.colorbar(ax[1].get_images()[0],
                        cax=ax[2], orientation="vertical")
    cbar.set_label("Normalized Power [dB]")
    sample_slider = Slider(
        ax=ax[0],
        label="Index",
        valmin=1,
        valmax=num_windows,
        valinit=1,
        valstep=1,
        orientation="vertical",
    )
    sample_slider.on_changed(lambda slider_value: update(
        fig, ax[1], channel, groundtruth, window_slowtime, slider_value*window_slowtime))
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plotting script for the UAV dataset."
    )
    parser.add_argument(
        "-c", "--channel-file", help="Path to the channel file.", default="1to2_H15_V11_VGH0_channel.h5",
    )
    parser.add_argument(
        "-t", "--target-file", help="Path to the target file.", default="1to2_H15_V11_VGH0_target.h5",
    )
    parser.add_argument(
        "-w",
        "--window",
        help="Length of the slow time window.",
        type=int,
        default=100,
    )
    args = parser.parse_args()

    main(args)
