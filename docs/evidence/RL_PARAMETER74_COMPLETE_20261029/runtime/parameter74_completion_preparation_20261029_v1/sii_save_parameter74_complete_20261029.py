from pathlib import Path
import json,time,hashlib,tarfile,ast,datetime,socket,os,subprocess,math
os.sched_setaffinity(0,{53})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';TAG='RL_PARAMETER74_COMPLETE_20261029'
OBS=B/'runtime/parameter74_completion_observation_20261029_v1';DRV=B/'runtime/parameter74_completion_preparation_20261029_v1';RUN=B/'runs/parameter_capacity_pool30_cycle75_20261026_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
assert read(OBS/'FINISHED.json')['completed'];assert read(RUN/'startup/REVIEW.json')['passed']
decision=read(B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json');assert decision['parent_cycle']==74 and decision['new_cycle']==75
for x in decision['evidence'].values():assert sha(Path(x['path']))==x['sha256']
loss=read(B/'runs/parameter74_loss_20261028_v1/REVIEW.json');full=read(B/'runs/parameter_capacity_pool30_cycle74_review_20261026_v1/REVIEW.json');labels=read(B/'runs/parameter_task_label_audit74_20261028_v1/COMPLETE73_74_SAVED_REVIEW.json');assert labels['passed'] and full['passed']
def identity(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19],state=f[0])
snap=dict(time=time.time(),learners=[],waiters={},guard_processes=[])
for j in read(RUN/'LAUNCH.json')['jobs']:
 d=identity(j);p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();d.update(controller=j['controller'],progress=read(p/'PROGRESS.json'));snap['learners'].append(d)
snap['archive_monitor']=identity(read(RUN/'MONITOR_LAUNCH.json'))
for key,folder in [('loss75','runs/parameter75_loss_20261028_v1'),('window74_76','runs/parameter_capacity74_76_reward_stability_20261029_v1')]:
 p=B/folder;j=read(p/'LAUNCH.json');d=identity(j);assert sha(p/'PLAN.json')==j['plan_sha256'];d['plan_sha256']=j['plan_sha256'];snap['waiters'][key]=d
assert snap['waiters']['window74_76']['pid']==541941 and snap['waiters']['window74_76']['proc_start_ticks']=='43375839'
for pid,ticks in [(3256866,'37410686'),(3256867,'37410690'),(3256868,'37410690'),(3256869,'37410691'),(3256870,'37410693')]:snap['guard_processes'].append(identity(dict(pid=pid,proc_start_ticks=ticks)))
g=Path('/tmp/sii_gpu_util_guard_20261028_v5');assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
observed=[json.loads(l) for l in (OBS/'samples.jsonl').read_text().splitlines()];raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and observed[0]['time']<=json.loads(l)['time']<=snap['time']];gs=[json.loads(l) for l in raw];assert len(gs)>10
snap['guard_stats']=[]
for i in range(4):
 vals=[next(v['utilization'] for v in row['gpus'] if v['gpu']==i) for row in gs];snap['guard_stats'].append(dict(gpu=i,minimum=min(vals),mean=math.fsum(vals)/len(vals),below50=sum(v<50 for v in vals)))
snap.update(guard_samples=len(gs),max_gap=max(b['time']-a['time'] for a,b in zip(gs,gs[1:])));write(OBS/'FINAL_SNAPSHOT.json',snap);(OBS/'gpu_samples.jsonl').write_bytes(b''.join(raw))
now=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).strftime('%H:%M:%S')
pointer=f'''# RL 2026-10-29 {now} UTC
ACTIVE.74 reviewed;75 running. GPU guard on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{TAG}.md
Receipt docs/{TAG}_SAVE.json
Large data SSD. No reboot service.
'''
hdd=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert len(pointer.encode())<=hdd.stat().st_size
sources={Path(x['path']) for x in decision['evidence'].values()}
for name in ['sii_observe74_completion_20261029.py','sii_save_parameter74_complete_20261029.py']:
 p=DRV/name
 if p.exists():assert p.read_bytes()==(Path('/tmp')/name).read_bytes()
 else:p.write_bytes((Path('/tmp')/name).read_bytes())
