"""Prospective full90 frozen88 plan; no physics or additional training launch."""
from pathlib import Path
import json,time,hashlib,ast,sys
D=Path(__file__).parent;B=D.parents[1];OLD=B/'runtime/history88_review_20261030_v3';R=B/'runs/parameter88_history_frozen_full30_20261030_v1';RUN=B/'runs/parameter_history_cycle88_20261030_v2';REV=B/'runs/parameter_history_cycle88_review_20261030_v2';ARC=B/'runs/parameter_history_cycle88_archive_20261030_v2'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
assert not R.exists();R.mkdir()
# Only evaluator dependencies; never copy old launch/preparation entrypoints.
names={p.name for p in OLD.glob('published_*.py')}|{p.name for p in OLD.glob('parameter_*.py')}|{'evaluate_history88.py','frozen_helpers.py','persisted_history_critic.py','history_consumers.py','audit_published_episode_20261025.py','summarize_published_episode_audit_20261025.py','replay_published_filter_audit_20261025.py','replay_published_torque_audit_20261025.py','validate_published_finite_check_20261025.py'}
for name in sorted(names):(D/name).write_bytes((OLD/name).read_bytes());ast.parse((D/name).read_text())
sources={n:sha(D/n) for n in sorted(names)};methods={}
startup=read(RUN/'startup_v3/REVIEW.json');assert startup['passed'];snapshots=read(OLD/'STARTUP_SNAPSHOT_MANIFEST.json')['files']
for m,cpu in [('impedance',7),('admittance',8),('vmc',9)]:
 p=RUN/m/'REGISTRATION.json';protocol=read(p);snapshot=next(x for x in snapshots if Path(x['path']).stem==m);assert snapshot['sha256']==startup['methods'][m]['checkpoint_sha256']
 assert len(protocol['conditions'])==30
 methods[m]=dict(controller=m,cpu=cpu,device='cuda:0',runtime=protocol['runtime'],audit_runtime=str(D),training_registration=str(p),training_registration_sha256=sha(p),checkpoint=str(ARC/m/'cycle_00088.pt'),required_review=str(REV/'REVIEW.json'),case_ids=[c['id'] for c in protocol['conditions']],gate_case_id=protocol['conditions'][0]['id'],parent_cycle=88,action_seed=2026102638,source_hashes=sources,history_binding=protocol['history_critic_amendment']['binding'],software_preflight_snapshot=snapshot)
put(R/'PRE_REGISTRATION.json',dict(time=time.time(),parent_cycle=88,methods=methods,episodes=90,maximum_actions=123750,maximum_substeps=99000000,optimizer_updates=0,replay_writes=0,automatic_training=False,automatic_evaluation=False,requires='Full exact88 archive/review/health/loss and actual plots, then exact frozen restore checks and explicit launch receipt',action_seed=2026102638,scope='All30 registered training conditions per method; same original frozen82 seed, no held-out or independent training-seed claim, not final ESN comparison'))
put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),sources=sources,cpu=12,device='cuda:0',actual_updated_startup_snapshots=methods,budget_seconds=1800,maximum_recorded_native_actions=8271,physical_steps=0,optimizer_updates=0,replay_writes=0,checks=['Nonzero learned history weights and moments','Complete fullstate restore of actual updated88 snapshots','Full1375 recorded native versus external action sequence and terminal history','Actor49 isolation after history weights update','Actual partial88 rejected as complete88','Every replay row immutable'],scope='Recorded-observation software check only; no new frozen-policy performance score'))
print('Prospective frozen88 full90 registered; dispatch remains gated')
