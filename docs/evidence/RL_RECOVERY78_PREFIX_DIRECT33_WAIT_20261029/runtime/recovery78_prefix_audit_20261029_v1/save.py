from pathlib import Path
import json,hashlib,time,os,subprocess,ast,tarfile,shutil,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'repository/SII_compliance';A=B/'repository/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029';E=R/'docs/evidence/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029';P=B/'runs/parameter_recovery78_first5000_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,j):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x') as f:f.write(json.dumps(j,indent=2)+'\n')
finished=read(D/'OBSERVATION_FINISHED.json');assert finished['passed'] and finished['samples']==11
assert read(P/'SAVED_REVIEW.json')['passed'] and read(P/'PEAK_CONTEXT_REVIEW.json')['passed'] and read(P/'PLOT_INSPECTION.json')['actually_viewed']
A.mkdir(exist_ok=False);E.mkdir(exist_ok=False)
last=finished['last'];steps={m:v['steps'] for m,v in last['parameter_progress'].items()};frozen=sum(x['completed'] for x in last['frozen_shards'])
previous=read(B/'repository/RL_DIRECT33_FROZEN_VALIDATION_20261029/FINAL_LOCAL_RECEIPT.json');raw=[l for l in (G/'samples.jsonl').read_text().splitlines() if json.loads(l)['time']>previous['time']];rows=list(map(json.loads,raw));assert rows
(D/'GPU_WINDOW.jsonl').write_text('\n'.join(raw)+'\n');gpu=dict(time=time.time(),samples=len(rows),first_time=rows[0]['time'],last_time=rows[-1]['time'],minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],latest=rows[-1],synthetic_guard_included=True,guard_continues_after_science=True,reboot_service=False,historical_downtime_and_warmup_not_erased=True);write(D/'GPU_WINDOW_REVIEW.json',gpu)
paths=list(P.iterdir())+[p for p in D.iterdir() if p.is_file()]
for folder,names in [(B/'runs/parameter_partial75_recovery_cycle78_20261029_v1',['LAUNCH.json','MONITOR_LAUNCH.json']), (B/'runs/serl_take33_frozen_full30_20261029_v1',['LAUNCH.json','REVIEW_LAUNCH.json','COMPARISON_LAUNCH.json']), (B/'runs/parameter_recovery76_78_reward_stability_20261029_v1',['PLAN.json','LAUNCH.json'])]:
 paths.extend(folder/n for n in names)
