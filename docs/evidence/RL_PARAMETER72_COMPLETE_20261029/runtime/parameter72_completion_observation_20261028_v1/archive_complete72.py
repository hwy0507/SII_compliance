from pathlib import Path
import json,time,hashlib,tarfile,ast,datetime,socket,os,subprocess
os.sched_setaffinity(0,{53})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');repo=B/'repository/SII_compliance';name='RL_PARAMETER72_COMPLETE_20261029';run=B/'runs/parameter_capacity_pool30_cycle73_20261026_v1';obs=B/'runtime/parameter72_completion_observation_20261028_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
startup=read(run/'startup/REVIEW.json');assert startup['passed']
assert read(obs/'FINISHED.json')['completed']
# The observer's bounded deadline does not imply scientific completion.
for current_ready in [B/'runs/parameter_capacity_pool30_cycle72_20261026_v1/ARCHIVE_REVIEW_FINISHED.json',B/'runs/parameter72_loss_20261028_v1/FINISHED.json',B/'runs/parameter_task_label_audit72_20261028_v1/FINISHED72.json',B/'runs/vmc72_terminal_anchor_followup_20261028_v1/FINISHED.json',B/'runs/admittance72_terminal_anchor_followup_20261028_v1/FINISHED.json']:
 assert read(current_ready)['completed']
assert read(B/'runtime/prepare_parameter73_20261028_v1/parameter_FINISHED.json')['prepared']
observed=[json.loads(l) for l in (obs/'samples.jsonl').read_text().splitlines()]
assert 0<len(observed)<=61 and all(r['guard_live'] and all(v['live'] or v['finished'] for v in r['learners'].values()) for r in observed)
loss=read(B/'runs/parameter72_loss_20261028_v1/REVIEW.json');decision=read(B/'runtime/prepare_parameter73_20261028_v1/DECISION73.json')
for v in decision['evidence'].values():assert sha(Path(v['path']))==v['sha256']
launch=read(run/'LAUNCH.json');snapshot=dict(time=time.time(),learners=[])
for j in launch['jobs']:
 p=Path(f"/proc/{j['pid']}/stat");st=p.read_text().rsplit(')',1)[1].split();assert st[19]==j['proc_start_ticks'] and st[0]!='Z'
 root=run/j['controller']/'train';assert not (root/'FAILURE.json').exists()
 snapshot['learners'].append(dict(controller=j['controller'],pid=j['pid'],start_ticks=st[19],state=st[0],progress=read(root/'PROGRESS.json')))
raw=[json.loads(x) for x in (obs/'samples.jsonl').read_text().splitlines()];guard=Path('/tmp/sii_gpu_util_guard_20261028_v5');gs=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];gs=[x for x in gs if raw[0]['time']<=x['time']<=snapshot['time']]
snapshot['guard_stats']=[]
for i in range(4):
 v=[next(g['utilization'] for g in r['gpus'] if g['gpu']==i) for r in gs];snapshot['guard_stats'].append(dict(gpu=i,minimum=min(v),mean=sum(v)/len(v),below50=sum(x<50 for x in v)))
snapshot['gpu_samples']=len(gs);snapshot['max_sample_gap']=max(b['time']-a['time'] for a,b in zip(gs,gs[1:]));snapshot['guard_processes']=[]
for pid,ticks in [(3256866,'37410686'),(3256867,'37410690'),(3256868,'37410690'),(3256869,'37410691'),(3256870,'37410693')]:
 st=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();assert st[19]==ticks and st[0]!='Z';snapshot['guard_processes'].append(dict(pid=pid,start_ticks=ticks,state=st[0]))
snapshot['waiters']={}
for key,folder in [('loss73','runs/parameter73_loss_20261028_v1'),('window71_73','runs/parameter_capacity71_73_reward_stability_20261028_v1')]:
 p=B/folder;j=read(p/'LAUNCH.json');st=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert st[19]==j['proc_start_ticks'] and st[0]!='Z'
 assert sha(p/'PLAN.json')==j['plan_sha256'];snapshot['waiters'][key]=j
