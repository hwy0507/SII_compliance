from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';T=B/'runs/parameter_violation_cycle93_20261031_v1';O=B/'runs/violation93_fixed92_terminal_followup_20261031_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';FP=B/'runtime/violation90_frozen_postprocess_20261030_v1';X=D/'prefix5000_v2'
TAG='RL_PREFIX93_FROZEN90_COMPLETE_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
prefix=read(X/'REVIEW.json');observed=read(D/'OBSERVATION_REVIEW.json');assert prefix['passed'] and observed['passed'] and read(O/'PREFLIGHT_REVIEW.json')['passed'] and read(O/'VALIDATOR_REVIEW.json')['passed'] and read(O/'VALIDATOR_REVIEW.json')['negative_count']==27
frozen_complete=read(D/'FROZEN90_COMPLETION_REVIEW.json');assert frozen_complete['passed'] and read(FP/'FINISHED.json')['passed']
assert read(X/'PLOT_INSPECTION.json')['actual_visual_inspection']
for x in read(X/'PLOT_INSPECTION.json')['plots']:assert x['inspected'] and sha(x['path'])==x['sha256']
for n,h in read(O/'PLAN.json')['source_hashes'].items():assert sha(D/n)==h
identities=observed['identities'];completed=[]
for j in identities:
 s=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==j['start']
