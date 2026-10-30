from pathlib import Path
import hashlib,json,shutil,difflib,ast,time,subprocess,socket
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R=B/'runtime/parameter86_frozen_switches_20261030_v1'; O=B/'runs/parameter86_frozen_switches_20261030_v1'
R.mkdir(exist_ok=False); O.mkdir(exist_ok=False)
shutil.copy2(__file__,R/'prepare.py')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
old=B/'runtime/parameter82_frozen_full30_20261030_v1'
for p in old.glob('*.py'):shutil.copy2(p,R/p.name)
name='evaluate_parameter86_frozen_switches_20261030.py'
s=(old/'evaluate_parameter82_frozen_full30_20261030.py').read_text(); original=s
changes=[
('Frozen complete82 parameter policies on all30 registered training conditions.','Frozen complete86 parameter policies on four prospectively selected method/case groups.'),
('One external action seed per method;', 'Four fixed external action seeds per group;'),
("assert expected_cycle in (81, 82)","assert expected_cycle == 86"),
('def main(registration, check_only, expected_cycle=82):','def main(registration, check_only, expected_cycle=86):'),
('    if expected_cycle != 82 and not check_only:\n        raise ValueError("Only planned82 may execute physics; validation81 is check-only")\n    if expected_cycle not in (81, 82):\n        raise ValueError("Unregistered parent cycle")','    if expected_cycle != 86:\n        raise ValueError("Only registered complete86 is allowed")'),
("    assert len(reg['case_ids']) == len(set(reg['case_ids'])) == 30\n    assert reg['action_seed'] == 2026102638", "    validate_design(reg)"),
("    assert reg['case_ids'] == [c['id'] for c in protocol['conditions']]", "    assert reg['case_ids'][0] in [c['id'] for c in protocol['conditions']]"),
("reg['action_seed'], reg['gate_case_id']", "reg['action_seeds'][0], reg['gate_case_id']"),
("checkpoint_sha256=sha(reg['checkpoint']), action_seed=reg['action_seed'], case_ids=reg['case_ids'],", "checkpoint_sha256=sha(reg['checkpoint']), action_seeds=reg['action_seeds'], case_ids=reg['case_ids'],"),
('expected_episodes=30,','expected_episodes=4,'),
('maximum_actions=41250, maximum_substeps=33000000','maximum_actions=5500, maximum_substeps=4400000'),
("scope='Prospectively selected complete82 frozen policy on all30 training conditions, one external action seed; not independent training seeds, held-out tests or final ESN comparison'", "scope='Complete86 selected method/case sensitivity: four predeclared action seeds, no updates; not all30, independent training seeds, generalization, entropy intervention, historical causal attribution or final ESN comparison'"),
("    seed = reg['action_seed']\n    for case in reg['case_ids']:", "    case = reg['case_ids'][0]\n    for seed in reg['action_seeds']:"),
('folder = output/case',"folder = output/f'seed_{seed}'"),
("output/f'{case}.stderr.log'", "output/f'seed_{seed}.stderr.log'"),
('completed_conditions=len(results)', 'completed_episodes=len(results)'),
("output/f'{case}_REVIEW.json'", "output/f'seed_{seed}_REVIEW.json'"),
('expected=30','expected=4'),
('time=time.time(), episodes=30,','time=time.time(), episodes=4,'),
("choices=[81,82], default=82", "choices=[86], default=86")]
for a,b in changes:
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
validation='''
SEEDS = [2026102633, 2026102634, 2026102635, 2026102636]
GROUPS = {
    'impedance_short0600': ('impedance', 'active_short_train_0600', 7),
    'admittance_short0900': ('admittance', 'active_short_train_0900', 8),
    'admittance_long0200': ('admittance', 'active_long_train_0200', 9),
    'vmc_short0000': ('vmc', 'active_short_train_0000', 10),
}

def validate_design(reg):
    plan_path = Path(reg['plan'])
    assert sha(plan_path) == reg['plan_sha256']
    plan = json.loads(plan_path.read_text())
    assert plan['parent_cycle'] == reg['parent_cycle'] == 86
    assert plan['action_seeds'] == reg['action_seeds'] == SEEDS
    assert plan['episodes'] == 16 and plan['maximum_actions'] == 22000
    assert plan['maximum_substeps'] == 17600000 and plan['optimizer_updates'] == 0
    assert plan['automatic_extension'] is False
    assert set(plan['groups']) == set(GROUPS)
    for key, (method, case, cpu) in GROUPS.items():
        group = plan['groups'][key]
        assert group['controller'] == method and group['case_ids'] == [case] and group['cpu'] == cpu
    entry = plan['groups'][reg['group']]
    for key in ['controller', 'case_ids', 'cpu', 'device', 'checkpoint', 'checkpoint_sha256',
                'training_registration', 'training_registration_sha256', 'required_review',
                'required_review_sha256', 'gate_observations', 'gate_observations_sha256',
                'gate_case_id', 'runtime', 'audit_runtime', 'source_hashes']:
        assert reg[key] == entry[key], key
    assert reg['gate_case_id'] == reg['case_ids'][0]

'''
s=s.replace('\ndef main(',validation+'\ndef main(',1)
ast.parse(s);(R/name).write_text(s)
(R/(name+'.diff')).write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='frozen82_source',tofile=name)))
source={p.name:sha(p) for p in R.glob('*.py') if p.name!='prepare.py'}
seeds=[2026102633,2026102634,2026102635,2026102636]
groups={}
for key,method,case,cpu in [('impedance_short0600','impedance','active_short_train_0600',7),('admittance_short0900','admittance','active_short_train_0900',8),('admittance_long0200','admittance','active_long_train_0200',9),('vmc_short0000','vmc','active_short_train_0000',10)]:
 reg=json.loads((B/f'runs/parameter82_frozen_full30_20261030_v1/{method}/REGISTRATION.json').read_text())
 reg.update(cpu=cpu,audit_runtime=str(R),case_ids=[case],gate_case_id=case,parent_cycle=86,action_seeds=seeds)
 del reg['action_seed']
 for k in ['checkpoint','training_registration','required_review','gate_observations']:
  reg[k]=reg[k].replace('cycle82','cycle86').replace('cycle_00082','cycle_00086')
 reg['gate_observations']=str(B/f'runs/parameter_partial75_recovery_cycle86_20261029_v1/{method}/train/cycle_00086/{case}/actor_intervals.jsonl')
 for k in ['checkpoint','training_registration','required_review','gate_observations']:reg[k+'_sha256']=sha(reg[k])
 reg['source_hashes']=source
 groups[key]=reg
