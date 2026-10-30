from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;O=B/'runtime/recovery77_verified_wait_0705_20261029_v1';RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY77_FOLLOWUPS_20261029'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19])
f=read(O/'FINISHED.json');assert f['samples']==11 and f['all_original_identities_live'] and f['elapsed']>=300
assert read(RUN/'startup/REVIEW.json')['passed']
folders=[B/'runs'/n for n in ['parameter_recovery77_task_labels_20261029_v1','vmc_recovery77_terminal_followup_20261029_v1','admittance_recovery77_terminal_followup_20261029_v1']]
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],waiters={},archive=live(read(RUN/'MONITOR_LAUNCH.json')))
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller'];assert not (p/'train/FAILURE.json').exists() and not (p/'DRIVER_FAILURE.json').exists();v=live(j);v.update(method=j['controller'],progress=read(p/'train/PROGRESS.json'),samplers=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert v['samplers']==30;snap['learners'].append(v)
for p in folders+[B/'runs/parameter_recovery77_loss_20261029_v1',B/'runs/parameter_recovery76_78_reward_stability_20261029_v1']:
 j=read(p/'LAUNCH.json');assert sha(p/'PLAN.json')==j['plan_sha256']
 assert not (p/'FAILURE.json').exists() and not (p/'WAIT_FAILURE.json').exists()
 for n,h in read(p/'PLAN.json').get('sources',{}).items():assert sha(p/n)==h
 snap['waiters'][p.name]=dict(live(j),plan_sha256=j['plan_sha256'])
