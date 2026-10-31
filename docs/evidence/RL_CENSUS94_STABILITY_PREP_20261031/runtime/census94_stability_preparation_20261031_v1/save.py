from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle94_20261031_v1';T=B/'runs/census94_fixed93_terminal_20261031_v1';TAG='RL_CENSUS94_STABILITY_PREP_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [D/'PREPARATION_REVIEW.json',D/'OBSERVATION_REVIEW.json']:assert rd(p)['passed']
ob=rd(D/'OBSERVATION_REVIEW.json')
O=B/'runs/parameter_census94_96_reward_stability_20261031_v1'
for n,h in rd(O/'SOURCE_LOCK.json')['files'].items():assert sha(O/n)==h
assert not (O/'REGISTRATION.json').exists() and not (O/'REVIEW.json').exists()
for j in ob['identities']:live(j)
waiter=rd(T/'LAUNCH.json');live(waiter)
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last']['steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=waiter,comparison_waiter=rd(B/'runtime/census94_comparison_20261031_v1/PROCESS.json'),formal94_running=True,complete94=False,automatic95=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.npz','.png','.diff'}};files.update(p for p in T.glob('*.json'));files.update(p for p in O.iterdir() if p.suffix in {'.json','.py'})
for n in ['audit.py','review_saved.py','PLAN.json','REGISTRATION.json','REVIEW.json','SAVED_ARITHMETIC_REVIEW.json']:files.add(B/'runs/parameter_violation90_92_reward_stability_20261030_v1'/n)
files.add(B/'runtime/census94_online_20261031_v1/STABILITY_WINDOW_INTENT.json');files.add(B/'runtime/census94_comparison_20261031_v1/PROCESS.json')
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS94_COMPARISON_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census94_online_20261031_v1/NEXT_REVIEW_NOTES.md')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Prepared fixed94–96 census stability source and guarded full-input binder; exact original90–92 arithmetic reproduced and independent scalar bootstrap checked;33 malformed protocols rejected; actual94/95/96 complete bindings and statistics absent;600s original101-identity progress. No full94 result, no new scientific training, no convergence. Large checkpoints/journals remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large94 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)


