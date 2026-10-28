"""Wait for one existing local rsync, then verify/publish its immutable archive.

One-shot storage follow-up; no simulation, scheduler, deletion or remote training.
An exited transfer is not considered successful until every remote hash matches.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import subprocess
import time
from office_v7_uniform24_20261008 import read, write, sha


def identity(pid):
    try:
        stat=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        return dict(start_ticks=stat[19],argv=Path(f'/proc/{pid}/cmdline').read_bytes().decode().split('\0')[:-1])
    except (FileNotFoundError, ProcessLookupError):return None


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pid',type=int,required=True)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--receipt',type=Path,required=True)
    a=p.parse_args()
    assert not a.receipt.exists()
    expected=sha(a.archive/'archive_manifest.json')
    process=identity(a.pid)
    destination='arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/incoming/rl_closed110k_20261010/'
    if process is not None:
        assert Path(process['argv'][0]).name=='rsync' and process['argv'][-1]==destination
    state=dict(status='waiting_for_transfer',started_utc=datetime.now(timezone.utc).isoformat(),
        pid=a.pid,process_identity=process,manifest_sha256=expected,source_sha256=sha(__file__),
        local_archive=str(a.archive.resolve()),server_compute=False)
    write(a.receipt,state)
    try:
        end=time.monotonic()+24*3600
        while process is not None and identity(a.pid)==process:
            if time.monotonic()>=end:raise TimeoutError('Transfer still running after24h; preserve incoming and source')
            time.sleep(30)
        state['status']='verifying_remote';write(a.receipt,state)
        base='/home/arm1/sii_shared/SII_compliance'
        args=['python3',base+'/runs/main/rl_convergence_v2_setup_20261010/evidence/source/tools/archive_tool_campaign_20261002.py',
            '--root',base+'/incoming/rl_closed110k_20261010',
            '--publish',base+'/runs/main/rl_closed110k_20261010/evidence']
        result=subprocess.check_output(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',
            'arm1@192.168.31.70',shlex.join(args)],text=True,timeout=1800)
        verified=json.loads(result)
        assert verified['manifest_sha256']==expected
        state.update(status='verified_published',verification=verified)
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=datetime.now(timezone.utc).isoformat();write(a.receipt,state)


if __name__=='__main__':main()
