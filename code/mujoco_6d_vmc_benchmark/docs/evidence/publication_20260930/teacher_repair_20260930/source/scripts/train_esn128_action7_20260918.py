"""Balanced BC. Checkpoint selection uses source validation, never office."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import numpy as np
import torch
from torch import nn
from esn128_action7_20260918 import ESN128Action7


def dump(path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, indent=2, allow_nan=False)); temp.replace(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--dataset', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--epochs', type=int, default=120)
    p.add_argument('--posture-invariant', action='store_true')
    p.add_argument('--smoothness', type=float, default=0.)
    p.add_argument('--rest-weight', type=float, default=1.)
    p.add_argument('--weight-decay', type=float, default=1e-5)
    p.add_argument('--yaw-augmentation', action='store_true')
    p.add_argument('--seed', type=int, default=20260918)
    p.add_argument('--corner-repeat', type=int, default=1)
    args = p.parse_args(); out = args.output; out.mkdir(parents=True, exist_ok=True)
    if (out / 'TRAINING_COMPLETE.json').exists():
        raise RuntimeError('Preserve completed training')
    torch.set_num_threads(4); torch.manual_seed(args.seed)
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    root = args.dataset; manifest = json.loads((root / 'manifest.json').read_text())
    assert json.loads((root / 'READY.json').read_text())['ready']
    dataset_sha = hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest()
    with np.load(root / 'dataset/normalization_train_only.npz') as z:
        actor = ESN128Action7(z['mean'], z['std'], seed=args.seed)
    if args.posture_invariant:
        # The task-space teachers do not directly consume absolute q or dq;
        # task twist/errors/load estimates remain encoder-derived inputs.
        actor.input_mask[:14] = 0.
    if args.yaw_augmentation:
        # Rotate world-vector inputs together with their action labels. Joint
        # coordinates/loads do not change under a world-coordinate rotation.
        # Equal xy normalization avoids encoding one preferred world heading.
        for j in (14,17,20,23,26,29,39,42):
            actor.mean[j:j+2]=0.
            actor.std[j:j+2]=max(actor.std[j],actor.std[j+1])
        rng=np.random.default_rng(2026091807)
        extra=[dict(r,yaw_augmentation=float(rng.uniform(-np.pi,np.pi))) for r in manifest['train_clean']]
        manifest['train']=manifest['train']+extra
    original_train=list(manifest['train']); extra=[r for r in original_train if r['scene']=='corner']*(max(1,args.corner_repeat)-1); manifest['train']=original_train+extra
    rows = manifest['train'] + manifest['validation'] + manifest['test']
    train_n = len(manifest['train']); val_n = len(manifest['validation'])
    contract = dict(reservoir=128, readout_hidden=128, output=7, observation=45,
        trainable='nonlinear readout only; fixed reservoir', policy_hz=25,
        input='proprioception plus shared task command; no scene/time/contact truth',
        selection='scene/episode balanced source-validation scaled action MSE',
        sampler='uniform scene, then uniform episode, then uniform time within episode',
        smoothing_alpha=1., seed=args.seed, dataset_manifest_sha256=dataset_sha,
        office_used_for_training_or_selection=False, device=str(device), epochs=args.epochs,
        posture_invariant=args.posture_invariant,smoothness=args.smoothness,
        rest_weight=args.rest_weight,weight_decay=args.weight_decay,yaw_augmentation=args.yaw_augmentation)
    dump(out / 'protocol.json', contract)
    win = torch.tensor(actor.win, dtype=torch.float32, device=device)
    w = torch.tensor(actor.w, dtype=torch.float32, device=device)
    leak = torch.tensor(actor.leak, dtype=torch.float32, device=device)
    mean = torch.tensor(actor.mean, dtype=torch.float32, device=device)
    std = torch.tensor(actor.std, dtype=torch.float32, device=device)
    features = []; targets = []; lengths = []
    start_time = time.time()
    # Parallel independent sequences on the GPU, with a fresh state per episode.
    for begin in range(0, len(rows), 64):
        chunk = rows[begin:begin+64]; arrays = []
        for row in chunk:
            trace_path = Path(row['trace']); trace_path = trace_path if trace_path.is_absolute() else root / trace_path
            with np.load(trace_path, allow_pickle=False) as z:
                raw=z['observation'].copy();target=z['teacher_action'].copy()
                if 'yaw_augmentation' in row:
                    theta=row['yaw_augmentation'];c,s=np.cos(theta),np.sin(theta)
                    rotation=np.array([[c,-s,0],[s,c,0],[0,0,1]])
                    for j in (14,17,20,23,26,29,39,42):raw[:,j:j+3]=raw[:,j:j+3]@rotation.T
                    target[:,1:4]=target[:,1:4]@rotation.T;target[:,4:7]=target[:,4:7]@rotation.T
                    target=np.clip(target,-1.,1.)
                arrays.append((raw,target))
        maxlen = max(len(x) for x, _ in arrays)
        batch = torch.zeros((len(chunk), maxlen, 45), device=device)
        for i, (x, _) in enumerate(arrays):
            batch[i, :len(x)] = torch.as_tensor(x, device=device)
        x = torch.clamp((batch-mean)/std, -12, 12)*torch.as_tensor(actor.input_mask,dtype=torch.float32,device=device)
        drive = x @ win[:, 1:].T + win[:, 0]
        state = torch.zeros((len(chunk), 128), device=device)
        hist = torch.empty((len(chunk), maxlen, 128), device=device)
        with torch.no_grad():
            for t in range(maxlen):
                state = state + leak*(torch.tanh(drive[:, t] + state @ w.T)-state)
                hist[:, t] = state
        for i, (raw, y) in enumerate(arrays):
            features.append(torch.cat((x[i, :len(raw)], hist[i, :len(raw)]), dim=1))
            targets.append(torch.as_tensor(y, device=device)); lengths.append(len(raw))
        dump(out / 'status.json', dict(phase='reservoir_features', episodes=min(begin+64,len(rows)), total=len(rows)))
    starts = np.r_[0, np.cumsum(lengths)]
    f = torch.cat(features); y = torch.cat(targets); del features, targets
    clean_n = len(manifest['train_clean'])
    assert all(not r.get('augmentation') for r in rows[:clean_n])
    fmean = f[:starts[clean_n]].mean(0)
    fstd = f[:starts[clean_n]].std(0, unbiased=False).clamp_min(.03)
    f = (f-fmean)/fstd
    scale = y[:starts[clean_n]].std(0, unbiased=False).clamp_min(.03)
    actor.head.update(fmean=fmean.cpu().numpy(), fstd=fstd.cpu().numpy())
    head = nn.Sequential(nn.Linear(173,128), nn.Tanh(), nn.Linear(128,7)).to(device)
    # Output bias near the teacher marginal mean avoids an initial 50% slowdown.
    with torch.no_grad():
        ym = y[:starts[clean_n]].mean(0)
        head[2].bias.copy_(torch.atanh(ym.clamp(-.95,.95)))
        head[2].bias[0] = torch.logit(ym[0].clamp(.001,.999))
    def predict(z):
        raw = head(z)
        return torch.cat((torch.sigmoid(raw[:, :1]), torch.tanh(raw[:, 1:])), dim=1)
    optimizer = torch.optim.AdamW(head.parameters(), lr=.001, weight_decay=args.weight_decay)
    scenes = ('ball','push','corner','table_corner')
    episode_tables = {}
    for scene in scenes:
        indices = [i for i, r in enumerate(rows[:train_n]) if r['scene']==scene]
        episode_tables[scene] = (torch.tensor(starts[indices],device=device),
            torch.tensor(np.asarray(lengths)[indices],device=device))
    def sample():
        indices=[]
        for scene in scenes:
            bases, lens = episode_tables[scene]
            ids = torch.randint(len(bases),(1024,),device=device)
            indices.append(bases[ids]+(torch.rand(1024,device=device)*lens[ids]).long())
        return torch.cat(indices)
    def evaluate(begin,end):
        totals={s:[] for s in scenes}; raw_totals={s:[] for s in scenes}
        with torch.no_grad():
            for i in range(begin,end):
                err=(predict(f[starts[i]:starts[i+1]])-y[starts[i]:starts[i+1]])**2
                totals[rows[i]['scene']].append(float((err/scale.square()).mean()))
                raw_totals[rows[i]['scene']].append(float(err.mean()))
        return dict(balanced_scaled_mse=float(np.mean([np.mean(totals[s]) for s in scenes])),
            per_scene_scaled_mse={s:float(np.mean(totals[s])) for s in scenes},
            per_scene_action_mse={s:float(np.mean(raw_totals[s])) for s in scenes})
    best=float('inf'); history=[]; best_epoch=0
    for epoch in range(args.epochs):
        head.train(); loss_sum=0.
        for step in range(64):
            idx=sample(); optimizer.zero_grad(set_to_none=True)
            prediction=predict(f[idx])
            per_sample=((prediction-y[idx])/scale).square().mean(1)
            rest=(torch.linalg.vector_norm(y[idx,1:],dim=1)<.02)&(y[idx,0]<.02)
            weights=1.+(args.rest_weight-1.)*rest.float()
            loss=(per_sample*weights).sum()/weights.sum()
            if args.smoothness:
                # Finite-difference local Jacobian regularization, no new
                # teacher labels and no office data. Applicable to MLP too.
                noisy=predict(f[idx]+torch.randn_like(f[idx])*.1)
                loss=loss+args.smoothness*((noisy-prediction)/scale/.1).square().mean()
            loss.backward(); nn.utils.clip_grad_norm_(head.parameters(),5.); optimizer.step()
            loss_sum += float(loss.detach())
        if (epoch+1)%5==0 or epoch==0:
            head.eval(); val=evaluate(train_n,train_n+val_n)
            record=dict(epoch=epoch+1,loss=loss_sum/64,validation=val,elapsed_s=time.time()-start_time)
            history.append(record); print(json.dumps(record),flush=True)
            if val['balanced_scaled_mse']<best:
                best=val['balanced_scaled_mse'];best_epoch=epoch+1
                for key,tensor in (('w1',head[0].weight),('b1',head[0].bias),('w2',head[2].weight),('b2',head[2].bias)):
                    actor.head[key]=tensor.detach().cpu().numpy().copy()
                actor.save(out/'best.tmp.npz',dict(**contract,best_epoch=best_epoch,validation=val))
                (out/'best.tmp.npz').replace(out/'best.npz')
            dump(out/'status.json',dict(phase='readout_training',**record,best_epoch=best_epoch))
            dump(out/'history.json',history)
    # Restore source-validation-selected weights before any holdout evaluation.
    actor=ESN128Action7.load(out/'best.npz')
    with torch.no_grad():
        for tensor,key in ((head[0].weight,'w1'),(head[0].bias,'b1'),(head[2].weight,'w2'),(head[2].bias,'b2')):
            tensor.copy_(torch.as_tensor(actor.head[key],device=device))
    holdout=evaluate(train_n+val_n,len(rows))
    validation=evaluate(train_n,train_n+val_n)
    trace_path = Path(rows[train_n]['trace']); trace_path = trace_path if trace_path.is_absolute() else root / trace_path
    with np.load(trace_path) as z:
        replay=np.stack([actor.act(o) for o in z['observation']])
    with torch.no_grad():expected=predict(f[starts[train_n]:starts[train_n+1]]).cpu().numpy()
    delta=float(np.max(np.abs(replay-expected)))
    if delta>5e-4:raise RuntimeError(f'Sequential deployment mismatch: {delta}')
    result=dict(**contract,best_epoch=best_epoch,validation=validation,source_holdout=holdout,
        trainable_parameters=sum(p.numel() for p in head.parameters()),
        deployment_max_abs_error=delta,elapsed_s=time.time()-start_time,
        checkpoint_sha256=hashlib.sha256((out/'best.npz').read_bytes()).hexdigest(),
        training_sequences=train_n,training_samples=int(starts[train_n]),complete=True)
    dump(out/'TRAINING_COMPLETE.json',result);dump(out/'status.json',dict(phase='complete',**result))


if __name__=='__main__':main()
