from pathlib import Path
import json,time,hashlib,math,ast
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_frozen_batch_diagnosis_20261031_v1';T=B/'runs/parameter_violation_cycle93_20261031_v1/impedance/train';rd=lambda p:json.loads(p.read_text())
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
r=rd(O/'SAVED_REVIEW.json');assert r['passed'];maximum=r['methods']['impedance']['maximum_batch'];index=maximum['top20'][0]['replay_index'];matches=[]
with (T/'transitions.jsonl').open() as f:
 for line in f:
  row=json.loads(line)
  if row['step']==index+1:matches.append(row)
assert len(matches)==1;transition=matches[0];assert transition['cycle']==93 and transition['done'];C=T/'cycle_00093'/transition['condition'];roll=rd(C/'rollout.json');term=rd(C/'TERMINAL.json')
assert roll['abort_reason'] is None and roll['full_task_horizon_completed'] and roll['physical_valid'] and not roll['task_success'];assert roll['baseline_policy']['actions']==1375 and math.isclose(term['terminal_time_s'],55.,abs_tol=1e-7);assert term['placement_hold_s']==roll['placement_hold_s']<.5
records=rd(O/'impedance/REVIEW.json')['records'];manifest=rd(O/'impedance/RAW_MANIFEST.json')['files'];rows=[]
for record,item in zip(records,manifest):
 p=Path(item['path']);assert ref(p)['sha256']==item['sha256']
 with np.load(p) as z:
  selected=z['indices']==index;count=int(selected.sum());contribution=0.
  if count:
   np.testing.assert_array_equal(z['dones'][selected],1);np.testing.assert_array_equal(z['bits'][selected],0);np.testing.assert_array_equal(z['target'][selected],np.float32(transition['reward']));np.testing.assert_array_equal(z['rewards'][selected],np.float32(transition['reward']));np.testing.assert_array_equal(z['masks'][selected],1)
   weights=z['masks'].astype(float)*(1+127*z['dones'].astype(float))[:,None];den=weights.sum(0);contribution=float((((z['q'][selected].astype(float)-z['target'][selected,None])**2)*weights[selected]/den).sum())
  rows.append(dict(batch=record['batch'],occurrences=count,native_loss=record['native_loss'],same_denominator_row_contribution=contribution,remaining_contribution=record['reconstructed_loss']-contribution,target_pair=record['pair']))
present=[x for x in rows if x['occurrences']];absent=[x for x in rows if not x['occurrences']];assert len(rows)==64 and present and absent
rawmask=r['methods']['impedance']['maximum_batch']['top20'][0]['mask'];assert rawmask==[1]*5
source=B/'runtime/source_train17_clock/source/scripts/validate_office_apparatus_v5_20260917.py';manifest_source=rd(B/'runtime/source_train17_clock/SOURCE_HASHES.json');assert ref(source)['sha256']==manifest_source['scripts/'+source.name]
tree=ast.parse(source.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='canonical_observation');canonical=ast.get_source_segment(source.read_text(),node)
put(O/'SPIKE_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),method='impedance',replay_index=index,source_transition=transition,episode=dict(condition=transition['condition'],actions=1375,full_horizon=True,abort=None,physical_valid=True,task=False,strict=roll['strict_success'],stage=roll['final_task_stage'],terminal_time_s=term['terminal_time_s'],placement_hold_s=term['placement_hold_s'],required_final_hold_s=.5,placement_error_xy_m=roll['placement_error_xy_m'],success_definition=roll['success_definition'],release_supported=roll['release_supported'],global_peak_mm=roll['stats']['max_penetration_m']*1000,external_peak_mm=roll['stats']['max_external_penetration_m']*1000),all64_batches=rows,present_batches=present,absent_batches=len(absent),absent_native_loss_range=[min(x['native_loss'] for x in absent),max(x['native_loss'] for x in absent)],maximum_batch_row_fraction=maximum['top20'][0]['contribution']/maximum['loss'],canonical_observation_source=canonical,sources=[ref(p) for p in [T/'transitions.jsonl',C/'rollout.json',C/'TERMINAL.json',C/'executed_evaluator.py.txt',source,B/'runtime/source_train17_clock/SOURCE_HASHES.json',O/'SAVED_REVIEW.json',O/'impedance/RAW_MANIFEST.json']],new_physics=0,optimizer_updates=0,replay_rows_removed=0,scope='All64 frozen native batches. Dominant full93 row is full-horizon failed placement, not a global-safety abort. Terminal target equals reward irrespective of sampled target pair. Original hold0.5 gate retained. Proprio canonical48 and current critic additions do not explicitly encode placement dwell state; this static observation does not prove irreducible ambiguity or justify a specific new feature. No historical online gradient/batch replay or claim of causal online-spike reproduction.'))
print(json.dumps(dict(index=index,condition=transition['condition'],present=present,absent_range=[min(x['native_loss'] for x in absent),max(x['native_loss'] for x in absent)],max_fraction=maximum['top20'][0]['contribution']/maximum['loss']),indent=2))
