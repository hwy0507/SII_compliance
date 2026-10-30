"""Contract, frozen gate, and actual full health-entrypoint software fixtures."""
from pathlib import Path
import os,sys,json,time,copy,gc,subprocess,traceback,ast
D=Path(__file__).parent;B=D.parents[1];I=B/'runtime/history87_critic_interface_20261030_v1';R=B/'runs/parameter_history_cycle88_20261030_v1';F=D/'health_fixture';F.mkdir();(F/'archive').mkdir();(F/'view').mkdir();os.sched_setaffinity(0,{53})
sys.path[:0]=[str(D),str(B/'runtime/source_train17_clock/source/tools')]
import numpy as np
import torch
from driver import read,sha,put,validate_protocol,validate_parent,transform
from history_consumers import restore_learner
from frozen_helpers import gate
from evaluate_history88 import validate_recovery
from validate_published_finite_check_20261025 import digest
start=time.monotonic();torch.set_num_threads(1);results={}
def reject(fn,label,items):
 try:fn()
 except (AssertionError,ValueError,KeyError,RuntimeError) as e:items.append(dict(case=label,error=str(e)))
 else:raise AssertionError('Accepted invalid '+label)
try:
 for n,h in read(D/'SOURCES.json')['files'].items():assert sha(D/n)==h
 for m in ['impedance','admittance','vmc']:
  p=read(R/m/'REGISTRATION.json');st=p['post_interruption_continuation'];validate_protocol(st['parent_registration']['sha256'],p);ck=torch.load(st['checkpoint']['path'],map_location='cpu',weights_only=False);validate_parent(ck,p);rejected=[]
  for key,val in [('learner_batch_size',256),('learner_updates_per_transition',2),('critic_clock',False),('physics_dt_s',.0001)]:
   bad=copy.deepcopy(p);bad[key]=val;reject(lambda:validate_protocol(ck['protocol_sha256'],bad),key,rejected)
  for key,val in [('parent_cycle',86),('new_cycle',89),('new_cycles',2),('maximum_new_actions',82500),('automatic_followup',True),('optimizer_settings_changed',True),('old_window_continuity_claim',True),('environment_state_saved',True)]:
   bad=copy.deepcopy(p);bad['post_interruption_continuation'][key]=val;reject(lambda:validate_protocol(ck['protocol_sha256'],bad),key,rejected)
  for key,val in [('critic_replay_dimension',50),('actor_information_dimension',50),('weights_from_offline_fit',True),('target_entropy_changed',True)]:
   bad=copy.deepcopy(p);bad['history_critic_amendment'][key]=val;reject(lambda:validate_protocol(ck['protocol_sha256'],bad),key,rejected)
  for key,val in [('cycle',86),('boundary','partial_episode_valid_replay_reset_environment_on_resume'),('environment_state_saved',True),('seed',1),('steps',ck['steps']-1)]:
   bad=dict(ck);bad[key]=val;reject(lambda:validate_parent(bad,p),'parent_'+key,rejected)
  reject(lambda:validate_recovery(ck,p,88),'actual87 rejected as frozen88',rejected)
  # Metadata-only positive fixture does not create or promote a cycle88 result.
  metadata=dict(ck,cycle=88,cycles=ck['cycles']+[dict(cycle=88)],recovery_continuation=p['post_interruption_continuation']);validate_recovery(metadata,p,88)
  state=torch.load(I/(m+'_migrated_learner.pt'),map_location='cpu',weights_only=False);learner=restore_learner(state,p['history_critic_amendment']['binding'],B/'runtime/source_train17_clock','cuda:0');initial=digest(learner.state_dict());case={'impedance':'active_short_train_0600','admittance':'active_short_train_0900','vmc':'active_short_train_0000'}[m];journal=B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train/cycle_00087/{case}/actor_intervals.jsonl'
  with journal.open() as f:rows=[json.loads(next(f)) for _ in range(3)]
  tested=gate(learner,ck,rows,2026102638,case,digest);assert tested['passed'] and digest(learner.state_dict())==initial
  source=Path(st['trainer_path']).read_text();changed=transform(source);a=ast.parse(source);b=ast.parse(changed)
  getlaunch=lambda tree:next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='launch')
  assert ast.dump(getlaunch(a),include_attributes=False)==ast.dump(getlaunch(b),include_attributes=False)
  # Complete87 interface-only checkpoint drives the *actual* health script;
  # this is explicitly a software fixture at cycle87, not formal history88.
  migration=torch.load(B/f'runs/history87_interface_snapshots_20261030_v1/{m}.pt',map_location='cpu',weights_only=False);fixture=dict(ck,learner=migration['learner'],replay=migration['replay'],protocol_sha256=sha(R/m/'REGISTRATION.json'),software_interface_fixture=True,history_critic_amendment=p['history_critic_amendment'])
  folder=F/m;folder.mkdir();(folder/'train').mkdir();(F/'archive'/m).mkdir();(folder/'REGISTRATION.json').write_bytes((R/m/'REGISTRATION.json').read_bytes());(F/'view'/m).symlink_to(folder/'train')
  for name in ['optimizer.jsonl','episodes.jsonl','transitions.jsonl']:(folder/'train'/name).symlink_to(B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train/{name}')
  execution=read(B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train/EXECUTION.json');execution.update(protocol_sha256=sha(folder/'REGISTRATION.json'),software_interface_fixture=True);put(folder/'train/EXECUTION.json',execution)
  torch.save(fixture,F/'archive'/m/'cycle_00087.pt')
  result=dict(passed=True,negative_rejections=rejected,native_frozen_gate=tested,actual_formal87_rejected_as88=True,metadata_only_positive_fixture=True,physics_launch_ast_unchanged=True,health_fixture_cycle=87,health_fixture_not_formal_training=True)
  results[m]=result;put(D/(m+'_CONTRACT_REVIEW.json'),result);print('CONTRACT',m,len(rejected),flush=True);del ck,state,learner,migration,fixture,metadata;gc.collect();torch.cuda.empty_cache()
 env=dict(os.environ,PYTHONPATH=str(D)+':'+str(B/'runtime/source_train17_clock/source/tools'),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
 subprocess.run([str(B/'env/bin/python'),str(D/'health88.py'),'--runtime',str(B/'runtime/source_train17_clock'),'--run',str(F/'view'),'--output',str(F/'health'),'--cycle-archive',str(F/'archive'),'--cycle','87'],check=True,env=env)
 report=read(F/'health/DIAGNOSIS.json');old=read(B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1/health/DIAGNOSIS.json')
 for m in results:
  r=report['methods'][m];assert r['network_state_unchanged'] and r['terminal_count']==old['methods'][m]['terminal_count']
  for key in ['terminal_reward','terminal_q_predictions','terminal_q_absolute_error','terminal_q_in_bag_absolute_error','terminal_q_out_of_bag_absolute_error']:assert r[key]==old['methods'][m][key],(m,key)
 put(D/'INTEGRATION_REVIEW.json',dict(passed=True,time=time.time(),elapsed_s=time.monotonic()-start,methods=results,actual_health_script_all3_passed=True,all_terminal_health_metrics_exact_to87=True,source_hashes=read(D/'SOURCES.json'),new_physics=0,optimizer_updates=0,health_fixture_not_formal88=True))
except BaseException as e:put(D/'INTEGRATION_FAILURE.json',dict(error=repr(e),traceback=traceback.format_exc()));raise
