# 八小时 baseline 计划与接续（2026-10-01）

窗口约05:41–13:41 UTC（13:41–21:41北京时间）。目标是可审计的有限预算baseline，不预设ESN胜出，不保证充分收敛。开工读取main3336864、baseline c918548；main无新ESN。本分支不改main、旧训练继续暂停。

## 诊断及修正

pilot01：两reward×entropy-.5/-2，seed51001，gamma.9995，Gaussian std.02 warmup，实际10k，LR预算200k。warmup访问抓取/搬运/放置，学习后新回合全approach。真实放置成功且物理有效仍因曝光不足被罚-20；该错误目标已修正。早期熵项过强和critic上界堆积另有证据，无官方loss符号颠倒。
pilot02：两reward×initial temperature .01/.0001；entropy固定-.5，其余同pilot01标准熵分支，terminal统一task_physical。.01分支隔离终末修复；.0001分支检验温度初始化。选择只用起点>=5000的完整训练回合，先两reward较低grasp率，再总grasp数，平局标准温度。warmup不计学到的成功。

## 预注册主批次

- 两reward各3配对seed61001/61002/61003，目标100k/条、UTD2、每10k checkpoint，另存episode-boundary。
- 官方SimbaV2网络/归一化/SAC；Office特定reward，不称论文通用Office奖励。
- task reward含真实完整任务成功/失败、共享势函数、时间；metric再加全子步误差、实际峰值力矩增量、弱动作变化。
- 两组共享gamma.9995/std.02探索/所选初始温度；无VMC、teacher、BC。raw48→canonical7（减速+Cartesian残差），相同WBC/filter/全action范围，不是直接关节力矩。
- 训练dt1e-4；最终55秒dt5e-5。训练variant -4/-3/-2/-1，评估6个新参数组合在已见variant0/1/2几何；不称未知办公室或真机。
- 所有六条取最大共同周期checkpoint；不按test选模。12:31UTC停止新增训练、保存checkpoint，预留70分钟评测。
- ESN已有128+128模型纯学生，与显式75%VMC+25%ESN分开重评；零动作是名义WBC诊断控制。
- 新局部柔顺推进、严格行为、完整放置、物理有效、曝光、unknown分别报告。RMSE/峰矩Nm/峰速m/s对所有失败保留。
- RL先每seed平均6条件再3seed均值/SD；ESN单权重仅条件波动，不能假造训练seed误差条。全55秒与earlyabort单列，不做混合时长排名。
- MJB/权重/源码/hash、normalizer冻结、实际时长、returncode核验；0.5/1/2倍空间阈值敏感性不选最优阈值。

## 路径与自动化

源码 /home/arm1/SII_compliance_baseline/code/mujoco_6d_vmc_benchmark/experiments/simba_behavior_20261001/
研究根 /home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/
pilot01：exploration_pilot_01/；冻结frozen_pilot_01/。
pilot02：exploration_pilot_02/；冻结frozen_exploration_pilot_02/。
主批次计划 campaign_01/；冻结frozen_main_01/。
BOOTSTRAP_STATE.json：等待pilot02→最新source的telemetry_invariance_02→主训练→共同条件评估→报告。
报告计划 campaign_01/report/REPORT.md、SUMMARY.json；生成前不是已有结果。
单run checkpoint在campaign_01/<reward>_seed<seed>/checkpoint_step_*/。

总sim并发<=4，旧1150890–1150893保持SIGSTOP。heartbeat simbav2每20分钟检查真实状态，正常不打扰，异常/完成/截止交付报告后暂停。代码/简明证据push baseline，模型/媒体/raw全部留Spark。
