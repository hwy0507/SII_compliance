from pathlib import Path
import json,hashlib,ast,tarfile,time,socket,subprocess,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';TAG='RL_PARAMETER74_EARLY_ANCHOR_20261029'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
S=B/'runtime/parameter74_followups_snapshot_20261029_v1';D=B/'runtime/parameter74_followups_preparation_20261029_v1';P=B/'runs/parameter74_first5000_20261028_v1';snap=read(S/'SNAPSHOT.json');early=read(P/'REVIEW.json')
assert time.time()-snap['time']<600 and read(D/'DEPLOYMENT_STATIC_REVIEW.json')['passed']
assert read(P/'SAVED_REVIEW.json')['passed'] and read(P/'PLOT_INSPECTION.json')['actual_image_viewed']
for j in snap['learners']+[snap['archive_monitor']]+list(snap['waiters'].values())+snap['guard_processes']:
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z'
now=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).strftime('%H:%M:%S')
pointer=f'''# RL 2026-10-29 {now} UTC
ACTIVE.74 running;75 restore only. GPU guard on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{TAG}.md
Receipt docs/{TAG}_SAVE.json
Large data SSD. No reboot service.
'''
hdd=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert len(pointer.encode())<=hdd.stat().st_size,(len(pointer.encode()),hdd.stat().st_size)
folders=[D,S,P,B/'runtime/prepare_parameter75_20261029_v1',B/'runtime/parameter_task_label_audit74_20261028_v1',B/'runs/parameter_task_label_audit74_20261028_v1']+[B/f'runs/{m}74_terminal_anchor_followup_20261028_v1' for m in ['vmc','admittance']]
sources=set()
for folder in folders:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in ['.py','.json','.diff','.npz','.png','.jsonl'] and p.stat().st_size<5_000_000:sources.add(p)
for folder in ['runs/parameter74_loss_20261028_v1','runs/parameter_capacity74_76_reward_stability_20261029_v1']:
 for name in ['PLAN.json','LAUNCH.json']:sources.add(B/folder/name)
