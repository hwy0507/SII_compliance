"""One-shot local campaign: audited baseline first, then real teacher data and students.

No scheduler, server compute, sealed identities, online teacher, or gate changes.
The coordinator alone owns the global simulation lock; workers never acquire it.
"""
import argparse
import copy
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
import os
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
from research72_protocol_20261003 import sample
from research72_register_controller_search_20261003 import lhs

ROOT = Path(__file__).resolve().parents[1]
START = '2026-10-12T13:28:00+00:00'
SEEDS = (2026101201, 2026101202, 2026101203)
FAMILIES = ('esn', 'matched_rnn', 'matched_mlp', 'ordinary_rnn', 'ordinary_mlp')


def require(value, message):
    if not value:
        raise ValueError(message)


def predecessor_ready(state):
    if state['status'] == 'running':
        return False
    require(state['status'] == 'complete_review_required', 'Baseline failed/stopped; do not dispatch teacher')
    require(state['verified_rows'] == 168 and state['new_episodes_completed'] == 64,
            'Baseline completion counts differ')
    return True


def qualified(a):
    return bool(a['full_horizon'] and a['task_success'] and a['strict_success'])


def pareto(rows):
    """Minimize both metrics after full task/strict feasibility on all search IDs."""
    eligible = [r for r in rows if r['qualified'] == r['expected']]
    def dominates(a, b):
        return all(a[k] <= b[k] for k in ('rmse_mm', 'peak_torque_nm')) and any(
            a[k] < b[k] for k in ('rmse_mm', 'peak_torque_nm'))
    return [r for r in eligible if not any(dominates(s, r) for s in eligible)]


