from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
RUN=B/'runs/parameter_history_cycle88_20261030_v2';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';T=B/'runs/history88_fixed87_terminal_followup_20261030_v1'
TAG='RL_HISTORY88_FROZEN_READY_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def identity(pid,expected):
    fields=Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
    assert fields[0]!='Z' and fields[19]==str(expected)
    return dict(pid=pid,start_ticks=fields[19])
pre=read(D/'UPDATED_FROZEN_REVIEW.json');assert pre['passed']
assert read(D/'FINAL_REGISTRATION_GATE_REVIEW.json')['actual_incomplete88_rejected']
identities=[];progress={}
for j in read(RUN/'LAUNCH.json')['jobs']:
    identities.append(identity(j['pid'],j['proc_start_ticks']))
    m=j['controller'];assert not (RUN/m/'train/FAILURE.json').exists();assert not (RUN/m/'DRIVER_FAILURE.json').exists()
    progress[m]=read(RUN/m/'train/PROGRESS.json')
monitor=read(RUN/'REVIEW3_MONITOR_LAUNCH.json');identities.append(identity(monitor['pid'],monitor['proc_start_ticks']))
wait=read(T/'PROCESS_V2.json');identities.append(identity(wait['pid'],wait['start_ticks']))
assert not list(T.glob('WAIT_V2_FAILURE*')) and not (RUN/'ARCHIVE_REVIEW_FAILURE.json').exists()
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]:identities.append(identity(pid,start))
rows=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()]
rows=[x for x in rows if x['time']>=read(D/'PREFLIGHT_PLAN.json')['time']]
assert rows and time.time()-rows[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),first_time=rows[0]['time'],last_time=rows[-1]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),goal='active',identities=identities,progress=progress,gpu=gpu,original_training_unchanged=True,automatic89=False))
files=[]
for folder in [D,F,T]:
    files.extend(p for p in folder.iterdir() if p.is_file() and p.suffix in {'.py','.json','.jsonl','.log'} and p.stat().st_size<10_000_000)
