from pathlib import Path
import json,time,subprocess,socket,hashlib
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';A=B/'repository/RL_VIOLATION92_PROGRESS_20261030'
read=lambda p:json.loads(p.read_text())
def git(*args):return subprocess.check_output(['git',*args],cwd=R).decode()
commit=git('rev-parse','HEAD').strip();remote=git('ls-remote','--heads','origin','refs/heads/main','refs/heads/baseline');assert commit+'\trefs/heads/main' in remote and read(D/'REMOTE_START.json')['baseline']+'\trefs/heads/baseline' in remote
assert not git('status','--porcelain');assert read(A/'GIT_BYTES_REVIEW.json')['commit']==commit
ids=[]
for j in read(D/'OBSERVATION_REVIEW.json')['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start'];ids.append(dict(**j,state=s[0]))
T=B/'runs/parameter_violation_cycle92_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
training={m:read(T/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};frozen={m:read(F/m/'PROGRESS.json') for m in training}
assert all(training[m]['steps']>read(D/'SAVE_SNAPSHOT.json')['training92'][m]['steps'] for m in training)
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(O.glob('WAIT_FAILURE_*.json'))
assert not (S/'REGISTRATION.json').exists() and not (S/'REVIEW.json').exists()
for m in training:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
rows=[json.loads(x) for x in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if x.endswith('}')];latest=rows[-1];assert time.time()-latest['time']<25
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert pointer.stat().st_size==254 and b'RL_VIOLATION92_PROGRESS_20261030.md' in pointer.read_bytes()
record=dict(time=time.time(),host=socket.gethostname(),commit=commit,normal_push=True,actual_remote_heads=remote,remote_verified=True,clean_worktree=True,identities=ids,training92=training,frozen90=frozen,terminal_waiter=read(O/'PROCESS.json'),full92_terminal_predictions_pending=True,stability_registration_pending=True,original_early_failure_preserved=True,gpu_last=latest,synthetic_guard_included=True,guard_continues_after_science=True,archive=read(A/'RECEIPT.json'),pointer_bytes=254,pointer_sha256=hashlib.sha256(pointer.read_bytes()).hexdigest(),goal='active',automatic93=False)
with (A/'PUBLICATION.json').open('x') as f:json.dump(record,f,indent=2);f.write('\n')
print(json.dumps(dict(commit=commit,steps={m:x['steps'] for m,x in training.items()},frozen={m:x['completed_conditions'] for m,x in frozen.items()},gpu=latest,identities=len(ids))))
