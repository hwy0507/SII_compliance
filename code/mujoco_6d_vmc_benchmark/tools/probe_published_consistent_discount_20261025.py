"""Finite fresh-learner discount study with consistent PBRS on complete episodes.

Reconstructs a separate cycle6 replay subset; formal replay is never relabeled.
Same fresh full learner and sampling stream; only Bellman and shaping gamma
change together. No online performance claim and no auxiliary weights saved.
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

from diagnose_published_value_bound_20261025 import soft_upper_bound, audit_episode
from validate_published_finite_check_20261025 import digest


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def discount_rewards(rows, gamma, *, source_gamma=.9995, horizon=1375):
    if not 0 < gamma < 1:
        raise ValueError('Discount must lie strictly between zero and one')
    if len(rows) != horizon or any(r['reward_terms']['failure_tail'] != 0 for r in rows):
        raise ValueError('Only complete full-horizon episodes without failure tails are supported')
    audit_episode(rows, source_gamma, 5.)
    changed = copy.deepcopy(rows)
    for row in changed:
        terms = row['reward_terms']
        progress = 5.*(gamma*(0. if row['done'] else terms['next_potential'])-terms['current_potential'])
        row['reward'] += progress-terms['progress']
        terms['progress'] = progress
        terms['final_reward'] = row['reward']
    audit_episode(changed, gamma, 5.)
    return np.asarray([r['reward'] for r in changed], dtype=np.float32)


def main(args):
    p=json.loads(args.registration.read_text())
    for name,expected in p['source_hashes'].items():
        if sha(Path(__file__).with_name(name))!=expected:raise ValueError('Frozen probe source drift')
    os.sched_setaffinity(0,{p['cpus'][args.controller]});os.nice(10);torch.set_num_threads(1)
    root=Path(p['runtime'])
    if sha(root/'RUNTIME.json')!=p['runtime_sha256']:raise ValueError('Runtime manifest drift')
    hashes=json.loads((root/'SOURCE_HASHES.json').read_text())
    for name in ['published_compliance_learner_20261025.py','published_replay_device_cache_20261025.py',
                 'train_published_compliance_20261025.py','spt_rl_reward_20261025.py','training_comparison_metrics_20261025.py']:
        if sha(root/'source/tools'/name)!=hashes['tools/'+name]:raise ValueError('Runtime source drift')
    for name,expected in p['reward_sources'].items():
        if sha(root/'source/tools'/name)!=expected:raise ValueError('Reward bound contract drift')
    sys.path.insert(0,str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from published_replay_device_cache_20261025 import DeviceReplayCache
    from train_published_compliance_20261025 import Replay
    item=p['checkpoints'][args.controller]
    if sha(item['path'])!=item['sha256']:raise ValueError('Immutable checkpoint drift')
    ck=torch.load(item['path'],map_location='cpu',weights_only=False)
    if (ck['controller']!=args.controller or ck['cycle']!=6
            or ck['boundary']!='complete_condition_cycle' or ck['learner']['algorithm']!='cheq'):
        raise ValueError('Expected registered complete CHEQ cycle6')
    state,original=ck['learner'],ck['replay']['arrays'];parent_digest=digest(state);replay_digest=digest(ck['replay'])
    if ck['replay']['size']!=ck['steps'] or ck['replay']['cursor']!=ck['steps']:
        raise ValueError('Expected unwrapped original replay')
    if sha(item['transitions'])!=item['transitions_sha256']:
        raise ValueError('Frozen transition evidence drift')
    from collections import defaultdict
    groups=defaultdict(list)
    for line in Path(item['transitions']).read_text().splitlines():
        row=json.loads(line)
        if row['cycle']!=6:raise ValueError('Expected isolated cycle6 transitions')
        groups[row['condition']].append(row)
    if len(groups)!=30:raise ValueError('Expected all30 registered conditions')
    rows=[row for group in groups.values() for row in group]
    indices=np.array([r['step']-1 for r in rows])
    if len(set(indices))!=len(indices):raise ValueError('Duplicate transition index')
    arrays={k:v[indices].copy() for k,v in original.items()}
    np.testing.assert_array_equal(arrays['rewards'][:,0],np.array([r['reward'] for r in rows],dtype=np.float32))
    np.testing.assert_array_equal(arrays['dones'][:,0],np.array([r['done'] for r in rows],dtype=np.float32))
    variants={gamma:np.concatenate([discount_rewards(group,gamma) for group in groups.values()])[:,None]
              for gamma in (.99,.9995)}
    np.testing.assert_array_equal(variants[.9995],arrays['rewards'])
    subset_digest=digest(arrays)
    learner=PublishedLearner(root,dimension=arrays['actions'].shape[1],direct=args.controller=='direct',
        seed=p['seed'],device=args.device,algorithm='cheq',critic_layer_norm=state['critic_layer_norm'],
        numerical_amendments=state['numerical_amendments'])
    initial=learner.state_dict()
    if initial['num_gradient_steps']!=0 or initial['q_optimizer']['state'] or initial['actor_optimizer']['state']:
        raise AssertionError('Expected entirely fresh learner, no inherited weights or optimizer')
    replay=Replay(arrays['actions'].shape[1],arrays['observations'].shape[1],p['seed'])
    replay.arrays=arrays;replay.size=len(rows);replay.cursor=len(rows);cache=DeviceReplayCache(replay,args.device)
    terminal=np.flatnonzero(arrays['dones'][:,0]==1)
    ordinary=np.flatnonzero(arrays['dones'][:,0]==0)
    sample=np.random.default_rng(p['seed']).choice(ordinary,p['diagnostic_samples'],replace=False)
    discounts=p['discount_order'][args.controller]
    if len(discounts)!=2 or set(discounts)!={.99,.9995}:raise ValueError('Expected registered discount arms')
    args.output.mkdir(exist_ok=False)

    def diagnose(gamma):
        agent=learner.learner.agent
        # Diagnostic sampling must not change the next optimization RNG stream.
        with torch.random.fork_rng(devices=[learner.device.index]),torch.no_grad():
            with torch.cuda.device(learner.device):torch.cuda.manual_seed(p['seed']+17)
            obs=torch.as_tensor(arrays['observations'][sample],device=args.device)
            actions=torch.as_tensor(arrays['actions'][sample],device=args.device)
            q=torch.stack([agent.get_q_value(obs,actions,i).reshape(-1) for i in range(agent.ensemble_size)])
            action,log_pi=agent.get_action_and_log_prob(obs)
            policy_q=torch.stack([agent.get_q_value(obs,action,i).reshape(-1) for i in range(agent.ensemble_size)])
            uncertainty=policy_q.std(dim=0)
            tobs=torch.as_tensor(arrays['observations'][terminal],device=args.device)
            tact=torch.as_tensor(arrays['actions'][terminal],device=args.device)
            tq=torch.stack([agent.get_q_value(tobs,tact,i).reshape(-1) for i in range(agent.ensemble_size)])
            reward=torch.as_tensor(variants[gamma][terminal,0],device=args.device)
            mask=torch.as_tensor(arrays['masks'][terminal].T,device=args.device).bool()
            error=abs(tq-reward);alpha=float(learner.learner.alpha)
            bound=float(soft_upper_bound(alpha,learner.learner.gamma,1375,
                learner.spaces.action_space.low,learner.spaces.action_space.high,
                terminal_cap=30.,shaping_weight=5.))
            return dict(replay_q_mean=float(q.mean()),
                in_bag_terminal_mae=float(error[mask].mean()),alpha=alpha,global_soft_bound=bound,
                above_global_bound_fraction=float((q>bound+.01).float().mean()),
                sampled_policy_entropy=float(-log_pi.mean()),uncertainty_mean=float(uncertainty.mean()),
                implied_minimum_rl_authority_fraction=float((uncertainty>=.2).float().mean()))

    results=[];initial_reference=None
    for gamma in discounts:
        learner.load_state_dict(copy.deepcopy(initial))
        learner.learner.gamma=gamma
        cache.arrays['rewards'].copy_(torch.as_tensor(variants[gamma],device=args.device))
        for param in learner.learner.agent.parameters():param.grad=None
        restored=digest(learner.state_dict())
        if initial_reference is None:initial_reference=restored
        elif restored!=initial_reference:raise AssertionError('Arms have unequal fresh full states')
        replay.rng=np.random.default_rng(p['seed'])
        entry=dict(gamma=gamma,initial_full_state_sha256=restored,initial=diagnose(gamma),curve=[])
        start=time.time()
        for update in range(p['updates_per_arm']):
            metrics=learner.update(cache.sample(p['batch_size']))
            if (update+1)%p['record_every']==0:
                row=dict(updates=update+1,metrics=metrics,diagnostic=diagnose(gamma),updated_unix=time.time())
                entry['curve'].append(row);write(args.output/'PROGRESS.json',dict(gamma=gamma,**row))
        if learner.learner.num_gradient_steps!=p['updates_per_arm']:raise AssertionError('Update budget mismatch')
        if digest(state)!=parent_digest or digest(ck['replay'])!=replay_digest:
            raise AssertionError('Immutable parent or original replay changed')
        # Cache sampling/scaling must not mutate the authoritative CPU replay.
        if digest(replay.arrays)!=subset_digest:
            raise AssertionError('Discount study modified original CPU subset')
        entry.update(final=diagnose(gamma),elapsed_s=time.time()-start,
            sampling_rng_sha256=digest(replay.rng.bit_generator.state),parent_unchanged=True,
            terminal_discount_1374=gamma**1374)
        results.append(entry);write(args.output/f'gamma_{gamma:g}.json',entry)
    if results[0]['sampling_rng_sha256']!=results[1]['sampling_rng_sha256']:
        raise AssertionError('Unequal replay sampling streams')
    write(args.output/'FINISHED.json',dict(controller=args.controller,results=results,
        checkpoint_sha256=item['sha256'],registration_sha256=sha(args.registration),
        updates=2*p['updates_per_arm'],new_physics=0,auxiliary_weights_saved=False,formal_training_changed=False,
        fresh_entire_learner=True,parent_unchanged=True,finished_unix=time.time(),
        replay_subset_size=len(rows),reward_and_bellman_discounts_matched=True,
        limitations=['Frozen historical behavior/context, not online policy-quality evidence.',
            'Same complete fresh initialization and alpha; Bellman/PBRS gamma changed together.',
            'Single fresh seed and finite update budget; no convergence or transfer claim.',
            'Low discount attenuates delayed terminal success; stable Q alone cannot select it.',
            'All30 full55s episodes included; this reducer rejects early abort episodes.',
            'CHEQ absolute uncertainty thresholds unchanged; implied mixing is diagnostic only.']))



if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True);parser.add_argument('--controller',required=True)
    parser.add_argument('--device',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:main(args)
    except BaseException as error:
        args.output.mkdir(exist_ok=True);write(args.output/'FAILURE.json',dict(error=repr(error)));raise
