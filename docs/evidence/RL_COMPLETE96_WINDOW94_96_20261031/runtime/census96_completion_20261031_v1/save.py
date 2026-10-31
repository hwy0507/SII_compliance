from pathlib import Path
import json,hashlib,time,socket,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
RUN=B/'runs/parameter_census_cycle96_20261031_v1';V=B/'runs/parameter_census_cycle96_review_20261031_v1';T=B/'runs/census96_fixed95_terminal_20261031_v1';C=B/'runtime/census96_comparison_20261031_v1';W=B/'runs/parameter_census94_96_reward_stability_20261031_v1';O=B/'runs/census96_completion_wait_20261031_v1'
TAG='RL_COMPLETE96_WINDOW94_96_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
scientific=read(D/'COMPLETE96_SCIENTIFIC_REVIEW.json');methods=scientific['methods'];assert scientific['passed']
window=read(W/'REVIEW.json');assert window['passed'] and read(W/'SAVED_ARITHMETIC_REVIEW.json')['passed'] and read(D/'WINDOW_BOOTSTRAP_SCALAR_REVIEW.json')['passed']
assert read(W/'BINDING_REVIEW.json')['all_nine_actual_checkpoints_checked'] and read(W/'PLOT_INSPECTION.json')['actual_visual_inspection']
assert read(O/'COMPLETION_REVIEW.json')['all_complete'];assert read(V/'FINISHED.json')['completed'] and read(T/'FINISHED.json')['passed'] and read(C/'COMPARISON_FINISHED.json')['passed']
for x in read(W/'PLOT_INSPECTION.json')['plots']:assert x['inspected'] and sha(Path(x['path']))==x['sha256']
for p in scientific['inputs']:assert sha(Path(p['path']))==p['sha256']
guard=read(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(guard['root']);assert not (G/'STOP').exists()
for j in guard['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
started=read(O/'PREFIX_HEALTH.json')['time'];rows=[json.loads(x) for x in (G/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=started];assert rows and time.time()-rows[-1]['time']<20
gpu=dict(samples=len(rows),minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,training96_and_consumers_completed=True,goal='active',cycle97_launched=False))
files=set()
for root,suffixes,recursive in [(D,{'.py','.json','.jsonl','.diff'},True),(O,{'.json','.jsonl'},False),(B/'runtime/census96_completion_wait_20261031_v1',{'.py'},False),(V,{'.json','.npz','.png'},True),(T,{'.json','.npz','.png'},False),(W,{'.py','.json','.png','.npz'},False)]:
 files.update(p for p in (root.rglob('*') if recursive else root.iterdir()) if p.is_file() and p.suffix in suffixes)
for n in ['COMPARISON_FINISHED.json','COMPARISON_PLAN.json','INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','CHANGED_CASES_REVIEW.json','CACHE_POPULATION_FULL_REVIEW.json','PLOT_INSPECTION.json','training95_96_all90.png','interpret96.py','changed_cases.py','check_terminal_population.py']:files.add(C/n)
for root,names in [(B/'runtime/census96_prefix_20261031_v1',['terminal96.py','wait_terminal96.py']),(B/'runtime/census96_continuation_20261031_v1',['driver.py','census_native.py','health96.py','loss96.py','SCIENTIFIC_DECISION.json','SOURCES.json']),(B/'runtime/census96_consumer_repair_20261031_v1',['review_repaired.py','archive_repaired.py','REPAIR_PLAN.json','FAILURE_REVIEW.json'])]:
 for n in names:files.add(root/n)
files.update(RUN.glob('*.json'))
for m in methods:
 for root in [RUN/m,RUN/m/'train']:files.update(root.glob('*.json'))
 files.add(RUN/m/'train/episodes.jsonl');files.update((RUN/m/'train/cycle_00096').glob('*/rollout.json'))
 files.add(B/f'runs/parameter_census_cycle96_archive_20261031_v1/{m}/cycle_00096.json')
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS_CAPACITY6M_GPU_20261031'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Full96 scientific checks, all123750 saved metrics, all90 comparison and regressions, all8533 fixed95 terminals, complete94-96 original window binding/statistics/independent arithmetic/actual plots; original failures retained. Large checkpoints/raw stay sharedSSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for e in t.getmembers():assert t.extractfile(e).read()==(E/e.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main='f529b4ff0a436a94375e090fef4c642958af5d79',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='SharedSSD small evidence; HDD254-byte pointer only; large96 checkpoints/raw stay SSD,not full backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/f'{TAG}_SAVE.json',receipt)
training=['|方法|完整96步数|Task/Strict（各30）|reward均值|原loss均值|原loss最大|','|---|---:|---:|---:|---:|---:|']
table=['|方法|94/95/96 reward均值|相邻相对变化|94→96相对变化|原5%描述性检查|','|---|---|---|---:|---|']
for m,r in methods.items():
 tr=r['training'];q=r['loss']['agent_train/original_sampled_q_loss'];training.append(f"|{m}|{tr['steps']}|{tr['task']}/{tr['strict']}|{tr['reward_mean']:.9f}|{q['mean']:.6f}|{q['maximum']:.6f}|")
 x=window['methods'][m];table.append(f"|{m}|"+'/'.join(f"{a['reward_mean']:.6f}" for a in x['cycles'])+'|'+ '/'.join(f'{a*100:.4f}%' for a in x['adjacent_relative_mean_changes'])+f"|{x['endpoint_relative_mean_change']*100:.4f}%|{x['descriptive_five_percent_check']}|")
entry=f'''## 2026-10-31 — 完整96及原94–96窗口已审；A/V稳定失败，V末段原loss尖峰保留

- [交接](docs/{TAG}.md)。三路各41250新增/30完整55秒/0中止，旧回放及新52/action/reward精确；Task/Strict18/17、16/16、17/16。全部123750更新原日志/保存数组/标量与实际图通过，原loss均值.94550/1.06071/.73557、最大1.87303/1.60079/8.75540；V末段尖峰与actor漂移保持，未收敛。
- 全8533固定95终端/all5/原mask通过：masked SSE变化−29.633%/−.428%/+3.865%，1300/1563/1225样本退化保留。90真实新terminal、总8623，完整日志/replay/32分层核验；非在线逐层tensor观察或独立泛化。A获long0500/0900、失short0600；V失short0600 Strict。
- 原94–96九组真实checkpoint/父链/原loss/实际图绑定，原5%/nearzero1/5000bootstrap/seed2026102861及独立标量/区间复核通过；描述性reward检查I通过、A/V失败，不是联合收敛。首次过早调用binder与相对root命令失败原件保留，后续成功，统计源码/窗口未变。
- 原96三训练/archive/两消费者正常结束勿重启，下一步准确全96父、6m接入与有限97准备前核新终端/short0600退化，尚未派发97。Direct原数值/冻结0/0、旧28缺口/恢复2已证及指定ESN缺失保持，Goal active。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}；科学结束仍guard，SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。

'''
report=f'''# 完整96与原94–96固定窗口审查

原第96轮三路训练、归档与两个比较消费者全部正常结束。**尚未收敛，Goal active**。上一轮实质完成6m GPU兼容性；本轮完成完整96、真实终端增长、原固定窗口统计及实际图审查，没有重复训练或改动原科学设置。

## 完整训练与loss

{chr(10).join(training)}

每方法30个完整55秒回合/41250新transition，无中止。旧回放所有字段、历史/违规特征保留，新current/next52、raw/mixed action和原reward journal重建精确，reward最大误差0。原网络/Adam有限，完整checkpoint严格恢复；physics/MJB/Task/Strict/canonical48/actor49/critic52/filter/执行器限制/dt5e-5、reward/LR/masks/terminal128/batch65536/UTD1和4m历史23/47容量保持。该reward核验是原journal算术，不是全部原始物理子步重演。

全部123750 optimizer行与保存NPZ所有字段逐值核对，首末1000/均值/极值用math.fsum独立复算，最大20原loss记录保留。实际查看九栏loss和六栏health。I原loss均值约.945，actor上升后趋缓；A中段loss上升后回落、actor仍变；V均值约.736但末段原loss出现8.7554尖峰。具体step3975483对应条件loss.961916、terminal_population2863、sampled_terminal_rows44；原loss3.235736还出现在3975532。不能以条件估计更平滑代替原健康口径，也不能从日志推断某一被抽样transition造成峰值（未保存抽样索引）。V actor上移且末段alpha下降，entropy近目标但有波动。health4096 TD为未投影fixed-min-pair诊断，不等于真实投影/I-min/A-V-mean目标。

## 真实终端与全部条件比较

活跃前缀逐步绑定真实done累计及完成55秒回合，首次检查新增I20/A21/V20终端，真实增长少记一条会被拒。前缀字节hash再与最终日志核对；完整三路每次更新population、全部回放done、新30终端/方法、原8533 indices/masks及存档32分层均通过。最终各2875/2874/2874，总8623。在线逐分层tensor没有日志，不声称已逐值观察。

95→96全90条件模型/reward分项/Task/Strict/abort与变化rollout核验。I标签不变且平均reward+0.003167；A平均+1.686877，long0500和long0900获Task/Strict但short0600失去两者；V平均−1.742864，short0600保持Task但失去Strict。成功总数不能掩盖这些变化，完整原失败都保留。

固定全部8533旧95终端，在准确96 checkpoint下零更新/零physics，完整learner/Adam/replay/RNG不变，保存SSE标量与实际九栏图通过。原mask总SSE相对变化I−29.6328%、A−.4278%、V+3.8651%；逐样本退化1300/1563/1225。I部分critic退化，A masked critic2/3及all-row critic2/4退化，V masked critic1/3退化，虽然V每个critic的all-row SSE下降。原历史79/90/92中止及93放置失败残差仍包含；这是已见历史拟合，不是新96终端评估、独立泛化或全方法改进。

## 原94–96窗口

{chr(10).join(table)}

原窗口/5%/nearzero1/5000 bootstrap/seed2026102861保持；意向登记在94启动后首个完整回合之前，不改写为启动前。完整九组输入含原协议/全部30episode/全部更新/原loss/真实两图/checkpoint，实际读取九份checkpoint并核验连续父链。原绑定器、audit.py和review_saved.py未改，所有源锁保持。原始270回合标量及bootstrap区间用独立math.fsum与排序线性分位数再次核验；区间衡量条件组成敏感性，不是独立训练seed。实际查看reward_stability.png。I仅通过描述性reward稳定检查；A/V失败，有限loss及5%均不能独自建立健康收敛。原90–92和所有后续失败继续保留。

本轮两个操作错误有原件：输入map哈希检查尚未退出时过早调用binder，缺文件退出；等待map成功后原binder通过。统计第一次以相对--root启动，原binding_source绝对路径一致性检查拒绝；随后使用绝对--root运行同一源码成功，原FAILURE.json及WINDOW_RELATIVE_ROOT_FAILURE.json保留。没有改变数据、阈值或统计kernel。

## 下一步及恢复

下一步先核查新96终端残差和short0600退化，再依据准确全96父状态登记有限97：6m容量候选已完成真实全95 CPU/GPU兼容性及边界测试，尚未正式接入；仍需全96 learner/Adam/RNG/replay恢复、三容量marker贯穿协议/checkpoint/startup/fullreview，原生更新及实际跨4m保留检查。4m已不足完整97，禁止覆盖旧数据。97尚未派发，不自动98/Direct34；后续统计须单独前瞻登记，不能替换本次失败窗口。

Direct33原数值验收/冻结30条件Task/Strict0/0、旧28完整memory不变性缺口及恢复2已证保持。指定ESN仍缺，最终独立评测/公平对照和联合收敛未完成。恢复以已核验完整96为父，不能回退95；MuJoCo物理state未保存。原96完成进程勿重启，guard在科学结束后仍继续。

## 来源与保存

主机 `{socket.gethostname()}`，共享SSD `{B}`，Python `{B}/env/bin/python`。按sii-research-sync实际query/fetch/read main f529b4ff/baseline f6e8f8c2，无子agent。训练 `{RUN}`；完整归档 `{B}/runs/parameter_census_cycle96_archive_20261031_v1`；科学汇总 `{D}`；原固定窗口 `{W}`。各checkpoint SHA：

'''+''.join(f"- {m}: `{r['training']['checkpoint_sha256']}`\n" for m,r in methods.items())+f'''
GPU保存窗口{gpu['samples']}样本最低{gpu['minimum']}%、低于50次数{gpu['below50']}，末值{gpu['last']}；含synthetic guard，不等于正式吞吐或每瞬时保证。5个guard身份仍在，非系统重启服务。

小证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员字节/JSON/AST核验。包含原loss数组、终端数组、五张实际图、全90摘要、原固定统计及失败原件。大型checkpoint/replay/raw仍仅共享SSD，HDD仅254字节LATEST指针，非HDD/arm1完整备份。实际发布收据 `{A}/PUBLICATION.json`。
'''
(R/'docs'/f'{TAG}.md').write_text(report)
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=R/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/f'{TAG}.md')+'\nGoal active; SSD assets.\n').encode();size=pointer.stat().st_size;assert len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(passed=True,receipt=receipt,gpu=gpu)))
