"""Finite fresh-learner reward-unit study on immutable real replay.

Only sampled rewards are multiplied by a fixed positive scalar. Both arms
restore the same fresh actor/critics/targets/optimizers/alpha/RNG. All original
replay fields and parent checkpoints remain immutable; no weights are saved.
This does not evaluate online task success or prove a transferable remedy.
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

from diagnose_published_value_bound_20261025 import soft_upper_bound
from validate_published_finite_check_20261025 import digest


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def scaled_batch(batch,scale):
    if not np.isfinite(scale) or scale<=0:raise ValueError('Positive finite reward scale required')
    return dict(batch,rewards=batch['rewards']*scale)


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
    state,arrays=ck['learner'],ck['replay']['arrays'];parent_digest=digest(state);replay_digest=digest(ck['replay'])
    learner=PublishedLearner(root,dimension=arrays['actions'].shape[1],direct=args.controller=='direct',
        seed=p['seed'],device=args.device,algorithm='cheq',critic_layer_norm=state['critic_layer_norm'],
        numerical_amendments=state['numerical_amendments'])
    initial=learner.state_dict()
    if initial['num_gradient_steps']!=0 or initial['q_optimizer']['state'] or initial['actor_optimizer']['state']:
        raise AssertionError('Expected entirely fresh learner, no inherited weights or optimizer')
    replay=Replay(arrays['actions'].shape[1],arrays['observations'].shape[1],p['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']));cache=DeviceReplayCache(replay,args.device)
    terminal=np.flatnonzero(arrays['dones'][:,0]==1)
    ordinary=np.flatnonzero(arrays['dones'][:,0]==0)
    sample=np.random.default_rng(p['seed']).choice(ordinary,p['diagnostic_samples'],replace=False)
    scales=p['scale_order'][args.controller]
    if len(scales)!=2 or set(scales)!={1.,.04}:raise ValueError('Expected original and success-unit reward arms')
    args.output.mkdir(exist_ok=False)

    def diagnose(scale):
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
            reward=torch.as_tensor(arrays['rewards'][terminal,0]*scale,device=args.device)
            mask=torch.as_tensor(arrays['masks'][terminal].T,device=args.device).bool()
            error=abs(tq-reward);alpha=float(learner.learner.alpha)
            bound=float(soft_upper_bound(alpha,learner.learner.gamma,1375,
                learner.spaces.action_space.low,learner.spaces.action_space.high,
                terminal_cap=30.*scale,shaping_weight=5.*scale))
            return dict(replay_q_mean=float(q.mean()),replay_q_mean_original_reward_units=float(q.mean())/scale,
                in_bag_terminal_mae=float(error[mask].mean()),
                in_bag_terminal_mae_original_reward_units=float(error[mask].mean())/scale,
                alpha=alpha,alpha_original_reward_units=alpha/scale,
                global_soft_bound=bound,global_soft_bound_original_reward_units=bound/scale,
                above_global_bound_fraction=float((q>bound+.01*scale).float().mean()),
                sampled_policy_entropy=float(-log_pi.mean()),uncertainty_mean=float(uncertainty.mean()),
                implied_minimum_rl_authority_fraction=float((uncertainty>=.2).float().mean()))

    results=[];initial_reference=None
    for scale in scales:
        learner.load_state_dict(copy.deepcopy(initial))
        for param in learner.learner.agent.parameters():param.grad=None
        restored=digest(learner.state_dict())
        if initial_reference is None:initial_reference=restored
        elif restored!=initial_reference:raise AssertionError('Arms have unequal fresh full states')
        replay.rng=np.random.default_rng(p['seed'])
        entry=dict(scale=scale,initial_full_state_sha256=restored,initial=diagnose(scale),curve=[])
        start=time.time()
        for update in range(p['updates_per_arm']):
            metrics=learner.update(scaled_batch(cache.sample(p['batch_size']),scale))
            if (update+1)%p['record_every']==0:
                row=dict(updates=update+1,metrics=metrics,diagnostic=diagnose(scale),updated_unix=time.time())
                entry['curve'].append(row);write(args.output/'PROGRESS.json',dict(scale=scale,**row))
        if learner.learner.num_gradient_steps!=p['updates_per_arm']:raise AssertionError('Update budget mismatch')
        if digest(state)!=parent_digest or digest(ck['replay'])!=replay_digest:
            raise AssertionError('Immutable parent or original replay changed')
        # Cache sampling/scaling must not mutate the authoritative CPU replay.
        retained=replay.state_dict();retained['rng']=copy.deepcopy(ck['replay']['rng'])
        if digest(retained)!=replay_digest:raise AssertionError('Reward study modified stored replay')
        entry.update(final=diagnose(scale),elapsed_s=time.time()-start,
            sampling_rng_sha256=digest(replay.rng.bit_generator.state),parent_unchanged=True)
        results.append(entry);write(args.output/f'scale_{scale:g}.json',entry)
    if results[0]['sampling_rng_sha256']!=results[1]['sampling_rng_sha256']:
        raise AssertionError('Unequal replay sampling streams')
    write(args.output/'FINISHED.json',dict(controller=args.controller,results=results,
        checkpoint_sha256=item['sha256'],registration_sha256=sha(args.registration),
        updates=2*p['updates_per_arm'],new_physics=0,auxiliary_weights_saved=False,formal_training_changed=False,
        fresh_entire_learner=True,parent_unchanged=True,finished_unix=time.time(),
        limitations=['Frozen historical behavior/context and no online collection; not policy-quality evidence.',
            'Same initial alpha in both arms; reward scaling changes initial relative entropy pressure.',
            'Normalize Q/error/alpha by reward scale before interpretation; lower raw loss is not a remedy.',
            'One fresh seed per interface and finite update budget; no convergence or online transfer claim.',
            'CHEQ absolute uncertainty thresholds remain unchanged; implied mixing is only a frozen-data diagnostic.']))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True);parser.add_argument('--controller',required=True)
    parser.add_argument('--device',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:main(args)
    except BaseException as error:
        args.output.mkdir(exist_ok=True);write(args.output/'FAILURE.json',dict(error=repr(error)));raise
