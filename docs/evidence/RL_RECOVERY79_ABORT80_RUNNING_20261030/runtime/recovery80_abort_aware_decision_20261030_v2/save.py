from pathlib import Path
import json,time,hashlib,ast,tarfile,subprocess,socket,datetime,os
B=Path('/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl');R=B/'repository/SII_compliance';D=Path(__file__).parent;RUN=B/'runs/parameter_partial75_recovery_cycle80_20261029_v1';PREP=B/'runtime/prepare_recovery80_20261029_v1';REV=B/'runs/parameter_partial75_recovery_cycle79_review_20261029_v1';TAG='RL_RECOVERY79_ABORT80_RUNNING_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
read=lambda p:json.loads(Path(p).read_text())
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def put(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,ensure_ascii=False);f.write('\n')
def live(j):
 p=Path(f'/proc/{j["pid"]}/stat')
 if not p.exists():return False
 f=p.read_text().rsplit(')',1)[1].split();return f[19]==j['proc_start_ticks'] and f[0]!='Z'
assert read(D/'DECISION80.json')['passed'] and read(D/'OBSERVATION_FINISHED.json')['passed']
startup=read(RUN/'startup/REVIEW.json');assert startup['passed'] and len(startup['methods'])==3
assert read(B/'runtime/recovery80_followups_20261030_v1/FINISHED.json')['passed']
for m in ['impedance','admittance','vmc']:
 assert read(RUN/m/'INITIAL_STATE_REVIEW.json')['passed']
 assert startup['methods'][m]['retained_replay_all_fields_exact'] and startup['methods'][m]['max_reward_reconstruction_error']==0
for x in read(D/'LAUNCH_SOURCE_REVIEW.json')['files']:assert sha(x['path'])==x['sha256']
progress={}
for j in read(RUN/'LAUNCH.json')['jobs']:
 assert live(j);p=RUN/j['controller']/'train';assert not (p/'FAILURE.json').exists();progress[j['controller']]=read(p/'PROGRESS.json')
obs=read(D/'OBSERVATION_FINISHED.json');saved=[json.loads(l) for l in (D/'OBSERVATIONS.jsonl').read_text().splitlines()];assert len(saved)==obs['samples'] and saved[-1]['elapsed']>=180
for m in progress:assert obs['first_steps'][m]==saved[0]['parameter'][m]['steps'] and obs['last_steps'][m]==saved[-1]['parameter'][m]['steps']
g=Path('/tmp/sii_gpu_util_guard_20261030_v7');rows=[json.loads(l) for l in (g/'samples.jsonl').read_text().splitlines()];since=read(PREP/'SAVE_SNAPSHOT.json')['time'];gpu=[v for v in rows if v['time']>since];assert gpu and time.time()-gpu[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in gpu));(D/'guard_source.py').write_bytes((g/'guard.py').read_bytes())
for name in ['LAUNCH.json','RECOVERY.json','CONTROL.json']:(D/('guard_'+name)).write_bytes((g/name).read_bytes())
guard=dict(samples=len(gpu),minimum=[min(v['gpus'][i]['utilization'] for v in gpu) for i in range(4)],below50=[sum(v['gpus'][i]['utilization']<50 for v in gpu) for i in range(4)],last=[v['utilization'] for v in gpu[-1]['gpus']],synthetic_included=True,keep_after_science=True,no_reboot_service=True)
snapshot=dict(time=time.time(),host=socket.gethostname(),parameter80=progress,actual_startup_passed=True,guard=guard,decision=read(D/'DECISION80.json'),goal='active',direct34=False);put(D/'SAVE_SNAPSHOT.json',snapshot)
folders=[D,PREP,B/'runtime/recovery80_completion_preparation_20261030_v1',B/'runtime/recovery80_followups_20261030_v1',B/'runtime/recovery79_completion_watch_20261030_v1',REV,B/'runs/parameter_partial75_recovery_cycle79_archive_20261029_v1',B/'runs/parameter_recovery79_loss_20261029_v1',B/'runs/parameter_recovery79_task_labels_20261029_v1',B/'runs/vmc_recovery79_terminal_followup_20261029_v1',B/'runs/admittance_recovery79_terminal_followup_20261029_v1',B/'runs/impedance_recovery79_abort_review_20261030_v1',B/'runs/parameter_partial75_recovery_cycle80_review_20261029_v1',B/'runs/parameter_recovery80_loss_20261029_v1',B/'runs/parameter_recovery80_task_labels_20261029_v1',B/'runs/vmc_recovery80_terminal_followup_20261029_v1',B/'runs/admittance_recovery80_terminal_followup_20261029_v1',B/'runs/parameter_recovery79_81_reward_stability_20261030_v1']
files=set()
for folder in folders:
 for p in folder.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.json','.jsonl','.py','.txt','.diff','.log','.png','.npz'] and p.stat().st_size<10_000_000:files.add(p)
