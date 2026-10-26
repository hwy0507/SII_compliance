"""Audit necessary upper bounds on frozen-policy finite-horizon soft values.

Potential shaping telescopes to -w*phi(initial); other running terms are <=0.
Terminal reward plus efficiency is <=30. Differential entropy is <=log(action
volume). This bounds the value of a fixed policy at the checkpoint's fixed
alpha; it is not a proof about a future nonstationary alpha schedule.
No clipping, learner updates, actor information changes or physics are applied.
"""
import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import sys
import time

import numpy as np
import torch


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def soft_upper_bound(alpha, gamma, remaining_steps, action_low, action_high,
                     potential=0., terminal_cap=30., shaping_weight=5.):
    n=np.asarray(remaining_steps,dtype=float)
    low,high=np.asarray(action_low,dtype=float),np.asarray(action_high,dtype=float)
    phi=np.asarray(potential,dtype=float)
    if (low.ndim!=1 or high.shape!=low.shape or np.any(high<=low)
            or not np.isfinite(low).all() or not np.isfinite(high).all()
            or not np.isfinite(n).all() or np.any(n<1) or np.any(n!=np.floor(n))
            or not np.isfinite(phi).all() or np.any(phi<0) or np.any(phi>1)
            or not np.isfinite(alpha) or alpha<0 or not 0<=gamma<=1):
        raise ValueError('Invalid finite-horizon bound inputs')
    log_volume=np.log(high-low).sum()
    if log_volume<0:
        raise ValueError('This relaxed upper bound assumes nonnegative maximum entropy')
    entropy_sum=n-1 if gamma==1 else gamma*(1-gamma**(n-1))/(1-gamma)
    return terminal_cap-shaping_weight*phi+alpha*log_volume*entropy_sum


def stats(values):
    x=np.asarray(values,dtype=float)
    if not x.size or not np.isfinite(x).all():raise ValueError('Invalid diagnostic')
    return dict(mean=float(x.mean()),minimum=float(x.min()),maximum=float(x.max()),p95=float(np.percentile(x,95)))


def audit_episode(rows,gamma,weight):
    costs=('occupancy','time','comfort_torque','contact_force','torque_slew','penetration','peak_torque','failure_tail')
    for i,row in enumerate(rows):
        terms=row['reward_terms']
        if any(terms[k]>1e-10 for k in costs):raise AssertionError('Positive running cost')
        phi,nxt=terms['current_potential'],terms['next_potential']
        if not 0<=phi<=1 or not 0<=nxt<=1:raise AssertionError('Invalid potential')
        if row['done']!=(i==len(rows)-1):raise AssertionError('Incomplete episode')
        if i and abs(phi-rows[i-1]['reward_terms']['next_potential'])>1e-10:
            raise AssertionError('Potential discontinuity')
        expected=weight*(gamma*(0 if row['done'] else nxt)-phi)
        if abs(terms['progress']-expected)>1e-9:raise AssertionError('Shaping mismatch')
        if not row['done'] and (terms['terminal'] or terms['completion_efficiency']):
            raise AssertionError('Nonterminal positive bonus')
        if not -25<=terms['terminal']<=25 or not 0<=terms['completion_efficiency']<=5:
            raise AssertionError('Terminal cap violation')
        reconstructed=sum(terms[k] for k in costs)+terms['progress']+terms['terminal']+terms['completion_efficiency']
        if abs(reconstructed-row['reward'])>1e-8:raise AssertionError('Reward reconstruction mismatch')
    discount=gamma**np.arange(len(rows))
    telescoping=float(discount @ np.array([r['reward_terms']['progress'] for r in rows]))
    expected=-weight*rows[0]['reward_terms']['current_potential']
    if abs(telescoping-expected)>1e-8:raise AssertionError('Potential failed to telescope')
    actual=float(discount @ np.array([r['reward'] for r in rows]))
    if actual>30+expected+1e-8:raise AssertionError('Discounted reward exceeds bound')
    return dict(steps=len(rows),discounted_return=actual,discounted_shaping=telescoping,
                discounted_reward_upper_bound=30+expected)


