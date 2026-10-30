from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;DEC=B/'runtime/recovery80_completion_preparation_20261030_v1';RUN=B/'runs/parameter_partial75_recovery_cycle79_20261029_v1';OUT=B/'runs/parameter_partial75_recovery_cycle80_20261029_v1';TAG='RL_RECOVERY80_PREPARATION_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,j):
 with p.open('x') as f:f.write(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 return s is not None and s[19]==j['proc_start_ticks'] and s[0]!='Z'
obs=read(D/'OBSERVATION_FINISHED.json');rows=[json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()];plan=read(D/'OBSERVATION_PLAN.json');assert obs['passed'] and len(rows)==obs['samples']==11 and obs['elapsed']>=300 and obs['identities']==len(plan['jobs'])
for row in rows:
 assert [(x['pid'],x['proc_start_ticks']) for x in row['identities']]==[(x['identity']['pid'],x['identity']['proc_start_ticks']) for x in plan['jobs']]
 assert all(x['status'] in ['live','terminal_receipt'] for x in row['identities'])
for m in ['impedance','admittance','vmc']:
 assert obs['first_steps'][m]==rows[0]['parameter'][m]['steps'] and obs['last_steps'][m]==rows[-1]['parameter'][m]['steps']
 assert all(a['parameter'][m]['steps']<=z['parameter'][m]['steps'] for a,z in zip(rows,rows[1:]))
for p,h in plan['sources'].items():assert sha(p)==h
put(D/'OBSERVATION_SAVED_REVIEW.json',dict(passed=True,time=time.time(),all_saved_identities_and_steps_verified=True,samples=11,scientific_restart=False))
for p in [D/'DRIVER_SOURCE_REVIEW.json',D/'CONTRACT_REVIEW.json',D/'INCOMPLETE79_REJECTION.json',D/'FUTURE_REVIEW_SOURCE_REVIEW.json',D/'HEALTH_DEPENDENCY_IMPORT_REVIEW.json',DEC/'PREPARATION_REVIEW.json']:assert read(p)['passed']
assert not (DEC/'DECISION80.json').exists() and not (OUT/'LAUNCH.json').exists();assert live(read(D/'LAUNCH.json')) or (D/'FINISHED.json').exists()
progress={}
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller']/'train';assert live(j) or (p/'FINISHED.json').exists();assert not (p/'FAILURE.json').exists();progress[j['controller']]=read(p/'PROGRESS.json')
g=Path('/tmp/sii_gpu_util_guard_20261030_v7');allrows=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];previous=read(B/'runtime/recovery79_newhost_20261030_v1/SAVE_SNAPSHOT.json')['time'];gpu=[x for x in allrows if x['time']>previous];assert gpu and time.time()-gpu[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in gpu));guard=dict(samples=len(gpu),minimum=[min(x['gpus'][i]['utilization'] for x in gpu) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in gpu) for i in range(4)],last=gpu[-1],synthetic_included=True,keep_after_science=True)
snap=dict(time=time.time(),host=socket.gethostname(),parameter79=progress,prepare80=read(D/'LAUNCH.json'),actual80_restore_complete=(D/'FINISHED.json').exists(),decision80=False,training80=False,direct34=False,guard=guard,goal='active');put(D/'SAVE_SNAPSHOT.json',snap)
sources=set()
for folder in [D,DEC,B/'runs/parameter_partial75_recovery_cycle80_review_20261029_v1',B/'runs/parameter_recovery80_loss_20261029_v1']:
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in ['.py','.json','.jsonl','.log','.diff','.txt'] and '__pycache__' not in p.parts:sources.add(p)
E.mkdir(exist_ok=False);A.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();assert len(data)<5_000_000;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,large_artifacts_retained_shared_ssd=True,active_logs_are_snapshots=True))
tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for member in t.getmembers():assert t.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,manifest_entries=len(manifest),all_members_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),remote_main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(),remote_baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=R,text=True).strip(),host=snap['host'],large_artifacts='Shared SSD; not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={m:v['steps'] for m,v in progress.items()};stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()
doc=f'''# 第80轮仅恢复与审查准备；原79连续训练

{stamp}，Goal active。上一轮完成完整78/76–78结果、第79轮恢复和Direct33全30评测与发布，属于实质进展；本轮完成可能后续80的仅恢复/审查工具及连续观察。**没有DECISION80，没有启动80训练；实际完整79→80恢复完成={snap['actual80_restore_complete']}。** 原79三路steps `{steps}`，各完整状态与采样继续，不能用前缀有限或GPU占用宣称收敛。

执行主机 `{snap['host']}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。源码基线 `{receipt['source_base_commit']}`；本轮实际查询/fetch/read main `{receipt['remote_main']}`、baseline `{receipt['remote_baseline']}`及日志，未变，非RL并行工作保持。沿用已读sii-research-sync流程，无子agent。

## 状态恢复检查

源码 `{D}`。恢复driver `resume_recovery79.py`只推进当前完整父79/后继80与前驱78/79的身份、路径和描述，递归验证完整原79→78→77→76→partial75。trainer transform与79逐字一致，移除五处状态/历史metadata插入后与原冻结trainer逐字一致；所有数字AST常量仅相应周期变化，恢复构造器占位seed20261078保持，实际RNG由checkpoint恢复。CUDA可见性保护保留，避免CPU check-only丢失CUDA RNG。

三路协议/父边界正例通过，每路19协议拒绝和8边界拒绝（科学参数、父边界、完整性与历史链损坏），实际当前未完整79被拒绝且未创建80运行目录。fixture不是实际完整79恢复。仅恢复等待器PID{snap['prepare80']['pid']}/start{snap['prepare80']['proc_start_ticks']}已经真实部署；只在79归档/full review/health完成且原learner退出后执行准确全state/replay/下一65536采样检查，0新物理/0优化。固定4小时观察上限，到期不重启科学。

原30×55s/最多41250新增、4m append、markers23/47、terminal128、batch65536/UTD1、LR/reward/masks/物理/MJB/gates保持。完整75始终缺失，不补造75或原74–76窗口。当前运行79、潜在80/81仍沿用已登记`_20261029_v1`目录名，不按当前日期另开重复科学run。

## 完整审查与决策入口

`runs/parameter_partial75_recovery_cycle80_review_20261029_v1`准备完整reward/replay/history/optimizer审查和health；startup80/archive80只推进周期、历史75→76保持。实际导入health两个依赖通过，未做新网络forward。完整80 loss工具在`runs/parameter_recovery80_loss_20261029_v1`；完整49–74和76–79历史全部保留，路径回归覆盖这些完整周期并继续拒绝75，下一配对79→80。尚未部署80 loss waiter。

`runtime/recovery80_completion_preparation_20261030_v1`的decision80/launch80/deploy_loss80已准备。真实未完整79、缺DECISION80、缺80 LAUNCH三个入口拒绝通过，0物理/0更新。后续决定必须绑定完整79 loss/配对/180标签/90reward/health/旧2334+新30终端和四张实际图、准确恢复80、全部prior79决定证据、原76–78完整结果及已查看图。还精确绑定79–81 PLAN SHA `5cf5efb87a63b432091276c3b96a3b16126c2ab891a2e195b6c857e93cf110a0`；其5%/近零1/bootstrap5000/seed2026102855/anchor55不变。没有预写CONTINUATION_REASON或决定，没有因未来窗口而自动启动80/81。

原76–78 I近零不可判、A失败5%、V仅reward通过而loss健康未证的结论保持；原79前5000 I/V尖峰18.15/18.07只是描述，有限尖峰本身不是新增拒绝门槛。后续须结合完整趋势、alpha/critic/终端诊断判断，不挑短窗口或把nearzero当改变reward方向的理由。Direct33已接受的数值阶段与冻结全30 Task/Strict0/0、旧最终内存证明缺失均保持，不启动34；指定ESN及完整最终比较仍未完成。

## 连续观察与保存

原79三learner/archive/全loss/标签/两终端/79–81、80仅恢复等待和GPU supervisor/四worker，共{obs['identities']}身份连续11样本/{obs['elapsed']:.3f}s均live或以完整终态核验；步数{obs['first_steps']}→{obs['last_steps']}，所有绑定source保持。保存后逐行独立检查身份/步号/首尾一致；observer自然结束，科学未重启。

上次保存以来GPU {guard['samples']}个5秒样本，最低{guard['minimum']}%，低于50次数{guard['below50']}；最后{[x['utilization'] for x in gpu[-1]['gpus']]}%。含合成保活，不当科研吞吐；科学全部完成仍保载。历史停机、v7预热0和v6的31/33/44低谷保留，不宣称永久无低谷，不是重启自启服务。

SSD证据包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/hash及Python AST核验；收据[{TAG}_SAVE.json]({TAG}_SAVE.json)。运行log是当时快照，大checkpoint/replay/raw继续留共享SSD，非HDD/arm1完整备份。现有HDD LATEST按原长度原位更新，入口仍指向主交接；GitHub发布以本轮实际收据为准。

下一步先收齐正在运行的79完整科学结果与实际图、核80准确恢复，再决定是否有限80。不得重复派发79、仅恢复检查或原Direct33评测。Goal active，GPU保活继续。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-30 — 原79继续；80仅恢复及完整审查准备

- [交接](docs/{TAG}.md)。80科学trainer与79逐字相同、五metadata插入可逆；三路正例/每路19协议+8边界拒绝、真实未完整79拒绝通过。仅恢复等待{snap['prepare80']['pid']}已部署，准确80恢复完成={snap['actual80_restore_complete']}，无80决定/训练；原79steps{steps}。
- startup/archive/fullreview/health实际依赖和完整80loss/79→80配对工具准备；decision绑定完整79/四实际图、准确恢复、原76–78完整结果及79–81准确PLAN，三个缺前置真实拒绝。11样本/{obs['elapsed']:.3f}s共{obs['identities']}身份保持并独立保存复核，观察器自然结束，科学不重启；Goal active、无Direct34。
- guard{guard['samples']}样本min{guard['minimum']}%、低于50{guard['below50']}，科研结束仍合成保活，历史低谷保留。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}逐成员/AST已核，非HDD/arm1全备份；main{receipt['remote_main'][:8]}/baseline{receipt['remote_baseline'][:8]}已读，发布待收据，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':h,t=s.split('\n',1);p.write_text(h+'\n\n'+entry+t.lstrip('\n'))
 else:p.write_text(entry+s)
for p,link in [(R/'HANDOFF.md','docs/'+TAG+'.md'),(R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md',TAG+'.md')]:p.write_text(f'> **最新：[80仅恢复/审查准备]({link})。原79继续，无80训练决定，GPU科研结束仍保活。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');n=p.stat().st_size;v=f'# RL {datetime.datetime.fromtimestamp(snap["time"],datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}\n79;prep80;guardv7.\nSSD {B}\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n'.encode();assert len(v)<=n
with p.open('r+b') as f:f.write(v+b' '*(n-len(v)));f.flush();os.fsync(f.fileno())
assert p.read_bytes()==v+b' '*(n-len(v));print(json.dumps(receipt));print(json.dumps(snap))
