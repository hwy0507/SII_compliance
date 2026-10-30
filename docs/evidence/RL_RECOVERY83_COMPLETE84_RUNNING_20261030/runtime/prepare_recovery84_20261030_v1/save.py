from pathlib import Path
import ast,hashlib,json,os,socket,subprocess,tarfile,time
B=Path(__file__).resolve().parents[2];R=B/'repository/SII_compliance';D=Path(__file__).parent;TAG='RL_RECOVERY83_PREFIX84_PREPARATION_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG;RUN=B/'runs/parameter_partial75_recovery_cycle83_20261029_v1';F=B/'runs/parameter82_frozen_full30_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==str(j.get('proc_start_ticks',j.get('start'))) and s[0]!='Z'
assert read(D/'OBSERVATION_FINISHED.json')['passed'];assert read(B/'runs/parameter_recovery83_first5000_20261030_v1/SAVED_REVIEW.json')['passed'];assert read(B/'runs/parameter82_frozen_first2_saved_audit_20261030_v1/SAVED_REVIEW.json')['passed']
progress={};frozen={}
for j in read(RUN/'LAUNCH.json')['jobs']:
 assert live(j);p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();progress[j['controller']]=read(p/'PROGRESS.json')
for j in read(F/'LAUNCH.json')['jobs']:
 assert live(j);p=F/j['controller'];assert not (p/'FAILURE.json').exists();frozen[j['controller']]=read(p/'PROGRESS.json')
assert live(read(D/'LAUNCH.json'));assert not (D/'FAILURE.json').exists();assert not (B/'runtime/recovery84_completion_preparation_20261030_v1/DECISION84.json').exists()
identities=[]
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:
 j=dict(pid=pid,proc_start_ticks=start);assert live(j);identities.append(j)
since=read(B/'runtime/recovery82_full_review_20261030_v1/SAVE_SNAPSHOT.json')['time'];samples=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];samples=[s for s in samples if s['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples));guard=dict(identities=identities,samples=len(samples),minimum=[min(s['gpus'][i]['utilization'] for s in samples) for i in range(4)],below50=[sum(s['gpus'][i]['utilization']<50 for s in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle83=progress,frozen82=frozen,guard=guard,goal='active',actual84_restore=(B/'runs/parameter_partial75_recovery_cycle84_20261029_v1/CHECK_ONLY_COMPLETE.json').exists(),actual84_training=False,direct34=False))
folders=[D,B/'runtime/recovery84_completion_preparation_20261030_v1',B/'runtime/recovery84_followups_20261030_v1',B/'runs/parameter_recovery83_first5000_20261030_v1',B/'runs/parameter82_frozen_first2_saved_audit_20261030_v1',B/'runs/parameter_partial75_recovery_cycle84_review_20261029_v1',B/'runs/parameter_recovery84_loss_20261029_v1'];files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 for n in ['REGISTRATION.json','STARTUP_REVIEW.json','PROGRESS.json','RESULTS.json']:
  p=F/m/n
  if p.exists():files.add(p)
 for case in read(F/'PLAN.json')['case_ids'][:2]:files.add(F/m/f'{case}_REVIEW.json')
 files.add(RUN/m/'train/PROGRESS.json')
for p in F.glob('*.json'):files.add(p)
for p in (F/'comparison55_82').glob('*.json'):files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,active_logs_are_snapshots=True))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='538b1f9cb929f10be9dcfcce29fd91c9010077de',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt))
