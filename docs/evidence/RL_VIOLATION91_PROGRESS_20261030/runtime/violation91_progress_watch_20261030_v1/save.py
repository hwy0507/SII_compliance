from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle91_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation91_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
TAG='RL_VIOLATION91_PROGRESS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
observed=read(D/'OBSERVATION_REVIEW.json');assert observed['passed'] and read(B/'runtime/violation91_stability_preparation_20261030_v1/INPUT90_REVIEW.json')['passed']
plan=read(S/'PLAN.json');assert sha(S/'audit.py')==plan['source_sha256'] and sha(S/'review_saved.py')==plan['review_source_sha256'] and sha(S/'PLAN.json')==read(B/'runtime/violation91_stability_preparation_20261030_v1/BINDING_PLAN.json')['original_plan_sha256']
assert not (S/'REGISTRATION.json').exists() and not (S/'REVIEW.json').exists()
for j in observed['identities']:
 stat=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert stat[0]!='Z' and stat[19]==j['start']
assert not list(O.glob('*FAILURE*.json')) and not (T/'ARCHIVE_REVIEW_FAILURE.json').exists()
progress={};frozen={}
for m in ['impedance','admittance','vmc']:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
 progress[m]=read(T/m/'train/PROGRESS.json');frozen[m]=read(F/m/'PROGRESS.json')
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if l.endswith('}')];rows=[r for r in rows if r['time']>=read(D/'OBSERVATION_PLAN.json')['time']];assert time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[r['utilization'] for r in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=observed['identities'],training91=progress,frozen90=frozen,gpu=gpu,goal='active',automatic92=False,full_stability_statistics_evaluated=False))
files=set()
for folder in [D,S]:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 files.add(T/m/'train/PROGRESS.json');files.add(F/m/'PROGRESS.json')
for p in [T/'LAUNCH.json',T/'MONITOR_LAUNCH.json',F/'LAUNCH.json',F/'REVIEW_LAUNCH.json',O/'PROCESS.json',O/'PLAN.json']:files.add(p)
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_VIOLATION91_STABILITY_READY_20261030'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Shared SSD verified wait on original105 identities and current progress and live observations. Full statistics not run. Original diff context retained. Large artifacts remain SSD; not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for member in tar.getmembers():assert tar.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='bab8faff155883990b624a008a5b7b1261615ff4',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD, HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 原91训练与冻结90继续：十分钟连续观察

2026-10-30 UTC，Goal active。本轮为verified wait：从/proc实际确认原105身份存活后，连续观察{observed['elapsed_s']:.3f}秒/{observed['samples']}样本，全部身份保持，三路训练步数增加。没有新训练/物理/优化器派发或新的统计实验；原作业持续产生真实进度，不把观察结束当作科学阶段结束。

主机 `{socket.gethostname()}`；共享SSD `{B}`；Python `{B}/env/bin/python`；观察源码和原始记录 `{D}`。实际query/fetch/read main `bab8faff155883990b624a008a5b7b1261615ff4` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无相关科学协议变化；采用sii-research-sync，无子agent。

保存时总steps `{ {m:v['steps'] for m,v in progress.items()} }`，完成训练条件 `{ {m:v['completed_conditions'] for m,v in progress.items()} }`/各30；冻结90完成 `{ {m:v['completed_conditions'] for m,v in frozen.items()} }`/各30。原learner689755/689761/689763、archive689765、冻结evaluator283421/283428/283430、collector283433/postprocessor292743、固定终端等待1706570和guard保持原身份，未重启、未延长预算。

完整91 review/health/loss、固定87全部7813终端/all5/masks的91诊断、冻结90全90/raw/88→90配对/最终全state仍待。90—92输入绑定已准备且实际90含I安全中止检查通过，完整窗口REGISTRATION/REVIEW仍未生成，无92/Direct34派发。前序[稳定性输入绑定交接](RL_VIOLATION91_STABILITY_READY_20261030.md)及[固定终端诊断](RL_VIOLATION91_TERMINAL_FOLLOWUP_20261030.md)继续有效。

GPU原v7继续，科学全部结束后仍保载。本轮{gpu['samples']}样本最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；含合成负载，非科学吞吐/每瞬时保证，非重启自启服务。所有物理/MJB/Task/Strict/filter/执行器/dt5e−5、actor49/canonical48、critic52/历史/Adam/RNG及原训练协议不变。

没有新增收敛结论。91早期I/V尖峰和I actor漂移、90 I全局穿透安全中止及外部bit0局限、A/V旧终端退化、旧失败窗口、partial75、74—76不可判、79中止、半std拒绝和软件失败全部保留。Direct原数值验收和冻结33全30 Task/Strict0/0、旧28最终内存证明缺失保持；指定ESN仍缺，不替用其他模型。

证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，全部tar成员和AST核验；Git index/commit字节及正常push/远端确认后写包外PUBLICATION。大产物共享SSD，HDD仅254字节原位指针，非HDD/arm1全备份。下一步继续监测原91完整结果，审查全部科学证据后再决定有限后续。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 原91与冻结90持续：十分钟verified wait

- [交接](docs/{TAG}.md)。原105身份实际存活并连续{observed['elapsed_s']:.3f}s/{observed['samples']}样本保持，三路steps增长；总steps{ {m:v['steps'] for m,v in progress.items()} }，冻结完成{ {m:v['completed_conditions'] for m,v in frozen.items()} }。原archive/固定终端等待继续，无重启、新训练或预算延长。
- 完整91/loss/health/终端诊断、冻结90全90/raw/paired仍待；90—92绑定准备保持，无完整窗口统计/自动92/Direct34，未收敛。全部旧失败、Direct原结论及指定ESN缺失保持。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针，非全备份。mainbab8faff/baselinef6e8f8c已query/fetch/read，正常发布见收据；Goal active，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()})))
