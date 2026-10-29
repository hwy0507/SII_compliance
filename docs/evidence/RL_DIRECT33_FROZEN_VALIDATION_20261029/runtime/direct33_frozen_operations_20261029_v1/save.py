from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;O=B/'runs/serl_take33_frozen_full30_20261029_v1';RT=B/'runtime/serl_take33_frozen_full30_20261029_v1';P=B/'runs/parameter_partial75_recovery_cycle78_20261029_v1';G=Path('/tmp/sii_gpu_util_guard_20261029_v6');TAG='RL_DIRECT33_FROZEN_VALIDATION_20261029'
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def write(p,x):
 with p.open('x') as f:f.write(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def live(j):
 q=Path(f'/proc/{j["pid"]}/stat');f=q.read_text().rsplit(')',1)[1].split() if q.exists() else None
 return f is not None and f[19]==j['proc_start_ticks'] and f[0]!='Z'
obs=read(D/'OBSERVATION_FINISHED.json');assert obs['passed'] and obs['all_original_identities_live'] and obs['elapsed']>=120 and obs['samples']==5
assert read(D/'ACTUAL_FROZEN33_STARTUP_REVIEW.json')['passed'];assert not (O/'REVIEW_FAILURE.json').exists() and not (O/'COMPARISON_FAILURE.json').exists()
reg=read(O/'REGISTRATION.json')
for x in list(reg['inputs'].values())+list(reg['sources'].values()):assert sha(x['path'])==x['sha256']
snap=dict(time=time.time(),host=socket.gethostname(),parameter78=[],frozen33=[],review=read(O/'REVIEW.json') if (O/'REVIEW.json').exists() else None,goal='active',direct34=False)
for j in read(P/'LAUNCH.json')['jobs']:
 assert live(j);m=j['controller'];assert not (P/m/'train/FAILURE.json').exists() and not (P/m/'DRIVER_FAILURE.json').exists();snap['parameter78'].append(dict(method=m,pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],progress=read(P/m/'train/PROGRESS.json')))
for j in read(O/'LAUNCH.json')['jobs']:
 assert live(j);folder=Path(j['output']);assert not (folder/'FAILURE.json').exists();result=read(folder/'RESULTS.json') if (folder/'RESULTS.json').exists() else None
 snap['frozen33'].append(dict(pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],output=str(folder),completed_conditions=len(result['episodes']) if result else 0,finished=result['finished'] if result else False,active_case_progress={p.parent.name:read(p) for p in folder.glob('*/rollout.progress.json')}))
