from pathlib import Path
import ast, datetime, hashlib, json, os, socket, subprocess, tarfile, time

B = Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl')
R = B / 'repository/SII_compliance'
D = Path(__file__).parent
TAG = 'RL_RECOVERY80_COMPLETE81_RUNNING_20261030'
E = R / 'docs/evidence' / TAG
A = B / 'repository' / TAG
RUN = B / 'runs/parameter_partial75_recovery_cycle81_20261029_v1'
REV = B / 'runs/parameter_partial75_recovery_cycle80_review_20261029_v1'
PREP = B / 'runtime/prepare_recovery81_20261030_v1'
DEC = B / 'runtime/recovery81_completion_preparation_20261030_v1'

def read(p):
    return json.loads(Path(p).read_text())

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def put(p, x):
    with p.open('x') as f:
        json.dump(x, f, indent=2, ensure_ascii=False)
        f.write('\n')

def live(j):
    p = Path(f'/proc/{j["pid"]}/stat')
    if not p.exists():
        return False
    s = p.read_text().rsplit(')', 1)[1].split()
    return s[19] == j['proc_start_ticks'] and s[0] != 'Z'

assert read(REV / 'REVIEW.json')['passed']
assert read(PREP / 'FINISHED.json')['prepared']
assert read(DEC / 'DECISION81.json')['passed']
assert read(B / 'runtime/recovery81_followups_20261030_v1/FINISHED.json')['passed']
assert read(B / 'runtime/recovery80_completion_watch_20261030_v1/FINISHED.json')['passed']
assert read(D / 'OBSERVATION_FINISHED.json')['passed']
assert read(RUN / 'startup/REVIEW.json')['passed']
progress = {}
for j in read(RUN / 'LAUNCH.json')['jobs']:
    assert live(j)
    p = RUN / j['controller'] / 'train'
    assert not (p / 'FAILURE.json').exists()
    progress[j['controller']] = read(p / 'PROGRESS.json')
