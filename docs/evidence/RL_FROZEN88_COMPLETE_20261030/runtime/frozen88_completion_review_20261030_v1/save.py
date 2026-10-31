from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,os
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
TAG='RL_FROZEN88_COMPLETE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
O=B/'runs/parameter88_history_frozen_full30_20261030_v1';T=B/'runs/parameter_violation_cycle90_20261030_v1'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
r=read(D/'REVIEW.json');assert r['passed'];assert read(D/'PLOT_INSPECTION.json')['inspected']
start=read(D/'START.json');live={};exited={}
for pid,old in start['identities'].items():
 p=Path(f'/proc/{pid}/stat')
 if p.exists():
  fields=p.read_text().rsplit(')',1)[1].split()
  if fields[0]!='Z':
   assert fields[19]==old['start'];live[pid]=dict(start=fields[19],state=fields[0]);continue
 exited[pid]=old
for pid in (97370,97399,97400,97401,97402,1096445,1096447,1096449,1096452,2283008):assert str(pid) in live
for pid in (2675653,2675660,2675662,2675665,2713409):assert str(pid) in exited
progress={m:read(T/m/'train/PROGRESS.json') for m in r['methods']}
for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists()
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists()
rows=[json.loads(line) for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines() if line.strip()]
rows=[x for x in rows if x['time']>=start['time']]
assert rows and time.time()-rows[-1]['time']<25 and not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists()
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress90=progress,original_live=live,original_finished=exited,goal='active',automatic91=False))
files={p for p in D.iterdir() if p.suffix in {'.py','.json','.jsonl'}}
for directory in (O,B/'runs/parameter88_history_frozen_saved_audit_20261030_v1',B/'runtime/history88_frozen_postprocess_20261030_v1'):
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in {'.json','.py','.png','.diff'} and p.stat().st_size<4_000_000:
   # Raw episode directory receipts remain on SSD with audited hashes; collect method and root reviews.
   rel=p.relative_to(directory)
   if directory==O and len(rel.parts)>2:continue
   files.add(p)
for m in progress:
 for n in ('EXECUTION.json','PROGRESS.json'):files.add(T/m/'train'/n)
for n in ('LAUNCH.json','MONITOR_LAUNCH.json'):files.add(T/n)
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_VIOLATION90_TERMINAL_FOLLOWUP_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Completed original frozen88 all90, full learner/replay invariance, same-seed82 pairs, independent raw audit; original90 and guard continue.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
remote=read(D/'REMOTE_START.json')
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
lines=[]
for m,v in r['methods'].items():
 c=v['comparison82_88'];lines.append(f"| {m} | {c['task_before']} → {v['task']} | {c['strict_before']} → {v['strict']} | {v['mean_reward']:.9f} | {c['mean_reward_delta']:.9f} | {v['machine_safety_violation_count']} |")
