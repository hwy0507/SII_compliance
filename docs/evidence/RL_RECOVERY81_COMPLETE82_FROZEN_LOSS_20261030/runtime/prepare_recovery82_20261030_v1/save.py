from pathlib import Path
import ast, datetime, hashlib, json, os, socket, subprocess, tarfile, time
B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R = B / 'repository/SII_compliance'
D = Path(__file__).parent
F = B / 'runs/parameter_recovery81_first5000_20261030_v1'
C = B / 'runtime/recovery82_completion_preparation_20261030_v1'
H = B / 'runtime/recovery82_followups_20261030_v1'
W = B / 'runtime/recovery79_81_saved_audit_wait_20261030_v1'
RUN = B / 'runs/parameter_partial75_recovery_cycle81_20261029_v1'
TAG = 'RL_RECOVERY81_PREFIX82_PREPARATION_20261030'
E = R / 'docs/evidence' / TAG
A = B / 'repository' / TAG
def read(p): return json.loads(Path(p).read_text())
def sha(p):
    with Path(p).open('rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
def put(p, x):
    with p.open('x') as f: json.dump(x, f, indent=2, ensure_ascii=False); f.write('\n')
def live(j):
    p = Path(f'/proc/{j["pid"]}/stat')
    if not p.exists(): return False
    s = p.read_text().rsplit(')', 1)[1].split()
    return s[19] == j['proc_start_ticks'] and s[0] != 'Z'
for p in [D/'DRIVER_SOURCE_REVIEW.json', D/'CONTRACT_REVIEW.json', D/'FINAL_SOURCE_REVIEW.json', D/'FUTURE_REVIEW_SOURCE_REVIEW.json', D/'HEALTH_DEPENDENCY_IMPORT_REVIEW.json', D/'OBSERVATION_FINISHED.json', F/'SAVED_REVIEW.json', C/'DEPENDENCY_BINDING_REVIEW.json', H/'PREPARATION_REVIEW.json']:
    assert read(p)['passed'], p
assert read(F/'PLOT_INSPECTION.json')['actual_image_viewed']
for x in read(D/'FINAL_SOURCE_REVIEW.json')['files']: assert sha(x['path']) == x['sha256']
for x in read(C/'LAUNCH_SOURCE_REVIEW.json')['files']: assert sha(x['path']) == x['sha256']
assert not (C/'DECISION82.json').exists() and not (C/'CONTINUATION_REASON.txt').exists()
assert not (B/'runs/parameter_partial75_recovery_cycle82_20261029_v1/LAUNCH.json').exists()
obs = read(D/'OBSERVATION_FINISHED.json')
assert obs['elapsed'] >= 600 and obs['saved_rows_verified']
assert live(read(D/'LAUNCH.json')) or (D/'FINISHED.json').exists()
assert not (W/'FAILURE.json').exists()
assert live(read(W/'LAUNCH.json')) or (W/'FINISHED.json').exists()
progress = {}
for j in read(RUN/'LAUNCH.json')['jobs']:
    assert live(j)
    p = RUN/j['controller']/'train'
    assert not (p/'FAILURE.json').exists()
    progress[j['controller']] = read(p/'PROGRESS.json')
g = Path('/tmp/sii_gpu_util_guard_20261030_v7')
since = read(B/'runtime/recovery80_complete81_running_20261030_v1/SAVE_SNAPSHOT.json')['time']
gpu = [v for v in map(json.loads, (g/'samples.jsonl').read_text().splitlines()) if v['time'] > since]
assert gpu and time.time() - gpu[-1]['time'] < 20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in gpu))
guard = dict(samples=len(gpu), minimum=[min(v['gpus'][i]['utilization'] for v in gpu) for i in range(4)], below50=[sum(v['gpus'][i]['utilization'] < 50 for v in gpu) for i in range(4)], last=[v['utilization'] for v in gpu[-1]['gpus']], synthetic_included=True, keep_after_science=True)
snap = dict(time=time.time(), host=socket.gethostname(), cycle81=progress, guard=guard, actual82_restore_complete=(D/'FINISHED.json').exists(), decision82=False, training82=False, direct34=False, goal='active')
put(D/'SAVE_SNAPSHOT.json', snap)
folders = [D, F, C, H, W, B/'runs/parameter_partial75_recovery_cycle82_review_20261029_v1', B/'runs/parameter_recovery82_loss_20261029_v1']
E.mkdir(exist_ok=False); A.mkdir(exist_ok=False)
files = sorted({p for folder in folders for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json', '.jsonl', '.py', '.diff', '.txt', '.png', '.log'}})
manifest = []
for p in files:
    data = p.read_bytes(); assert len(data) < 10_000_000
    rel = p.relative_to(B); q = E/rel; q.parent.mkdir(parents=True, exist_ok=True); q.write_bytes(data)
    if p.suffix == '.py': ast.parse(data)
    manifest.append(dict(source=str(p), relative=str(rel), bytes=len(data), sha256=sha(q)))
put(E/'MANIFEST.json', dict(time=time.time(), files=manifest, active_logs_are_snapshots=True, depends_on_prior_package='RL_RECOVERY80_COMPLETE81_RUNNING_20261030', large_artifacts_retained_shared_ssd=True))
tar = A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar, 'w:gz') as t:
    for p in sorted(E.rglob('*')):
        if p.is_file(): t.add(p, arcname=str(p.relative_to(E)), recursive=False)
with tarfile.open(tar, 'r:gz') as t:
    assert len(t.getmembers()) == len(manifest)+1
    for member in t.getmembers(): assert t.extractfile(member).read() == (E/member.name).read_bytes()
receipt = dict(time=time.time(), archive=str(tar), bytes=tar.stat().st_size, sha256=sha(tar), members=len(manifest)+1, all_members_bytes_and_ast_verified=True, host=snap['host'], source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(), start_main='1f0b9b725af98202d83816ee14a6718755440207', inspected_main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(), baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=R,text=True).strip(), large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt); put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps = {m:v['steps'] for m,v in progress.items()}
doc = f'''# 第81轮固定前缀审查与第82轮恢复/派发准备

{datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()}。Goal active。原81继续，steps `{steps}`；第82轮仅恢复校验等待器已部署，实际恢复完成={snap['actual82_restore_complete']}。没有DECISION82、CONTINUATION_REASON或82训练，没有Direct34。

实际主机 `{snap['host']}`，解释器 `{B}/env/bin/python`，大checkpoint/replay/raw位于共享SSD `{B}`。开工实时读取main1f0b9b72、baselinef6e8f8c；发布前tracking main `{receipt['inspected_main']}`，保留另一主机非RL工作。不是HDD/arm1完整备份。

## 固定5000记录的实际审查

事后登记的描述性前缀，固定取原81每路最早5000条完整optimizer记录，不挑较平坦片段。保存原字节、连续步号、全部数值有限、独立标量算术和实际六栏图通过；不是reward平稳或全周期健康验证。

|方法|critic首1000均值|末1000均值|最大值|actor首→末1000|
|---|---:|---:|---:|---|
|阻抗|2.795769|2.513341|19.474987|23.732548→23.712854|
|导纳|1.193168|1.146491|4.374383|−8.726660→−8.716748|
|VMC|1.091015|1.018133|14.953114|−12.544312→−12.587853|

阻抗反复尖峰且actor略下降，导纳前缀较平但有独立尖峰，VMC反复尖峰且actor下降。完整80的VMC74.12尖峰、short0600 Strict失败及新增terminal误差集中仍保留，不能因81早期均值降低称修复。81完整loss/replay/reward/health/标签/终端及原79–81窗口继续由原进程等待。

原窗口必要条件只读检查另已完成：从完整79/80各30回合独立复算的相邻reward相对变化I4.828534%、A16.264213%、V59.630723%。原check要求两相邻和首尾变化都≤5%，且任何轮均值绝对值<1时不可判。因此无论81结果如何，A/V本窗口不能得到five_percent_check=true（81近零则不可判，否则已有相邻失败）；I只通过第一个相邻条件，完整结论仍待。该逻辑只预判原reward判据的必要条件，不是完整81统计/健康审查，不删改原窗口或自动训练82。证据ORIGINAL_WINDOW_NECESSARY_CONDITION.json。

## 第82轮准备的边界

`{D}`：restore driver生成后的科学trainer与81逐字一致，五处metadata添加可完全逆转回原75科学trainer。仅轮次/父路径更新，原partial75历史、23/47容量marker、4m append-only、terminal128、batch65536、UTD1、LR/reward/masks/物理/gates保持。三路协议/父边界正fixture和每路19协议+8边界负例通过；真实未完成81拒绝通过，无82输出。生成helper第一次误将OLD路径后缀替换为不存在driver，FileNotFoundError原源和修正说明保留；修正后source/fixture绑定通过，无科学重启。

恢复等待PID `{read(D/'LAUNCH.json')['pid']}` 绑定原81三个learner及archive身份，须完整81回放/health审查、原learner退出后才做全state/replay/next65536只读恢复，不自动训练。未来82 startup/archive/fullreview源码准备，两个health依赖真实导入通过；完整82 loss审查保留49–74、76–81历史及原79安全失败、拒绝完整75路径，新增81→82配对数学不变。

`{C}`：82决定须完整81全审、四实际图、准确恢复、原76–78结果以及**完整原79–81结果、独立保存算术和实际统计图**。精确79–81 PLAN SHA `5cf5efb87a63b432091276c3b96a3b16126c2ab891a2e195b6c857e93cf110a0`保持；不把窗口审计passed当reward收敛passed。继承DECISION81的238证据逐hash核验，包含旧79失败及原76–78结论；新阶段必须有基于实际完整结果的续训理由，当前没有。launcher父81/driver81路径核验；缺完整81、缺决定、缺LAUNCH三项真实拒绝通过，无自动82/83。

`{H}`：82标签及两终端followup helper仅准备，预计完整81锚点2424→完整82终端2454，保留原focus与两分母。缺实际82 LAUNCH在创建输出前拒绝，未部署锚点或等待器。实际81锚点仍2394→2424，不混淆。

## 连续观察和保存

原79–81窗口wait_register_and_audit.py仅运行主audit，独立review_saved.py已有源码但没有自动接续。新只读等待器 `{W}`、PID `{read(W/'LAUNCH.json')['pid']}` 绑定原窗口PID/start及精确PLAN/源码hash；原主报告成功且原等待器退出后仅执行一次既有review_saved.py，拒绝覆盖已有SAVED_ARITHMETIC_REVIEW，原截止时间不延长、不重启原审查。bootstrap不重跑且独立区间复算限制保持，实际统计图仍须生成后人工查看。当前仅等待，无完整81/79–81结果。

{obs['samples']}样本/{obs['elapsed']:.3f}s、{obs['identities']}个原训练/审查/窗口/82恢复等待/GPU进程身份核验，steps `{obs['first_steps']}`→`{obs['last_steps']}`。保存观察行逐项回读一致；观察器自然结束，原科学继续，无重启。

上次保存后GPU{guard['samples']}样本，最低{guard['minimum']}%，低于50次数{guard['below50']}，最后{guard['last']}%。含合成保载，不是科学吞吐；按用户要求科研完成后仍继续。历史v6低谷/v7预热0保留，当前guard非重启自启服务。

SSD小证据包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，全部成员大小/hash/AST通过；依赖前轮完整80/81实际启动归档。HDD既有254字节LATEST原位更新回读，大数据仍共享SSD。实际发布收据见本归档目录PUBLICATION.json。

接续检查原81及所有后续PID/start/终态和guard年龄；继续完整81及原79–81审查，再基于实际结果决定下一阶段。原75不完整、原74–76不可判、原76–78 I近零不可判/A5%失败/V仅reward通过而loss未证全部保留。Direct33数值接受和冻结30失败/旧28内存不变证明缺失保持，不启动34；指定ESN及最终冻结比较仍待。Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(doc); (A/'HANDOFF.md').write_text(doc)
entry = f'''## 2026-10-30 — 原81前5000已审；82恢复与完整窗口决策准备

