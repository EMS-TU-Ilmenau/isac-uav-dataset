import h5py
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Slider, Button


class PostprocessBase:
    def __init__(self, channel_file_path: str, target_file_path):
        # load channel, positions
        channel, groundtruth, positions = PostprocessBase.load_dataset(channel_file_path, target_file_path)

        # init plot
        self.slider_figure = Plot_With_Slider(channel_dataset=channel, groundtruth=groundtruth, positions=positions)

    def show(self) -> None:
        """
        ###########
        RUN THIS TO SHOW FIGURE !!
        ###########
        """
        plt.show()

    @staticmethod
    def fft(data: np.ndarray) -> np.ndarray:
        data = np.fft.fft(data, axis=1)
        data = np.fft.fftshift(data, axes=1)
        data = np.fft.ifft(data, axis=0)
        data = 20 * np.log10(abs(data))
        return data

    @staticmethod
    def time_window_len(resolution: float) -> int:
        """

        :param resolution: define a resolution, then based on this calculate the corresponding window length
        :return: window_len: int
        """
        window_len = 1280
        return window_len

    @staticmethod
    def load_dataset(channel_file_path: str, target_file_path: str):
        """
        load channel and positions
        """
        Channel_file = h5py.File(channel_file_path, 'r')
        Target_file = h5py.File(target_file_path, 'r')

        channel = np.array(Channel_file['Channel/FrequencyResponses/Data'])

        gt_Doppler = np.array(Channel_file['TargetParameters/Doppler/Data'])
        gt_Delay = np.array(Channel_file['TargetParameters/Delay/Data'])
        groundtruth = np.concatenate((gt_Delay, gt_Doppler), axis=1)  # size x [delay, doppler]

        positions = {
            'positionRx': np.array(Channel_file['AntennaPositions/PositionRx/Data']),
            'positionTx': np.array(Channel_file['AntennaPositions/PositionTx/Data']),
            'positionUAV': np.array(Target_file['Positions/Data'])
        }

        return channel, groundtruth, positions


