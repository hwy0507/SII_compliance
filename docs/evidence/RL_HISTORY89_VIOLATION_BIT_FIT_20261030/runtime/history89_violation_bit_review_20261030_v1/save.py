from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/history89_violation_bit_paired_fit_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1'
TAG='RL_HISTORY89_VIOLATION_BIT_FIT_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
for name in ('PREFLIGHT_REVIEW.json','REVIEW.json','SAVED_REVIEW.json','FINISHED.json','RUN_FINISHED.json','OBSERVATION_REVIEW.json'):assert read(T/name)['passed']
inspection=read(T/'PLOT_INSPECTION.json');assert inspection['actual_visual_inspection'] and sha(T/'paired_violation_bit_fit.png')==inspection['plot_sha256']
decision=read(D/'SCIENTIFIC_DECISION.json');assert decision['all_methods_and_critics_retained']
observed=read(T/'OBSERVATION_REVIEW.json');live=[]
for j in observed['original_live_identities']:
 p=Path('/proc',str(j['pid']));s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start'];live.append(j)
frozen={m:read(F/m/'PROGRESS.json') for m in ('impedance','admittance','vmc')}
rows=[]
for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 if r['time']>=read(T/'PLAN.json')['time']:rows.append(r)
assert time.time()-rows[-1]['time']<25 and not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists()
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[r['utilization'] for r in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),original_identities=live,frozen=frozen,gpu=gpu,goal='active',automatic90=False,trained_weights_promoted=False))
files=set()
for folder in (T,D):
 for p in folder.iterdir():
  if p.is_file() and p.suffix in ('.json','.jsonl','.py','.png','.npz','.log') and p.stat().st_size<10_000_000:files.add(p)
for m in frozen:files.add(F/m/'PROGRESS.json')
for name in ('PLAN.json','LAUNCH.json','REVIEW_LAUNCH.json'):files.add(F/name)
for name in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_COMPLETE89_BOUNDARY_DIAGNOSIS_20261030'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();relative=p.relative_to(B);q=E/relative;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(relative),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Registered matched terminal diagnostic, all six500-step arms, all saved endpoints and plots, decision and live frozen/GPU snapshot; original complete89 checkpoints and raw87 histories remain shared SSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='8610fd8e864c10e573e5f1a3cd20e42494645219',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; HDD254-byte pointer only, not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
pre=read(T/'PREFLIGHT_REVIEW.json');fit=read(T/'REVIEW.json');saved=read(T/'SAVED_REVIEW.json');plan=read(T/'PLAN.json')
text=f'''# 完整89因果穿透违规位：匹配离线拟合结果

2026-10-30 UTC，Goal active。上一轮完整89/固定87终端跟踪发现阻抗critic3对刚超过穿透阈值的旧终端明显退化；本轮完成单独登记的有限配对拟合。全部三方法和五critic保留，正式89 checkpoint、actor/alpha/target与物理没有更新，拟合权重未保存推广。原冻结88与四卡GPU保持程序继续，未启动90/Direct34。

主机 `{socket.gethostname()}`；共享SSD `{B}`；解释器 `{B}/env/bin/python`。运行/源码 `{T}`，后续决定 `{D}/SCIENTIFIC_DECISION.json`。前序完整证据见[完整89交接](RL_COMPLETE89_BOUNDARY_DIAGNOSIS_20261030.md)。

## 事前登记与实际匹配

PLAN SHA256 `{sha(T/'PLAN.json')}`，源、完整89 checkpoint/registration、原87 sidecar、原完整审查及全部端点值均绑定。CPU11/GPU1，拟合阶段900秒预算，每方法每臂固定500步，总3000个clone Q优化器步；完整运行耗时{fit['elapsed_s']:.3f}秒。先完成三方法0更新的实际恢复预检，再启动独立有限supervisor2839122、fit2839166与observer2839124，三者正常完成后不可重启。

两臂都将critic输入51→52，保留已学连续history列50，在观测索引51插入零权重列，动作权重列右移；全部旧Adam矩/step/group保持，新列矩0。对照新增输入恒0，实验新增输入`float(raw动作前累计外穿透>.0002)`。两臂同参数量、初始模型/optimizer逐位相同，三方法实际初始Q与原51模型/保存89预测误差全部0；完整learner及Python/NumPy/local/Torch/CUDA RNG前后保持。

原87固定全部终端I2605/A2604/V2604；违规位非零70/60/45行。原observations51/actions/rewards/masks及indices与完整89 replay逐位核验；因果raw sidecar和原连续feature精确对齐。只优化五critic之原mask终端MSE之和，fullbatch每步，全部为terminal故terminal128系数约掉；无bootstrap、actor/alpha/target更新。固定500终点为主，不选择中间最好步数。

| 方法 | 初始masked loss | 对照500步 | 违规位500步 | 违规位−对照 |
|---|---:|---:|---:|---:|
'''
for m,x in saved['methods'].items():
 s=x['stats'];text+=f"| {m} | {s['initial']['control']['masked_loss']:.9f} | {s['final']['control']['masked_loss']:.9f} | {s['final']['bit']['masked_loss']:.9f} | {x['bit_minus_control_final_loss']:+.9f} |\n"
