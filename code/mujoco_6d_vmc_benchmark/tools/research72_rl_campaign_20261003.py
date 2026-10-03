"""Finite office RL adaptation after controller selection and paired development.

Three sequential queues share four simulation leases with future ESN work.
Each model uses an explicit 5,500-step segment then a verified boundary resume,
with an unchanged 80,000-step total schedule/cap. No new sealed conditions.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone, timedelta
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from run_all_methods_formal_20261003 import PARAMETER
from run_paper_final_validation_20261003 import ENV
from research72_checkpoint_20261003 import checkpoint_hashes
from research72_slots_20261003 import simulation_slot


def read(p):
    return json.loads(p.read_text())


def queue(root, out, index):
    spec = read(out/'SPECIFICATION.json')
    deadline = datetime.fromisoformat(spec['development_deadline_utc'])
    dest = out/f'queue_{index}'
    dest.mkdir(exist_ok=False)
    state = dict(status='waiting_for_simulation_lease', started_utc=now(), rows=[])
    write(dest/'execution.json', state)
    try:
        with simulation_slot(root, deadline) as lease:
            state.update(status='running', simulation_lease=lease)
            write(dest/'execution.json', state)
            for job in spec['jobs'][index::3]:
                if datetime.now(timezone.utc) >= deadline:
                    state['status'] = 'deadline_no_new_dispatch'
                    break
                model = dest/job['name']
                model.mkdir()
                row = dict(name=job['name'], seed=job['seed'], family=job['family'], segments=[])
                state['rows'].append(row)
                previous = None
                for stage, limit in (('initial',5500),('continued',80000)):
                    if datetime.now(timezone.utc) >= deadline:
                        break
                    output = model/stage
                    command = [sys.executable, str(ROOT/'tools/research72_train_rl_20261003.py'),
                        '--root',str(root),'--output',str(output),'--reward',job['reward'],
                        '--seed',str(job['seed']),'--steps','80000','--stop-at-step',str(limit),
                        '--probe-receipt',spec['ipc_probe_receipt'],
                        '--parameter-source',str(out/'parameter_source')]
                    if job['controller']:
                        command += ['--controller',job['controller']]
                    if previous:
                        command += ['--resume-checkpoint',previous['path']]
                    part = dict(stage=stage,command=command,started_utc=now())
                    row['segments'].append(part)
                    write(dest/'execution.json',state)
                    with (model/(stage+'.log')).open('x') as log:
                        part['returncode'] = subprocess.run(command,cwd=ROOT,
                            stdout=log,stderr=subprocess.STDOUT).returncode
                    part['ended_utc'] = now()
                    write(dest/'execution.json',state)
                    assert part['returncode']==0, 'Failed training retained, no automatic retry'
                    result = read(output/'execution.json')
                    assert result['status']=='complete'
                    previous = result['checkpoint_rows'][-1]
                    assert previous['step']==result['steps']
                    assert checkpoint_hashes(previous['path'])==previous['hashes']
                    part.update(cumulative_steps=result['steps'],new_segment_steps=result['new_segment_steps'],
                        episodes=result['episodes'],updates=result['updates'],
                        execution_sha256=sha(output/'execution.json'))
                    manifest = dict(checkpoint=previous['path'],hashes=previous['hashes'],controller=job['controller'],
                        seed=job['seed'],family=job['family'],cumulative_physics_steps=result['steps'],
                        training_protocol=str(output/'PROTOCOL.json'),training_protocol_sha256=sha(output/'PROTOCOL.json'))
                    write(model/(stage+'_CHECKPOINT.json'),manifest)
                    row.update(latest_manifest=str(model/(stage+'_CHECKPOINT.json')),
                        latest_manifest_sha256=sha(model/(stage+'_CHECKPOINT.json')))
                    write(dest/'execution.json',state)
                assert previous is not None, 'No completed training segment'
            else:
                state['status']='complete'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc))
        raise
    finally:
        state['ended_utc']=now()
        write(dest/'execution.json',state)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--predecessor',type=Path)
    p.add_argument('--checkpoint-probe',type=Path)
    p.add_argument('--queue',type=int,choices=range(3))
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    if a.queue is not None:
        queue(root,out,a.queue)
        return
    assert a.predecessor and a.checkpoint_probe
    protocol=read(root/'PROTOCOL.json')
    deadline=datetime.fromisoformat(protocol['authorization_start_utc'])+timedelta(hours=48)
    assert protocol['budget_caps']['rl_adaptation_steps_per_family_seed']==80000
    probe=read(a.checkpoint_probe)
    assert probe['status']=='complete' and probe['physics_steps']==0
    assert {r['action_dimension'] for r in probe['rows']}=={5,7}
    assert all(r['exact_future_action_and_update_replay'] and r['exact_replay_rng_restore'] for r in probe['rows'])
    ipc=root/'prepare_learning_v2/rl_parity/execution.json'
    assert read(ipc)['observations_and_physics_exact']
    out.mkdir(parents=True,exist_ok=False)
    families=[('parameter_'+c,c,'metric') for c in ('admittance','impedance','vmc')]
    families += [('direct_metric',None,'metric'),('direct_office_task',None,'office_task')]
    assert [f[0] for f in families]==protocol['budget_caps']['rl_families']
    jobs=[dict(name=f'{family}_{seed}',family=family,controller=c,reward=reward,seed=seed)
        for seed in protocol['budget_caps']['training_seeds'] for family,c,reward in families]
    spec=dict(registered_utc=now(),protocol_sha256=sha(root/'PROTOCOL.json'),jobs=jobs,
        development_deadline_utc=deadline.isoformat(),checkpoint_probe_sha256=sha(a.checkpoint_probe),
        ipc_probe_receipt=str(ipc),ipc_probe_sha256=sha(ipc),source_sha256=sha(Path(__file__)),
        method='Official SimbaV2, three paired seeds, from scratch on registered office training identities.',
        priors='Original controller laws and bounds; initialize each parameter family at its previously registered development-selected classical center.',
        budgets='80,000 cumulative physics steps per family/seed, never per segment. No replay resets on continuation.',
        reserved_simulators=3,shared_simulator_cap=4,
        role='Training/development only; no final-test unlock or outcome-based early checkpoint selection.')
    write(out/'SPECIFICATION.json',spec)
    state=dict(status='waiting_for_predecessor',started_utc=now(),specification_sha256=sha(out/'SPECIFICATION.json'))
    write(out/'execution.json',state)
    try:
        while True:
            previous=read(a.predecessor/'execution.json')
            if previous['status']=='complete':
                break
            assert previous['status']=='waiting_for_controller_screen' or previous['status'].startswith('running_'), previous['status']
            assert datetime.now(timezone.utc)<deadline, 'Development cutoff; no new dispatch'
            time.sleep(30)
        choice=read(a.predecessor/'CONTROLLER_CHOICE.json')
        assert choice['protocol_sha256']==sha(root/'PROTOCOL.json')
        assert choice['baseline_priors_sha256']==sha(PARAMETER/'PRIORS.json')
        parameter=out/'parameter_source'
        shutil.copytree(PARAMETER,parameter,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        priors=read(PARAMETER/'PRIORS.json')
        for controller in ('admittance','impedance','vmc'):
            selected=next(c for c in choice['candidates'] if c.get('controller')==controller)
            priors['methods'][controller]['center']=selected['config']['parameters']
        priors.update(selection='Registered office development-selected centers; original equations/bounds retained.',
            office_choice_sha256=sha(a.predecessor/'CONTROLLER_CHOICE.json'),
            primitive_prior_sha256=sha(PARAMETER/'PRIORS.json'))
        write(parameter/'PRIORS.json',priors)
        state.update(status='running',office_choice_sha256=priors['office_choice_sha256'],
            adapted_prior_sha256=sha(parameter/'PRIORS.json'))
        write(out/'execution.json',state)
        def launch(index):
            command=['systemd-run','--user','--wait','--pipe','--collect',
                '--unit=sii-r72-rl-'+out.name.replace('_','-')+'-'+str(index),
                '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=CPUQuota=100%']
            env={**ENV,'SII_SOURCE_BASE_COMMIT':os.environ['SII_SOURCE_BASE_COMMIT']}
            command += ['--setenv='+k+'='+v for k,v in env.items()]
            command += [sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--output',str(out),'--queue',str(index)]
            with (out/f'queue_{index}.log').open('x') as log:
                rc=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT).returncode
            return dict(queue=index,returncode=rc,command=command)
        with ThreadPoolExecutor(max_workers=3) as pool:
            state['queues']=list(pool.map(launch,range(3)))
        assert all(q['returncode']==0 for q in state['queues'])
        states=[read(out/f'queue_{i}/execution.json') for i in range(3)]
        state['status']='complete' if all(q['status']=='complete' for q in states) else 'deadline_no_new_dispatch'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc))
        raise
    finally:
        state['ended_utc']=now()
        write(out/'execution.json',state)


if __name__=='__main__':
    main()
