from pathlib import Path
import json,time,hashlib,math
D=Path(__file__).parent
read=lambda p:json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
plan=read(D/'KNOWN_CASE_CAPTURE_PLAN.json');obs=read(D/'OBSERVATION_FINISHED.json');assert obs['passed']
for x in plan['inputs'].values():assert sha(x['path'])==x['sha256']
values={}
for label in ['FIRST','LAST']:
 r=read(D/('KNOWN_CASE_'+label+'.json'));p=Path(r['prefix_snapshot']['path']);assert sha(p)==r['prefix_snapshot']['sha256'];raw=p.read_bytes();assert raw.endswith(b'\n');rows=[json.loads(v) for v in raw.splitlines()];assert len(rows)==r['journal_rows'] and rows[0]['interval'] is None
 elapsed=0.;substeps=0;peak=0.
 for row in rows[1:]:
  v=row['interval'];assert v['substeps']==800 and math.isclose(v['elapsed_s'],.04,abs_tol=1e-12);elapsed+=v['elapsed_s'];substeps+=v['substeps'];peak=max(peak,v['external_penetration_peak_m'])
 assert math.isclose(elapsed,r['completed_interval_elapsed_s'],abs_tol=1e-8) and substeps==r['completed_interval_substeps'] and peak==r['completed_robot_external_penetration_peak_m']
 assert math.isclose(elapsed,substeps*5e-5,abs_tol=1e-8)
 values[label]=dict(rows=len(rows),elapsed_s=elapsed,substeps=substeps,robot_external_penetration_peak_m=peak,terminal_exists=r['terminal_exists'])
assert (D/'KNOWN_CASE_LAST.jsonl').read_bytes().startswith((D/'KNOWN_CASE_FIRST.jsonl').read_bytes())
assert values['LAST']['elapsed_s']>values['FIRST']['elapsed_s']>27
prior=read(plan['inputs']['prior79_diagnosis']['path']);assert prior['abort_preserved'] and prior['physical_valid'] is False and prior['actual_actions']==675 and math.isclose(prior['actual_time_s'],27,abs_tol=1e-8)
report=dict(passed=True,time=time.time(),original79_failure_preserved=True,first_prefix_exactly_retained_in_last=True,independent_scalar_elapsed_and_substeps=True,values=values,new_physics=0,new_updates=0,no_convergence_or_safety_pass_claim=True,limitation=plan['scope'],global_penetration_not_available_in_interval_journal=True,source_sha256=sha(__file__))
with (D/'KNOWN_CASE_SAVED_REVIEW.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
print(json.dumps(report))
