from pathlib import Path
import json,time,hashlib,subprocess,os,tarfile,ast,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;P=B/'runtime/prepare_recovery79_20261029_v1';R=B/'repository/SII_compliance';A=B/'repository/RL_RECOVERY79_PREPARATION_20261029';E=R/'docs/evidence/RL_RECOVERY79_PREPARATION_20261029';RUN=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';F=B/'runs/serl_take33_frozen_full30_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,j):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
assert read(P/'OBSERVATION_FINISHED.json')['passed'] and read(P/'PREPARATION_REVIEW.json')['passed'] and read(D/'PREPARATION_REVIEW.json')['passed']
assert not (D/'DECISION79.json').exists() and not (B/'runs/parameter_partial75_recovery_cycle79_20261029_v1/LAUNCH.json').exists()
obs=[json.loads(l) for l in (P/'OBSERVATIONS.jsonl').read_text().splitlines()];end=read(P/'OBSERVATION_FINISHED.json');assert obs[0]==end['first'] and obs[-1]==end['last'] and len(obs)==end['samples']
assert all(len(row['states'])==19 and all(s['live'] or s['terminal'] is not None for s in row['states']) for row in obs)
for m in ['impedance','admittance','vmc']:
 steps=[r['parameter_progress'][m]['steps'] for r in obs];assert steps==sorted(steps) and steps[-1]>steps[0]
put(P/'OBSERVATION_SAVED_REVIEW.json',dict(passed=True,time=time.time(),all_rows19_live_or_verified_terminal=True,first_last_exact=True,parameter_steps_monotonic_and_advanced=True,scientific_restart=False))
for plan in [P/'DRIVER_SOURCE_REVIEW.json',P/'FUTURE_REVIEW_SOURCE_REVIEW.json',D/'LAUNCH_SOURCE_REVIEW.json']:
 for item in read(plan)['files']:
  path=Path(item['path']) if 'path' in item else P/item['name'];assert sha(path)==item['sha256'],str(path)
cut=read(B/'repository/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029/FINAL_LOCAL_RECEIPT.json')['time'];raw=[l for l in (G/'samples.jsonl').read_text().splitlines() if json.loads(l)['time']>cut];g=list(map(json.loads,raw));assert g
(D/'GUARD_SAMPLES.jsonl').write_text('\n'.join(raw)+'\n');gpu=dict(samples=len(g),minimum=[min(x['gpus'][i]['utilization'] for x in g) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in g) for i in range(4)],latest=g[-1],synthetic_guard_included=True,continues_after_science=True,reboot_service=False)
progress={m:read(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};shards=[dict(pid=j['pid'],completed=len(read(Path(j['output'])/'RESULTS.json')['episodes'])) for j in read(F/'LAUNCH.json')['jobs']]
state=dict(time=time.time(),parameter78=progress,frozen33=shards,full78_review_finished=(RUN/'ARCHIVE_REVIEW_FINISHED.json').exists(),restore79_prepared=(P/'FINISHED.json').exists(),restore79_failure=(P/'FAILURE.json').exists(),no79_decision=True,no79_training=True,guard=gpu,goal='active');put(D/'FINAL_SNAPSHOT.json',state)
assert not state['restore79_failure']
A.mkdir(exist_ok=False);E.mkdir(exist_ok=False);manifest=[]
roots=[P,D,B/'runs/parameter_partial75_recovery_cycle79_review_20261029_v1',B/'runs/parameter_recovery79_loss_20261029_v1']
for root in roots:
 for source in sorted(root.rglob('*')):
  if not source.is_file() or '__pycache__' in source.parts or source.suffix=='.pyc':continue
  assert source.stat().st_size<10_000_000
  rel=source.relative_to(B);target=E/rel;target.parent.mkdir(parents=True,exist_ok=True);data=source.read_bytes();target.write_bytes(data)
  if source.suffix=='.py':ast.parse(data.decode())
  manifest.append(dict(path=str(rel),source=str(source),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),captured_snapshot=True))
for root,names in [(B/'runs/parameter_recovery76_78_reward_stability_20261029_v1',['PLAN.json','LAUNCH.json']), (RUN,['LAUNCH.json','MONITOR_LAUNCH.json']), (F,['LAUNCH.json','REVIEW_LAUNCH.json','COMPARISON_LAUNCH.json'])]:
 for n in names:
  source=root/n;data=source.read_bytes();rel=source.relative_to(B);p=E/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);manifest.append(dict(path=str(rel),source=str(source),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),captured_snapshot=True))
