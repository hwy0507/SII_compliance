"""Finite registered 32768/65536 update comparison from complete SERL11.

Equal outer-update budgets, unequal sampled-row budgets; no new physics,
checkpoint output or promotion. Both arms restore the full formal state.
"""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import sys
import time


def sha(p):
    with Path(p).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(p, value):
    temporary=p.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    temporary.replace(p)


def main(args):
    os.sched_setaffinity(0,{54})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg=json.loads(args.registration.read_text())
    assert reg['batches']==[32768,65536] and reg['outer_updates_per_arm']==2000 and reg['record_every']==100
    assert reg['auxiliary_weights_promoted'] is False
    for ref in [reg['checkpoint'],reg['cycle_review'],reg['health_review']]:assert sha(ref['path'])==ref['sha256']
    for name,h in reg['source_hashes'].items():assert sha(Path(__file__).with_name(name))==h
    sys.path.insert(0,reg['adapter_runtime'])
    for name,h in reg['adapter_hashes'].items():assert sha(Path(reg['adapter_runtime'])/name)==h
    sys.path.insert(0,reg['base_adapter_runtime'])
    from train_serl_state_20261026 import Replay
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner,replay_class
    from serl_multistep_replay_gather_20261026 import optimized_class
    from serl_multistep_batch_transfer_20261026 import transfer_class
    from validate_serl_state_20261026 import digest
    ck=torch.load(reg['checkpoint']['path'],map_location='cpu',weights_only=False)
    assert ck['cycle']==11 and ck['boundary']=='complete_condition_cycle'
    assert json.loads(Path(reg['cycle_review']['path']).read_text())['passed']
    assert json.loads(Path(reg['health_review']['path']).read_text())['network_optimizer_rng_unchanged']
    parent_digest=digest(ck['learner']);replay_digest=digest(ck['replay']);arrays=ck['replay']['arrays'];extra=ck['replay']['multistep_target_extension']
    assert not extra['pending']
    terminal=np.flatnonzero(arrays['dones'][:,0]);assert len(terminal)==360
    ids=np.random.default_rng(reg['seed']).choice(ck['replay']['size'],4096,replace=False)
    def select(rows):
        result={k:v[rows] for k,v in arrays.items()}
        result.update(rewards=extra['target_rewards'][rows,None],next_observations=arrays['next_observations'][extra['target_endpoints'][rows]],_bootstrap=extra['target_bootstrap'][rows])
        return result
    cls=transfer_class(SerlMultistepLearner);results=[]
    for batch_size in reg['batches']:
        a=cls(Path(reg['runtime']),upstream=Path(reg['upstream']),upstream_manifest=Path(reg['upstream_manifest']),dimension=7,direct=True,seed=20261026,device='cuda:0')
        a.load_state_dict(copy.deepcopy(ck['learner']))
        replay=optimized_class(replay_class(Replay))(7,49,reg['seed'])
        replay.load_state_dict(copy.deepcopy(ck['replay']))
        assert digest(a.state_dict())==parent_digest and digest(replay.state_dict())==replay_digest
        initial_rng=digest(replay.rng.bit_generator.state)
        def diagnose():
            before=digest(a.state_dict());jax=a.jax;t=a.batch(select(terminal));tb=a.batch(select(ids));key,actionkey=jax.random.split(jax.random.PRNGKey(262))
            tq=np.asarray(a.agent.forward_critic(t['observations'],t['actions'],rng=jax.random.PRNGKey(261)))
            error=np.abs(tq-np.asarray(t['rewards'])[None])
            pred=a.agent.forward_critic(tb['observations'],tb['actions'],rng=key)
            acts,_=a.agent._compute_next_actions(tb,actionkey);targetq=a.agent.forward_target_critic(tb['next_observations'],acts,rng=key)
            _,pairkey=jax.random.split(key);pair=jax.random.randint(pairkey,(2,),0,10)
            target=tb['rewards']+.9995*tb['masks']*targetq[pair].min(axis=0)
            td=np.abs(np.asarray(pred-target[None]))
            assert digest(a.state_dict())==before
            return dict(terminal_mae=float(error.mean()),terminal_max=float(error.max()),q_mean=float(np.asarray(pred).mean()),multistep_td_mae=float(td.mean()),temperature=float(a.agent.forward_temperature()))
        initial=diagnose();points=[];durations=[];losses=[]
        for step in range(1,reg['outer_updates_per_arm']+1):
            start=time.perf_counter();metrics=a.update(replay.sample(batch_size));durations.append(time.perf_counter()-start);losses.append(float(metrics['serl/critic/critic_loss']))
            if step%reg['record_every']==0:
                point=dict(outer_updates=step,critic_updates=step*8,**diagnose(),last100_critic_loss=float(np.mean(losses[-100:])),last100_outer_seconds=float(np.mean(durations[-100:])))
                points.append(point);write(args.output/f'batch{batch_size}_PROGRESS.json',dict(initial=initial,points=points));print(batch_size,step,point['terminal_mae'],flush=True)
        final=a.state_dict()
        assert final['num_gradient_steps']-ck['learner']['num_gradient_steps']==16000
        assert digest(ck['learner'])==parent_digest and digest(ck['replay'])==replay_digest
        result=dict(batch_size=batch_size,initial=initial,initial_learner_digest=parent_digest,initial_replay_digest=replay_digest,initial_sample_rng_digest=initial_rng,final_sample_rng_digest=digest(replay.rng.bit_generator.state),sampled_rows=batch_size*2000,points=points,outer_updates=2000,critic_updates=16000,actor_updates=2000,first_outer_seconds=durations[0],mean_outer_seconds_excluding_first=float(np.mean(durations[1:])),weights_saved=False)
        results.append(result);write(args.output/f'batch{batch_size}_RESULT.json',result)
        del a,replay
    assert results[0]['initial']==results[1]['initial']
    assert results[0]['initial_sample_rng_digest']==results[1]['initial_sample_rng_digest']
    assert sha(reg['checkpoint']['path'])==reg['checkpoint']['sha256']
    write(args.output/'REVIEW.json',dict(passed=True,checkpoint=reg['checkpoint'],results=results,total_critic_updates=32000,total_actor_updates=4000,new_physics=0,weights_saved=False,formal_state_unchanged=True,limitation='Fixed historical replay; equal optimizer clocks but doubled sampled-row budget for65536. Concurrent formal12 shares GPU0, timings are not isolated or pure-formal utilization. No task-improvement or convergence claim.'))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
