from pathlib import Path
import json,datetime,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY84_COMPLETE85_RUNNING_20261030'
def read(p):return json.loads(p.read_text())
s=read(D/'SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));g=s['guard'];steps={m:r['steps'] for m,r in s['cycle85'].items()};obs=read(D/'OBSERVATION_FINISHED.json')
full=read(B/'runs/parameter_partial75_recovery_cycle84_review_20261029_v1/REVIEW.json')['methods'];health=read(B/'runs/parameter_partial75_recovery_cycle84_review_20261029_v1/health/DIAGNOSIS.json')['methods'];loss=read(B/'runs/parameter_recovery84_loss_20261029_v1/REVIEW.json')['methods'];labels=read(B/'runs/parameter_recovery84_task_labels_20261029_v1/COMPLETE83_84.json')
window=read(B/'runs/parameter_recovery82_84_reward_stability_20261030_v1/REVIEW.json');fixed=read(B/'runs/recovery82_84_fixed_terminal_critic_followup_20261030_v1/REVIEW.json');new=read(D/'NEW84_TERMINAL_CASE_REVIEW.json')['methods'];frozen=read(D/'FROZEN82_SNAPSHOT.json');decision=read(B/'runtime/recovery85_completion_preparation_20261030_v1/DECISION85.json')
rows=[];healthrows=[];hashes=[];labelrows=[];winrows=[];termrows=[];criticrows=[]
for m in ['impedance','admittance','vmc']:
 r=full[m];q=loss[m]['loss']['agent_train/q_loss'];ac=loss[m]['loss']['agent_train/actor_loss'];h=health[m];w=window['methods'][m]
 rows.append(f"|{m}|{r['steps']}|{r['reward_mean']:.9f}|{r['task']}/{r['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{ac['first1000']:.6f}→{ac['last1000']:.6f}|")
 healthrows.append(f"|{m}|{100*h['sampled_q_above_global_bound_fraction']:.8f}%|{h['terminal_q_in_bag_absolute_error']['mean']:.6f}|{h['terminal_q_out_of_bag_absolute_error']['mean']:.6f}|")
 hashes.append(f"- {m}：`{r['checkpoint_sha256']}`。")
 winrows.append(f"- {m}：nearzero={w['near_zero_guard_triggered']}，相邻变化={w['adjacent_relative_mean_changes']}，端点变化={w['endpoint_relative_mean_change']}，原5%描述检查={w['descriptive_five_percent_check']}，condition bootstrap95% delta={w['bootstrap_condition_sensitivity95_delta']}。")
 for c in labels['methods'][m]['all30']:
  if c['changed_fields']:
   cases=[{k:v for k,v in x.items() if k in ['cycle','task','strict','physical_valid','penetration_mm','abort_reason']} for x in c['cases']]
   labelrows.append(f"- {m} {c['condition']}：变化{c['changed_fields']}；{json.dumps(cases,ensure_ascii=False)}。")
for m in ['vmc','admittance']:
 t=read(B/f'runs/{m}_recovery84_terminal_followup_20261029_v1/REVIEW.json')
 termrows.append(f"- {m}：旧2484终端SSE {t['old2484_sse_before']:.6f}→{t['old2484_sse_after']:.6f}，新增30贡献{t['new30_contribution']:.9f}；新30贡献前三为 "+'、'.join(f"{x['condition']} {100*x['share_of_new30']:.3f}%" for x in new[m]['cases'][:3])+'。')
 for c in fixed['methods'][m]['critics']:
  criticrows.append(f"|{m}|{c['critic']}|{c['sse82']:.6f}|{c['sse83']:.6f}|{c['sse84']:.6f}|{c['opposite_sign82']}→{c['opposite_sign83']}→{c['opposite_sign84']}|")
fp={m:(v['progress']['completed_conditions'],v['progress']['condition'],v['progress']['actions']) for m,v in frozen['progress'].items()}
stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat()
report=f'''# 完整84与原82—84窗口已审；有限85续训

{stamp}，Goal active。第84轮三路完整结果已保存与审查，reward稳定和loss健康尚未共同成立。依据完整结果明确登记一轮85，三路精确恢复、实际startup及{obs['elapsed']:.3f}秒观察通过；保存steps `{steps}`。冻结82全90评测仍运行，无自动86/87、无Direct34。

主机 `{s['host']}`；解释器 `{B}/env/bin/python`。checkpoint/replay/raw/runtime在共享SSD `{B}`。开工真实ls-remote及fetch/read main `30d2010bb4210e6a5aaecc6b68a9110fe4d0f2c6`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；按仓库sii-research-sync执行、保留另一主机非RL工作，无子agent。发布成功以SSD本轮PUBLICATION.json的push与之后实际远端核验为准。

|第84轮方法|steps|reward均值|Task/Strict，各30|critic首→末1000|critic最大|actor首→末1000|
|---|---:|---:|---|---|---:|---|
{chr(10).join(rows)}

每路30个完整55秒条件、41250新增、无abort；旧replay全部字段保持，全部新reward由原物理区间journal重建误差0，网络与optimizer有限。完整loss独立保存算术、全标签{labels['saved_rollouts_checked']}条保存rollout、health与两个终端审查以及实际四张图均已检查。reward重建不是重新仿真全部物理子步。

全部标签变化（含Task/Strict未变而physical_valid改变）保留：

{chr(10).join(labelrows)}

实际loss六栏显示阻抗均值下降但反复尖峰、actor下降；导纳critic下降且尖峰收小，actor先降后升；VMC有39.625248孤立尖峰和末段簇、actor上漂。有限值及平均下降不是健康证明，没有追加事后尖峰阈值。

|方法|采样Q超当前固定alpha全局上界|终端mask内MAE|终端mask外MAE|
|---|---:|---:|---:|
{chr(10).join(healthrows)}

health网络状态不变、checkpoint与full review绑定。固定alpha上界仅诊断，mask外不参与对应critic训练；不把终端零误差作为新门槛。

{chr(10).join(termrows)}

上述终端跟踪锚点为83全部2484，末84为2514。另一个前瞻登记的固定2454样本跟踪只取82原锚点，逐字段绑定同一features/actions/reward/masks，对82/83/84全部5critic比较；不同分母/样本范围不能混用。原数组和独立标量保存审查通过，无额外网络forward/physics/optimizer：

|方法|critic索引|82 SSE|83 SSE|84 SSE|mask内异号数82→83→84|
|---|---:|---:|---:|---:|---|
{chr(10).join(criticrows)}

原第82—84窗口按原PLAN SHA `ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c` 完成，实际图和独立保存算术已审；原seed2026102855/5000bootstrap/nearzero1/5%/anchor55及原截止保持：

{chr(10).join(winrows)}

原标量bootstrap补充全部5000抽样以math.fsum/manual quantile复核通过；共享NumPy RNG，不是独立训练seed，也不是新收敛门。原PLAN reason有陈旧“79–81”文本，实际cycles/路径/registration_state/seed/source明确82–84；原字节不改，单独保存ORIGINAL_PLAN_TEXT_CLARIFICATION。

实际有限85决定：

{decision['reason']}

85的scientific trainer与84逐字相同，metadata扩展可逆，三路19协议+8边界负例以及实际未完整84拒绝通过。全部learner/optimizer/replay/RNG及next65536准确恢复，实际startup通过。仅每路一轮30条件×最多55秒/最多41250新增；4m append-only、23/47历史标记、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates保持。全loss/回放/health/标签/两终端后续已部署，85终端锚点2514→预期2544。旧82—84与固定2454等待器按成功收据自然结束，不以进程退出冒充成功。

新85—87非重叠窗口在85实际LAUNCH前登记：seed2026102858、5000bootstrap、nearzero1/5%/anchor55与原算法；所有85—87结果尚未知。实际85启动后才部署4小时窗口等待器及标量补充，原截止不延长。登记仅统计等待，不授权自动86/87；每一轮仍需完整结果决定。原76—78 I近零不可判/A失败/V仅reward描述通过，79—81 I描述通过/A,V失败、partial75及74—76不可判、79安全中止均保留。

完整84 checkpoint `runs/parameter_partial75_recovery_cycle84_archive_20261029_v1/<method>/cycle_00084.pt`：

{chr(10).join(hashes)}

冻结82保存进度(完成条件,在途条件,动作数) `{fp}`。原三evaluator/rootreview/55→82比较/全保存raw审计身份保持，原全90预算、action_seed2026102638、55秒/dt5e−5不变。全90结果、最终全learner/replay内存不变证明、独立保存审计、实际图及配对比较尚待；只在开发训练条件/单动作seed上验证，不证明泛化或最终ESN排名。Direct33数值阶段接受但冻结30 Task/Strict0/0，原中断28最终内存不变证明缺失继续披露；指定ESN仍缺，不替换为另一主机非RL模型。

GPU {g['samples']}样本，最低{g['minimum']}%、低于50次数{g['below50']}、末值{g['last']}%。原v7 supervisor及四worker PID/start核验，科学全部结束仍保留补载。合成负载单列，不算科学吞吐；采样不保证每瞬时，历史v6的31/33/44和v7预热0保留。这是当前主机进程，不是重启自启服务。

共享SSD小证据 `{a['archive']}`，{a['members']}成员/{a['bytes']}字节、SHA256 `{a['sha256']}`；逐tar成员字节与Python AST核验。Git force-add ignored nested runs，小证据与提交blob另核。大checkpoint/replay/raw在原SSD，非HDD/arm1全备份；HDD LATEST原位保持254字节，运行日志是快照。

后续先查85、冻结82、窗口和所有审查的PID/start、FAILURE/FINISHED与guard时效，不重复派发。85完整后审全部reward/loss/health/标签/终端和实际图，再决定下一有限轮。新85—87完整前不报稳定；冻结82全证据齐前不报完整验证，Goal active。
'''
assert not (R/'docs'/(TAG+'.md')).exists()
(R/'docs'/(TAG+'.md')).write_text(report)
entry=f'''## 2026-10-30 — 完整84/原82—84已审；有限85运行

- [交接](docs/{TAG}.md)。84各30×55/41250/noabort、完整replay/reward/loss/health/标签/两终端/四图通过；reward−.597524/−8.556481/−4.629474、Task/Strict18/18、14/14、17/16。原82—84/标量bootstrap及固定2454全部5critic已核；未收敛，历史失败保留。
- 明确有限85决定/准确恢复/actual startup/{obs['elapsed']:.1f}秒观察通过，steps{steps}；全后续部署。新85—87在85启动前登记、原算法和新seed2858、统计等待不授权86/87。冻结82完整90仍在途，无Direct34，Goal active。
- GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学结束仍合成保载；SSD{a['members']}成员/SHA{a['sha256'][:8]}逐字核验，非HDD/arm1全备份。main30d2010b/baselinef6e8f8c已fetch/read，发布见SSD收据，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';line,rest=p.read_text().split('\n',1);p.write_text(line+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();size=p.stat().st_size;assert size==254 and len(data)<=size
if len(data)<size:data+=b' '*(size-len(data)-1)+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print('Full84/85 handoff, logs and254byte HDD pointer written')
