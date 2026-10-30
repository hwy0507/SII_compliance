from pathlib import Path
import ast,hashlib,json,socket,subprocess,tarfile,time
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY85_COMPLETE86_RUNNING_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
run=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1';rev=B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1'
assert read(D/'OBSERVATION_FINISHED.json')['passed'];assert read(run/'startup/REVIEW.json')['passed'];assert read(B/'runtime/recovery86_completion_preparation_20261030_v1/DECISION86.json')['passed'];assert read(B/'runtime/recovery86_followups_20261030_v1/FINISHED.json')['passed']
assert read(rev/'FINISHED.json')['completed'] and read(rev/'REVIEW.json')['passed']
for p in [rev/'health/PLOT_INSPECTION.json',B/'runs/parameter_recovery85_loss_20261029_v1/PLOT_INSPECTION.json',D/'FIXED_INPUT85_PLOT_INSPECTION.json']+[B/f'runs/{m}_recovery85_terminal_followup_20261029_v1/PLOT_INSPECTION.json' for m in ['vmc','admittance']]:assert read(p)['actual_image_viewed']
states={}
for j in read(D/'OBSERVATION_PLAN.json')['identities']:
 for p in j['failure_paths']:assert not Path(p).exists(),p
 if live(j):states[j['name']]='live'
 else:
  assert j['terminal_requirements'],j['name']
  for r in j['terminal_requirements']:assert read(Path(r['path']))[r['key']]==r['value']
  states[j['name']]='verified_terminal'
progress={m:read(run/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for j in read(run/'LAUNCH.json')['jobs']:assert live(j)
frozen=B/'runs/parameter82_frozen_full30_20261030_v1';fp={m:read(frozen/m/'PROGRESS.json') for m in progress}
since=read(D/'PREPARATION_SAVE_SNAPSHOT.json')['time'];g=Path('/tmp/sii_gpu_util_guard_20261030_v7');samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[s for s in samples if s['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'FULL85_GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples))
guard=dict(samples=len(samples),minimum=[min(s['gpus'][i]['utilization'] for s in samples) for i in range(4)],below50=[sum(s['gpus'][i]['utilization']<50 for s in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle86=progress,states=states,frozen82=fp,guard=guard,goal='active',automatic87=False,direct34=False))
folders=[D,rev,B/'runs/parameter_recovery85_loss_20261029_v1',B/'runs/parameter_recovery85_task_labels_20261029_v1',B/'runs/vmc_recovery85_terminal_followup_20261029_v1',B/'runs/admittance_recovery85_terminal_followup_20261029_v1',B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1',B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1',B/'runtime/recovery85_completion_watch_20261030_v1',B/'runtime/prepare_recovery86_20261030_v1',B/'runtime/recovery86_completion_preparation_20261030_v1',B/'runtime/recovery86_followups_20261030_v1',B/'runs/parameter_partial75_recovery_cycle86_review_20261029_v1',B/'runs/parameter_recovery86_loss_20261029_v1',B/'runs/parameter_recovery86_task_labels_20261029_v1',B/'runs/vmc_recovery86_terminal_followup_20261029_v1',B/'runs/admittance_recovery86_terminal_followup_20261029_v1',B/'runs/parameter_recovery85_87_reward_stability_20261030_v1',B/'runs/recovery85_87_bootstrap_scalar_review_20261030_v1']
files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz','.md'} and p.stat().st_size<10_000_000:files.add(p)
for cycle in [85,86]:
 root=B/f'runs/parameter_partial75_recovery_cycle{cycle}_20261029_v1'
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and 'train' not in p.relative_to(root).parts and p.suffix in {'.json','.py','.log','.txt'} and p.stat().st_size<3_000_000:files.add(p)
 for m in progress:
  for n in ['PROGRESS.json','FINISHED.json','INITIAL_STATE.json']:
   p=root/m/'train'/n
   if p.exists():files.add(p)
for m in progress:files.add(B/f'runs/parameter_partial75_recovery_cycle85_archive_20261029_v1/{m}/cycle_00085.json')
for tag in ['RL_RECOVERY85_CAUSAL_HISTORY86_READY_20261030','RL_RECOVERY85_PREFIX86_INPUT_DIAGNOSIS_20261030']:
 for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository'/tag/n)
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
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='74b2d54efbfd2bdc6ac39ea6fcc6048766ec26e1',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Original shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt));print('GPU',guard);print('steps',{m:x['steps'] for m,x in progress.items()})
