from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';DIS=B/'runtime/recovery78_completion_preparation_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY77_COMPLETE78_RUNNING_20261029'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 q=Path(f'/proc/{j["pid"]}/stat');f=q.read_text().rsplit(')',1)[1].split() if q.exists() else None
 return dict(pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],live=f is not None and f[19]==j['proc_start_ticks'] and f[0]!='Z')
assert read(D/'FINISHED.json')['passed'];assert read(RUN/'startup/REVIEW.json')['passed'];assert read(DIS/'DECISION78.json')['passed']
for x in read(DIS/'DECISION78.json')['evidence'].values():assert sha(x['path'])==x['sha256']
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],waiters={},goal='active',direct34=False)
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller'];assert not (p/'train/FAILURE.json').exists() and not (p/'DRIVER_FAILURE.json').exists();v=live(j);assert v['live'];v.update(method=j['controller'],progress=read(p/'train/PROGRESS.json'),samplers=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert v['samplers']==30;assert read(p/'INITIAL_STATE_REVIEW.json')['passed'];snap['learners'].append(v)
snap['archive']=live(read(RUN/'MONITOR_LAUNCH.json'));assert snap['archive']['live'];assert not (RUN/'ARCHIVE_REVIEW_FAILURE.json').exists()
for n in ['parameter_recovery78_task_labels_20261029_v1','vmc_recovery78_terminal_followup_20261029_v1','admittance_recovery78_terminal_followup_20261029_v1','parameter_recovery78_loss_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1']:
 p=B/'runs'/n;j=read(p/'LAUNCH.json');assert sha(p/'PLAN.json')==j['plan_sha256'];assert not (p/'FAILURE.json').exists() and not (p/'WAIT_FAILURE.json').exists();snap['waiters'][n]=dict(live(j),plan_sha256=j['plan_sha256']);assert snap['waiters'][n]['live']
start=read(DIS/'FINAL_SNAPSHOT.json')['time'];rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=start];assert rows and time.time()-rows[-1]['time']<20 and not (G/'FAILURE.json').exists()
glaunch=read(G/'LAUNCH.json');guard_pids=[glaunch['pid']]+list(glaunch['workers'].values());snap['guard_processes']=[]
for pid in guard_pids:
 q=Path(f'/proc/{pid}/stat');f=q.read_text().rsplit(')',1)[1].split();assert f[0]!='Z';snap['guard_processes'].append(dict(pid=pid,proc_start_ticks=f[19],cmdline=Path(f'/proc/{pid}/cmdline').read_bytes().replace(b'\0',b' ').decode()))
