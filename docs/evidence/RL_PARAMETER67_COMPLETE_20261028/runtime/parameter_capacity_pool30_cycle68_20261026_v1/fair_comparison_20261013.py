"""One-shot local fairness correction and prospective paired audit.

No geometry/gate changes, no access to older sealed sets, no outcome-dependent
dispatch or selection. A single coordinator owns the existing simulation lock.
"""
import argparse
from datetime import datetime, timedelta, timezone
import fcntl
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
from teacher_student_15h_20261012 import Campaign, require
from research72_protocol_20261003 import sample
from compare_local_baselines_20261012 import summarise
from audit_local_paired_comparison_20261012 import verify_grid, verify_values

ROOT = Path(__file__).resolve().parents[1]
SEEDS = (2026101301, 2026101302, 2026101303)
FAMILIES = ('esn_gradient', 'rnn_scratch', 'mlp_scratch', 'esn_ridge', 'rnn_from_ridge')
RATES = (.00001, .0001, .001)
UPDATES = 8000


def prepare(out, predecessor):
    require(platform.node() == 'airpig' and not out.exists(), 'Local new run only')
    old = read(predecessor/'REGISTRATION.json'); baseline = Path(old['baseline'])
    parent = Path(old['parent']); protocol = read(parent/'PROTOCOL.json')
    audit = read(predecessor/'BASELINE_FINAL_AUDIT.json')
    require(audit['status'] == 'passed' and sha(baseline/'REPORT.json') == audit['report_sha256'], 'Baseline audit pin')
    require(hashes(predecessor/'source') == read(predecessor/'SOURCE_HASHES.json'), 'Frozen source changed')
    out.mkdir(parents=True)
    for directory in ('receipts','configs','metrics','learning','evaluation','dependencies'): (out/directory).mkdir()
    shutil.copytree(predecessor/'source', out/'source', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    for name in (Path(__file__).name, 'train_fair_students_20261013.py'):
        shutil.copy2(ROOT/'tools'/name, out/'source/tools'/name)
    shutil.copytree(predecessor/'data', out/'data')
    require(sha(out/'data/training_data.npz') == read(out/'data/DATA_COMPLETE.json')['training_data_sha256'], 'Data pin')
    # Prospective identities use the already registered distribution, not new
    # geometry. They are never passed to fitting and do not reuse an old seal.
    conditions = sample(2026101308128, [('acceptance', 8)])
    known = set()
    for path in (parent/'CONDITIONS.json', predecessor/'CONDITIONS.json',
                 ROOT/'docs/evidence/research72_20261003/CONDITIONS.json'):
        known.update(json.dumps(c['overrides'], sort_keys=True) for c in read(path)['conditions'])
    for c in conditions:
        c['id'] = 'prospective_20261013_' + c['id']
        require(json.dumps(c['overrides'], sort_keys=True) not in known, 'Public identity overlap')
    write(out/'CONDITIONS.json', dict(conditions=conditions))
    protocol.update(schema='sii-baseline-strengthening-v1', condition_file_sha256=sha(out/'CONDITIONS.json'))
    # Remove the old sealed pointer entirely; acceptance workers read only the
    # new eight records after the complete model lock has been written.
    protocol.pop('sealed_condition_sha256', None)
    write(out/'PROTOCOL.json', protocol)
    references = {r['family']:r for r in read(baseline/'REFERENCE_MODELS.json')['candidates']}
    rows = read(baseline/'REPORT.json')['rows']; roster = []
    for method in sorted({r['method'] for r in rows}):
        row = next(r for r in rows if r['method'] == method)
        run = Path(row['run']); execution = read(run/'execution.json'); prov = execution['runtime_provenance']
        spec = dict(name='historical_'+method, family=method, group='historical_system', config=execution['config'],
                    origin_run=str(run), origin_audit_sha256=sha(run/'AUDIT.json'))
        dep = out/'dependencies'/method; dep.mkdir()
        if row['kind'] == 'reused_rl':
            manifest = read(run/'ADAPTED_RL_CHECKPOINT.json')
            cp = Path(manifest['checkpoint']); shutil.copytree(cp, dep/'checkpoint')
            require(all(sha(dep/'checkpoint'/k) == h for k,h in manifest['hashes'].items()), 'RL checkpoint pin')
            training = Path(manifest['training_protocol']); shutil.copy2(training, dep/'TRAINING_PROTOCOL.json')
            require(sha(dep/'TRAINING_PROTOCOL.json') == manifest['training_protocol_sha256'], 'RL training pin')
            manifest.update(checkpoint=str(dep/'checkpoint'), training_protocol=str(dep/'TRAINING_PROTOCOL.json'))
            parameter = Path(next(k for k in prov['agent_source_sha256'] if k.endswith('/PRIORS.json'))).parent
            shutil.copytree(parameter, dep/'parameter', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            require(all(sha(dep/'parameter'/Path(k).relative_to(parameter)) == h
                        for k,h in prov['agent_source_sha256'].items()), 'RL implementation pin')
            write(dep/'CHECKPOINT_MANIFEST.json', manifest)
            spec.update(worker_kind='adapted_rl', controller=manifest['controller'], parameter_source=str(dep/'parameter'),
                        agent_checkpoint=str(dep/'checkpoint'), checkpoint_manifest=str(dep/'CHECKPOINT_MANIFEST.json'),
                        training_regime='RL without teacher demonstrations; one historical training seed; not equal-data architecture control')
        elif row['kind'] == 'reused_classical':
            parameter = Path(prov['parameter_source'])
            shutil.copytree(parameter, dep/'parameter', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            require(all(sha(dep/'parameter'/k) == h for k,h in prov['parameter_source_sha256'].items()), 'Classical law pin')
            require(prov['fixture'] == 'frozen' and not prov['diagnostic_collision_changes'], 'Non-frozen diagnostic excluded')
            spec.update(worker_kind='classical', controller=prov['controller'], parameter_source=str(dep/'parameter'),
                        training_regime='Historical finite model-based parameter search; both finalists retained')
        else:
            ref = references[method]
            spec.update(worker_kind='nominal' if ref.get('nominal') else 'office',
                        training_regime='Historical frozen reference, unequal prior training; not primary matched architecture comparison')
            if ref.get('checkpoint'):
                shutil.copy2(ref['checkpoint'], dep/'checkpoint.npz')
                require(sha(dep/'checkpoint.npz') == ref['checkpoint_sha256'], 'Reference checkpoint pin')
                spec.update(checkpoint=str(dep/'checkpoint.npz'), checkpoint_sha256=ref['checkpoint_sha256'])
            if method == 'enhanced_teacher':
                spec['training_regime'] = 'Privileged hand-designed teacher reference; excluded from proprioception-only architecture claim'
        roster.append(spec)
    require(len(roster) == 21, 'Preserve all historical configurations')
    write(out/'HISTORICAL_ROSTER.json', dict(models=roster))
    write(out/'DEPENDENCY_HASHES.json', {str(p.relative_to(out/'dependencies')):sha(p)
        for p in (out/'dependencies').rglob('*') if p.is_file()})
    write(out/'SOURCE_HASHES.json', hashes(out/'source'))
    start = datetime.now(timezone.utc)
    registration = dict(schema='sii-fair-prospective-20261013-v1', registered_utc=now(),
        authority='User: remove unfair factors and produce the fairest comparison; new scoped authorization, not extension of old15h',
        dispatch_deadline_utc=(start+timedelta(hours=48)).isoformat(),
        deadline_basis='Agent-chosen finite48h safety ceiling for39 fits and288 evaluations; finish early when grid complete',
        repository=str(ROOT.parents[1]), predecessor=str(predecessor), baseline=str(baseline), parent=str(parent),
        fitting_python=old['fitting_python'], simulation_python=old['simulation_python'],
        source_manifest_sha256=sha(out/'SOURCE_HASHES.json'), dependency_manifest_sha256=sha(out/'DEPENDENCY_HASHES.json'),
        historical_roster_sha256=sha(out/'HISTORICAL_ROSTER.json'), protocol_sha256=sha(out/'PROTOCOL.json'),
        training_data_sha256=sha(out/'data/training_data.npz'), metadata_sha256=sha(out/'data/DATA_COMPLETE.json'),
        data='Identical44train/11validation actual teacher trajectories, same two-teacher mixture for every new student; no condition/teacher ID actor input',
        seeds=SEEDS, families=FAMILIES, rates=RATES, updates=UPDATES, width=128,
        primary=['esn_gradient', 'rnn_scratch', 'mlp_scratch'], auxiliary=['esn_ridge', 'rnn_from_ridge'],
        shared='Same allowed18 fields in canonical48,156 drive features,128 units,4 time scales,state-context linear readout; shared initial matrices/readout and train-only normalizer',
        objective='Unclipped requested-action weighted MSE + common normalized-readout ridge .1; identical deployment clipping/filter',
        optimization='Primary3: Adam,8 histories per batch,TBPTT64,8000updates,3 learning rates,validation at0 and every1000; same history order per seed; no warm start',
        selection='All39 fits before any new physics; per-run best validation clipped-action MSE then rate minimizing mean across3seeds; all3seeds evaluated, no online selection',
        auxiliary_rule='Analytic ESN solves same readout objective at fixed rho.8/input gain.25. RNN-from-ridge uses that same unselected ridge parent; update0 allowed and identity disclosed.',
        comparison='Architecture/mechanism controlled, not equal trainable parameters or compute; total storage,learned parameters,wall time and exposure separately reported',
        analysis='Original Task/Strict primary; all RMSE,torque,speed,per-event contact coverage/P95/impulse,recovery censoring reported. Primary ESN-gradient minus RNN/MLP paired differences with seed-and-condition bootstrap95% intervals (2000,seed713); descriptive, no multiplicity-adjusted significance claim.',
        prospective='8 new acceptance identities inside old ranges; model-lock before first evaluation; older sealed sets never read; no test-based retuning; not broad real-world generalization',
        conditions_sha256=sha(out/'CONDITIONS.json'), fits=39, new_physics_episodes=288,
        resources=dict(host='airpig', server_compute=False, simulators=1, threads=1, memory_max_bytes=3*1024**3, memory_swap_max=0),
        unchanged=['geometry','Task/Strict','actuator amplitude/slew','common WBC/filter','dt5e-5','55s horizon'],
        source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        baseline_commit=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=ROOT,text=True).strip())
    write(out/'REGISTRATION.json', registration)
    print(json.dumps(dict(out=str(out), registration_sha256=sha(out/'REGISTRATION.json'), fits=39, rollouts=288)))


def selection(rows):
    chosen = []
    for family in FAMILIES:
        group = [r for r in rows if r['family'] == family]
        rates = [None] if family == 'esn_ridge' else list(RATES)
        for lr in rates:
            require({r['seed'] for r in group if r['rate'] == lr} == set(SEEDS), 'Missing seed/rate')
            require(sum(r['rate'] == lr for r in group) == 3, 'Duplicate training row')
        best = min(rates, key=lambda lr: (statistics.mean(r['validation_mse'] for r in group if r['rate'] == lr), lr or 0))
        chosen.extend(r for r in group if r['rate'] == best)
    return chosen


class FairCampaign(Campaign):
    def train(self):
        self.save(status='training'); rows = []
        for seed in SEEDS:
            for family in FAMILIES:
                for rate in ([None] if family == 'esn_ridge' else RATES):
                    name = f'{family}_s{seed}_lr{rate}'; dest = self.out/'learning'/name
                    cmd = [self.reg['fitting_python'],str(self.source/'tools/train_fair_students_20261013.py'),
                        '--data',str(self.out/'data/training_data.npz'),'--metadata',str(self.out/'data/DATA_COMPLETE.json'),
                        '--output',str(dest),'--family',family,'--seed',str(seed),'--updates',str(UPDATES),
                        '--learning-rate',str(rate or .0001)]
                    self.job('fit_'+name,cmd,maximum=1800)
                    meta = read(dest/'TRAINING_COMPLETE.json'); cp = dest/'checkpoint.npz'
                    require(meta['training_data_sha256'] == self.reg['training_data_sha256'] and sha(cp) == meta['checkpoint_sha256'], 'Training pin')
                    self.products('fit_'+name,[dest/'TRAINING_COMPLETE.json',cp,dest/'initialization.npz',dest/'schedule.json'])
                    rows.append(dict(name=f'{family}_s{seed}',family=family,seed=seed,rate=rate,worker_kind='office',config={},
                        checkpoint=str(cp),checkpoint_sha256=sha(cp),validation_mse=meta['validation_mse'],
                        metadata=str(dest/'TRAINING_COMPLETE.json'),metadata_sha256=sha(dest/'TRAINING_COMPLETE.json'),
                        selected_update=meta['selected_update'],effective_recurrent_update=meta['effective_recurrent_update'],
                        trainable_parameters=meta['trainable_parameters'],stored_float_scalars=meta['stored_float_scalars'],
                        duration_s=meta['duration_s'],group='primary' if family in self.reg['primary'] else 'auxiliary'))
                    write(self.out/'TRAINING_RESULTS.json',dict(rows=rows))
        require(len(rows)==39,'Training grid incomplete')
        # Audit equality of the actual primary initialization and data exposure,
        # not merely matching CLI labels. Runs at all rates retain their evidence.
        import numpy as np
        for seed in SEEDS:
            group=[r for r in rows if r['seed']==seed and r['group']=='primary']
            origin=None; schedule=None
            for r in group:
                p=Path(r['metadata']).parent
                with np.load(p/'initialization.npz') as z:
                    values={k:z[k].copy() for k in z.files}
                if origin is None:origin=values
                else:
                    for k in origin:np.testing.assert_array_equal(origin[k],values[k])
                h=sha(p/'schedule.json')
                if schedule is None:schedule=h
                else:require(schedule==h,'Primary training exposure differs')
        selected=selection(rows)
        models=selected+read(self.out/'HISTORICAL_ROSTER.json')['models']
        write(self.out/'MODEL_LOCK.json',dict(status='frozen',created_utc=now(),models=models,
            training_results_sha256=sha(self.out/'TRAINING_RESULTS.json'),registration_sha256=sha(self.out/'REGISTRATION.json'),
            conditions_sha256=self.reg['conditions_sha256'],models_count=36,expected_rows=288))
        self.save(status='models_locked',fits_complete=39,model_lock_sha256=sha(self.out/'MODEL_LOCK.json'))

    def evaluate_model(self, model, condition):
        require(sha(self.out/'MODEL_LOCK.json')==self.state['model_lock_sha256'],'Model lock changed')
        name=model['name']+'__'+condition['id'];dest=self.out/'evaluation'/name
        config=self.out/'configs'/(name+'.json')
        if not config.exists():write(config,model['config'])
        else:require(read(config)==model['config'],'Config changed')
        cmd=[self.reg['simulation_python'],str(self.source/'tools/baseline_repair_worker_20261008.py'),
            '--research-protocol',str(self.out/'PROTOCOL.json'),'--protocol-sha256',self.reg['protocol_sha256'],
            '--research-condition',condition['id'],'--phase','acceptance','--worker-kind',model['worker_kind'],
            '--v6-input',str(Path(self.protocol['runtime'])/'v6'),
            '--reference',str(Path(self.protocol['runtime'])/'v6/esn_original_v2/rollout.json'),
            '--config',str(config),'--output',str(dest),'--contact-audit','--physics-dt','.00005']
        for key in ('checkpoint','parameter_source','agent_checkpoint','checkpoint_manifest','controller'):
            if model.get(key) is not None:cmd+=['--'+key.replace('_','-'),str(model[key])]
        if model.get('checkpoint'):require(sha(model['checkpoint'])==model['checkpoint_sha256'],'Checkpoint changed')
        self.job(name,cmd,maximum=1800)
        a=read(dest/'AUDIT.json');e=read(dest/'execution.json')
        require(e['status']=='complete' and a['model_sha256']==self.protocol['formal_model_sha256'],'Physical execution pin')
        require(a['common_filter_replay_max_abs']==0,'Filter replay failed')
        if model.get('checkpoint'):
            require(e['checkpoint_sha256']==model['checkpoint_sha256'],'Wrong executed model')
            require(a['actor_replay_performed'] and a['action_replay_max_abs']<=1e-10,'Actor replay failed')
            require(a['reservoir_replay_max_abs'] is None or a['reservoir_replay_max_abs']<=1e-10,'State replay failed')
        if model['worker_kind']=='adapted_rl':require(a['raw_actor_replay_max_abs']==0 and a['normalization_unchanged'],'RL replay failed')
        if model['worker_kind']=='classical':require(a['policy_trace_consistency_max_abs']==0,'Classical trace mismatch')
        self.products(name,[dest/'AUDIT.json',dest/'execution.json',dest/'rollout.npz',dest/'execution_chain.npz'])
        metric=self.out/'metrics'/(name+'.json')
        self.job(name+'_metrics',[self.reg['simulation_python'],str(self.source/'tools/paper_metrics_20261002.py'),
            '--run',str(dest),'--output',str(metric)],dispatch=False)
        m=read(metric);verify_values(a,m);self.products(name+'_metrics',[metric])
        return dict(method=model['name'],family=model['family'],group=model['group'],seed=model.get('seed'),
            condition=condition['id'],run=str(dest),metrics=m,metric_file=str(metric),metric_sha256=sha(metric),
            audit_sha256=sha(dest/'AUDIT.json'),trace_sha256=sha(dest/'rollout.npz'))

    def compare(self):
        self.save(status='prospective_evaluation')
        models=read(self.out/'MODEL_LOCK.json')['models'];conditions=read(self.out/'CONDITIONS.json')['conditions'];rows=[]
        for condition in conditions:
            for model in models:
                rows.append(self.evaluate_model(model,condition))
                report=dict(updated_utc=now(),interpretation='Prospective8 same-range identities;3seed primary matched controls, auxiliary ridge/fine-tune,21historical systems. Not equal training regimes across systems; no universal superiority claim.',
                    rows=rows,methods=summarise(rows,[m['name'] for m in models],{c['id'] for c in conditions}),expected_rows=288,
                    previous_sealed_test_reads=0,condition_file_sha256=sha(self.out/'CONDITIONS.json'))
                write(self.out/'REPORT.json',report);(self.out/'REPORT.md').write_text(render(report))
                self.save(evaluated=len(rows),expected=288)
            self.safe_publish('condition_'+condition['id'])
        self.job('independent_final_audit',[self.reg['simulation_python'],str(self.source/'tools/fair_comparison_20261013.py'),
            'audit','--out',str(self.out)],dispatch=False)
        require(read(self.out/'FINAL_AUDIT.json')['status']=='passed','Final audit failed')
        stats=paired_statistics(rows)
        write(self.out/'PAIRED_STATISTICS.json',stats)
        with (self.out/'REPORT.md').open('a') as f:
            f.write('\n## 主对照配对差值（ESN-gradient 减去对照）\n\n')
            f.write('|对照|指标|均值差|描述性95%区间|\n|---|---|---:|---|\n')
            for r in stats['comparisons']:
                f.write(f"|{r['other']}|{r['metric']}|{r['difference']:.6g}|[{r['low']:.6g}, {r['high']:.6g}]|\n")
            f.write('\n按训练seed和条件两轴配对重采样；仅3seed/8条件，区间不证明全局优势。成功率差越大越好，误差/力/冲量差越小越好；必须同时看任务和接触覆盖。\n')
        self.save(status='complete_review_required')

    def run(self):
        require(platform.node()=='airpig','Local only')
        require(sha(self.out/'REGISTRATION.json')==self.state.get('registration_sha256',sha(self.out/'REGISTRATION.json')),'Registration changed')
        require(hashes(self.source)==read(self.out/'SOURCE_HASHES.json') and sha(self.out/'SOURCE_HASHES.json')==self.reg['source_manifest_sha256'],'Source pin')
        require(sha(self.out/'PROTOCOL.json')==self.reg['protocol_sha256'],'Protocol pin')
        require(sha(self.out/'CONDITIONS.json')==self.reg['conditions_sha256'],'Condition pin')
        require(sha(self.out/'data/training_data.npz')==self.reg['training_data_sha256'],'Data pin')
        require(sha(self.out/'data/DATA_COMPLETE.json')==self.reg['metadata_sha256'],'Split metadata pin')
        require(sha(self.out/'HISTORICAL_ROSTER.json')==self.reg['historical_roster_sha256'],'Roster pin')
        require(sha(self.out/'DEPENDENCY_HASHES.json')==self.reg['dependency_manifest_sha256'],'Dependency pin')
        require(all(sha(self.out/'dependencies'/p)==h for p,h in read(self.out/'DEPENDENCY_HASHES.json').items()),'Dependency changed')
        with (self.out/'coordinator.lock').open('a') as singleton:
            fcntl.flock(singleton,fcntl.LOCK_EX|fcntl.LOCK_NB)
            try:
                self.save(status='waiting_for_compute',registration_sha256=sha(self.out/'REGISTRATION.json'),server_compute=False)
                self.lock=(self.parent.parent/'.local-rl-compute.lock').open('a')
                while True:
                    self.check()
                    try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB);break
                    except BlockingIOError:time.sleep(5)
                self.train();self.safe_publish('models_locked');self.compare()
            except BaseException as exc:
                self.save(status='failed_preserved',error=repr(exc));raise
            finally:
                if self.lock:self.lock.close()
                self.save(ended_utc=now());self.safe_publish('final')

    def publish(self, stage):
        """Archive at immutable stage boundaries, then publish factual status."""
        from archive_tool_campaign_20261002 import make
        dest=self.out/('delivery_'+stage)
        if dest.exists():return
        dest.mkdir();evidence=dest/'evidence';evidence.mkdir()
        for p in self.out.iterdir():
            if p.is_file() and p.suffix in ('.json','.md'):shutil.copy2(p,evidence/p.name)
        if (evidence/'execution.json').exists():
            state=read(evidence/'execution.json');state['live_campaign_status']=state['status'];state['status']='report_snapshot';write(evidence/'execution.json',state)
        # Small progress snapshots; full data/dependencies/raw once at final.
        for folder in ('source',):shutil.copytree(self.out/folder,evidence/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        folders=('learning',) if stage=='models_locked' else ()
        if stage=='final':folders=('data','learning','dependencies','receipts','configs','metrics','evaluation')
        for folder in folders:shutil.copytree(self.out/folder,evidence/folder,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        archive=dict(status='pending',local=str(evidence))
        try:
            make(evidence);name=self.out.name+'_'+stage
            incoming='/home/arm1/sii_shared/SII_compliance/incoming/'+name
            published='/home/arm1/sii_shared/SII_compliance/runs/main/'+name+'/evidence'
            subprocess.run(['rsync','-a','--timeout=60','-e','ssh -o BatchMode=yes -o ConnectTimeout=10',str(evidence)+'/',
                'arm1@192.168.31.70:'+incoming+'/'],check=True,timeout=3600,capture_output=True,text=True)
            result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','arm1@192.168.31.70',
                'python3',incoming+'/source/tools/archive_tool_campaign_20261002.py','--root',incoming,'--publish',published],
                check=True,timeout=1800,capture_output=True,text=True)
            archive=dict(status='verified',receipt=json.loads(result.stdout))
        except Exception as exc:archive.update(error=repr(exc))
        write(dest/'ARCHIVE_STATUS.json',archive)
        repo=Path(self.reg['repository'])
        docs=repo/'code/mujoco_6d_vmc_benchmark/docs'
        paths=[docs/'FAIR_COMPARISON_LIVE_20261013.md',repo/'UPDATE_LOG.md',
               docs/'ESN_VMC_JOINT_PROGRESS_20260927.md',docs/'BASELINE_WEEKLY_REPORT_20260923.md']
        try:
            require('UPDATE_LOG.md' in (repo/'AGENTS.md').read_text(),'Read publishing instructions')
            require(subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip()=='main','Main only')
            require(not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=repo,text=True).strip(),'Concurrent staged changes')
            names=[str(p.relative_to(repo)) for p in paths]
            require(not subprocess.check_output(['git','status','--porcelain','--',*names],cwd=repo,text=True).strip(),'Concurrent report edits')
            subprocess.run(['git','fetch','origin','refs/heads/main:refs/remotes/origin/main'],cwd=repo,check=True,timeout=60,capture_output=True)
            require(subprocess.run(['git','merge-base','--is-ancestor','origin/main','HEAD'],cwd=repo).returncode==0,'Remote advanced')
            content=f'# 公平性修正：实时状态\n\n{now()}；{stage}；状态 `{self.state["status"]}`。\n\n'
            content+='主对照统一数据、特征、初始化、损失、Adam预算和选择机会；ridge与父模型微调单列。既有21配置同新条件重评，训练信息/预算差异不归因于网络结构。\n\n'
            content+='归档：\n```json\n'+json.dumps(archive,ensure_ascii=False,indent=2)+'\n```\n\n'
            if (self.out/'REPORT.md').exists():content+=(self.out/'REPORT.md').read_text()
            if (self.out/'MODEL_LOCK.json').exists():
                content+='\n|新模型|seed|选中update|循环权重有效更新|验证MSE|可训练参数|存储float|\n|---|---:|---:|---|---:|---:|---:|\n'
                for m in read(self.out/'MODEL_LOCK.json')['models']:
                    if m['group']=='historical_system':continue
                    content+=f"|{m['family']}|{m['seed']}|{m['selected_update']}|{m['effective_recurrent_update']}|{m['validation_mse']:.7g}|{m['trainable_parameters']}|{m['stored_float_scalars']}|\n"
            paths[0].write_text(content)
            entry=f'\n## {now()} — 公平性修正 {stage}\n\n- 状态 `{self.state["status"]}`，新条件已评 {self.state.get("evaluated",0)}/288；39拟合/3seed，旧封存集未读。\n- 归档 `{archive["status"]}`，详情 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。失败保留；不能在完整审计前宣称胜出或所有baseline充分收敛。\n'
            for p in paths[1:]:
                first,_,rest=p.read_text().partition('\n');p.write_text(first+'\n'+entry+'\n'+rest)
            subprocess.run(['git','add','--',*names],cwd=repo,check=True)
            subprocess.run(['git','commit','-m','Report prospective fairness campaign '+stage,'--',*names],cwd=repo,check=True,timeout=60,capture_output=True)
            subprocess.run(['git','push','origin','HEAD:main'],cwd=repo,check=True,timeout=120,capture_output=True)
            head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
            remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=repo,text=True,timeout=60).split()[0]
            require(head==remote,'Push verification');write(dest/'GIT_STATUS.json',dict(status='pushed_verified',commit=head))
        except Exception as exc:write(dest/'GIT_STATUS.json',dict(status='pending',error=repr(exc)))


