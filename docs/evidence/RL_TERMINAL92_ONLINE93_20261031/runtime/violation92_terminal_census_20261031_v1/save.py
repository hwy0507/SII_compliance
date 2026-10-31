from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance';O=B/'runs/violation92_terminal_census_20261031_v1'
P=B/'runtime/violation93_continuation_20261031_v1';Q=B/'runtime/violation93_review_20261031_v1';T=B/'runs/parameter_violation_cycle93_20261031_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1';FP=B/'runtime/violation90_frozen_postprocess_20261030_v1'
TAG='RL_TERMINAL92_ONLINE93_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
census=read(O/'SAVED_REVIEW.json');assert census['passed'] and read(O/'FINISHED.json')['passed']
for x in read(O/'PLOT_INSPECTION.json')['plots']:assert x['inspected'] and sha(x['path'])==x['sha256']
startup=read(T/'startup/REVIEW.json');observed=read(Q/'ONLINE_OBSERVATION_REVIEW.json');assert startup['passed'] and observed['passed'] and read(P/'PREFLIGHT_FINISHED.json')['passed'] and read(Q/'CONSUMER_PARENT_BOUNDARY_REVIEW.json')['passed']
identities=list(observed['identities'])+[read(F/'REVIEW_LAUNCH.json'),read(FP/'PROCESS.json')];frozen_finished={}
for j in read(F/'LAUNCH.json')['jobs']:
 path=Path('/proc',str(j['pid']),'stat');fields=path.read_text().rsplit(')',1)[1].split() if path.exists() else None
 if fields is not None and fields[0]!='Z' and fields[19]==str(j['start']):identities.append(j)
 else:
  method=j.get('controller',j.get('method'));assert method in census['methods'];finish=read(F/method/'FINISHED.json');assert finish['passed'] and finish['episodes']==30 and finish['full_learner_state_unchanged'] and finish['full_replay_state_unchanged'] and finish['initial_learner_digest']==finish['final_learner_digest'] and finish['new_optimizer_updates']==0;frozen_finished[method]=finish
for j in identities:
 fields=Path('/proc',str(j['pid']),'stat').read_text().rsplit(')',1)[1].split();assert fields[0]!='Z' and fields[19]==str(j.get('start',j.get('proc_start_ticks')))
for folder in (P,Q):
 for n,h in read(folder/'SOURCES.json')['files'].items():assert sha(folder/n)==h
assert not (T/'ARCHIVE_REVIEW_FAILURE.json').exists() and not (Q/'OBSERVATION_FAILURE.json').exists() and not (F/'REVIEW_FAILURE.json').exists() and not list(FP.glob('FAILURE*'))
progress={m:read(T/m/'train/PROGRESS.json') for m in census['methods']};frozen={m:read(F/m/'PROGRESS.json') for m in progress}
for m in progress:assert not (T/m/'DRIVER_FAILURE.json').exists() and not (T/m/'train/FAILURE.json').exists() and not (F/m/'FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=read(O/'PLAN.json')['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows));gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=identities,progress93=progress,frozen90=frozen,frozen_finished=frozen_finished,gpu=gpu,goal='active',automatic94=False))
files=set()
for folder in (D,P,Q,O):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.npz','.png'} and p.stat().st_size<10_000_000:files.add(p)
files.update(T.glob('*.json'));files.add(T/'startup/REVIEW.json')
for m in progress:
 for n in ('REGISTRATION.json','CHECK_ONLY_REVIEW.json','INITIAL_STATE_REVIEW.json','VIOLATION_EXECUTION.json','trainer_registered.py','check/INITIAL_STATE_REVIEW.json','train/EXECUTION.json','train/PROGRESS.json'):files.add(T/m/n)
 for n in ('PROGRESS.json','STARTUP_REVIEW.json'):files.add(F/m/n)
 for n in ('FINISHED.json','RESULTS.json'):
  if (F/m/n).exists():files.add(F/m/n)
for n in ('LAUNCH.json','REVIEW_LAUNCH.json'):files.add(F/n)
for n in ('PROCESS.json','LAUNCH_BINDING.json'):files.add(FP/n)
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_VIOLATION92_BATCH_DIAGNOSIS_20261031'/n)
for item in read(P/'SCIENTIFIC_DECISION.json')['evidence']:files.add(Path(item['path']))
if (D/'FROZEN_I_COMPLETION.json').exists():
 for item in read(D/'FROZEN_I_COMPLETION.json')['sources']:files.add(Path(item['path']))
