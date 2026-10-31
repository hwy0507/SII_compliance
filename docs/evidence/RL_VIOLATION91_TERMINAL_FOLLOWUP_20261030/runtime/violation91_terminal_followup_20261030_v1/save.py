from pathlib import Path
import json,time,os,socket,hashlib,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];P=D;R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle91_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';N=B/'runs/violation91_fixed87_terminal_followup_20261030_v1';TAG='RL_VIOLATION91_TERMINAL_FOLLOWUP_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
updated=read(N/'PREFLIGHT_REVIEW.json');observed=read(D/'OBSERVATION_REVIEW.json');assert updated['passed'] and observed['passed'] and read(N/'VALIDATOR_REVIEW.json')['passed']
assert not (N/'FINISHED.json').exists() and not list(N.glob('WAIT_FAILURE_*.json'))
for name,h in read(N/'PLAN.json')['source_hashes'].items():assert sha(D/name)==h
for j in observed['identities']:
 f=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==j['start']
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists()
for m in updated['methods']:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
progress={m:read(T/m/'train/PROGRESS.json') for m in updated['methods']};frozen={m:read(F/m/'PROGRESS.json') for m in updated['methods']};rows=[]
for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines():
 try:x=json.loads(line)
 except json.JSONDecodeError:continue
 if x['time']>=read(N/'PLAN.json')['time']:rows.append(x)
assert time.time()-rows[-1]['time']<25 and not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists();(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress91=progress,frozen90=frozen,identities=observed['identities'],goal='active',fixed87_complete91_predictions=False,automatic92=False))
files=set()
for directory in [D,P,N]:
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.log','.diff','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 for n in ['EXECUTION.json','PROGRESS.json']:files.add(T/m/'train'/n)
 for n in ['PROGRESS.json']:files.add(F/m/n)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json']:files.add(T/n)
