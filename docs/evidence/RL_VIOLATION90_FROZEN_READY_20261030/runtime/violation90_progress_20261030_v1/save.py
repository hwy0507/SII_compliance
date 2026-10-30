from pathlib import Path
import json,time,os,socket,hashlib,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];P=B/'runtime/violation90_frozen_preparation_20261030_v1';R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle90_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';N=B/'runs/parameter90_violation_frozen_full30_20261030_v1';TAG='RL_VIOLATION90_FROZEN_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
updated=read(P/'UPDATED_FROZEN_REVIEW.json');observed=read(D/'OBSERVATION_REVIEW.json');prefix=read(D/'prefix5000/REVIEW.json')
assert updated['passed'] and observed['passed'] and prefix['passed'] and read(D/'prefix5000/PLOT_INSPECTION.json')['actual_visual_inspection'];assert read(P/'FINAL_REGISTRATION_GATE_REVIEW.json')['passed']
for pid,start in observed['original_identities'].items():
 f=Path('/proc',pid,'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==start
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists()
for m in updated['methods']:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
progress={m:read(T/m/'train/PROGRESS.json') for m in updated['methods']};frozen={m:read(F/m/'PROGRESS.json') for m in updated['methods']};rows=[]
for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines():
 try:x=json.loads(line)
 except json.JSONDecodeError:continue
 if x['time']>=read(P/'PREFLIGHT_PLAN.json')['time']:rows.append(x)
assert time.time()-rows[-1]['time']<25 and not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists();(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress90=progress,frozen88=frozen,original_identities=observed['original_identities'],goal='active',frozen90_physics=False,automatic91=False))
files=set()
for directory in [D,P,N]:
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.log','.diff','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 for n in ['EXECUTION.json','PROGRESS.json']:files.add(T/m/'train'/n)
 for n in ['PROGRESS.json','RESULTS.json']:files.add(F/m/n)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json']:files.add(T/n)
for n in ['LAUNCH.json','REVIEW_LAUNCH.json']:files.add(F/n)
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_VIOLATION90_ONLINE_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Learned90 frozen software interface and first5000 loss diagnostics. Actual snapshots remain original shared SSD; no new physical frozen90 performance result.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='cb2631f0afc589a0b38e752471632e15ba74ce16',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; HDD existing254-byte pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 已更新90违规位冻结接口通过；首5000 loss检查

2026-10-30 UTC，Goal active。上一轮[有限90实际启动](RL_VIOLATION90_ONLINE_20261030.md)是progress。本轮核验真实更新后的52维模型能否完整恢复、保持RNG并执行冻结评测接口；原90训练和原88冻结继续，没有重启、加训练预算或自动91/Direct34。使用sii-research-sync，无子agent。

主机 `{socket.gethostname()}`；共享SSD `{B}`；解释器 `{B}/env/bin/python`。开工及发布前实际query/fetch/read main `cb2631f0afc589a0b38e752471632e15ba74ce16`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未发现新相关科学协议变化。

## 真实已学违规位的冻结接口

源 `{P}`；预登记 `{N}/PRE_REGISTRATION.json`。读取原90启动时保存的准确快照：I新增1000、A1000、V2000；不是完整90 checkpoint。逐SHA绑定原startup报告及训练登记，恢复全部learner/Adam/alpha/RNG和全4m容量replay。两架构marker和23/47历史容量marker保持；原51历史已学状态不重置。

`evaluate_violation90.py`从原88完整评测器适配为52维，保留原物理/filter/torque/reward审计、0更新、30条件和外部随机种子；新增history与bit双绑定、实际90 continuation与步数/维度检查。完整90恢复入口真实拒绝当前partial90；不调用只允许原完整89元数据的迁移准备validator。正式物理入口还要求单独的LAUNCH_AUTHORIZATION绑定三路最终registration SHA，目前不存在，未派发。

实际三份更新后快照各执行同原89 short0600的1375条记录输入，连续native和每动作外部RNG切换的全部观测/raw/mixed/context精确相同，terminal clock/history/raw bit精确。实际bit0/1计数 `{ {m:[v['raw_bit_zero_count'],v['raw_bit_one_count']] for m,v in updated['methods'].items()} }`，覆盖真实阈值切换。全1375 actor49隔离检查通过；全部learner、replay、全局/局部RNG与原checkpoint hash不变。每方法10个已学bit online/target列、5个在线Adam一/二阶矩非零，所有native动作总8271，耗时{updated['elapsed_s']:.3f}秒；0新物理/0更新/0回放写入。这里只证明软件接口，记录输入来自89，不能当新90闭环结果。

