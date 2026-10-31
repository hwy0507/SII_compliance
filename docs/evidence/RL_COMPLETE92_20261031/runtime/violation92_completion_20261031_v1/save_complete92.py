from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
T=B/'runs/parameter_violation_cycle92_20261030_v1';V=B/'runs/parameter_violation_cycle92_review_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';O=B/'runs/violation92_fixed87_terminal_followup_20261030_v1'
FD=B/'runtime/violation90_frozen_dispatch_20261030_v1';FP=B/'runtime/violation90_frozen_postprocess_20261030_v1';FA=B/'runs/parameter90_violation_frozen_saved_audit_20261030_v1'
TAG='RL_COMPLETE92_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
assert read(S/'REVIEW.json')['passed'] and read(S/'SAVED_ARITHMETIC_REVIEW.json')['passed']
full=read(V/'REVIEW.json');loss=read(V/'loss/REVIEW.json');interpret=read(D/'INTERPRETATION.json');follow=read(O/'REVIEW.json');observed=read(D/'WAIT_REVIEW.json')
assert all(x['passed'] for x in [full,loss,interpret,follow,read(D/'INTERPRETATION_SAVED_REVIEW.json'),read(D/'TERMINAL_SAVED_REVIEW.json'),read(D/'CHANGED_CASES_REVIEW.json')])
assert observed['outcome']=='ready' and read(V/'FINISHED.json')['completed'] and read(O/'FINISHED.json')['passed']
for folder in (D,V,O,B/'runs/parameter_violation90_92_reward_stability_20261030_v1'):
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
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'WAIT_PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=identities,frozen90=frozen,gpu=gpu,training92_completed=True,original92_archive_and_fixed_followup_completed=True,goal='active',automatic93=False))
files=set()
for folder in (D,V,O):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.npz','.png'} and p.stat().st_size<10_000_000:files.add(p)
for p in F.rglob('*.json'):
 if len(p.relative_to(F).parts)<=2:files.add(p)
for m in full['methods']:
 for n in ('REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json'):files.add(T/m/n)
 for n in ('FINISHED.json','PROGRESS.json','EXECUTION.json'):files.add(T/m/'train'/n)
 for p in (B/'runs/parameter_violation_cycle92_archive_20261030_v1'/m).glob('*.json'):files.add(p)
