from pathlib import Path
import ast,hashlib,json,os,socket,subprocess,tarfile,time
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;TAG='RL_RECOVERY82_COMPLETE83_RUNNING_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
RUN=B/'runs/parameter_partial75_recovery_cycle83_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
assert read(D/'OBSERVATION_FINISHED.json')['passed']
assert read(D/'FROZEN82_OBSERVATION_FINISHED.json')['passed']
assert read(RUN/'startup/REVIEW.json')['passed']
assert read(B/'runtime/recovery83_completion_preparation_20261030_v1/DECISION83.json')['passed']
progress={}
for j in read(RUN/'LAUNCH.json')['jobs']:
 assert live(j);p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();progress[j['controller']]=read(p/'PROGRESS.json')
g=Path('/tmp/sii_gpu_util_guard_20261030_v7');launch=read(g/'LAUNCH.json')
identities=[]
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:
 j=dict(pid=pid,proc_start_ticks=start);assert live(j);identities.append(j)
since=read(B/'runtime/prepare_recovery83_20261030_v1/SAVE_SNAPSHOT.json')['time']
samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[s for s in samples if s['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples))
guard=dict(identities=identities,samples=len(samples),minimum=[min(s['gpus'][i]['utilization'] for s in samples) for i in range(4)],below50=[sum(s['gpus'][i]['utilization']<50 for s in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle83=progress,guard=guard,goal='active',direct34=False,automatic84=False))
folders=[D,B/'runtime/parameter82_frozen_full30_20261030_v1',B/'runs/parameter82_frozen_full30_20261030_v1',B/'runtime/prepare_recovery83_20261030_v1',B/'runtime/recovery83_completion_preparation_20261030_v1',B/'runtime/recovery83_followups_20261030_v1',B/'runtime/recovery82_completion_watch_20261030_v1',B/'runs/parameter_partial75_recovery_cycle82_review_20261029_v1',B/'runs/parameter_recovery82_loss_20261029_v1',B/'runs/parameter_recovery82_task_labels_20261029_v1',B/'runs/vmc_recovery82_terminal_followup_20261029_v1',B/'runs/admittance_recovery82_terminal_followup_20261029_v1',B/'runs/recovery76_81_bootstrap_scalar_review_20261030_v1',B/'runs/recovery82_84_bootstrap_scalar_review_20261030_v1',B/'runs/parameter_recovery82_84_reward_stability_20261030_v1',B/'runs/parameter_recovery83_loss_20261029_v1',B/'runs/parameter_recovery83_task_labels_20261029_v1',B/'runs/vmc_recovery83_terminal_followup_20261029_v1',B/'runs/admittance_recovery83_terminal_followup_20261029_v1']
files=set();large=[]
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts:
   if folder==B/'runs/parameter82_frozen_full30_20261030_v1' and any(x in read(folder/'PLAN.json')['case_ids'] for x in p.relative_to(folder).parts):continue
   if p.name=='sample_indices.npy':large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)));continue
   if p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for cycle in [82,83]:
 root=B/f'runs/parameter_partial75_recovery_cycle{cycle}_20261029_v1'
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and 'train' not in p.relative_to(root).parts and p.suffix in {'.json','.py','.log','.txt'} and p.stat().st_size<3_000_000:files.add(p)
 for m in progress:
  for n in ['PROGRESS.json','INITIAL_STATE.json']:
   p=root/m/'train'/n
   if p.exists():files.add(p)
put(D/'LARGE_DIAGNOSTIC_ASSETS.json',dict(files=large,location='Shared SSD, excluded from Git small evidence; no HDD or arm1 copy claimed'))
files.add(D/'LARGE_DIAGNOSTIC_ASSETS.json');E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,active_logs_are_snapshots=True,large_diagnostic_assets=large))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='034889ab336719db28a3ceb55555b2bd833572d5',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt))
