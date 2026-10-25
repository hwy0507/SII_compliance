# 第10轮CHEQ审计、SAC Direct5与冻结第9轮完整代表评估 — 2026-10-25

四类CHEQ all-five Bellman阶段的第10轮已完整归档、原审计与9→10配对复核已结束；四路均已进入原登记第11轮。新证据没有表明all5修复了学习问题：critic loss继续增长，Q均值显著转负，Direct任务成功回落。当前11继续、不作中途干预；尚未部署source16。

## CHEQ完整第10轮

四checkpoint及120条完整条件/终端/冻结模型收据已核验。每例55秒、1375动作，条件集合与登记30项一致；奖励由完整transition日志重建，诊断确认网络未变、Bellman count5、0更新/0新physics。训练曲线及9→10配对图已目视核对。

| Interface | Steps | Task/30 | Strict: 9→10 | Mean reward: 9→10 |
|---|---:|---:|---:|---:|
| direct | 532944 | 5 | 10 → 5 | -15.17483 → -23.86560 |
| impedance | 533471 | 18 | 18 → 17 | -0.49960 → -2.27449 |
| admittance | 534320 | 15 | 15 → 15 | -6.92703 → -6.94580 |
| vmc | 535026 | 17 | 17 → 17 | -2.83447 → -2.81183 |

| Interface | Critic loss, last1000: 9→10 | Sampled Q mean: 9→10 | Terminal MAE: 9→10 |
|---|---:|---:|---:|
| direct | 4194.21 → 194367.53 | 1244.61 → -4092.71 | 584.06 → 2948.58 |
| impedance | 337248.32 → 1133706.81 | 5974.67 → -16747.48 | 3067.68 → 6868.94 |
| admittance | 144168.72 → 890991.73 | 2017.73 → -11521.68 | 4157.38 → 9106.66 |
| vmc | 973517.62 → 1590252.63 | 12899.18 → -17506.19 | 13049.82 → 8213.34 |

Direct训练Strict按被动/短期/长期为4/1/0（各10）；失败阶段lift20、load_transfer5。相对9丢失6个原Strict成功条件、新增1个；参数三方法为0/9/8、0/10/5、0/10/7。Admittance总成功数相同但条件有一失一得，不把计数相同说成行为不变。

当前alpha上界超限比例Direct/Impedance/Admittance/VMC为0/0/8.8232/2.1045%。Q转负后更容易满足上界，这不是价值校准证据。VMC终端MAE有所降低，其余三路增大，不能笼统声称四路每个诊断都变差。critic loss、Q漂移和Direct任务回落共同排除“已健康收敛”的说法。

这些是训练中变化策略的完整条件周期，不是固定checkpoint接受测试。单seed、不同replay内容，before/after不构成纯因果对照；仅可判断本次已观察的在线结果尚不支持修复。第11轮仍按原两轮计划继续，之后复核整阶段，再决定后续算法/训练设置。

## 新完成的SAC Direct第5轮只读审计

从不可变cycle5 checkpoint冻结输入，单独审计该新周期；其他三SAC未重复诊断。30条件/终端/模型收据、41250条transition、82500条optimizer日志与输入hash核验，奖励重建和网络不变检查通过。图已目视检查，2862832已退出；0physics/更新，原SAC继续6。

| Cycle | Steps | Task/Strict /30 | Critic loss, last1000 | Q mean | Terminal MAE |
|---|---:|---|---:|---:|---:|
| 4 | 223990 | 0/0 | 69660.35 | 32509.98 | 1738.26 |
| 5 | 265240 | 0/0 | 216711.88 | 59261.41 | 3445.31 |

第5轮30项均approach失败，平均reward−34.45517、std1.41493。alpha4.2480→6.7314，当前alpha上界17582.39→27843.57，样本超限比例仍99.9268%。平稳失败reward和接近目标−7的entropy不能替代任务成功及critic健康。上界只针对当前冻结policy/alpha，不约束未来变化alpha；不将Q增长归因为单一未证实bug。

## 冻结第9轮代表条件矩阵完成

原参数协调器4191390及末VMC evaluator1836087已退出，不应重启。与此前独立Direct9确定性结果合并，4接口×3预选0000条件共12例完整55s，所有物理/filter/torque收据检查通过；新VMC3例的9份审计输入hash另行重读核验。固定checkpoint9的身份及确定性模式已验证。

| Interface | Deterministic Task/Strict /3 | Short completion | Long completion | Long peak torque | Long contact compliance |
|---|---|---:|---:|---:|---:|
| direct | 0/0 | NA | NA | 35.2399Nm | 100.0000% |
| impedance | 2/2 | 13.04s | 20.04s | 51.7783Nm | 22.0727% |
| admittance | 2/2 | 45.04s | 45.32s | 52.6288Nm | 100.0000% |
| vmc | 2/2 | 27.52s | 32.40s | 46.6636Nm | 100.0000% |

12例机器安全违规0；四方法被动均失败。新VMC短/长完成27.52/32.40秒，峰矩47.1968/46.6636Nm；短期无人接触为NA，长期接触6.62165秒、合规100%。峰矩是全回合指标，接触合规只统计人接触窗口。Direct长期虽接触合规100%仍任务失败；不能用舒适指标替代成功。

同一Direct9另有已完成的随机模式三seed×三条件诊断，Task9/9、Strict7/9、机器安全违规2/9；原确定性0/3必须保留。不同模式/seed范围分开报告，不能挑最好seed替代正式评估。这些代表条件均不是完整30训练集，更不是最终与ESN的排名，尚未选择最终Tref。

## 持续任务状态与位置

计算主机`rltest-1025--a6ed2ff39b3c-s5gnp35dxg`，集群SSD根目录`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。本轮main/baseline fetch/read仍为a52dfba/f6e8f8c。

- `runs/bellman_minimum_stage_audit_v1/bellman_cycle10/REVIEW.json`：完整周期数值、120收据与归档hash。
- `runs/bellman_minimum_paired_review_v1/parent09_to_bellman10`：配对COMPARISON及图；原审计1346884/reviewer1346887继续等11。
- `runs/diagnosis_sac_direct_cycle05_v1/REVIEW.json`：新SAC完整周期只读审计。
- `runs/interim_cheq_cycle09_parameters_v1/COMPLETE_FOUR_INTERFACE_REVIEW.json`：确定性四接口完整代表矩阵；Direct来源仍保留独立run。
- source16性能候选仍prepared_only，四CHEQ14/四SAC09继续；无新增优化干预，不修改物理/MJB/gate/actor/filter/执行器/dt。
- 四卡持续50%尚未达到；最终充分训练/优化健康、完整训练集固定策略/SPT和指定ESN公平比较仍未完成。指定ESN仍缺，不用历史checkpoint替代。
