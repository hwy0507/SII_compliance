"""45 proprioceptive/task inputs, fixed 128-unit reservoir, 128-unit head."""
import json
import numpy as np


class ESN128Action7:
    kind = 'esn'
    dt = .04
    reservoir = 128

    def __init__(self, mean, std, seed=20260918):
        self.mean = np.asarray(mean); self.std = np.asarray(std)
        self.seed = seed
        self.input_mask = np.ones(45)
        self.alpha = 1.
        self.output_gain = 1.
        rng = np.random.default_rng(seed)
        self.win = rng.normal(0, .45 / np.sqrt(45), (128, 46))
        w = rng.normal(size=(128, 128)) * (rng.random((128, 128)) < .08)
        self.w = w * (.9 / np.max(np.abs(np.linalg.eigvals(w))))
        tau = np.concatenate([np.full(len(i), t) for i, t in zip(
            np.array_split(np.arange(128), 3), (.08, .4, 1.6))])
        self.leak = 1 - np.exp(-self.dt / tau)
        self.head = {}
        self.reset()

    def reset(self):
        self.state = np.zeros(128)
        self.previous_action = np.zeros(7)

    def features(self, observation):
        x = np.asarray(observation)
        if x.shape != (45,) or not np.isfinite(x).all():
            raise ValueError('Expected finite contact45 observation')
        x = np.clip((x - self.mean) / self.std, -12, 12) * self.input_mask
        self.state += self.leak * (np.tanh(self.win @ np.r_[1., x] + self.w @ self.state) - self.state)
        return np.r_[x, self.state]

    def act(self, observation):
        f = (self.features(observation) - self.head['fmean']) / self.head['fstd']
        h = np.tanh(self.head['w1'] @ f + self.head['b1'])
        logits = self.head['w2'] @ h + self.head['b2']
        result = np.tanh(logits)
        result[0] = 1 / (1 + np.exp(-np.clip(logits[0], -60, 60)))
        result *= self.output_gain
        self.previous_action += self.alpha * (result-self.previous_action)
        return self.previous_action.copy()

    def save(self, path, metadata):
        with open(path, 'wb') as stream:
            np.savez_compressed(stream, contract='four_scene_contact45_action7_v1',
                metadata=json.dumps(metadata), seed=self.seed, mean=self.mean, std=self.std,
                win=self.win, w=self.w, leak=self.leak, input_mask=self.input_mask, alpha=self.alpha, output_gain=self.output_gain, **self.head)

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as z:
            if str(z['contract']) != 'four_scene_contact45_action7_v1':
                raise ValueError('Wrong checkpoint contract')
            obj = cls.__new__(cls)
            obj.seed = int(z['seed'])
            obj.input_mask = z['input_mask'].copy() if 'input_mask' in z else np.ones(45)
            obj.alpha = float(z['alpha']) if 'alpha' in z else 1.
            obj.output_gain = float(z['output_gain']) if 'output_gain' in z else 1.
            for k in ('mean', 'std', 'win', 'w', 'leak'):
                setattr(obj, k, z[k].copy())
            obj.head = {k: z[k].copy() for k in ('fmean', 'fstd', 'w1', 'b1', 'w2', 'b2')}
        obj.reset()
        return obj
