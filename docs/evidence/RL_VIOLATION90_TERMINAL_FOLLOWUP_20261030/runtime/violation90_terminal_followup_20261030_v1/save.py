from pathlib import Path
import json,time,os,socket,hashlib,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];P=D;R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle90_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';N=B/'runs/violation90_fixed87_terminal_followup_20261030_v1';TAG='RL_VIOLATION90_TERMINAL_FOLLOWUP_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
updated=read(N/'PREFLIGHT_REVIEW.json');observed=read(D/'OBSERVATION_REVIEW.json');assert updated['passed'] and observed['passed'] and read(D/'DIRECT_SCOPE_REVIEW.json')['passed']
assert not (N/'FINISHED.json').exists() and not list(N.glob('WAIT_FAILURE_*.json'))
for name,h in read(N/'PLAN.json')['source_hashes'].items():assert sha(D/name)==h
for pid,start in observed['original_identities'].items():
 f=Path('/proc',pid,'stat').read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==start
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (D/'OBSERVATION_FAILURE.json').exists()
for m in updated['methods']:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
progress={m:read(T/m/'train/PROGRESS.json') for m in updated['methods']};frozen={m:read(F/m/'PROGRESS.json') for m in updated['methods']};rows=[]
for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines():
 try:x=json.loads(line)
 except json.JSONDecodeError:continue
 if x['time']>=read(N/'PLAN.json')['time']:rows.append(x)
assert time.time()-rows[-1]['time']<25 and not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists();(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress90=progress,frozen88=frozen,original_identities=observed['original_identities'],goal='active',fixed87_complete90_predictions=False,automatic91=False))
files=set()
for directory in [D,P,N]:
 for p in directory.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.log','.diff','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for m in progress:
 for n in ['EXECUTION.json','PROGRESS.json']:files.add(T/m/'train'/n)
 for n in ['PROGRESS.json','RESULTS.json']:files.add(F/m/n)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json']:files.add(T/n)
