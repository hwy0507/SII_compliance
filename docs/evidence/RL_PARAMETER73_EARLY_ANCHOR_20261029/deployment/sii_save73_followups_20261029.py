from pathlib import Path
import json,hashlib,ast,tarfile,time,socket,subprocess,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance'
tag='RL_PARAMETER73_EARLY_ANCHOR_20261029'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
snap=read(B/'runtime/parameter73_followups_snapshot_20261028_v1/SNAPSHOT.json');early=read(B/'runs/parameter73_first5000_20261028_v1/REVIEW.json')
assert read(B/'runtime/parameter73_followups_preparation_20261028_v1/DEPLOYMENT_STATIC_REVIEW.json')['passed']
assert read(B/'runs/parameter73_first5000_20261028_v1/PLOT_INSPECTION.json')['actual_image_viewed']
assert read(B/'runs/parameter73_first5000_20261028_v1/SAVED_REVIEW.json')['passed']
now=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).strftime('%H:%M:%S')
pointer=f'''# RL 2026-10-29 {now} UTC
ACTIVE. Cycle73 running; GPU guard stays on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{tag}.md
Receipt docs/{tag}_SAVE.json
No74 training. No reboot service. Large data SSD.
'''
hdd=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert len(pointer.encode())<=hdd.stat().st_size
E=R/'docs/evidence'/tag;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 d=E/rel;d.parent.mkdir(parents=True,exist_ok=True);data=p.read_bytes();d.write_bytes(data);assert d.read_bytes()==data
 if d.suffix=='.py':ast.parse(data)
 manifest.append(dict(path=str(rel),source=str(p),bytes=len(data),sha256=sha(d)))
folders=['runs/vmc73_terminal_anchor_followup_20261028_v1','runs/admittance73_terminal_anchor_followup_20261028_v1','runtime/parameter_task_label_audit73_20261028_v1','runs/parameter_task_label_audit73_20261028_v1','runtime/prepare_parameter74_20261028_v1','runtime/parameter73_followups_snapshot_20261028_v1','runtime/parameter73_followups_preparation_20261028_v1','runs/parameter73_first5000_20261028_v1']
for folder in folders:
 for p in sorted((B/folder).iterdir()):
  if p.is_file() and p.suffix in ['.py','.json','.diff','.npz','.jsonl','.png']:copy(p,Path(folder)/p.name)
for folder in ['runs/parameter73_loss_20261028_v1','runs/parameter_capacity71_73_reward_stability_20261028_v1']:
 for n in ['PLAN.json','LAUNCH.json']:copy(B/folder/n,Path(folder)/n)
for n in ['sii_prepare73_followups_20261028.py','sii_deploy73_labels_20261028.py','sii_deploy73_terminal_waiters_20261028.py','sii_prepare74_restore_20261028.py','sii_make74_restore_preparation_20261029.py','sii_audit73_prefix_20261028.py','sii_snapshot73_followups_20261028.py','sii_review73_deployment_20261029.py','sii_save73_followups_20261029.py']:copy(Path('/tmp')/n,Path('deployment')/n)
for n in ['guard.py','LAUNCH.json','CONTROL.json']:copy(Path('/tmp/sii_gpu_util_guard_20261028_v5')/n,Path('guard_snapshot')/n)
for m in ['vmc','admittance']:
 plan=read(B/f'runs/{m}73_terminal_anchor_followup_20261028_v1/PLAN.json')
 for k,v in plan['inputs'].items():
  p=Path(v['path']);assert sha(p)==v['sha256']
  if not any(x['source']==str(p) for x in manifest):copy(p,Path('bound_inputs')/m/(k+'_'+p.name))
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,all_bytes_and_python_ast_verified=True))
A=B/'repository'/(tag+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'));A.mkdir();archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 members=t.getmembers()
 for m in members:assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),sha256=sha(archive),bytes=archive.stat().st_size,members=len(members),member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),large_artifacts='Original shared SSD; not a full HDD or arm1 backup',source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip())
