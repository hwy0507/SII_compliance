from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');D=Path(__file__).parent;R=B/'repository/SII_compliance';RUN=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';P=B/'runs/parameter_recovery76_first5000_20261029_v1';O=B/'runtime/recovery76_verified_wait_0613_20261029_v1';V=B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY76_PREFIX77_PREPARATION_20261029'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19])
assert read(O/'FINISHED.json')['all_original_identities_live'] and read(O/'FINISHED.json')['samples']==11
rows=[json.loads(x) for x in (O/'SAMPLES.jsonl').read_text().splitlines()];assert len(rows)==11
for m in ['impedance','admittance','vmc']:
 assert all(rows[i]['progress'][m]['steps']<=rows[i+1]['progress'][m]['steps'] for i in range(len(rows)-1))
for n in ['SAVED_REVIEW.json','PREFIX_BOUNDARY_REVIEW.json']:assert read(P/n)['passed']
assert read(P/'PLOT_REVIEW.json')['plot_inspected']
for n in ['DRIVER_SOURCE_REVIEW.json','CONTRACT_REVIEW.json','INCOMPLETE76_REJECTION.json','FUTURE_REVIEW_SOURCE_REVIEW.json']:assert read(D/n)['passed']
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],waiters={},archive=live(read(RUN/'MONITOR_LAUNCH.json')))
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();v=live(j);v.update(method=j['controller'],progress=read(p/'PROGRESS.json'),samplers=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert v['samplers']==30;snap['learners'].append(v)
snap['prepare77']=live(read(D/'LAUNCH.json'));assert sha(D/'REGISTRATION.json')==read(D/'LAUNCH.json')['registration_sha256']
for n,h in read(D/'REGISTRATION.json')['sources'].items():assert sha(D/n)==h
for x in read(D/'FUTURE_REVIEW_SOURCE_REVIEW.json')['files']:assert sha(Path(x['path']))==x['sha256']
for name in ['parameter_recovery76_loss_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1','parameter_recovery76_task_labels_20261029_v1','vmc_recovery76_terminal_followup_20261029_v1','admittance_recovery76_terminal_followup_20261029_v1']:
 p=B/'runs'/name;j=read(p/'LAUNCH.json');assert sha(p/'PLAN.json')==j['plan_sha256'];assert not (p/'FAILURE.json').exists() and not (p/'WAIT_FAILURE.json').exists();snap['waiters'][name]=live(j)
assert not (B/'runs/parameter_partial75_recovery_cycle77_20261029_v1').exists()
start=read(B/'runtime/parameter75_interruption_recovery_20261029_v1/FOLLOWUP_FINAL_SNAPSHOT.json')['time']
guard=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];guard=[g for g in guard if g['time']>=start];assert guard and time.time()-guard[-1]['time']<15
for pid in [read(G/'LAUNCH.json')['pid'],*read(G/'LAUNCH.json')['workers'].values()]:assert Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
snap['guard']=dict(samples=len(guard),minimum=[min(x['gpus'][i]['utilization'] for x in guard) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in guard) for i in range(4)],last=guard[-1],synthetic=True,keep_after_science=True);write(D/'FINAL_SNAPSHOT.json',snap);(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(g)+'\n' for g in guard))
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
sources={p for folder in [D,P,O,V] for p in folder.rglob('*') if p.is_file() and p.suffix in ['.py','.json','.jsonl','.diff','.png','.log'] and '__pycache__' not in p.parts};sources.add(B/'runtime/parameter75_interruption_recovery_20261029_v1/audit_prefix76.py')
for p in sorted(sources):
 data=p.read_bytes();assert len(data)<10_000_000;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);assert sha(q)==sha(p)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,large_artifacts_excluded=True))
