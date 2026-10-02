"""Independent numerical audit from saved native trajectories."""
import argparse,json
from pathlib import Path
import numpy as np
import mujoco
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def audit_ball(p):
 r=json.loads((p/'result.json').read_text());native=p/'ball_native_substeps.npz'
 if not native.exists():return None
 x=np.load(native)['values'];m=mujoco.MjModel.from_binary_path(str(p/'model.mjb'));j=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_JOINT,'primitive_free_ball_joint');b=int(m.jnt_bodyid[j]);mass=float(m.body_mass[b])
 contacts=[v for k,v in r['contacts'].items() if 'primitive_free_ball' in k]
 if not contacts:
  out=dict(intended_contact=False,native_rows=len(x));(p/'BALL_AUDIT.json').write_text(json.dumps(out,indent=2));return out
 first=min(v['first_s'] for v in contacts);near=x[(x[:,0]>=first-.03)&(x[:,0]<=first+.20)]
 dv=near[:,8:11]-near[:,5:8];imp=near[:,11:14]*near[:,1,None];grav=(1-near[:,17,None])*mass*m.opt.gravity*near[:,1,None];res=mass*dv-imp-grav
 out=dict(intended_contact=True,first_robot_contact_s=first,mass_kg=mass,native_rows=len(x),audit_window_s=[float(near[0,0]),float(near[-1,0])],velocity_before_mps=near[0,5:8].tolist(),velocity_after_mps=near[-1,8:11].tolist(),contact_impulse_vector_ns=imp.sum(axis=0).tolist(),gravity_impulse_vector_ns=grav.sum(axis=0).tolist(),momentum_balance_residual_vector_ns=res.sum(axis=0).tolist(),max_native_momentum_residual_ns=float(np.linalg.norm(res,axis=1).max()),peak_ball_pair_force_in_window_n=float(near[:,14].max()),robot_contact_pairs={k:v for k,v in r['contacts'].items() if 'primitive_free_ball' in k},interpretation='Momentum balance checks recorded physics consistency, not realism of a chosen contact model. Ball can receive work from robot. Window includes all ball contacts.')
 (p/'BALL_AUDIT.json').write_text(json.dumps(out,indent=2))
 fig,ax=plt.subplots(3,1,figsize=(8.2,7.6),sharex=True,layout='constrained')
 colors=['#2870ad','#d38723','#40926b']
 for i,lab in enumerate(['x','y','z']):
  ax[0].plot(near[:,0]-first,near[:,8+i],label=lab,color=colors[i]);ax[1].plot(near[:,0]-first,near[:,11+i],label=lab,color=colors[i])
 ax[0].set_ylabel('Ball velocity (m/s)');ax[1].set_ylabel('Contact force (N)');ax[2].plot(near[:,0]-first,np.linalg.norm(res,axis=1),color='#9b426b');ax[2].set_ylabel('Momentum residual (N s)');ax[2].set_xlabel('Time relative to first robot contact (s)')
 for a in ax:a.grid(alpha=.2);a.axvline(0,color='0.4',ls='--',lw=.8)
 ax[0].legend(ncol=3);fig.suptitle(f'{r["method"]} | {r["fixture_id"]} | native substep audit')
 fig.savefig(p/'ball_contact_audit.png',dpi=170);fig.savefig(p/'ball_contact_audit.pdf');plt.close(fig);return out

def audit_metrics(p):
 r=json.loads((p/'result.json').read_text());raw=p/'substeps.npz'
 if not raw.exists():return None
 x=np.load(raw)['values'];dt=x[:,1];total=float(dt.sum());values=dict(rmse_m=float(np.sqrt(np.sum(np.sum(x[:,2:5]**2,axis=1)*dt)/total)),peak_torque_nm=float(x[:,5:12].max()),peak_speed_mps=float(x[:,12].max()),max_external_penetration_m=float(x[:,13].max()))
 errors={k:abs(v-r[k]) for k,v in values.items()}
 intervals=json.loads((p/'intervals.json').read_text());integration=dict(elapsed_s=sum(v['elapsed_s'] for v in intervals),rmse_m=float(np.sqrt(sum(v['error_integral'] for v in intervals)/sum(v['elapsed_s'] for v in intervals))))
 out=dict(substeps=len(x),native_duration_s=total,independent_metrics=values,absolute_errors=errors,interval_integration=integration,pass_numeric=max(errors.values())<1e-9 and abs(integration['rmse_m']-values['rmse_m'])<1e-9)
 if not out['pass_numeric']:raise RuntimeError(f'Independent metric mismatch {p}: {out}')
 (p/'METRIC_AUDIT.json').write_text(json.dumps(out,indent=2));return out

def main():
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--recursive',action='store_true');a=p.parse_args()
 dirs=sorted({f.parent for f in a.directory.rglob('result.json')}) if a.recursive else [a.directory]
 rows=[]
 for d in dirs:
  metrics=audit_metrics(d);ball=audit_ball(d);rows.append(dict(episode=str(d),metrics_pass=metrics['pass_numeric'] if metrics else None,ball_momentum_max_residual_ns=ball.get('max_native_momentum_residual_ns') if ball else None));print(json.dumps(rows[-1]),flush=True)
 (a.directory/'INDEPENDENT_AUDIT.json').write_text(json.dumps(rows,indent=2))
if __name__=='__main__':main()
