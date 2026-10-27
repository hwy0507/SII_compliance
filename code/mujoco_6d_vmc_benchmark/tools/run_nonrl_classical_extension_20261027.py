"""Frozen six-classical x twelve-condition extension of the existing108 matrix.

No training, RL, test-based controller choice, or modification of old receipts.
Run with the frozen MuJoCo3.11 interpreter in a single-thread/3GiB/no-swap cgroup.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import numpy as np
from run_nonrl_spt_matrix_20261025 import read, sha, now, comfort_and_safety, completion_time
from nonrl_task_conditional_metrics_20261027 import aggregate, render

BASE = Path(__file__).resolve().parents[1]
ROSTER = ('admittance_boundary_06', 'admittance_boundary_07',
          'impedance_boundary_01', 'impedance_boundary_02', 'vmc_boundary_00', 'vmc_boundary_05')


def require(ok, message):
    if not ok: raise RuntimeError(message)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    os.replace(temporary, path)


def manifest(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and p.suffix in ('.py', '.json') and '__pycache__' not in p.parts}


def prepare(root):
    require(not root.exists(), 'Never overwrite an existing run')
    parent = BASE/'outputs/nonrl_new30_fair_20261026_v2'
    classical = BASE/'outputs/fair_comparison_20261013_v2'
    previous = read(parent/'execution.json')
    require(previous['status'] == 'complete', 'Existing108 incomplete')
    require(sha(parent/'REPORT.json') == previous['report_sha256'], 'Existing report changed')
    original = read(parent/'REPORT.json')
    require(len(original['rows']) == 108, 'Expected exactly108 learned episodes')
    original_registration = read(parent/'REGISTRATION.json')
    require({k:v for k,v in manifest(parent/'physics_source').items() if k.endswith('.py')} == original_registration['physics_source_sha256'],
            'Parent physics source changed')
    models = {m['name']: m for m in read(classical/'MODEL_LOCK.json')['models']}
    selected = [dict(models['historical_' + n]) for n in ROSTER]
    for m in selected:
        require(m['worker_kind'] == 'classical' and m['controller'] in ('admittance','impedance','vmc'), 'RL is excluded')
        audit = Path(m['origin_run'])/'AUDIT.json'
        require(sha(audit) == m['origin_audit_sha256'], 'Historical controller audit changed')
        require(manifest(Path(m['parameter_source'])) == read(audit)['parameter_source_sha256'],
                'Historical controller dependencies changed')
    root.mkdir(parents=True)
    for d in ('coordinator','dependencies','configs','evaluation','metrics','logs'): (root/d).mkdir()
    for name in ('CONDITIONS.json','PROTOCOL.json'):
        shutil.copy2(parent/name, root/name)
    shutil.copytree(parent/'physics_source', root/'physics_source', ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for name in ('run_nonrl_classical_extension_20261027.py','nonrl_task_conditional_metrics_20261027.py',
                 'run_nonrl_spt_matrix_20261025.py'):
        shutil.copy2(BASE/'tools'/name, root/'coordinator'/name)
    shutil.copy2(parent/'REPORT.json', root/'LEARNED_ORIGINAL_REPORT.json')
    shutil.copy2(classical/'MODEL_LOCK.json', root/'HISTORICAL_ORIGINAL_LOCK.json')
    for m in selected:
        old = Path(m['parameter_source']); new = root/'dependencies'/m['name']
        shutil.copytree(old, new, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        m.update(original_parameter_source=str(old), parameter_source=str(new), parameter_source_sha256=manifest(new))
        write(root/'configs'/f"{m['name']}.json", m['config'])
    write(root/'MODEL_LOCK.json', dict(status='frozen', frozen_utc=now(), models=selected,
          selection='Both historically locked finalists per classical family; no new tuning or test-based selection',
          historical_lock_sha256=sha(classical/'MODEL_LOCK.json')))
    registration = dict(schema='sii-nonrl-task-conditional-classical-v1', registered_utc=now(),
        benchmark=str(BASE), parent=str(parent), simulation_python=sys.executable,
        runtime=original_registration['runtime'], protocol_sha256=sha(root/'PROTOCOL.json'),
        conditions_sha256=sha(root/'CONDITIONS.json'), models_sha256=sha(root/'MODEL_LOCK.json'),
        learned_report_sha256=sha(root/'LEARNED_ORIGINAL_REPORT.json'),
        parent_model_lock_sha256=sha(parent/'MODEL_LOCK.json'),
        physics_source_sha256=manifest(root/'physics_source'), coordinator_sha256=manifest(root/'coordinator'),
        config_sha256=manifest(root/'configs'), expected_new_episodes=72, expected_total_episodes=180,
        resources=dict(workers=1,threads=1,memory_max_bytes=3*1024**3,swap_max_bytes=0),
        spt_definition='mean(T_ref/max(T,T_ref) over Task=true only); Strict not an inclusion gate; no successes=>NA',
        reference='Global minimum over Task successes across complete180; partial extensions do not produce final reference or ranking',
        comfort=dict(threshold_nm=[43.5]*4+[6]*3, force_threshold_n=.05, denominator='actual human contact dt'),
        comparison_limits=['Classical fixed historical model-based search; not matched imitation data or tuning budget.',
            'Each deterministic configuration has12 conditions, not fake three identical seed replicates.',
            'New conditions were unseen when historical parameters were locked; researchers have already inspected learned results.',
            'Classical audit covers policy trace consistency, common filter and raw physical metrics; no independent full classical actor/physics replay.',
            'Impedance retains historical native Cartesian torque backend; VMC/admittance use action adapter. This is a system comparison, not an identical-policy-interface ablation.'])
    write(root/'REGISTRATION.json', registration)
    report = dict(status='complete_learned108_reaggregation_only_classical_pending',
                  original_report_sha256=registration['learned_report_sha256'], **aggregate(original['rows']))
    write(root/'LEARNED_TASK_CONDITIONAL.json', report)
    (root/'LEARNED_TASK_CONDITIONAL.md').write_text(render(report))
    write(root/'execution.json', dict(status='prepared', prepared_utc=now(), evaluation=[],
                                     registration_sha256=sha(root/'REGISTRATION.json')))
    print(json.dumps(dict(root=str(root), status='prepared', episodes=72, learned_t_ref_s=report['t_ref_s'])))


def check_frozen(root, reg):
    for file, key in [('PROTOCOL.json','protocol_sha256'),('CONDITIONS.json','conditions_sha256'),
                      ('MODEL_LOCK.json','models_sha256'),('LEARNED_ORIGINAL_REPORT.json','learned_report_sha256')]:
        require(sha(root/file) == reg[key], file + ' changed')
    for directory in ('physics_source','coordinator','configs'):
        key = 'config_sha256' if directory == 'configs' else directory + '_sha256'
        require(manifest(root/directory) == reg[key], directory + ' changed')
    parent = Path(reg['parent'])
    require(sha(parent/'REPORT.json') == reg['learned_report_sha256'], 'Parent report changed')
    require(sha(parent/'MODEL_LOCK.json') == reg['parent_model_lock_sha256'], 'Parent model lock changed')
    for m in read(root/'MODEL_LOCK.json')['models']:
        require(manifest(Path(m['parameter_source'])) == m['parameter_source_sha256'], 'Controller source changed')


def classical_row(root, model, condition, out, metric):
    a = read(out/'AUDIT.json'); m = read(metric); execution = read(out/'execution.json')
    require(execution['status'] == 'complete', 'Worker did not finish its audit')
    require(execution['config'] == model['config'], 'Executed config differs')
    require(execution['config_sha256'] == sha(root/'configs'/f"{model['name']}.json"), 'Config hash differs')
    require(a['actor_replay_performed'] is False and a['policy_trace_consistency_max_abs'] == 0., 'Classical trace audit failed')
    require(a['common_filter_replay_max_abs'] == 0., 'Public action filter replay failed')
    require(a['parameter_source_sha256'] == model['parameter_source_sha256'], 'Executed parameter dependencies differ')
    result = read(out/'rollout.json')
    require(all(result['arguments'][k] == v for k,v in condition['overrides'].items()), 'Condition mismatch')
    expected = read(root/'PROTOCOL.json')['formal_model_sha256']
    require(a['model_sha256'] == sha(out/'rollout.mjb') == expected, 'Frozen MJB mismatch')
    for file, key in [('rollout.npz','trace_sha256'),('execution_chain.npz','chain_sha256'),
                      ('rollout_metrics/substep_metrics.npz','metrics_sha256')]:
        require(sha(out/file) == a[key], 'Worker audit hash mismatch: ' + file)
    require(a['task_success'] == m['task_success'] and a['strict_success'] == m['strict_success'], 'Gate disagreement')
    comfort = comfort_and_safety(out)
    require(np.isclose(max(comfort['peak_torque_by_joint_nm']), m['peak_torque_nm'], rtol=3e-7), 'Raw torque mismatch')
    return dict(method=model['name'], condition=condition['id'], run=str(out),
        task_success=m['task_success'], strict_success=m['strict_success'], completion_time_s=completion_time(out),
        duration_s=m['duration_s'], peak_torque_nm=m['peak_torque_nm'], comfort=comfort,
        rmse_mm=a['rmse_mm'], peak_speed_mps=a['peak_speed_mps'], abort_reason=a['abort_reason'], final_stage=a['stage'],
        actor_replay_performed=False, policy_trace_consistency_max_abs=0., common_filter_replay_max_abs=0.,
        metric_sha256=sha(metric), audit_sha256=sha(out/'AUDIT.json'), trace_sha256=a['trace_sha256'],
        model_sha256=expected, execution_sha256=sha(out/'execution.json'), chain_sha256=a['chain_sha256'],
        substep_metrics_sha256=a['metrics_sha256'], research_substeps_sha256=sha(out/'research_substeps.npz'))


def run(root):
    reg = read(root/'REGISTRATION.json'); state = read(root/'execution.json')
    require(state['status'] == 'prepared', 'Refuse duplicate dispatch or silent resume')
    require(sha(root/'REGISTRATION.json') == state['registration_sha256'], 'Registration changed')
    require(sys.executable == reg['simulation_python'], 'Wrong frozen interpreter')
    check_frozen(root, reg)
    cg = Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    require(int((cg/'memory.max').read_text()) <= 3*1024**3 and int((cg/'memory.swap.max').read_text()) == 0,
            'Requires3GiB/no-swap cgroup')
    require(shutil.disk_usage(root).free > 32*1024**3, 'Requires32GiB available storage')
    models = read(root/'MODEL_LOCK.json')['models']; conditions = read(root/'CONDITIONS.json')['conditions']
    require(len(models) == 6 and len(conditions) == 12, 'Unexpected grid')
    env = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
               PYTHONDONTWRITEBYTECODE='1', MUJOCO_MENAGERIE_PATH=str(Path(reg['runtime'])/'menagerie'))
    with (root.parent/'.local-rl-compute.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state.update(status='running', pid=os.getpid(), host=platform.node(), started_utc=now())
        write(root/'execution.json', state)
        rows=[]
        def child(command, log):
            with log.open('x') as stream:
                rc = subprocess.run(command, env=env, stdout=stream, stderr=subprocess.STDOUT,
                                    pass_fds=(lock.fileno(),)).returncode
            require(rc == 0, f'Child failed rc={rc}; preserved {log}')
        try:
            for condition in conditions:
                for model in models:
                    if (root/'STOP_REQUESTED').exists():
                        state.update(status='stopped_at_episode_boundary', ended_utc=now())
                        write(root/'execution.json', state); return
                    require(shutil.disk_usage(root).free > 4*1024**3, 'Disk reserve reached')
                    name = model['name'] + '__' + condition['id']; out = root/'evaluation'/name
                    command = [sys.executable, str(root/'physics_source/tools/baseline_repair_worker_20261008.py'),
                        '--research-protocol', str(root/'PROTOCOL.json'), '--protocol-sha256', reg['protocol_sha256'],
                        '--research-condition', condition['id'], '--phase','acceptance','--worker-kind','classical',
                        '--v6-input', str(Path(reg['runtime'])/'v6'),
                        '--reference', str(Path(reg['runtime'])/'v6/esn_original_v2/rollout.json'),
                        '--config',str(root/'configs'/f"{model['name']}.json"), '--output',str(out),
                        '--contact-audit','--physics-dt','.00005', '--parameter-source',model['parameter_source'],
                        '--controller',model['controller']]
                    entry=dict(name=name,status='running',started_utc=now(),command=command)
                    state['evaluation'].append(entry); state['current']=name; write(root/'execution.json',state)
                    started=time.monotonic()
                    child(command,root/'logs'/f'{name}.log')
                    metric = root/'metrics'/f'{name}.json'
                    child([sys.executable,str(root/'physics_source/tools/paper_metrics_20261002.py'),
                           '--run',str(out),'--output',str(metric)],root/'logs'/f'{name}_metrics.log')
                    rows.append(classical_row(root,model,condition,out,metric))
                    entry.update(status='complete',ended_utc=now(),wall_seconds=time.monotonic()-started)
                    write(root/'PARTIAL_ROWS.json',dict(status='incomplete_no_final_reference_or_ranking',rows=rows))
                    state['completed']=len(rows);write(root/'execution.json',state)
                    (root/'PROGRESS.md').write_text(f'# Classical extension\n\n{len(rows)}/72 audited episodes; updated {now()}.\n\nFinal common reference/comparison pending full72.\n')
            require(len(rows) == 72, 'Incomplete grid')
            check_frozen(root, reg)
            report = dict(status='complete180_task_conditional', registration_sha256=sha(root/'REGISTRATION.json'),
                          audit_limitations=reg['comparison_limits'],
                          **aggregate(read(root/'LEARNED_ORIGINAL_REPORT.json')['rows'] + rows))
            write(root/'REPORT.json',report); (root/'REPORT.md').write_text(render(report))
            state.update(status='complete',ended_utc=now(),report_sha256=sha(root/'REPORT.json'))
            write(root/'execution.json',state)
        except BaseException as e:
            state.update(status='failed_preserved',error=repr(e),ended_utc=now())
            write(root/'execution.json',state)
            raise


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',required=True,type=Path)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare',action='store_true'); mode.add_argument('--run',action='store_true')
    args=parser.parse_args()
    (prepare if args.prepare else run)(args.root.resolve())