snap['guard']=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True);write(D/'SAVE_SNAPSHOT.json',snap);(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
folders=[D,DIS,B/'runtime/recovery77_health_dependency_fix_20261029_v1',B/'runtime/recovery78_state_check_diagnosis_20261029_v1',B/'runtime/prepare_recovery78_20261029_v1',B/'runtime/recovery77_completion_monitor_20261029_v1']
folders += [B/'runs'/n for n in ['parameter_partial75_recovery_cycle77_review_20261029_v1','parameter_partial75_recovery_cycle78_review_20261029_v1','parameter_recovery77_loss_20261029_v1','parameter_recovery78_loss_20261029_v1','parameter_recovery77_task_labels_20261029_v1','parameter_recovery78_task_labels_20261029_v1','vmc_recovery77_terminal_followup_20261029_v1','admittance_recovery77_terminal_followup_20261029_v1','vmc_recovery78_terminal_followup_20261029_v1','admittance_recovery78_terminal_followup_20261029_v1']]
sources={p for folder in folders for p in folder.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.jsonl','.diff','.log','.png','.npz','.txt'] and '__pycache__' not in p.parts and p.stat().st_size<5_000_000}
for cycle in [77,78]:
 run=B/f'runs/parameter_partial75_recovery_cycle{cycle}_20261029_v1'
 sources.update(p for p in run.iterdir() if p.is_file() and p.suffix in ['.json','.py','.log'])
 for m in ['impedance','admittance','vmc']:
  sources.update(p for p in (run/m).iterdir() if p.is_file() and p.suffix in ['.json','.py','.log'])
  for n in ['FINISHED.json','EXECUTION.json','PROGRESS.json','episodes.jsonl']:
   p=run/m/'train'/n
   if p.exists():sources.add(p)
sources.add(RUN/'startup/REVIEW.json');sources.add(B/'runs/parameter_partial75_recovery_cycle77_archive_20261029_v1/FINISHED.json')
for n in ['PLAN.json','LAUNCH.json','wait.py']:
 p=B/'runs/parameter_recovery76_78_reward_stability_20261029_v1'/n
 if p.exists():sources.add(p)
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();assert len(data)<5_000_000;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
for p in [G/'guard.py',G/'LAUNCH.json',G/'RECOVERY.json',G/'CONTROL.json']:
 data=p.read_bytes();rel=Path('guard_v6')/p.name;q=E/rel;q.parent.mkdir(exist_ok=True);q.write_bytes(data);manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
write(E/'MANIFEST.json',dict(files=manifest,time=time.time(),large_artifacts_excluded=True,active_logs_are_point_in_time_snapshots=True))
A=B/'repository'/TAG;A.mkdir(exist_ok=False);tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),member_bytes_and_python_ast_verified=True,large_artifacts='Shared SSD; no full HDD/arm1 backup');write(A/'RECEIPT.json',receipt);write(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={j['method']:j['progress']['steps'] for j in snap['learners']};stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()
doc=f'''# 完整恢复77审查与78实际续训

{stamp}，Goal active。第77轮科学正常完成，完整审查和两项基础设施故障修复已核验；第78轮三路已实际启动，启动审查通过，当前steps {steps}。本报告取代[原77等待/78准备状态](RL_RECOVERY77_WAIT78_DEPLOY_20261029.md)作为当前状态入口，历史失败均保留。

执行主机 `{snap['host']}`，共享SSD根 `{B}`，解释器 `{B}/env/bin/python`。科学配置仍30条件×55秒、每路每轮41250新增、4m追加回放、历史markers23/47、terminal128、batch65536、UTD1、原学习率/reward/masks/物理/gates。没有Direct34、没有自动79。

## 完整77

|方法|steps|平均reward|Task/Strict（30）|critic首→末1000|critic最大|
|---|---:|---:|---|---|---:|
|阻抗|3194648|-2.342727843|18/17|3.194033→2.548128|33.366371|
|导纳|3196250|-6.820801913|15/15|1.200749→1.180500|67.836517|
|VMC|3197250|-4.622457555|17/16|0.915801→0.848468|44.592030|

三路均30完整55秒、41250新增、无abort；全部旧replay/history保持，新reward全量重算最大误差0，网络/optimizer有限。不能据此判健康loss或收敛：尖峰和actor漂移仍在，完整loss、health及V/A两张终端图均已实际查看并保存收据。导纳总成功数不变但long0200恢复、long0500退化；全部180标签/90reward对独立复核，I/V既有物理/Strict失败保留。I long0000 reward下降2.596544而标签未变。

V/A全部2274旧终端SSE分别3883.440215→1997.718105、2815.605065→2352.728519；并非每条改善，VMC两原focus退化保留。新30贡献分别.08326542724914057/.0036010946824885973，原两分母、完整总体和原focus均保留，无因果归因。health中超过当前冻结alpha上界的sampleQ份额I/A/V为0/.000732421875/.0010742187732830644，诊断不新增收敛门槛。

## 修复与准确恢复

原归档监视器在完整77 checkpoint/reward/replay审查成功后，因缺`diagnose_published_value_bound_20261025`退出。按原76版本逐字补齐helper（SHA2a5b04c7），仅继续缺失health，未重跑科学或完整review。原`ARCHIVE_REVIEW_FAILURE.json`、monitor.log和依赖等待器失败均保留，`runtime/recovery77_health_dependency_fix_20261029_v1/HEALTH_RECOVERY_REVIEW.json`串联修复后完成收据；未来78依赖也已补齐。

后续恢复检查首次失败，原因是补跑环境设置空`CUDA_VISIBLE_DEVICES`，导致`state_dict`看不到已存CUDA RNG。CPU learner的设备可见/隐藏对照只发现`cuda_rng`差异；修正环境后，三路原driver未改，全learner/optimizer/RNG/replay及next65536准确检查和每路9拒绝均通过。原失败log/JSON、初次非零exitcodes均保留于`runtime/recovery78_state_check_diagnosis_20261029_v1`证据链；无训练重启，无绕过状态相等校验。

## 当前78与后续

`{DIS}/DECISION78.json`绑定完整77全部审查/实际图、准确恢复、历史证据、两次故障修复收据及有限理由。原75缺完整终态、不补造数据，旧74–76窗口unassessable；原前瞻76–78 PLAN SHA57b3d6be84b8b384922a35879ddfd5cd1c6e7a6b71b35ca5652c2ddfc8cd4e85及5%/nearzero1/seed2026102855/5000bootstrap/anchor55保持。近零保护不是把reward推离零的目标。

实际训练 `{RUN}`，三learner身份与30sampler、完整state初始核验及startup首批映射/原replay/optimizer/新reward核验通过，见startup/REVIEW.json及本证据SAVE_SNAPSHOT。完整78归档/health、全loss、标签和V/A终端等待器已部署，原76–78窗口保持原PID。新的终端锚点从完整77已审Q与准确checkpoint提取全2304条，无新forward，原focus及两分母保留；78预计全2334条，不冒充旧2274。标签入口对真实未完成78拒绝通过。

Direct33已接受的训练条件数值结论保持，Task/Strict0/0，未启动Direct34；旧冻结29不能认证最新33，最终冻结策略和指定ESN比较仍待，不缩小原Goal。第78轮尚在进行，不能预告reward稳定或loss健康。

## GPU与保存

从上次保存起guard {len(rows)}个5秒间隔样本，四卡最低{snap['guard']['minimum']}%，低于50次数{snap['guard']['below50']}；最后利用率{[x['utilization'] for x in rows[-1]['gpus']]}%。保活原supervisor78710/四worker身份保持，科研全部完成后仍继续。合成负载不计科学吞吐；不能用本窗口掩盖此前容器停机及v6最初两个预热0样本，也不是系统重启自启服务。

实际fetch/read远端main b1deda6593c6b4bc76a76b89e30b5a6fc4998178、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，另一主机非RL99/108新增保留，没有操作其进程，无子agent。源基线 `{receipt['source_base_commit']}`；发布以最终push收据为准，既有HTTPS认证缺失。

本轮共享SSD包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员原字节和Python AST核验；[归档收据]({TAG}_SAVE.json)。完整checkpoint/replay/轨迹仍共享SSD，非HDD或arm1全量备份；HDD现有LATEST入口指向主恢复文档。

下一步持续观察原78及GPU，完成78全审并实际查看图，读取原76–78统计，按原reward稳定与loss健康要求判定。观察器超时或审计失败不重启科学；如需修复保留失败链。不要重复运行本轮launcher，不启动自动79。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 完整77、诊断/恢复环境修复与78实际续训

- [交接](docs/{TAG}.md)。完整77三路30×55/41250、旧回放保持/新reward0误差；全loss/180标签/90reward对/health/2274+30终端和实际图全审，尖峰/actor漂移与导纳long0200改善、long0500退化保留，未收敛。
- 缺health依赖按76原字节补齐，仅接缺失审查；空CUDA可见性导致仅恢复RNG误判已对照定位，原driver不变、三路准确state/replay/next65536和实际78startup通过。原失败链保留，无科学重启。78当前steps{steps}，各30sampler，全loss/标签/2304终端锚点后续及原76–78窗口已部署，Goal active、无自动79/Direct34。
- guard{len(rows)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}，科研完成仍保载、合成非吞吐。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐成员/AST核验，非HDD/arm1全备份；mainb1deda65/baselinef6e8f8c已读，认证发布待，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':a,z=s.split('\n',1);p.write_text(a+'\n\n'+entry+z.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[完整77审查与78实际续训](docs/{TAG}.md)。完整78训练/审查和原76–78/GPU保活继续，Goal active，勿重复启动。**\n\n'+p.read_text())
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n更新：[完整77审查与78实际续训]({TAG}.md)。两项基础设施失败已保留并修复，原78训练和GPU保活继续。\n')
print(json.dumps(receipt));print(json.dumps(snap))