class Plot_With_Slider:
    def __init__(self, channel_dataset: np.ndarray, groundtruth: np.ndarray, positions: dict):
        # setup measurement parameters
        self.sampling_frequency = 1 / (20 * 16e-6)  # slow time domain, in Hz
        self.tau_max = 16e-6  # inverse of the sub-carriers space, in s
        self.num_subcarriers = channel_dataset.shape[3]

        # load dataset
        self.channel = channel_dataset
        self.groundtruth = groundtruth
        self.positionRx = positions['positionRx']
        self.positionTx = positions['positionTx']
        self.positionUAV = positions['positionUAV']

        # calculate window length in time domain
        self.window_len = PostprocessBase.time_window_len(1)

        # init plot
        self.fig = None
        self.plt_channel = None
        self.plt_gt = None
        self.plt_uav_posi = None
        self.snapshot_slider = None
        self.tx_slider = None
        self.rx_slider = None
        self.button = None
        self.scale = self._position_scale()

        self._init_figure()

    def _init_figure(self):
        """
        initialize figures
        ========================
        Part_1: Doppler_range map
        Part_2: Normalized positions of TX, Rx, and target. Tx as the reference position
        Part_3: Sliders for snapshots, Tx ports, Rx Ports. A reset button is also built.
        """
        data_init, gt_init, uav_posi_init = self._slice_process_data(idx={'idx_snapshot': 0, 'idx_rx': 0, 'idx_tx': 0})  # init data
        self.fig = plt.figure(figsize=(20, 10))
        gs = GridSpec(20, 40, figure=self.fig)  # The whole figure is organized as (row x col)

        # ------------------------------ Doppler-range map ------------------------------
        points_on_axis = 11  # Must be an odd number, to make sure that zero is on axis
        self.fig.add_subplot(gs[1:14, 4:20])  # set position of the plot
        self.plt_channel = plt.imshow(data_init, origin='lower')  # plot doppler range map
        self.plt_gt = plt.scatter(x=gt_init[1], y=gt_init[0], c='r', marker='x')  # mark target
        plt.xticks(ticks=np.linspace(0, self.window_len, points_on_axis),
                   labels=np.round(np.linspace(-self.sampling_frequency / 2, self.sampling_frequency / 2, points_on_axis)))
        plt.yticks(ticks=np.linspace(0, self.num_subcarriers, points_on_axis),
                   labels=np.round(np.linspace(0, self.tau_max * 1e6, points_on_axis)))
        plt.legend(handles=[self.plt_gt], labels=['Target'])
        plt.xlabel('Doppler/Hz')
        plt.ylabel('Delay/μs')
        plt.title('Delay-Doppler map')

        # ------------------------------ Normalized positions ------------------------------
        self.fig.add_subplot(gs[1:14, 20:36])
        posi_Rx = (self.positionRx[0, :2] - self.positionTx[0, :2]) / self.scale + 0.5  # calculate normalized positions
        plt_tx_posi = plt.scatter(x=0.5, y=0.5, c='k', marker='o')
        plt_rx_posi = plt.scatter(x=posi_Rx[0], y=posi_Rx[1], c='g', marker='o')
        self.plt_uav_posi = plt.scatter(x=uav_posi_init[0], y=uav_posi_init[1], c='r', marker='x')
        plt.xticks(ticks=np.linspace(0, 1, 11), labels=np.round(np.linspace(-0.5, 0.5, 11), 1))
        plt.yticks(ticks=np.linspace(0, 1, 11), labels=np.round(np.linspace(-0.5, 0.5, 11), 1))
        ax = plt.gca()
        ax.set_aspect(1)
        plt.grid()
        plt.xlim((0, 1))
        plt.ylim((0, 1))
        plt.legend(handles=[self.plt_uav_posi, plt_tx_posi, plt_rx_posi], labels=['Target', 'Tx', 'Rx'], loc='best')
        plt.title('Position map (Top view)')

        # ------------------------------ Sliders and reset button ------------------------------
        num_snapshots = self.channel.shape[0] // self.window_len
        self.fig.add_subplot(gs[16, 10:30])
        self.snapshot_slider = Slider(ax=plt.gca(), label='Idx_snapshot', valinit=1, valmin=1, valmax=num_snapshots,
                                      valstep=1, orientation='horizontal')
        self.fig.add_subplot(gs[17, 10:30])
        self.tx_slider = Slider(ax=plt.gca(), label='Idx_tx', valinit=1, valmin=1, valmax=self.channel.shape[1],
                                valstep=1, orientation='horizontal')
        self.fig.add_subplot(gs[18, 10:30])
        self.rx_slider = Slider(ax=plt.gca(), label='Idx_rx', valinit=1, valmin=1, valmax=self.channel.shape[2],
                                valstep=1, orientation='horizontal')
        self.snapshot_slider.on_changed(self.up_date)
        self.tx_slider.on_changed(self.up_date)
        self.rx_slider.on_changed(self.up_date)

        # init reset button
        ax_reset = plt.axes([0.1, 0.2, 0.1, 0.05])
        self.button = Button(ax_reset, 'Reset', hovercolor='0.975')
        self.button.on_clicked(self.reset)

    def _position_scale(self) -> float:
        """
        Based on the maximum distance between target and Tx calculate a reasonable scale for position axes
        """
        idx_target = 0

        # search max distance between Tx and target
        position_Tx = np.repeat(self.positionTx[:, :2], self.positionUAV.shape[0], axis=0)
        max_distance_TT = np.max(abs(self.positionUAV[:, idx_target, :2] - position_Tx))

        # distance between Tx and Rx
        max_distance_TR = np.max(abs(self.positionTx[:, :2] - self.positionRx[:, :2]))

        max_distance = max(max_distance_TT, max_distance_TR)
        scale = max_distance * 2.1  # 0.1 makes the target not reach the edge

        return scale

    def reset(self, event) -> None:
        """
        function for reset button
        """
        self.snapshot_slider.reset()
        self.tx_slider.reset()
        self.rx_slider.reset()

    def up_date(self, value) -> None:
        """
        procedures:
        1. grab new slider values
        2. Slice and process date with _slice_process_data()
        """
        # update index
        idx_dict = {
            'idx_snapshot': self.snapshot_slider.val - 1,
            'idx_rx': self.rx_slider.val - 1,
            'idx_tx': self.tx_slider.val - 1
        }

        # update data
        update_channel, updata_gt, uav_position = self._slice_process_data(idx_dict)

        # update plot
        self.plt_channel.set_data(update_channel)
        self.plt_gt.set_offsets(updata_gt[::-1])
        self.plt_uav_posi.set_offsets(uav_position[::-1])

        # Window to monitor Delay and Doppler
        ax_window = plt.axes([0.1, 0.35, 0.1, 0.1])
        delay_doppler = self.groundtruth[int(idx_dict['idx_snapshot'] + 0.5) * self.window_len]
        Button(ax_window, 'Delay:{:.4}μs\nDoppler:{:.4}Hz'.format(delay_doppler[0] * 1e6, delay_doppler[1]))

        self.fig.canvas.draw_idle()

    def _slice_process_data(self, idx: dict) -> np.ndarray:
        idx_snapshot = idx['idx_snapshot']
        idx_tx = idx['idx_tx']
        idx_rx = idx['idx_rx']
        idx_target = 0  # since for now only 1 target, todo: add idx_target later

        # update channel
        update_channel = PostprocessBase.fft(self.channel[idx_snapshot * self.window_len:(idx_snapshot + 1) * self.window_len,
                                             idx_tx, idx_rx, :].T)

        # update gt
        update_gt = self._convert_gt(self.groundtruth[int((idx_snapshot + 0.5) * self.window_len), :])

        # update positions
        uav_posi = (self.positionUAV[idx_snapshot * self.window_len, idx_target, :2] - self.positionTx[0, :2]) / self.scale + 0.5

        return update_channel, update_gt, uav_posi

    def _convert_gt(self, groundtruth: np.ndarray) -> np.ndarray:
        """
        Convert gt to coordinate of doppler-range map
        """
        gt = groundtruth.copy()
        # normalize delay
        gt[0] = gt[0] / self.tau_max * self.num_subcarriers
        # normalize doppler
        gt[1] = (gt[1] / self.sampling_frequency + 0.5) * self.window_len

        return gt



if __name__ == '__main__':
    channel_file_path = 'D:\FTPserver\\1to2_H15_V11_channel.h5'
    channel_file = h5py.File(channel_file_path)
    uav_file_path = 'D:\FTPserver\\1to2_H15_V11_target.h5'
    uav_file = h5py.File(uav_file_path)
    print(channel_file.keys())
    print(uav_file.keys())
    print(channel_file['Channel/FrequencyResponses/Data'].shape)

    delay = channel_file['TargetParameters/Delay/Data']
    doppler = channel_file['TargetParameters/Doppler/Data']
    dataset = channel_file['Channel/FrequencyResponses/Data']

    process = PostprocessBase(channel_file_path, uav_file_path)
    process.show()


