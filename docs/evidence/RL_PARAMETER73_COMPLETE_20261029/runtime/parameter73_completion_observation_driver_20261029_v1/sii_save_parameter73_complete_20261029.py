from pathlib import Path
import json,time,hashlib,tarfile,ast,datetime,socket,os,subprocess,math
os.sched_setaffinity(0,{53})
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';TAG='RL_PARAMETER73_COMPLETE_20261029'
OBS=B/'runtime/parameter73_completion_observation_20261029_v1';DRV=B/'runtime/parameter73_completion_observation_driver_20261029_v1';RUN=B/'runs/parameter_capacity_pool30_cycle74_20261026_v1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
assert read(OBS/'FINISHED.json')['completed'];assert read(RUN/'startup/REVIEW.json')['passed']
decision=read(B/'runtime/prepare_parameter74_20261028_v1/DECISION74.json')
for x in decision['evidence'].values():assert sha(Path(x['path']))==x['sha256']
loss=read(B/'runs/parameter73_loss_20261028_v1/REVIEW.json');full=read(B/'runs/parameter_capacity_pool30_cycle73_review_20261026_v1/REVIEW.json');labels=read(B/'runs/parameter_task_label_audit73_20261028_v1/COMPLETE72_73_SAVED_REVIEW.json');window=read(B/'runs/parameter_capacity71_73_reward_stability_20261028_v1/REVIEW.json');bootstrap=read(B/'runtime/parameter71_73_bootstrap_independent_20261029_v1/REVIEW.json')
assert labels['passed'] and bootstrap['passed']
def identity(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19],state=f[0])
snap=dict(time=time.time(),learners=[],waiters={},guard_processes=[])
for j in read(RUN/'LAUNCH.json')['jobs']:
 d=identity(j);p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();d.update(controller=j['controller'],progress=read(p/'PROGRESS.json'));snap['learners'].append(d)
snap['archive_monitor']=identity(read(RUN/'MONITOR_LAUNCH.json'))
for key,folder in [('loss74','runs/parameter74_loss_20261028_v1'),('window74_76','runs/parameter_capacity74_76_reward_stability_20261029_v1')]:
 p=B/folder;j=read(p/'LAUNCH.json');d=identity(j);assert sha(p/'PLAN.json')==j['plan_sha256'];d['plan_sha256']=j['plan_sha256'];snap['waiters'][key]=d