assert live(read(O/'REVIEW_LAUNCH.json')) and live(read(O/'COMPARISON_LAUNCH.json'))
for j in read(D/'OBSERVATION_PLAN.json')['jobs']:assert live(j)
start=read(B/'repository/RL_RECOVERY77_COMPLETE78_RUNNING_20261029/FINAL_LOCAL_RECEIPT.json')['time'];rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=start];assert rows and time.time()-rows[-1]['time']<20 and not (G/'FAILURE.json').exists()
snap['guard']=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=rows[-1],synthetic=True,keep_after_science=True);write(D/'SAVE_SNAPSHOT.json',snap);(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
sources={p for p in D.iterdir() if p.is_file() and p.suffix in ['.py','.json','.jsonl','.log','.diff']}
sources.update(p for p in O.iterdir() if p.is_file() and p.suffix in ['.json','.log'])
for folder in [O/'check_only',O/'shard0',O/'shard1']:
 sources.update(p for p in folder.iterdir() if p.is_file() and p.suffix in ['.json','.log'])
for folder in [O/'shard0',O/'shard1']:
 for case in folder.iterdir():
  if not case.is_dir():continue
  for n in ['rollout.progress.json','ADAPTER.json','executed_evaluator.py.txt','rollout.json','AUDIT_EXTENSION.json']:
   p=case/n
   if p.exists():sources.add(p)
for name in ['evaluate_serl33_frozen_20261029.py','review_serl33_frozen_matrix_20261029.py','audit_published_episode_20261025.py','summarize_published_episode_audit_20261025.py','replay_published_filter_audit_20261025.py','replay_published_torque_audit_20261025.py']:sources.add(RT/name)
for p in [B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json',B/'runs/serl_take_cycle33_review_20261027_v1/REVIEW.json',B/'runs/serl_take_cycle33_review_20261027_v1/FINISHED.json',B/'runs/serl_take29_frozen_full30_20261027_v1/REVIEW.json',B/'runs/serl_take29_frozen_full30_20261027_v1/SOURCE_FREEZE.json']:sources.add(p)
E=R/'docs/evidence'/TAG;E.mkdir(exist_ok=False);manifest=[]
for p in sorted(sources):
 data=p.read_bytes();assert len(data)<5_000_000;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
write(E/'MANIFEST.json',dict(files=manifest,time=time.time(),large_artifacts_excluded=True,active_logs_are_point_in_time_snapshots=True))
for n in ['evaluate_serl33_frozen_20261029.py','review_serl33_frozen_matrix_20261029.py']:
 p=R/'tools'/n;assert not p.exists();p.write_bytes((RT/n).read_bytes());assert sha(p)==sha(RT/n)
A=B/'repository'/TAG;A.mkdir(exist_ok=False);tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),member_bytes_and_python_ast_verified=True,large_artifacts='Shared SSD; no full HDD/arm1 backup');write(A/'RECEIPT.json',receipt);write(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={x['method']:x['progress']['steps'] for x in snap['parameter78']};stamp=datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat();complete=sum(x['completed_conditions'] for x in snap['frozen33'])
doc=f'''# 最新Direct33冻结验证：登记、准确恢复与实际启动

{stamp}，Goal active。上轮[完整77与78续训](RL_RECOVERY77_COMPLETE78_RUNNING_20261029.md)已完成并继续；本轮补齐最新Direct33的冻结验证入口并实际启动全30条件。**当前冻结33完成{complete}/30回合，完整物理审查尚未完成，不预告成功或完整通过。** 参数78原三路继续，steps {steps}。

共享SSD `{B}`，执行主机 `{snap['host']}`。SERL推理用`{B}/serl_env/bin/python`，物理及根审查用`{B}/env/bin/python`，沿用原锁定upstream。源码基线 `{receipt['source_base_commit']}`；本轮实际fetch/read main b1deda6593c6b4bc76a76b89e30b5a6fc4998178、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，均未变，非RL新增保留，无子agent。

## 选择和范围

原Direct数值阶段决定保留完整33并禁止额外34，但旧冻结只覆盖29，不能用29认证33。本轮固定最新33 SHA783eaa7f7b03226915539e41cce313a5faeb4d49a15ae25626bb9762a9f47849（1369290steps）；登记明确这是训练结束后的最新checkpoint选择，非新的前瞻收敛窗口或未见测试。

`{O}/PLAN.json` SHA `{sha(O/'PLAN.json')}` 在任何新33恢复/物理前固定，沿用冻结29全部30条件/顺序、独立动作seed2026102626、independent noise、30×55秒、最多41250动作/33000000子步，0优化/0replay写入。两个交错15条件分片；CPU0推理、CPU1/2物理、CPU3审查、GPU0。先查CPU0–3无其他固定Python任务，原参数78仍CPU13–51/GPU1–3，guard52–54保持。单训练seed和单动作seed/训练条件结果，不替代指定ESN、最终完整比较或held-out泛化。

## 源码与准确恢复

独立runtime `{RT}`。原冻结29全部703文件逐字复制并核hash，与当前33恢复依赖逐hash一致；新增evaluator只把允许的物理周期29改33，完整物理loop和外部随机动作函数保持原字节/AST。root reviewer改33元数据、完整26..33历史和CPU3，并显式检查总动作≤41250；原物理/filter/torque三审计不变。错误周期29请求在创建输出/读checkpoint前拒绝，0物理。

真实check-only原PID2567326已完成，完整learner/optimizer/RNG、2m replay及历史摘要精确，原930隔离行及raw/derived字段全部保留、不能采样、不补造完整25。同外部seed动作一致、不同seed动作不同、时间采样规则通过，状态未改变。完整33恢复digest：learner ff4b521adea259a4d3bf248c89e846d1612ceb5ceffd42e3895c6afcb0100b57；replay e74ccbea8fb92d2f79c6c1d06d9669727b1cee29a8813689084f154ccc19c4f7；history2436e4bd667690fef00bd3c43fcedd4eef0a09764b51f66ffd597ab6dc62dfa3。

通过独立PRELAUNCH后，两原evaluator PID2686848/2686852启动，root reviewer2686856；全部启动身份记录在LAUNCH/REVIEW_LAUNCH。实际两分片FULL_STATE_RESTORE与check-only逐字段完全一致，外部RNG gate、checkpoint/登记/模型/公共动作桥和CPU亲和核验通过。**该启动检查不冒充完整30回合的物理/最终状态不变审查。**

初始只读观察器错误地将`executed_evaluator.py.txt`函数hash与audit入口模块hash比较而失败。原源码/log/FAILURE保留，改为对照ADAPTER的函数hash和冻结29同条件执行函数，并单独核入口模块hash，两边均通过。`OBSERVER_FIX_REVIEW.json`与diff记录证据；没有修改科学源码或重启科学进程。修正后的观察器连续5样本/{obs['elapsed']:.3f}秒，{obs['identities']}个原身份全部保持，参数步号{obs['first_parameter_steps']}→{obs['last_parameter_steps']}；观察器自然结束，评测/训练继续。

## 完整评测后续

原root reviewer等待两分片最终POLICY_UNCHANGED，再对全部30逐原始子步、滤波和力矩记录核验，校验原learner/optimizer/RNG/replay/history未变、MJB/种子/预算及全部失败分母。固定21600秒观察上限；超时不是科学终止，不自动重启。

`COMPARISON_PLAN.json`在完整33评测前登记29→33描述性配对，保留全部30条件Task/Strict、完整时长、机器违规、各关节峰矩、实际人体接触时长与舒适时长/接触分母、完成时刻/阶段/abort；无接触为NA。比较等待器PID2754155，须完整33审查通过后运行，只读保存JSON/CSV与独立计数/均值/差值核验。不会从这部分比较选最终SPT的Tref，不冒充指定ESN或多独立训练seed比较。

参数78原全loss/标签/2304终端锚点后续、完整归档/health和原前瞻76–78统计均保持；本轮不改变训练LR/reward/masks/physics/gates、batch65536/UTD1/terminal128或4m markers。参数reward稳定与loss健康仍未证明；原Goal完整范围保留。

## GPU与保存

自上次最终保存起guard {len(rows)}个5秒样本，四卡最低{snap['guard']['minimum']}%，低于50次数{snap['guard']['below50']}，最后利用率{[x['utilization'] for x in rows[-1]['gpus']]}%。含合成保载，非纯科研吞吐；保活在科学全部完成后仍继续。历史容器停机与v6预热空闲保留，非重启自启服务。

本轮SSD小证据 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，逐成员及Python AST核验。[收据]({TAG}_SAVE.json)。新入口源码也复制至仓库tools，冻结runtime/hash仍为执行依据；703原依赖manifest与共享SSD原件保留，大checkpoint/raw/回放仍SSD，非HDD或arm1全备份。GitHub发布以最终实际push收据为准；既有HTTPS认证缺失。

下一步观察原冻结33到完整30及审计/配对，查看真实结果后报告；持续原参数78，收齐78完整loss/health/终端/labels及76–78统计再作科学判断。不要重复启动33冻结，不追加Direct34，不因观察过期重启科学。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-29 — 最新Direct33冻结验证实际启动

- [交接](docs/{TAG}.md)。原Direct33数值阶段/不启动34保持；新全30冻结验证固定最新33、原29条件和动作seed2026102626/41250动作/3300万子步，明确训练后选最新checkpoint。703原依赖/物理loop/动作函数保持，真实33全state/replay/930隔离/RNG恢复和两分片实际启动核验通过；当前{complete}/30，完整审查未完。
- 两evaluator2686848/2686852、rootreview2686856及只读29→33配对等待2754155；CPU0–3/GPU0，原参数78steps{steps}与全审/76–78继续。观察器哈希对象误配失败保留并修正，无科学重启；5样本/{obs['elapsed']:.3f}秒{obs['identities']}原身份保持。Goal active、指定ESN/最终比较未完成。
- guard{len(rows)}样本min{snap['guard']['minimum']}%、低于50{snap['guard']['below50']}，科研完成仍保载、合成非吞吐。SSD{receipt['members']}成员/{receipt['bytes']}字节/SHA{receipt['sha256'][:8]}逐成员/AST核验，非HDD/arm1全备份；mainb1deda65/baselinef6e8f8c已读，发布待实际收据，无子agent。

'''
for n in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/n;s=p.read_text()
 if n=='AGENTS.md':h,t=s.split('\n',1);p.write_text(h+'\n\n'+entry+t.lstrip('\n'))
 else:p.write_text(entry+s)
p=R/'HANDOFF.md';p.write_text(f'> **RL最新：[最新Direct33冻结验证实际启动](docs/{TAG}.md)。原参数78及完整审查/GPU保活继续；完整冻结33尚未完成，勿重复启动。**\n\n'+p.read_text())
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(p.read_text()+f'\n\n更新：[最新Direct33冻结验证实际启动]({TAG}.md)。原78训练和GPU保活继续，最新33冻结验证运行中。\n')
print(json.dumps(receipt));print(json.dumps(dict(parameter_steps=steps,frozen_completed=complete,guard=snap['guard'],observation=obs)))
