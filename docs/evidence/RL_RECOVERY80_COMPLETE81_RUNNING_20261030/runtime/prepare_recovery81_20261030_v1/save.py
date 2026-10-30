from pathlib import Path
import json,time,hashlib,tarfile,ast,socket,subprocess,datetime,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;P=B/'runs/parameter_recovery80_first5000_20261029_v1';RUN=B/'runs/parameter_partial75_recovery_cycle80_20261029_v1';TAG='RL_RECOVERY80_PREFIX81_PREPARATION_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 q=Path(f'/proc/{j["pid"]}/stat')
 if not q.exists():return False
 s=q.read_text().rsplit(')',1)[1].split();return s[19]==j['proc_start_ticks'] and s[0]!='Z'
for n in ['DRIVER_SOURCE_REVIEW.json','CONTRACT_REVIEW.json','INCOMPLETE80_REJECTION.json','FUTURE_REVIEW_SOURCE_REVIEW.json','HEALTH_DEPENDENCY_IMPORT_REVIEW.json','FINAL_SOURCE_REVIEW.json','OBSERVATION_FINISHED.json']:assert read(D/n)['passed']
for n in ['REVIEW.json','SAVED_REVIEW.json']:assert read(P/n)['passed']
assert read(P/'PLOT_INSPECTION.json')['actual_image_viewed']
assert live(read(D/'LAUNCH.json')) or (D/'FINISHED.json').exists()
for x in read(D/'FINAL_SOURCE_REVIEW.json')['files']:assert sha(x['path'])==x['sha256']
obs=read(D/'OBSERVATION_FINISHED.json');rows=[json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()];assert len(rows)==obs['samples'] and rows[-1]['elapsed']>=300 and obs['saved_rows_verified']
progress={}
for j in read(RUN/'LAUNCH.json')['jobs']:
 assert live(j) or (RUN/j['controller']/'train/FINISHED.json').exists();assert not (RUN/j['controller']/'train/FAILURE.json').exists();progress[j['controller']]=read(RUN/j['controller']/'train/PROGRESS.json')
future=B/'runs/parameter_partial75_recovery_cycle81_20261029_v1';assert not (future/'LAUNCH.json').exists()
g=Path('/tmp/sii_gpu_util_guard_20261030_v7');allrows=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];since=read(B/'runtime/recovery80_abort_aware_decision_20261030_v2/SAVE_SNAPSHOT.json')['time'];gpu=[v for v in allrows if v['time']>since];assert gpu and time.time()-gpu[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in gpu));guard=dict(samples=len(gpu),minimum=[min(v['gpus'][i]['utilization'] for v in gpu) for i in range(4)],below50=[sum(v['gpus'][i]['utilization']<50 for v in gpu) for i in range(4)],last=[v['utilization'] for v in gpu[-1]['gpus']],synthetic_included=True,keep_after_science=True)
snap=dict(time=time.time(),host=socket.gethostname(),parameter80=progress,prepare81=read(D/'LAUNCH.json'),actual81_restore_complete=(D/'FINISHED.json').exists(),training81=False,direct34=False,guard=guard,goal='active');put(D/'SAVE_SNAPSHOT.json',snap)
files=set()
for folder in [D,P,B/'runtime/recovery80_prefix_audit_20261030_v1',B/'runs/parameter_partial75_recovery_cycle81_review_20261029_v1',B/'runs/parameter_recovery81_loss_20261029_v1']:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.json','.jsonl','.py','.log','.diff','.png','.txt']:files.add(p)
E.mkdir(exist_ok=False);A.mkdir(exist_ok=False);manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<10_000_000;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,large_artifacts_retained_shared_ssd=True,active_logs_are_snapshots=True,depends_on_prior_complete79_archive='RL_RECOVERY79_ABORT80_RUNNING_20261030'))
tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,all_members_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),start_main='ecdfdd530c97121ad1f86d0f198e3f111e80f6d9',remote_main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(),baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=R,text=True).strip(),host=snap['host'],large_artifacts='Shared SSD; not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={m:v['steps'] for m,v in progress.items()};table=[]
for m,x in read(P/'REVIEW.json')['methods'].items():
 q=x['metrics']['agent_train/q_loss'];a=x['metrics']['agent_train/actor_loss'];table.append(f"|{m}|{x['first_step']}–{x['last_step']}|{q['first1000']:.6f} → {q['last1000']:.6f}|{q['maximum']:.6f}|{a['first1000']:.6f} → {a['last1000']:.6f}|")
