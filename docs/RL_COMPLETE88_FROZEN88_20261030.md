# 完整88已审；冻结88全90评测实际运行

2026-10-30 UTC，Goal active。本轮原三个训练进程均正常完成唯一有限history88周期并停止，完整检查、固定终端比较和四张实际图已核。reward稳定与loss最终健康尚未证明；当前新科学作业是已预登记的冻结88三方法×30条件，尚未训练89/90或Direct34。

实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。原启动及所有失败见[88在线交接](RL_HISTORY88_ONLINE_20261030.md)，更新后快照恢复见[上一交接](RL_HISTORY88_FROZEN_READY_20261030.md)。

## 完整88结果

原活动汇总 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle88_20261030_v2`；完整静态checkpoint `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle88_archive_20261030_v2`；完整审查 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle88_review_20261030_v2`。三路各30×55s、41250新transition/更新，0abort；总新增123750。原10,824,948行的旧字段与历史列全部保留精确，完整88合计10,948,698行；新51维current/next、raw→mixed动作映射、全部reward重构最大误差均0。网络/优化器有限，原LR/reward/masks、batch65536/UTD1、4m append-only和23/47标记、terminal128、actor49/canonical48及物理/gates/filter/dt保持。

|方法|完整总steps|平均reward|Task/Strict（各/30）|critic loss首→末1000均值|最大单次critic loss|
|---|---:|---:|---:|---|---:|
|impedance|3647698|-2.375353897|18/17|2.757372→1.683260|39.466644|
|admittance|3650000|-5.201837297|16/16|1.343984→1.135157|7.902052|
|vmc|3651000|-2.815045946|17/17|1.268404→0.860563|22.221096|

`health/training_diagnostics.png`、`loss/loss88.png`、`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_completion_20261030_v1/training87_88_all90.png` 均已实际查看并绑定hash，PLOT_INSPECTION在完整review目录。critic滚动均值下降，有限尖峰仍在；I/A actor loss缓慢上移、V小幅漂移，entropy接近登记target，alpha有限。单个history周期不是稳定窗口；不以有限/下降代替完整收敛判断。health terminal_count为I2635/A2634/V2634，含原I多1条；报告mask内与mask外误差，不能把混合误差当统一训练目标。全局soft bound诊断超界分数I0、A0.000244140625、V0.0029785155784338713，保留该非零结果；必要界诊断不是新的通过判据。

原87→88全90训练配对 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_completion_20261030_v1/INTERPRETATION.json`：I mean+1.841153883，Strict增加short0100；V mean+1.774734458，Strict增加short0600，二者无标签损失。A mean+3.360302619，Strict增加short0600/long0200/long0900，但 **short0900 Task/Strict均由通过变失败**，终态retreat→carry，reward16.568644293→−33.434595599，差−50.003239891；该退化完整保留。A净Task+1/Strict+2。均值增加主要来自terminal项；奖励分项分解仅算术，不证明history因果或泛化。

## 固定原87终端的完整88跟踪

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history88_fixed87_terminal_followup_20261030_v1`：完整88前登记，原87全部终端I2605/A2604/V2604、all5 critic、原观测/动作/reward/masks及历史列逐值一致。基线只用先前保存的initial_control（未拟合原87），不读final拟合权重、不晋升克隆。全learner/RNG不变，0新物理/更新，保存预测独立标量重算和实际图通过。

原mask内SSE，V五critic全改善；I critic3退化429.293186669，A critic2/3退化195.554795199/320.091349370，其余改善。全部终端/全部critic SSE总和I344406.079→316900.645、A182348.127→168221.366、V173003.845→139445.078；全行包含故意mask外样本，非独立泛化。history置零敏感性仅同模型输入检查，不能当架构因果或实际策略成绩。首版等待器的路径类型失败和v2修复记录继续保留，v2本轮正常完成。

## 已实际启动冻结88

唯一活动run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1`；冻结源 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_frozen_preparation_20261030_v1`；调度/汇总 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_frozen_dispatch_20261030_v1`。完整review/health/loss/实际图前置全部通过后生成最终登记；三份完整88 check-only的全learner/replay精确恢复、RNG gate、checkpoint/source hash通过，随后单独执行launch。不同于此前partial软件预检，本轮确实已开始物理评测。

原已登记预算：3×全部30训练条件、seed2026102638（同冻结82）、每回合最多55s，总最多123750动作/9900万子步，0optimizer更新/正式replay写入。evaluator PID和start见 `LAUNCH.json`；CPU I7/A8/V9、GPU cuda:0。90.019秒/10样本的原evaluator和watcher身份、实际物理CPU绑定/进度观察通过。保存时进度 `{'impedance': {'condition': 'passive_corner_train_0000', 'actions': 900, 'completed': 0}, 'admittance': {'condition': 'passive_corner_train_0000', 'actions': 900, 'completed': 0}, 'vmc': {'condition': 'passive_corner_train_0000', 'actions': 900, 'completed': 0}}`。全90结果及最终内存不变证明仍待，不提前写成完成。

后处理 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history88_frozen_postprocess_20261030_v1` 已实际等待原collector；全部90的saved raw审计 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_saved_audit_20261030_v1`，同seed冻结82→88配对在 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1/comparison82_88`。预先核过所有条件、原physics/reward一致；原始audit子步hash/count×dt/力矩/接触/奖励复算及全部增益退化均保留。它不重新积分动力学；82→88含新增训练和history修订，不能单独归因。collector原最长21600秒等待；后处理不自动延长/重启评测。首批根REVIEW和全raw/配对输出出现后，需要实际看最终图并核验最终全state不变。

下一步继续完成冻结88并据完整88（含旧终端三critic退化与Ashort0900失败）作明确有限后续决定。未来88—90稳定性方案仍只有原预登记；未派发89/90，不跨revision合并旧失败窗口。

## GPU、归档和恢复

原v7 supervisor97370与四worker继续。窗口含三路训练结束的过渡，418采样min `[71, 67, 65, 64]`%、低于50 `[0, 0, 0, 0]`，末值 `[80, 71, 70, 80]`%；含合成保载，不冒充训练吞吐，科研全部结束仍保载。历史v7预热0及v6 31/33/44低谷保留；采样不保证每瞬时，非重启服务。

本轮起始实际query/fetch/read main7ae9d9af/baselinef6e8f8c，收尾main新增c5f5f9d7（另一主机v7推理契约、局部支持、时间线及训练拟合诊断），已阅读相关日志/报告并fast-forward保留，不替代本机指定ESN模型。沿用sii-research-sync，无子agent。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_COMPLETE88_FROZEN88_20261030/SMALL_EVIDENCE.tar.gz`，129成员/6129355字节，SHA256 `22003725c5c722bb3367a4283d610ee7aac8aea0521795ccb6517b474a10c362`，tar逐成员与Python AST校验；Git index/commit另核，成功normal push并实际ls-remote后包外PUBLICATION。raw.diff原件上下文空格精确保留，whitespace例外仅这些原件。大checkpoint/轨迹仍共享SSD，完整88三checkpoint SHA见收据；HDD仅原位更新254字节LATEST，非HDD/arm1全备份。

Direct33数值阶段接受但冻结30 Task/Strict0/0，28中断缺最终内存不变证明；指定ESN仍不可用，既有询问不重复、不替换他主机模型。partial75、74—76不可判、79安全中止、所有旧窗口失败（含85—87）、半std失败和未推广、88初次准备/LR误拒/只读父轮号失败全部保留。Goal active。