for item in observed['dynamic']:
 j=item['job'];p=Path('/proc',str(j['pid']),'stat');s=p.read_text().rsplit(')',1)[1].split() if p.exists() else None
 if s is not None and s[0]!='Z' and s[19]==str(j.get('start',j.get('proc_start_ticks'))):continue
 receipt=Path(item['finished']);record=read(receipt);assert record['passed'];completed.append(dict(kind=item['kind'],pid=j['pid'],receipt=str(receipt),sha256=sha(receipt)))
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not list(O.glob('*FAILURE*')) and not (F/'REVIEW_FAILURE.json').exists() and not list(FP.glob('FAILURE*'))
progress={m:read(T/m/'train/PROGRESS.json') for m in prefix['methods']};frozen={m:(30 if (F/m/'FINISHED.json').exists() else read(F/m/'PROGRESS.json')['completed_conditions']) for m in progress}
for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(s) for s in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(D/'PREFIX_PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=identities,normal_frozen_completions=completed,progress93=progress,frozen90=frozen,gpu=gpu,goal='active',automatic94=False))
files=set()
for folder in (D,O):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.npz','.png'} and p.stat().st_size<10_000_000:files.add(p)
for n in ('LAUNCH.json','MONITOR_LAUNCH.json','PRELAUNCH_REVIEW.json','startup/REVIEW.json'):files.add(T/n)
for m in progress:
 for n in ('REGISTRATION.json','train/EXECUTION.json','train/PROGRESS.json'):files.add(T/m/n)
 for n in ('PROGRESS.json','STARTUP_REVIEW.json','FINISHED.json'):
  if (F/m/n).exists():files.add(F/m/n)
for n in ('LAUNCH.json','REVIEW_LAUNCH.json'):files.add(F/n)
for n in ('PROCESS.json','LAUNCH_BINDING.json'):files.add(FP/n)
for p in F.rglob('*.json'):
 if len(p.relative_to(F).parts)<=2:files.add(p)
files.add(F/'frozen_full30_results.png')
for folder in [FP,B/'runs/parameter90_violation_frozen_saved_audit_20261030_v1']:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.py','.json','.diff'}:files.add(p)
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_TERMINAL92_ONLINE93_20261031'/n)
for m,e in read(O/'PLAN.json')['methods'].items():files.add(Path(e['baseline_values']));files.add(Path(e['baseline_review']))
for p in [B/'runs/violation92_terminal_census_20261031_v1/SAVED_REVIEW.json',B/'runtime/violation92_terminal_census_20261031_v1/FROZEN_I_COMPLETION.json',B/'runtime/violation92_terminal_census_20261031_v1/FIXED92_FOLLOWUP_REFERENCE.json',B/'runtime/violation93_continuation_20261031_v1/SCIENTIFIC_DECISION.json']:files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Fixed actual93 first5000 original bytes/scalars/actual plot with preserved path failure; all8263 fixed92 followup baseline arithmetic/actual partial93 rejection/27 metadata rejects, one finite waiter and300s live progress. Original frozen90 all90/full-state/raw98391200/paired88-90/actual plot complete. Complete93 pending.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for m in tar.getmembers():assert tar.extractfile(m).read()==(E/m.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={m:v['steps'] for m,v in progress.items()};table='\n'.join(f"| {m} | {x['stats']['agent_train/q_loss']['first1000']:.9f} → {x['stats']['agent_train/q_loss']['last1000']:.9f} | {x['stats']['agent_train/q_loss']['maximum']:.9f} | {x['stats']['agent_train/actor_loss']['first1000']:.9f} → {x['stats']['agent_train/actor_loss']['last1000']:.9f} |" for m,x in prefix['methods'].items())
report=f'''# 第93轮前5000与固定终端后续；冻结90全部评测审查完成（2026-10-31）

原第93轮持续训练，固定前5000 loss仍有尖峰，尚未收敛。全部8263固定92终端后续已登记、真实partial93与缺完整93拒绝检查通过，唯一有限等待器已启动；它只在原完整93归档审查通过后执行零更新诊断，无自动94/Direct34。

原冻结90全部90评测、完整learner/replay不变、全部98391200原始子步审计和88→90配对已完成，实际结果图已查看。所有原冻结evaluator/collector/postprocessor正常结束，勿重启；训练93和固定终端等待器继续。

主机 `{socket.gethostname()}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，遵循仓库sii-research-sync，无子agent。当前源码 `{D}`，后续结果 `{O}`，固定前缀 `{X}`；原训练 `{T}`、完整归档消费者 `{B}/runtime/violation93_review_20261031_v1`。seed、版本、源/MJB和checkpoint hash保留原登记。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。

## 固定前5000

在读取loss值前固定三路各前5000真实更新；按完整92实际父steps3811512/3815000/3816000逐步号检查，update_index均0，原optimizer前缀字节精确。全部字段有限、critic非负，保存NPZ逐字段与原前缀精确，math.fsum独立复核首末1000/全5000均值与极值；实际六栏图已查看并SHA绑定。

| 方法 | critic首1000→末1000 | critic最大 | actor首1000→末1000 |
|---|---:|---:|---:|
{table}

I仍有密集尖峰、actor均值上移；A中段critic抬升/尖峰、actor局部近似平稳；V间歇尖峰且末1000均值高于首1000。仅早期prefix，不能代替完整reward/loss稳定性或因果改善。完整92原结论和全部失败窗口保持。

首版prefix脚本的文本替换误把父92 review路径改成不存在的93 review，FileNotFoundError发生在读取optimizer前缀前。原source、原PLAN和空输出目录保留；v2仅修正两个父路径并使用新输出目录，失败/修复hash和diff已保存。未改变训练、模型或研究协议，不隐藏该软件失败。

## 固定92后续

精确绑定完整92全部8263终端：I2755/A2754/V2754，原observations52/actions/rewards/masks及全部五critic预测不变，包括79/90/92中止。原保存masked/all-row SSE算术预检通过；真实缺完整93被拒绝。三份不可变startup93 checkpoint实际验证准确父steps、双架构marker、完整52维及4m/23/47历史标记；全部实际partial均拒绝作complete，27个错误metadata/partial边界反例拒绝。此阶段0新physics、0optimizer update、0新neural forward。

新比较器在真实完整93后要求完整review/health/loss一致、精确checkpoint SHA、complete_condition_cycle、完整93周期历史；固定92的全部终端索引/current52/actions/reward/masks与新回放前缀逐位核对，再恢复完整learner/Adam/RNG计算all5。计算前后完整learner/replay/RNG及磁盘checkpoint不变验证；保存全行92/93预测，独立保存算术审查和图，保留每critic退化及三条中止变化，不以挑选子集替代全队列。这些后续计算尚未执行，不声称已有93终端结果。

唯一等待器PID `{read(O/'PROCESS.json')['pid']}`，原archive monitor729497/start578235463绑定，截止 `{read(O/'PLAN.json')['wait_deadline_unix']}`（原monitor启动+14400秒），不延长；原完整93归档后诊断预算1800秒，保存算术300秒。实际图仍需完成后查看。固定队列是解释loss的诊断，不追加为数值收敛门槛，也不证明策略安全/泛化。

## 在途与约束

本轮连续{observed['elapsed_s']:.3f}秒/{observed['samples']}样本，原{len(identities)}个训练/archive/固定终端等待/90sampler/guard身份保持，三路steps增长；保存steps `{steps}`。冻结90进程按原PID/start核对，正常结束以各完整收据确认，动态正常结束记录 `{completed}`。冻结完成 `{frozen}`；原evaluator/collector/postprocessor全结束且收据核验。原阻抗冻结30中29完整+1在614动作/24.56秒安全中止保持，不能写成全30成功。

## 冻结90全部结果

同原30训练条件、外部动作seed2026102638：I/A/V Task分别17/15/17、Strict16/15/16，mean reward分别−4.332399381/−6.792978865/−4.576672118；机器安全违规回合数2/0/1。I有29完整回合，A/V各30完整；全部122989动作、98391200子步，0optimizer updates，完整learner/replay最终内存证明通过。

原raw auditor按全部90条件核对实际原始hash、dt5e−5、逐关节峰矩、实际人体接触分母、工程阈值下合规时长、外部穿透及原reward公式，最大reward重建误差2.842170943e−14。原动作/filter/torque审查收据保持；这是保存轨迹审计，不是独立动力学重跑，也没有在evaluator退出后再计算一次已释放内存digest。最终保存summary与全部raw审计行、配对结果逐组复核，实际图SHA绑定。

与冻结88配对：I mean reward−1.958963614，long0000失去Task/Strict并安全中止；A mean+.076426122但Task16→15、Strict15→15，long0900获Task/Strict、short0600获Strict、short0900与long0300失去Task/Strict；V mean−1.705101673，Task17→17、Strict17→16，short0600失去Strict。全90配对与失败保留，不只报告净计数。I short0600外部穿透.219463635mm，V同条件.200654869mm，均超过原.2mm门；I long0000全局目标物体/台面安全中止，external .111942929mm，不能因external低于门而抹去全局失败。

原训练条件单一外部动作seed的描述性配对包含额外训练曝光和critic修订，不是独立训练seed、未见条件、因果改善或最终SPT/指定ESN比较；工程人体阈值不能声称已验证人体舒适性。完整93及固定92终端对照仍待，原90–92稳定性失败不被这些评测覆盖。

原critic/replay52、actor49/canonical48信息、clock49/history50/bit51及已学权重、Adam/RNG、双marker、append-only4m replay与23/47历史marker保持；terminal128、batch65536、UTD1、原LR/reward/masks、30×55秒/最多41250每方法原预算不变。冻结physics/MJB、Task/Strict gate、filter/执行器/dt5e−5不变，无离线权重推广或自动94。原90–92 I/A失败、V reward-only通过及所有历史失败保留。

Direct33原数值验收与冻结全30 Task/Strict0/0、旧28缺最终内存证明/恢复2完整不变保持，不追加Task成功为数值收敛要求、不为占用训练34。指定ESN仍缺，不替换其他主机模型。partial75、不可评74–76、79/90/92安全中止、halfstd拒绝、全部软件失败保持。Goal active。

原guard97370/97399–97402继续，threshold50/target70/min duty.7，科学完成仍保活，非重启服务。本轮{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末值{gpu['last']}%。含synthetic guard，不等于科学吞吐或每瞬时保证，旧低谷保留。

共享SSD `{archive}`：{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐tar成员字节/AST核验；manifest在 `docs/evidence/{TAG}/MANIFEST.json`，index/commit逐字和实际远端push收据在 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。大checkpoint/replay/raw仍SSD，HDD配额满，仅现有254字节LATEST原地更新并回读，非HDD/arm1全备份。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 第93轮前5000/固定终端等待；冻结90全部审查完成

- [交接](docs/{TAG}.md)。固定first5000原字节/保存算术/实际六栏图通过；critic首末I1.416558→1.376017、A1.080119→1.091732、V.762984→.803952，最大15.038/2.379/2.838，I密集尖峰与actor上移保留，非收敛。首版父路径失败原件保留，v2仅修路径。
- 全8263固定92/all5/原masks算术预检、实际partial93拒绝和27metadata反例通过；唯一等待器{read(O/'PROCESS.json')['pid']}沿原archive截止，完整93后零更新比较，尚无93终端结果/自动94/Direct34。原训练{observed['elapsed_s']:.3f}s/{len(identities)}身份保持，steps{steps}。
- 原冻结90全90/98391200子步/full-state/raw/88→90配对与实际图完成，Task/Strict17/16、15/15、17/16；I长0000安全中止与I/V短0600违规保留，所有原冻结进程正常结束勿重启。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束仍守护。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份；main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。Goal active，无子agent，Direct原结论/指定ESN缺失保持。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps,frozen=frozen)))