folders=[OBS,DRV,B/'runtime/prepare_parameter75_20261029_v1',B/'runtime/parameter75_loss_preparation_20261029_v1',B/'runtime/parameter_task_label_audit74_20261028_v1',B/'runs/parameter_capacity_pool30_cycle74_review_20261026_v1',B/'runs/parameter_capacity_pool30_cycle74_review_20261026_v1/health',B/'runs/parameter74_loss_20261028_v1',B/'runs/parameter75_loss_20261028_v1',B/'runs/parameter_task_label_audit74_20261028_v1',B/'runs/parameter_capacity74_76_reward_stability_20261029_v1',RUN,RUN/'startup']+[B/f'runs/{m}74_terminal_anchor_followup_20261028_v1' for m in ['vmc','admittance']]
for folder in folders:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in ['.json','.py','.diff','.png','.npz','.log','.jsonl','.txt'] and p.stat().st_size<=5_000_000:sources.add(p)
for m in ['impedance','admittance','vmc']:
 for n in ['FINISHED.json','episodes.jsonl']:sources.add(B/f'runs/parameter_capacity_pool30_cycle74_20261026_v1/{m}/train'/n)
 for n in ['REGISTRATION.json','TRAINER_PATCH.json','BATCH_SIZE_STAGE_EXECUTION.json','trainer_registered.py']:
  p=RUN/m/n
  if p.exists():sources.add(p)
 for n in read(RUN/m/'REGISTRATION.json')['batch_size_stage']['dependency_hashes']:sources.add(B/'runtime/parameter_capacity_pool30_cycle75_20261026_v1'/n)