for n in ['RECEIPT.json','PUBLICATION.json']:files.append(B/'repository/RL_HISTORY88_ONLINE_20261030'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
    data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
    if p.suffix=='.py':ast.parse(data)
    manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,large_artifacts=[x['snapshot'] for x in pre['methods'].values()],scope='Shared SSD; immutable input hashes inherited from verified startup manifest. No full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
    for p in sorted(E.rglob('*')):
        if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as t:
    assert len(t.getmembers())==len(manifest)+1
    for member in t.getmembers():assert t.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_bytes_and_python_ast_verified=True,initial_main='271ce4e4d4b58d4375f723a703e0af002e31739d',merged_main='9df3bf3df9221a254b40ba5b04b00adee1b2cd45',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
table=[]
for m,p in progress.items():
    binding=read(RUN/m/'REGISTRATION.json')['history_critic_amendment']['binding']
    table.append(f"|{m}|{p['steps']}|{p['steps']-binding['rows']} / 41250|{p['completed_conditions']} / 30|")
text=f'''# History88继续；更新后冻结恢复验证通过

2026-10-30 UTC，Goal active。三路有限88仍用原进程训练，未重启、未更换父checkpoint、未启动89。当前仍未证明reward稳定及loss健康。原完整科学背景和所有失败见[上一交接](RL_HISTORY88_ONLINE_20261030.md)。实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。

## 当前训练和GPU

活动汇总 `{RUN}`：impedance/vmc链接原v1，admittance为v2零物理失败后的唯一有效重试。三路父均完整87，原51维history修订、actor49、30×55s/41250、batch65536/UTD1、4m append-only与23/47标记、LR/reward/masks/terminal128/物理/gates/filter/dt全部保持。

|方法|总steps|本轮新增|完整条件|
|---|---:|---:|---:|
{chr(10).join(table)}

三learner、原archive monitor7296、固定终端跟踪waiter{wait['pid']}、guard supervisor97370及四worker的PID/start ticks已核。归档审查仍由 `runtime/history88_review_20261030_v3/archive88.py` 自动在完整边界触发，结果在 `runs/parameter_history_cycle88_review_20261030_v2`；保存时尚无完整88review，不提前写结果。

本轮GPU {gpu['samples']}样本，最低 `{gpu['minimum']}`%，低于50次数 `{gpu['below50']}`，末值 `{gpu['last']}`%。原v7守护继续，以70%为目标、50%为阈值，科研任务完成后继续保载；利用率含合成负载，不等同科学吞吐。历史v7预热0和v6 31/33/44低谷仍保留，采样不保证所有瞬时；不是重启服务。

## 实际更新后的冻结预检

代码和证据 `{D}`。`PREFLIGHT_PLAN.json`、补充脚本/hash及原87完整journal/terminal绑定 `PREFLIGHT_IMPLEMENTATION.json` 均在执行前落盘；实际执行耗时 {pre['elapsed_s']:.3f}s，`UPDATED_FROZEN_REVIEW.json`通过。

- 三份已审启动88静态快照：I新增5000、A2000、V6000步。全10critic新增history列和5个online critic的Adam一二阶矩均已非零。原快照SHA再次复核未变，没有采用离线拟合权重。
- 每方法完整learner状态和每个replay字段恢复digest精确；三动作gate、不同seed变化、错误seed拒绝通过。对原87 I short0600/A short0900/V short0000的完整1375记录输入，连续native RNG与逐动作ExternalActions的obs51/raw/mixed/context全序列完全一致，terminal历史/clock亦精确。
- 全1375输入上改变clock/history时actor输出精确不变；全learner、全部replay和全局/局部RNG前后digest不变。总8271动作调用，0新物理步、0optimizer更新、0replay写入。它证明更新后接口和恢复正确，不是完整88、物理策略表现或收敛证据。
- actual partial88被正式complete88入口拒绝。日志保留PyTorch对requires_grad tensor转标量的UserWarning；这里只读取权重幅值、未反传或更新，最终状态digest相等。

## 下一步的具体入口

冻结全90方案 `{F}/PRE_REGISTRATION.json`：3方法×全部30训练条件、每条件最多55s，最多123750动作/9900万物理子步，沿用冻结82动作seed2026102638，0更新。非held-out、独立训练seed或最终指定ESN比较。当前 **automatic_evaluation=False，尚未派发物理评测**。

完整88完成后，先读取完整review、health、loss，实际查看 `health/training_diagnostics.png` 和 `loss/loss88.png`。在该review目录写 `PLOT_INSPECTION.json`，必须含 `actual_visual_inspection: true`，以及 `plots` 列表中每张图的绝对path、sha256和 `inspected: true`。这表示实际查看，不能仅凭脚本生成而填写。

随后运行 `{D}/register_complete88.py`：它检查全部前置、三方法完整checkpoint/hash及条件journal后才生成三个最终REGISTRATION。当前真实未完成88已被该入口拒绝，`FINAL_REGISTRATION_GATE_REVIEW.json`保留结果；未创建最终方法登记。

最终登记后，按方法执行 `{B}/env/bin/python {D}/evaluate_history88.py --registration {F}/<method>/REGISTRATION.json --check-only`，先确认三个完整88准确恢复及gate，再具体登记并启动有限冻结评测。入口准备与partial软件验证不代替完整88 check-only；不自动训练89或Direct34。

另一个只读任务 `{T}`，在完整88尚未结束前登记：固定原87全终端I2605/A2604/V2604及all5 critic、原actions/rewards/masks，以先前匹配拟合保存的 **initial_control（未拟合原87）** 为基线。完整88审查成功后比较同终端的masked MSE/SSE与全行SSE，另报告同一88模型history置零敏感性。输入旧50维、历史列及终端索引都必须逐值相等；不读取final拟合权重、不更新/晋升权重。敏感性不是因果或策略性能结论，旧训练样本拟合不是泛化。

有限等待器PID `{wait['pid']}`、start `{wait['start_ticks']}`，最长7200秒，仅在原归档完整review/health/loss结束后执行一次，结果和图需后续实际查看。保存时仍等待，无比较结果。原v1等待器因sha(__file__)传入字符串而helper仅接受Path，启动即失败、没有比较/physics/update；原失败及log保留，v2仅修复路径类型并更名启动收据。保存检查先发现失效PID后终止，尚未生成归档或写交接，修复后重新保存。

## 同步和保存

本轮起始实际query/fetch/read main271ce4e4、baselinef6e8f8c；收尾发现main9df3bf3d新增另一主机v7 teacher接管安全失败报告，已阅读日志和报告并fast-forward保留。本机RL冻结runtime未改，该远端ESN不替代指定最终对照。沿用仓库sii-research-sync，无子agent。

证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，tar逐成员与源码AST已核，Git index/commit另核。冻结frozen_helpers.py的原始EOF空行逐字保留，whitespace检查仅对该原件例外，其余检查必须通过。成功normal push且实际ls-remote确认后在包外写PUBLICATION。大checkpoint/raw留共享SSD；HDD配额限制只原位更新现有254字节LATEST，不是HDD/arm1全备份。

Direct33数值阶段接受但冻结30 Task/Strict0/0；28中断缺最终内存不变证明。指定ESN仍不可用，既有询问不重复。partial75、74—76不可判、79安全中止、全部旧窗口失败（含85—87）、halfstd失败/未推广、启动88的准备文件名/LR误拒/只读父轮号三类失败全部保留。Goal保持active，下一轮优先完成88科学审查和冻结评测，依据证据作后续有限决定。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — History88更新后冻结接口通过；原训练继续

- [交接](docs/{TAG}.md)。三份实际更新partial88全learner/replay恢复、非零history权重/Adam、1375连续native与外部RNG重放/terminal/actor49隔离精确，8271记录动作、0physics/update；全state/RNG/hash不变。partial不能冒充完整88，非新性能/收敛。
- 完整88冻结90预登记及完整review/health/loss/实际图强制入口已准备，真实缺前置拒绝；最终恢复/物理评测仍待。固定原87全部终端all5对完整88跟踪已预登记并有限等待PID{wait['pid']}，只用initial_control，不晋升拟合权重。
- 原88三路及archive7296持续，总steps{ {m:p['steps'] for m,p in progress.items()} }。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束继续合成保载；旧低谷/所有失败保留。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，非HDD/arm1全备份。main271ce4e4→9df3bf3d及baselinef6e8f8c已fetch/read/fast-forward，发布见收据；Goal active，无子agent，无自动89/Direct34。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
    p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(receipt));print(json.dumps(dict(progress=progress,gpu=gpu)))
