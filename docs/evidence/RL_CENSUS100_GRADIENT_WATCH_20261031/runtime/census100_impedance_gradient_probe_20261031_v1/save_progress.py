from pathlib import Path
import ast, hashlib, json, socket, subprocess, tarfile, time

D=Path(__file__).resolve().parent; B=D.parents[1]
O=B/'runs/census100_impedance_gradient_probe_20261031_v1'
W=B/'runtime/census100_remaining_watch_20261031_v1'
R=B/'runs/parameter_census_cycle100_20261031_v1'
REPO=B/'repository/SII_compliance'
TAG='RL_CENSUS100_GRADIENT_WATCH_20261031'
E=REPO/'docs/evidence'/TAG; A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split()
 assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
report=rd(O/'REVIEW.json'); assert report['passed'] and rd(O/'SAVED_REVIEW.json')['passed']
assert not (D/'FAILURE.json').exists() and not (W/'WATCH_FAILURE.json').exists()
identities=rd(B/'runtime/census100_completion_preparation_20261031_v1/OBSERVATION_PLAN.json')['identities']
for j in identities:live(j)
live(rd(W/'PROCESS.json'))
plan=rd(W/'PLAN.json'); assert sha(W/'watch.py')==plan['source_sha256']
observations=[json.loads(s) for s in (W/'OBSERVATIONS.jsonl').read_text().splitlines()]
assert time.time()-observations[-1]['time']<30
assert all(all(x['live'] and not x['finished'] for x in row['status'].values()) for row in observations)
guard=Path(plan['guard']['root']); assert not (guard/'STOP').exists() and not (guard/'FAILURE.json').exists()
samples=[json.loads(s) for s in (guard/'samples.jsonl').read_text().splitlines()]
samples=[x for x in samples if x['time']>=plan['time']]
assert time.time()-samples[-1]['time']<30
gpu=dict(samples=len(samples),seconds=samples[-1]['time']-samples[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_guard_included=True)
steps={m:rd(R/m/'train/PROGRESS.json')['steps'] for m in ['impedance','admittance','vmc']}
parents=dict(impedance=4099894,admittance=4103750,vmc=4104750)
growth={m:steps[m]-observations[0]['progress'][m]['steps'] for m in steps}
new={m:steps[m]-parents[m] for m in steps}
main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=REPO,text=True).strip()
baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=REPO,text=True).strip()
assert main=='fadfbd4f92cecbd5aaa4d5f1274e9ca6be5b9ec6'
snapshot=dict(time=time.time(),host=socket.gethostname(),original_103_identities_verified=True,watcher_identity=rd(W/'PROCESS.json'),watcher_running=True,watcher_observed_seconds=observations[-1]['elapsed_s'],watcher_samples=len(observations),watcher_first=observations[0],watcher_last=observations[-1],steps=steps,new_steps=new,growth_since_watch_start=growth,gpu=gpu,main=main,baseline=baseline,goal='active',full100_pending=True,automatic101=False,guard_after_science=True)
put(D/'SAVE_SNAPSHOT.json',snapshot)
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples))
E.mkdir();A.mkdir();manifest=[]
files=[]
for root in [D,O,W]:
 for p in root.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.npz','.diff'}:files.append(p)
for p in sorted(files):
 data=p.read_bytes();assert len(data)<20*1024**2
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 if p.suffix=='.jsonl':
  lines=data.splitlines();data=b'\n'.join(lines)+b'\n'
  for line in lines:json.loads(line)
 rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Completed exploratory gradient probe plus saved arithmetic review; running bounded completion watcher snapshot. No complete100 result or convergence claim.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as z:
 for p in sorted(E.rglob('*')):
  if p.is_file():z.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as z:
 assert len(z.getmembers())==len(manifest)+1
 for member in z.getmembers():assert z.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_members_verified=True,initial_main=main,baseline=baseline,backup_scope='SharedSSD small evidence including gradient arrays; HDD existing254-byte pointer only. Large checkpoint/replay/raw remain sharedSSD; not fullHDD/arm1 backup.')