for c in [78,79]:
 case=B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1/impedance/train/cycle_{c:05d}/active_long_train_0000'
 for p in case.iterdir():
  if p.is_file() and p.suffix in ['.json','.jsonl','.txt','.npz','.log'] and p.stat().st_size<10_000_000:files.add(p)
for c in [79,80]:
 root=B/f'runs/parameter_partial75_recovery_cycle{c}_20261029_v1'
 files.update(p for p in root.glob('*') if p.is_file() and p.suffix in ['.json','.py'])
 for m in ['impedance','admittance','vmc']:
  files.update(p for p in (root/m).glob('*.json'))
  for n in ['EXECUTION.json','PROGRESS.json','FINISHED.json','episodes.jsonl']:
   p=root/m/'train'/n
   if p.exists():files.add(p)
files.add(RUN/'startup/REVIEW.json');files.add(B/'runs/parameter_recovery76_78_reward_stability_20261029_v1/PLAN.json')
E.mkdir(exist_ok=False);A.mkdir(exist_ok=False);manifest=[]
for p in sorted(files):
 data=p.read_bytes();rel=p.relative_to(B);q=E/rel;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 if p.suffix=='.py':ast.parse(data)
 manifest.append(dict(source=str(p),relative=str(rel),bytes=len(data),sha256=sha(q)))
put(E/'MANIFEST.json',dict(time=time.time(),files=manifest,large_artifacts_retained_shared_ssd=True,active_logs_are_snapshots=True))
tar=A/'SMALL_EVIDENCE.tar.gz'
with tarfile.open(tar,'w:gz') as t:
 for p in sorted(E.rglob('*')):
  if p.is_file():t.add(p,arcname=str(p.relative_to(E)),recursive=False)
with tarfile.open(tar,'r:gz') as t:
 assert len(t.getmembers())==len(manifest)+1
 for member in t.getmembers():assert t.extractfile(member).read()==(E/member.name).read_bytes()
receipt=dict(time=time.time(),archive=str(tar),bytes=tar.stat().st_size,sha256=sha(tar),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),start_main='cd8bbf33c44dfb497f1fb7551451c89312b3ae28',remote_main=subprocess.check_output(['git','rev-parse','origin/main'],cwd=R,text=True).strip(),baseline=subprocess.check_output(['git','rev-parse','origin/baseline'],cwd=R,text=True).strip(),host=snapshot['host'],large_artifacts='Shared SSD; not full HDD/arm1 backup');put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
steps={m:v['steps'] for m,v in progress.items()};full=read(REV/'REVIEW.json');loss=read(B/'runs/parameter_recovery79_loss_20261029_v1/REVIEW.json');table=[]
for m,v in full['methods'].items():
 q=loss['methods'][m]['loss']['agent_train/q_loss'];table.append(f"|{m}|{v['steps']}|{v['new_transitions']}|{v['reward_mean']:.9f}|{v['task']}/{v['strict']}|{v['full_horizon_count']}/30|{q['first1000']:.6f} → {q['last1000']:.6f}|{q['maximum']:.6f}|")
