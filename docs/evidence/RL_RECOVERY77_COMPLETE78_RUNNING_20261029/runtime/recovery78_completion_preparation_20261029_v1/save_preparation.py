from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;P=B/'runtime/prepare_recovery78_20261029_v1';O=B/'runtime/recovery77_completion_verified_wait_20261029_v1';RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY77_WAIT78_DEPLOY_20261029'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 q=Path(f'/proc/{j["pid"]}/stat');f=q.read_text().rsplit(')',1)[1].split() if q.exists() else None
 return dict(pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],live=f is not None and f[19]==j['proc_start_ticks'] and f[0]!='Z')
f=read(O/'FINISHED.json');assert f['samples']==21 and f['all_original_identities_live'] and f['elapsed']>=600
assert read(D/'PREPARATION_REVIEW.json')['passed'] and read(D/'DIRECT33_PERSISTENCE_REVIEW.json')['passed']
for x in read(D/'LAUNCH_SOURCE_REVIEW.json')['files']:assert sha(x['path'])==x['sha256']
assert not (D/'DECISION78.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle78_20261029_v1/LAUNCH.json').exists()
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],archive=live(read(RUN/'MONITOR_LAUNCH.json')),restore78_waiter=live(read(P/'LAUNCH.json')),waiters={},decision78=False,training78=False)
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller'];assert not (p/'train/FAILURE.json').exists() and not (p/'DRIVER_FAILURE.json').exists();v=live(j);v.update(method=j['controller'],progress=read(p/'train/PROGRESS.json'),finished=read(p/'train/FINISHED.json') if (p/'train/FINISHED.json').exists() else None)
 if v['live']:v['samplers']=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split())
 else:assert v['finished']['status']=='stopped_at_complete_cycle'
 snap['learners'].append(v)
assert not (RUN/'ARCHIVE_REVIEW_FAILURE.json').exists()
if not snap['archive']['live']:assert read(RUN/'ARCHIVE_REVIEW_FINISHED.json')['completed']
assert not (P/'FAILURE.json').exists()
if not snap['restore78_waiter']['live']:assert read(P/'FINISHED.json')['prepared']
for n in ['parameter_recovery77_task_labels_20261029_v1','vmc_recovery77_terminal_followup_20261029_v1','admittance_recovery77_terminal_followup_20261029_v1','parameter_recovery77_loss_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1']:
 p=B/'runs'/n;j=read(p/'LAUNCH.json');assert sha(p/'PLAN.json')==j['plan_sha256'];assert not (p/'FAILURE.json').exists() and not (p/'WAIT_FAILURE.json').exists();snap['waiters'][n]=dict(live(j),plan_sha256=j['plan_sha256'])
 if not snap['waiters'][n]['live']:assert read(p/'FINISHED.json')['completed']
