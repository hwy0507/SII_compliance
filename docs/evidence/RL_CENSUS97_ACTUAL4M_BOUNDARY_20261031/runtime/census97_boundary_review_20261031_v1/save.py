"""Publish small immutable evidence after the actual boundary checks complete."""
from pathlib import Path
import json, time, hashlib, tarfile, ast, socket

D = Path(__file__).resolve().parent
B = D.parents[1]
R = B / 'repository/SII_compliance'
BOUND = B / 'runs/census97_capacity_boundary_20261031_v1'
RUN = B / 'runs/parameter_census_cycle97_20261031_v1'
TAG = 'RL_CENSUS97_ACTUAL4M_BOUNDARY_20261031'
E = R / 'docs/evidence' / TAG
A = B / 'repository' / TAG
read = lambda p: json.loads(p.read_text())

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def put(p, obj):
    with p.open('x') as f:
        json.dump(obj, f, indent=2, allow_nan=False)
        f.write('\n')

boundary = read(BOUND / 'REVIEW.json')
continuity = read(D / 'CONTINUITY_REVIEW.json')
observation = read(D / 'OBSERVATION_REVIEW.json')
assert boundary['passed'] and continuity['passed'] and observation['passed']
assert continuity['original_boundary_review_sha256'] == sha(BOUND / 'REVIEW.json')
assert not list(BOUND.glob('FAILURE*')) and not list(D.glob('*FAILURE*'))
plan = read(D / 'PLAN.json')
for j in plan['identities']:
    if j['pid'] == plan['boundary_pid']:
        continue
    state = Path('/proc', str(j['pid']), 'stat').read_text().rsplit(')', 1)[1].split()
    assert state[0] != 'Z' and state[19] == j['start']
progress = {m: read(RUN / m / 'train/PROGRESS.json') for m in plan['methods']}
guard = Path(plan['guard_root'])
assert not (guard / 'STOP').exists() and not (guard / 'FAILURE.json').exists()
samples = [json.loads(x) for x in (guard / 'samples.jsonl').read_text().splitlines()]
samples = [x for x in samples if x['time'] >= plan['time']]
assert samples and time.time() - samples[-1]['time'] < 20
gpu = dict(samples=len(samples), minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],
           below50=[sum(x['gpus'][i]['utilization'] < 50 for x in samples) for i in range(4)],
           last=[g['utilization'] for g in samples[-1]['gpus']], synthetic_guard_included=True)
(D / 'GPU_SAMPLES.jsonl').write_text(''.join(json.dumps(x) + '\n' for x in samples))
put(D / 'SAVE_SNAPSHOT.json', dict(time=time.time(), host=socket.gethostname(), progress=progress,
    gpu=gpu, original_boundary_finished=True, goal='active', complete97=(RUN / 'ARCHIVE_REVIEW_FINISHED.json').exists(),
    guard_kept_after_science=True, reboot_service=False))
files = {p for p in D.iterdir() if p.is_file() and p.suffix in ('.py', '.json', '.jsonl')}
files.update(BOUND.rglob('*.json'))
old = B / 'runtime/census97_prefix_comparison_20261031_v1'
for p in [old / 'boundary.py', old / 'prepare_boundary.py', old / 'SOURCE_ORDER_REVIEW.json',
          old / 'DIRECT_SCOPE_RECHECK.json', old / 'PROCESS.json', old / 'WAIT_PLAN.json',
          RUN / 'LAUNCH.json', RUN / 'MONITOR_LAUNCH.json',
          B / 'runs/census97_fixed96_terminal_20261031_v1/WAIT_LAUNCH.json',
          B / 'runtime/census97_continuation_20261031_v1/SCIENTIFIC_DECISION.json',
          B / 'runtime/census97_continuation_20261031_v1/STABILITY_WINDOW_INTENT.json',
          B / 'runtime/host_recovery_census93_20261031_v1/CURRENT_GUARD.json']:
    files.add(p)