def render(report):
    lines=['# 前瞻性同条件比较','',report['interpretation'],'',
           '|方法/seed|已评/8|Task|Strict|RMSE mm|峰矩均值 Nm|峰速均值 m/s|早停|',
           '|---|---:|---:|---:|---:|---:|---:|---:|']
    for m in report['methods']:
        values=[f"{m['task']}/8",f"{m['strict']}/8",*[f'{v:.4f}' for v in m['means'].values()]] if m['complete'] else ['pending']*5
        lines.append('| '+' | '.join([m['method'],f"{m['evaluated']}/8",*values,str(m['short'])])+' |')
    lines+=['','每个新网络有3个seed，不挑最好seed。历史方法每配置仍只有既有训练seed，不能复制成3seed。',
            '全部失败计入分母，未完成不记0/0；早停的低速度/低冲量不能当作优点。',
            '接触P95、冲量、接触覆盖、恢复删失及原始指标均存 REPORT.json；结果不完整时不宣布排名。','']
    lines+=['|方法/seed|人手P95 N / 接触回合|棍P95 N / 接触回合|桌角P95 N / 接触回合|人手冲量 N·s|棍冲量 N·s|桌角冲量 N·s|',
            '|---|---:|---:|---:|---:|---:|---:|']
    for m in report['methods']:
        if not m['complete'] or 'contacts' not in m:continue
        c=m['contacts'];events=('human','rod','unknown_edge')
        forces=[('NA' if c[k]['mean_exposed_episode_p95_n'] is None else f"{c[k]['mean_exposed_episode_p95_n']:.3f}")+f" / {c[k]['exposed']}" for k in events]
        lines.append('| '+' | '.join([m['method'],*forces,*[f"{c[k]['mean_impulse_ns']:.3f}" for k in events]])+' |')
    lines+=['','不接触的P95为NA；冲量按全部回合描述，不能忽略未到达接触位置或早停的失败。','']
    return '\n'.join(lines)