预登记未来完整90三方法×全部30条件、原seed2026102638、最多123750动作/99000000物理子步/0更新。无需开发成功才能比较，所有失败保留；最终派发必须先有完整90 archive、full review、health、完整loss及实际图检查，再执行真正完整父check-only和单独launch。`register_complete90.py`对当前缺完整结果真实拒绝，三个最终registration尚未创建。原冻结88仍按原截止继续，新90评测未占用它的物理CPU。

## 固定前5000次更新的实际loss

源 `{D}/prefix90.py`，结果 `{D}/prefix5000`。三方法都取原始optimizer日志前5000个完整行，选择规则先登记；保存原字节、NPZ并独立标量复算全部统计，源prefix回读精确，六栏PNG已实际查看。critic首1000→末1000均值：

- I：{prefix['methods']['impedance']['stats']['agent_train/q_loss']['first1000']:.6f}→{prefix['methods']['impedance']['stats']['agent_train/q_loss']['last1000']:.6f}，最大{prefix['methods']['impedance']['stats']['agent_train/q_loss']['maximum']:.6f}；尾均值略升，3000与4500附近有抬升，尖峰保留。
- A：{prefix['methods']['admittance']['stats']['agent_train/q_loss']['first1000']:.6f}→{prefix['methods']['admittance']['stats']['agent_train/q_loss']['last1000']:.6f}，最大{prefix['methods']['admittance']['stats']['agent_train/q_loss']['maximum']:.6f}；早期尖峰保留。
- V：{prefix['methods']['vmc']['stats']['agent_train/q_loss']['first1000']:.6f}→{prefix['methods']['vmc']['stats']['agent_train/q_loss']['last1000']:.6f}，最大{prefix['methods']['vmc']['stats']['agent_train/q_loss']['maximum']:.6f}；局部尖峰保留。

全部记录值有限，但I actor loss仍有上漂，不能从actor loss正负或A/V早期下降推出任务成功/健康收敛。旧完整89尾段仅单列作上下文，51→52架构边界不能混合做同修订稳定统计；原88—90 A/V失败、I窗口不完整及其他历史失败不变。完整90 reward、loss与90—92新窗口尚未完成。

## 原进程、GPU与接续

训练 `{T}`，三原PID1096445/1096447/1096449及archive1096452保持。新检查期间{observed['elapsed_s']:.3f}秒/{observed['samples']}样本/{observed['identity_count']}个原训练/90sampler/冻结88/guard身份保持，三路steps均增加。保存时 `{ {m:v['steps'] for m,v in progress.items()} }`；仍是部分90。

原冻结88 `{F}`，保存已完成条件 `{ {m:v['completed_conditions'] for m,v in frozen.items()} }`，全90回合、最后全state不变、raw复算及82→88配对仍待；保留原21600s截止，不因观察窗口结束而重启。Direct33已接受数值阶段但冻结Task/Strict0/0，Direct28最终内存证明缺失仍披露；指定ESN缺失不替代，partial75/74—76不可判/79安全abort/所有失败窗口与halfstd拒绝均保留。

原v7 GPU守护继续；用户要求科研全部完成后仍保载，阈值50%/目标70%，不创建STOP。本轮{gpu['samples']}采样最低{gpu['minimum']}%，低于50样本{gpu['below50']}，末值{gpu['last']}%；含合成守护，不代表科研吞吐或每瞬时保证，旧预热及历史低谷保留。守护不等于重启服务。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，tar全部成员和Python AST已核；Git index/commit逐字核验、正常push和实际远端确认另记包外PUBLICATION。大快照/轨迹仍共享SSD，HDD仅原位254字节指针，非HDD/arm1全备份。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 已学90违规位冻结接口通过；首5000 loss保留尖峰

- [交接](docs/{TAG}.md)。实际partial90三份全learner/replay恢复、双marker/非零bit及Adam、1375 native与外部RNG精确重放/terminal bit/actor49隔离通过，8271记录动作、0新physics/update。完整90冻结全90预登记及缺前置真实拒绝，最终恢复/评测仍待；不把partial当complete。
- 三路固定前5000原字节/保存标量/实际六栏图通过。critic首末I1.990384→2.029705、A1.367704→1.220512、V1.013427→.812925；I尖峰34.85与actor漂移保留，非收敛。原90/88冻结继续，{observed['elapsed_s']:.3f}秒/{observed['identity_count']}身份保持，总steps{ {m:v['steps'] for m,v in progress.items()} }。
- GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载；冻结88完成数{ {m:v['completed_conditions'] for m,v in frozen.items()} }，最终全90/raw/paired待。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份。maincb2631f0/baselinef6e8f8c已query/fetch/read，发布见收据；Goal active，无自动91/Direct34，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,progress90={m:v['steps'] for m,v in progress.items()},frozen88={m:v['completed_conditions'] for m,v in frozen.items()})))
