"""Independent scalar reconstruction and inventory accounting of saved audit."""
from pathlib import Path
import json,hashlib,time,math
import numpy as np
import mujoco
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
D=Path(__file__).resolve().parent;B=D.parents[1];O=B/'runs/violation93_placement_audit_20261031_v1'
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,r):
 with Path(p).open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
r=rd(O/'REVIEW.json');assert r['passed'] and rd(O/'FINISHED.json')['passed'];checked=[]
for e in r['episodes']:
 p=Path(e['episode']);roll=rd(p/'rollout.json');dest=roll['placement_destination'];m=mujoco.MjModel.from_binary_path(str(p/'rollout.mjb'));g=m.geom('target_object_geom').id;body=int(m.geom_bodyid[g]);j=int(m.body_jntadr[body]);v=int(m.jnt_dofadr[j]);f=[int(m.joint(k).qposadr[0]) for k in ['finger_joint1','finger_joint2']];a_file=np.load(p/'rollout.npz');a={k:a_file[k] for k in ['object_position','qvel','qpos']};a_file.close();z_file=np.load(e['saved']['path']);z={k:z_file[k] for k in z_file.files};z_file.close();assert sha(e['saved']['path'])==e['saved']['sha256'];counter=0;last_reset=None;last_bad=[]
 for i in range(e['rows']):
  obj=a['object_position'][i];vel=a['qvel'][i];qp=a['qpos'][i];values=[math.hypot(obj[0]-dest[0],obj[1]-dest[1]),math.sqrt(sum(float(x)**2 for x in vel[v:v+3])),float(qp[f[0]]+qp[f[1]]),abs(obj[2]-dest[2]),math.sqrt(sum(float(x)**2 for x in vel[v+3:v+6]))];gates=[values[0]<.025,values[1]<.015,values[2]>.075,values[3]<.015,values[4]<.15]
  np.testing.assert_allclose(z['necessary_values'][i],values,atol=2e-15,rtol=1e-14);np.testing.assert_array_equal(z['necessary_gates'][i],gates);assert abs(z['pre_upper_s'][i]-counter*.04)<1e-12
  if all(gates):counter+=1
  else:counter=0;last_reset=i;last_bad=[name for name,ok in zip(['xy','linear_speed','finger_opening','height','angular_speed'],gates) if not ok]
  assert abs(z['post_upper_s'][i]-counter*.04)<1e-12
 assert last_reset==e['last_necessary_failure_index'] and last_bad==e['last_necessary_failed_gates'];assert abs(counter*.04-e['post_final_upper_s'])<1e-12;assert e['actual_final_hold_s']<=counter*.04+1e-10
 checked.append(dict(episode=e['episode'],rows=e['rows'],sha256=e['saved']['sha256']))
inv=[json.loads(l) for l in (O/'HISTORY85_INVENTORY.jsonl').read_text().splitlines()];inventory={}
for method in ['impedance','admittance','vmc']:
 rows=[x for x in inv if x['method']==method];missing=[x for x in rows if not x['exists']['rollout.npz']];assert all(not x['terminal_retained'] for x in missing);assert sum(x['retained_transitions'] for x in rows)==r['history85_inventory'][method]['retained_rows']
 for x in rows:
  for name,exists in x['exists'].items():assert (Path(x['episode'])/name).is_file()==exists
 inventory[method]=dict(episode_cohorts=len(rows),missing_raw_cohorts=len(missing),missing_raw_retained_rows=sum(x['retained_transitions'] for x in missing),all_missing_raw_are_retained_partial_cohorts=True)
# A purely logical terminal retrospective implication; NOT a preaction feature or training input.
spike=next(e for e in r['episodes'] if e['cycle']==93 and e['method']=='impedance' and Path(e['episode']).name=='active_long_train_0000');z=np.load(spike['saved']['path']);streak=round(spike['actual_final_hold_s']/.04);reset=len(z['time'])-streak-1;assert np.all(z['necessary_gates'][reset:]);assert abs(streak*.04-spike['actual_final_hold_s'])<1e-12
inference=dict(last_forced_reset_time_s=float(z['time'][reset]),last_forced_reset_index=reset,final_successful_gate_steps=streak,necessary_gates_all_true_at_reset=True,missing_contact_predicate_must_have_failed=True,which_contact_predicate='Not identifiable: support contact normal force >0.05N false OR robot contact normal force >0.05N true; either or both.',scope='Retrospective consistency deduction from final hold and original recurrence, not recovered full dwell series or preaction input.')
fig,axes=plt.subplots(2,2,figsize=(12,8));t=z['time'];tail=t>53.;names=['XY /25mm','linear /15mm/s','height /15mm','angular /0.15rad/s'];cols=[0,1,3,4];thresholds=[.025,.015,.015,.15]
for col,lim,name in zip(cols,thresholds,names):axes[0,0].plot(t[tail],z['necessary_values'][tail,col]/lim,label=name)
axes[0,0].axhline(1,color='black',ls='--');axes[0,0].axvline(t[reset],color='red',ls=':');axes[0,0].set(title='Impedance93 long0000: saved necessary gates',ylabel='Value / gate threshold',xlabel='Post-action time (s)');axes[0,0].legend(fontsize=7)
axes[0,1].plot(t[tail],z['post_upper_s'][tail],label='Post-action necessary-gate upper bound');axes[0,1].plot(t[tail],z['pre_upper_s'][tail],label='Causal preaction upper bound');axes[0,1].scatter([t[-1]],[spike['actual_final_hold_s']],color='red',label='Recorded terminal hold (only endpoint)');axes[0,1].axhline(.5,color='black',ls='--',label='Original final gate');axes[0,1].set(title='Upper bound is not the true hold',ylabel='Seconds',xlabel='Time (s)');axes[0,1].legend(fontsize=7)
for method in ['impedance','admittance','vmc']:
 group=[e for e in r['episodes'] if e['method']==method and e['selection']=='all_complete93'];axes[1,0].scatter([e['actual_final_hold_s'] for e in group],[e['post_final_upper_s'] for e in group],alpha=.65,label=method)
axes[1,0].plot([0,55],[0,55],'k--',lw=.8);axes[1,0].set(title='All90 endpoints (overlapping points retained)',xlabel='Recorded final hold (s)',ylabel='Necessary-gate upper bound (s)');axes[1,0].legend(fontsize=7)
axes[1,1].bar(list(inventory),[v['missing_raw_retained_rows'] for v in inventory.values()]);axes[1,1].set(title='Complete85 retained rows missing finalized raw',ylabel='Retained transitions (not dropped)');fig.tight_layout();plot=O/'placement_audit.png';fig.savefig(plot,dpi=150);plt.close(fig)
put(O/'SAVED_REVIEW.json',dict(passed=True,time=time.time(),checked=checked,all_scalar_gates_and_pre_post_upper_bounds_checked=True,inventory=inventory,spike_contact_reset_inference=inference,plot=dict(path=str(plot),sha256=sha(plot)),new_physics=0,optimizer_updates=0,contact_forward_calls=0))
print(json.dumps(dict(passed=True,episodes=len(checked),rows=sum(e['rows'] for e in checked),inventory=inventory,inference=inference),indent=2))
