"""Finite development-only baseline strengthening, never automatic final claims.

Register before dispatch; immutable source/priors; at most four simulators.
Completed historical development episodes are reused only with their original
hashes and condition/config equality. Failed attempts are never overwritten.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
from scipy.stats import qmc
from office_v7_uniform24_20261008 import read, write, sha, now, V6, MENAGERIE, FAMILIES
from prepare_baseline_repair_20261008 import sample
from run_paper_final_validation_20261003 import ENV

HISTORY = Path('/home/arm1/sii_shared/SII_compliance/runs/main/baseline_repair_15h_20261008')
SOURCE_FILES = ('baseline_repair_worker_20261008.py', 'train_baseline_repair_rl_20261008.py',
    'baseline_fullrange_controllers_20261009.py', 'test_baseline_fullrange_20261009.py',
    'strengthen_baselines_20261009.py')


def hashes(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p.suffix in ('.py', '.json')}


def prepare(root, history):
    root.mkdir(parents=True, exist_ok=False)
    source = root/'source'
    shutil.copytree(history/'source_v9', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in SOURCE_FILES:
        shutil.copy2(Path(__file__).with_name(name), source/'tools'/name)
    # Import preflight also covers the historical late-report dependency defect.
    shutil.copy2(Path(__file__).with_name('report_office_v7_uniform24_20261008.py'),
                 source/'tools/report_office_v7_uniform24_20261008.py')
    parameter = root/'parameter_fullrange_v1'
    shutil.copytree(history/'parameter_v2', parameter, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    shutil.copy2(Path(__file__).with_name('baseline_fullrange_controllers_20261009.py'), parameter)
    (parameter/'controllers.py').write_text('"""Separately registered full-range baseline variant."""\nfrom baseline_fullrange_controllers_20261009 import *\n')
    priors = read(parameter/'PRIORS.json')
    priors['parameter_mapping'] = 'piecewise_log_full_bounds_center_zero_v1; original rate/tank unchanged'
    write(parameter/'PRIORS.json', priors)
    old_protocol = read(history/'PROTOCOL.json')
    conditions = read(history/'CONDITIONS.json')
    # Existing training/development are deliberately reused; old final is NOT used.
    write(root/'CONDITIONS.json', conditions)
    shutil.copy2(history/'teacher.json', root/'teacher.json')
    shutil.copy2(history/'FINAL_MODELS.json', root/'HISTORICAL_MODELS.json')
    (root/'sealed').mkdir()
    write(root/'sealed/HELDOUT.json', dict(conditions=sample(202610090503, 'final', 24)))
    (root/'sealed/HELDOUT.json').chmod(0o400)
    candidates = read(history/'CLASSICAL_CANDIDATES.json')['candidates']
    for method in ('vmc', 'admittance', 'impedance'):
        bounds = np.asarray(priors['methods'][method]['bounds'])
        points = qmc.Sobol(len(bounds), scramble=True, seed=2026100904).random_base2(4)
        for index, point in enumerate(points, 24):
            theta = np.exp(np.log(bounds[:, 0])+point*np.log(bounds[:, 1]/bounds[:, 0]))
            candidates.append(dict(name=f'{method}_{index:02d}', method=method, parameters=theta.tolist()))
    write(root/'CLASSICAL_CANDIDATES.json', dict(candidates=candidates,
        design='Historical 24 plus 16 preregistered Sobol candidates; all receive all eight development conditions'))
    start = datetime.now(timezone.utc)
    protocol = dict(schema='sii-baseline-strengthening-v1', registered_utc=now(),
        authorization='2026-10-09 user: strengthen baseline implementation/tuning/fairness, then compare. New bounded work; old 15h run remains closed.',
        source_base_commit='0a1080709b85a9918aa0a1975f4401836ee48f30',
        baseline_commit='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d', history=str(history),
        history_protocol_sha256=sha(history/'PROTOCOL.json'),
        formal_model_sha256=old_protocol['formal_model_sha256'], physics_dt_s=.00005, duration_s=55.,
        condition_file_sha256=sha(root/'CONDITIONS.json'), sealed_condition_sha256=sha(root/'sealed/HELDOUT.json'),
        authorization_start_utc=start.isoformat(),
        training_dispatch_deadline_utc=(start+timedelta(hours=72)).isoformat(),
        dispatch_deadline_utc=(start+timedelta(hours=72)).isoformat(),
        deadline_basis='Agent-imposed finite 72h fail-safe, not a new user-specified duration or extension of the old 15h grant. Finite job/step caps dominate; stop at completed episode boundaries.',
        budgets=dict(training_seeds=[2026100911, 2026100912, 2026100913],
            rl_steps_per_family_seed=500000, initial_rl_segment_steps=50000,
            rl_families=['parameter_vmc','parameter_admittance','parameter_impedance','direct_metric','direct_office_task'],
            classical_candidates_per_family=40, classical_conditions_per_candidate=8,
            initial_rl_diagnostic_families=['parameter_impedance','direct_office_task'],
            initial_rl_diagnostic_seeds=[2026100911],
            pilot_is_not_training_sufficiency=True),
        rl_hyperparameters=dict(historical=dict(entropy_coef=-2.,initial_temperature=.0001),
                                exploratory=dict(entropy_coef=-.5,initial_temperature=.01)),
        unchanged=old_protocol['unchanged'],
        resources=dict(spark_max_simulators=4, local_max_simulators=1, threads=1,
                       memory_max_per_worker=3221225472, memory_swap_max=0),
        selection='All eight development identities for every classical candidate; strict/task/full then worst/sum actual payload target distance, penetration, RMSE/torque. No final-result selection.',
        saturation='Compare cumulative best at24/32/40 candidates on identical8 conditions. No success plus flat curve is not sufficient alone: inspect boundary optima and task/force stall mechanism before declaring bounded-search limitation.',
        rl_stopping='Initial50k is exploration/mapping diagnostic only. Review checkpoint development curves and value/entropy diagnostics before extending same configurations to100k/250k/500k. Repeat chosen setting with three seeds. Zero-success collapse is unresolved, never auto-certified sufficient.',
        neural_fairness='Reuse verified same20train/5validation teacher cohort across all six neural families/three seeds; evaluate the same development conditions. Report parent pretraining and search costs. Do not silently keep old18/6 selected MLPs.',
        final_policy='No final evaluation entry in this tool. Freeze all methods only after readiness review, then use new sealed24. Prior24 are historical only. Baseline failure is allowed; infrastructure/known implementation defects are not.',
        pure_rl='No teacher/BC in these rows; any later BC warmstart must be a separate named method and budget.',
        completion='This queue produces development evidence, not proof of baseline optimality or ESN superiority.')
    write(root/'PROTOCOL.json', protocol)
    write(root/'SOURCE_HASHES.json', hashes(source))
    write(root/'PARAMETER_HASHES.json', hashes(parameter))
    write(root/'execution.json', dict(status='registered', registered_utc=now(),
        protocol_sha256=sha(root/'PROTOCOL.json'), final_evaluation_started=False))
    print(json.dumps(dict(root=str(root), protocol_sha256=sha(root/'PROTOCOL.json'))))


def managed(root, command, label, gpu=False):
    env = dict(ENV, SII_SOURCE_BASE_COMMIT=read(root/'PROTOCOL.json')['source_base_commit'],
               MUJOCO_MENAGERIE_PATH=str(MENAGERIE), JAX_PLATFORMS='cuda' if gpu else 'cpu')
    return ['systemd-run', '--user', '--wait', '--pipe', '--collect', '--unit='+label,
        '--property=MemoryMax=3G', '--property=MemorySwapMax=0', '--property=TasksMax=256',
        '--property=CPUAffinity=5-9,15-19', '--property=AllowedCPUs=5-9,15-19',
        '--working-directory='+str(root/'source')] + ['--setenv='+k+'='+v for k,v in env.items()] + command


def classical_jobs(root):
    protocol = read(root/'PROTOCOL.json'); history = Path(protocol['history'])
    conditions = [c for c in read(root/'CONDITIONS.json')['conditions'] if c['role']=='development']
    candidates = read(root/'CLASSICAL_CANDIDATES.json')['candidates']
    jobs = []
    for candidate in candidates:
        for condition in conditions:
            name = candidate['name']+'__'+condition['id']
            reused = None
            for phase in ('classical_confirmation', 'classical_screen'):
                receipt = history/phase/(name+'.execution.json')
                if receipt.exists():
                    old = read(receipt)
                    if old['status'] != 'complete':
                        continue
                    if old['candidate'] != candidate or old['condition'] != condition['id']:
                        raise ValueError('Historical candidate/condition mismatch')
                    run = history/phase/name
                    assert sha(run/'AUDIT.json') == old['audit_sha256']
                    assert sha(run/'rollout.npz') == old['trace_sha256']
                    old_condition = next(c for c in read(history/'CONDITIONS.json')['conditions'] if c['id']==condition['id'])
                    assert old_condition == condition
                    # Static classical raw parameter action is zero, so use its
                    # original repaired adapter for all new classical episodes.
                    reused = dict(receipt=str(receipt), receipt_sha256=sha(receipt),
                        audit_sha256=old['audit_sha256'], trace_sha256=old['trace_sha256'], run=str(run))
                    break
            jobs.append(dict(name=name, kind='classical', candidate=candidate, condition=condition, reused=reused))
    return jobs


def rl_jobs(root):
    p = read(root/'PROTOCOL.json'); jobs = []
    for family in p['budgets']['initial_rl_diagnostic_families']:
        for hp in p['rl_hyperparameters']:
            for seed in p['budgets']['initial_rl_diagnostic_seeds']:
                name = f'{family}_{hp}_{seed}_segment050k'
                jobs.append(dict(name=name, kind='rl', family=family, hyperparameter_id=hp, seed=seed))
    return jobs


def execute(root, job):
    p = read(root/'PROTOCOL.json'); source = root/'source'
    directory = root/'development'; directory.mkdir(exist_ok=True)
    receipt = directory/(job['name']+'.execution.json')
    if receipt.exists():
        old = read(receipt)
        if old['status'] not in ('complete', 'historical_reused'):
            raise RuntimeError('Incomplete attempt preserved: '+str(receipt))
        for path, digest in old['artifacts'].items():
            assert sha(path) == digest
        return old
    if job.get('reused'):
        reused = job['reused']
        row = dict(status='historical_reused', job=job, completed_utc=now(),
            artifacts={reused['receipt']:reused['receipt_sha256'],
                       str(Path(reused['run'])/'AUDIT.json'):reused['audit_sha256'],
                       str(Path(reused['run'])/'rollout.npz'):reused['trace_sha256']})
        write(receipt, row); return row
    if datetime.now(timezone.utc) >= datetime.fromisoformat(p['dispatch_deadline_utc']):
        raise RuntimeError('New dispatch stopped at finite deadline')
    run = directory/job['name']
    parameter = root/'parameter_fullrange_v1'
    if job['kind']=='classical':
        # Identical source/prior semantics to historical classical runs.
        parameter = Path(p['history'])/'parameter_v2'
        config = directory/(job['name']+'.config.json')
        write(config, dict(parameters=job['candidate']['parameters']))
        command = [sys.executable, str(source/'tools/baseline_repair_worker_20261008.py'),
            '--research-protocol', str(root/'PROTOCOL.json'), '--protocol-sha256', sha(root/'PROTOCOL.json'),
            '--research-condition', job['condition']['id'], '--phase', 'development', '--worker-kind', 'classical',
            '--v6-input', str(V6), '--reference', str(V6/'esn_original_v2/rollout.json'),
            '--config', str(config), '--output', str(run), '--contact-audit', '--physics-dt', '.00005',
            '--controller', job['candidate']['method'], '--parameter-source', str(parameter)]
    else:
        command = [sys.executable, str(source/'tools/train_baseline_repair_rl_20261008.py'),
            '--root', str(root), '--output', str(run), '--parameter-source', str(parameter),
            '--reward', 'office_task', '--seed', str(job['seed']), '--steps', '500000',
            '--stop-at-step', str(p['budgets']['initial_rl_segment_steps']),
            '--hyperparameter-id', job['hyperparameter_id']]
        if job['family'].startswith('parameter_'):
            command += ['--controller', job['family'].removeprefix('parameter_')]
    command = managed(root, command, 'sii-strength-'+job['name'].replace('_','-'), gpu=job['kind']=='rl')
    row = dict(status='running', job=job, command=command, started_utc=now(),
               protocol_sha256=sha(root/'PROTOCOL.json'))
    write(receipt, row)
    with (directory/(job['name']+'.log')).open('x') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    row.update(ended_utc=now(), returncode=result.returncode)
    if result.returncode:
        row['status']='failed_preserved'; write(receipt,row)
        raise RuntimeError('Job failed, preserved: '+job['name'])
    if job['kind']=='classical':
        audit=read(run/'AUDIT.json')
        assert audit['model_sha256']==p['formal_model_sha256']
        artifacts={str(run/name):sha(run/name) for name in ('AUDIT.json','rollout.npz','rollout.json')}
    else:
        state=read(run/'execution.json'); assert state['status']=='complete'
        artifacts={str(run/name):sha(run/name) for name in ('execution.json','PROTOCOL.json')}
        # Each saved checkpoint has its own complete checksum manifest in execution.
        assert state['checkpoint_rows'] and state['steps'] <= p['budgets']['initial_rl_segment_steps']
    row.update(status='complete',artifacts=artifacts); write(receipt,row); return row


def run(root, mode, workers):
    assert 1 <= workers <= 4
    if (root/'HOLD.json').exists():
        raise RuntimeError('Campaign is on explicit hold; inspect HOLD.json and preserve interrupted attempts')
    lock=(root/'.dispatch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for directory, manifest in ((root/'source',root/'SOURCE_HASHES.json'),
                                (root/'parameter_fullrange_v1',root/'PARAMETER_HASHES.json')):
        assert hashes(directory)==read(manifest), 'Frozen source changed'
    assert read(root/'FULLRANGE_CONTRACT.json')['status']=='passed'
    # One process owns every future worker; stable runs are never restarted.
    jobs = (rl_jobs(root) if mode=='rl-pilot' else classical_jobs(root) if mode=='classical' else
            rl_jobs(root)[:2]+classical_jobs(root)+rl_jobs(root)[2:])
    spec=root/(mode+'_JOBS.json')
    if spec.exists():
        assert read(spec)['jobs']==jobs
    else:
        write(spec,dict(registered_utc=now(),jobs=jobs,workers=workers,mode=mode))
    state=dict(status='running',mode=mode,started_utc=now(),expected=len(jobs),completed=0,
               reused=0,failures=[],final_evaluation_started=False)
    write(root/'execution.json',state)
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures={pool.submit(execute,root,j):j for j in jobs}
            for future in as_completed(futures):
                try:
                    row=future.result();state['completed']+=1
                    state['reused']+=int(row['status']=='historical_reused')
                except Exception as exc:
                    state['failures'].append(dict(name=futures[future]['name'],error=repr(exc)))
                    # Cancel only not-yet-started own jobs. Running episodes finish.
                    for pending in futures: pending.cancel()
                state['updated_utc']=now();write(root/'execution.json',state)
        state['status']='failed_preserved' if state['failures'] else 'development_complete_review_required'
    finally:
        state['ended_utc']=now();write(root/'execution.json',state)
    if state['failures']:raise RuntimeError(state['failures'])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--history',type=Path,default=HISTORY)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--mode',choices=('classical','rl-pilot','combined'),default='combined')
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    if args.prepare:prepare(args.root.resolve(),args.history.resolve())
    else:run(args.root.resolve(),args.mode,args.workers)


if __name__=='__main__':main()