for n in ['ARCHIVE_REVIEW_FINISHED.json','LAUNCH.json','MONITOR_LAUNCH.json']:sources.add(B/'runs/parameter_capacity_pool30_cycle74_20261026_v1'/n)
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();d=E/p.relative_to(B);d.parent.mkdir(parents=True,exist_ok=True);d.write_bytes(data);assert d.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(d.relative_to(E)),bytes=len(data),sha256=sha(d)))
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,large_checkpoint_replay_raw_excluded=True))
A=B/'repository'/(TAG+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'));A.mkdir();tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),sha256=sha(tar),bytes=tar.stat().st_size,members=len(manifest)+1,member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),large_artifacts='Original shared SSD; not a full HDD or arm1 backup');write(R/'docs'/(TAG+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
steps='/'.join(str(j['progress']['steps']) for j in snap['learners']);mins='/'.join(str(v['minimum']) for v in snap['guard_stats']);below=[v['below50'] for v in snap['guard_stats']]
report=f'''# 完整第74轮审查与准确有限75接续

2026-10-29 {now} UTC，Goal active。实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器env/bin/python。全74已审查，整体收敛尚未证明，准确接续有限75。Direct33原训练条件数值结论及Task/Strict0/0保持，不启动34。

三路自然完成30×55秒/41250新增/noabort，旧73回放/history保持，新reward重建0误差、网络optimizer有限；全loss/180标签/90reward对/health/终端数组及实际图已审。原30条件/4m append/markers23/47/terminal128/batch65536/UTD1/LR/masks/reward/物理/gates不变；未重新积分全部原始物理。

|方法|最终steps|reward均值|Task/Strict（各30）|critic首→末1000|critic最大值|actor首→末1000|
|---|---:|---:|---|---|---:|---|
'''
for m in ['impedance','admittance','vmc']:
 v=loss['methods'][m];h=v['reward_history'][-1];q=v['loss']['agent_train/q_loss'];a=v['loss']['agent_train/actor_loss'];report+=f"|{m}|{full['methods'][m]['steps']}|{h['reward_mean']:.9f}|{h['task']}/{h['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{a['first1000']:.6f}→{a['last1000']:.6f}|\n"
report+='\n全标签变化（含Task-only，全30条件保持）：\n\n'
for m,v in labels['methods'].items():
 report+=f"- {m} physical-valid73→74 {v['counts']['73']['physical_valid']}→{v['counts']['74']['physical_valid']}（各30）；"
 for c in v['changes']:
  a,z=c['cases'];report+=f"{c['condition']} {','.join(c['fields'])}，Task{a['task']}→{z['task']}、Strict{a['strict']}→{z['strict']}，穿透{a['penetration_mm']:.9f}→{z['penetration_mm']:.9f}mm；"
 report+='\n'
report+='\n全2214旧终端与新增30分别比较，总2244，保留两分母及原关注样本。不新增零误差停止门、不作梯度因果判断。\n\n|路|旧2214 SSE前→后|变化|旧贡献（新分母）|旧贡献（旧分母）|新30贡献|\n|---|---|---:|---:|---:|---:|\n'
for m in ['vmc','admittance']:
 v=read(B/f'runs/{m}74_terminal_anchor_followup_20261028_v1/REVIEW.json');report+=f"|{m}|{v['old2214_sse_before']:.6f}→{v['old2214_sse_after']:.6f}|{100*(v['old2214_sse_ratio']-1):.4f}%|{v['old2214_contribution_after']:.9f}|{v['old2214_after_using_old_denominator']:.9f}|{v['new30_contribution']:.9f}|\n"
for m in ['vmc','admittance']:
 v=read(B/f'runs/{m}74_terminal_anchor_followup_20261028_v1/REVIEW.json');report+='\n'+m+'：'+'；'.join(f"index{x['replay_index']} SSE{x['sse_before']:.6f}→{x['sse_after']:.6f}" for x in v['focus'])+'。\n'
report+='\n续训依据：\n\n'+decision['reason']+'\n\n'
report+=f"DECISION75 SHA `{sha(B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json')}`，绑定{len(decision['evidence'])}项证据。准确74全state/replay/下一65536恢复及实际75 startup通过；只接续一轮，无自动76。\n\n原71–73完整审查及不稳定结论、独立bootstrap与全部历史窗口保持。原74–76 PLANd8c243d9/waiter541941/start43375839保持，未重启或重新登记，完整窗口结果仍待76。近零保护不是将reward推离零的新目标。\n\n|当前任务|PID / start ticks|\n|---|---|\n"
for j in snap['learners']:report+=f"|75 {j['controller']}|{j['pid']} / {j['proc_start_ticks']}|\n"
for k,j in snap['waiters'].items():report+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|\n"
report+=f"\n{now}三路steps {steps}。75全loss已部署；原74–76窗口继续，无自动后续训练。\n\n"
f=read(OBS/'FINISHED.json');report+=f"本轮observer自然结束{f['samples']}样本/{f['duration']:.3f}秒，结束时当前74审查/75恢复就绪{f['all_current_cycle_ready']}；原74–76完整结果就绪{f['future_window74_76_ready']}。保存前全部74实际审查/75恢复另行确认；不以观察时限重启科学。\n\n"
report+=f"从观察开始到当前快照共{len(gs)}guard样本，四卡最低{mins}%，低于50计数{below}，最大间隔{snap['max_gap']:.6f}秒。原v5五进程保持，含合成负载，非纯科学吞吐或每瞬时保证；科研完成仍保载，非跨重启服务。\n\n"
report+=f"开工实际fetch/read maine89ad58a8df24627aa46eed9d967461f4a41372e/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d；保存前再次实际fetch/read main334835c93d5de14b318fed673cb2182b2d3c11c7与未变baseline，阅读非RL正式方向采集与CPU约束修复及原108推进到45/108、另一主机内存压力记录，安全fast-forward保留并行记录；非RL原108继续，未操作其进程。保存源码基线{receipt['source_base_commit']}。遵循sii-research-sync，保留并行非RL工作，无子agent。\n\n共享SSD包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST已核。[收据]({TAG}_SAVE.json)。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份，既有HDD入口更新回读。\n\n下一步保持原75与guard，准备75标签/全终端及76仅恢复审查，跟进原74–76完整统计；以完整reward平稳与loss健康判据继续推进。Goal active。\n"
(R/'docs'/(TAG+'.md')).write_text(report);(A/'HANDOFF.md').write_text(report)
entry=f'''## 2026-10-29 — 完整74审查与准确有限75

- [交接](docs/{TAG}.md)。三路完整74各30×55/41250/noabort，旧73 replay/history保持、新reward重算0、网络optimizer有限；全loss/180标签/90reward对/health/全2214终端及实际图已审，具体改善和退化保留。
- 尚未整体收敛，DECISION75绑定{len(decision['evidence'])}证据，准确74全state/replay/next65536和实际75 startup通过；{now}steps{steps}。75全loss已部署，原74–76 PLAN/waiter保持，无自动76，Direct34false，Goal active。
- 原71–73完整不稳定结论和全部历史窗口、5%/近零1/seed/anchor55均保持。observer自然结束{f['samples']}样本，当前审查就绪{f['all_current_cycle_ready']}，之后另核实际完成，不重启科学。
- {len(gs)}guard样本min{mins}%、低于50{below}，科研完成仍保载。SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工maine89ad58a/baselinef6e8f8c实际fetch/read，无子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[完整74与有限75](docs/{TAG}.md)。75已实际接续，原74–76等待保持；GPU科研完成仍保载，Goal active。**\n\n'+p.read_text())
hdd.write_text(pointer);assert hdd.read_text()==pointer;print(json.dumps(receipt,indent=2))
