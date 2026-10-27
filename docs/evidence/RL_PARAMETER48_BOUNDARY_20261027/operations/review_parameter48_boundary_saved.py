from pathlib import Path
import json,time,hashlib,ast
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/parameter48_boundary_preparation_20261027_v1';RUN=B/'runs/parameter_capacity_pool30_cycle48_20261026_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not Path('/proc/401313').exists() and not (O/'SAVED_REVIEW.json').exists()
plan=read(O/'PLAN.json');r=read(O/'evidence/REVIEW.json');parent=read(B/'runs/parameter_capacity_pool30_cycle47_review_20261026_v1/REVIEW.json');startup=read(RUN/'startup/REVIEW.json')
assert r['passed'] and parent['passed'] and startup['passed'] and sha(O/'audit.py')==plan['source_sha256'] and sha(RUN/'LAUNCH.json')==plan['formal_launch_sha256']
ast.parse((O/'audit.py').read_text());checks={};inputs={}
for m,v in r['methods'].items():
 a=parent['methods'][m];cp=O/'evidence'/(m+'.pt');reg=read(RUN/m/'REGISTRATION.json');oldreg=read(Path(reg['resume_parent_registration']['path']))
 assert v['boundary_observed'] and v['threshold']==plan['threshold']==2001000 and v['current_replay_capacity']==4000000
 assert v['steps']>=v['threshold'] and v['rows_beyond_old_capacity']==v['steps']-2000000
 assert v['retained_replay_rows']==a['steps'] and v['added_steps']==v['steps']-a['steps']==v['new_transition_mapping_count']
 assert v['updates']-a['updates']==v['added_steps']
 assert v['checkpoint_sha256']==sha(cp) and v['parent_sha256']==a['checkpoint_sha256']==sha(B/'runs/parameter_capacity_pool30_cycle47_archive_20261026_v1'/m/'cycle_00047.pt')
 assert v['retained_replay_all_fields_exact'] and v['history_retained'] and v['optimizer_hyperparameters_retained'] and v['max_reward_reconstruction_error']==0
 assert v['terminal_coverage_count']==0 and v['registered_sampler_count']==v['model_count']==30 and v['startup_sampler_count_verified']
 assert v['saved_next65536_retained_draws']>0 and v['saved_next65536_beyond_old_capacity_draws']>0 and v['saved_next65536_retained_draws']+v['saved_next65536_beyond_old_capacity_draws']<=65536
 assert 'not a live learner sample log' in v['sampling_scope']
 assert v['replay_capacity_followup']==reg['replay_capacity_followup_stage']['marker'] and reg['replay_capacity_followup_stage']['parent_cycle']==47
 assert reg['replay_capacity_stage']==oldreg['replay_capacity_stage'] and reg['replay_capacity_stage']['parent_cycle']==23
 assert reg['replay_capacity_followup_stage']['entry_checkpoint']['sha256']==a['checkpoint_sha256']
 ident=plan['identities'][m];p=Path(f"/proc/{ident['pid']}");st=(p/'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and st[19]==ident['start_ticks'] and RUN.name.encode() in (p/'cmdline').read_bytes()
 checks[m]=dict(steps=v['steps'],added_steps=v['added_steps'],retained_rows=v['retained_replay_rows'],rows_beyond_old_capacity=v['rows_beyond_old_capacity'],old_draws=v['saved_next65536_retained_draws'],beyond_draws=v['saved_next65536_beyond_old_capacity_draws'],snapshot_sha256=v['checkpoint_sha256'],parent_sha256=v['parent_sha256'],terminal_coverage_count=0,formal_pid=ident['pid'])
 for f in [cp,RUN/m/'REGISTRATION.json']:inputs[str(f)]=sha(f)
for f in [O/'PLAN.json',O/'audit.py',O/'evidence/REVIEW.json',RUN/'LAUNCH.json',RUN/'startup/REVIEW.json']:inputs[str(f)]=sha(f)
out=dict(passed=True,time=time.time(),methods=checks,inputs=inputs,new_physics=0,optimizer_updates=0,scope='Independent saved arithmetic, registration lineage, immutable snapshot hashes and live formal identities. Original full-array/reward audit retained; no duplicate snapshot replay or new learner sampling. Snapshots contain no new terminals; complete48 fullreview must cover later terminal rewards.',convergence_claim=False)
(O/'SAVED_REVIEW.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(checks,indent=2))
