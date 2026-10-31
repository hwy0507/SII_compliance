from pathlib import Path
import json,hashlib,ast,time,socket,os,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';O=B/'runs/violation93_gradient_diagnosis_20261031_v1';Q=B/'runs/violation93_frozen_batch_diagnosis_20261031_v1';QD=B/'runtime/violation93_batch_diagnosis_20261031_v1';TAG='RL_VIOLATION93_DIAGNOSIS_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
for folder,names in [(O,['REVIEW.json','NEIGHBOR_REVIEW.json','SAVED_REVIEW.json','FINISHED.json']),(Q,['FINISHED.json','SAVED_REVIEW.json','SPIKE_SOURCE_REVIEW.json'])]:
 for n in names:assert rd(folder/n)['passed']
 assert not list(folder.glob('*FAILURE*'));pi=rd(folder/'PLOT_INSPECTION.json');assert pi['actual_visual_inspection']
 for p in pi['plots']:assert p['inspected'] and sha(p['path'])==p['sha256']
for j in [rd(O/'PROCESS.json')]+rd(Q/'LAUNCH.json')['jobs']:
 p=Path('/proc',str(j['pid']),'stat')
 if p.exists():
  s=p.read_text().rsplit(')',1)[1].split();assert s[0]=='Z' or s[19]!=j['start']
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:
 s=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==start
G=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True);put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,all_new_diagnostics_finished=True,automatic94=False,goal='active'))
files=set()
for folder in [D,O,QD,Q]:
 for p in folder.rglob('*'):
  if p.is_file() and 'raw' not in p.relative_to(folder).parts and p.suffix in {'.py','.json','.jsonl','.npz','.png','.diff','.md'}:files.add(p)
for item in rd(Q/'SPIKE_SOURCE_REVIEW.json')['sources']:
 p=Path(item['path'])
 if p.name!='transitions.jsonl':files.add(p)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_COMPLETE93_20261031'/n)
for folder in [B/'runs/parameter_violation_cycle93_review_20261031_v1',B/'runtime/violation93_finish_watch_20261031_v1']:
 for n in ['REVIEW.json','TERMINAL_DECOMPOSITION.json','ADJACENT92_93_REVIEW.json']:
  if (folder/n).exists():files.add(folder/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed92 terminal gradients at full92/full93, all-row neighbors, all3 full93 native64 batch arithmetic and new placement-failure binding. Raw192 NPZ remain SSD with manifests; no optimizer/physics updates.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for p in tar.getmembers():assert tar.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],raw_storage=rd(D/'RAW_STORAGE_REVIEW.json'),backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
footer=f'''

## 来源和保存

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，应用仓库sii-research-sync。源码 `{D}`、`{QD}`；诊断 `{O}`、`{Q}`；父仍为原完整92/93归档，源/配置/checkpoint hash及预算见PLAN/PROCESS/LAUNCH。诊断正常退出且逐PID/start核验。

GPU原guard科学完成后继续，{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%。含synthetic guard、非纯科研吞吐或每瞬时保证，非重启服务。

SSD `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员/AST核验。manifest `docs/evidence/{TAG}/MANIFEST.json`，提交字节和实际正常push收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。raw192仅SSD并逐hash核验。HDD配额满，仅现有LATEST254字节原地更新回读，非HDD/arm1全备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
'''
(R/'docs'/(TAG+'.md')).write_text((D/'REPORT_BODY.md').read_text()+footer)
entry=(D/'ENTRY.md').read_text()+f'''\n- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，raw192共363377306字节单独SSD；HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，发布见收据，Goal active。\n\n'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu)))
