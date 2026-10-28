"""One-shot lease fairness intervention between completed development episodes.

Never stop a worker, change frozen source, or restart a training service. Pause
one exact queue parent only with no child and no simulation lock; promptly
resume it once the previously waiting RL queue owns a lease, or on timeout.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import signal
import time
from research72_rl_final_boundary_20261004 import process_info,option,sha


def now():return datetime.now(timezone.utc).isoformat()
def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)
def stopped(pid):return Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0] in ('T','t')
def children(pid):return Path(f'/proc/{pid}/task/{pid}/children').read_text().split()


def owners(root):
    keys={}
    for index in range(4):
        stat=(root/f'simulation_slots/slot_{index}.lock').stat()
        keys[(os.major(stat.st_dev),os.minor(stat.st_dev),stat.st_ino)]=index
    result={}
    for line in Path('/proc/locks').read_text().splitlines():
        words=line.split()
        if len(words)<8 or words[1]!='FLOCK' or words[3]!='WRITE':continue
        major,minor,inode=words[5].split(':');key=(int(major,16),int(minor,16),int(inode))
        if key in keys:result[int(words[4])]=keys[key]
    return result


def same(info):
    current=process_info(info['pid'])
    assert current['start_ticks']==info['start_ticks'] and current['argv']==info['argv']
    assert current['uid']==os.getuid()


def idle_pause(info,fd,lock_owners):
    """A race that starts a new episode is immediately resumed, never retained."""
    same(info)
    if stopped(info['pid']) or children(info['pid']) or info['pid'] in lock_owners():return False
    signal.pidfd_send_signal(fd,signal.SIGSTOP)
    retain=False
    try:
        limit=time.monotonic()+1
        while not stopped(info['pid']) and time.monotonic()<limit:time.sleep(.005)
        retain=stopped(info['pid']) and not children(info['pid']) and info['pid'] not in lock_owners()
        return retain
    finally:
        if not retain:signal.pidfd_send_signal(fd,signal.SIGCONT)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--yielding-pid',type=int,required=True);p.add_argument('--recipient-pid',type=int,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    assert not out.exists() and not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    yielding=process_info(a.yielding_pid);recipient=process_info(a.recipient_pid)
    for info in (yielding,recipient):
        assert info['uid']==os.getuid() and option(info['argv'],'--root')==str(root) and not stopped(info['pid'])
    assert Path(yielding['argv'][1]).name=='research72_batch_20261003.py'
    assert '--managed-slots' in yielding['argv'] and option(yielding['argv'],'--queue')=='0'
    assert Path(option(yielding['argv'],'--output')) in (
        root/'additional_development_v1/neural_lr_development',root/'context_gate_development_v1/development')
    assert Path(recipient['argv'][1]).name=='research72_rl_campaign_20261003.py'
    assert option(recipient['argv'],'--queue')=='1'
    assert option(recipient['argv'],'--output')==str(root/'rl_office_adaptation_v2')
    qpath=root/'rl_office_adaptation_v2/queue_1/execution.json'
    assert json.loads(qpath.read_text())['status'] in ('waiting_for_simulation_lease','running')
    out.mkdir();state=dict(status='waiting_for_idle_boundary',started_utc=now(),source_sha256=sha(__file__),
        yielding_process=yielding,recipient_process=recipient,initial_lease_owners=owners(root),
        physics_steps=0,new_fits=0,source_or_original_receipts_modified=False,events=[])
    write(out/'execution.json',state)
    fd=os.pidfd_open(yielding['pid']);paused=False
    def interrupt(*_):raise InterruptedError('Signal; resume yielding queue in finally')
    signal.signal(signal.SIGTERM,interrupt)
    limit=time.monotonic()+900;pause_time=None;last_save=time.monotonic()
    try:
        while time.monotonic()<limit:
            same(yielding);same(recipient);locks=owners(root)
            if recipient['pid'] in locks:
                state.update(status='complete',recipient_slot=locks[recipient['pid']],handoff_observed_utc=now())
                break
            if not paused:
                previous_mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGTERM,signal.SIGINT})
                try:
                    acquired=idle_pause(yielding,fd,lambda:owners(root))
                    if acquired:paused=True;pause_time=time.monotonic()
                finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous_mask)
                if acquired:
                    state.update(status='briefly_yielding_after_episode')
                    state['events'].append(dict(kind='SIGSTOP_queue_parent',utc=now(),
                        stopped_after_signal=stopped(yielding['pid']),children_after_signal=children(yielding['pid']),
                        lease_owners_after_signal=owners(root)))
                    write(out/'execution.json',state)
            elif time.monotonic()-pause_time>30:
                raise TimeoutError('RL did not acquire a free slot within30s; resume without retry')
            if time.monotonic()-last_save>60:
                state['last_checked_utc']=now();write(out/'execution.json',state);last_save=time.monotonic()
            time.sleep(.1)
        else:raise TimeoutError('No idle boundary within15min; no restart')
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        if paused:
            signal.pidfd_send_signal(fd,signal.SIGCONT)
            state['events'].append(dict(kind='SIGCONT_same_queue_parent',utc=now(),
                pause_seconds=time.monotonic()-pause_time))
            resume_limit=time.monotonic()+1
            while stopped(yielding['pid']) and time.monotonic()<resume_limit:time.sleep(.005)
        os.close(fd)
        state.update(ended_utc=now(),final_lease_owners=owners(root),
            yielding_parent_running_after_cleanup=not stopped(yielding['pid']))
        write(out/'execution.json',state)
    assert state['yielding_parent_running_after_cleanup']
    print(json.dumps(dict(status=state['status'],events=state['events'],recipient_slot=state['recipient_slot'])))


if __name__=='__main__':main()