- [交接](docs/{TAG}.md)。81固定前5000原字节/独立算术/实际图通过；critic首→尾I2.795769→2.513341、A1.193168→1.146491、V1.091015→1.018133，I/V尖峰19.475/14.953及actor漂移保留，非收敛。原81steps{steps}。
- 82科学trainer逐字同81、三路metadata正例/每路19协议+8边界拒绝、真实未完整81拒绝通过；仅恢复等待{read(D/'LAUNCH.json')['pid']}部署，准确恢复={snap['actual82_restore_complete']}。决定入口要求完整81和完整原79–81结果/实际图，238既有证据重核；缺三个前置真实拒绝，82后续helper仅准备。生成helper路径错误修正保留，无82训练/Direct34，Goal active。
- {obs['samples']}样本/{obs['elapsed']:.3f}s共{obs['identities']}身份保持；GPU{guard['samples']}样本min{guard['minimum']}%、低于50{guard['below50']}，科研完成仍合成保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份；main1f0b9b72后{receipt['inspected_main'][:8]}/baselinef6e8f8c已读，发布见SSD PUBLICATION收据，无子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
    p=R/name; s=p.read_text()
    if name=='AGENTS.md': h,t=s.split('\n',1); p.write_text(h+'\n\n'+entry+t.lstrip('\n'))
    else: p.write_text(entry+s)
for p,link in [(R/'HANDOFF.md','docs/'+TAG+'.md'),(R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md',TAG+'.md')]: p.write_text(f'> **最新：[81前缀审查与82准备]({link})。原81及GPU保载继续，82仅恢复等待，无82训练。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md'); n=p.stat().st_size
v=f'# RL {datetime.datetime.fromtimestamp(snap["time"],datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}\n81;prep82;guardv7.\nSSD {B}\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n'.encode(); assert n==254 and len(v)<=n
with p.open('r+b') as f: f.write(v+b' '*(n-len(v))); f.flush(); os.fsync(f.fileno())
assert p.read_bytes()==v+b' '*(n-len(v))
print(json.dumps(receipt)); print(json.dumps(snap))
