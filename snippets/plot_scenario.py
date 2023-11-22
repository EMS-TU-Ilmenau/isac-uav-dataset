import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import argparse
from uavdataset import UAVDataset
matplotlib.use('webagg')

__author__ = "steffen.schieler@tu-ilmenau.de, FG EMS"
__credits__ = "Zhixiang Zhao, Carsten Smeenk"
__all__ = ["UAVDataset"]

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
    
# def fft_upsample(x: np.ndarray, factor: int) -> np.ndarray:
#     x_n, y_n = x.shape
#     X = np.fft.ifft(np.fft.fft(x, axis=1), axis=0)
#     return np.fft.fft(np.fft.ifft(X, axis=1, n=factor*y_n), axis=0, n=factor*x_n)

def get_channel(x: np.ndarray, start_idx: int, window_slowtime: int, filter_clutter: bool=False, upsample: int = 1) -> np.ndarray:
    if start_idx > x.shape[0] - window_slowtime:
        raise ValueError(
            "Start index must be smaller than the number of slowtime samples minus the window size.")
        
    x = x[start_idx:start_idx+window_slowtime+1, :]
    if filter_clutter:
        x = np.diff(x, n=1, axis=0)
    
    t_n, f_n = x.shape 
    y = np.fft.fft(np.fft.ifft(x, n=f_n*upsample, axis=1), n=t_n*upsample, axis=0)
    y /= np.linalg.norm(y)
    y = np.fft.fftshift(y, axes=0)
    y = y[:, :80*upsample]
    
    return y

def get_groundtruth(x: np.ndarray, start_idx: int, window_slowtime: int):
    if start_idx > x.shape[0] - window_slowtime:
        raise ValueError(
            "Start index must be smaller than the number of slowtime samples minus the window size.")

    delay = x[start_idx+window_slowtime//2, 0]
    doppler = x[start_idx+window_slowtime//2, 1]

    return np.array([delay, doppler])


def get_data(channel: np.ndarray, groundtruth: np.ndarray, window_slowtime: int, start_idx: int):
    channel = get_channel(channel, start_idx, window_slowtime, filter_clutter=True, upsample=2)
    groundtruth = get_groundtruth(groundtruth, start_idx, window_slowtime)
    return channel, groundtruth

def update_fig(fig: plt.Figure, ax: plt.Axes, channel: np.ndarray, groundtruth: np.ndarray):
    ax.clear()
    ax.imshow(20*np.log10(np.abs(channel)), aspect="auto",
              cmap="inferno", vmin=-60, vmax=0, extent=[0, 1e-6, +1/(2*320e-6), -1/(2*320e-6)])
    ax.plot(groundtruth[0], groundtruth[1], **MARKER_STYLE)
    ax.set_xlabel("Delay [$s$]")
    ax.set_ylabel("Doppler-Shift [Hz]")
    fig.canvas.draw_idle()
    return fig, ax

def update(fig: plt.Figure, ax: plt.Axes, channel: np.ndarray, groundtruth: np.ndarray, window_slowtime: int, start_idx: int):
    channel_window, groundtruth_window = get_data(
        channel, groundtruth, window_slowtime, start_idx)
    update_fig(fig, ax, channel_window, groundtruth_window)
    
def update_all(fig: plt.Figure, ax: list[plt.Axes,], channel: list[np.ndarray,], groundtruth: list[np.ndarray,], window_slowtime: int, start_idx: int):
    for aa, cc, gg in zip(ax, channel, groundtruth):
        update(fig, aa, cc, gg, window_slowtime, start_idx)


def main(args):
    rxs = ["VGH0", "VGH1", "VGH2"]
    dataset = [
        UAVDataset(f"{args.scenario}_{rx}_channel.h5",
                   f"{args.scenario}_{rx}_target.h5",
        ) for rx in rxs
    ]
    channel = [
        d.channel for d in dataset
    ]
    groundtruth = [
        d.groundtruth for d in dataset
    ]
    window_slowtime = args.window
    num_windows = (len(dataset[0]) - window_slowtime) // window_slowtime

    fig, ax = plt.subplots(
        1, 5,
        figsize=(16, 5),
        tight_layout=True,
        gridspec_kw={"width_ratios": [0.05, 1, 1, 1, 0.05]},
    )
    update_all(fig, ax[1:4], channel, groundtruth, window_slowtime, 0)
    ax[1].set_title("VGH0")
    ax[2].set_title("VGH1")
    ax[3].set_title("VGH2")
    cbar = plt.colorbar(ax[1].get_images()[0],
                        cax=ax[-1], orientation="vertical")
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
    sample_slider.on_changed(lambda slider_value: update_all(
        fig, ax[1:4], channel, groundtruth, window_slowtime, slider_value*window_slowtime))
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Plotting script for the UAV dataset."
    )
    parser.add_argument(
        "-s", "--scenario", help="Scenario name.", default="1to2_H15_V11",
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
