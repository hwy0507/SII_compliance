from pathlib import Path
import ast,hashlib,json,socket,subprocess,tarfile,time,os,datetime
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';F=B/'runs/parameter82_frozen_full30_20261030_v1';A82=B/'runs/parameter82_frozen_full_saved_audit_20261030_v1';S86=B/'runs/parameter86_frozen_switches_20261030_v1';FIX=B/'runs/recovery84_87_fixed_terminal_critic_followup_20261030_v1';TAG='RL_FROZEN82_COMPLETE87_PROGRESS_20261030';E=R/'docs/evidence'/TAG;A=B/'repository'/TAG
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
assert read(D/'WATCH_FINISHED.json')['all82_ready'] and read(D/'INTERPRETATION.json')['passed'] and read(D/'SAVED_REVIEW.json')['passed']
assert read(D/'PLOT_INSPECTION.json')['actual_image_viewed'] and read(F/'PLOT_INSPECTION.json')['actual_image_viewed']
assert read(A82/'FINISHED.json')['passed'] and read(F/'comparison55_82/SAVED_REVIEW.json')['passed']
identities=read(D/'PLAN.json')['identities'];j=read(FIX/'LAUNCH.json');identities.append(dict(name='fixed2514_84_87',pid=j['pid'],proc_start_ticks=j['proc_start_ticks'],failure_paths=[str(FIX/'FAILURE.json')],terminal_requirements=[dict(path=str(FIX/'FINISHED.json'),key='passed',value=True)]))
states={j['name']:state(j) for j in identities}
progress={m:read(B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train/PROGRESS.json') for m in ['impedance','admittance','vmc']}
seedprogress={k:read(S86/k/'PROGRESS.json') for k in read(S86/'PLAN.json')['groups']}
since=read(S86/'SAVE_SNAPSHOT.json')['time'];samples=[json.loads(l) for l in Path('/tmp/sii_gpu_util_guard_20261030_v7/samples.jsonl').read_text().splitlines()];samples=[r for r in samples if r['time']>=since];assert time.time()-samples[-1]['time']<20
(D/'GUARD_SAMPLES.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in samples))
g=dict(samples=len(samples),start=samples[0]['time'],end=samples[-1]['time'],minimum=[min(x['gpus'][i]['utilization'] for x in samples) for i in range(4)],below50=[sum(x['gpus'][i]['utilization']<50 for x in samples) for i in range(4)],last=[x['utilization'] for x in samples[-1]['gpus']],synthetic_included=True,keep_after_science=True,reboot_service=False,historical_dips_preserved=True)
snapshot=dict(time=time.time(),host=socket.gethostname(),states=states,identities=identities,cycle87=progress,frozen86=seedprogress,guard=g,goal='active',automatic88=False,direct34=False)
put(D/'SAVE_SNAPSHOT.json',snapshot)
files=set()
for folder in [D,A82,F/'comparison55_82',FIX,B/'runtime/parameter82_frozen_full30_20261030_v1']:
 for p in folder.iterdir():
  if p.is_file() and p.suffix in {'.json','.jsonl','.py','.diff','.txt','.log','.png','.npz'} and p.stat().st_size<10_000_000:files.add(p)
for p in F.iterdir():
 if p.is_file() and p.suffix in {'.json','.log','.png'}:files.add(p)
for m in progress:
 for p in (F/m).iterdir():
  if p.is_file() and p.suffix in {'.json','.log'}:files.add(p)
 files.add(B/f'runs/parameter_partial75_recovery_cycle87_20261029_v1/{m}/train/PROGRESS.json')
for k in seedprogress:
 for n in ['PROGRESS.json','RESULTS.json','FINISHED.json']:
  p=S86/k/n
  if p.exists():files.add(p)
for n in ['PLAN.json','LAUNCH.json','REVIEW_LAUNCH.json']:files.add(S86/n)
files.add(B/'runtime/recovery82_full_review_20261030_v1/compare_frozen55_82.py')
for n in ['RECEIPT.json','PUBLICATION.json']:files.add(B/'repository/RL_RECOVERY87_FROZEN86_SEEDS_20261030'/n)
for n in ['PLAN.json','REVIEW.json','SAVED_REVIEW.json','PLOT_INSPECTION.json']:files.add(B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1'/n)
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
receipt=dict(time=time.time(),archive=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),members=len(manifest)+1,all_member_bytes_and_ast_verified=True,source_base_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),inspected_main='80e94020d78a3df407541a8c547ff1e9ca56994a',baseline='f6e8f8c2711a93f0b5dfc88c608bd82647084d5d',host=socket.gethostname(),large_artifacts='Original shared SSD; not full HDD/arm1 backup')
put(A/'RECEIPT.json',receipt);put(R/'docs'/(TAG+'_SAVE.json'),receipt)
report=read(D/'INTERPRETATION.json');full=read(F/'REVIEW.json');watch=read(D/'WATCH_FINISHED.json');steps={m:r['steps'] for m,r in progress.items()}
table=[];detail=[]
for m,r in report['methods'].items():
 before,after=r['endpoints']['before'],r['endpoints']['after']
 table.append(f"|{m}|{before['reward_mean']:.9f}→{after['reward_mean']:.9f}|{before['task']}→{after['task']}|{before['strict']}→{after['strict']}|{before['machine_violation_count']}→{after['machine_violation_count']}|")
 detail.append(f"- {m}: Task增加{r['task_gained']}、减少{r['task_lost']}；Strict增加{r['strict_gained']}、减少{r['strict_lost']}。均值差{r['mean_reward_delta']:.9f}，标签改变条件贡献{r['label_partition']['changed_label_mean_contribution']:.9f}，标签未变贡献{r['label_partition']['unchanged_label_mean_contribution']:.9f}；原reward标量重建最大误差{r['max_reward_reconstruction_error']:.3g}。")
cps='\n'.join(f"- {m}: checkpoint `{r['checkpoint_sha256']}`，initial=final learner digest `{r['initial_and_final_learner_digest']}`。" for m,r in full['methods'].items())
contact='\n'.join(f"- {m}: 55接触{r['endpoints']['before']['human_contact_seconds']:.6f}s、82接触{r['endpoints']['after']['human_contact_seconds']:.6f}s；contact-only比例55={r['endpoints']['before']['contact_weighted_compliance_ratio']}、82={r['endpoints']['after']['contact_weighted_compliance_ratio']}（None即NA）。" for m,r in report['methods'].items())
text=f'''# 冻结82完整90回合已审；原87与冻结86多seed继续

{datetime.datetime.fromtimestamp(snapshot['time'],datetime.timezone.utc).isoformat()}，Goal active。冻结82三方法全30/共90回合已完成，全部55秒、123750动作/9900万子步；完整learner/replay最终不变、原动作native重放/physical/filter/torque、全保存raw独立复核、55→82全部90配对和两张实际图均已核。该完成不等于训练收敛或最终泛化；原87继续，steps `{steps}`，冻结86固定16回合继续，无自动88/Direct34。

主机 `{snapshot['host']}`，共享SSD `{B}`，解释器 `{B}/env/bin/python`。本轮实际ls-remote、fetch/read main `80e94020d78a3df407541a8c547ff1e9ca56994a` /baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按仓库sii-research-sync发布，保留他主机非RL，无子agent。源码 `{D}`，原评测 `{F}`。

## 完整冻结82与相同seed55→82比较

原PRE_REGISTRATION SHA `baf37d1715635e1d5352deea7434b33e36e666c4c0d3036f43f404b685935b76`，evaluation PLAN SHA `12359f695a69fa03579ab0515ce8c2cbfb8ecf47b5dc0200240bda3046b97783`，动作seed2026102638、全部30原开发训练条件保持。三路每路41250动作/3300万子步，0优化器更新、0replay追加，全部有限完整55s、无abort。所有原evaluator自然完成，旧PROGRESS是末次周期进度、最终以FINISHED为准，不重启。

|方法|mean reward55→82|Task55→82/30|Strict55→82/30|机器判据违规55→82|
|---|---|---|---|---|
{chr(10).join(table)}

{chr(10).join(detail)}

阻抗short0100外穿透0.154178→0.202805mm，越过原0.2mm线，Task仍真但Strict失败；导纳long0500由成功变为lift阶段失败，外穿透0.040687→0.045634mm，该任务退化不是跨越0.2mm门。

全90条件均保留，全部条件的回报差之和/30与两个端点均值差独立一致；标签分组贡献只是算术，不分解随机性与学习变化的历史因果。55与82动作seed/condition fixture/模型/物理dt/actor period/horizon/reference/torque阈值/reward均一致，但训练暴露量不同、包含partial75历史，不能当相等预算或独立training-seed试验。

完整独立保存审计 `{A82}` 逐原始文件hash、9900万子步dt5e-5/有限值、实际接触时长/舒适分母/关节峰矩/穿透量、全部123750动作journal重算reward/Task/Strict/安全标签，与原review一致。该审计没有新physics/forward/update，复用原evaluator完整内存不变和原native-action重放收据；不声称在退出后重算其已不存在的内存。

{contact}

无接触为NA，不以低力矩空闲替代舒适，也不平均每回合舒适比例。两张实际图：原 `frozen_full30_results.png` 与新 `{D}/frozen55_82_all90_pairs.png`，全部90返回差和55/82外穿透、原0.2mm线已目视核对，证据见各PLOT_INSPECTION。

{cps}

## 原87与固定2514后续

原87每方法最多41250新增、30条件×最多55秒、4m append-only、历史23/47、terminal128/batch65536/UTD1及原LR/reward/masks/physics/filter/gates保持。PID2291679/80/81 start573936642；原archive/loss/labels/两终端后续继续，完整87仍待。85—87原PLAN SHA6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e、seed2026102858、5000bootstrap/nearzero1/5%/anchor55/原4h截止不改；A/V 85→86相邻已超5%，87不能追认该窗口通过。

在完整87之前登记同一2514旧终端/all5critic的84/85/86/87跟踪 `{FIX}`，PLAN SHA `{sha(FIX/'PLAN.json')}`，等待PID `{read(FIX/'LAUNCH.json')['pid']}` /start `{read(FIX/'LAUNCH.json')['proc_start_ticks']}`。已验证旧2514 inputs/actions/rewards/masks与当前86anchor前缀精确一致，当前anchor2574、预测87共2604，全部5critic旧86值逐位一致；真实缺完整87执行被正确拒绝。

此跟踪只汇总既有两终端审计的保存预测，0新forward/physics/update，保留全部旧样本与30新84cohort，检查VMC86改善及Acritic4回归是否持续。沿用原87monitor+14400截止，不延长原85—87统计窗口、不新增健康门槛、无自动88。完整87后需结合全loss/health/标签/固定群体和完整窗口决定是否独立登记训练修订。

## 冻结86动作seed诊断与其他范围

上一轮登记的完整86四组合×四动作seed固定16回合继续，PLAN SHA42dc5ea17bbcde872335568ca6c02da16f42620500b8a6d31b9021bc43fd8234，不改预算/源/seed。当前保存(已完成回合,seed,在途动作) `{ {k:(v['completed_episodes'],v['seed'],v['actions']) for k,v in seedprogress.items()} }`。完整16/最终全state证明/独立saved图仍待；不能只用部分seed判断当前策略稳定。既有冻结29敏感性证据/原12回合结束状态保持，不宣称首次发现随机性。

Direct33数值阶段已接受，冻结30 Task/Strict0/0，无Direct34；中断28缺最终内存不变证明保留。指定ESN仍缺，不替换他主机模型、不重复追问。partial75与原74—76不可判、原76—78/79—81/82—84结论及79真实安全中止均保留；完整85历史重建只是数据可行性，无actor输入修订。

本轮完成观察{watch['samples']}样本/{watch['elapsed_s']:.3f}秒，原34进程身份保持live或合法完成；最后另核新fixed87等待，共35身份。观察器自然结束不重启科学。GPU原v7守护保持，科学结束仍合成保载，{g['samples']}样本min `{g['minimum']}`%、低于50次数 `{g['below50']}`，末值 `{g['last']}`%。合成利用率不是科学吞吐；历史预热0及GPU0=31/GPU2=33/44低谷保留，不保证采样间每瞬时，非重启自启服务。

小证据SSD `{archive}`，{receipt['members']}成员/{receipt['bytes']}字节，SHA256 `{receipt['sha256']}`；逐tar成员字节/源码AST已核，Git index/commit字节另核。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份，HDD LATEST保持254字节原位更新。运行日志为快照，成功push及后续实际远端核验见SSD本包PUBLICATION.json。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 冻结82完整90已审；87与冻结86多seed继续

- [交接](docs/{TAG}.md)。冻结82全90×55s/123750动作/9900万子步、全部最终learner/replay不变、raw独立审计/55→82全90配对/两实际图通过。I/A/V Task/Strict18/17、14/14、17/17，改善和退化均保留，开发单动作seed，非收敛/泛化。
- 新同2514/all5的84—87保存值跟踪在完整87前登记，真实缺前置拒绝/已知anchor输入及86预测逐位核验，等待PID{read(FIX/'LAUNCH.json')['pid']}，无新forward/physics/update；原87steps{steps}、冻结86固定16与原85—87继续，无自动88/Direct34，Goal active。
- {watch['elapsed_s']:.1f}秒原34身份观察完成，最后35身份核验；GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学结束仍保载。SSD{receipt['members']}成员/SHA{receipt['sha256'][:8]}核验、非HDD/arm1全备份；main80e94020/baselinef6e8f8c实际fetch/read，发布见收据，无子agent。

'''
for n in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/n;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';first,rest=p.read_text().split('\n',1);p.write_text(first+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.stat().st_size==254 and p.read_bytes()==data
print(json.dumps(receipt));print('GPU',g);print('steps87',steps)