put(E/'MANIFEST.json',dict(time=time.time(),entries=manifest,large_artifacts='Shared SSD; not full HDD/arm1 backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)))
with tarfile.open(archive) as t:
 members=t.getmembers();assert len(members)==len(manifest)+1
 for m in members:assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(members),manifest_entries=len(manifest),all_member_bytes_and_python_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),remote_main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(),remote_baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=R,text=True).strip(),host=os.uname().nodename,large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs/RL_RECOVERY79_PREPARATION_20261029_SAVE.json',receipt)
steps={m:v['steps'] for m,v in progress.items()};counts={m:v['completed_conditions'] for m,v in progress.items()};fc=sum(x['completed'] for x in shards);actual_prepared=state['restore79_prepared']
doc=f'''# 恢复79仅恢复与完整审查准备；原78及冻结33继续

{datetime.datetime.now(datetime.timezone.utc).isoformat()}，Goal active。上轮[78固定前缀诊断](RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029.md)保留：VMC185.416763尖峰和actor漂移、阻抗重复尖峰不能称loss健康。本轮为可能的有限后续79准备准确恢复与完整审查工具，**没有写DECISION79，也没有启动79训练**。是否继续须依据完整78和原76–78统计，不把数值有限或GPU占用当收敛。

执行主机 `{receipt['host']}`，共享SSD `{B}`；解释器 `{B}/env/bin/python`。本轮源码基线 `{receipt['source_base_commit']}`；实际fetch/read main `{receipt['remote_main']}`、baseline `{receipt['remote_baseline']}`，未变。对方非RL完整108/v9补采记录已读并保持，无子agent。

## 准确恢复准备

`{P}`。新的resume_recovery78.py仅将当前完整父78/后继79的元数据与路径推进，递归校验原78→77→76→partial75历史；完整父checkpoint必须匹配原continuation。训练器transform结果与78逐字相同，移除原五处元数据/初始state检查插入后与原trainer逐字相同。原23/47容量markers、4m replay、30条件、55秒、最多41250新增、batch65536/UTD1/terminal128、学习率/reward/masks/physics/gates均保持；恢复构造器的占位seed未改变，实际RNG由完整checkpoint恢复。

三路metadata正例、每路19协议负例和8父边界负例通过，真实尚未完整78被拒绝且未创建79输出。加入空CUDA_VISIBLE_DEVICES拒绝，防止CPU check-only丢失CUDA RNG的旧环境误判；原驱动恢复行为保持。仅恢复等待PID4005471/start45874952已部署，绑定原三learner与archive monitor；只在完整78审查和原learner退出后才运行三路fullstate/replay/next65536检查，0物理/0更新。最终快照恢复79已完成={actual_prepared}，完整78审查已完成={state['full78_review_finished']}；准确结论依各CHECK_ONLY_REVIEW及FINISHED，不能用metadata fixtures冒充实际恢复。

初次构建把父runtime78下驱动文件仍写成resume_recovery76.py，metadata测试FileNotFoundError；部署前改为实际resume_recovery77.py后全测试通过。初始源码/失败和fixtures原件保留在initial_source_failure与contract_fixtures，修正测试使用独立contract_fixtures_retry，无科学重启。

## 后续审查与派发源码

`{B}/runs/parameter_partial75_recovery_cycle79_review_20261029_v1` 的全review/coordinator和startup79/archive79仅推进当前周期，逐逆变换核验；所有旧reward/replay/history/optimizer/30条件审查保持，partial75→76历史不改。参数health所需published诊断与value-bound依赖逐字复制78并实际导入通过。初次准备误将未使用的SERL helper当必需导致中断，保存原失败后核对现有部分文件字节并补齐真正所需的两份源，没有改动运行中的78 reviewer。

`{B}/runs/parameter_recovery79_loss_20261029_v1` 准备完整79 loss与78→79配对；完整49–74/76–78历史保持，75仍拒绝。路径回归与AST核验通过，没有部署79 loss waiter。

`{D}` 的decision79/launch79/deploy_loss79已准备，实际未完整78、缺DECISION79、缺79 LAUNCH三种拒绝通过。新决定必须绑定完整78全loss/health/所有标签/2304旧终端+30新终端、五张实际图、原76–78结果及独立已存算术、准确恢复79和全部prior78历史证据；仍需实际CONTINUATION_REASON才能写决定。原76–78PLAN SHA57b3d6be保持，5%/近零1/bootstrap5000/seed2026102855/anchor55不改。没有自动79/80或Direct34，也没有新窗口替代原结果。

## 原任务连续性与保存

VMC78原训练已完整结束：30×55秒/41250新增、无abort，runtime reward均值−4.605158151062658，Task17/30、Strict16/30；按原FINISHED及全部30episode身份核验，见VMC78_RUNTIME_FINISHED.json。该先行runtime统计不冒充完整checkpoint/replay/health审查。

本轮观察{end['samples']}样本/{end['elapsed']:.3f}秒，19原身份均live或由终态产物核验，原科学不因观察到期重启；保存后独立检查首尾/逐行身份和步号单调。最新78steps{steps}、完成条件{counts}，冻结Direct33 runtime{fc}/30。原全部loss/标签/终端/health/76–78和冻结33根审查/配对继续，尚未完成的结论不预告。

GPU原guard从上次收据后{gpu['samples']}样本，最低{gpu['minimum']}%，低于50次数{gpu['below50']}。包含合成保活，不当科学吞吐；科研全部结束仍保载，非重启自启服务，历史容器停机/预热空闲保留。

SSD证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，逐成员/AST核验，[收据](RL_RECOVERY79_PREPARATION_20261029_SAVE.json)。运行log仅捕获当时快照，大checkpoint/raw/replay仍SSD，非HDD或arm1全备份。HDD既有LATEST原位更新不增长；GitHub发布依实际push，已有HTTPS认证缺失。

下一步收齐完整78全审和原76–78结果/实际图，结合尖峰/actor漂移及条件级成功退化判断是否有限79；未通过完整审查前不得训练。Direct33继续至全30及完整物理/状态不变/配对结果；指定ESN和最终比较范围保持，Goal active。
'''
(R/'docs/RL_RECOVERY79_PREPARATION_20261029.md').write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 恢复79仅恢复及完整审查准备

