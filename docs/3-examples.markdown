---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: page
permalink: /examples/
title: Code Examples
nav_order: 3
---
# Examples and Tutorials

Welcome to the Examples Section! Here, we provide practical Python code snippets to help you seamlessly navigate and utilize the Dataset for your ISAC-related projects. These examples are designed to be straightforward and easy to follow, serving as a solid starting point for your experimentation.

{: .new}
All examples shown here are available in the repository under [`snippets/`](https://github.com/EMS-TU-Ilmenau/isac-uav-dataset/tree/main/snippets).


## How to use the dataset
We provide two examples how to work with the dataset in the `snippets` folder.
- `snippets/load_example.py` demonstrates how to load the dataset from the `*.h5` files into Python. It provides a `Dataset`-class that can also be used in other scripts.
- `snippets/torch_dataset.py` demonstrates how to use the `Dataset`-class to create a PyTorch `Dataset` for training a neural network.
- `snippets/delay_doppler_plot.py` demonstrates how to use the `Dataset`-class to plot a Delay-Doppler Map with the groundtruth of the UAV position.

### Example 1: Working with `*.h5`
The provided `UAVDataset`-class can be used to load the dataset from the `*.h5` files into Python.
```python
channel_file = "1to2_H15_V11_VGH0_channel.h5"
target_file = "1to2_H15_V11_VGH0_target.h5"

dataset = UAVDataset(channel_file, target_file)
print(dataset)
```

Available properties are:
- `dataset.channel`: The channel dataset as a `numpy.ndarray` of shape `(n_snapshots, n_freq)`.
- `dataset.groundtruth`: The target groundtruth (delay, Doppler) as a `numpy.ndarray` of shape `(n_snapshots, 2)`.
- `dataset.tx`: Position of the Tx antenna (`numpy.ndarray`) with shape `(1, 3)`.
- `dataset.rx`: Position of the Rx antenna (`numpy.ndarray`) with shape `(1, 3)`.
- `dataset.uav`: Position of the UAV (`numpy.ndarray`) with shape `(n_snapshots, 3)`.

Check the implementation of the class in `snippets/load_example.py` to learn more about the available properties.

### Example 2: Creating a PyTorch `Dataset`
The provided `UAVDataset`-class can be used to create a PyTorch `Dataset` for training a neural network.
```python
class TorchDataset(Dataset):
    def __init__(self, dataset: UAVDataset, t_window: int = 100, return_uavpos: bool = False):
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
```

To create a `DataLoader` with complex baseband and delay-doppler groundtruth, e.g., use:
```python
dataset = UAVDataset(channel_file)
dataloader = DataLoader(
  TorchDataset(dataset), 
  batch_size=16, 
  shuffle=True,
)
```

To create a `DataLoader` with complex baseband, delay-doppler groundtruth, and UAV positions, e.g., use:
```python
dataset = UAVDataset(channel_file, target_file)
dataloader = DataLoader(
  TorchDataset(dataset, return_uavpos=True), 
  batch_size=16, 
  shuffle=True,
)
```

Check the provided file `snippets/torch_dataset.py` to learn more about the available options.

### Example 3: Plotting Delay-Doppler Map with UAV Groundtruth (RADAR)
You need to use `-p` and specify the `.h5` data files, namely channel dataset and target dataset, which should be placed in the main folder.    
```
python postprocessing.py -c channel.h5 -t target.h5 -p
```

**Optional: Slice the channel**  
You can also slice the channel using `-s` by giving three idx: idx_snapshot idx_Tx idx_Rx
```
python postprocessing.py -c channel.h5 -t target.h5 -s idx_snapshot idx_Tx idx_Rx
```