for m,e in read(O/'PLAN.json')['methods'].items():
 for abort in e['known_aborts']:
  for source in abort['sources']:
   p=Path(source['path'])
   if p.name!='transitions.jsonl':files.add(p)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='All8263 full92 terminal census and independent saved/source/actual-plot review; finite unchanged93 registration, full92 restore,108 rejection controls,6 clone repeated updates, actual startup and120s live progression. Large replay/checkpoints/raw on SSD.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for m in tar.getmembers():assert tar.extractfile(m).read()==(E/m.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
counts={m:(30 if m in frozen_finished else v['completed_conditions']) for m,v in frozen.items()};steps={m:v['steps'] for m,v in progress.items()}
table='\n'.join(f"| {m} | {x['terminal_rows']} | {x['total_masked_sse']:.6f} | {100*x['top_k_fractions']['1']:.4f}% | {100*x['top_k_fractions']['2']:.4f}% | {100*x['top_k_fractions']['100']:.4f}% |" for m,x in census['methods'].items())
report=f'''# 完整92全部终端审查；同52协议有限93实际训练（2026-10-31）

全部8263终端普查完成，阻抗90/92两条安全中止贡献76.3184%的终端masked SSE。依据完整92、原生冻结batch和全终端证据，单独登记并实际启动一轮相同协议93，每方法最多41250新增。Goal active，未达到全部方法reward平稳且loss健康；无自动94/Direct34。原冻结90继续。

## 来源与恢复

主机 `{socket.gethostname()}`；共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮按仓库sii-research-sync实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，无子agent。诊断源码 `{D}`，结果 `{O}`；续训源码 `{P}`，消费者 `{Q}`，实际训练 `{T}`。版本、seed20261025、源/MJB hash和完整命令沿REGISTRATION/EXECUTION。

完整父92在 `{B}/runs/parameter_violation_cycle92_archive_20261030_v1/<method>/cycle_00092.pt`，精确SHA与原steps在各93 REGISTRATION。I/A/V父steps为3811512/3815000/3816000，I真实新增40562含安全中止，不能误作41250；新93首步3811513/3815001/3816001、最大末步3852762/3856250/3857250，均未越4m容量。原92和本次终端诊断已完成，不重启。

## 全部终端结果

原52观测、动作、reward、全部五critic和原masks，I2755/A2754/V2754终端全部保留。完整learner/Adam/replay/RNG不变，零optimizer update/physics。原固定87队列的观测/动作/reward/masks精确，全部旧预测与本次结果最大差均0。三份values NPZ保留所有输入和预测，独立保存算术重算分组/SSE/排名、三个安全中止原journal+rollout/TERMINAL绑定及实际图核验通过。

| 方法 | 终端数 | masked SSE总和 | top1占比 | top2占比 | top100占比 |
|---|---:|---:|---:|---:|---:|
{table}

阻抗cycle90 replay index3726050为第1名，SSE2933.777778，占59.8990%；cycle92 index3804982为第2名，SSE804.201953，占16.4194%；cycle79 index3264118为第16名，SSE10.589127，占.2162%。三者external bit均0，原全局目标物体/台面安全失败保持。90 mask=[1,0,1,1,1]；92 mask=[0,0,0,0,1]，唯一参与该行损失的critic4预测−9.531266，对应target−37.889721。保留其余未参与该行loss的预测，不能把masked拟合改善称为所有critic准确。

全五critic散点图显示未被mask选中时仍可能有大误差，A/V也保留该现象。旧79当前拟合好于90/92是不同记录在同一模型下的观察，不构成纵向学习改善、不可约表示错误或纯训练不足的证明。全回放加权终端贡献按真实全回放mask分母+127倍terminal mask计算，分别.188288177/.077552319/.032673478；这是全回放加权损失的终端部分，不是随机batch loss的数学期望。先前64批抽样结果、全部192原NPZ及所有历史尖峰均保留。

## 科学决定与正式93

完整92 I/A原90–92 reward条件失败，V只通过reward条件；全loss尖峰和actor漂移仍未解决。现在有直接证据表明I终端误差高度集中于新近安全失败，但不能证明已有表示无法拟合。选择一个有限93继续原生学习，跟踪固定92全部8263终端、三条中止、各critic退化及完整loss/30条件结果；如误差不降或加剧，复审学习干扰/表示问题，不盲目自动连续训练。

不改变采样、masks、terminal128、batch65536、UTD1、原LR/reward、critic/replay52、actor49/canonical48、clock49/history50/bit51、已学history/violation权重、Adam/RNG和两个架构标记。append-only4m与历史23/47标记不变。冻结physics/MJB、Task/Strict gate、filter/执行器/dt5e−5不变，无离线权重推广、无失败样本删除。原90–92方案与失败结论保留，不以移动窗口抹去原失败。

driver和审查消费者仅适配完整92→93边界；实际trainer与92逐字相同，health算法逐字相同，学习数值依赖逐字相同。三路共108个负例拒绝通过，涵盖错误周期/partial/预算/自动后续/marker/51维/回放cursor/capacity/优化器计数/LR；各2次原生batch65536 clone更新重复后全state恢复，共6次，0正式更新/physics。

实际startup新增步数 `{ {m:x['added_steps'] for m,x in startup['methods'].items()} }`，全部旧replay字段逐位相同，新52 current/next、raw bit/history/clock、raw→mixed action及所有新增reward重建误差 `{ {m:x['max_reward_reconstruction_error'] for m,x in startup['methods'].items()} }`。30MJB/30sampler及原CPU配置通过；这是保存journal审查，不是独立动力学重跑。

启动后实际观察{observed['elapsed_s']:.3f}秒、{observed['identity_count']}身份/{observed['samples']}样本保持、三路steps增长；保存时steps `{steps}`。原archive完整消费者按14400秒上限等待，完整checkpoint复制/hash后执行全回放/new reward/health/loss审查，实际完整图仍须查看。命令/PID/start在LAUNCH和MONITOR/STARTUP/OBSERVER_LAUNCH；先核验现有进程，禁止重复派发。

## 冻结评测、GPU与未完成

原冻结90 `{F}`、原三evaluator283421/283428/283430及collector283433、postprocessor292743按原PID/start核验；已正常结束的方法 `{list(frozen_finished)}` 以30回合FINISHED和全learner/replay不变收据核验，其余保持原进程。完成 `{counts}`/各30，最终全90/raw/88→90配对及其余方法完整内存不变仍待。沿原seed2026102638与launch+21600秒截止，零updates，不延长重启。完整93与后续固定92比较仍待，本轮不新增冻结93。

原冻结90的阻抗现已正常结束：Task17/30、Strict16/30，29完整回合加long0000在614动作/24.56秒全局穿透安全中止，共40489动作。失败和完整learner/replay不变收据、原rollout/TERMINAL来源均保存于FROZEN_I_COMPLETION；完成是指评测结束，不代表所有回合成功。该记录属于原90冻结评测，不是93训练新增失败。

Direct33原数值验收保持；冻结33全30 Task/Strict0/0，旧28缺最终内存证明、恢复2完整不变保持；不把Task成功追加为数值收敛要求。指定ESN仍缺，不替换其他主机模型。partial75、不可评74–76、79/90/92安全中止、halfstd拒绝及所有失败窗口/软件失败保持。

原guard supervisor97370/workers97399–97402继续，threshold50/target70/min duty.7，科研完成仍保活，不是重启服务。本轮{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，最低{gpu['minimum']}%、低于50次数{gpu['below50']}、末值{gpu['last']}%。包含synthetic guard，不等于科研吞吐或每瞬时保证；旧warmup0/v6低值保留。

## 保存

共享SSD `{archive}`：{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐tar成员字节和Python AST核验。清单 `docs/evidence/{TAG}/MANIFEST.json`；index/commit逐字和实际远端正常push收据在 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。原大checkpoint/replay/raw保留SSD；HDD配额满，仅原地更新254字节LATEST指针并回读，非HDD/arm1全备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 全部92终端已审；有限同协议93实际训练

- [交接](docs/{TAG}.md)。全部8263终端/all5/原masks及原79/90/92中止来源、保存算术和实际图核验，完整learner/Adam/replay/RNG不变。I90/92两条占masked SSE76.3184%，79占.2162%；非纵向改善/不可约/历史在线因果证明，A/V和未参与mask的critic误差保留。
- 据完整92与集中误差单独登记一轮93，每方法≤41250，实际trainer/数值协议不变；108负例、6原生batch clone重复恢复、实际startup旧replay/新52/action/reward0误差通过。{observed['elapsed_s']:.3f}s/{observed['identity_count']}身份保持，steps{steps}。完整93及固定92比较待，无自动94/Direct34；原90–92 I/A失败、V reward-only通过保持，未收敛。
- 原冻结90继续，完成{counts}，最终全90/raw/paired待。GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍守护。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，HDD仅254字节指针、非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。全部历史失败/Direct原结论/指定ESN缺失保持；Goal active，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,steps=steps,frozen=counts)))
