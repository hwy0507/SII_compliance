# all5两轮阶段结束、完整名义矩阵与后续有限诊断（2026-10-25）

CHEQ-core all-five-target敏感性阶段10/11已按登记结束，四learner及原整组审计/配对复核均结束，不应重启旧进程。整阶段没有修复训练：Direct和Admittance任务表现退化，四路critic loss与终端误差继续增长。决定不原样延长all5阶段；下一在线阶段尚未选择。四路原SAC仍在运行，新的四路有限折扣诊断已经实际更新。

## 完整第11轮

120个55s回合/每例1375动作的终端、原MJB和四个不可变checkpoint核验完成；奖励由原审计器重建，网络未变，Bellman count5正确。第11轮诊断图与9→11/10→11配对图已目视检查。原审计1346884、配对复核1346887正常结束。

| 接口 | 累计环境步数 | Task/Strict /30 | Strict：9→10→11 | 第11轮平均reward | 失败阶段 |
|---|---:|---|---|---:|---|
| Direct | 574194 | 0/0 | 10→5→0 | -32.67272 | lift22、approach8 |
| Impedance | 574721 | 18/18 | 18→17→18 | -0.47113 | carry12 |
| Admittance | 575570 | 11/11 | 15→15→11 | -13.76801 | carry18、release1 |
| VMC | 576276 | 17/17 | 17→17→17 | -2.80114 | carry13 |

| 接口 | critic loss末1000：10→11 | 样本Q均值：10→11 | 终端MAE：10→11 | alpha：10→11 |
|---|---:|---:|---:|---:|
| direct | 194368 → 2227461 | -4093 → -13795 | 2949 → 8372 | 6.988 → 28.978 |
| impedance | 1133707 → 11732350 | -16747 → -64349 | 6869 → 24772 | 2.124 → 10.139 |
| admittance | 890992 → 9211282 | -11522 → -70726 | 9107 → 27268 | 1.423 → 6.285 |
| vmc | 1590253 → 6770601 | -17506 → -67643 | 8213 → 19103 | 4.861 → 13.502 |

负soft-Q本身并非错误，微分熵可以为负；这里的否定结论依据任务退化、loss和误差增大，而非Q符号。所有当前alpha上界超限比例降至0，也不证明校准。Direct回报std仅1.40667，反映一致失败，不能当有效收敛。训练中policy变化、replay变化、仅一个seed，不是固定策略排名或all5因果效应证明。

## 名义矩阵120/120完成

复用前次Impedance/VMC的60项只读验证，新完成Direct/Admittance60项，共核验1.32亿既有物理子步。未重仿真；原slot0/1进程2210514/2210515均正常结束，新只读380039也已退出。原文件hash、零动作、公共filter、reward、实际力矩幅值/相邻servo slew和接触指标均通过对应复核。v4缺少投影内部输入及第一servo previous torque的限制继续保留，不称完整投影重放。

| 固定名义接口 | Task/30 | Strict/30 | 被动/短/长Strict（各10） | 峰广义力矩 Nm | 实际接触时间加权合规率 | 机器安全违规/30 |
|---|---:|---:|---|---:|---:|---:|
| Direct | 18 | 18 | 0/10/8 | 47.8462 | 67.0038% | 0 |
| Impedance | 18 | 18 | 0/10/8 | 59.2441 | 31.9774% | 0 |
| Admittance | 16 | 15 | 0/9/6 | 54.1645 | 72.2187% | 1 |
| VMC | 17 | 17 | 0/10/7 | 48.0088 | 72.0975% | 0 |

Admittance active_short_train_0600完成Task但外穿透0.209567mm超原0.2mm gate，Strict失败并留在分母；它的实际力矩幅值/slew通过不代表所有物理gate通过。接触各8回合，所有失败接触保留；无接触为NA。阈值是工程参考，并无人体舒适性认证。表中是名义基准，不能与变化中RL训练数直接推断学习收益。最终RL/ESN固定策略比较与共同Tref/SPT尚未完成。

## 已启动的有限折扣延长诊断

原配对诊断每arm仅5000更新，结束时采样entropy约+3.4至+4.7，尚未到目标−action_dimension，不能支持后续训练阶段稳定性判断。此次沿用相同cycle6完整30回合replay、fresh seed、源码和随机采样流，仅把每arm预算扩展为50000；四接口×两gamma共400000辅助更新。Bellman和PBRS shaping的gamma同时为.99或.9995，其他设置保持原probe，采用原random-two target，不是继续all5。

原probe未保存辅助权重，所以前5000需要重算；这不是独立重复实验，也不会把重算前缀当新增独立证据。新四路在4000/5000更新处的metrics和diagnostic与原对应前缀逐项精确相同，均值差0。两arm完整state/RNG/CPU replay不变等收据仍须结束后检查。诊断没有新physics、不导出/导入策略权重，原SAC不改；source16仍未部署。较小gamma显著衰减远期终端奖励，因此即使离线Q更稳定，也不能单凭这一点选定在线gamma或宣称任务成功。

四辅助PID361333/361334/361335/361336，CPU0/14/26/39、GPU0/1/2/3。GPU60样本/66.85s均值63.53/55.98/60.57/61.23%，最小44/44/49/46%，八PID身份不变。这是四辅助加四正式SAC的混合负载，不是正式在线训练独立达50%，也不是每时刻达50%。

## 证据与持续任务

集群SSD根目录`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`：

- `runs/BELLMAN_FINAL_SCIENTIFIC_REVIEW_V1.json`：完整阶段科学结论和下一有限诊断依据。
- `runs/bellman_minimum_online_seed20261025_v1/CYCLE11_ALL_TRAINING_REVIEW.json`：120终端/模型及四checkpoint。
- `runs/bellman_minimum_stage_audit_v1`、`bellman_minimum_paired_review_v1`：原只读审计与配对结果全部完成，勿重启旧observer。
- `runs/nominal_four_interfaces_cohort30_v1/COMPLETE_MATRIX_REVIEW.json`：复用两组60项复核的完整名义矩阵。
- `runs/consistent_discount_extended_cycle06_v1`与`runtime/consistent_discount_extended_v1`：新有限配对诊断，REGISTRATION/EXECUTION/PREFIX_REVIEW/GPU_60S_01已落盘，最终结果待完成。
- 原SAC四learner与剩余Admittance/VMC cycle3只读observer3759872继续，未停止或迁移。physics/MJB/gate/actor/filter/执行器/dt不变。

本轮已fetch/read main a52dfba、baseline f6e8f8c。最终收敛、充分训练、四类固定策略/SPT及指定ESN公平比较仍未完成，目标持续；已登记阶段结束不是Goal结束。
