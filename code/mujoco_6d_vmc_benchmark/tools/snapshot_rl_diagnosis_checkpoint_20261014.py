"""Archive a completed checkpoint prefix while its parent training continues.

Only immutable closed episodes/checkpoints are hardlinked; live receipts and
logs are copied or prefix-extracted. Historical execution paths remain intact.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
from archive_tool_campaign_20261002 import make
from research72_checkpoint_20261003 import checkpoint_hashes
from rl_reward_diagnosis_audit_20261014 import read,write,sha


def link_tree(source,destination):
    shutil.copytree(source,destination,copy_function=os.link,
        ignore=shutil.ignore_patterns('__pycache__','*.pyc'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--pair',required=True)
    p.add_argument('--step',type=int,required=True);a=p.parse_args()
    root=a.root.resolve();out=a.output.resolve();assert not out.exists()
    protocol=read(root/'PROTOCOL.json');pair=next(r for r in protocol['pairs'] if r['id']==a.pair)
    selected=[]
    for arm in pair['arms']:
        name=a.pair+'_'+arm+'_train';training=root/name
        captured=(training/'execution.json').read_bytes();state=json.loads(captured)
        cp=next(r for r in state['checkpoint_rows'] if r['step']==a.step)
        assert checkpoint_hashes(Path(cp['path']))==cp['hashes']
        rows=[r for r in state['rows'] if 'result' in r and r['step_after']<=a.step]
        assert rows and rows[-1]['step_after']==a.step
        for row in rows:
            run=Path(row['run']);assert sha(run/'rollout.npz')==row['trace_sha256']
            assert sha(run/'AUDIT.json')==row['audit_sha256']
            assert read(run/'execution.json')['status']!='running'
        selected.append((name,training,captured,cp,rows))
    out.mkdir(parents=True)
    for folder in ('source','parameter_fullrange'):link_tree(root/folder,out/folder)
    for file in ('PROTOCOL.json','SOURCE_HASHES.json','PARAMETER_HASHES.json','CONDITIONS.json','teacher.json','RUNTIME_VERSIONS.json'):
        shutil.copy2(root/file,out/file)
    metadata=dict(status='completed_checkpoint_prefix_snapshot',created_utc=datetime.now(timezone.utc).isoformat(),
        parent_run=str(root),source_sha256=sha(__file__),pair=a.pair,checkpoint_step=a.step,
        parent_campaign_still_running=True,not_a_completed_comparison=True,arms=[])
    for name,training,captured,cp,rows in selected:
        dest=out/name;dest.mkdir();(dest/'captured_parent_execution.json').write_bytes(captured)
        shutil.copy2(training/'PROTOCOL.json',dest/'PROTOCOL.json')
        link_tree(Path(cp['path']),dest/Path(cp['path']).name)
        for row in rows:link_tree(Path(row['run']),dest/Path(row['run']).name)
        for log in ('training.jsonl','optimizer.jsonl'):
            with (training/log).open() as src,(dest/log).open('x') as dst:
                for line in src:
                    if not line.endswith('\n'):break
                    record=json.loads(line)
                    if record['step']>a.step:break
                    dst.write(line)
        write(dest/'SNAPSHOT.json',dict(status='complete_prefix',checkpoint=cp,rows=rows,
            captured_parent_status=json.loads(captured)['status'],new_physics_steps=0))
        metadata['arms'].append(dict(name=name,checkpoint=cp,episodes=len(rows),
            task=sum(r['result']['task_success'] for r in rows),strict=sum(r['result']['strict_success'] for r in rows)))
    helpers=out/'audit_tools';helpers.mkdir()
    for name in ('snapshot_rl_diagnosis_checkpoint_20261014.py','audit_rl_reward_live_20261014.py',
                 'audit_rl_learning_mechanisms_20261014.py','archive_tool_campaign_20261002.py'):
        shutil.copy2(Path(__file__).with_name(name),helpers/name)
    for name in ('COMPLETED_TRAIN_REWARD_AUDIT_0222.json','FIRST_EPISODE_REWARD_AUDIT_v3.json','HISTORICAL_LEARNING_MECHANISM_AUDIT_v1.json'):
        shutil.copy2(root/name,out/name)
    metadata['audit_scope_note']='Existing captured audits may also refer to later local episodes; only the listed checkpoint prefix raw files are included here.'
    write(out/'SNAPSHOT.json',metadata);make(out)


if __name__=='__main__':main()
