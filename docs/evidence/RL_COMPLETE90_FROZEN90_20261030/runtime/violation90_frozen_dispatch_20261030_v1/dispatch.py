"""Explicit finite frozen90 dispatch after complete review and exact restores."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
D=Path(__file__).resolve().parent;B=D.parents[1]
P=B/'runtime/violation90_frozen_preparation_20261030_v1';R=B/'runs/parameter90_violation_frozen_full30_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def sources():
    registration=read(D/'SOURCES.json')
    for n,h in registration['files'].items():assert sha(D/n)==h
    return registration

def validate_final():
    sources()
    sys.path.insert(0,str(P))
    from register_complete90 import validate_inputs
    expected=validate_inputs()
    assert read(R/'REGISTERED.json')['exact_restore_check_only_still_required']
    for m,reg in expected.items():assert read(R/m/'REGISTRATION.json')==reg
    return expected

def check():
    regs=validate_final()
    assert not (R/'CHECK_ONLY_LAUNCH.json').exists()
    jobs=[]
    for m in regs:
        command=[str(B/'env/bin/python'),'-u',str(P/'evaluate_violation90.py'),'--registration',str(R/m/'REGISTRATION.json'),'--check-only']
        jobs.append(dict(controller=m,command=command,registration_sha256=sha(R/m/'REGISTRATION.json')))
    put(R/'CHECK_ONLY_LAUNCH.json',dict(time=time.time(),jobs=jobs,physics_steps=0,optimizer_updates=0,dispatcher_sha256=sha(__file__)))
    for job in jobs:
        folder=R/job['controller']
        with (folder/'check_only.log').open('x') as log:
            subprocess.run(job['command'],check=True,stdout=log,stderr=subprocess.STDOUT,timeout=1800,
                env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        result=read(folder/'CHECK_ONLY_REVIEW.json')
        assert result['passed'] and result['validated_parent_cycle']==90
        assert result['full_replay_restored_exact'] and result['full_learner_state_unchanged']
        assert result['checkpoint_sha256']==regs[job['controller']]['checkpoint_sha256']
    put(R/'CHECK_ONLY_COMPLETE.json',dict(time=time.time(),passed=True,
        reviews={m:sha(R/m/'CHECK_ONLY_REVIEW.json') for m in regs},
        registrations={m:sha(R/m/'REGISTRATION.json') for m in regs},physics_steps=0,optimizer_updates=0))

def launch():
    regs=validate_final();checked=read(R/'CHECK_ONLY_COMPLETE.json');assert checked['passed']
    assert read(B/'runtime/history88_frozen_postprocess_20261030_v1/FINISHED.json')['passed']
    assert not (R/'LAUNCH_AUTHORIZATION.json').exists()
    assert not (R/'LAUNCH.json').exists() and not (R/'PLAN.json').exists()
    pre=read(R/'PRE_REGISTRATION.json');cases=next(iter(regs.values()))['case_ids']
    for m,reg in regs.items():
        assert sha(R/m/'REGISTRATION.json')==checked['registrations'][m]
        assert sha(R/m/'CHECK_ONLY_REVIEW.json')==checked['reviews'][m]
        assert reg['case_ids']==cases and reg['action_seed']==2026102638
        assert not (R/m/'EVALUATION.json').exists() and not (R/m/'FAILURE.json').exists()
    plan=dict(time=time.time(),preregistration=dict(path=str(R/'PRE_REGISTRATION.json'),sha256=sha(R/'PRE_REGISTRATION.json')),
        parent_cycle=90,controllers=list(regs),case_ids=cases,episodes=90,maximum_actions=123750,
        maximum_substeps=99000000,action_seed=2026102638,optimizer_updates=0,replay_writes=0,
        exact_restore_review_sha256=sha(R/'CHECK_ONLY_COMPLETE.json'),dispatcher_sha256=sha(__file__),
        collector_sha256=sha(D/'review_frozen90.py'),automatic_training=False,
        scope=pre['scope'])
    put(R/'PLAN.json',plan)
    put(R/'LAUNCH_AUTHORIZATION.json',dict(time=time.time(),parent_cycle=90,registration_hashes={m:sha(R/m/'REGISTRATION.json') for m in regs},episodes=90,maximum_actions=123750,maximum_substeps=99000000,optimizer_updates=0,plan_sha256=sha(R/'PLAN.json'),scope='Explicit finite dispatch after complete90 scientific review, actual plot inspection and all3 exact check-only restores; no automatic training.'))
    jobs=[]
    for m in regs:
        command=[str(B/'env/bin/python'),'-u',str(P/'evaluate_violation90.py'),'--registration',str(R/m/'REGISTRATION.json')]
        with (R/m/'evaluator.log').open('x') as log:
            proc=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
                env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'))
        fields=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split()
        job=dict(controller=m,command=command,pid=proc.pid,start=fields[19],time=time.time())
        put(R/(m+'_LAUNCH.json'),job);jobs.append(job)
    put(R/'LAUNCH.json',dict(time=time.time(),jobs=jobs,plan_sha256=sha(R/'PLAN.json'),automatic_followup=False))
    put(R/'REVIEW_REGISTRATION.json',dict(evaluators=jobs,source_sha256=sha(D/'review_frozen90.py'),plan_sha256=sha(R/'PLAN.json')))
    with (R/'review.log').open('x') as log:
        proc=subprocess.Popen([str(B/'env/bin/python'),'-u',str(D/'review_frozen90.py'),'--root',str(R)],
            stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    fields=Path(f'/proc/{proc.pid}/stat').read_text().rsplit(')',1)[1].split()
    put(R/'REVIEW_LAUNCH.json',dict(pid=proc.pid,start=fields[19],time=time.time()))
    print(json.dumps(jobs),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['check','launch']);args=parser.parse_args()
    try:
        check() if args.mode=='check' else launch()
    except BaseException as e:
        import traceback
        put(D/(args.mode+'_FAILURE_'+str(time.time_ns())+'.json'),dict(error=repr(e),traceback=traceback.format_exc()));raise
