"""Feature-matched learned MLP/leaky RNN controls for the fixed-reservoir ESN.

The same 128 units, proprioceptive products, time constants and bounded linear
readout are used. Input weights (and RNN recurrent weights) are trainable.
No model-based controller, event signal, or extra hidden readout is present.
"""
import numpy as np
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN

CONTRACT='proprio48_context_network_v1'

class _Core(OfficeVMCMemoryESN):
    contract=CONTRACT

class OfficeContextNetwork:
    contract=CONTRACT
    input_dim=48

    def __init__(self,path):
        with np.load(path,allow_pickle=False) as z:
            self.kind=str(z['network_kind'])
        if self.kind not in ('mlp','rnn'):raise ValueError('Expected feature-matched MLP/RNN')
        self.core=_Core(path)
        if self.core.w.shape!=(128,128) or self.core.win.shape!=(128,156):
            raise ValueError('Expected 128 context units')
        if self.core.nonlinear:
            raise ValueError('No hidden nonlinear readout in this control')
        if self.core.reset_at_each_observation!=(self.kind=='mlp'):
            raise ValueError('MLP must be memoryless; RNN must retain state')

    @property
    def state(self):
        if self.kind=='mlp':raise AttributeError('MLP has no recurrent state')
        return self.core.state

    def reset(self):self.core.reset()
    def act(self,observation):return self.core.act(observation)
