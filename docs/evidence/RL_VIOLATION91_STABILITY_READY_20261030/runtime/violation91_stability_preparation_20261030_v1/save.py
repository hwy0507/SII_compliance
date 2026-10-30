from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle91_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation91_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
TAG='RL_VIOLATION91_STABILITY_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
observed=read(D/'OBSERVATION_REVIEW.json');assert observed['passed'] and read(D/'INPUT90_REVIEW.json')['passed']
plan=read(S/'PLAN.json');assert sha(S/'audit.py')==plan['source_sha256'] and sha(S/'review_saved.py')==plan['review_source_sha256'] and sha(S/'PLAN.json')==read(D/'BINDING_PLAN.json')['original_plan_sha256']
assert not (S/'REGISTRATION.json').exists() and not (S/'REVIEW.json').exists()
for j in observed['identities']:
 stat=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert stat[0]!='Z' and stat[19]==j['start']
assert not list(O.glob('*FAILURE*.json')) and not (T/'ARCHIVE_REVIEW_FAILURE.json').exists()
progress={};frozen={}
for m in ['impedance','admittance','vmc']:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
 progress[m]=read(T/m/'train/PROGRESS.json');frozen[m]=read(F/m/'PROGRESS.json')
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if l.endswith('}')];rows=[r for r in rows if r['time']>=read(D/'BINDING_PLAN.json')['time']];assert time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[r['utilization'] for r in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=observed['identities'],training91=progress,frozen90=frozen,gpu=gpu,goal='active',automatic92=False,full_stability_statistics_evaluated=False))
files=set()
for folder in [D,S]:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 files.add(T/m/'train/PROGRESS.json');files.add(F/m/'PROGRESS.json')
for p in [T/'LAUNCH.json',T/'MONITOR_LAUNCH.json',F/'LAUNCH.json',F/'REVIEW_LAUNCH.json',O/'PROCESS.json',O/'PLAN.json']:files.add(p)
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_VIOLATION91_TERMINAL_FOLLOWUP_20261030'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Shared SSD abort-aware stability input binding and live observations. Full statistics not run. Original diff context retained. Large artifacts remain SSD; not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for member in tar.getmembers():assert tar.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='20c5b5fc3ee7f1f57488290790136de0ea48a3d3',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD, HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 原91继续；90—92稳定性实际输入绑定准备

2026-10-30 UTC，Goal active。前序[91固定终端跟踪](RL_VIOLATION91_TERMINAL_FOLLOWUP_20261030.md)。本轮准备原90—92统计方案的输入绑定，核验完整90真实数据，并观察原105进程；没有新训练、物理或bootstrap，没有完整91/92结果，不自动92/Direct34。

主机 `{socket.gethostname()}`，共享SSD `{B}`，Python `{B}/env/bin/python`，绑定脚本 `{D}/bind_inputs.py`。实际query/fetch/read main `20c5b5fc3ee7f1f57488290790136de0ea48a3d3`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无相关科学契约变化；采用sii-research-sync，无子agent。

原方案 `{S}/PLAN.json`、audit.py、review_saved.py保持原hash；cycles90/91/92、seed2026102861、5000bootstrap、nearzero1、relative5%、原55科学锚点及两架构amendment保持。旧88—90失败及修订边界原件hash核验，不重写训练前登记或统计公式。

较早history88—90绑定器假定每轮41250且用固定历史起点推算累计步数，不能直接用于90阻抗安全中止。新入口使用各轮准确parent review.steps + 实际new_transitions，并绑定各轮科学决定/continuation、原协议、历史与违规位修订、23/47容量、完整review/health/loss/FINISHED及实际图。完整90的I40752新步/29完整+1中止、A/V各41250/30完整均验证；原30条件分母、abort列表、reward/Task/Strict、实际optimizer连续步数和文件hash精确，I long0000 877动作安全中止不会丢失或填满。90的初始52迁移父与91之后的已学父分别按实际证据绑定，不把旧89 bit binding行数误当90后父行数。

`--check-only`已对完整90三方法通过上述约束与原55科学契约，真实缺完整91被拒绝。当前没有生成REGISTRATION.json、完整窗口REVIEW或bootstrap结果。最终绑定入口要求完整91及另外明确登记、审查的92实际路径：`--cycle92-run`和`--cycle92-review`，各周期均须准确parent/new cycle、单轮预算、科学决定hash及完整图审查通过。此入口不启动训练，不构成92授权。

原统计按真实回合长度保留中止，比较相邻/端点均值变化、3类条件分层配对bootstrap；区间仅为条件组合敏感性，非独立训练seed/冻结策略泛化。原review_saved只独立复算标量，不独立复算bootstrap区间。5%描述检查和有限loss均不能单独证明整体健康收敛。本轮没有计算缺失周期的结果。

连续{observed['elapsed_s']:.3f}秒/{observed['samples']}样本，105个原训练/sampler/archive/冻结/collector/postprocessor/固定终端等待/guard身份保持，三路steps增长。保存总steps `{ {m:v['steps'] for m,v in progress.items()} }`；冻结90完成 `{ {m:v['completed_conditions'] for m,v in frozen.items()} }`/各30。完整91 review/health/loss、固定87终端诊断和冻结90全90/raw/88→90配对/最终全state仍待，原预算不延长。

GPU原守护97370/97399–97402继续，科学全结束仍保载；{gpu['samples']}采样最低{gpu['minimum']}%、低于50{gpu['below50']}，末值{gpu['last']}%；含合成负载，非科研吞吐/每瞬时保证，非重启自启。原物理/MJB/gates/filter/执行器/dt5e−5、actor49/canonical48、critic52/history/Adam/RNG、4m/terminal128/batch65536/UTD1/原LR/reward保持。

Direct原数值阶段接受及冻结33全30 Task/Strict0/0、旧28最终内存证明缺失保持，指定ESN仍缺，不替换其他模型。所有旧失败窗口、partial75、74—76不可判、79/90安全中止、半std拒绝和软件失败保留。原91早期I/V尖峰与actor漂移未因此解决，未收敛。

证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，逐tar成员/AST核验；index/commit逐字、正常push和远端确认后写包外PUBLICATION。大产物共享SSD，HDD仅原位254字节指针，非HDD/arm1全备份。继续等待原91完整审查，依据实际结果决定下一有限阶段。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 原91继续；90—92稳定性实际90输入绑定通过

- [交接](docs/{TAG}.md)。原90—92方案/hash/5%/nearzero1/5000bootstrap不变；新绑定以准确父+实际新增步数替代早期固定41250假设，实际90 I40752/29完整+1安全中止、A/V41250及30分母/reward/loss/原55契约通过。真实缺91拒绝，无完整窗口统计/REGISTRATION、无92派发。
- 原91/冻结90/archive/固定终端等待及guard持续，{observed['elapsed_s']:.3f}s/105身份保持，总steps{ {m:v['steps'] for m,v in progress.items()} }，冻结完成{ {m:v['completed_conditions'] for m,v in frozen.items()} }。完整91及冻结90全90/raw/paired仍待，未收敛。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针，非全备份。main20c5b5fc/baselinef6e8f8c实际query/fetch/read，正常发布见收据；Goal active，无子agent，全部旧失败保持。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()})))