- [交接](docs/RL_RECOVERY79_PREPARATION_20261029.md)。79科学trainer与78逐字同一、五metadata插入可逆，递归保留原78/77/76/partial75；三路正例与每路19协议+8边界拒绝、真实未完整78拒绝通过。仅恢复等待4005471部署，准确恢复完成={actual_prepared}，无79决定/训练。
- startup/archive/fullreview/health依赖实际导入及完整79loss历史/78→79配对准备；新decision须完整78和原76–78结果/五张实际图。两个准备错误已部署前修正保留，无科学重启。原78steps{steps}/完成{counts}、冻结33 runtime{fc}/30；观察{end['samples']}样本/{end['elapsed']:.3f}秒19身份live或核验终态，Goal active、Direct34false。
- guard{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研完成仍保载、合成非吞吐。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐成员/AST核验，非HDD/arm1全备份；main{receipt['remote_main'][:8]}/baseline{receipt['remote_baseline'][:8]}已读不变，认证发布待收据，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text();p.write_text((s.split('\n',1)[0]+'\n\n'+entry+s.split('\n',1)[1].lstrip('\n')) if n=='AGENTS.md' else entry+s)
p=R/'HANDOFF.md';p.write_text('> **RL最新：[79仅恢复/完整审查准备](docs/RL_RECOVERY79_PREPARATION_20261029.md)。原78/冻结33/GPU保活继续，无79决定或训练；必须先审原76–78完整结果。**\n\n'+p.read_text())
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text('> **最新：[79仅恢复/完整审查准备](RL_RECOVERY79_PREPARATION_20261029.md)。原78/冻结33继续，GPU科研结束仍保活，无79训练决定。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');old=p.read_bytes();s='# RL '+datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')+'\n78+D33;prep79;guardv6.\nSSD '+str(B)+'\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n';data=s.encode();assert len(data)<=len(old)
with p.open('r+b') as f:f.write(data+b' '*(len(old)-len(data)));f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data+b' '*(len(old)-len(data))
print(json.dumps(receipt,indent=2))
