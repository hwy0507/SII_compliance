"""Continue four fully finished and reviewed stages without stopping old jobs.

Requires immutable complete-cycle archives and an explicit scientific decision
receipt. Does not decide whether to change an algorithm or declare convergence.
A failure preserves any launched jobs; never retry into an existing output.
"""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import torch
from validate_published_finite_check_20261025 import digest

METHODS=('direct','impedance','admittance','vmc')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');tmp.replace(path)


def verify_boundary(state,finished,method,parent_digest,cycle,review_hash):
    if (state['boundary']!='complete_condition_cycle' or state['controller']!=method
        or state['protocol_sha256']!=parent_digest or state['cycle']!=cycle
        or state['steps']!=finished['steps'] or finished['status']!='stopped_at_complete_cycle'):
        raise ValueError('Parent is not the reviewed complete boundary: '+method)
    if review_hash is None:raise ValueError('Missing reviewed checkpoint identity')


def prepare_state(state,factor,target_count=None):
    result=copy.deepcopy(state)
    before=digest(state)
    groups=result['learner']['actor_optimizer']['param_groups']
    if factor not in (None,.1):raise ValueError('Unregistered learning-rate intervention')
    receipt=dict(parent_full_state_sha256=before,actor_lr_before=[g['lr'] for g in groups])
    if factor is not None:
        if any(abs(g['lr']-3e-4)>1e-12 for g in groups):raise ValueError('Expected parent actor LR3e-4')
        for group in groups:group['lr']*=factor
        # Prevent pooling unlike objective/optimizer stages in plateau summaries.
        result['cycles']=[]
    if target_count is not None:
        if (target_count != 5 or factor is not None
                or state['learner'].get('bellman_target_count', 2) != 2
                or state['learner'].get('algorithm') != 'cheq'):
            raise ValueError('Only explicit CHEQ pair-to-five target intervention is supported')
        result['learner']['bellman_target_count'] = target_count
        result['cycles'] = []
    check=copy.deepcopy(result)
    if target_count is not None:
        if 'bellman_target_count' in state['learner']:
            check['learner']['bellman_target_count'] = state['learner']['bellman_target_count']
        else:
            check['learner'].pop('bellman_target_count')
    check['cycles']=copy.deepcopy(state['cycles'])
    for new,old in zip(check['learner']['actor_optimizer']['param_groups'],state['learner']['actor_optimizer']['param_groups']):
        new['lr']=old['lr']
    if digest(check)!=before or digest(state)!=before:raise AssertionError('Unexpected learning-state mutation')
    receipt.update(actor_lr_after=[g['lr'] for g in groups],all_other_state_exact=True,
        cycle_history_cleared=factor is not None or target_count is not None,
        bellman_target_count_before=state['learner'].get('bellman_target_count',2),
        bellman_target_count_after=result['learner'].get('bellman_target_count',2),
        prepared_full_state_sha256=digest(result))
    return result,receipt


