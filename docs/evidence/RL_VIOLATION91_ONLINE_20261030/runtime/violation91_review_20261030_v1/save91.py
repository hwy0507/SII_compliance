from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,os
D=Path(__file__).resolve().parent;B=D.parents[1];P=B/'runtime/violation91_continuation_20261030_v1';R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle91_20261030_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';FP=B/'runtime/violation90_frozen_postprocess_20261030_v1'
TAG='RL_VIOLATION91_ONLINE_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
startup=read(T/'startup/REVIEW.json');observed=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert startup['passed'] and observed['passed'] and read(P/'PREFLIGHT_FINISHED.json')['passed'] and read(D/'CONSUMER_PARENT_BOUNDARY_REVIEW.json')['passed']
identities=list(observed['identities'])+read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(FP/'PROCESS.json')]
for j in identities:
 fields=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert fields[0]!='Z' and fields[19]==str(j.get('start',j.get('proc_start_ticks')))
for folder in (D,P):
 for name,h in read(folder/'SOURCES.json')['files'].items():assert sha(folder/name)==h
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists() and not (F/'REVIEW_FAILURE.json').exists() and not list(FP.glob('FAILURE*'))
progress={m:read(T/m/'train/PROGRESS.json') for m in ('impedance','admittance','vmc')};frozen={m:read(F/m/'PROGRESS.json') for m in progress}
for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(l) for l in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(P/'SCIENTIFIC_DECISION.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),progress91=progress,frozen90=frozen,identities=identities,gpu=gpu,goal='active',automatic92=False))
files=set()
for directory in (D,P):
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.log'} and p.stat().st_size<10_000_000:files.add(p)
files.update(T.glob('*.json'));files.add(T/'startup/REVIEW.json')
for m in progress:
 for n in ('REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json','VIOLATION_EXECUTION.json','trainer_registered.py'):files.add(T/m/n)
 files.add(T/m/'check/INITIAL_STATE_REVIEW.json')
 for n in ('EXECUTION.json','PROGRESS.json'):files.add(T/m/'train'/n)
 for n in ('PROGRESS.json','STARTUP_REVIEW.json'):files.add(F/m/n)
for n in ('LAUNCH.json','REVIEW_LAUNCH.json'):files.add(F/n)
for n in ('PROCESS.json','LAUNCH_BINDING.json'):files.add(FP/n)
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_COMPLETE90_FROZEN90_20261030'/n)
for p in [B/'runs/parameter_violation_cycle90_review_20261030_v1/REVIEW.json',B/'runs/parameter_violation_cycle90_review_20261030_v1/loss/REVIEW.json',B/'runs/parameter_violation_cycle90_review_20261030_v1/PLOT_INSPECTION.json',B/'runs/violation90_fixed87_terminal_followup_20261030_v1/REVIEW.json',B/'runtime/violation90_completion_20261030_v1/ABORT_REVIEW.json',B/'runs/parameter_violation90_92_reward_stability_20261030_v1/PLAN.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Finite same52 continuation91, actual complete90 including safety abort retained;108 negative guards,6 restored native clone updates, exact initial state and live startup/full old replay/new mappings,120s identities. Complete91 still pending; frozen90 and guard continue.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
remote=read(P/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 精确完整90接续有限91；原冻结90继续

2026-10-30 UTC，Goal active。完整90 review/loss/health、全部89→90对照及固定87终端诊断已审；本轮单独登记并启动同52修订的有限91，不自动92，不启动Direct34。原冻结90评测/collector/postprocessor保持原身份运行，最终全90/raw/88→90配对仍待。前序[完整90与冻结90](RL_COMPLETE90_FROZEN90_20261030.md)。

主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。实际query/fetch/read main `{remote['main']}` 与baseline `{remote['baseline']}`，无新相关科学协议变化；采用sii-research-sync，无子agent。新driver及登记源码 `{P}`，消费者 `{D}`，实际训练 `{T}`。完整父checkpoint均来自 `{B}/runs/parameter_violation_cycle90_archive_20261030_v1/<method>/cycle_00090.pt`，不回退原89迁移快照、不重新初始化。

科学依据：90 critic尾部均值下降，但I后段尖峰/actor漂移；固定旧终端总masked SSE I改善83.45%、A退化9.70%、V退化146.79%，全部critic退化保留。A/V在线标签恢复部分成功，而I long0000在35.08s发生全局物体/角台穿透安全中止，外部bit0并不覆盖该事件。该混合证据未证明收敛或架构全面有效；单独再运行一个同52/原目标周期，以检查改善和退化的持续性，减少再次改变算法造成的解释混淆。原失败/安全门不修改，无离线权重晋升。完整91审查前不得自动92；90—92统计预登记本身不授权训练。

新driver恢复准确已学90，不再调用只接受迁移89的validate_migrated。注册元数据只变有限continuation，所有科学/历史协议与实际90相同；trainer_registered.py与实际90源码逐字相同，interval消费一次、plateau修订floor仍90、两架构持久字段保留。完整parent的learner/replay/RNG/optimizer/history精确恢复，真实I rows3729700、A3732500、V3733500；I40752新步及安全中止保留，不假定它有41250。两marker、52维、4m append、23/47历史容量、原clock/history/bit、全历史cycles及partial75排除保持。

三方法各36负例，共108拒绝：周期/预算/自动后续/超参/协议变更、错误父身份/partial/seed/steps、缺marker、51维旧current/next、cursor/capacity/优化器计数及错误violation amendment。全部真实父通过；实际batch65536各2次可丢弃clone更新，共6次，重复metrics/完整state精确，随后learner/replay RNG原状态恢复，0正式更新/物理、无clone权重推广。保存check-only精确digest及正式启动INITIAL_STATE_REVIEW。

新startup/full review/health/loss/archive消费者沿原实现。health91算法与health90逐字相同；loss首步由准确完整90 review.steps绑定，I3729701/A3732501/V3733501开始，避免以原89 binding或假定完整41250算错中止后的边界。新archive只消费完整91，保留全部终端/原masks、实际中止长度；完整loss/health仍待。

实际启动全旧回放所有52列/其他字段逐位保留，三方法startup新增 `{ {m:x['added_steps'] for m,x in startup['methods'].items()} }`；新current/next raw bit、连续history、clock、action和reward逐条核验，reward最大误差 `{ {m:x['max_reward_reconstruction_error'] for m,x in startup['methods'].items()} }`。每方法30冻结MJB/30sampler/learner原CPU组、batch65536/UTD1/terminal128/原LR、4m markers与历史保持。120秒观察实际 `{observed['elapsed_s']:.3f}s`、{observed['identity_count']}身份、{observed['samples']}样本通过，总steps `{ {m:x['steps'] for m,x in progress.items()} }`。

固定物理/MJB/Task/Strict/filter/执行器/dt5e−5、actor49/canonical48不变。每方法仅30×55s/最多41250新transition，critic/replay52、clock49/history50/rawbit51不变；同修订window只有完整90，尚无完整91/92，未跑缺失窗口统计。91早期进度不是reward稳定/loss健康结论。旧88—90失败、partial75、74—76不可判、79/90安全中止、半std拒绝、全部软件失败保持。

原冻结90仍 `{F}`，evaluator283421/283428/283430、collector283433、postprocessor292743保持原身份；保存完成数 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`，不重启、不扩展原21600s截止。Direct原数值阶段已接受，冻结33全30 Task/Strict0/0和原28最终内存证明缺失保持；指定ESN仍缺，不替用其他主机模型。

原GPU guard97370及97399–97402继续，科研完成后仍保载。本轮{gpu['samples']}采样/{gpu['elapsed_s']:.1f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；含合成负载，不等于科学吞吐或每瞬时保证。历史v7 warmup0/v6低谷保留，非重启自启服务。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，逐tar成员/AST核验。Git index/commit逐字及正常push/实际远端确认后写包外PUBLICATION。大checkpoint/raw仍共享SSD；HDD仅原位254字节指针，非HDD/arm1全备份。

接续：保持原91、唯一archive/完整review/health/loss消费者及原冻结90；完整91与90→91差异到齐后再决定下一有限阶段，并继续原90—92稳定性方案的实际输入绑定，不把新阶段启动当作收敛。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整90精确恢复；同52修订有限91实际运行

- [交接](docs/{TAG}.md)。依据完整90混合结果及I安全中止单独登记91，trainer与实际90逐字相同，原52/actor49/历史/Adam/RNG及全部协议保持，无自动92/Direct34。108负例、6真实batch65536 clone重复恢复通过；I按实际3729700父行保留中止，loss边界不假定41250。
- 实际startup旧52全回放/新bit-history-clock/action/reward0误差、30MJB/30sampler通过；{observed['elapsed_s']:.3f}s/{observed['identity_count']}身份保持，总steps{ {m:x['steps'] for m,x in progress.items()} }。完整91、reward稳定和loss健康待；原90冻结完成数{ {m:x['completed_conditions'] for m,x in frozen.items()} }继续，最终全90/raw/paired待。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验、HDD仅254字节指针，非HDD/arm1全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read，正常发布见收据；Goal active，无子agent，所有旧失败保留。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()},frozen={m:x['completed_conditions'] for m,x in frozen.items()})))