plan=dict(time=time.time(),host=socket.gethostname(),parent_cycle=86,action_seeds=seeds,groups=groups,episodes=16,maximum_actions=22000,maximum_substeps=17600000,maximum_simulated_seconds=880,optimizer_updates=0,automatic_extension=False,wall_dispatch_deadline_seconds=21600,
 rationale='At complete86, impedance short0600 lost Strict, admittance short0900 lost Task and long0200 gained Task, vmc short0000 regained Strict relative85. Four selected groups represent all three methods and both Task and Strict switches; selection uses known85/86 outcomes. Diagnose fixed-current-weight variation before choosing a training amendment. No new86 evaluation result has been inspected at registration.',
 prior_evidence='Frozen29 short0600, all3 methods and same four action seeds, already established within-policy I/A outcome sensitivity. Old12-episode budget remains closed. New complete86 follows57 more cycles; three groups are different conditions. Only impedance short0600 shares method/case and may be compared descriptively to29; checkpoint/training-stage differences do not identify a causal training mechanism.',
 outcomes='Report all16 returns, Task/Strict, horizon/abort, external penetration, completion time, contact/comfort and torque; all four seeds per group, range and sample success fractions. No best-seed promotion. Any within-group label variation establishes fixed86 policy sensitivity on those sampled seeds. No variation with n=4 does not establish robustness or zero failure probability.',
 limits='Development conditions selected after85/86, not representative all30 or generalization; common action seeds are not independent training seeds and cannot recreate online85/86 random streams. No historical causal variance decomposition, entropy intervention, new convergence threshold or automatic88. Original85-87 deadline and results stay unchanged.',
 invariants='Original canonical48 actor, critic50, learner/optimizer/replay/RNG restored exactly; 4m capacity with23/47 history; no updates or replay appends; fixed86 step and native stochastic CHEQ action/mixing; identical physical MJB/dt5e-5/filter/actuator/gates/reward. Entire action stream independently replayed, full initial/final learner/replay digest and checkpoint hashes required.',
 remote=dict(main='f7817a1018835facc330ce9e571ba54ff73556de',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',queried_fetched_read=True),
 old29_report=str(B/'repository/SII_compliance/docs/RL_PARAMETER31_FROZEN29_SEEDS_20261026.md'))
write(O/'PLAN.json',plan)
for key,reg in groups.items():
 d=O/key;d.mkdir();reg=dict(reg,group=key,plan=str(O/'PLAN.json'),plan_sha256=sha(O/'PLAN.json'));write(d/'REGISTRATION.json',reg)
write(R/'SOURCE_REVIEW.json',dict(passed=True,original_evaluator_sha256=sha(old/'evaluate_parameter82_frozen_full30_20261030.py'),new_evaluator_sha256=sha(R/name),copied_sources_exact=all(sha(R/p.name)==sha(p) for p in old.glob('*.py')),plan_sha256=sha(O/'PLAN.json'),physics_action_loop_changed=False,changes=len(changes),new_physics=0,new_optimizer_updates=0))
print(json.dumps(dict(runtime=str(R),root=str(O),plan_sha256=sha(O/'PLAN.json'))))
