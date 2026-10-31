"""Reconcile original complete98 identities and terminal results, without restarting work."""
from pathlib import Path
import hashlib,json,time
D=Path(__file__).resolve().parent;B=D.parents[1];W=B/'runtime/census98_completion_watch_20261031_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
p=read(W/'PLAN.json');assert sha(W/'watch.py')==p['source_sha256']
interruption=read(D/'TOOL_SESSION_INTERRUPTION.json');assert interruption['watch_exit_code']==143
assert not (W/'WATCH_REVIEW.json').exists()
assert not list(W.glob('WATCH_FAILURE*'))
rows=[json.loads(line) for line in (W/'OBSERVATIONS.jsonl').read_text().splitlines()];assert rows
assert all(all(s['live'] or s['finished'] for s in row['status'].values()) for row in rows)
assert not all(s['finished'] for s in rows[-1]['status'].values())
assert sha(W/'OBSERVATIONS.jsonl')==interruption['watch_last_observation_sha256']
assert all(min(row['gpu'])>=50 for row in rows)
minimum_gpu=[min(row['gpu'][i] for row in rows) for i in range(4)]
final={}
for job in p['jobs']:
 f=Path(job['finished']);assert read(f)[job['finished_key']]==job['finished_value']
 final[job['name']]=dict(path=str(f),sha256=sha(f))
for j in p['guard']['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split()
 assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
assert not Path(p['guard']['root'],'STOP').exists()
result=dict(passed=True,time=time.time(),all_complete=True,samples=len(rows),elapsed_seconds=rows[-1]['time']-rows[0]['time'],first_steps={m:q['steps'] for m,q in rows[0]['progress'].items()},last_steps={m:q['steps'] for m,q in rows[-1]['progress'].items()},minimum_gpu=minimum_gpu,final_gates=final,watch_interruption=dict(path=str(D/'TOOL_SESSION_INTERRUPTION.json'),sha256=sha(D/'TOOL_SESSION_INTERRUPTION.json')),original_watch_completed=False,original_raw_observations_sha256=sha(W/'OBSERVATIONS.jsonl'),actual_plots_pending=True,convergence_claim=False,training_restarted=False,physics_restarted=False,guard_continues=True,scope='Original watcher terminated143 without terminal receipt; partial observations preserved. Original finite98 and all three registered consumers now individually verified complete. No claim that the interrupted watcher observed every finish. Raw observed identities and GPU samples rechecked. Separate full scientific/plot review still required.')
with (D/'COMPLETION_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print('Complete98 terminal receipts reconciled')
