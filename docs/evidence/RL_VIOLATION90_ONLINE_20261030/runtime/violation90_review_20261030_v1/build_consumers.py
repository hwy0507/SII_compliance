from pathlib import Path
import re,ast,hashlib,json,difflib,time,shutil
D=Path(__file__).resolve().parent;B=D.parents[1];OLD=B/'runtime/history89_review_20261030_v1';P=B/'runtime/violation90_online_20261030_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def once(s,a,b):
 assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
records={}
for src in ['startup89.py','review89.py','archive89.py','loss89.py','observe89.py','launch89.py','health89.py']:
 dst=src.replace('89','90');old=(OLD/src).read_text();s=old
 paths={'history89_continuation_20261030_v1':'violation90_online_20261030_v1','parameter_history_cycle89':'parameter_violation_cycle90','cycle_00089':'cycle_00090','startup89.py':'startup90.py','review89.py':'review90.py','archive89.py':'archive90.py','observe89.py':'observe90.py','health89.py':'health90.py','loss89.py':'loss90.py','loss89.png':'loss90.png','automatic90':'automatic91','Cycle89 archive':'Cycle90 archive','New history89 updates':'New violation90 updates','complete history88':'complete migrated89'}
 s=re.sub('|'.join(map(re.escape,sorted(paths,key=len,reverse=True))),lambda m:paths[m.group()],s)
 s=re.sub(r"(\['(?:cycle|parent_cycle|new_cycle)'\]\s*==\s*)(88|89)\b",lambda m:m[1]+str(int(m[2])+1),s)
 s=s.replace('cycle=89','cycle=90').replace("'--cycle','89'","'--cycle','90'")
 if src=='startup89.py':
  s=s.replace('time.monotonic()+300','time.monotonic()+1800')
  s=once(s," assert e['replay_observation_dimension']==51 and e['actor_observation_dimension']==49", " from persisted_violation_critic import marker as violation_marker, KEY as VK\n v=reg['violation_critic_amendment'];assert x['violation_critic_amendment']==old['violation_critic_amendment']==e['violation_critic_amendment']==v\n assert s[VK]==x['replay'][VK]==original[VK]==old['replay'][VK]==violation_marker(v['binding'])\n assert a['observations'].shape[1]==a['next_observations'].shape[1]==52\n assert e['replay_observation_dimension']==52 and e['actor_observation_dimension']==49")
  s=once(s,"   np.testing.assert_array_equal(a['observations'][k,:48]", "   assert a['observations'][k,51]==float((0. if j['interval'] is None else j['interval']['external_penetration_peak_m'])>.0002)\n   assert a['next_observations'][k,51]==float(nxt['interval']['external_penetration_peak_m']>.0002)\n   np.testing.assert_array_equal(a['observations'][k,:48]")
  s=s.replace('history_retained=True','history_retained=True,violation_marker_retained=True,new_current_next52_exact=True')
 if src=='review89.py':
  s=once(s,"    transitions=[t for t in lines", "    from persisted_violation_critic import marker as violation_marker, KEY as VK\n    v=reg['violation_critic_amendment'];assert x['violation_critic_amendment']==old['violation_critic_amendment']==execution['violation_critic_amendment']==v\n    assert x['learner'][VK]==x['replay'][VK]==old['learner'][VK]==old['replay'][VK]==violation_marker(v['binding'])\n    assert arr['observations'].shape[1]==arr['next_observations'].shape[1]==52\n    assert execution['replay_observation_dimension']==52 and execution['actor_observation_dimension']==49 and execution['protocol_sha256']==x['protocol_sha256']\n    transitions=[t for t in lines")
  s=once(s,"    assert len(transitions)==x['steps']-old['steps']", "    assert 0<len(transitions)<=41250 and len(transitions)==x['steps']-old['steps']")
  s=once(s,"            expected_current=np.r_", "            assert arr['observations'][k,51]==float((0. if j['interval'] is None else j['interval']['external_penetration_peak_m'])>.0002)\n            assert arr['next_observations'][k,51]==float(nxt['interval']['external_penetration_peak_m']>.0002)\n            expected_current=np.r_")
  s=s.replace('new_current_next51_and_raw_mixed_action_exact','new_current_next52_and_raw_mixed_action_exact').replace('retained_history_features_exact=True','retained_history_features_exact=True,retained_violation_features_exact=True')
 if src=='archive89.py':
  s=once(s,";del x\n", ";assert x['violation_critic_amendment']['first_cycle']==90;del x\n")
 if src=='loss89.py':
  s=once(s,"n=reg['history_critic_amendment']['binding']['rows']+41250;assert len(rows)==41250 and [r['step'] for r in rows]==list(range(n+1,n+41251))", "n=reg['violation_critic_amendment']['binding']['rows'];count=len(rows);assert 0<count<=41250 and count==read(O.parent/(m+'_REVIEW.json'))['new_transitions'] and [r['step'] for r in rows]==list(range(n+1,n+count+1))")
  s=s.replace('/1000,last1000_mean','/min(1000,len(a)),last1000_mean').replace('/1000,mean=','/min(1000,len(a)),mean=')
  s=once(s,"ax.plot(np.arange(499,len(a)),np.convolve(a,np.ones(500)/500,'valid'),lw=1)","ax.plot(np.arange(min(500,len(a))-1,len(a)),np.convolve(a,np.ones(min(500,len(a)))/min(500,len(a)),'valid'),lw=1)")
  s=s.replace('All41250 new updates per method','All actual contiguous updates per method (max41250); abort lengths retained').replace('rows=len(rows),optimizer','rows=len(rows),endpoint_window_count=min(1000,len(rows)),optimizer')
 if src=='launch89.py':
  s=s.replace('==84','==93').replace('negative_rejections=84','negative_rejections=93').replace('full_complete88_learner_and_replay_exact','full_migrated89_learner_and_replay_exact')
  s=once(s," contracts=read(P/'CONTRACT_REVIEW.json')", " assert read(P/'PREFLIGHT_FINISHED.json')['passed']\n contracts=read(P/'CONTRACT_REVIEW.json')")
 if src=='health89.py':
  s=once(s,"        learner = history_class(PublishedLearner, binding)(root", "        from persisted_violation_critic import violation_class, marker as violation_marker, KEY as VK\n        bit = protocol['violation_critic_amendment']['binding']\n        assert state[VK] == checkpoint['replay'][VK] == violation_marker(bit)\n        assert checkpoint['history_critic_amendment'] == execution['history_critic_amendment'] == protocol['history_critic_amendment']\n        assert checkpoint['violation_critic_amendment'] == execution['violation_critic_amendment'] == protocol['violation_critic_amendment']\n        assert checkpoint['protocol_sha256'] == sha(folder.resolve().parent/'REGISTRATION.json')\n        assert execution['replay_observation_dimension'] == 52 and execution['actor_observation_dimension'] == 49\n        assert checkpoint['replay']['arrays']['observations'].shape[1] == checkpoint['replay']['arrays']['next_observations'].shape[1] == 52\n        learner = violation_class(history_class(PublishedLearner, binding), bit)(root")
  s=s.replace('remaining time and causal history;','remaining time, causal history and raw violation bit;')
 ast.parse(s);(D/dst).write_text(s);(D/(dst+'.diff')).write_text(''.join(difflib.unified_diff(old.splitlines(True),s.splitlines(True),fromfile=str(OLD/src),tofile=str(D/dst))))
 records[dst]=dict(parent=str(OLD/src),parent_sha256=sha(OLD/src),sha256=sha(D/dst))
for name in ['persisted_history_critic.py','diagnose_published_value_bound_20261025.py','published_pair_reduction_learner_20261026.py','published_exact_projected_learner_20261026.py','published_finite_target_projection_20261026.py','published_projected_terminal_learner_20261026.py','published_target_pair_mean_20261026.py','published_terminal_loss_weight_20261026.py']:
 shutil.copyfile(OLD/name,D/name)
shutil.copyfile(P/'persisted_violation_critic.py',D/'persisted_violation_critic.py')
(D/'CONSUMER_ADAPTATION.json').write_text(json.dumps(dict(time=time.time(),files=records,old_replay_all52_columns_directly_equal=True,dual_markers=True,raw_strict_threshold=.0002,loss_baseline_full89_rows=True,abort_lengths_preserved=True,physical_steps=0,updates=0),indent=2)+'\n')
(D/'OBSERVATION_PLAN.json').write_text(json.dumps(dict(time=time.time(),source_sha256=sha(D/'observe90.py'),startup_wait_seconds=1800,observe_seconds=120,interval_seconds=10),indent=2)+'\n')
print('Consumers built; not yet registered')
