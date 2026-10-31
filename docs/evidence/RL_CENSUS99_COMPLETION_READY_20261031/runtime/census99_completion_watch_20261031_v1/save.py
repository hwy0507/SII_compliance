from pathlib import Path
import json,hashlib,time,tarfile,ast,socket,subprocess
D=Path(__file__).resolve().parent;B=D.parents[1];C=B/'runtime/census99_completion_20261031_v1';R=B/'runs/parameter_census_cycle99_20261031_v1';REPO=B/'repository/SII_compliance'
TAG='RL_CENSUS99_COMPLETION_READY_20261031';A=B/'repository'/TAG;E=REPO/'docs/evidence'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
obs=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert obs['passed'] and obs['identity_count']==103
for j in obs['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
assert read(C/'WAIT_PREFLIGHT.json')['passed'];assert not list(C.glob('WAIT_FAILURE*'))
plan=read(C/'WAIT_PLAN.json')
for p,h in plan['sources'].items():assert sha(p)==h
assert not (C/'AUTOMATED_CHECKS_FINISHED.json').exists() and not (C/'COMPLETE99_SCIENTIFIC_REVIEW.json').exists()
assert not (B/'runs/parameter_census97_99_reward_stability_20261031_v1/REGISTRATION.json').exists()
G=Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1');assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists()
samples=[json.loads(x) for x in (G/'samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=plan['time']]
assert samples and time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples))
steps={m:read(R/m/'train/PROGRESS.json')['steps'] for m in obs['first_steps']}
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),steps=steps,gpu=gpu,goal='active',original99_and_four_consumers_live=True,guard_kept_after_science=True))
files=set()
for root in [C,D]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.diff','.json','.jsonl','.log'}:files.add(p)
for p in [R/'LAUNCH.json',R/'MONITOR_LAUNCH.json',B/'repository/RL_CENSUS99_DIAGNOSTICS_20261031/RECEIPT.json',B/'repository/RL_CENSUS99_DIAGNOSTICS_20261031/PUBLICATION.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete99 read-only closure preparation and registered waiter; original99 live. Depends on149f0ee7 diagnostics and ba3dfba4 complete98/startup evidence plus original sharedSSD large data. No full99 or convergence claim.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for m in z.getmembers():assert z.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='149f0ee7291844bcec06f5ff3ba4bae009c5884b',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD evidence only; HDD254-byte pointer, not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
delta={m:obs['last_steps'][m]-obs['first_steps'][m] for m in steps}
report=f'''# 第99轮完整检查已准备并接入等待 — 2026-10-31

**Goal active；原三路99训练、归档及三个诊断消费者继续。新增的第四个只读消费者等待原99核心完成，完整99/原97–99窗口统计/loss健康及最终指定ESN公平评测仍待。**

`{C}`保存完整检查源码及相对完整98的逐行diff：

- `check_full_context99.py`：每条新增transition覆盖；非终端全52维与同条件下一current状态精确相连，所有current context对原journal精确，30终端next context遵守原复制规则；checkpoint前后hash不变。
- `review_saved99.py`：全部原始optimizer行和11种保存指标逐值精确、有限；原loss/条件loss/actor全部均值、首末1000和极值独立复算，保留原loss最高20点。
- `consolidate99.py`：原回放/新52/action/reward/全90条件/8803旧及90新终端与全8893参考/五实际图审查后才汇总；通过不代表loss健康或收敛，原97–99统计仍须独立完成。

逐行diff与AST结构核对完成，仅阶段标记/路径/相应终端总数变化；原97 continuity helper、原97–99 intent和94–96失败引用未变，600万容量和41250上限保持。真实完整98父checkpoint绑定通过；当前缺完整99时三脚本均实际拒绝且未生成结果，日志属于预期负向预检，不是正式训练失败。

唯一等待器PID `{read(C/'PROCESS.json')['pid']}`，身份见`{C}/PROCESS.json`，代码/计划/helper hash锁定。等原archive core FINISHED后依次跑context/loss两项，单项最多1800秒；等待截止沿原99启动+14400秒，未扩展训练。未来`AUTOMATED_CHECKS_FINISHED.json`仍明确实际图/汇总/原97–99统计待；不自动执行汇总或启动100。恢复先核PID/start ticks与输出，不因观察超时重启。

103身份连续{obs['elapsed_s']:.3f}s/{obs['samples']}样本保持，三路步数增长{delta}；保存累计steps{steps}。GPU{gpu['samples']}采样/{gpu['seconds']:.3f}s最低{gpu['minimum']}%，低于50次数{gpu['below50']}，末{gpu['last']}%。含保活负载，不算科学吞吐或保证所有瞬时；科学完成后guard继续、勿创建STOP，非重启自启服务。

原97→98的5%必要条件三路失败不变，完整99仍要完成原前瞻97–99审查，不能换98–100。Direct33原数值验收与冻结30 Task/Strict0/0保持，不派发34；旧28最终memory缺口/恢复2已证、指定ESN/共同最终集合SPT与公平比较均待。

主机`{socket.gethostname()}`；共享SSD根`{B}`；解释器`{B}/env/bin/python`。证据包`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员回读核验。依赖上轮149f0ee7/完整98与99启动ba3dfba4及原共享SSD大型checkpoint/replay/raw，非HDD/arm1全备份。HDD配额满，仅原254-byte LATEST入口更新。

开工实际query/fetch/read main149f0ee7/baselinef6e8f8c2；发布核验见`{A}/PUBLICATION.json`。
'''
(REPO/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 第99轮完整context/loss检查准备通过，第四只读消费者等待

- [交接](docs/{TAG}.md)。完整99全新增52/context与全部loss日志/数组/独立算术检查已准备；汇总需全90/8803旧+90新终端与五实际图。逐行diff/AST结构通过，原97 helper/97–99意向/94–96失败保持。
- 实际98父绑定及缺完整99三脚本拒绝通过，未生成完整结果；唯一第四只读等待器沿原archive截止，core后自动执行context/loss，无100派发。103身份连续{obs['elapsed_s']:.3f}s、steps增长{delta}；原科学作业继续。
- 完整99/原97–99统计与loss健康、指定ESN/最终公平比较仍待，Goal active；原97→98必要条件失败及Direct33原验收/冻结0/0/历史缺口保持。GPU{gpu['samples']}样本最低{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。
- SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254-byte指针；main149f0ee7/baselinef6e8f8c2实际query/fetch/read，发布见收据。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();new=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+new+rest.lstrip('\n'))
 else:p.write_text(new+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');size=pointer.stat().st_size;data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps),indent=2))