def main(args):
    p=json.loads(args.registration.read_text())
    if sha(__file__)!=p['source_sha256']:raise ValueError('Source drift')
    os.sched_setaffinity(0,{p['cpu']});os.nice(10);torch.set_num_threads(1)
    root=Path(p['runtime'])
    if sha(root/'RUNTIME.json')!=p['runtime_sha256']:raise ValueError('Runtime drift')
    hashes=json.loads((root/'SOURCE_HASHES.json').read_text())
    for name in ['published_compliance_learner_20261025.py','spt_rl_reward_20261025.py','training_comparison_metrics_20261025.py']:
        if sha(root/'source/tools'/name)!=hashes['tools/'+name]:raise ValueError('Protected source drift')
    sys.path.insert(0,str(root/'source/tools'))
    from published_compliance_learner_20261025 import PublishedLearner
    from spt_rl_reward_20261025 import CONFIG
    if (CONFIG['gamma'],CONFIG['progress_weight'],CONFIG['success_bonus'],CONFIG['horizon_s'],CONFIG['control_dt_s'])!=(.9995,5.,25.,55.,.04):
        raise ValueError('Bound proof requires the audited reward contract')
    out=Path(p['output']);out.mkdir(parents=True,exist_ok=False)
    result=dict(started_unix=time.time(),optimizer_updates=0,new_physical_transitions=0,
                formal_state_changed=False,methods={})
    for item in p['checkpoints']:
        if sha(item['path'])!=item['sha256'] or sha(item['transitions'])!=item['transitions_sha256']:
            raise ValueError('Frozen checkpoint/transition evidence drift')
        ck=torch.load(item['path'],map_location='cpu',weights_only=False)
        if ck['boundary']!='complete_condition_cycle' or ck['controller']!=item['method'] or ck['cycle']!=item['cycle']:
            raise ValueError('Checkpoint identity mismatch')
        arrays=ck['replay']['arrays'];state=ck['learner']
        if ck['replay']['size']!=ck['steps'] or ck['replay']['cursor']!=ck['steps']:
            raise ValueError('Only an unwrapped complete replay is supported')
        groups=defaultdict(list)
        for line in Path(item['transitions']).read_text().splitlines():
            row=json.loads(line)
            if row['cycle']==item['cycle']:groups[row['condition']].append(row)
        if len(groups)!=30:raise ValueError('Expected complete registered30-condition cycle')
        rows=[];audits={};remaining=[];potentials=[]
        for condition,group in groups.items():
            audits[condition]=audit_episode(group,CONFIG['gamma'],CONFIG['progress_weight'])
            rows.extend(group);remaining.extend(1375-n for n in range(len(group)))
            potentials.extend(r['reward_terms']['current_potential'] for r in group)
        indices=np.array([r['step']-1 for r in rows])
        np.testing.assert_array_equal(arrays['rewards'][indices,0],np.array([r['reward'] for r in rows],dtype=np.float32))
        np.testing.assert_array_equal(arrays['dones'][indices,0],np.array([r['done'] for r in rows],dtype=np.float32))
        selection=np.random.default_rng(p['seed']).choice(len(rows),min(p['sample_size'],len(rows)),replace=False)
        indices=indices[selection]
        learner=PublishedLearner(root,dimension=arrays['actions'].shape[1],direct=item['method']=='direct',seed=p['seed'],
            device='cpu',algorithm=state['algorithm'],critic_layer_norm=state['critic_layer_norm'],numerical_amendments=state['numerical_amendments'])
        agent=learner.learner.agent;agent.load_state_dict(state['agent']);alpha=float(state['alpha']);gamma=learner.learner.gamma
        low,high=learner.spaces.action_space.low,learner.spaces.action_space.high
        global_bound=float(soft_upper_bound(alpha,gamma,1375,low,high))
        clock_bound=soft_upper_bound(alpha,gamma,np.array(remaining)[selection],low,high,np.array(potentials)[selection])
        row=dict(cycle=ck['cycle'],steps=ck['steps'],alpha=alpha,gamma=gamma,log_action_volume=float(np.log(high-low).sum()),
            global_bound=global_bound,clock_bound=stats(clock_bound),sample_size=len(indices),audited_episodes=audits,
            sampled_replay_indices_sha256=hashlib.sha256(indices.tobytes()).hexdigest(),critics={})
        with torch.no_grad():
            obs=torch.as_tensor(arrays['observations'][indices]);act=torch.as_tensor(arrays['actions'][indices])
            for target in [False,True]:
                if state['algorithm']=='cheq':q=torch.stack([agent.get_q_value(obs,act,i,target=target).reshape(-1) for i in range(agent.ensemble_size)]).numpy()
                else:
                    nets=[agent.qf1_target,agent.qf2_target] if target else [agent.qf1,agent.qf2]
                    q=torch.stack([net(obs,act).reshape(-1) for net in nets]).numpy()
                row['critics']['target' if target else 'online']=dict(q=stats(q),
                    above_global_bound_fraction=float(np.mean(q>global_bound+.01)),
                    above_clock_bound_fraction=float(np.mean(q>clock_bound+.01)),
                    all_critics_above_global_fraction=float(np.mean((q>global_bound+.01).all(axis=0))),
                    all_critics_above_clock_fraction=float(np.mean((q>clock_bound+.01).all(axis=0))),
                    positive_global_excess=stats(np.maximum(0,q-global_bound)),
                    positive_clock_excess=stats(np.maximum(0,q-clock_bound)))
        if any(v.grad is not None for v in agent.parameters()) or learner.learner.num_gradient_steps!=0:raise AssertionError('Unexpected learning')
        if not all(torch.equal(v, state['agent'][k]) for k,v in agent.state_dict().items()):raise AssertionError('Network changed')
        row['network_state_unchanged']=True;result['methods'][item['method']]=row
        (out/(item['method']+'.json')).write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')
        print(json.dumps(dict(method=item['method'],global_bound=global_bound,online=row['critics']['online'])),flush=True)
        del ck,state,arrays,learner,agent
    result.update(finished_unix=time.time(),registration_sha256=sha(args.registration),limitations=[
        'Bounds apply to the frozen checkpoint policy and alpha, not a changing future temperature schedule.',
        'Global bound does not need time as an actor or critic input. Clock threshold is only contextual: a critic averaging over hidden time may legitimately exceed an individual hidden-time bound.',
        'A .01 excess tolerance covers reward float32 rounding; bounded absolute one-step reward is below64 for this contract.',
        'Exceeding a necessary value bound shows calibration failure, not an identified implementation bug or successful repair.',
        'Being below the bound does not prove calibrated values or convergence.',
        'No value clipping, reward change, actor information change, optimizer update or physics.'])
    (out/'SUMMARY.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--registration',type=Path,required=True)
    main(parser.parse_args())
