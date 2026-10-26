from pathlib import Path
import os,json,hashlib,time,shutil
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).parent
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def finite(v):
    if isinstance(v,dict):return all(finite(x) for x in v.values())
    if isinstance(v,(list,tuple)):return all(finite(x) for x in v)
    if torch.is_tensor(v):return bool(torch.isfinite(v).all())
    if isinstance(v,(np.ndarray,float)):return bool(np.isfinite(v).all())
    return True
report=dict(time=time.time(),new_physics=0,optimizer_updates=0,methods={})
for m in ['direct']:
    run=(B/'runs/serl_pool30_cycle05_06_20261026_v2/direct' if m=='direct'
         else B/'runs/clock_parameter_reviewed_cycle06_07_20261026_v1'/m/'train')
    execution=json.loads((run/'EXECUTION.json').read_text())
    parent=Path(execution['resumed_from'])
    assert sha(parent)==execution['resumed_checkpoint_sha256']
    saved=OUT/(m+'.pt')
    with (run/'checkpoint_latest.pt').open('rb') as src,saved.open('xb') as dst:shutil.copyfileobj(src,dst)
    x=torch.load(saved,map_location='cpu',weights_only=False)
    old=torch.load(parent,map_location='cpu',weights_only=False)
    n=old['replay']['size']
    assert x['steps']>old['steps'] and x['replay']['size']==x['steps']
    for k,v in old['replay']['arrays'].items():assert np.array_equal(v,x['replay']['arrays'][k][:n])
    ratio=8 if m=='direct' else 1
    assert x['learner']['num_gradient_steps']-old['learner']['num_gradient_steps']==ratio*(x['steps']-old['steps'])
    assert finite(x['learner']) and execution['batch_size']==32768
    if m=='direct':
        assert x['learner']['config']==old['learner']['config']
        assert x['learner']['critic_actor_ratio']==8
        assert x['cycles']==old['cycles']
        assert x['learner']['source_receipt']==old['learner']['source_receipt']
    else:
        assert x['learner']['critic_clock']
        assert x['learner'].get('bellman_target_count',2)==(5 if m=='vmc' else 2)
        assert x['learner']['actor_optimizer']['param_groups'][0]['lr']==old['learner']['actor_optimizer']['param_groups'][0]['lr']
        assert abs(x['learner']['actor_optimizer']['param_groups'][0]['lr']-(3e-5 if m=='admittance' else 3e-4))<1e-12
    reg=json.loads((run.parent/'REGISTRATION.json').read_text())
    assert sha(run.parent/'REGISTRATION.json')==x['protocol_sha256']==execution['protocol_sha256']
    conditions={c['id']:c for c in reg['conditions']}
    models=0
    for f in run.glob('cycle_*/*/rollout.mjb'):
        assert sha(f)==conditions[f.parent.name]['model_sha256'];models+=1
    report['methods'][m]=dict(steps=x['steps'],updates=x['learner']['num_gradient_steps'],
        retained_replay_rows=n,retained_replay_all_fields_exact=True,added_steps=x['steps']-old['steps'],
        exact_registered_update_increment=True,finite_network_optimizer=True,model_count=models,
        expected_actor_learning_rate=(None if m=='direct' else (3e-5 if m=='admittance' else 3e-4)),
        target_count=(5 if m=='vmc' else 2),checkpoint_sha256=sha(saved),parent_sha256=sha(parent))
    del x,old
import collections
import sys
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
from spt_rl_reward_20261025 import SPTReward
run=B/'runs/serl_pool30_cycle05_06_20261026_v2/direct'
x=torch.load(OUT/'direct.pt',map_location='cpu',weights_only=False)
arr=x['replay']['arrays'];n=report['methods']['direct']['retained_replay_rows']
def lines(path):
    with path.open() as f:
        for line in f:
            if line.endswith('\n'):yield json.loads(line)
transitions=[t for t in lines(run/'transitions.jsonl') if t['step']<=x['steps']]
assert len(transitions)==x['steps']-n
by_case=collections.defaultdict(list)
for t in transitions:by_case[t['condition']].append(t)
error=0.;checked=0
for name,ts in by_case.items():
    journal=list(lines(run/'cycle_00005'/name/'actor_intervals.jsonl'))
    reward=SPTReward()
    for i,t in enumerate(ts):
        assert not t['done']
        j,nxt=journal[i],journal[i+1]
        value,_=reward(current_potential=j['payload_potential'],next_potential=nxt['payload_potential'],interval=nxt['interval'],terminated=False,task_success=False,strict_success=False)
        error=max(error,abs(value-t['reward']));assert error<1e-10
        k=t['step']-1;scale=x['learner']['observation_scale']
        np.testing.assert_array_equal(arr['observations'][k],np.asarray(j['observation'],np.float32)/scale)
        a=arr['actions'][k].copy();a[0]=np.float32(.5)*(a[0]+np.float32(1.))
        np.testing.assert_array_equal(a,np.asarray(j['action'],np.float32))
        np.testing.assert_array_equal(a,np.asarray(j['executed_action'],np.float32))
        np.testing.assert_array_equal(arr['next_observations'][k],np.asarray(nxt['observation'],np.float32)/scale)
        assert arr['rewards'][k,0]==np.float32(t['reward']) and arr['dones'][k,0]==0
        checked+=1
launch=json.loads((run.parent/'LAUNCH.json').read_text());pid=launch['pid']
children=[int(v) for v in Path(f'/proc/{pid}/task/{pid}/children').read_text().split()]
assert len(children)==30 and os.sched_getaffinity(pid)=={0}
assert all(os.sched_getaffinity(p)==set(range(1,13)) for p in children)
assert report['methods']['direct']['model_count']==30
report.update(actual_sampler_count=30,learner_cpu=[0],sampler_cpus=list(range(1,13)),new_transition_mappings_checked=checked,max_reward_reconstruction_error=error,terminal_coverage=False)
report['passed']=True
(OUT/'REVIEW.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2),flush=True)