E.mkdir()
A.mkdir()
manifest = []
for p in sorted(files):
    data = p.read_bytes()
    assert len(data) < 16 * 1024**2
    if p.suffix == '.py':
        ast.parse(data)
    if p.suffix == '.json':
        json.loads(data)
    rel = p.relative_to(B)
    q = E / rel
    q.parent.mkdir(parents=True, exist_ok=True)
    q.write_bytes(data)
    manifest.append(dict(source=str(p), relative=str(rel), bytes=len(data), sha256=sha(q)))
put(E / 'MANIFEST.json', dict(files=manifest, scope='Actual97 crossing4m original snapshots and all96 replay retention; supplemental full52 continuity/next-context closure; bounded original-process observation. Large snapshots remain SSD. No full97/convergence claim.'))
archive = A / 'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive, 'w:gz') as t:
    for p in sorted(E.rglob('*')):
        if p.is_file():
            t.add(p, arcname=str(p.relative_to(E)), recursive=False)
with tarfile.open(archive) as t:
    assert len(t.getmembers()) == len(manifest) + 1
    for e in t.getmembers():
        assert t.extractfile(e).read() == (E / e.name).read_bytes()
receipt = dict(time=time.time(), host=socket.gethostname(), archive=str(archive), bytes=archive.stat().st_size,
    sha256=sha(archive), members=len(manifest)+1, all_members_verified=True,
    initial_main='75f4bd3b40586ba37d1b96ff1ce8309a8f3041d7', baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',
    backup_scope='SharedSSD small evidence; existing254-byte HDD pointer only. Large checkpoints/replay/raw staySSD, not fullHDD/arm1 backup.')
put(A / 'RECEIPT.json', receipt)
put(R / 'docs' / (TAG + '_SAVE.json'), receipt)
table = ['|方法|完整96旧行逐字段保持|真实边界快照步数|超过400万行数|全部52维连续链接|快照尾部未配对行|',
         '|---|---:|---:|---:|---:|---:|']
for m, v in boundary['methods'].items():
    c = continuity['methods'][m]
    table.append(f"|{m}|{v['parent_steps']}|{v['steps']}|{v['rows_beyond4m']}|{c['exact_all52_links']}|{c['tail_rows_without_following_in_snapshot']}|")
