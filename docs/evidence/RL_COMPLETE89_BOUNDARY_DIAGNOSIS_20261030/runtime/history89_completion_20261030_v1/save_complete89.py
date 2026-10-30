from pathlib import Path
import ast,hashlib,json,os,socket,tarfile,time
D=Path(__file__).resolve().parent;B=D.parents[1];R=B/'repository/SII_compliance'
T=B/'runs/parameter_history_cycle89_20261030_v1';V=B/'runs/parameter_history_cycle89_review_20261030_v1';F=B/'runs/parameter88_history_frozen_full30_20261030_v1';O=B/'runs/history89_fixed87_terminal_followup_20261030_v1'
TAG='RL_COMPLETE89_BOUNDARY_DIAGNOSIS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
full=read(V/'REVIEW.json');assert full['passed'] and read(D/'WATCH_REVIEW.json')['passed'] and read(D/'BOUNDARY_AND_CONTRIBUTORS_REVIEW.json')['passed']
assert read(D/'INTERPRETATION.json')['passed'] and read(O/'REVIEW.json')['passed']
for folder in (V,O):
 for item in read(folder/'PLOT_INSPECTION.json').get('plots',[]):assert sha(Path(item['path']))==item['sha256']
identities=[]
for pid,start in [(97370,'570509460'),(97399,'570509475'),(97400,'570509475'),(97401,'570509475'),(97402,'570509475'),(2675653,'575369491'),(2675660,'575369492'),(2675662,'575369492'),(2675665,'575369492'),(2713409,'575376596')]:
 p=Path('/proc',str(pid));s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z' and s[19]==start
 identities.append(dict(pid=pid,start=start,command=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode()))
assert not Path('/tmp/sii_gpu_util_guard_20261030_v7/STOP').exists()
frozen={};training={}
for m in full['methods']:
 training[m]=read(T/m/'train/FINISHED.json');assert training[m]['status']=='stopped_at_complete_cycle'
 frozen[m]=read(F/m/'PROGRESS.json');assert not (F/m/'FAILURE.json').exists()
 p=Path('/proc',str(frozen[m]['physics_pid']));s=(p/'stat').read_text().rsplit(')',1)[1].split();assert s[0]!='Z'
 identities.append(dict(pid=int(p.name),start=s[19],command=(p/'cmdline').read_bytes().replace(b'\x00',b' ').decode()))
rows=[]
for line in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 if r['time']>=read(D/'WATCH_PLAN.json')['time']:rows.append(r)
assert rows and time.time()-rows[-1]['time']<25
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
gpu=dict(samples=len(rows),minimum=[min(r['gpus'][i]['utilization'] for r in rows) for i in range(4)],below50=[sum(r['gpus'][i]['utilization']<50 for r in rows) for i in range(4)],last=[r['utilization'] for r in rows[-1]['gpus']],synthetic_guard_included=True)
put(D/'SAVE_SNAPSHOT.json',dict(time=time.time(),host=socket.gethostname(),identities=identities,training89=training,frozen88=frozen,gpu=gpu,goal='active',automatic90=False,offline_fit_registered=False,full_stability_statistics_evaluated=False))
files=set()
for folder in (D,V,O,B/'runtime/history89_prefix_followup_20261030_v1',B/'runtime/history89_review_20261030_v1'):
 for p in folder.rglob('*'):
  if p.is_file() and p.suffix in {'.py','.json','.jsonl','.diff','.npz','.png'} and p.stat().st_size<10_000_000:files.add(p)
for m in full['methods']:
 for p in (T/m/'PROTOCOL.json',T/m/'train/FINISHED.json',T/m/'train/PROGRESS.json',F/m/'PROGRESS.json'):
  if p.exists():files.add(p)
 for p in (B/'runs/parameter_history_cycle89_archive_20261030_v1'/m).glob('*.json'):files.add(p)
for folder in (T,B/'runs/parameter_history_cycle89_archive_20261030_v1'):
 files.update(folder.glob('*.json'))
for p in (F/'LAUNCH.json',F/'REVIEW_LAUNCH.json',B/'runs/parameter_history88_90_reward_stability_20261030_v1/PLAN.json',B/'runtime/history89_continuation_20261030_v1/SCIENTIFIC_DECISION.json'):
 files.add(p)
