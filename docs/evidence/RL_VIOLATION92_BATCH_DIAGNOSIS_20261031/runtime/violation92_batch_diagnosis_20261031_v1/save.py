from pathlib import Path
import ast,hashlib,json,os,socket,subprocess,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
O=B/'runs/violation92_frozen_batch_diagnosis_20261031_v1';F=B/'runs/parameter90_violation_frozen_full30_20261030_v1'
TAG='RL_VIOLATION92_BATCH_DIAGNOSIS_20261031';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with Path(p).open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
review=read(O/'SAVED_REVIEW.json');spike=read(O/'SPIKE_SOURCE_REVIEW.json');plan=read(O/'PLAN.json')
assert review['passed'] and spike['passed'] and read(O/'FINISHED.json')['passed']
plot=O/'native_batch_decomposition.png';assert sha(plot)==review['plot_sha256']
put(O/'PLOT_INSPECTION.json',dict(time=time.time(),actual_visual_inspection=True,plots=[dict(path=str(plot),sha256=sha(plot),inspected=True)],findings=['I batches21/41 show terminal-dominated spikes near7.7; nonterminal contribution remains near1.2.','A and V vary within approximately .90–1.39 and .51–1.06; no historical large spikes reproduced in these64 draws.','All ten unordered target pairs shown with unequal counts. Pair0/1 co-occurrence is not causality: the dominant terminal target equals reward.'],scope='Actual image viewed; source and saved arithmetic independently checked. Not historical online spike replay.'))
put(D/'INTERPRETATION.json',dict(time=time.time(),passed=True,source_review_sha256=sha(O/'SAVED_REVIEW.json'),source_spike_review_sha256=sha(O/'SPIKE_SOURCE_REVIEW.json'),finding='Both I frozen spikes are dominated by original90 global-safety-abort terminal index3726050; its external violation bit is0.',decision='Preserve full92 checkpoint and original protocol. Next bounded investigation should quantify all current terminal fitting errors, including abort79/90/92, and distinguish sampling concentration from missing causal information before a new online cycle is registered.',not_proven=['Historical online spike cause','Irreducible observation aliasing','A/V spike disappearance','Joint healthy convergence'],no_automatic93=True,optimizer_updates=0,new_physics=0,excluded_rows=0))
raw=[]
for method in plan['methods']:
 result=read(O/method/'REVIEW.json');assert result['passed'] and result['first_batch_exact_repeat'] and result['full_learner_optimizer_replay_rng_restored']
 assert result['optimizer_updates']==result['new_physics']==result['backward_calls']==0
 rows=read(O/method/'RAW_MANIFEST.json')['files'];assert len(rows)==64
 for x in rows:
  p=Path(x['path']);assert p.stat().st_size==x['bytes'] and sha(p)==x['sha256'];raw.append(x)
assert len(raw)==192
put(D/'RAW_STORAGE_REVIEW.json',dict(passed=True,time=time.time(),files=len(raw),bytes=sum(x['bytes'] for x in raw),manifest_refs=[dict(path=str(O/m/'RAW_MANIFEST.json'),sha256=sha(O/m/'RAW_MANIFEST.json')) for m in plan['methods']],all192_size_sha256_verified=True,location=str(O),scope='Raw NPZ remain shared SSD, excluded from Git and small-evidence tar.'))
identities=[]
fp=B/'runtime/violation90_frozen_postprocess_20261030_v1'
jobs=read(F/'LAUNCH.json')['jobs']+[read(F/'REVIEW_LAUNCH.json'),read(fp/'PROCESS.json')]
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475')]+[(j['pid'],j['start']) for j in jobs]:
 p=Path('/proc',str(pid));s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==str(start);identities.append(dict(pid=pid,start=s[19],state=s[0]))
frozen={m:read(F/m/'PROGRESS.json') for m in plan['methods']}
assert not list(O.glob('*FAILURE*')) and not (F/'REVIEW_FAILURE.json').exists() and not list(fp.glob('FAILURE*'))
for m in plan['methods']:assert not (F/m/'FAILURE.json').exists()
guard=Path('/tmp/sii_gpu_util_guard_20261030_v7');assert not (guard/'STOP').exists()
rows=[json.loads(x) for x in (guard/'samples.jsonl').read_text().splitlines()];rows=[x for x in rows if x['time']>=plan['time']];assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in rows))
gpu=dict(samples=len(rows),elapsed_s=rows[-1]['time']-rows[0]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in rows) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in rows) for i in range(4)],last=[x['utilization'] for x in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=identities,frozen90=frozen,gpu=gpu,training92_completed=True,batch_diagnosis_completed=True,goal='active',automatic93=False))
files=set()
for folder in (D,O):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.png'} and 'raw' not in p.relative_to(folder).parts:files.add(p)
for p in F.rglob('*.json'):
 if len(p.relative_to(F).parts)<=2:files.add(p)
