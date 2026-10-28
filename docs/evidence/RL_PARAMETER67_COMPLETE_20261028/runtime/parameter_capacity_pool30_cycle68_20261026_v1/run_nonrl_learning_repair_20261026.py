"""Finite matched fit diagnostic; no physics, RL, test-based selection or resume."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def write(p, value):
    temp = p.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    temp.replace(p)


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--matrix', type=Path, required=True)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--budgets', type=int, nargs='+', default=[8000,32000])
    p.add_argument('--learning-rate-schedule', choices=('constant','cosine'), default='constant')
    a = p.parse_args()
    assert len(set(a.budgets)) == len(a.budgets) and all(0 < b <= 32000 for b in a.budgets)
    a.parent = a.parent.resolve(); a.matrix = a.matrix.resolve(); root = a.root.resolve()
    assert read(a.matrix/'execution.json')['status'] == 'complete', 'Wait for current physics grid'
    assert read(a.matrix/'FINAL_AUDIT.json')['status'] == 'passed', 'Audit grid first'
    cg = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    assert int((cg/'memory.max').read_text()) <= 3*1024**3
    assert int((cg/'memory.swap.max').read_text()) == 0
    root.mkdir(parents=True, exist_ok=False)
    source = root/'source'
    # Full dependency tree pinned; trainer is the sole replacement from current code.
    shutil.copytree(a.parent/'source', source)
    trainer = source/'tools/train_fair_students_20261013.py'
    shutil.copy2(Path(__file__).with_name(trainer.name), trainer)
    source_hashes = {str(f.relative_to(source)):sha(f) for f in sorted(source.rglob('*.py'))}
    write(root/'SOURCE_HASHES.json', source_hashes)
    jobs = [dict(family=family, rate=rate, updates=updates, seed=2026101301)
            for updates in a.budgets for family,rate in (
                ('esn_gradient',1e-5),('rnn_scratch',1e-5),('mlp_scratch',1e-4))]
    registration = dict(created_utc=now(), jobs=jobs,
        authority='User ongoing goal: diagnose data then learning and repair non-RL comparison',
        data=str(a.parent/'data/training_data.npz'), data_sha256=sha(a.parent/'data/training_data.npz'),
        metadata_sha256=sha(a.parent/'data/DATA_COMPLETE.json'),
        source_hashes_sha256=sha(root/'SOURCE_HASHES.json'),
        parent_matrix_sha256=sha(a.matrix/'REPORT.json'),
        changes=['fixed global importance normalization including short-tail regularization',
                 'full-training-set objective and MSE every 1000 updates'],
        budgets=a.budgets, learning_rate_schedule=a.learning_rate_schedule,
        unchanged=['data','44/11 trajectory split','actor fields','initialization seed',
                   'preselected family learning rates','feature transform','filter','physical gates'],
        selection='Per-fit best imitation validation MSE; no selection by current 8-condition scores',
        convergence='Descriptive evidence only: >=10% full-train objective reduction and last 4 logged values range/mean <=1%; report validation trends separately. Budget exhausted alone is not convergence.',
        scope='Finite offline fits, no simulation or new data. One seed pilot, not final fair multi-seed comparison. Current 8 conditions are seen diagnostic data after inspection; next confirmatory test must be newly registered.',
        resources=dict(threads=1,memory_max_bytes=3*1024**3,swap_max_bytes=0,concurrent_fits=1),
        python=sys.executable)
    write(root/'REGISTRATION.json',registration)
    state=dict(status='running',started_utc=now(),expected=len(jobs),completed=0,jobs=[])
    write(root/'execution.json',state)
    try:
        for j in jobs:
            name=f"{j['family']}_s{j['seed']}_u{j['updates']}"
            dest=root/name
            cmd=[sys.executable,str(trainer),'--data',registration['data'],
                 '--metadata',str(a.parent/'data/DATA_COMPLETE.json'),'--output',str(dest),
                 '--family',j['family'],'--seed',str(j['seed']),'--learning-rate',str(j['rate']),
                 '--updates',str(j['updates']),'--objective-normalization','global','--full-training-diagnostics',
                 '--learning-rate-schedule',a.learning_rate_schedule]
            receipt=dict(**j,name=name,command=cmd,started_utc=now())
            state['jobs'].append(receipt);write(root/'execution.json',state)
            with (root/(name+'.log')).open('x') as log:
                result=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=os.environ.copy())
            receipt.update(returncode=result.returncode,ended_utc=now())
            assert result.returncode==0, f'{name} failed; preserved, no automatic retry'
            meta=read(dest/'TRAINING_COMPLETE.json')
            assert sha(dest/'checkpoint.npz') == meta['checkpoint_sha256']
            assert meta['training_data_sha256'] == registration['data_sha256']
            history=meta['history']; tail=[h['full_train_objective'] for h in history[-4:]]
            relative_range=(max(tail)-min(tail))/max(sum(tail)/len(tail),1e-12)
            reduction=1-history[-1]['full_train_objective']/max(history[0]['full_train_objective'],1e-12)
            receipt.update(checkpoint_sha256=meta['checkpoint_sha256'],selected_update=meta['selected_update'],
                           validation_mse=meta['validation_mse'],last4_full_train_relative_range=relative_range,
                           full_train_relative_reduction=reduction,
                           diagnostic_plateau=relative_range<=.01 and reduction>=.1,
                           completion_sha256=sha(dest/'TRAINING_COMPLETE.json'))
            state['completed']+=1;write(root/'execution.json',state)
        state['status']='complete'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['updated_utc']=now();write(root/'execution.json',state)


if __name__ == '__main__':
    main()
