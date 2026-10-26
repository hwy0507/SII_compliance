from pathlib import Path
import os,sys,json,time,hashlib,collections
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=Path(__file__).parent
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
from spt_rl_reward_20261025 import SPTReward
from training_comparison_metrics_20261025 import completion_bonus
def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def lines(p):
    with p.open() as f:
        for line in f:
            if line.endswith('\n'):yield json.loads(line)
def finite(x):
    if isinstance(x,dict):return all(finite(v) for v in x.values())
    if isinstance(x,(list,tuple)):return all(finite(v) for v in x)
    if torch.is_tensor(x):return bool(torch.isfinite(x).all())
    if isinstance(x,(float,np.ndarray)):return bool(np.isfinite(x).all())
    return True
methods={}
for m in ['direct']:
    run=B/'runs/serl_multistep_batch65536_cycle17_20261026_v1/direct'
    cp=B/'runs/serl_multistep_batch65536_cycle17_archive_20261026_v1'/m/'cycle_00017.pt'
    deadline=time.monotonic()+7200
    while not cp.exists():
        if time.monotonic()>deadline or (run/'FAILURE.json').exists():raise RuntimeError('Cycle17 archive unavailable: '+m)
        time.sleep(2)
    x=torch.load(cp,map_location='cpu',weights_only=False)
    execution=read(run/'EXECUTION.json');parent=Path(execution['resumed_from'])
    assert sha(parent)==execution['resumed_checkpoint_sha256']
    stage_parent=parent
    old=torch.load(parent,map_location='cpu',weights_only=False)
    assert x['cycle']==17 and x['boundary']=='complete_condition_cycle'
    assert x['cycles'][:-1]==old['cycles'] and x['cycles'][-1]['cycle']==17
    assert finite(x['learner']) and x['learner']['config']==old['learner']['config']
    assert x['learner']['critic_clock_extension']==old['learner']['critic_clock_extension']
    assert x['learner']['critic_actor_ratio']==8 and x['learner']['config']['critic_ensemble_size']==10
    reg=read(run.parent/'REGISTRATION.json');conditions={r['id']:r for r in reg['conditions']}
    assert x['protocol_sha256']==sha(run.parent/'REGISTRATION.json')
    n=old['replay']['size'];arr=x['replay']['arrays']
    for k,v in old['replay']['arrays'].items():assert np.array_equal(v,arr[k][:n])
    transitions=[t for t in lines(run/'transitions.jsonl') if t['cycle']==17]
    assert len(transitions)==x['steps']-old['steps']
    assert [t['step'] for t in transitions]==list(range(old['steps']+1,x['steps']+1))
    assert x['learner']['num_gradient_steps']-old['learner']['num_gradient_steps']==8*len(transitions)
    np.testing.assert_array_equal(arr['rewards'][n:,0],np.array([t['reward'] for t in transitions],np.float32))
    np.testing.assert_array_equal(arr['dones'][n:,0],np.array([t['done'] for t in transitions],np.float32))
    by_case=collections.defaultdict(list)
    for t in transitions:by_case[t['condition']].append(t)
    episodes=[e for e in lines(run/'episodes.jsonl') if e['cycle']==17]
    assert len(conditions)==30 and len(episodes)==30 and {e['condition'] for e in episodes}==set(conditions)
    max_reward_error=0.
    for e in episodes:
        folder=Path(e['episode_path']);terminal=read(folder/'TERMINAL.json')
        assert sha(folder/'rollout.mjb')==conditions[e['condition']]['model_sha256']==terminal['model_sha256']
        assert sha(conditions[e['condition']]['path'])==conditions[e['condition']]['sha256']
        for key in ['task_success','strict_success','abort_reason','full_task_horizon_completed']:
            assert e[key]==terminal['result'][key]
        ts=by_case[e['condition']];journal=list(lines(folder/'actor_intervals.jsonl'))
        assert len(journal)==len(ts)==e['steps'] and sum(t['done'] for t in ts)==1 and ts[-1]['done']
        reward=SPTReward()
        for i,(t,j) in enumerate(zip(ts,journal)):
            nxt=terminal if t['done'] else journal[i+1]
            value,terms=reward(current_potential=j['payload_potential'],next_potential=nxt['payload_potential'],
                interval=nxt['interval'],terminated=t['done'],task_success=e['task_success'] if t['done'] else False,
                strict_success=e['strict_success'] if t['done'] else False)
            if t['done'] and e['strict_success']:
                value+=completion_bonus(task_success=True,strict_success=True,completion_time_s=e['completion_time_s'])
            error=abs(value-t['reward']);max_reward_error=max(max_reward_error,error);assert error<1e-10
            index=t['step']-1
            scale=x['learner']['observation_scale']
            observed=np.asarray(j['observation'],np.float32)/scale
            np.testing.assert_array_equal(arr['observations'][index,:48],observed)
            expected=arr['actions'][index].copy();expected[0]=np.float32(.5)*(expected[0]+np.float32(1.))
            np.testing.assert_array_equal(expected,np.asarray(j['action'],np.float32))
            np.testing.assert_array_equal(expected,np.asarray(j['executed_action'],np.float32))
            expected_next=observed if t['done'] else np.asarray(nxt['observation'],np.float32)/scale
            np.testing.assert_array_equal(arr['next_observations'][index,:48],expected_next)
            assert arr['observations'][index,48]==np.float32((1375-i)/1375)
            assert arr['next_observations'][index,48]==np.float32((1374-i)/1375)

        assert abs(sum(t['reward'] for t in ts)-e['reward'])<1e-8
    assert sha(reg['reference_plan'])==reg['reference_plan_sha256']
    sys.path.insert(0,str(B/'runtime/serl_multistep_batch65536_cycle17_20261026_v1'))
    from audit_serl_multistep_replay_20261026 import audit
    multistep=audit(x,old,transitions)
    assert multistep['new_pending_rows']==0
    result=dict(multistep_replay=multistep,steps=x['steps'],updates=x['learner']['num_gradient_steps'],checkpoint_sha256=sha(cp),
        new_transitions=len(transitions),retained_replay_rows=n,retained_replay_all_fields_exact=True,
        conditions=30,task=sum(e['task_success'] for e in episodes),strict=sum(e['strict_success'] for e in episodes),
        reward_mean=float(np.mean([e['reward'] for e in episodes])),
        full_horizon_count=sum(e['full_task_horizon_completed'] for e in episodes),
        aborts=[e for e in episodes if e['abort_reason']],max_reward_reconstruction_error=max_reward_error,
        reward_audit_scope='Reconstructed every new reward from physical interval journal with frozen reward implementation; not independent raw-substep physics reconstruction',
        source_parent_sha256=sha(parent),stage_resumed_parent_sha256=sha(stage_parent),optimizer_and_network_finite=True,convergence_claim=False)
    methods[m]=result;(OUT/(m+'_REVIEW.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(m,json.dumps(result),flush=True)
    del x,old,arr,transitions,journal,by_case
(OUT/'REVIEW.json').write_text(json.dumps(dict(time=time.time(),methods=methods,new_physics=0,optimizer_updates=0,passed=True),indent=2)+'\n')
