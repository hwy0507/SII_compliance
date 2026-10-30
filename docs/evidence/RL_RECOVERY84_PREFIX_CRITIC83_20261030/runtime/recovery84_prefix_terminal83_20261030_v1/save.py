from pathlib import Path
import json,hashlib,ast,time,tarfile,socket,subprocess
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY84_PREFIX_CRITIC83_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
P=B/'runs/parameter_recovery84_first5000_20261030_v1';C=B/'runs/recovery82_83_old_terminal_population_20261030_v1';W=B/'runs/recovery82_84_fixed_terminal_critic_followup_20261030_v1';RUN=B/'runs/parameter_partial75_recovery_cycle84_20261029_v1'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2);f.write('\n')
def live(j):
 s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();return s[19]==str(j.get('proc_start_ticks',j.get('start'))) and s[0]!='Z'
assert read(D/'OBSERVATION_FINISHED.json')['passed']
for p in [P,C]:assert read(p/'REVIEW.json')['passed'] and read(p/'SAVED_REVIEW.json')['passed'] and read(p/'PLOT_INSPECTION.json')['actual_image_viewed']
identities=read(D/'OBSERVATION_PLAN.json')['identities']+[read(W/'LAUNCH.json')]+[dict(pid=p,proc_start_ticks='570509475') for p in [97399,97400,97401,97402]]
assert all(live(j) for j in identities);assert not (W/'FAILURE.json').exists()
for folder in [RUN,B/'runs/parameter82_frozen_full30_20261030_v1']:
 assert not list(folder.glob('*FAILURE.json')) and not list(folder.glob('*/FAILURE.json')) and not list(folder.glob('*/train/FAILURE.json'))
progress={m:read(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};F=B/'runs/parameter82_frozen_full30_20261030_v1';frozen={m:read(F/m/'PROGRESS.json') for m in progress}
g=Path('/tmp/sii_gpu_util_guard_20261030_v7');since=read(B/'runtime/recovery83_full_review_20261030_v1/SAVE_SNAPSHOT.json')['time'];samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[r for r in samples if r['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in samples));guard=dict(samples=len(samples),minimum=[min(r['gpus'][i]['utilization'] for r in samples) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in samples) for i in range(4)],last=[r['utilization'] for r in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle84=progress,frozen82=frozen,guard=guard,identities=identities,goal='active',direct34=False,training85=False))
files=set()
for folder in [D,P,C,W]:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.jsonl','.png','.txt','.log','.diff','.npz'}:assert p.stat().st_size<10_000_000;files.add(p)
for folder in [C,W]:
 for ref in read(folder/'PLAN.json')['inputs'].values():
  p=Path(ref['path']);assert sha(p)==ref['sha256'];assert p.stat().st_size<10_000_000;files.add(p)
for m in progress:
 files.add(RUN/m/'train/PROGRESS.json');files.add(RUN/m/'INITIAL_STATE_REVIEW.json')
 files.add(F/m/'PROGRESS.json')
for name in ['LAUNCH.json','MONITOR_LAUNCH.json','STARTUP_LAUNCH.json','startup/REVIEW.json']:files.add(RUN/name)
prior=B/'repository/RL_RECOVERY83_COMPLETE84_RUNNING_20261030';files.update([prior/'PUBLICATION.json',prior/'RECEIPT.json'])
E.mkdir();A.mkdir(exist_ok=True);assert not (A/'SMALL_EVIDENCE.tar.gz').exists();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);dest=E/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(dest)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,active_logs_are_snapshots=True,prior_complete83_archive=str(prior/'SMALL_EVIDENCE.tar.gz')))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='00dad983a9d1b29c99a81e8ff02341089684da15',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt))