def prepare(out, baseline, old_data):
    require(platform.node() == 'airpig', 'Local computation only')
    require(not out.exists(), 'Never overwrite a run')
    br = read(baseline/'REGISTRATION.json')
    parent = Path(br['parent']); pp = read(parent/'PROTOCOL.json')
    require(hashes(baseline/'source') == read(baseline/'SOURCE_HASHES.json'), 'Baseline source changed')
    old_meta = read(old_data/'DATA_COMPLETE.json')
    require(sha(old_data/'training_data.npz') == old_meta['training_data_sha256'], 'Historical dataset changed')
    teacher = next(c for c in read(baseline/'REFERENCE_MODELS.json')['candidates'] if c['family'] == 'enhanced_teacher')
    require(teacher['config'] == old_meta['teacher_selection_receipt']['candidate']['config'], 'Historical teacher lineage differs')
    public_archive=ROOT/'docs/evidence/research72_20261003'
    require(sha(public_archive/'CONDITIONS.json')==read(public_archive/'PROTOCOL.json')['condition_file_sha256'], 'Historical public conditions changed')
    public = [read(parent/'CONDITIONS.json'), read(public_archive/'CONDITIONS.json')]
    out.mkdir(parents=True)
    source = out/'source'
    shutil.copytree(baseline/'source', source, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in (Path(__file__).name, 'audit_local_paired_comparison_20261012.py'):
        shutil.copy2(ROOT/'tools'/name, source/'tools'/name)
    # New training identities within the existing registered disturbance ranges.
    # Never read the sealed set. Explicitly avoid every public historical identity.
    known = {json.dumps(c['overrides'], sort_keys=True) for p in public for c in p['conditions']}
    rows = sample(202610121528, [('train', 66), ('imitation_validation', 16)])
    for c in rows:
        c['id'] = 'expanded_' + c['id']
        require(json.dumps(c['overrides'], sort_keys=True) not in known, 'Public condition overlap')
    write(out/'CONDITIONS.json', dict(conditions=rows))
    search_ids = [c['id'] for c in rows if c['role'] == 'train'][:2]
    train = [c['id'] for c in rows if c['role'] == 'train'][2:]
    val = [c['id'] for c in rows if c['role'] == 'imitation_validation']
    # Fixed prefix remains balanced if the collection wall-time limit is reached.
    order = [x for i in range(16) for x in [val[i], *train[4*i:4*i+4]]]
    keys = ['threshold_n', 'attack_s', 'release_s', 'offset_m', 'gain_per_s', 'velocity_mps', 'progress_distance_m']
    bounds = [(.25, 1.), (.06, .24), (.5, 1.5), (.025, .045), (2.5, 5.5), (.08, .16), (.012, .04)]
    candidates = [dict(name='teacher_center', config=teacher['config'])]
    for i, values in enumerate(lhs(202610121529, bounds, 5)):
        config = copy.deepcopy(teacher['config']); config['recovery'].update(dict(zip(keys, values)))
        candidates.append(dict(name=f'teacher_lhs_{i}', config=config))
    write(out/'TEACHERS.json', dict(candidates=candidates, keys=keys, bounds=bounds, search_ids=search_ids))
    end = datetime.fromisoformat(START) + timedelta(hours=15)
    write(out/'PROTOCOL.json', dict(schema='sii-research72-v1',
        condition_file_sha256=sha(out/'CONDITIONS.json'), physics_dt_s=pp['physics_dt_s'],
        formal_model_sha256=pp['formal_model_sha256'], source_base_commit=pp['source_base_commit'], runtime=pp['runtime'],
        authorization_start_utc=START, dispatch_deadline_utc=end.isoformat()))
    write(out/'SOURCE_HASHES.json', hashes(source))
    write(out/'REGISTRATION.json', dict(schema='sii-teacher-student-local-15h-v1', registered_utc=now(),
        authorization_start_utc=START, dispatch_deadline_utc=end.isoformat(),
        time_basis='Conservative 21:28 CST Oct12 user authorization, inclusive of baseline wait and setup; 15h total.',
        collection_deadline_utc=(end-timedelta(hours=4.5)).isoformat(),
        baseline=str(baseline), baseline_registration_sha256=sha(baseline/'REGISTRATION.json'),
        parent=str(parent), parent_protocol_sha256=sha(parent/'PROTOCOL.json'),
        source_manifest_sha256=sha(out/'SOURCE_HASHES.json'), protocol_sha256=sha(out/'PROTOCOL.json'),
        teacher_manifest_sha256=sha(out/'TEACHERS.json'), old_data=str(old_data),
        old_data_sha256=old_meta['training_data_sha256'], old_metadata_sha256=sha(old_data/'DATA_COMPLETE.json'),
        repository=str(ROOT.parents[1]), simulation_python=sys.executable,
        fitting_python=str(ROOT.parents[2]/'.venv-rl/bin/python'),
        compute_host='airpig', server_compute=False, simulations=1, threads=1, memory_max_bytes=3*1024**3,
        search_episodes=12, collection_maximum=80, collection_order=order,
        selection='Full task/strict on both training search identities; Pareto RMSE/peak torque, choose minimum RMSE then torque then name. Peak speed is reported and original safety gates retained. If none qualify, retain historical center, explicitly failed new search.',
        data='New collection uses one frozen teacher. Append the previous25 real demonstrations under their original identity splits; no relabeling. If teacher changed, disclose the two-teacher mixture and do not call this a pure data-volume ablation. Search traces retained but not student labels.',
        qualification='Only unchanged task AND strict AND full55s. Retain all failed raw traces and rejection ledger. At least8 new train/2 new validation identities before any new fitting.',
        families=list(FAMILIES), seeds=list(SEEDS), width=128, neural_updates=4000,
        neural_learning_rates=[.00001, .0001, .001],
        learning='ESN12 ridge/reservoir candidates per seed; matched parents use same-data ESN or memoryless. Neural3 rates x4000 updates per seed; choose rate by mean validation action MSE across all3 seeds. Report unequal compute and parameter counts; no closed-loop selection.',
        evaluation='Five families, predeclared first seed2026101201, all8 existing baseline development conditions, formal dt5e-5.40 new rollouts; other seeds offline only within this window. Not blind generalization or multi-seed closed-loop proof.',
        no_new_dispatch_after_deadline=True, sealed_reads=0, unchanged=['geometry', 'task/strict gates', 'canonical48 allowed proprioception', 'actuator limits', 'public action filter']))
    print(json.dumps(dict(out=str(out), registration_sha256=sha(out/'REGISTRATION.json'), deadline=end.isoformat())))


def build_data(out):
    """Append actual new trajectories, never oracle/counterfactual targets."""
    import numpy as np
    from research72_build_demonstrations_20261003 import filtered_labels
    reg = read(out/'REGISTRATION.json'); old = Path(reg['old_data'])
    require(sha(old/'training_data.npz') == reg['old_data_sha256'], 'Historical dataset changed')
    require(sha(old/'DATA_COMPLETE.json') == reg['old_metadata_sha256'], 'Historical metadata changed')
    meta = read(old/'DATA_COMPLETE.json'); lineage = copy.deepcopy(meta['lineage'])
    with np.load(old/'training_data.npz', allow_pickle=False) as z:
        arrays = {k: [z[k].copy()] for k in z.files}
    for entry in lineage:
        entry['teacher_config_sha256'] = meta['teacher_config_sha256']
        entry['historical_dataset_sha256'] = reg['old_data_sha256']
    choice = read(out/'TEACHER_CHOICE.json'); config = choice['selected']['config']
    conditions = {c['id']: c for c in read(out/'CONDITIONS.json')['conditions']}
    ledger = []
    for cid in reg['collection_order']:
        run = out/'collection'/cid
        if not (run/'AUDIT.json').exists():
            ledger.append(dict(condition_id=cid, included=False, reason='not_dispatched_or_unfinished'))
            continue
        audit = read(run/'AUDIT.json'); e = read(run/'execution.json'); c = conditions[cid]
        require(e['status'] == 'complete', 'Unfinished collection')
        for file, key in [('rollout.npz', 'trace_sha256'), ('execution_chain.npz', 'chain_sha256'),
                          ('rollout_metrics/substep_metrics.npz', 'metrics_sha256')]:
            require(sha(run/file) == audit[key], 'Collection evidence changed: '+file)
        require(e['runtime_provenance']['research_condition'] == c, 'Collection condition changed')
        require(e['runtime_provenance']['research_protocol_sha256'] == reg['protocol_sha256'], 'Role lineage changed')
        require(read(run/'config.json') == config, 'Teacher switched during collection')
        include = qualified(audit)
        ledger.append(dict(condition_id=cid, role=c['role'], included=include, run=str(run),
            task=audit['task_success'], strict=audit['strict_success'], full_horizon=audit['full_horizon'],
            reason='qualified' if include else 'original_task_strict_full_horizon_failed', trace_sha256=audit['trace_sha256']))
        if not include:
            continue
        with np.load(run/'rollout.npz', allow_pickle=False) as z:
            obs = z['observation'].copy(); requested = z['applied_action'].copy()
        with np.load(run/'execution_chain.npz', allow_pickle=False) as z:
            chain = {k: z[k].copy() for k in z.files}
        require(obs.shape == (1375,48) and requested.shape == (1375,7), 'Incomplete demonstration')
        raw, filtered = filtered_labels(obs, config)
        np.testing.assert_allclose(raw, requested, rtol=0, atol=1e-10)
        np.testing.assert_array_equal(requested, chain['requested_action'])
        np.testing.assert_allclose(filtered, chain['filtered_action'], rtol=0, atol=1e-12)
        n = len(obs); eid = len(lineage)
        values = dict(observation=obs, episode=np.full(n,eid,np.int32), train=np.full(n,c['role']=='train',bool),
            importance=np.ones(n), requested_teacher_action=requested, filtered_teacher_action=chain['filtered_action'],
            clipped_teacher_action=chain['clipped_action'], executed_yield_twist=chain['yield_twist'],
            executed_wbc_scale=chain['wbc_scale'], physical_execution=np.ones(n,bool))
        require(set(values) == set(arrays), 'Dataset contract changed')
        for key, value in values.items():
            require(np.isfinite(value).all(), 'Nonfinite label'); arrays[key].append(value)
        lineage.append(dict(episode=eid, condition_id=cid, data_role=c['role'], path=str(run/'rollout.npz'),
            sha256=audit['trace_sha256'], chain_sha256=audit['chain_sha256'], teacher_config_sha256=sha(run/'config.json'),
            actual_execution_labels=True, counterfactual_relabel=False, synthetic=False, task_success=True, strict_success=True,
            physics_dt_s=.00005, execution_sha256=sha(run/'execution.json')))
    dest = out/'data'; dest.mkdir(exist_ok=False)
    write(dest/'QUALIFICATION_LEDGER.json', ledger)
    counts = {role: sum(r.get('role') == role and r['included'] for r in ledger) for role in ('train','imitation_validation')}
    require(counts['train'] >= 8 and counts['imitation_validation'] >= 2, 'Insufficient new qualified identities; no substitute labels')
    combined = {k: np.concatenate(v) for k,v in arrays.items()}
    require(not set(combined['episode'][combined['train']]) & set(combined['episode'][~combined['train']]), 'Identity leakage')
    require(len({x['condition_id'] for x in lineage}) == len(lineage), 'Duplicate identity in data')
    np.savez_compressed(dest/'training_data.npz', **combined)
    write(dest/'DATA_COMPLETE.json', dict(completed_utc=now(), training_data_sha256=sha(dest/'training_data.npz'),
        lineage=lineage, all_real_execution=True, position_error_context=True, protocol_sha256=reg['protocol_sha256'],
        episodes=len(lineage), frames=len(combined['episode']), new_qualified=counts,
        training_identities=sum(x['data_role']=='train' for x in lineage),
        validation_identities=sum(x['data_role']=='imitation_validation' for x in lineage),
        old_dataset_sha256=reg['old_data_sha256'], actual_requested_labels_preserved=True, actual_filter_replay_verified=True,
        teacher_mixture=choice['selected']['config'] != meta['teacher_selection_receipt']['candidate']['config'],
        selection_split='Whole preassigned train/validation identities; no development or final labels',
        limitations='Positive demonstrations only; failures retained. Existing local disturbance ranges, no broad-world claim. Multiple teacher policies if selected config differs; no teacher identity is an actor input.'))


class Campaign:
    def __init__(self, out):
        self.out = out; self.reg = read(out/'REGISTRATION.json'); self.source = out/'source'
        self.baseline = Path(self.reg['baseline']); self.parent = Path(self.reg['parent'])
        self.protocol = read(out/'PROTOCOL.json'); self.env = environment(self.protocol)
        self.deadline = datetime.fromisoformat(self.reg['dispatch_deadline_utc'])
        self.state = read(out/'execution.json') if (out/'execution.json').exists() else dict(
            status='waiting_for_baseline', started_utc=now(), jobs=[], server_compute=False, final_test_reads=0)
        self.lock = None

    def save(self, **kwargs):
        self.state.update(kwargs, updated_utc=now()); write(self.out/'execution.json', self.state)

    def check(self, cutoff=None):
        require(datetime.now(timezone.utc) < (cutoff or self.deadline), 'Dispatch deadline reached')
        require(not (self.out/'STOP_REQUESTED').exists(), 'Stop requested at boundary')

    def job(self, name, command, maximum=1800, cutoff=None, dispatch=True):
        receipt = self.out/'receipts'/(name+'.json')
        if receipt.exists():
            r = read(receipt)
            require(r['status']=='complete' and r['command']==command, 'Incomplete/changed attempt preserved: '+name)
            require(all(Path(p).is_file() and sha(p)==h for p,h in r.get('products',{}).items()), 'Completed product changed')
            return
        if dispatch:
            self.check(cutoff)
        require(shutil.disk_usage(self.out).free > 35*1024**3, 'Disk reserve')
        available = int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))
        require(available >= 4*1024**2, 'Available memory below4GiB; preserve job rather than OOM')
        unit = 'sii-ts15-'+hashlib.sha256((str(self.out)+name).encode()).hexdigest()[:16]
        argv = ['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit,
                '--property=MemoryMax=3G','--property=MemorySwapMax=0','--property=TasksMax=256',
                '--property=RuntimeMaxSec='+str(maximum), '--property=CPUAffinity=1,6',
                '--working-directory='+str(self.source)]
        argv += ['--setenv='+k+'='+v for k,v in self.env.items()] + command
        r = dict(status='running', command=command, managed_command=argv, started_utc=now(), unit=unit)
        write(receipt,r); self.save(active=dict(name=name,unit=unit,started_utc=now()))
        with (self.out/'receipts'/(name+'.log')).open('x') as log:
            rc = subprocess.run(argv, stdout=log, stderr=subprocess.STDOUT).returncode
        r.update(status='complete' if rc==0 else 'failed_preserved',returncode=rc,ended_utc=now())
        write(receipt,r); self.save(active=None)
        require(rc==0, 'Child failed: '+name)

    def products(self, name, paths):
        p = self.out/'receipts'/(name+'.json'); r=read(p)
        r['products'] = {str(p):sha(p) for p in paths};write(p,r)

    def evaluate(self, name, cid, config, dest, checkpoint=None, student=False):
        config_path = self.out/'configs'/(name+'.json')
        if config_path.exists(): require(read(config_path)==config,'Config changed')
        else: write(config_path,config)
        protocol_path = self.parent/'PROTOCOL.json' if student else self.out/'PROTOCOL.json'
        script = 'baseline_repair_worker_20261008.py' if student else 'research72_worker_20261003.py'
        command = [sys.executable,str(self.source/'tools'/script),'--research-protocol',str(protocol_path),
                   '--protocol-sha256',sha(protocol_path),'--research-condition',cid]
        if student: command += ['--phase','development']
        runtime = Path(self.protocol['runtime'])
        command += ['--v6-input',str(runtime/'v6'),'--reference',str(runtime/'v6/esn_original_v2/rollout.json'),
                    '--config',str(config_path),'--output',str(dest),'--contact-audit','--physics-dt','.00005']
        if checkpoint: command += ['--checkpoint',str(checkpoint)]
        self.job(name,command)
        a = read(dest/'AUDIT.json'); e=read(dest/'execution.json')
        require(e['status']=='complete' and a['model_sha256']==self.protocol['formal_model_sha256'], 'Invalid physical receipt')
        require(a['common_filter_replay_max_abs']==0 and a['action_replay_max_abs']<=1e-10, 'Action/filter replay failed')
        require(a['reservoir_replay_max_abs'] is None or a['reservoir_replay_max_abs']<=1e-10, 'State replay failed')
        if checkpoint:require(e['checkpoint_sha256']==sha(checkpoint),'Executed checkpoint changed')
        self.products(name,[dest/'AUDIT.json',dest/'rollout.npz',dest/'execution_chain.npz',dest/'execution.json'])
        metric = self.out/'metrics'/(name+'.json')
        # Audits finish even if the dispatch cutoff passed during the episode.
        self.job(name+'_metrics',[sys.executable,str(self.source/'tools/paper_metrics_20261002.py'),
            '--run',str(dest),'--output',str(metric)],dispatch=False)
        m=read(metric)
        from audit_local_paired_comparison_20261012 import verify_values
        verify_values(a,m);self.products(name+'_metrics',[metric])
        return m

    def search(self):
        path=self.out/'TEACHER_CHOICE.json'
        if path.exists():return read(path)
        spec=read(self.out/'TEACHERS.json');rows=[]
        self.save(status='teacher_search')
        for candidate in spec['candidates']:
            metrics=[]
            for cid in spec['search_ids']:
                name=candidate['name']+'__'+cid
                metrics.append(self.evaluate(name,cid,candidate['config'],self.out/'search'/name))
            rows.append(dict(candidate=candidate, expected=len(metrics),qualified=sum(qualified(m) for m in metrics),
                rmse_mm=statistics.mean(m['rmse_mm'] for m in metrics),
                peak_torque_nm=statistics.mean(m['peak_torque_nm'] for m in metrics),
                peak_speed_mps=max(m['peak_speed_mps'] for m in metrics),metrics=metrics))
            write(self.out/'SEARCH_RESULTS.json',dict(rows=rows))
        frontier=pareto(rows)
        selected=min(frontier,key=lambda r:(r['rmse_mm'],r['peak_torque_nm'],r['candidate']['name']))['candidate'] if frontier else spec['candidates'][0]
        choice=dict(created_utc=now(), selected=selected,pareto_candidates=[r['candidate']['name'] for r in frontier],
            search_success=bool(frontier),fallback=not bool(frontier),search_results_sha256=sha(self.out/'SEARCH_RESULTS.json'),
            warning='Search uses two training identities; no robustness claim. All candidates and failed attempts retained. Historical center fallback is not search success.')
        write(path,choice);return choice

    def collect(self,choice):
        self.save(status='collecting')
        cutoff=datetime.fromisoformat(self.reg['collection_deadline_utc'])
        for cid in self.reg['collection_order']:
            receipt=self.out/'receipts'/('collect_'+cid+'.json')
            if not receipt.exists() and datetime.now(timezone.utc)>=cutoff:break
            self.evaluate('collect_'+cid,cid,choice['selected']['config'],self.out/'collection'/cid)
            self.save(collection_completed=sum((self.out/'collection'/c/'AUDIT.json').exists() for c in self.reg['collection_order']))
        if not (self.out/'data/DATA_COMPLETE.json').exists():
            self.job('export_data',[sys.executable,str(self.source/'tools'/Path(__file__).name),'build-data','--out',str(self.out)])
            self.products('export_data',[self.out/'data/DATA_COMPLETE.json',self.out/'data/training_data.npz'])

    def train(self):
        self.save(status='training'); data=self.out/'data';rows=[]
        def fit(name,script,extra,seed,family,rate=None):
            dest=self.out/'learning'/name
            command=[self.reg['fitting_python'],str(self.source/'tools'/script),'--data',str(data/'training_data.npz'),
                '--metadata',str(data/'DATA_COMPLETE.json'),'--output',str(dest),'--seed',str(seed),*extra]
            self.job('fit_'+name,command,maximum=1800)
            meta=read(dest/'TRAINING_COMPLETE.json')
            require(meta.get('training_data_sha256',meta.get('data_sha256'))==sha(data/'training_data.npz'), 'Unequal training data')
            cp=dest/'checkpoint.npz';require(sha(cp)==meta['checkpoint_sha256'],'Training checkpoint changed')
            self.products('fit_'+name,[cp,dest/'TRAINING_COMPLETE.json'])
            # Compare exported, episode-reset predictions using the same loss for every family.
            import numpy as np
            with np.load(data/'training_data.npz') as z:
                target=z['requested_teacher_action']; mask=~z['train']
            with np.load(dest/'exported_replay.npz') as z: prediction=z['prediction']
            mse=float(np.mean((target[mask]-prediction[mask])**2))
            with np.load(cp) as z:
                stored={k:int(z[k].size) for k in z.files if z[k].dtype.kind=='f'}
            learned=meta.get('trainable_readout_coefficients',meta.get('trainable_parameters'))
            row=dict(name=name,family=family,seed=seed,rate=rate,validation_mse=mse,
                checkpoint=str(cp),checkpoint_sha256=sha(cp),training_metadata_sha256=sha(dest/'TRAINING_COMPLETE.json'),
                trainable_parameters=learned,stored_float_scalars=sum(stored.values()),stored_arrays=stored,
                selected_update=meta.get('selected_update'),training_receipt=str(self.out/'receipts'/('fit_'+name+'.json')))
            rows.append(row);write(self.out/'TRAINING_RESULTS.json',dict(rows=rows))
            return dest
        for seed in SEEDS:
            esn=fit(f'esn_{seed}','train_paper_context_esn_20261003.py',['--state-context-readout'],seed,'esn')
            memoryless=fit(f'memoryless_{seed}','train_paper_context_esn_20261003.py',
                          ['--state-context-readout','--memory-reset'],seed,'memoryless')
            for family in FAMILIES[1:]:
                kind=family.split('_')[-1]
                for lr in self.reg['neural_learning_rates']:
                    extra=['--kind',kind,'--updates',str(self.reg['neural_updates']),'--learning-rate',str(lr)]
                    if family.startswith('matched'):
                        parent=esn if kind=='rnn' else memoryless
                        extra+=['--checkpoint',str(parent/'checkpoint.npz'),'--parent-metadata',str(parent/'TRAINING_COMPLETE.json'),'--integral-weight','0']
                        script='train_paper_feature_matched_network_20261003.py'
                    else:
                        extra+=['--target','requested','--absolute-inputs','--precision','float64','--drift-weight','0']
                        script='train_office_mlp_rnn_20261002.py'
                    fit(f'{family}_{seed}_lr{lr}',script,extra,seed,family,lr)
        selected=[]
        for family in FAMILIES:
            candidates=[r for r in rows if r['family']==family]
            if family!='esn':
                rates=self.reg['neural_learning_rates']
                best=min(rates,key=lambda lr:(statistics.mean(r['validation_mse'] for r in candidates if r['rate']==lr),lr))
                candidates=[r for r in candidates if r['rate']==best]
            require(len(candidates)==3,'Missing training seed')
            selected.extend(candidates)
        write(self.out/'STUDENT_LOCK.json',dict(created_utc=now(),selected=selected,training_data_sha256=sha(data/'training_data.npz'),
            closed_loop_seed=SEEDS[0],rule='Rate chosen by3-seed mean identity-validation MSE; first seed fixed before training, not best seed',
            caveat='Same data, width and allowed fields; unequal parameter/feature/training compute. Matched parent fitting cost must be counted. Stored float scalars include normalizers; not all are trainable model parameters.'))

    def compare(self):
        from compare_local_baselines_20261012 import summarise, render
        self.save(status='student_evaluation')
        candidates=[r for r in read(self.out/'STUDENT_LOCK.json')['selected'] if r['seed']==SEEDS[0]]
        conditions=read(self.baseline/'CONDITIONS.json')['conditions'];rows=[]
        for c in conditions:
            for model in candidates:
                name='student_'+model['family']+'__'+c['id'];dest=self.out/'evaluation'/name
                if not (self.out/'receipts'/(name+'.json')).exists() and datetime.now(timezone.utc)>=self.deadline:
                    self.save(status='deadline_partial_comparison');return
                m=self.evaluate(name,c['id'],{},dest,Path(model['checkpoint']),student=True)
                rows.append(dict(method=model['family'],condition=c['id'],run=str(dest),metrics=m,
                    metric_sha256=sha(self.out/'metrics'/(name+'.json')),audit_sha256=sha(dest/'AUDIT.json'),
                    trace_sha256=sha(dest/'rollout.npz')))
                report=dict(updated_utc=now(),interpretation='Expanded real teacher dataset; same8 development identities and formal resolution. Predeclared one closed-loop seed;3 seeds offline. Not final heldout or proof of superiority.',
                    methods=summarise(rows,list(FAMILIES),{c['id'] for c in conditions}),rows=rows,expected_rows=40,final_test_reads=0)
                write(self.out/'STUDENT_REPORT.json',report);(self.out/'STUDENT_REPORT.md').write_text(render(report))
                self.save(student_rows=len(rows))
        require(len(rows)==40,'Incomplete student grid')
        self.job('student_final_audit',[sys.executable,str(self.source/'tools'/Path(__file__).name),
            'audit-students','--out',str(self.out)],dispatch=False)
        require(read(self.out/'STUDENT_FINAL_AUDIT.json')['status']=='passed','Final student integrity failed')
        self.save(status='complete_review_required')

    def run(self):
        require(platform.node()=='airpig','No remote computation')
        require(sha(self.out/'SOURCE_HASHES.json')==self.reg['source_manifest_sha256'] and hashes(self.source)==read(self.out/'SOURCE_HASHES.json'),'Source changed')
        require(sha(self.out/'PROTOCOL.json')==self.reg['protocol_sha256'],'Protocol changed')
        require(sha(self.out/'TEACHERS.json')==self.reg['teacher_manifest_sha256'],'Teacher plan changed')
        require(sha(self.baseline/'REGISTRATION.json')==self.reg['baseline_registration_sha256'],'Baseline registration changed')
        require(sha(self.parent/'PROTOCOL.json')==self.reg['parent_protocol_sha256'],'Baseline protocol changed')
        for folder in ('receipts','configs','metrics','search','collection','learning','evaluation'):
            (self.out/folder).mkdir(exist_ok=True)
        with (self.out/'coordinator.lock').open('a') as singleton:
            fcntl.flock(singleton,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:
                # Waiting takes only the run-specific singleton, never the global simulator lock.
                while not predecessor_ready(read(self.baseline/'execution.json')):
                    self.check(); old=read(self.baseline/'execution.json')
                    self.save(status='waiting_for_baseline',baseline_verified_rows=old['verified_rows'],baseline_active=old.get('active'))
                    time.sleep(30)
                self.save(status='baseline_final_audit')
                self.job('baseline_final_audit',[sys.executable,str(self.source/'tools/audit_local_paired_comparison_20261012.py'),
                    '--root',str(self.baseline),'--output',str(self.out/'BASELINE_FINAL_AUDIT.json')],maximum=1800)
                audit=read(self.out/'BASELINE_FINAL_AUDIT.json')
                require(audit['status']=='passed' and audit['verified_rows']==168,'Baseline audit incomplete')
                self.products('baseline_final_audit',[self.out/'BASELINE_FINAL_AUDIT.json'])
                for file in ('REPORT.json','REPORT.md'):
                    shutil.copy2(self.baseline/file,self.out/('BASELINE_'+file))
                self.save(baseline_completed_utc=now(),baseline_report_sha256=sha(self.out/'BASELINE_REPORT.json'))
                self.safe_publish('baseline_complete')
                self.lock=(self.parent.parent/'.local-rl-compute.lock').open('a')
                while True:
                    self.check()
                    try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                    except BlockingIOError:time.sleep(5)
                choice=self.search(); self.collect(choice); self.safe_publish('teacher_data_complete')
                self.train();self.compare()
            except BaseException as exc:
                self.save(status='failed_preserved',error=repr(exc));raise
            finally:
                if self.lock:self.lock.close()
                self.save(ended_utc=now())
                self.safe_publish('final')

    def safe_publish(self, stage):
        try:self.publish(stage)
        except Exception as exc:
            self.save(publication_error=dict(stage=stage,error=repr(exc),status='pending'))

    def publish(self, stage):
        """Local report and explicit archive/push outcome; publication never affects selection."""
        from archive_tool_campaign_20261002 import make
        dest=self.out/('delivery_'+stage)
        if dest.exists():return
        dest.mkdir(); evidence=dest/'evidence';evidence.mkdir()
        for name in ('REGISTRATION.json','PROTOCOL.json','CONDITIONS.json','TEACHERS.json','SOURCE_HASHES.json',
                     'execution.json','BASELINE_FINAL_AUDIT.json','BASELINE_REPORT.json','BASELINE_REPORT.md',
                     'TEACHER_CHOICE.json','SEARCH_RESULTS.json','TRAINING_RESULTS.json','STUDENT_LOCK.json',
                     'STUDENT_REPORT.json','STUDENT_REPORT.md','STUDENT_FINAL_AUDIT.json'):
            if (self.out/name).exists():shutil.copy2(self.out/name,evidence/name)
        # Snapshot is explicitly a report receipt, not a completed experiment.
        if (evidence/'execution.json').exists():
            s=read(evidence/'execution.json');s['live_campaign_status']=s['status'];s['status']='report_snapshot';write(evidence/'execution.json',s)
        shutil.copytree(self.source,evidence/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('data','learning','receipts','metrics'):
            if (self.out/folder).exists():
                shutil.copytree(self.out/folder,evidence/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        # Completed raw traces are hard-linked into the immutable local package;
        # rsync sends normal files. Reused baseline paths get an explicit mapping.
        raw=evidence/'raw';raw.mkdir();mapping=[]
        if stage=='baseline_complete':
            for i,row in enumerate(read(self.out/'BASELINE_REPORT.json')['rows']):
                source=Path(row['run']);target=raw/f'baseline_{i:03d}'
                shutil.copytree(source,target,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
                mapping.append(dict(source=str(source),archive=str(target.relative_to(evidence))))
        elif stage=='final':
            for category in ('search','collection','evaluation'):
                for source in sorted((self.out/category).iterdir()):
                    if source.is_dir():
                        target=raw/(category+'_'+source.name)
                        shutil.copytree(source,target,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
                        mapping.append(dict(source=str(source),archive=str(target.relative_to(evidence))))
        write(evidence/'RAW_PATH_MAPPING.json',mapping)
        archive=dict(status='pending',stage=stage)
        try:
            make(evidence)
            name=self.out.name+'_'+stage
            incoming='/home/arm1/sii_shared/SII_compliance/incoming/'+name
            published='/home/arm1/sii_shared/SII_compliance/runs/main/'+name+'/evidence'
            subprocess.run(['rsync','-a','--timeout=60','-e','ssh -o BatchMode=yes -o ConnectTimeout=10',
                str(evidence)+'/', 'arm1@192.168.31.70:'+incoming+'/'],check=True,timeout=1800,capture_output=True,text=True)
            result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','arm1@192.168.31.70',
                'python3',incoming+'/source/tools/archive_tool_campaign_20261002.py','--root',incoming,'--publish',published],
                check=True,timeout=1800,capture_output=True,text=True)
            archive=dict(status='verified',receipt=json.loads(result.stdout))
        except Exception as exc:archive=dict(status='pending',error=repr(exc),local=str(evidence))
        write(dest/'ARCHIVE_STATUS.json',archive)
        repo=Path(self.reg['repository'])
        report=repo/'code/mujoco_6d_vmc_benchmark/docs/TEACHER_STUDENT_15H_LIVE_20261012.md'
        try:
            require((repo/'AGENTS.md').read_text().find('UPDATE_LOG.md')>=0, 'Re-read repository publishing instructions')
            require(subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip()=='main','Publish on main only')
            require(not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=repo,text=True).strip(),'Other staged changes; defer publication')
            progress=repo/'code/mujoco_6d_vmc_benchmark/docs/ESN_VMC_JOINT_PROGRESS_20260927.md'
            weekly=repo/'code/mujoco_6d_vmc_benchmark/docs/BASELINE_WEEKLY_REPORT_20260923.md'
            paths=[str(report.relative_to(repo)),'UPDATE_LOG.md',str(progress.relative_to(repo)),str(weekly.relative_to(repo))]
            require(not subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=repo,text=True).strip(),'Publication files concurrently edited')
            subprocess.run(['git','fetch','origin','refs/heads/main:refs/remotes/origin/main'],cwd=repo,check=True,timeout=60,capture_output=True)
            require(subprocess.run(['git','merge-base','--is-ancestor','origin/main','HEAD'],cwd=repo).returncode==0,'Remote advanced; defer automatic integration')
            content=f'# 15小时本机teacher→student进展\n\n更新时间：{now()}；阶段：{stage}。\n\n'
            content+='Baseline完整表先审计，然后才采集/训练；新数据与模型结果不得当作封存泛化成绩。\n\n'
            content+='```json\n'+json.dumps(dict(execution=self.state,archive=archive),ensure_ascii=False,indent=2)+'\n```\n\n'
            if (self.out/'data/DATA_COMPLETE.json').exists():
                d=read(self.out/'data/DATA_COMPLETE.json')
                content+=f"数据：{d['training_identities']}训练身份、{d['validation_identities']}验证身份，{d['frames']}实际控制帧；teacher混合={d['teacher_mixture']}。\n\n"
            if (self.out/'STUDENT_LOCK.json').exists():
                content+='|网络|seed|可训练参数|存储浮点标量（含固定矩阵/归一化）|验证动作MSE|\n|---|---:|---:|---:|---:|\n'
                for row in read(self.out/'STUDENT_LOCK.json')['selected']:
                    content+=f"|{row['family']}|{row['seed']}|{row['trainable_parameters']}|{row['stored_float_scalars']}|{row['validation_mse']:.7g}|\n"
                content+='\n存储标量不等于可训练参数；matched包含父ESN拟合成本。闭环仅预登记首seed，另两seed仅离线。\n'
            for name in ('BASELINE_REPORT.md','STUDENT_REPORT.md'):
                if (self.out/name).exists():content+='\n'+(self.out/name).read_text()+'\n'
            report.write_text(content)
            log=repo/'UPDATE_LOG.md';text=log.read_text();heading='# 更新日志\n'
            require(text.startswith(heading),'Unexpected update log header')
            entry=f'\n## {now()} — 15小时teacher/student接续：{stage}\n\n- 实际状态 `{self.state["status"]}`；baseline审计：{(self.out/"BASELINE_FINAL_AUDIT.json").exists()}。\n- 归档状态 `{archive["status"]}`；详情见 `code/mujoco_6d_vmc_benchmark/docs/TEACHER_STUDENT_15H_LIVE_20261012.md`。\n- 单模拟器/1线程/3GiB，只本机计算；不改环境/gate、不解封保留条件，失败均保留。\n'
            log.write_text(heading+entry+text[len(heading):])
            for path in (progress,weekly):
                existing=path.read_text(); first,sep,rest=existing.partition('\n')
                path.write_text(first+'\n'+entry+'\n'+rest)
            subprocess.run(['git','add','--',*paths],cwd=repo,check=True)
            subprocess.run(['git','commit','-m','Report finite teacher/student campaign '+stage,'--',*paths],cwd=repo,check=True,timeout=60,capture_output=True)
            subprocess.run(['git','push','origin','HEAD:main'],cwd=repo,check=True,timeout=120,capture_output=True)
            head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
            remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=repo,text=True,timeout=60).split()[0]
            require(head==remote,'Remote verification differs');write(dest/'GIT_STATUS.json',dict(status='pushed_verified',commit=head))
        except Exception as exc:write(dest/'GIT_STATUS.json',dict(status='pending',error=repr(exc)))


