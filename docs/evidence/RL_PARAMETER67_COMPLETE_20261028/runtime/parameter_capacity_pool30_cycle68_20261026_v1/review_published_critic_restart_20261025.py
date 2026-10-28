"""Finite read-only paired review after the existing stage auditor finishes.

Does not start/stop learners or physics. A missing observer is not interpreted
as stopped training. Completed audited reports remain usable after its exit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n');tmp.replace(path)


def observer_alive(item):
    try:
        stat=Path(f"/proc/{item['pid']}/stat").read_text().rsplit(')',1)[1].split()
        return stat[0]!='Z' and stat[19]==item['start_ticks']
    except FileNotFoundError:
        return False


def main(registration):
    p=json.loads(registration.read_text());out=Path(p['output']);out.mkdir(exist_ok=False)
    os.sched_setaffinity(0,{p['cpu']});os.nice(10)
    write(out/'EXECUTION.json',dict(pid=os.getpid(),registration_sha256=sha(registration),started_unix=time.time()))
    completed=[]
    try:
        for name,expected in p['source_hashes'].items():
            if sha(Path(__file__).with_name(name))!=expected:raise ValueError('Frozen review source drift')
        cohort=Path(p['cohort_registration'])
        if sha(cohort)!=p['cohort_registration_sha256']:raise ValueError('Cohort registration drift')
        audit=Path(p['audit_root'])
        for item in p['comparisons']:
            stages=[audit/item[k] for k in ('before_stage','after_stage')]
            while not all((s/'FINISHED.json').exists() for s in stages):
                if (audit/'FAILURE.json').exists():raise RuntimeError('Existing stage auditor reported failure')
                if not observer_alive(p['observer']):raise RuntimeError('Auditor handle absent before required complete reports; training unchanged')
                if time.time()>p['deadline_unix']:raise TimeoutError('Read-only review deadline; training unchanged')
                write(out/'PROGRESS.json',dict(waiting_for=item['name'],completed=completed,
                    observer_identity_verified=True,updated_unix=time.time()))
                time.sleep(10)
            paths=[s/'results/DIAGNOSIS.json' for s in stages]
            for stage,path in zip(stages,paths):
                if sha(path)!=json.loads((stage/'FINISHED.json').read_text())['report_sha256']:
                    raise ValueError('Finished stage report hash mismatch')
            cmd=[sys.executable,'-B',str(Path(__file__).with_name('compare_published_complete_cycles_20261025.py')),
                 '--before',str(paths[0]),'--after',str(paths[1]),'--before-cycle',str(item['before_cycle']),
                 '--after-cycle',str(item['after_cycle']),'--cohort-registration',str(cohort),'--output',str(out/item['name'])]
            with (out/(item['name']+'.log')).open('x') as log:subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,check=True)
            completed.append(item['name'])
        write(out/'FINISHED.json',dict(completed=completed,finished_unix=time.time(),new_physics=0,
            optimizer_updates=0,convergence_claim=False,training_changed=False))
    except BaseException as error:
        write(out/'FAILURE.json',dict(error=repr(error),completed=completed,training_changed=False));raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--registration',type=Path,required=True)
    main(parser.parse_args().registration)