assert not (guard/'STOP').exists() and not (guard/'FAILURE.json').exists()
(obs/'FINAL_SNAPSHOT.json').write_text(json.dumps(snapshot,indent=2)+'\n');(obs/'gpu_samples.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in gs))
sources=set(Path(v['path']) for v in decision['evidence'].values())
(obs/'inflight_prefix_check.py').write_bytes(Path('/tmp/sii_check72_inflight_20261029.py').read_bytes());sources.add(obs/'inflight_prefix_check.py')
(obs/'archive_complete72.py').write_bytes(Path(__file__).read_bytes());sources.add(obs/'archive_complete72.py')
folders=[obs,obs/'tail_inflight',B/'runtime/parameter72_completion_observation_driver_20261028_v1',B/'runs/parameter_capacity68_70_reward_stability_20261028_v1',B/'runs/parameter_capacity71_73_reward_stability_20261028_v1',B/'runtime/prepare_parameter73_20261028_v1',B/'runtime/parameter73_loss_preparation_20261028_v1',B/'runtime/parameter_task_label_audit72_20261028_v1',B/'runs/parameter_capacity_pool30_cycle72_review_20261026_v1',B/'runs/parameter_capacity_pool30_cycle72_review_20261026_v1/health',B/'runs/parameter72_loss_20261028_v1',B/'runs/parameter73_loss_20261028_v1',B/'runs/parameter_task_label_audit72_20261028_v1',run,run/'startup']+[B/f'runs/{m}72_terminal_anchor_followup_20261028_v1' for m in ['vmc','admittance']]
for p in folders:
 if not p.exists():continue
 for f in p.iterdir():
  if f.is_file() and f.suffix in ['.json','.py','.diff','.png','.npz','.log','.jsonl'] and f.stat().st_size<=5_000_000:sources.add(f)
for m in ['impedance','admittance','vmc']:
 for n in ['FINISHED.json','episodes.jsonl']:
  sources.add(B/f'runs/parameter_capacity_pool30_cycle72_20261026_v1/{m}/train'/n)
for m in ['impedance','admittance','vmc']:
 for n in ['REGISTRATION.json','TRAINER_PATCH.json','BATCH_SIZE_STAGE_EXECUTION.json','trainer_registered.py']:
  f=run/m/n
  if f.exists():sources.add(f)
 for n in read(run/m/'REGISTRATION.json')['batch_size_stage']['dependency_hashes']:
  sources.add(B/'runtime/parameter_capacity_pool30_cycle73_20261026_v1'/n)
for n in ['ARCHIVE_REVIEW_FINISHED.json','LAUNCH.json','MONITOR_LAUNCH.json']:
 sources.add(B/'runs/parameter_capacity_pool30_cycle72_20261026_v1'/n)
(obs/'decision_and_launch73.py').write_bytes(Path('/tmp/sii_decide_launch73_20261028.py').read_bytes());sources.add(obs/'decision_and_launch73.py')
ev=repo/'docs/evidence'/name;ev.mkdir();manifest=[]
for src in sorted(sources):
 data=src.read_bytes();dst=ev/src.relative_to(B);dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data);assert dst.read_bytes()==data
 if src.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(src),relative=str(dst.relative_to(ev)),bytes=len(data),sha256=sha(dst)))
(ev/'MANIFEST.json').write_text(json.dumps(dict(time=time.time(),files=manifest,large_checkpoint_replay_raw_excluded=True),indent=2)+'\n')
pack=B/'repository'/f'{name}_{datetime.datetime.now(datetime.timezone.utc).strftime("%H%M%S")}';pack.mkdir();tar=pack/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as tf:
 for src in sorted(ev.rglob('*')):
  if src.is_file():tf.add(src,arcname=str(src.relative_to(ev)),recursive=False)
with tarfile.open(tar,'r:gz') as tf:
 for m in tf.getmembers():assert tf.extractfile(m).read()==(ev/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),sha256=sha(tar),bytes=tar.stat().st_size,members=len(manifest)+1,member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),source_base_commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip(),large_checkpoint_replay_raw_on_shared_ssd=True,not_hdd_or_arm1_full_backup=True)
