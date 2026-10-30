from pathlib import Path
import json,time,hashlib,tarfile,ast,datetime,socket,subprocess,math
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle76_20261029_v1';AUD=B/'runs/parameter75_interruption_recovery_20261029_v1';W=B/'runs/parameter_recovery76_78_reward_stability_20261029_v1';L=B/'runs/parameter_recovery76_loss_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_RECOVERY75_PARTIAL_TO76_20261029'
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def identity(j):
 f=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split();assert f[19]==j['proc_start_ticks'] and f[0]!='Z';return dict(pid=j['pid'],proc_start_ticks=f[19],state=f[0])
assert read(AUD/'REVIEW.json')['passed'] and read(RUN/'startup/REVIEW.json')['passed'] and read(D/'FOLLOWUP_DEPLOYMENT_REVIEW.json')['passed']
decision=read(D/'DECISION_RECOVERY76.json')
for x in decision['evidence'].values():assert sha(Path(x['path']))==x['sha256']
snap=dict(time=time.time(),host=socket.gethostname(),learners=[],waiters={},guard=[])
for j in read(RUN/'LAUNCH.json')['jobs']:
 v=identity(j);p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists() and not (p.parent/'DRIVER_FAILURE.json').exists();v.update(controller=j['controller'],progress=read(p/'PROGRESS.json'),samplers=len(Path(f'/proc/{j["pid"]}/task/{j["pid"]}/children').read_text().split()));assert v['samplers']==30;snap['learners'].append(v)
snap['archive']=identity(read(RUN/'MONITOR_LAUNCH.json'))
for key,p in [('loss76',L),('window76_78',W)]:
 j=read(p/'LAUNCH.json');assert sha(p/'PLAN.json')==j['plan_sha256'];snap['waiters'][key]=dict(identity(j),plan_sha256=j['plan_sha256'])
g=read(G/'LAUNCH.json')
for pid in [g['pid'],*g['workers'].values()]:
 f=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z';snap['guard'].append(identity(dict(pid=pid,proc_start_ticks=f[19])))
assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists()
raw=[l for l in (G/'samples.jsonl').read_bytes().splitlines(keepends=True) if l.endswith(b'\n')];rows=[json.loads(l) for l in raw];assert time.time()-rows[-1]['time']<15
first=next(i for i,r in enumerate(rows) if all(v['utilization']>=50 for v in r['gpus']));stable=rows[first:];assert len(stable)>20
stats=[]
for i in range(4):
 values=[next(v['utilization'] for v in r['gpus'] if v['gpu']==i) for r in stable];allvalues=[next(v['utilization'] for v in r['gpus'] if v['gpu']==i) for r in rows];stats.append(dict(gpu=i,stable_min=min(values),stable_mean=math.fsum(values)/len(values),stable_below50=sum(v<50 for v in values),all_below50=sum(v<50 for v in allvalues)))
