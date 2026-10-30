# History89固定前5000与原87终端跟踪

2026-10-30 UTC，Goal active。上一轮实际续训及发布属于实质进展；本轮原89训练与冻结88持续，完成固定前5000 loss原字节/独立算术/实际图核验，并在完整89出现前登记原87全部终端all5跟踪。完整89、reward稳定和最终loss健康仍未证明，无自动90/Direct34。

执行主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。原训练、全state准确恢复、84负例/6 clone更新及真实startup详见[89在线交接](RL_HISTORY89_ONLINE_20261030.md)。本轮runtime `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_prefix_followup_20261030_v1`；训练原run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_history_cycle89_20261030_v1`，三个原learner及90sampler均未重启。

## 固定前5000实际loss

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_prefix_followup_20261030_v1/prefix5000`保存三方法原optimizer.jsonl前5000行的准确字节，读取前固定同样长度，未按loss值挑选窗口。父steps取完整88审查，连续step/每transition单update、全部指标有限、Q loss非负通过；NPZ回读独立math.fsum统计，并再与原源前缀逐字比较。

|方法|critic首→末1000均值|单次critic最大值|actor首→末1000均值|
|---|---|---:|---|
|impedance|1.850637334→1.681221605|16.777208328|21.098310787→21.147080750|
|admittance|1.193332950→1.186347319|6.414630413|-8.390161189→-8.393384604|
|vmc|0.777596097→0.785049814|7.391708374|-12.063364181→-12.054428429|

实际查看 `prefix5000.png` 六栏图并绑定hash。I Q滚动均值约1.5–2.3且有尖峰，actor轻微上移；A Q约1.1–1.4，早期6.415尖峰，actor基本平；V Q约0.7–1.0且有7.392尖峰，actor有轻微后段漂移。无NaN/Inf只支持该保存前缀数值有限，不能据此判定完整loss健康或收敛。旧88最后1000统计另列于REVIEW，不跨架构拼接旧失败窗口；此时无完整89周期reward结论。分析0新物理/0优化器更新。

## 完整89的原87固定终端预登记

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_fixed87_terminal_followup_20261030_v1`，PLAN绑定原88跟踪保存值、旧完整87初始control、89登记及科学决定、恢复源码hash。仍是I2605/A2604/V2604原87终端/all5 critic/原masks/相同51维观测、动作与reward，保留原87与完整88预测，待完整89仅新增一次各critic forward；报告每critic88→89和87→89的mask内SSE差与全行误差。不能只选择此前退化的I critic3或A critic2/3，其余改善/退化全部保留。

预检已独立复算原87/88所有保存SSE/MSE并与原报告精确一致；真实缺失完整89时强制gate拒绝，0forward/physics/update。新等待器PID `4055969` 已核验真实存活，绑定原archive监视PID3433024和原启动+14400s截止 `1793395707.748525`；完整89的review/health/loss/FINISHED全部通过才执行，分析预算1800s。目标89原checkpoint精确、全部固定输入/marker不变、full learner与RNG不变、checkpoint原hash不变均为运行强制检查；尚未出现89结果，不把准备验证写成完成。未来图生成后仍需实际查看。

此跟踪是已见终端的拟合/保留诊断，不是独立泛化、history因果证明、策略成绩或新的收敛gate；没有加载先前离线fit后的权重，不训练、不派发下一周期。

## 原作业持续与GPU

本轮180.048秒/13样本，原105个learner/sampler/归档/冻结/后处理/guard/新等待器身份保持，三路训练steps持续增加。保存时总steps `{'impedance': 3660477, 'admittance': 3662709, 'vmc': 3663789}`。完整89归档/review/health/loss仍由原3433024负责，未重复启动。

冻结88原run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1`：保存进度 `{'impedance': {'completed': 4, 'condition': 'passive_corner_train_0337', 'actions': 1000}, 'admittance': {'completed': 5, 'condition': 'passive_corner_train_0400', 'actions': 100}, 'vmc': {'completed': 4, 'condition': 'passive_corner_train_0337', 'actions': 1000}}`；原evaluator/collector/后处理继续，最终90、全state不变、raw保存审计及82→88全部配对仍待。没有重启或延长原冻结预算，前期失败保留，非held-out独立seed结论。

原v7 GPU守护保持，即使科学任务结束也继续；阈值50、控制目标70。本轮105采样min `[68, 62, 69, 68]`%、低于50 `[0, 0, 0, 0]`，末值 `[74, 93, 95, 94]`%；包含合成保载，不当科研吞吐或每瞬时保证。v7预热0、v6 31/33/44历史低谷保留，不是重启自启服务。

## 保存和未完成项

实际query/fetch/read main `b17dfd17f72ea243643359daa379f4a7e69313e0`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关变更。沿用sii-research-sync，无子agent。小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY89_PREFIX_FOLLOWUP_20261030/SMALL_EVIDENCE.tar.gz`，42成员/1444472字节，SHA256 `6e77ef8d0319c192f96fdd74b3de48d66cd6e649a4e3e9f7ca0a10a3d4d54578`，tar逐成员和Python AST已核；Git index/commit逐字核验后normal push与实际远端确认，包外PUBLICATION记录。

HDD只原位更新254字节LATEST；大checkpoint/轨迹留共享SSD，非HDD/arm1全备份。Direct33数值接受但冻结30 Task/Strict0/0、28中断缺最终内存不变；指定ESN未提供且不替代；partial75、74—76不可判、79安全中止、全部旧稳定性失败、半std失败及所有软件失败继续披露。88—90方案只有88完成/89运行/90未派发，先审完整89再作有限后续决定。Goal active。
