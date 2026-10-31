from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle93_20261031_v1';F=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';V=B/'runs/parameter_violation_cycle93_review_20261031_v1'
TAG='RL_VIOLATION93_COMPARE_READY_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
observed=read(D/'OBSERVATION_REVIEW.json');assert observed['passed'] and read(D/'COMPARISON_PREFLIGHT.json')['passed']
for n,h in read(D/'WAIT_PLAN.json')['source_hashes'].items():assert sha(D/n)==h
assert not (V/'FINISHED.json').exists() and not (D/'COMPARISON_FINISHED.json').exists() and not (F/'FINISHED.json').exists()
for j in observed['identities']:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(F.glob('*FAILURE*')) and not list(D.glob('COMPARISON_FAILURE_*'))
progress={m:read(T/m/'train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'COMPARISON_PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),progress93=progress,identities=observed['identities'],gpu=gpu,goal='active',complete93_pending=True,automatic94=False))
files=set()
for p in D.rglob('*'):
 if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff'}:files.add(p)
for n in ['LAUNCH.json','MONITOR_LAUNCH.json','PRELAUNCH_REVIEW.json','startup/REVIEW.json']:files.add(T/n)
for m in progress:
 for n in ['REGISTRATION.json','train/PROGRESS.json','train/EXECUTION.json']:files.add(T/m/n)