table='\n'.join(table)
doc=f'''# 第80轮前缀核查与第81轮仅恢复准备

{datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()}。Goal active。上一轮完成79全审/真实安全失败诊断和有限80实际续训，属于实质进展；本轮完成80固定首5000核查、81仅恢复及完整审查工具准备，并连续观察原80。**80仍在运行，steps {steps}；81训练未启动，实际完整80→81恢复完成={snap['actual81_restore_complete']}。**

主机`{snap['host']}`，共享SSD`{B}`，解释器`{B}/env/bin/python`。沿用已读sii-research-sync流程，无子agent。开工实际查询main`{receipt['start_main']}`与baseline`{receipt['baseline']}`，随后fetch/read main从1cccff20前进至`{receipt['remote_main']}`，非RL日志56→66/75已读并安全快进、源码未动；另一主机实验不替代本任务。

## 固定首5000实际结果

数据`runs/parameter_recovery80_first5000_20261029_v1`，注册明确在80训练启动及前缀可用之后，仅沿用原5000长度作描述，不冒充事先注册的新收敛窗口。三个原日志前缀逐字节核对、连续step和全部数值有限、独立标量算术通过；六面板原始点/1000更新均值图已实际查看并绑定SHA。

|方法|累计步号区间|critic首→尾1000|critic最大|actor首→尾1000|
|---|---:|---:|---:|---:|
{table}

I重复尖峰并有后段均值抬升区；A尖峰仍在、末1000 critic均值较首1000升高；V均值下降但仍有尖峰。Actor仅此短前缀漂移较小，不能替代完整趋势。没有根据这段结果改LR/reward/掩码/物理或判收敛，原完整80 loss/health/标签/终端及79–81窗口继续。

完整79 I在long0000的27s/675动作安全失败仍保留：40550新增、29full，原97.689mm子步global穿透记录不能由25Hz保存帧重建，根因未定；terminal−25/failure_tail−9.940790/Task-Strict-physical false不变。不重跑失败，不虚构55s；完整79与版本2有限80决定见[前次交接](RL_RECOVERY79_ABORT80_RUNNING_20261030.md)。第81轮的准备不意味着80安全/性能通过，更不自动继承允许任何失败的决定。

## 81仅恢复及审查准备

`runtime/prepare_recovery81_20261030_v1`。准确80父注册、checkpoint、完整review/health与前驱driver递归绑定，继续保留79已知失败与全部partial75暴露；75完整历史仍缺失。新`resume_recovery80.py`只推进父80/后继81及前驱79/80身份与路径，科学trainer transform与80逐字一致，五metadata插入移除后与原冻结trainer逐字一致；数字AST只允许周期变更，构造器占位seed20261078与实际checkpoint RNG保持。

三路protocol/parent正fixture通过，每路19协议+8边界负fixture拒绝；真正未完整80被prepare入口拒绝，未创建81运行目录。fixture不等于准确完整80状态恢复。仅恢复等待器PID{snap['prepare81']['pid']}/start{snap['prepare81']['proc_start_ticks']}已部署，只等原80完整归档/review/health且learner退出后做全state/replay/下一65536采样核验，0新物理/优化；4小时观察上限到期不重启科学。未来运行目录沿用`parameter_partial75_recovery_cycle81_20261029_v1`，不要另建重复run。

startup81/archive81/fullreview81准备，原75→76中断字段、markers23/47、4m append-only及全部reward/replay/history/optimizer检查保持；health两个实际依赖逐字复制并实际导入通过。完整81 loss工具保留49–74与76–80全部历史、继续拒绝75，配对仅80→81；路径回归通过，原算术/gate不改，尚未部署81loss waiter。未创建DECISION81/CONTINUATION_REASON或81训练启动入口；须完整80图与证据解释后另决定。

原30条件/55s上限、最多41250新transition、batch65536/UTD1、terminal128、LR/reward/masks/物理/安全检查不变。原76–78 I近零不可判/A不满足5%/V仅reward满足但loss未证保持；前瞻79–81 PLAN SHA `5cf5efb87a63b432091276c3b96a3b16126c2ab891a2e195b6c857e93cf110a0`保持，近零保护不是改变reward方向的目标。

## 连续观察与保存

{obs['samples']}样本/{obs['elapsed']:.3f}秒，{obs['identities']}个原80三learner/archive/loss/labels/两terminal/79–81、81仅恢复以及GPU supervisor/四worker身份live或核完整终态。steps {obs['first_steps']}→{obs['last_steps']}，所有绑定源码保持、保存行独立核验；观察器自然结束，不重启科学。

上次保存以来GPU{guard['samples']}样本，最低{guard['minimum']}%，低于50次数{guard['below50']}，最后{guard['last']}%；含合成保活且科研全部结束仍运行，不能当科研吞吐。guardv7仍CPU4–6、目标70%/阈值50%，历史停机/预热0与v6低谷保持；非重启自启服务。

SSD补充证据包`{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA`{receipt['sha256']}`，逐成员字节/hash及AST核验；[保存收据]({TAG}_SAVE.json)。依赖前次完整79/80启动包，大checkpoint/raw仍共享SSD、非HDD/arm1全备份。HDD既有254字节LATEST指针原位更新回读，GitHub发布以实际收据为准。

下一步继续原80，检查完整条件结果、loss/health、全部标签/终端、准确81恢复及79–81等待器，再决定有限81。Direct33数值阶段及冻结全30 Task/Strict0/0、旧最终内存证明缺失保持；不启动34，指定ESN及最终冻结比较仍待。Goal active，GPU保活继续。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-30 — 原80前5000已核；81仅恢复准备

- [交接](docs/{TAG}.md)。80三路前5000原日志字节/连续step/全部有限/独立算术/实际六图核验；critic首→尾I2.714394→2.630187、A1.330159→1.485200、V0.978321→0.870612，尖峰仍在，仅描述前缀非收敛。原80steps{steps}，全审查继续，79安全失败及原窗口保持。
- 81科学trainer与80逐字同一、五metadata插入可逆；三路正fixture/每路19协议+8边界拒绝及真实未完整80拒绝通过。仅恢复等待{snap['prepare81']['pid']}已部署，准确恢复完成={snap['actual81_restore_complete']}，startup/archive/fullreview/health实际依赖与完整loss/80→81配对准备；无81决定/训练、无Direct34，Goal active。
- {obs['samples']}样本/{obs['elapsed']:.3f}s共{obs['identities']}身份保持；GPU{guard['samples']}样本min{guard['minimum']}%、低于50{guard['below50']}，科研结束仍合成保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份。mainecdfdd53后{receipt['remote_main'][:8]}/baselinef6e8f8c已fetch/read并保留非RL66/75；发布待收据，无子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':h,t=s.split('\n',1);p.write_text(h+'\n\n'+entry+t.lstrip('\n'))
 else:p.write_text(entry+s)
for p,link in [(R/'HANDOFF.md','docs/'+TAG+'.md'),(R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md',TAG+'.md')]:p.write_text(f'> **最新：[80前缀与81仅恢复准备]({link})。原80运行，无81训练决定，GPU保活继续。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');n=p.stat().st_size;v=f'# RL {datetime.datetime.fromtimestamp(snap["time"],datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}\n80;prep81;guardv7.\nSSD {B}\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n'.encode();assert n==254 and len(v)<=n
with p.open('r+b') as f:f.write(v+b' '*(n-len(v)));f.flush();os.fsync(f.fileno())
assert p.read_bytes()==v+b' '*(n-len(v));print(json.dumps(receipt));print(json.dumps(dict(steps=steps,guard=guard)))