growth = {m:observation['last_steps'][m]-observation['first_steps'][m] for m in plan['methods']}
steps = {m:v['steps'] for m,v in progress.items()}
report = f'''# 第97轮真实跨400万回放检查

**Goal active：完成真实容量边界审查，参数RL收敛尚未证明。** 原三路97训练继续；本轮未重启训练、未改科学源码/超参/物理/门槛，审计零physics/optimizer。GPU保活独立于训练，科学全部结束后仍继续；它不是重启自启服务。

## 实际跨界证据

{chr(10).join(table)}

原登记检查器在每路首次满足观察条件时，各保存一份真实大于400万步的checkpoint。所有完整96旧回放数组逐字段逐块精确保持；新日志连续、reward/done逐值相同；600万容量和原2m/4m/新增6m标记保持。每路边界索引3999998–4000002五行的原actor journal观测/动作/clock/history核验通过。快照时间由原检查器的顺序I→A→V及1000-step保存间隔决定，不声称捕获恰4000000步。

审查发现原边界代码没有显式断言next_observations的第48列混合系数。已保留原代码/结果，并用独立只读补充闭合这一证据缺口：每个可配对的同条件新transition，其全部52维next_observation与下一条current_observation完全相同；全部新current context与原transition日志精确；五条边界next context逐条绑定下一条原日志。每个快照的未配对尾行明确排除，不能把它们算成通过的连续链接。两个分别篡改第48/0列的负例被拒绝。补充检查前后快照SHA相同。此处不是训练错误或训练修复，不改变已有结果。

原证据/大快照：`{BOUND}`。补充源码/计划/结果：`{D}`。`REVIEW.json`与`CONTINUITY_REVIEW.json`列出三快照完整SHA及精确边界行；大快照不进Git或小证据包。原检查器正常结束，不重跑。

## 持续进程与未完成项

连续观察{observation['elapsed_seconds']:.3f}秒/{observation['samples']}样本，原三learner、90sampler、archive、两个完整97消费者、五guard及边界检查共102身份保持。原有限observer到期，TIMEOUT记录保留；边界检查在其1000秒截止后{observation['boundary_completed_after_deadline_seconds']:.3f}秒完成，不把等待超时改写为成功、不延长预算、不停止训练。其余101身份在边界完成后单独重新核验。训练steps增加{growth}，保存时总steps{steps}。

完整97的30条件/方法、原loss完整审查与实际图、全部90条件96→97比较、固定8623终端比较、真实新终端计数仍待原消费者完成。边界检查不等于完整97/reward稳定/loss健康。原94–96 A/V不稳定和V96 loss尖峰8.7554保持；前瞻97–99固定统计仍缺完整九组，无自动98/99。

Direct33已满足原训练数值标准，保留其原验收，不因冻结Task/Strict0/0追加34。指定ESN/最终公平评测仍未完成；原28最终内存不变性缺口与恢复2证明保持。

恢复时先检查原进程PID/start_ticks及最新97 checkpoint，不能因对话退出回退完整96。科学runtime和训练目录分别为`{B}/runtime/census97_continuation_20261031_v1`与`{RUN}`；Python为`{B}/env/bin/python`，主机`{socket.gethostname()}`。

## GPU与保存

本轮登记后GPU日志{gpu['samples']}样本，四卡最低{gpu['minimum']}%，低于50%次数{gpu['below50']}，末样本{gpu['last']}%。含合成保活，非科学吞吐，也不是每瞬时保证。原guard目录`{guard}`；不创建STOP；科学结束/对话结束均保持运行。

已query/fetch/read远端main75f4bd3b与baselinef6e8f8c2，保留非RL工作。小证据`{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256`{receipt['sha256']}`，逐成员字节/JSON/AST核验。HDD仅既有254-byte LATEST指针，大产物共享SSD，非HDD/arm1全备份。实际提交/远端验证见`{A}/PUBLICATION.json`。
'''
(R / 'docs' / (TAG + '.md')).write_text(report)
entry = f'''## 2026-10-31 — 第97轮真实跨400万回放通过，补齐下一观测context证据

- [交接](docs/{TAG}.md)。原三路真实>4m快照完整旧96全字段保持、新reward/done及五条边界actor journal绑定通过，6m与全部历史容量标记保持。实际快照步数{ {m:v['steps'] for m,v in boundary['methods'].items()} }；零训练/物理更新。
- 原checker未单独断言next context的证据缺口已用独立只读full52同条件连续链接补齐；全部新current context/五条边界next context精确，尾部未配对排除，2损坏列拒绝，快照SHA不变。原checker正常完成勿重跑。
- 原训练/归档/完整97两消费者继续，102身份连续{observation['elapsed_seconds']:.3f}s，steps增长{growth}；完整97/原loss实际图/全90与8623终端/97–99统计仍待，无自动98。Direct33原验收与冻结0/0、指定ESN缺失及全部历史失败保持，Goal active。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}；科学全部结束仍独立guard。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}，HDD仅254-byte指针，非全备份。

'''
for name in ['AGENTS.md', 'HANDOFF.md', 'UPDATE_LOG.md', 'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md']:
    p = R / name
    old_text = p.read_text()
    add = entry.replace('(docs/', '(') if name.startswith('docs/') else entry
    if name == 'AGENTS.md':
        first, rest = old_text.split('\n', 1)
        p.write_text(first + '\n\n' + add + rest.lstrip('\n'))
    else:
        p.write_text(add + old_text)
pointer = Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md')
data = (str(R / 'docs' / (TAG + '.md')) + '\nGoal active; SSD assets.\n').encode()
size = pointer.stat().st_size
assert len(data) < size
with pointer.open('r+b') as f:
    f.write(data + b' '*(size-len(data)))
assert pointer.read_bytes().startswith(data) and pointer.stat().st_size == size
print(json.dumps(dict(receipt=receipt, gpu=gpu, steps=steps)))
