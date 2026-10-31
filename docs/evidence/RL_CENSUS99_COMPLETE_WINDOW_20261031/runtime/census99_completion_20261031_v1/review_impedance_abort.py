"""Read-only paired98/99 factual audit of actual99 impedance long0000 abort."""
from pathlib import Path
import json,hashlib,time,os,math
import numpy as np
os.sched_setaffinity(0,{54})
D=Path(__file__).resolve().parent;B=D.parents[1];case='active_long_train_0000';read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
results={};inputs=[]
for cycle in [98,99]:
 root=B/f'runs/parameter_census_cycle{cycle}_20261031_v1/impedance/train';ep=root/f'cycle_{cycle:05d}'/case
 rows=[json.loads(x) for x in (root/'episodes.jsonl').read_text().splitlines()];e=next(x for x in rows if x['condition']==case);r=read(ep/'rollout.json');terminal=read(ep/'TERMINAL.json')
 assert e['cycle']==cycle and e['model_sha256']==r['model_sha256']==terminal['model_sha256']==sha(ep/'rollout.mjb')
 for k in ['task_success','strict_success','abort_reason','full_task_horizon_completed','physical_valid']:
  assert e[k]==r[k]==terminal['result'][k]
 assert math.isclose(e['steps']*.04,terminal['terminal_time_s'],rel_tol=0,abs_tol=2e-8)
 metrics=ep/'rollout_metrics/substep_metrics.npz'
 with np.load(metrics) as z:
  assert len(z['time'])==r['metrics']['samples']==e['steps']*800
  np.testing.assert_array_equal(z['dt'],np.full_like(z['dt'],5e-5))
  assert math.isclose(float(z['time'][-1]),terminal['terminal_time_s'],rel_tol=0,abs_tol=1e-8)
  peak=np.max(np.abs(z['qfrc_actuator'].astype(np.float64)),axis=0)
  saved=np.asarray(r['metrics']['generalized_actuator_torque_peak_by_joint_nm'])
  np.testing.assert_allclose(peak,saved,rtol=2e-7,atol=2e-6)
  torque_error=float(np.max(np.abs(peak-saved)))
 trows=[json.loads(x) for x in (root/'transitions.jsonl').read_text().splitlines()]
 term=[x for x in trows if x['condition']==case and x['done']];assert len(term)==1
 results[str(cycle)]=dict(episode=e,terminal_time_s=terminal['terminal_time_s'],raw_physics_samples=r['metrics']['samples'],raw_dt=5e-5,raw_torque_peak_by_joint=peak.tolist(),float32_peak_reconstruction_max_abs_error=torque_error,
  recorded_global_penetration_m=r['stats']['max_penetration_m'],recorded_global_worst_pair=r['stats']['worst_pair'],recorded_external_penetration_m=r['stats']['max_external_penetration_m'],terminal_transition=term[0])
 inputs.extend(ref(p) for p in [root/'episodes.jsonl',root/'transitions.jsonl',ep/'rollout.json',ep/'TERMINAL.json',ep/'rollout.mjb',metrics])
a,b=results['98'],results['99'];assert b['episode']['abort_reason']=='global_penetration_exceeded_2mm' and not b['episode']['full_task_horizon_completed'];assert b['episode']['steps']==1007 and 1375-1007==368
assert a['episode']['model_sha256']==b['episode']['model_sha256']
assert b['raw_physics_samples']==805600
result=dict(passed=True,time=time.time(),case=case,methods='impedance',paired_cycles=results,same_model_sha256=b['episode']['model_sha256'],missing_actions_from_full_horizon=368,failed_case_retained_in_denominator=30,
 penetration_scope='Global/external penetration and worst pair are original recorded simulator statistics, not independently reconstructed contact depths; substep metrics do not log contact depth. Distinct metrics are not interchanged.',
 scope='Independent original episode/rollout/terminal labels, MJB binding, full raw substep count/dt/endtime and float32 actuator peak arithmetic. No causal claim about actor changes, no new simulation or training.',inputs=inputs,new_physics=0,optimizer_updates=0,convergence_claim=False)
with (D/'IMPEDANCE_LONG0000_ABORT_REVIEW.json').open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
print(json.dumps({c:{k:v[k] for k in ['terminal_time_s','raw_physics_samples','recorded_global_penetration_m','recorded_external_penetration_m','float32_peak_reconstruction_max_abs_error']} for c,v in results.items()},indent=2))
