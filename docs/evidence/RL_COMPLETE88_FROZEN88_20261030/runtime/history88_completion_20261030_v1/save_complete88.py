from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
O=B/'runs/parameter_history_cycle88_review_20261030_v2';T=B/'runs/history88_fixed87_terminal_followup_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';A88=B/'runs/parameter_history_cycle88_archive_20261030_v2';RUN=B/'runs/parameter_history_cycle88_20261030_v2';DIS=B/'runtime/history88_frozen_dispatch_20261030_v1';POST=B/'runtime/history88_frozen_postprocess_20261030_v1';RAW=B/'runs/parameter88_history_frozen_saved_audit_20261030_v1'
TAG='RL_COMPLETE88_FROZEN88_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def identity(j):
 f=Path(f"/proc/{j['pid']}/stat").read_text().rsplit(')',1)[1].split();assert f[0]!='Z' and f[19]==str(j['start']);return dict(pid=j['pid'],start=f[19])
full=read(O/'REVIEW.json');loss=read(O/'loss/REVIEW.json');interpret=read(D/'INTERPRETATION.json');fixed=read(T/'REVIEW.json');observed=read(DIS/'FROZEN_OBSERVATION_REVIEW.json')
assert full['passed'] and loss['passed'] and interpret['passed'] and fixed['passed'] and observed['passed']
assert read(O/'PLOT_INSPECTION.json')['actual_visual_inspection'] and read(T/'PLOT_INSPECTION.json')['actual_visual_inspection']
assert read(RUN/'ARCHIVE_REVIEW_FINISHED.json')['completed'] and read(T/'FINISHED.json')['passed']
for folder in [DIS,POST]:
 for n,h in read(folder/'SOURCES.json')['files'].items():assert sha(folder/n)==h
assert not list(POST.glob('FAILURE*'))
identities=[];progress={}
for j in read(F/'LAUNCH.json')['jobs']:
 identities.append(identity(j));m=j['controller'];assert not (F/m/'FAILURE.json').exists();assert read(F/m/'STARTUP_REVIEW.json')['passed'];progress[m]=read(F/m/'PROGRESS.json')
for j in [read(F/'REVIEW_LAUNCH.json'),read(POST/'PROCESS.json')]:identities.append(identity(j))
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:identities.append(identity(dict(pid=pid,start=start)))
large=[]
for m,v in full['methods'].items():
 p=A88/m/'cycle_00088.pt';assert sha(p)==v['checkpoint_sha256'];large.append(dict(path=str(p),bytes=p.stat().st_size,sha256=v['checkpoint_sha256']))
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=read(DIS/'OBSERVATION_PLAN.json')['time']];assert time.time()-rows[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_included=True,training_end_transition_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),goal='active',complete88=True,training89=False,frozen88_running=True,identities=identities,frozen_progress=progress,gpu=gpu,large_artifacts=large))
files=set()
def collect(folder,recursive=False):
 for p in folder.rglob('*') if recursive else folder.iterdir():
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.py','.json','.jsonl','.log','.diff','.txt','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for folder in [D,DIS,POST,RAW,T,F,F/'comparison82_88']:collect(folder)
collect(O,True)
for m in full['methods']:
 collect(F/m);files.add(A88/m/'cycle_00088.json');files.add(RUN/m/'train/FINISHED.json')
for n in ['FINISHED.json']:files.add(A88/n)
files.add(RUN/'ARCHIVE_REVIEW_FINISHED.json')
for n in ['review88.py','health88.py','loss88.py','SOURCES.json']:files.add(B/'runtime/history88_review_20261030_v3'/n)
for n in ['register_complete88.py','evaluate_history88.py','UPDATED_FROZEN_REVIEW.json']:files.add(B/'runtime/history88_frozen_preparation_20261030_v1'/n)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_HISTORY88_FROZEN_READY_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,large_artifacts=large,scope='Shared SSD; live frozen logs copied as dated snapshots. Not full HDD/arm1 backup. Raw diff context whitespace preserved exactly.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for x in t.getmembers():assert t.extractfile(x).read()==(E/x.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,large_artifacts=large,initial_main='7ae9d9af196f0740556b19f4d1f9b0e054952dc6',merged_main='c5f5f9d74005e1a7cdcaf1a6f4b87d7f14472b71',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; HDD254-byte pointer only, not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
table=[]
for m,v in full['methods'].items():
 q=loss['methods'][m]['stats']['agent_train/q_loss'];table.append(f"|{m}|{v['steps']}|{v['reward_mean']:.9f}|{v['task']}/{v['strict']}|{q['first1000_mean']:.6f}→{q['last1000_mean']:.6f}|{q['maximum']:.6f}|")