def paired_statistics(rows):
    import numpy as np
    primary=[r for r in rows if r['group']=='primary']
    conditions=sorted({r['condition'] for r in primary})
    index={(r['family'],r['seed'],r['condition']):r['metrics'] for r in primary}
    keys=('task_success','strict_success','rmse_mm','peak_torque_nm','peak_speed_mps',
          'human_impulse_ns','rod_impulse_ns','unknown_edge_impulse_ns')
    def value(m,k):
        return float(m['contact'][k[:-len('_impulse_ns')]]['impulse_ns']) if k.endswith('_impulse_ns') else float(m[k])
    rng=np.random.default_rng(713)
    seed_draw=rng.integers(0,len(SEEDS),(2000,len(SEEDS)))
    cond_draw=rng.integers(0,len(conditions),(2000,len(conditions)))
    results=[]
    for other in ('rnn_scratch','mlp_scratch'):
        for key in keys:
            delta=np.array([[value(index[('esn_gradient',s,c)],key)-value(index[(other,s,c)],key)
                             for c in conditions] for s in SEEDS])
            boots=delta[seed_draw[:,:,None],cond_draw[:,None,:]].mean((1,2))
            lo,hi=np.quantile(boots,[.025,.975])
            results.append(dict(other=other,metric=key,difference=float(delta.mean()),low=float(lo),high=float(hi)))
    return dict(schema='paired-crossed-seed-condition-bootstrap-v1',seeds=list(SEEDS),conditions=conditions,
                replicates=2000,seed=713,comparisons=results,
                limitation='Descriptive intervals,3training seeds/8conditions; no multiple-comparison significance or all-method structural claim')


