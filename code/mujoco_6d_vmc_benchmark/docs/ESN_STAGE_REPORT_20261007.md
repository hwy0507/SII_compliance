# SII_compliance 阶段性汇报：VMC teacher 蒸馏的纯 ESN 与统一 baseline 对比

日期：2026-10-07  
版本：本轮结果待提交至 GitHub `main`；统一主表与 sealed 条件保持不变。

## 一、研究问题与冻结边界

目标是在 frozen office-v6 pick-and-place 环境中，用纯本体感知的 ESN 学习 VMC teacher 的柔顺动作，并与 RNN、MLP、memoryless、经典 VMC/导纳/阻抗、参数调优 RL 和直接动作 RL 公平比较。

所有主比较共用 MuJoCo 3.11.0、同一 `rollout.mjb`（SHA256 `173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11`）、正式 `dt=5e-5`、55 s horizon、原任务 gate、原执行器幅值/变化率约束和 48D/action7 接口。actor 只读取本体/估计负载与参考相对量，不读取接触真值、球状态、事件时间、任务阶段、视觉或距离。

最终统一展示采用 24 个相同 held-out 条件、每个 family 一个固定模型；神经网络与 RL 固定模型锁中的 seed `2026100301`，经典控制器和 teacher 使用唯一冻结模型。原三 seed `/72` 统计保留为敏感性附录。

## 二、统一任务结果

ESN 在统一 `/24` cohort 上为 `20/24 task`、`16/24 strict`。Matched RNN 为 `16/24`、`15/24`，matched MLP 为 `12/24`、`11/24`。Enhanced teacher 为 `24/24 task`、`13/24 strict`。经典控制器、参数 RL 和直接动作 RL 在该组合条件集上均为 `0/24 task`。

ESN 的关键执行指标为 RMSE `31.451 mm`、峰值速度 `0.360 m/s`。相同 cohort 的 matched RNN 为 `32.678 mm`、`0.375 m/s`，matched MLP 为 `43.555 mm`、`0.376 m/s`。

## 三、柔顺性结果

从原始逐回合物理日志重算的事件指标如下：

- ESN 人手接触力 P95 `19.6 N`，棍子接触力 P95 `13.4 N`；matched RNN 为 `20.4 N`、`13.8 N`。
- ESN 人手/棍子恢复率分别为 `3/24`、`2/24`；matched RNN 为 `1/24`、`1/24`。
- ESN 最大外部/未知边缘穿透 `0.417 mm`，说明柔顺接触力较小并不等价于所有回合都通过 `0.2 mm` strict 门槛。
- Enhanced teacher 的棍子恢复率 `11/24`，但人手接触 P95 `40.9 N`、RMSE `41.643 mm`，且 strict 为 `13/24`。

因此当前最稳妥的结论是：ESN 在学习控制器中取得较好的任务完成率、速度/RMSE 权衡和较低的人手/棍子接触 P95；恢复能力和峰值力矩仍是主要缺口。

## 四点五、本轮 ESN-only 峰值力矩代理与泛化开发

### v2 anchored readout 的真实闭环复核

在同一 frozen `development_000`、正式 `dt=5e-5` 上，v2 `smooth_weight=0.01,
action_weight=0.0001,parent_trust=100` 候选 task/strict 均通过，RMSE `30.823 mm`、峰值力矩
`49.663 Nm`、峰值速度 `0.3659 m/s`、最大穿透 `0.1636 mm`。该候选相对父 ESN 锚点的 `49.981 Nm`
下降 `0.318 Nm`（约 `0.64%`），同时优于 `.03` 候选在同一条件下的 `51.595 Nm` 和 `33.303 mm`。
这是一个 development identity 的物理证据，尚未进入统一 `/24` 主表，也不能单独支持跨条件泛化结论；后续将把该候选在其余已登记 development identities 上验证，失败回合保留。

在固定 reservoir 和 20/5 identity split 上，预注册 36 个 readout 候选。最佳平滑候选为 `ridge=1.0, smooth_weight=0.1, action_weight=0.005`，checkpoint SHA256 为 `69ecee9d57f34d67be5bec47a4be621d58b9957cc066b1fad0cac7bf588146e4`。5 个验证身份上的 action delta energy 从父 ESN 的 `0.014357` 降至 `0.009489`，最大单步 action 跳变从 `1.566` 降至 `1.366`，action energy 从 `0.012396` 降至 `0.009701`；action MSE 从 `0.000242` 增至 `0.000612`。因此它是降低输出抖动和峰矩代理的候选，不是已经证明降低真实峰值力矩的结果。

