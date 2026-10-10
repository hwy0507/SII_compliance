"""Fixed 2x2 reward / n-step experiment on the SAME pure-RL 11k prefix.

No demonstrations, BC, new physics or evaluation. Fresh upstream SimbaV2 agents
consume retained train transitions in chronological order. This is explicitly
off-policy data reuse, not exact continuation of old learned weights. A future
online segment must use the matching independently registered root and adapter.
"""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import numpy as np
from office_v7_uniform24_20261008 import read,write,sha,now
from research72_checkpoint_20261003 import checkpoint_hashes
from local_rl_campaign_20261009 import hashes

OVERLAYS=['offline_credit_assignment_trial_20261009.py','multistep_rl_replay_20261009.py',
    'multistep_official_adapter_20261009.py','decoupled_task_safety_reward_20261009.py',
    'audit_decoupled_task_safety_reward_20261009.py','inspect_local_rl_progress_20261009.py',
    'train_baseline_repair_rl_20261008.py','baseline_repair_online_worker_20261008.py',
    'audit_rebuild_repair_reward_20261008.py']


def prepare(parent,out,budget):
    assert platform.node()=='airpig' and not out.exists()
    cp=parent/'direct_office_task_segment011k/checkpoint_0011000'
    state=read(cp.parent/'execution.json');assert state['status']=='complete'
    assert checkpoint_hashes(cp)==state['checkpoint_rows'][-1]['hashes']
    source_protocol=read(parent/'PROTOCOL.json');authorization=read(budget)
    assert datetime.now(timezone.utc)<datetime.fromisoformat(authorization['dispatch_deadline_utc'])
    out.mkdir(parents=True)
    jobs=[]
    for n_step in (1,25):
        for variant in ('original','task_safety'):
            root=out/f'n{n_step:02d}_{variant}';root.mkdir()
            shutil.copytree(parent/'source',root/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            for name in OVERLAYS:shutil.copy2(Path(__file__).with_name(name),root/'source/tools'/name)
            parameter=root/'parameter_fullrange'
            shutil.copytree(parent/'parameter_fullrange',parameter,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            (parameter/'official_parameter_agent.py').rename(parameter/'official_parameter_agent_base.py')
            (parameter/'official_parameter_agent.py').write_text(
                'from pathlib import Path\nfrom multistep_official_adapter_20261009 import make_adapter\n'
                'BATCH_SIZE=256\nOfficialParameterAgent=make_adapter(Path(__file__).with_name('
                '"official_parameter_agent_base.py"),n_step='+str(n_step)+')\n')
            for name in ('CONDITIONS.json','teacher.json'):shutil.copy2(parent/name,root/name)
            protocol=dict(source_protocol,registered_utc=now(),
                overlay_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                overlay_dirty_source_identification='Exact SOURCE_HASHES; overlay commit does not claim clean snapshot',
                source_scope='Frozen parent plus hashed reward/n-step training overlays; physics unchanged',
                training_dispatch_deadline_utc=authorization['dispatch_deadline_utc'],
                deadline_basis='Latest explicit15h user window ending2026-10-10T04:21Z',
                parent_protocol_sha256=sha(parent/'PROTOCOL.json'),reward_variants=[variant],
                reward_variant=variant,n_step=n_step,
                jobs=[dict(name='direct_office_task',controller=None,reward='office_task',hp='exploratory')],
                registration_kind='Independent 2x2 credit assignment trial; not a replacement final baseline',
                offline_prefix=dict(checkpoint=str(cp),hashes=checkpoint_hashes(cp),
                    steps=11000,ownership='Same original pure-RL interactions reused, not11000 new physics steps',
                    gradient_updates_per_cell=12002,teacher_or_bc=False),
                online_dispatch_authorized_by_this_script=False)
            write(root/'PROTOCOL.json',protocol)
            write(root/'SOURCE_HASHES.json',hashes(root/'source'))
            write(root/'PARAMETER_HASHES.json',hashes(parameter))
            shutil.copy2(parent/'RUNTIME_HASHES.json',root/'RUNTIME_HASHES.json')
            jobs.append(dict(root=str(root),n_step=n_step,reward_variant=variant,protocol_sha256=sha(root/'PROTOCOL.json')))
    write(out/'REGISTRATION.json',dict(registered_utc=now(),budget_sha256=sha(budget),
        source_sha256=sha(__file__),jobs=jobs,compute_host='airpig',simulations=0,
        offline_only=True,maximum_total_updates=48008,development_reads=0,final_reads=0,
        future='Retain all four outcomes; no claim of usable policy without paired closed-loop development. '
               'n-step off-policy returns introduce behavior-policy bias; this is a declared learning ablation.'))
    print('Registered four cells:',out)


def run(root):
    assert platform.node()=='airpig'
    p=read(root/'PROTOCOL.json');out=root/'direct_office_task_segment011k'
    assert not out.exists()
    assert hashes(root/'source')==read(root/'SOURCE_HASHES.json')
    assert hashes(root/'parameter_fullrange')==read(root/'PARAMETER_HASHES.json')
    deadline=datetime.fromisoformat(p['training_dispatch_deadline_utc'])
    assert datetime.now(timezone.utc)<deadline
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text())<=3*1024**3 and (cg/'memory.swap.max').read_text().strip()=='0'
    cp=Path(p['offline_prefix']['checkpoint']);assert checkpoint_hashes(cp)==p['offline_prefix']['hashes']
    parents=[];cursor=cp.parent
    while True:
        state=read(cursor/'execution.json');assert state['status']=='complete'
        parents.append(state)
        if 'resumed_from' not in state:break
        prior=Path(state['resumed_from']['checkpoint']).parent
        assert sha(prior/'execution.json')==state['resumed_from']['parent_execution_sha256'];cursor=prior
    rows=[row for state in reversed(parents) for row in state['rows']]
    train={c['id'] for c in read(root/'CONDITIONS.json')['conditions'] if c['role']=='train'}
    assert all(row['condition_id'] in train for row in rows)
    with np.load(cp/'office_replay.npz') as z:data={k:z[k] for k in z.files}
    assert len(data['reward'])==sum(row['steps'] for row in rows)==11000
    from decoupled_task_safety_reward_20261009 import TaskSafetyPenalty
    from audit_decoupled_task_safety_reward_20261009 import terminal_task_adjustment
    rewards=data['reward'].astype(float).copy();offset=0;input_evidence=[]
    for row in rows:
        run=Path(row['run']);assert sha(run/'rollout.npz')==row['trace_sha256']
        assert sha(run/'AUDIT.json')==row['audit_sha256']
        with np.load(run/'baseline_policy.npz') as z:
            np.testing.assert_array_equal(z['observation'].astype(np.float32),data['observation'][offset:offset+row['steps']])
            np.testing.assert_array_equal(z['raw_action'].astype(np.float32),data['action'][offset:offset+row['steps']])
        if p['reward_variant']=='task_safety':
            with np.load(run/'research_substeps.npz') as z:penetration=z['external_penetration_m'].copy()
            assert sha(run/'research_substeps.npz')==read(run/'research_channels.json')['telemetry_sha256']
            intervals=read(run/'RL_INTERVALS.json');assert intervals[0] is None
            assert len(intervals)==row['steps']+1
            penalty=TaskSafetyPenalty();position=0;elapsed=0.
            for j,iv in enumerate(intervals[1:]):
                end=position+iv['substeps'];elapsed+=iv['elapsed_s'];done=j==row['steps']-1
                cost,_=penalty(float(penetration[position:end].max()),terminated=done,elapsed_s=elapsed)
                rewards[offset+j]-=cost
                if done:rewards[offset+j]+=terminal_task_adjustment(row['result']['task_success'],row['result']['strict_success'])
                position=end
            assert position==len(penetration)
        input_evidence.append(dict(run=str(run),trace_sha256=row['trace_sha256'],audit_sha256=row['audit_sha256']))
        offset+=row['steps']
    out.mkdir()
    sys.path.insert(0,str(root/'parameter_fullrange'))
    from official_parameter_agent import OfficialParameterAgent,BATCH_SIZE
    from multistep_rl_replay_20261009 import MultiStepReplay
    from baseline_repair_rl_diagnostics_20261008 import flatten_metrics
    source_spec=read(cp.parent/'PROTOCOL.json');cfg=source_spec['agent_config'];seed=source_spec['seed']
    agent=OfficialParameterAgent(seed=seed,total_steps=500000,utd=2,gamma=cfg['gamma'],
        entropy_coef=cfg['temp_target_entropy_coef'],initial_temperature=cfg['temp_initial_value'],action_dimension=7)
    replay=MultiStepReplay(500000,7,seed+53,n_step=p['n_step'],gamma=cfg['gamma'])
    spec=dict(source_spec,registered_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),
        agent_config=agent.config,parameter_source=str(root/'parameter_fullrange'),
        prior_file_sha256=sha(root/'parameter_fullrange/PRIORS.json'),reward_variant=p['reward_variant'],
        initialization='Fresh upstream agent consuming identical retained pure-RL train prefix; no new physics',
        reward_metadata_rebuilt_from_physical_substeps=p['reward_variant']=='task_safety',
        source_sha256={str(root/'source'/k):v for k,v in read(root/'SOURCE_HASHES.json').items()},
        deadline_utc=p['training_dispatch_deadline_utc'])
    write(out/'PROTOCOL.json',spec)
    state=dict(status='running',started_utc=now(),host='airpig',steps=0,updates=0,rows=[],
        command=sys.argv,python=sys.executable,memory_max_bytes=int((cg/'memory.max').read_text()),
        source_episode_rows=rows,checkpoint_rows=[],episodes=0,new_physics_steps=0,
        source_checkpoint=str(cp),source_checkpoint_hashes=p['offline_prefix']['hashes'],
        input_evidence=input_evidence)
    write(out/'execution.json',state);pending=None
    try:
        with (out/'optimizer.jsonl').open('x') as stream:
            for i,reward in enumerate(rewards):
                agent.sample_action(data['observation'][i],previous_transition=pending,training=True)
                transition={k:v[i] for k,v in data.items()};transition['reward']=reward;replay.add(**transition)
                pending=dict(reward=reward,terminated=bool(data['terminated'][i]),truncated=False)
                if i+1>=5000:
                    for _ in range(2):
                        info=flatten_metrics(agent.update(replay.sample(BATCH_SIZE)))
                        assert all(np.isfinite(v) for v in info.values())
                        stream.write(__import__('json').dumps(dict(step=i+1,update=agent.updates,metrics=info))+'\n')
                if pending['terminated']:agent.consume_transition(**pending);pending=None
                if (i+1)%250==0:
                    state.update(steps=i+1,updates=agent.updates,updated_utc=now());write(out/'execution.json',state)
                    assert datetime.now(timezone.utc)<deadline,'No offline updates beyond authorized window'
        assert pending is None and agent.interactions==agent.reward_samples==11000
        target=out/'checkpoint_0011000';agent.save(target);metadata=replay.save(target/'office_replay.npz')
        runner=read(cp/'office_runner.json');runner.update(replay=metadata,offline_rebuilt=True)
        write(target/'office_runner.json',runner)
        state.update(status='complete',steps=11000,updates=agent.updates,episodes=runner['episode'],
            stop_reason='step_budget',checkpoint_rows=[dict(path=str(target),step=11000,episode=runner['episode'],hashes=checkpoint_hashes(target))],
            diagnostics=agent.diagnostics())
        assert agent.updates==12002
        assert checkpoint_hashes(cp)==p['offline_prefix']['hashes']
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(out/'execution.json',state)
    print(root.name,state['status'],state['updates'],'updates, no new physics')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--parent',type=Path)
    parser.add_argument('--budget',type=Path);args=parser.parse_args()
    if args.parent:prepare(args.parent.resolve(),args.root.resolve(),args.budget.resolve())
    else:run(args.root.resolve())