for n in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_COMPLETE92_20261031'/n)
for x in spike['sources']:
 p=Path(x['path'])
 if p.name!='transitions.jsonl':files.add(p)
files.add(B/'runtime/violation92_completion_20261031_v1/ABORT_REVIEW.json')
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Full92 frozen native batches, exact repeat/full-state invariance, independent saved arithmetic, source trace and actual inspected plot. All192 raw NPZ stay shared SSD with verified manifests.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for item in tar.getmembers():assert tar.extractfile(item).read()==(E/item.name).read_bytes()
remote=read(D/'REMOTE_START.json');receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main=remote['main'],baseline=remote['baseline'],raw_npz_files=len(raw),raw_npz_bytes=sum(x['bytes'] for x in raw),raw_npz_in_tar=False,backup_scope='Shared SSD; existing254-byte HDD pointer only, not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
counts={m:x['completed_conditions'] for m,x in frozen.items()}
result_rows='\n'.join(f"| {m} | {x['summary']['mean']:.9f} | {x['summary']['minimum']:.9f}–{x['summary']['maximum']:.9f} | {x['summary']['mean_terminal_loss']:.9f} | {x['summary']['mean_nonterminal_loss']:.9f} |" for m,x in review['methods'].items())
report=f'''# 第92轮冻结原生batch尖峰诊断（2026-10-31）

完整92模型冻结、每方法64个原生65536 batch、零梯度/优化器更新，阻抗两次尖峰追溯到第90轮同一安全中止终端。最大批中该行贡献85.5224%的loss。这是罕见失败终端拟合/采样集中的直接证据，不是全部历史在线尖峰的因果复现，也不是已解决或不可约表示误差的证明。Goal active，原冻结90继续，无自动93/Direct34。

## 来源与执行

主机 `{socket.gethostname()}`，共享SSD根 `{B}`，解释器 `{B}/env/bin/python`。按仓库同步skill实际query/fetch/read main `{remote['main']}`、baseline `{remote['baseline']}`，恢复后再次核验未变。源 `{D}`，结果 `{O}`。原完整92 checkpoint/hash、登记、版本、完整恢复源843项依赖绑定在PLAN；源与首次抽样起始RNG均保存。原92训练完成勿重启。

按PLAN，GPU1/2/3、CPU11/12/13、每方法1800秒上限，原生replay类/device cache/接受mask抽样/target pair及策略抽样/原投影。每批所有实际字段均与独立索引见证精确匹配，原生loss在q_optimizer.zero_grad之前捕获并停止，禁止step/target写入。每路首批重放逐位精确，完整learner/Adam/replay/RNG最终恢复、原checkpoint hash不变。保留全部192批，各65536行；零backward、optimizer update及新物理步。

后续冻结抽样没有消费原训练中actor/update使用的随机数，因此不是历史在线尖峰或下一轮训练序列重放。原FINISHED与SAVED_REVIEW中的查看待办是写入时状态；后续实际查看证据在PLOT_INSPECTION，不改旧收据。

## 全部结果

| 方法 | mean loss | min–max loss | 平均终端贡献 | 平均非终端贡献 |
|---|---:|---:|---:|---:|
{result_rows}

独立review重新读取全部192 NPZ，核对大小/SHA、原生float32 loss与float64算术（rtol3e−6/atol1e−6）、各critic真实加权分母、terminal/nonterminal、old/new92、bit0/1分组和top20。全部10种无序target pair均出现，次数不等。实际六栏图已查看且SHA绑定。

阻抗回放index3726050（全局transition step3726051）准确绑定到原cycle90/active_long_train_0000最后一步：877动作/35.08秒，全局穿透97.912589mm、external .046985938mm、bit0、done=true。stored reward与terminal target均为−37.7925643921，原journal float64为−37.7925657369。当前五critic预测约[−3.953916,.960974,−16.629107,−7.943429,−16.582642]，mask=[1,0,1,1,1]。

全部64批只有batch21/41包含此行。两批loss7.6586174965/7.6877813339，该行按不变全批分母贡献6.5068629483/6.5747751471；其他贡献1.1517541255/1.1130059555。其余62批loss范围1.0408611298–1.4884867668。全64原批均保留，没有移除样本、改变分母或另跑排除失败的训练。两尖峰恰与pair0/1同时出现，但该terminal target等于reward、不依赖target pair，因此不能把pair相关当原因。

导纳/VMC这64批没有复现原在线大尖峰，有限未复现不等于已消失；其最大批top行未追溯到原始回合，不作来源断言。

## 科学决定与未完成

这次证据优先指向罕见失败终端的拟合和抽样集中。下一有限诊断应审完整92全部终端（包含79/90/92安全中止），量化误差集中程度并核对现有因果信息是否足够，再单独登记下一在线轮的科学决定。当前不改LR、reward、masks、terminal128、batch65536、UTD1、4m append-only历史23/47标记或网络；不导入离线拟合权重。

critic/replay52、actor49、clock49/history50/raw violation51和已学权重/Adam/RNG/双架构标记保持；canonical48、冻结physics/MJB/Task与Strict gate/filter/执行器/dt5e−5保持。原90–92阻抗/导纳reward条件失败、VMC仅reward条件通过，全三路联合loss健康收敛仍未成立。原固定87 masked SSE的VMC退化及全部critic退化保留。

Direct33原数值验收保持；冻结33全30 Task/Strict0/0、旧28缺最终内存证明和恢复2完整不变均保留，不把Task成功追加为数值收敛门槛。指定ESN仍缺，不替换他机模型。partial75、不可评74–76、安全中止79/90/92、halfstd拒绝及全部旧失败窗口/软件失败均保留。本诊断无软件失败。

## 在途运行与恢复

保存时原冻结90完成 `{counts}`（各30）；原三evaluator283421/283428/283430、collector283433、postprocessor292743存活且start identity核验，最终全90/raw/88→90配对/内存不变仍待。沿原截止，不重启/延长。

原guard supervisor97370、workers97399–97402身份核验，`/tmp/sii_gpu_util_guard_20261030_v7` threshold50/target70/min duty.7继续，科研结束也保活，不是重启服务。本次{gpu['samples']}样本/{gpu['elapsed_s']:.3f}秒，最小{gpu['minimum']}%、低于50次数{gpu['below50']}、末样本{gpu['last']}%。包含synthetic guard，不等于科研吞吐或每瞬时保证；历史warmup0/v6低样本保留。

共享SSD小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`，逐tar成员大小/字节和Python AST核验。192原NPZ共{receipt['raw_npz_bytes']}字节位于 `{O}/<method>/raw`，逐大小/hash重新核验，三份RAW_MANIFEST入Git，但raw目录不入Git或tar。大checkpoint/replay原始记录仍共享SSD。

本轮清单 `docs/evidence/{TAG}/MANIFEST.json`，index/commit核验与实际远端发布收据在 `{A}/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原地更新现有254字节LATEST指针并回读，非HDD/arm1全备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
'''
(R/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-31 — 完整92冻结原生batch尖峰来源已核验

- [交接](docs/{TAG}.md)。三路各64×65536、首批精确重复、完整learner/Adam/replay/RNG不变，0update/physics；全部192原批独立算术与实际图核验。I两尖峰由原90安全中止terminal index3726050主导，最大贡献85.52%，bit0；非历史在线尖峰因果复现、pair因果或修复证明。A/V有限未复现大尖峰不等于已解决，未收敛。
- 原92和诊断完成勿重启；下一步完整终端误差集中审查后单独科学决定，无自动93/Direct34。原冻结90继续，完成{counts}，最终全90/raw/paired待；全部历史失败/Direct原结论/指定ESN缺失保持。
- GPU{gpu['samples']}样本min{gpu['minimum']}%、低于50{gpu['below50']}，科研结束仍守护。SSD{receipt['members']}小证据成员/SHA{receipt['sha256'][:8]}核验，192raw NPZ仅SSD且逐hash核验；HDD仅254字节指针，非全备份。main{remote['main'][:8]}/baseline{remote['baseline'][:8]}实际query/fetch/read，发布见收据。Goal active，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,frozen=counts)))
