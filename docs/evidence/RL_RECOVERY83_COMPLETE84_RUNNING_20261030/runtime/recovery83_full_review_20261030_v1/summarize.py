from pathlib import Path
import json
B=Path(__file__).resolve().parents[2]
def read(p):return json.loads(p.read_text())
rev=B/'runs/parameter_partial75_recovery_cycle83_review_20261029_v1'
for name in ['REVIEW.json','health/DIAGNOSIS.json']:
 p=rev/name
 if p.exists():
  r=read(p);print(name)
  for m,x in r['methods'].items():
   keys=['steps','new_transitions','retained_replay_all_fields_exact','task','strict','reward_mean','full_horizon_count','aborts','max_reward_reconstruction_error','optimizer_and_network_finite','checkpoint_sha256','sampled_q_above_global_bound_fraction','network_state_unchanged']
   print(m,{k:x[k] for k in keys if k in x})
   if 'terminal_q_in_bag_absolute_error' in x:print('terminal MAE in/out',x['terminal_q_in_bag_absolute_error']['mean'],x['terminal_q_out_of_bag_absolute_error']['mean'])
for m in ['vmc','admittance']:
 p=B/f'runs/{m}_recovery83_terminal_followup_20261029_v1/REVIEW.json'
 if p.exists():
  r=read(p);print(m,'terminal',{k:v for k,v in r.items() if k.startswith('old') or k in ['passed','new30_contribution','fixed_anchor_rows','new_terminal_rows']});print('focus',[(x['replay_index'],x['sse_before'],x['sse_after']) for x in r['focus']])
p=B/'runs/parameter_recovery83_task_labels_20261029_v1/COMPLETE82_83.json'
if p.exists():
 r=read(p);print('labels',r['passed'],r['saved_rollouts_checked'])
 for m,x in r['methods'].items():
  for c in x['all30']:
   if c['changed_fields']:print(m,c['condition'],c['changed_fields'],[{k:v for k,v in a.items() if k in ['cycle','task','strict','physical_valid','penetration_mm','abort_reason']} for a in c['cases']])
print('complete flags', {str(p.relative_to(B)):p.exists() for p in [rev/'FINISHED.json',B/'runtime/prepare_recovery84_20261030_v1/FINISHED.json',B/'runtime/recovery83_completion_watch_20261030_v1/FINISHED.json']})