def audit(out):
    reg=read(out/'REGISTRATION.json');lock=read(out/'MODEL_LOCK.json');report=read(out/'REPORT.json')
    require(hashes(out/'source')==read(out/'SOURCE_HASHES.json'),'Source changed')
    require(sha(out/'SOURCE_HASHES.json')==reg['source_manifest_sha256'],'Source manifest changed')
    require(sha(out/'data/training_data.npz')==reg['training_data_sha256'],'Data changed')
    require(sha(out/'CONDITIONS.json')==lock['conditions_sha256']==reg['conditions_sha256'],'Conditions changed')
    require(sha(out/'REGISTRATION.json')==lock['registration_sha256'],'Registration changed')
    require(sha(out/'TRAINING_RESULTS.json')==lock['training_results_sha256'],'Training ledger changed')
    conditions={c['id']:c for c in read(out/'CONDITIONS.json')['conditions']}
    models={m['name']:m for m in lock['models']}
    verify_grid(report['rows'],models,conditions)
    require(len(report['rows'])==288 and report['methods']==summarise(report['rows'],list(models),set(conditions)),'Aggregation mismatch')
    for row in report['rows']:
        model=models[row['method']];p=Path(row['run']);a=read(p/'AUDIT.json');e=read(p/'execution.json');m=row['metrics']
        require(sha(row['metric_file'])==row['metric_sha256'] and read(row['metric_file'])==m,'Metric pin')
        require(sha(p/'AUDIT.json')==row['audit_sha256'],'Audit pin')
        require(e['status']=='complete' and e['runtime_provenance']['research_condition']==conditions[row['condition']],'Condition receipt')
        require(datetime.fromisoformat(e['started_utc'])>datetime.fromisoformat(lock['created_utc']),'Evaluation before model lock')
        args=read(p/'rollout.json')['arguments']
        require(all(args[k]==v for k,v in conditions[row['condition']]['overrides'].items()),'Actual disturbance mismatch')
        require(sha(p/'rollout.mjb')==m['model_sha256']==read(out/'PROTOCOL.json')['formal_model_sha256'],'Physics model mismatch')
        for filename,key in [('rollout.npz','trace_sha256'),('rollout_metrics/substep_metrics.npz','native_metrics_sha256'),
                             ('research_substeps.npz','research_metrics_sha256'),('execution.json','execution_sha256')]:
            require(sha(p/filename)==m[key],'Raw evidence changed')
        require(sha(p/'execution_chain.npz')==a['chain_sha256'] and a['common_filter_replay_max_abs']==0,'Filter chain')
        if model.get('checkpoint'):
            require(sha(model['checkpoint'])==model['checkpoint_sha256']==e['checkpoint_sha256'],'Checkpoint changed')
            require(a['actor_replay_performed'] and a['action_replay_max_abs']<=1e-10,'Actor replay')
            require(a['reservoir_replay_max_abs'] is None or a['reservoir_replay_max_abs']<=1e-10,'State replay')
        if model['worker_kind']=='adapted_rl':require(a['raw_actor_replay_max_abs']==0 and a['normalization_unchanged'],'RL audit')
        if model['worker_kind']=='classical':require(a['policy_trace_consistency_max_abs']==0,'Classical audit')
        verify_values(a,m)
    write(out/'FINAL_AUDIT.json',dict(status='passed',verified_rows=288,created_utc=now(),
        report_sha256=sha(out/'REPORT.json'),model_lock_sha256=sha(out/'MODEL_LOCK.json'),
        previous_sealed_test_reads=0,limitation='8 new local-range conditions;3seeds only for new students; no universal dominance or RL convergence claim'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run','audit','publish'));p.add_argument('--out',type=Path,required=True)
    p.add_argument('--predecessor',type=Path);p.add_argument('--stage',default='manual')
    a=p.parse_args();out=a.out.resolve()
    if a.mode=='prepare':prepare(out,a.predecessor.resolve())
    elif a.mode=='audit':audit(out)
    elif a.mode=='publish':FairCampaign(out).publish(a.stage)
    else:FairCampaign(out).run()


if __name__=='__main__':main()
