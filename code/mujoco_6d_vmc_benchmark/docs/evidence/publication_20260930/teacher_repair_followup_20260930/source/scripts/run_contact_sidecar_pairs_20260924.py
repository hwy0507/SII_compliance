"""Freeze and execute only three contact sidecar on/off pairs, <=2 workers."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import numpy as np


def read(p):return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def dump(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n');tmp.replace(p)
def files(root):return {str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}
def replace_flag(command,flag,value):command[command.index(flag)+1]=str(value)


def canonical_contact(contact):
    """Only fields explicitly serialized from sets are order-insensitive."""
    out=dict(contact)
    for key in ('pairs','robot_geoms','robot_bodies','other_contacts'):
        out[key]=sorted(out[key])
    return out


def prepare(a):
    if a.output.exists():raise FileExistsError('Fresh output required')
    pairs=[('vmc',9403),('mlp',9400),('esn',9403)]
    a.output.mkdir(parents=True);source=a.output/'source_snapshot';shutil.copytree(a.source,source,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    audit=a.output/'audit_tools';audit.mkdir()
    for name in ('contact_substep_sidecar_20260924.py','run_with_contact_sidecar_20260924.py','run_contact_sidecar_pairs_20260924.py'):
        shutil.copy2(Path(__file__).with_name(name),audit/name)
    shutil.copy2(a.specification,a.output/'specification.md')
    jobs=[]
    for method,seed in pairs:
        original=a.validation/method/str(seed);record=read(original/'command.json')
        for enabled in (False,True):
            id=f'{method}_{seed}_'+('on' if enabled else 'off');directory=a.output/'jobs'/id
            command=[str(v).replace(str(a.source),str(source)) for v in record['command']]
            replace_flag(command,'--metrics-output',directory/'metrics');replace_flag(command,'--output',directory/'rollout/rollout')
            env={k:str(v).replace(str(a.source),str(source)) for k,v in record['environment'].items()}
            env.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',MUJOCO_GL='egl')
            outer=[sys.executable,str(audit/'run_with_contact_sidecar_20260924.py'),'--runner',command[1],
                '--frozen-scripts',str(source/'scripts'),'--contact-output',str(directory/'contact')]
            if not enabled:outer+=['--disable-contact']
            outer+=['--',*command[2:]]
            job=dict(id=id,method=method,seed=seed,enabled=enabled,directory=str(directory),historical_job=str(original),
                command=outer,environment=env,historical_model_sha256=sha(original/'rollout/rollout.mjb'),
                historical_trace_sha256=sha(original/'rollout/rollout.npz'))
            if a.reuse_first_pair and (method,seed)==pairs[0]:
                old=a.reuse_first_pair/'jobs'/id
                if read(old/'exit.json')['returncode']!=0:raise ValueError('Cannot reuse unsuccessful runner')
                directory.parent.mkdir(exist_ok=True)
                shutil.copytree(old,directory,copy_function=os.link)
                job.update(reused_from=str(old),reused_files_sha256=files(old))
            jobs.append(job)
    protocol=dict(version=2,created_unix=time.time(),scope='read-only contact instrumentation diagnostic; no controller/physics/gate change',
        max_workers=2,pairs=[dict(method=m,seed=s) for m,s in pairs],jobs=jobs,
        source=str(source),source_sha256=files(source),original_source=str(a.source),original_source_sha256=files(a.source),
        audit_tools_sha256=files(audit),specification_sha256=sha(a.output/'specification.md'),
        original_models=read(a.validation.parent/'protocol.json')['frozen_models'],
        stop_on_first_pair_invariance_failure=True,simulation_duration_s=24.,expected_physical_samples=480000,
        new_simulations=4 if a.reuse_first_pair else 6,
        reused_first_pair_root=str(a.reuse_first_pair) if a.reuse_first_pair else None,
        comparison_correction='sort only contact pairs/robot_geoms/robot_bodies/other_contacts serialized from sets; all numeric arrays and values remain exact')
    assert protocol['source_sha256']==protocol['original_source_sha256']
    dump(a.output/'protocol.json',protocol);dump(a.output/'READY.json',dict(protocol_sha256=sha(a.output/'protocol.json')))
    for root in (source,audit):
        for p in root.rglob('*'):
            if p.is_file():p.chmod(0o444)
    print(json.dumps(dict(prepared=str(a.output),jobs=len(jobs),protocol_sha256=sha(a.output/'protocol.json'))))


def compare_npz(left,right):
    with np.load(left,allow_pickle=False) as a,np.load(right,allow_pickle=False) as b:
        if set(a.files)!=set(b.files):raise ValueError('Array keys differ: '+str(left))
        differences=[key for key in a.files if not np.array_equal(a[key],b[key])]
        if differences:raise ValueError('Arrays differ '+str(left)+': '+str(differences))
        return dict(arrays=len(a.files),identical=True,left_sha256=sha(left),right_sha256=sha(right))


def verify_pair(pair,jobs):
    off,on=[Path(j['directory']) for j in sorted(jobs,key=lambda j:j['enabled'])];historical=Path(jobs[0]['historical_job'])
    checks={}
    for name in ('rollout.npz','contact_samples.npz','physics_states.npz'):
        checks['on_off_'+name]=compare_npz(on/'rollout'/name,off/'rollout'/name)
        checks['off_history_'+name]=compare_npz(off/'rollout'/name,historical/'rollout'/name)
    checks['on_off_physical']=compare_npz(on/'metrics/episode_0/substep_metrics.npz',off/'metrics/episode_0/substep_metrics.npz')
    checks['off_history_physical']=compare_npz(off/'metrics/episode_0/substep_metrics.npz',historical/'metrics/episode_0/substep_metrics.npz')
    result=read(on/'rollout/rollout.json');other=read(off/'rollout/rollout.json');old=read(historical/'rollout/rollout.json')
    for key in ('success','accepted_panel_demo','panel_audit','contact','endpoint_error_m','lift_m'):
        values=[r[key] for r in (result,other,old)]
        if key=='contact':values=[canonical_contact(v) for v in values]
        if values[0]!=values[1] or values[1]!=values[2]:raise ValueError('Original audit changed: '+key)
    model_hashes=[sha(p/'rollout/rollout.mjb') for p in (on,off,historical)]
    if len(set(model_hashes))!=1:raise ValueError('MJB differs')
    audit=read(on/'contact/manifest.json')
    if audit['error'] or len(audit['episodes'])!=1:raise ValueError('Contact audit incomplete')
    episode=audit['episodes'][0]
    if episode['samples']!=480000:raise ValueError('Incomplete episode')
    for i,name in enumerate(episode['obstacle_names']):
        if episode['max_depth_m'][i]!=result['panel_audit']['contacts'][name]['max_penetration_m']:
            raise ValueError('Contact peak differs from original audit: '+name)
    # Independently recompute threshold counts and longest contiguous runs.
    thresholds=np.array(episode['thresholds_m']);counts=np.zeros((len(episode['obstacle_names']),4),dtype=np.int64)
    longest=np.zeros_like(counts);current=np.zeros_like(counts);peaks=np.zeros(counts.shape[0]);samples=0
    for part in episode['raw_chunks']:
        with np.load(on/'contact/episode_0'/part['file'],allow_pickle=False) as raw:
            depth=raw['depth_m'];samples+=len(depth)
            if not np.isfinite(depth).all():raise ValueError('Nonfinite depth')
            peaks=np.maximum(peaks,depth.max(axis=0));mask=depth[:,:,None]>=thresholds[None,None,:]
            counts+=mask.sum(axis=0)
            for sample in mask:
                current=(current+1)*sample;longest=np.maximum(longest,current)
    if samples!=480000 or not np.array_equal(peaks,episode['max_depth_m']):raise ValueError('Raw peak/sample mismatch')
    if not np.array_equal(counts,episode['thresholds']['steps_at_or_above']) or not np.array_equal(longest,episode['thresholds']['longest_consecutive_steps']):
        raise ValueError('Raw threshold duration mismatch')
    return dict(pair=pair,invariance=checks,model_sha256=model_hashes[0],contact_summary=episode,
        task_success=result['success'],accepted_panel_demo=result['accepted_panel_demo'],raw_thresholds_recomputed=True)


def execute(a):
    root=a.protocol.parent;protocol=read(a.protocol)
    if sha(a.protocol)!=read(root/'READY.json')['protocol_sha256']:raise ValueError('Protocol changed')
    if (root/'status.json').exists():raise FileExistsError('No silent restart')
    if files(Path(protocol['source']))!=protocol['source_sha256']:raise ValueError('Frozen source changed')
    if files(root/'audit_tools')!=protocol['audit_tools_sha256']:raise ValueError('Audit tool changed')
    for model in protocol['original_models'].values():
        if sha(model['path'])!=model['sha256']:raise ValueError('Model changed')
    # Audit actual running command lines; grep/parent shell text is not counted.
    running=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:parts=(proc/'cmdline').read_bytes().split(b'\0')
        except (OSError,PermissionError):continue
        if len(parts)>1 and b'python' in parts[0] and any(x in parts[1] for x in
            (b'run_with_substep_metrics',b'run_panel_push',b'run_panel_vmc_zero_parameter',b'run_with_contact_sidecar')):
            running.append(dict(pid=int(proc.name),command=parts[1].decode()))
    dump(root/'worker_check.json',dict(existing=running,maximum_own_workers=2))
    if len(running)>2:raise RuntimeError('Existing simulation workers plus2 would exceed4; wait for release')
    started=time.time();results=[];completed_jobs=[]
    def run(job):
        directory=Path(job['directory'])
        if 'reused_from' in job:
            if files(directory)!=job['reused_files_sha256']:raise ValueError('Reused first pair evidence changed')
            return dict(id=job['id'],returncode=0,reused_from=job['reused_from'])
        directory.mkdir(parents=True)
        dump(directory/'command.json',job)
        with (directory/'run.log').open('w') as log:
            done=subprocess.run(job['command'],cwd=protocol['source'],env=dict(os.environ,**job['environment']),stdout=log,stderr=subprocess.STDOUT,timeout=3600)
        row=dict(id=job['id'],returncode=done.returncode);dump(directory/'exit.json',row);return row
    try:
        for pair in protocol['pairs']:
            jobs=[j for j in protocol['jobs'] if j['method']==pair['method'] and j['seed']==pair['seed']]
            dump(root/'status.json',dict(status='running',pid=os.getpid(),pair=pair,completed_jobs=len(completed_jobs)))
            with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,jobs))
            completed_jobs+=rows;dump(root/'job_results.json',completed_jobs)
            if any(r['returncode'] for r in rows):raise RuntimeError('Runner error; preserve failed jobs, stop queue')
            result=verify_pair(pair,jobs);results.append(result);dump(root/'pair_results.json',results)
            print(json.dumps(dict(pair=pair,invariance='exact',completed_pairs=len(results))),flush=True)
        if files(Path(protocol['source']))!=protocol['source_sha256'] or files(root/'audit_tools')!=protocol['audit_tools_sha256']:
            raise ValueError('Frozen snapshot changed during run')
        dump(root/'FINAL_RESULT.json',dict(pairs=results,completed_jobs=completed_jobs,elapsed_s=time.time()-started))
        dump(root/'COMPLETE.json',dict(pairs=3,jobs=6,all_arrays_exact=True,source_unchanged=True))
        dump(root/'status.json',dict(status='complete',pid=os.getpid(),pairs=3,jobs=6))
    except BaseException as exc:
        dump(root/'status.json',dict(status='failed',pid=os.getpid(),error=f'{type(exc).__name__}: {exc}',completed_jobs=len(completed_jobs)))
        raise


def main():
    p=argparse.ArgumentParser();p.add_argument('--protocol',type=Path);p.add_argument('--source',type=Path)
    p.add_argument('--validation',type=Path);p.add_argument('--specification',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--reuse-first-pair',type=Path)
    a=p.parse_args()
    if a.protocol:execute(a)
    else:prepare(a)


if __name__=='__main__':main()
