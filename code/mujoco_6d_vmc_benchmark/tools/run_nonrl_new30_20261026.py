"""Finite new30 imitation experiment: historical ridge ESN vs ordinary RNN/MLP.

Prepare freezes data, three seeds, twelve candidates per family/seed and twelve
prospective conditions. Run serially fits all candidates, locks nine models,
then evaluates the complete 108-episode grid. No outcome-dependent dispatch.
"""
from __future__ import annotations

import argparse
import fcntl
import itertools
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import numpy as np

from run_nonrl_spt_matrix_20261025 import read, sha, write, now, metric_row, aggregate, render
from research72_protocol_20261003 import sample

ROOT = Path(__file__).resolve().parents[1]
SEEDS = [2026102601, 2026102602, 2026102603]
RATES = [1e-4, 3e-4, 1e-3, 3e-3]
DECAYS = [0., 1e-5, 1e-4]
UPDATES = 32000


def require(ok, text):
    if not ok:
        raise RuntimeError(text)


def manifest(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*.py'))}


def prepare(root):
    require(not root.exists(), 'Never overwrite an experiment')
    parent = ROOT/'outputs/teacher_student_15h_20261012_v3'
    fair = ROOT/'outputs/fair_comparison_20261013_v2'
    meta = read(parent/'data/DATA_COMPLETE.json')
    require(sha(parent/'data/training_data.npz') == meta['training_data_sha256'], 'Parent dataset hash mismatch')
    lineage = meta['lineage'][25:]
    require(len(lineage) == 30 and len({r['teacher_config_sha256'] for r in lineage}) == 1, 'Expected one new teacher')
    new_ids = [r['episode'] for r in lineage]
    require(new_ids == list(range(25,55)), 'Unexpected parent episode numbering')
    # All original traces for these thirty identities must still exist and match.
    for r in lineage:
        run = Path(r['path']).parent
        for f, key in [('rollout.npz','sha256'),('execution_chain.npz','chain_sha256'),('execution.json','execution_sha256')]:
            require(sha(run/f) == r[key], f'New demonstration provenance changed: {run}/{f}')
        require(r['task_success'] and r['strict_success'], 'Nonqualified demonstration')
    with np.load(parent/'data/training_data.npz') as z:
        mask = np.isin(z['episode'],new_ids)
        values = {k:z[k][mask].copy() for k in z.files}
    values['episode'] -= 25
    ep, train = values['episode'], values['train']
    require(len(ep) == 41250 and len(np.unique(ep[train])) == 24 and len(np.unique(ep[~train])) == 6, 'Split mismatch')
    require(not set(ep[train]).intersection(ep[~train]), 'Identity leakage')
    require(np.all(values['physical_execution']) and np.all(values['importance'] == 1), 'Unexpected data weights/labels')
    root.mkdir(parents=True)
    (root/'data').mkdir()
    np.savez_compressed(root/'data/training_data.npz',**values)
    new_lineage = [dict(r, episode=r['episode']-25, parent_episode=r['episode']) for r in lineage]
    write(root/'data/DATA_COMPLETE.json',dict(training_data_sha256=sha(root/'data/training_data.npz'),
        parent_dataset_sha256=meta['training_data_sha256'],parent_metadata_sha256=sha(parent/'data/DATA_COMPLETE.json'),
        lineage=new_lineage,episodes=30,frames=41250,training_identities=24,validation_identities=6,
        all_real_execution=True,position_error_context=True,actual_requested_labels_preserved=True,
        teacher_mixture=False,teacher_config_sha256=lineage[0]['teacher_config_sha256'],
        selection_split='Unchanged preassigned new30 identities:24 train/6 validation; no old25; no test histories'))
    for directory in ('tools','scripts'):
        shutil.copytree(ROOT/directory,root/'source'/directory,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(fair/'source',root/'physics_source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    # Use the historical deployment implementations in both isolated snapshots.
    # The live checkout also supports later state-delta ESN variants; those are
    # outside this experiment. Neither live code nor the physics snapshot changes.
    for name in ['office_vmc_memory_esn_20260927.py','office_mlp_rnn_20261002.py']:
        shutil.copy2(root/'physics_source/scripts'/name,root/'source/scripts'/name)
        require(sha(root/'source/scripts'/name) == sha(root/'physics_source/scripts'/name), 'Deployment implementation drift')
    known = set()
    public = [parent/'CONDITIONS.json', fair/'CONDITIONS.json', ROOT/'docs/evidence/research72_20261003/CONDITIONS.json']
    for path in public:
        known.update(json.dumps(c['overrides'],sort_keys=True) for c in read(path)['conditions'])
    conditions = sample(2026102617,[('acceptance',12)])
    for c in conditions:
        c['id'] = 'new30_prospective_20261026_'+c['id']
        require(json.dumps(c['overrides'],sort_keys=True) not in known, 'Known condition overlap')
    write(root/'CONDITIONS.json',dict(conditions=conditions,sampling_seed=2026102617,
        interpretation='Prospective identities within existing narrow disturbance ranges; not new geometry'))
    parent_protocol = read(fair/'PROTOCOL.json')
    write(root/'PROTOCOL.json',dict(schema='sii-baseline-strengthening-v1',registered_utc=now(),
        authorization='User requested historical ESN learning on new30 with fair RNN/MLP comparison',
        physics_dt_s=5e-5,duration_s=55.,formal_model_sha256=parent_protocol['formal_model_sha256'],
        condition_file_sha256=sha(root/'CONDITIONS.json')))
    registration = dict(schema='sii-nonrl-new30-20261026-v1',registered_utc=now(),compute_host=platform.node(),
        seeds=SEEDS,families=['esn','rnn','mlp'],candidates_per_family_seed=12,
        esn_grid=dict(rho=[.5,.8],input_gain=[.08,.25,.6],ridge=[.001,.1]),
        neural_grid=dict(learning_rate=RATES,weight_decay=DECAYS),neural_updates=UPDATES,
        neural_options=dict(tbptt_steps=64,batch_size=8,precision='float64',lr_schedule='cosine',
                            final_rate_ratio=.01,action_delta_weight=0.,global_loss=True,raw_slowdown_loss=True),
        selection='Per family and seed: minimum terminal deployed requested-action MSE on same6 validation identities; deterministic candidate-name tie break. No best-epoch or test-based choice.',
        architecture='ESN:historical128 fixed reservoir+fixed state-context readout features,only ridge readout learns; RNN:ordinary128 Elman; MLP:ordinary128 tanh. Same18 canonical fields and action7, architecture-specific preprocessing disclosed; not parameter-matched.',
        data_sha256=sha(root/'data/training_data.npz'),metadata_sha256=sha(root/'data/DATA_COMPLETE.json'),
        protocol_sha256=sha(root/'PROTOCOL.json'),condition_sha256=sha(root/'CONDITIONS.json'),
        source_sha256=manifest(root/'source'),physics_source_sha256=manifest(root/'physics_source'),
        reference_public_condition_hashes={str(p):sha(p) for p in public},
        original_dataset_excluded=True,warm_start=False,physical_episodes=108,
        simulation_python=sys.executable,fitting_python=str(ROOT.parents[2]/'.venv-rl/bin/python'),
        runtime=str(ROOT/'outputs/baseline_local_rl_20261009/runtime'),
        resources=dict(workers=1,threads=1,memory_max_bytes=3*1024**3,swap_max_bytes=0),
        spt='Whole108 matrix global minimum Task AND Strict completion time; failures0; no successes=>T_refNA',
        comfort=dict(threshold_nm=[43.5]*4+[6]*3,human_force_threshold_n=.05,denominator='actual contact dt'),
        limitations=['Equal hyperparameter candidate count, not equal FLOPs or parameter count.',
                     '24 training and6 validation identities are a small positive-only narrow-distribution dataset.',
                     'Finite32k neural budget is not a convergence guarantee; report full training loss and failures.',
                     'No old checkpoint and no runtime teacher. Prior researcher exposure cannot be erased.'])
    write(root/'REGISTRATION.json',registration)
    write(root/'execution.json',dict(status='prepared',prepared_utc=now(),registration_sha256=sha(root/'REGISTRATION.json'),
                                     fits=[],evaluation=[],expected_fit_processes=75,expected_hyperparameter_candidates=108))
    print(json.dumps(dict(root=str(root),dataset_sha256=registration['data_sha256'],registration_sha256=sha(root/'REGISTRATION.json'))))


def child(command, log, env, lock_fd):
    with log.open('x') as stream:
        result = subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,env=env,pass_fds=(lock_fd,))
    require(result.returncode == 0, f'Child failed rc={result.returncode}: {log}; original outputs preserved')


def select_models(root,state):
    selected = []
    for seed in SEEDS:
        for family in ['esn','rnn','mlp']:
            fits = [f for f in state['fits'] if f['seed']==seed and f['family']==family]
            require(len(fits)==(1 if family=='esn' else 12), 'Incomplete fit grid')
            scored = []
            for fit in fits:
                out = Path(fit['output']); m = read(out/'TRAINING_COMPLETE.json')
                score = m['selected']['holdout_mse'] if family=='esn' else m['groups']['real_identity_validation']['action_mse']
                require(np.isfinite(score), 'Nonfinite validation score')
                require(sha(out/'checkpoint.npz') == m['checkpoint_sha256'], 'Fitted checkpoint hash changed')
                require((m['training_data_sha256'] if family=='esn' else m['data_sha256']) == sha(root/'data/training_data.npz'), 'Training data mismatch')
                scored.append((score,fit['name'],out,m))
            score,name,out,m = min(scored,key=lambda x:(x[0],x[1]))
            selected.append(dict(name=f'{family}_s{seed}',family=family,seed=seed,validation_mse=score,
                selected_trial=name,checkpoint=str(out/'checkpoint.npz'),checkpoint_sha256=m['checkpoint_sha256'],
                metadata=str(out/'TRAINING_COMPLETE.json'),metadata_sha256=sha(out/'TRAINING_COMPLETE.json'),
                trainable_parameters=m['trainable_readout_coefficients'] if family=='esn' else m['trainable_parameters'],
                worker_kind='office',config={}))
    return selected


def run(root):
    reg = read(root/'REGISTRATION.json'); state = read(root/'execution.json')
    require(state['status']=='prepared','Do not duplicate or silently resume a running/failed/completed experiment')
    require(sys.executable==reg['simulation_python'],'Use the frozen simulation interpreter for the coordinator')
    require(sha(root/'REGISTRATION.json') == state['registration_sha256'],'Registration changed')
    require(sha(root/'data/training_data.npz')==reg['data_sha256'] and sha(root/'data/DATA_COMPLETE.json')==reg['metadata_sha256'],'Data changed')
    require(manifest(root/'source')==reg['source_sha256'],'Training source changed')
    require(manifest(root/'physics_source')==reg['physics_source_sha256'],'Physics source changed')
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    require(int((cg/'memory.max').read_text())<=3*1024**3 and int((cg/'memory.swap.max').read_text())==0,'Resource cgroup required')
    require(shutil.disk_usage(root).free>24*1024**3,'Require24GiB for complete evaluation plus fitting evidence')
    with (root.parent/'.local-rl-compute.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        state.update(status='training',started_utc=now(),pid=os.getpid(),host=platform.node(),python=sys.executable)
        write(root/'execution.json',state)
        env = os.environ.copy()
        env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',
                   MUJOCO_MENAGERIE_PATH=str(Path(reg['runtime'])/'menagerie'))
        (root/'learning').mkdir();(root/'logs').mkdir()
        data_args = ['--data',str(root/'data/training_data.npz'),'--metadata',str(root/'data/DATA_COMPLETE.json')]
        jobs=[]
        for seed in SEEDS:
            name=f'esn_s{seed}'
            jobs.append((name,'esn',seed,[sys.executable,str(root/'source/tools/train_paper_context_esn_20261003.py'),
                         *data_args,'--seed',str(seed),'--state-context-readout']))
        for i,(rate,decay) in enumerate(itertools.product(RATES,DECAYS)):
            for seed in SEEDS:
                for family in ['rnn','mlp']:
                    name=f'{family}_s{seed}_candidate{i:02d}'
                    jobs.append((name,family,seed,[reg['fitting_python'],str(root/'source/tools/train_office_mlp_rnn_20261002.py'),
                        *data_args,'--kind',family,'--seed',str(seed),'--target','requested','--absolute-inputs',
                        '--precision','float64','--updates',str(UPDATES),'--learning-rate',str(rate),
                        '--weight-decay',str(decay),'--action-delta-weight','0','--lr-schedule','cosine',
                        '--global-loss','--raw-slowdown-loss','--selection','final']))
        try:
            for name,family,seed,command in jobs:
                require(not (root/'STOP_REQUESTED').exists(),'Stop requested at candidate boundary; preserve unfinished grid')
                out=root/'learning'/name
                entry=dict(name=name,family=family,seed=seed,output=str(out),started_utc=now(),status='running')
                state['fits'].append(entry);state['current']=name;write(root/'execution.json',state)
                started=time.monotonic()
                child(command+['--output',str(out)],root/'logs'/f'{name}.log',env,lock.fileno())
                require(read(out/'execution.json')['status']=='complete','Trainer did not complete')
                entry.update(status='complete',ended_utc=now(),wall_seconds=time.monotonic()-started,
                             metadata_sha256=sha(out/'TRAINING_COMPLETE.json'))
                write(root/'execution.json',state)
            selected=select_models(root,state)
            write(root/'MODEL_LOCK.json',dict(status='frozen',frozen_utc=now(),protocol_sha256=reg['protocol_sha256'],
                                             selection=reg['selection'],models=selected))
            state.update(status='evaluation',model_lock_sha256=sha(root/'MODEL_LOCK.json'));write(root/'execution.json',state)
            for d in ['evaluation','configs','metrics']:(root/d).mkdir()
            rows=[]
            for condition in read(root/'CONDITIONS.json')['conditions']:
                for model in selected:
                    require(not (root/'STOP_REQUESTED').exists(),'Stop requested at full-episode boundary')
                    require(shutil.disk_usage(root).free>1024**3+192*1024**2,'Storage guard at episode boundary')
                    name=model['name']+'__'+condition['id'];out=root/'evaluation'/name
                    config=root/'configs'/f'{name}.json';write(config,{})
                    require(sha(Path(model['checkpoint']))==model['checkpoint_sha256'],'Locked model changed')
                    command=[sys.executable,str(root/'physics_source/tools/baseline_repair_worker_20261008.py'),
                        '--research-protocol',str(root/'PROTOCOL.json'),'--protocol-sha256',reg['protocol_sha256'],
                        '--research-condition',condition['id'],'--phase','acceptance','--worker-kind','office',
                        '--v6-input',str(Path(reg['runtime'])/'v6'),'--reference',str(Path(reg['runtime'])/'v6/esn_original_v2/rollout.json'),
                        '--config',str(config),'--output',str(out),'--contact-audit','--physics-dt','.00005',
                        '--checkpoint',model['checkpoint']]
                    entry=dict(name=name,started_utc=now(),status='running');state['evaluation'].append(entry)
                    state['current']=name;write(root/'execution.json',state)
                    child(command,root/'logs'/f'{name}.log',env,lock.fileno())
                    metric=root/'metrics'/f'{name}.json'
                    child([sys.executable,str(root/'physics_source/tools/paper_metrics_20261002.py'),
                           '--run',str(out),'--output',str(metric)],root/'logs'/f'{name}_metrics.log',env,lock.fileno())
                    audit=read(out/'AUDIT.json')
                    require(audit['actor_replay_performed'] and audit['action_replay_max_abs']==0 and audit['common_filter_replay_max_abs']==0,'Actor/filter audit failed')
                    rows.append(metric_row(model['name'],condition,out,metric))
                    entry.update(status='complete',ended_utc=now());write(root/'execution.json',state)
                    write(root/'PARTIAL_ROWS.json',dict(status='incomplete_not_final_ranking',rows=rows))
            require(len(rows)==108,'Incomplete physics grid')
            require(manifest(root/'source')==reg['source_sha256'] and manifest(root/'physics_source')==reg['physics_source_sha256'],'Source changed during experiment')
            summary=aggregate(rows)
            report=dict(status='complete',registration_sha256=sha(root/'REGISTRATION.json'),
                        model_lock_sha256=sha(root/'MODEL_LOCK.json'),**summary)
            # Seeds, not individual test episodes, are the replicate units.
            report['family_summary']={}
            for family in ['esn','rnn','mlp']:
                methods=[m for m in summary['methods'] if m['method'].startswith(family+'_s')]
                stats={}
                for key in ['spt_mean','peak_torque_mean_nm','human_comfort_torque_compliance_contact_time_weighted','machine_safety_violation_rate']:
                    values=[m[key] for m in methods]
                    stats[key]=dict(per_seed=values,mean=float(np.mean(values)) if all(v is not None for v in values) else None,
                                    sample_sd=float(np.std(values,ddof=1)) if all(v is not None for v in values) else None)
                for key in ['task_success','strict_success']:
                    values=[m[key]/m['episodes'] for m in methods]
                    stats[key]=dict(per_seed=values,mean=float(np.mean(values)),sample_sd=float(np.std(values,ddof=1)))
                report['family_summary'][family]=stats
            write(root/'REPORT.json',report);(root/'REPORT.md').write_text(render(report))
            state.update(status='complete',ended_utc=now(),report_sha256=sha(root/'REPORT.json'))
            write(root/'execution.json',state)
        except BaseException as e:
            state.update(status='failed_preserved',error=repr(e),ended_utc=now());write(root/'execution.json',state)
            raise


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--prepare',action='store_true')
    p.add_argument('--run',action='store_true')
    a=p.parse_args();require(a.prepare != a.run,'Choose exactly one operation')
    root=a.root.resolve()
    if a.prepare:
        existed=root.exists()
        try:prepare(root)
        except BaseException as e:
            if not existed and root.exists():
                write(root/'execution.json',dict(status='prepare_failed_preserved',error=repr(e),ended_utc=now(),fits=0,simulations=0))
            raise
    else:run(root)


if __name__=='__main__':main()
