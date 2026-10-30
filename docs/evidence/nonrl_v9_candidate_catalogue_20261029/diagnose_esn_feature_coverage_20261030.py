"""Training-envelope diagnostic on already observed ESN development histories."""
import argparse
from pathlib import Path
import numpy as np
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from current_student_policy_20260921 import load_current

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
data=ROOT/'outputs/special_scene_direction_retrain_20261029_v9/data/training_data.npz'
meta=read(data.with_name('DATA_COMPLETE.json'));assert sha(data)==meta['training_data_sha256']
with np.load(data,allow_pickle=False) as z:
 obs=z['observation'];episode=z['episode'];train=z['train']
b=ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3/evaluations'
folders=[ROOT/'outputs/nonrl_v9_paired_scene_priority_20261029_v5/rod_00_esn_ridge/rod',
 b/'esn_ridge_s2026102801_rank2/rod_00/rod',b/'esn_ridge_s2026102801_rank3/rod_00/rod',b/'esn_ridge_s2026102802_rank1/rod_00/rod']
rows=[]
for folder in folders:
 cp=folder/'student_checkpoint.npz';before=sha(cp);actor=load_current(cp)
 assert not actor.nonlinear and not actor.state_delta_readout
 features=[]
 for identity in np.unique(episode[train]):
  actor.reset();features.extend(actor.features(o) for o in obs[(episode==identity)&train])
 features=np.asarray(features);assert len(features)==12600
 low=features.min(axis=0);high=features.max(axis=0);span=high-low
 with np.load(folder/'trajectory.npz',allow_pickle=False) as z:
  observations=z['observation'];actions=z['action'];time=z['time']
 actor.reset();np.testing.assert_array_equal(np.asarray([actor.act(o) for o in observations]),actions)
 actor.reset();live=np.asarray([actor.features(o) for o in observations]);raw=live@actor.weights
 np.testing.assert_array_equal(actor.weights,load_current(cp).weights)
 active=span>1e-8
 outside=(live[:,active]<low[active]-1e-8)|(live[:,active]>high[active]+1e-8)
 excess=np.maximum(np.maximum(low[active]-live[:,active],live[:,active]-high[active]),0)/span[active]
 # Descriptive feature envelope only. Correlated feature geometry is not covered.
 contribution=live[:,:,None]*actor.weights[None,:,:]
 absolute_sum=np.abs(contribution).sum(axis=1)
 ratio=np.divide(absolute_sum,np.abs(raw)+1e-12)
 worst_active=np.unravel_index(int(excess.argmax()),excess.shape)
 worst_feature=int(np.flatnonzero(active)[worst_active[1]])
 saturated=np.any(np.abs(actions[:,1:])>=.999,axis=1)
 q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
 for name,h in q['input_hashes'].items():assert sha(folder/name)==h
 assert sha(cp)==before
 rows.append(dict(folder=str(folder),checkpoint_sha256=before,qualified=q['status']=='qualified',
  features=int(features.shape[1]),
  worst_feature=dict(index=worst_feature,time_s=float(time[worst_active[0]]),
   train_low=float(low[worst_feature]),train_high=float(high[worst_feature]),
   student_value=float(live[worst_active[0],worst_feature])),
  first_saturation_time_s=float(time[np.flatnonzero(saturated)[0]]) if saturated.any() else None,
  windows=[dict(start_index=i,end_index_exclusive=min(i+50,len(time)),
    outside_frames=int(outside[i:i+50].any(axis=1).sum()),
    max_envelope_excess=float(excess[i:i+50].max()),
    max_residual_raw=float(np.abs(raw[i:i+50,1:]).max()),saturated_frames=int(saturated[i:i+50].sum()))
   for i in range(0,len(time),50)],variable_features=int(active.sum()),
  frames_with_any_feature_outside_train_envelope=int(np.any(outside,axis=1).sum()),
  frame_feature_outside_fraction=float(outside.mean()),maximum_normalized_envelope_excess=float(excess.max()),
  first_outside_time_s=float(time[np.flatnonzero(outside.any(axis=1))[0]]) if outside.any() else None,
  max_residual_raw=float(np.abs(raw[:,1:]).max()),
  residual_saturation_frames=int(np.any(np.abs(actions[:,1:])>=.999,axis=1).sum()),
  median_absolute_contribution_sum_residual= np.median(absolute_sum[:,1:],axis=0).tolist(),
  median_cancellation_ratio_residual=np.median(ratio[:,1:],axis=0).tolist(),
  input_hashes={'trajectory.npz':sha(folder/'trajectory.npz'),'qualification':sha(folder/'DEMONSTRATION_QUALIFICATION.json')}))
write(a.output,dict(status='read_only_training_envelope_diagnostic',rows=rows,training_frames=12600,
 training_sha256=sha(data),source_sha256=sha(Path(__file__)),actor_sha256=sha(ROOT/'scripts/office_vmc_memory_esn_20260927.py'),
 limitations=['All24 training histories only define each checkpoint envelope; no final test or fitting.',
 'Feature-envelope excess and cancellation are descriptive, not a causal proof or model-selection rule.',
 'Per-coordinate envelope ignores correlations and can contain unsupported joint feature combinations.',
 'Different student histories are not a common-input fit accuracy ranking.']))
print([(r['qualified'],r['frames_with_any_feature_outside_train_envelope'],r['maximum_normalized_envelope_excess'],r['max_residual_raw']) for r in rows])
