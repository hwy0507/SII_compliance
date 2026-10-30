from pathlib import Path
import json,time,hashlib,shutil,ast,difflib
D=Path(__file__).parent;B=D.parents[1];OLD=B/'runtime/parameter86_frozen_switches_20261030_v1';BASE=B/'runs/parameter86_frozen_switches_20261030_v1';R=B/'runtime/parameter86_half_std_paired_20261030_v1';O=B/'runs'/R.name
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
assert read(BASE/'FINISHED.json')['passed'] and read(BASE/'SAVED_REVIEW.json')['passed'] and read(BASE/'PLOT_INSPECTION.json')['actual_image_viewed']
assert read(D/'SEEDS_RAW_REVIEW.json')['passed'] and read(D/'SEEDS_RAW_SAVED_REVIEW.json')['passed']
R.mkdir(exist_ok=False);O.mkdir(exist_ok=False)
oldplan=read(BASE/'PLAN.json')
for name in oldplan['groups']['impedance_short0600']['source_hashes']:shutil.copy2(OLD/name,R/name)
shutil.copy2(D/'half_std_probe.py',R/'half_std_probe.py')
name='evaluate_parameter86_half_std_20261030.py'
original=(OLD/'evaluate_parameter86_frozen_switches_20261030.py').read_text();s=original
s=s.replace('Frozen complete86 parameter policies on four prospectively selected method/case groups.','Finite fixed86 paired intervention: pre-tanh Gaussian sampling std multiplied by0.5.')
s=s.replace('Four fixed external action seeds per group; no optimization or formal replay writes.','Same four groups and four external seeds as completed baseline; no updates or replay writes.\nSerialized learner state is unchanged; the actor sampling distribution intentionally changes.')
s=s.replace('from evaluate_parameter29_seeded_switch_20261026 import (','from half_std_probe import install_probe\nfrom evaluate_parameter29_seeded_switch_20261026 import (')
s=s.replace("    assert reg['gate_case_id'] == reg['case_ids'][0]", "    assert reg['gate_case_id'] == reg['case_ids'][0]\n    assert reg['pre_tanh_std_factor'] == plan['pre_tanh_std_factor'] == .5\n    for entry in plan['baseline_inputs'].values():assert sha(entry['path']) == entry['sha256']")
s=s.replace("    result = gate(learner, ck, observations, reg['action_seeds'][0], reg['gate_case_id'], digest)", "    probe = install_probe(learner, observations, digest)\n    write(output/('CHECK_ONLY_PROBE.json' if check_only else 'STARTUP_PROBE.json'), probe)\n    result = gate(learner, ck, observations, reg['action_seeds'][0], reg['gate_case_id'], digest)")
s=s.replace("scope='Complete86 selected method/case sensitivity: four predeclared action seeds, no updates; not all30, independent training seeds, generalization, entropy intervention, historical causal attribution or final ESN comparison'", "scope='Paired inference intervention: same fixed86 weights/groups/seeds, pre-tanh Gaussian std factor0.5. Serialized state unchanged but policy sampler intentionally changed. Not a training entropy intervention or convergence claim'",1)
s=s.replace("new_optimizer_updates=0, convergence_claim=False))", "new_optimizer_updates=0, convergence_claim=False, pre_tanh_std_factor=.5, sampling_distribution_intentionally_changed=True))")
ast.parse(s);(R/name).write_text(s);(R/(name+'.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='baseline_frozen86',tofile=name)))
# Preparation/launch keep the original finite budget and exact recovery checks.
for n in ['preflight.py','launch.py','review.py']:
 text=(OLD/n).read_text().replace('evaluate_parameter86_frozen_switches_20261030','evaluate_parameter86_half_std_20261030')
 if n=='preflight.py':
  text=text.replace("'plan_hash':'0'*64}","'plan_hash':'0'*64,'std_factor':1.0}")
  text=text.replace("'plan_hash':'plan_sha256'}","'plan_hash':'plan_sha256','std_factor':'pre_tanh_std_factor'}")
 if n=='review.py':
  text=text.replace("    write(O/'REVIEW.json',report)","    write(O/'REVIEW.json',report)") # handled exact indentation below
  assert " write(O/'REVIEW.json',report)" in text
  text=text.replace(" write(O/'REVIEW.json',report)"," from pair_review import review_paired\n report['paired_variance_intervention'] = review_paired(O, report, plan)\n write(O/'REVIEW.json',report)")
  text=text.replace("fig.suptitle('Frozen86 selected groups, four action seeds each; green=Strict success')","fig.suptitle('Frozen86 half-std intervention, same16 pairs; green=Strict success')")
 ast.parse(text);(R/n).write_text(text)
shutil.copy2(D/'pair_review.py',R/'pair_review.py')
source={p.name:sha(p) for p in R.glob('*.py') if p.name not in ['preflight.py','launch.py','review.py']}
groups={}
for key,reg in oldplan['groups'].items():
 reg=dict(reg,audit_runtime=str(R),source_hashes=source,pre_tanh_std_factor=.5);groups[key]=reg
baseline_inputs={n:ref(BASE/n) for n in ['PLAN.json','REVIEW.json','SAVED_REVIEW.json','FINISHED.json','PLOT_INSPECTION.json']}
baseline_inputs['raw_audit']=ref(D/'SEEDS_RAW_REVIEW.json');baseline_inputs['raw_saved']=ref(D/'SEEDS_RAW_SAVED_REVIEW.json')
for k in groups:
 for n in ['FINISHED.json','RESULTS.json','REGISTRATION.json']:baseline_inputs[k+'_'+n]=ref(BASE/k/n)
plan=dict(time=time.time(),parent_cycle=86,action_seeds=oldplan['action_seeds'],groups=groups,episodes=16,maximum_actions=22000,maximum_substeps=17600000,optimizer_updates=0,automatic_extension=False,wall_dispatch_deadline_seconds=7200,pre_tanh_std_factor=.5,baseline_root=str(BASE),baseline_inputs=baseline_inputs,
 rationale='Complete original16: Ishort0600 Task4/Strict2; Ashort0900 and Along0200 Task3/Strict3 each, seed35 carry failures; Vshort0000 Task4/Strict4. Fixed weights isolate observed within-policy sensitivity but do not show variance reduction helps. One paired factor0.5 intervention on all original4 groups/4seeds, including V without observed label variation. No further factor search or automatic training.',
 factor_rationale='One interpretable finite candidate halves Gaussian pre-tanh std at each fixed input while preserving its mean; Gaussian entropy would decrease by d*ln2 before tanh, but tanh/context and closed-loop state changes mean neither final action std nor policy entropy is guaranteed to halve. This is not direct evidence for a particular trained target entropy.',
 intervention='Instance forward wrapper returns original mean and original log_std-ln2. No parameter/optimizer/RNG changes, original tanh/bounds/CHEQ mixing/critic/reward/physics/gates preserved; sampler intentionally differs. All native actions replayed with the same registered wrapper. Native deterministic mean map remains unchanged at the same input.',
 outcomes='All16 per-seed paired returns, Task/Strict, horizon/abort, external penetration, contact comfort and torque retained. Report improvements and regressions, no best-seed promotion or automatic winner. Entire original baseline stays frozen and closed.',
 limits='Selected development conditions with known baseline outcomes, four action seeds, not independent training seeds or generalization. Paired effect applies only to this one inference distribution intervention at fixed86. Does not identify historical85/86/87 drift, establish healthy loss/convergence, or authorize entropy training or automatic88.',
 prior_evidence=oldplan['prior_evidence'],new_training_updates=0)
put(O/'PLAN.json',plan)
for key,reg in groups.items():
 d=O/key;d.mkdir();put(d/'REGISTRATION.json',dict(reg,group=key,plan=str(O/'PLAN.json'),plan_sha256=sha(O/'PLAN.json')))
put(R/'SOURCE_REVIEW.json',dict(passed=True,parent_evaluator=ref(OLD/'evaluate_parameter86_frozen_switches_20261030.py'),candidate_evaluator=ref(R/name),probe=ref(R/'half_std_probe.py'),pair=ref(R/'pair_review.py'),plan=ref(O/'PLAN.json'),serialized_state_unchanged_not_unchanged_policy=True,original_live_sources_edited=False,new_physics=0,new_optimizer_updates=0))
shutil.copy2(__file__,R/'prepare.py')
print('Registered',O,sha(O/'PLAN.json'))