put(A/'RECEIPT.json',receipt);put(REPO/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 第100轮继续：阻抗梯度诊断与完成监视 — 2026-10-31

Goal active，原训练与全部审查仍在运行，未收敛。本轮收取原梯度诊断正常退出结果，未重启任何训练，未派发101或Direct34。四GPU保活在科学任务完成后仍继续，勿创建STOP。

主机 `{socket.gethostname()}`；Python `{B}/env/bin/python`（3.11）；正式训练 `{R}`。保存时累计步数 `{steps}`，相对完整99新增 `{new}`，每方法原上限41250。原103个进程身份及新watcher PID2204928已核；watcher记录{len(observations)}次/{observations[-1]['elapsed_s']:.3f}s，三路自监视开始增长 `{growth}`。八项科学作业均原进程live，完整100尚待。

只读梯度探针 `{D}/probe.py` 在CPU10耗时{rd(O/'FINISHED.json')['elapsed_s']:.3f}s完成，计划上限600s。仅使用已保存完整99阻抗checkpoint及partial100+7000快照，未读取新在线快照，无物理步、优化器更新或权重推广。结果/梯度数组 `{O}`；source SHA `{sha(D/'probe.py')}`，两个checkpoint SHA完整记录于PLAN/REVIEW。原learner/Adam/replay/RNG和文件hash保持，参数.grad为空。

检查critic4（零起始，第五个critic）上两个失败终端及其余2385个原mask=1终端的平均SSE。旧92 replay index3804982，新99 index4097928，均为active_long_train_0000，但历史context和动作不同，原mask均保留。两个快照的局部梯度余弦如下：

|目标对|完整99|partial100+7000|
|---|---:|---:|
|旧92 / 新99|0.391403718|0.395202749|
|旧92 / 其余终端均值|0.174377951|0.204407849|
|新99 / 其余终端均值|0.354012447|0.332828543|

六项均正，所检查两个状态不支持这三个终端SSE目标的局部一阶冲突解释。仍不能据此解释实际线上旧样本退化：未包含非终端TD、真实抽样分母、其他critic、Adam预条件或actor更新，没有线上minibatch索引。此结果不是全程无冲突的证明，也不是完整100结论。

第五critic的SSE：旧92约9.466941→32.429546（退化），新99约1770.462946→1530.037558（改善），其余2385终端平均0.019679606→0.017298263。这里仅第五critic，不可与此前全五critic masked SSE总值混用。前向批形状不同，原预测仅核验rtol=atol=1e-5，不声称逐bit相等。保存数组独立复算全部六个dot/norm/cosine、各组完整成员/原mask及MSE通过；该复算不是第二次autograd执行。小表足够解释，无新增图检查声明。

完成监视 `{W}` PID2204928，原上限3600s/10s采样与archive截止1793478193.3637073不变；接受原进程身份或真实成功终态。当前仍运行，归档OBSERVATIONS仅截面，不冒充WATCH_REVIEW。监视超时不重启科学作业、不停止guard；原部分前缀SAVED_REVIEW早调用失败已恢复，不当作活跃comparison失败。

GPU实测{gpu['samples']}样本/{gpu['seconds']:.3f}s，各卡最低{gpu['minimum']}%、低于50次数{gpu['below50']}，末{gpu['last']}%。包含独立保活，非科研吞吐或每瞬时保证。guard `{guard}` supervisor96425/workers96426–96429；独立于对话，但不是重启自启服务。

下一步核真实完整100及四个消费者：原core/loss/health、固定8893、全90比较与population、新90/总8983、完整context/loss。实际查看五图后写收据，全90使用FULL100_PLOT_INSPECTION.json，再运行 `{B}/runtime/census100_completion_20261031_v1/consolidate100.py`。详见[完整审查交接](RL_CENSUS100_COMPLETION_READY_20261031.md)。未取得全部实际产物之前不得宣称100完整审查通过。

原97–99三路稳定性失败永久保留，不移为98–100。新100–102意向不变，101/102尚未登记，须逐阶段判断/预检；原reward与loss标准不放宽，I反复loss19–21及旧terminal退化保留。Direct33已过原数值标准、冻结30 Task/Strict0/0，不追加34；历史memory缺口/恢复2证据、指定ESN及最终公平比较/共同Tref/SPT仍待。

证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}bytes，SHA256 `{receipt['sha256']}`，逐成员核验。HDD仅在原254-byte LATEST指针内覆写；大checkpoint/replay/raw仍共享SSD，无完整HDD或arm1备份。main `{main}` / baseline `{baseline}`已实际远端query/fetch/read，发布后收据 `{A}/PUBLICATION.json`。
'''
(REPO/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-31 — 第100轮原训练继续，阻抗梯度诊断不支持局部冲突解释

- [交接](docs/{TAG}.md)。原完整99与partial100+7000第五critic只读梯度完成；旧92/新99余弦+.3914/+.3952，与其余2385终端均值亦均正。全保存成员/原mask/MSE/dot/norm/cosine复算通过，全state/checkpoint保持，零物理/优化更新；不作线上因果归因或收敛声明。
- 原103身份与新完成watcher核验，八科学作业仍运行；watcher{observations[-1]['elapsed_s']:.3f}s三路增长{growth}，完整100/五图/最终合并仍待。监视上限不延长科学预算，超时不重启，无101。
- 原97–99失败/100–102意向、I尖峰与旧样本退化、Direct33原验收与冻结0/0、指定ESN/最终比较待保持，Goal active。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束继续guard。
- SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254-byte指针；开工mainfadfbd4f/baselinef6e8f8c2已核，主机/绝对路径/完整hash见交接及SAVE。

'''
for name in ['AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
 p=REPO/name;old=p.read_text();addition=entry.replace('(docs/','(') if name.startswith('docs/') else entry
 if name=='AGENTS.md':first,rest=old.split('\n',1);p.write_text(first+'\n\n'+addition+rest.lstrip('\n'))
 else:p.write_text(addition+old)
pointer=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
size=pointer.stat().st_size;data=(str(REPO/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode()
assert size==254 and len(data)<size
with pointer.open('r+b') as f:f.write(data+b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data)
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps,new_steps=new),indent=2))