for pid,ticks in [(3256866,'37410686'),(3256867,'37410690'),(3256868,'37410690'),(3256869,'37410691'),(3256870,'37410693')]:snap['guard_processes'].append(identity(dict(pid=pid,proc_start_ticks=ticks)))
g=Path('/tmp/sii_gpu_util_guard_20261028_v5');assert not (g/'STOP').exists() and not (g/'FAILURE.json').exists()
observed=[json.loads(l) for l in (OBS/'samples.jsonl').read_text().splitlines()];raw=[l for l in (g/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n') and observed[0]['time']<=json.loads(l)['time']<=snap['time']];gs=[json.loads(l) for l in raw];assert len(gs)>10
snap['guard_stats']=[]
for i in range(4):
 vals=[next(v['utilization'] for v in row['gpus'] if v['gpu']==i) for row in gs];snap['guard_stats'].append(dict(gpu=i,minimum=min(vals),mean=math.fsum(vals)/len(vals),below50=sum(v<50 for v in vals)))
snap.update(guard_samples=len(gs),max_gap=max(b['time']-a['time'] for a,b in zip(gs,gs[1:])))
write(OBS/'FINAL_SNAPSHOT.json',snap);(OBS/'gpu_samples.jsonl').write_bytes(b''.join(raw))
now=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).strftime('%H:%M:%S')
pointer=f'''# RL 2026-10-29 {now} UTC
ACTIVE. Complete73 reviewed; finite74 running.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{TAG}.md
Receipt docs/{TAG}_SAVE.json
GPU guard on. Large data SSD. No reboot service.
'''
hdd=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');assert len(pointer.encode())<=hdd.stat().st_size
sources={Path(x['path']) for x in decision['evidence'].values()}
for name in ['sii_observe73_completion_20261029.py','sii_prepare73_completion_helpers_20261029.py','sii_bootstrap71_73_independent_20261029.py','sii_decide_launch74_20261029.py','sii_deploy74_window_20261029.py','sii_save_parameter73_complete_20261029.py']:
 p=DRV/name
 if p.exists():assert p.read_bytes()==(Path('/tmp')/name).read_bytes()
 else:p.write_bytes((Path('/tmp')/name).read_bytes())
folders=[OBS,DRV,B/'runtime/parameter71_73_bootstrap_independent_20261029_v1',B/'runtime/prepare_parameter74_20261028_v1',B/'runtime/parameter74_loss_preparation_20261029_v1',B/'runtime/parameter_task_label_audit73_20261028_v1',B/'runs/parameter_capacity_pool30_cycle73_review_20261026_v1',B/'runs/parameter_capacity_pool30_cycle73_review_20261026_v1/health',B/'runs/parameter73_loss_20261028_v1',B/'runs/parameter74_loss_20261028_v1',B/'runs/parameter_task_label_audit73_20261028_v1',B/'runs/parameter_capacity71_73_reward_stability_20261028_v1',B/'runs/parameter_capacity74_76_reward_stability_20261029_v1',RUN,RUN/'startup']+[B/f'runs/{m}73_terminal_anchor_followup_20261028_v1' for m in ['vmc','admittance']]
for p in folders:
 for f in p.iterdir():
  if f.is_file() and f.suffix in ['.json','.py','.diff','.png','.npz','.log','.jsonl','.txt'] and f.stat().st_size<=5_000_000:sources.add(f)
for m in ['impedance','admittance','vmc']:
 for n in ['FINISHED.json','episodes.jsonl']:sources.add(B/f'runs/parameter_capacity_pool30_cycle73_20261026_v1/{m}/train'/n)
 for n in ['REGISTRATION.json','TRAINER_PATCH.json','BATCH_SIZE_STAGE_EXECUTION.json','trainer_registered.py']:
  p=RUN/m/n
  if p.exists():sources.add(p)
 for n in read(RUN/m/'REGISTRATION.json')['batch_size_stage']['dependency_hashes']:sources.add(B/'runtime/parameter_capacity_pool30_cycle74_20261026_v1'/n)
for n in ['ARCHIVE_REVIEW_FINISHED.json','LAUNCH.json','MONITOR_LAUNCH.json']:sources.add(B/'runs/parameter_capacity_pool30_cycle73_20261026_v1'/n)
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
report=f'''# 完整第73轮、原71–73窗口审查与有限74接续

2026-10-29 {now} UTC，Goal active。实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器env/bin/python。全73及原71–73固定窗口已审查，尚未整体收敛，准确接续有限74。Direct33原训练条件数值结论保持，Task/Strict0/0，不启动34。

全73三路自然完成30×55秒/41250新增/noabort，全部旧72 replay/history保留，新reward重建误差0、网络optimizer有限。全loss独立算术、全部180标签/90reward对、health与终端数组及实际图已审。原30条件/4m append/markers23/47/terminal128/batch65536/UTD1/LR/masks/reward/物理/gates不变；未重新积分全部原始物理。

|方法|最终steps|reward均值|Task/Strict（各30）|critic首→末1000|critic最大值|actor首→末1000|
|---|---:|---:|---|---|---:|---|
'''
for m in ['impedance','admittance','vmc']:
 v=loss['methods'][m];h=v['reward_history'][-1];q=v['loss']['agent_train/q_loss'];a=v['loss']['agent_train/actor_loss'];report+=f"|{m}|{full['methods'][m]['steps']}|{h['reward_mean']:.9f}|{h['task']}/{h['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{a['first1000']:.6f}→{a['last1000']:.6f}|\n"
report+='\n全标签变化（完整保留Task-only）：\n\n'
for m,v in labels['methods'].items():
 report+=f"- {m} physical-valid72→73 {v['counts']['72']['physical_valid']}→{v['counts']['73']['physical_valid']}（各30）；"
 for c in v['changes']:
  a,z=c['cases'];report+=f"{c['condition']} {','.join(c['fields'])}，Task{a['task']}→{z['task']}、Strict{a['strict']}→{z['strict']}，穿透{a['penetration_mm']:.9f}→{z['penetration_mm']:.9f}mm；"
 report+='\n'
report+='\n原71–73窗口固定5%/近零1/seed2026102855/5000分层bootstrap/anchor55保持。独立完整算术及实际图已审；原SAVED_ARITHMETIC_REVIEW的bootstrap_reruns0保留历史事实，另有本轮独立整数抽样/标量均值/手写分位数复核，原输入输出不改。区间表示条件组成敏感性，不是独立训练seed泛化或等价性证明。\n\n'
for m,v in window['methods'].items():
 b=bootstrap['methods'][m];report+=f"- {m}：三均值{[x['reward_mean'] for x in v['cycles']]}；近零保护{v['near_zero_guard_triggered']}；相邻相对变化{v['adjacent_relative_mean_changes']}、首尾{v['endpoint_relative_mean_change']}；原描述性5%通过{v['descriptive_five_percent_check']}。独立delta区间{b['delta_interval']}，slope区间{b['slope_interval']}，最大区间差{b['maximum_saved_interval_difference']}。\n"
report+='\n全2184旧终端及本轮新30分别比较，总2214；保留两分母和原关注样本，不新增零误差停止门、不作梯度因果判断。\n\n|路|旧2184 SSE前→后|变化|旧贡献（新分母）|旧贡献（旧分母）|新30贡献|\n|---|---|---:|---:|---:|---:|\n'
for m in ['vmc','admittance']:
 v=read(B/f'runs/{m}73_terminal_anchor_followup_20261028_v1/REVIEW.json');report+=f"|{m}|{v['old2184_sse_before']:.6f}→{v['old2184_sse_after']:.6f}|{100*(v['old2184_sse_ratio']-1):.4f}%|{v['old2184_contribution_after']:.9f}|{v['old2184_after_using_old_denominator']:.9f}|{v['new30_contribution']:.9f}|\n"
for m in ['vmc','admittance']:
 v=read(B/f'runs/{m}73_terminal_anchor_followup_20261028_v1/REVIEW.json');report+='\n'+m+'：'+'；'.join(f"index{x['replay_index']} SSE{x['sse_before']:.6f}→{x['sse_after']:.6f}" for x in v['focus'])+'。\n'
report+='\n续训依据：\n\n'+decision['reason']+'\n\n'
report+=f"DECISION74 SHA `{sha(B/'runtime/prepare_parameter74_20261028_v1/DECISION74.json')}`，绑定{len(decision['evidence'])}项证据；准确73全state/replay/下一65536恢复及实际74 startup通过。无自动75，不重置优化器/回放/RNG/history；近零保护不是把reward推离零的目标。\n\n|当前任务|PID / start ticks|\n|---|---|\n"
for j in snap['learners']:report+=f"|74 {j['controller']}|{j['pid']} / {j['proc_start_ticks']}|\n"
for k,j in snap['waiters'].items():report+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|\n"
report+=f"\n{now}三路steps {steps}。原71–73完整结果保留；条件性74–76 PLANd8c243d9仅在实际74启动后部署固定14400秒等待器，无自动后续训练。\n\n"
f=read(OBS/'FINISHED.json');report+=f"本轮observer自然完成{f['samples']}样本/{f['duration']:.3f}秒，结束时all_science_ready={f['all_science_ready']}；保存前全部实际审查/恢复另外核验完成，观察时限不授权科学重启。\n\n"
report+=f"从观察开始至当前快照共{len(gs)}guard样本，四卡最低{mins}%，低于50计数{below}，最大间隔{snap['max_gap']:.6f}秒。原v5五进程保持，含合成负载，不是纯科学吞吐或每瞬时保证；科研完成后仍保载，非跨重启服务。\n\n"
report+=f"开工实际fetch/read main01bb350368f324a02116085b4e07912f985af372、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d；保存源码基线{receipt['source_base_commit']}。保存前再次fetch/read main f7fde7a3及baselinef6e8f8c，阅读非RL方向覆盖诊断与原108进度30→33，并安全fast-forward保留；未操作其他主机科学进程。遵循sii-research-sync，保留并行非RL工作，无子agent。\n\n共享SSD包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/Python AST核验。[保存收据]({TAG}_SAVE.json)。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份；HDD满只重写既有入口。\n\n下一步保持原74与guard，准备其标签/全终端后续审查，跟进原74–76窗口，继续以完整reward稳定和loss健康证据判断。Goal active。\n"
(R/'docs'/(TAG+'.md')).write_text(report);(A/'HANDOFF.md').write_text(report)
entry=f'''## 2026-10-29 — 完整73、原71–73审查与准确有限74

- [交接](docs/{TAG}.md)。三路完整73各30×55/41250/noabort，旧72 replay/history保持、新reward重算0、网络optimizer有限；全loss/180标签/90reward对/health/全2184终端及实际图已审。
- 原71–73完整算术/实际图及独立5000 bootstrap复核完成，原5%/近零1/seed/anchor55及全部历史结论保持，原算术收据bootstrap_reruns0未改。尚未整体收敛，具体失败/退化见交接。
- DECISION74绑定{len(decision['evidence'])}证据，准确73全state/replay/next65536及实际74 startup通过，{now}steps{steps}。全74loss和预登记74–76等待已部署，无自动75，Direct34false，Goal active。
- observer自然完成{f['samples']}样本，结束时当前审查就绪{f['all_science_ready']}，其后按实际状态核验，不重启科学。{len(gs)}guard样本min{mins}%、低于50{below}，含合成负载，科研完成仍保载。
- SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；开工main01bb3503/baselinef6e8f8c实际fetch/read，无子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[完整73、原71–73与有限74](docs/{TAG}.md)。74已实际接续，74–76等待已部署；GPU科研完成仍保载，Goal active。**\n\n'+p.read_text())
hdd.write_text(pointer);assert hdd.read_text()==pointer
print(json.dumps(receipt,indent=2))
