# Live learner profile and Adam resume-device validation — 2026-10-25

四类 CHEQ all5 在线阶段10/11与原四类SAC09继续；本轮没有修改live runtime、训练配置、网络权重或物理合同。新发现的是恢复时Adam步数计数器的同步开销；独立候选通过有限精确更新验证，尚未部署。四路仍未获得健康收敛证据。

## 当前采样与分母

外部py-spy0.4.1、每进程请求60秒/50Hz，四路并行采样，包含idle线程。每路14995样本中11996为空栈、2999带Python栈。空栈不等于GPU/CPU空闲；原格式没有thread ID，不能直接把非空栈称为主线程墙钟时间。原SUMMARY和raw文件保留，新REVIEW同时报告全样本与非空栈分母。五个解析/完整性测试通过。

以下比例均以2999个非空栈样本为分母，inclusive类别有重叠，不能相加，也不是CUDA kernel时间：

| Interface | Learner update | Adam | Replay | Target update | Checkpoint |
|---|---:|---:|---:|---:|---:|
| direct | 82.79% | 24.31% | 10.44% | 7.74% | 0.33% |
| impedance | 75.39% | 21.41% | 7.57% | 6.37% | 10.07% |
| admittance | 74.52% | 23.17% | 8.84% | 5.17% | 9.77% |
| vmc | 77.89% | 25.14% | 8.00% | 4.97% | 8.94% |

`_get_value`叶栈占非空栈约9.6–12.0%。训练入口`train_published_compliance_20261025.py`使用`torch.load(..., map_location=args.device)`；非capturable/nonfused Adam恢复时保留`step`的原device，偏差修正又用`_get_value(step).item()`读取标量。因此CUDA恢复会留下不必要的GPU标量读取。当前实际副本已复现每个learner的59个GPU计数器（actor8、critic50、alpha1）。这不是critic发散的已证实原因。

原采样前后进度时间戳相差约112秒，不能将其中步数增量除以60充当吞吐。采样时四learner仍实际更新；这次采样没有新增physics或优化更新。最新既有正式GPU窗口均值40.63/36.95/37.95/30.93%，仍未达到用户四卡50%的目标。

## 独立候选验证

登记`runs/adam_step_device_validation_v1/REGISTRATION.json`，冻结工具于`runtime/adam_step_device_validation_v1`。使用当前all5阶段的四份不可变parent checkpoint，按正式入口加载到对应CUDA设备；候选仅把非capturable、非fused、非differentiable Adam的scalar step移回CPU。四个helper测试通过。没有改Adam参数、学习率、网络、Bellman规则、batch16384、replay或随机采样。

每接口两种执行顺序，每顺序两arm，每arm256次真实辅助更新；总4096更新、0新physics，不保存/导入辅助权重。每arm恢复相同完整状态，核对所有数值状态与field hash、agent parameter gradients、采样RNG、父state/replay；仅59个step的device变化，其他tensor位置一致。四接口两次对照全部精确通过。未单独保存log_alpha.grad，alpha本体/optimizer完整数值已比较。

| Interface | Original/candidate time, first order | Reverse order | Exact numerical state / agent gradients / RNG |
|---|---:|---:|---|
| direct | 1.1261× | 1.0566× | pass / pass |
| impedance | 1.1711× | 1.0468× | pass / pass |
| admittance | 1.1494× | 0.9634× | pass / pass |
| vmc | 1.1772× | 1.1724× | pass / pass |

共享硬件短窗口计时有波动（Admittance反序0.9634×），不宣称普遍提速、正式吞吐提升或GPU50%达标。本验证仅涵盖四类CHEQ all5，不外推SAC。四辅助进程1825205/6/7/8均已结束。候选未接入正式adapter；下一步若采用，须在已登记阶段完成并科学复核后，用独立runtime验证恢复/再保存入口，保留完整状态和原始证据。当前10/11不打断。

## 新完成的冻结Admittance9评估

固定cycle9 checkpoint，原三个预选0000代表条件，确定性策略、完整55秒；三个物理审计（每例110万子步）、公共filter重放、执行器投影重放共9份收据及其输入hash已核验。此为父9策略，不是正在训练的all5策略。

| Condition | Task/Strict | Completion | Peak joint torque | Human contact | Contact compliance |
|---|---|---:|---:|---:|---:|
| passive_corner_train_0000 | False/False | NA | 40.0940Nm | 0.00000s | NA |
| active_short_train_0000 | True/True | 45.04s | 51.2252Nm | 0.00000s | NA |
| active_long_train_0000 | True/True | 45.32s | 52.6288Nm | 5.03325s | 100.00% |

三例无机器安全违规；被动在carry失败。短期相对nominal45.28秒略快至45.04秒，长期比nominal42.48秒更慢至45.32秒；长期两者接触合规均100%。无接触记NA。峰值力矩取全回合，接触合规仅在人接触窗口统计，二者分母不同。不能把三例视为完整cohort排名、收敛或ESN比较。

原evaluator的RESULTS保留`physical_substep_audit_completed=false`，因为其写入早于协调器的三项后处理审计；本轮首次复核曾误要求该历史字段为true，随后按实际后处理收据完成核验。没有修改原RESULTS来伪造审计状态。新的`ADMITTANCE_COMPLETED_REVIEW.json`明确记录来源。

当前参数9矩阵6/9已审计，原coordinator4191390转入VMC evaluator1836087（行动前重验）；不要重启已结束的Admittance790746。contact候选验证已10/12精确通过，VMC短期继续，尚未部署。

## 证据和剩余工作

计算主机：`rltest-1025--a6ed2ff39b3c-s5gnp35dxg`；集群SSD根目录：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。不是历史Spark主机；未宣称同步到旧服务器。小型hash证据见同名JSON。GitHub main/baseline本轮fetch仍为a52dfba/f6e8f8c。

- `runs/live_bellman_profile_v1/REVIEW.json`：原始采样分母及hash复核；原协调器1600842结束。
- `runs/adam_step_device_validation_v1/REVIEW.json`：四接口实际CUDA恢复、精确更新和两顺序有限计时。
- `runs/interim_cheq_cycle09_parameters_v1/ADMITTANCE_COMPLETED_REVIEW.json`：完成的三例冻结策略及9份审计输入完整性。
- 四CHEQ14仍原10/11；四SAC09继续。原auditor1346884/reviewer1346887等待完整10/11归档，不从部分窗口选结论。
- 收敛证据、成功策略的完整训练集评估、统一最终SPT与指定ESN比较仍未完成；指定ESN仍缺，不用历史ESN替代。
- physics/MJB、Task/Strict gate、actor输入、公共filter、执行器限制和dt均未改变；未按局部成功选择最终Tref。
