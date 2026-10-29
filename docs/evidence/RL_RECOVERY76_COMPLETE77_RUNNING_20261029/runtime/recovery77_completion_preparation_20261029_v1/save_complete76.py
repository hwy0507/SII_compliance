from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;P=B/'runtime/prepare_recovery77_20261029_v1';RUN=B/'runs/parameter_partial75_recovery_cycle77_20261029_v1';OLD=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';REV=B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1';L=B/'runs/parameter_recovery76_loss_20261029_v1';LABEL=B/'runs/parameter_recovery76_task_labels_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY76_COMPLETE77_RUNNING_20261029'
def read(p):return json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19])
decision=read(D/'DECISION77.json')
for x in decision['evidence'].values():assert sha(x['path'])==x['sha256']
assert read(REV/'REVIEW.json')['passed'] and read(REV/'FINISHED.json')['completed'] and read(OLD/'ARCHIVE_REVIEW_FINISHED.json')['completed']
assert read(RUN/'CHECK_ONLY_COMPLETE.json')['passed'] and read(RUN/'startup/REVIEW.json')['passed']
assert read(L/'SAVED_REVIEW.json')['passed'] and read(LABEL/'COMPLETE74_76_SAVED_REVIEW.json')['passed']
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],archive=live(read(RUN/'MONITOR_LAUNCH.json')),waiters={})
for j in read(RUN/'LAUNCH.json')['jobs']:
 p=RUN/j['controller'];assert read(p/'INITIAL_STATE_REVIEW.json')['passed'];assert not (p/'DRIVER_FAILURE.json').exists() and not (p/'train/FAILURE.json').exists();v=live(j);v.update(method=j['controller'],progress=read(p/'train/PROGRESS.json'),samplers=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert v['samplers']==30;snap['learners'].append(v)
for name in ['parameter_recovery77_loss_20261029_v1','parameter_recovery76_78_reward_stability_20261029_v1']:
 p=B/'runs'/name;j=read(p/'LAUNCH.json');assert sha(p/'PLAN.json')==j['plan_sha256'];assert not (p/'FAILURE.json').exists();snap['waiters'][name]=dict(live(j),plan_sha256=j['plan_sha256'])
rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];start=read(D/'FINAL_SNAPSHOT.json')['time'];rows=[x for x in rows if x['time']>=start];assert rows and time.time()-rows[-1]['time']<15
for pid in [read(G/'LAUNCH.json')['pid'],*read(G/'LAUNCH.json')['workers'].values()]:assert Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]!='Z'
snap['guard']=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True);write(D/'COMPLETE76_FINAL_SNAPSHOT.json',snap);(D/'COMPLETE76_GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
sources={Path(x['path']) for x in decision['evidence'].values()};folders=[D,P,RUN,RUN/'startup',OLD,REV,REV/'health',L,LABEL,B/'runs/parameter_recovery77_loss_20261029_v1',B/'runs/parameter_partial75_recovery_cycle77_review_20261029_v1',B/'runs/parameter_recovery76_78_reward_stability_20261029_v1']
for m in ['impedance','admittance','vmc']:
 folders += [RUN/m,OLD/m];sources.add(OLD/m/'train/FINISHED.json')
for m in ['vmc','admittance']:folders.append(B/f'runs/{m}_recovery76_terminal_followup_20261029_v1')
for folder in folders:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in ['.json','.jsonl','.py','.diff','.png','.npz','.log','.txt'] and p.stat().st_size<5_000_000:sources.add(p)
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
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
full=read(REV/'REVIEW.json')['methods'];loss=read(L/'REVIEW.json')['methods'];health=read(REV/'health/DIAGNOSIS.json')['methods'];startup=read(RUN/'startup/REVIEW.json')['methods'];terminal={m:read(B/f'runs/{m}_recovery76_terminal_followup_20261029_v1/REVIEW.json') for m in ['vmc','admittance']};steps='/'.join(str(j['progress']['steps']) for j in snap['learners']);stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()
doc=f'''# 完整恢复76审查与有限77实际接续

{stamp}，Goal active。恢复76三路完整结束并全审，准确恢复77已实际运行且startup通过。当前77 steps {steps}，各30sampler，无训练失败。整体reward稳定和loss健康仍未证明；Direct33原训练条件数值结论及Task/Strict0/0保持，不启动34。

共享SSD `{B}`，主机`{socket.gethostname()}`，Python env/bin/python。全部partial75已保存学习/replay状态保留，完整cycle历史仍缺75；76是重置物理环境后的新完整周期，77从完整76精确接续。原30条件×55秒/最多41250新增、4m append/markers23与47、terminal128、batch65536、UTD1、LR/masks/reward/物理/gates均不变。

|方法|76累计steps|reward均值|Task/Strict|critic首→末1000|max critic|actor首→末1000|
|---|---:|---:|---|---|---:|---|
'''
for m,v in full.items():
 c=loss[m]['loss']['agent_train/q_loss'];a=loss[m]['loss']['agent_train/actor_loss'];doc+=f"|{m}|{v['steps']}|{v['reward_mean']:.9f}|{v['task']}/{v['strict']}|{c['first1000']:.9f}→{c['last1000']:.9f}|{c['maximum']:.9f}|{a['first1000']:.9f}→{a['last1000']:.9f}|\n"
doc+='\n三路各30完整55秒、41250新增、无abort；旧回放所有字段/history保持，全部新增reward由冻结物理间隔日志重建最大误差0，network/optimizer有限，marker和原学习参数保持。完整loss所有日志及保存算术、90reward配对和全180标签核验通过。有限数值不等于健康loss。\n\n'
doc+='全轮loss与health图已实际查看：I critic持续尖峰并有尾段burst，actor先升后降；A critic约1.2且稀疏尖峰，actor尾段略升；V critic局部/尾段burst、actor明显上移。health混合mask终端MAE和in-bag/out-of-bag分栏保留，不能把heldout误差当所有拟合失败或新增零误差门槛。\n\n'
doc+='74→76标签比较跨越保留的partial75额外曝光：I无标签变化；A long0200真→假，long0500/short0900假→真，short0600恢复Strict（穿透.204262→.189901mm），总体14/13→15/15；V short0600失去Strict（.178927→.213513mm），17/17→17/16。全部改善和退化保留，非随机性/梯度因果证明。\n\n'
doc+='终端基准取真实partial75权重，固定2244旧样本+76新增30；不是拿完整74权重替代。两路所有保存数组/独立scalar算术与实际散点图已审：\n\n'
for m,v in terminal.items():doc+=f"- {m} 旧2244 SSE {v['old2244_sse_before']:.9f}→{v['old2244_sse_after']:.9f}，原分母贡献{v['old2244_contribution_before']:.9f}→新分母{v['old2244_contribution_after']:.9f}，after仍用旧分母{v['old2244_after_using_old_denominator']:.9f}；新30贡献{v['new30_contribution']:.9f}，全终端{v['all_terminal_contribution']:.9f}。\n"
doc+='\nV原2050526 SSE1.4808→48.8337、2423133 2.8373→15.1305退化，2423122 8.3721→2.3999改善；A原2752093 43.6609→31.9523改善但全群体退化。不只挑好focus；原focus/两分母不变。V新30贡献较大，仍不能断言历史minibatch或梯度因果。\n\n'
doc+=f'''DECISION77绑定{len(decision['evidence'])}项准确证据，SHA `{sha(D/'DECISION77.json')}`；理由原件`runtime/recovery77_completion_preparation_20261029_v1/CONTINUATION_REASON.txt`。未证明收敛，因此接续一轮同科学配置77并采集原前瞻76–78窗口，不保证更多训练必然改善。旧53–55及后续全部失败窗口保留，原74–76因75中断无法评定；新76–78 PLAN SHA57b3d6be原件不变、原5%/近零1/seed2026102855/5000/anchor55保持。近零保护不用于推离零。

准确77 CHECK_ONLY三路全learner/optimizer/RNG/replay和next65536一致、各9拒绝通过；77协议新增显式post_interruption_continuation绑定完整76，保留原initial恢复历史与旧stage字段，明确不伪造完整75。三路实际GPU INITIAL_STATE精确；首批实际checkpoint旧回放/历史、原优化器/物理映射/奖励/30模型/30sampler/CPU affinity审查通过：

'''
for m,v in startup.items():doc+=f"- {m} 新增{v['added_steps']}，旧{v['retained_replay_rows']}行全部字段保持，reward最大误差{v['max_reward_reconstruction_error']}。\n"
doc+='\n|当前任务|PID / start ticks|\n|---|---|\n'
for j in snap['learners']:doc+=f"|77 {j['method']}|{j['pid']} / {j['proc_start_ticks']}|\n"
doc+=f"|77 archive/health|{snap['archive']['pid']} / {snap['archive']['proc_start_ticks']}|\n"
for k,j in snap['waiters'].items():doc+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|\n"
doc+='\n77完整loss/独立保存算术自动等待已部署，保留49–74/76历史、显式拒绝75，配对76→77；77归档/replay/reward/health和startup均绑定源码。77完整标签、基于完整76的全2274终端锚点后续仍需准备，实际77完整结果未有；无自动78。\n\n'
doc+=f'''从前次保存起{len(rows)}个guard样本最低{snap['guard']['minimum']}%，低于50次数{snap['guard']['below50']}。76结束到77启动之间是CPU审查/恢复准备，GPU当时由合成保底占用，不能称科学吞吐持续；原v6进程保持，科学全部完成后仍保载。早前容器空档与预热样本保留，非重启自启服务。

开工实际fetch/read main6492ab17、baselinef6e8f8c，发布前又读mainc1e2bf02（另一主机非RL86→89）及交接，双方新增日志安全合并原字节保留；未操作非RL进程，无子agent。源码基线{receipt['source_base_commit']}。本轮此前push128缺HTTPS认证，不能称远端已发布；待最终实际结果记录。

共享SSD证据 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员/AST核验。[收据]({TAG}_SAVE.json)。大checkpoint/replay/raw仍SSD，非HDD/arm1全备份；现有HDD最新入口仍指已补本报告链接的主恢复文档。

下一步保持原77/76–78/guard，补77全标签与全2274终端后续；等完整77全审/实际图后再决定78，按原reward/loss目标判断，Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n当前最新：[完整76审查与77实际接续]({TAG}.md)。77启动审查通过，原76–78与GPU保载继续，Goal active。\n')
entry=f'''## 2026-10-29 — 完整恢复76与有限77实际接续

- [最新交接](docs/{TAG}.md)。76三路各30×55/41250/noabort，旧partial75 replay/history全部保留、新reward重算0、网络optimizer有限；全loss/180标签/90reward对/health/全2244+30终端/实际图全审。I尖峰、Vactor漂移和short0600 Strict退化、A总体改善及long0200退化全部保留，未收敛。
- DECISION77绑定{len(decision['evidence'])}证据，三路准确全state/replay/next65536和actual INITIAL_STATE/startup通过，当前steps{steps}、各30sampler。原科学参数/75中断/76–78准确PLAN保持，无自动78、Direct34false，Goal active。77全loss和归档health已部署，77标签/2274锚点待补。
- guard{len(rows)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}，审查空档含合成保载、科研完成仍继续。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐成员/AST已核，大数据SSD非HDD/arm1全备份。main6492ab17后c1e2bf02/baselinef6e8f8c已读安全合并，认证发布待，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':a,b=s.split('\n',1);p.write_text(a+'\n\n'+entry+b.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[完整恢复76与77运行](docs/{TAG}.md)。完整76全审、77实际启动审查通过，原76–78与GPU保底继续；无自动78，Goal active。**\n\n'+p.read_text())
print(json.dumps(receipt));print(json.dumps(snap))
