from pathlib import Path
import ast,hashlib,json,socket,subprocess,tarfile,time
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY85_CAUSAL_HISTORY86_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 s=p.read_text().rsplit(')',1)[1].split();return s[19]==str(j['proc_start_ticks']) and s[0]!='Z'
diag=B/'runs/recovery84_causal_history_audit_20261030_v1';assert read(diag/'FINISHED.json')['passed'] and read(diag/'SAVED_REVIEW.json')['passed'];assert read(diag/'PLOT_INSPECTION.json')['actual_image_viewed']
for x in read(diag/'PLAN.json')['source']:assert sha(Path(x['path']))==x['sha256']
watch=B/'runtime/recovery85_completion_watch_20261030_v1';plan=read(watch/'PLAN.json');assert not (watch/'FAILURE.json').exists();states={}
for j in plan['identities']:
 for p in j['failure_paths']:assert not Path(p).exists(),p
 if live(j):states[j['name']]='live'
 else:
  assert j['terminal_requirements'],j['name']
  for r in j['terminal_requirements']:assert read(Path(r['path']))[r['key']]==r['value']
  states[j['name']]='verified_terminal'
observed=[json.loads(l) for l in (watch/'OBSERVATIONS.jsonl').read_text().splitlines()];assert time.time()-observed[-1]['time']<45
for a,b in zip(observed,observed[1:]):
 assert a['time']<b['time']
 for m in ['impedance','admittance','vmc']:assert a['progress'][m]['steps']<=b['progress'][m]['steps']
put(D/'OBSERVATION_SNAPSHOT_REVIEW.json',dict(time=time.time(),passed=True,samples=len(observed),elapsed=observed[-1]['elapsed'],identities=len(states),all_original_live_or_verified_terminal=True,all_saved_rows_checked=True,observer_complete=(watch/'FINISHED.json').exists(),automatic_training=False))
run=B/'runs/parameter_partial75_recovery_cycle85_20261029_v1';progress={m:read(run/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
since=read(B/'runtime/recovery85_prefix86_input_diagnosis_20261030_v1/SAVE_SNAPSHOT.json')['time'];g=Path('/tmp/sii_gpu_util_guard_20261030_v7');samples=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];samples=[s for s in samples if s['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(s)+'\n' for s in samples))
guard=dict(samples=len(samples),minimum=[min(s['gpus'][i]['utilization'] for s in samples) for i in range(4)],below50=[sum(s['gpus'][i]['utilization']<50 for s in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
prep=B/'runtime/prepare_recovery86_20261030_v1';dec=B/'runtime/recovery86_completion_preparation_20261030_v1';run86=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1'
assert not (dec/'DECISION86.json').exists() and not (run86/'LAUNCH.json').exists()
for p in [dec/'PREPARATION_REVIEW.json',B/'runtime/recovery86_followups_20261030_v1/PREPARATION_REVIEW.json']:assert read(p)['passed']
put(D/'PREPARATION_SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),cycle85=progress,states=states,guard=guard,goal='active',actual86_restore_complete=(prep/'FINISHED.json').exists(),actual86_decision=False,actual86_training=False,automatic_training=False,direct34=False))
folders=[D,diag,watch,dec,B/'runtime/recovery86_followups_20261030_v1',prep,B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1']
files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz','.md'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:files.add(run/m/'train/PROGRESS.json')
for n in ['tools/published_compliance_episode_20261025.py','scripts/validate_office_apparatus_v5_20260917.py','tools/spt_rl_reward_20261025.py']:files.add(B/'runtime/source_train17_clock/source'/n)
files.add(B/'runtime/source_train17_clock/SOURCE_HASHES.json')
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_RECOVERY85_PREFIX86_INPUT_DIAGNOSIS_20261030'/n)
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
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='3d3b5caeb50121e58a0fa397ef640d86cfe158a4',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Original shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt);print(json.dumps(receipt));print('GPU',guard);print('steps',{m:x['steps'] for m,x in progress.items()})