(repo/'docs'/f'{name}_SAVE.json').write_text(json.dumps(receipt,indent=2)+'\n')
now=datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S');ststr='/'.join(str(x['progress']['steps']) for x in snapshot['learners']);mins='/'.join(str(x['minimum']) for x in snapshot['guard_stats']);low=[x['below50'] for x in snapshot['guard_stats']]
window=read(B/'runs/parameter_capacity68_70_reward_stability_20261028_v1/REVIEW.json');labels=read(B/'runs/parameter_task_label_audit72_20261028_v1/COMPLETE71_72_SAVED_REVIEW.json')
review=read(B/'runs/parameter_capacity_pool30_cycle72_review_20261026_v1/REVIEW.json')
report=f'''# 完整第72轮审查与准确有限第73轮接续

2026-10-29 {now} UTC，Goal active。主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器env/bin/python。本轮完整审查72、独立核验、实际看图后决定准确接续有限73，非整体收敛声明。Direct33原训练条件数值收敛判断保持、TaskStrict0/0，不启动34。

## 完整72与原协议

三路原learner均自然完成30×55秒、41250新交互、noabort；全部旧71 replay字段/history保持，新reward按原冻结日志重建最大误差0，网络/optimizer有限。固定4m append、markers23/47、terminal128、batch65536、UTD1、原LR/masks/reward/物理/gates不变。未独立重积分全部原始物理。

|方法|最终steps|平均reward|Task/Strict（各30）|critic首→末1000|critic最大值|actor首→末1000|
|---|---:|---:|---|---|---:|---|
'''
for m in ['impedance','admittance','vmc']:
 v=loss['methods'][m];h=v['reward_history'][-1];q=v['loss']['agent_train/q_loss'];a=v['loss']['agent_train/actor_loss'];r=review['methods'][m]
 report+=f"|{m}|{r['steps']}|{h['reward_mean']:.9f}|{h['task']}/{h['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{a['first1000']:.6f}→{a['last1000']:.6f}|\n"
report+='\n全41250 optimizer连续/全字段有限，独立保存算术、全180标签/90reward对复核通过。实际loss和health图已查看；有限值不能单独证明收敛。完整标签变化如下（保留Task-only变化）：\n\n'
for m,v in labels['methods'].items():
 report+=f"- {m}：physical-valid71→72 {v['counts']['71']['physical_valid']}→{v['counts']['72']['physical_valid']}（各30）；"
 if not v['changes']:report+='Task/Strict/abort标签无变化。\n'
 else:
  for c in v['changes']:
   a,z=c['cases'];report+=f"{c['condition']} {','.join(c['fields'])}，Task {a['task']}→{z['task']}、Strict {a['strict']}→{z['strict']}，穿透{a['penetration_mm']:.9f}→{z['penetration_mm']:.9f}mm；"
  report+='\n'
report+='\n## 全2154旧终端对比\n\n从完整71提取的全部2154条固定终端输入与本轮新30分别报告，总2184，不与旧2124口径混用。独立保存数组/标量和实际图已核验；原V五focus及A原66short0600保持。\n\n|路|旧2154 SSE前→后|变化|旧贡献（新总分母）|旧贡献（旧分母）|新30贡献|\n|---|---|---:|---:|---:|---:|\n'
for m in ['vmc','admittance']:
 p=B/f'runs/{m}72_terminal_anchor_followup_20261028_v1';v=read(p/'REVIEW.json')
 report+=f"|{m}|{v['old2154_sse_before']:.6f}→{v['old2154_sse_after']:.6f}|{100*(v['old2154_sse_ratio']-1):.4f}%|{v['old2154_contribution_after']:.9f}|{v['old2154_after_using_old_denominator']:.9f}|{v['new30_contribution']:.9f}|\n"
report+='\n具体focus变化及图观察：\n\n'
for m in ['vmc','admittance']:
 p=B/f'runs/{m}72_terminal_anchor_followup_20261028_v1';v=read(p/'REVIEW.json')
 report+=f"- {m}："+'；'.join(f"index{x['replay_index']} SSE{x['sse_before']:.6f}→{x['sse_after']:.6f}" for x in v['focus'])+'。\n'
