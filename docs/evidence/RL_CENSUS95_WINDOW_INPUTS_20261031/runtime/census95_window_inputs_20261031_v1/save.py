from pathlib import Path
import json,hashlib,time,socket,os,ast,tarfile
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';RUN=B/'runs/parameter_census_cycle95_20261031_v1';T=B/'runs/census95_fixed94_terminal_20261031_v1';TAG='RL_CENSUS95_WINDOW_INPUTS_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
rd=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def live(j):
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j.get('start',j.get('proc_start_ticks'))
for p in [D/'COMPLETE94_BINDING_REVIEW.json',D/'OBSERVATION_REVIEW.json']:assert rd(p)['passed']
ob=rd(D/'OBSERVATION_REVIEW.json')
W=B/'runs/parameter_census94_96_reward_stability_20261031_v1'
for n,h in rd(W/'SOURCE_LOCK.json')['files'].items():assert sha(W/n)==h
C=B/'runtime/census95_comparison_20261031_v1'
for n,h in rd(C/'WAIT_PLAN.json')['source_hashes'].items():assert sha(C/n)==h
for j in ob['identities']:live(j)
waiter=rd(T/'LAUNCH.json');live(waiter)
assert not list(RUN.rglob('*FAILURE.json')) and not list(T.glob('*FAILURE*')) and not list(D.glob('*FAILURE*'))
progress={m:rd(RUN/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert progress[m]['steps']>=ob['last']['steps'][m]
cg=rd(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');G=Path(cg['root']);assert not (G/'STOP').exists();rows=[json.loads(l) for l in (G/'samples.jsonl').read_text().splitlines()];rows=[r for r in rows if r['time']>=rd(D/'REMOTE_START.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),gpu=gpu,progress=progress,live_identities=ob['identities'],terminal_waiter=waiter,comparison_waiter=rd(C/'PROCESS.json'),formal95_running=True,complete95=False,automatic96=False,goal='active'))
files={p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl','.md','.npz','.png','.diff'}};files.update(p for p in W.glob('*') if p.is_file() and p.suffix in {'.py','.json'})
files.add(C/'PROCESS.json');files.add(T/'LAUNCH.json')
for n in ['PUBLICATION.json','RECEIPT.json']:files.add(B/'repository/RL_CENSUS95_COMPARISON_20261031'/n)
files.add(B/'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json');files.add(B/'runtime/census95_continuation_20261031_v1/NEXT_REVIEW_NOTES.md')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();assert len(data)<16*1024**2;rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 if p.suffix=='.json':json.loads(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Three actual complete94 input groups verified by exact locked per-group AST, checkpoints loaded; original all-nine validator rejects partial map. Fixed94–96 window unchanged and incomplete;180s101-identity original95 training progress. No full95 result or convergence. Large checkpoints/journals remain sharedSSD, not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
 assert len(t.getmembers())==len(manifest)+1
 for p in t.getmembers():assert t.extractfile(p).read()==(E/p.name).read_bytes()
remote=rd(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD small evidence;254-byte HDD pointer only;large95 checkpoints/raw stay SSD,not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)

check=rd(D/'COMPLETE94_BINDING_REVIEW.json');growth={m:ob['last']['steps'][m]-ob['first']['steps'][m] for m in progress}
entry=f'''## 2026-10-31 — 固定94–96窗口完整94输入通过；原95继续

- [交接](docs/{TAG}.md)。三个真实完整94输入组的原protocol/review/health/finished、全部30episodes/41250optimizer、原loss和两实际图、checkpoint均完成锁定逐组检查；三完整checkpoint实际加载。抽取原逐组AST逐句精确，未改统计源码/窗口；原全九组检查拒绝仅三组输入，无最终REGISTRATION或稳定性结果。
- 完整95/96仍缺，原三训练/archive/固定8443终端与全90比较等待继续，无新增等待器或自动96。原101身份{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}，保存总steps{ {m:x['steps'] for m,x in progress.items()} }。原loss尖峰/全部失败、Direct数值验收与冻结0/0、指定ESN缺失保持，Goal active，未收敛。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}；HDD仅254字节指针、大产物SSD，非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。

'''
report=f'''# 固定94–96窗口的完整94输入核验

Goal active，原第95轮三路训练继续，尚未收敛。主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。开工实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，保留并行非RL工作；沿仓库sii-research-sync流程。

## 本轮实质进展

固定统计目录 `{W}` 的PLAN/SOURCE_LOCK/audit/review_saved/binding_rules/bind_inputs保持原字节。窗口94–96、相对5%、nearzero1、5000bootstrap、seed2026102861不变；原意向仍是94已启动且首完整回合结果前登记，未追溯改写。

`{D}/COMPLETE94_INPUT_MAP.json`绑定三方法真实完整94，每组11项：protocol、review、health、finished、episodes、optimizer、loss_plot、health_plot、loss_review、plot_inspection、checkpoint。check_complete94_inputs.py从锁定binding_rules的validate_registration抽取原内层逐组AST，全部语句ast.dump逐项精确，并以真实m/c=94执行；没有虚构95/96或修改全九组门槛。EXTRACTED_GROUP_SOURCE记录源码hash和抽取范围。

三组逐个实际加载完整94checkpoint，验证完整边界/协议hash、census marker、历史与violation架构、52维全回放、4m容量和计数；核验父链review、完整30回合和41250次原optimizer、步号连续、update_index0、原抽样loss有限非负、q_loss与条件估计相等、Task/Strict/abort和reward汇总、模型身份以及两实际图/原查看记录。三方法Task/Strict18/17、15/14、17/17保持；这表示输入完整性通过，不是loss健康或reward稳定通过。三个checkpoint及绑定文件在验证后hash仍一致。

随后将这三组真实输入交给原未改的全九组validate_registration，被 `All nine complete input groups required` 拒绝。完整95/96 FINISHED仍不存在，统计目录没有REGISTRATION或REVIEW，没有运行bootstrap或改变失败门槛。最终必须在三轮全九组真实完成并查看实际图后重新执行原完整binder。

## 当前训练和待办

原101身份连续{ob['elapsed_s']:.3f}s/{ob['samples']}样本保持，steps增长{growth}；保存总steps{ {m:x['steps'] for m,x in progress.items()} }，完成条件{ {m:x['completed_conditions'] for m,x in progress.items()} }。身份包括3learner、90sampler、archive、原固定8443终端和全90条件两个等待器以及5个GPU守护进程。本轮仅有限只读检查与观察，没有新增训练或比较等待器。

下一步等完整95原archive/review/health/loss完成，核对两原比较消费者结果，实际查看图并核验保存算术；运行 `{C}/check_terminal_population.py --complete` 检查全部95终端增长与回放done。之后依据完整95科学结果单独决定有限96，无自动96或Direct34。94–96统计仍须全部95/96真实输入，不能把目前的三组完整性检查当完整窗口绑定。96可容纳于4m；97需要单独容量决策，不覆盖旧回放。

第95轮前5000 I反复尖峰/actor上移、第94轮A short0200成功丢失、原90–92失败及所有历史退化保持。Direct33原数值验收与冻结30例Task/Strict0/0、旧28证据限制、指定ESN缺失不变。若中断，保留最新95 partial的完整权重/Adam/RNG/replay/journals，另登记census-aware部分恢复；不回退94重跑95，MuJoCo状态未保存。

## GPU与交接

原独立guard `{G}` 保留，科学结束仍运行，不创建STOP，不是重启服务。当前{gpu['samples']}样本/{gpu['elapsed_s']:.3f}s，最低{gpu['minimum']}%、低于50{gpu['below50']}、末值{gpu['last']}%。synthetic负载与实际训练吞吐分列，不承诺每瞬时利用率；旧主机切换0%历史保留。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节、SHA256 `{receipt['sha256']}`，逐成员字节/AST/JSON已核验；52维大回放、checkpoint和原始日志仍在共享SSD，通过input map引用。发布提交/实际远端字节收据 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD原LATEST仅原地更新254字节指针，非HDD/arm1完整备份。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps={m:x['steps'] for m,x in progress.items()})))
