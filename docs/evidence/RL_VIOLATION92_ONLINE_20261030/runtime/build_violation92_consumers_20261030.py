from pathlib import Path
import ast,shutil,re,difflib,hashlib,json,time
B=Path(__file__).resolve().parent.parent;OLD=B/'runtime/violation91_review_20261030_v1';D=B/'runtime/violation92_review_20261030_v1';D.mkdir();records={}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['startup91.py','review91.py','archive91.py','loss91.py','observe91.py','launch91.py','health91.py']:
 s=(OLD/name).read_text();before=s;new=name.replace('91','92')
 mapping={'violation91_continuation_20261030_v1':'violation92_continuation_20261030_v1','parameter_violation_cycle91':'parameter_violation_cycle92','cycle_00091':'cycle_00092','automatic92':'automatic93','Cycle91 archive':'Cycle92 archive','New violation91 updates':'New violation92 updates','complete trained90':'complete trained91','full_trained90_learner_and_replay_exact':'full_trained91_learner_and_replay_exact','loss91.png':'loss92.png'}
 mapping.update({n:n.replace('91','92') for n in ['startup91.py','review91.py','archive91.py','loss91.py','observe91.py','health91.py']})
 s=re.sub('|'.join(map(re.escape,sorted(mapping,key=len,reverse=True))),lambda m:mapping[m[0]],s)
 s=re.sub(r"(\['(?:cycle|parent_cycle|new_cycle)'\]\s*==\s*)(90|91)\b",lambda m:m[1]+str(int(m[2])+1),s)
 s=s.replace('cycle=91','cycle=92').replace("'--cycle','91'","'--cycle','92'")
 ast.parse(s);(D/new).write_text(s);(D/(new+'.diff')).write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile=str(OLD/name),tofile=new)))
 records[new]=dict(parent=str(OLD/name),parent_sha256=sha(OLD/name),sha256=sha(D/new))
for name in ['persisted_history_critic.py','persisted_violation_critic.py','diagnose_published_value_bound_20261025.py','published_pair_reduction_learner_20261026.py','published_exact_projected_learner_20261026.py','published_finite_target_projection_20261026.py','published_projected_terminal_learner_20261026.py','published_target_pair_mean_20261026.py','published_terminal_loss_weight_20261026.py']:shutil.copyfile(OLD/name,D/name)
assert (D/'health92.py').read_bytes()==(OLD/'health91.py').read_bytes()
(D/'CONSUMER_ADAPTATION.json').write_text(json.dumps(dict(time=time.time(),files=records,actual_parent91_rows=True,all52_columns_and_dual_markers_preserved=True,first_revision_cycles_remain_history88_violation90=True,loss_rows_start_at_complete91_steps_not_original89_binding=True,physics_steps=0,updates=0),indent=2)+'\n')
(D/'OBSERVATION_PLAN.json').write_text(json.dumps(dict(time=time.time(),source_sha256=sha(D/'observe92.py'),startup_wait_seconds=1800,observe_seconds=120,interval_seconds=10),indent=2)+'\n')
(D/'SOURCES.json').write_text(json.dumps(dict(time=time.time(),files={p.name:sha(p) for p in D.glob('*.py')}),indent=2)+'\n')
print('Finite92 consumers ready; no dispatch')