for p in folders[1:]:assert read(p/'ANCHOR_REVIEW.json')['passed'] and read(p/'ANCHOR_SAVED_REVIEW.json')['passed']
start=read(D/'COMPLETE76_FINAL_SNAPSHOT.json')['time'];rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=start];assert rows and time.time()-rows[-1]['time']<15
assert not (G/'FAILURE.json').exists()
for j in read(O/'REGISTRATION.json')['jobs'][-5:]:live(j)
snap['guard']=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True)
write(D/'FOLLOWUPS77_SNAPSHOT.json',snap);(D/'FOLLOWUPS77_GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
sources={D/n for n in ['prepare_labels77.py','prepare_terminal77.py','deploy_terminal77.py','observe77_0705.py','observe77_0705.py.diff','save_followups77.py','FOLLOWUPS77_SNAPSHOT.json','FOLLOWUPS77_GUARD_SAMPLES.jsonl','MERGE_BA9748_REVIEW.json','MERGE_1F581096_REVIEW.json']}
sources.add(B/'repository/RL_RECOVERY76_COMPLETE77_RUNNING_20261029/FINAL_LOCAL_RECEIPT.json')
for p in folders+[O]:
 for q in p.iterdir():
  if q.is_file() and q.suffix in ['.json','.jsonl','.py','.diff','.log','.npz'] and q.stat().st_size<5_000_000:sources.add(q)
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
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
steps={j['method']:j['progress']['steps'] for j in snap['learners']};stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()
doc=f'''# 恢复77完整标签与固定终端后续

{stamp}，Goal active。原77三路继续，当前steps {steps}，各30sampler；未完成77，不判断收敛。完整76审查和实际77启动见[此前报告](RL_RECOVERY76_COMPLETE77_RUNNING_20261029.md)。原科学配置、历史75中断及前瞻76–78 PLAN保持，无自动78、无Direct34。GPU保底在全部科学工作完成后仍继续，合成占用不计科学吞吐；非重启自启服务。

实际计算主机 `{snap['host']}`，共享SSD `{B}`，解释器env/bin/python。

77标签等待已部署，比较两个完整周期76→77，检查全部180保存回合/90reward对/Task及Strict-only变化、原.2mm物理gate、model和evaluator hash；再独立对照全loss的reward与标签计数。真实未完成77已拒绝，无输出，无新积分/优化器更新；中断75仍拒绝，不补造完整75。

导纳及VMC完整76终端锚点已完成并独立复核。每路全部2274条（包含76新增30条）的索引、reward、masks、Q和分母与先前已审values逐项相等；observations/actions来自准确完整76 checkpoint。只复用此前审查过的Q，无新网络前向/训练/物理。VMC总masked SSE3883.440215203、贡献.180412988282；导纳2815.605065203、贡献.130720576160，独立scalar复算通过。它们是全2274基准，不能与此前仅旧2244 SSE混为一谈。

两路77后续已登记并实际等待，完整77预期2304终端：固定全部2274旧样本与新增30分栏，保留原历史focus、更新分母和旧分母两种贡献；全群体改善与退化均保留。等待原训练及完整归档/health审查结束后才做CPU只读前向与独立标量检查，原训练权重、replay、采样和gates不变。后续实际图仍须查看，当前只有基准没有77结果。

|任务|原PID / start ticks|
|---|---|
'''
for j in snap['learners']:doc+=f"|77 {j['method']}|{j['pid']} / {j['proc_start_ticks']}|\n"
doc+=f"|77 archive/health|{snap['archive']['pid']} / {snap['archive']['proc_start_ticks']}|\n"
for n,j in snap['waiters'].items():doc+=f"|{n}|{j['pid']} / {j['proc_start_ticks']}|\n"
doc+=f'''\n连续观察11样本/{f['elapsed']:.3f}秒，全部14原PID/start身份在观察期live，steps {f['first_steps']}→{f['last_steps']}。观察器自然完成不表示训练完成，不重启科学。保存时重新核原训练、归档和五等待器活跃、PLAN/source hash保持。

从前次保存起guard {len(rows)}样本，四卡最低{snap['guard']['minimum']}%，低于50次数{snap['guard']['below50']}；合成保载保持。原容器中断和v6预热两空闲样本在此前记录中保留，不声称跨重启无间断。

完整76证据提交68f3e0b4共316manifest条目已逐大小/SHA核暂存及提交Git blob；本轮开工实际fetch/read mainba9748b1、baselinef6e8f8c，新增非RL第十条件/接触范围说明已读，并以606c3162安全合并，双方日志新增块逐字保留。禁交互push返回128缺GitHub HTTPS用户名认证，仍仅本地提交，远端未发布；这不阻断共享SSD训练/归档。发布前又实际fetch/read main1f581096（非RL93→96）和对应交接并安全合并，双方新增日志逐字保留。没有操作他机非RL任务，无子agent。

小证据 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员字节/源码AST已核。[收据]({TAG}_SAVE.json)。大型checkpoint、回放及raw在共享SSD；不是HDD或arm1完整备份。HDD入口就地更新且不增加文件大小。

下一步保持原77、归档、全loss、标签、两终端跟踪与原76–78窗口；等完整77全审和实际图后才决定有限78，reward稳定与loss健康尚未证明。用户要求全部工作完成后保留GPU保底。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 恢复77全标签与2274终端后续

- [交接](docs/{TAG}.md)。77全180标签/90reward配对自动等待已部署，真实未完成77拒绝；V/A完整76全部2274终端锚点hash/独立标量通过，SSE3883.440215203/2815.605065203，无新forward/物理/更新。两路77终端等待已部署，预计2304、原focus及两分母保留；当前无77结果、无自动78，Goal active。
- 原77连续11样本/{f['elapsed']:.3f}秒14身份均live，当前steps{steps}、各30sampler；观察器自然结束、科学不重启。guard{len(rows)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}；全部科研完成仍保载，合成非科学吞吐。
- SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST已核，非HDD/arm1全备份。mainba9748b1后1f581096/baselinef6e8f8c已读，非RL新增逐字保留安全合并；68f3e0b4全316提交blob核验，push128缺HTTPS认证，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':a,b=s.split('\n',1);p.write_text(a+'\n\n'+entry+b.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[77全标签与2274终端后续](docs/{TAG}.md)。原77继续、全部后续已部署；原76–78和GPU保底保持，无自动78，Goal active。**\n\n'+p.read_text())
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n更新：[77全标签与2274终端后续]({TAG}.md)。各后续实际部署，原科学和GPU保底继续。\n')
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');old=p.read_bytes();text=f'# RL {datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}\nACTIVE.77 running;guardv6.\nSSD {B}\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n'.encode();assert len(text)<=len(old);text=text+b' '*(len(old)-len(text))
with p.open('r+b') as stream:stream.write(text)
assert p.read_bytes()==text
print(json.dumps(receipt));print(json.dumps(snap))