snap['guard_review']=dict(total_samples=len(rows),startup_samples=first,first_all_above50=stable[0]['time'],seconds_to_first_all_above50=stable[0]['time']-rows[0]['time'],stable_samples=len(stable),stats=stats,synthetic_guard_included=True,no_reboot_service=True);write(D/'FINAL_SNAPSHOT.json',snap);(D/'GUARD_SAMPLES.jsonl').write_bytes(b''.join(raw))
now=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).strftime('%H:%M:%S')
pointer=f'''# RL 2026-10-29 {now} UTC
ACTIVE.75 interrupted;76 recovery running. Guardv6 on.
SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl
Read repository/SII_compliance/docs/{TAG}.md
Large data SSD. No reboot service.
'''
hdd=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
if len(pointer.encode())>hdd.stat().st_size:pointer=pointer.replace('ACTIVE.75 interrupted;76 recovery running. Guardv6 on.','ACTIVE.76 recovery;guardv6.')
assert len(pointer.encode())<=hdd.stat().st_size
sources={Path(x['path']) for x in decision['evidence'].values()};folders=[D,AUD,RUN,RUN/'startup',L,W,B/'runs/parameter_partial75_recovery_cycle76_review_20261029_v1',B/'runtime/parameter75_verified_wait_0312_20261029_v1',B/'runtime/parameter75_wait76_preparation_20261029_v1']
for m in ['impedance','admittance','vmc']:folders.extend([AUD/m,RUN/m])
for folder in folders:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in ['.json','.py','.diff','.log','.jsonl','.txt','.png','.npz'] and p.stat().st_size<5_000_000:sources.add(p)
sources.add(B/'runs/parameter_capacity74_76_reward_stability_20261029_v1/PLAN.json');sources.add(B/'runtime/prepare_parameter75_20261029_v1/DECISION75.json')
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
def copy(p,rel):
 data=p.read_bytes();dest=E/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data);assert dest.read_bytes()==data
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(dest)))
for p in sorted(sources):copy(p,p.relative_to(B))
for n in ['guard.py','LAUNCH.json','CONTROL.json','RECOVERY.json']:copy(G/n,Path('guard_v6')/n)
write(E/'MANIFEST.json',dict(time=time.time(),files=manifest,large_checkpoints_replay_raw_excluded=True))
A=B/'repository'/(TAG+'_'+datetime.datetime.now(datetime.timezone.utc).strftime('%H%M%S'));A.mkdir();tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),sha256=sha(tar),bytes=tar.stat().st_size,members=len(manifest)+1,member_bytes_and_python_ast_verified=True,compute_host=socket.gethostname(),source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),large_artifacts='Shared SSD; not a full HDD or arm1 backup');write(R/'docs'/(TAG+'_SAVE.json'),receipt);write(A/'RECEIPT.json',receipt)
steps='/'.join(str(j['progress']['steps']) for j in snap['learners']);metrics=read(AUD/'REVIEW.json')['methods'];startup=read(RUN/'startup/REVIEW.json');mins='/'.join(str(x['stable_min']) for x in stats)
doc=f'''# 第75轮意外中断后的完整状态恢复与第76轮接续

2026-10-29 {now} UTC，Goal active。**当前主机 `{socket.gethostname()}`，当前运行是 `runs/parameter_partial75_recovery_cycle76_20261029_v1`；旧75及旧76准备路径不得重启。** 完整reward稳定与loss健康仍未证明。Direct33历史原训练条件数值结论、Task/Strict0/0保持，不启动34。

05:30UTC核验发现主机由rltest-1025--a6ed2ff39b3c-hsje5ateny变为当前容器，原75三learner/archive/全部等待器和guardv5进程消失；原75没有FINISHED、没有完整30回合，无训练FAILURE文件。不能以缺FAILURE当正常完成。此前03:11:56–03:21:56十分钟观察确已自然结束21样本/600.139秒，全部原身份当时live，末steps3113063/3113769/3114949；这是历史有效观察，不代表重启后存活。重启/退出具体原因与准确时间未确认，不冒充观察超时或算法故障。

发现时四GPU均0%且无compute应用，原v5最后样本03:21:05已过期。先在独立`/tmp/sii_gpu_util_guard_20261029_v6`启动与v5逐字节相同的已验证源码，保留全部旧记录。恢复后最初{first}个样本低于50，约{snap['guard_review']['seconds_to_first_all_above50']:.3f}秒后首次四卡均≥50；其后{len(stable)}个样本最低{mins}%，低于50次数{[x['stable_below50'] for x in stats]}。不得把重启空档写成持续达标。含合成负载，科研结束仍保载，仍非重启自启服务。

共享SSD `{B}`、解释器env/bin/python。三份原子落盘checkpoint_latest已复制到`runs/parameter75_interruption_recovery_20261029_v1/<method>/checkpoint_partial75.pt`并逐hash核验。完整网络/optimizer和所有回放数值有限；旧74回放全部字段精确，历史完整cycle记录不变；新增已保存transition的观察/action/context/clock及全部reward与原物理间隔日志重建一致。无新物理或优化更新用于此审查。

|方法|partial75 checkpoint steps|保留的75新增更新|最后PROGRESS超出checkpoint|checkpoint SHA256|
|---|---:|---:|---:|---|
'''
for m,v in metrics.items():doc+=f"|{m}|{v['steps']}|{v['retained_partial75_updates']}|{v['progress_beyond_checkpoint']}|{v['checkpoint_sha256']}|\n"
doc+='\n这些partial checkpoint没有MuJoCo中途状态。恢复保留全部已落盘learner/optimizer/RNG/replay/masks/history，启动30个新的物理回合作为独立完整76；不是补齐75、不是逐物理子步无缝续接。旧轨迹、未落盘进度和失败/中断记录不删除，不伪造terminal，不回退到完整74。\n\n'
doc+='三路CHECK_ONLY完整learner/replay及下一65536采样精确，原科学参数与恢复边界共9项错误配置/方法协议拒绝每路通过。恢复driver绑定准确partial checkpoint/原75登记/全部依赖hash；原训练器只增加3处恢复元数据与初始状态审查调用，逆变换逐字等于原注册训练源码。原完整边界验证被独立、显式、严格的partial75边界验证替代，未伪称原完整边界验证通过。实际GPU启动INITIAL_STATE_REVIEW三路全state精确，首批新增checkpoint及真实物理映射也已审查：\n\n'
for m,v in startup['methods'].items():doc+=f"- {m} 实际新增{v['added_steps']}，旧回放/完整历史保留，reward重建最大误差{v['max_reward_reconstruction_error']}，30模型/30sampler/CPU affinity核验。\n"
doc+=f'''\nDECISION_RECOVERY76绑定{len(decision['evidence'])}项证据，SHA `{sha(D/'DECISION_RECOVERY76.json')}`。仅一轮76、无自动77。原30条件×55秒/最多41250新增、4m append/markers23与47、terminal128、batch65536、UTD1、LR/masks/reward/物理/gates和历史目标配对归约全部保持。当前steps {steps}，各30sampler，无FAILURE。

|任务|PID / start ticks|
|---|---|
'''
for j in snap['learners']:doc+=f"|76 {j['controller']}|{j['pid']} / {j['proc_start_ticks']}|\n"
for k,j in snap['waiters'].items():doc+=f"|{k}|{j['pid']} / {j['proc_start_ticks']}|\n"
doc+=f"|archive/health|{snap['archive']['pid']} / {snap['archive']['proc_start_ticks']}|\n"
doc+='\n76归档/完整回放reward审查/health自动监控已部署；完整loss及独立保存值算术自动审查已部署。完整49–74历史继续保留，75明确缺完整reward，新增76；74→76配对明确跨越partial75额外训练曝光，非原连续周期替代。全标签/终端后续与实际全轮图仍需审查。\n\n'
doc+=f'''原74–76 PLAN d8c243d9原件不变，因75中断明确无法评定，不重启原541941等待器或把部分结果塞入窗口。新的`runs/parameter_recovery76_78_reward_stability_20261029_v1/PLAN.json` SHA `{sha(W/'PLAN.json')}`，在76启动前登记76/77/78三个新的完整周期，保留5%/近零1/seed2026102855/5000bootstrap/anchor55和全部历史窗口/失败结论；只是中断后前瞻窗口，不按76结果选端点。新等待器已启动，无自动训练/停止。近零保护不是推离零的新目标。

旧canonical76 prepare/原76loss静态工具、原75完成观察/决定工具及旧75标签/终端/74–76等待全部不再适用，路径清单见`runtime/parameter75_interruption_recovery_20261029_v1/SUPERSEDED_PREPARATIONS.json`。保留旧源和hash，仅新建恢复登记；不要运行旧DECISION76助手或另启动canonical76造成重复训练。03时段准备记录保留，未执行的旧保存脚本也不能现在强行执行。

开工及恢复时实际fetch/read远端main08437d86（查询瞬间ba81b92c随后前进）、baselinef6e8f8c，阅读非RL原108进度77/108及最新衔接记录；本地6bc2e423与并行非RL安全合并，两处日志冲突双方新增逐字保留，记录REMOTE_MERGE_REVIEW。未操作另一主机进程。当前保存源码基线{receipt['source_base_commit']}，遵循sii-research-sync，无子agent。

此前push诊断为GitHub HTTP401转入VSCode askpass等待；禁交互返回128无法读取HTTPS用户名，不能继续称纯网络故障。前轮本地提交及本次恢复保存须按实际push结果区分，不能假定已远端发布；不索取私钥/token。源码和小证据已保存本地Git/共享SSD，大数据未同步arm1。

共享SSD证据包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员与Python AST核验。[收据]({TAG}_SAVE.json)。大partialcheckpoint/startup checkpoint/replay/raw均仍共享SSD，非HDD/arm1全备份；HDD最新入口已重写回读。

下一步保持当前76和guardv6，补齐76全标签/基于partial75的全2244终端诊断；待完整76全审/真实图后再决定有限77。新76–78窗口保持原门槛，原75中断始终保留。Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 新容器partial75精确恢复与完整76

- [最新交接](docs/{TAG}.md)。05:30发现容器主机更换、旧75/全部等待/guardv5消失，无FINISHED75；旧21样本观察当时有效，不能冒充当前live。旧75明确中断，原74–76无法评定，旧canonical76准备全部superseded，勿重复启动。
- 三partial75 checkpoint保留新增23000/24000/24000；完整旧回放/history、全新增物理间隔reward/action/clock及有限网络optimizer审查通过，reward误差0。全state/next65536检查及每路9拒绝通过；新独立76实际INITIAL_STATE与startup通过，当前steps{steps}，无回退或伪造terminal/完整75。
- 原科学参数/4m markers/65536/UTD1/terminal128保持，只登记一轮76无自动77；新76全loss/归档health和前瞻76–78窗口已部署，原5%/近零1/bootstrap/anchor55及全部历史结论保持。Direct34false、Goal active。
- guardv6同v5源码独立恢复，约{snap['guard_review']['seconds_to_first_all_above50']:.3f}秒后四卡≥50；其后{len(stable)}样本min{mins}%、低于50{[x['stable_below50'] for x in stats]}，保留最初{first}空闲样本和重启空档，科研完成仍保载，非自启服务。
- SSD包{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐字节/AST核验，大数据SSD非HDD/arm1全备份；实际fetch/read main08437d86/baselinef6e8f8c，安全合并非RL双方日志，无子agent。GitHub此前认证缺失，发布须以实际push为准。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':title,rest=s.split('\n',1);p.write_text(title+'\n\n'+entry+rest.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[新容器partial75恢复→76](docs/{TAG}.md)。旧75已中断，原74–76无法评定；当前独立76/76–78/guardv6运行，勿执行旧canonical76工具。Goal active。**\n\n'+p.read_text())
hdd.write_text(pointer);assert hdd.read_text()==pointer;print(json.dumps(receipt,indent=2))
