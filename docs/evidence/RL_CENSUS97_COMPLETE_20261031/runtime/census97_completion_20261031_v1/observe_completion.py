"""Bounded observation of existing97 jobs through their original completion gates."""
from pathlib import Path
import os, json, time, hashlib, traceback
D = Path(__file__).resolve().parent
B = D.parents[1]
read = lambda p: json.loads(Path(p).read_text())

def put(p, value):
    with p.open('x') as f:
        json.dump(value, f, indent=2)
        f.write('\n')

def live(j):
    s = Path('/proc', str(j['pid']), 'stat').read_text().rsplit(')',1)[1].split()
    assert s[0] != 'Z' and s[19] == j.get('start',j.get('proc_start_ticks'))

def main():
    os.sched_setaffinity(0,{54})
    p = read(D/'COMPLETION_PLAN.json')
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == p['source_sha256']
    rows = []
    with (D/'COMPLETION_OBSERVATIONS.jsonl').open('x') as f:
        while time.time() < p['deadline_unix']:
            for j in p['guards']:
                live(j)
            guard = Path(p['guard_root'])
            assert not (guard/'STOP').exists() and not (guard/'FAILURE.json').exists()
            statuses = {}
            for name, job in p['jobs'].items():
                for parent, pattern in job['failures']:
                    assert not list(Path(parent).glob(pattern)), (name,parent,pattern)
                end = Path(job['finished'])
                if end.exists():
                    result = read(end)
                    assert result[job['finish_key']] == job['finish_value']
                    statuses[name] = 'original_finished_gate_passed'
                else:
                    live(job['identity'])
                    statuses[name] = 'original_identity_live'
            progress = {m:read(Path(p['run'])/m/'train/PROGRESS.json') for m in p['methods']}
            gpu = json.loads((guard/'samples.jsonl').read_text().splitlines()[-1])
            assert time.time()-gpu['time'] < 20
            complete = all(v == 'original_finished_gate_passed' for v in statuses.values())
            row = dict(time=time.time(),statuses=statuses,progress=progress,gpu=gpu,all_complete=complete)
            rows.append(row)
            f.write(json.dumps(row)+'\n')
            f.flush()
            print(json.dumps(dict(time=row['time'],steps={m:x['steps'] for m,x in progress.items()},
                completed_conditions={m:x['completed_conditions'] for m,x in progress.items()},
                jobs=statuses,gpu=[x['utilization'] for x in gpu['gpus']])),flush=True)
            if complete:
                put(D/'COMPLETION_REVIEW.json',dict(passed=True,time=time.time(),all_complete=True,
                    samples=len(rows),elapsed_seconds=rows[-1]['time']-rows[0]['time'],
                    first_steps={m:rows[0]['progress'][m]['steps'] for m in p['methods']},
                    last_steps={m:progress[m]['steps'] for m in p['methods']},
                    actual_plots_pending=True,convergence_claim=False))
                return
            time.sleep(30)
    put(D/'COMPLETION_TIMEOUT.json',dict(time=time.time(),samples=len(rows),scientific_failure=False,
        scope='Finite observer ended; original jobs and guard were not stopped or restarted.'))

if __name__ == '__main__':
    try:
        main()
    except BaseException:
        put(D/('COMPLETION_FAILURE_'+str(time.time_ns())+'.json'),dict(time=time.time(),traceback=traceback.format_exc()))
        raise
