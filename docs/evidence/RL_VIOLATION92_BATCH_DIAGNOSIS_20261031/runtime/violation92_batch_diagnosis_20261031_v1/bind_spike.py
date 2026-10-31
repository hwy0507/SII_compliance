from pathlib import Path
import json,time,hashlib,math
import numpy as np
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation92_frozen_batch_diagnosis_20261031_v1';T=B/'runs/parameter_violation_cycle90_20261030_v1/impedance/train';C=T/'cycle_00090/active_long_train_0000'
read=lambda p:json.loads(p.read_text())
def ref(p):
 with p.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
 return dict(path=str(p),sha256=h)
r=read(O/'SAVED_REVIEW.json');assert r['passed'];maximum=r['methods']['impedance']['maximum_batch'];index=maximum['top20'][0]['replay_index'];assert index==3726050
found=[]
with (T/'transitions.jsonl').open() as f:
 for line in f:
  x=json.loads(line)
  if x['step']==index+1:found.append(x)
assert len(found)==1;transition=found[0];assert transition['cycle']==90 and transition['condition']=='active_long_train_0000' and transition['done']
roll=read(C/'rollout.json');term=read(C/'TERMINAL.json');old=read(B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json');assert roll['abort_reason']==old['abort']==term['result']['abort_reason']=='global_penetration_exceeded_2mm';assert old['actual_actions']==877 and math.isclose(term['terminal_time_s'],35.08,abs_tol=1e-8)
assert roll['stats']['max_external_penetration_m']<.0002 and roll['stats']['max_penetration_m']>.002
rows=[];manifest=read(O/'impedance/RAW_MANIFEST.json')['files'];records=read(O/'impedance/REVIEW.json')['records']
for record,item in zip(records,manifest):
 p=Path(item['path']);assert ref(p)['sha256']==item['sha256']
 with np.load(p) as z:
  selected=z['indices']==index;count=int(selected.sum());loss=0.
  if count:
   np.testing.assert_array_equal(z['dones'][selected],1);np.testing.assert_array_equal(z['bits'][selected],0);np.testing.assert_array_equal(z['target'][selected],np.float32(transition['reward']));np.testing.assert_array_equal(z['rewards'][selected],np.float32(transition['reward']))
   weights=z['masks'].astype(np.float64)*(1+127*z['dones'].astype(np.float64))[:,None];den=weights.sum(0);loss=float((((z['q'][selected].astype(np.float64)-z['target'][selected,None])**2)*weights[selected]/den).sum())
  rows.append(dict(batch=record['batch'],occurrences=count,native_loss=record['native_loss'],same_denominator_row_contribution=loss,remaining_contribution=record['reconstructed_loss']-loss,target_pair=record['pair']))
present=[x for x in rows if x['occurrences']];absent=[x for x in rows if not x['occurrences']];assert len(rows)==64 and [x['batch'] for x in present]==[21,41]
result=dict(passed=True,time=time.time(),method='impedance',replay_index=index,source_transition=transition,original_abort_summary=old,all64_batches=rows,present_batches=present,absent_batches=len(absent),absent_native_loss_range=[min(x['native_loss'] for x in absent),max(x['native_loss'] for x in absent)],maximum_batch_row_fraction=maximum['top20'][0]['contribution']/maximum['loss'],sources=[ref(p) for p in [T/'transitions.jsonl',C/'rollout.json',C/'TERMINAL.json',B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json',O/'SAVED_REVIEW.json',O/'impedance/RAW_MANIFEST.json']],new_physics=0,optimizer_updates=0,replay_rows_removed=0,scope='All64 fixed-state native batches retained. Both dominant spikes contain the same cycle90 global-safety-abort terminal, whose Bellman target is exactly reward regardless of sampled critic pair; pair0/1 co-occurrence is not evidence of a pair effect. Contribution uses unchanged full-batch denominators, not a rerun excluding rows. No historical online spike replay or proof of irreducible representation error.')
with (O/'SPIKE_SOURCE_REVIEW.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({k:result[k] for k in ['replay_index','present_batches','absent_native_loss_range','maximum_batch_row_fraction']},indent=2))
