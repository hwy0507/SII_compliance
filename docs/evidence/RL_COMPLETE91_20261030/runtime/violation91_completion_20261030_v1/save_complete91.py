from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
T=B/'runs/parameter_violation_cycle91_20261030_v1';V=B/'runs/parameter_violation_cycle91_review_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation91_fixed87_terminal_followup_20261030_v1'
FD=B/'runtime/violation90_frozen_dispatch_20261030_v1';FP=B/'runtime/violation90_frozen_postprocess_20261030_v1';FA=B/'runs/parameter90_violation_frozen_saved_audit_20261030_v1'
TAG='RL_COMPLETE91_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
full=read(V/'REVIEW.json');loss=read(V/'loss/REVIEW.json');interpret=read(D/'INTERPRETATION.json');follow=read(O/'REVIEW.json');observed=read(D/'WATCH_REVIEW.json')
assert all(x['passed'] for x in [full,loss,interpret,follow,observed,read(D/'INTERPRETATION_SAVED_REVIEW.json'),read(D/'TERMINAL_SAVED_REVIEW.json'),read(D/'CHANGED_CASES_REVIEW.json'),read(D/'COMPLETE91_BINDING_REVIEW.json')])
assert observed['complete_reviews_ready'] and read(V/'FINISHED.json')['completed'] and read(O/'FINISHED.json')['passed']
for folder in (D,V,O):
 plots=read(folder/'PLOT_INSPECTION.json');assert plots['actual_visual_inspection']
 for x in plots['plots']:assert x['inspected'] and sha(x['path'])==x['sha256']
completed=read(T/'LAUNCH.json')['jobs']+[read(T/'MONITOR_LAUNCH.json'),read(O/'PROCESS.json')]
for j in completed:
 p=Path('/proc',str(j['pid']),'stat')
 if p.exists():
  f=p.read_text().rsplit(')',1)[1].split();assert f[0]=='Z' or f[19]!=str(j.get('start',j.get('proc_start_ticks')))
identities=[]
jobs=read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(FP/'PROCESS.json')]
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]+[(j['pid'],j['start']) for j in jobs]:
 p=Path('/proc',str(pid));s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==str(start);identities.append(dict(pid=pid,start=s[19],state=s[0]))
frozen={}
for m in full['methods']:
 assert read(T/m/'train/FINISHED.json')['status']=='stopped_at_complete_cycle';assert not (F/m/'FAILURE.json').exists()
 frozen[m]=read(F/m/'PROGRESS.json');assert read(F/m/'STARTUP_REVIEW.json')['passed']
assert not (F/'REVIEW_FAILURE.json').exists() and not list(FP.glob('FAILURE*'))
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'WATCH_PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=identities,frozen90=frozen,gpu=gpu,training91_completed=True,original91_archive_and_fixed_followup_completed=True,goal='active',automatic92=False))
files=set()
for folder in (D,V,O):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.npz','.png','.log'} and p.stat().st_size<10_000_000:files.add(p)
for p in F.rglob('*.json'):
 if len(p.relative_to(F).parts)<=2:files.add(p)
for m in full['methods']:
 for n in ('REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json'):files.add(T/m/n)
 for n in ('FINISHED.json','PROGRESS.json','EXECUTION.json'):files.add(T/m/'train'/n)
 for p in (B/'runs/parameter_violation_cycle91_archive_20261030_v1'/m).glob('*.json'):files.add(p)
files.update(T.glob('*.json'))
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_VIOLATION91_PROGRESS_20261030'/n)
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/PLAN.json')
files.add(B/'runs/parameter_history88_90_reward_stability_20261030_v1/REVISION_BOUNDARY_90.json')
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/EARLY_WINDOW_FAILURE_91.json')
files.add(B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json')
for item in read(D/'CHANGED_CASES_REVIEW.json')['cases']:
 for endpoint in item['pair'].values():files.add(Path(endpoint['source']['path']))
for m in full['methods']:files.add(T/m/'train/episodes.jsonl')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete91 all90 outcomes, full loss/health, six changed pairs, fixed87 terminals, four actual plots and original90-92 necessary-condition failure. Frozen90 continues; all historical failures retained. Large checkpoints/raw remain SSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)

