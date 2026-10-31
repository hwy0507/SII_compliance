from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile,math,subprocess
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle95_20261031_v1';V=B/'runs/parameter_census_cycle95_review_20261031_v1';T=B/'runs/census95_fixed94_terminal_20261031_v1';C=B/'runtime/census95_comparison_20261031_v1';TAG='RL_COMPLETE95_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
scientific=rd(D/'COMPLETE95_SCIENTIFIC_REVIEW.json');assert scientific['passed'];methods=scientific['methods']
for m,v in methods.items():
 f=rd(RUN/m/'train/FINISHED.json');assert f['status']=='stopped_at_complete_cycle' and f['cycles_completed']==1 and f['steps']==v['training']['steps']
 snap=rd(D/'TRAINING_FINISH_SNAPSHOT.json')['methods'][m]
 assert snap['finished']==f
W=B/'runtime/census95_completion_watch_20261031_v1'
assert rd(W/'FOLLOW_REVIEW.json')['passed'] and rd(W/'FOLLOW_REVIEW.json')['all_complete']
assert rd(V/'FINISHED.json')['completed']
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists()
for j in cg['identities']:live(j)
rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,guard_identities=cg['identities'],original95_training_and_consumers_finished=True,complete95=True,cycle96_launched=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.diff'}}
files.update(p for p in W.glob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl'})
files.update(p for p in V.rglob('*') if p.is_file() and p.suffix in {'.json','.npz','.png'})
files.update(p for p in T.glob('*') if p.suffix in {'.json','.npz','.png'})
for n in ['COMPARISON_FINISHED.json','COMPARISON_PLAN.json','INTERPRETATION.json','INTERPRETATION_SAVED_REVIEW.json','CHANGED_CASES_REVIEW.json','CACHE_POPULATION_FULL_REVIEW.json','PLOT_INSPECTION.json','training94_95_all90.png','interpret95.py','changed_cases.py','check_terminal_population.py']:files.add(C/n)
for n in ['terminal95.py','wait_terminal95.py']:files.add(B/'runtime/census95_prefix_20261031_v1'/n)
for n in ['driver.py','census_native.py','review95.py','health95.py','loss95.py','archive95.py','SCIENTIFIC_DECISION.json','SOURCES.json','SOURCE_REVIEW.json','CPU_CONSUMER_REVIEW.json']:files.add(B/'runtime/census95_continuation_20261031_v1'/n)
files.update(p for p in RUN.glob('*.json'))
for m in methods:
 files.update(p for p in (RUN/m).glob('*.json'))
 files.update(p for p in (RUN/m/'train').glob('*.json'))
 files.add(RUN/m/'train/episodes.jsonl')
 files.update((RUN/m/'train/cycle_00095').glob('*/rollout.json'))
 files.add(B/f'runs/parameter_census_cycle95_archive_20261031_v1/{m}/cycle_00095.json')
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS95_PROGRESS_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Completed95 all90 original full replay/health/loss reviews, actual four plot inspection receipts, full8443 fixed94 terminal comparison, live/full terminal-population growth, all90 comparison and regressions. Frozen original training sources referenced; current small evidence archived. No convergence or cycle96 launch; A94->95 original5% necessary condition fails, window unchanged. Large checkpoints and raw logs remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large95 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
watch=rd(W/'FOLLOW_REVIEW.json');early=rd(D/'EARLY_WINDOW94_95_REVIEW.json');prefix=rd(D/'LIVE_TERMINAL_GROWTH_REVIEW.json')
entry=f'''## 2026-10-31 — 完整95已审；loss与历史终端改善，导纳稳定性必要条件失败保留

- [交接](docs/{TAG}.md)。三路各41250新增/30完整55秒/0中止，旧回放及新52/action/reward精确，Task/Strict18/17、15/15、17/17。原抽样loss均值1.01709/1.02828/.72058，最大3.43406/1.56734/1.22933；I重复尖峰和actor变化保持，未完成联合收敛验收。
- 全8443固定94终端/all5/原mask严格恢复、保存标量及实际图通过，masked SSE下降40.52%/22.92%/19.25%，1194/1463/1185样本退化及I/A/V部分critic退化保留；旧I90残差560.052→260.108仍在，79/93小幅退化。全部41250次更新terminal总数和完整回放done/mask通过，90新终端、总8533；非在线逐分层张量观察或独立泛化。
- 全90比较：A恢复short0200 Task/Strict、short0000新增Strict，但long0900失去Task/Strict；I/V无标签变化。94→95 reward相对变化2.869%/19.769%/.473%，A违反原5%必要条件，固定94–96窗口不改，96/全九组绑定/统计仍待。原训练/archive/两消费者正常结束勿重启；下一步准确全95父同协议有限96准备，尚未登记/派发，无自动97/Direct34。全部历史失败、Direct原验收/冻结0/0和指定ESN缺失保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。

'''
lines=['|方法|总steps|Task/Strict（各30）|reward均值|原loss均值|原loss首1000→末1000|原loss最大|','|---|---:|---:|---:|---:|---:|---:|']
for m,x in methods.items():
 tr=x['training'];q=x['loss']['agent_train/original_sampled_q_loss'];lines.append(f"|{m}|{tr['steps']}|{tr['task']}/{tr['strict']}|{tr['reward_mean']:.9f}|{q['mean']:.6f}|{q['first1000_mean']:.6f}→{q['last1000_mean']:.6f}|{q['maximum']:.6f}|")
term=['|方法|固定94终端数|原mask总SSE 94→95|相对变化|逐样本退化数|','|---|---:|---:|---:|---:|']
for m,x in methods.items():
 g=x['fixed94_terminal_groups']['all'];term.append(f"|{m}|{g['rows']}|{g['masked_sse94']:.6f}→{g['masked_sse95']:.6f}|{g['relative_change']*100:.4f}%|{x['fixed94_regression_rows']}|")
report=f'''# 完整95审查与有限96接续决定

第95轮三路训练、原归档与两个分析消费者已正常完成，**尚未收敛，Goal active**。本轮实质完成完整95审查；此前十分钟观察是verified wait。主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`；沿仓库sii-research-sync流程，保留并行非RL工作。

## 完整训练与原loss

{chr(10).join(lines)}

三路各新增41250 transition、30完整55s回合、零中止。所有旧回放字段/history/rawbit与新增current/next52、raw/mixed action精确，全部新reward由原physical interval journal重建最大误差0。这是journal算术验证，不是重新仿真全部物理子步。完整94父learner/Adam/RNG/回放承接，网络与优化器有限；原23/47容量marker、4m append-only、双架构/census marker保持。固定physics/MJB/Task/Strict、actor49/canonical48、critic52、dt5e-5、原LR/reward/masks/terminal128/batch65536/UTD1保持。

全部123750条optimizer记录与保存NPZ所有metrics逐值一致，math.fsum独立复算首末1000、均值、极值通过；各方法原loss最大20条及对应step/条件loss/actor/population均保留。原loss最大较94的16.365/3.949/1.258减小为3.434/1.567/1.229；均值也降低。健康口径始终为 `agent_train/original_sampled_q_loss`；q_loss等于条件估计，不能以更平滑的条件估计替代。

实际查看九栏loss和六栏health：I重复尖峰随本轮减小但仍存在，均值下降；A总体略降；V约后30000步小幅抬升后返回接近起点。actor首末I27.089055→28.220069、A−7.620020→−7.333035、V−10.184065→−9.788037，仍有变化；这不是单靠actor上移判定实现错误，也不能据此宣称稳定。entropy接近目标，I alpha略上升、V后段有隆起。完整state/RNG不变；health4096 TD仍为未投影固定min-pair诊断，不等于实际投影及A/V mean训练目标。右上标题略裁剪但数据可见，原图不改，真实查看收据 `{V}/PLOT_INSPECTION.json`。

## 实际终端增长与全回放

前5000没有新终端不作为增长证明。本轮完成日志前缀实际见{ {m:(v['rows'],v['new_terminal_rows']) for m,v in prefix['methods'].items()} }（更新数/新终端），逐步population等于父总数加包含本步的done累计。随后完整检查三路全部41250更新、全回放done、新30终端条件/方法及保留8443 terminal indices/masks，末总数2845/2844/2844，共8533。前缀原字节hash再次与最终日志绑定。存档32 mask分层计数已核对；在线逐分层tensor没有日志，不声称逐值观测。

## 固定94全部8443终端

完整95严格CPU恢复，全部五critic和原masks，零optimizer/physics，完整learner/Adam/replay/RNG不变。基准是完整94原预测，旧8353与前次保存full94精确、新90个94终端原journal已绑定，没有推广辅助拟合权重。保存数组回读、标量SSE与原已知失败索引核验通过，实际九栏图已查看。

{chr(10).join(term)}

全8443总masked SSE均改善，但不是每个critic/样本都改善。I五critic masked均下降，all-row及unmasked critic1/4退化；A masked critic4增加3.659，all-row整体各critic下降，但新94组all-row critic2/4分别增加86.120/31.186；V masked critic0增加4.881，all-row critic0/2/3/4分别增加1185.451/672.068/3107.473/1542.400。所有分组、逐critic和最大20样本退化保留。新94组masked总SSE下降55.31%/92.40%/78.21%，旧≤93组分别下降40.24%/15.76%/17.54%。

I历史90中止索引3726050 masked SSE560.052297→260.108112，92中止77.846473→56.461428；79中止2.250010→2.489540、93完整55s放置失败尖峰.225316→.371369小幅退化。旧90大残差仍保留。以上是已见历史终端拟合，不是独立泛化、新95终端性能或在线因果证明。

## 全90条件与原稳定门槛

94→95全部90条件的模型、reward分项、Task/Strict、abort及每个标签变化rollout绑定，保存算术和实际图通过。I/V无Task/Strict标签变化，reward均值分别−.067109/−.013474；I long0000 reward下降约1.1，不能因总成功数相同而抹去连续指标变化。

A reward均值+1.692614，但存在三处标签变化：short0000 Task保持、Strict由false→true（外部峰值穿透.221224→.093390mm）；short0200恢复Task/Strict；long0900由Task/Strict成功退为carry阶段失败。三者都完整55s、无abort且模型一致。不能仅用Strict总数+1掩盖long0900退化。

`EARLY_WINDOW94_95_REVIEW.json`以两轮各30原episodes独立标量均值复算，原nearzero1未触发，既有相邻5%必要条件变化I2.868972%、A19.768884%、V.472855%。**A已违反固定94–96窗口的必要条件**；不移动窗口，不改5%门槛，不把改善方向当作平稳。I/V仅此相邻对没有违反，仍不代表三轮通过。96未完成，尚无全九组绑定或完整bootstrap；原90–92失败仍保留。

## 接续与未完成项

`{D}/NEXT_FINITE_DECISION.json`决定准备单次有限96：从**准确归档完整95**恢复learner/Adam/RNG/全部回放，保持census与全部原科学设置，每方法最多41250/30×55s。理由是本轮数值和总历史终端误差改善，但原尖峰、actor变化、A稳定性失败和条件退化仍需后续证据；96用于完成原窗口并观察，不把已失败的A相邻门槛改成通过。

96尚未登记/启动。现95 driver仅支持完整94→95，需单独适配完整95→96的父链、全state兼容/负例/原生更新与CPU消费者、资源/无重复、启动及完整审查。无自动97或Direct34。最大96 steps为I3976512/A3980000/V3981000，均≤4m；此后余23488/20000/19000，无法容纳完整97，必须另行容量决策且不覆盖旧回放。

完整94三组输入映射已准备，但最终统计需加上真实95/96全部输入并重跑原全九组binder。原loss健康与最终独立评测/指定ESN对照仍待。Direct33原数值验收保留，冻结33全30 Task/Strict0/0不改写为成功；旧28完整memory invariance缺口与恢复2已证保持，指定ESN仍缺，不能用其他ESN替代。

## 恢复与保存

正式run `{RUN}`；完整归档 `{B}/runs/parameter_census_cycle95_archive_20261031_v1/{{method}}/cycle_00095.pt`；原review `{V}`；固定终端 `{T}`；全90比较 `{C}`；本轮汇总 `{D}`，进程生命周期跟踪 `{W}`。checkpoint SHA256：

'''+''.join(f"- {m}: `{x['training']['checkpoint_sha256']}`\n" for m,x in methods.items())+f'''
原三learner/90sampler/archive/两消费者全部正常完成。有限跟踪{watch['samples']}样本/{watch['elapsed_s']:.3f}s核验运行→自然结束，退出sampler与原episode/rollout绑定，未新增训练或重复消费者，勿重启95。早期IN_PROGRESS是历史未完成快照；原plot-pending字段由后续带hash实际查看收据完成，不改写原收据。

独立guard `{G}` 五进程身份正常，科学结束仍保留，不创建STOP，不是主机重启服务。当前{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；包含synthetic负载，不等于科学吞吐或每瞬时保证，旧主机切换0%历史保持。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节、SHA256 `{receipt['sha256']}`，tar逐成员字节/AST/JSON核验；包含完整loss数组、固定终端数组、四实际图、90条rollout摘要及全部审查。Git字节与远端发布收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。大checkpoint/optimizer/transitions/raw仍共享SSD，HDD仅原地254字节LATEST指针；非HDD/arm1全备份。原训练解释器/库/MJB与运行源码hash沿SOURCE登记保持。
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