text+='\n五critic最终masked SSE差（违规位−对照，负为更低）：\n\n'
for m,x in saved['methods'].items():text+=f"- {m}: `{x['bit_minus_control_final_sse_by_critic']}`。\n"
text+=f'''
保存预测由独立逐标量math.fsum重算全部初末SSE和masked loss，与训练日志在登记的浮点容差内一致；各501点曲线、全部行/all5保留。六栏图已实际查看，记录：{inspection['findings']}

## 科学判断及后续

{decision['interpretation']}

{decision['next_action']}

这是已在训练中使用过的原87终端上的离线拟合，不能证明在线reward改善、未见样本泛化、失败因果或整体收敛。没有改变物理MJB、Task/Strict/未知边缘门、canonical48 actor信息、filter、执行器、dt5e-5、正式LR或reward。原88—90 A/V相邻5%窗口失败仍成立；不存在全三轮bootstrap结果，不能以此诊断替代稳定性证据。

## 仍运行的评测与GPU

原冻结88 `{F}` 保存完成数 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`；原evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409与五个guard身份持续。观察{observed['elapsed_s']:.3f}秒/{observed['samples']}样本，诊断正常完成，冻结物理继续。原21600秒截止不延长，最终全90/全state不变/raw审计/82→88配对仍待，无重复派发。

原v7 supervisor97370与workers97399–97402继续，科研全部结束也保载，阈值50%、目标70%。本轮{gpu['samples']}采样min `{gpu['minimum']}`%、低于50次数 `{gpu['below50']}`，末值 `{gpu['last']}`%；含合成负载，非科研吞吐或每瞬时保证；旧v7预热0及v6 31/33/44低谷保留。不是重启自启服务。

## 发布与完整目标

本轮query/fetch/read main8610fd8e864c10e573e5f1a3cd20e42494645219及baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d。沿用sii-research-sync，无子agent。共享SSD `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；tar与AST通过，index/commit逐字核验及成功push/真实远端确认后PUBLICATION见包外收据。

HDD仅原位254字节LATEST，原大checkpoint/raw/sidecar继续共享SSD，非HDD/arm1全备份。Direct33数值接受但冻结30 Task/Strict0/0，28中断缺最终内存不变证明；指定ESN未提供、不替代其他主机模型。partial75、74—76不可判、79安全中止、全部失败窗口、halfstd拒绝及软件失败保留。完整reward稳定、loss健康、最终冻结及原ESN比较未证实，Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整89匹配因果违规位离线拟合完成

- [交接](docs/{TAG}.md)。准确完整89两组同52维/新列零/原已学history及Adam保留，三方法实际恢复与初始Q误差0；原87全部7813终端/原masks/all5，每臂固定500步共3000 clone更新，actor/alpha/target/正式checkpoint与RNG不变，0physics/无权重推广。
- {decision['short_result']} 全初末保存值独立标量复算/六栏实际图通过，仅已见终端拟合；{decision['short_next']} 原88—90失败窗口保持，未收敛、无90/Direct34。
- 原冻结88完成数{ {m:x['completed_conditions'] for m,x in frozen.items()} }，原evaluator/collector/postprocessor继续，最终全90/raw/配对待。GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份。main8610fd8e/baselinef6e8f8c已query/fetch/read，发布见收据，无子agent，Goal active。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print(json.dumps(dict(receipt=receipt,gpu=gpu,frozen={m:x['completed_conditions'] for m,x in frozen.items()})))