for n in ['LAUNCH.json','REVIEW_LAUNCH.json']:files.add(F/n)
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_VIOLATION90_FROZEN_READY_20261030'/n)
files.add(B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json')
files.add(B/'runs/serl_take33_frozen_combined_review_20261030_v3/REVIEW.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed original87 terminal followup preregistration for complete90, saved87/88/89 arithmetic and raw-bit inputs checked. No full90 predictions yet; original scientific jobs continue.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='4b19b5f9f797fecad4bc2a27d9b4b8fab9349aa7',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; HDD existing254-byte pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 原90继续；固定87终端跟踪90已登记

2026-10-30 UTC，Goal active。上一轮[已学90冻结接口与首5000 loss](RL_VIOLATION90_FROZEN_READY_20261030.md)为progress。本轮在原90训练继续期间准备固定旧终端的完整90后续诊断，不重复Direct训练/评测，不增加90预算、不自动91或Direct34。

主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。已实际query/fetch/read main `4b19b5f9f797fecad4bc2a27d9b4b8fab9349aa7`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关科学协议变化。采用仓库sii-research-sync，无子agent。

## 固定终端跟踪

来源 `{D}`，运行/方案 `{N}`。原87全部终端集合不变：I2605、A2604、V2604，共7813条；每条保留全部5 critic和原masks，不挑选后续表现较好的样本。原87/88/89预测、indices、observations51、actions、rewards、masks直接取已审保存NPZ。

新52维终端输入为原51特征附加当前raw preaction严格穿透bit。原完整89 raw sidecar/bit SHA逐一绑定90的violation amendment；原终端历史特征逐位相同，bit逐条与raw >0.0002m独立复算一致。终端bit0/1数量 `{ {m:v['bit_counts'] for m,v in updated['methods'].items()} }`。原87/88/89全部masked SSE/MSE、all-row SSE、mask分母保存值独立标量复算与已有报告精确一致；0新神经forward/0物理/0更新。真实缺完整90审查前置条件拒绝通过，不把partial90当complete。

`compare90.py`在完整90 REVIEW/FINISHED/health/loss通过且绑定同一checkpoint后才运行；使用已验证的52维violation恢复接口，检查实际90完整边界、双marker、原continuation、全旧终端indices/52特征/actions/rewards/masks精确。每方法所有5 critic仅做一次完整旧终端预测，检查完整learner/replay/RNG/hash不变，保存87/88/89/90结果、独立标量统计及六栏图。全部改善和退化保留，不引入零终端误差收敛门槛。

唯一等待器PID `{read(N/'PROCESS.json')['pid']}`/start `{read(N/'PROCESS.json')['start']}` 已启动，并实时核验原archive1096452身份。截止沿用原90 launch+14400s（Unix `{read(N/'PLAN.json')['wait_deadline_unix']}`），没有扩展原训练/归档预算；诊断自身最多1800s。此等待器不启动训练/新物理，完整90当前仍缺、尚未产生新90终端预测。生成图后仍需实际查看。

这是固定已见终端的保留/拟合诊断。90包含新在线训练和51→52修订，不能把差异归因为bit的单独因果收益、泛化、策略性能或整体收敛。它也不覆盖88—90新增终端；完整90的原health仍负责全部回放终端。原88—90失败窗口保留，新90—92统计方案不授权91/92训练。

## Direct范围复核

重新读取原DIRECT_STAGE_DECISION及其7项hash绑定证据，并检查完整冻结33的实际保存审查。Direct原数值阶段已经接受，原27—29窗口及33平稳loss支持此有限范围；不能因Task/Strict0/0另加新的收敛条件或为了GPU占用重新启动34。

最新冻结33仍全30、Task/Strict0/0、机器违规0，原28已保存动作精确重现、新2最终全state不变；原28最终内存证明丢失仍明确保留，额外877中断动作不计入完整分母。没有重跑已有物理、训练或bootstrap，指定ESN与最终比较仍缺，不替换他主机模型。新 `{D}/DIRECT_SCOPE_REVIEW.json`仅核验现有证据和范围，不覆盖原决定。

## 当前科学与GPU

原90三路训练及90sampler、原冻结88、collector/postprocessor和guard均保持原身份。新{observed['elapsed_s']:.3f}秒/{observed['samples']}样本/{observed['identity_count']}身份观察通过，三路steps增加。保存总steps `{ {m:v['steps'] for m,v in progress.items()} }`；原冻结88完成数 `{ {m:v['completed_conditions'] for m,v in frozen.items()} }`。完整90与原冻结88最终全90/raw/82→88配对仍待，原21600s冻结截止不延长。

原科学协议保持：30×55s/最多41250新transition、4m append/23与47marker、terminal128、batch65536/UTD1/原LR/reward/masks、actor49/canonical48、clock49/history50/bit51、物理/MJB/gates/filter/执行器限制/dt5e-5。既有partial75、74—76不可判、79安全abort、全部旧失败窗口、半std拒绝及软件失败保留。首5000 loss的I尖峰和actor漂移不能被此准备工作解释为解决。

GPU原v7 supervisor97370/worker97399–97402继续，科学全部结束后仍按用户要求保载，不创建STOP。本轮{gpu['samples']}采样最低{gpu['minimum']}%，低于50样本{gpu['below50']}，末值{gpu['last']}%；含合成负载，不作科学吞吐或每瞬时保证。历史低谷保留，guard不是重启服务。

## 保存与接续

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节/SHA256 `{receipt['sha256']}`，全部tar成员/AST核验。Git index/commit逐字核验、正常push与真实远端确认后写包外PUBLICATION。大产物仍原共享SSD，HDD只原位更新已有254字节指针，非HDD/arm1全备份。

下一步保持原90、原冻结88与唯一固定87终端等待器；完整结果到齐后收全loss/health/任务标签、终端跟踪和实际图，再决定有限下一步。未有完整90前不发布其性能或reward稳定结论。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 原90继续；固定87全部终端跟踪90已登记

- [交接](docs/{TAG}.md)。固定原87全部7813终端/all5/原masks，旧87/88/89保存算术精确；新增52输入与raw bit/历史逐位绑定通过，真实缺完整90拒绝。唯一等待器{read(N/'PROCESS.json')['pid']}沿原archive截止等待，无新forward/physics/update、无90新终端结果或自动91。
- Direct原数值验收及冻结33全30 Task/Strict0/0、旧28最终内存证明缺失复核保留，不额外启动34。原90/冻结88持续，{observed['elapsed_s']:.3f}秒/{observed['identity_count']}身份保持，总steps{ {m:v['steps'] for m,v in progress.items()} }，完整结果与健康收敛仍待。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载；冻结88完成数{ {m:v['completed_conditions'] for m,v in frozen.items()} }。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份。main4b19b5f9/baselinef6e8f8c已query/fetch/read，发布见收据；Goal active，无子agent，所有历史失败保留。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:v['steps'] for m,v in progress.items()},frozen={m:v['completed_conditions'] for m,v in frozen.items()})))
