from pathlib import Path
import json,hashlib,ast,difflib,time,os,subprocess
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;OLD=B/'runtime/serl_take33_frozen_full30_20261029_v1';RT=D/'replay_runtime';RT.mkdir(exist_ok=False);F=B/'runs/serl_take33_frozen_full30_20261029_v1';O=B/'runs/serl_take33_frozen_remaining2_20261030_v1'
for p in OLD.iterdir():
 if p.name=='__pycache__':continue
 (RT/p.name).symlink_to(p)
s=(OLD/'evaluate_serl33_frozen_20261029.py').read_text();needle="    if args.check_only:\n        assert digest(replay.state_dict()) == replay_digest";assert s.count(needle)==1
insert="""    if args.check_only:
        # Independent saved-action replay; no physical simulator or optimizer call.
        from replay_saved28 import verify
        verify(learner, output, case_action_seed, seeded_action, digest)
        assert digest(replay.state_dict()) == replay_digest"""
v=s.replace(needle,insert);ast.parse(v);(RT/'evaluate_replay28.py').write_text(v);(D/'evaluate_replay28.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True))))
helper='''from pathlib import Path
import json,hashlib,time,numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');F=B/'runs/serl_take33_frozen_full30_20261029_v1';O=B/'runs/serl_take33_frozen_remaining2_20261030_v1'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def verify(learner,output,case_seed,sample,digest):
 plan=json.loads((O/'PLAN.json').read_text());before=digest(learner.state_dict());rows=[]
 for shard in plan['original_shards']:
  folder=Path(shard['original_job']['output']);ref=shard['results'];assert sha(Path(ref['path']))==ref['sha256'];results=json.loads(Path(ref['path']).read_text())
  for episode in results['episodes']:
   case=episode['condition'];p=folder/case/'actor_intervals.jsonl';h=sha(p);journal=[json.loads(l) for l in p.read_text().splitlines()];assert len(journal)==episode['actions']
   key=learner.jax.random.PRNGKey(case_seed(2026102626,case));learner.reset_episode();maxerr=0.
   for i,row in enumerate(journal):
    action,key=sample(learner,row['observation'],i,key,'independent');saved=np.asarray(row['action'],np.float32);np.testing.assert_array_equal(action,saved);maxerr=max(maxerr,float(np.max(np.abs(action-saved))));assert row['action']==row['executed_action']
   assert sha(p)==h and digest(learner.state_dict())==before
   rows.append(dict(case=case,actions=len(journal),maximum_error=maxerr,journal_path=str(p),journal_sha256=h))
   (output/'REPLAY_PROGRESS.json').write_text(json.dumps(dict(time=time.time(),completed=len(rows),rows=rows),indent=2)+'\\n')
 assert len(rows)==28 and len({r['case'] for r in rows})==28
 (output/'SAVED28_ACTION_REPLAY.json').write_text(json.dumps(dict(passed=True,time=time.time(),episodes=rows,total_actions=sum(r['actions'] for r in rows),all_saved_actions_exact=True,replay_learner_state_unchanged=digest(learner.state_dict())==before,new_physics=0,new_updates=0,limitation='All original28 saved observation/action pairs reproduced exactly by pinned33 and original per-case RNG. Does not reconstruct unavailable final memory of interrupted original evaluator; original final invariant receipt remains missing.'),indent=2)+'\\n')
'''
ast.parse(helper);(RT/'replay_saved28.py').write_text(helper)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(D/'REPLAY_SOURCE_REVIEW.json').write_text(json.dumps(dict(passed=True,time=time.time(),original_evaluator_sha256=sha(OLD/'evaluate_serl33_frozen_20261029.py'),derived_evaluator_sha256=sha(RT/'evaluate_replay28.py'),helper_sha256=sha(RT/'replay_saved28.py'),only_inserted_check_only_saved_replay=True,original_physics_loop_unchanged=True,new_physics=0,new_updates=0),indent=2)+'\n')
cmd=json.loads((O/'COMMANDS.json').read_text())['jobs'][0]['command'];cmd=list(cmd);cmd[1]=str(RT/'evaluate_replay28.py');cmd[cmd.index('--output')+1]=str(O/'saved28_replay');cmd+=['--check-only']
with (O/'saved28_replay.log').open('x') as f:p=subprocess.Popen(cmd,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',XLA_PYTHON_CLIENT_PREALLOCATE='false'))
(O/'REPLAY_LAUNCH.json').write_text(json.dumps(dict(pid=p.pid,start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),command=cmd),indent=2)+'\n');print('saved28 replay launched',p.pid)