text=f'''# 完整88已审；冻结88全90评测实际运行

2026-10-30 UTC，Goal active。本轮原三个训练进程均正常完成唯一有限history88周期并停止，完整检查、固定终端比较和四张实际图已核。reward稳定与loss最终健康尚未证明；当前新科学作业是已预登记的冻结88三方法×30条件，尚未训练89/90或Direct34。

实际主机 `{socket.gethostname()}`；共享SSD `{B}`；解释器 `{B}/env/bin/python`。原启动及所有失败见[88在线交接](RL_HISTORY88_ONLINE_20261030.md)，更新后快照恢复见[上一交接](RL_HISTORY88_FROZEN_READY_20261030.md)。

## 完整88结果

原活动汇总 `{RUN}`；完整静态checkpoint `{A88}`；完整审查 `{O}`。三路各30×55s、41250新transition/更新，0abort；总新增123750。原10,824,948行的旧字段与历史列全部保留精确，完整88合计10,948,698行；新51维current/next、raw→mixed动作映射、全部reward重构最大误差均0。网络/优化器有限，原LR/reward/masks、batch65536/UTD1、4m append-only和23/47标记、terminal128、actor49/canonical48及物理/gates/filter/dt保持。

|方法|完整总steps|平均reward|Task/Strict（各/30）|critic loss首→末1000均值|最大单次critic loss|
|---|---:|---:|---:|---|---:|
{chr(10).join(table)}

`health/training_diagnostics.png`、`loss/loss88.png`、`{D}/training87_88_all90.png` 均已实际查看并绑定hash，PLOT_INSPECTION在完整review目录。critic滚动均值下降，有限尖峰仍在；I/A actor loss缓慢上移、V小幅漂移，entropy接近登记target，alpha有限。单个history周期不是稳定窗口；不以有限/下降代替完整收敛判断。health terminal_count为I2635/A2634/V2634，含原I多1条；报告mask内与mask外误差，不能把混合误差当统一训练目标。全局soft bound诊断超界分数I0、A0.000244140625、V0.0029785155784338713，保留该非零结果；必要界诊断不是新的通过判据。

原87→88全90训练配对 `{D}/INTERPRETATION.json`：I mean+1.841153883，Strict增加short0100；V mean+1.774734458，Strict增加short0600，二者无标签损失。A mean+3.360302619，Strict增加short0600/long0200/long0900，但 **short0900 Task/Strict均由通过变失败**，终态retreat→carry，reward16.568644293→−33.434595599，差−50.003239891；该退化完整保留。A净Task+1/Strict+2。均值增加主要来自terminal项；奖励分项分解仅算术，不证明history因果或泛化。

## 固定原87终端的完整88跟踪

`{T}`：完整88前登记，原87全部终端I2605/A2604/V2604、all5 critic、原观测/动作/reward/masks及历史列逐值一致。基线只用先前保存的initial_control（未拟合原87），不读final拟合权重、不晋升克隆。全learner/RNG不变，0新物理/更新，保存预测独立标量重算和实际图通过。

原mask内SSE，V五critic全改善；I critic3退化429.293186669，A critic2/3退化195.554795199/320.091349370，其余改善。全部终端/全部critic SSE总和I344406.079→316900.645、A182348.127→168221.366、V173003.845→139445.078；全行包含故意mask外样本，非独立泛化。history置零敏感性仅同模型输入检查，不能当架构因果或实际策略成绩。首版等待器的路径类型失败和v2修复记录继续保留，v2本轮正常完成。

## 已实际启动冻结88

唯一活动run `{F}`；冻结源 `{B}/runtime/history88_frozen_preparation_20261030_v1`；调度/汇总 `{DIS}`。完整review/health/loss/实际图前置全部通过后生成最终登记；三份完整88 check-only的全learner/replay精确恢复、RNG gate、checkpoint/source hash通过，随后单独执行launch。不同于此前partial软件预检，本轮确实已开始物理评测。

原已登记预算：3×全部30训练条件、seed2026102638（同冻结82）、每回合最多55s，总最多123750动作/9900万子步，0optimizer更新/正式replay写入。evaluator PID和start见 `LAUNCH.json`；CPU I7/A8/V9、GPU cuda:0。90.019秒/10样本的原evaluator和watcher身份、实际物理CPU绑定/进度观察通过。保存时进度 `{ {m:dict(condition=p['condition'],actions=p['actions'],completed=p['completed_conditions']) for m,p in progress.items()} }`。全90结果及最终内存不变证明仍待，不提前写成完成。

后处理 `{POST}` 已实际等待原collector；全部90的saved raw审计 `{RAW}`，同seed冻结82→88配对在 `{F}/comparison82_88`。预先核过所有条件、原physics/reward一致；原始audit子步hash/count×dt/力矩/接触/奖励复算及全部增益退化均保留。它不重新积分动力学；82→88含新增训练和history修订，不能单独归因。collector原最长21600秒等待；后处理不自动延长/重启评测。首批根REVIEW和全raw/配对输出出现后，需要实际看最终图并核验最终全state不变。

下一步继续完成冻结88并据完整88（含旧终端三critic退化与Ashort0900失败）作明确有限后续决定。未来88—90稳定性方案仍只有原预登记；未派发89/90，不跨revision合并旧失败窗口。

## GPU、归档和恢复

原v7 supervisor97370与四worker继续。窗口含三路训练结束的过渡，{gpu['samples']}采样min `{gpu['minimum']}`%、低于50 `{gpu['below50']}`，末值 `{gpu['last']}`%；含合成保载，不冒充训练吞吐，科研全部结束仍保载。历史v7预热0及v6 31/33/44低谷保留；采样不保证每瞬时，非重启服务。

本轮起始实际query/fetch/read main7ae9d9af/baselinef6e8f8c，收尾main新增c5f5f9d7（另一主机v7推理契约、局部支持、时间线及训练拟合诊断），已阅读相关日志/报告并fast-forward保留，不替代本机指定ESN模型。沿用sii-research-sync，无子agent。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，tar逐成员与Python AST校验；Git index/commit另核，成功normal push并实际ls-remote后包外PUBLICATION。raw.diff原件上下文空格精确保留，whitespace例外仅这些原件。大checkpoint/轨迹仍共享SSD，完整88三checkpoint SHA见收据；HDD仅原位更新254字节LATEST，非HDD/arm1全备份。

Direct33数值阶段接受但冻结30 Task/Strict0/0，28中断缺最终内存不变证明；指定ESN仍不可用，既有询问不重复、不替换他主机模型。partial75、74—76不可判、79安全中止、所有旧窗口失败（含85—87）、半std失败和未推广、88初次准备/LR误拒/只读父轮号失败全部保留。Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整history88已审；冻结88全90实际运行

- [交接](docs/{TAG}.md)。88三路各30×55s/41250/0abort，全旧replay及新51维映射/reward0误差/full loss/health已审；Task/Strict18/17、16/16、17/17，reward−2.375354/−5.201837/−2.815046。critic首末均值下降但尖峰/actor漂移保留，单轮未收敛；Ashort0900从通过退化至carry失败，所有90配对保留。
- 固定87全终端all5，V全部mask内SSE改善；Icritic3与Acritic2/3退化，原state/RNG不变。health/loss/训练配对/固定终端四实际图已查看。完整88三路冻结恢复通过后，全90/seed2026102638/0更新实际启动；90.019秒10样本身份/物理CPU/进度通过，最终全90/raw/配对及内存证明仍待。
- 原88训练正常停止，原guard继续；GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，非HDD/arm1全备份。main7ae9d9af→c5f5f9d7/baselinef6e8f8c已fetch/read/fast-forward，发布见收据；Goal active，无子agent，无自动89/Direct34。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(receipt));print(json.dumps(dict(gpu=gpu,frozen_progress=progress)))
