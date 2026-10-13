"""Shared-feature, shared-objective controls; no teacher parent selection.

The primary ESN/RNN/MLP comparison starts from the same random matrices and
readout, uses the same optimizer schedule, and differs only in memory and which
matrices learn. Analytic ESN and its RNN fine-tune are separate mechanism rows.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import platform
import sys
import time

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from office_v7_uniform24_20261008 import read, write, sha, now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from office_context_network_20261003 import OfficeContextNetwork, CONTRACT
from train_paper_feature_matched_network_20261003 import Network

FAMILIES = ('esn_gradient', 'rnn_scratch', 'mlp_scratch', 'esn_ridge', 'rnn_from_ridge')
FIELDS = sorted(set(range(14, 17)) | set(range(20, 23)) | set(range(26, 29)) | set(range(39, 48)))
WIDTH = 128
RIDGE = .1


def initial_actor(seed):
    rng = np.random.default_rng(seed)
    a = OfficeVMCMemoryESN.__new__(OfficeVMCMemoryESN)
    base = rng.normal(size=(WIDTH, WIDTH)) * (rng.random((WIDTH, WIDTH)) < .08)
    a.w = .8 * base / max(np.max(abs(np.linalg.eigvals(base))), 1e-12)
    a.win = .25 * rng.normal(size=(WIDTH, 156)); a.win[:, 12:] /= 3
    a.scale = np.array([8., 8., 8., 1., 1., 1.])
    a.leak = 1 - np.exp(-.04 / np.repeat([.04, .12, .5, 2.], 32))
    a.absolute_inputs = a.context_inputs = a.position_context = True
    a.context_dimension = 12
    a.reset_at_each_observation = False
    a.context_gate_w = a.context_gate_limits = None
    a.state_context_readout_w = np.random.default_rng(seed + 50000).normal(0, 1/np.sqrt(12), (WIDTH, 12))
    a.weights = np.zeros((552, 7))
    a.reset()
    return a


def encoded(obs, scale):
    force = np.clip(obs[:, 39:45] / scale, -12, 12)
    context = np.c_[np.clip(np.c_[obs[:, 14:17]/.06, obs[:, 26:29]/.06, obs[:, 45:48]], -4, 4),
                    np.clip(obs[:, 20:23]/.08, -4, 4)]
    load = np.c_[force, abs(force)]
    cross = (load[:, :, None] * context[:, None, :]).reshape(len(obs), 144)
    return [np.c_[load, cross], force, cross, context]


def history_features(actor, obs, episode):
    result = []; previous = None
    for e, o in zip(episode, obs):
        if e != previous: actor.reset(); previous = e
        result.append(actor.features(o))
    return np.asarray(result)


class RawNetwork(Network):
    """Train pre-clipping outputs; clipping remains identical at deployment.

    This makes the fixed-reservoir ridge solution and gradient learners share
    exactly the weighted squared-error/readout-regularization objective, without
    an output clamp eliminating gradients. No temporal loss is applied to one
    family only. Last twelve context-only readout rows stay identically zero.
    """
    def forward(self, drive, force, cross, context, state=None):
        projection = drive @ self.win.T
        if self.kind == 'mlp':
            hidden = torch.tanh(projection) * self.leak
        else:
            if state is None: state = projection.new_zeros((len(projection), WIDTH))
            states = []
            for t in range(projection.shape[1]):
                state = state + self.leak * (torch.tanh(projection[:, t] + state @ self.echo.T) - state)
                states.append(state)
            hidden = torch.stack(states, 1)
        signed = torch.cat((force, hidden), -1)
        features = torch.cat((signed, signed.abs(), cross,
                              hidden * torch.tanh(context @ self.state_context_readout_w.T), context), -1)
        return (features / self.norm) @ (self.coeff * self.mask), state


def bounded(value):
    return np.c_[np.clip(value[:, :1], 0, 1), np.clip(value[:, 1:], -1, 1)]


def check_split(ep, train):
    assert train.dtype == bool and np.any(train) and np.any(~train)
    assert not set(ep[train]).intersection(ep[~train]), 'Identity leakage'
    # Recurrence must reset exactly once per contiguous episode.
    starts = np.r_[True, ep[1:] != ep[:-1]]
    assert len(ep[starts]) == len(np.unique(ep)), 'Non-contiguous identity'


def export(model, actor, family, path):
    values = dict(scale=actor.scale, w=model.echo.detach().numpy(), win=model.win.detach().numpy(),
        leak=actor.leak, weights=(model.coeff * model.mask).detach().numpy()/model.norm.numpy()[:, None],
        state_context_readout_w=actor.state_context_readout_w, absolute_inputs=True, context_inputs=True,
        position_context=True, axis_separable=False, readout_activation='clipped_linear', output_gain=1.,
        reset_at_each_observation=(family == 'mlp_scratch'))
    if family.startswith('esn'):
        values['contract'] = OfficeVMCMemoryESN.contract
    else:
        values.update(contract=CONTRACT, network_kind='mlp' if family == 'mlp_scratch' else 'rnn')
    np.savez_compressed(path, **values)
    return OfficeVMCMemoryESN(path) if family.startswith('esn') else OfficeContextNetwork(path)


def fit(a):
    out = a.output.resolve(); out.mkdir(parents=True, exist_ok=False)
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cg/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3*1024**3
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    torch.set_num_threads(1); torch.manual_seed(a.seed)
    meta = read(a.metadata); assert sha(a.data) == meta['training_data_sha256']
    started = time.monotonic()
    state = dict(status='running', started_utc=now(), argv=sys.argv, host=platform.node(), python=sys.executable,
        torch=torch.__version__, numpy=np.__version__, memory_max=memory, source_sha256=sha(Path(__file__)))
    write(out/'execution.json', state)
    try:
        with np.load(a.data) as z:
            obs, ep, train, importance, target = [z[k].copy() for k in
                ('observation', 'episode', 'train', 'importance', 'requested_teacher_action')]
            assert z['physical_execution'].all()
        check_split(ep, train)
        assert obs.shape == (len(ep), 48) and target.shape == (len(ep), 7)
        assert all(np.isfinite(x).all() for x in (obs, importance, target)) and np.all(importance > 0)
        actor = initial_actor(a.seed)
        features = history_features(actor, obs, ep)
        # Identical train-only normalizer for all five rows, including MLP.
        norm = np.maximum(features[train].std(0), .005)
        x = features[train, :-12]/norm[None, :-12]
        ridge = np.zeros((552, 7))
        ridge[:-12] = np.linalg.solve(x.T@(importance[train, None]*x) + RIDGE*np.eye(540),
                                      x.T@(importance[train, None]*target[train]))
        del x, features
        initial = np.random.default_rng(a.seed+60000).normal(0, 1e-4, (552, 7)); initial[-12:] = 0
        actor.weights = initial/norm[:, None]
        model = RawNetwork(actor, 'mlp' if a.family == 'mlp_scratch' else 'rnn', norm)
        if a.family.startswith('esn'):
            model.win.requires_grad_(False); model.echo.requires_grad_(False)
        if a.family in ('esn_ridge', 'rnn_from_ridge'):
            with torch.no_grad(): model.coeff.copy_(torch.from_numpy(ridge))
        origin = copy.deepcopy(model.state_dict())
        arrays = encoded(obs, actor.scale) + [target, importance]
        seq = {int(e): np.flatnonzero(ep == e) for e in np.unique(ep)}
        train_ids, val_ids = np.unique(ep[train]), np.unique(ep[~train])
        def predictions(ids):
            values = {}
            with torch.no_grad():
                for e in ids:
                    ids_e = seq[int(e)]
                    values[int(e)] = model(*[torch.from_numpy(v[ids_e])[None] for v in arrays[:4]])[0][0].numpy()
            return values
        def validation():
            raw = np.concatenate(list(predictions(val_ids).values()))
            y = np.concatenate([target[seq[int(e)]] for e in val_ids])
            return float(np.mean((bounded(raw)-y)**2)), float(np.mean((raw-y)**2))
        score, raw_score = validation()
        best = score; selected = 0; best_state = copy.deepcopy(model.state_dict())
        history = [dict(update=0, validation_mse=score, validation_raw_mse=raw_score)]
        schedule = []; gradients = {}; update = epoch = 0
        params = [p for p in model.parameters() if p.requires_grad]
        optimizer = torch.optim.Adam(params, lr=a.learning_rate)
        rng = np.random.default_rng(a.seed+2000)
        total_mass = float(importance[train].sum())
        updates = 0 if a.family == 'esn_ridge' else a.updates
        while update < updates:
            order = rng.permutation(train_ids)
            for begin in range(0, len(order), 8):
                group = order[begin:begin+8]; length = max(len(seq[int(e)]) for e in group)
                padded = [np.zeros((len(group), length, *v.shape[1:]), np.float64) for v in arrays]
                for i, e in enumerate(group):
                    for dest, src in zip(padded, arrays): dest[i, :len(seq[int(e)])] = src[seq[int(e)]]
                hidden = None
                for offset in range(0, length, 64):
                    values = [torch.from_numpy(v[:, offset:offset+64]) for v in padded]
                    pred, hidden = model(*values[:4], state=hidden)
                    y, weight = values[4:]
                    loss = ((pred-y).square()*weight[..., None]).sum()/(7*weight.sum())
                    loss += RIDGE/(7*total_mass)*(model.coeff*model.mask).square().sum()
                    assert torch.isfinite(loss)
                    optimizer.zero_grad(set_to_none=True); loss.backward()
                    if update == 0:
                        gradients = {k:float(v.grad.norm()) for k,v in model.named_parameters() if v.requires_grad}
                        assert all(np.isfinite(x) and x > 0 for x in gradients.values()), gradients
                    torch.nn.utils.clip_grad_norm_(params, 1.); optimizer.step()
                    if hidden is not None: hidden = hidden.detach()
                    update += 1; schedule.append((epoch, [int(e) for e in group], offset, int((weight > 0).sum())))
                    if update % 1000 == 0 or update == updates:
                        score, raw_score = validation()
                        history.append(dict(update=update, validation_mse=score, validation_raw_mse=raw_score,
                                            last_train_loss=float(loss.detach())))
                        write(out/'training_progress.json', history[-1])
                        if score < best:
                            best = score; selected = update; best_state = copy.deepcopy(model.state_dict())
                    if update >= updates: break
                if update >= updates: break
            epoch += 1
        last_delta = {k:float((v-origin[k]).norm()) for k,v in model.named_parameters()}
        model.load_state_dict(best_state)
        selected_delta = {k:float((v-origin[k]).norm()) for k,v in model.named_parameters()}
        deployed = export(model, actor, a.family, out/'checkpoint.npz')
        predicted = []; previous = None
        for e,o in zip(ep, obs):
            if e != previous: deployed.reset(); previous = e
            predicted.append(deployed.act(o))
        predicted = np.asarray(predicted)
        torch_predictions = predictions(seq)
        parity = max(float(np.max(abs(predicted[ids]-bounded(torch_predictions[e])))) for e,ids in seq.items())
        assert parity < 5e-5, parity
        assert abs(float(np.mean((predicted[~train]-target[~train])**2))-best) < 1e-8
        other = export(model, actor, a.family, out/'isolation_checkpoint.npz')
        deployed.reset(); forbidden = sorted(set(range(48))-set(FIELDS))
        for o in obs[:200]:
            altered = o.copy(); altered[forbidden] = 123
            np.testing.assert_array_equal(deployed.act(o), other.act(altered))
        deployed.reset()
        for o in obs[:200]:
            zero = o.copy(); zero[39:45] = 0
            np.testing.assert_array_equal(deployed.act(zero), np.zeros(7))
        np.savez_compressed(out/'exported_replay.npz', prediction=predicted, episode=ep)
        write(out/'history.json', history); write(out/'schedule.json', schedule)
        np.savez_compressed(out/'initialization.npz', win=origin['win'].numpy(), w=origin['echo'].numpy(),
                            coeff=origin['coeff'].numpy(), norm=norm)
        with np.load(out/'checkpoint.npz') as z:
            stored = {k:int(z[k].size) for k in z.files if z[k].dtype.kind == 'f'}
        result = dict(family=a.family, seed=a.seed, learning_rate=a.learning_rate, updates=update,
            selected_update=selected, validation_mse=best, history=history, first_gradient_norms=gradients,
            final_parameter_delta_norm=last_delta, selected_parameter_delta_norm=selected_delta,
            effective_recurrent_update=bool(selected_delta['echo'] > 0),
            training_data_sha256=sha(a.data), metadata_sha256=sha(a.metadata),
            initialization_sha256=sha(out/'initialization.npz'), schedule_sha256=sha(out/'schedule.json'),
            checkpoint_sha256=sha(out/'checkpoint.npz'), normalizer_train_only=True,
            width=WIDTH, trainable_parameters=sum(p.numel() for p in params)-84,
            stored_float_scalars=sum(stored.values()), stored_arrays=stored, actor_fields=FIELDS,
            train_identities=[int(e) for e in train_ids], validation_identities=[int(e) for e in val_ids],
            numpy_torch_max_abs=parity, unused_field_isolation_pass=True, zero_load_equilibrium_pass=True,
            duration_s=time.monotonic()-started, raw_linear_objective=True, readout_ridge=RIDGE,
            objective='sum(weight*raw_action_error^2)/(7*train_weight_mass) + .1*sum(normalized_readout^2)/(7*train_weight_mass)',
            limitation='Same width/mechanisms, not equal trainable parameters or FLOPs. Ridge/fine-tune are auxiliary; update0 retained and explicitly reported.')
        write(out/'TRAINING_COMPLETE.json', result)
        state.update(status='complete', selected_update=selected, checkpoint_sha256=result['checkpoint_sha256'])
        print(json.dumps({k:result[k] for k in ('family', 'seed', 'selected_update', 'validation_mse', 'duration_s')}), flush=True)
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc'] = now(); write(out/'execution.json', state)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('data', 'metadata', 'output'): p.add_argument('--'+k, type=Path, required=True)
    p.add_argument('--family', choices=FAMILIES, required=True)
    p.add_argument('--seed', type=int, required=True)
    p.add_argument('--learning-rate', type=float, default=1e-4)
    p.add_argument('--updates', type=int, default=8000)
    a = p.parse_args(); assert 0 < a.updates <= 8000 and 0 < a.learning_rate <= .001
    fit(a)


if __name__ == '__main__': main()
