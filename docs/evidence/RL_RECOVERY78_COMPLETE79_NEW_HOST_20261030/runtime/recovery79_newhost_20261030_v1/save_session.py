from pathlib import Path
import json,hashlib,ast,tarfile,time,socket,subprocess,datetime,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;P=B/'runs/parameter_partial75_recovery_cycle79_20261029_v1';O=B/'runs/serl_take33_frozen_remaining2_20261030_v2';TAG='RL_RECOVERY78_COMPLETE79_NEW_HOST_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,j):
 with p.open('x') as f:f.write(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==j.get('proc_start_ticks',j.get('start')) and s[0]!='Z'
assert read(P/'startup/REVIEW.json')['passed'];assert read(D/'CONTINUATION_OBSERVATION_FINISHED.json')['passed']
assert read(B/'runtime/recovery79_followups_20261030_v1/DEPLOYMENT_REVIEW.json')['passed']
snap=dict(time=time.time(),host=socket.gethostname(),goal='active',direct34=False,automatic80=False,parameter79={},direct33={},guard={})
for j in read(P/'LAUNCH.json')['jobs']:
 m=j['controller'];assert live(j) or (P/m/'train/FINISHED.json').exists();assert not (P/m/'train/FAILURE.json').exists();snap['parameter79'][m]=dict(pid=j['pid'],start=j['proc_start_ticks'],progress=read(P/m/'train/PROGRESS.json'))
for j in read(O/'LAUNCH.json')['jobs']:
 p=Path(j['output']);assert live(j) or (p/'POLICY_UNCHANGED.json').exists();assert not (p/'FAILURE.json').exists();snap['direct33'][p.name]=dict(pid=j['pid'],start=j['start'],finished=(p/'POLICY_UNCHANGED.json').exists(),progress={f.parent.name:read(f) for f in p.glob('*/rollout.progress.json')})
for n in ['REVIEW.json','PAIRED29_33.json','PAIRED_SAVED_REVIEW.json']:
 p=B/'runs/serl_take33_frozen_combined_review_20261030_v3'/n;snap['direct33'][n]=dict(path=str(p),sha256=sha(p),passed=read(p)['passed']) if p.exists() else None
for label in ['20261029_v6','20261030_v7']:
 g=Path('/tmp/sii_gpu_util_guard_'+label);data=(g/'samples.jsonl').read_bytes();rows=list(map(json.loads,data.splitlines()));first=next(i for i,x in enumerate(rows) if min(y['utilization'] for y in x['gpus'])>=50);post=rows[first:]
 snap['guard'][label]=dict(samples=len(rows),first_all50_index=first,first_all50_seconds=rows[first]['time']-rows[0]['time'],all_min=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],post_warmup_min=[min(x['gpus'][i]['utilization'] for x in post) for i in range(4)],post_warmup_below50=[sum(x['gpus'][i]['utilization']<50 for x in post) for i in range(4)],last=rows[-1],synthetic_included=True)
 folder=D/('guard_'+label);folder.mkdir(exist_ok=False)
 for p in g.iterdir():
  if p.is_file() and p.suffix in ['.py','.json','.log']:(folder/p.name).write_bytes(p.read_bytes())
 (folder/'samples.jsonl').write_bytes(data)
 if label.endswith('v7'):
  assert time.time()-rows[-1]['time']<20
  jobs=read(g/'LAUNCH.json');identities=[]
  for pid in [jobs['pid']]+list(jobs['workers'].values()):
   s=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z';identities.append(dict(pid=pid,start=s[19],cpu_affinity=sorted(os.sched_getaffinity(pid))))
  snap['guard'][label]['live_identities']=identities
put(D/'SAVE_SNAPSHOT.json',snap)
roots=[B/'runs/serl_take33_frozen_combined_review_20261030_v3',D,B/'runtime/recovery79_followups_20261030_v1',B/'runtime/recovery79_prefix_audit_20261030_v1',B/'runtime/direct33_interruption_recovery_20261030_v1',B/'runtime/gpu_guard_affinity_20261029_v1',B/'runtime/recovery79_completion_preparation_20261029_v1',B/'runtime/prepare_recovery79_20261029_v1']
for name in ['parameter_partial75_recovery_cycle78_review_20261029_v1','parameter_partial75_recovery_cycle78_archive_20261029_v1','parameter_recovery78_loss_20261029_v1','parameter_recovery78_task_labels_20261029_v1','vmc_recovery78_terminal_followup_20261029_v1','admittance_recovery78_terminal_followup_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1','parameter_partial75_recovery_cycle79_20261029_v1','parameter_partial75_recovery_cycle79_review_20261029_v1','parameter_recovery79_loss_20261029_v1','parameter_recovery79_task_labels_20261029_v1','vmc_recovery79_terminal_followup_20261029_v1','admittance_recovery79_terminal_followup_20261029_v1','parameter_recovery79_81_reward_stability_20261030_v1','parameter_recovery79_first5000_20261029_v1','serl_take33_frozen_remaining2_20261030_v1','serl_take33_frozen_remaining2_20261030_v2']:roots.append(B/'runs'/name)
sources=set();excluded=[]
for root in roots:
 assert root.exists(),str(root)
 for p in root.rglob('*'):
  if not p.is_file() or p.is_symlink() or '__pycache__' in p.parts:continue
  if p.suffix not in ['.py','.json','.jsonl','.log','.diff','.txt','.png','.npz','.md','.csv']:continue
  if p.name in ['transitions.jsonl','optimizer.jsonl','actor_intervals.jsonl']:continue
  if p.stat().st_size>=8_000_000:excluded.append(dict(path=str(p),bytes=p.stat().st_size));continue
  sources.add(p)
# Original interrupted episode evidence: source metadata and hashes in PLAN; raw/journals stay SSD.
f=B/'runs/serl_take33_frozen_full30_20261029_v1'
for p in f.glob('*.json'):sources.add(p)
for p in f.glob('shard*/*.json'):sources.add(p)
E.mkdir(exist_ok=False);A.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,time=time.time(),excluded_large=excluded,large_checkpoints_and_raw_remain_shared_ssd=True,active_files_are_snapshots=True))
tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 members=t.getmembers();assert len(members)==len(manifest)+1
 for x in members:assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,manifest_entries=len(manifest),all_member_bytes_and_python_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),remote_main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(),remote_baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=R,text=True).strip(),host=snap['host'],large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
print(json.dumps(receipt));print(json.dumps(snap))
