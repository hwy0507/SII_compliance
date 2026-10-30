from pathlib import Path
import json,hashlib,time,os,math,traceback
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def stat(p):
 s=p.stat();return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)
def cli(job,key):return job['command'][job['command'].index(key)+1]
plan=read(D/'PLAN.json');os.sched_setaffinity(0,{plan['cpu']});start=time.monotonic()
def budget():assert time.monotonic()-start<plan['budget_seconds'],'Registered inventory budget expired; do not restart science'
try:
 for x in plan['inputs']:assert sha(Path(x['path']))==x['sha256']
 full=read(B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1/REVIEW.json');assert full['passed']
 shutdown=read(B/'runs/user_shutdown_pause_20261026_v1/RECOVERY_MANIFEST.json');shutdown_steps={x['method']:x['checkpoints']['periodic']['steps'] for x in shutdown['checkpoints']}
 original_launch=B/'runs/cheq_clock_online_seed20261025_v1/LAUNCH.json';recovery_launch=B/'runs/recovery_cheq_resume_20261026_v1/LAUNCH.json';batch_launch=B/'runs/cheq_batch32768_online_20261026_v1/LAUNCH.json'
 launch_refs=[ref(p) for p in [original_launch,recovery_launch,batch_launch]]
 methods={}
 with (D/'PROGRESS.jsonl').open('x') as log:
  for m,rootreg in zip(plan['methods'],plan['roots']):
   budget();p=Path(rootreg);chain=[];seen=set()
   for _ in range(plan['max_registration_nodes_per_method']):
    assert p not in seen;seen.add(p);r=read(p);kind=None;parent=None
    for key in ['post_interruption_continuation','interrupted_episode_recovery']:
     if key in r:kind=key;parent=r[key]['parent_registration'];break
    if parent is None and 'resume_parent_registration' in r:kind='resume_parent_registration';parent=r[kind]
    chain.append(dict(registration=ref(p),parent_kind=kind,parent=parent))
    assert r['runtime']==str(B/'runtime/source_train17_clock')
    if parent is None:break
    p=Path(parent['path']);assert sha(p)==parent['sha256']
   else:raise AssertionError('Registration chain budget')
   chain.reverse();physical=[];extra=[]
   for node in chain:
    p=Path(node['registration']['path'])
    if p.parent==B/'runs/clock_online_control_v1':
     j=next(x for x in read(original_launch)['jobs'] if x['controller']==m);assert cli(j,'--registration')==str(p);train=Path(cli(j,'--output'));ex=read(train/'EXECUTION.json');assert ex['protocol_sha256']==node['registration']['sha256'] and ex['resumed_from'] is None;extra.append(ref(train/'EXECUTION.json'))
     physical.append(dict(train=str(train),registration=node['registration'],early_source='original LAUNCH/EXECUTION'))
     j=next(x for x in read(recovery_launch)['jobs'] if x['method']==m);train=Path(cli(j,'--output'));reg=train.parent/'REGISTRATION.json';rr=read(reg);assert rr['registration_sha256']==node['registration']['sha256'] and rr['resume_checkpoint']==cli(j,'--resume');extra.append(ref(reg));physical.append(dict(train=str(train),registration=ref(reg),early_source='shutdown recovery LAUNCH and wrapper registration'))
    elif p.parent==B/'runs/cheq_batch32768_online_20261026_v1':
     j=next(x for x in read(batch_launch)['jobs'] if x['method']==m);train=Path(cli(j,'--output'));assert Path(cli(j,'--resume')).parent==Path(physical[-1]['train']);ex=train.parent/'BATCH_TRIAL_EXECUTION.json';assert read(ex)['protocol_sha256']==node['registration']['sha256'];extra.append(ref(ex));physical.append(dict(train=str(train),registration=node['registration'],early_source='batch LAUNCH/EXECUTION'))
    else:
     assert p.parent.name==m;physical.append(dict(train=str(p.parent/'train'),registration=node['registration'],early_source=None))
   assert len(physical)<=plan['max_training_roots_per_method'] and len({x['train'] for x in physical})==len(physical)
   for x in physical:
    p=Path(x['train'])/'transitions.jsonl';assert p.exists();first=json.loads(p.open('rb').readline());x['first_step']=first['step']
   assert physical[0]['first_step']==1 and physical[1]['first_step']==shutdown_steps[m]+1
   partial=read(B/f'runs/parameter75_interruption_recovery_20261029_v1/{m}/REVIEW.json');extra.append(ref(B/f'runs/parameter75_interruption_recovery_20261029_v1/{m}/REVIEW.json'))
   n76=next(i for i,x in enumerate(physical) if 'partial75_recovery_cycle76_' in x['train']);assert physical[n76]['first_step']==partial['steps']+1
   endpoint=full['methods'][m]['steps'];total=0;tails=0;episodes=[];problems=[]
   for ri,x in enumerate(physical):
    budget();train=Path(x['train']);p=train/'transitions.jsonl';before=stat(p);h=hashlib.sha256();lo=x['first_step'];hi=physical[ri+1]['first_step']-1 if ri+1<len(physical) else endpoint;assert hi>=lo
    counters={};count=0;kept=0;tail=0;last=lo-1;bad_json=0;discontinuities=[]
    with p.open('rb') as f:
     for line in f:
      h.update(line);count+=1
      if count%10000==0:budget()
      try:r=json.loads(line)
      except json.JSONDecodeError:
       bad_json+=1;continue
      step=r['step']
      if step!=last+1:discontinuities.append(dict(line=count,previous=last,step=step))
      last=step
      if step>hi:tail+=1;continue
      assert lo<=step<=hi and math.isfinite(r['reward'])
      key=(r['cycle'],r['condition']);c=counters.setdefault(key,dict(transitions=0,done_count=0,first_global_step=step,last_global_step=step));assert c['done_count']==0
      c['transitions']+=1;c['done_count']+=int(r['done']);c['last_global_step']=step;kept+=1
    assert stat(p)==before,'Historical log changed during audit'
    if bad_json or discontinuities or kept!=hi-lo+1:problems.append(dict(train=str(train),bad_json=bad_json,step_discontinuities=discontinuities[:20],count=kept,expected=hi-lo+1))
    for (cycle,condition),c in counters.items():
     ep=train/f'cycle_{cycle:05d}'/condition;journal=ep/'actor_intervals.jsonl';terminal=ep/'TERMINAL.json';exists=journal.exists();termok=c['done_count']==0 or terminal.exists()
     if not exists or not termok:problems.append(dict(episode=str(ep),journal_exists=exists,terminal_required=bool(c['done_count']),terminal_exists=terminal.exists()))
     episodes.append(dict(train=str(train),cycle=cycle,condition=condition,**c,journal=str(journal),journal_exists=exists,journal_bytes=journal.stat().st_size if exists else None,terminal_required=bool(c['done_count']),terminal_exists=terminal.exists(),minimum_journal_rows_needed=c['transitions']+(0 if c['done_count'] else 1),raw_bytes_checked=False))
    x.update(transitions=dict(path=str(p),bytes=before[2],sha256=h.hexdigest()),selected_first_step=lo,selected_last_step=hi,retained_transitions=kept,parsed_log_lines=count,last_parsed_step=last,post_checkpoint_tail_rows=tail,episode_count=len(counters),bad_json_lines=bad_json,step_discontinuities=discontinuities[:20]);total+=kept;tails+=tail
    progress=dict(time=time.time(),method=m,root_index=ri+1,roots=len(physical),selected_steps=total,endpoint=endpoint);log.write(json.dumps(progress)+'\n');log.flush()
   assert total==endpoint
   out=D/(m+'_episodes.jsonl')
   with out.open('x') as f:
    for e in episodes:f.write(json.dumps(e)+'\n')
   methods[m]=dict(registration_nodes=len(chain),chain=chain,physical_logs=len(physical),roots=physical,extra_bindings=extra,retained_transition_rows=total,expected_complete85_steps=endpoint,post_checkpoint_tail_rows=tails,episode_cohorts=len(episodes),retained_partial_episode_cohorts=sum(not e['terminal_required'] for e in episodes),missing_journals=sum(not e['journal_exists'] for e in episodes),missing_required_terminals=sum(e['terminal_required'] and not e['terminal_exists'] for e in episodes),problems=problems,selected_log_step_coverage_verified=not problems,episode_inventory=ref(out),full_checkpoint_row_equality_proven=False,history_values_reconstructed=False)
   print(m,{k:v for k,v in methods[m].items() if k not in ['chain','roots','extra_bindings','episode_inventory','problems']},flush=True)
 for x in plan['inputs']:assert sha(Path(x['path']))==x['sha256']
 for x in launch_refs:assert sha(Path(x['path']))==x['sha256']
 passed=all(x['selected_log_step_coverage_verified'] for x in methods.values())
 put(D/'REVIEW.json',dict(passed=passed,audit_completed=True,time=time.time(),elapsed_s=time.monotonic()-start,plan=ref(D/'PLAN.json'),launch_bindings=launch_refs,methods=methods,new_physics=0,new_network_forward=0,optimizer_updates=0,replay_writes=0,limitation='Full retained JSON log step coverage and required raw-file presence only. Not full journal content verification, independent penetration reconstruction, actual final replay row equality or permission for model amendment. Historical post-checkpoint tails counted but not used or deleted.'))
 put(D/'FINISHED.json',dict(time=time.time(),completed=True,passed=passed,automatic_training=False))
except BaseException as e:
 put(D/'FAILURE.json',dict(time=time.time(),error=repr(e),traceback=traceback.format_exc()));raise
