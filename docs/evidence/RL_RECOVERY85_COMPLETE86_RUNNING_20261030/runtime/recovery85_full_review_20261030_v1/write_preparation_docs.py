from pathlib import Path
import json,datetime,os
B=Path(__file__).resolve().parents[2];D=Path(__file__).parent;R=B/'repository/SII_compliance';TAG='RL_RECOVERY85_CAUSAL_HISTORY86_READY_20261030'
read=lambda p:json.loads(p.read_text())
s=read(D/'PREPARATION_SAVE_SNAPSHOT.json');a=read(R/'docs'/(TAG+'_SAVE.json'));g=s['guard'];steps={m:r['steps'] for m,r in s['cycle85'].items()};obs=read(D/'OBSERVATION_SNAPSHOT_REVIEW.json');frozen=read(D/'FROZEN82_SNAPSHOT.json');diag=read(B/'runs/recovery84_causal_history_audit_20261030_v1/REVIEW.json')
fp={m:(v['progress']['completed_conditions'],v['progress']['condition'],v['progress']['actions']) for m,v in frozen['progress'].items()}
stamp=datetime.datetime.fromtimestamp(s['time'],datetime.timezone.utc).isoformat()
text=f'''# 第85轮继续：84历史穿透信息审查完成，86决策入口仅准备

{stamp}，Goal active。原85三路继续，保存steps `{steps}`，尚未收齐完整85结果。86的完整审查、决定、派发入口及后续标签/终端工具已准备并验证拒绝缺失前置；没有86决定或训练，实际86全state恢复完成={s['actual86_restore_complete']}。“READY”文件名只指入口准备，不代表科学准入通过。reward稳定与loss健康尚未共同成立。

主机 `{s['host']}`，解释器 `{B}/env/bin/python`；大checkpoint/replay/raw保留共享SSD `{B}`。本轮实际ls-remote、fetch/read main `3d3b5caeb50121e58a0fa397ef640d86cfe158a4`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未有新远端科学变化；此前一次fetch TLS握手失败后重试成功，本次再次fetch成功。按仓库sii-research-sync工作，保留非RL成果，无子agent。发布以SSD本包PUBLICATION.json的实际push与随后远端核验为准。

新增只读诊断 `runs/recovery84_causal_history_audit_20261030_v1`。这是对已完成84数据的回顾审查，登记前已经查看VMC short0600一例；PLAN没有冒充采集数据前预登记。随后固定三方法全部30条件，共90回合、123750动作，不只选择失败回合。预算600秒/CPU53，第一遍实际{diag['elapsed_s']:.3f}秒；0新物理、0网络forward、0optimizer/replay写入。

已绑定原SOURCE_HASHES中的episode adapter/evaluator/reward源码。源码中累计外穿透从0初始化，仅新更大值才更新。每物理子步sample记录这个累计值；下一次act先调用interval并发送到learner，然后才读取动作并写journal。因此row0 interval=None且无已执行物理区间时历史峰值为0；row i>0的interval只含动作i之前已经完成的区间。terminal.interval只作为最后一个transition的next信息，不能回填最后动作的preaction输入。

全部90回合：1375原journal行、每区间800子步/.04秒、原始48维观测与执行动作对rollout数组逐位一致；累计峰值非负/有限/单调。累计区间时间与neuron_time误差小于预登记1e−6秒，终点峰值与rollout.stats完全一致；Task/Strict/physical/abort等原标签交叉核对。保存90个派生npz，包含每次动作的时间、preaction历史峰值、next峰值及原0.2mm穿透门状态。随后独立按行和math.fsum回读全部123750动作、输入/输出hash与时间/峰值/首次越界位置检查通过，实际四栏图已查看。

|方法|全部回合|最终穿透超限|动作之前已知超限|仅最后动作后才超限|Task真/Strict假|
|---|---:|---:|---:|---:|---|
|impedance|30|0|0|0|无|
|admittance|30|1|1|0|无|
|vmc|30|1|1|0|short0600|

两个超限回合均为active_short_train_0600；第一条已知超限preaction为零基row96、约3.84秒，发生越界的transition为row95。导纳最大0.224348509mm，Task/Strict=false/false；VMC最大0.219398094mm，Task/Strict=true/false。每例后续1279次动作已有历史超限信息，最终preaction和terminal峰值相同；这明确排除了这两个案例“只有最终一步才知道穿透失败”的解释。已有84critic输入/梯度诊断仍保持：没有显式累计穿透历史，部分近邻异号目标局部回归方向相反。

该证据只证明第84轮保存journal与源码的因果可用性及一致性，不是独立重新计算物理子步穿透。现有substep_metrics没有穿透数组；不宣称全历史约350万条replay都能重建，也不证明加历史信息必然改善拟合或是Adam漂移唯一原因。没有修改actor canonical48、critic输入、奖励/门或原85—87统计。若后续探索privileged critic历史特征，仍须另登记科学修订、检查全部旧replay可重建性与公平协议；当前输入差异/局部负余弦不能单独授权变更。

`runtime/recovery86_completion_preparation_20261030_v1` 新decision86要求完整85的replay/reward/health/loss/全部标签/两终端/四张实际图，精确86全learner/replay/RNG/next65536恢复，并继承DECISION85的完整证据链；另外强制原完整82—84/独立bootstrap/固定2454全部critic结果，以及完整85时固定2514输入的84→85跟踪。原85—87 PLAN SHA `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e` 绑定保持；无自动87。

原require_completed82_84函数逐字一致，完整30×55/41250/noabort前置不放松。缺完整85、缺DECISION86、缺实际LAUNCH86和缺fixed2514输入85结果，四个真实入口拒绝均保存。初版生成器误匹配函数定义，被逐字断言提前挡下；原源码与PREPARATION_SOURCE_FIX.json保留，修为准确调用加换行匹配后通过，无科学运行受影响。没有CONTINUATION_REASON或DECISION86。restore86等待器仍是原1064870，科学trainer同85、19+8负例等已在上一交接发布，不重复派发。

`runtime/recovery86_followups_20261030_v1` 仅生成helper：旧85终端锚点2544→预期86共2574，数字AST只改轮次和计数，缺实际86LAUNCH的真实执行在输出前拒绝。未部署后续任务。`runtime/recovery85_full_review_20261030_v1` 另准备完整85汇总/全部新增终端贡献/冻结82快照只读工具；保留原82—84和固定2454历史结果，不复跑旧科学。

原完整85固定输入跟踪 `runs/recovery84_85_fixed_terminal_input_followup_20261030_v1` 仍等待完整85及两终端成功：固定2514/all5 critic、完整30新增84 cohort、原PLAN SHA `7703cce3f9428f187fdd796df22e540eb945411b55108cf7e8d3aaee70306494` 不变，未得到完整结果前不作86决定。

完成观察器PID2235579/start573326633，原27身份保持live或成功收据终止。保存时{obs['samples']}样本、覆盖{obs['elapsed']:.3f}秒，原steps单调，记录逐行回读；观察器仍运行，有限3600秒，无自动重启或派发。观察超时不是科学失败或重新启动理由。

冻结82进度(已完成条件,在途条件,动作) `{fp}`，原三evaluator/rootreview/比较/全保存raw审计身份保持。仍需完整90、最终全learner/replay内存不变证明、独立保存审计、实际图和55→82比较。原55秒/dt5e−5、单动作seed2026102638与开发训练条件不改，不宣称泛化/最终ESN排名。

保持上一交接全部限制：完整84reward−.597524/−8.556481/−4.629474、Task/Strict18/18、14/14、17/16；原82—84 I近零不可判，A/V失败5%。原76—78/79—81、partial75/74—76不可判、79安全中止仍保留。Direct33数值阶段接受但冻结30 Task/Strict0/0，无Direct34；原中断28最终内存不变证明缺失保留。指定ESN仍缺，不替换其他主机模型。

GPU原v7 supervisor及四worker继续；{g['samples']}样本最低{g['minimum']}%、低于50次数{g['below50']}，末值{g['last']}%。用户明确要求科学完成后继续占用，已继续保留；合成占用不记为科学吞吐。采样间瞬时不能保证，历史v7预热0及v6低谷保留，不是系统重启自启服务。

共享SSD小证据 `{a['archive']}`，{a['members']}成员/{a['bytes']}字节、SHA256 `{a['sha256']}`，逐tar成员字节/源码AST核验；Git index/commit blob另核。大raw/replay/checkpoint仍原SSD，非HDD/arm1全备份。HDD LATEST原位保持254字节，已归档的运行日志是快照。

下一步先核对85/冻结82/restore86/固定2514/原85—87/guard原身份与FAILURE/FINISHED时效。完整85结束后审全reward/loss/health/标签/终端与四实际图，尤其同2514的预测是否继续竞争或恢复，再明确作下一有限阶段决定。不要只凭85前缀、梯度余弦或本次历史可用性审查直接启动86或变更模型。Goal保持active。
'''
p=R/'docs'/(TAG+'.md');assert not p.exists();p.write_text(text)
entry=f'''## 2026-10-30 — 84因果历史信息审查完成；85继续、86入口仅准备

- [交接](docs/{TAG}.md)。完整84全部90回合/123750动作的preaction历史穿透、原观测/动作/时间/标签/hash及独立标量回读与四栏实际图通过。A/V short0600均row96/3.84s已知超限、后1279动作可用；非独立物理重建/全历史replay覆盖或模型修订。
- 86decision强制完整85/全部图/精确恢复/原82—84及固定2514输入85结果，四缺前置真实拒绝通过；生成器误匹配由断言挡下后修复并留证。86标签/终端2544→2574仅准备未部署，无86决定/训练。原85steps{steps}，{obs['samples']}样本/27身份保持；冻结82/85—87继续，Goal active。
- GPU{g['samples']}样本min{g['minimum']}%、低于50{g['below50']}，科学完成仍补载；SSD{a['members']}成员/SHA{a['sha256'][:8]}核验、非HDD/arm1全备份。main3d3b5cae/baselinef6e8f8c实际fetch/read，发布见收据，无子agent。

'''
for name in ['UPDATE_LOG.md','HANDOFF.md']:
 p=R/name;p.write_text(entry+p.read_text())
p=R/'AGENTS.md';line,rest=p.read_text().split('\n',1);p.write_text(line+'\n\n'+entry+rest.lstrip('\n'))
p=R/'docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md';p.write_text(entry.replace('(docs/','(')+p.read_text())
p=Path('/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md');data=(str(R/'docs'/(TAG+'.md'))+'\nGoal active; SSD assets.\n').encode();assert p.stat().st_size==254 and len(data)<=254
if len(data)<254:data+=b' '*(253-len(data))+b'\n'
with p.open('r+b') as f:f.write(data);f.flush();os.fsync(f.fileno())
assert p.read_bytes()==data and p.stat().st_size==254
print('Docs and254byte pointer saved')
