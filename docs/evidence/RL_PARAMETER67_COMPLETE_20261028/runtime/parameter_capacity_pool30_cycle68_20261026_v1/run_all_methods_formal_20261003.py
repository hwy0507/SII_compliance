"""Finite, newly authorized 26-model evaluation; never retrains or tunes.

All models use the same frozen v6 anchor at 50 us on the original native runtime.
Four disjoint sequential queues, each under a 3 GiB systemd unit. The former
12-hour deadline and archived runs are not changed or reused as new executions.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from run_paper_final_validation_20261003 import ENV, FORMAL_HASH

BASE_COMMIT = 'c2bbc79de083564b6107fbe200ab2ecf10bb3207'
LOCK_HASH = '755974da1d4d5a3fb1aa24aa779cf91ede2e83768de2b9dd21089de863166701'
V6 = Path('/home/arm1/vmc_mujoco_runtime/office_validation_v6_20261002')
PARAMETER = Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/parameter_rl/frozen_train02')
MENAGERIE = Path('/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_runtime_inputs_complete_20260930/menagerie')


def active_workers():
    found = []
    for p in Path('/proc').glob('[0-9]*'):
        try:
            status = (p/'status').read_text()
            if any(s.startswith('State:') and ('T (stopped)' in s or 't (tracing stop)' in s) for s in status.splitlines()):
                continue
            names = {Path(x.decode(errors='replace')).name for x in (p/'cmdline').read_bytes().split(b'\0')[1:]}
            if names.intersection({'paper_office_worker_20261002.py', 'paper_classical_worker_20261002.py',
                                   'paper_rl_worker_20261002.py', 'validate_office_v5_20260918.py',
                                   'validate_office_apparatus_v5_20260917.py'}):
                found.append(int(p.name))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            pass
    return found


def run_queue(root, queue):
    protocol = json.loads((root/'PROTOCOL.json').read_text())
    assert sha(root/'VALIDATION_LOCK.json') == LOCK_HASH
    candidates = json.loads((root/'VALIDATION_LOCK.json').read_text())['candidates'][queue::4]
    phase = root/f'queue_{queue}'
    phase.mkdir(exist_ok=False)
    source = phase/'source'
    for folder in ('scripts', 'assets', 'tools'):
        shutil.copytree(ROOT/folder, source/folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs'))
    env = {**os.environ, **ENV, 'SII_SOURCE_BASE_COMMIT': BASE_COMMIT,
           'MUJOCO_MENAGERIE_PATH': str(MENAGERIE)}
    state = dict(status='running', started_utc=now(), argv=sys.argv,
                 protocol_sha256=sha(root/'PROTOCOL.json'), validation_lock_sha256=LOCK_HASH,
                 selected_candidate_names=[c['name'] for c in candidates], rows=[])
    write(phase/'manifest.json', dict(candidates=candidates))
    def save(): write(phase/'execution.json', state)
    save()
    try:
        for c in candidates:
            name = c['name']
            assert Path(name).name == name
            config = phase/(name+'.config.json')
            write(config, c.get('config', {}))
            script = ('paper_rl_worker_20261002.py' if c.get('rl_case') else
                      'paper_classical_worker_20261002.py' if c.get('controller') else 'paper_office_worker_20261002.py')
            command = [sys.executable, str(source/'tools'/script), '--v6-input', str(V6),
                       '--reference', str(V6/'esn_original_v2/rollout.json'), '--config', str(config),
                       '--output', str(phase/name), '--contact-audit', '--physics-dt', str(protocol['physics_dt'])]
            if c.get('rl_case'):
                command += ['--case', c['rl_case'], '--bridge', str(V6/'source/bridge_frozen.py')]
            elif c.get('controller'):
                command += ['--controller', c['controller'], '--parameter-source', str(PARAMETER)]
            elif c.get('checkpoint'):
                assert sha(Path(c['checkpoint'])) == c['checkpoint_sha256']
                command += ['--checkpoint', c['checkpoint']]
            if c.get('memory_ablation'):
                command += ['--memory-ablation', c['memory_ablation']]
            row = dict(name=name, started_utc=now(), command=command, category=c['category'])
            state['rows'].append(row); save()
            with (phase/(name+'.log')).open('x') as log:
                rc = subprocess.run(command, cwd=source, env=env, stdout=log, stderr=subprocess.STDOUT).returncode
            row.update(returncode=rc, ended_utc=now())
            if (phase/name/'AUDIT.json').exists():
                row['audit'] = json.loads((phase/name/'AUDIT.json').read_text())
            save()
            if rc:
                raise RuntimeError(name+' infrastructure error preserved; no automatic retry')
        state['status'] = 'complete'
    except BaseException as exc:
        state.update(status='failed_preserved', error=repr(exc)); raise
    finally:
        state['ended_utc'] = now(); save()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--frozen-root', type=Path)
    p.add_argument('--queue', type=int, choices=range(4))
    a = p.parse_args(); root = a.root.resolve()
    if a.queue is not None:
        run_queue(root, a.queue); return
    assert a.frozen_root is not None
    assert not active_workers(), 'Existing workers; no duplicate dispatch'
    lockpath = a.frozen_root/'final_model_lock/VALIDATION_LOCK.json'
    assert sha(lockpath) == LOCK_HASH
    locked = json.loads(lockpath.read_text())
    assert len(locked['candidates']) == 26
    assert sha(V6/'construction/rollout.mjb') == '173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11'
    root.mkdir(exist_ok=False)
    with (root/'coordinator.lock').open('x') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        shutil.copy2(lockpath, root/'VALIDATION_LOCK.json')
        write(root/'PROTOCOL.json', dict(registered_utc=now(),
            authorization='User 2026-10-03 asks to run proposed and all GitHub baselines together in the test environment.',
            scope='Finite 26 frozen models x one unchanged v6 anchor; no training/tuning/retries; includes previously ineligible methods.',
            interpretation='Known anchor re-evaluation; not unseen generalization and not equal training exposure.',
            source_base_commit=BASE_COMMIT, runner_sha256=sha(Path(__file__)),
            baseline_commit='ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6',
            validation_lock_sha256=LOCK_HASH, physics_dt=.00005, expected_model_sha256=FORMAL_HASH,
            episodes=26, horizon_s=55, seed=2026091751, maximum_simulation_concurrency=4,
            memory_max_per_queue='3G', threads_per_worker=1, reference=str(V6/'esn_original_v2/rollout.json'),
            baseline_protocol_sha256=sha(V6/'PROTOCOL.json'), frozen_root=str(a.frozen_root),
            conditions=dict(ball_launch_s=2, ball_speed_mps=1.45, hand_start_s=4, rod_start_s=13, rod_hold_s=6),
            preserved=['world', 'target', 'planner', 'actor observation', 'actuator bounds', 'task/strict gates', 'checkpoint', 'normalization'],
            reporting=['task and strict shown separately', 'all failures preserved', 'contact exposure NA when absent',
                       'physical substep metrics', 'frozen policy/source audits', 'independent placement reconstruction']))
        state = dict(status='running', started_utc=now(), argv=sys.argv, phases=[], commands=[])
        def save(): write(root/'execution.json', state)
        save()
        def queue(i):
            unit='sii-all-formal-20261003-'+root.name.split('_')[-1]+'-'+str(i)
            command=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
                     '--property=MemoryMax=3G','--property=MemorySwapMax=0']
            command += ['--setenv='+k+'='+v for k,v in {**ENV, 'SII_SOURCE_BASE_COMMIT':BASE_COMMIT}.items()]
            command += [sys.executable,str(Path(__file__).resolve()),'--root',str(root),'--queue',str(i)]
            with (root/f'queue_{i}.log').open('x') as log:
                result=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
            return dict(queue=i, command=command, returncode=result.returncode)
        def post(script, args, label):
            command=[sys.executable,str(ROOT/'tools'/script),*map(str,args)]
            state['commands'].append(command);save()
            with (root/(label+'.log')).open('x') as log:
                subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT)
        try:
            with ThreadPoolExecutor(max_workers=4) as pool:
                state['phases']=list(pool.map(queue,range(4)))
            save()
            assert all(r['returncode']==0 for r in state['phases']), 'Queue failure preserved'
            phases=[root/f'queue_{i}' for i in range(4)]
            names=[r['name'] for phase in phases for r in json.loads((phase/'execution.json').read_text())['rows']]
            assert sorted(names)==sorted(c['name'] for c in locked['candidates']) and len(names)==len(set(names))
            for phase in phases:
                post('audit_paper_phase_20261003.py',['--phase',phase,'--output',root/(phase.name+'_analysis'),
                     '--model-sha256',FORMAL_HASH],phase.name+'_audit')
            post('audit_paper_common_cohort_20261003.py',['--phases',*phases,'--output',root/'COMMON_COHORT.json'],'common_cohort')
            post('report_all_methods_formal_20261003.py',['--root',root],'report')
            post('audit_paper_contact_windows_20261003.py',['--report',root/'report/results.json','--output',root/'CONTACT_WINDOWS.json'],'contact_windows')
            post('audit_paper_final_placement_20261003.py',['--report',root/'report/results.json','--output',root/'placement_audits'],'placements')
            state['status']='complete'
        except BaseException as exc:
            state.update(status='failed_preserved',error=repr(exc));raise
        finally:
            state['ended_utc']=now();save()


if __name__ == '__main__': main()