manifest=[]
for p in paths:
 if not p.is_file():continue
 rel=p.relative_to(B);target=E/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);assert target.read_bytes()==p.read_bytes()
 if p.suffix=='.py':ast.parse(target.read_text())
 manifest.append(dict(path=str(rel),source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
for n in ['guard.py','LAUNCH.json']:
 p=G/n;target=E/'guard'/n;target.parent.mkdir(exist_ok=True);shutil.copyfile(p,target);manifest.append(dict(path='guard/'+n,source=str(p),bytes=p.stat().st_size,sha256=sha(p)))
write(E/'MANIFEST.json',dict(time=time.time(),entries=manifest,large_artifacts='Shared SSD; no full HDD/arm1 backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)))
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers();assert len(members)==len(manifest)+1
 for m in members:assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(members),manifest_entries=len(manifest),all_members_exact=True,python_ast_passed=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),remote_main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(),remote_baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=R,text=True).strip(),host=os.uname().nodename,large_artifacts='Shared SSD; no full HDD/arm1 backup')
write(A/'RECEIPT.json',receipt);write(R/'docs/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029_SAVE.json',receipt)
review=read(P/'REVIEW.json');table=[]
for m,v in review['methods'].items():
 q=v['metrics']['agent_train/q_loss'];a=v['metrics']['agent_train/actor_loss'];table.append(f"|{m}|{q['first1000']:.6f} → {q['last1000']:.6f}|{q['maximum']:.6f}|{a['first1000']:.6f} → {a['last1000']:.6f}|")
now=datetime.datetime.now(datetime.timezone.utc).isoformat();doc=f'''# 恢复78前缀诊断与原Direct33连续观察

{now}，Goal active。承接[完整77/78续训](RL_RECOVERY77_COMPLETE78_RUNNING_20261029.md)和[Direct33冻结评测](RL_DIRECT33_FROZEN_VALIDATION_20261029.md)。本轮不启动或重启科学任务，原78与冻结33持续推进；无79或Direct34。

## 固定前5000次更新

三路各固定前5000条optimizer原字节、连续步号、所有数值有限、独立标量复算和源码逆变换全部通过。该描述性检查登记在训练与前缀可用之后，不冒充前瞻窗口，也不据局部均值宣布收敛。源自77已审工具，仅改变周期/路径/标题；完整78审查与原76–78 PLAN保持不变。

|方法|critic 首1000 → 末1000均值|critic 最大值|actor 首1000 → 末1000均值|
|---|---:|---:|---:|
'''+ '\n'.join(table)+f'''

六栏loss图已实际查看：阻抗critic反复尖峰；导纳均值较平但有孤立尖峰；VMC早期大尖峰且actor仍向负值漂移。VMC第3198125步critic185.416763，随后55.847782、5.147417、3.592860；前后原始记录单独保存并独立核验。日志没有该时刻minibatch逐样本归因，不能据此编造终端样本原因。没有NaN/Inf不代表loss健康，原训练保持，完整78终端/health/loss和76–78 reward结果仍待。

前缀证据 `{P}`；实际图/检查为PLOT_INSPECTION.json，尖峰原记录与算术为PEAK_CONTEXT.json和PEAK_CONTEXT_REVIEW.json。解释器 `{B}/env/bin/python`。未改变学习率、reward、masks、物理、gate、batch65536/UTD1/terminal128、4m replay及23/47历史markers。partial75继续作为不完整曝光保留，原74–76不可评定。

## 连续观察

`{D}` 的11样本/{finished['elapsed']:.3f}秒观察完成，18个原PID/start_ticks身份全部持续live；观察器自然结束不触发科学重启。参数步号到 {steps}，各30条件仍按原流程运行。Direct33完整runtime回合到{frozen}/30，尚未有完整30物理/filter/torque和最终policy不变审查结论；原root reviewer和29→33配对等待继续。该冻结比较仍是一个训练seed/动作seed、训练条件，不能替代指定ESN或最终SPT比较。

## GPU与保存

从上次最终收据之后取原guard全部{gpu['samples']}个5秒样本，四卡最低{gpu['minimum']}%，低于50次数{gpu['below50']}，最新{[x['utilization'] for x in rows[-1]['gpus']]}%。合成保活和科研吞吐分别记账；保活不依赖训练/评测结束状态，用户要求全部科学结束仍继续。原supervisor78710及workers78730–78733保持，历史停机和预热空闲未抹去；不是重启自启服务。

执行主机 `{receipt['host']}`，共享SSD `{B}`。本轮证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，逐成员/hash/Python AST核验通过，[收据](RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029_SAVE.json)。大checkpoint/raw/replay仍SSD，非HDD或arm1全备份；HDD既有LATEST指针仅原位更新不增长。

本轮实际fetch/read main `{receipt['remote_main']}` 和baseline `{receipt['remote_baseline']}`。远端非RL已完整108（Task1/108、Strict0/108）、八球完成并启动v9补采，和本RL不同任务。共享AGENTS/UPDATE_LOG的新增冲突逐段保留双方；其余14远端文件逐字相同。合并commit8d5319b5；没有改动对方实验。GitHub推送以最终实际收据为准，既有HTTPS认证缺失。

下一步等原78完成，检查全loss/health/标签、2304旧终端与新增30终端及实际图、原76–78统计后再决定有限下一阶段；不自动追加79。原冻结33完整后审查原物理及配对结果，不能用旧29代替。Goal保持active。
'''
(R/'docs/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029.md').write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 恢复78前缀异常与原Direct33继续

- [交接](docs/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029.md)。78前三路5000原字节/连续步号/全部有限/独立算术和实际图通过；VMC critic185.416763→55.847782尖峰及actor漂移、阻抗反复尖峰保留，日志不能归因minibatch。仅描述性前缀、未收敛，原全loss/终端/labels/health和76–78保持。
- 11样本/{finished['elapsed']:.3f}秒18原身份live，steps{steps}，冻结33 runtime{frozen}/30、完整审查待；观察器自然结束，科学不重启。Goal active，无79/Direct34，指定ESN/最终比较仍待。
- guard{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研完成仍保载、合成非吞吐。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐成员/AST核验，非HDD/arm1全备份；main{receipt['remote_main'][:8]}/baseline{receipt['remote_baseline'][:8]}已读安全合并非RL新增，认证发布以收据为准，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text();p.write_text((s.split('\n',1)[0]+'\n\n'+entry+s.split('\n',1)[1].lstrip('\n')) if n=='AGENTS.md' else entry+s)
p=R/'HANDOFF.md';p.write_text('> **RL最新：[78前缀异常与Direct33连续观察](docs/RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029.md)。原78/冻结33/全部审查/GPU保活继续，未收敛，勿重复启动。**\n\n'+p.read_text())
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text('> **最新：[78前缀异常与Direct33连续观察](RL_RECOVERY78_PREFIX_DIRECT33_WAIT_20261029.md)。原训练/评测/审查继续，GPU科研结束仍保活。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');old=p.read_bytes();text='# RL '+datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')+'\nACTIVE.78+D33;guardv6.\nSSD '+str(B)+'\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n';data=text.encode();assert len(data)<=len(old)
with p.open('r+b') as f:f.write(data+b' '*(len(old)-len(data)));f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data+b' '*(len(old)-len(data))
print(json.dumps(receipt,indent=2))