for name in ['PLAN.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json','PLOT_INSPECTION.json']:sources.add(B/'runs/parameter_capacity71_73_reward_stability_20261028_v1'/name)
for m in ['vmc','admittance']:
 for x in read(B/f'runs/{m}74_terminal_anchor_followup_20261028_v1/PLAN.json')['inputs'].values():
  p=Path(x['path']);assert sha(p)==x['sha256'];assert p.stat().st_size<5_000_000;sources.add(p)
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 data=p.read_bytes();dest=E/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);assert dest.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(dest)))
for p in sorted(sources):copy(p,p.relative_to(B))
for name in ['sii_prepare74_followup_drivers_20261029.py','sii_prepare74_followups_20261028.py','sii_deploy74_labels_20261028.py','sii_deploy74_terminal_waiters_20261028.py','sii_audit74_prefix_20261028.py','sii_prepare75_restore_20261029.py','sii_review74_followups_20261029.py','sii_snapshot74_followups_20261029.py','sii_save74_followups_20261029.py']:copy(Path('/tmp')/name,Path('deployment')/name)
for name in ['guard.py','LAUNCH.json','CONTROL.json']:copy(Path('/tmp/sii_gpu_util_guard_20261028_v5')/name,Path('guard_snapshot')/name)
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,all_bytes_and_python_ast_verified=True))
A=B/'repository'/(TAG+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'));A.mkdir();archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 for member in t.getmembers():assert t.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(manifest)+1,member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),large_artifacts='Original shared SSD; not a full HDD or arm1 backup')
write(R/'docs'/(TAG+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
steps='/'.join(str(j['progress']['steps']) for j in snap['learners']);mins='/'.join(str(j['minimum']) for j in snap['guard_stats']);below=[j['below50'] for j in snap['guard_stats']]
doc=f'''# 第74轮早期loss、全2214终端锚点及75仅恢复准备

2026-10-29 {now} UTC，Goal active。承接[完整73及准确有限74](RL_PARAMETER73_COMPLETE_20261029.md)。第74轮原三路继续，尚未整体收敛；Direct33原训练条件数值结论及Task/Strict0/0保持，不启动34。

实际主机 `{snap['compute_host']}`；共享SSD `{B}`；解释器env/bin/python。I/A/V steps {steps}，原PID/start ticks均live、各30sampler，无失败。原30×55秒/41250新增、4m append、markers23/47、terminal128、batch65536、UTD1及LR/masks/reward/物理/gate不变。

|当前任务|PID / start ticks|登记SHA前缀|
|---|---|---|
'''
for j in snap['learners']:doc+=f"|74 {j['controller']}|{j['pid']} / {j['proc_start_ticks']}|原启动|\n"
for k,j in snap['waiters'].items():doc+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|{j['registration_sha256'][:12]}|\n"
doc+='\n前5000原日志前缀逐字节、连续步号、全数值有限、独立算术及实际图已审。登记发生于前缀可用后，不称前瞻注册；完整74及74–76结论仍待。\n\n|路|critic首→末1000|critic最大值|actor首→末1000|\n|---|---|---:|---|\n'
for m,v in early['methods'].items():
 q=v['metrics']['agent_train/q_loss'];a=v['metrics']['agent_train/actor_loss'];doc+=f"|{m}|{q['first1000']:.9f}→{q['last1000']:.9f}|{q['maximum']:.9f}|{a['first1000']:.9f}→{a['last1000']:.9f}|\n"
doc+='\nI前缀critic近似平稳但保留尖峰；A均值下降；V末段均值略升。三路actor略降。不能据此前缀宣称全轮loss健康、抹去73尾段尖峰或改原71–73未收敛结论。\n\n全73的2214×57 features/indices/reward/mask/Q逐元素核验，独立标量SSE通过；Q来自已核验73结果，0新网络前向/物理/优化更新。此锚点包含73新增30条，不能与完整73对旧2184条的SSE2776.925280/6111.633635混用。\n\n|路|全2214 masked SSE|anchor73.npz SHA256|\n|---|---:|---|\n'
for m in ['vmc','admittance']:
 v=read(B/f'runs/{m}74_terminal_anchor_followup_20261028_v1/ANCHOR_REVIEW.json');doc+=f"|{m}|{v['groups']['all2214']['masked_sse_after']:.12f}|{v['anchor_sha256']}|\n"
doc+='''
完整74比较全部2214旧终端及新30（预计总2244），保留旧/新分母。原V五focus[2050526,2299142,2046571,2423133,2423122]与A原66short0600/index2752093保持。两终端等待器已部署，source/inputs/PLAN hash和AST消费focus已独立静态审查。

全标签通用审计器与73逐字节相同。真实不完整74调用拒绝且未生成COMPLETE73_74；等待器已部署。完整后需执行runtime/parameter_task_label_audit74_20261028_v1/review_labels74.py，要求全74 loss SAVED_REVIEW，并核全180标签/90reward对。

第75轮仅恢复等待器已部署，路径runtime/prepare_parameter75_20261029_v1；wait_prepare.py与原74逐字节相同。仅完整74全审且原三learner退出后，执行全state/replay/下一65536 check-only。真实缺DECISION75调用已拒绝，无75训练目录/训练。launcher保留原68–70和原71–73完整审查/独立算术/实际图及原71–73 PLAN，并额外绑定原74–76 PLAN；不提前要求未来74–76结果。75实际恢复、续训决定和全loss准备均尚待。

原71–73 PLAN c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf及完整不稳定结论保留；原74–76 PLAN d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703及waiter541941/start43375839保持。原5%/近零1/seed2026102855/5000/anchor55及全部历史结论不变；近零保护不是将reward推离零的新目标。
'''
doc+=f'''
从上次完整交接快照起{snap['guard_window']['samples']}个guard样本，四卡最低{mins}%，低于50计数{below}，最大间隔{snap['guard_window']['max_gap']:.6f}秒。原v5五进程身份保持，STOP/FAILURE不存在，科研完成后继续保载；含合成负载，非纯科学吞吐/每瞬时保证/跨重启服务。

开工实际fetch/read main c0dd97129e1b4f744bc223f970dc67be29eef294 与baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d；保存源码基线{receipt['source_base_commit']}。遵循sii-research-sync，保留并行非RL工作，无子agent。

共享SSD包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST已核。[收据]({TAG}_SAVE.json)。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份；既有HDD入口更新回读。

下一步保持原74与六等待器和guard，准备75全loss；待完整74 loss/labels/health/终端全审、实际看图与准确恢复后再决定有限75。第74–76窗口保持原计划，观察时限不授权科学重启。Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 参数74早期loss、全2214锚点与75仅恢复

- [交接](docs/{TAG}.md)。原74三路身份保持，{now}steps{steps}，各30sampler无失败。前5000原字节/连续步号/全数值/独立算术及实际图通过；I/A critic略降、V略升，有限尖峰保留，仅前缀非收敛。
- 全73的2214×57 V/A锚点精确，独立SSE6280.163604/6328.963926，含73新增30、0新前向；74预期2244，原focus/两分母保持。两个终端及全标签等待器已部署，真实不完整74拒绝。
- 75仅恢复等待中，原wait源保持，无75训练，真实缺DECISION75拒绝。75launcher保留原68–70和原71–73全审/PLAN，新增原74–76准确PLAN绑定，不提前要求未来结果。原74全loss及74–76等待保持，阈值不变。
- {snap['guard_window']['samples']}guard样本min{mins}%、低于50{below}，科研完成仍保载，非瞬时保证/重启服务。SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工mainc0dd9712/baselinef6e8f8c实际fetch/read，无子agent，Goal active、Direct34false。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[74早期loss、全终端与75仅恢复](docs/{TAG}.md)。原74/74–76继续，无75训练；GPU科研结束仍保载，Goal active。**\n\n'+p.read_text())
hdd.write_text(pointer);assert hdd.read_text()==pointer;print(json.dumps(receipt,indent=2))
