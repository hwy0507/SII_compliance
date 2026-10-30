from pathlib import Path
import ast,json,time,hashlib,socket,tarfile,subprocess
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY85_PREFIX86_INPUT_DIAGNOSIS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert read(D/'OBSERVATION_FINISHED.json')['passed']
diag=B/'runs/recovery83_84_terminal_behavior_alignment_20261030_v1'
for n in ['REVIEW.json','SAVED_REVIEW.json','UPDATE_AVAILABILITY_REVIEW.json','INPUT_REVIEW.json','INPUT_SAVED_REVIEW.json','GRADIENT_REVIEW.json','GRADIENT_SAVED_REVIEW.json']:assert read(diag/n)['passed']
assert read(diag/'PLOT_INSPECTION.json')['actual_image_viewed'];assert not (diag/'GRADIENT_FAILURE.json').exists()
follow=B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1';assert live(read(follow/'LAUNCH.json')) and not (follow/'FAILURE.json').exists()
prep=B/'runtime/prepare_recovery86_20261030_v1';assert live(read(prep/'LAUNCH.json')) and not (prep/'FAILURE.json').exists();assert not (B/'runs/parameter_partial75_recovery_cycle86_20261029_v1/LAUNCH.json').exists()
states={}
for j in read(D/'OBSERVATION_PLAN.json')['identities']:
 for p in j['failure_paths']:assert not Path(p).exists(),p
 if live(j):states[j['name']]='live'
 else:
  assert j['terminal_requirements'],j['name']
  for r in j['terminal_requirements']:assert read(Path(r['path']))[r['key']]==r['value']
  states[j['name']]='verified_terminal'
states['fixed2514_84_85']='live'
run=B/'runs/parameter_partial75_recovery_cycle85_20261029_v1';progress={m:read(run/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
since=read(B/'runtime/recovery84_full_review_20261030_v1/SAVE_SNAPSHOT.json')['time'];g=Path('/tmp/sii_gpu_util_guard_20261030_v7');samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[s for s in samples if s['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples))
guard=dict(samples=len(samples),minimum=[min(s['gpus'][i]['utilization'] for s in samples) for i in range(4)],below50=[sum(s['gpus'][i]['utilization']<50 for s in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle85=progress,states=states,guard=guard,goal='active',actual86_restore_complete=(prep/'FINISHED.json').exists(),automatic86=False,direct34=False))
folders=[D,diag,follow,prep,B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1',B/'runs/parameter_recovery86_loss_20261029_v1',B/'runs/parameter_recovery85_first5000_20261030_v1']
files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz','.md'} and p.stat().st_size<10_000_000:files.add(p)
for m in ['vmc','admittance']:
 root=B/f'runs/{m}_recovery85_terminal_followup_20261029_v1'
 for n in ['anchor84.npz','ANCHOR_PLAN.json','ANCHOR_REVIEW.json','ANCHOR_SAVED_REVIEW.json','PLAN.json','LAUNCH.json','SOURCE_REVIEW.json']:files.add(root/n)
for p in run.rglob('*'):
 if p.is_file() and '__pycache__' not in p.parts and 'train' not in p.relative_to(run).parts and p.suffix in {'.json','.py','.log','.txt'} and p.stat().st_size<3_000_000:files.add(p)
for m in progress:files.add(run/m/'train/PROGRESS.json');files.add(run/m/'INITIAL_STATE_REVIEW.json');files.add(run/m/'trainer_registered.py')
for n in ['scripts/validate_office_apparatus_v5_20260917.py','tools/published_compliance_learner_20261025.py','tools/spt_rl_reward_20261025.py']:files.add(B/'runtime/source_train17_clock/source'/n)
files.add(B/'runtime/source_train17_clock/SOURCE_HASHES.json');files.add(B/'repository/RL_RECOVERY84_COMPLETE85_RUNNING_20261030/RECEIPT.json');files.add(B/'repository/RL_RECOVERY84_COMPLETE85_RUNNING_20261030/PUBLICATION.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,active_logs_are_snapshots=True,large_checkpoints_replay_raw='Original shared SSD paths; not HDD/arm1 full backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='ab8cbd7b75cfe9c3e16adc4564462c21c695662a',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Original shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt))