table='\n'.join(table)
doc=f'''# 完整79、安全中止审查与有限80续训

{datetime.datetime.fromtimestamp(snapshot['time'],datetime.timezone.utc).isoformat()}。**Goal active，三路参数RL第80轮已真实续训；当前steps {steps}，准确恢复/实际startup通过。未证明reward平稳且loss健康；无自动81，无Direct34。GPU科研结束后仍合成保载。**

执行主机 `{snapshot['host']}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。按sii-research-sync流程开工真实fetch/read main `{receipt['start_main']}`、baseline `{receipt['baseline']}`；保存前main前进至`{receipt['remote_main']}`，只改共享日志、非RL进度27→55/75，已安全快进并读其日志，非RL源码保持。无子agent，未代替另一主机派发teacher/学生工作。

## 完整79结果与限制

|方法|累计steps|实际新增|平均reward|Task/Strict|完整55s|critic首→尾1000|critic最大|
|---|---:|---:|---:|---:|---:|---:|---:|
{table}

三路完整30条件已结束，旧回放全部字段/history保持，所有新增reward重建误差0、done与回放精确匹配，网络/optimizer有限；完整loss独立算术、全部180标签/90reward配对、health、两路终端全锚点审查完成。四张原完整图及一张新几何图已实际查看，收据逐图hash绑定。有限数值不等于loss健康。

I反复critic尖峰且actor24.673951→24.081640持续漂移；A后段critic尖峰簇且actor−9.031459→−8.871949，Task/Strict16/16→14/13；V critic均值下降但仍尖峰/actor漂移，Task/Strict17/16→17/17。A的short0600 Strict退化、short0900及long0500任务退化，I long0000安全中止，V short0600 Strict恢复均保留。A/V采样Q超过当前alpha软上界比例分别0.00078125/0.00190430，不能据此声称校准完成。

完整旧2334终端固定观测/action/reward/mask精确：V SSE8084.666548→3396.003020改善但仍有大残差，各focus有升有降；A SSE1449.305195→2084.328691退化，原focus36.476726→5.730751改善不能替代总体。旧新两个回放分母保留，A新30终端贡献0.152839883，全部贡献0.245985272；V全部贡献0.152400481。独立saved-values审查通过，0新物理/更新。

原76–78 I近零1保护不可判、A不满足5%、V reward满足但loss健康未证保持；原75仍不完整，原74–76不可判。79–81前瞻PLAN SHA `5cf5efb87a63b432091276c3b96a3b16126c2ab891a2e195b6c857e93cf110a0`不变，5%/nearzero1/bootstrap5000/seed2026102855/anchor55保持；不能以近零保护为改变reward方向的理由，不能抹去短回合。

## 阻抗79真实安全失败

`runs/impedance_recovery79_abort_review_20261030_v1/FINAL_REVIEW.json`。long0000在27.0000000003s/675动作/540000物理子步终止，原reason `global_penetration_exceeded_2mm`，Task/Strict/physical_valid均false，阶段retreat。记录全子步global峰值97.689118mm，最深对为corner_top与target_object；机器人外部穿透峰值0.072362mm。78同MJB/执行evaluator该条件55s成功。79物块最后保存位置与广义速度出现跳变。

原安全检查在actor间隔结束读取累计global峰值，已按原2mm终止；未提高安全阈值。25Hz保存帧各675个，78/79几何重建共1350次mj_forward、0次mj_step：最大保存帧穿透0.053973/0.066135mm。训练没有保存全部子步状态，**该几何检查不能重建或否定97.689mm记录峰值，根因未确定，不能称为无害尖峰/全局被动性通过**。实际evaluator.log非JSON行无匹配warning记录，但这也不能证明积分全程无警告。

675行shield递推全部误差0、6750伺服记录检查通过，能量最小0.762900626；仅核记录指令，不替代物理速度/力矩审计。终端done恰一次，step3264119，终端transition reward−38.100159404；整条reward−40.529577442，terminal−25及failure_tail−9.940790457保持。全cycle新增40550=29×1375+675，不虚构41250或55s，不重跑该失败，不删除其回放。

## 明确登记的80决定及启动

原`runtime/recovery80_completion_preparation_20261030_v1/decision80.py`因40550/29full/abort正确拒绝，`COMPLETE79_ABORT_REJECTION.json`保留，原源码不改。另建`runtime/recovery80_abort_aware_decision_20261030_v2`，在完整79及诊断之后登记PLAN和理由，仅针对**精确已审79 checkpoint及该唯一失败**允许一轮有限80，不允许任意失败通过。12个负例拒绝及三路真实正例、缺决定拒绝通过，绑定全部原证据、五图、准确80恢复与原窗口。版本2不等于原no-abort guard通过；不声称失败已修好。

续训依据是网络/optimizer有限、原reward/done和回放/精确恢复正确、记录shield/servo未见执行偏差，允许继续模拟学习以观察失败是否持续；根因仍待更细证据。原30条件、55s上限、最多41250新transition、4m append-only、markers23/47、terminal128、batch65536/UTD1、LR/masks/reward/物理/MJB/安全门槛均不改。

准备入口另发现旧`launch80.py`残留parent78和`resume_recovery78.py`引用。原错误源和拒绝保留，v2只修为parent79及真实`resume_recovery79.py`；以真实driver导入、三路注册/命令/hash/CPU可用性预检通过后启动。v2构建脚本一次括号SyntaxError在执行前失败，原件/失败收据保留后修复，没有科学重启。实际LAUNCH及INITIAL_STATE在`runs/parameter_partial75_recovery_cycle80_20261029_v1`，三路原数据完整，actual startup全部30sampler/模型/源/奖励映射通过。

完整80 archive/review/health/loss/79→80标签等待均已部署，两路新终端anchor各保留完整79全部2364，V/A SSE3410.810921813/5503.511132148，hash及独立标量复算通过；预计完整80各2394行。旧focus与两个分母保留。所有进程PID/start在LAUNCH收据，先核身份再接续；不得重复派发80。81须完整80证据后另决定。

## 连续观察、GPU与恢复入口

原79完成观察38样本/1110.270秒，三训练/归档/loss/labels/终端/仅恢复80全部完成。80启动后{obs['samples']}样本/{obs['elapsed']:.3f}秒、{obs['identities']}个原身份保持live或核完整终态，保存行独立核验；steps {obs['first_steps']}→{obs['last_steps']}，观察器自然结束、科学不重启。

上次准备保存以来GPU{guard['samples']}个5秒样本，最低{guard['minimum']}%，低于50次数{guard['below50']}；最后{guard['last']}%。负载包含合成保活，不能当科研吞吐。guardv7 supervisor97370/start570509460，四worker97399–97402/start570509475，CPU4–6，target70%、floor50%；科学全部完成仍运行。历史停机、v7预热0和v6的31/33/44低谷保留，不能保证每个瞬时无低谷；尚非重启自启服务。

Direct33数值阶段接受状态保持，冻结全30 Task/Strict0/0；旧28最终内存不变证明仍缺失，原中断877额外动作单列。不启动Direct34；指定ESN和最终冻结比较范围仍待，非RL另一主机进度不替代本任务。

SSD小证据包 `{tar}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA `{receipt['sha256']}`，全部成员字节/hash及Python AST核验。收据[{TAG}_SAVE.json]({TAG}_SAVE.json)。大checkpoint/回放/轨迹留原共享SSD，活动日志为快照，**非HDD/arm1全量备份**。HDD原254字节LATEST指针原位更新回读。GitHub发布以实际发布收据为准。

下一步继续原80科学进程，检查完整loss/health/labels/terminal与79–81等待器，按实际物理失败和loss趋势决定有限81；继续GPU保载。勿把本轮有限续训或保存成功写成收敛完成。
'''
(R/'docs'/(TAG+'.md')).write_text(doc);(A/'HANDOFF.md').write_text(doc)
entry=f'''## 2026-10-30 — 完整79含真实安全中止；明确登记有限80续训

- [交接](docs/{TAG}.md)。79三路reward−2.511717/−10.141245/−2.874607，Task/Strict17/17、14/13、17/17；I long0000在27s安全中止、40550新增/29full，失败/惩罚全部保留。完整回放/reward/loss/health/180标签/终端/五实际图已审，未收敛。
- 原80 no-abort决定正确拒绝保留；v2只绑定精确已审失败另登记有限80，原2mm安全/reward/学习参数不改。shield675/servo6750通过但25Hz几何不能重建97.689mm子步峰值，根因未定。修旧launcher父轮次/driver引用并做真实预检，12负例通过；准确80恢复/实际startup通过，当前steps{steps}，各30sampler及全后续已部署；无自动81/Direct34，Goal active。
- {obs['samples']}样本/{obs['elapsed']:.3f}s共{obs['identities']}身份验证，GPU{guard['samples']}样本min{guard['minimum']}%、低于50{guard['below50']}；科研结束仍合成保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验，非HDD/arm1全备份。开工maincd8bbf33/baselinef6e8f8c2，后main{receipt['remote_main'][:8]}非RL55/75已读快进保留；发布待收据，无子agent。

'''
for name in ['AGENTS.md','UPDATE_LOG.md']:
 p=R/name;s=p.read_text()
 if name=='AGENTS.md':h,t=s.split('\n',1);p.write_text(h+'\n\n'+entry+t.lstrip('\n'))
 else:p.write_text(entry+s)
for p,link in [(R/'HANDOFF.md','docs/'+TAG+'.md'),(R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md',TAG+'.md')]:p.write_text(f'> **最新：[完整79/安全失败与有限80续训]({link})。80运行、Goal active，GPU科研结束仍保活。**\n\n'+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');n=p.stat().st_size;v=f'# RL {datetime.datetime.fromtimestamp(snapshot["time"],datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}\n80;abort79;guardv7.\nSSD {B}\nRead repository/SII_compliance/docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md\nLarge data SSD. No reboot service.\n'.encode();assert n==254 and len(v)<=n
with p.open('r+b') as f:f.write(v+b' '*(n-len(v)));f.flush();os.fsync(f.fileno())
assert p.read_bytes()==v+b' '*(n-len(v));print(json.dumps(receipt));print(json.dumps(dict(steps=steps,guard=guard)))
