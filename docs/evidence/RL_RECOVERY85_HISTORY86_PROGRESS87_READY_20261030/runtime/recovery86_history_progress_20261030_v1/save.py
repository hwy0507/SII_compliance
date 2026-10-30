from pathlib import Path
import ast,hashlib,json,socket,subprocess,tarfile,time
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY85_HISTORY86_PROGRESS87_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==str(j['proc_start_ticks']) and s[0]!='Z'
history=B/'runs/recovery85_history_reconstruction_20261030_v1';inventory=B/'runs/recovery85_history_lineage_inventory_20261030_v1'
for folder in [history,inventory]:
 for n in ['REVIEW.json','SAVED_REVIEW.json','FINISHED.json']:assert read(folder/n)['passed']
assert read(history/'PLOT_INSPECTION.json')['actual_image_viewed'];assert read(D/'FINISHED.json')['passed'];assert read(D/'HISTORY_REVIEW_FINISHED.json')['passed']
prep=B/'runtime/prepare_recovery87_20261030_v1';dec=B/'runtime/recovery87_completion_preparation_20261030_v1';follow=B/'runtime/recovery87_followups_20261030_v1'
for p in [prep/'FINAL_SOURCE_REVIEW.json',prep/'HEALTH_DEPENDENCY_IMPORT_REVIEW.json',dec/'PREPARATION_REVIEW.json',follow/'PREPARATION_REVIEW.json']:assert read(p)['passed']
assert not (dec/'DECISION87.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle87_20261029_v1/LAUNCH.json').exists()
states={}
for j in read(D/'PLAN.json')['identities']:
 for p in j['failure_paths']:assert not Path(p).exists(),p
 if live(j):states[j['name']]='live'
 else:
  assert j['terminal_requirements'],j['name']
  for r in j['terminal_requirements']:assert read(Path(r['path']))[r['key']]==r['value']
  states[j['name']]='verified_terminal'
run=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1';progress={m:read(run/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};frozen=B/'runs/parameter82_frozen_full30_20261030_v1';fp={m:read(frozen/m/'PROGRESS.json') for m in progress}
since=read(B/'runtime/recovery85_full_review_20261030_v1/SAVE_SNAPSHOT.json')['time'];g=Path('/tmp/sii_gpu_util_guard_20261030_v7');samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[s for s in samples if s['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples));guard=dict(samples=len(samples),minimum=[min(s['gpus'][i]['utilization'] for s in samples) for i in range(4)],below50=[sum(s['gpus'][i]['utilization']<50 for s in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle86=progress,frozen82=fp,states=states,guard=guard,goal='active',actual87_restore_complete=(prep/'FINISHED.json').exists(),actual87_training=False,automatic_training=False,direct34=False))
folders=[D,history,inventory,prep,dec,follow,B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1',B/'runs/parameter_recovery87_loss_20261029_v1']
files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.md'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 files.add(run/m/'train/PROGRESS.json');files.add(frozen/m/'PROGRESS.json')
for n in ['PLAN.json','LAUNCH.json']:
 for folder in ['runs/parameter_recovery85_87_reward_stability_20261030_v1','runs/recovery85_87_bootstrap_scalar_review_20261030_v1','runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1']:
  p=B/folder/n
  if p.exists():files.add(p)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_RECOVERY85_COMPLETE86_RUNNING_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
large=[m['sidecar'] for m in read(history/'REVIEW.json')['methods'].values()]
for r in large:assert sha(Path(r['path']))==r['sha256'] and Path(r['path']).stat().st_size==r['bytes']
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,large_history_sidecars=large,active_logs_are_snapshots=True,large_checkpoints_replay_raw='Original shared SSD; not HDD/arm1 full backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,large_history_sidecars=large,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='2679effbd6ae4f5bb2fb215d70692a7b1e4ce775',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Original shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt));print('GPU',guard);print('steps',{m:x['steps'] for m,x in progress.items()})
