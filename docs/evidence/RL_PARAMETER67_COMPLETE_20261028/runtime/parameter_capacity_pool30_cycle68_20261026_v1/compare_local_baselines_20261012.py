"""Finite paired development comparison after the existing RL node completes.

Reuse the audited 7 RL configurations and 6 classical finalists on exactly the
same eight conditions. Evaluate the eight frozen reference methods locally.
Never read a sealed set, retrain, replace an attempt, or hold the simulation
lock while waiting for the existing owner. This is not a held-out paper result.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
from pathlib import Path
import platform
import shutil
import statistics
import subprocess
import sys
import time

from office_v7_uniform24_20261008 import read, write, sha, now
from local_rl_campaign_20261009 import hashes
from launch_rl_convergence_20261010 import environment
from report_rl_longrun_20261011 import verified_node
from monitor_classical_search_20261010 import Monitor

REFERENCE = ('esn', 'matched_rnn', 'matched_mlp', 'ordinary_rnn',
             'ordinary_mlp', 'memoryless', 'enhanced_teacher', 'nominal_zero')
TERMINAL = {'complete_review_required', 'failed_preserved', 'stopped_at_deadline', 'stopped_requested'}


def require(value, message):
    if not value:
        raise ValueError(message)


def same_conditions(a, b):
    require(len(a) == len(b) == 8, 'Expected eight development identities')
    require(len({d['id'] for d in a}) == 8, 'Duplicate identities')
    require({d['id']: d for d in a} == {d['id']: d for d in b}, 'Different conditions')
    require(all(d['role'] == 'development' for d in a), 'Development only')


def prepare(parent, classical, completion, models, out):
    require(platform.node() == 'airpig', 'Local compute only')
    require(not out.exists(), 'Preserve existing attempt')
    protocol = read(parent/'PROTOCOL.json')
    require(sha(parent/'CONDITIONS.json') == protocol['condition_file_sha256'], 'Conditions changed')
    conditions = [d for d in read(parent/'CONDITIONS.json')['conditions'] if d['role'] == 'development']
    cr = read(classical/'REGISTRATION.json')
    same_conditions(conditions, cr['conditions'])
    require(cr['frozen_model_sha256'] == protocol['formal_model_sha256'], 'Different MJB')
    require(read(classical/'execution.json')['status'] == 'complete', 'Classical search incomplete')
    require(hashes(completion/'source') == read(completion/'SOURCE_HASHES.json'), 'RL source changed')
    # The classical diagnostic wrapper is extra; all shared robot/control
    # scripts are byte-identical. Frozen fixture changes are checked per row.
    shared = {}
    for p in (completion/'source/scripts').glob('*.py'):
        other = classical/'source/scripts'/p.name
        require(other.exists() and sha(p) == sha(other), 'Physics script mismatch: '+p.name)
        shared['scripts/'+p.name] = sha(p)
    original = read(models)['candidates']
    references = [c for c in original if c['family'] in REFERENCE]
    require(len(references) == 8 and {c['family'] for c in references} == set(REFERENCE), 'Reference roster')
    out.mkdir(parents=True)
    source = out/'source'
    shutil.copytree(completion/'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in (Path(__file__).name, 'monitor_classical_search_20261010.py', 'classical_acceptance_20261010.py'):
        shutil.copy2(Path(__file__).parent/name, source/'tools'/name)
    (out/'checkpoints').mkdir()
    mappings = []
    for c in references:
        if not c.get('checkpoint'):
            continue
        remote = c['checkpoint']
        require(remote.startswith('/home/arm1/sii_shared/SII_compliance/runs/main/'), 'Unexpected checkpoint source')
        local = out/'checkpoints'/(c['family']+'.npz')
        subprocess.run(['rsync', '-a', '--timeout=30', '-e', 'ssh -o BatchMode=yes -o ConnectTimeout=10',
                        'arm1@192.168.31.70:'+remote, str(local)], check=True, timeout=120)
        require(sha(local) == c['checkpoint_sha256'], 'Downloaded checkpoint mismatch')
        mappings.append(dict(server='arm1@192.168.31.70:'+remote, local=str(local), sha256=sha(local)))
        c['checkpoint'] = str(local)
    write(out/'REFERENCE_MODELS.json', dict(candidates=references, original=str(models), original_sha256=sha(models)))
    write(out/'CHECKPOINT_MAPPING.json', mappings)
    write(out/'CONDITIONS.json', dict(conditions=conditions))
    write(out/'SOURCE_HASHES.json', hashes(source))
    stamp = datetime.now(timezone.utc)
    write(out/'REGISTRATION.json', dict(schema='sii-local-paired-development-v1', registered_utc=stamp.isoformat(),
        authority='2026-10-12 user: continue baseline construction and comparison with proposed; local compute only',
        parent=str(parent), parent_protocol_sha256=sha(parent/'PROTOCOL.json'),
        completion=str(completion), completion_registration_sha256=sha(completion/'REGISTRATION.json'),
        classical=str(classical), classical_registration_sha256=sha(classical/'REGISTRATION.json'),
        source_base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        reference_manifest_sha256=sha(out/'REFERENCE_MODELS.json'), source_manifest_sha256=sha(out/'SOURCE_HASHES.json'),
        condition_sha256=sha(out/'CONDITIONS.json'), shared_physics_scripts=shared,
        formal_model_sha256=protocol['formal_model_sha256'], physics_dt_s=protocol['physics_dt_s'], duration_s=55.,
        dispatch_deadline_utc=(stamp+timedelta(hours=14)).isoformat(),
        deadline_basis='Agent-chosen finite safety ceiling for 64 reference evaluations and audits; not a convergence target',
        new_episodes=64, reused_rl_episodes=56, reused_classical_episodes=48, expected_rows=168,
        families=16, auxiliary_rows='Two entropy configurations and three classical runners-up retained; no outcome-based dropping',
        resources=dict(host='airpig', server_compute=False, simulators=1, threads=1, memory_max_bytes=3*1024**3,
                       memory_swap_max=0, min_available_kib=4*1024**2, min_free_disk_bytes=40*1024**3),
        interpretation='Shared development cohort, not final/heldout generalization or equal training budget. No new training. Original gates unchanged.',
        final_test_reads=0))
    print('Prepared', out, sha(out/'REGISTRATION.json'), flush=True)


def ready(status):
    if status in TERMINAL:
        require(status == 'complete_review_required', 'Existing RL task failed/stopped; preserve and review')
        return True
    require(status == 'running', 'Unexpected predecessor state: '+status)
    return False


def wait_for_predecessor(completion, check, tick):
    """Deliberately has no lock argument and never acquires the compute lock."""
    while not ready(read(completion/'execution.json')['status']):
        check(); tick(); time.sleep(30)


def metric_row(method, condition, run, audit, measured, kind):
    require(measured['model_sha256'] == audit['model_sha256'], 'Metric model mismatch')
    for k in ('rmse_mm', 'peak_torque_nm', 'peak_speed_mps'):
        require(abs(measured[k]-audit[k]) < 1e-4, 'Independent metric mismatch: '+k)
    for k in ('task_success', 'strict_success', 'full_horizon'):
        require(measured[k] == audit[k], 'Independent outcome mismatch: '+k)
    return dict(method=method, condition=condition, run=str(run), kind=kind,
                audit_sha256=sha(run/'AUDIT.json'), trace_sha256=sha(run/'rollout.npz'),
                metrics=measured)


def summarise(rows, methods, identities):
    pairs = [(r['method'], r['condition']) for r in rows]
    require(len(set(pairs)) == len(pairs), 'Duplicate pair')
    require(all(m in methods and d in identities for m,d in pairs), 'Unregistered pair')
    summaries = []
    for method in methods:
        group = [r['metrics'] for r in rows if r['method'] == method]
        complete = len(group) == len(identities)
        summary=dict(method=method, evaluated=len(group), expected=len(identities), complete=complete,
            task=sum(m['task_success'] for m in group) if complete else None,
            strict=sum(m['strict_success'] for m in group) if complete else None,
            short=sum(not m['full_horizon'] for m in group),
            means={k: statistics.mean(m[k] for m in group) for k in
                   ('rmse_mm','peak_torque_nm','peak_speed_mps')} if complete else None)
        if complete and all('contact' in m and 'recovery' in m for m in group):
            summary['contacts']={}
            for event in ('ball','human','rod','unknown_edge'):
                contact=[m['contact'][event] for m in group]
                forces=[r['contact_p95_force_n'] for r in contact if r['contact_p95_force_n'] is not None]
                summary['contacts'][event]=dict(exposed=sum(r['exposure'] for r in contact),
                    mean_exposed_episode_p95_n=statistics.mean(forces) if forces else None,
                    mean_impulse_ns=statistics.mean(r['impulse_ns'] for r in contact),
                    mean_contact_duration_s=statistics.mean(r['contact_duration_s'] for r in contact))
            summary['recovery']={event:dict(exposed=sum(m['recovery'][event]['exposed'] for m in group),
                observed_recovered=sum(m['recovery'][event]['settled_rejoin_time_s'] is not None for m in group),
                censored=sum(m['recovery'][event]['right_censored'] for m in group)) for event in ('ball','human','rod')}
        summaries.append(summary)
    return summaries


def render(report):
    lines = ['# 同一八条件开发比较', '', report['interpretation'], '',
             '|方法|已评/计划|Task|Strict|RMSE mm|回合峰矩均值 Nm|回合峰速均值 m/s|早停|',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in report['methods']:
        values = [f"{m['task']}/8", f"{m['strict']}/8"]+[f'{x:.4f}' for x in m['means'].values()] if m['complete'] else ['pending']*5
        lines.append('| '+' | '.join([m['method'], f"{m['evaluated']}/8", *values, str(m['short'])])+' |')
    lines += ['', '失败均计入分母；早停的连续指标只覆盖实际时长，不与完整55秒直接判优。',
              '', '## 接触窗口柔顺指标（描述性，需同时看接触覆盖和任务成功）', '',
              '|方法|人手P95 N / 接触回合|棍P95 N / 接触回合|桌角P95 N / 接触回合|人手冲量 N·s|棍冲量 N·s|人手恢复/暴露|棍恢复/暴露|',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in report['methods']:
        if 'contacts' not in m: continue
        c=m['contacts'];r=m['recovery']
        force=lambda event: ('NA' if c[event]['mean_exposed_episode_p95_n'] is None else
                            f"{c[event]['mean_exposed_episode_p95_n']:.3f}")+f" / {c[event]['exposed']}"
        lines.append('| '+' | '.join([m['method'],*[force(k) for k in ('human','rod','unknown_edge')],
            f"{c['human']['mean_impulse_ns']:.3f}",f"{c['rod']['mean_impulse_ns']:.3f}",
            *[f"{r[k]['observed_recovered']}/{r[k]['exposed']}" for k in ('human','rod')]])+' |')
    lines += ['', 'P95列为各实际接触回合P95的均值；冲量按全部8回合实际窗口均值，非接触为真实零冲量。',
              '未观测到恢复者按既定窗口删失；未接触不作为恢复失败。此表不是相同接触轨迹的因果排名。',
              '所有逐回合接触/冲量/恢复指标保留在REPORT.json rows[].metrics；缺接触与删失不填零。',
              '经典两候选、RL两个熵附组全部展示；不能把开发调参成绩称为盲测或RL收敛。', '']
    return '\n'.join(lines)


def run(out):
    require(platform.node() == 'airpig', 'Local compute only')
    reg = read(out/'REGISTRATION.json'); parent=Path(reg['parent']); source=out/'source'
    completion=Path(reg['completion']); classical=Path(reg['classical'])
    require(not (out/'execution.json').exists(), 'Preserve existing attempt; no blind restart')
    state=dict(status='waiting_for_rl', started_utc=now(), registration_sha256=sha(out/'REGISTRATION.json'),
               new_episodes_completed=0, verified_rows=0, final_test_reads=0, server_compute=False)
    write(out/'execution.json', state)
    lock=None
    try:
        require(sha(parent/'PROTOCOL.json')==reg['parent_protocol_sha256'], 'Parent changed')
        require(sha(completion/'REGISTRATION.json')==reg['completion_registration_sha256'], 'RL registration changed')
        require(sha(classical/'REGISTRATION.json')==reg['classical_registration_sha256'], 'Classical registration changed')
        require(sha(out/'SOURCE_HASHES.json')==reg['source_manifest_sha256'] and hashes(source)==read(out/'SOURCE_HASHES.json'), 'Source changed')
        require(sha(out/'REFERENCE_MODELS.json')==reg['reference_manifest_sha256'], 'Reference models changed')
        require(sha(out/'CONDITIONS.json')==reg['condition_sha256'], 'Conditions changed')
        conditions=read(out/'CONDITIONS.json')['conditions']; ids={d['id'] for d in conditions}
        deadline=datetime.fromisoformat(reg['dispatch_deadline_utc'])
        def check():
            require(datetime.now(timezone.utc)<deadline, 'Dispatch deadline; no new work')
            require(not (out/'STOP_REQUESTED').exists(), 'Stop requested; prior evidence retained')
        # Crucially, no global simulation lock is opened while waiting.
        def tick():
            state['updated_utc']=now(); write(out/'execution.json',state)
        wait_for_predecessor(completion, check, tick)
        # The predecessor writes terminal before closing its lock; retry only
        # this release race, bounded by the same deadline. Never hold-and-wait.
        lock=(parent.parent/'.local-rl-compute.lock').open('a')
        while True:
            check()
            try: fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB); break
            except BlockingIOError: time.sleep(5)
        protocol=read(parent/'PROTOCOL.json'); env=environment(protocol)
        references=read(out/'REFERENCE_MODELS.json')['candidates']
        for c in references:
            if c.get('checkpoint'): require(sha(c['checkpoint'])==c['checkpoint_sha256'], 'Reference checkpoint changed')
        rl_matrix=read(completion/'SEVEN_METHOD_DEVELOPMENT.json')
        require(len(rl_matrix['methods'])==7 and not rl_matrix['cpu_probe_included'], 'Incomplete CUDA cohort')
        classic=Monitor(classical).snapshot(rehash=True)
        require(classic['status']=='verified_complete', 'Classical evidence not complete')
        selection=read(classical/'SELECTION.json')
        finalists=[r['candidate']['name'] for g in selection['ranked'].values() for r in g[:2]]
        methods=list(REFERENCE)+finalists+list(rl_matrix['methods'])
        require(len(methods)==21 and len(set(methods))==21, 'Full method roster')
        write(out/'MODEL_LOCK.json', dict(created_utc=now(), references=references,
            classical_finalists=finalists, rl=rl_matrix, classical_selection_sha256=sha(classical/'SELECTION.json'),
            selection='All reference models frozen before this run; both classical finalists and all seven RL configurations retained',
            conditions_sha256=reg['condition_sha256']))
        rows=[]
        def save():
            report=dict(updated_utc=now(), interpretation=reg['interpretation'], methods=summarise(rows,methods,ids),
                        rows=rows, final_test_reads=0, expected_rows=168)
            write(out/'REPORT.json',report); (out/'REPORT.md').write_text(render(report))
            state.update(updated_utc=now(),verified_rows=len(rows));write(out/'execution.json',state)
        state['status']='running'; save()
        (out/'episodes').mkdir(); (out/'analysis').mkdir()
        def managed(target, command):
            check()
            require(shutil.disk_usage(out).free>=reg['resources']['min_free_disk_bytes'], 'Disk reserve')
            available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))
            require(available>=reg['resources']['min_available_kib'], 'Insufficient available memory')
            receipt=Path(str(target)+'.execution.json')
            require(not receipt.exists() and not target.exists(), 'Never overwrite an attempt')
            unit='sii-paired-dev-'+hashlib.sha256(str(target).encode()).hexdigest()[:16]
            argv=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
                '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=TasksMax=256',
                '--property=RuntimeMaxSec=1800',
                '--property=CPUAffinity=1,6','--working-directory='+str(source)]
            argv+=['--setenv='+k+'='+v for k,v in env.items()]+command
            receipt_value=dict(status='running',command=command,managed_command=argv,started_utc=now(),unit=unit)
            write(receipt,receipt_value);state['active']=dict(target=str(target),unit=unit,started_utc=now());save()
            with Path(str(target)+'.log').open('x') as log:
                rc=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),)).returncode
            receipt_value.update(status='complete' if rc==0 else 'failed_preserved',returncode=rc,ended_utc=now())
            write(receipt,receipt_value);state['active']=None
            require(rc==0, 'Child failed: '+str(receipt))
        def analyse(method, d, path, kind):
            audit=read(path/'AUDIT.json')
            require(audit['model_sha256']==reg['formal_model_sha256']==sha(path/'rollout.mjb'), 'Different model')
            require(audit['trace_sha256']==sha(path/'rollout.npz'), 'Trace changed')
            require(audit['chain_sha256']==sha(path/'execution_chain.npz'), 'Execution chain changed')
            arguments=read(path/'rollout.json')['arguments']
            require(all(arguments[k]==v for k,v in d['overrides'].items()), 'Actual conditions changed')
            require(audit['common_filter_replay_max_abs']==0, 'Filter replay failed')
            target=out/'analysis'/(method+'__'+d['id']+'.json')
            managed(target,[sys.executable,str(source/'tools/paper_metrics_20261002.py'),'--run',str(path),'--output',str(target)])
            row=metric_row(method,d['id'],path,audit,read(target),kind)
            row.update(metric_file=str(target),metric_sha256=sha(target));rows.append(row);save()
        # Verify each reused method, then recompute its physical/contact metrics
        # from raw telemetry. This invokes no policy and adds no physics steps.
        for name,node in rl_matrix['methods'].items():
            verified_node(dict(audit=node['audit'],audit_sha256=node['audit_sha256'],steps=node['steps'],
                               scheduled_limit=node['scheduled_limit']),ids,{})
            for row in read(node['audit'])['rows']:
                path=Path(row['run'])
                require(sha(path/'AUDIT.json')==row['audit_sha256'], 'RL audit changed')
                require(sha(path/'rollout_metrics/substep_metrics.npz')==row['raw_metrics_sha256'], 'RL raw metrics changed')
                require(sha(path/'rollout.npz')==row['trace_sha256'], 'RL trace changed')
                analyse(name,next(d for d in conditions if d['id']==row['condition']),path,'reused_rl')
        for name in finalists:
            selected=[r for r in classic['rows'] if r['candidate']==name]
            require(len(selected)==8 and {r['condition'] for r in selected}==ids, 'Classical cohort mismatch')
            for r in selected:
                analyse(name,next(d for d in conditions if d['id']==r['condition']),
                        classical/(name+'__'+r['condition']),'reused_classical')
        for d in conditions:
            for c in references:
                label=c['family']+'__'+d['id'];path=out/'episodes'/label
                config=out/'episodes'/(label+'.config.json');write(config,c.get('config',{}))
                command=[sys.executable,str(source/'tools/baseline_repair_worker_20261008.py'),
                    '--research-protocol',str(parent/'PROTOCOL.json'),'--protocol-sha256',reg['parent_protocol_sha256'],
                    '--research-condition',d['id'],'--phase','development','--worker-kind','nominal' if c.get('nominal') else 'office',
                    '--v6-input',str(Path(protocol['runtime'])/'v6'),'--reference',str(Path(protocol['runtime'])/'v6/esn_original_v2/rollout.json'),
                    '--config',str(config),'--output',str(path),'--contact-audit','--physics-dt','.00005']
                if c.get('checkpoint'):command+=['--checkpoint',c['checkpoint']]
                managed(path,command)
                audit=read(path/'AUDIT.json')
                if c.get('checkpoint'):
                    require(audit['actor_replay_performed'] and audit['action_replay_max_abs']<=1e-10, 'Student replay failed')
                    require(audit['reservoir_replay_max_abs'] is None or audit['reservoir_replay_max_abs']<=1e-10, 'State replay failed')
                    require(read(path/'execution.json')['checkpoint_sha256']==c['checkpoint_sha256'], 'Executed checkpoint changed')
                state['new_episodes_completed']+=1
                analyse(c['family'],d,path,'new_reference')
        require(len(rows)==168 and state['new_episodes_completed']==64, 'Incomplete matrix')
        state['status']='complete_review_required';save()
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(out/'execution.json',state)
        if lock is not None:lock.close()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run'));p.add_argument('--out',type=Path,required=True)
    for name in ('parent','classical','completion','models'):p.add_argument('--'+name,type=Path)
    a=p.parse_args();a.out=a.out.resolve()
    if a.mode=='prepare':
        prepare(a.parent.resolve(),a.classical.resolve(),a.completion.resolve(),a.models.resolve(),a.out)
    else:run(a.out)


if __name__=='__main__':main()
