from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile,math,subprocess
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle94_20261031_v1';V=B/'runs/parameter_census_cycle94_review_20261031_v1';T=B/'runs/census94_fixed93_terminal_20261031_v1';C=B/'runtime/census94_comparison_20261031_v1';TAG='RL_COMPLETE94_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
scientific=rd(D/'COMPLETE94_SCIENTIFIC_REVIEW.json');assert scientific['passed'];methods=scientific['methods']
for m,v in methods.items():
 f=rd(RUN/m/'train/FINISHED.json');assert f['status']=='stopped_at_complete_cycle' and f['cycles_completed']==1 and f['steps']==v['training']['steps']
 snap=rd(D/'TRAINING_FINISH_SNAPSHOT.json')['methods'][m]
 assert snap['task']==v['training']['task'] and snap['strict']==v['training']['strict'] and math.isclose(snap['reward_mean'],v['training']['reward_mean'],abs_tol=1e-13)
 assert sha(RUN/m/'train/episodes.jsonl')==snap['episodes_sha256']
assert rd(D/'WATCH_REVIEW.json')['reason']=='all_existing_training_and_consumers_finished'
assert rd(V/'FINISHED.json')['completed']
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists()
for j in cg['identities']:live(j)
rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,guard_identities=cg['identities'],original94_training_and_consumers_finished=True,complete94=True,cycle95_launched=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md'}}
files.update(p for p in V.rglob('*') if p.is_file() and p.suffix in {'.json','.npz','.png'})
files.update(p for p in T.glob('*') if p.suffix in {'.json','.npz','.png'})
for n in ['COMPARISON_FINISHED.json','COMPARISON_PLAN.json','INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','CHANGED_CASES_REVIEW.json','CACHE_POPULATION_FULL_REVIEW.json','PLOT_INSPECTION.json','training93_94_all90.png','interpret94.py','changed_cases.py','check_terminal_population.py']:files.add(C/n)
for n in ['terminal94.py','wait_terminal94.py']:files.add(B/'runtime/census94_prefix_20261031_v1'/n)
for n in ['driver.py','census_native.py','review94.py','health94.py','loss94.py','archive94.py','SCIENTIFIC_DECISION.json','STABILITY_WINDOW_INTENT.json','SOURCES.json','SOURCE_REVIEW.json','CPU_CONSUMER_REVIEW.json']:files.add(B/'runtime/census94_online_20261031_v1'/n)
files.update(p for p in RUN.glob('*.json'))
for m in methods:
 files.update(p for p in (RUN/m).glob('*.json'))
 files.update(p for p in (RUN/m/'train').glob('*.json'))
 files.add(RUN/m/'train/episodes.jsonl')
 files.update((RUN/m/'train/cycle_00094').glob('*/rollout.json'))
 files.add(B/f'runs/parameter_census_cycle94_archive_20261031_v1/{m}/cycle_00094.json')
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS94_STABILITY_PREP_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Completed94 all90 original full replay/health/loss reviews, actual four plot inspection receipts, full8353 fixed93 terminal comparison, live/full terminal-population growth, all90 comparison and regressions. Frozen original training sources referenced; current small evidence archived. No convergence or cycle95 launch. Large checkpoints and raw logs remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large94 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
entry=f'''## 2026-10-31 — 完整94已审；历史终端拟合改善，原loss尖峰与未收敛保持

- [交接](docs/{TAG}.md)。三路各41250新增/30完整55秒/0中止，旧回放及新52/action/reward精确，Task/Strict18/17、15/14、17/17。原抽样loss均值1.0982/1.0442/.7287、最大16.365/3.949/1.258；actor漂移与I/A尖峰保留，条件估计平滑不替代原loss健康，94–96窗口未完整，未收敛。
- 全8353固定93终端/all5/原mask严格恢复与保存标量/实际图通过，masked SSE下降92.35%/87.44%/89.08%；394/924/1138个样本退化、I部分unmasked与A/V critic0退化保留。I93原尖峰5893.163→.225、旧90中止1252.204→560.052仍较大，不是泛化或线上因果证明。
- 全90比较和全部标签变化核验：I long0000新增Task/Strict，A short0900获益但short0200失去成功，V short0600新增Strict。每路全部41250次更新终端总数与done累计精确，90新终端、总8443；未声称在线分层张量逐值观测。原三训练/archive/两个消费者正常结束勿重启；下一步准确全94父、同census有限95恢复/登记，尚未派发，无自动96/Direct34。全部历史失败、Direct原结论和指定ESN缺失保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。

'''
lines=['|方法|总steps|Task/Strict（各30）|reward均值|原loss首1000→末1000|原loss最大|','|---|---:|---:|---:|---:|---:|']
for m,x in methods.items():
 tr=x['training'];q=x['loss']['agent_train/original_sampled_q_loss'];lines.append(f"|{m}|{tr['steps']}|{tr['task']}/{tr['strict']}|{tr['reward_mean']:.9f}|{q['first1000_mean']:.6f}→{q['last1000_mean']:.6f}|{q['maximum']:.6f}|")
