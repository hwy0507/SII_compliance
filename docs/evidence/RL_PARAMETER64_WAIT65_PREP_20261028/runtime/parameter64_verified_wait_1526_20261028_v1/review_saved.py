from pathlib import Path
import json,time,hashlib,statistics,subprocess
OUT=Path(__file__).parent;B=OUT.parents[1]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
finished=read(OUT/'OBSERVER_FINISHED.json');rows=[json.loads(l) for l in (OUT/'SAMPLES.jsonl').read_text().splitlines()]
assert finished['observer_finished'] and not finished['science_restarted'] and not finished['science_completion_claim']
assert [r['index'] for r in rows]==list(range(len(rows)))
assert all(a['time']<b['time'] for a,b in zip(rows,rows[1:]))
assert all(x['live'] for r in rows for x in r['learners']+r['watchers'])
assert all(not x['finished'] and not x['failure'] for r in rows for x in r['learners'])
for i in range(3):assert all(a['learners'][i]['progress']['steps']<b['learners'][i]['progress']['steps'] for a,b in zip(rows,rows[1:]))
assert finished['reason']=='finite_observation_elapsed' and len(rows)==21
review=dict(passed=True,time=time.time(),samples=len(rows),first_time=rows[0]['time'],last_time=rows[-1]['time'],initial_steps=[x['progress']['steps'] for x in rows[0]['learners']],last_steps=[x['progress']['steps'] for x in rows[-1]['learners']],all_observed_identities_held=True,all_steps_strictly_increasing=True,no_scientific_completion=True,no_scientific_failure=True,observation_exit_not_scientific_termination=True,samples_sha256=sha(OUT/'SAMPLES.jsonl'),science_restarted=False)
(OUT/'REVIEW.json').write_text(json.dumps(review,indent=2)+'\n')
raw=[]
with Path('/tmp/sii_gpu_util_guard_20261028_v5/samples.jsonl').open() as f:
 for l in f:
  if not l.endswith('\n'):continue
  r=json.loads(l)
  if rows[0]['time']<=r['time']<=rows[-1]['time']:raw.append(r)
assert len(raw)>2
(OUT/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in raw))
stats={str(i):dict(minimum=min(v),mean=statistics.mean(v),below50=sum(x<50 for x in v)) for i in range(4) for v in [[g['utilization'] for r in raw for g in r['gpus'] if g['gpu']==i]]}
g=dict(samples=len(raw),first_time=raw[0]['time'],last_time=raw[-1]['time'],max_gap_seconds=max(b['time']-a['time'] for a,b in zip(raw,raw[1:])),gpus=stats,synthetic_guard_included=True,per_instant_guarantee=False)
(OUT/'GUARD_REVIEW.json').write_text(json.dumps(g,indent=2)+'\n')
j=read(B/'runs/vmc64_ranked63_terminal_followup_20261028_v1/LAUNCH.json');p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split();assert s[19]==j['proc_start_ticks'] and s[0]!='Z'
(OUT/'RANKED_WAITER_EXTRA_SNAPSHOT.json').write_text(json.dumps(dict(time=time.time(),job=j,identity_live=True,not_part_of_original_observer=True),indent=2)+'\n')
print(json.dumps(review,indent=2));print(json.dumps(g,indent=2))
