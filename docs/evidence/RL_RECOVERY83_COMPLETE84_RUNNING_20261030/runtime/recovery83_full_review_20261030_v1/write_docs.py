from pathlib import Path
import json,datetime,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY83_COMPLETE84_RUNNING_20261030'
def read(p):return json.loads(p.read_text())
s=read(D/'SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));steps={m:r['steps'] for m,r in s['cycle84'].items()};g=s['guard'];stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat()
full=read(B/'runs/parameter_partial75_recovery_cycle83_review_20261029_v1/REVIEW.json')['methods'];health=read(B/'runs/parameter_partial75_recovery_cycle83_review_20261029_v1/health/DIAGNOSIS.json')['methods'];loss=read(B/'runs/parameter_recovery83_loss_20261029_v1/REVIEW.json')['methods'];labels=read(B/'runs/parameter_recovery83_task_labels_20261029_v1/COMPLETE82_83.json');terms={m:read(B/f'runs/{m}_recovery83_terminal_followup_20261029_v1/REVIEW.json') for m in ['vmc','admittance']};new=read(D/'NEW83_TERMINAL_CASE_REVIEW.json')['methods'];frozen=read(D/'FROZEN82_SNAPSHOT.json');obs=read(D/'OBSERVATION_FINISHED.json')
rows=[];hashes=[];healthrows=[];terminalrows=[]
for m,title in [('impedance','阻抗'),('admittance','导纳'),('vmc','VMC')]:
 r=full[m];q=loss[m]['loss']['agent_train/q_loss'];ac=loss[m]['loss']['agent_train/actor_loss'];h=health[m]
 rows.append(f"|{title}|{r['steps']}|{r['reward_mean']:.9f}|{r['task']}/{r['strict']}|{q['first1000']:.6f}→{q['last1000']:.6f}|{q['maximum']:.6f}|{ac['first1000']:.6f}→{ac['last1000']:.6f}|")
 hashes.append(f"- {title}：`{r['checkpoint_sha256']}`。")
 healthrows.append(f"|{title}|{100*h['sampled_q_above_global_bound_fraction']:.8f}%|{h['terminal_q_in_bag_absolute_error']['mean']:.6f}|{h['terminal_q_out_of_bag_absolute_error']['mean']:.6f}|")
for m,r in terms.items():
 terminalrows.append(f"{m}旧2454终端masked SSE {r['old2454_sse_before']:.6f}→{r['old2454_sse_after']:.6f}，比值{r['old2454_sse_ratio']:.6f}；新增30贡献{r['new30_contribution']:.9f}，前三贡献为 "+'、'.join(f"{x['condition']} {100*x['share_of_new30']:.3f}%" for x in new[m]['cases'][:3])+'。')
fp={m:(v['progress']['completed_conditions'],v['progress']['condition'],v['progress']['actions']) for m,v in frozen['progress'].items()}
text=f'''# 完整83已审；有限84续训与冻结82评测继续

{stamp}，Goal active。第83轮三路完整审查完成，尚未证明reward稳定且loss健康共同成立。明确登记有限第84轮后，三路精确恢复、实际startup与{obs['elapsed']:.3f}秒观察通过，保存时steps `{steps}`。冻结82完整90评测继续，最终结果/完整内存不变证明/55→82比较尚待；不启动Direct34，不自动派发85。

实际计算主机 `{s['host']}`，解释器 `{B}/env/bin/python`。checkpoint、replay、raw、runtime均在共享SSD `{B}`。开工实际ls-remote、fetch/read main `155a4c4c74201e78bd38548021418944b575fc32` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，保留另一主机非RL工作；按仓库sii-research-sync执行，无子agent。最终发布以SSD本轮PUBLICATION.json中的成功push及随后实际远端核验为准。

|第83轮方法|steps|reward均值|Task/Strict，各30|critic首→末1000|critic最大|actor首→末1000|
|---|---:|---:|---|---|---:|---|
{chr(10).join(rows)}

各30完整55秒/41250新增、无安全中止；旧replay所有字段精确保持，每条新reward由原物理区间journal重建误差0，optimizer与网络全部有限。完整loss独立保存算术、health、全标签{labels['saved_rollouts_checked']}个保存rollout、两终端及实际四张图全部检查。reward重建不冒称重新仿真全部物理子步。

阻抗short0100 Task仍成功，但相关穿透0.149640→0.210033mm导致physical_valid/Strict失败，Strict17→16，reward均值−2.389068→−4.174417。导纳short0200和long0300恢复Task/Strict成功，同时short0900失去Task/Strict、short0000穿透0.138090→0.207785mm而失去Strict；Task11→12、Strict11不变，reward−13.677125→−13.596636，不能称全面改善。导纳short0600的Task/Strict本来已失败，physical_valid另由真变假，穿透0.198826→0.235936mm，也完整保留。VMC标签17/17不变、reward−2.805262→−2.810608。原55秒、0.2mm合规门和2mm安全中止门保持，不以较小超限删除失败。

实际loss图显示I反复尖峰和末段均值升高、actor持续下降；A有孤立78.689468尖峰和末段簇，actor先降后部分回升；V末段43.236988尖峰且actor持续上漂。所有值有限并不证明健康收敛，也不把有限尖峰擅自设成新拒绝阈值。健康图、固定alpha诊断与两终端图实际查看记录独立保存。

|方法|采样Q超当前固定alpha全局上界|终端mask内MAE|终端mask外MAE|
|---|---:|---:|---:|
{chr(10).join(healthrows)}

mask外行未参与对应critic训练；当前Q上界是固定policy/alpha诊断，终端误差不是新设零误差门。健康forward的网络状态不变，各方法checkpoint SHA绑定完整83审查。

{chr(10).join(terminalrows)}

VMC旧终端SSE总量增至5.394288倍，原focus2423122却从2896.964431改善至1.428606，其他历史行明显退化；不能以单个focus改善代表总体。导纳旧SSE总量降至0.243208倍，但原focus2752093从9.374596增至17.139708。两终端保留完整旧2454锚点、30新终端、原和新回放分母、原focus及逐condition映射。新贡献由保存values.npz独立math.fsum核对，不做新网络forward或physics；它定位末checkpoint误差，不重建历史minibatch或证明策略变化因果。

完整83 checkpoint路径 `runs/parameter_partial75_recovery_cycle83_archive_20261029_v1/<method>/cycle_00083.pt`：

{chr(10).join(hashes)}

新增第81→82行为与终端时序审查位于 `runs/recovery81_82_terminal_behavior_alignment_20261030_v1`。全部90条件配对、A/V全部60终端配对、stage事件和标签、mask内SSE/贡献已核；不同轮次状态/动作/mask与采集时策略不同，不能把配对当相同输入或因果实验。导纳82 long0300到54.92秒才进入load_transfer、hold0，Task失败；终端reward−28.32657，四个mask内Q仍正，SSE6648.77787。其replay index3402499恰是本轮最后一条，原trainer append→steps++→一次update及完整41250连续optimizer日志证明，写入后仅有一次更新机会；long0200两次。实际minibatch是否抽到样本未记录，同一batch也可重复抽样，故不能声称经过充分训练后仍拟合失败。short0200原82 release54.36/retreat54.88、hold.32低于原.5秒要求，XY4.04mm也不满足成功。原阈值/55秒保持。

该只读诊断保存全部90新终端更新机会，未做forward、优化、replay写入或新物理；2×2实际图已查看，SSE轴下界修正为0后重绘并核hash。图中旧81/新82都在完整82 checkpoint上评估，不能作为同一终端跨checkpoint学习曲线。原不合适负symlog刻度是出图问题，未改科学数值。

冻结进度快照helper初稿假设全部LAUNCH使用proc_start_ticks，但原evaluator使用start字段，输出前KeyError；已保留初稿并按原观察器兼容两字段、仍逐字核实际/proc身份，无科学重启。new_terminal_cases helper第一次调用时VMC保存值审查尚未落盘，入口因缺SAVED_VALUES_REVIEW正确拒绝，尚未计算或写输出；保留EARLY_TERMINAL_CASE_ATTEMPT，待原审查成功后再运行，无科学重启。

第84轮 `runtime/recovery84_completion_preparation_20261030_v1/DECISION84.json` 绑定完整83/四实际图/精确恢复、原76–78和79–81结果、原82–84 PLAN及原bootstrap标量补充。全learner/optimizer/replay/RNG和next65536准确恢复，三路实际startup及全部后续派发通过。每方法仅一轮30条件×最多55秒、最多41250新增；4m append-only、历史23/47容量标记、partial75、terminal128、batch65536、UTD1、LR/reward/masks/physics/filter/gates不变。84标签与终端跟踪已部署，旧83锚点2484、预期完整84终端2514；观察核验全部原身份和进度单调。无自动85。

原76–78 I近零不可判/A失败5%/V reward描述通过但loss健康未证；原79–81 I描述通过/A,V失败。原74–76因partial75不完整仍不可判，原79阻抗安全中止保留。原82–84 PLAN SHA `ec47d7a5d8b3f04f1fcb88f5901888baa1e20931bdee97a12021316b8c8e728c` 保持，seed2026102855、5000bootstrap、nearzero1和5%规则及原截止不变；原等待器及标量审计继续，不在84完成前给窗口结论。

冻结82仍按原30条件×3方法全90执行，action_seed2026102638、55秒/dt5e−5、最多123750动作/99000000子步。保存时(已完成条件,在途条件,动作数)为 `{fp}`。三evaluator、rootreview、55→82比较及新完整保存审计等待器PID/start核验，原进程未重启。新增 `runs/parameter82_frozen_full_saved_audit_20261030_v1` 在已知前2失败且评测运行时登记，全部原90纳入、不按结果筛选；真正缺root REVIEW拒绝已验证。必须等原rootreview完成退出、全90结果和三个最终全learner/replay内存不变证明，再独立核原raw hash、count×dt时长/接触/舒适分母、峰矩/穿透、reward与gate。原rootreview+21600秒截止不延长；当前只是等待，不是已通过审查。

冻结82是开发训练条件/单动作seed，不能证明泛化或最终ESN排名；无人体接触时舒适为NA。Direct33数值阶段接受、冻结全30 Task/Strict0/0，原中断28最终内存不变证明缺失继续披露，不重跑旧28、不启动34。指定ESN仍缺，不能用另一主机非RL模型替代；最终公平比较未完成，Goal active。

GPU保存{g['samples']}样本，最低{g['minimum']}%、低于50次数{g['below50']}、末值{g['last']}%。原v7 supervisor97370/start570509460及四worker97399–97402/start570509475核验；即使科学完成仍合成保载。含补载不算科研吞吐，采样不保证每瞬时；历史v6的31/33/44及v7预热0保留。这是当前主机进程，不是重启自启服务。

共享SSD小证据 `{a['archive']}`：{a['members']}成员/{a['bytes']}字节，SHA256 `{a['sha256']}`，tar每成员原字节和Python AST已核；Git强制纳入ignored nested runs。大checkpoint/replay/raw仍原SSD，非HDD/arm1完整备份。HDD LATEST原位更新且保持254字节；运行日志以快照保存。

下次先查guard及84/冻结82/窗口/所有审查的原PID与start、最新进度、FAILURE/FINISHED；不要重复派发。完整84之后审全reward/loss/health/标签/两终端和实际图，读取原82–84完整窗口与标量复核，再决定下一有限阶段；不自动85。冻结82收齐90后检查最终内存不变证明、独立保存审计、实际结果图和55→82比较。保持历史失败、ESN缺口及Goal active；发布前再次fetch/read并保留另一主机工作。
'''
(R/'docs'/(TAG+'.md')).write_text(text)
entry=f'''## 2026-10-30 — 完整83已审；84续训与终端时序诊断

- [交接](docs/{TAG}.md)。83各30×55/41250/noabort、全replay/reward/loss/health/标签/两终端/四图已审；I/A/V reward−4.174417/−13.596636/−2.810608、Task/Strict18/16、12/11、17/17。阻抗新Strict失败、导纳改善与退化并存，尖峰55.21/78.69/43.24全部保留，未收敛。
- 81→82全90行为/60终端与实际图核验：A82 long0300写入后仅一次更新机会，实际抽样未知，不据末误差断言充分拟合失败。明确有限84决定/准确恢复/actual startup/{obs['elapsed']:.1f}秒观察通过，steps{steps}，全部后续已部署。冻结82及原82–84继续，新全90保存审计等最终内存不变证明；无自动85/Direct34，Goal active。
- GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学结束仍合成保载；SSD{a['members']}成员/SHA{a['sha256'][:8]}逐字核验，非HDD/arm1全备份。main155a4c4c/baselinef6e8f8c已fetch/read，发布见SSD收据，保留非RL，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';line,rest=p.read_text().split('\n',1);p.write_text(line+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();size=p.stat().st_size;assert size==254 and len(data)<=size
if len(data)<size:data+=b' '*(size-len(data)-1)+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print('Detailed report, AGENTS/log/HANDOFF/primary and254byte pointer written')
