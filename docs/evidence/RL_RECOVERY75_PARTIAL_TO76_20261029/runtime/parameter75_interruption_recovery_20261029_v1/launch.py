from pathlib import Path
import os,json,time,hashlib,ast,subprocess,importlib.util,copy
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';AUD=B/'runs/parameter75_interruption_recovery_20261029_v1';W=B/'runs/parameter_recovery76_78_reward_stability_20261029_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
assert not (R/'LAUNCH.json').exists();assert read(AUD/'REVIEW.json')['passed'] and read(R/'CHECK_ONLY_COMPLETE.json')['passed']
old=read(B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json')
for v in old['evidence'].values():assert sha(v['path'])==v['sha256']
assert read(W/'PLAN.json')['cycles']==[76,77,78] and not read(D/'ORIGINAL_WINDOW_INTERRUPTED.json')['assessable']
assert sha(B/'runs/parameter_capacity74_76_reward_stability_20261029_v1/PLAN.json')=='d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703'
spec=importlib.util.spec_from_file_location('recovery',D/'resume_partial75.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
evidence=dict(partial_review=ref(AUD/'REVIEW.json'),previous_decision75=ref(B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json'),original_window_interrupted=ref(D/'ORIGINAL_WINDOW_INTERRUPTED.json'),prospective_recovery_window=ref(W/'PLAN.json'),full_review_source=ref(B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1/SOURCE_REVIEW.json'))
registration_hashes={}
for m in ['impedance','admittance','vmc']:
 p=read(R/m/'REGISTRATION.json');st=p['interrupted_episode_recovery'];v=read(R/m/'CHECK_ONLY_REVIEW.json');assert v['passed'] and v['negative_rejections']==9 and v['full_learner_state_exact'] and v['full_replay_and_next65536_exact']
 assert v['checkpoint_sha256']==st['checkpoint']['sha256'] and sha(st['checkpoint']['path'])==v['checkpoint_sha256']
 assert st['driver_sha256']==sha(D/'resume_partial75.py')
 module.validate_protocol(st['parent_registration']['sha256'],p,sha(R/m/'REGISTRATION.json'))
 original=Path(st['trainer_path']).read_text();modified=module.transform(original)
 # Remove exactly the three declared metadata/initial-state additions, requiring identical scientific trainer source.
 restored=modified.replace("\n        _verify_initial_state(learner, replay, checkpoint, out.parent)",'').replace("            interruption_recovery=protocol['interrupted_episode_recovery'],\n",'').replace("\n        interruption_recovery=protocol['interrupted_episode_recovery'],",'');assert restored==original
 assert not (R/m/'train').exists();registration_hashes[m]=sha(R/m/'REGISTRATION.json');evidence[m+'_checkonly']=ref(R/m/'CHECK_ONLY_REVIEW.json');evidence[m+'_protocol']=ref(R/m/'REGISTRATION.json')
for p in D.glob('*.py'):ast.parse(p.read_text())
write(D/'SOURCE_REVIEW.json',dict(time=time.time(),passed=True,driver_sha256=sha(D/'resume_partial75.py'),original_scientific_trainer_inverse_exact=True,metadata_and_initial_state_only_source_changes=3,validation_exception_explicit_partial75=True,full_restore_and_nine_negative_checks_per_method=True,original_historical_markers_and_hyperparameters_retained=True,new_physics_cycles=1,automatic_followup=False));evidence['source_review']=ref(D/'SOURCE_REVIEW.json')
reason='Container replaced and all prior scientific handles lost without FINISHED75. Preserve all audited partial75 learned state and every replay row; no resetting/rollback or fabricated full75. Three methods retain23000/24000/24000 updates beyond complete74, all raw reward/action/observation mappings and finite optimizer logs verified. Exact fullstate and next65536 restore passed with9 negative recovery/scientific contract checks each. New76 is one additional full30-condition physical cycle from reset environments, frozen objective/physics/gates/batch65536/UTD1/terminal128/4m markers unchanged. Original74-76 explicitly unavailable due incomplete75; prospective76-78 registered before launch with unchanged5percent/nearzero1/seed/bootstrap/anchor55; all old failed windows retained. No automatic77, no Direct34, no convergence claim.'
write(D/'DECISION_RECOVERY76.json',dict(time=time.time(),passed=True,parent_cycle=75,parent_partial=True,new_cycle=76,new_cycles=1,convergence_claim=False,evidence=evidence,reason=reason,automatic_followup=False))
write(R/'PRELAUNCH_REVIEW.json',dict(passed=True,time=time.time(),registration_hashes=registration_hashes,decision=ref(D/'DECISION_RECOVERY76.json'),source_review=ref(D/'SOURCE_REVIEW.json'),new_cycles=1,automatic_followup=False))
env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1');jobs=read(R/'COMMANDS.json')['jobs']
for j in jobs:
 m=j['controller'];f=(R/(m+'_driver.log')).open('x');p=subprocess.Popen(j['command'],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True);f.close();j.update(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time())
write(R/'LAUNCH.json',dict(time=time.time(),jobs=jobs,new_cycles=1,automatic_followup=False))
for name,script in [('MONITOR',D/'archive76.py'),('STARTUP',R/'startup_review.py')]:
 if name=='STARTUP':script.write_bytes((D/'startup76.py').read_bytes())
 f=(R/(name.lower()+'.log')).open('x');p=subprocess.Popen([str(B/'env/bin/python'),str(script)],stdout=f,stderr=subprocess.STDOUT,env=env,start_new_session=True);f.close();write(R/(name+'_LAUNCH.json'),dict(pid=p.pid,proc_start_ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19],time=time.time(),script_sha256=sha(script)))
print(json.dumps({'jobs':[{k:j[k] for k in ['controller','pid','proc_start_ticks']} for j in jobs],'monitor':read(R/'MONITOR_LAUNCH.json'),'startup':read(R/'STARTUP_LAUNCH.json')},indent=2))
