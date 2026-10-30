from pathlib import Path
import ast,json,os,socket,hashlib,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_history_cycle89_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';O=B/'runs/history89_fixed87_terminal_followup_20261030_v1';S=B/'runs/parameter_history88_90_reward_stability_20261030_v2'
TAG='RL_HISTORY89_STABILITY_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
observed=read(D/'OBSERVATION_REVIEW.json');assert observed['passed'] and read(D/'INPUT88_REVIEW.json')['passed'] and read(S/'LABEL_CORRECTION.json')['passed']
for j in observed['identities']:
 stat=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert stat[0]!='Z' and stat[19]==j['start']
assert not list(O.glob('*FAILURE*.json')) and not (T/'ARCHIVE_REVIEW_FAILURE.json').exists()
progress={};frozen={}
for m in ['impedance','admittance','vmc']:
 assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
 progress[m]=read(T/m/'train/PROGRESS.json');frozen[m]=read(F/m/'PROGRESS.json')
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if l.endswith('}')];rows=[r for r in rows if r['time']>=1793382595.0];assert time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[r['utilization'] for r in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=observed['identities'],training89=progress,frozen88=frozen,gpu=gpu,goal='active',automatic90=False,full_stability_statistics_evaluated=False))
files=set()
for folder in [D,S]:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 files.add(T/m/'train/PROGRESS.json');files.add(F/m/'PROGRESS.json')
for p in [T/'LAUNCH.json',T/'MONITOR_LAUNCH.json',F/'LAUNCH.json',F/'REVIEW_LAUNCH.json',O/'PROCESS.json',O/'PLAN.json']:files.add(p)
for name in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_HISTORY89_PREFIX_FOLLOWUP_20261030'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Shared SSD supplemental stability label correction/input binding and live observations. Full statistics not run. Original diff context retained. Large artifacts remain SSD; not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for member in tar.getmembers():assert tar.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='d8ef159fa84acbde264c1460453fa50153dc0b76',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD, HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 原89继续；88—90稳定性报告标签和真实输入绑定核验

2026-10-30 UTC，Goal active。原89训练、冻结88及所有后处理继续；上一轮完成固定5000科学审查和终端跟踪登记，本轮修正预先准备的稳定性脚本中旧窗口标签，验证完整88输入，并持续观察原105进程。没有完整89/90或稳定性结论，没有自动90/Direct34。

主机 `{socket.gethostname()}`；共享SSD `{B}`；Python `{B}/env/bin/python`。上一完整状态见[89前缀与终端跟踪交接](RL_HISTORY89_PREFIX_FOLLOWUP_20261030.md)。

## 发现与修正

原预登记 `{B}/runs/parameter_history88_90_reward_stability_20261030_v1/PLAN.json` 在history88启动前已固定cycles88/89/90、seed2026102861、5000bootstrap、nearzero1和relative5%。检查发现原audit.py实际计算轮号已正确，但图标题/limitation及`paired85_to87_mean_delta`输出字段仍残留85—87名称，review_saved.py说明和读取字段同样残留。原版本尚未部署或产生该窗口统计，不存在需要覆盖的历史结果。

在独立 `{S}` 修正标题/说明及字段为`paired88_to90_mean_delta`；保留原v1文件。`LABEL_CORRECTION.json`绑定父/新源hash，明确除字符串元数据和该字段名之外AST完全相同，原计算公式、阈值、seed、采样、周期及科学契约均未改变。原PLAN逐字存为ORIGINAL_PLAN.json并保持原hash/时间，不将修正文档冒充训练前登记的新算法。旧85—87失败窗口继续保留。

## 输入绑定入口

`{D}/bind_inputs.py`，`--check-only`已对实际完整88三方法的review/health/loss/FINISHED/实际图、同history amendment、原55科学契约、23/47容量标记、全30条件/model/cycle/reward总和、41250条预算及optimizer原hash验证。88活动汇总使用真实v2目录，保留I/V原目录链接及A仅恢复重试后的实际源，不伪造单一旧v1父。

真实未完整89的绑定被拒绝；没有生成全窗口REGISTRATION，也没有计算88—90统计或绘制不存在的结果。之后只有完整89及单独决定/登记后的完整90都已完成review/health/loss并实际查看图，才可向bind_inputs.py传入真实`--cycle90-run`和`--cycle90-review`路径生成最终REGISTRATION；再执行v2的`audit.py --root`及`review_saved.py`并实际看图。该入口不启动任何训练，也不是90授权。

原指标含相邻及端点相对变化、nearzero保护、按3类条件分层的5000配对bootstrap。置信区间仅反映条件组合敏感性，不是独立训练seed或冻结策略泛化；标量复算程序明确不独立重算bootstrap区间。有限loss和5%描述检查都不能单独宣告完整健康收敛，不能跨history修订拼接旧失败窗口。

## 原作业及GPU继续

本轮{observed['elapsed_s']:.3f}秒/{observed['samples']}样本，105个原训练/sampler/归档/冻结/后处理/终端等待/guard身份保持，三路训练实际steps均增长。保存时总steps `{ {m:v['steps'] for m,v in progress.items()} }`；原完整89archive/review监视3433024与固定87终端等待4055969继续，没有重启或新训练。

原冻结88 `{F}`，保存进度 `{ {m:dict(completed=v['completed_conditions'],condition=v['condition'],actions=v['actions']) for m,v in frozen.items()} }`。最终全90/全state不变、raw保存审计及82→88配对仍待；原预算未延长，所有失败保留。

原v7守护继续，科学任务全部结束也保载，阈值50%、目标70%。本轮{gpu['samples']}采样min `{gpu['minimum']}`%、低于50 `{gpu['below50']}`，末值 `{gpu['last']}`%；含合成负载，非科研吞吐、非每瞬时保证。历史v7预热0和v6 31/33/44低谷保留，非开机自启服务。

## 归档与剩余目标

本轮实际query/fetch/read main `d8ef159fa84acbde264c1460453fa50153dc0b76`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。沿用sii-research-sync，无子agent。共享SSD包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，tar成员和Python AST已核；index/commit另逐字核验，正常push及实际远端确认后写包外PUBLICATION。原diff上下文空格逐字保留。

HDD仅原位更新254字节LATEST，checkpoint/raw仍共享SSD，非HDD/arm1全备份。Direct33数值接受但冻结Task/Strict0/0，28中断缺最终内存不变证明；指定ESN仍缺失，不替代其他主机模型。partial75、74—76不可判、79安全中止、旧稳定性失败、半std失败及历史软件失败全部保留。当前仅88完成、89运行、90未派发；完整reward稳定、loss健康和原全范围目标尚未证明，Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 原89继续；88—90稳定性标签修正及真实88绑定通过

- [交接](docs/{TAG}.md)。原88—90预登记脚本遗留85—87图题/字段/说明，独立v2仅修标签，原PLAN/hash保留；除字符串与字段名外AST相同，公式/原seed/5000bootstrap/5%/nearzero1不变。实际完整88三路全输入/历史revision/55科学契约绑定通过，未完整89真实拒绝；未跑全窗口统计，不授权90。
- 原89与冻结88、archive3433024和固定87终端等待4055969继续，{observed['elapsed_s']:.3f}秒/105身份观察通过；总steps{ {m:v['steps'] for m,v in progress.items()} }，完整89/稳定性及冻结88全90回合结果仍待，无自动90/Direct34。
- GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束继续守护；共享SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，非HDD/arm1全备份。maind8ef159f/baselinef6e8f8c已query/fetch/read，发布见收据；Goal active，无子agent，历史失败保留。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()})))