for n in ['LAUNCH.json','REVIEW_LAUNCH.json']:files.add(F/n)
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_VIOLATION91_PREFIX_20261030'/n)
files.add(B/'runs/violation90_fixed87_terminal_followup_20261030_v1/REVIEW.json')
files.add(B/'runs/violation90_fixed87_terminal_followup_20261030_v1/PLOT_INSPECTION.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed original87 terminal followup preregistration for complete91, saved87/88/89/90 arithmetic and raw-bit inputs checked. No full91 predictions yet; original scientific jobs continue.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='6a0ff6876927768cd6c16df193489677238aed6a',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; HDD existing254-byte pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 原91继续；固定87全部终端跟踪91已登记

2026-10-30 UTC，Goal active。前序[91固定前5000审查](RL_VIOLATION91_PREFIX_20261030.md)。本轮在原91运行期间登记完整91后的固定旧终端诊断；没有新训练阶段或物理派发，无自动92/Direct34。完整91 reward和loss健康仍待。

主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。实际query/fetch/read main `6a0ff6876927768cd6c16df193489677238aed6a` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关科学协议变化。采用sii-research-sync，无子agent。源码 `{D}`，诊断run `{N}`。

固定原87全部7813终端（I2605/A2604/V2604）、all5 critic和原masks；87/88/89/90全部预测及inputs来自已审90跟踪NPZ。全部masked SSE/MSE、all-row SSE和分母精确复算，52维输入逐位绑定原51特征与raw preaction >.0002m位，bit分布 `{ {m:x['bit_counts'] for m,x in updated['methods'].items()} }`。没有新增forward/physics/update，真实缺完整91入口拒绝通过。全部改善和退化保留，不挑表现较好的critic或终端。

原evaluate_violation90只允许90，因此新增本诊断专用validate_architecture91/validate_recovery91，不修改原冻结90 evaluator。准确parent steps取完整90已审记录，I3729700/A3732500/V3733500；继承bit/history原修订floor90/88，双marker、learner/replay52、seed/controller/registration、4m cursor/size、continuation和partial75排除保持。以实际不可变startup91三份checkpoint核验：architecture均通过，完整边界均拒绝，27项错误周期/seed/协议/controller/旧89步数/cursor/capacity/marker/next51负例均拒绝。该检查没有构造未来完整91证据、没有网络forward或训练。

首check91.py在第一路写报告时出现JSON字符串路径.read_text的AttributeError，原源码、PLAN及失败说明保留；check91_v2.py只把读取参数转Path，三路重新完成。原科学作业未重启。LAUNCH_REVIEW绑定实际v2源码hash及VALIDATOR_REVIEW，原PLAN所有source hash仍一致。

唯一等待器PID `{read(N/'PROCESS.json')['pid']}`、start `{read(N/'PROCESS.json')['start']}` 已启动，核验原archive689765身份；沿用原91 launch+14400s截止Unix `{read(N/'PLAN.json')['wait_deadline_unix']}`，不延长训练/归档预算。完整91 REVIEW/FINISHED/health/loss全部到齐且同checkpoint后，才读取准确归档cycle_00091.pt做all5原终端预测，检查learner/replay/RNG/checkpoint不变、独立复算并出六栏图；分析预算1800s，最终实际图检查仍需人工执行。当前没有91终端预测结果。

这是固定已见旧终端拟合/保留诊断，不是策略安全或泛化/收敛门槛；原90 I改善83.45%、A退化9.70%、V退化146.79%的masked SSE证据不覆盖。91新终端由原全回放health诊断负责。完整90 I long0000全局穿透安全中止与外部bit0局限、原失败窗口、partial75、74—76不可判、79安全中止、半std拒绝和所有软件失败保留。Direct原数值验收与冻结33全30 Task/Strict0/0及旧28最终内存证明缺失保持；指定ESN仍缺，不替用其他模型。

原91训练/采样/归档、原冻结90/evaluator/collector/postprocessor、guard及新唯一等待器经过{observed['elapsed_s']:.3f}s/{observed['samples']}样本/{len(observed['identities'])}身份检查，三路steps增加。保存steps `{ {m:x['steps'] for m,x in progress.items()} }`，冻结90完成 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`/各30。完整91和冻结90全90/raw/88→90配对及最终内存不变仍待。

GPU原97370/97399–97402继续，科学结束仍保载；{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；含合成负载、非科研吞吐或每瞬时保证，非重启自启服务。原物理/MJB/Task/Strict/filter/执行器/dt5e−5、actor49/canonical48、52输入/历史/Adam/RNG、4m/terminal128/batch65536/UTD1/原LR/reward/masks保持。

证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，逐成员及源码AST核验；Git index/commit逐字和正常push/远端确认后写包外PUBLICATION。大产物共享SSD，HDD仅254字节指针，非HDD/arm1全备份。接续保持现有原91与冻结90，完整91后审查loss/health/固定终端和任务标签，再决定后续有限阶段。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 原91继续；固定87终端跟踪91已登记

- [交接](docs/{TAG}.md)。原7813终端/all5/原masks，87—90保存算术及52 raw输入精确；真实缺完整91拒绝。专用91边界按实际90 steps，三份startup架构/partial拒绝和27负例通过；check91路径类型错误原件保留，v2仅Path转换修复，无新forward/physics/update。
- 唯一等待器{read(N/'PROCESS.json')['pid']}沿原archive截止；原91/冻结90继续，{observed['elapsed_s']:.3f}s/{len(observed['identities'])}身份保持，总steps{ {m:x['steps'] for m,x in progress.items()} }。完整91/新终端诊断及冻结90全90/raw/paired待，未收敛、无自动92/Direct34。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍守护；冻结完成{ {m:x['completed_conditions'] for m,x in frozen.items()} }。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份。main6a0ff687/baselinef6e8f8c已query/fetch/read，发布见收据；Goal active，无子agent，全部失败保持。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()},frozen={m:v['completed_conditions'] for m,v in frozen.items()})))
