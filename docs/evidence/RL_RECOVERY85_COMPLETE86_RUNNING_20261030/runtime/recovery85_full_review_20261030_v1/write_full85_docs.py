from pathlib import Path
import json,datetime,os,hashlib
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY85_COMPLETE86_RUNNING_20261030'
read=lambda p:json.loads(p.read_text())
s=read(D/'SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));g=s['guard'];steps={m:r['steps'] for m,r in s['cycle86'].items()};obs=read(D/'OBSERVATION_FINISHED.json')
full=read(B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1/REVIEW.json')['methods'];health=read(B/'runs/parameter_partial75_recovery_cycle85_review_20261029_v1/health/DIAGNOSIS.json')['methods'];loss=read(B/'runs/parameter_recovery85_loss_20261029_v1/REVIEW.json')['methods'];labels=read(B/'runs/parameter_recovery85_task_labels_20261029_v1/COMPLETE84_85.json');fixed=read(B/'runs/recovery84_85_fixed_terminal_input_followup_20261030_v1/REVIEW.json');new=read(D/'NEW85_TERMINAL_CASE_REVIEW.json')['methods'];avail=read(D/'UPDATE_AVAILABILITY85_REVIEW.json')['methods'];decision=read(B/'runtime/recovery86_completion_preparation_20261030_v1/DECISION86.json');startup=read(B/'runs/parameter_partial75_recovery_cycle86_20261029_v1/startup/REVIEW.json')
rows=[];hr=[];hashes=[];changes=[];critics=[];terms=[]
for m in ['impedance','admittance','vmc']:
 r=full[m];q=loss[m]['loss']['agent_train/q_loss'];ac=loss[m]['loss']['agent_train/actor_loss'];h=health[m]
 rows.append(f"|{m}|{r['steps']}|{r['reward_mean']:.9f}|{r['task']}/{r['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{ac['first1000']:.6f}→{ac['last1000']:.6f}|")
 hr.append(f"|{m}|{100*h['sampled_q_above_global_bound_fraction']:.8f}%|{h['terminal_q_in_bag_absolute_error']['mean']:.6f}|{h['terminal_q_out_of_bag_absolute_error']['mean']:.6f}|")
 hashes.append(f"- {m}：`{r['checkpoint_sha256']}`。")
 for c in labels['methods'][m]['all30']:
  if c['changed_fields']:
   cs=[{k:v for k,v in x.items() if k in ['cycle','task','strict','physical_valid','penetration_mm','abort_reason']} for x in c['cases']];changes.append(f"- {m} {c['condition']}：{json.dumps(cs,ensure_ascii=False)}。")
for m in ['vmc','admittance']:
 t=read(B/f'runs/{m}_recovery85_terminal_followup_20261029_v1/REVIEW.json')
 terms.append(f"- {m}：旧2514终端SSE {t['old2514_sse_before']:.6f}→{t['old2514_sse_after']:.6f}，新增30贡献{t['new30_contribution']:.9f}；新30贡献前三为 "+'、'.join(f"{x['condition']} {100*x['share_of_new30']:.3f}%" for x in new[m]['cases'][:3])+'。')
 for c in fixed['methods'][m]['critics']:critics.append(f"|{m}|{c['critic']}|{c['sse84']:.6f}|{c['sse85']:.6f}|{c['opposite_sign84']}→{c['opposite_sign85']}|")
fp={m:(r['completed_conditions'],r['condition'],r['actions']) for m,r in s['frozen82'].items()};sp={m:r['added_steps'] for m,r in startup['methods'].items()};stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat()
follow=B/'runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1';followsha=hashlib.sha256((follow/'PLAN.json').read_bytes()).hexdigest();fj=read(follow/'LAUNCH.json');run=B/'runs/parameter_partial75_recovery_cycle86_20261029_v1';jobs={j['controller']:j['pid'] for j in read(run/'LAUNCH.json')['jobs']}
report=f'''# 完整第85轮已审；有限第86轮实际续训

{stamp}，Goal active。第85轮全部三路完整结果已保存与审查；reward稳定和loss健康尚未共同成立。明确登记原协议一个有限86周期，PID `{jobs}`；三路完整state精确恢复、实际startup及{obs['elapsed']:.3f}秒观察通过，保存steps `{steps}`。冻结82及原85—87统计继续；不自动87，无Direct34。

主机 `{s['host']}`，解释器 `{B}/env/bin/python`，大checkpoint/replay/raw/runtime在共享SSD `{B}`。本轮实际ls-remote、fetch/read main `74b2d54efbfd2bdc6ac39ea6fcc6048766ec26e1`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留其他主机非RL成果，无子agent。按仓库sii-research-sync工作，发布以SSD本包PUBLICATION.json中的成功push及之后实际远端核验为准。

|第85轮方法|steps|reward均值|Task/Strict，各30|critic首→末1000|critic最大|actor首→末1000|
|---|---:|---:|---|---|---:|---|
{chr(10).join(rows)}

全部三路30个完整55秒回合、各41250新增、无abort；旧replay所有字段精确保持，全部新reward由原journal重建误差0，optimizer和network有限。完整loss独立保存算术、health、{labels['saved_rollouts_checked']}保存标签/rollout、两终端保存复核、原固定2514/all5跟踪，以及五张实际图均已检查。奖励重建不是独立重跑物理子步。

实际loss六栏图：阻抗critic均值略降但反复尖峰，actor先上拱后回到接近起点；导纳/VMC的末段出现尖峰簇且末1000均值上升，actor上漂。这和仅首5000观察的范围不同，不能用前缀替代完整周期。entropy接近原I−5/A,V−7，alpha保持有限正值、nextQ尺度没有数值崩溃；有限值并非loss健康证明，没有追加事后尖峰阈值。

全部标签变化：

{chr(10).join(changes)}

因此导纳Task14→15仍Strict14；VMC两个条件一退一进使总Strict仍16。行为不等同于相同总成功率，穿透门保持0.2mm。

|方法|采样Q超当前固定alpha全局上界|终端mask内MAE|终端mask外MAE|
|---|---:|---:|---:|
{chr(10).join(hr)}

诊断使用精确85checkpoint，网络状态保持；上界仅诊断，mask外不参与对应critic训练，终端非零误差不是新增健康门。

{chr(10).join(terms)}

同一2514固定84输入/actions/rewards/masks的前瞻85跟踪按原PLAN SHA `7703cce3f9428f187fdd796df22e540eb945411b55108cf7e8d3aaee70306494` 完成。全部5028保存行和25140 Q配对经标量重算，原数组与报告一致；没有新网络forward。所有5critic结果如下，保留改善和退化：

|方法|critic索引|84 SSE|85 SSE|mask内异号数84→85|
|---|---:|---:|---:|---|
{chr(10).join(critics)}

VMC旧84 short0600（index3478427）SSE2624.382648→328.452727，有效Q从[5.229,.228,−2.555]改善至约[−27.687,−10.844,−24.135]；相邻正reward long0400（index3478443）765.100376→733.931484，critic1仍给负值−3.207513。旧84 short0100另由0.804835恶化至122.004646；全部30新增84群体保留，四栏新图实际查看。局部误差竞争仍有残留，但85不改输入也能改善旧失败行，不能由84负梯度余弦推导“现有输入必然不可拟合”。这不是历史Adam或样本抽取因果证明。

新增完整85全部90终端的更新机会审查：绑定实际trainer的append→steps++→一次update与连续41250日志，每个终端按真实写入step和完整末step计算。VMC新Strict失败short0000在index3522137写入后仍有5113次更新机会；导纳short0600在index3520919后仍有5331次。实际minibatch包含次数未知，同一batch可重复抽样；不能解释成只剩最后一次更新，也不能断言已充分抽到。新30终端贡献分别95.5782%/87.8657%集中在这两个条件，旧样本退化同时存在。

实际有限86的科学决定（原文保留）：

{decision['reason']}

86科学trainer与85逐字相同、metadata扩展可逆；19协议+8边界负例、缺完整85/决定/LAUNCH/固定输入85真实拒绝保留。完整learner/optimizer/replay/RNG及next65536精确恢复；实际startup新增检查步数 `{sp}`，每路30sampler/MJB/旧replay/历史markers/新动作clock和reward0误差通过。86仅每方法30条件×最多55秒、最多41250新增，4m append-only、23/47历史容量标记、terminal128、batch65536、UTD1、LR/reward/masks/物理/滤波/gates不变。无自动87。

标签86/完整loss86/全回放及health86/两终端86后续已部署；终端锚点为完整85全部2544→预期86共2574，旧锚点和保存值标量复核通过。新增 `runs/recovery84_86_fixed_terminal_critic_followup_20261030_v1` 在86启动后且结果未知时前瞻登记同一2514/all5，比较84/85/86并保留全部30新84 cohort，PID{fj['pid']}/start{fj['proc_start_ticks']}，PLAN SHA `{followsha}`。复用原三checkpoint标量算法，仅推进准确轮次/计数并补cohort映射；缺完整86实际入口拒绝通过。等待原86全review和两终端成功及原进程退出，截止为原86monitor+14400秒；0新forward/physics/update，不新增健康门、不自动87。下一轮决定必须检查这项结果。

原85完成观察器自然成功，57样本/1680.389秒、27身份核验。新86连续观察7样本/{obs['elapsed']:.3f}秒、28身份保持live或原成功终止，steps单调且保存观测逐行回读。启动检查后所有后台任务继续，观察结束不重启科学。

原85—87窗口与标量bootstrap等待器继续：PLAN SHA `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`、seed2026102858、5000bootstrap、nearzero1、5%、anchor55及原4小时截止不变，当前只有完整85，86在途/87未启动。原82—84 I近零不可判、A/V失败5%，原76—78/79—81、partial75/原74—76不可判和79安全中止全部保持。两个相邻均值接近不是完整三轮窗口，也不是健康收敛。

完整85checkpoint `runs/parameter_partial75_recovery_cycle85_archive_20261029_v1/<method>/cycle_00085.pt`：

{chr(10).join(hashes)}

冻结82进度(完成条件,在途条件,动作) `{fp}`。原三evaluator/rootreview/55→82比较/独立全保存raw审计继续，仍需完整90、最终全learner/replay内存不变证明、实际图和完整比较。单动作seed2026102638/开发训练条件，不证明泛化或最终ESN排名。Direct33数值阶段接受但冻结30 Task/Strict0/0；原中断28最终内存不变证明缺失仍披露，指定ESN仍缺且不替换。

GPU {g['samples']}采样，最低{g['minimum']}%、低于50次数{g['below50']}，末值{g['last']}%。原v7 supervisor及四worker保持，即使所有科学任务结束也继续合成补载；合成负载不计科学吞吐，采样间瞬时不能保证，历史低谷保留，不是重启自启服务。

共享SSD小证据 `{a['archive']}`，{a['members']}成员/{a['bytes']}字节、SHA256 `{a['sha256']}`；逐tar成员原字节/Python AST核验，Git index/commit blob另核。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份；HDD LATEST原位保持254字节。运行日志是归档时快照。

后续先核86/冻结82/85—87/固定2514/guard原PID与start及FAILURE/FINISHED，避免重复派发。完整86后审全部结果、实际图、固定2514三checkpoint变化，再作87或科学修订的具体决定。原完整85全部失败、近零限制和未完成范围保留，Goal active。
'''
p=R/'docs'/(TAG+'.md');assert not p.exists();p.write_text(report)
entry=f'''## 2026-10-30 — 完整85与固定2514已审；有限86实际续训

- [交接](docs/{TAG}.md)。85各30×55/41250/noabort、全replay/reward0误差/loss/health/185标签/两终端/五实际图通过；reward−.590930/−8.629324/−4.586652，Task/Strict18/18、15/14、17/16。A/V末段loss上升，VMC short0600恢复但short0000新Strict失败，未收敛。
- 固定2514/all5 V总SSE9046.061→3556.825，A1283.626→3932.823；改善退化分项全部保留。新85V short0000/A short0600仍5113/5331更新机会，实际抽样未知。明确有限86决定/精确恢复/实际startup/{obs['elapsed']:.1f}秒28身份观察通过，steps{steps}；全后续及84—86固定2514跟踪已部署，无自动87，Goal active。
- GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学完成仍补载；SSD{a['members']}成员/SHA{a['sha256'][:8]}核验，非HDD/arm1全备份。main74b2d54e/baselinef6e8f8c已实际fetch/read，发布见收据，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';line,rest=p.read_text().split('\n',1);p.write_text(line+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print('Full85/86 docs and254byte pointer saved')
