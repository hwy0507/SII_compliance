from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle92_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
TAG='RL_VIOLATION92_STABILITY_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
observed=read(D/'OBSERVATION_REVIEW.json');assert observed['passed'] and read(D/'INPUT90_91_READY_REVIEW.json')['passed']
assert read(D/'PLOT_BINDING_GUARD_REVIEW.json')['passed']
plan=read(S/'PLAN.json');assert sha(S/'audit.py')==plan['source_sha256'] and sha(S/'review_saved.py')==plan['review_source_sha256'] and sha(S/'PLAN.json')==read(D/'BINDING_PLAN.json')['original_plan_sha256']
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
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=observed['identities'],training92=progress,frozen90=frozen,gpu=gpu,goal='active',automatic93=False,full_stability_statistics_evaluated=False))
files=set()
for folder in [D,S]:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 files.add(T/m/'train/PROGRESS.json');files.add(F/m/'PROGRESS.json')
for p in [T/'LAUNCH.json',T/'MONITOR_LAUNCH.json',F/'LAUNCH.json',F/'REVIEW_LAUNCH.json',O/'PROCESS.json',O/'PLAN.json']:files.add(p)
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_VIOLATION92_DIAGNOSTICS_20261030'/name)
files.add(B/'runtime/build_violation92_stability_binding_20261030.py')
files.add(B/'runtime/violation91_completion_20261030_v1/COMPLETE91_BINDING_REVIEW.json')
for group in read(D/'INPUT90_91_READY_REVIEW.json')['inputs90_91'].values():
 for item in group.values():
  p=Path(item['path'])
  if p.suffix in {'.json','.png'} and p.stat().st_size<10_000_000:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Original90-92 complete90/91 input groups preserved with additional exact inspected figure/loss/plan/early-failure hashes;16 malformed metadata refusals and actual missing92 rejection. Ten-minute verified original process wait. Original numerical statistics not run or changed; large artifacts remain SSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for member in tar.getmembers():assert tar.extractfile(member).read()==(E/member.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD, HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)