start=read(P/'FINAL_SNAPSHOT.json')['time'];rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=start];assert rows and time.time()-rows[-1]['time']<15;assert not (G/'FAILURE.json').exists()
for j in read(O/'REGISTRATION.json')['jobs'][-5:]:assert live(j)['live']
snap['guard']=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True);write(D/'FINAL_SNAPSHOT.json',snap);(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
sources={p for folder in [D,O,B/'runs/parameter_recovery78_loss_20261029_v1',B/'runs/parameter_partial75_recovery_cycle78_review_20261029_v1'] for p in folder.iterdir() if p.is_file() and p.suffix in ['.py','.json','.jsonl','.diff','.log']};sources.update(P/n for n in ['prepare_review_sources.py','FUTURE_REVIEW_SOURCE_REVIEW.json','startup78.py','startup78.py.diff','archive78.py','archive78.py.diff'])
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();assert len(data)<5_000_000;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
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
steps={j['method']:j['progress']['steps'] for j in snap['learners']};stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()
doc=f'''# 恢复77等待与78审查/派发准备

{stamp}，Goal active。上轮77前缀和78仅恢复准备属于progress，本轮完成78启动/归档/完整reward-replay-health审查、全loss/配对与续训派发入口准备，并连续观察原任务。当前77 steps {steps}，完整结果与终态以证据原件为准；无DECISION78、无78训练。前轮交接见[77前缀与恢复准备](RL_RECOVERY77_PREFIX78_PREPARATION_20261029.md)。

共享SSD `{B}`；主机 `{snap['host']}`；Python env/bin/python。原科学30×55秒/41250新增、4m append/markers23与47、terminal128、batch65536、UTD1、LR/reward/masks/物理/gates保持。Direct33既有训练条件数值结论及Task/Strict0/0保持，不启动Direct34；完整reward稳定和loss健康尚未证明。

本轮在当前容器重新逐hash核原Direct33决定绑定的七项证据和完整33 checkpoint（SHA783eaa7f），全部保持；这只是持久状态核验，未重算bootstrap或新增冻结评测。Direct既有数值结论保留，Task/Strict0/0、冻结29不认证最新33、指定ESN/最终比较未由本轮准备证明的限制保留，不缩小原Goal。

78 startup/archive/fullreview源码已准备，保留原新reward全量物理间隔重算、旧replay所有字段、history、optimizer、30条件、health检查。只适配当前78与完整77父路径和metadata，并增加父checkpoint continuation必须与父registration一致；历史75→76恢复字段保留，不能补造完整75。旧77运行和绑定源码不变，新源码尚未对实际78运行结果执行。

78完整loss工具保留49–74与76/77历史，新增78；episode路径明确恢复76/77/78，拒绝中断75；配对改为完整77→78，原reward/Strict/abort算术与gate不变。三方法74/76/77/78路径及75拒绝检查通过，源码AST通过；无78 loss等待器实际启动，无新的统计结果。该全历史描述不替代原前瞻76–78窗口。

新的decision78收集入口要求完整77归档/health、loss/独立算术、180标签/90reward对、V/A全部2274固定终端+新增30/独立标量、四张实际图查看收据，以及准确78全state/replay/next65536 CHECK_ONLY。原DECISION77及其全部历史证据逐hash保留；原74–76中断记录和前瞻76–78 PLAN准确SHA57b3d6be、原5%/nearzero1/seed2026102855/5000bootstrap/anchor55均保持，不用近零保护推离零。

launch78只接受该收集结果与显式有限续训理由，最多一个78，无自动79。当前真实不完整77、缺DECISION78、缺78 LAUNCH三个入口拒绝均通过，无新训练、无新决定，源码binding {len(read(D/'LAUNCH_SOURCE_REVIEW.json')['files'])}项已核。78全标签及终端后续仍需在准确完整77证据可用时准备，不能拿旧76基准冒充77。

原78仅恢复等待PID110433/start45315607保持按已登记规则运行，实际状态见snapshot；其完成也不等于78训练启动。原77训练/完整归档、loss、标签、V/A终端和76–78窗口均检查身份及失败原件，无科学重启。21样本/{f['elapsed']:.3f}秒共15原PID/start身份在观察期有效，steps {f['first_steps']}→{f['last_steps']}；观察器自然完成不代表科学完成。

保存时三路状态：{[dict(method=x['method'],live=x['live'],finished=x['finished'] is not None,steps=x['progress']['steps']) for x in snap['learners']]}。

从前次保存起guard {len(rows)}样本，最低{snap['guard']['minimum']}%，低于50次数{snap['guard']['below50']}。合成保载不是科学吞吐，按用户要求科研全部完成后仍继续；此前容器空档/v6预热两空闲样本保留，非重启自启服务。

本轮实际fetch/read mainb1deda65与baselinef6e8f8c，另一主机非RL第十一条件/99条runtime交接已读，原配置无相关变化；不操作其进程，无子agent。本轮前源码基线{receipt['source_base_commit']}，GitHub既有push128缺HTTPS认证，发布以最终实际收据为准，不声称已远端发布。

共享SSD小证据 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节及Python AST核验。[收据]({TAG}_SAVE.json)。大型checkpoint/replay/raw仍SSD，非HDD/arm1全备份；HDD最新入口指向已追加本链接的主恢复交接。

下一步收原完整77 loss/labels/health/terminal及实际图、完成准确78 CHECK_ONLY；根据结果写明确有限决定后才启动78，保持原76–78及GPU保底。Goal active，收敛目标未完成。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 恢复77等待与78完整审查/派发准备

- [交接](docs/{TAG}.md)。78 startup/archive/reward-replay-health、完整loss及77→78配对源码准备，保留49–74/76/77历史、75拒绝和原算术/gate。decision78绑定完整77全审/四张实际图/准确恢复/全部历史和原76–78PLAN；真实未完整77、缺决定、缺78LAUNCH拒绝通过，无78决定/训练。
- 原77连续21样本/{f['elapsed']:.3f}秒15身份live，当前steps{steps}；观察器自然结束，原科学与78仅恢复等待继续，终态依FINISHED。guard{len(rows)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}，科研完成仍保载、合成非吞吐。Goal active、Direct34false。
- SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐成员/AST核验，非HDD/arm1全备份；mainb1deda65/baselinef6e8f8c已读，认证发布待，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':a,b=s.split('\n',1);p.write_text(a+'\n\n'+entry+b.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[77等待与78完整审查/派发准备](docs/{TAG}.md)。原77全检查/仅恢复等待/76–78/GPU保底继续，无78决定或训练，Goal active。**\n\n'+p.read_text())
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n更新：[77等待与78完整审查/派发准备]({TAG}.md)。原任务继续，后续入口已准备，无78训练。\n')
print(json.dumps(receipt));print(json.dumps(snap))
