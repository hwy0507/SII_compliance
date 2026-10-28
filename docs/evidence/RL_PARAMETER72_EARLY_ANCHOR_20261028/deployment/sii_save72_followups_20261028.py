from pathlib import Path
import json,hashlib,ast,tarfile,time,socket,subprocess,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
tag='RL_PARAMETER72_EARLY_ANCHOR_20261028'; E=R/'docs/evidence'/tag;E.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
manifest=[]
def copy(p,rel):
 d=E/rel;d.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();d.write_bytes(data);assert d.read_bytes()==data
 if d.suffix=='.py':ast.parse(data)
 manifest.append(dict(path=str(rel),source=str(p),bytes=len(data),sha256=sha(d)))
folders=['runs/vmc72_terminal_anchor_followup_20261028_v1','runs/admittance72_terminal_anchor_followup_20261028_v1','runtime/parameter_task_label_audit72_20261028_v1','runs/parameter_task_label_audit72_20261028_v1','runtime/prepare_parameter73_20261028_v1','runtime/parameter72_followups_snapshot_20261028_v1','runs/parameter72_first5000_20261028_v1']
for folder in folders:
 for p in sorted((B/folder).iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.diff','.npz','.jsonl','.png']:copy(p,Path(folder)/p.name)
for folder in ['runs/parameter72_loss_20261028_v1','runs/parameter_capacity71_73_reward_stability_20261028_v1']:
 for n in ['PLAN.json','LAUNCH.json']:copy(B/folder/n,Path(folder)/n)
 if (B/folder/'SOURCE_REVIEW.json').exists():copy(B/folder/'SOURCE_REVIEW.json',Path(folder)/'SOURCE_REVIEW.json')
for n in ['sii_prepare72_followups_20261028.py','sii_deploy72_labels_20261028.py','sii_deploy72_terminal_waiters_20261028.py','sii_prepare73_restore_20261028.py','sii_audit72_prefix_20261028.py','sii_snapshot72_followups_20261028.py','sii_save72_followups_20261028.py']:copy(Path('/tmp')/n,Path('deployment')/n)
for n in ['guard.py','LAUNCH.json','CONTROL.json']:copy(Path('/tmp/sii_gpu_util_guard_20261028_v5')/n,Path('guard_snapshot')/n)
for m in ['vmc','admittance']:
 p=read(B/f'runs/{m}72_terminal_anchor_followup_20261028_v1/PLAN.json')
 for k,v in p['inputs'].items():
  src=Path(v['path']);assert sha(src)==v['sha256']
  if not any(x['source']==str(src) for x in manifest):copy(src,Path('bound_inputs')/m/(k+'_'+src.name))
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,all_bytes_and_python_ast_verified=True))
snap=read(B/'runtime/parameter72_followups_snapshot_20261028_v1/SNAPSHOT.json')
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S');A=B/'repository'/(tag+'_'+stamp);A.mkdir()
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers()
 for member in members:assert t.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(members),member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),large_artifacts='Original shared SSD; not a full HDD or arm1 backup',source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip())