steps={m:v['steps'] for m,v in progress.items()};counts={m:v['completed_conditions'] for m,v in frozen.items()}
text=f"""# 第92轮继续：原90—92稳定性完整输入与实际图绑定准备

本轮补齐原稳定性分析的图与 loss 收据来源绑定，原数值统计未运行、未改变。Goal active，三路第92轮训练及原冻结90继续；尚不能宣称 reward 平稳且 loss 健康。

实际主机 `{socket.gethostname()}`，共享SSD根 `{B}`。本轮按 `skills/sii-research-sync/SKILL.md` 实际 query/fetch/read main `{remote['main']}` 与 baseline `{remote['baseline']}`；两个分支没有新增科学协议。无子agent。

## 已完成的输入检查

最终来源 `{D}/bind_inputs.py` 与 `BINDING_PLAN.json`、原来源 diff 一同保存。实际完整90/91共六组的 protocol/review/health/finished/episodes/optimizer 引用与已发布 COMPLETE91_BINDING_REVIEW 完全一致；每组追加准确 loss_plot、health_plot、loss_review、plot_inspection、window_plan、early_window_failure 六个 hash 引用。必须存在当轮两张实际图、逐图已查看记录及正确 SHA，loss 汇总中的图 SHA 也必须一致；后续原 audit/review_saved 会检查全部输入引用。

`INPUT90_91_READY_REVIEW.json` 通过，真实缺完整92被拒绝。`PLOT_BINDING_GUARD_REVIEW.json` 的16个错误元数据案例全部被拒绝，覆盖未查看、空/缺/重复图、单图未查看、错SHA、loss汇总错SHA及错轮次。来源自身与原早期失败 hash 被锁定。builder仅是生成中间来源，最终源及diff为权威版本，含执行前追加的来源/早期失败锁。

原 `{S}/PLAN.json`、audit.py、review_saved.py 字节未变：90/91/92，seed2026102861，5000 bootstrap，nearzero1，相邻5%。原90→91 I42.5116001%、A20.8292134%已违反必要条件，`EARLY_WINDOW_FAILURE_91.json` 保留；V .0964836%仅一个相邻对。不得因等待完整92而抹掉失败。REGISTRATION/REVIEW仍未生成，无完整窗口统计。原 review_saved 独立复算标量，不独立重算 bootstrap 区间，此限制保持。

## 运行与GPU实测

原105进程身份连续保持 {observed['elapsed_s']:.3f}秒、{observed['samples']}次观测，三路steps均增长。保存时 steps `{steps}`；冻结90完成数 `{counts}`，每方法总30。原92 learner463617/463619/463621、archive463623；固定87终端等待器1234380；冻结90 evaluator283421/283428/283430、collector283433、postprocessor292743继续，不重启、不延长原截止。训练全92/health/loss与固定7813终端92比较、冻结全90/raw/88→90 paired及内存不变证明仍待。

GPU {gpu['samples']}样本，四卡最低 `{gpu['minimum']}`%，低于50计数 `{gpu['below50']}`，末样本 `{gpu['last']}`%。包括原synthetic guard的占用，不是纯科研吞吐，也不是每瞬时保证。原 `/tmp/sii_gpu_util_guard_20261030_v7` supervisor97370与四worker97399–97402继续，threshold50/target70/min duty.7；按用户要求科研完成也继续保活，不写STOP。不是重启服务。原warmup0及v6历史31/33/44低利用率记录保持。

## 后续明确入口

仅当完整92 REVIEW、FINISHED、health、loss已经完成并实际查看两张图、记录准确 PLOT_INSPECTION 后执行：

```bash
{B}/env/bin/python {D}/bind_inputs.py --cycle92-run {T} --cycle92-review {B}/runs/parameter_violation_cycle92_review_20261030_v1
{B}/env/bin/python {S}/audit.py --root {S}
{B}/env/bin/python {S}/review_saved.py
```

随后实际查看生成统计图并保存检查结果。不得将这个准备文档当完整窗口验收；绑定脚本不会自动训练或运行统计。没有新训练派发或自动93/Direct34。

第92轮首5000的I密集critic尖峰、actor上移及V约2000尖峰簇仍保留，非健康收敛。原完整91混合结果与所有失败窗口、partial75、不可评74–76、79/90安全中止、halfstd拒绝及软件失败均保留。Direct33原数值收敛验收保持，冻结全30 Task/Strict0/0；旧28缺最终内存证明，恢复2完整不变。不能额外用task成功替代数值目标。指定ESN仍缺，不替换他机模型。

科学协议保持：冻结物理/MJB/dt5e−5/Task与Strict gate/canonical48/filter/执行器限制；每方法30×55秒、最多41250新增、append-only4m replay与23/47标记、terminal128/batch65536/UTD1及原LR/reward/masks。critic/replay52、actor49、clock49/history50/raw bit51；学习过的history/violation、Adam/RNG及双架构标记保持，不提升离线拟合权重。

## 保存与恢复

SSD小证据包 `{archive}`：{receipt['members']}成员、{receipt['bytes']}字节、SHA256 `{receipt['sha256']}`，所有tar成员逐字核验，Python AST通过。清单位于 `docs/evidence/{TAG}/MANIFEST.json`；发布后commit、index与blob逐字检查及实际远端核验记录在 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。

HDD配额满，仅原地更新现有 `sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md`，严格254字节并回读；大checkpoint/raw/replay/runtime仍在共享SSD，不是HDD或arm1全量备份。主要恢复依据 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`，本交接与前轮诊断互相衔接。
"""
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f"""## 2026-10-30 — 原90—92实际图与loss绑定就绪；92继续

- [交接](docs/{TAG}.md)。完整90/91六组原核心引用精确保留，每组补充实际两图/loss收据/查看记录/原plan/早期失败hash；16错误元数据与真实缺完整92均拒绝。原统计/5%/5000bootstrap未改、未运行，I/A必要条件失败保留，无自动93/Direct34，未收敛。
- 原105身份连续{observed['elapsed_s']:.3f}s/{observed['samples']}样本保持、三路steps增长；保存steps{steps}，冻结完成{counts}。完整92、固定终端92及冻结全90/raw/paired仍待；所有历史失败/Direct原结论/指定ESN缺失保持。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，发布见收据。Goal active，无子agent。

"""
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()})))
