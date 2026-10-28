"""Finish ONE already-started, named storage transfer; never launch simulation.

Wait on the exact local rsync identity, verify every remote file, then publish
to a new run directory. A stopped transfer alone is not evidence of completion.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import time
from finish_rl_archive_20261010 import identity
from office_v7_uniform24_20261008 import read, write, sha, now


def destination(name):
    if not re.fullmatch(r'(?:rl|classical)_[a-z0-9_]+',name):
        raise ValueError('Expected one rl_ or classical_ archive run name, not a path')
    return '/home/arm1/sii_shared/SII_compliance/incoming/'+name


def transfer_source(argument, process_cwd):
    """Resolve an rsync argument in the sender's cwd, not this service's cwd."""
    path=Path(argument)
    return (path if path.is_absolute() else Path(process_cwd)/path).resolve()


def source_matches(argument, process_cwd, archive):
    expected=Path(archive).resolve()
    if transfer_source(argument,process_cwd)==expected:return True
    # rsync chdir()s into a directory source while retaining the original
    # relative argument in /proc/cmdline. Require both exact cwd and basename;
    # destination/process identity and the complete archive hashes are checked
    # separately, so this is not permission to trust arbitrary sender paths.
    supplied=Path(argument)
    return (not supplied.is_absolute() and supplied.name==expected.name
            and Path(process_cwd).resolve()==expected)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pid',type=int,required=True)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--run-name',required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    assert not a.receipt.exists()
    remote=destination(a.run_name)
    process=identity(a.pid)
    process_cwd=None
    if process is not None:
        assert Path(process['argv'][0]).name=='rsync'
        assert process['argv'][-1]=='arm1@192.168.31.70:'+remote+'/'
        process_cwd=str(Path('/proc')/str(a.pid)/'cwd')
        process_cwd=str(Path(process_cwd).resolve(strict=True))
        assert source_matches(process['argv'][-2],process_cwd,a.archive)
    expected=sha(a.archive/'archive_manifest.json')
    state=dict(status='waiting_for_transfer',started_utc=now(),pid=a.pid,process_identity=process,
        source_sha256=sha(__file__),local_archive=str(a.archive.resolve()),transfer_working_directory=process_cwd,
        manifest_sha256=expected,server_compute=False,server_use='storage verification only')
    write(a.receipt,state)
    try:
        deadline=time.monotonic()+24*3600
        while process is not None and identity(a.pid)==process:
            if time.monotonic()>=deadline:raise TimeoutError('Preserved transfer still active after24h')
            time.sleep(30)
        state['status']='verifying_remote';write(a.receipt,state)
        base='/home/arm1/sii_shared/SII_compliance'
        published=base+'/runs/main/'+a.run_name+'/evidence'
        command=['python3',base+'/runs/main/rl_convergence_v2_setup_20261010/evidence/source/tools/archive_tool_campaign_20261002.py',
            '--root',remote,'--publish',published]
        verified=json.loads(subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',
            'arm1@192.168.31.70',shlex.join(command)],text=True,timeout=1800))
        assert verified['manifest_sha256']==expected and verified['published_evidence']==published
        state.update(status='verified_published',verification=verified)
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=now();write(a.receipt,state)


if __name__=='__main__':main()