comparison=rd(B/'runtime/census94_comparison_20261031_v1/PROCESS.json');growth={m:ob['last']['steps'][m]-ob['first']['steps'][m] for m in progress}
entry=f"""## 2026-10-31 — 第94轮继续；固定94–96稳定性程序与完整输入绑定保护就绪

- [交接](docs/{TAG}.md)。沿94启动后首完整回合前的原意向，锁94–96/5%/nearzero1/5000bootstrap/seed2026102861；统计kernel除输出键名外与原90–92逐字相同，实际旧数据全部结果精确复现、独立标量bootstrap区间通过，I/A旧失败与V reward-only通过保持，非94–96新结果。
- 实际94协议及33损坏配置拒绝通过；完整九组输入、原抽样loss/真实图、完整checkpoint/census marker/父链/原物理与23/47容量标记等绑定检查已准备，真实缺完整94与空输入拒绝。尚无REGISTRATION/94–96统计或95/96派发；原loss健康与最终独立评测仍待。
- 原101身份{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}，保存总steps{ {m:x['steps'] for m,x in progress.items()} }；原三训练/archive/两个只读等待继续，无重启、自动95/Direct34。全部历史失败/Direct原验收/指定ESN缺失保留，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254字节指针，非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。

"""
report=f"""# 条件终端估计器固定94–96统计准备

第94轮三路训练继续，仍未收敛。本轮没有训练派发、改训练参数或权重。实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。开工实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，沿sii-research-sync保存；非RL工作保持。

## 固定窗口与口径

准备目录 `{O}`；PLAN精确引用原 `{B}/runtime/census94_online_20261031_v1/STABILITY_WINDOW_INTENT.json`。固定94、95、96三轮，5%相邻及首末相对均值变化，近零保护1，5000次按三类各10条件的配对分层bootstrap，seed2026102861；保留真实中止与实际回合长度。意向登记时点准确为94启动后、首完整回合返回前，本轮源码准备更晚，未冒充启动前登记。95/96仍需单独完整科学审查与有限登记。

原90–92 audit/review_saved程序在只改变窗口、输出键名、原抽样loss字段和新增严格绑定检查后复用。94 agent_train/q_loss是条件估计器，所以本统计的loss均值/最大/图与独立算术统一读取agent_train/original_sampled_q_loss；不以条件估计的平滑替代原loss健康。保留旧55科学参数anchor、历史23/47容量标记、history/rawbit/census版本一致性。

## 已实际完成的验证

统计kernel从sorted条件矩阵到相邻/首末变化、bootstrap、配对结果，除paired输出键名外与原90–92源码逐字一致。在实际旧90–92全部270回合数据上重算，原报告全部字段精确复现；另用math.fsum对每个bootstrap抽样独立计算均值及95%区间/斜率，全部通过。原I/A失败、V reward条件通过保持。**这是旧数据算术兼容性证据，不是94–96训练结果。**

三份真实94协议与原55科学配置/原census意向一致；33个错controller/cycle/parent/预算/自动派发/terminal权重/健康loss/物理步长/batch/actor LR的损坏协议均被拒绝。空九组完整输入拒绝，实际完整94 FINISHED缺失已核验。全部源码AST与SOURCE_LOCK检查通过，没有运行未来完整统计。

## 实际完整输入绑定尚待

未来全部94–96完成后，bind_inputs.py接受显式九组input map；每组必须绑定protocol、review、health、finished、episodes、optimizer、loss_plot、health_plot、loss_review、plot_inspection、checkpoint的真实路径和SHA256。保护覆盖三路×三轮全30条件、真实model/reward/Task/Strict/abort/长度/连续更新、原抽样与条件loss双列、真实两图查看收据、完整checkpoint边界及census/架构/52维回放/容量、正式父链与原有限科学决定。

任何一组缺失或版本变化即拒绝；仅完整且通过实际checkpoint检查才写REGISTRATION和BINDING_REVIEW，随后才能运行audit.py与review_saved.py，实际结果图仍须查看。**目前REGISTRATION.json、REVIEW.json均不存在，九组完整绑定未完成，无95/96训练登记或排队。**本轮仅准备并验证统计与绑定源码，不能称未来输入已核验。条件bootstrap反映条件组成敏感性，不是独立训练seed区间；5%与有限loss不能单独宣布联合健康收敛或解锁最终测试。

## 当前训练与下一步

原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，三路增长{growth}；保存steps{ {m:x['steps'] for m,x in progress.items()} }、完整条件{ {m:x['completed_conditions'] for m,x in progress.items()} }。原三训练/90sampler/archive和两个只读等待器{waiter['pid']}/{comparison['pid']}继续，完整94尚待。

完整94后仍需原全回放/action/reward审查、health与原抽样/条件/actor实际图、全8353旧93终端比较、全90训练条件比较，以及 `{B}/runtime/census94_comparison_20261031_v1/check_terminal_population.py --complete` 的真实新终端增长核验。首次5000无新terminal不替代此检查；health4096未投影固定min-pair仍是诊断。按完整结果独立决定下一有限95，无自动95/Direct34。

全部历史失败与90–92失败/92→93波动、Direct33原数值验收和冻结0/0/旧28证据限制、指定ESN缺失保持；Goal active。若中断，保存最新94 partial权重/Adam/RNG/replay/journal再登记census-aware恢复，不回退93或重跑整个94，MuJoCo物理state未保存。

## GPU和交接

独立guard `{G}` 保留，科学结束继续，不创建STOP，不是系统重启服务。窗口{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%；含synthetic guard，不等于科学吞吐或每瞬时保证，旧主机切换0%记录保留。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员/AST/JSON核验；原diff上下文空格保留。提交字节和远端收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原LATEST254字节原地更新，大checkpoint/replay/raw仍共享SSD，不是HDD/arm1全备份。
"""
(R/'docs'/(TAG+'.md')).write_text(report)
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()})))