g = Path('/tmp/sii_gpu_util_guard_20261030_v7')
since = read(DEC / 'SAVE_SNAPSHOT.json')['time']
gpu = [json.loads(l) for l in (g / 'samples.jsonl').read_text().splitlines()]
gpu = [v for v in gpu if v['time'] > since]
assert gpu and time.time() - gpu[-1]['time'] < 20
(D / 'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in gpu))
guard = dict(samples=len(gpu), minimum=[min(v['gpus'][i]['utilization'] for v in gpu) for i in range(4)],
             below50=[sum(v['gpus'][i]['utilization'] < 50 for v in gpu) for i in range(4)],
             last=[x['utilization'] for x in gpu[-1]['gpus']], synthetic_included=True, keep_after_science=True)
snap = dict(time=time.time(), host=socket.gethostname(), cycle81=progress, guard=guard,
            goal='active', direct34=False, automatic82=False)
put(D / 'SAVE_SNAPSHOT.json', snap)
folders = [D, DEC, PREP, B / 'runtime/recovery81_followups_20261030_v1',
           B / 'runtime/recovery80_completion_watch_20261030_v1', REV,
           B / 'runs/parameter_recovery80_loss_20261029_v1',
           B / 'runs/parameter_recovery80_task_labels_20261029_v1',
           B / 'runs/impedance_recovery80_known_case_review_20261030_v1',
           B / 'runs/vmc_recovery80_terminal_followup_20261029_v1',
           B / 'runs/admittance_recovery80_terminal_followup_20261029_v1',
           B / 'runs/parameter_recovery81_loss_20261029_v1',
           B / 'runs/parameter_recovery81_task_labels_20261029_v1',
           B / 'runs/vmc_recovery81_terminal_followup_20261029_v1',
           B / 'runs/admittance_recovery81_terminal_followup_20261029_v1']
files = set()
for folder in folders:
    for p in folder.rglob('*'):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix in {'.json', '.jsonl', '.py', '.diff', '.txt', '.log', '.png', '.npz'} and p.stat().st_size < 10_000_000:
            files.add(p)
for p in RUN.rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts and 'train' not in p.relative_to(RUN).parts and p.suffix in {'.json', '.py', '.log', '.txt'} and p.stat().st_size < 3_000_000:
        files.add(p)
for m in progress:
    for name in ['PROGRESS.json', 'INITIAL_STATE.json']:
        p = RUN / m / 'train' / name
        if p.exists(): files.add(p)
parent = B / 'runs/parameter_partial75_recovery_cycle80_20261029_v1'
for name in ['ARCHIVE_REVIEW_FINISHED.json', 'LAUNCH.json']:
    files.add(parent / name)
E.mkdir(exist_ok=False)
A.mkdir(exist_ok=False)
manifest = []
for p in sorted(files):
    data = p.read_bytes()
    rel = p.relative_to(B)
    q = E / rel
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_bytes(data)
    if p.suffix == '.py': ast.parse(data)
    manifest.append(dict(source=str(p), relative=str(rel), bytes=len(data), sha256=sha(q)))
put(E / 'MANIFEST.json', dict(time=time.time(), files=manifest, active_logs_are_snapshots=True,
                             prior_packages=['RL_RECOVERY79_ABORT80_RUNNING_20261030', 'RL_RECOVERY80_PREFIX81_PREPARATION_20261030', 'RL_RECOVERY81_DISPATCH_PREPARATION_20261030']))
archive = A / 'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive, 'w:gz') as t:
    for p in sorted(E.rglob('*')):
        if p.is_file(): t.add(p, arcname=str(p.relative_to(E)), recursive=False)
with tarfile.open(archive, 'r:gz') as t:
    assert len(t.getmembers()) == len(manifest) + 1
    for member in t.getmembers():
        assert t.extractfile(member).read() == (E / member.name).read_bytes()
receipt = dict(time=time.time(), archive=str(archive), bytes=archive.stat().st_size, sha256=sha(archive),
               members=len(manifest)+1, all_members_bytes_and_ast_verified=True, host=snap['host'],
               source_base_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip(),
               start_main='b5460e16c9789e65819a469760c4cce7ba8d6453',
               inspected_main='450dcce3cea6c7cd4a1a2eb67535aa5ac417edbd',
               baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',
               large_artifacts='Shared SSD; not full HDD/arm1 backup')
put(A / 'RECEIPT.json', receipt)
put(R / 'docs' / (TAG + '_SAVE.json'), receipt)
steps = {m: p['steps'] for m, p in progress.items()}
doc = f'''# 完整第80轮审查与第81轮实际续训

{datetime.datetime.fromtimestamp(snap['time'], datetime.timezone.utc).isoformat()}。Goal active。第80轮完整审查和第81轮精确恢复通过，已明确登记并实际启动一个有限81；当前steps `{steps}`。没有自动82或Direct34。科学运行及GPU合成保载继续。

执行主机 `{snap['host']}`；解释器 `{B}/env/bin/python`；全部大checkpoint/replay/raw位于共享SSD `{B}`。HDD仓库为该SSD checkout的入口；不是HDD或arm1完整备份。开工延续main b5460e16，实时fetch/read main450dcce3、baselinef6e8f8c，安全快进保留另一主机非RL fixed27的9/27结果（MLP棍推1/3 Strict），不将其替代本RL/指定ESN比较。

## 完整80结果及诊断

|方法|steps|新增|平均reward|Task/Strict（30）|完整55s|
|---|---:|---:|---:|---|---:|
|阻抗|3317698|41250|−2.3904375104|18/17|30|
|导纳|3320000|41250|−8.4918512704|14/14|30|
|VMC|3321000|41250|−4.5887559705|17/16|30|

三路无安全中止，全部旧回放字段精确保留，41250新reward由冻结实现/interval日志重算误差0，网络和optimizer有限；健康度forward前后网络不变。不是独立全物理子步重建，也不是冻结策略评测。180条保存rollout标签及90对reward独立复算通过。

完整loss及实际六栏图：阻抗critic首/末1000均值2.714394→2.674734、max26.822237，反复尖峰和actor下降；导纳1.330159→1.125426、max10.130503，尖峰减弱但actor漂移；VMC0.978321→1.277092、max74.120689，末段尖峰和actor漂移。不能称健康收敛。阻抗max在step3312236、short0600完成3312159之后77步；VMCmax3320045、short0600完成3318759之后1286步。未记录minibatch身份，时序接近不能证明失败terminal造成尖峰。只读检查一次误用episode的step字段，已改用真实total_steps并保留错误说明。

I/V short0600仍Task成功而Strict退化，穿透分别0.232516/0.221289mm，原0.2mm判据和失败惩罚不变。导纳long0900改善至Task/Strict成功，但short0600 Task由真变假、physical由假变真，Strict仍假，不能只报改善。已知79阻抗long0000安全中止保持：27s/675动作/global97.689118mm/失败惩罚；80同条件55s/1375动作、完成52.2s、Task/Strict/physical真，global0.170378mm。模型/evaluator相同，训练策略变化；此事后已知案例对照不证明根因修复、泛化或79峰值独立重建。

健康度图已实际查看。I/A/V sampled Q global上界36.116820/31.888751/33.035671；超界比例0/0.0292969%/0.1953125%。终端mask内MAE0.299866/0.209845/0.231896，mask外3.483180/2.295938/1.872446。mask外未参与对应critic训练，应分栏解释，不能加零误差门槛。

V/A终端跟踪完整保留2364旧行+30新行、原focus及新旧两分母，forward和RNG不变，保存标量独立复算、两散点图实际查看。V旧SSE3410.810922→2329.821680，旧贡献0.152400→0.102793（沿旧分母0.104084），新30贡献0.142613、全0.245407；部分focus恶化，旧总体改善不等于健康。A旧SSE5503.511132→1505.663480，旧贡献0.245985→0.066430（旧分母0.067269），新30贡献0.001459、全0.067888；原focus5.730751→2.912095。

保存的全部30新terminal与episode逐索引核对：VMC short0600失败行的masked SSE3054.377630、贡献0.134723，占新增30贡献约94.47%；其后short0100/short0300贡献0.004332/0.001505。此为完整80末checkpoint上的误差分解，不是训练minibatch归因，也不能据此证明74.12 loss尖峰原因。A新30最大贡献为long0500的0.000335。完整30行保存在NEW80_TERMINAL_CASE_REVIEW.json。

## 第81轮实际续接

`{DEC}/DECISION81.json`及`CONTINUATION_REASON.txt`绑定完整80/四实际图/精确恢复、原76–78窗口和版本2 DECISION80失败历史。三路full learner/replay/next65536精确恢复和每路9负例拒绝通过；actual startup独立核验通过。原4m append-only、23/47历史marker、terminal128/batch65536/UTD1、LR/reward/masks/physics/filter/gates和30条件×最多55s/41250新增全部保持。原partial75保留，不补造完整75。

运行 `{RUN}`；每路30 sampler，full archive/replay/health/loss/labels/两终端后续已部署。完整80的2394终端锚点核验后等待81预计2424行。79–81前瞻窗口保持原PLAN及seed/bootstrap5000/nearzero1/relative5%；等待身份收据见本包，不自动训练82。原76–78 I近零不可判、A5%失败、V仅reward通过而loss未证；原74–76不完整不可判，不能换窗口或奖励掩盖失败。

Direct33数值阶段已有接受、冻结全30 Task/Strict0/0，旧28最终内存不变证明缺失继续披露，不启动Direct34。指定ESN及最终完整冻结比较仍待。

## 持续运行与保存

80 completion watcher自然结束、55样本/1620.682s，所有原训练和审查终态核验；81实际启动与连续观察收据在本包。GPU上次保存后{guard['samples']}个样本，最低{guard['minimum']}%，低于50次数{guard['below50']}，最后{guard['last']}%。包含合成保载，不能当科学吞吐；按用户要求科研完成后仍运行。历史v6低谷及v7预热0保留，guardv7不是重启自启服务。

SSD小证据包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐成员字节/hash/源码AST核验。保存收据 `{TAG}_SAVE.json`。依赖既有79完整包及80/81准备包；大产物继续共享SSD。HDD既有254字节LATEST原位更新回读。实际commit/push结果另记同归档目录PUBLICATION.json，不能将保存时快照冒充发布后状态。

接续先检查原81及后续PID/start/FINISHED/FAILURE和guard采样年龄，不重复派发；完成81后审查完整窗口、loss、健康度、终端和冻结验证需求，再登记下一有限步骤。Goal保持active。
'''
(R / 'docs' / (TAG + '.md')).write_text(doc)
(A / 'HANDOFF.md').write_text(doc)
entry = f'''## 2026-10-30 — 完整80已审；有限81实际续训

- [交接](docs/{TAG}.md)。80三路各30×55/41250/noabort、旧回放/reward0误差/全loss/health/180标签/两终端/四实际图通过；reward−2.390438/−8.491851/−4.588756，Task/Strict18/17、14/14、17/16。I/V short0600 Strict退化、A Task退化、V74.12尖峰及Q超界保留，未收敛。
- 三路准确81恢复和实际startup通过；明确DECISION81、全后续及2394锚点已部署，steps{steps}。79阻抗安全中止及75不完整保留；80已知案例成功不证明修复。原76–78/79–81窗口、Direct33限制与指定ESN范围保持，无自动82/Direct34，Goal active。
- GPU{guard['samples']}样本min{guard['minimum']}%、低于50{guard['below50']}，科研完成仍合成保载；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}逐字核验，非HDD/arm1全备份。main450dcce3/baselinef6e8f8c已fetch/read并快进保留非RL9/27；发布见SSD PUBLICATION收据，无子agent。

'''
for name in ['AGENTS.md', 'UPDATE_LOG.md']:
    p = R / name
    s = p.read_text()
    if name == 'AGENTS.md':
        h, tail = s.split('\n', 1)
        p.write_text(h + '\n\n' + entry + tail.lstrip('\n'))
    else:
        p.write_text(entry + s)
for p, link in [(R / 'HANDOFF.md', 'docs/' + TAG + '.md'), (R / 'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md', TAG + '.md')]:
    p.write_text(f'> **最新：[完整80已审、81实际运行]({link})。Goal active，81及GPU保载继续，无自动82/Direct34。**\n\n' + p.read_text())
p = Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
n = p.stat().st_size
v = f'# RL {datetime.datetime.fromtimestamp(snap["time"], datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}\n81 running;guardv7.\nSSD {B}\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n'.encode()
assert n == 254 and len(v) <= n
with p.open('r+b') as f:
    f.write(v + b' ' * (n - len(v)))
    f.flush()
    os.fsync(f.fileno())
assert p.read_bytes() == v + b' ' * (n - len(v))
print(json.dumps(receipt))
print(json.dumps(snap))
