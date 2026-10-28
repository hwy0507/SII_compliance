"""Prospective common RL boundary and one-shot, episode-safe budget governor.

Never edits the live runtime, its receipts, weights, or queued commands. For the
two legacy segments after the selected boundary, signal only their exact
learner after it has installed its handler and written execution.json. The
existing handler finishes an in-flight episode and saves normally. Any extra
training is retained and costed, but cannot change the preregistered finalist.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import time

AMENDMENT = 'AMENDMENT_RL_FINAL_BOUNDARY.json'
BOUNDARY = 49500
STAGE = 'cumulative_0049500'
EXCESS_STAGES = ('cumulative_0071500', 'cumulative_0080000')


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def now(): return datetime.now(timezone.utc).isoformat()


def write(path, value, exclusive=False):
    content = json.dumps(value, indent=2, allow_nan=False)+'\n'
    if exclusive:
        with path.open('x') as stream: stream.write(content)
    else:
        temp = path.with_suffix(path.suffix+'.tmp'); temp.write_text(content); temp.replace(path)


def option(argv, name):
    assert argv.count(name) == 1, 'Missing/duplicate option: '+name
    return argv[argv.index(name)+1]


def process_info(pid):
    proc = Path('/proc')/str(pid)
    stat = (proc/'stat').read_text().rsplit(')', 1)[1].split()
    status = dict(line.split(':', 1) for line in (proc/'status').read_text().splitlines() if ':' in line)
    return dict(pid=pid, parent=int(stat[1]), start_ticks=int(stat[19]),
                argv=[part.decode(errors='replace') for part in (proc/'cmdline').read_bytes().split(b'\0') if part],
                caught=int(status['SigCgt'].strip(), 16), uid=int(status['Uid'].split()[0]))


def find_command(command):
    found = []
    for proc in Path('/proc').glob('[0-9]*'):
        try:
            info = process_info(int(proc.name))
            if info['argv'] == command: found.append(info)
        except (FileNotFoundError, ProcessLookupError, PermissionError): continue
    assert len(found) <= 1, 'Duplicate registered process'
    return found[0] if found else None


def check_target(info, command, parent, root, campaign, model, stage):
    assert stage in EXCESS_STAGES and info['argv'] == command
    assert info['parent'] == parent['pid'] and info['uid'] == os.getuid()
    assert len(command) > 2 and Path(command[1]).name == 'research72_train_rl_20261003.py'
    assert Path(command[1]) == Path(parent['argv'][1]).with_name('research72_train_rl_20261003.py')
    assert Path(option(command, '--root')).resolve() == root.resolve()
    assert Path(option(command, '--output')).resolve() == (campaign/f'queue_{parent["queue"]}'/model/stage).resolve()
    assert int(option(command, '--steps')) == 80000
    assert int(option(command, '--stop-at-step')) == int(stage.split('_')[1])
    assert option(command, '--seed') == model.rsplit('_',1)[1]
    assert info['caught'] & (1 << (signal.SIGUSR1-1)), 'Learner handler not installed'


def signal_stop(info, command, parent, root, campaign, model, stage):
    """Pin the exact process with a pidfd; a natural exit is a polling race."""
    try:
        fd=os.pidfd_open(info['pid'])
        try:
            current=process_info(info['pid'])
            assert current['start_ticks']==info['start_ticks']
            check_target(current,command,parent,root,campaign,model,stage)
            signal.pidfd_send_signal(fd,signal.SIGUSR1)
        finally: os.close(fd)
    except (FileNotFoundError,ProcessLookupError): return False
    return True


def selected_boundary(queue, row):
    parts = [part for part in row['segments'] if part['stage'] == STAGE]
    assert len(parts) == 1, 'Missing/duplicate common boundary'
    part = parts[0]
    assert part.get('returncode') == 0
    path = queue/row['name']/STAGE/'execution.json'; state = read(path)
    assert state['status'] == 'complete' and sha(path) == part['execution_sha256']
    assert state['stop_reason'] == 'remaining_budget_less_than_one_full_episode'
    assert BOUNDARY-1375 < state['steps'] <= BOUNDARY
    manifest_path = queue/row['name']/(STAGE+'_CHECKPOINT.json'); manifest = read(manifest_path)
    assert state['checkpoint_rows'][-1]['path'] == manifest['checkpoint']
    assert state['steps'] == part['cumulative_steps'] == manifest['cumulative_physics_steps']
    assert sha(manifest['training_protocol']) == manifest['training_protocol_sha256']
    protocol = read(manifest['training_protocol'])
    assert protocol['segment_step_limit'] == BOUNDARY and protocol['maximum_new_physics_steps'] == 80000
    return dict(name=row['name'], selected_steps=state['steps'], selected_manifest=str(manifest_path),
                selected_manifest_sha256=sha(manifest_path), selected_execution=str(path),
                selected_execution_sha256=sha(path))


def final_policy(root, campaign):
    """No alternate checkpoint if any model or closure evidence is missing."""
    path=root/AMENDMENT
    if not path.exists(): return None
    amendment=read(path); output=Path(amendment['output'])
    assert amendment['protocol_sha256']==sha(root/'PROTOCOL.json')
    assert amendment['scope']=='outcome_independent_common_rl_final_boundary'
    assert amendment['active_campaign']==campaign.name and amendment['selected_stage']==STAGE
    assert amendment['selected_step_limit']==BOUNDARY and amendment['all_fifteen_models_required']
    assert not amendment['selection_uses_rewards_or_task_results'] and not amendment['sealed_contents_read']
    assert sha(campaign/'SPECIFICATION.json')==amendment['specification_sha256']
    for name in ('registration','forecast','governor_source'):
        assert sha(amendment[name])==amendment[name+'_sha256']
    execution=read(output/'execution.json');closure=read(output/'CLOSURE.json')
    assert execution['status']==closure['status']=='complete' and not execution['dry_run']
    assert execution['amendment_sha256']==closure['amendment_sha256']==sha(path)
    assert execution['source_sha256']==closure['source_sha256']==amendment['governor_source_sha256']
    assert sha(output/'CLOSURE.json')==execution['closure_sha256']
    assert {Path(entry['path']) for entry in closure['queue_executions']}=={
        campaign/f'queue_{index}/execution.json' for index in range(3)}
    for entry in closure['queue_executions']:
        assert sha(entry['path'])==entry['sha256'] and read(entry['path'])['status']=='complete'
    assert len(closure['queue_executions'])==3 and len(closure['models'])==15
    assert {model['name'] for model in closure['models']}=={
        job['name'] for job in read(campaign/'SPECIFICATION.json')['jobs']}
    return dict(amendment=amendment,closure=closure,
                evidence=[path,output/'CLOSURE.json',Path(amendment['registration']),Path(amendment['forecast']),Path(amendment['governor_source'])],
                completion=output/'execution.json')


def register(root, output, forecast):
    assert not (root/AMENDMENT).exists() and not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    assert not output.exists()
    campaign = root/'rl_office_adaptation_v2'; spec = read(campaign/'SPECIFICATION.json')
    protocol = read(root/'PROTOCOL.json')
    assert spec['protocol_sha256'] == sha(root/'PROTOCOL.json')
    assert spec['dispatch_schedule'] == 'round_robin_cumulative_boundaries'
    assert spec['cumulative_step_boundaries'] == [5500,27500,49500,71500,80000]
    assert len(spec['jobs']) == 15 and protocol['budget_caps']['rl_adaptation_steps_per_family_seed'] == 80000
    assert datetime.now(timezone.utc) < datetime.fromisoformat(spec['development_deadline_utc'])
    estimate = read(forecast)
    assert estimate['forecast_only'] and not estimate['final_condition_contents_read']
    assert estimate['optional_episodes_hypothetical'] == 0
    parents = []; snapshots = []
    for index in range(3):
        path = campaign/f'queue_{index}/execution.json'; data = path.read_bytes(); state = json.loads(data)
        assert state['status'] in ('running','waiting_for_simulation_lease')
        assert [row['name'] for row in state['rows']] == [job['name'] for job in spec['jobs'][index::3]]
        for row in state['rows']:
            for part in row['segments']:
                assert part['stage'] not in (STAGE, *EXCESS_STAGES), 'Register before any model reaches target round'
        candidates = []
        for proc in Path('/proc').glob('[0-9]*'):
            try:
                info = process_info(int(proc.name)); argv = info['argv']
                if len(argv)>2 and Path(argv[1]).name == 'research72_rl_campaign_20261003.py' and '--queue' in argv:
                    if option(argv,'--output') == str(campaign) and option(argv,'--queue') == str(index):
                        assert option(argv,'--root') == str(root) and info['uid'] == os.getuid()
                        candidates.append(info)
            except (FileNotFoundError,ProcessLookupError,PermissionError): continue
        assert len(candidates) == 1
        parents.append(dict(candidates[0], queue=index))
        snapshots.append(dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), snapshot=state))
    output.mkdir()
    receipt = dict(status='complete', created_utc=now(), source_sha256=sha(__file__),
        parents=parents, queue_snapshots=snapshots, selected_boundary_not_started=True,
        physics_steps=0, signals_sent=0, sealed_reads=0)
    write(output/'REGISTRATION.json', receipt, True)
    amendment = dict(protocol_sha256=sha(root/'PROTOCOL.json'), registered_utc=now(),
        scope='outcome_independent_common_rl_final_boundary', active_campaign=campaign.name,
        specification_sha256=sha(campaign/'SPECIFICATION.json'), selected_stage=STAGE, selected_step_limit=BOUNDARY,
        original_optimizer_schedule_steps=80000, original_exposure_cap=80000,
        all_fifteen_models_required=True, selection_uses_rewards_or_task_results=False, sealed_contents_read=False,
        rationale='Measured serial queue capacity threatens the complete38x24 final matrix within72h. Use the existing common49500 round prospectively for every RL family/seed.',
        preserved=['all5families and3seeds','original model/reward/optimizer schedule','all failed and short episodes',
                   'live runtime and receipts','formal physics/gates/actuator limits','full final38x24matrix'],
        selector='Every model uses the natural completed49500-stage boundary, never later outcome-ranked weights.',
        episode_budget_range=[BOUNDARY-1374,BOUNDARY],
        excess_stages=list(EXCESS_STAGES), maximum_compatibility_extra_steps_per_model=2750,
        compatibility='Immutable coordinators still dispatch their two later stages. SIGUSR1 to exact handler-ready learner finishes at most one in-flight1375-step episode per later stage. All extra cost/data remain; final weight is the earlier common boundary.',
        forecast=str(forecast.resolve()), forecast_sha256=sha(forecast),
        registration=str(output/'REGISTRATION.json'), registration_sha256=sha(output/'REGISTRATION.json'),
        output=str(output), governor_source=str(Path(__file__).resolve()), governor_source_sha256=sha(__file__),
        completion='Requires natural queue closure, all15 common boundaries, exact parent identities and immutable evidence. No missing model replacement or outcome-based cutoff.')
    write(root/AMENDMENT, amendment, True)
    return amendment


def watch(root, output, dry_run=False):
    amendment_path = root/AMENDMENT; amendment = read(amendment_path); amendment_sha = sha(amendment_path)
    assert amendment['protocol_sha256'] == sha(root/'PROTOCOL.json') and not amendment['sealed_contents_read']
    assert amendment['scope'] == 'outcome_independent_common_rl_final_boundary'
    assert amendment['selected_stage'] == STAGE and amendment['selected_step_limit'] == BOUNDARY
    assert Path(amendment['output']) == output and sha(__file__) == amendment['governor_source_sha256']
    assert sha(amendment['registration']) == amendment['registration_sha256']
    registration = read(amendment['registration']); parents = registration['parents']
    campaign = root/amendment['active_campaign']; spec = read(campaign/'SPECIFICATION.json')
    assert sha(campaign/'SPECIFICATION.json') == amendment['specification_sha256']
    path = output/('DRY_RUN.json' if dry_run else 'execution.json'); assert not path.exists()
    state = dict(status='watching', started_utc=now(), source_sha256=sha(__file__),
                 amendment_sha256=amendment_sha, rows=[], signals_sent=0, physics_steps=0, sealed_reads=0,
                 dry_run=dry_run, owner_pid=os.getpid())
    write(path,state,True); signaled=set(); last_save=time.monotonic()
    try:
        while True:
            assert sha(amendment_path)==amendment_sha and not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
            states=[]; closures=[]; handles=[]
            for parent in parents:
                queue=campaign/f'queue_{parent["queue"]}'; qpath=queue/'execution.json'; q=read(qpath); states.append(q)
                assert [row['name'] for row in q['rows']]==[job['name'] for job in spec['jobs'][parent['queue']::3]]
                if q['status']=='complete':
                    for row in q['rows']:
                        chosen=selected_boundary(queue,row)
                        actual=read(row['latest_manifest'])['cumulative_physics_steps']
                        assert sha(row['latest_manifest'])==row['latest_manifest_sha256']
                        assert 0<=actual-chosen['selected_steps']<=2750
                        closures.append(dict(chosen, actual_total_training_steps=actual,
                                             unused_compatibility_steps=actual-chosen['selected_steps']))
                    handles.append(dict(path=str(qpath),sha256=sha(qpath)))
                    continue
                assert q['status'] in ('running','waiting_for_simulation_lease'), 'Queue failure retained: '+q['status']
                try: alive=process_info(parent['pid'])
                except (FileNotFoundError,ProcessLookupError):
                    assert read(qpath)['status']=='complete', 'Registered queue process disappeared before closure'
                    continue
                assert alive['start_ticks']==parent['start_ticks'] and alive['argv']==parent['argv']
                for row in q['rows']:
                    for part in row['segments']:
                        stage=part['stage']; key=(parent['queue'],row['name'],stage)
                        if stage not in EXCESS_STAGES or 'returncode' in part or key in signaled: continue
                        chosen=selected_boundary(queue,row)
                        child_path=queue/row['name']/stage/'execution.json'
                        if not child_path.exists(): continue
                        child=read(child_path)
                        if child['status']=='complete': continue
                        assert child['status']=='running'
                        info=find_command(part['command'])
                        if info is None: continue
                        check_target(info,part['command'],parent,root,campaign,row['name'],stage)
                        event=dict(queue=parent['queue'],model=row['name'],stage=stage,pid=info['pid'],
                            start_ticks=info['start_ticks'],requested_utc=now(),command=part['command'],
                            selected=chosen, observed_steps=child['steps'], signal='SIGUSR1',
                            source_execution=str(child_path), already_requested=child.get('stop_requested',False))
                        if not dry_run and not child.get('stop_requested',False):
                            if not signal_stop(info,part['command'],parent,root,campaign,row['name'],stage): continue
                            state['signals_sent']+=1
                        state['rows'].append(event); signaled.add(key); write(path,state)
            if dry_run:
                state.update(status='complete',queues_checked=len(states)); break
            if all(q['status']=='complete' for q in states):
                assert len(closures)==15 and {r['name'] for r in closures}=={j['name'] for j in spec['jobs']}
                receipt=dict(status='complete',completed_utc=now(),amendment_sha256=amendment_sha,
                    models=closures,queue_executions=handles,source_sha256=sha(__file__),signals_sent=state['signals_sent'],
                    no_original_receipts_modified=True,selected_by_common_boundary_not_outcome=True)
                write(output/'CLOSURE.json',receipt,True); state.update(status='complete',closure_sha256=sha(output/'CLOSURE.json')); break
            assert datetime.now(timezone.utc)<datetime.fromisoformat(read(root/'PROTOCOL.json')['dispatch_deadline_utc'])
            if time.monotonic()-last_save>=60:
                state['last_checked_utc']=now();write(path,state);last_save=time.monotonic()
            time.sleep(1)
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(path,state)
    return state


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--mode',choices=('register','dry-run','watch'),required=True)
    parser.add_argument('--forecast',type=Path)
    args=parser.parse_args();root=args.root.resolve();output=args.output.resolve()
    if args.mode=='register':
        assert args.forecast is not None;result=register(root,output,args.forecast)
    else:result=watch(root,output,dry_run=args.mode=='dry-run')
    print(json.dumps(dict(mode=args.mode,status=result.get('status','registered'),output=str(output))))
