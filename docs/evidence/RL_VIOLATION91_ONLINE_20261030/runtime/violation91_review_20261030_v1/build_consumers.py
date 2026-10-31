from pathlib import Path
import re,ast,hashlib,json,difflib,time,shutil
D=Path(__file__).resolve().parent;B=D.parents[1];OLD=B/'runtime/violation90_review_20261030_v1';P=B/'runtime/violation91_continuation_20261030_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records={}
for name in ['startup90.py','review90.py','archive90.py','loss90.py','observe90.py','launch90.py','health90.py']:
 newname=name.replace('90','91');old=(OLD/name).read_text();s=old
 changes={'violation90_online_20261030_v1':'violation91_continuation_20261030_v1','parameter_violation_cycle90':'parameter_violation_cycle91','cycle_00090':'cycle_00091','startup90.py':'startup91.py','review90.py':'review91.py','archive90.py':'archive91.py','observe90.py':'observe91.py','health90.py':'health91.py','loss90.py':'loss91.py','loss90.png':'loss91.png','automatic91':'automatic92','Cycle90 archive':'Cycle91 archive','New violation90 updates':'New violation91 updates','complete migrated89':'complete trained90','full_migrated89_learner_and_replay_exact':'full_trained90_learner_and_replay_exact'}
 s=re.sub('|'.join(map(re.escape,sorted(changes,key=len,reverse=True))),lambda m:changes[m.group()],s)
 s=re.sub(r"(\['(?:cycle|parent_cycle|new_cycle)'\]\s*==\s*)(89|90)\b",lambda m:m[1]+str(int(m[2])+1),s)
 s=s.replace('cycle=90','cycle=91').replace("'--cycle','90'","'--cycle','91'")
 if name=='loss90.py':
  target="n=reg['violation_critic_amendment']['binding']['rows']";assert s.count(target)==1
  s=s.replace(target,"n=read(Path(reg['post_interruption_continuation']['cycle_review']['path']))['methods'][m]['steps']")
 if name=='launch90.py':
  s=s.replace('==93','==108').replace('negative_rejections=93','negative_rejections=108')
  s=s.replace("initial['learned_history_weights_and_adam_retained']", "initial['learned_history_weights_and_adam_retained'] and initial['learned_violation_weights_and_adam_retained']")
  old_ids="(2675653,'575369491'),(2675660,'575369492'),(2675662,'575369492'),(2675665,'575369492'),(2713409,'575376596')"
  new_ids="(283421,'576955693'),(283428,'576955694'),(283430,'576955694'),(283433,'576955694'),(292743,'576957672')"
  assert s.count(old_ids)==1;s=s.replace(old_ids,new_ids)
 ast.parse(s);(D/newname).write_text(s);(D/(newname+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(OLD/name),tofile=newname)))
 records[newname]=dict(parent=str(OLD/name),parent_sha256=sha(OLD/name),sha256=sha(D/newname))
for name in ['persisted_history_critic.py','persisted_violation_critic.py','diagnose_published_value_bound_20261025.py','published_pair_reduction_learner_20261026.py','published_exact_projected_learner_20261026.py','published_finite_target_projection_20261026.py','published_projected_terminal_learner_20261026.py','published_target_pair_mean_20261026.py','published_terminal_loss_weight_20261026.py']:shutil.copyfile(OLD/name,D/name)
(D/'CONSUMER_ADAPTATION.json').write_text(json.dumps(dict(time=time.time(),files=records,actual_parent90_rows_including_abort=True,all52_columns_and_dual_markers_preserved=True,first_revision_cycles_remain_history88_violation90=True,loss_rows_start_at_complete90_steps_not_original89_binding=True,physics_steps=0,updates=0),indent=2)+'\n')
(D/'OBSERVATION_PLAN.json').write_text(json.dumps(dict(time=time.time(),source_sha256=sha(D/'observe91.py'),startup_wait_seconds=1800,observe_seconds=120,interval_seconds=10),indent=2)+'\n')
(D/'SOURCES.json').write_text(json.dumps(dict(time=time.time(),files={p.name:sha(p) for p in D.glob('*.py')}),indent=2)+'\n')
print('Finite91 consumers prepared; no training dispatched')
