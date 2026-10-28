"""Finite temporal transfer diagnostic on recorded, entropy-free behavior returns.
Fit cycle 0 only; assess cycle 1 from changing behavior policies. This is not
soft-Q evaluation or an unseen-condition test. Parent initialization is from
cycle 0, never cycle 1. No auxiliary weights are promoted.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def write(p, obj):
    p = Path(p)
    tmp = p.with_suffix('.tmp')
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')
    tmp.replace(p)


def returns(rewards, gamma):
    out = np.empty(len(rewards), np.float64)
    value = 0.
    for i in range(len(rewards)-1, -1, -1):
        value = float(rewards[i]) + gamma * value
        out[i] = value
    return out


def main(a):
    p = json.loads(a.registration.read_text())
    assert sha(__file__) == p['source_sha256']
    item = p['methods'][a.method]
    os.sched_setaffinity(0, {item['cpu']})
    os.nice(10)
    torch.set_num_threads(1)
    rt = Path(p['runtime'])
    assert sha(rt/'RUNTIME.json') == p['runtime_sha256']
    for name, h in json.loads((rt/'SOURCE_HASHES.json').read_text()).items():
        assert sha(rt/'source'/name) == h
    assert sha(item['checkpoint']) == item['checkpoint_sha256']
    assert sha(item['transitions']) == item['transitions_sha256']
    assert sha(item['parent_checkpoint']) == item['parent_checkpoint_sha256']
    ck = torch.load(item['checkpoint'], map_location='cpu', weights_only=False)
    parent_ck = torch.load(item['parent_checkpoint'], map_location='cpu', weights_only=False)
    assert ck['cycle'] == 1 and parent_ck['cycle'] == 0
    assert ck['boundary'] == parent_ck['boundary'] == 'complete_condition_cycle'
    arrays = ck['replay']['arrays']
    assert ck['steps'] == ck['replay']['size']
    rows = [json.loads(l) for l in Path(item['transitions']).read_text().splitlines()]
    assert len(rows) == ck['steps'] and {t['cycle'] for t in rows} == {0,1}
    np.testing.assert_array_equal(arrays['rewards'][:,0], np.asarray([t['reward'] for t in rows],np.float32))
    np.testing.assert_array_equal(arrays['dones'][:,0], np.asarray([t['done'] for t in rows],np.float32))
    for key, value in parent_ck['replay']['arrays'].items():
        np.testing.assert_array_equal(arrays[key][:parent_ck['steps']], value)
    conditions = sorted({t['condition'] for t in rows})
    assert len(conditions) == 30
    groups = {(cycle,c): np.array([i for i,t in enumerate(rows) if t['condition']==c and t['cycle']==cycle]) for cycle in [0,1] for c in conditions}
    y = np.empty(ck['steps'], np.float64)
    for (cycle,c), ids in groups.items():
        assert 0 < len(ids) <= 1375
        assert arrays['dones'][ids,0].sum()==1 and rows[ids[-1]]['done']
        np.testing.assert_array_equal(arrays['observations'][ids,-1], ((1375-np.arange(len(ids)))/1375).astype(np.float32))
        np.testing.assert_array_equal(arrays['next_observations'][ids[:-1]], arrays['observations'][ids[1:]])
        y[ids] = returns(arrays['rewards'][ids,0],p['gamma'])
        np.testing.assert_allclose(y[ids[:-1]],arrays['rewards'][ids[:-1],0]+p['gamma']*y[ids[1:]],rtol=0,atol=1e-12)
        assert y[ids[-1]]==arrays['rewards'][ids[-1],0]
    train = np.concatenate([ids for (cycle,c),ids in groups.items() if cycle==0])
    test = np.concatenate([ids for (cycle,c),ids in groups.items() if cycle==1])
    assert len(train)==41250 and len(train)+len(test)==ck['steps'] and not np.intersect1d(train,test).size
    out = Path(item['output'])
    out.mkdir(exist_ok=False)
    receipt = dict(pid=os.getpid(), method=a.method, cpu=item['cpu'], device=item['device'],
        registration_sha256=sha(a.registration), checkpoint_sha256=sha(item['checkpoint']), parent_checkpoint_sha256=sha(item['parent_checkpoint']),
        source_sha256=sha(__file__), train_count=len(train), withheld_count=len(test),
        new_physics=0, actor_updates=0, auxiliary_only=True, targets_sha256=hashlib.sha256(y.tobytes()).hexdigest())
    write(out/'DATA_VALIDATED.json', receipt)
    sys.path.insert(0, str(rt/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    state = parent_ck['learner']
    learner = PublishedLearner(rt, dimension=arrays['actions'].shape[1], direct=a.method=='direct',
        seed=p['seed'], device=item['device'], algorithm='cheq', critic_clock=True,
        critic_layer_norm=state['critic_layer_norm'], numerical_amendments=state['numerical_amendments'])
    agent = learner.learner.agent
    fresh = copy.deepcopy(agent.ensemble.state_dict())
    agent.load_state_dict(state['agent'])
    parent = copy.deepcopy(agent.ensemble.state_dict())
    actor = {k:v.detach().clone() for k,v in agent.actor.state_dict().items()}
    x = torch.as_tensor(np.concatenate([arrays['observations'], arrays['actions']], 1), device=item['device'])
    target = torch.as_tensor(y, dtype=torch.float32, device=item['device'])
    ti = torch.as_tensor(train, device=item['device'])
    vi = torch.as_tensor(test, device=item['device'])
    def predict(ids):
        return torch.stack([q.q_net(x[ids]).flatten() for q in agent.ensemble])
    def metrics():
        result = {}
        with torch.no_grad():
            for name, ids in [('fit_cycle0', ti), ('transfer_cycle1', vi)]:
                errors = torch.cat([(predict(ix)-target[ix]).flatten() for ix in ids.split(2048)])
                result[name] = dict(mae=float(errors.abs().mean()), rmse=float(errors.square().mean().sqrt()))
        return result
    write(out/'STARTED.json', dict(**receipt, started_unix=time.time(), initial=metrics()))
    results = []
    for arm in p['arm_order'][a.method]:
        agent.ensemble.load_state_dict(parent if arm == 'parent' else fresh)
        optimizer = torch.optim.Adam(agent.ensemble.parameters(), lr=p['learning_rate'])
        torch.manual_seed(p['seed'])
        curve = [dict(update=0, metrics=metrics())]
        for step in range(1, p['updates_per_arm']+1):
            ids = ti[torch.randint(len(ti), (p['batch_size'],), device=item['device'])]
            loss = (predict(ids)-target[ids]).square().mean()
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            if step % p['record_every'] == 0:
                assert torch.isfinite(loss) and all(torch.isfinite(v).all() for v in agent.ensemble.parameters())
                row = dict(update=step, loss=float(loss), metrics=metrics(), updated_unix=time.time())
                curve.append(row)
                write(out/'PROGRESS.json', dict(method=a.method, arm=arm, **row))
        results.append(dict(arm=arm, curve=curve))
        write(out/(arm+'.json'), results[-1])
    assert all(torch.equal(actor[k], v) for k,v in agent.actor.state_dict().items())
    assert sha(item['checkpoint']) == item['checkpoint_sha256']
    write(out/'FINISHED.json', dict(**receipt, finished_unix=time.time(), results=results,
        auxiliary_updates=2*p['updates_per_arm'], actor_unchanged=True, promoted_weights=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration', type=Path, required=True)
    parser.add_argument('--method', required=True)
    args = parser.parse_args()
    try:
        main(args)
    except Exception as exc:
        p = json.loads(args.registration.read_text())
        out = Path(p['methods'][args.method]['output'])
        out.mkdir(exist_ok=True)
        write(out/'FAILURE.json', dict(error=repr(exc), failed_unix=time.time(), pid=os.getpid()))
        raise
