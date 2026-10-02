"""Paired pure MLP/Elman RNN imitation, with complete-identity validation."""
import argparse
import copy
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
import torch
from torch import nn
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from office_mlp_rnn_20261002 import OfficeMLPRNN, CONTRACT


class Network(nn.Module):
    def __init__(self, kind, dimension, seed):
        super().__init__()
        self.kind = kind
        self.core = (nn.RNN(dimension, 128, batch_first=True, bias=False)
                     if kind == 'rnn' else nn.Linear(dimension, 128, bias=False))
        self.head = nn.Linear(128, 7, bias=False)
        rng = np.random.default_rng(seed)
        input_w = rng.normal(0, 1/np.sqrt(dimension), (128, dimension))
        output_w = rng.normal(0, .1/np.sqrt(128), (7, 128))
        with torch.no_grad():
            if kind == 'rnn':
                self.core.weight_ih_l0.copy_(torch.tensor(input_w))
                q, _ = np.linalg.qr(np.random.default_rng(seed+1000).normal(size=(128, 128)))
                self.core.weight_hh_l0.copy_(torch.tensor(.8*q))
            else:
                self.core.weight.copy_(torch.tensor(input_w))
            self.head.weight.copy_(torch.tensor(output_w))

    def forward(self, x, state=None):
        if self.kind == 'rnn':
            hidden, state = self.core(x, state)
        else:
            hidden = torch.tanh(self.core(x))
        raw = self.head(hidden)
        action = torch.cat((raw[..., :1].clamp(0, 1), torch.tanh(raw[..., 1:])), -1)
        return action, state

    def export(self, fields, scale):
        result = dict(contract=np.asarray(CONTRACT), kind=np.asarray(self.kind), fields=fields,
                      scale=scale, input_w=(self.core.weight_ih_l0 if self.kind == 'rnn' else self.core.weight).detach().numpy(),
                      output_w=self.head.weight.detach().numpy())
        if self.kind == 'rnn':
            result['recurrent_w'] = self.core.weight_hh_l0.detach().numpy()
        return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data', type=Path, required=True)
    p.add_argument('--metadata', type=Path, required=True)
    p.add_argument('--kind', choices=('mlp', 'rnn'), required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--updates', type=int, default=2400)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cg/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3*1024**3
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    torch.set_num_threads(1)
    torch.manual_seed(a.seed)
    sources = sorted((ROOT/'scripts').glob('*.py')) + [Path(__file__), ROOT/'tools/optimize_tool_contact_20261002.py']
    source_hash = {str(f.relative_to(ROOT)): sha(f) for f in sources}
    subprocess.run(['tar', '-czf', str(a.output/'source_overlay.tar.gz'), *source_hash], cwd=ROOT, check=True)
    state = dict(status='running', started_utc=now(), argv=sys.argv, host=platform.node(),
                 source_commit_base=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                 source_sha256=source_hash, python=sys.executable, python_version=platform.python_version(),
                 torch_version=torch.__version__, numpy_version=np.__version__, memory_max=memory, threads=1)
    write(a.output/'execution.json', state)
    try:
        metadata = json.loads(a.metadata.read_text())
        assert sha(a.data) == metadata['training_data_sha256']
        fields = np.asarray([*range(14, 17), *range(20, 23), *range(26, 29), *range(39, 48)]
                            if metadata.get('position_error_context') else list(range(39, 45)))
        with np.load(a.data) as z:
            obs, target, episode, train, importance = [z[k].copy() for k in
                ('observation', 'filtered_teacher_action', 'episode', 'train', 'importance')]
        assert all(np.isfinite(x).all() for x in (obs, target, importance))
        train_ids, val_ids = np.unique(episode[train]), np.unique(episode[~train])
        assert not set(train_ids).intersection(val_ids)
        scale = np.maximum(obs[train][:, fields].std(0), .005)
        features = np.clip(obs[:, fields]/scale, -12, 12).astype(np.float32)
        seq = {int(ep): np.flatnonzero(episode == ep) for ep in np.unique(episode)}
        assert all(np.unique(train[ids]).size == 1 for ids in seq.values())
        model = Network(a.kind, len(fields), a.seed)
        optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=1e-5)
        rng = np.random.default_rng(a.seed+2000)
        def predict_all(ids):
            values = {}
            with torch.no_grad():
                for ep in ids:
                    index = seq[int(ep)]
                    values[int(ep)] = model(torch.from_numpy(features[index])[None])[0][0].numpy()
            return values
        history, schedule = [], []
        best, best_state, best_step = float('inf'), None, None
        update, epoch = 0, 0
        while update < a.updates:
            order = rng.permutation(train_ids)
            for start in range(0, len(order), 8):
                group = order[start:start+8]
                length = max(len(seq[int(ep)]) for ep in group)
                x = np.zeros((len(group), length, len(fields)), np.float32)
                y = np.zeros((len(group), length, 7), np.float32)
                w = np.zeros((len(group), length), np.float32)
                for i, ep in enumerate(group):
                    ids = seq[int(ep)]; n = len(ids)
                    x[i, :n], y[i, :n], w[i, :n] = features[ids], target[ids], importance[ids]
                hidden = None
                for offset in range(0, length, 64):
                    xx, yy, ww = [torch.from_numpy(v[:, offset:offset+64]) for v in (x, y, w)]
                    prediction, hidden = model(xx, hidden)
                    loss = (((prediction-yy)**2)*ww[..., None]).sum()/(7*ww.sum())
                    pair_w = torch.minimum(ww[:, 1:], ww[:, :-1])
                    delta = ((prediction[:, 1:]-prediction[:, :-1])-(yy[:, 1:]-yy[:, :-1]))**2
                    delta_loss = (delta*pair_w[..., None]).sum()/(7*pair_w.sum().clamp_min(1))
                    total = loss+.25*delta_loss
                    if not torch.isfinite(total):
                        raise ValueError('Nonfinite training loss')
                    optimizer.zero_grad(set_to_none=True)
                    total.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1.)
                    optimizer.step()
                    if hidden is not None:
                        hidden = hidden.detach()
                    update += 1
                    schedule.append((epoch, tuple(int(ep) for ep in group), offset, int((ww > 0).sum())))
                    if update >= a.updates:
                        break
                if update >= a.updates:
                    break
            values = predict_all(val_ids)
            err = np.concatenate([values[int(ep)]-target[seq[int(ep)]] for ep in val_ids])
            score = float(np.mean(err**2))
            history.append(dict(update=update, epoch=epoch, last_train_loss=float(total.detach()), validation_mse=score))
            if score < best:
                best, best_state, best_step = score, copy.deepcopy(model.state_dict()), update
            epoch += 1
        model.load_state_dict(best_state)
        np.savez_compressed(a.output/'checkpoint.npz', **model.export(fields, scale))
        exported = OfficeMLPRNN(a.output/'checkpoint.npz')
        predictions = np.empty_like(target)
        max_error = 0.
        values = predict_all(seq)
        for ep, ids in seq.items():
            exported.reset()
            predictions[ids] = np.asarray([exported.act(o) for o in obs[ids]])
            max_error = max(max_error, float(np.max(abs(predictions[ids]-values[ep]))))
        if max_error > 5e-5:
            raise ValueError(f'Export precision differs: {max_error}')
        other = OfficeMLPRNN(a.output/'checkpoint.npz')
        exported.reset(); other.reset()
        unused = sorted(set(range(48))-set(fields))
        for o in obs[:200]:
            perturbed = o.copy(); perturbed[unused] = 123.
            np.testing.assert_array_equal(exported.act(o), other.act(perturbed))
        exported.reset()
        np.testing.assert_array_equal(exported.act(np.zeros(48)), np.zeros(7))
        write(a.output/'schedule.json', schedule)
        write(a.output/'history.json', history)
        np.savez_compressed(a.output/'exported_replay.npz', prediction=predictions, episode=episode)
        groups = {}
        for name, mask in [('synthetic_train', train & (episode < 48)), ('synthetic_holdout', ~train),
                           ('seen_physical_histories', episode >= 48)]:
            groups[name] = dict(samples=int(mask.sum()), action_mse=float(np.mean((predictions[mask]-target[mask])**2)))
        result = dict(kind=a.kind, seed=a.seed, updates=update, selected_update=best_step, width=128,
                      trainable_parameters=sum(p.numel() for p in model.parameters()), fields=fields.tolist(),
                      data_sha256=sha(a.data), metadata_sha256=sha(a.metadata), lineage=metadata['lineage'],
                      checkpoint_sha256=sha(a.output/'checkpoint.npz'), schedule_sha256=sha(a.output/'schedule.json'),
                      exported_replay_sha256=sha(a.output/'exported_replay.npz'), groups=groups,
                      numpy_torch_max_abs=max_error, unused_field_isolation_pass=True, zero_input_equilibrium_pass=True,
                      batch_size=8, tbptt_steps=64, action_delta_weight=.25, source_sha256=source_hash,
                      limitation='Synthetic identity holdout and seen failed-teacher histories; physical success measured separately. No runtime teacher/controller. Width-matched, not parameter-matched.')
        assert all(sha(ROOT/k) == v for k, v in source_hash.items())
        write(a.output/'TRAINING_COMPLETE.json', result)
        state.update(status='complete', checkpoint_sha256=result['checkpoint_sha256'])
        print(json.dumps({k: result[k] for k in ('kind', 'seed', 'groups', 'selected_update', 'trainable_parameters', 'numpy_torch_max_abs')}))
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc))
        raise
    finally:
        state['ended_utc'] = now()
        write(a.output/'execution.json', state)


if __name__ == '__main__':
    main()