for name in ('RECEIPT.json','PUBLICATION.json'):files.add(B/'repository/RL_HISTORY89_STABILITY_READY_20261030'/name)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(files=manifest,scope='Complete89 reviews, all90 pair, fixed87 terminal predictions/all5/SSE decomposition, raw boundary review, original failed window and live GPU/frozen observations. Large checkpoints/raw remain shared SSD; not full HDD/arm1 backup.'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
 for p in sorted(E.rglob('*')):
  if p.is_file():tar.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive) as tar:
 assert len(tar.getmembers())==len(manifest)+1
 for member in tar.getmembers():assert tar.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),host=socket.gethostname(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_tar_members_and_python_ast_verified=True,initial_main='9207ff427aa1c90e6e27926dbe86c8a3943e4f0e',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',backup_scope='Shared SSD, HDD254-byte pointer only; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
text=f'''# 完整89、稳定性失败及边界诊断交接

2026-10-30 UTC，Goal active。第89轮三方法及archive/full review/固定87终端跟踪全部正常完成；原冻结88与GPU v7保持程序继续。**未收敛，90未决定、未登记、未启动，Direct34未启动。** 原训练PID3433021–3433023、archive3433024、固定终端等待4055969已正常结束，不要重启。

主机 `{socket.gethostname()}`；共享SSD `{B}`；解释器 `{B}/env/bin/python`。前序见[89稳定性准备](RL_HISTORY89_STABILITY_READY_20261030.md)。本轮计算源码 `{D}`；完整训练 `{T}`；准确完整checkpoint `{B}/runs/parameter_history_cycle89_archive_20261030_v1/<method>/cycle_00089.pt`；完整审查 `{V}`。

| 方法 | 完整steps | mean reward | Task /30 | Strict /30 | checkpoint SHA256 |
|---|---:|---:|---:|---:|---|
'''
for m,x in full['methods'].items():text+=f"| {m} | {x['steps']} | {x['reward_mean']:.12f} | {x['task']} | {x['strict']} | `{x['checkpoint_sha256']}` |\n"
text+=f'''
三方法各30×55s、41250新transition/update、0abort；旧10,948,698行全部精确保留，新总计11,072,448行。全新51维current/next、raw→mixed动作及所有reward复算误差0。原history51 critic/replay、actor49隔离、学习权重和Adam、容量4m及历史23/47标记、LR/reward/masks/terminal128/batch65536/UTD1保持。全state/恢复与前缀审计详见原89启动证据；本轮没有重复迁移。

critic首1000→末1000 mean：I1.850637334→1.906305303（max36.066699982），A1.193332950→1.292978051（max18.906759262），V.777596097→.867219645（max60.554065704）。全部loss有限但末段均值上升、尖峰仍在；actor缓慢漂移。固定早期5000结果只是前缀，不能替代完整41250记录。health/loss/训练全90配对/固定终端四张图已实际查看，各自PLOT_INSPECTION绑定hash。

完整88→89全部90条对照见 `{D}/INTERPRETATION.json` 与 `training88_89_all90.png`。I mean变化+0.014952281，无Task/Strict标签变化；A−6.787970094，Task丢失short0300/long0200/long0900，Strict还丢失short0600；V−1.786483825，仅Strict丢失short0600。无新增通过条件。A/V终端reward项分别贡献−6.666666667/−1.666666667，仅算术分解，非策略因果归因。

原88—90窗口PLAN不变：seed2026102861、5000bootstrap、nearzero1、相邻5%。88→89相对变化I0.629%、A130.492%、V63.462%；A/V已经违反必要条件，任何90结果都不能逆转原窗口失败。I仍不能声称完整窗口通过。`EARLY_WINDOW_FAILURE.json`保留原PLAN/hash；没有全三周期统计、bootstrap或新替换窗口。不能为凑窗口盲目启动90。

固定原87终端跟踪 `{O}` 全部I2605/A2604/V2604行、all5/原masks/原始87 initial_control及已保存88预测保持。89恢复后0update/0physics，learner/RNG/checkpoint不变。89−88 masked SSE（critic0..4）：I[95.687190,−2782.676920,365.106803,9288.196479,2975.999834]；A[180.185950,−356.711810,80.752865,−583.498667,−106.861038]；V[−44.237431,−9.890996,6.600121,67.447710,105.707614]。相对原87，V全部5仍改善，I c3/c4及A c0/c2退化。所有critic/行保留，未晋升离线拟合权重。

`FIXED87_SSE_CONTRIBUTORS.json`精确分解所有行/5critic，top10仅解释。I c3最大退化原row195208，reward−28.35566、history .504114，Q88−27.40384→Q89+22.41979，单项SSE增加2577.24；其他几个大项也刚超过history .5。这支持研究“显式已知穿透违规标志能否更稳拟合”的假设，尚非证实根因。

新可复现 `review_boundary.py` 核验冻结adapter/evaluator源hash：raw累计外穿透≤.0002m，无额外容差，Strict还依赖Task/abort/未知边缘等门。全10,824,948原87 sidecar行及7813终端精确核对；本数据中raw>.0002与float32 history>.5分歧为0。数学反例nextafter(.0002,+∞)说明float32特征可能舍入成.5；若后续诊断新增标志，应从**动作前raw累计穿透>.0002**计算，而非舍入特征阈值。该标志不是最终Strict标签，不可泄漏未来；没有证据认为本次退化由舍入造成。保存SSE全部总和/正负数/解释行已独立复算，0新forward/update/physics。

下一步候选是单独登记有限配对离线critic拟合：准确完整89，两臂相同52维模型及新零列/零Adam矩，控制臂新增输入0，候选臂原始因果违规位；原51权重/Adam均保留，同固定87全终端/原masks/all5/三方法，有限步数，无actor/alpha/target更新、无物理、无权重推广。**目前仅候选，未登记或运行，也未实现52维正式架构。** 必须先绑定完整89与全部输入/源/预算、验证插入列51及动作列移位/初始预测/Adam/RNG；不能直接复用旧50→51迁移。

原冻结88 `{F}`：当前保存完成数 `{ {m:x['completed_conditions'] for m,x in frozen.items()} }`，具体condition/action/物理PID及start见SAVE_SNAPSHOT。evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409原身份保持；原21600s截止，不延长/重复派发。最终全90、最终内存不变、raw审计及82→88全90配对仍待。保留所有早期失败。

原v7 supervisor97370与worker97399–97402身份保持，阈值50%、目标70%，无STOP，科学任务结束也继续运行。本轮{gpu['samples']}采样min `{gpu['minimum']}`%，低于50次数 `{gpu['below50']}`，末值 `{gpu['last']}`%；包含合成负载，单独记录，非科研吞吐或每瞬时保证。历史v7预热0与v6 31/33/44低谷全部保留；不是重启自启服务。

本轮实际query/fetch/read main9207ff427aa1c90e6e27926dbe86c8a3943e4f0e及baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，无新远端科学改动。按sii-research-sync发布，无子agent。共享SSD包 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；tar逐字及Python AST已核，index/commit逐字核验另见包外收据，成功push与真实ls-remote后才写PUBLICATION。大checkpoint/raw仍原SSD；HDD仅254字节原位指针，非HDD/arm1全备份。

Direct33数值接受但冻结30 Task/Strict0/0；Direct28中断缺最终内存不变证明。指定ESN仍缺失，不重复询问或替用其他主机模型。partial75、74—76不可判、79安全中止、全部失败稳定性窗口、halfstd拒绝及软件失败保持。完整reward稳定、loss健康、最终冻结评测与原ESN比较尚未完成，Goal active。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整89与边界诊断已审；原88—90 A/V稳定性失败

- [交接](docs/{TAG}.md)。89三路正常完成，各30×55/41250/0abort，全旧replay及新51映射/reward0误差；Task/Strict18/17、13/12、17/16，mean−2.360402/−11.989807/−4.601530。完整loss末段均值上升/尖峰，全90配对A丢4 Strict、V丢1，无新增通过；四实际图已查看，未收敛。
- 原88→89 A130.492%/V63.462%已违反5%必要条件，保留原失败窗口，无完整三轮/bootstrap、无90/Direct34。固定87全部终端/all5已跟踪89，Icritic3退化突出；全SSE解释算术和10,824,948 raw历史边界核验通过，现存舍入判定分歧0。显式因果违规位离线拟合仅候选，未登记/运行/晋升。
- 原89/archive/固定终端等待正常结束勿重启；冻结88完成数{ {m:x['completed_conditions'] for m,x in frozen.items()} }，原evaluator/collector/postprocessor继续，最终全90/raw/paired待。GPU{gpu['samples']}采样min{gpu['minimum']}%、低于50{gpu['below50']}，科学结束继续保载，非科研吞吐。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份；main9207ff42/baselinef6e8f8c已query/fetch/read，发布见收据，无子agent，Goal active。

'''
for name in ('UPDATE_LOG.md','HANDOFF.md'):
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<254;data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(dict(receipt=receipt,gpu=gpu,frozen={m:x['completed_conditions'] for m,x in frozen.items()})))
