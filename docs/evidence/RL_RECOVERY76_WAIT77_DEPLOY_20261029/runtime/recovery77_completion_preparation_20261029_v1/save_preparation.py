from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'repository/SII_compliance';P=B/'runtime/prepare_recovery77_20261029_v1';RUN=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';LOSS=B/'runs/parameter_recovery77_loss_20261029_v1';O=B/'runtime/recovery76_verified_wait_0625_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY76_WAIT77_DEPLOY_20261029'
def read(p):return json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def state(j):
 q=Path(f'/proc/{j["pid"]}/stat');f=q.read_text().rsplit(')',1)[1].split() if q.exists() else None
 return dict(pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],live=bool(f and f[19]==j['proc_start_ticks'] and f[0]!='Z'))
assert (O/'FINISHED.json').exists()
for n in ['FINAL_SOURCE_REVIEW.json','LAUNCH_SOURCE_REVIEW.json','decision77.py.REJECTION.json','launch77.py.REJECTION.json','deploy_loss77.py.REJECTION.json']:assert read(D/n)['passed']
for x in read(D/'LAUNCH_SOURCE_REVIEW.json')['files']:assert sha(Path(x['path']))==x['sha256']
assert not (D/'DECISION77.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle77_20261029_v1/LAUNCH.json').exists() and not (LOSS/'LAUNCH.json').exists()
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],archive=state(read(RUN/'MONITOR_LAUNCH.json')),prepare77=state(read(P/'LAUNCH.json')),archive76_finished=(RUN/'ARCHIVE_REVIEW_FINISHED.json').exists(),prepare77_finished=(P/'FINISHED.json').exists())
assert not (RUN/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (P/'FAILURE.json').exists()
for j in read(RUN/'LAUNCH.json')['jobs']:
 folder=RUN/j['controller']/'train';v=state(j);v.update(method=j['controller'],progress=read(folder/'PROGRESS.json'),finished=(folder/'FINISHED.json').exists());assert not (folder/'FAILURE.json').exists()
 if not v['live']:assert v['finished'] and read(folder/'FINISHED.json')['status']=='stopped_at_complete_cycle'
 snap['learners'].append(v)
start=read(P/'FINAL_SNAPSHOT.json')['time'];rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=start];assert rows and time.time()-rows[-1]['time']<15
for pid in [read(G/'LAUNCH.json')['pid'],*read(G/'LAUNCH.json')['workers'].values()]:assert Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
snap['guard']=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True);write(D/'FINAL_SNAPSHOT.json',snap);(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
sources=[p for folder in [D,LOSS,O] for p in folder.iterdir() if p.is_file() and p.suffix in ['.json','.jsonl','.py','.diff','.log']]
for p in sorted(sources):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);assert sha(q)==sha(p)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
write(E/'MANIFEST.json',dict(files=manifest,time=time.time(),large_artifacts_excluded=True))
A=B/'repository'/TAG;A.mkdir(exist_ok=False);tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),member_bytes_and_python_ast_verified=True,large_artifacts='Shared SSD; no full HDD/arm1 backup');write(A/'RECEIPT.json',receipt);write(R/'docs'/(TAG+'_SAVE.json'),receipt)
obs=read(O/'FINISHED.json');stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat();steps={x['method']:x['progress']['steps'] for x in snap['learners']};states={x['method']:dict(live=x['live'],finished=x['finished']) for x in snap['learners']}
doc=f'''# 恢复76连续观察与77完整审查及派发准备

{stamp}，Goal active。本轮完成新完整loss/续训证据检查/派发源码准备及原进程连续观察，属于progress。当前76 steps {steps}，状态{states}；完整76归档结束={snap['archive76_finished']}，77仅恢复检查结束={snap['prepare77_finished']}。未启动77训练。Direct33原训练条件数值结论及Task/Strict0/0保持，不启动34，整体收敛仍未证明。

共享SSD `{B}`；主机`{socket.gethostname()}`；Python env/bin/python。原75中断、全部保留partial75学习状态和76新物理周期语义保持；30×55秒/最多41250新增、4m append/markers23与47、terminal128、batch65536、UTD1、LR/reward/physics/gates全不变。

新`runs/parameter_recovery77_loss_20261029_v1`只有审查源码和SOURCE_REVIEW，尚无PLAN/LAUNCH/结果。原49–74和76历史保留，新增完整77；75路径显式拒绝。配对改为完整76→77，保留历史75缺口说明。原full loss/连续步号/有限性/完整30条件、全部90reward配对和保存值独立算术保持；路径74/76/77与75拒绝、AST提取完整历史和配对周期检查通过，原0.2mm门槛不变。新waiter将先核source hash再等待真实原77进程终态，当前未运行。

新`runtime/recovery77_completion_preparation_20261029_v1/decision77.py`要求完整76归档/replay/reward/health、全loss/保存算术、全180标签、V/A全2244旧+30新终端及实际四图收据，准确77 CHECK_ONLY和实际解释文件CONTINUATION_REASON.txt。重新核所有历史DECISION75与恢复76证据hash，绑定原74–76中断事实及准确76–78 PLAN，不要求尚未来临窗口结果，不改变5%/nearzero1规则。

`launch77.py`要求已明确写出的DECISION77及所有证据与源码hash一致，核原76退出及精确checkpoint后，才启动唯一有限77、实际startup、archive/health和完整loss等待；无自动78、无Direct34。`deploy_loss77.py`只有真实77三learner身份确认后才派发。真实当前不完整76、缺DECISION77、缺77 LAUNCH三个调用全部拒绝，无训练/结果副作用。当前CONTINUATION_REASON/DECISION77尚未写，不能把代码准备当续训决定或科学通过。

原15个训练/归档/诊断/77仅恢复准备/GPU进程的连续观察已结束：{obs['samples']}样本/{obs['elapsed']:.3f}秒，全部原身份持续live={obs['all_original_identities_live']}。起点{obs['first_steps']}，终点{obs['last_steps']}。如出现BOUNDARY_REQUIRES_INSPECTION，代表原进程终态须结合FINISHED检查，不据观察超时重启科学；实际状态见上表和FINAL_SNAPSHOT。

本窗口guard {len(rows)}样本，四卡最低{snap['guard']['minimum']}%、低于50次数{snap['guard']['below50']}。含合成保底负载，科学完成后继续；此前容器空档与预热保留，非跨重启服务。

开工实际fetch/read main6492ab17和baselinef6e8f8c，非RL实际球示范运动报告及85/108状态保留；不操作另一主机。源码基线{receipt['source_base_commit']}，遵循sii-research-sync，无子agent。此前push缺HTTPS认证，当前本地/共享SSD保存不冒充远端发布。

共享SSD证据 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`；逐成员与AST核验。[收据]({TAG}_SAVE.json)。大checkpoint/replay/raw仍SSD，非HDD/arm1全备份，HDD LATEST原主恢复文档已补本报告链接。

下一步按真实76完成状态读取全审/四图，审查恢复77 CHECK_ONLY；只有实际证据支持继续才写CONTINUATION_REASON与DECISION77并派发。原76–78窗口、全部历史失败和GPU保载保持，Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n后续最新：[76连续观察与77完整loss/派发准备]({TAG}.md)。77训练未启动，原目标与GPU保载继续。\n')
entry=f'''## 2026-10-29 — 恢复76观察与77完整审查/派发准备

- [交接](docs/{TAG}.md)。77全loss保留49–74/76历史、75拒绝、新76→77配对；独立算术/原gate保持，路径及AST检查通过。新decision/launcher绑定完整76全审/实际图/准确77恢复/历史证据/原76–78PLAN，实际不完整76、缺DECISION77、缺77LAUNCH拒绝，无新训练或决定。
- 原观察{obs['samples']}样本/{obs['elapsed']:.3f}s，全部原身份live={obs['all_original_identities_live']}，当前steps{steps}；终态须按FINISHED核验，不重启科学。guard{len(rows)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}，科研完成仍保载。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}已核，非HDD/arm1全备份；main6492ab17/baselinef6e8f8c已读，认证发布待，Goal active、Direct34false。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':a,b=s.split('\n',1);p.write_text(a+'\n\n'+entry+b.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[76观察与77派发准备](docs/{TAG}.md)。77尚未训练，按完整76证据接续；GPU保底继续，Goal active。**\n\n'+p.read_text())
print(json.dumps(receipt));print(json.dumps(snap))
