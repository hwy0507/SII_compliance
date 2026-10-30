from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_history_cycle89_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';O=B/'runs/history89_fixed87_terminal_followup_20261030_v1';POST=B/'runtime/history88_frozen_postprocess_20261030_v1'
TAG='RL_HISTORY89_PREFIX_FOLLOWUP_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def identity(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==str(j.get('start',j.get('proc_start_ticks')));return dict(pid=j['pid'],start=s[19])
prefix=read(D/'prefix5000/REVIEW.json');observed=read(D/'OBSERVATION_REVIEW.json');preflight=read(O/'PREFLIGHT_REVIEW.json');assert prefix['passed'] and observed['passed'] and preflight['passed'] and read(D/'prefix5000/PLOT_INSPECTION.json')['actual_visual_inspection']
ids=[identity(j) for j in observed['identities']];assert not list(O.glob('*FAILURE*.json')) and not (T/'ARCHIVE_REVIEW_FAILURE.json').exists()
progress={};frozen={}
for m in ['impedance','admittance','vmc']:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
 progress[m]=read(T/m/'train/PROGRESS.json');frozen[m]=read(F/m/'PROGRESS.json')
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if l.endswith('}')];rows=[r for r in rows if r['time']>=1793381895.0];assert time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[r['utilization'] for r in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=ids,training89=progress,frozen88=frozen,gpu=gpu,goal='active',automatic90=False))
files=set()
for folder in [D,D/'prefix5000',O]:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.npz','.png'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 for name in ['PROGRESS.json','EXECUTION.json']:files.add(T/m/'train'/name)
 for name in ['PROGRESS.json','RESULTS.json']:files.add(F/m/name)
for name in ['LAUNCH.json','MONITOR_LAUNCH.json']:files.add(T/name)
for name in ['LAUNCH.json','REVIEW_LAUNCH.json']:files.add(F/name)
files.add(POST/'PROCESS.json')
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_HISTORY89_ONLINE_20261030'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Shared SSD supplement to RL_HISTORY89_ONLINE; exact fixed5000 optimizer prefixes, snapshots, readonly followup sources/plan. Large checkpoints/raw stay original SSD; not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for member in tar.getmembers():assert tar.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='b17dfd17f72ea243643359daa379f4a7e69313e0',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; HDD254-byte pointer only, not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
table=[]
for m,v in prefix['methods'].items():
 q=v['stats']['agent_train/q_loss'];actor=v['stats']['agent_train/actor_loss'];table.append(f"|{m}|{q['first1000']:.9f}→{q['last1000']:.9f}|{q['maximum']:.9f}|{actor['first1000']:.9f}→{actor['last1000']:.9f}|")
