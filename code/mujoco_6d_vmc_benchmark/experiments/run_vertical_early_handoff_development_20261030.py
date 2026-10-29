"""One prospective early-handoff development after two bounded-feedback failures.

Reuse the same three nominal train probes; test safe student handoffs at 7s/9s.
Keep the tested gain2/s, 0.02m/s cap and 1N gate unchanged.
No threshold/physics/source mutation, fitting, unseen input or automatic retry.
"""
from pathlib import Path
import argparse,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tools')]
from collect_special_scene_actions_20261028 import read,write,sha
from select_v9_closed_loop_candidates_v3_20261029 import properties
import run_vertical_aware_cross_track_campaign_20261030 as base
PARENT=ROOT/'outputs/vertical_stage_gain2_development_20261030_v4'
REVIEW=ROOT.parents[1]/'docs/evidence/nonrl_v9_candidate_catalogue_20261029/VERTICAL_AWARE_GAIN2_COMPLETE_REVIEW_20261030.json'

def prerequisite():
 p=properties('sii-vertical-stage-gain2-development-20261030.service');assert p['ActiveState']=='inactive' and p['MainPID']=='0'
 state=read(PARENT/'execution.json');r=read(REVIEW)
 assert state['status']=='complete_five_probes_pending_independent_campaign_review'
 assert len(state['rows'])==5 and [v['qualified'] for v in state['rows']]==[True,True,True,True,False]
 assert r['status']=='verified_complete_five_development_probes' and r['qualified_cases']==4
 assert r['execution_snapshot_sha256']==sha(PARENT/'execution.json') and r['registration_sha256']==sha(PARENT/'REGISTRATION.json')
 assert r['reviewer_sha256']==sha(ROOT/'tools/review_vertical_aware_cross_track_campaign_20261030.py')
 last=r['rows'][-1];assert last['task_success'] and last['safety_valid'] and not last['scene_behavior_valid']
 assert last['rod']['checks']['persistent_rejoin_before_withdrawal'] is False

def prepare(root):
 assert not root.exists();prerequisite();base.prepare(root)
 cfg=read(root/'teacher.json');cfg['cross_track_recovery']['gain_per_s']=2.;cfg['cross_track_recovery']['maximum_speed_mps']=.02;write(root/'teacher.json',cfg)
 reg=read(root/'REGISTRATION.json');reg.update(teacher_config_sha256=sha(root/'teacher.json'),previous_execution_sha256=sha(PARENT/'execution.json'),previous_review_sha256=sha(REVIEW),development_adjustment='Keep gain2/s, cap0.02m/s and load1N; move the late student handoff from 11s to 9s (225 steps), retaining the 7s (175-step) case. Same train identity and frozen gates; no test exposure.')
 reg['cases'][3]['student_steps']=175;reg['cases'][3]['id']='rod_prefix175'
 reg['cases'][4]['student_steps']=225;reg['cases'][4]['id']='rod_prefix225'
 reg['source_sha256'][str(Path(__file__).resolve().relative_to(ROOT))]=sha(Path(__file__))
 write(root/'REGISTRATION.json',reg);base.check(root,reg)

def run(root):
 prerequisite();reg=read(root/'REGISTRATION.json')
 assert sha(PARENT/'execution.json')==reg['previous_execution_sha256'] and sha(REVIEW)==reg['previous_review_sha256']
 assert read(root/'teacher.json')['cross_track_recovery']==dict(version='bounded_cross_track_recovery_v3',gain_per_s=2.,maximum_speed_mps=.02,load_scale_n=1.)
 base.run(root)

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--prepare',action='store_true');a=p.parse_args()
 if a.prepare:prepare(a.root.resolve())
 else:run(a.root.resolve())
