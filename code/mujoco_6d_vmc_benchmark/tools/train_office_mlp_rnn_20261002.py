"""Paired pure MLP/Elman RNN imitation, with complete-identity validation."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import numpy as np
import torch
from torch import nn
from optimize_tool_contact_20261002 import ROOT, sha, write, now, source_base_commit
from office_mlp_rnn_20261002 import OfficeMLPRNN, CONTRACT


class Network(nn.Module):
    def __init__(self, kind, dimension, seed, norm_slowdown=False, modular=False):
        super().__init__()
        self.kind = kind
        self.norm_slowdown = norm_slowdown
        self.modular = modular
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
        self.active_parameters = sum(p.numel() for p in self.parameters())
        if modular:
            if dimension != 6 or not norm_slowdown:
                raise ValueError('Matched modular baseline requires six load fields and norm slowdown')
            input_mask = torch.zeros(128, 6); recurrent_mask = torch.zeros(128, 128); output_mask = torch.zeros(7, 128)
            begin = 0
            for axis, width in enumerate((22,22,21,21,21,21)):
                stop = begin+width
                input_mask[begin:stop,axis]=1
                recurrent_mask[begin:stop,begin:stop]=1
                output_mask[axis+1,begin:stop]=1
                begin=stop
            pairs=[(self.core.weight_ih_l0 if kind=='rnn' else self.core.weight,input_mask),(self.head.weight,output_mask)]
            if kind=='rnn':pairs.append((self.core.weight_hh_l0,recurrent_mask))
            self.active_parameters=int(sum(mask.sum() for _,mask in pairs))
            for parameter,mask in pairs:
                with torch.no_grad():parameter.mul_(mask)
                parameter.register_hook(lambda gradient,mask=mask:gradient*mask)

    def forward(self, x, state=None):
        if self.kind == 'rnn':
            hidden, state = self.core(x, state)
        else:
            hidden = torch.tanh(self.core(x))
        raw = self.head(hidden)
        residual = torch.tanh(raw[..., 1:])
        slowdown = (raw[..., :1] if self.training and getattr(self, 'raw_slowdown_loss', False)
                    else raw[..., :1].clamp(0, 1))
        scale = (torch.linalg.vector_norm(residual, dim=-1, keepdim=True)/np.sqrt(6)
                 if self.norm_slowdown else slowdown)
        action = torch.cat((scale, residual), -1)
        return action, state

    def export(self, fields, scale, absolute_inputs=False):
        result = dict(contract=np.asarray(CONTRACT), kind=np.asarray(self.kind), fields=fields,
                      norm_slowdown=np.asarray(self.norm_slowdown),
                      absolute_inputs=np.asarray(absolute_inputs),
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
    p.add_argument('--target', choices=('requested', 'filtered'), default='filtered')
    p.add_argument('--norm-slowdown', action='store_true')
    p.add_argument('--modular',action='store_true',help='Same per-axis 128-unit structure as the proposed modular ESN')
    p.add_argument('--learning-rate',type=float,default=.001)
    p.add_argument('--drift-weight',type=float,default=0.)
    p.add_argument('--initialize-checkpoint',type=Path)
    p.add_argument('--parent-metadata',type=Path)
    p.add_argument('--absolute-inputs',action='store_true')
    p.add_argument('--precision',choices=('float32','float64'),default='float32',
                   help='Train/export with matched arithmetic; float64 avoids long recurrent replay drift')
    p.add_argument('--tbptt-steps',type=int,default=64,help='Sequence length per optimizer update; actual exposure is recorded')
    p.add_argument('--action-delta-weight',type=float,default=.25)
    p.add_argument('--weight-decay',type=float,default=1e-5)
    p.add_argument('--lr-schedule',choices=('constant','cosine'),default='constant')
    p.add_argument('--selection',choices=('best','final'),default='best',
                   help='Final uses only the terminal checkpoint as a hyperparameter candidate')
    p.add_argument('--global-loss',action='store_true',help='Constant batch mass; do not overweight short tail chunks')
    p.add_argument('--raw-slowdown-loss',action='store_true',help='Avoid zero gradient below slowdown clamp during training only')
    a = p.parse_args()
    if not 0<=a.action_delta_weight<=2 or not 0<=a.weight_decay<=1 or a.updates<1:
        raise ValueError('Invalid loss/decay/update budget')
    if not 16<=a.tbptt_steps<=2048:raise ValueError('TBPTT steps must be 16..2048')
    a.output.mkdir(parents=True, exist_ok=False)
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cg/'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3*1024**3
    assert (cg/'memory.swap.max').read_text().strip() == '0'
    assert all(os.environ.get(k) == '1' for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'))
    torch.set_num_threads(1)
    torch.set_default_dtype(torch.float64 if a.precision=='float64' else torch.float32)
    array_dtype=np.float64 if a.precision=='float64' else np.float32
    torch.manual_seed(a.seed)
    sources = sorted((ROOT/'scripts').glob('*.py')) + [Path(__file__), ROOT/'tools/optimize_tool_contact_20261002.py']
    source_hash = {str(f.relative_to(ROOT)): sha(f) for f in sources}
    subprocess.run(['tar', '-czf', str(a.output/'source_overlay.tar.gz'), *source_hash], cwd=ROOT, check=True)
    state = dict(status='running', started_utc=now(), argv=sys.argv, host=platform.node(),
                 source_commit_base=source_base_commit(),
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
                ('observation', a.target+'_teacher_action', 'episode', 'train', 'importance')]
            physical = z['physical_execution'].astype(bool) if 'physical_execution' in z.files else episode >= 48
        assert all(np.isfinite(x).all() for x in (obs, target, importance))
        train_ids, val_ids = np.unique(episode[train]), np.unique(episode[~train])
        assert not set(train_ids).intersection(val_ids)
        scale = np.maximum(obs[train][:, fields].std(0), .005)
        features = np.clip(obs[:, fields]/scale, -12, 12).astype(array_dtype)
        if a.absolute_inputs:features=np.c_[features,np.abs(features)]
        seq = {int(ep): np.flatnonzero(episode == ep) for ep in np.unique(episode)}
        assert all(np.unique(train[ids]).size == 1 for ids in seq.values())
        model = Network(a.kind, features.shape[1], a.seed, a.norm_slowdown,a.modular)
        model.raw_slowdown_loss = a.raw_slowdown_loss
        if not 0<=a.drift_weight<=2:raise ValueError('Invalid integrated-action loss weight')
        parent_sha=None
        if a.initialize_checkpoint is not None:
            if a.parent_metadata is None:raise ValueError('Parent metadata required')
            parent=json.loads(a.parent_metadata.read_text());parent_sha=sha(a.initialize_checkpoint)
            assert parent_sha==parent['checkpoint_sha256']
            assert parent['data_sha256']==sha(a.data) and parent['kind']==a.kind and parent['modular']==a.modular
            with np.load(a.initialize_checkpoint) as z,torch.no_grad():
                np.testing.assert_array_equal(z['fields'],fields);np.testing.assert_array_equal(z['scale'],scale)
                assert bool(z['norm_slowdown'])==a.norm_slowdown
                assert (bool(z['absolute_inputs']) if 'absolute_inputs' in z.files else False)==a.absolute_inputs
                (model.core.weight_ih_l0 if a.kind=='rnn' else model.core.weight).copy_(torch.from_numpy(z['input_w']))
                model.head.weight.copy_(torch.from_numpy(z['output_w']))
                if a.kind=='rnn':model.core.weight_hh_l0.copy_(torch.from_numpy(z['recurrent_w']))
        if not 0<a.learning_rate<=.01:raise ValueError('Invalid learning rate')
        optimizer = torch.optim.AdamW(model.parameters(), lr=a.learning_rate, weight_decay=a.weight_decay)
        rng = np.random.default_rng(a.seed+2000)
        def predict_all(ids):
            values = {}
            was_training = model.training
            model.eval()
            with torch.no_grad():
                for ep in ids:
                    index = seq[int(ep)]
                    values[int(ep)] = model(torch.from_numpy(features[index])[None])[0][0].numpy()
            model.train(was_training)
            return values
        history, schedule = [], []
        best, best_state, best_step = float('inf'), None, None
        proxy_scale=torch.tensor([.32,.32,.32,.6,.6,.6])/torch.tensor([.02,.02,.02,.05,.05,.05])*.04
        def validation_score(values):
            errors=[values[int(ep)]-target[seq[int(ep)]] for ep in val_ids]
            mse=float(np.mean(np.concatenate(errors)**2))
            windows=[]
            for err in errors:
                for start in range(0,len(err)-15,16):
                    windows.append(np.sum(err[start:start+16,1:],axis=0)*proxy_scale.numpy())
            integrated=float(np.mean(np.asarray(windows)**2))
            return mse,integrated,mse+a.drift_weight*integrated
        if parent_sha is not None:
            vm,vd,best=validation_score(predict_all(val_ids));best_state=copy.deepcopy(model.state_dict());best_step=0
            history.append(dict(update=0,validation_mse=vm,validation_integrated_proxy=vd,selection_score=best))
        update, epoch = 0, 0
        while update < a.updates:
            order = rng.permutation(train_ids)
            for start in range(0, len(order), 8):
                group = order[start:start+8]
                length = max(len(seq[int(ep)]) for ep in group)
                x = np.zeros((len(group), length, features.shape[1]), array_dtype)
                y = np.zeros((len(group), length, 7), array_dtype)
                w = np.zeros((len(group), length), array_dtype)
                for i, ep in enumerate(group):
                    ids = seq[int(ep)]; n = len(ids)
                    x[i, :n], y[i, :n], w[i, :n] = features[ids], target[ids], importance[ids]
                hidden = None
                for offset in range(0, length, a.tbptt_steps):
                    xx, yy, ww = [torch.from_numpy(v[:, offset:offset+a.tbptt_steps]) for v in (x, y, w)]
                    prediction, hidden = model(xx, hidden)
                    mass = 8*a.tbptt_steps*float(importance[train].mean()) if a.global_loss else ww.sum()
                    loss = (((prediction-yy)**2)*ww[..., None]).sum()/(7*mass)
                    pair_w = torch.minimum(ww[:, 1:], ww[:, :-1])
                    delta = ((prediction[:, 1:]-prediction[:, :-1])-(yy[:, 1:]-yy[:, :-1]))**2
                    delta_loss = (delta*pair_w[..., None]).sum()/(7*pair_w.sum().clamp_min(1))
                    total = loss+a.action_delta_weight*delta_loss
                    if a.drift_weight and prediction.shape[1]>=16:
                        residual=prediction[...,1:]-yy[...,1:]
                        accumulated=residual.unfold(1,16,1).sum(-1)*proxy_scale
                        window_weights=ww.unfold(1,16,1).amin(-1)
                        integrated=(accumulated.square()*window_weights[...,None]).sum()/(6*window_weights.sum().clamp_min(1))
                        total=total+a.drift_weight*integrated
                    if not torch.isfinite(total):
                        raise ValueError('Nonfinite training loss')
                    optimizer.zero_grad(set_to_none=True)
                    total.backward()
                    nn.utils.clip_grad_norm_(model.parameters(), 1.)
                    rate = a.learning_rate
                    if a.lr_schedule == 'cosine':
                        rate *= .01+.99*.5*(1+math.cos(math.pi*update/max(a.updates-1,1)))
                    for group_param in optimizer.param_groups:
                        group_param['lr'] = rate
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
            validation_mse,validation_integral,score=validation_score(values)
            history.append(dict(update=update, epoch=epoch, last_train_loss=float(total.detach()), validation_mse=validation_mse,
                                validation_integrated_proxy=validation_integral,selection_score=score))
            if epoch % 20 == 0 or update == a.updates:
                tv = predict_all(train_ids)
                history[-1]['full_train_deployed_mse'] = float(np.mean(np.concatenate([
                    tv[int(e)]-target[seq[int(e)]] for e in train_ids])**2))
            if score < best or a.selection == 'final':
                best, best_state, best_step = score, copy.deepcopy(model.state_dict()), update
            write(a.output/'progress.json',dict(update=update,epoch=epoch,learning_rate=rate,
                                               latest=history[-1],selected_update=best_step))
            write(a.output/'history.json',history)
            epoch += 1
        model.load_state_dict(best_state)
        np.savez_compressed(a.output/'checkpoint.npz', **model.export(fields, scale,a.absolute_inputs))
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
        masks = ([('real_train', train & physical), ('real_identity_validation', ~train & physical)]
                 if metadata.get('all_real_execution') else [('synthetic_train', train & (episode < 48)),
                    ('synthetic_holdout', ~train), ('seen_physical_histories', physical)])
        for name, mask in masks:
            groups[name] = dict(samples=int(mask.sum()), action_mse=float(np.mean((predictions[mask]-target[mask])**2)) if np.any(mask) else None)
        result = dict(kind=a.kind, seed=a.seed, updates=update, selected_update=best_step, width=128,
                      target=a.target, norm_slowdown=a.norm_slowdown,
                      modular=a.modular,active_trainable_parameters=model.active_parameters,learning_rate=a.learning_rate,
                      drift_weight=a.drift_weight,drift_window_s=.64,parent_checkpoint_sha256=parent_sha,
                      absolute_inputs=a.absolute_inputs,precision=a.precision,
                      trainable_parameters=sum(p.numel() for p in model.parameters()), fields=fields.tolist(),
                      data_sha256=sha(a.data), metadata_sha256=sha(a.metadata), lineage=metadata['lineage'],
                      checkpoint_sha256=sha(a.output/'checkpoint.npz'), schedule_sha256=sha(a.output/'schedule.json'),
                      exported_replay_sha256=sha(a.output/'exported_replay.npz'), groups=groups,
                      numpy_torch_max_abs=max_error, unused_field_isolation_pass=True, zero_input_equilibrium_pass=True,
                      batch_size=8, tbptt_steps=a.tbptt_steps, actual_nonpadding_observations=sum(s[3] for s in schedule),
                      action_delta_weight=a.action_delta_weight,weight_decay=a.weight_decay,
                      lr_schedule=a.lr_schedule,checkpoint_selection=a.selection,
                      global_loss=a.global_loss,raw_slowdown_loss=a.raw_slowdown_loss, source_sha256=source_hash,
                      validation_split=metadata.get('selection_split','Legacy synthetic identity holdout'),
                      limitation='Data provenance and whole-history split declared in dataset metadata; physical success measured separately. No runtime teacher/controller. Width-matched, not parameter-matched.')
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
