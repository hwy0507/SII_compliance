from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;P=B/'runs/parameter_recovery77_first5000_20261029_v1';O=B/'runtime/recovery77_prepare78_verified_wait_20261029_v1';RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY77_PREFIX78_PREPARATION_20261029'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19])
f=read(O/'FINISHED.json');assert f['samples']==11 and f['all_original_identities_live'] and f['elapsed']>=300
assert read(P/'SAVED_REVIEW.json')['passed'] and read(P/'PLOT_INSPECTION.json')['actual_image_viewed'] and sha(P/'loss.png')==read(P/'PLOT_INSPECTION.json')['plot_sha256']
assert read(D/'DRIVER_SOURCE_REVIEW.json')['passed'] and read(D/'CONTRACT_REVIEW.json')['passed'] and read(D/'INCOMPLETE77_REJECTION.json')['passed']
assert not (B/'runs/parameter_partial75_recovery_cycle78_20261029_v1').exists() and not (D/'FAILURE.json').exists()
prep=read(D/'LAUNCH.json');assert sha(D/'REGISTRATION.json')==prep['registration_sha256']
for n,h in read(D/'REGISTRATION.json')['sources'].items():assert sha(D/n)==h
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],archive=live(read(RUN/'MONITOR_LAUNCH.json')),restore78_waiter=live(prep),waiters={},actual78_restore=False,actual78_training=False)
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller'];assert not (p/'train/FAILURE.json').exists() and not (p/'DRIVER_FAILURE.json').exists();v=live(j);v.update(method=j['controller'],progress=read(p/'train/PROGRESS.json'),samplers=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert v['samplers']==30;snap['learners'].append(v)
for n in ['parameter_recovery77_task_labels_20261029_v1','vmc_recovery77_terminal_followup_20261029_v1','admittance_recovery77_terminal_followup_20261029_v1','parameter_recovery77_loss_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1']:
 p=B/'runs'/n;j=read(p/'LAUNCH.json');assert sha(p/'PLAN.json')==j['plan_sha256'];assert not (p/'FAILURE.json').exists() and not (p/'WAIT_FAILURE.json').exists();snap['waiters'][n]=dict(live(j),plan_sha256=j['plan_sha256'])
