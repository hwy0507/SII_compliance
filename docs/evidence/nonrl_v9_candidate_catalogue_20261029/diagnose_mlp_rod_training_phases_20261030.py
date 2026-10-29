"""Training-only rod phase residuals, not a new checkpoint-selection rule."""
import argparse
from pathlib import Path
import numpy as np
from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from current_student_policy_20260921 import load_current
from review_repaired_student_closures_20261029 import error_stats
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
b=Path(__file__).resolve().parent;catalogue=read(b/'CATALOGUE.json');training=ROOT/'outputs/special_scene_direction_retrain_20261029_v9';data=training/'data/training_data.npz';meta=read(data.with_name('DATA_COMPLETE.json'));assert sha(data)==meta['training_data_sha256']==catalogue['data_sha256']
with np.load(data,allow_pickle=False) as z:obs=z['observation'];target=z['requested_teacher_action'];episode=z['episode'];train=z['train']
lineage=[r for r in meta['lineage'] if r['split']=='train' and r['scene']=='rod'];assert len(lineage)==8
histories=[];inputs={str(data):sha(data),str(data.with_name('DATA_COMPLETE.json')):sha(data.with_name('DATA_COMPLETE.json')),str(b/'CATALOGUE.json'):sha(b/'CATALOGUE.json')}
for row in lineage:
 folder=Path(row['folder']);ids=np.flatnonzero(episode==row['episode']);assert train[ids].all()
 with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
  np.testing.assert_array_equal(z['observation'],obs[ids]);np.testing.assert_array_equal(z['action'],target[ids]);time=z['time']
 rod=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json');assert rod['status']=='passed'
 for name,h in rod['hashes'].items():assert sha(ROOT/'tools'/name if name.endswith('.py') else folder/name)==h
 inputs[str(folder/'trajectory.npz')]=sha(folder/'trajectory.npz');inputs[str(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')]=sha(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
 contact=rod['hand_contact_first_s'];passed=rod['pass_s'];rejoin=rod['rejoin_confirmed_s'];retract=rod['retract_start_s']
 masks={'before_contact':time<contact,'contact_to_pass':(time>=contact)&(time<passed),'pass_to_rejoin':(time>=passed)&(time<rejoin),'rejoined_until_retract':(time>=rejoin)&(time<retract),'after_retract':time>=retract}
 assert np.all(np.sum(list(masks.values()),axis=0)==1);histories.append((row['id'],ids,masks))
group=next(g for g in catalogue['groups'] if g['family']=='mlp_scratch' and g['seed']==2026102802);candidates=group['ordered_candidates'].copy()
for family,seed,rank in [('mlp_scratch',2026102801,1),('esn_ridge',2026102801,4)]:
 g=next(g for g in catalogue['groups'] if g['family']==family and g['seed']==seed);candidates.append(g['ordered_candidates'][rank-1])
rows=[]
for candidate in candidates:
 cp=Path(candidate['checkpoint']);assert sha(cp)==candidate['checkpoint_sha256'];assert sha(Path(candidate['metadata']))==candidate['metadata_sha256'];actor=load_current(cp);phases={k:([],[]) for k in histories[0][2]};all_pred=[];all_target=[]
 for identity,ids,masks in histories:
  actor.reset();pred=np.asarray([actor.act(o) for o in obs[ids]]);all_pred.append(pred);all_target.append(target[ids])
  for name,mask in masks.items():phases[name][0].append(pred[mask]);phases[name][1].append(target[ids][mask])
 row=dict(id=candidate['id'],family=candidate['family'],seed=candidate['seed'],validation_rank=candidate['validation_rank'],checkpoint_sha256=candidate['checkpoint_sha256'],all_rod_train=error_stats(np.concatenate(all_pred),np.concatenate(all_target)),phases={})
 for name,(pred,label) in phases.items():
  pred=np.concatenate(pred);label=np.concatenate(label);row['phases'][name]=dict(**error_stats(pred,label),teacher_channel_mean=label.mean(axis=0).tolist(),teacher_channel_rms=np.sqrt(np.mean(label**2,axis=0)).tolist())
 assert sha(cp)==candidate['checkpoint_sha256'];rows.append(row)
for path,h in inputs.items():assert sha(Path(path))==h
write(a.output,dict(status='training_only_phase_diagnostic',rows=rows,training_rod_episodes=8,training_rod_frames=4000,source_sha256=sha(Path(__file__)),input_sha256=inputs,
 limitations=['All12 MLP02 candidates plus already observed passing controls, no fitting/physics/validation-result selection/final test.', 'Windows use teacher geometry histories only; phase means are not student closed-loop recovery evidence.', 'Channel2 is normalized translation_y request, not physical hand displacement or force.', 'Low phase MSE cannot establish stable student dynamics or unique root cause.']))
print([(r['seed'],r['validation_rank'],r['phases']['pass_to_rejoin']['mse'],r['phases']['pass_to_rejoin']['channel_bias'][2]) for r in rows])