A=B/'repository'/TAG;A.mkdir(exist_ok=False);tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),sha256=sha(tar),bytes=tar.stat().st_size,members=len(manifest)+1,member_bytes_and_python_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),large_artifacts='Shared SSD; not a full HDD or arm1 backup',remote_main_reviewed='7445692e944fecda1ad447e871ee39007e7aa8ae',baseline_reviewed='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d');write(A/'RECEIPT.json',receipt);write(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps='/'.join(str(j['progress']['steps']) for j in snap['learners']);t=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat();observed=read(O/'FINISHED.json');prefix=read(P/'REVIEW.json')['methods']
doc=f'''# 恢复76早期loss、有限77仅恢复准备与连续观察

{t}，Goal active。本轮完成早期loss独立审查、下一轮恢复检查部署与连续观察，属于progress。原76三路继续，当前steps {steps}，每路30sampler，无训练失败。Direct33原训练条件数值结论及Task/Strict0/0保留，不启动34。训练收敛仍未证明。

实际主机`{socket.gethostname()}`，共享SSD`{B}`，Python env/bin/python。原75中断记录不变；保留全部已落盘partial75学习/replay状态，新76是30个新物理回合。原30×55秒、最多41250新增、4m append/markers23与47、terminal128、batch65536、UTD1和LR/reward/物理/gates保持。

前5000固定长度日志前缀逐字节、连续步号、所有数值有限、独立算术与真实六面板图已核。每路首step严格等于partial75保存step+1。登记发生于前缀可用之后，非前瞻注册；不替代完整76loss/health或76–78窗口。

|方法|critic首→末1000|critic最大值|actor首→末1000|
|---|---|---:|---|
'''
for m,v in prefix.items():
 c=v['metrics']['agent_train/q_loss'];a=v['metrics']['agent_train/actor_loss'];doc+=f"|{m}|{c['first1000']:.9f}→{c['last1000']:.9f}|{c['maximum']:.9f}|{a['first1000']:.9f}→{a['last1000']:.9f}|\n"
doc+=f'''\n实际图仍显示I持续尖峰且均值略升；A critic略升、actor略降；V存在局部尖峰，尾1000均值高于首1000，actor略升。有限数值不能证明loss健康，原完整74及71–73失败结论保留。新76–78原PLAN不变，原74–76仍因75缺完整结果无法评定，近零保护不变。

新准备路径`runtime/prepare_recovery77_20261029_v1`。等待PID {snap['prepare77']['pid']} / start {snap['prepare77']['proc_start_ticks']}，只有完整76归档/完整replay-reward与health审查通过且原learner退出后，才创建已预登记的recovery77运行目录并执行全state/replay/下一65536 CHECK_ONLY，0物理/优化更新。当前77实际恢复尚未执行，77训练目录不存在；无自动训练/DECISION77/自动78。

77独立driver保留原76所有科学协议和initial interrupted_episode_recovery，新增post_interruption_continuation显式绑定完整76；历史completed_stage/batch字段仍是原历史记录，不伪称连续75完整阶段。严格验证新完整76边界、缺失完整75历史及原恢复标记，递归复核原partial75协议与原75历史依赖。训练源仅5处初始state审查/历史恢复与新接续元数据插入，逆变换逐字等于原科学trainer。新增metadata fixture正例及每路17协议拒绝+7边界拒绝通过；这些是小型schema测试，不冒充真实完整76恢复。真实当前不完整76调用已拒绝且未创建77运行输出。

源码构建两次被inverse检查拒绝，原return缩进1格而替换写成4格，新增metadata未插入；两次都在driver写入前退出，无训练启动。初版源码和失败说明保留，修正为断言唯一精确seam后五插入逆变换通过。仅恢复等待器与source hash已绑定；77启动检查/完整归档审查源码另已准备，尚未运行。

原76/归档/全loss/全标签/V与A终端/76–78/GPU guard及新77仅恢复等待共15个原PID身份在{observed['samples']}样本/{observed['elapsed']:.3f}秒观察中保持live；步数由{observed['first_steps']}推进至{observed['last_steps']}。观察器已自然结束，不重启科学。此次保存前再次独立核验真实进程。

自上次快照起{len(guard)}个guard样本各卡最低{snap['guard']['minimum']}%，低于50次数{snap['guard']['below50']}。含合成保底负载，科研完成后继续运行；先前启动预热及容器重启空档仍保留，不宣称每瞬时/跨重启保障。

开工实际fetch/read main7445692e（另一主机非RL第九条件81/108，所有失败保留）与baselinef6e8f8c，安全合并双方日志原字节，见REMOTE_MERGE_REVIEW。未操作另一主机非RL。保存源码基线{receipt['source_base_commit']}，遵循sii-research-sync，无子agent。此前禁交互push128缺HTTPS用户名认证，远端发布仍待，不能称纯网络失败；本地训练不受影响。

共享SSD证据包`{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`；逐成员/源码AST核验。大型checkpoint/replay/raw仍SSD，非HDD/arm1全备份。HDD LATEST仍指向已补本报告链接的主恢复文档。[收据]({TAG}_SAVE.json)。

下一步保持原76，等完整loss/标签/health/2244旧+30新终端诊断及实际图，核真实77 CHECK_ONLY后再决定有限77。当前完整76和77恢复尚待，Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n后续最新：[恢复76早期loss、77仅恢复准备及连续观察]({TAG}.md)。原76保持，77仅恢复等待，实际77训练未启动，GPU保载继续。\n')
entry=f'''## 2026-10-29 — 恢复76早期审查与77仅恢复

- [交接](docs/{TAG}.md)。前5000原字节/连续步号/全数值/独立算术和实际图核验；I/V尖峰保留，仅前缀非收敛。原76steps{steps}、各30sampler，原全loss/标签/终端/76–78继续。
- 新77driver显式完整76父边界和原partial75历史，五metadata插入逆变换等于原trainer；每路17协议+7边界负例、实际不完整76拒绝通过。仅恢复等待{snap['prepare77']['pid']}部署，77实际恢复/训练未执行；启动/归档review源码仅准备。两次构建失败原件保留，无科学重启。
- {observed['samples']}样本/{observed['elapsed']:.3f}s全部原身份保持、observer自然结束。guard{len(guard)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}，科研完成仍保载。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}已核，非HDD/arm1全备份；main7445692e/baselinef6e8f8c已读并安全合并，push认证仍待，Goal active、Direct34false。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':a,b=s.split('\n',1);p.write_text(a+'\n\n'+entry+b.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[恢复76前缀与77仅恢复](docs/{TAG}.md)。原76/76–78/GPU保底继续，77尚未训练，Goal active。**\n\n'+p.read_text())
print(json.dumps(receipt,indent=2));print(json.dumps(snap,ensure_ascii=False))
