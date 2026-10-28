"""Finite interventions isolating actor/temperature feedback in critic updates.

Three arms restore identical complete-cycle state: ordinary full updates,
actor updates with fixed alpha, and frozen actor/alpha with moving critics and
targets. Per-update common random seeds couple next-action draws and critic
pairs across arms. This intentionally differs from the formal RNG stream.
All data are frozen; weights are discarded; no online-performance claim.
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

from validate_published_finite_check_20261025 import digest
from diagnose_published_value_bound_20261025 import soft_upper_bound


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def main(args):
    p=json.loads(args.registration.read_text())
    for name,expected in p['source_hashes'].items():
        if sha(Path(__file__).with_name(name))!=expected:raise ValueError('Frozen diagnostic source drift')
    os.sched_setaffinity(0,{p['cpus'][args.controller]});os.nice(10);torch.set_num_threads(1)
    root=Path(p['runtime'])
    if sha(root/'RUNTIME.json')!=p['runtime_sha256']:raise ValueError('Runtime drift')
    if set(p['arm_order'][args.controller])!={'full','actor_fixed_alpha','frozen_actor_fixed_alpha'} or len(p['arm_order'][args.controller])!=3:
        raise ValueError('Expected the three registered interventions')
    source_hashes=json.loads((root/'SOURCE_HASHES.json').read_text())
    for name in ['published_compliance_learner_20261025.py','published_replay_device_cache_20261025.py','train_published_compliance_20261025.py']:
        if sha(root/'source/tools'/name)!=source_hashes['tools/'+name]:raise ValueError('Runtime source drift')
    sys.path.insert(0,str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from train_published_compliance_20261025 import Replay
    from published_replay_device_cache_20261025 import DeviceReplayCache
    item=p['checkpoints'][args.controller]
    if sha(item['path'])!=item['sha256']:raise ValueError('Checkpoint drift')
    ck=torch.load(item['path'],map_location='cpu',weights_only=False)
    if ck['controller']!=args.controller or ck['boundary']!='complete_condition_cycle' or ck['cycle']!=3:
        raise ValueError('Expected registered cycle3 checkpoint')
    state,arrays=ck['learner'],ck['replay']['arrays']
    if state['algorithm']!='cheq' or state['num_gradient_steps']<=0:raise ValueError('Expected trained CHEQ')
    initial_parent=digest(state);initial_replay=digest(ck['replay'])
    learner=PublishedLearner(root,dimension=arrays['actions'].shape[1],direct=args.controller=='direct',seed=p['seed'],
        device=args.device,algorithm='cheq',critic_layer_norm=state['critic_layer_norm'],numerical_amendments=state['numerical_amendments'])
    original_frequency=learner.learner.policy_frequency
    replay=Replay(arrays['actions'].shape[1],arrays['observations'].shape[1],p['seed'])
    replay.load_state_dict(copy.deepcopy(ck['replay']));cache=DeviceReplayCache(replay,args.device)
    terminal=np.flatnonzero(arrays['dones'].reshape(-1)==1)
    ordinary=np.flatnonzero(arrays['dones'].reshape(-1)==0)
    ordinary=ordinary[ordinary>=ck['cycles'][-2]['steps']]
    sample=np.random.default_rng(p['seed']).choice(ordinary,4096,replace=False)
    args.output.mkdir(parents=True,exist_ok=False)

    def diagnose():
        agent=learner.learner.agent
        with torch.no_grad():
            obs=torch.as_tensor(arrays['observations'][terminal],device=args.device)
            act=torch.as_tensor(arrays['actions'][terminal],device=args.device)
            tq=torch.stack([agent.get_q_value(obs,act,i).reshape(-1) for i in range(agent.ensemble_size)])
            reward=torch.as_tensor(arrays['rewards'][terminal,0],device=args.device)
            mask=torch.as_tensor(arrays['masks'][terminal].T,device=args.device).bool()
            error=abs(tq-reward)
            obs=torch.as_tensor(arrays['observations'][sample],device=args.device)
            act=torch.as_tensor(arrays['actions'][sample],device=args.device)
            q=torch.stack([agent.get_q_value(obs,act,i).reshape(-1) for i in range(agent.ensemble_size)])
            alpha=float(learner.learner.alpha)
            bound=float(soft_upper_bound(alpha,learner.learner.gamma,1375,learner.spaces.action_space.low,learner.spaces.action_space.high))
            return dict(in_bag_terminal_mae=float(error[mask].mean()),out_of_bag_terminal_mae=float(error[~mask].mean()),
                latest_cycle_replay_q_mean=float(q.mean()),alpha=alpha,global_soft_bound=bound,
                above_global_bound_fraction=float((q>bound+.01).float().mean()))

    result=dict(controller=args.controller,checkpoint_sha256=item['sha256'],started_unix=time.time(),arms=[])
    reference=None
    for arm in p['arm_order'][args.controller]:
        learner.learner.autotune=True;learner.learner.policy_frequency=original_frequency
        learner.load_state_dict(copy.deepcopy(state))
        for parameter in learner.learner.agent.parameters():parameter.grad=None
        restored=digest(learner.state_dict())
        if reference is None:reference=restored
        elif restored!=reference:raise AssertionError('Unequal full initial learner state')
        replay.rng=np.random.default_rng(p['seed'])
        frozen_actor=arm=='frozen_actor_fixed_alpha';fixed_alpha=arm!='full'
        learner.learner.autotune=not fixed_alpha
        if frozen_actor:
            # All update indices are strictly between0 and this divisor, so
            # the upstream delayed policy branch cannot run even once.
            learner.learner.policy_frequency=state['num_gradient_steps']+p['updates_per_arm']+1
        actor_before=digest(learner.learner.agent.actor.state_dict())
        critic_before=digest({k:v for k,v in learner.learner.agent.state_dict().items() if not k.startswith('actor.')})
        actor_optimizer_before=digest(learner.learner.actor_optimizer.state_dict())
        alpha_before=digest((learner.learner.log_alpha,learner.learner.alpha,learner.learner.a_optimizer.state_dict()))
        initial=diagnose();start=time.time();curve=[]
        for update in range(p['updates_per_arm']):
            batch=cache.sample(p['batch_size'])
            # Same next-policy standard-normal draws and sampled critic pair
            # at each update, despite differing extra actor draws across arms.
            np.random.seed(p['seed']+update)
            with torch.cuda.device(args.device):torch.cuda.manual_seed(p['seed']+update)
            metrics=learner.update(batch)
            if (update+1)%p['record_every']==0:
                metric={k:v for k,v in metrics.items() if 'q_loss' in k or 'next_q_values' in k}
                row=dict(arm=arm,updates=update+1,critic_metrics=metric,diagnostic=diagnose(),updated_unix=time.time())
                curve.append(row);write(args.output/'PROGRESS.json',row)
        final=diagnose()
        if learner.learner.num_gradient_steps-state['num_gradient_steps']!=p['updates_per_arm']:
            raise AssertionError('Unexpected update count')
        actor_same=actor_before==digest(learner.learner.agent.actor.state_dict())
        actor_optimizer_same=actor_optimizer_before==digest(learner.learner.actor_optimizer.state_dict())
        alpha_same=alpha_before==digest((learner.learner.log_alpha,learner.learner.alpha,learner.learner.a_optimizer.state_dict()))
        if critic_before==digest({k:v for k,v in learner.learner.agent.state_dict().items() if not k.startswith('actor.')}):
            raise AssertionError('Critics did not change')
        if frozen_actor and not (actor_same and actor_optimizer_same):raise AssertionError('Frozen actor changed')
        if not frozen_actor and actor_same:raise AssertionError('Expected real actor updates')
        if fixed_alpha and not alpha_same:raise AssertionError('Fixed temperature changed')
        if digest(state)!=initial_parent or digest(ck['replay'])!=initial_replay:
            raise AssertionError('Immutable parent changed')
        entry=dict(arm=arm,initial=initial,final=final,curve=curve,elapsed_s=time.time()-start,
            initial_full_state_sha256=restored,actor_unchanged=actor_same,actor_optimizer_unchanged=actor_optimizer_same,
            alpha_and_optimizer_unchanged=alpha_same,replay_rng_final_sha256=digest(replay.rng.bit_generator.state),
            critic_optimizer_final_sha256=digest(learner.learner.q_optimizer.state_dict()),parent_unchanged=True)
        result['arms'].append(entry);write(args.output/(arm+'.json'),entry)
        print(json.dumps(dict(controller=args.controller,arm=arm,initial=initial,final=final)),flush=True)
    if len({x['replay_rng_final_sha256'] for x in result['arms']})!=1:
        raise AssertionError('Different replay sampling streams')
    result.update(finished_unix=time.time(),registration_sha256=sha(args.registration),
        auxiliary_updates=len(result['arms'])*p['updates_per_arm'],new_physical_transitions=0,
        formal_policy_changed=False,auxiliary_weights_saved=False,convergence_claim=False,
        limitations=['Frozen replay and short interventions; no online policy-quality or convergence conclusion.',
            'Actor-updating versus frozen-actor pair both hold alpha fixed; full arm separately includes alpha adaptation.',
            'Per-update common random reseeding intentionally differs from formal training RNG.',
            'Stored rewards/gamma/masks are unchanged; no value clipping or privileged actor information.'])
    write(args.output/'FINISHED.json',result)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True);parser.add_argument('--controller',required=True)
    parser.add_argument('--device',required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:main(args)
    except BaseException as error:
        args.output.mkdir(parents=True,exist_ok=True);write(args.output/'FAILURE.json',dict(error=repr(error)));raise
