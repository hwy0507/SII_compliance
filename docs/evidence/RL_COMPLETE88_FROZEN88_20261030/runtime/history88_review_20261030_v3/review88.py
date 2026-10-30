from pathlib import Path
import os,sys,json,time,hashlib,collections
os.sched_setaffinity(0,{53})
import numpy as np
import torch
torch.set_num_threads(1)
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
OUT=B/'runs/parameter_history_cycle88_review_20261030_v2'
sys.path.insert(0,str(B/'runtime/source_train17_clock/source/tools'))
sys.path.insert(0,str(B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1'))
from parameter_replay_capacity_20261026 import MARKER as CAPACITY_MARKER
from parameter_replay_capacity4m_20261027 import MARKER as FOLLOWUP_MARKER
from validate_published_finite_check_20261025 import digest
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
for m in ['impedance', 'admittance', 'vmc']:
    run=B/'runs/parameter_history_cycle88_20261030_v2'/m/'train'
    cp=B/'runs/parameter_history_cycle88_archive_20261030_v2'/m/'cycle_00088.pt'
    deadline=time.monotonic()+7200
    while not cp.exists():
        if time.monotonic()>deadline or (run/'FAILURE.json').exists():raise RuntimeError('Cycle88 archive unavailable: '+m)
        time.sleep(2)
    x=torch.load(cp,map_location='cpu',weights_only=False)
    execution=read(run/'EXECUTION.json');parent=Path(execution['resumed_from'])
    assert sha(parent)==execution['resumed_checkpoint_sha256']
    stage_parent=parent
    # Exact parent is complete recovery87; incomplete75 remains absent from complete-cycle history.
    old=torch.load(parent,map_location='cpu',weights_only=False)
    assert x['replay']['capacity']==4_000_000 and x['replay']['replay_capacity_followup']==FOLLOWUP_MARKER and x['replay']['replay_capacity_extension']==CAPACITY_MARKER
    assert old['replay']['capacity']==4_000_000 and old['replay']['replay_capacity_extension']==CAPACITY_MARKER and old['replay']['replay_capacity_followup']==FOLLOWUP_MARKER
    assert x['replay']['size']==x['replay']['cursor']==x['steps'] and x['steps']>1_000_000
    assert x['cycle']==88 and x['boundary']=='complete_condition_cycle'
    assert x['learner']['target_pair_reduction']==dict(version=1,target={'impedance':'minimum','admittance':'mean','vmc':'mean'}[m],actor='minimum',sampled_targets=2)
    assert x['cycles'][:-1]==old['cycles'] and x['cycles'][-1]['cycle']==88
    assert finite(x['learner']) and x['learner']['critic_clock']
    assert x['learner']['terminal_loss_weight']==128
    assert x['learner']['finite_target_projection']==dict(version=1,terminal_cap=30.,gamma=.9995,maximum_actions=1375,position='target critic Q before stochastic entropy term',upper_only=True)
    for key in ('actor_optimizer','q_optimizer','alpha_optimizer'):assert x['learner'][key]['param_groups']==old['learner'][key]['param_groups']
    assert x['learner'].get('bellman_target_count',2)==2
    assert execution['batch_size']==65536 and execution['updates_per_transition']==1
    reg=read(run.parent/'REGISTRATION.json');conditions={r['id']:r for r in reg['conditions']}
    assert x['protocol_sha256']==sha(run.parent/'REGISTRATION.json')
    previous=read(reg['post_interruption_continuation']['parent_registration']['path'])
    assert old['recovery_continuation']==previous['post_interruption_continuation']
    assert sha(reg['post_interruption_continuation']['parent_registration']['path'])==reg['post_interruption_continuation']['parent_registration']['sha256']
    assert reg['replay_capacity_stage']==previous['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
    followup=reg['replay_capacity_followup_stage']
    assert followup['marker']==FOLLOWUP_MARKER and followup['parent_cycle']==47
    assert followup==previous['replay_capacity_followup_stage']
    assert sha(followup['entry_checkpoint']['path'])==followup['entry_checkpoint']['sha256'] and old['cycle']==87
    baseline_deps=previous['batch_size_stage']['dependency_hashes'];deps=reg['batch_size_stage']['dependency_hashes']
    assert deps==baseline_deps
    assert all(deps[k]==v for k,v in baseline_deps.items())
    for name,expected in deps.items():assert sha(B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1'/name)==expected
    recovery=reg['interrupted_episode_recovery']
    assert old['boundary']=='complete_condition_cycle' and not old['environment_state_saved']
    assert x['interruption_recovery']==recovery and recovery['parent_cycle']==75 and recovery['new_cycle']==76
    assert not any(c['cycle']==75 for c in x['cycles'])
    assert read(run.parent/'CHECK_ONLY_REVIEW.json')['passed'] and read(run.parent/'INITIAL_STATE_REVIEW.json')['passed']
    assert sha(recovery['partial_audit']['path'])==recovery['partial_audit']['sha256']
    continuation=reg['post_interruption_continuation']
    assert x['recovery_continuation']==continuation and continuation['parent_cycle']==87 and continuation['new_cycle']==88
    assert old['interruption_recovery']==recovery and sha(parent)==continuation['checkpoint']['sha256']
    n=old['replay']['size'];arr=x['replay']['arrays']
    for k,v in old['replay']['arrays'].items():assert np.array_equal(v,arr[k][:n,:50] if k in ('observations','next_observations') else arr[k][:n])
    from persisted_history_critic import marker,feature,KEY
    h=reg['history_critic_amendment'];assert x['history_critic_amendment']==h and x['learner'][KEY]==x['replay'][KEY]==marker(h['binding'])
    peaks=np.load(h['sidecar']['path'],mmap_mode='r')
    for col,key in enumerate(('observations','next_observations')):np.testing.assert_array_equal(arr[key][:n,50],feature(peaks[:,col]))
    transitions=[t for t in lines(run/'transitions.jsonl') if t['cycle']==88]
    assert len(transitions)==x['steps']-old['steps']
    assert [t['step'] for t in transitions]==list(range(old['steps']+1,x['steps']+1))
    assert x['learner']['num_gradient_steps']-old['learner']['num_gradient_steps']==len(transitions)
    np.testing.assert_array_equal(arr['rewards'][n:,0],np.array([t['reward'] for t in transitions],np.float32))
    np.testing.assert_array_equal(arr['dones'][n:,0],np.array([t['done'] for t in transitions],np.float32))
    by_case=collections.defaultdict(list)
    for t in transitions:by_case[t['condition']].append(t)
    episodes=[e for e in lines(run/'episodes.jsonl') if e['cycle']==88]
    assert len(episodes)==30 and {e['condition'] for e in episodes}==set(conditions)
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
            k=t['step']-1
            assert arr['observations'][k,50]==feature(0. if j['interval'] is None else j['interval']['external_penetration_peak_m'])
            assert arr['next_observations'][k,50]==feature(nxt['interval']['external_penetration_peak_m'])
            expected_current=np.r_[np.asarray(j['observation'],np.float32)/x['learner']['observation_scale'],np.float32(t['context']),np.float32((1375-i)/1375)].astype(np.float32)
            np.testing.assert_array_equal(arr['observations'][k,:50],expected_current)
            if t['done']:expected_next=np.r_[expected_current[:49],np.float32((1374-i)/1375)].astype(np.float32)
            else:expected_next=np.r_[np.asarray(nxt['observation'],np.float32)/x['learner']['observation_scale'],np.float32(ts[i+1]['context']),np.float32((1374-i)/1375)].astype(np.float32)
            np.testing.assert_array_equal(arr['next_observations'][k,:50],expected_next)
            np.testing.assert_array_equal(arr['actions'][k]*np.float32(t['context']),np.asarray(j['action'],np.float32))

        assert abs(sum(t['reward'] for t in ts)-e['reward'])<1e-8
    assert sha(reg['reference_plan'])==reg['reference_plan_sha256']
    result=dict(steps=x['steps'],updates=x['learner']['num_gradient_steps'],checkpoint_sha256=sha(cp),
        replay_capacity_extension=CAPACITY_MARKER, replay_capacity_followup=FOLLOWUP_MARKER, current_replay_capacity=4_000_000, historical_entry_cycle=23, crossed_second_capacity=x['replay']['size']>2_000_000, rows_beyond_second_capacity=max(0,x['replay']['size']-2_000_000), replay_size=x['replay']['size'], crossed_original_capacity=True, new_transitions=len(transitions),retained_replay_rows=n,retained_replay_all_old_fields_exact=True,retained_history_features_exact=True,new_current_next51_and_raw_mixed_action_exact=True,
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