def audit_students(out):
    """Fresh process checks every evaluation against immutable data/model/condition receipts."""
    from audit_local_paired_comparison_20261012 import verify_grid, verify_values
    from compare_local_baselines_20261012 import summarise
    reg=read(out/'REGISTRATION.json');lock=read(out/'STUDENT_LOCK.json');report=read(out/'STUDENT_REPORT.json')
    conditions=read(Path(reg['baseline'])/'CONDITIONS.json')['conditions'];ids={c['id']:c for c in conditions}
    models={r['family']:r for r in lock['selected'] if r['seed']==SEEDS[0]}
    require(sha(out/'SOURCE_HASHES.json')==reg['source_manifest_sha256'] and hashes(out/'source')==read(out/'SOURCE_HASHES.json'),'Source integrity failed')
    require(sha(out/'data/training_data.npz')==lock['training_data_sha256']==read(out/'data/DATA_COMPLETE.json')['training_data_sha256'],'Dataset changed')
    require(len(models)==5 and set(models)==set(FAMILIES),'Student roster changed')
    verify_grid(report['rows'],FAMILIES,ids)
    require(report['methods']==summarise(report['rows'],list(FAMILIES),set(ids)),'Student aggregates changed')
    for row in report['rows']:
        path=Path(row['run']);m=row['metrics'];model=models[row['method']]
        a=read(path/'AUDIT.json');e=read(path/'execution.json');detail=read(path/'rollout.json')
        require(sha(path/'AUDIT.json')==row['audit_sha256'],'Worker audit changed')
        require(sha(model['checkpoint'])==model['checkpoint_sha256']==e['checkpoint_sha256'],'Checkpoint changed')
        require(a['model_sha256']==sha(path/'rollout.mjb')==read(out/'PROTOCOL.json')['formal_model_sha256'],'MJB changed')
        require(e['status']=='complete' and e['runtime_provenance']['research_condition']==ids[row['condition']],'Identity mismatch')
        require(all(detail['arguments'][k]==v for k,v in ids[row['condition']]['overrides'].items()),'Actual disturbance changed')
        for file,key in [('rollout.npz','trace_sha256'),('rollout_metrics/substep_metrics.npz','native_metrics_sha256'),
                         ('research_substeps.npz','research_metrics_sha256'),('execution.json','execution_sha256')]:
            require(sha(path/file)==m[key],'Raw trace/metric hash changed')
        require(sha(path/'execution_chain.npz')==a['chain_sha256'],'Execution chain changed')
        require(a['actor_replay_performed'] and a['action_replay_max_abs']<=1e-10 and a['common_filter_replay_max_abs']==0,'Action/filter replay failed')
        require(a['reservoir_replay_max_abs'] is None or a['reservoir_replay_max_abs']<=1e-10,'State replay failed')
        verify_values(a,m)
    write(out/'STUDENT_FINAL_AUDIT.json',dict(status='passed',verified_rows=40,created_utc=now(),
        report_sha256=sha(out/'STUDENT_REPORT.json'),model_lock_sha256=sha(out/'STUDENT_LOCK.json'),
        dataset_sha256=lock['training_data_sha256'],final_test_reads=0,
        interpretation='Independent integrity verification of raw-substep recomputation and action/state replay; development cohort, not blind generalization.'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run','build-data','audit-students'));p.add_argument('--out',type=Path,required=True)
    p.add_argument('--baseline',type=Path);p.add_argument('--old-data',type=Path)
    a=p.parse_args();out=a.out.resolve()
    if a.mode=='prepare':prepare(out,a.baseline.resolve(),a.old_data.resolve())
    elif a.mode=='build-data':build_data(out)
    elif a.mode=='audit-students':audit_students(out)
    else:Campaign(out).run()


if __name__=='__main__':main()
