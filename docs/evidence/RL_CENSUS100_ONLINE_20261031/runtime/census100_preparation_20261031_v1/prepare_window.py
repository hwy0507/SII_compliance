from pathlib import Path
import json,hashlib,ast,time,difflib
P=Path(__file__).resolve().parent;B=P.parents[1];D=B/'runtime/census100_continuation_20261031_v1';O=B/'runs/parameter_census97_99_reward_stability_20261031_v1';W=B/'runs/parameter_census100_102_reward_stability_20261031_v1'
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
W.mkdir();rows=[]
for name in ['audit.py','review_saved.py','binding_rules.py','bind_inputs.py']:
 s=(O/name).read_text();n=s.replace('[97, 98, 99]','[100, 101, 102]').replace('[97,98,99]','[100,101,102]').replace('census97-99','census100-102')
 n=n.replace('paired97_to99_mean_delta','paired100_to102_mean_delta').replace('Fixed97-99','Fixed100-102').replace('Census97-99','Census100-102').replace('before97 launch','before100 launch').replace('First97 protocol','First100 protocol')
 if name=='audit.py':
  assert n.count("row['current_replay_capacity'] == 4_000_000")==1
  n=n.replace("row['current_replay_capacity'] == 4_000_000","row['current_replay_capacity'] == 6_000_000")
 if name=='binding_rules.py':
  n=n.replace("check_ref(p['previous94_96_failed_report'])","check_ref(p['previous94_96_failed_report']);check_ref(p['previous97_99_failed_report'])")
  n=n.replace("'protocol97'","'protocol100'").replace('if c==97:','if c==100:').replace('Initial94 registration changed','Initial100 registration changed')
  n=n.replace("previous94_96_failed_report=plan['previous94_96_failed_report']","previous94_96_failed_report=plan['previous94_96_failed_report'],previous97_99_failed_report=plan['previous97_99_failed_report']")
 if name=='bind_inputs.py':n=n.replace("previous94_96_failed_report=p['previous94_96_failed_report']","previous94_96_failed_report=p['previous94_96_failed_report'],previous97_99_failed_report=p['previous97_99_failed_report']")
 ast.parse(n);(W/name).write_text(n);(P/(name+'.window.diff')).write_text(''.join(difflib.unified_diff(s.splitlines(True),n.splitlines(True),fromfile=str(O/name),tofile=str(W/name))))
 rows.append(dict(parent=ref(O/name),new=ref(W/name)))
 # Audit AST differs only in title, cycle IDs and already-proven capacity literal.
 if name=='audit.py':
  expected=s.replace('census97-99','census100-102').replace('[97, 98, 99]','[100, 101, 102]').replace("row['current_replay_capacity'] == 4_000_000","row['current_replay_capacity'] == 6_000_000")
  expected=expected.replace('paired97_to99_mean_delta','paired100_to102_mean_delta').replace('Fixed97-99','Fixed100-102').replace('Census97-99','Census100-102').replace('before97 launch','before100 launch').replace('First97 protocol','First100 protocol')
  assert ast.dump(ast.parse(expected))==ast.dump(ast.parse(n))
p=read(O/'PLAN.json');p.update(time=time.time(),cycles=[100,101,102],intent=ref(D/'STABILITY_WINDOW_INTENT.json'),source_sha256=sha(W/'audit.py'),review_source_sha256=sha(W/'review_saved.py'),previous97_99_failed_report=ref(O/'REVIEW.json'),registration_timing='Before100 launch; no100 data;101/102 not registered or launched',source_preparation_timing='After complete failed97-99 audit and before100 launch',scope='New nonoverlapping prospective100-102 observation; original failed90-92/94-96/97-99 retained, original statistics unchanged, original sampled loss health separately required. No automatic training.')
p.pop('protocol97');p['protocol100']={m:ref(B/f'runs/parameter_census_cycle100_20261031_v1/{m}/REGISTRATION.json') for m in ['impedance','admittance','vmc']};put(W/'PLAN.json',p)
put(W/'SOURCE_LOCK.json',dict(files={f.name:sha(f) for f in sorted(W.glob('*.py'))}))
put(P/'WINDOW_SOURCE_REVIEW.json',dict(passed=True,time=time.time(),sources=rows,original_plan=ref(O/'PLAN.json'),original_lock=ref(O/'SOURCE_LOCK.json'),statistical_ast_unchanged_except_cycle_labels_and_capacity_assertion=True,capacity_repair_provenance=ref(B/'runtime/census99_window_completion_preparation_20261031_v1/CAPACITY_ASSERTION_REPAIR_REVIEW.json'),no_final_registration=True))
print('prospective100-102 sources locked; final9 inputs not yet available')