start=read(B/'runtime/recovery77_completion_preparation_20261029_v1/FOLLOWUPS77_SNAPSHOT.json')['time'];rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=start];assert rows and time.time()-rows[-1]['time']<15
assert not (G/'FAILURE.json').exists()
for j in read(O/'REGISTRATION.json')['jobs'][-5:]:live(j)
snap['guard']=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True);write(D/'FINAL_SNAPSHOT.json',snap);(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
sources={p for folder in [D,P,O] for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.diff','.png','.log']};E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();assert len(data)<5_000_000;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
write(E/'MANIFEST.json',dict(files=manifest,time=time.time(),large_artifacts_excluded=True))
A=B/'repository'/TAG;A.mkdir(exist_ok=False);tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),member_bytes_and_python_ast_verified=True,large_artifacts='Shared SSD; no full HDD/arm1 backup');write(A/'RECEIPT.json',receipt);write(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={j['method']:j['progress']['steps'] for j in snap['learners']};stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat();prefix=read(P/'REVIEW.json')['methods']
doc=f'''# 恢复77早期loss审查与78仅恢复准备

{stamp}，Goal active。上轮完成完整76归档与77全标签/终端后续部署，本轮完成77前5000原始日志和实际图检查、新78恢复工具与等待部署。原77三路仍进行中，当前steps {steps}，各30sampler；完整77结果尚无，不能判断收敛。完整76和77后续见[此前交接](RL_RECOVERY77_FOLLOWUPS_20261029.md)。

实际计算主机 `{snap['host']}`，共享SSD `{B}`，解释器env/bin/python。原30条件×55秒/最多41250新增、4m append/23与47标记、terminal128、batch65536、UTD1、LR/reward/masks/物理/gates不变。历史75仍中断，原74–76无法评定；原前瞻76–78的5%/nearzero1/seed2026102855/5000bootstrap/anchor55及历史失败窗口保持，近零保护不用于推离零；Direct33既有数值结论与Task/Strict0/0保持，无Direct34。

77前5000检查登记在训练启动且该前缀可用之后，只作描述。三路原字节前缀、连续步号、所有数值字段有限、独立scalar均值/极值复算通过，audit仅修改周期/path/描述且逆变换等于76原工具，无训练更新或新物理。实际查看完整六栏图：

|方法|critic首→末1000|max critic|actor首→末1000|
|---|---|---:|---|
'''
for m,v in prefix.items():
 c=v['metrics']['agent_train/q_loss'];a=v['metrics']['agent_train/actor_loss'];doc+=f"|{m}|{c['first1000']:.9f}→{c['last1000']:.9f}|{c['maximum']:.9f}|{a['first1000']:.9f}→{a['last1000']:.9f}|\n"
doc+='\nI critic基线约2–3但反复高尖峰，rolling均值下降中仍有局部上升，actor约25.7且尾段略升；A critic约1.2、稀疏尖峰，actor缓慢下降；V critic约.8但仍有局部尖峰，actor约−12.8。没有非有限数值不等于loss健康；只是前5000，不代替完整77 loss/reward/终端审查，也不作收敛断言。\n\n'
doc+=f'''78恢复driver `runtime/prepare_recovery78_20261029_v1/resume_recovery77.py` 当前源码SHA `{sha(D/'resume_recovery77.py')}`。与77的科学trainer逐字相同；原五处仅metadata/初始state审查插入可逆还原冻结trainer。新的parent指向完整77，必须保留前一轮recovery_continuation且与父registration一致；递归验证原77 driver及其完整76证据，再验证原partial75恢复和历史科学依赖。新当前continuation替换上一层，但上一层通过准确parent文件/hash完整保留，不把历史completed_stage当当前连续轮号。

三路metadata正例、每路19协议拒绝和8边界拒绝通过，包括被改的上一轮continuation、丢失父checkpoint continuation、科学设置和伪造完整75；这些是标明fixture的metadata测试，不是实际77 checkpoint恢复。对真实尚未完整77调用prepare已拒绝，无78 run输出。没有重启77。

只恢复等待PID {prep['pid']} / start {prep['proc_start_ticks']} 已实际部署，REGISTRATION SHA `{sha(D/'REGISTRATION.json')}`。等待原77完整归档/health审查且三learner退出后，才执行三个CPU CHECK_ONLY，全learner/optimizer/RNG/replay和next65536必须精确；当前该实际恢复尚未运行，没有78物理/优化器更新。等待器不会派发训练；78启动仍需完整77 loss/全标签/两终端/实际图审查、明确有限续训决定及独立启动/归档检查准备。

原77及完整loss、全180标签/90reward对、V/A固定2274终端后续和原76–78窗口均保持。观察11样本/{f['elapsed']:.3f}秒共15原PID/start身份在观察期有效，steps {f['first_steps']}→{f['last_steps']}。观察器自然完成不代表科学完成，不因此重启。保存时所有原任务及仅恢复等待已重新核活跃、PLAN hash保持。

从前次保存起GPU guard {len(rows)}样本，最低{snap['guard']['minimum']}%，低于50次数{snap['guard']['below50']}。合成占用不计科学吞吐；按用户要求科学全部完成后继续保载。此前容器空档/v6预热两空闲样本保留，当前guard不是重启自启服务。

本轮实际fetch/read main1f581096、baselinef6e8f8c；另一主机非RL93→96记录已读且上轮已安全合并，无科学配置变化，不操作其进程。上轮本地7880fb64和68f3e0b4证据已核提交blob，GitHub push128缺HTTPS认证，不能声称已远端发布。发布前另fetch/read mainb1deda65及非RL第十一条件完整/99条进度交接，并安全合并保留双方新增日志逐字一致。当前本轮源基线{receipt['source_base_commit']}；无子agent。

共享SSD小证据 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节与Python AST核验。[收据]({TAG}_SAVE.json)。大型checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；HDD最新入口仍指已补本报告链接的主恢复交接。

下一步保持原77和全部原审查及78仅恢复等待；完整77后实际查看全图，再决定有限78。reward稳定与loss健康仍待，Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 恢复77前缀审查与78仅恢复准备

- [交接](docs/{TAG}.md)。77前5000原字节/连续步号/所有数值/独立算术和实际六栏图通过；I/V尖峰保留，仅前缀非收敛。原77steps{steps}、各30sampler，原全loss/标签/终端/76–78保持。
- 78driver科学trainer与77逐字同一，五metadata插入可逆；准确77父continuation和原77/76/partial75历史递归验证。三路metadata正例、每路19协议+8边界拒绝通过，真实未完整77拒绝。仅恢复等待{prep['pid']}部署，实际78恢复/训练尚未运行，须完整77证据才决定，Goal active。
- 11样本/{f['elapsed']:.3f}秒15原身份保持，observer自然结束科学继续；guard{len(rows)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}，科研完成仍保载、合成非吞吐。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}已核，非HDD/arm1全备份；main1f581096后b1deda65/baselinef6e8f8c已读安全合并，认证发布待，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':a,b=s.split('\n',1);p.write_text(a+'\n\n'+entry+b.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[77前缀与78仅恢复准备](docs/{TAG}.md)。原77全检查/76–78/GPU保底继续，78仅恢复等待已部署，无78训练，Goal active。**\n\n'+p.read_text())
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n更新：[77前缀审查与78仅恢复准备]({TAG}.md)。原77继续，78仅恢复等待已部署；无78训练。\n')
print(json.dumps(receipt));print(json.dumps(snap))