text=f'''# 冻结88全90完成；原90训练继续

2026-10-30 UTC，Goal active。主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际query/fetch/read main `{remote['main']}` 与baseline `{remote['baseline']}`，未发现新相关协议变化。采用仓库sii-research-sync，无子agent。

原冻结88三方法各30个原训练条件、固定动作seed2026102638已全部完成，共{r['total_actions']}动作/{r['total_substeps']}物理子步。原evaluator、collector、postprocessor正常结束，均未重启；全部final full learner/replay状态不变，初末digest一致、0优化器更新。完整评测的成功标签与实现审计通过分开陈述。

| 方法 | Task82→88（/30） | Strict82→88（/30） | 88平均reward | 配对平均变化 | 88机器违规数 |
|---|---:|---:|---:|---:|---:|
{chr(10).join(lines)}

两项机器违规均为`active_short_train_0600`：I峰穿透0.2434523239mm、A0.2053474959mm，超过原0.20mm。I总Strict未变，但short0100获成功、short0600失成功；A新增short0900和long0500双成功，同时short0600丢Strict。V成功集合不变、mean reward略降。各方法最初10条passive条件均失败，低穿透不能替代任务完成。

完整逐条件结果、获失成功、失败条件、力矩/实际接触时间及按接触分母汇总见 `{D}/REVIEW.json`。原始90回合reward、物理dt/子步、穿透、逐关节峰力矩、机器违规、实际接触舒适比例均经独立raw审计和保存回读核验；no-contact保持NA。原审计 `{B}/runs/parameter88_history_frozen_saved_audit_20261030_v1`，所有82→88配对 `{O}/comparison82_88`，完整原评测 `{O}`。实际查看六栏结果图并另存PLOT_INSPECTION，不把文件存在当目视核验。

该比较仍是原训练集合/单外部动作seed；82→88包含额外在线训练与history critic修订，不能单独归因修订、声称保留集泛化或证明reward稳定。所有失败保留，非最终SPT/指定ESN比较。Direct原数值验收保持，冻结33全30 Task/Strict0/0、原28最终内存证明缺失仍保留；不启动Direct34。指定ESN仍缺，不替换其他主机模型。

原有限90三路PID1096445/1096447/1096449与archive1096452、固定87终端等待器2283008仍保持原身份。保存总steps `{ {m:v['steps'] for m,v in progress.items()} }`，各30sampler继续。完整90/health/loss/固定终端90预测仍待，尚未收敛；不自动91/92。90–92统计预登记不代表训练授权或完成窗口；旧失败窗口、partial75、74–76不可判、79安全abort、半std拒绝及软件失败保持。第90轮首5000中I critic尖峰/actor漂移的限制不被本次冻结88结果消除。

物理/MJB/Task/Strict/filter/执行器/dt5e−5、canonical48/actor49、30×55s/41250新transition、4m append和23/47 markers、terminal128/batch65536/UTD1/原LR/reward/masks保持。训练90当前critic/replay52、clock49/history50/rawbit51和已学history/Adam/双marker保持；无离线拟合权重晋升。

GPU原guard97370及97399–97402继续，科研完成后也保载；本轮{gpu['samples']}个样本/{gpu['elapsed_s']:.1f}秒，最低{gpu['minimum']}%，低于50计数{gpu['below50']}，末值{gpu['last']}%。含合成负载，非科研吞吐，不保证每个瞬时；旧v7 warmup0/v6低谷保留。没有创建STOP，guard非重启服务。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`；逐tar成员与Python AST已核验，Git index/commit逐字核验和正常push/实际远端确认记录在包外PUBLICATION。大checkpoint/raw仍共享SSD；HDD仅原位更新254字节指针，非HDD/arm1全备份。

接续：原90完整结束后收齐archive/review/health/loss及固定87终端跟踪90图，实际查看再作有限下一步科学决定；完整90冻结方案已准备，但仍需完整门槛、实际check-only、最终登记及独立派发。本轮完成88原评测后处理，不重复物理回合。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 冻结88全部90评测与raw/配对审计完成

- [交接](docs/{TAG}.md)。原三路各30、{r['total_actions']}动作/{r['total_substeps']}子步，final full learner/replay不变、0updates；原evaluator/collector/postprocessor正常结束勿重启。Task/Strict分别{[(v['task'],v['strict']) for v in r['methods'].values()]}，全90 raw/reward/力矩/接触分母与82→88配对/保存算术通过，实际图已查看，全部失败保留，非泛化/收敛。
- 原90/归档/固定87终端等待器继续，总steps{ {m:v['steps'] for m,v in progress.items()} }；完整90与健康稳定待。无自动91/Direct34，指定ESN仍缺。GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载，非科研吞吐。
- SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非HDD/arm1全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read；正常发布见收据，Goal active，无子agent，全部历史失败保留。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print(json.dumps(dict(receipt=receipt,gpu=gpu,progress90=progress)))
