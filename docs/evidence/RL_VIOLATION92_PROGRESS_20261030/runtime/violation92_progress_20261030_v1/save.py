from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle92_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
TAG='RL_VIOLATION92_PROGRESS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
observed=read(D/'OBSERVATION_REVIEW.json');assert observed['passed'] and read(B/'runtime/violation92_stability_ready_20261030_v1/INPUT90_91_READY_REVIEW.json')['passed']
assert read(B/'runtime/violation92_stability_ready_20261030_v1/PLOT_BINDING_GUARD_REVIEW.json')['passed']
plan=read(S/'PLAN.json');assert sha(S/'audit.py')==plan['source_sha256'] and sha(S/'review_saved.py')==plan['review_source_sha256'] and sha(S/'PLAN.json')==read(B/'runtime/violation92_stability_ready_20261030_v1/BINDING_PLAN.json')['original_plan_sha256']
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
for folder in [D]:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 files.add(T/m/'train/PROGRESS.json');files.add(F/m/'PROGRESS.json')
for p in [T/'LAUNCH.json',T/'MONITOR_LAUNCH.json',F/'LAUNCH.json',F/'REVIEW_LAUNCH.json',O/'PROCESS.json',O/'PLAN.json']:files.add(p)
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_VIOLATION92_STABILITY_READY_20261030'/name)
files.add(B/'runtime/violation92_stability_ready_20261030_v1/INPUT90_91_READY_REVIEW.json')
files.add(S/'EARLY_WINDOW_FAILURE_91.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Ten-minute verified wait on original92 training, frozen90 and GPU guard. Actual process identities and progress; no new training, no statistical result. Previous bindings and early failure preserved. Large artifacts remain shared SSD; not full HDD/arm1 backup.'))
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
growth={m:observed['last']['steps'][m]-observed['first']['steps'][m] for m in progress}
text=f"""# 原第92轮与冻结90继续：十分钟 verified wait

Goal active。上一轮实际完成了完整90/91稳定性输入/实际图/loss来源绑定，属于 progress；本轮为原活跃进程的 verified wait。没有将等待或GPU保活当作数值收敛。

实际主机 `{socket.gethostname()}`，共享SSD根 `{B}`。按照 `skills/sii-research-sync/SKILL.md`，实际 query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，两分支无新变更；无子agent。

## 实际等待证据

开工逐个读取 `/proc/PID/stat` 确认原三路92 learner463617/463619/463621、archive463623、固定87终端等待器1234380、冻结90 evaluator283421/283428/283430、collector283433、postprocessor292743以及原guard存活且start ticks一致。随后 `{D}/observe.py` 按预先保存的 `OBSERVATION_PLAN.json` 连续观测 {observed['elapsed_s']:.3f}秒、{observed['samples']}次，原105身份（含90sampler子进程）保持，三路累计步数增加 `{growth}`。

保存时92总steps `{steps}`。原三路92仍各30条件运行中，完整 REVIEW/FINISHED/health/loss 未生成；原archive与固定7813终端92比较等待仍活跃。冻结90完成数 `{counts}`，每方法总30；完整全90/raw/88→90 paired及learner/replay不变证明待。不得重启仍活跃任务、延长原截止或把partial当complete。未派发新训练，无自动93/Direct34。

GPU记录 `{D}/GUARD_SAMPLES.jsonl` 共{gpu['samples']}样本，四卡min `{gpu['minimum']}`%，低于50次数 `{gpu['below50']}`，末样本 `{gpu['last']}`%。原 `/tmp/sii_gpu_util_guard_20261030_v7` 的supervisor97370/worker97399–97402保持，threshold50/target70/min duty.7；用户要求科学完成后也继续保活。采样含synthetic guard占用，不是纯科研吞吐或每瞬时保证；历史warmup0及v6的31/33/44低值记录保持。守护不是重启自动服务。

## 继续工作入口

待实际完整92审查后，按前轮 `docs/RL_VIOLATION92_STABILITY_READY_20261030.md` 的绑定和原统计命令执行，并实际查看图。原PLAN/audit/review_saved的hash已重新核对，原REGISTRATION/REVIEW仍不存在。原90→91相邻 I42.5116%、A20.8292%失败已保存在 `EARLY_WINDOW_FAILURE_91.json`，V一个相邻对不足以判定窗口。原5%/nearzero1/5000bootstrap/seed不变，未运行完整窗口统计。原独立review仅复算标量，不重算bootstrap区间。

固定87终端92预测尚待；原第92轮首5000 loss已有I密集尖峰/actor上移、V尖峰簇，完整91亦未达到健康收敛。所有失败窗口、partial75、不可评74–76、79/90安全中止、halfstd拒绝与软件失败保持。Direct33原数值验收与冻结全30 Task/Strict0/0保留，旧28最终内存证明缺失、恢复2完整不变；不追加task成功作为数值收敛条件。指定ESN仍不可用，不替换其他主机模型。

冻结physics/MJB、dt5e−5、canonical48 actor信息、filter/执行器与Task/Strict门槛均保持；每方法30×55秒、最多41250新增、4m append-only replay及23/47标记、terminal128/batch65536/UTD1/原LR reward masks。critic/replay52、actor49、clock49/history50/raw bit51、已学history与violation权重、Adam/RNG/双marker保持，无新参数更改。

## 保存

小证据归档 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`。tar成员逐字与清单核对、Python AST通过。清单 `docs/evidence/{TAG}/MANIFEST.json`；后续实际提交字节与远端验证在 `{A}/GIT_BYTES_REVIEW.json` 和 `PUBLICATION.json`。本包依赖前轮完整输入绑定证据，未重复复制大文件。

HDD配额满，仅原地更新现有 `sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md` 严格254字节并回读。checkpoint/raw/replay/runtime仍共享SSD，不是HDD/arm1全备份。恢复主入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
"""
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f"""## 2026-10-30 — 原92与冻结90持续：十分钟 verified wait

- [交接](docs/{TAG}.md)。原105身份连续{observed['elapsed_s']:.3f}s/{observed['samples']}样本保持，三路steps增长{growth}；保存steps{steps}，冻结完成{counts}。原archive/终端等待继续，无重启、新训练或预算延长。
- 完整92/健康稳定/固定终端92与冻结90全90/raw/paired仍待；前轮绑定和原I/A失败保持，无完整窗口统计/自动93/Direct34，未收敛。全部历史失败、Direct原结论及指定ESN缺失保持。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，正常发布见收据。Goal active，无子agent。

"""
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()})))
