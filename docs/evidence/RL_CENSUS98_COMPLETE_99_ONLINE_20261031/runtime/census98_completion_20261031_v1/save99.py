"""Publish verified complete98 and actual finite99 startup; never infer completion from preparation."""
from pathlib import Path
import json,hashlib,time,tarfile,ast,socket
D=Path(__file__).resolve().parent;B=D.parents[1];REPO=B/'repository/SII_compliance';S=B/'runtime/census99_continuation_20261031_v1';RUN=B/'runs/parameter_census_cycle99_20261031_v1';V=B/'runs/parameter_census_cycle98_review_20261031_v1';T=B/'runs/census98_fixed97_terminal_20261031_v1';N=B/'runs/census98_new_terminal_diagnosis_20261031_v1';C=B/'runtime/census98_prefix_comparison_20261031_v1';W=B/'runtime/census98_completion_watch_20261031_v1';WIN=B/'runtime/census99_window_inputs_recovery_20261031_v1';TAG='RL_CENSUS98_COMPLETE_99_ONLINE_20261031';E=REPO/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
full=read(D/'COMPLETE98_SCIENTIFIC_REVIEW.json');assert full['passed'];assert read(D/'COMPLETION_REVIEW.json')['all_complete'];assert read(WIN/'COMPLETE98_BINDING_REVIEW.json')['passed']
obs=read(S/'ONLINE_OBSERVATION_REVIEW.json');assert obs['passed'];start=read(RUN/'startup/REVIEW.json');assert start['passed'];assert read(S/'PREFLIGHT_FINISHED.json')['passed']
for j in obs['identities']:
 st=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert st[0]!='Z' and st[19]==j['start']
G=Path(read(W/'PLAN.json')['guard']['root']);assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists()
samples=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];samples=[r for r in samples if r['time']>=read(W/'PLAN.json')['time']];assert samples and time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(r['gpus'][i]['utilization'] for r in samples) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in samples) for i in range(4)],last=[r['utilization'] for r in samples[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in samples))
progress={m:read(RUN/m/'train/PROGRESS.json') for m in full['methods']};put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),goal='active',complete98=True,finite99_running=True,progress=progress,gpu=gpu,identities=obs['identities'],guard_kept_after_science=True))
files=set()
for root in [D,W,S,V,T,N,B/'runtime/census99_preparation_20261031_v1',B/'runtime/census99_window_inputs_20261031_v1',WIN,B/'runtime/census98_new_terminal_diagnosis_20261031_v1']:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.jsonl','.npz','.png','.diff','.log'}:files.add(p)
for n in ['INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','CHANGED_CASES_REVIEW.json','CACHE_POPULATION_FULL_REVIEW.json','COMPARISON_FINISHED.json','FULL98_PLOT_INSPECTION.json','training97_98_all90.png','WAIT_PLAN.json','PROCESS.json']:files.add(C/n)
files.update(RUN.glob('*.json'));files.update((RUN/'startup').rglob('*.json'))
for m in full['methods']:
 files.update((RUN/m).glob('*.json'));files.update((RUN/m/'check').glob('*.json'))