files.update(T.glob('*.json'))
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_VIOLATION92_PROGRESS_20261030'/n)
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/PLAN.json')
files.add(B/'runs/parameter_history88_90_reward_stability_20261030_v1/REVISION_BOUNDARY_90.json')
files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1/EARLY_WINDOW_FAILURE_91.json')
files.add(B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json')
for item in read(D/'ABORT_REVIEW.json')['sources']:files.add(Path(item['path']))
S=B/'runs/parameter_violation90_92_reward_stability_20261030_v1'
for p in S.iterdir():
 if p.is_file() and p.suffix in {'.py','.json','.png','.diff'}:files.add(p)
files.add(B/'runtime/violation92_stability_ready_20261030_v1/bind_inputs.py')
files.add(B/'runtime/violation92_stability_ready_20261030_v1/BINDING_PLAN.json')
for item in read(D/'CHANGED_CASES_REVIEW.json')['cases']:
 for endpoint in item['pair'].values():files.add(Path(endpoint['source']['path']))
for m in full['methods']:files.add(T/m/'train/episodes.jsonl')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete92 all90 outcomes, full loss/health, changed labels and safety abort, fixed87 terminal arithmetic, actual inspected plots and original90-92 full window. Frozen90 continues; historical failures retained. Large checkpoints/raw remain shared SSD.'))
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
stability=read(S/'REVIEW.json');terminal=read(D/'TERMINAL_SAVED_REVIEW.json');counts={m:v['completed_conditions'] for m,v in frozen.items()}
stability_rows='\n'.join(f"| {m} | {x['adjacent_relative_mean_changes'][0]*100:.6f}% | {x['adjacent_relative_mean_changes'][1]*100:.6f}% | {x['endpoint_relative_mean_change']*100:.6f}% | {x['descriptive_five_percent_check']} |" for m,x in stability['methods'].items())
terminal_rows='\n'.join(f"| {m} | {x['total_masked_sse91']:.6f} | {x['total_masked_sse92']:.6f} | {x['relative_total_change']*100:+.4f}% |" for m,x in terminal['summary'].items())
text=f"""# 完整第92轮、原90—92稳定性与固定终端审查（2026-10-31）

完整92训练、归档、回放/health/loss审查及固定87终端比较均已正常完成，旧任务不要重启。原90—92窗口：阻抗/导纳未通过5%检查，VMC通过该reward检查；全方法 reward 平稳且 loss 健康尚未成立，Goal active。当前原冻结90及其后处理继续。无自动93、冻结92或Direct34派发。

## 来源与恢复

实际主机 `{socket.gethostname()}`，共享SSD根 `{B}`，解释器 `{B}/env/bin/python`。本轮按 `skills/sii-research-sync/SKILL.md` 实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，无子agent。计算从10月31日UTC开始；运行目录保留原10月30日run-id，不重命名历史产物。

训练 `{T}`；原源码 `{B}/runtime/violation92_continuation_20261030_v1`，审查源码 `{B}/runtime/violation92_review_20261030_v1`；版本、seed、源/MJB hash与EXECUTION保持原登记。完整checkpoint在 `{B}/runs/parameter_violation_cycle92_archive_20261030_v1/<method>/cycle_00092.pt`，完整审查 `{V}`。本轮分析源码及证据 `{D}`，固定87终端 `{O}`，原稳定性 `{S}`。主要恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。

## 完整92结果

| 方法 | 累计steps | 新增transitions | Task | Strict | mean reward | checkpoint SHA256 |
|---|---:|---:|---:|---:|---:|---|
{result_rows}

I为29完整55秒+1原安全中止，A/V各30完整55秒。全部旧replay字段/history/violation保留精确，新current-next52/raw-mixed action精确，原interval journal与冻结reward实现重建所有新增reward的最大误差0。这不是独立重跑每个物理子步。

原critic/replay52、actor49、clock49/history50/raw bit51保持；canonical48信息、冻结physics/MJB、Task/Strict gate、filter/执行器/dt5e−5保持。4m append-only replay与23/47历史marker、terminal128/batch65536/UTD1/原LR reward masks及已学history/violation权重、Adam/RNG/双架构标记保持；没有引入离线拟合权重。

## Loss与完整窗口

| 方法 | critic首1000→末1000均值 | critic最大值 | actor首1000→末1000均值 |
|---|---:|---:|---:|
{loss_rows}

实际loss与health图已查看并按SHA绑定。I均值下降但仍密集critic尖峰；A约末段存在尖峰；V间歇尖峰簇。三路actor均值上移。有限值和局部均值下降不足以宣布健康收敛。

原90—92 PLAN/audit/review_saved字节未改，绑定了全部90/91/92完整回放/loss/health及实际图、查看记录、原plan、早期失败引用；保持nearzero1、5%、seed2026102861、5000分层条件bootstrap和全部30分母/实际中止长度。原audit、独立保存标量复算通过，实际稳定性图已查看。

| 方法 | 90→91相对变化 | 91→92相对变化 | 90→92端点相对变化 | 原5%检查 |
|---|---:|---:|---:|---|
{stability_rows}

I端点只变1.53%不能掩盖中间大幅波动；A最后相邻对约.123%不能抹去原窗口失败。V通过此reward条件，未在本轮验收其联合loss健康收敛。原 `EARLY_WINDOW_FAILURE_91.json` 与此前全部失败窗口保持。bootstrap区间只反映同组条件组成敏感性，非独立训练seed或冻结策略泛化；`review_saved.py`独立复算标量、不独立重算bootstrap区间，限制保留。

## 91→92变化与安全中止

全部90个方法/条件均对照，reward项分解与保存算术通过，实际图已查看。I平均reward−1.890877251，唯一Task/Strict损失为long0000。A平均+0.012699247但long0200/long0500获得成功、short0200/short0900失去成功；均值接近不表示行为不变。V平均+0.047626029，标签保持。五组变化已与两轮实际rollout摘要/model hash绑定；这是描述性算术，不是因果解释。

I long0000在687动作/27.48000000035秒中止，global penetration87.966473mm，最坏pair为office_v5_corner_top/target_object_geom；external peak .080090363mm，最后current/terminal raw external bit均0。前91同条件Task/Strict成功、global peak .177492913mm。687完整转移和reward−40.543700551已核对，终端失败项保留；全局目标物体/台面失败不被现有external bit覆盖，不能删除失败、改物理或门槛。`ABORT_REVIEW.json`只审原始记录，无独立动力学复现或checkpoint replay断言。

## 原固定87终端比较

原7813终端/all5/原masks及52 raw输入保持，完整learner/replay/RNG不变；原87–92保存预测的所有masked/all-row SSE与MSE逐标量复核通过，实际图已查看。

| 方法 | 91 masked SSE总和 | 92 masked SSE总和 | 相对变化 |
|---|---:|---:|---:|
{terminal_rows}

零起始critic索引：I critic2退化；A critics0/2/4退化；V critics0/4退化。全部15个critic的all-row SSE下降。固定已见终端拟合仅是诊断，不是策略安全、泛化或额外数值验收门槛。

## 运行、GPU与后续

本轮事件等待实际持续{observed['last']['elapsed_s']:.3f}秒/{observed['samples']}样本，初始105身份实际存活，记录了95个原训练/采样/archive/终端等待进程正常结束。没有因观测超时重启或延长任务预算。原冻结90及collector/postprocessor、原guard共10身份仍存活；冻结完成数 `{counts}`，各总30。全90/raw/88→90 paired及最终内存不变证明仍待。

GPU {gpu['samples']}样本，min `{gpu['minimum']}`%，低于50次数 `{gpu['below50']}`，末样本 `{gpu['last']}`%。原 `/tmp/sii_gpu_util_guard_20261030_v7` supervisor97370/worker97399–97402继续，threshold50/target70/min duty.7；按用户要求科学结束仍保活。含synthetic guard占用，不等于科学吞吐或每瞬时保证；历史warmup0/v6低值保持。不是重启服务。

下一步依据完整92快照调查残余critic尖峰和actor漂移，同时完成原冻结90；任何下一轮训练须单独登记科学决定，当前没有自动93。Direct33原数值验收保持，冻结全30 Task/Strict0/0；旧28缺最终内存证明、恢复2完整不变。不把task成功追加为数值收敛要求。指定ESN仍缺，不替换其他主机模型。partial75、不可评74–76、79/90/92安全中止、halfstd拒绝和全部软件失败均保留。

## 保存

共享SSD `{archive}`：{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，全部tar成员逐字与清单核对、Python AST通过。manifest在 `docs/evidence/{TAG}/MANIFEST.json`；后续index/commit/blob核验及正常push实际远端收据在 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。

HDD配额满，现有 `sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md`仅原地更新、严格254字节并回读。大checkpoint/raw/replay/runtime仍共享SSD，非HDD或arm1全量备份。
"""
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f"""## 2026-10-31 — 完整92与原90—92窗口已审；I/A失败保留

- [交接](docs/{TAG}.md)。I40562新增/29完整+1安全中止，A/V41250各30完整；旧replay与新52/action/reward精确，Task/Strict17/16、14/13、17/17。I long0000在687动作/27.48s全局87.97mm中止，external bit0不覆盖该失败。全loss仍有尖峰/actor上移，未收敛。
- 原90—92固定5%/5000bootstrap实际完成并保存算术/实际图核验；I/A失败、V reward条件通过，非联合健康收敛。全91→92及五组标签变化绑定通过；固定87全部终端masked SSE I−54.37%、A−5.39%、V+22.61%，单critic退化保留，0updates。
- 原92/archive/终端等待正常完成勿重启，无自动93/Direct34；原冻结90继续，完成{counts}，最终全90/raw/paired待。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍守护。
- SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，发布见收据。Goal active，无子agent；全部历史失败/Direct原结论/指定ESN缺失保持。

"""
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in full['methods'].items()})))
