from pathlib import Path
import json,time,hashlib,ast,tarfile,socket,subprocess,os,datetime
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance'
TAG='RL_COMPLETE87_HALF_STD86_RUNNING_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
P=B/'runs/parameter86_half_std_paired_20261030_v3';S=B/'runs/parameter86_frozen_switches_20261030_v1'
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def state(j):
 for p in j['failure_paths']:assert not Path(p).exists(),p
 try:
  s=Path(f'/proc/{j["pid"]}/stat').read_text().rsplit(')',1)[1].split()
  if s[19]==str(j['proc_start_ticks']) and s[0]!='Z':return 'live'
 except FileNotFoundError:pass
 assert j['terminal_requirements'],j['name']
 for q in j['terminal_requirements']:assert read(q['path'])[q['key']]==q['value']
 return 'verified_terminal'
assert read(D/'WATCH_FINISHED.json')['all87_and_seeds_ready']
assert read(D/'PROBE_OBSERVATION_FINISHED.json')['passed']
assert read(P/'STARTUP_SAVED_AUDIT.json')['passed']
assert read(P/'STARTUP_SAVED_AUDIT.json')['all_unchanged_native_helpers_exact']
assert read(D/'SEEDS_RAW_SAVED_REVIEW.json')['passed']
ids=read(D/'PROBE_OBSERVATION_PLAN.json')['identities'];states={j['name']:state(j) for j in ids}
progress={k:read(P/k/'PROGRESS.json') for k in read(P/'PLAN.json')['groups']}
samples=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];samples=[x for x in samples if x['time']>=read(D/'PLAN.json')['time']];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples))
g=dict(samples=len(samples),start=samples[0]['time'],end=samples[-1]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
snap=dict(time=time.time(),host=socket.gethostname(),identities=ids,states=states,half_std=progress,guard=g,goal='active',automatic88=False,direct34=False)
put(D/'SAVE_SNAPSHOT.json',snap)
full=read(B/'runs/parameter_partial75_recovery_cycle87_review_20261029_v1/REVIEW.json');loss=read(B/'runs/parameter_recovery87_loss_20261029_v1/REVIEW.json');window=read(B/'runs/parameter_recovery85_87_reward_stability_20261030_v1/REVIEW.json');fix=read(B/'runs/recovery84_87_fixed_terminal_critic_followup_20261030_v1/REVIEW.json');seeds=read(S/'REVIEW.json')
assert all(not x['descriptive_five_percent_check'] for x in window['methods'].values())
for x in full['methods'].values():assert x['new_transitions']==41250 and x['full_horizon_count']==30 and not x['aborts'] and x['retained_replay_all_fields_exact'] and x['max_reward_reconstruction_error']==0 and x['optimizer_and_network_finite']
put(D/'INTERPRETATION.json',dict(passed=True,time=time.time(),complete87=full['methods'],window85_87=window['methods'],fixed2514=fix['methods'],seed_groups=seeds['groups'],decision='No unchanged automatic88. One registered fixed86 half-pre-tanh-std paired inference intervention running; review all16 before considering a separate training amendment.',no_convergence=True,no_automatic_promotion=True,training_entropy_state_not_serialized=True))
files=set()
allowed={'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz'}
def collect(folder,recurse=False):
 for p in (folder.rglob('*') if recurse else folder.iterdir()):
  if p.is_file() and p.suffix in allowed and p.stat().st_size<10_000_000:files.add(p)
collect(D)
for n in ['parameter_partial75_recovery_cycle87_review_20261029_v1','parameter_recovery87_loss_20261029_v1','parameter_recovery87_task_labels_20261029_v1','vmc_recovery87_terminal_followup_20261029_v1','admittance_recovery87_terminal_followup_20261029_v1','parameter_recovery85_87_reward_stability_20261030_v1','recovery85_87_bootstrap_scalar_review_20261030_v1','recovery84_87_fixed_terminal_critic_followup_20261030_v1']:
 collect(B/'runs'/n,True)
for n in ['parameter86_frozen_switches_20261030_v1','parameter86_half_std_paired_20261030_v1','parameter86_half_std_paired_20261030_v2','parameter86_half_std_paired_20261030_v3']:
 collect(B/'runtime'/n);o=B/'runs'/n;collect(o)
 for k in read(o/'PLAN.json')['groups']:collect(o/k)
for m in full['methods']:
 for n in ['REGISTRATION.json','LAUNCH.json']:
  p=B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}'/n
  if p.exists():files.add(p)
 for n in ['FINISHED.json','PROGRESS.json']:
  files.add(B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train'/n)
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_FROZEN82_COMPLETE87_PROGRESS_20261030'/n)
for n in ['published_cheq/agents/rl/sac_ensemble.py','source/tools/published_compliance_learner_20261025.py','source/tools/published_critic_clock_20261026.py']:files.add(B/'runtime/source_train17_clock'/n)
for n in ['gpu_guard_v7.py.txt','GPU_GUARD_SOURCE.json']:files.add(B/'runtime/recovery86_history_progress_20261030_v1'/n)
E.mkdir();A.mkdir();manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,active_logs_are_snapshots=True,large_artifacts='Original shared SSD, not HDD/arm1 full backup'))
archive=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(archive,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(archive,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for m in t.getmembers():assert t.extractfile(m).read()==(E/m.name).read_bytes()
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='f47cd2386691ef6bb7e33f46e4359658ea6f2180',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=snap['host'],large_artifacts='Original shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
table=[];checkpoints=[]
for m,x in full['methods'].items():
 q=loss['methods'][m]['loss']['agent_train/q_loss'];a=loss['methods'][m]['loss']['agent_train/actor_loss']
 table.append(f"|{m}|{x['steps']}|{x['reward_mean']:.9f}|{x['task']}/{x['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{a['first1000']:.6f}→{a['last1000']:.6f}|")
 checkpoints.append(f"- {m}: `{B}/runs/parameter_partial75_recovery_cycle87_archive_20261029_v1/{m}/cycle_00087.pt`，SHA256 `{x['checkpoint_sha256']}`。")
seedtable=[]
for k,x in seeds['groups'].items():seedtable.append(f"|{k}|{x['task']}/{x['strict']}|{x['reward_range']}|{x['penetration_range_mm']}|")
watch=read(D/'PROBE_OBSERVATION_FINISHED.json')
text=f'''# 完整87尚未收敛；冻结86方差配对评测实际运行

{datetime.datetime.fromtimestamp(snap['time'],datetime.timezone.utc).isoformat()}。Goal active。原87及全部后续审查、原冻结86全部16回合均已完整结束；不重启这些任务。原85—87稳定性检查三方法全未通过。基于现有seed敏感性证据，已独立登记并启动唯一候选：固定完整86模型、同四组合×同四seed，将pre-tanh Gaussian std乘0.5；最多16回合/22000动作/1760万子步、0更新。新评测仍在途，不提前宣称改善；无自动88/Direct34。GPU科学结束仍保载。

主机 `{snap['host']}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际查询/fetch/read main `f47cd2386691ef6bb7e33f46e4359658ea6f2180` 与 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；收工复查main已到49fb9ae13b5dafc3e2c24e459f05079dffba3f58，实际fetch/read其v7 MLP支持域诊断、恢复拟合审计及报告后快进整合；非RL改动保持，RL冻结runtime不变。按仓库sii-research-sync同步，无子agent。

## 完整87与健康检查

三方法各30原条件×55s、41250新增、无安全中止；完整旧replay逐字段精确保留、新reward重建误差0、网络/optimizer全部有限。原4m append-only、容量历史23/47、terminal128/batch65536/UTD1、原LR/reward/masks/filter/physics/gates保持。

|方法|累计steps|平均reward|Task/Strict /30|critic首→末1000|critic max|actor首→末1000|
|---|---|---|---|---|---|---|
{chr(10).join(table)}

全loss图含尖峰、health图、V/A终端图均实际查看并保存PLOT_INSPECTION。I首尾均值下降不能掩盖末段从中段回升；V末段loss明显上升，A基本约1.2但末尾尖峰保留。entropy约I−5/A,V−7，alpha有限正值，Q未整体塌缩；不等同loss健康已确认。采样Q超固定alpha全局界比例I0/A0.0001464844/V0.0023925782，诊断而非新验收门。终端in-mask MAE为I0.438088/A0.173765/V0.253886，out-mask为3.436292/2.415404/1.916477。

86→87全187保存rollout标签核验通过。I short0100外穿透0.162323→0.201807mm新Strict失败；short0600原失败仍在。A long0200/0900 Task失败、long0500/short0900 Task恢复，short0600穿透0.188750→0.230166mm新Strict失败。V short0600为0.188604→0.218863mm新Strict失败，原0.2mm gate不变。

{chr(10).join(checkpoints)}

完整审查 `{B}/runs/parameter_partial75_recovery_cycle87_review_20261029_v1`；loss/labels/terminal证据见本包同名runs目录。三原learner及全部后续均为已核验终态，不能依据旧PROGRESS再次启动。

## 原85—87窗口与固定终端群体

原PLAN `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`，seed2026102858、5000bootstrap、nearzero1、5%、anchor55与原4h截止保持。完整窗口和所有bootstrap抽样标量独立审查通过，但三方法稳定性条件均失败。I reward−0.590930→−2.408941→−4.216508、Strict18→17→16，near-zero保护触发，相对变化不定义；端点差95%区间[−9.027732,0.007020]。A相邻变化22.473%/27.983%，V38.266%/62.095%；A/V端点近似不代表中间稳定。A端点差区间[−4.878116,5.043456]，V[−5.295160,5.331534]，这是条件bootstrap敏感性而非独立训练seed泛化。

同一固定2514旧终端/all5 critic跨84—87的输入/动作/reward/mask一致；前瞻PLAN `7cb97319d8b3cb10e862ebb1ada6dbfe79d97b87cc04035facd3be04d348346d`，保存预测核验/图已完成，0新forward/physics/update。V总SSE9046.061→3556.825→1158.553→2829.904，86→87四critic退化，仅critic4改善；critic2为99.796→1192.429最大退化。A1283.626→3932.823→2110.926→1036.234，四critic改善，critic3为195.430→374.886退化。全部分项保留，不引入新健康阈值或历史抽样因果解释。

另一个原86 anchor2574群体：V1205.453→2959.256，重点2423133为56.484→844.758，2423122为21.174→1.624；A2974.555→1126.414，2752093为56.984→12.016。新87的30终端对完整loss贡献V0.220010/A0.089248。2514与2574分母不同，不混写。

## 原冻结86全部16回合

`{S}`，原PLAN `42dc5ea17bbcde872335568ca6c02da16f42620500b8a6d31b9021bc43fd8234`。四组合×动作seed2026102633/34/35/36，共16完整55s/22000动作/1760万子步，0optimizer/replay更新。最终全learner/optimizer/RNG/replay不变、native动作重放、原审计和独立raw全子步/全部动作复算通过；reward最大重建误差1.4210854715202004e−14。全16图已实际检查。

|组合|Task/Strict /4|reward范围|外穿透mm范围|
|---|---|---|---|
{chr(10).join(seedtable)}

I seeds33/34越过0.2mm导致Strict失败，35/36通过，Task全真。A两组合seed35在carry失败，其余三通过；case哈希产生不同RNG流，不推断普遍坏seed。V四次全过不能证明零失败概率。冻结29已建立敏感性，当前86是新的固定模型/条件复核，不是首次发现或历史因果分解。

## 唯一半标准差干预与两次预检失败

运行 `{P}`，runtime `{B}/runtime/parameter86_half_std_paired_20261030_v3`，PLAN SHA `0d857019e679d3b86c69498cda6a6c39e94264839e771779a69d4a620ada9c89`。相同完整86checkpoint/四组/四seed、同原物理初态与所有gate；仅原actor forward输出的log_std减ln2，同输入mean逐位保持。保留原clock pre-hook、tanh/动作限幅/native CHEQ混合。序列化权重/optimizer/replay/RNG不变，但采样策略行为有意改变，不能写成policy unchanged。高斯pre-tanh熵在同输入减少d·ln2，不等于最终动作std减半或训练target_entropy等价。

v1 PLAN1370af9a：raw forward误收50列而线性层需49；v2 PLANe6c06513：module误收49列，原clock pre-hook期望50列。四组各次check-only均在EVALUATION/physics前失败，退出记录、源码、注册和日志全部保留。v3通过actor(obs50)保留原hook，包装内的cached raw forward接收49；真实native接口随机初始化检查先通过，随后四真实86完整checkpoint恢复、native/external动作一致及56设计/metadata负例全部通过。修正不新增科学预算，不删除失败。

实际LAUNCH四评测PID1280069/1280072/1280075/1280076，start574382314/315/315/315；reviewer1280079/start574382315。启动后全state/replay核验、实际400保存动作/canonical48/MJB/CPU7–10和原physics-action循环AST一致，所有未变native helper hash一致，改动sampler明确分列。新观察{watch['samples']}样本/{watch['elapsed_s']:.3f}秒，原35+新5身份保持live或已核验完成。快照进度 `{ {k:(v['completed_episodes'],v['seed'],v['actions']) for k,v in progress.items()} }`；这只是进度，最终16结果/不变证明/paired图仍待。

等待既有reviewer产出FINISHED、REVIEW、PAIRED_REVIEW与PAIRED_SAVED_REVIEW，必须审全部16的Task/Strict增减、reward/穿透/安全中止和实际图，禁止挑seed、搜索因子或自动晋升。任何后续训练修订独立登记，父训练仍完整87，不能从诊断86回退训练。原SAC target_entropy=−dimension未进入PublishedLearner state_dict/load；未来若改训练熵目标，须版本化序列化/恢复/诊断并验证，不能只赋值后声称可恢复。当前未建立任何88或Direct34。

## GPU、恢复与保存

原v7守护supervisor97370/start570509460、workers97399–97402/start570509475仍保持；控制目标70%、阈值50%。本轮{g['samples']}样本min `{g['minimum']}`%、低于50次数 `{g['below50']}`，末值 `{g['last']}`%。用于保活的合成负载不是科研吞吐，科学结束后仍保留。历史v7预热0及v6 GPU0=31/GPU2=33/44低谷不删除；采样不保证每个瞬时，非系统重启自启服务。源码已随包保存。

Direct33数值阶段接受，冻结33全30 Task/Strict0/0、中断28最终内存证明缺失；指定ESN仍不可用，不替换他主机模型、不重复追问。冻结82完整90已于f47cd238发布，不重跑；partial75、原74—76不可判、原所有历史稳定性结论和79真实安全中止保留。科学Goal active。

小证据 `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；逐tar成员字节/源码AST已核，Git index/commit核验另存。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份。HDD LATEST只原位更新254字节指针，不能当全备份。运行文件为时间点快照；成功正常push并实际观察远端后才在包外写PUBLICATION.json。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整87与冻结86全16已审；半标准差配对评测运行

- [交接](docs/{TAG}.md)。87三路各30×55/41250/noabort、全replay/reward0误差/loss/health/187标签/两终端已审；Task/Strict18/16、15/14、17/16。原85—87全失败稳定性，固定2514 V1158.553→2829.904退化、A2110.926→1036.234改善但critic3退化，六实际图保留；未收敛，无自动88/Direct34。
- 原冻结86全16与1760万raw子步独立审计/最终全state不变/图通过，I Strict2/4、A两组3/4、V4/4。唯一std×0.5固定86同16配对已启动，PLAN0d857019，v1/v2零物理接口预检失败保留，v3四真实恢复/56负例/实际400行与native循环通过；{watch['elapsed_s']:.1f}秒40身份观察通过，最终16/paired图待。序列化state不变但sampler有意改变，非训练熵目标等价，Goal active。
- GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学完成仍保载；SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验、非HDD/arm1全备份。mainf47cd238/baselinef6e8f8c实际fetch/read，正常发布见收据，无子agent。

'''
for n in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/n;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(receipt));print('GPU',g)