随后对 v2 anchored `smooth_weight=0.01, action_weight=0.0001, parent_trust=100` 做了真实闭环审计。
在八个已登记 development identities 上 task/strict 为 `5/8` 和 `4/8`；通过回合 RMSE 为 `28.338–36.499 mm`，
峰值力矩为 `48.836–49.909 Nm`，大多数通过回合略低于父 ESN 锚点 `49.981 Nm`；失败回合全部保留：
`development_002/003/006` task/strict 失败但完整执行、穿透分别 `0.174/0.139/0.160 mm`；
`development_005` task 通过但 strict 因 `0.486 mm` 穿透失败。配对父 ESN 在 development_002 更早因 `2.602 mm` 穿透中止。
该结果支持“轻度降矩并改善困难条件穿透”的候选解释，同时明确表明低力矩/低穿透不等于放置成功；
尚未更新统一 `/24` 主表，也未读取 sealed 条件。详细审计见 `docs/ESN_TORQUE_GENERALIZATION_20261007.md`。

同样测试的本体噪声一致性候选 checkpoint SHA256 为 `c327ee61c583beb5a392b3752496f6e8eabc136e181551408d4471ded7acab6e`，验证 MSE `0.000548`、delta energy `0.010215`，作为折中候选保留。物理闭环统一转到 arm1 的兼容 worker（MuJoCo 3.11.0、显式 `MemoryMax≤3G`）；本机 cgroup 不可用这一限制已记录。没有读取 sealed 条件、没有改动正式矩阵。

## 五、证据与限制

最终服务器证据根：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`

统一物理报告 `SUMMARY.json` SHA256 为 `e6d29024bf0e80df16554325193f7a94c6ba8e1193cc31f168a08c9da7346660`；逐回合比较报告 `REPORT.json` SHA256 为 `100341d7cd42cac944fb5f28849c6028890faf160adfdd27201b0ed4d3fb8d45`。原始 912 条物理回合和 360 条 RL actor replay 均保留，失败、short 回合、右删失恢复均未删除。

当前结果仍是固定几何和有限条件分布内的仿真证据，不是硬件安全、被动性证明或真实办公室泛化证明。最新 ESN v4 state-delta checkpoint 已完成离线和部署 parity，但尚无同一 office-v6 闭环收据，因此没有把它混入上面的正式主表。

## 六、下一步：ESN-only 峰值力矩与泛化实验

下一轮只修改 ESN 读出学习机制，不改环境、gate、actor 输入或执行器约束：

1. 在固定储备池上加入 action-increment 和输入扰动一致性正则，抑制高频读出变化并提高对负载/时序扰动的泛化；
2. 训练/验证阶段只用 20/5 identity split，模型选择优先保持 task/strict，再比较峰值力矩、接触 P95 和恢复；
3. 在未参与选择的新条件组合上做一次预注册确认，单独报告开发、确认和历史 final cohort，不用已开封 24 条条件反复调参；
4. 只有完成闭环收据后，才把新候选与当前 ESN、matched RNN 做对照。

本汇报不预先承诺峰值力矩一定下降；若降矩导致任务或恢复恶化，将保留该失败结论。

## v2 `.003` 候选收尾

固定 reservoir 的下一预注册读出候选（`smooth_weight=0.003`，其它参数不变）在八个 development 条件上完成正式
`dt=5e-5` 闭环，task/strict 为 `4/8`、`3/8`。独立 `paper_metrics_20261002.py` 逐回合重算通过，四个 strict
通过回合峰矩 `49.907–50.485 Nm`；最低峰矩失败回合为 `40.169 Nm`，因此低力矩与任务成功脱钩。该候选不进入正式
`/24` 主表，完整证据见 `docs/ESN_TORQUE_GENERALIZATION_20261007.md` 和
`outputs/esn_torque_v2_corrected_20261007/closed_loop_v2_s005_summary.json`。
