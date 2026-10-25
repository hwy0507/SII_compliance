# 同样本 Bellman 目标分解：CHEQ 第9→10轮（2026-10-25）

在完全相同的第9轮历史观测/动作上，第10轮四接口Q均明显转负；固定相同next-action时，critic间分歧及pair-min与all5-min差距均扩大。这排除了“仅因两次诊断抽取不同replay样本”对本次比较的解释，但不等于证明真实价值低估或all5是唯一原因。负soft-Q本身允许出现，尤其连续动作的微分熵可为负。当前第11轮保持原登记，不据这份诊断中途改变学习器。

## 比较范围与验证

新增 `tools/diagnose_published_matched_targets_20261025.py`。四接口各取4096个第9轮非终端样本，加其全部348个终端样本；确认这些索引的全部字段（含observations内混合context、actions、rewards、dones、Bernoulli masks）在第10轮replay中逐字节相同。两checkpoint的target critics读取同一第9轮policy生成的next actions；另以匹配随机种子分别采样各自policy的next actions，分解其目标。两个policy不同，因此“自身policy”分栏不称动作相同。

pair-min为全部10个不同critic pair的最小值的精确平均；all5为5个critic的最小值。固定动作栏隔离了评估动作差异，仍不能把在线训练before/after视为只改变一个变量的反事实实验：两轮网络、alpha、policy均已更新。

运行进程3520396已退出，四JSON与SUMMARY一致。八个不可变checkpoint文件、登记source/input hashes再次核验；网络tensor未变、无梯度、0 optimizer更新、0新增physics，父replay未变。终端bootstrap为0、不求值其next-state占位。组件均值加和与gamma×pair/all5差核验通过。图 `MATCHED_TARGETS.png` 已目视检查。冻结source14、live learner及source16候选均未修改。

## 相同观测与动作下的变化

| 接口 | 历史动作Q均值：9→10 | 同一父next-action的critic std：9→10 | 同一父next-action的pair-min减all5-min：9→10 |
|---|---:|---:|---:|
| direct | 1230.40 → -4228.21 | 15.95 → 163.14 | 9.97 → 97.93 |
| impedance | 5982.32 → -16636.60 | 56.43 → 208.50 | 36.21 → 135.48 |
| admittance | 2087.96 → -12102.74 | 24.07 → 137.35 | 15.42 → 90.27 |
| vmc | 12680.29 → -17615.20 | 119.71 → 207.87 | 74.59 → 140.16 |

这里的std是逐样本五critic标准差再平均（ddof=1），不是跨样本回报方差。CHEQ混合规则使用raw ensemble std，Q正负号本身不改变规则；本报告没有重新测量混合权重分布。

## 第10轮自身policy的非终端目标

对这4096个非终端样本，`y = r + gamma*(-alpha*log_pi) + gamma*min_i Q_target(s_next,a_next)`，gamma=0.9995。

| 接口 | 即时reward均值 | 折扣熵项均值 | 折扣未来all5-Q均值 | all5目标均值 | pair→all5使目标额外降低 |
|---|---:|---:|---:|---:|---:|
| direct | -0.00566 | -52.00087 | -4185.88903 | -4237.89555 | 389.45311 |
| impedance | -0.00193 | -10.51145 | -16624.69084 | -16635.20422 | 131.43115 |
| admittance | -0.00249 | -9.59777 | -12123.49083 | -12133.09109 | 95.79262 |
| vmc | -0.00257 | -34.45636 | -17577.17314 | -17611.63207 | 141.06924 |

最后一列是两种目标的差，已经包含在all5未来Q选择中，不能再加到前四列上。四路该差均大于平均熵项绝对值和非终端平均即时reward绝对值，说明critic间分歧对目标选择的影响值得跟进；不意味着即时任务奖励不重要。本样本分栏不含±25终端奖励，微分熵为负也不是非法值。

Direct alpha从0.45643增至6.98792；其自身policy动作对应目标的pair/all5差389.65，固定父动作仅97.93，表明动作选择也明显影响所测分歧。不能把两种分栏混合后归因为单一target规则。

| 接口 | all5目标减历史Q：有符号均值 | 五critic对all5目标的平均绝对差 | 同一348终端样本MAE：9→10 |
|---|---:|---:|---:|
| direct | -9.69 | 120.69 | 584.06 → 2995.07 |
| impedance | 1.40 | 219.41 | 3067.68 → 6872.59 |
| admittance | -30.35 | 165.59 | 4157.38 → 9033.47 |
| vmc | 3.57 | 214.06 | 13049.82 → 7916.90 |

有符号均值接近0可由正负误差相消，不能当作逐样本Bellman误差很小。终端MAE前三升、VMC降；无remaining-time输入带来终端状态混叠的可能性，终端MAE归零不是本项目的硬收敛条件。所有数值都是所选历史分布上的网络预测，不是独立测得的真实soft-return。不能根据这些结果声称收敛、已修复、全局低估、任务排名或ESN优越。

## 当前推进与产物

核验时CHEQ四接口在原第11轮，累计552558/556554/554350/553442真实步；SAC为278004/186830/169637/174861步。八原进程均仍活跃且更新，无重复启动。原审计1346884、配对复核1346887继续等完整11；名义四接口矩阵116/120已落盘，原2210514/2210515继续，未选最终Tref。步数仅为带时间戳快照，不是完成量或收敛证据。

计算主机：`rltest-1025--a6ed2ff39b3c-s5gnp35dxg`。产物根目录：
`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/matched_bellman_targets_cycle09_10_v1`，含REGISTRATION、LAUNCH、results、REVIEW及图。冻结诊断源码在同一SSD根目录的`runtime/matched_bellman_targets_v1`；输入学习器为`runtime/source_train14`。小型结构化证据见本报告同名JSON；大型checkpoint/原始replay不提交Git。

本轮远端main为a52dfba4486af8d263d5cd0a976c3102482ff249，baseline为f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，已fetch并读取两分支日志。GPU正式窗口先前均值35.13/39.40/30.07/33.97%，50%要求仍未达到，本轮没有用短时快照宣称持续达标，也没有启动占位负载。当前阶段结束后做完整科学复核，再登记下一步；source16性能候选尚未部署。

最终目标仍未完成：充分优化/收敛、完整训练集固定策略SPT与指定ESN公平对比均待完成。指定ESN checkpoint仍未提供，已问过，不用历史checkpoint替代。physics/MJB、Task/Strict gates、actor信息、公共filter、执行器限制和dt均保持。
