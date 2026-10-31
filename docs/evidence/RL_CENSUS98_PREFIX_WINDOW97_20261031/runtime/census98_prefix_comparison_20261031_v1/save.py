from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];W=B/'runtime/census98_window_inputs_20261031_v1';R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle98_20261031_v1';TAG='RL_CENSUS98_PREFIX_WINDOW97_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [D/'prefix5000/REVIEW.json',D/'PREFIX_SAVED_REVIEW.json',D/'PLOT_INSPECTION.json',D/'COMPARISON_PREFLIGHT.json',D/'CAPACITY_COMPARISON_REVIEW.json',D/'PRIOR90_REVIEW.json',D/'SOURCE_ORDER_REVIEW.json',D/'CACHE_POPULATION_PREFIX_REVIEW.json',D/'CACHE_POPULATION_NEGATIVE_REVIEW.json',D/'ONLINE_OBSERVATION_REVIEW.json',W/'COMPLETE97_BINDING_REVIEW.json']:assert rd(p)['passed']
assert sha(W/'check_complete97_inputs.py')==rd(W/'PLAN.json')['source_sha256'];ob=rd(D/'ONLINE_OBSERVATION_REVIEW.json')
for j in ob['identities']:live(j)
assert not list(D.glob('*FAILURE*')) and not list(W.glob('*FAILURE*')) and not list(RUN.rglob('*FAILURE*'))
for n,h in rd(D/'WAIT_PLAN.json')['source_hashes'].items():assert sha(D/n)==h
window=B/'runs/parameter_census97_99_reward_stability_20261031_v1';assert not (window/'REGISTRATION.json').exists() and not (window/'REVIEW.json').exists()
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']};assert all(x['steps']>=ob['last_steps'][m] for m,x in progress.items())
g=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(g['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],formal98_running=True,complete98=False,automatic99=False,goal='active'))
files=set()
for folder in [D,W]:files.update(p for p in folder.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.diff','.txt','.png','.npz'})
for n in ['PUBLICATION.json','RECEIPT.json','FINAL_LIVE_STATUS.json']:files.add(B/'repository/RL_CENSUS98_ONLINE_20261031'/n)
for n in ['PLAN.json','SOURCE_LOCK.json','binding_rules.py','bind_inputs.py']:files.add(window/n)
files.add(B/'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json');files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json')
for n in ['LAUNCH.json','MONITOR_LAUNCH.json']:files.add(RUN/n)
files.add(B/'runs/census98_fixed97_terminal_20261031_v1/PROCESS.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed first5000 actual98 raw/all saved loss metrics/scalars/actual plot; inherited6m all90 97->98 comparison plus total population consumer registered; original97-99 complete97 groups checked by exact per-group AST, missing98/99 rejected. 101 live identities verified for300s. Full98/99/statistics/convergence remain pending. Large assets shared SSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence; existing254-byte HDD pointer only, not full HDD/arm1 backup; live98 checkpoints/raw remain SSD');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
prefix=rd(D/'PREFIX_SAVED_REVIEW.json');stats={m:v['original_loss'] for m,v in prefix['methods'].items()};growth={m:ob['last_steps'][m]-ob['first_steps'][m] for m in progress};steps={m:x['steps'] for m,x in progress.items()}
body=f'''# 第98轮固定前缀及97–99窗口输入 — 2026-10-31

Goal active。原三路98训练/90sampler/archive/固定8713终端消费者继续，新增全90比较等待器；没有新训练派发或重启，也未运行99/Direct34。

实际主机 `{socket.gethostname()}`，共享SSD根 `{B}`，Python `{B}/env/bin/python`。本轮分析目录 `{D}`，固定窗口输入审查 `{W}`，训练目录 `{RUN}`。恢复先核原PID/startticks及最新98 checkpoint，避免重复或回退。

## 固定前5000更新

PREFIX_PLAN在读取loss数值前锁定每方法最前5000。原日志前5000行的字节、连续step/update_index、全部11种metric保存NPZ逐值、每项均值/首尾1000/min/max独立回读重算通过；原sampled Q与conditional loss分开，实际九栏图已打开并记录hash。

原sampled Q loss统计：

|方法|均值|首1000均值|末1000均值|最大|
|---|---:|---:|---:|---:|
'''
for m,s in stats.items():body+=f"|{m}|{s['mean']:.9f}|{s['first1000']:.9f}|{s['last1000']:.9f}|{s['maximum']:.9f}|\n"
body+=f'''
全部数值有限。I Q均值略升、actor稍降；A约2500更新附近有短暂均值抬升后回落、actor轻微趋向较不负；V Q在.72附近波动、actor小幅变化。保留每条原日志及top20，不把没有96规模尖峰的早期片段当作原异常消失或全轮健康结论。该前缀无新终端，不能据此判断完整reward稳定或收敛。

## 全90条件与终端总计数

完整97三方法全部90条件的模型hash、rollout Task/Strict/abort、reward分项/均值与完整审查绑定通过。97→98比较逐字段要求所有科学字段含第三容量阶段完全继承，仅本轮continuation变化；18损坏协议被拒。原94–96失败与前瞻97–99窗口保持，未移成98–100。

真实前5000的每条optimizer terminal_population逐步匹配完整97原终端数加done累计：2905/2904/2904，各无新增；15损坏日志/计数负例被拒。实际trainer源码已核验add/cache同步先于本步更新和日志。线上逐32分层tensor未记录，不声称观察到；完整98后才核真实新增terminal/replay/最终32分层。

COMPARISON_PLAN/WAIT_PLAN已锁定唯一等待器，沿原98 archive的4h截止。待原FINISHED后执行全90 reward分项/Task/Strict/abort变化、所有改变条件rollout绑定、全轮terminal总计数和完整replay核验；结果与图仍待，没有借用前缀图作为完整比较图。原独立8713终端消费者保持。

## 原97–99窗口完整97输入

从锁定binding_rules提取原逐组AST，所有语句逐项相同，实际载入三份完整97 checkpoint并验证原30episodes/41250updates/回放计数/600万marker/父链/原loss/实际两图等全部原检查。`COMPLETE97_INPUT_MAP.json`是三个实际输入组的证据，原完整九组验证器明确拒绝此map：All nine complete input groups required。

完整98/99仍缺，原窗口没有REGISTRATION/统计输出；未降低阈值或替换窗口，未改冻结binder/统计源码。Direct33原数值验收与冻结30条Task/Strict0/0、旧28最终memory证明缺口/恢复2已证、指定ESN和最终SPT公平比较待完成均保持，Goal不完成。

## 连续运行、保存与下一步

原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，三路steps增长 `{growth}`；保存时总steps `{steps}`。完整98尚未完成。继续等待真实完整98及两消费者，审原完整loss图/新终端/全90变化，再作有限99决定，不自动训练下一轮。

GPU保活独立运行，科学结束也不停止。保存窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，min `{gpu['minimum']}`%、低于50计数 `{gpu['below50']}`，末值 `{gpu['last']}`%；含synthetic guard，不是科学吞吐或每瞬时保证。

本轮实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`。小证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；所有成员字节/AST已回读核验。Git和远端字节核验见 `{A}/PUBLICATION.json`。大checkpoint/replay/raw继续共享SSD，HDD配额满仅更新既有254字节LATEST入口，非HDD/arm1完整备份。
'''
(R/'docs'/(TAG+'.md')).write_text(body)
entry=f'''## 2026-10-31 — 第98轮固定前5000已审；全90比较及原97–99完整97输入通过

- [交接](docs/{TAG}.md)。固定first5000原日志/11种保存metrics/全部标量及实际九栏图通过，原loss均值I1.020804/A1.036098/V.721204、最大1.713230/1.510725/1.178259。A约2500短暂抬升与actor漂移保留，无新终端，非全98健康稳定/收敛。
- 全97→98的90条件比较登记，真实完整97模型/标签/reward算术通过；全科学字段含继承6m stage不变，18损坏协议拒绝。前5000 terminal总数2905/2904/2904逐步精确，15损坏计数拒绝，线上逐分层tensor未记录。唯一新增只读消费者沿原archive截止等待完整98。
- 原97–99窗口三组完整97实际checkpoint/原episodes与updates/原loss/两图绑定通过，逐组AST逐句不变；原九组门拒绝三组map，98/99缺失，无最终登记或统计，不移窗口。原94–96失败/Direct33原验收和冻结0/0/历史缺口与指定ESN待保持，Goal active。
- 101身份连续{ob['elapsed_s']:.3f}s保持，steps增长{growth}；原训练/archive/两消费者继续，无自动99。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅指针。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}已query/fetch/read。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
paths=[str((E/x['relative']).relative_to(R)) for x in manifest]+[str((E/'MANIFEST.json').relative_to(R)),f'docs/{TAG}.md',f'docs/{TAG}_SAVE.json','AGENTS.md','HANDOFF.md','UPDATE_LOG.md','docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md'];put(A/'TASK_PATHS.json',dict(paths=paths));print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps)))
