from pathlib import Path
import json,hashlib,time,socket,tarfile,ast
D=Path(__file__).resolve().parent;B=D.parents[1];T=B/'runtime/census100_prefix_terminal_probe_20261031_v1';N=B/'runs/census100_prefix_terminal_probe_20261031_v1';R=B/'runs/parameter_census_cycle100_20261031_v1';REPO=B/'repository/SII_compliance';TAG='RL_CENSUS100_PREFIX_DIAGNOSIS_20261031';E=REPO/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(p.read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
prefix=read(D/'prefix5000/REVIEW.json');probe=read(N/'REVIEW.json');assert prefix['passed'] and probe['passed'] and read(N/'FINISHED.json')['passed'] and read(N/'REGRESSION_REVIEW.json')['passed']
for p in [D/'PREFIX_SAVED_REVIEW.json',D/'PRIOR90_REVIEW.json',D/'CAPACITY_COMPARISON_REVIEW.json',D/'CACHE_POPULATION_NEGATIVE_REVIEW.json',D/'CACHE_POPULATION_PREFIX_REVIEW.json',D/'SOURCE_ORDER_REVIEW.json',D/'COMPARISON_PREFLIGHT.json']:assert read(p)['passed']
for p in [D/'PLOT_INSPECTION.json',N/'PLOT_INSPECTION.json']:assert read(p)['actual_visual_inspection']
start=read(D/'LIVE_START.json')
for j in start['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
steps={m:read(R/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']};growth={m:steps[m]-start['steps'][m] for m in steps};assert all(v>0 for v in growth.values());assert not list(R.rglob('*FAILURE*'))
G=Path('/tmp/sii_gpu_util_guard_20261031_recovery_v1');assert not (G/'STOP').exists() and not (G/'FAILURE.json').exists();samples=[json.loads(x) for x in (G/'samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(D/'SOURCE_ADAPTATION_REVIEW.json')['time']];assert time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples));put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),gpu=gpu,steps=steps,growth=growth,identity_count=len(start['identities']),endpoint_identity_check_elapsed_s=time.time()-start['time'],goal='active',complete100=False,automatic101=False,guard_after_science=True))
files=set()
for root in [D,T,N]:
 for p in root.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.jsonl','.npz','.png','.diff'}:files.add(p)
# Preserve parent scientific decision and observation intent as references, not duplicate checkpoints.
for p in [B/'runtime/census100_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',B/'runtime/census100_continuation_20261031_v1/SCIENTIFIC_DECISION.json',B/'runs/census100_fixed99_terminal_20261031_v1/PLAN.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2,(p,len(data))
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data);manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed first5000 source logs/all metrics/scalars/actual plot; full99-to100 comparison and population waiter; exploratory actual partial100 snapshots all8893 fixed99 terminals/read-only invariant checks/actual plot. Snapshots and original large replay/raw stay sharedSSD, not Git.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for x in z.getmembers():assert z.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main=start['main'],baseline=start['baseline'],backup_scope='SharedSSD evidence and existing254-byte HDD pointer; big snapshots/replay/raw remain sharedSSD, not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
table=['|方法|前5000原loss均值 / 最大|快照新增步|固定旧终端SSE变化|改善 / 退化行|','|---|---:|---:|---:|---:|']
for m in steps:
 s=prefix['methods'][m]['stats']['agent_train/original_sampled_q_loss'];x=probe['methods'][m];table.append(f"|{m}|{s['mean']:.6f} / {s['maximum']:.6f}|{x['new_steps']}|{x['masked_sse_change_percent']:+.4f}%|{x['improvements']} / {x['regressions']}|")
i=probe['methods']['impedance']['known_rows'][-1]
report=f'''# 第100轮固定前缀与旧失败拟合诊断 — 2026-10-31

Goal active，未收敛。原第100轮三训练/90sampler/归档/固定8893终端消费者继续；本轮新增唯一全90条件与终端计数只读消费者，等待原100完整归档。无101派发。

{chr(10).join(table)}

固定前5000原日志/全部11种metrics保存数组/独立标量复核通过，九栏实际图已看。I原loss反复约19–21尖峰，原loss首1000均值1.449878、末1000为1.348768，actor向下漂移；conditional更平滑不能替代原健康指标。A/V本段较平缓但actor变化保留，有限值不是loss健康或收敛。此处沿用历史同一first5000规则，但先前513/507/495预览已知，且登记时数据已产生，不声称生成前预登记。首次独立保存审查因尚缺实际看图收据拒绝，失败记录保留；看图写入收据后原程序通过。

当前partial100只读probe每方法取一次当时最新原子checkpoint，三个实际步数不同，明确为观察前5000尖峰后的探索性诊断。全部8893旧99终端/原mask/五critic/原预测块边界与实际replay绑定；保存数组/独立scalar SSE以及完整learner/Adam/replay/RNG不变通过，零优化器更新/物理交互，不推广权重。所有退化行保留，不能作为完整100或未见泛化结果。

I第99轮long0000穿透失败原reward{i['reward']:.9f}，五critic从{i['complete99_prediction']}变为{i['prefix100_prediction']}；该原mask全1样本SSE由{i['complete99_masked_sse']:.6f}降至{i['prefix100_masked_sse']:.6f}，仍很大。原全局穿透与外部穿透不同、原violation bit0保持；无训练抽样索引，不将其与原loss尖峰作因果绑定。其余方法/样本改善和退化均见probe原报告，不能只报总均值。

独立逐行标量审查全部8893行并保留各方法20个最大退化。I旧92 long0000原mask仅critic4为1，masked SSE9.467058→32.429589；新99失败改善同时旧失败退化。V旧11 short0600 masked SSE.224989→6.377385，原critic3 mask0保持，其预测−17.8339→−5.6605、target−28.4238只列未mask误差，不混入masked健康损失。A最大退化为旧16 short0000，.136660→.968864。不能据同条件或时间关联声称因果。

完整99→100全90条件/Task/Strict/奖励项/失败与实际终端计数对照已登记。实际完整99全部90原模型/rollout标签/奖励分解通过；18科学契约损坏与15终端计数损坏拒绝，真实partial/缺完整100不被当作完整。前5000每步终端计数核验I2965/A2964/V2964、均无新增terminal；线上逐分层tensor未日志记录，不声称观察到。本轮consumer沿原archive截止，仅等待，不重启或复制训练。

原97–99三路5%稳定失败、新100–102非重叠前瞻意向、原统计阈值及loss口径保持。Direct33原数值验收/冻结30 Task与Strict0/0、原28memory缺口/恢复2已证保持，不追加34；指定ESN、最终公平冻结比较及共同集合Tref/SPT仍待。

运行首尾{len(start['identities'])}身份一致，间隔{time.time()-start['time']:.3f}s、steps增长{growth}，保存步数{steps}；不是连续逐样本身份观察。GPU{gpu['samples']}样本/{gpu['seconds']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末{gpu['last']}%；含保活负载，非科研吞吐或瞬时保证。科学结束仍保留`{G}`，勿创建STOP，非开机自启。

主机`{socket.gethostname()}`；解释器`{B}/env/bin/python`，正式`{R}`，本轮全90/前缀证据`{D}`，独立probe`{N}`。其三大snapshot.pt仍共享SSD，hash/实际步数见各方法REVIEW，不是完整cycle checkpoint。后续优先收完整100/new90终端与全loss/context/实际图，原终端与全90等待器勿重复派发。

小证据`{archive}`，{receipt['members']}成员/{receipt['bytes']}bytes，SHA256`{receipt['sha256']}`，逐成员回读通过。HDD配额满，仅254-byte LATEST指针；非完整HDD/arm1备份。开工main9de58411/baselinef6e8f8c2已实际query/fetch/read，发布见`{A}/PUBLICATION.json`。
'''
(REPO/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 第100轮first5000与旧终端快照诊断：I尖峰仍在，失败拟合缓慢改善

- [交接](docs/{TAG}.md)。前5000全部11metrics原日志/数组/标量/实际九栏图通过；原loss均值I1.450083/A1.027932/V.769687，最大21.345860/1.516276/1.247959。I反复尖峰与actor漂移保留，非收敛。
- partial100三实际快照全部8893旧99终端原mask/五critic/块边界与fullstate不变/保存算术通过；I新99穿透中止样本SSE{i['complete99_masked_sse']:.3f}→{i['prefix100_masked_sse']:.3f}，仍巨大，无抽样索引不作因果。各方法不同快照步数仅探索诊断，改善和退化全保留。
- 全90对照/实际终端计数消费者已登记等待完整100；完整99原90标签/模型/reward通过，18科学协议及15计数损坏拒绝；前5000无新terminal。原97–99失败/新100–102/Direct33结论/指定ESN待保持，Goal active，无101。
- 原{len(start['identities'])}身份首尾一致、steps增长{growth}；GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针；开工main9de58411/baselinef6e8f8c2已核。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();add=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+add+rest.lstrip('\n'))
 else:p.write_text(add+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');size=pointer.stat().st_size;data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data);print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps),indent=2))
