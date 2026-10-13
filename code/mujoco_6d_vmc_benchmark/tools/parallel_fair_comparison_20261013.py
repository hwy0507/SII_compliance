"""Resource-only continuation of the frozen fairness campaign.

No scientific-source edit or model reselection. Completed receipts are reused;
workers execute the original frozen commands. Only the coordinator owns the
global simulation lock. Memory admission reserves remaining hard caps, not just
current RSS, before admitting another lane. The server performs no experiments.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

GIB = 1024**3


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path=Path(path);temp=path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def available_bytes():
    return 1024*int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))


def admission(available, new_cap, active, reserve):
    """Each active=(hard cap,current cgroup bytes); account future growth too."""
    future=sum(max(0, cap-current) for cap,current in active)
    return available >= new_cap+future+reserve


def neural_cap(peak, full_horizon):
    if not full_horizon or peak <= 0:return 3*GIB
    # At least 2x the full-episode peak including compression/audit/analysis.
    for cap in (3*GIB//2,2*GIB,3*GIB):
        if 2*peak <= cap:return cap
    return 3*GIB


def memory_receipt(path):
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    write(path,dict(created_utc=now(),cgroup=str(cg),memory_peak_bytes=int((cg/'memory.peak').read_text()),
        memory_max=(cg/'memory.max').read_text().strip(),memory_swap_max=(cg/'memory.swap.max').read_text().strip(),
        memory_events=(cg/'memory.events').read_text(),source_sha256=sha(Path(__file__))))


def prepare(out):
    dest=out/'dispatch_v3';dest.mkdir(exist_ok=False)
    script=dest/Path(__file__).name;shutil.copy2(Path(__file__),script)
    old=read(out/'REGISTRATION.json')
    write(dest/'REGISTRATION.json',dict(schema='sii-fair-resource-amendment-v3',registered_utc=now(),
        authority='2026-10-13 user: fully use compute and accelerate evaluation; local only remains in force',
        source_sha256=sha(script),original_registration_sha256=sha(out/'REGISTRATION.json'),
        original_source_manifest_sha256=sha(out/'SOURCE_HASHES.json'),
        original_deadline_utc=old['dispatch_deadline_utc'],new_dispatch_deadline=False,
        handoff_stop_sha256=sha(out/'STOP_REQUESTED'),previous_service='sii-fair-comparison-20261013-v2.service',
        max_lanes=4,cpu_cores=[1,6,2,7],numeric_threads=1,heavy_memory_cap_bytes=3*GIB,
        headroom_bytes=3*GIB//4,memory_swap_max=0,
        admission='Available >= new hard cap + sum(active hard cap-current cgroup usage) + .75GiB. Stop admissions under pressure; no killing desktop apps.',
        pilot='First registered new ESN evaluation, full55s required for low-memory tier; no extra episode or result-based selection. Cap1.5/2/3GiB requires >=2x measured cgroup peak including postprocessing.',
        dispatch='At most4lanes. First wait for original coordinator/child/publication to exit, reuse all completed fits and any evaluated pairs. Then per condition select first memory-admissible model. Heavy candidates interleaved with neural checkpoints; no outcome-based scheduling.',
        scope='39fits/288original episodes, unchanged source/data/selection/models/environment/gates/dt/seed/audits. Classical and RL retain3GiB caps. RL GPU contexts remain native; never migrate frozen physics to GPU.',
        stop_file=str(out/'DISPATCH_STOP_REQUESTED'),server_compute=False))
    print(json.dumps(dict(dispatch=str(dest),sha256=sha(dest/'REGISTRATION.json'))))


def build_class(out):
    # All experiment logic is imported from the immutable original snapshot.
    sys.path.insert(0,str(out/'source/tools'))
    from fair_comparison_20261013 import FairCampaign, render, paired_statistics
    from compare_local_baselines_20261012 import summarise
    from teacher_student_15h_20261012 import require

    class ParallelCampaign(FairCampaign):
        def __init__(self, root):
            self.mutex=threading.RLock();self.local=threading.local();self.lanes={}
            super().__init__(root)
            self.amend=read(root/'dispatch_v3/REGISTRATION.json')
            require(sha(Path(__file__))==self.amend['source_sha256'],'Dispatcher source changed')
            require(sha(root/'REGISTRATION.json')==self.amend['original_registration_sha256'],'Science registration changed')
            require(sha(root/'SOURCE_HASHES.json')==self.amend['original_source_manifest_sha256'],'Frozen source changed')
            require(self.reg['dispatch_deadline_utc']==self.amend['original_deadline_utc'],'Deadline changed')
            self.cg_parent=(Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')).parent
            self.memory_cap=3*GIB
            if (root/'dispatch_v3/RESOURCE_PILOT.json').exists():
                self.memory_cap=read(root/'dispatch_v3/RESOURCE_PILOT.json')['neural_cap_bytes']

        def save(self, **kwargs):
            with self.mutex:super().save(**kwargs)

        def check(self, cutoff=None):
            require(datetime.now(timezone.utc)<(cutoff or self.deadline),'Dispatch deadline reached')
            require(not (self.out/'DISPATCH_STOP_REQUESTED').exists(),'Stop requested at boundary')
            # The original stop is consumed only by this explicitly registered
            # resource handoff. An unrelated/changed stop is never ignored.
            require(sha(self.out/'STOP_REQUESTED')==self.amend['handoff_stop_sha256'],'Handoff stop changed')

        def train(self):
            if (self.out/'MODEL_LOCK.json').exists():
                lock=read(self.out/'MODEL_LOCK.json')
                require(lock['status']=='frozen' and lock['registration_sha256']==sha(self.out/'REGISTRATION.json'),'Existing model lock changed')
                require(sha(self.out/'TRAINING_RESULTS.json')==lock['training_results_sha256'],'Training ledger changed')
                self.save(status='models_locked',fits_complete=39,model_lock_sha256=sha(self.out/'MODEL_LOCK.json'))
                return
            super().train()

        def cap(self,model):
            return self.memory_cap if model.get('checkpoint') and model['worker_kind']=='office' else 3*GIB

        def usage(self):
            result=[]
            for lane in self.lanes.values():
                unit=lane.get('unit');current=0
                if unit:
                    p=self.cg_parent/(unit+'.service')/'memory.current'
                    try:current=int(p.read_text())
                    except FileNotFoundError:pass
                result.append((lane['cap'],current))
            return result

        def job(self,name,command,maximum=1800,cutoff=None,dispatch=True):
            if not getattr(self.local,'reserved',False):
                return super().job(name,command,maximum,cutoff,dispatch)
            receipt=self.out/'receipts'/(name+'.json')
            if receipt.exists():
                r=read(receipt)
                require(r['status']=='complete' and r['command']==command,'Incomplete or changed old attempt: '+name)
                require(all(Path(p).is_file() and sha(p)==h for p,h in r.get('products',{}).items()),'Completed product changed')
                return
            if dispatch:self.check(cutoff)
            require(shutil.disk_usage(self.out).free>35*GIB,'Disk reserve')
            lane_id=self.local.lane
            with self.mutex:
                lane=self.lanes[lane_id];cap=lane['cap'];cpu=lane['cpu']
            unit='sii-fair-p3-'+hashlib.sha256((str(self.out)+name).encode()).hexdigest()[:16]
            profile=self.out/'dispatch_v3'/(name+'.memory.json')
            # ExecStopPost captures the exact kernel peak BEFORE the cgroup is
            # removed; sampled RSS would miss compression/allocation spikes.
            import shlex
            stop=shlex.join([self.reg['simulation_python'],str(Path(__file__)),'memory-receipt','--out',str(profile)])
            argv=['systemd-run','--user','--wait','--pipe','--collect','--slice=app.slice','--unit='+unit,
                '--property=MemoryMax='+str(cap),'--property=MemorySwapMax=0','--property=TasksMax=256',
                '--property=RuntimeMaxSec='+str(maximum),'--property=CPUAffinity='+str(cpu),
                '--property=ExecStopPost='+stop,'--working-directory='+str(self.source)]
            argv+=['--setenv='+k+'='+v for k,v in self.env.items()]+command
            r=dict(status='running',command=command,managed_command=argv,started_utc=now(),unit=unit,
                   lane=lane_id,cpu=cpu,memory_cap_bytes=cap,dispatch_sha256=sha(self.out/'dispatch_v3/REGISTRATION.json'))
            write(receipt,r)
            with self.mutex:
                lane.update(unit=unit,job=name,started_utc=now())
                self.save(active_jobs={str(k):dict(v) for k,v in self.lanes.items()},active=None)
            with (self.out/'receipts'/(name+'.log')).open('x') as log:
                rc=subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT).returncode
            memory=read(profile) if profile.exists() else None
            r.update(status='complete' if rc==0 else 'failed_preserved',returncode=rc,ended_utc=now(),memory=memory)
            write(receipt,r)
            with self.mutex:
                lane.update(unit=None,job=None)
                self.save(active_jobs={str(k):dict(v) for k,v in self.lanes.items()})
            require(rc==0,'Child failed, preserve and drain other in-flight episodes: '+name)
            require(memory is not None and int(memory['memory_max'])==cap and memory['memory_swap_max']=='0','Resource receipt missing')
            require('oom_kill 0' in memory['memory_events'],'Worker OOM event')

        def lane_evaluate(self,lane_id,model,condition):
            self.local.reserved=True;self.local.lane=lane_id
            try:return super().evaluate_model(model,condition)
            finally:self.local.reserved=False

        def write_report(self,rows,models,conditions):
            # Deterministic output order independent of completion timing.
            mi={m['name']:i for i,m in enumerate(models)};ci={c['id']:i for i,c in enumerate(conditions)}
            ordered=sorted(rows,key=lambda r:(ci[r['condition']],mi[r['method']]))
            report=dict(updated_utc=now(),interpretation='Same prospective8 and frozen39fit/36model lock; resource-only local parallel dispatch. Same science as serial protocol, no test-based model changes.',
                rows=ordered,methods=summarise(ordered,[m['name'] for m in models],set(ci)),expected_rows=288,
                previous_sealed_test_reads=0,condition_file_sha256=sha(self.out/'CONDITIONS.json'),
                resource_amendment_sha256=sha(self.out/'dispatch_v3/REGISTRATION.json'))
            write(self.out/'REPORT.json',report);(self.out/'REPORT.md').write_text(render(report))
            self.save(evaluated=len(rows),expected=288,dispatcher='parallel_v3',neural_memory_cap_bytes=self.memory_cap)

        def compare(self):
            self.save(status='prospective_evaluation',dispatcher='parallel_v3')
            models=read(self.out/'MODEL_LOCK.json')['models'];conditions=read(self.out/'CONDITIONS.json')['conditions']
            rows=[];completed=set()
            # A genuine serial full episode can be reused but never relabeled
            # as a measured-memory pilot when it has no cgroup receipt.
            if (self.out/'REPORT.json').exists():
                for r in read(self.out/'REPORT.json')['rows']:
                    require(sha(r['metric_file'])==r['metric_sha256'] and sha(Path(r['run'])/'AUDIT.json')==r['audit_sha256'],'Old row changed')
                    rows.append(r);completed.add((r['method'],r['condition']))
            def add(row):
                key=(row['method'],row['condition']);require(key not in completed,'Duplicate episode')
                rows.append(row);completed.add(key);self.write_report(rows,models,conditions)
            # One original planned episode; budget remains288, not289.
            pilot_file=self.out/'dispatch_v3/RESOURCE_PILOT.json'
            if not pilot_file.exists():
                pair=next(((m,c) for c in conditions for m in models if m['group']=='primary' and
                           m['family']=='esn_gradient' and (m['name'],c['id']) not in completed),None)
                require(pair is not None,'No unrun registered ESN available for resource pilot')
                m,c=pair
                while not admission(available_bytes(),3*GIB,[],self.amend['headroom_bytes']):
                    self.check();time.sleep(5)
                self.lanes[0]=dict(cap=3*GIB,cpu=self.amend['cpu_cores'][0],unit=None)
                row=self.lane_evaluate(0,m,c);self.lanes.clear();add(row)
                name=m['name']+'__'+c['id']
                peak=max(read(self.out/'dispatch_v3'/(n+'.memory.json'))['memory_peak_bytes'] for n in (name,name+'_metrics'))
                self.memory_cap=neural_cap(peak,row['metrics']['full_horizon'])
                write(pilot_file,dict(created_utc=now(),episode=name,full_horizon=row['metrics']['full_horizon'],
                    peak_bytes=peak,neural_cap_bytes=self.memory_cap,rule='2x peak; all heavy methods keep3GiB',
                    metric_sha256=row['metric_sha256'],extra_episodes=0))
                self.save(neural_memory_cap_bytes=self.memory_cap,pilot_peak_bytes=peak)
            for c in conditions:
                pending=[m for m in models if (m['name'],c['id']) not in completed]
                # Start a heavy worker alongside light ones, so RL/classical do
                # not form a wholly serial tail. This depends on type, not score.
                pending.sort(key=lambda m:(self.cap(m)<3*GIB,models.index(m)))
                failure=None;futures={};last_log=0
                with ThreadPoolExecutor(max_workers=self.amend['max_lanes']) as executor:
                    while pending or futures:
                        try:self.check()
                        except Exception as exc:failure=failure or exc
                        if failure:pending=[]
                        if not failure:
                            with self.mutex:
                                free=[i for i in range(self.amend['max_lanes']) if i not in self.lanes]
                                for lane_id in free:
                                    choice=next((i for i,m in enumerate(pending) if admission(available_bytes(),self.cap(m),self.usage(),self.amend['headroom_bytes'])),None)
                                    if choice is None:break
                                    m=pending.pop(choice)
                                    self.lanes[lane_id]=dict(cap=self.cap(m),cpu=self.amend['cpu_cores'][lane_id],unit=None)
                                    futures[executor.submit(self.lane_evaluate,lane_id,m,c)]=lane_id
                        if not futures:
                            if pending:
                                if time.monotonic()-last_log>30:
                                    self.save(waiting_for_memory=True,available_bytes=available_bytes(),remaining_this_condition=len(pending));last_log=time.monotonic()
                                time.sleep(5)
                            continue
                        done,_=wait(futures,timeout=3,return_when=FIRST_COMPLETED)
                        for future in done:
                            lane_id=futures.pop(future)
                            with self.mutex:self.lanes.pop(lane_id)
                            try:add(future.result())
                            except Exception as exc:failure=failure or exc
                        # In-flight peers finish and are saved even if one fails;
                        # no further dispatch, no loss of their audit/results.
                    if failure:raise failure
                self.safe_publish('parallel_condition_'+c['id'])
            self.job('independent_final_audit',[self.reg['simulation_python'],str(self.source/'tools/fair_comparison_20261013.py'),
                'audit','--out',str(self.out)],dispatch=False)
            require(read(self.out/'FINAL_AUDIT.json')['status']=='passed','Final scientific audit failed')
            stats=paired_statistics(rows);write(self.out/'PAIRED_STATISTICS.json',stats)
            with (self.out/'REPORT.md').open('a') as f:
                f.write('\n## 主对照配对差值\n\n|对照|指标|均值差|描述性95%区间|\n|---|---|---:|---|\n')
                for r in stats['comparisons']:f.write(f"|{r['other']}|{r['metric']}|{r['difference']:.6g}|[{r['low']:.6g},{r['high']:.6g}]|\n")
            self.save(status='complete_review_required',active_jobs={})

        def publish(self,stage):
            phase='parallel_'+stage if not stage.startswith('parallel_') else stage
            publish_snapshot(self,phase)

    return ParallelCampaign


def publish_snapshot(campaign,stage):
    """Immutable source+dispatch evidence; final includes ALL raw episodes."""
    from archive_tool_campaign_20261002 import make
    out=campaign.out;dest=out/('delivery_'+stage)
    if dest.exists():return
    dest.mkdir();evidence=dest/'evidence';evidence.mkdir()
    for p in out.iterdir():
        if p.is_file() and p.suffix in ('.json','.md'):shutil.copy2(p,evidence/p.name)
    s=read(evidence/'execution.json');s['live_campaign_status']=s['status'];s['status']='report_snapshot';write(evidence/'execution.json',s)
    shutil.copytree(campaign.source,evidence/'source',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(out/'dispatch_v3',evidence/'dispatch_v3',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    folders=('learning',) if stage=='parallel_models_locked' else ()
    if stage=='parallel_final':folders=('data','learning','dependencies','receipts','configs','metrics','evaluation')
    for folder in folders:shutil.copytree(out/folder,evidence/folder,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    archive=dict(status='pending',local=str(evidence))
    try:
        make(evidence);name=out.name+'_'+stage
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
    repo=Path(campaign.reg['repository']);docs=repo/'code/mujoco_6d_vmc_benchmark/docs'
    paths=[docs/'FAIR_COMPARISON_LIVE_20261013.md',repo/'UPDATE_LOG.md',
           docs/'ESN_VMC_JOINT_PROGRESS_20260927.md',docs/'BASELINE_WEEKLY_REPORT_20260923.md']
    try:
        assert 'UPDATE_LOG.md' in (repo/'AGENTS.md').read_text()
        assert subprocess.check_output(['git','branch','--show-current'],cwd=repo,text=True).strip()=='main'
        assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=repo,text=True).strip(),'Concurrent staged changes'
        names=[str(p.relative_to(repo)) for p in paths]
        assert not subprocess.check_output(['git','status','--porcelain','--',*names],cwd=repo,text=True).strip(),'Concurrent report edits'
        subprocess.run(['git','fetch','origin','refs/heads/main:refs/remotes/origin/main'],cwd=repo,check=True,timeout=60,capture_output=True)
        assert subprocess.run(['git','merge-base','--is-ancestor','origin/main','HEAD'],cwd=repo).returncode==0,'Remote advanced'
        content=f'# 公平性修正：实时状态\n\n{now()}；{stage}；状态 `{campaign.state["status"]}`。\n\n'
        content+='本机动态内存准入、最多4独立CPU核、每worker1线程/禁swap；完整保留39拟合/288回合原协议，服务器只归档。\n\n'
        content+='```json\n'+json.dumps(dict(archive=archive,execution=campaign.state),ensure_ascii=False,indent=2)+'\n```\n\n'
        if (out/'REPORT.md').exists():content+=(out/'REPORT.md').read_text()
        paths[0].write_text(content)
        entry=f'\n## {now()} — 公平比较并行调度 {stage}\n\n- 状态 `{campaign.state["status"]}`，已评 {campaign.state.get("evaluated",0)}/288；资源调整不改实验/模型/门槛，旧封存集未读。\n- 归档 `{archive["status"]}`，详见 `code/mujoco_6d_vmc_benchmark/docs/FAIR_COMPARISON_LIVE_20261013.md`。全部失败保留，完成前不作结果排名。\n'
        for p in paths[1:]:
            first,_,rest=p.read_text().partition('\n');p.write_text(first+'\n'+entry+'\n'+rest)
        subprocess.run(['git','add','--',*names],cwd=repo,check=True)
        subprocess.run(['git','commit','-m','Report memory-admitted fairness run '+stage,'--',*names],cwd=repo,check=True,timeout=60,capture_output=True)
        subprocess.run(['git','push','origin','HEAD:main'],cwd=repo,check=True,timeout=120,capture_output=True)
        head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
        remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/main'],cwd=repo,text=True,timeout=60).split()[0]
        assert head==remote,'Push verification';write(dest/'GIT_STATUS.json',dict(status='pushed_verified',commit=head))
    except Exception as exc:write(dest/'GIT_STATUS.json',dict(status='pending',error=repr(exc)))


def run(out):
    amend=read(out/'dispatch_v3/REGISTRATION.json')
    assert sha(Path(__file__))==amend['source_sha256']
    # Wait without the global simulator lock. Avoid original publisher races.
    while True:
        p=subprocess.run(['systemctl','--user','is-active',amend['previous_service']],capture_output=True,text=True)
        if p.stdout.strip() not in ('active','activating','deactivating'):break
        if datetime.now(timezone.utc)>=datetime.fromisoformat(amend['original_deadline_utc']):raise RuntimeError('Deadline while waiting')
        time.sleep(5)
    previous=out/'dispatch_v3/PREVIOUS_EXECUTION.json'
    if not previous.exists():shutil.copy2(out/'execution.json',previous)
    state=read(previous)
    assert state.get('error')=="ValueError('Stop requested at boundary')",'Unexpected predecessor failure; do not mask it'
    cls=build_class(out);campaign=cls(out)
    campaign.state.pop('ended_utc',None);campaign.state.pop('error',None)
    campaign.save(dispatcher='parallel_v3',handoff_completed_utc=now(),previous_execution_sha256=sha(previous))
    campaign.run()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','run','memory-receipt'));p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.mode=='memory-receipt':memory_receipt(a.out)
    elif a.mode=='prepare':prepare(a.out.resolve())
    else:run(a.out.resolve())


if __name__=='__main__':main()
