"""Prospective full90 frozen evaluation and finite actual-partial software preflight."""
from pathlib import Path
import ast,json,time,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'runs/parameter90_violation_frozen_full30_20261030_v1';T=B/'runs/parameter_violation_cycle90_20261030_v1';O=B/'runs/parameter_violation_cycle90_review_20261030_v1';A=B/'runs/parameter_violation_cycle90_archive_20261030_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
assert not R.exists();R.mkdir();startup=read(T/'startup/REVIEW.json');assert startup['passed'];assert read(B/'runtime/violation90_review_20261030_v1/ACTUAL_STARTUP_BIT_REVIEW.json')['passed']
for p in D.glob('*.py'):ast.parse(p.read_text())
sources={p.name:sha(p) for p in D.glob('*.py')};methods={};episodes={}
for m,cpu in [('impedance',7),('admittance',8),('vmc',9)]:
 p=T/m/'REGISTRATION.json';protocol=read(p);cp=T/'startup'/(m+'.pt');assert sha(cp)==startup['methods'][m]['checkpoint_sha256'];snapshot=dict(path=str(cp),sha256=sha(cp),bytes=cp.stat().st_size)
 methods[m]=dict(controller=m,cpu=cpu,device='cuda:0',runtime=protocol['runtime'],audit_runtime=str(D),training_registration=str(p),training_registration_sha256=sha(p),checkpoint=str(A/m/'cycle_00090.pt'),required_review=str(O/'REVIEW.json'),case_ids=[c['id'] for c in protocol['conditions']],gate_case_id=protocol['conditions'][0]['id'],parent_cycle=90,action_seed=2026102638,source_hashes=sources,history_binding=protocol['history_critic_amendment']['binding'],violation_binding=protocol['violation_critic_amendment']['binding'],software_preflight_snapshot=snapshot)
 case='active_short_train_0600';ep=B/'runs/parameter_history_cycle89_20261030_v1'/m/'train/cycle_00089'/case
 episodes[m]=dict(cycle=89,condition=case,journal=str(ep/'actor_intervals.jsonl'),terminal=str(ep/'TERMINAL.json'),journal_sha256=sha(ep/'actor_intervals.jsonl'),terminal_sha256=sha(ep/'TERMINAL.json'))
put(R/'PRE_REGISTRATION.json',dict(time=time.time(),parent_cycle=90,methods=methods,episodes=90,maximum_actions=123750,maximum_substeps=99000000,optimizer_updates=0,replay_writes=0,automatic_training=False,automatic_evaluation=False,requires='Complete exact90 archive/review/health/loss and actual plots, then exact frozen restore checks and explicit launch authorization; original frozen88 continues independently.',action_seed=2026102638,scope='All30 registered training conditions per method; same frozen82/88 seed. No performance-dependent case choice, held-out generalization or independent training seed claim. No final ESN comparison.'))
put(D/'PREFLIGHT_PLAN.json',dict(time=time.time(),sources=sources,cpu=12,device='cuda:0',actual_updated_startup_snapshots=methods,budget_seconds=1800,maximum_recorded_native_actions=8271,physical_steps=0,optimizer_updates=0,replay_writes=0,checks=['Exact updated partial90 full learner/replay restore','Learned bit online/target/Adam all nonzero','Full1375 recorded native/external sequence and terminal history/rawbit exact','All49-only actor isolation','Partial90 cannot pass complete90 recovery gate','All global/local RNG and full learner/replay remain unchanged'],scope='Original89 recorded observations with actually learned90 startup weights. Not a physical performance result or complete90 approval.'))
put(D/'PREFLIGHT_IMPLEMENTATION.json',dict(time=time.time(),script_sha256=sha(D/'check_updated_frozen.py'),plan_sha256=sha(D/'PREFLIGHT_PLAN.json'),episodes=episodes,physical_steps=0,optimizer_updates=0))
print('Frozen90 prospectively registered; finite recorded-input check ready, no physical launch')
