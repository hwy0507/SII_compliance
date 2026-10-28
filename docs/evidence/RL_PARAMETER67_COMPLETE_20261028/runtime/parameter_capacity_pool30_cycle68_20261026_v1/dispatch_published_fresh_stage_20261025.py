"""Dispatch a reviewed fresh CHEQ stage after named jobs release their CPUs.

No checkpoint/replay import, no stopping existing processes, no retries. Each
learner has a finite registered number of complete balanced condition cycles.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, data):
    tmp=path.with_suffix('.tmp')
    tmp.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def identity(pid):
    try:
        stat=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()
        return None if stat[0]=='Z' else stat[19]
    except FileNotFoundError:
        return None


def validate(protocol, plan, allowed):
    if any(protocol.get(k) for k in ('recovered_replay','resume_parent_registration',
                                    'critic_restart','completed_stage_continuation')):
        raise ValueError('Fresh stage cannot import replay or continuation state')
    if protocol['algorithms']!=['cheq'] or protocol['reward']['gamma']!=.9995:
        raise ValueError('Expected original CHEQ pair target and long-horizon objective')
    if (protocol['learner_batch_size'],protocol['learner_updates_per_transition'])!=(256,1):
        raise ValueError('Expected registered reduced replay reuse')
    if plan['cycles']!=6 or plan['seed'] not in protocol['seeds']:
        raise ValueError('Expected six complete cycles and registered seed')
    if {j['controller'] for j in plan['jobs']}!=set(protocol['controllers']) or len(plan['jobs'])!=4:
        raise ValueError('Expected four unique interfaces')
    used=set(plan['reserved_cpus'])|{plan['coordinator_cpu']}
    for job in plan['jobs']:
        cpus=job['cpus']
        if (len(cpus)!=job['workers']+1 or len(set(cpus))!=len(cpus)
                or not set(cpus)<=set(allowed) or set(cpus)&used):
            raise ValueError('CPU allocation conflict')
        used.update(cpus)
        if not job['wait_for']:
            raise ValueError('Require explicit resource-release evidence')


def resources_released(job):
    for previous in job['wait_for']:
        current=identity(previous['pid'])
        if current==previous['start_ticks']:
            return False
        if current is not None:
            raise ValueError('PID reused; inspect resource ownership before dispatch')
        path=Path(previous['finished'])
        if not path.exists():
            raise RuntimeError('Named process exited without successful completion receipt')
        receipt=json.loads(path.read_text())
        if any(receipt.get(k)!=v for k,v in previous['expected'].items()):
            raise ValueError('Resource release receipt does not match expected completion')
    return True


def main(args):
    plan=json.loads(args.plan.read_text());registration=Path(plan['registration'])
    if sha(registration)!=plan['registration_sha256'] or sha(__file__)!=plan['dispatcher_sha256']:
        raise ValueError('Registered dispatch source/protocol drift')
    p=json.loads(registration.read_text());validate(p,plan,os.sched_getaffinity(0))
    root=Path(p['runtime']);out=Path(plan['output']);cpu=plan['coordinator_cpu']
    review=Path(plan['scientific_review']['path'])
    if sha(review)!=plan['scientific_review']['sha256']:
        raise ValueError('Scientific decision drift')
    if json.loads(review.read_text())['decision']!='start_fresh_reduced_reuse_stage':
        raise ValueError('Fresh stage not selected by scientific review')
    if sha(root/'RUNTIME.json')!=p['runtime_sha256']:
        raise ValueError('Frozen runtime drift')
    archive=Path(plan['archive_tool'])
    if sha(archive)!=plan['archive_tool_sha256']:
        raise ValueError('Archive source drift')
    os.sched_setaffinity(0,{cpu});out.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,MUJOCO_GL='disable',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    launched=[];children={}
    write(out/'DISPATCH.json',dict(pid=os.getpid(),plan=str(args.plan),plan_sha256=sha(args.plan),started_unix=time.time()))
    try:
        with (out/'migration_archive.log').open('xb') as log:
            observer=subprocess.Popen([sys.executable,'-B',str(archive),'--run',str(out),
                '--output',str(out/'early_archive'),'--migration-only'],env=env,
                stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(out/'EARLY_ARCHIVE.json',dict(pid=observer.pid,note='Follows growing LAUNCH; no learner migration'))
        while True:
            if (out/'DISPATCH_STOP').exists():
                write(out/'DISPATCH_STOPPED.json',dict(launched=launched));return
            for job in plan['jobs']:
                method=job['controller']
                if method in children:
                    if children[method].poll() is not None:
                        raise RuntimeError('Fresh learner exited before dispatch completion: '+method)
                    continue
                if not resources_released(job):continue
                if sha(registration)!=plan['registration_sha256']:
                    raise ValueError('Registration changed while waiting')
                command=[sys.executable,'-B',str(root/'source/tools/train_published_compliance_20261025.py'),
                    '--runtime',str(root),'--registration',str(registration),'--output',str(out/method),
                    '--controller',method,'--algorithm','cheq','--seed',str(plan['seed']),
                    '--device','cuda:'+str(job['gpu']),'--cpus',','.join(map(str,job['cpus'])),
                    '--workers',str(job['workers']),'--cycles',str(plan['cycles'])]
                os.sched_setaffinity(0,set(job['cpus'])|{cpu})
                try:
                    with (out/(method+'.log')).open('xb') as log:
                        child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                                               env=env,start_new_session=True)
                finally:os.sched_setaffinity(0,{cpu})
                children[method]=child
                launched.append(dict(controller=method,pid=child.pid,gpu=job['gpu'],cpus=job['cpus'],command=command))
                write(out/'LAUNCH.json',dict(jobs=launched,registration=str(registration),fresh=True))
            progress={m:json.loads((out/m/'PROGRESS.json').read_text()) for m in children if (out/m/'PROGRESS.json').exists()}
            write(out/'DISPATCH_PROGRESS.json',dict(updated_unix=time.time(),launched=list(children),progress=progress))
            if len(progress)==4 and all(v['updates']>0 for v in progress.values()):
                with (out/'cycle_archive.log').open('xb') as log:
                    observer=subprocess.Popen([sys.executable,'-B',str(archive),'--run',str(out),
                        '--output',str(out/'cycle_archive')],env=env,stdout=log,
                        stderr=subprocess.STDOUT,start_new_session=True)
                # Existing read-only archive uses this flag for growing-LAUNCH handoff.
                write(out/'MIGRATION_FINISHED.json',dict(scope='archive_handoff_only_no_learner_migration',archive_pid=observer.pid))
                write(out/'DISPATCH_FINISHED.json',dict(ended_unix=time.time(),all_four_updated=True,convergence_claim=False));return
            time.sleep(5)
    except BaseException as error:
        write(out/'MIGRATION_FAILURE.json',dict(scope='archive_stop_flag',error=repr(error)))
        write(out/'DISPATCH_FAILURE.json',dict(error=repr(error),launched=launched,note='Preserve launched learners and inspect; no automatic retry'))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    main(parser.parse_args())
