from pathlib import Path
import json,hashlib,ast,time,os,subprocess,difflib
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;P=B/'runtime/direct33_frozen_operations_20261029_v1';F=B/'runs/serl_take33_frozen_full30_20261029_v1';O=B/'runs/serl_take33_frozen_remaining2_20261030_v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def put(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2)+'\n')
s=(P/'compare.py').read_text();v=s.replace("O=B/'runs/serl_take33_frozen_full30_20261029_v1'","O=B/'runs/serl_take33_frozen_remaining2_20261030_v2'")
v=v.replace("read(O/'REGISTRATION.json')","read(B/'runs/serl_take33_frozen_full30_20261029_v1/REGISTRATION.json')")
needle=" assert report['checkpoint_sha256']==reg['inputs']['checkpoint']['sha256'] and report['formal_state_unchanged'] and report['optimizer_updates']==report['replay_writes']==0"
replacement=""" assert report['checkpoint_sha256']==reg['inputs']['checkpoint']['sha256'] and report['optimizer_updates']==report['replay_writes']==0
 if cy==29:assert report['formal_state_unchanged']
 else:
  assert report['formal_state_unchanged'] is False and report['original_final_inmemory_state_unavailable'] is True
  assert report['all28_original_saved_actions_reproduced_exactly'] and report['new2_full_state_unchanged'] and report['original_completed']==28 and report['recovered_completed']==2
  replay_ref=report['action_replay'];assert sha(replay_ref['path'])==replay_ref['sha256'];rp=read(replay_ref['path']);assert rp['passed'] and rp['all_saved_actions_exact'] and rp['replay_learner_state_unchanged'] and len(rp['episodes'])==28
  assert len({x['case'] for x in rp['episodes']})==28 and all(x['maximum_error']==0 for x in rp['episodes'])"""
assert v.count(needle)==1;v=v.replace(needle,replacement)
v=v.replace("final_spt_reference=None,","original33_final_inmemory_state_unavailable=True,formal33_state_unchanged=False,recovered33_action_provenance_verified=True,additional_interrupted_prefix_actions=new['additional_interrupted_prefix_actions'],final_spt_reference=None,")
ast.parse(v);script=D/'compare_recovered.py';script.write_text(v);(D/'compare_recovered.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),v.splitlines(True))))
s=(P/'wait_compare.py').read_text();v=s.replace('serl_take33_frozen_full30_20261029_v1','serl_take33_frozen_remaining2_20261030_v2').replace("D/'compare.py'","D/'compare_recovered.py'").replace("O/'REVIEW_LAUNCH.json'","O/'COMBINED_REVIEW_LAUNCH.json'").replace("O/'REVIEW_FAILURE.json'","O/'COMBINED_REVIEW_FAILURE.json'").replace("j['proc_start_ticks']","j['start']")
ast.parse(v);wait=D/'wait_compare_recovered.py';wait.write_text(v)
plan=json.loads((F/'COMPARISON_PLAN.json').read_text());plan.update(time=time.time(),source_sha256=sha(script),waiter_sha256=sha(wait));plan['inputs']['recovered_plan']=ref(O/'PLAN.json');plan['inputs']['combined_review_plan']=ref(O/'COMBINED_REVIEW_PLAN.json');plan['limitation']+=' Recovery33 includes28 original completed and2 repeated incomplete cases, plus separately retained interrupted prefixes. Original33 final in-memory invariant is unavailable. Independent action replay28 and full invariant new2 provide documented action provenance, not the lost original invariant. This is a descriptive training-cohort comparison only.'
put(O/'COMPARISON_PLAN.json',plan)
# Actual missing review must fail before any paired result is produced.
r=subprocess.run([str(B/'env/bin/python'),str(script)],capture_output=True,text=True);assert r.returncode!=0 and 'FileNotFoundError' in r.stderr and not (O/'PAIRED29_33.json').exists();put(O/'COMPARISON_INCOMPLETE_REJECTION.json',dict(passed=True,returncode=r.returncode,stderr=r.stderr,new_physics=0,new_updates=0))
with (O/'compare.log').open('x') as f:p=subprocess.Popen([str(B/'env/bin/python'),str(wait)],stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'))
put(O/'COMPARISON_LAUNCH.json',dict(pid=p.pid,start=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),source=ref(wait)))
print('Recovered comparison waiter',p.pid)
