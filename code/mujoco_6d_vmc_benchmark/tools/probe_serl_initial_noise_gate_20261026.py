"""Paired short-prefix exploration test from a frozen formal SERL checkpoint.

128 predetermined external action seeds, independent versus constant base noise;
6 actions/.24s each, original model/physics/task gates. These are truncated
physical diagnostics, not task evaluations or transitions for formal replay.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import selectors
import subprocess
import sys
import time


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def write(path,data):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def main(args):
    os.sched_setaffinity(0,{52})
    import numpy as np
    import torch
    torch.set_num_threads(1)
    reg=json.loads(args.registration.read_text());out=args.output
    assert reg['pairs']==128 and reg['prefix_seconds']==.24 and reg['actions_per_trial']==6
    assert reg['optimizer_updates']==0 and reg['maximum_physical_substeps']==1228800
    assert reg['action_seed_start']==2026102616 and reg['physics_cpus']==[53,54]
    for name in ['checkpoint','training_registration','cycle_review','health_review']:
        assert sha(reg[name]['path'])==reg[name]['sha256']
    for ref in reg['source_hashes'].values():assert sha(ref['path'])==ref['sha256']
    protocol=json.loads(Path(reg['training_registration']['path']).read_text())
    root=Path(protocol['runtime']);adapter=Path(reg['adapter_runtime'])
    for name,h in json.loads((root/'SOURCE_HASHES.json').read_text()).items():assert sha(root/'source'/name)==h
    for name,h in {**protocol['multistep_stage']['source_hashes'],**protocol['gather_stage']['source_hashes']}.items():assert sha(adapter/name)==h
    for name,h in protocol['source_adapter_hashes'].items():assert sha(Path(protocol['source_adapter'])/name)==h
    assert sha(protocol['reference_plan'])==protocol['reference_plan_sha256']
    sys.path[:0]=[str(adapter),str(root/'source/tools'),str(Path(__file__).parent)]
    from serl_multistep_state_adapter_20261026 import SerlMultistepLearner
    from validate_serl_state_20261026 import digest
    from evaluate_serl_seeded_multistep_20261026 import seeded_action,case_action_seed
    ck=torch.load(reg['checkpoint']['path'],map_location='cpu',weights_only=False)
    assert ck['cycle']==13 and ck['boundary']=='complete_condition_cycle' and ck['protocol_sha256']==reg['training_registration']['sha256']
    assert json.loads(Path(reg['cycle_review']['path']).read_text())['methods']['direct']['checkpoint_sha256']==reg['checkpoint']['sha256']
    assert json.loads(Path(reg['health_review']['path']).read_text())['network_optimizer_rng_unchanged']
    learner=SerlMultistepLearner(root,upstream=Path(reg['upstream']),upstream_manifest=Path(reg['upstream_manifest']),dimension=7,direct=True,seed=ck['seed'],device='cuda:0')
    learner.load_state_dict(ck['learner']);initial=digest(learner.state_dict());assert initial==digest(ck['learner'])
    condition=next(c for c in protocol['conditions'] if c['id']==reg['case_id'])
    assert sha(condition['path'])==condition['sha256']
    seeds=[case_action_seed(reg['action_seed_start']+i,condition['id']) for i in range(128)];assert len(set(seeds))==128
    rows=[];paired=[]
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1',MUJOCO_GL='disable')
    for index,seed in enumerate(seeds):
        sel=selectors.DefaultSelector();active={};pair=[]
        for mode,cpu in zip(['independent','episode_constant'],reg['physics_cpus']):
            folder=out/f'pair_{index:03d}'/mode
            folder.parent.mkdir(exist_ok=True)
            cmd=['taskset','-c',str(cpu),reg['sampler_python'],reg['episode_adapter'],'--runtime',str(root),'--output',str(folder),'--fixture',condition['path'],'--reference-plan',protocol['reference_plan'],'--controller','direct','--ipc','--probe-seconds','.24']
            log=(folder.parent/(mode+'.stderr.log')).open('x')
            child=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,bufsize=1,env=env)
            item=dict(child=child,log=log,folder=folder,mode=mode,key=learner.jax.random.PRNGKey(seed),actions=0,first_action=None,first_observation=None,command=cmd)
            active[child.pid]=item;sel.register(child.stdout,selectors.EVENT_READ,item)
            write(folder.parent/(mode+'_LAUNCH.json'),dict(pid=child.pid,time=time.time(),command=cmd,seed=seed))
        try:
            while active:
                events=sel.select(timeout=300)
                if not events:raise TimeoutError('Original prefix sampler had no event for300s; no automatic repeat')
                for key,_ in events:
                    item=key.data;child=item['child'];line=child.stdout.readline()
                    if not line:raise RuntimeError('Sampler exited before terminal')
                    event=json.loads(line)
                    if event['kind']=='error':raise RuntimeError(event['error'])
                    if event['kind']=='observation':
                        i=item['actions'];assert i<6
                        if i==0:
                            assert sha(item['folder']/'rollout.mjb')==condition['model_sha256']
                            item['first_observation']=event['observation']
                        action,item['key']=seeded_action(learner,event['observation'],i,item['key'],item['mode'])
                        if i==0:item['first_action']=action.tolist()
                        child.stdin.write(json.dumps(dict(action=action.tolist()))+'\n');child.stdin.flush();item['actions']+=1
                    elif event['kind']=='terminal':
                        assert child.wait(timeout=60)==0 and item['actions']<=6
                        assert event['model_sha256']==condition['model_sha256']
                        assert not event['result']['full_task_horizon_completed']
                        record=dict(pair=index,seed=seed,mode=item['mode'],folder=str(item['folder']),actions=item['actions'],first_action=item['first_action'],first_observation=item['first_observation'],terminal=event,left_initial_approach=event['result']['final_task_stage']!='approach')
                        pair.append(record);rows.append(record);sel.unregister(child.stdout);child.stdin.close();child.stdout.close();item['log'].close();del active[child.pid]
                    else:raise ValueError('Unexpected event')
            assert len(pair)==2
            np.testing.assert_array_equal(pair[0]['first_action'],pair[1]['first_action'])
            np.testing.assert_array_equal(pair[0]['first_observation'],pair[1]['first_observation'])
            paired.append(dict(index=index,seed=seed,first_action_equal=True,first_observation_equal=True))
            write(out/'PROGRESS.json',dict(completed_pairs=len(paired),episodes=rows))
            print('pairs',len(paired),'left_initial',{m:sum(r['left_initial_approach'] for r in rows if r['mode']==m) for m in ['independent','episode_constant']},flush=True)
        finally:
            # Only clean up this evaluator's still-live diagnostic children on
            # an error; formal trainers are separate sessions and untouched.
            for item in active.values():
                child=item['child'];child.stdin.close()
                try:child.wait(timeout=20)
                except subprocess.TimeoutExpired:child.terminate();child.wait(timeout=20)
                item['log'].close()
            sel.close()
    assert digest(learner.state_dict())==initial and sha(reg['checkpoint']['path'])==reg['checkpoint']['sha256']
    assert len(rows)==256 and sum(r['actions'] for r in rows)<=1536
    write(out/'REVIEW.json',dict(passed=True,time=time.time(),checkpoint=reg['checkpoint'],episodes=rows,paired=paired,completed_pairs=128,full_learner_optimizer_rng_unchanged=True,initial_state_digest=initial,final_state_digest=digest(learner.state_dict()),optimizer_updates=0,replay_writes=0,weights_saved=False,maximum_physical_substeps=1228800,limitation='Truncated .24s prefix only, one original condition and128 predeclared paired action seeds. Leaving initial approach is not task success. No full-episode extension, seed selection, formal replay injection, demonstrations, nominal mixing, or deployed policy change. Physical/filter/torque and action replay review remains separate.',convergence_claim=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--registration',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    try:main(a)
    except BaseException as e:
        write(a.output/'FAILURE.json',dict(time=time.time(),error=repr(e)));raise