for n in ['PLAN.json','PREFLIGHT_REVIEW.json','VALIDATOR_REVIEW.json','LAUNCH_REVIEW.json','PROCESS.json']:files.add(F/n)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_PREFIX93_FROZEN90_COMPLETE_20261031'/n)
files.add(B/'runtime/violation93_terminal_followup_20261031_v1/FROZEN90_COMPLETION_REVIEW.json')
files.add(B/'runtime/violation93_terminal_followup_20261031_v1/prefix5000_v2/REVIEW.json')
files.add(B/'runtime/violation93_terminal_followup_20261031_v1/prefix5000_v2/PLOT_INSPECTION.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Full92-to93 all90 saved comparison preparation and actual missing93 rejection; one bounded comparison waiter and600s original training/archive/terminal-waiter/all90-sampler/guard identity progression. Full93 not yet complete.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for m in tar.getmembers():assert tar.extractfile(m).read()==(E/m.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={m:v['steps'] for m,v in progress.items()};deltas={m:observed['last']['steps'][m]-observed['first']['steps'][m] for m in progress}
report=f'''# 第93轮持续训练；完整92→93全条件比较已准备（2026-10-31）

原第93轮继续，完整93尚未产生；Goal active，未收敛。本轮准备并实际启动了一个只读结果比较等待器，完整93后比较全部90个方法/条件对。原全8263固定92终端等待器保持。没有新训练轮次、参数修改、重启或原截止延长，无自动94/Direct34。

实际主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。按仓库sii-research-sync实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，无子agent。源码/收据 `{D}`；原训练 `{T}`，完整消费者 `{B}/runtime/violation93_review_20261031_v1`；原固定终端后续 `{F}`。全部seed、版本、源/MJB/原完整92 checkpoint hash与实际REGISTRATION/EXECUTION不变。

## 比较消费者

COMPARISON_PLAN固定92→93全部三方法×30条件，完整92 review/health/loss/实际图及三份93登记按原字节hash绑定。预检读取真实完整92所有90记录及准确父checkpoint，验证条件无遗漏；真实缺少完整93时拒绝，未伪造未来结果。仅脚本AST、真实旧输入和缺新输入的前置核验完成，未来完整比较尚未执行。

比较器在原FINISHED、review、health和loss相符后，核验两轮科学合同不变、完整30条件、checkpoint一致、Task/Strict计数、reward均值及逐奖励项差值求和。保留全部条件、成功和失败，输出全部reward分项差值、标签得失、abort/stage与完整critic/actor loss；保存结果再按两端独立求和核验。全部标签变化额外绑定两轮真实rollout摘要及相同MJB hash，保留global/external peak和实际完整/中止标记。这是描述性在线训练比较，不是因果说明、独立训练seed或新稳定性验收窗口；原90–92 I/A失败不被替换。

唯一比较等待器PID `{read(D/'PROCESS.json')['pid']}`，原archive monitor729497/start578235463绑定，截止 `{read(D/'WAIT_PLAN.json')['deadline']}`（原monitor启动+14400秒）。只在原完整归档后执行interpret93.py和changed_cases.py，各最多600秒、CPU10、无新physics/update；结果图必须完成后实际查看。原固定92等待器1461907仍沿相同原archive截止，负责全部8263 seen92终端/all5/原masks及79/90/92中止对照，不与本消费者重复写目录。不能把任何等待器存活等同于已有结果。

## 实际推进与GPU

本轮连续{observed['elapsed_s']:.3f}秒/{observed['samples']}样本，原{len(observed['identities'])}身份（3learner、90sampler、archive、两只读等待器、5guard）逐PID/start保持，三路steps增长 `{deltas}`；保存steps `{steps}`。完整93、完整loss/health/实际图、固定92终端及全90训练比较仍待。仅观测窗口完成，原训练继续；不因观测时间到而重启。

原guard supervisor97370/workers97399–97402继续，threshold50/target70/min duty.7，科学完成后仍保活，非重启服务。从比较登记起{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，四卡最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末值{gpu['last']}%。含synthetic guard，不等于科研吞吐或每瞬时保证；所有旧低谷保持。

## 保留的结论与下一步

第93轮前5000的I密集尖峰/actor上移、A中段尖峰、V末段均值上升保留，不能以有限值或局部下降宣布健康。完整92原90–92 I/A reward失败、V仅reward条件通过保持。完整93后结合固定92终端误差是否改善、全loss和所有条件变化再作科学决定，当前无自动94。

原冻结90全部90/98391200子步/full learner-replay不变/raw/88→90配对和实际图已完成，所有原冻结进程正常结束勿重启。Task/Strict17/16、15/15、17/16；I long0000安全中止与I/V short0600穿透违规保留。它仅是原训练条件、一个外部动作seed的评测，不证明泛化或训练收敛。Direct33原数值验收、冻结全30 Task/Strict0/0、旧28缺最终内存证明与恢复2完整不变保持；不把Task成功追加为数值收敛要求。指定ESN仍缺，不替换其他主机模型。

critic/replay52、actor49/canonical48、clock49/history50/bit51、已学history/violation与Adam/RNG/双marker、append-only4m/历史23/47标记、terminal128/batch65536/UTD1/原LR reward masks、冻结physics/MJB/Task/Strict/filter/执行器/dt5e−5与本轮最多41250预算保持。partial75、不可评74–76、79/90/92安全中止、halfstd拒绝、全部失败窗口与软件失败保持；本轮未发生新的执行失败。

## 保存

共享SSD `{archive}`：{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐tar成员字节与Python AST核验。清单 `docs/evidence/{TAG}/MANIFEST.json`，index/commit逐字及实际远端正常push收据在 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅现有254字节LATEST原地更新回读；大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 第93轮继续；完整92→93全90比较等待器已启动

- [交接](docs/{TAG}.md)。全90训练条件reward分项/Task/Strict/abort/loss及变化rollout绑定消费者已准备，真实完整92输入/缺完整93拒绝通过；唯一等待器{read(D/'PROCESS.json')['pid']}沿原archive截止、0update/physics，无未来比较结果或自动94/Direct34。
- 原101身份连续{observed['elapsed_s']:.3f}s/{observed['samples']}样本保持，三路steps增长{deltas}，保存steps{steps}。原archive/固定92全部终端等待继续，完整93/健康稳定/两项比较仍待，未收敛。冻结90全部审查已完成勿重启，所有失败/Direct原结论/指定ESN缺失保持。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份；main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，正常发布见收据。Goal active，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps,deltas=deltas)))
