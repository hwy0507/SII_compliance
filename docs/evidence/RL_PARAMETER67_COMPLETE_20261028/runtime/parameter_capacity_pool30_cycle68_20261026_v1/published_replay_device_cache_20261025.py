"""Optional exact device mirror of the authoritative CPU replay buffer.

Keeps NumPy sampling RNG, bootstrap-mask rejection and CPU checkpoints intact.
Only accepted sample gathers move to the device. All updates are synchronous
in the caller's CUDA stream, with no new RNG, prefetching or changed batch size.
This candidate is not enabled in any frozen formal runtime by this module.
"""
import numpy as np
import torch


class DeviceReplayCache:
    def __init__(self, replay, device):
        self.replay = replay
        self.device = torch.device(device)
        self.arrays = {k: torch.empty(v.shape, dtype=torch.float32, device=self.device)
                       for k, v in replay.arrays.items()}
        if any(v.dtype != np.float32 for v in replay.arrays.values()):
            raise ValueError('Expected float32 replay fields')
        self.refresh()

    def refresh(self):
        for key, value in self.replay.arrays.items():
            self.arrays[key][:self.replay.size].copy_(torch.from_numpy(value[:self.replay.size]))

    def add(self, **row):
        index = self.replay.cursor
        self.replay.add(**row)
        for key, value in self.replay.arrays.items():
            self.arrays[key][index].copy_(torch.from_numpy(value[index]))

    def sample(self, count=256):
        while True:
            index = self.replay.rng.integers(self.replay.size, size=count)
            # Same values, reduction dtype and rejection as the existing sampler.
            if np.any(self.replay.arrays['masks'][index].sum(axis=0) == 0):
                continue
            device_index = torch.as_tensor(index, device=self.device)
            return {key: torch.index_select(value, 0, device_index)
                    for key, value in self.arrays.items()}

    def state_dict(self):
        return self.replay.state_dict()

    def load_state_dict(self, state):
        self.replay.load_state_dict(state)
        self.refresh()

    @property
    def size(self):
        return self.replay.size
