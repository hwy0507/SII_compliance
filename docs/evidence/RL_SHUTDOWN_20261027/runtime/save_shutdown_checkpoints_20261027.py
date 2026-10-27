from pathlib import Path
import json,hashlib,time,os,shutil
import torch,numpy as np
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');O=B/'runs/user_shutdown_pause_20261027_v1';os.sched_setaffinity(0,{52});torch.set_num_threads(1)
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def copy(source,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 with source.open('rb') as a,target.open('xb') as z:shutil.copyfileobj(a,z,1024*1024);z.flush();os.fsync(z.fileno())
 assert sha(source)==sha(target)
 return target
items=[dict(method='direct',role='preferred_preinterrupt_partial25',path=O/'direct/checkpoint_before_interrupt.pt',source=B/'runs/serl_capacity_batch65536_cycle25_20261027_v1/direct/checkpoint_latest.pt',source_note='Source path was atomically replaced after interruption; copied preinterrupt hash is authoritative.')]
source=B/'runs/serl_capacity_batch65536_cycle24_archive_20261027_v1/direct/cycle_00024.pt';items.append(dict(method='direct',role='full24_fallback',path=copy(source,O/'direct/last_complete_cycle24.pt'),source=source))
for m in ['impedance','admittance','vmc']:
 for c,role in [(41,'preferred_complete41'),(40,'full40_fallback')]:
  source=B/f'runs/parameter_capacity_pool30_cycle{c}_archive_20261026_v1/{m}/cycle_{c:05d}.pt';items.append(dict(method=m,role=role,path=copy(source,O/m/f'complete_cycle{c}.pt'),source=source))
rows=[]
for item in items:
 p=item['path'];ck=torch.load(p,map_location='cpu',weights_only=False);replay=ck['replay'];arr=replay['arrays'];assert replay['size']==ck['steps']==replay['cursor'];assert replay['capacity']==2000000
 assert all(np.isfinite(v).all() and len(v)==ck['steps'] for v in arr.values());assert 'replay_capacity_extension' in replay
 learner=ck['learner'];row={k:str(v) if isinstance(v,Path) else v for k,v in item.items()};row.update(bytes=p.stat().st_size,sha256=sha(p),cycle=ck['cycle'],steps=ck['steps'],boundary=ck['boundary'],seed=ck['seed'],protocol_sha256=ck['protocol_sha256'],root_fields=list(ck),learner_fields=list(learner),replay_capacity=replay['capacity'],replay_size=replay['size'],replay_marker=replay['replay_capacity_extension'],raw_replay_finite=True,history_entries=len(ck['cycles']),environment_state_saved=ck.get('environment_state_saved'),optimizer_state_preserved_in_serialized_learner=True,verification='File hash, torch deserialization, metadata and raw replay finite/length checks; not a new GPU restore or physics test.')
 if item['method']=='direct':
  extra=replay['multistep_target_extension'];row['derived_fields']=list(extra);row['mature_rows']=len(extra['ready']);row['pending_stream_lengths']={str(k):len(v) for k,v in extra['pending'].items()};row['multistep_marker']=extra['marker']
  row['learner_counters']={k:v for k,v in learner.items() if isinstance(v,(int,float,str,bool))}
 else:
  row['terminal_weight']=learner['terminal_loss_weight'];row['target_pair_reduction']=learner['target_pair_reduction'];row['learner_counters']={k:v for k,v in learner.items() if isinstance(v,(int,float,str,bool))}
 rows.append(row);del ck,replay,arr,learner
manifest=dict(time=time.time(),goal_status='paused',snapshots=rows,primary_direct_resume='Preferred partial25 must retain full learner/replay/RNG/history; requires a separately reviewed interrupted-stream resume adapter. Existing complete-cycle continuation must not be used unchanged. Full24 fallback is retained, not automatic rollback.',parameter_resume='Use complete41 with capacity replay plus pair learner, full state and historical entry23;42 was not launched.',scope='Independent snapshot copies on shared SSD. Does not claim full HDD/arm1 checkpoint backup.')
(O/'RECOVERY_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps([{k:r.get(k) for k in ['method','role','cycle','steps','boundary','sha256','mature_rows','pending_stream_lengths','learner_counters']} for r in rows],indent=2))
