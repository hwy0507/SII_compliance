from pathlib import Path
import json,hashlib,time,tarfile,ast,socket
D=Path(__file__).resolve().parent;B=D.parents[1];REPO=B/'repository/SII_compliance';C=B/'runtime/census99_prefix_comparison_20261031_v1';T=B/'runtime/census99_terminal_20261031_v1';F=B/'runs/census99_fixed98_terminal_20261031_v1';ND=B/'runtime/census99_new_terminal_diagnosis_20261031_v1';N=B/'runs/census99_new_terminal_diagnosis_20261031_v1';P=B/'runtime/census99_window_completion_preparation_20261031_v1';R=B/'runs/parameter_census_cycle99_20261031_v1';TAG='RL_CENSUS99_DIAGNOSTICS_20261031';E=REPO/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,r):
 with p.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
obs=read(D/'ONLINE_OBSERVATION_REVIEW.json');assert obs['passed']
for j in obs['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
for p in [F/'PREFLIGHT_REVIEW.json',F/'PARTIAL_REJECTION_REVIEW.json',C/'PREFIX_SAVED_REVIEW.json',C/'PRIOR90_REVIEW.json',C/'CAPACITY_COMPARISON_REVIEW.json',C/'CACHE_POPULATION_PREFIX_REVIEW.json',C/'CACHE_POPULATION_NEGATIVE_REVIEW.json',C/'COMPARISON_PREFLIGHT.json',C/'SOURCE_ORDER_REVIEW.json',N/'REPORT_CONTRACT_REVIEW.json',N/'PREFLIGHT_REVIEW.json']:assert read(p)['passed']
assert not (N/'FINISHED.json').exists() and not (B/'runs/parameter_census_cycle99_review_20261031_v1/FINISHED.json').exists();W=B/'runs/parameter_census97_99_reward_stability_20261031_v1';assert not (W/'REGISTRATION.json').exists()
G=Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1');assert not (G/'STOP').exists();samples=[json.loads(x) for x in (G/'samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(F/'PLAN.json')['time']];assert samples and time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(r['gpus'][i]['utilization'] for r in samples) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples));steps={m:read(R/m/'train/PROGRESS.json')['steps'] for m in obs['first_steps']};put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),steps=steps,gpu=gpu,goal='active',original99_jobs_and_three_consumers_live=True,no_full99_result=True,guard_kept_after_science=True))
files=set()
for root in [D,C,T,F,ND,N,P]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.jsonl','.png','.npz','.diff','.log'}:files.add(p)
for p in [R/'LAUNCH.json',R/'MONITOR_LAUNCH.json',B/'runtime/census99_continuation_20261031_v1/SOURCES.json',B/'runtime/census98_completion_20261031_v1/WINDOW97_99_NECESSARY_CONDITION_98.json',B/'runtime/census99_window_inputs_recovery_20261031_v1/COMPLETE98_BINDING_REVIEW.json',B/'runtime/census99_window_inputs_recovery_20261031_v1/COMPLETE98_INPUT_MAP.json',W/'PLAN.json',W/'SOURCE_LOCK.json',B/'runtime/direct34_dispatch_preparation_20261028_v1/DIRECT_STAGE_DECISION.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2,(p,len(data));rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Actual99 fixedfirst5000 original loss and diagnostics registration/preflight/live evidence. No full99 result, no window statistics. Depends on full98/actual99 startup publication ba3dfba4 and sharedSSD large assets.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for member in z.getmembers():assert z.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='ba3dfba40c504732f7b82102cb189fb9760f18d8',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD evidence; existing254-byte HDD pointer only, not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
prefix=read(C/'PREFIX_SAVED_REVIEW.json')['methods'];table=['|方法|原loss均值|首1000 / 末1000|最大|','|---|---:|---:|---:|']
for m,x in prefix.items():
 l=x['original_loss'];table.append(f"|{m}|{l['mean']:.9f}|{l['first1000']:.9f} / {l['last1000']:.9f}|{l['maximum']:.9f}|")
report=f'''# 第99轮前缀已审，完整比较与新旧终端诊断等待 — 2026-10-31

**Goal active。原99三路训练与archive继续，完整99、原97–99最终统计、loss健康/收敛与最终指定ESN公平评测仍未完成。** 本轮没有重启训练或启动100；新增三个只读消费者，沿原99归档截止，不增加物理或正式更新。

固定前5000在查看99 loss值前登记，全部原始JSONL字节、11种保存NPZ指标、独立标量和九栏实际图通过：

{chr(10).join(table)}

I短暂起伏后约1.1、actor缓慢下降；A约1.02且actor大致平稳；V约.744和actor大致平稳。原loss与条件loss分别保存，所有峰值保留。前缀无新终端，2,935/2,934/2,934总人口与逐更新done累计精确；15损坏计数拒绝。该前缀不能证明全99健康或回报稳定。

完整98→99全90条件比较已登记，实际完整98模型/rollout标签/reward分项算术核验通过。原600万容量stage entry96/first97及全部科学字段保持，18损坏协议拒绝；已核源码add/cache同步先于同step更新/日志。比较等待器`{C}/PROCESS.json`等待原核心完整99，再分析全部90条件及最终回放/32分层；线上逐分层tensor未记录。

固定全部8803完整98终端的CPU比较已登记`{F}`，保留原五critic/mask/块边界与全部历史失败、新98最大残差及V short0600 mask0大残差。原参考保存算术和实际partial99拒绝完整检查通过；唯一等待器`{F}/PROCESS.json`在原99 core完成后运行，不训练。

新终端诊断`{N}`等待core/固定8803/全90与population结果，再构建8893参考并逐条诊断90新99终端；旧8803预测须逐值复现、全learner/Adam/replay/RNG不变。实际98报告schema正例和27损坏输入拒绝通过，原97 binder失败修复证据保持。short0600配对、原loss最大点时序、原mask和全部失败保留；无抽样索引不得作因果解释。未来图明确标注original masked SSE，未mask残差另存。**当前尚无完整99推理/诊断结果。**

原97–99最终输入/独立bootstrap脚本仅准备于`{P}`，未执行：继承已核的97/98六组，须实际完整99科学审查及两核心图后添加三组，再调用原锁定九组binder/audit/review与独立标量区间复算；5%/nearzero1/5000/seed2026102861保持，原95%区间字段及.025/.975分位数未误改。97→98三路必要条件42.9154%/24.5166%/59.4027%失败及原94–96失败保持，不移窗口到98–100。

102身份连续{obs['elapsed_s']:.3f}s/{obs['samples']}样本保持，步数增长{ {m:obs['last_steps'][m]-obs['first_steps'][m] for m in obs['first_steps']} }；保存总steps{steps}。GPU{gpu['samples']}样本/{gpu['seconds']:.3f}s，min{gpu['minimum']}%、低于50{gpu['below50']}，末{gpu['last']}%。包含独立保活负载，不是科研吞吐或瞬时保证；科学全部结束仍保留guard`{G}`，勿创建STOP，非重启自启服务。

主机`{socket.gethostname()}`；共享SSD根`{B}`；Python`{B}/env/bin/python`；正式99`{R}`。恢复先核原LAUNCH身份和最新进度，不重启99或回退完整98。原Direct33数值验收保留，冻结30 Task/Strict0/0不追加34；原28最终memory缺口/恢复2已证、指定ESN缺失与最终完整集合SPT/公平冻结比较仍待。

mainba3dfba4/baselinef6e8f8c2实际query/fetch/read，发布见`{A}/PUBLICATION.json`。小证据包`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256`{receipt['sha256']}`，逐成员核验。依赖上一轮完整98/99启动证据和原共享SSD大checkpoint/replay/raw；HDD配额满，仅既有254-byte LATEST指针更新，非HDD/arm1全备份。
'''
(REPO/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 第99轮前5000已审，三个完整只读消费者等待

- [交接](docs/{TAG}.md)。固定first5000原日志/11metrics/保存算术/实际图通过，原loss均值1.1000/1.023411/.744277、最大2.064256/1.450504/1.142057；无新终端，非全99健康或收敛。
- 全8803旧终端比较/全90条件与population/8893参考及90新终端诊断均已独立登记等待，原archive截止不变；实际partial99拒绝、完整98算术/schema正例及27损坏报告、18科学协议/15计数负例通过。原五critic/mask/块边界/全部state不变与历史失败要求保持，零额外训练。
- 原97–99最终九组绑定与bootstrap仅静态准备，原六组继承，完整99和图审查仍待；97→98必要条件三路失败、原94–96失败不移窗口。Direct33原验收/冻结0/0、历史缺口、指定ESN与最终比较仍待，Goal active，无100派发。
- 原102身份连续{obs['elapsed_s']:.3f}s保持，steps增长{ {m:obs['last_steps'][m]-obs['first_steps'][m] for m in obs['first_steps']} }；GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。mainba3dfba4/baselinef6e8f8c2已query/fetch/read。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();size=pointer.stat().st_size;assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data);print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps),indent=2))