result_rows='\n'.join(f"| {m} | {x['steps']} | {x['new_transitions']} | {x['task']}/30 | {x['strict']}/30 | {x['reward_mean']:.12f} | `{x['checkpoint_sha256']}` |" for m,x in full['methods'].items())
loss_rows='\n'.join(f"| {m} | {x['stats']['agent_train/q_loss']['first1000_mean']:.9f} → {x['stats']['agent_train/q_loss']['last1000_mean']:.9f} | {x['stats']['agent_train/q_loss']['maximum']:.9f} | {x['stats']['agent_train/actor_loss']['first1000_mean']:.9f} → {x['stats']['agent_train/actor_loss']['last1000_mean']:.9f} |" for m,x in loss['methods'].items())
text=f'''# 完整第91轮结果、90→91变化与固定终端诊断（2026-10-30）

Goal active，未达到全部方法 reward 平稳且 loss 健康。第91轮三路训练、归档、完整 review/health/loss 和固定87终端跟踪已正常完成，不能重启旧作业。当前第90轮冻结全90评测及其后处理继续。没有登记或派发92，没有启动冻结91或 Direct34。

## 来源与恢复位置

实际计算主机 `{socket.gethostname()}`；共享SSD根 `{B}`，解释器 `{B}/env/bin/python`。本轮实际 query/fetch/read 的 main `{remote['main']}`、baseline `{remote['baseline']}`，收尾再次核对，两分支未变；baseline既有开发比较不能替代指定ESN。本轮遵循 [sii-research-sync](../skills/sii-research-sync/SKILL.md)。

- 训练与实际 execution/registration：`{T}`，训练源码 `{B}/runtime/violation91_continuation_20261030_v1`，运行时依赖 `{B}/runtime/source_train17_clock`。版本、seed、源与MJB hash沿原登记，未更换解释器或模型。
- 完整 checkpoint：`{B}/runs/parameter_violation_cycle91_archive_20261030_v1/<method>/cycle_00091.pt`；完整 review `{V}`。
- 本轮分析与保存源码：`{D}`，主要入口 `interpret91.py`、`changed_cases.py`、`assess_adjacent.py`、`terminal_saved_review.py`、`save_complete91.py`。
- 固定87终端跟踪：`{O}`；冻结90 `{F}`，后处理 `{FP}`。
- 主恢复说明 [RL_RECOVERY75_PARTIAL_TO76_20261029.md](RL_RECOVERY75_PARTIAL_TO76_20261029.md)。所有文件必须按记录hash及 FINISHED/REVIEW 核验，不能仅由文件名推断完成。

## 完整91结果

| 方法 | 累计steps | 本轮新增 | Task | Strict | mean reward | checkpoint SHA256 |
|---|---:|---:|---:|---:|---:|---|
{result_rows}

各方法均30条完整55秒、41,250新transition、0安全中止。全部旧replay字段及history/violation列精确保留；新current/next52、raw/mixed动作核验通过。基于原物理interval journal和冻结reward实现重建所有新reward，最大误差0；这不等于独立重跑每个物理子步。

原52维critic/replay、49维actor、clock49、连续history50、raw bit51=`float(raw_preaction_peak > .0002)`保持；canonical48信息、冻结物理/MJB、Task/Strict gate、filter、执行器限制、dt5e-5不改。append-only4m replay及23/47历史marker、terminal128、batch65536、UTD1、原LR/reward/masks及学得的history/violation权重、Adam和RNG保持，没有推广离线拟合权重。

## Loss与健康诊断

| 方法 | critic首1000→末1000均值 | critic最大值 | actor首1000→末1000均值 |
|---|---:|---:|---:|
{loss_rows}

完整loss原字节及保存标量均值独立复算通过。实际查看 loss 图：阻抗持续密集尖峰且尾部抬升；导纳约35k处晚期尖峰；VMC早期孤立尖峰；三路actor均值上移。有限值及单轮结束不能替代健康收敛结论。

Health inbag terminal MAE 为I .252393186 / A .220689373 / V .128191282，最大误差35.96883/7.57797/8.97056；抽样TD MAE .228401688/.209677976/.144344178。诊断未改变网络；health实际图及loss实际图核验收据在 `{V}/PLOT_INSPECTION.json`，覆盖底层早期 `plot_viewed=false` 状态。

## 同52协议90→91全部90条件对照

配对严格核对除continuation外的协议相同，包括violation amendment。全部90条件reward分项、保存端点聚合及独立算术通过，实际图 `training90_91_all90.png` 已查看；这是在线训练描述性对照，不是独立动力学复跑或因果证明。

I mean变化+1.825131070，唯一Task/Strict增加为active_long_train_0000。A mean变化−1.774648146：Task增加short0900/long0300，失去long0200/long0900；Strict还失去short0600，因此Strict增加2、减少3。V mean变化−.002760453，Task/Strict集合不变。

六个发生标签变化的方法/条件均绑定原90、91 rollout summary及hash：I long0000原90在35.08秒发生global penetration 97.912589mm安全中止（external .046986mm），91完整并双成功，global .177493mm/external .091466mm；原中止保留。A short0600仍Task成功，但ball–link6 external穿透由.191335582增至.223731156mm，超过冻结.2mm门，Strict退化。A short0900由lift到retreat、long0300由carry到retreat；long0200/long0900由retreat到carry。证据 `CHANGED_CASES_REVIEW.json`，不把阶段标签变化当成独立因果解释。

## 原90–92窗口必要条件已经失败

原方案5%相邻门槛、nearzero1、seed2026102861、5000 bootstrap计划均未改。90→91相对变化I .4251160009870729、A .20829213354108633、V .000964835764664803。I/A已经违反原窗口必要条件，未来92不能修复这次已观察到的相邻违反；V仅此相邻不失败，不代表完整窗口通过。

准确90、91实际steps/reward/loss输入绑定均通过，保留90 I只有40,752新步及安全中止，不假定所有方法每轮都41,250。新追加 `{B}/runs/parameter_violation90_92_reward_stability_20261030_v1/EARLY_WINDOW_FAILURE_91.json` 固定原PLAN和本轮判定hash；原PLAN未改，原窗口REGISTRATION/REVIEW仍未生成，没有完整三轮/bootstrap或首尾窗口统计。

## 固定87全部7813终端跟踪91

I2605/A2604/V2604，原masks及all5 critics不变。保存87/88/89/90预测，恢复原生已学91；全learner/replay/RNG/checkpoint不变。87–91保存masked SSE/MSE、all-row SSE和mask数已独立以标量math.fsum复算通过；实际五端点图已查看，收据 `TERMINAL_SAVED_REVIEW.json` 和 `{O}/PLOT_INSPECTION.json`。

masked总SSE90→91：I3362.887087→2254.573677（−32.9572%），A1550.062353→1944.968772（+25.4768%），V1722.701171→676.730002（−60.7169%）。I critic1/3退化；A只有critic3改善；V critic4退化。all-row SSE中I/A所有critic下降，V critic2增加744.923368，其余下降。保留所有退化；已见终端拟合不代表策略安全、泛化或收敛。

原check91路径类型错误及只作Path转换的v2修复保留（`CHECK91_FAILURE_AND_FIX.json`），实际3 startup/27拒绝检查已通过。本轮save builder初次模板按列表匹配实际tuple而失败，发生在执行保存脚本之前；`SAVE_BUILDER_FAILURE.json` 保留，没有影响科学源码或作业。

## 正在运行与下一阶段

原91 learners689755/689761/689763、归档689765和终端等待1706570均通过实际FINISHED判定为正常结束；1320.223秒/133次观察覆盖完成边界。保存时冻结90已完成条件数 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`，原evaluator283421/283428/283430、collector283433和postprocessor292743身份存活。继续原有限全90、seed2026102638、0updates任务；原截止为1793395746.736+21600，不延长、不重复派发。完整raw审计、88→90配对及最终不变性仍待。

下一阶段须根据完整91的混合进退、I/A原窗口必要条件失败及loss/终端退化，单独选择并登记有限训练或诊断，再通过实际恢复核验后执行；不把完成91或GPU占用要求当作自动启动92的依据。保留原5%失败窗口，不能更换窗口来抹去失败。Direct33数值收敛已接受，冻结33全部30 Task/Strict0/0；旧28保存动作精确但最终内存不变性缺失，恢复后2条完整不变性通过。不得把任务成功附加为Direct数值收敛的新要求，也不为占用启动34。指定ESN仍缺，不重复询问或用另一主机模型替代。

所有历史失败窗口、partial75、74–76不可评估、79/90安全中止、halfstd否决及软件失败均保留；本报告不覆盖旧记录。

## GPU与保存范围

用户明确要求科学工作完成后也继续GPU保载。原v7 supervisor97370及workers97399–97402仍运行，threshold50%、target70%、min duty.7，CPU4–6。不得创建STOP；当前守护不因科学任务结束退出，但不是重启自启服务。

本轮自WATCH_PLAN起{gpu['samples']}个守护样本、跨度{gpu['elapsed_s']:.3f}秒，四卡最低{gpu['minimum']}%、低于50%次数{gpu['below50']}，保存末次{gpu['last']}%。包括合成保载，不能称纯科学吞吐；采样不保证每瞬时，旧v7 warmup0及v6的31/33/44低值仍保留。

本轮共享SSD归档 `{receipt['archive']}`，{receipt['members']}成员、{receipt['bytes']}字节、SHA256 `{receipt['sha256']}`，全部tar成员及Python AST已核验。清单在 `docs/evidence/{TAG}/MANIFEST.json`，收据 [{TAG}_SAVE.json]({TAG}_SAVE.json)。大型checkpoint/replay/raw仍在共享SSD，HDD配额已满，只在原位置原地更新254字节LATEST指针，不是HDD或arm1全备份。Git index/commit逐文件字节核验与实际push/remote结果在外部 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`，以实际后续收据为准。
'''
p=R/'docs'/(TAG+'.md')
with p.open('x') as f:f.write(text)
entry=f'''## 2026-10-30 — 完整91审计完成；原90–92 I/A必要条件失败

- [交接](docs/{TAG}.md)。三路各30完整55秒/41250新增/0abort，旧replay及新52/action/reward精确；Task/Strict18/17、14/13、17/17。全loss仍有尖峰、I尾部抬升，actor均值上移，未收敛；原91/archive/固定终端等待正常结束勿重启。
- 全90训练对照及六个标签变化案例绑定通过，原90 I97.91mm安全中止和A short0600跨.2mm失败保留。原90–92相邻I42.5116%/A20.8292%违反5%必要条件，V .09648%仅一对不失败；准确90/91绑定通过，原PLAN未改、无完整窗口/bootstrap或自动92/Direct34。
- 固定87全部7813终端/all5跟踪91完成，masked SSE I−32.96%、A+25.48%、V−60.72%，各critic退化均保留；独立保存算术和四实际图通过。冻结90原评测/后处理继续，完成数{ {m:x['completed_conditions'] for m,x in frozen.items()} }，最终全90/raw/paired待。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}逐成员核验，HDD仅254字节指针，非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已实际query/fetch/read，发布见收据；Goal active，无子agent，全部历史失败及指定ESN缺失保持。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,frozen=frozen)))
