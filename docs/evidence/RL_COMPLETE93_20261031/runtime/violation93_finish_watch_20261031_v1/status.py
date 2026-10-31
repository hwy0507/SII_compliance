from pathlib import Path
import json,time
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runs/parameter_violation_cycle93_20261031_v1';V=B/'runs/parameter_violation_cycle93_review_20261031_v1';F=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';C=B/'runtime/violation93_completion_20261031_v1';read=lambda p:json.loads(p.read_text())
results={}
for label,j,target in [('archive',read(T/'MONITOR_LAUNCH.json'),V/'FINISHED.json'),('terminals',read(F/'PROCESS.json'),F/'FINISHED.json'),('comparison',read(C/'PROCESS.json'),C/'COMPARISON_FINISHED.json')]:
 p=Path('/proc',str(j['pid']),'stat');alive=False
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split();alive=s[0]!='Z' and s[19]==str(j.get('start',j.get('proc_start_ticks')))
 assert alive or target.exists(),label
 results[label]=dict(live=alive,finished=target.exists())
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(F.glob('*FAILURE*')) and not list(C.glob('COMPARISON_FAILURE_*'))
x=dict(time=time.time(),processes=results,review_files=[str(p.relative_to(V)) for p in V.rglob('*.json')],gpu=json.loads(Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()[-1]))
with (D/'FOLLOWUP_OBSERVATIONS.jsonl').open('a') as f:f.write(json.dumps(x)+'\n')
print(json.dumps(x))
if all(v['finished'] for v in results.values()):
 assert read(V/'FINISHED.json')['completed'] and read(F/'FINISHED.json')['passed'] and read(C/'COMPARISON_FINISHED.json')['passed']
 with (D/'COMPLETION_REVIEW.json').open('x') as f:json.dump(dict(passed=True,time=time.time(),processes=results,prior_observation_bound_kept=True,original_science_deadlines_unchanged=True),f,indent=2);f.write('\n')
