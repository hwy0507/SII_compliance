"""Plot actual paired development trajectories, never test/student-final results."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3]/'code/mujoco_6d_vmc_benchmark'
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,sha
from diagnose_v9_teacher_handoff_recovery_20261030 import summarize
from cross_track_recovery_teacher_20261030 import CrossTrackRecoveryTeacher
from vertical_aware_cross_track_teacher_20261030 import VerticalAwareCrossTrackTeacher
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 new=ROOT/'outputs/vertical_aware_cross_track_development_20261030_v3'
 old=ROOT/'outputs/cross_track_teacher_development_20261030_v1'
 assert read(new/'execution.json')['status']=='complete_five_probes_pending_independent_campaign_review'
 out=Path(__file__).parent/'VERTICAL_STAGE_RECOVERY_COMPARISON_20261030'
 assert not out.with_suffix('.json').exists()
 fig,axes=plt.subplots(2,2,figsize=(11,6.5),sharex=True);rows=[];inputs={}
 for col,prefix in enumerate((175,275)):
  paired=[];row={'student_prefix_steps':prefix,'versions':{}}
  for label,base,cls,color in [('v1: horizontal-only',old,CrossTrackRecoveryTeacher,'#ba4137'),('v3: vertical-aware',new,VerticalAwareCrossTrackTeacher,'#16769b')]:
   f=base/('rod_prefix'+str(prefix))/'rod';q=read(f/'HANDOFF_REVIEW.json');h=read(f/'HANDOFF_EXECUTION.json')
   assert h['source_stable'] is True and h['completed_steps']==500
   with np.load(f/'trajectory.npz') as z:t=z['time'].copy();obs=z['observation'].copy();action=z['action'].copy()
   actor=cls(read(f/'teacher.json'));actor.reset();pred=[];vel=[]
   for o in obs:actor.observe(o);pred.append(actor.act(o[39:45]));vel.append(actor.last_cross_track_velocity.copy())
   np.testing.assert_array_equal(np.asarray(pred)[prefix:],action[prefix:])
   paired.append((obs,action,sha(f/'scene.mjb')))
   active=t>=prefix*.04
   axes[0,col].plot(t[active],obs[active,21]*1000,label=label,color=color,lw=1.7)
   axes[1,col].plot(t[active],np.asarray(vel)[active,1]*1000,color=color,lw=1.7)
   summary=summarize(f);row['versions'][label]={'qualified':q['qualified'],'recovery_summary':summary}
   inputs[str(f/'trajectory.npz')]=sha(f/'trajectory.npz');inputs[str(f/'HANDOFF_REVIEW.json')]=sha(f/'HANDOFF_REVIEW.json')
  assert paired[0][2]==paired[1][2]
  np.testing.assert_array_equal(paired[0][0][:prefix],paired[1][0][:prefix]);np.testing.assert_array_equal(paired[0][1][:prefix],paired[1][1][:prefix])
  axes[0,col].set_title(f'Same student prefix: {prefix*.04:g} s')
  for ax in axes[:,col]:ax.axhline(0,color='gray',lw=.6);ax.axvline(12.8,color='gray',ls='--',lw=1);ax.grid(alpha=.22);ax.set_xlim(6.8,20)
  axes[0,col].legend(fontsize=8);axes[1,col].set_xlabel('Episode time (s); dashed line = rod withdrawal')
  rows.append(row)
 axes[0,0].set_ylabel('Saved y reference error (mm)');axes[1,0].set_ylabel('Teacher added y return velocity (mm/s)')
 fig.suptitle('Actual teacher recovery probes on a training identity — not final student/test performance',fontsize=11)
 fig.tight_layout();fig.savefig(out.with_suffix('.png'),dpi=170);fig.savefig(out.with_suffix('.pdf'));plt.close(fig)
 result=dict(status='verified_actual_paired_development_comparison',rows=rows,input_sha256=inputs,source_sha256=sha(Path(__file__)),figures={str(out.with_suffix(ext)):sha(out.with_suffix(ext)) for ext in ('.png','.pdf')},limitations='Two train-identity physical probes; shared prefix/MJB and actual teacher suffix replay verified. Not final ESN/MLP/RNN performance or proof of general safety.')
 out.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n')
 print('saved actual paired comparison')
if __name__=='__main__':main()