write(R/'docs'/(tag+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
steps='/'.join(str(j['progress']['steps']) for j in snap['learners']);mins='/'.join(str(j['minimum']) for j in snap['guard_stats']);below=[j['below50'] for j in snap['guard_stats']]
doc=f'''# 第73轮早期loss、全2184终端基准与74仅恢复准备

2026-10-29 {now} UTC，Goal active。承接[完整72与准确73接续](RL_PARAMETER72_COMPLETE_20261029.md)。原73三路训练继续，当前尚未整体收敛。Direct33原训练条件数值结论保持、Task/Strict0/0，不启动34。

实际主机 `{snap['compute_host']}`，共享SSD `{B}`，解释器env/bin/python。三路I/A/V steps {steps}，原PID/start ticks身份均live，各30sampler，无失败。固定30×55秒/41250新增/4m append/markers23/47/terminal128/batch65536/UTD1及原LR/masks/reward/物理/gate保持。

|任务|PID / start ticks|登记SHA前缀|
|---|---|---|
'''
for j in snap['learners']:doc+=f"|73 {j['controller']}|{j['pid']} / {j['proc_start_ticks']}|原启动|\n"
for k,j in snap['waiters'].items():doc+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|{j['registration_sha256'][:12]}|\n"
j=snap['archive_monitor'];doc+=f"|73归档|{j['pid']} / {j['proc_start_ticks']}|原监视器|\n"
doc+='\n前5000原字节前缀、连续步号、全数值有限、独立算术与实际loss图已审。登记发生在前缀可用之后，非前瞻注册。\n\n|路|critic首→末1000|critic最大值|actor首→末1000|\n|---|---|---:|---|\n'
for m,v in early['methods'].items():
 q=v['metrics']['agent_train/q_loss'];a=v['metrics']['agent_train/actor_loss'];doc+=f"|{m}|{q['first1000']:.9f}→{q['last1000']:.9f}|{q['maximum']:.9f}|{a['first1000']:.9f}→{a['last1000']:.9f}|\n"
doc+='\n三路critic前缀末均值较低，但有限尖峰仍在，I actor略升、A/V略降。不能用前缀替代完整73 loss或原71–73窗口，也不覆盖72末段异常。独立算术收据保留当时plot_inspected=false，实际图审另见PLOT_INSPECTION.json。\n\n全72的V/A全部2184×57终端features/indices/reward/mask/Q精确提取，独立数组及标量SSE通过，0新网络前向/物理/优化更新。此基准包括72新增30条，不能与完整72报告只比较旧2154条的SSE1328.573581/6731.893154混用。\n\n|路|全2184 masked SSE|anchor72.npz SHA256|\n|---|---:|---|\n'
for m in ['vmc','admittance']:
 p=B/f'runs/{m}73_terminal_anchor_followup_20261028_v1';v=read(p/'ANCHOR_REVIEW.json');assert read(p/'ANCHOR_SAVED_REVIEW.json')['passed'];doc+=f"|{m}|{v['groups']['all2184']['masked_sse_after']:.12f}|{v['anchor_sha256']}|\n"
doc+='''
73完成后比较全部2184旧终端和新增30（总2214），保留旧/新分母。原V五focus[2050526,2299142,2046571,2423133,2423122]及A原66short0600/index2752093保持。五源码/hash/逆映射/AST/输入hash均审查；独立静态检查核对PLAN与AST读取focus，两个CPU53/7200秒等待器绑定实际73原进程，不自动训练。

全标签通用审计器保持原字节。真实不完整73调用被拒绝且未生成COMPLETE72_73输出；等待器已部署。完整后仍需运行review_labels73，核180标签/90reward对，并要求完整73 loss SAVED_REVIEW。

第74轮仅恢复等待器已部署：原wait_prepare.py逐字节不变，只在完整73审查且原learner退出后执行全state/replay/下一65536 check-only。实际缺DECISION74调用拒绝，没有74训练目录或训练。launcher继续绑定原68–70完整审查及原71–73 PLAN；因为73结束后原窗口应齐全，有限74启动还必须绑定原71–73完整REVIEW、独立算术和实际图审。这是兑现原窗口审查要求，没有改变原科学阈值。当前74恢复尚未执行，74全loss准备也尚未创建。

原71–73 PLAN c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf、waiter2909145/start42204920保持，5%/近零1/seed2026102855/5000/anchor55及全部历史结论不变。近零保护是相对统计解释限制，不是把reward推离零的新目标。
'''
doc+=f'''
自上次完整交接快照至本次共{snap['guard_window']['samples']}个guard样本，四卡最低{mins}%，低于50计数{below}，最大间隔{snap['guard_window']['max_gap']:.6f}秒。原v5 supervisor3256866及四workers身份保持，STOP/FAILURE不存在。含合成负载，非纯科学吞吐或每瞬时保证；科研完成后也保载，非跨重启服务。

开工实际fetch/read main24a17b0b89cc664e0aac960b610c8eced4417d53/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保存前再次核验未变。遵循sii-research-sync，保留并行非RL工作，无子agent。

[证据manifest](evidence/{tag}/MANIFEST.json)。共享SSD包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST核验。[保存收据]({tag}_SAVE.json)。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份；HDD满只重写既有入口。

下一步保持原73与guard，收齐完整73 loss/标签/health/终端和原71–73窗口，独立复算并实际看图，再决定是否需要有限74。不得因观察结束重启原科学任务。
'''
(R/'docs'/(tag+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 参数73早期loss、全2184锚点与74仅恢复

- [交接](docs/{tag}.md)。原73身份保持，{now}steps{steps}，各30sampler无失败。前5000原字节/连续步号/全数值/独立算术及实际图通过；critic首末I2.572366→2.395603、A2.417616→1.874660、V1.217786→1.046713，max16.821136/41.378468/20.496380尖峰保留，仅前缀非收敛。
- 全72的2184×57 V/A锚点精确，独立SSE8916.873140/24329.209051，含72新增30、0新前向；73预期2214，原focus/两分母保持。两个终端及全标签等待器已部署，真实不完整73拒绝；74仅恢复等待中，无74训练，真实缺DECISION74拒绝。
- 原73全loss及原71–73等待保持；74launcher绑定原68–70及原71–73PLAN，并要求原71–73完整审查/独立算术/实际图后才有限74，不改阈值。{snap['guard_window']['samples']}guard样本min{mins}%、低于50{below}，科研完成也保载，非瞬时保证/重启服务。Goal active、Direct34false。
- SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工及保存前main24a17b0b/baselinef6e8f8c实际fetch/read，无子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[73早期loss与74仅恢复](docs/{tag}.md)。原73/71–73继续，无74训练；GPU科研结束后仍保载，Goal active。**\n\n'+p.read_text())
hdd.write_text(pointer);assert hdd.read_text()==pointer
print(json.dumps(receipt,indent=2))