text=f'''# History89固定前5000与原87终端跟踪

2026-10-30 UTC，Goal active。上一轮实际续训及发布属于实质进展；本轮原89训练与冻结88持续，完成固定前5000 loss原字节/独立算术/实际图核验，并在完整89出现前登记原87全部终端all5跟踪。完整89、reward稳定和最终loss健康仍未证明，无自动90/Direct34。

执行主机 `{socket.gethostname()}`；共享SSD `{B}`；解释器 `{B}/env/bin/python`。原训练、全state准确恢复、84负例/6 clone更新及真实startup详见[89在线交接](RL_HISTORY89_ONLINE_20261030.md)。本轮runtime `{D}`；训练原run `{T}`，三个原learner及90sampler均未重启。

## 固定前5000实际loss

`{D}/prefix5000`保存三方法原optimizer.jsonl前5000行的准确字节，读取前固定同样长度，未按loss值挑选窗口。父steps取完整88审查，连续step/每transition单update、全部指标有限、Q loss非负通过；NPZ回读独立math.fsum统计，并再与原源前缀逐字比较。

|方法|critic首→末1000均值|单次critic最大值|actor首→末1000均值|
|---|---|---:|---|
{chr(10).join(table)}

实际查看 `prefix5000.png` 六栏图并绑定hash。I Q滚动均值约1.5–2.3且有尖峰，actor轻微上移；A Q约1.1–1.4，早期6.415尖峰，actor基本平；V Q约0.7–1.0且有7.392尖峰，actor有轻微后段漂移。无NaN/Inf只支持该保存前缀数值有限，不能据此判定完整loss健康或收敛。旧88最后1000统计另列于REVIEW，不跨架构拼接旧失败窗口；此时无完整89周期reward结论。分析0新物理/0优化器更新。

## 完整89的原87固定终端预登记

`{O}`，PLAN绑定原88跟踪保存值、旧完整87初始control、89登记及科学决定、恢复源码hash。仍是I2605/A2604/V2604原87终端/all5 critic/原masks/相同51维观测、动作与reward，保留原87与完整88预测，待完整89仅新增一次各critic forward；报告每critic88→89和87→89的mask内SSE差与全行误差。不能只选择此前退化的I critic3或A critic2/3，其余改善/退化全部保留。

预检已独立复算原87/88所有保存SSE/MSE并与原报告精确一致；真实缺失完整89时强制gate拒绝，0forward/physics/update。新等待器PID `{read(O/'PROCESS.json')['pid']}` 已核验真实存活，绑定原archive监视PID3433024和原启动+14400s截止 `{read(O/'PLAN.json')['wait_deadline_unix']}`；完整89的review/health/loss/FINISHED全部通过才执行，分析预算1800s。目标89原checkpoint精确、全部固定输入/marker不变、full learner与RNG不变、checkpoint原hash不变均为运行强制检查；尚未出现89结果，不把准备验证写成完成。未来图生成后仍需实际查看。

此跟踪是已见终端的拟合/保留诊断，不是独立泛化、history因果证明、策略成绩或新的收敛gate；没有加载先前离线fit后的权重，不训练、不派发下一周期。

## 原作业持续与GPU

本轮{observed['elapsed_s']:.3f}秒/{observed['samples']}样本，原105个learner/sampler/归档/冻结/后处理/guard/新等待器身份保持，三路训练steps持续增加。保存时总steps `{ {m:v['steps'] for m,v in progress.items()} }`。完整89归档/review/health/loss仍由原3433024负责，未重复启动。

冻结88原run `{F}`：保存进度 `{ {m:dict(completed=v['completed_conditions'],condition=v['condition'],actions=v['actions']) for m,v in frozen.items()} }`；原evaluator/collector/后处理继续，最终90、全state不变、raw保存审计及82→88全部配对仍待。没有重启或延长原冻结预算，前期失败保留，非held-out独立seed结论。

原v7 GPU守护保持，即使科学任务结束也继续；阈值50、控制目标70。本轮{gpu['samples']}采样min `{gpu['minimum']}`%、低于50 `{gpu['below50']}`，末值 `{gpu['last']}`%；包含合成保载，不当科研吞吐或每瞬时保证。v7预热0、v6 31/33/44历史低谷保留，不是重启自启服务。

## 保存和未完成项

实际query/fetch/read main `b17dfd17f72ea243643359daa379f4a7e69313e0`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关变更。沿用sii-research-sync，无子agent。小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，tar逐成员和Python AST已核；Git index/commit逐字核验后normal push与实际远端确认，包外PUBLICATION记录。

HDD只原位更新254字节LATEST；大checkpoint/轨迹留共享SSD，非HDD/arm1全备份。Direct33数值接受但冻结30 Task/Strict0/0、28中断缺最终内存不变；指定ESN未提供且不替代；partial75、74—76不可判、79安全中止、全部旧稳定性失败、半std失败及所有软件失败继续披露。88—90方案只有88完成/89运行/90未派发，先审完整89再作有限后续决定。Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — History89前5000已审；完整89固定87终端跟踪等待

- [交接](docs/{TAG}.md)。三方法固定5000原字节/独立保存算术/实际六栏图通过；critic首末均值I1.850637→1.681222、A1.193333→1.186347、V.777596→.785050，尖峰及I actor上移保留，非完整loss/reward稳定。
- 同原87全部终端/all5/原masks的87/88/89跟踪已在完整89前登记；已保存87/88算术精确、真实缺89前置拒绝，等待器{read(O/'PROCESS.json')['pid']}按原archive截止运行，0新forward/physics/update，实际89结果待。原89与冻结88持续，{observed['elapsed_s']:.3f}秒/105身份观察通过，总steps{ {m:v['steps'] for m,v in progress.items()} }。
- GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束继续守护；共享SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，非HDD/arm1全备份。mainb17dfd17/baselinef6e8f8c已query/fetch/read，发布见收据；Goal active，无子agent，无自动90/Direct34，历史失败保留。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()})))