report+='\n不作历史梯度因果判断，不把零终端误差新增为训练门槛。\n\n## 续训决定与当前73\n\n'+decision['reason']+'\n\n'
report+=f"DECISION73 SHA `{sha(B/'runtime/prepare_parameter73_20261028_v1/DECISION73.json')}`，绑定{len(decision['evidence'])}项证据。准确72全state/replay/下一65536恢复通过，有限73实际启动且startup通过；不重置optimizer/replay/RNG/history、不导入辅助权重，无自动73。\n\n"
report+='原68–70结果及独立bootstrap补充保持；近零保护限制相对统计解释，不是将reward推离零的新目标。原71–73 PLAN c160b5d6及原waiter保持，当前已有完整71和72，不能提前宣布三轮窗口通过。\n\n|当前任务|PID / start ticks|\n|---|---|\n'
for j in snapshot['learners']:report+=f"|73 {j['controller']}|{j['pid']} / {j['start_ticks']}|\n"
for k,j in snapshot['waiters'].items():report+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|\n"
report+=f"\n{now}快照三路steps {ststr}，新73全loss等待器已部署，原71–73等待器未重启。行动前核验实时PID/start ticks与输出。\n\n"
report+=f'''## GPU、观察与保存

在途检查曾核验I/A/V各25086/25535/25564条完整日志前缀数值有限、步号连续，最新1000原字节及独立算术通过；该前缀只代表当时，后续完整41250审查已保留A/V末段新增尖峰，不能用早期前缀掩盖它们。

本轮完成边界observer按最多1800秒/30秒登记，实际{len(observed)}样本、{read(obs/'FINISHED.json')['duration']:.3f}秒，观察结束时全部当前审查就绪标记为{read(obs/'FINISHED.json')['all_science_ready']}，本报告保存前另行确认全72审查/标签/终端/73仅恢复已实际完成；原71–73未来窗口不被误作本轮必须完成项。观察本身不启动或停止科学进程。

从观察开始到当前快照共{snapshot['gpu_samples']}个guard样本，四卡最低{mins}%，低于50计数{low}，最大间隔{snapshot['max_sample_gap']:.6f}秒。原v5五进程身份保持、STOP/FAILURE不存在。含合成占用，非科学吞吐或每瞬时保证；用户要求科研完成后仍保载，继续保持，非跨重启服务。

开工实际fetch/read main73d9239070c982b546c39f17e1424a73d435d60c、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保留并行非RL工作。收尾再次fetch/read main80efd331并安全fast-forward，保留非RL完整18/108及同教师历史诊断，未操作其进程。遵循sii-research-sync，无子agent。

共享SSD归档 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST核验。[保存收据]({name}_SAVE.json)。大checkpoint/replay/raw留原共享SSD；HDD满只重写既有入口，非HDD/arm1全备份。

下一步保持原73与guard；准备73完整标签及终端审查、等待原71–73，继续基于完整结果判断reward稳定和loss健康，不因有界观察结束重启科学任务。Goal active。
'''
(repo/'docs'/f'{name}.md').write_text(report);(pack/'HANDOFF.md').write_text(report);(pack/'RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
entry=f'''## 2026-10-29 — 完整72独立审查与准确有限73

- [交接](docs/{name}.md)。三路完整72各30×55/41250/noabort，旧71 replay/history保持、新reward重算0、网络optimizer有限；全loss/标签/health/全2154终端及实际图已审。
- DECISION73绑定{len(decision['evidence'])}证据，准确72全state/replay/next65536恢复通过，有限73实际启动/startup通过，{now}steps {ststr}。全73loss已部署，原71–73保持，无自动73，Direct34false，Goal active。
- 本轮observer自然完成{len(observed)}样本，全72审查/73仅恢复就绪；不以观察超时重启科学。{snapshot['gpu_samples']}guard样本min{mins}%、低于50{low}，含合成占用、科研完成也继续，非跨重启服务。
- SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工main73d92390/baselinef6e8f8c实际fetch/read，无子agent。原窗口/阈值及历史结论保持。

'''
for f in ['AGENTS.md','UPDATE_LOG.md']:
 p=repo/f;s=p.read_text()
 if f=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=repo/'HANDOFF.md';p.write_text(f'> **RL最新：[完整72与有限73](docs/{name}.md)。73实际启动/恢复验证通过，原71–73继续，GPU完成后仍保载，Goal active。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
pointer=f'''# RL 2026-10-29 {now} UTC
ACTIVE. Complete72 reviewed; finite73 running.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{name}.md
Receipt docs/{name}_SAVE.json
GPU guard3256866 stays on; not reboot service.
Large data SSD; not HDD/arm1 backup.
'''
assert len(pointer.encode())<=p.stat().st_size;p.write_text(pointer);assert p.read_text()==pointer
print(json.dumps(receipt,indent=2))