def main(args):
    torch.set_num_threads(1)
    p=json.loads(args.registration.read_text());stage=p['completed_stage_continuation']
    for name,expected in stage['dispatch_source_hashes'].items():
        if sha(Path(__file__).with_name(name))!=expected:raise ValueError('Frozen dispatcher drift')
    if stage['new_cycles']!=2:raise ValueError('Expected two newly registered complete cycles before review')
    runtime=Path(p['runtime']);parent=Path(stage['parent_run'])
    if sha(runtime/'RUNTIME.json')!=p['runtime_sha256']:raise ValueError('Runtime drift')
    review_path=Path(stage['review']['path'])
    if sha(review_path)!=stage['review']['sha256']:raise ValueError('Scientific review receipt drift')
    review=json.loads(review_path.read_text());factor=stage['actor_learning_rate_factor']
    target_count=stage.get('bellman_target_count')
    expected_action='continue_registered_bellman_stage' if target_count is not None else 'continue_registered_stage'
    if target_count is not None and review['decision'].get('bellman_target_count') != target_count:
        raise ValueError('Bellman stage does not match scientific review')
    if (review['decision']['action']!=expected_action or review['cycle']!=stage['parent_cycle']
        or review['decision']['actor_learning_rate_factor']!=factor or not review['all_four_methods_reviewed']):
        raise ValueError('Continuation does not match explicit full-stage review')
    diagnosis=Path(review['diagnosis']['path'])
    if sha(diagnosis)!=review['diagnosis']['sha256']:raise ValueError('Reviewed diagnosis drift')
    diagnosed=json.loads(diagnosis.read_text())
    if diagnosed['cycle']!=stage['parent_cycle']:raise ValueError('Wrong diagnosed stage')
    sys.path.insert(0,str(runtime/'source/tools'))
    from train_published_compliance_20261025 import validate_resume_protocol, registered_stage_actor_rates
    pdigest=p['resume_parent_registration']['sha256']
    validate_resume_protocol(pdigest,p,sha(args.registration))
    jobs=json.loads((parent/'LAUNCH.json').read_text())['jobs']
    if sorted(j['controller'] for j in jobs)!=sorted(METHODS):raise ValueError('Expected four unique parent jobs')
    # Validate every parent before creating output or starting any replacement.
    parents={}
    for job in jobs:
        method=job['controller'];folder=parent/method;proc=Path('/proc',str(job['pid']),'cmdline')
        if proc.exists() and str(folder).encode() in proc.read_bytes():
            raise ValueError('Parent learner remains live: '+method)
        if (folder/'FAILURE.json').exists():raise ValueError('Parent failed: '+method)
        execution=json.loads((folder/'EXECUTION.json').read_text());finished=json.loads((folder/'FINISHED.json').read_text())
        if execution['protocol_sha256']!=pdigest:raise ValueError('Parent registration mismatch')
        checkpoint=parent/'cycle_archive'/method/f"cycle_{stage['parent_cycle']:05d}.pt"
        expected=diagnosed['methods'][method]['checkpoint_sha256']
        if not diagnosed['methods'][method]['network_state_unchanged'] or sha(checkpoint)!=expected:
            raise ValueError('Parent archive not covered by invariant diagnosis')
        state=torch.load(checkpoint,map_location='cpu',weights_only=False)
        verify_boundary(state,finished,method,pdigest,stage['parent_cycle'],expected)
        registered_before,_=registered_stage_actor_rates(stage)
        actual_before=[g['lr'] for g in state['learner']['actor_optimizer']['param_groups']]
        if (len(actual_before)!=len(registered_before)
                or any(not math.isfinite(a) or abs(a-b)>1e-12 for a,b in zip(actual_before,registered_before))):
            raise ValueError('Parent actor learning rate differs from registration: '+method)
        parents[method]=dict(checkpoint=str(checkpoint),sha256=expected,steps=state['steps'],
            updates=state['learner']['num_gradient_steps'],execution=execution,job=job)
        del state
    args.output.mkdir(exist_ok=False);(args.output/'parent_checkpoints').mkdir();launched=[];children={}
    env=dict(os.environ,MUJOCO_GL='disable',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
    write(args.output/'DISPATCH.json',dict(pid=os.getpid(),registration_sha256=sha(args.registration),
        started_unix=time.time(),parents=parents,review_sha256=sha(review_path),no_stop_requests=True))
    try:
        for method in METHODS:
            parent_info=parents[method];job=parent_info['job'];execution=parent_info['execution']
            state=torch.load(parent_info['checkpoint'],map_location='cpu',weights_only=False)
            prepared,receipt=prepare_state(state,factor,target_count)
            path=args.output/'parent_checkpoints'/(method+'.pt');torch.save(prepared,path)
            receipt.update(parent_checkpoint_sha256=parent_info['sha256'],prepared_checkpoint_sha256=sha(path),
                no_auxiliary_weights=True,review_sha256=sha(review_path))
            write(path.with_suffix('.json'),receipt);del state,prepared
            command=[sys.executable,'-B',str(runtime/'source/tools/train_published_compliance_20261025.py'),
                '--runtime',str(runtime),'--registration',str(args.registration),'--output',str(args.output/method),
                '--controller',method,'--algorithm',execution['algorithm'],'--seed',str(execution['seed']),
                '--device',execution['device'],'--cpus',','.join(map(str,job['cpus'])),
                '--workers',str(execution['workers']),'--resume',str(path),'--cycles',str(stage['new_cycles'])]
            with (args.output/(method+'.log')).open('x') as log:
                child=subprocess.Popen(command,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            children[method]=child;launched.append(dict(controller=method,pid=child.pid,gpu=job['gpu'],cpus=job['cpus'],command=command))
            write(args.output/'LAUNCH.json',dict(jobs=launched,parent_run=str(parent),registration=str(args.registration)))
        deadline=time.monotonic()+600
        while True:
            progress={}
            for method,child in children.items():
                if child.poll() is not None:raise RuntimeError('New learner exited during startup: '+method)
                path=args.output/method/'PROGRESS.json'
                if path.exists():progress[method]=json.loads(path.read_text())
            write(args.output/'STARTUP_PROGRESS.json',dict(updated_unix=time.time(),progress=progress))
            if len(progress)==4 and all(progress[m]['steps']>parents[m]['steps'] and progress[m]['updates']>parents[m]['updates'] for m in METHODS):break
            if time.monotonic()>deadline:raise TimeoutError('Startup observation expired; inspect existing jobs before any action')
            time.sleep(5)
        with (args.output/'cycle_archive.log').open('x') as log:
            monitor=subprocess.Popen(['taskset','-c',str(stage['archive_cpu']),sys.executable,'-B',
                str(runtime/'source/tools/archive_published_cycle_checkpoints_20261025.py'),'--run',str(args.output),
                '--output',str(args.output/'cycle_archive')],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write(args.output/'STARTUP_FINISHED.json',dict(ended_unix=time.time(),all_learners_updated=True,
            archive_pid=monitor.pid,convergence_claim=False))
    except BaseException as error:
        write(args.output/'DISPATCH_FAILURE.json',dict(error=repr(error),launched=launched,
            note='Existing launched jobs are preserved. Inspect handles and receipts; do not repeat dispatch.'))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--registration',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    main(parser.parse_args())
