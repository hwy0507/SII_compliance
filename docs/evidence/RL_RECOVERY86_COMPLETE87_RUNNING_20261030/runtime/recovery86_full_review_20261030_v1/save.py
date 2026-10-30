from pathlib import Path
import ast,hashlib,json,socket,subprocess,tarfile,time
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY86_COMPLETE87_RUNNING_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG;read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==str(j['proc_start_ticks']) and s[0]!='Z'
run=B/'runs/parameter_partial75_recovery_cycle87_20261029_v1';rev=B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1';fixed=B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1'
assert read(D/'OBSERVATION87_FINISHED.json')['passed'] and read(D/'WATCH_FINISHED.json')['all_full86_and_restore87_ready'];assert read(run/'startup/REVIEW.json')['passed'];assert read(B/'runtime/recovery87_completion_preparation_20261030_v1/DECISION87.json')['passed'];assert read(B/'runtime/recovery87_followups_20261030_v1/FINISHED.json')['passed']
assert read(rev/'FINISHED.json')['completed'] and read(rev/'REVIEW.json')['passed']
for p in [rev/'health/PLOT_INSPECTION.json',B/'runs/parameter_recovery86_loss_20261029_v1/PLOT_INSPECTION.json',fixed/'PLOT_INSPECTION.json']+[B/f'runs/{m}_recovery86_terminal_followup_20261029_v1/PLOT_INSPECTION.json' for m in ['vmc','admittance']]:assert read(p)['actual_image_viewed']
for n in ['NEW86_TERMINAL_CASE_REVIEW.json','UPDATE_AVAILABILITY86_REVIEW.json','PRIOR85_COHORT86_REVIEW.json','PRIOR85_COHORT86_TOTAL_REVIEW.json']:assert read(D/n)['passed']
states={}
for j in read(D/'OBSERVATION87_PLAN.json')['identities']:
 for p in j['failure_paths']:assert not Path(p).exists(),p
 if live(j):states[j['name']]='live'
 else:
  assert j['terminal_requirements'],j['name']
  for rr in j['terminal_requirements']:assert read(Path(rr['path']))[rr['key']]==rr['value']
  states[j['name']]='verified_terminal'
progress={m:read(run/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};fp={m:read(B/f'runs/parameter82_frozen_full30_20261030_v1/{m}/PROGRESS.json') for m in progress}
since=read(B/'runtime/recovery86_history_progress_20261030_v1/SAVE_SNAPSHOT.json')['time'];g=Path('/tmp/sii_gpu_util_guard_20261030_v7');samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[s for s in samples if s['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples));guard=dict(samples=len(samples),minimum=[min(s['gpus'][i]['utilization'] for s in samples) for i in range(4)],below50=[sum(s['gpus'][i]['utilization']<50 for s in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
ff={m:read(B/f'runs/parameter82_frozen_full30_20261030_v1/{m}/FINISHED.json') for m in progress if (B/f'runs/parameter82_frozen_full30_20261030_v1/{m}/FINISHED.json').exists()}
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle87=progress,frozen82=fp,frozen82_finished=ff,states=states,guard=guard,goal='active',automatic88=False,direct34=False))
folders=[D,rev,fixed,B/'runtime/prepare_recovery87_20261030_v1',B/'runtime/recovery87_completion_preparation_20261030_v1',B/'runtime/recovery87_followups_20261030_v1',B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1',B/'runs/parameter_recovery85_87_reward_stability_20261030_v1',B/'runs/recovery85_87_bootstrap_scalar_review_20261030_v1']
for c in [86,87]:
 folders += [B/f'runs/parameter_recovery{c}_loss_20261029_v1',B/f'runs/parameter_recovery{c}_task_labels_20261029_v1',B/f'runs/vmc_recovery{c}_terminal_followup_20261029_v1',B/f'runs/admittance_recovery{c}_terminal_followup_20261029_v1']
files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz','.md'} and p.stat().st_size<10_000_000:files.add(p)
for c in [86,87]:
 root=B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1'
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and 'train' not in p.relative_to(root).parts and p.suffix in {'.json','.py','.log','.txt'} and p.stat().st_size<3_000_000:files.add(p)
 for m in progress:
  for n in ['PROGRESS.json','FINISHED.json','INITIAL_STATE.json']:
   p=root/m/'train'/n
   if p.exists():files.add(p)
for m in progress:files.add(B/f'runs/parameter_partial75_recovery_cycle86_archive_20261029_v1/{m}/cycle_00086.json')
for m in ff:
 for n in ['FINISHED.json','RESULTS.json','EVALUATION.json','REGISTRATION.json','STARTUP_REVIEW.json','CHECK_ONLY_REVIEW.json']:
  p=B/f'runs/parameter82_frozen_full30_20261030_v1/{m}'/n
  if p.exists():files.add(p)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_RECOVERY85_HISTORY86_PROGRESS87_READY_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,active_logs_are_snapshots=True,large_checkpoints_replay_raw='Original shared SSD; not HDD/arm1 full backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='f3a48112e015997eb486d9f0c9ae2026d0219ad0',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Original shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt));print('GPU',guard);print('steps',{m:x['steps'] for m,x in progress.items()})
