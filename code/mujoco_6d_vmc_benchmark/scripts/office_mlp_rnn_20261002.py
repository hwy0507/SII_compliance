"""Pure learned 128-unit MLP/Elman RNN with the public proprio48/action7 API."""
import numpy as np

CONTRACT = 'proprio48_office_mlp_rnn_v1'


class OfficeMLPRNN:
    contract = CONTRACT
    input_dim = 48

    def __init__(self, path):
        with np.load(path, allow_pickle=False) as z:
            if str(z['contract']) != CONTRACT:
                raise ValueError('Unsupported MLP/RNN contract')
            self.kind = str(z['kind'])
            self.fields = z['fields'].astype(int)
            self.scale = z['scale'].astype(float)
            self.input_w = z['input_w'].astype(float)
            self.output_w = z['output_w'].astype(float)
            self.recurrent_w = z['recurrent_w'].astype(float) if self.kind == 'rnn' else None
            self.norm_slowdown = bool(z['norm_slowdown']) if 'norm_slowdown' in z.files else False
            self.absolute_inputs = bool(z['absolute_inputs']) if 'absolute_inputs' in z.files else False
        allowed = set(range(14, 17)) | set(range(20, 23)) | set(range(26, 29)) | set(range(39, 48))
        if self.kind not in ('mlp', 'rnn') or not set(self.fields).issubset(allowed):
            raise ValueError('Invalid architecture or non-proprioceptive field selection')
        if len(set(self.fields)) != len(self.fields) or self.scale.shape != (len(self.fields),):
            raise ValueError('Invalid input transform')
        if self.input_w.shape != (128, len(self.fields)*(2 if self.absolute_inputs else 1)) or self.output_w.shape != (7, 128):
            raise ValueError('Expected 128 hidden units/action7')
        arrays = [self.scale, self.input_w, self.output_w]
        if self.kind == 'rnn':
            if self.recurrent_w.shape != (128, 128):
                raise ValueError('Invalid RNN state matrix')
            arrays.append(self.recurrent_w)
        if not all(np.isfinite(x).all() for x in arrays) or np.any(self.scale <= 0):
            raise ValueError('Invalid network parameters')
        self.reset()

    def reset(self):
        if self.kind == 'rnn':
            self.state = np.zeros(128)

    def act(self, observation):
        obs = np.asarray(observation, dtype=float)
        if obs.shape != (48,) or not np.isfinite(obs).all():
            raise ValueError('Expected finite canonical48')
        x = np.clip(obs[self.fields]/self.scale, -12, 12)
        if self.absolute_inputs:x=np.r_[x,np.abs(x)]
        hidden = self.input_w @ x
        if self.kind == 'rnn':
            hidden += self.recurrent_w @ self.state
        hidden = np.tanh(hidden)
        if self.kind == 'rnn':
            self.state = hidden
        raw = self.output_w @ hidden
        result = np.tanh(raw)
        result[0] = (np.clip(np.linalg.norm(result[1:])/np.sqrt(6), 0, 1)
                     if self.norm_slowdown else np.clip(raw[0], 0, 1))
        return result
