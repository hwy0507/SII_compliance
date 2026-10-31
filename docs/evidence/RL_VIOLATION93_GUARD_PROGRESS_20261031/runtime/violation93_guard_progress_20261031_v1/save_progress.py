from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';C=B/'runtime/violation93_completion_20261031_v1';T=B/'runs/parameter_violation_cycle93_20261031_v1';F=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';V=B/'runs/parameter_violation_cycle93_review_20261031_v1'
TAG='RL_VIOLATION93_GUARD_PROGRESS_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
observed=read(D/'OBSERVATION_REVIEW.json');assert observed['passed']
for n,h in read(C/'WAIT_PLAN.json')['source_hashes'].items():assert sha(C/n)==h
assert not (V/'FINISHED.json').exists() and not (C/'COMPARISON_FINISHED.json').exists() and not (F/'FINISHED.json').exists()
for j in observed['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(F.glob('*FAILURE*')) and not list(C.glob('COMPARISON_FAILURE_*'))
progress={m:read(T/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists() and not (guard/'FAILURE.json').exists()
assert (guard/'guard.py').read_bytes()==(B/'runtime/recovery86_history_progress_20261030_v1/gpu_guard_v7.py.txt').read_bytes()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'OBSERVATION_PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'GUARD_REVIEW.json',dict(passed=True,time=time.time(),source_sha256=sha(guard/'guard.py'),durable_source=str(B/'runtime/recovery86_history_progress_20261030_v1/gpu_guard_v7.py.txt'),launch=read(guard/'LAUNCH.json'),control=read(guard/'CONTROL.json'),source_matches_durable_copy=True,independent_of_science_completion=True,reboot_service=False,gpu=gpu))
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),progress93=progress,identities=observed['identities'],gpu=gpu,goal='active',complete93_pending=True,automatic94=False))
files=set(p for p in D.rglob('*') if p.is_file() and p.suffix in {'.py','.json','.jsonl'})
for n in ['LAUNCH.json','MONITOR_LAUNCH.json','PRELAUNCH_REVIEW.json','startup/REVIEW.json']:files.add(T/n)
for m in progress:
 for n in ['REGISTRATION.json','train/PROGRESS.json','train/EXECUTION.json']:files.add(T/m/n)
for n in ['PLAN.json','PROCESS.json']:files.add(F/n)
for n in ['COMPARISON_PLAN.json','WAIT_PLAN.json','PROCESS.json']:files.add(C/n)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_VIOLATION93_COMPARE_READY_20261031'/n)
files.add(B/'runtime/recovery86_history_progress_20261030_v1/gpu_guard_v7.py.txt')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Original93 continued with original101 process identities; user reiterates GPU occupancy after science ends; original guard verified unchanged and sampled, not reboot persistence. Full93 pending.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for m in tar.getmembers():assert tar.extractfile(m).read()==(E/m.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={m:v['steps'] for m,v in progress.items()};deltas={m:observed['last']['steps'][m]-observed['first']['steps'][m] for m in progress}
entry=f'''## 2026-10-31 — 第93轮继续；科学完成后仍保持四卡GPU保活

- [交接](docs/{TAG}.md)。用户再次要求全部完成后仍保持GPU≥50%；原独立guard源码与SSD持久副本逐字相符，原5进程正常，训练结束不触发退出。不是重启服务，不承诺每瞬时利用率。
- 原101身份连续{observed['elapsed_s']:.3f}s/{observed['samples']}样本保持，三路steps增长{deltas}，保存steps{steps}。原93/archive/两个只读等待器继续，完整93/健康稳定/两项比较仍待，无新训练或自动94/Direct34，未收敛。原冻结90完成勿重启；所有历史失败、Direct原结论、指定ESN缺失保持。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，含synthetic guard、不等于科学吞吐。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份；main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，正常发布见收据。Goal active，无子agent。

'''
report=f'''# 第93轮持续推进与GPU保活复核（2026-10-31）

用户要求即使全部科学工作完成仍保持四卡利用率≥50%。原GPU保活正常运行，目标70%、最低duty .7；独立于训练完成标记，未设置STOP。此次没有重启训练、等待器或guard，没有更改科学协议。

{entry.replace('(docs/','(')}
实际主机 `{socket.gethostname()}`。共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮依据仓库sii-research-sync实际query/fetch/read main `{remote['main']}` 与 baseline `{remote['baseline']}`，相关科学协议无新变化。运行证据 `{D}`；原训练 `{T}`。原checkpoint、seed、环境和MJB hash、启动登记见本次复制的REGISTRATION/EXECUTION及前交接 `RL_VIOLATION93_COMPARE_READY_20261031.md`。

原learner729494/729495/729496、90sampler、archive729497、固定92终端等待1461907、全90比较等待2089103、guard97370/97399–97402均按PID/start ticks连续核验。{observed['samples']}样本/{observed['elapsed_s']:.3f}秒的三路实际steps增量为 `{deltas}`。保存时完整93尚未出现，两等待器仍沿原截止1793422944.4276955；不能把存活称为已有最终结果。当前无自动94/Direct34。

GPU保活源码与 `{B}/runtime/recovery86_history_progress_20261030_v1/gpu_guard_v7.py.txt` 逐字核验，SHA256 `{sha(guard/'guard.py')}`。观测{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末值{gpu['last']}%。采样与合成负载不等于每瞬时保证或训练吞吐；原历史低谷保持。当前guard独立于对话和科学完成运行，但位于/tmp、不是重启服务，不能据此宣称系统镜像或重启恢复已验证。

下一步读取完整93的归档/review/health/loss，并实际查看结果图；固定全部8263终端/all5/masks比较及全90训练92→93比较结束后独立核算和查看图，保留任何新abort或退化。依据证据再决定后续，不盲目续94。原90–92 I/A稳定性失败、V仅reward通过；原93前5000的I尖峰和actor上移、A中段抬升、V末段均值上升保持，当前不能宣布reward与loss联合收敛。

冻结90全90/98391200子步审查及raw/88→90比较已完成，Task/Strict I17/16、A15/15、V17/16，I long0000安全中止及I/V short0600违规保留；原完成进程不重启。Direct33原数值验收、冻结全30 Task/Strict0/0、旧28缺最终内存证明与恢复2完全不变保持；不把任务成功追加为数值收敛条件。指定ESN仍缺，不替换其他主机模型。

保持critic/replay52、actor49/canonical48、clock49/history50/bit51、已学history/violation及Adam/RNG/双marker、append-only4m及23/47历史标记、terminal128/batch65536/UTD1/原LR reward masks、冻结physics/MJB/Task/Strict/filter/执行器/dt5e−5，每方法本轮最多41250新增。保留partial75、不可评74–76、79/90/92中止、halfstd拒绝和全部失败窗口/软件失败。

共享SSD归档 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；逐成员字节/Python AST核验。manifest在 `docs/evidence/{TAG}/MANIFEST.json`。提交字节核验和实际push远端收据位于 `{A}/GIT_BYTES_REVIEW.json` 和 `PUBLICATION.json`。HDD配额满，仅现有LATEST254字节原地更新回读；大checkpoint/replay/raw仍在SSD，非HDD/arm1完整备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps,deltas=deltas)))