for p in [B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',B/'runs/parameter_census94_96_reward_stability_20261031_v1/REVIEW.json',B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2,(str(p),len(data));rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,scope='Actual complete98 scientific evidence and separately verified finite99 startup. Original interrupted read-only sessions retained. Large checkpoint/replay/trajectories remain sharedSSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for member in z.getmembers():assert z.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='414db88d09d91f7c9ca34eee38be849031de2bcb',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD small evidence; existing254-byte HDD pointer only. Large checkpoint/replay/raw remainSSD, not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
table=['|方法|完整98步数|Task / Strict（各30）|平均回报|原loss均值 / 最大|','|---|---:|---:|---:|---:|'];details=[]
for m,x in full['methods'].items():
 t=x['training'];l=x['loss']['agent_train/original_sampled_q_loss'];table.append(f"|{m}|{t['steps']}|{t['task']} / {t['strict']}|{t['reward_mean']:.9f}|{l['mean']:.6f} / {l['maximum']:.6f}|");details.append(f"- {m}: 旧终端masked SSE变化{x['fixed97_terminal_groups']['all']['relative_change']:.4%}，退化{x['fixed97_regression_rows']}行；新98终端masked SSE {x['new98_terminal_diagnosis']['total_new98_masked_sse']:.9f}；Task新增{x['task_gained']} / 丢失{x['task_lost']}；Strict新增{x['strict_gained']} / 丢失{x['strict_lost']}。")
report=f'''# 完整98已审，有限99精确接续 — 2026-10-31

**Goal active，尚未收敛，最终指定ESN公平比较未完成。** 原98三路训练、归档和三个只读消费者均已实际完成，不重启；新99已独立登记并通过真实预检与启动检查，只续一轮，每方法最多41250新步，无自动100。GPU guard继续，即使科学工作完成也不停止。

{chr(10).join(table)}

全部三路各41250新步、30完整55秒、零中止；旧replay所有字段与历史marker保持、新reward重建误差0、600万容量继承entry96/first97。所有123750更新原日志/保存数组/独立标量、完整52维next-context连续性及五张实际图通过。I loss首/末1000均值1.017286→1.093342且actor下降；A/V原loss晚段尖峰2.883007/1.799195保留，不能用较平滑条件loss代替健康指标。上述数据正确性通过并非loss健康或收敛通过。

{chr(10).join(details)}

全部8713旧终端保持原mask/五critic/原块边界，新增90及8803全终端参考通过，旧预测逐值复现；learner/Adam/replay/RNG/checkpoint不变。线上总终端计数与最终32分层通过；逐更新32分层tensor未记录。VMC short0600第98轮Strict丢失，外穿透.214752mm超过原.2mm门；critic2原mask0、预测15.207对奖励−28.415、全5 SSE1902.982单列，masked SSE仅.038827。原最大loss在该终端后101更新，但无采样索引，不作因果归因。I/A新终端最大残差为long0000/long0300。

原94–96失败保持。原97–99六组实际输入按锁定逐组规则及完整98父链通过；全九组门正确拒绝缺99。97→98原相邻5%必要条件三路变化42.9154%/24.5166%/59.4027%，均失败；窗口不移到98–100，完整99与最终bootstrap/九组审查仍待。99是单独有限接续以继续学习和补全固定观察，不能使已失败的相邻条件变成通过。Direct33原数值验收及冻结全30 Task/Strict0/0保持，不追加34；原28最终memory证明缺口/恢复2已证、指定ESN尚缺、最终统一SPT与公平冻结比较仍待。

原完成watch与窗口binder工具会话收到SIGTERM/退出143，原因未知，原watch在2876.793秒后无最终收据；原日志/部分map保留。所有原科学作业未重启，最终七个完成标记另行核验。窗口binder在独立recovery目录重做统一只读核验并完成，原失败不覆盖；原watch不冒称成功或全程覆盖。全loss/全context原检查正常完成。

99真实恢复来自完整98 learner/Adam/RNG/所有回放，120损坏契约拒绝、6次原生65536隔离重复更新后恢复、三CPU消费者、原97–99协议及资源/启动门禁均通过。实际启动新数据及current/next52/action/reward/MJB/sampler检查见`{RUN}/startup/REVIEW.json`；原99身份连续{obs['elapsed_s']:.3f}s/{obs['samples']}样本保持，步数增长{ {m:obs['last_steps'][m]-obs['first_steps'][m] for m in obs['first_steps']} }。不加载辅助权重、不改physics/gate/filter/dt，不回退98以前状态。

主机`{socket.gethostname()}`，共享SSD根`{B}`，Python`{B}/env/bin/python`。运行`{RUN}`；启动身份`{RUN}/LAUNCH.json`；runtime`{S}`；完整98审查`{D}/COMPLETE98_SCIENTIFIC_REVIEW.json`。恢复先核最新99进度/身份/checkpoint，不重新启动98或重复99。下一步收全99、原loss/全部条件/终端诊断及原97–99最终统计后单独决定后续。

GPU窗口{gpu['samples']}样本/{gpu['seconds']:.3f}s，min{gpu['minimum']}%、低于50次数{gpu['below50']}，末{gpu['last']}%；含独立合成负载，不是科学吞吐或每瞬时保证。guard`{G}`继续，勿创建STOP；它独立于本对话，但不是重启自启服务。

main414db88d/baselinef6e8f8c2已实际query/fetch/read。证据包`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256`{receipt['sha256']}`，逐成员字节/JSON/AST核验。大文件仍共享SSD，HDD仅既有254字节LATEST指针，非HDD/arm1完整备份。发布核验见`{A}/PUBLICATION.json`。
'''
(REPO/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 完整98全部审查完成，有限99精确恢复上线

- [交接](docs/{TAG}.md)。完整98各41250新步/30完整55秒/零中止；Task/Strict18/17、15/14、17/16。全旧replay/新52/reward、全部loss数组/标量及五实际图通过；原loss均值1.061054/1.029716/.733140，最大2.070614/2.883007/1.799195，I上升与A/V尖峰保留，未收敛。
- 固定8713旧+90新/全部8803终端/state不变与原mask通过，旧masked SSE−16.762%/−3.124%/+9.692%；V short0600 Strict丢失及mask0大残差单列，无抽样索引不作因果归因。97/98六组绑定通过，97→98原5%必要条件三路均失败；原97–99不移窗口、完整99统计待。
- watch与窗口binder会话143中断原件保留，原科学作业均正常完成未重启；独立核验实际七完成标记，窗口recovery完成。99准确全98恢复，120负例/6native隔离更新恢复/三CPU/原窗口/资源/启动通过；{obs['identity_count']}身份连续{obs['elapsed_s']:.3f}s保持，无自动100，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。Direct33原验收/冻结0/0、历史缺口与指定ESN最终比较待保持。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254-byte指针。main414db88d/baselinef6e8f8c2已query/fetch/read。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();size=pointer.stat().st_size;assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(receipt=receipt,gpu=gpu,progress=progress),indent=2))