write(R/'docs'/(tag+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
early=read(B/'runs/parameter72_first5000_20261028_v1/REVIEW.json')
now=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).strftime('%H:%M:%S')
steps='/'.join(str(j['progress']['steps']) for j in snap['learners']);mins='/'.join(str(j['minimum']) for j in snap['guard_stats']);below=[j['below50'] for j in snap['guard_stats']]
doc=f'''# 参数72早期检查、全2154终端基准与73仅恢复准备

2026-10-28 {now} UTC。Goal active，原72训练继续。承接[完整71与准确72启动](RL_PARAMETER71_COMPLETE_20261028.md)。Direct33原训练条件数值收敛判断保留、TaskStrict0/0，不启动34；当前参数RL尚未整体收敛。

## 当前运行

实际主机 `{snap['compute_host']}`，共享SSD `{B}`，env/bin/python。快照三路I/A/V steps {steps}，原身份均live，各30sampler，无完整或失败；没有73训练。固定30×55/41250新增/4m append replay/markers23/47/terminal128/batch65536/UTD1及原LR/masks/reward/物理/gate保持。

|任务|PID / start ticks|登记SHA前缀|
|---|---|---|
'''
for j in snap['learners']:doc+=f"|72 {j['controller']}|{j['pid']} / {j['proc_start_ticks']}|原实际启动|\n"
for k,j in snap['waiters'].items():doc+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|{j['registration_sha256'][:12]}|\n"
j=snap['archive_monitor'];doc+=f"|72归档|{j['pid']} / {j['proc_start_ticks']}|原监视器|\n"
doc+=f'\n完整命令/hash/source差异与核验见[证据manifest](evidence/{tag}/MANIFEST.json)。行动前核验实际身份与输出，勿据旧PID重复启动。\n\n## 前5000更新\n\n原始前缀逐字节一致、步号连续、全数值有限、独立标量均值/极值复核通过；实际loss.png已查看。登记发生在前缀可用之后，非前瞻注册。\n\n|路|critic首→末1000|critic最大值|actor首→末1000|\n|---|---|---:|---|\n'
for m,v in early['methods'].items():
 q=v['metrics']['agent_train/q_loss'];a=v['metrics']['agent_train/actor_loss'];doc+=f"|{m}|{q['first1000']:.9f}→{q['last1000']:.9f}|{q['maximum']:.9f}|{a['first1000']:.9f}→{a['last1000']:.9f}|\n"
doc+='\nI critic在约2.4附近波动、末段略升且有限尖峰较多；A critic/actor近似平坦；V中段和末段critic上升，actor稍升。早期前缀不代表完整72或收敛。算术收据plot_inspected=false保留当时事实，后续图审见PLOT_INSPECTION.json。\n\n## 全2154基准与完成后审查\n\n从已核完整71保存值提取V/A全部2154×57 features，以及indices/reward/mask/Q；独立数组与SSE复算通过，0新网络前向/物理/优化更新。基准包括71新增30，不能与上一报告的旧2124 SSE混用。\n\n|路|全2154 masked SSE|anchor71.npz SHA256|\n|---|---:|---|\n'
for m in ['vmc','admittance']:
 p=B/f'runs/{m}72_terminal_anchor_followup_20261028_v1';v=read(p/'ANCHOR_REVIEW.json');assert read(p/'ANCHOR_SAVED_REVIEW.json')['passed'];doc+=f"|{m}|{v['groups']['all2154']['masked_sse_after']:.12f}|{v['anchor_sha256']}|\n"
doc+='''
72完成后需比较全部2154旧终端及新增30（总2184），保留两个分母。原V五focus[2050526,2299142,2046571,2423133,2423122]及A原66short0600/index2752093与历史背景不变。五源周期/数量映射、完整hash文字保护、逆变换/AST/diff/输入hash通过；capture只更新已核完整71 checkpoint身份。两个CPU53/7200秒等待器已绑定实际72 jobs/归档/source/input，不自动训练。

全标签通用audit_labels.py SHA77e985c2保持原字节，wait72/review_labels72映射核验通过。实际不完整72调用以Incomplete cycle 72非零拒绝，无COMPLETE71_72输出；等待器已部署。完整后仍需独立review_labels72核180标签/90reward对，依赖完整72 loss SAVED_REVIEW，不提前pass。

## 73仅恢复

runtime/prepare_parameter73_20261028_v1四源从原72同时周期映射，保护原68–70、原71–73路径及[71,72,73]列表/完整hash；逆变换/AST/diff通过。wait_prepare.py SHA c4617a04逐字节保持。launcher仍绑定原68–70完整审查与原71–73准确PLAN，不要求未来73结果才能启动73，也不新增科学阈值。

实际缺DECISION73启动已拒绝，未创建73训练目录；CPU53/14400秒等待器只在完整72审查、原learner退出后执行全state/replay/下一65536的check-only。当前未执行该恢复、更没有73训练。73 full-loss准备尚未创建。

原71–73 PLAN c160b5d6与waiter2909145/start42204920保持，5%/近零1/seed2026102855/5000/anchor55不变；原68–70及独立bootstrap补充和全部历史结论保留。近零保护是统计解释限制，不是把reward推离零的训练目标。
'''
doc+=f'''
## GPU与保存

用户要求科研完成后也保留GPU负载。原v5 supervisor3256866及四workers身份保持，STOP/FAILURE不存在；约5秒采样，低于65%增保载。自上次完整交接快照至本次共{snap['guard_window']['samples']}样本，最低{mins}%，低于50计数{below}，最大间隔{snap['guard_window']['max_gap']:.6f}秒。含合成负载，非科学吞吐或每瞬时保证，非跨重启服务。

开工main9e4d6c5701d23f462b75da5c47e45c51c5d74fc3/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d实际fetch/read，保留并行非RL工作，遵循sii-research-sync，无子agent。

共享SSD包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST核验。[保存收据]({tag}_SAVE.json)。大checkpoint/replay/raw留原共享SSD，非HDD/arm1全备份；HDD满只重写既有入口。

下一步保持原72及guard，完成全72 loss/标签/health/终端数组/实际图审查，准确恢复后再决定有限73；不因观察超时重启科学。Goal active。
'''
(R/'docs'/(tag+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-28 — 参数72早期loss、全2154锚点与73仅恢复

- [交接](docs/{tag}.md)。原72身份保持，{now}steps{steps}，各30sampler无失败。前5000原字节/连续步号/全数值/独立算术/实际图通过：critic首末I2.425788→2.465293、A1.182205→1.174083、V.783421→.908691，有限尖峰保留；仅前缀非收敛。
- 全71的2154×57 V/A锚点精确，独立SSE761.227960/1258.445655，0新前向；72预期2184，原focus/两分母保持。V1062827/A1062828等待器已部署，原完整比较待。全标签978935真实不完整72拒绝；73仅恢复997695，无73训练，真实缺DECISION73拒绝。
- 原72全loss708626/原71–73 2909145保持，73launcher保留原68–70审查和71–73 PLAN/列表，不提前要求未来结果或改阈值。{snap['guard_window']['samples']}guard样本min{mins}%、低于50{below}，科学完成也保载，非瞬时保证/跨重启服务。Goal active、Direct34false。
- SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工main9e4d6c57/baselinef6e8f8c实际fetch/read，无子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[72早期检查与73仅恢复](docs/{tag}.md)。原72/71–73继续，无73训练；GPU完成后仍保载，Goal active。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
pointer=f'''# RL 2026-10-28 {now} UTC
ACTIVE. Cycle72 running; GPU guard stays on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{tag}.md
Receipt docs/{tag}_SAVE.json
NO73 training. Guard3256866, not reboot service.
Large data SSD; not HDD/arm1 backup. Direct34=false.
'''
assert len(pointer.encode())<=p.stat().st_size;p.write_text(pointer);assert p.read_text()==pointer
print(json.dumps(receipt,indent=2))