report=f'''# 完整94条件终端估计器审查与续接

第94轮三路正式训练及全部既有审查已正常结束，**尚未收敛，Goal active**。实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`；恢复后再次核验两分支一致，非RL final108仍仅登记完整性、0/108，不改其工作。

## 完整训练与原loss

{chr(10).join(lines)}

三路均新增41250 transition、30完整55s回合、零中止；原旧回放所有字段/history/rawbit与新current/next52、raw/mixed action全部精确，全部新reward由原physical interval journal重建误差0。此为冻结reward实现下的journal算术，不声称重新独立模拟全部物理子步。网络/优化器有限，完整93父权重/Adam/RNG/回放承接，旧容量23/47 marker、4m append-only、双架构和census marker保留。固定physics/MJB/Task/Strict、actor49/canonical48、critic52、dt5e-5、原LR/reward/masks/terminal128/batch65536/UTD1未改。

全部123750条原JSONL optimizer记录与保存NPZ所有metric逐值一致；math.fsum独立复算首末1000/均值/极值通过，每方法原loss前20大尖峰及对应step、条件估计值、actor、population均保留。I/A/V原loss均值1.098207/1.044163/.728686，较93的1.312305/1.094638/.782221下降；最大16.365429/3.949249/1.258129，93最大32.685043/6.166541/17.468910。

新 `agent_train/q_loss` 等于条件终端估计loss，**健康判断使用 `agent_train/original_sampled_q_loss`**。I条件最大仅1.934500，不能据此抹掉原16.365尖峰。I原loss前期密集高尖峰后下降，但末段仍有尖峰；A后段孤立3.949/3.35尖峰，V较有界。actor首末I25.318340→27.051406、A−7.730148→−7.620333、V−10.636989→−10.196831，漂移未消失。九栏loss图和六栏health图已真实查看，标准收据 `{V}/PLOT_INSPECTION.json`。health严格恢复完整state/RNG不变；4096 TD仍为未投影固定min-pair诊断，不等于实际投影及A/V mean目标。health图右上标题略裁剪，数据可见，原图保留。

## 实际在线终端增长

先前first5000没有新终端，不当作增长证据。本轮实时前缀审查实际覆盖I36999/A37000/V37012条更新，见22/21/21新终端；随后完整核验每方法41250条、30新终端，全94 replay dones与全部保留93 terminal索引/mask绑定，通过全部inclusive done cumsum与日志population逐值检查，末总数2815/2814/2814，共8443。完整检查包含checkpoint的32 strata计数；**在线每个stratum张量内容未记录，不声称逐值观测**。完整结果覆盖并保留前缀证据。

## 固定93全部8353终端对比

从完整94严格census-aware CPU恢复，零optimizer/physics，完整learner/Adam/replay/RNG不变；使用完整93 potential审查的 `initial_prediction`，没有使用隔离拟合权重。保存数组回读、独立标量SSE与已知中止/尖峰索引核验通过，九栏图已实际查看。

|方法|固定93终端数|原mask总SSE 93→94|相对变化|逐样本退化数|
|---|---:|---:|---:|---:|
|impedance|2785|12060.415846→922.911537|−92.3476%|394|
|admittance|2784|1234.932440→155.109124|−87.4399%|924|
|vmc|2784|964.600317→105.289509|−89.0846%|1138|

三方法所有五个critic的masked SSE均下降，≤92旧终端分别下降83.95%/87.38%/87.68%，新93组下降99.946%/90.651%/98.753%。I已知79/90/92中止分别34.0198→2.2500、1252.2042→560.0523、138.3928→77.8465；93完整55s放置失败spike3851694从5893.16295→.225316。旧90终端残差仍显著。

不隐藏退步：I unmasked critic0/1/3 SSE增加326.602/155.181/592.369；A critic0 all-row SSE+736.247、unmasked+868.959；V critic0 unmasked+231.644。全部样本最大20退化、all-row和masked分项保留；未参与某critic训练的mask0不能混为拟合损失。这里只是已见历史终端拟合，不是独立泛化，也不能单靠下降归因于新估计器或宣布收敛。

## 全90训练条件变化

完整93→94按相同条件/模型绑定reward分项、Task/Strict、abort与全部变化rollout，保存算术通过、全90图已实际查看。I平均reward +1.636158，long0000新增Task/Strict，terminal均值贡献+1.666667。A平均−.014961，short0900新增Task/Strict，但short0200从成功退为load_transfer失败，计数抵消不可隐藏。V平均+1.737384，short0600 Task保持、Strict转为通过，外部最大穿透.216775→.170706mm，terminal均值贡献+1.666667。四个变化条件均完整55s、无abort，MJB相同。这是在线条件描述比较；94估计器改变，不是独立配对因果试验或94–96稳定性结论。

## 续接决定与未完成项

`{D}/NEXT_FINITE_DECISION.json` 根据完整证据决定准备一次同设置有限95：每方法最多41250新增/30×55s，从**归档完整94**准确全state续接，采用census-aware恢复与完整协议/父链保护。现在95尚未登记/派发，96无自动排队，Direct34未派发。旧94 driver仅将93迁入首94，不能直接拿来启动95；先实现并核验保留census/架构/容量marker的95恢复路径、资源/无重复和独立登记，再启动并做真实startup及完整归档审查。

固定94–96意向登记时点为94启动后、首完整回合结果前；既有固定5%/nearzero1/5000 bootstrap/seed2026102861程序不变。95/96未完成，九组完整输入binder的REGISTRATION/统计REVIEW不存在，不以93→94变化替代该窗口；原loss健康与最终独立评测另需通过。原90–92 I/A失败、V reward-only通过及其他历史失败均保留。Direct33原数值验收保留，但冻结33全30 Task/Strict0/0；旧28缺完整memory invariance、恢复2已证，不能改写为Task成功。指定ESN仍缺，不以其他ESN替代。

## 恢复地址与保存

正式run `{RUN}`；完整归档 `{B}/runs/parameter_census_cycle94_archive_20261031_v1/{{method}}/cycle_00094.pt`；全review `{V}`；固定终端 `{T}`；全90比较 `{C}`；本轮总结/观察 `{D}`。checkpoint SHA256：

'''+''.join(f"- {m}: `{x['training']['checkpoint_sha256']}`\n" for m,x in methods.items())+f'''
原三learner/archive/两个只读消费者均有正常完成收据，watch200样本/1993.834s核验其运行→完成，不重启94。此前 `IN_PROGRESS.md` 是未完成阶段历史快照，其待完成描述由本报告覆盖；原review中的plot pending字段由后续带hash的PLOT_INSPECTION收据完成，不改原收据。

独立guard `{G}` 的五个PID/start身份当前核验正常，**科学结束后仍保留**，不创建STOP。采样{gpu['samples']}个/{gpu['elapsed_s']:.3f}s，min{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%。这是包含synthetic guard的占用，不等同科研吞吐或每瞬时保证；旧主机切换0%历史保留。guard不是系统重启服务，重启要核对主机和新进程身份。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，全部tar成员/JSON/源码AST核验；包括三路完整loss数组、固定终端数组、四张图、90条rollout摘要及来源审查。Git字节核验与实际远端发布见 `{A}/GIT_BYTES_REVIEW.json` 和 `PUBLICATION.json`。完整checkpoint、原optimizer/transitions/raw大产物仍共享SSD，非HDD/arm1全备份。HDD配额已满，仅既有LATEST原地写254字节指针，指向本报告。代码入口和源码hash沿正式94 SOURCE记录，原训练解释器/库/MJB保持。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu)))
