"""Preserve the accidental CPU restore probe separately from registered CUDA training.

Read saved physical substeps and provenance; never run a policy or modify history.
The original ad-hoc outer receipts are incomplete and remain untouched. Inner
worker executions and frozen checkpoints provide the independently checked inputs.
"""
import argparse
from pathlib import Path
import shutil
import statistics

from office_v7_uniform24_20261008 import read, write, sha, now
from audit_local_rl_development_20261009 import audit_run
from launch_rl_convergence_20261010 import verify_checkpoint
from local_rl_campaign_20261009 import hashes

OVERLAYS = ('scale_rl/agents/jax_utils/network.py', 'scale_rl/agents/wrappers/normalization.py')
NAME = 'parameter_impedance_historical_entropy_step165000'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('capture','audit'))
    for arg in ('root','parent','output'):
        p.add_argument('--'+arg,type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();parent=a.parent.resolve();out=a.output.resolve()
    protocol=read(root/'PROTOCOL.json');runtime=Path(protocol['runtime'])/'SimbaV2'
    if a.mode=='capture':
        assert not out.exists()
        old=read(root/'RUNTIME_HASHES.json')['SimbaV2'];actual=hashes(runtime)
        changed={k:dict(registered=old.get(k),actual=actual.get(k)) for k in set(old)|set(actual) if old.get(k)!=actual.get(k)}
        assert set(changed)==set(OVERLAYS), changed
        out.mkdir(parents=True)
        for name in OVERLAYS:
            target=out/'runtime_overlay'/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(runtime/name,target)
        shutil.copy2('/tmp/continue_pending_rl_eval.sh',out/'actual_ad_hoc_dispatch.sh')
        shutil.copy2(__file__,out/Path(__file__).name)
        write(out/'PROVENANCE.json',dict(created_utc=now(),runtime_differences=changed,
            actual_backend='cpu',checkpoint_step=97625,registered_target_step=165000,
            experiment_role='post-hoc development compatibility probe; not registered CUDA node',
            faults=['Sandbox-only GPU query was mistaken for host driver failure; host RTX5080 is healthy',
                'Initial shell launch lacked host bus access; no simulation started',
                'Direct CPU load failed CUDA sharding; no simulation started',
                'First target-aware restore lacked required memory cgroup and was rejected',
                'Relative training_protocol path failed before physics; absolute manifest used in later run'],
            limitations=['CPU/GPU numerical equivalence has not been established',
                'Early ad-hoc receipts did not contain complete commands or artifact hash maps',
                'Runtime was patched in place for this probe; snapshot preserved before exact restoration',
                'No training was performed during this CPU probe; do not label it a 165k result'],
            preserved_dispatch_sha256=sha(out/'actual_ad_hoc_dispatch.sh')))
        return
    assert not (out/'AUDIT.json').exists()
    state,cp=verify_checkpoint(parent/NAME)
    assert state['steps']==97625
    manifest=read(parent/(NAME+'.checkpoint_cpu_restore.json'))
    assert manifest['hashes']==cp['hashes'] and manifest['checkpoint']==cp['path']
    assert sha(manifest['training_protocol'])==manifest['training_protocol_sha256']
    conditions=[c for c in read(root/'CONDITIONS.json')['conditions'] if c['role']=='development']
    assert len(conditions)==8
    rows=[]
    for c in conditions:
        name=NAME+'__'+c['id']
        if c['id'].endswith('_000'):name+='_cpu_restore_retry_v3'
        run=parent/name
        execution=read(run/'execution.json');role=read(run/'REPAIR_ROLE.json')
        assert execution['status']=='complete' and int(execution['memory_max'])==3*1024**3
        assert role['condition']==c and role['protocol_sha256']==sha(root/'PROTOCOL.json')
        assert read(run/'ADAPTED_RL_CHECKPOINT.json')==manifest
        pa=read(run/'INDEPENDENT_PARAMETER_AUDIT.json');assert pa['status']=='passed'
        for path,digest in pa['evidence'].items():assert sha(path)==digest
        files=[run/'execution.json',run/'AUDIT.json',run/'REPAIR_ROLE.json',run/'INDEPENDENT_PARAMETER_AUDIT.json']
        row=audit_run(run,{'artifacts':{str(f):sha(f) for f in files}},protocol)
        rows.append(dict(row,condition=c['id'],inner_execution_sha256=sha(run/'execution.json')))
    write(out/'AUDIT.json',dict(status='passed',created_utc=now(),checkpoint=cp,steps=97625,
        backend='cpu',registered_cuda_node=False,completed=len(rows),rows=rows,
        task=sum(r['task'] for r in rows),strict=sum(r['strict'] for r in rows),
        means={k:statistics.mean(r[k] for r in rows) for k in ('rmse_mm','peak_torque_nm','peak_speed_mps')},
        physics_steps_recomputed=sum(r['physical_steps'] for r in rows),new_physics_steps=0,
        final_test_reads=0,gradient_updates=0,provenance_sha256=sha(out/'PROVENANCE.json')))
    print('CPU probe independently audited; excluded from CUDA node matrix',flush=True)


if __name__=='__main__':main()
