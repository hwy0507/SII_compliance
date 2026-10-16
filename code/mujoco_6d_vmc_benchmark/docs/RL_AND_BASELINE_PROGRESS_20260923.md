# RL 与经典柔顺 baseline 工作记录（2026-09-23）

## 2026-10-16 14:21 CST Direct阶段结束，阻抗已自动接续

Direct61,531步/95,189更新，本阶段8完整回合Task/Strict0/8、physical_valid3/8，最终hash通过。
原协调器自动切至impedance，真实250步/0更新（5000步热身），后两族排队；无重复训练。
密集tracking的fresh同seed两组对照已登记，各11k、总22k；前序四族全部闭合后才允许派发。
30项测试和两组真实丢弃更新预检通过（相同初始网络hash、峰值1.36GB/OOM0），源码/登记/
预检已归档。未启动新对照，未收敛/未最终验收；详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:10 CST 密集跟踪奖励组件与隔离检查完成

Direct60,090步/93,748更新，第七回合继续，已完成六回合Task/Strict0/6；其他三类排队。
新增可选有界tracking奖励（权重4）和提前失败剩余成本，旧新奖励resume及统计拼接均拒绝。
27项相关测试与trainer编译通过；五条真实历史轨迹奖励复算确认更好的跟踪获得更高候选回报。
仅验证奖励算术，未部署新训练、不声称策略改善；活动源码/物理保持，Goal继续。
源码/测试/完整输入与复算证据已核验归档，详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 14:01 CST 训练奖励诊断与第六回合闭合

Direct58,781步/92,439更新，6个完整回合Task/Strict0/6，58,781 checkpoint hash通过；
第7回合继续，其余三方法排队。新增奖励分解工具/3项测试，五回合完整快照通过公式/日志核验。
Task信号每1375步仅末步−20；无安全罚分的两条失败轨迹跟踪cost差异很大但折扣总回报相同。
支持下一阶段检验密集跟踪奖励，未证明唯一根因，未改变当前训练或重标最终gate。
诊断源码/完整证据已归档核验，路径/hash见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:55 CST 五个完整回合与失败产物归档

Goal active；Stage01 Direct57,750步/91,408更新，新增7219/7219，5完整回合Task/Strict0/5、
physical_valid2/5；第5回合return−35.653907、仍停approach，第6回合在途，其余三方法排队。
57,406 checkpoint hash通过，OOM0/swap0，但内存已触及硬限回收，继续观察。
episode38–40原始轨迹及三个checkpoint已核验归档，835,219,332字节；episode41之后待同步。
未收敛、未最终验收，详细hash/服务器位置见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:39 CST 收敛统计可复核，第四回合继续

Stage01 Direct optimizer已到55,804步/89,462更新，54,656 checkpoint hash通过；3完整回合
return均值−31.810846、标准差7.480807，Task/Strict0/3、physical_valid1/3，第四回合在途。
新增按精确阶段lineage统计的收敛筛选，落实原登记96回合/两个32回合窗口及联合成功要求，
保留失败/未完成，拒绝重复计数或跨reward拼接；8项测试通过，真实结果不满足收敛。
worker OOM0/swap0，其他三类未启动。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:31 CST 精确接续入口完成，第三回合继续

Stage01 Direct已到54,500步/88,158更新，保持UTD1；2个结束回合Task/Strict0/2，第三回合在途。
补齐四方法各自checkpoint的prepare-next及逐方法预检封存，避免后续阶段误从零重训。
15项测试通过；真实53,281步n25 checkpoint/replay/RNG恢复与一次丢弃更新通过（峰值1.13GB/OOM0）。
当前running阶段被正确拒绝提前接续，未建立stage02，活动冻结源码不变。其他三类排队，
其真实接续预检待checkpoint生成后执行；未收敛/未验收。入口见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:22 CST Goal训练继续，完成只读Bellman/动作诊断

同一Stage01 Direct worker已完成2个完整回合，到53,281步/86,939更新，新增2750/2750；
return−21.667945/−34.277519，Task/Strict0/2、physical_valid1/2，第三回合运行中。
固定51,906 checkpoint的训练replay诊断通过：target裁剪概率质量极小，但terminal附近
当前动作Q明显高于历史动作，新回合TD残差较大；记录为动作外推/样本学习候选线索，未断言bug。
2项数学测试通过；真实只读诊断无梯度/仿真，峰值924MB、OOM0，模型hash/RNG不变。
活动训练和冻结快照保持，其他三类排队，未收敛、未验收。详见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 13:02 CST 持续Goal接续，Stage01已启动

用户明确开启持续Goal，旧15小时截止不再作为后续工作的终止授权；旧run保持原始收据。
旧恢复结束于50,531步，本段5个完整回合Task/Strict0/5，最终checkpoint hash通过。
新`outputs/rl_goal_20261016_stage01/`已登记四方法串行、各新增最多11k、25步回报、UTD1，
Direct保留旧checkpoint及原始replay，仅作明确的信用窗口迁移。13项测试与真实checkpoint
预检通过；协调器与Direct worker已启动，其余三方法排队，未收敛、未验收。
后续优先检查该阶段execution/service；详情与完成判据见[Goal进度](RL_GOAL_PROGRESS_20261016.md)。

## 2026-10-16 12:04 CST 已授权修复落地，恢复训练完成首个回合

用户明确授权后，旧v2保存卡死进程已退出，partial checkpoint保留；旧v3b两路收完在途回合，
阻抗112,750步、Direct73,365步checkpoint均校验通过，末尾历史源码变更导致的失败收据保留。
确认子进程退出才结束旧协调器。新独立service已从v4的43,656步checkpoint恢复：新增1375步/
1375更新，45,031步checkpoint hash通过，真实UTD1、3GiB硬限、swap0、OOM0，源码hash一致。
首个55秒回合return−22.1773，Task/Strict均false，尚未收敛；下一回合已运行。其余三方法
未启动，未做统一acceptance。原派发截止12:33:19 CST仍有效，结束在途回合后保存退出。

**后续监视入口改为**父目录`RECOVERY_CURRENT.json`与
`outputs/rl_tuned_20261015_v4/recovery_20261016_1140b/direct_task_safety/execution.json`，
service为`sii-rl-v4-recovery-recovery-20261016-1140b.service`；旧execution保留为历史，不得
重复启动旧协调器。详细故障、reward分项与只读critic诊断见[修复报告](RL_V4_REPAIR_20261016.md)。

## 2026-10-16 11:32 CST 修复进展

已实查v2保存卡死、v3b遗留并发和UTD失配；完善独立硬限恢复入口与每回合checkpoint，
5项回归测试通过。真实checkpoint恢复/梯度更新诊断通过（峰值约1.45GiB、OOM0），
排除该checkpoint不加载或完全不更新，但尚未证明闭环收敛。恢复登记已就绪，旧进程处理被
自动审批拒绝、未执行，仍需明确授权才能释放资源并启动恢复。
详见 [修复与验证报告](RL_V4_REPAIR_20261016.md)。

## 2026-10-16 11:06 CST 复查

v4无进程、无新增交互，日志仍47,448步/84,898更新；34已结束回合Task/Strict各0/34，
其他三方法未启动，43,656步checkpoint hash复核通过。MemAvailable约3072MiB仅等于worker
上限且无余量，旧v3b两路仍运行，本轮未恢复或验收，原截止12:33:19 CST不变。
本轮收据及资源细节见 [v4监视报告](RL_V4_MONITOR_20261016.md)。

## 2026-10-16 10:46 CST 复查

v4进程为空、无新增步数；原running收据为中断前状态。仍为47,448步持久化日志、34已结束
回合，Task/Strict各0/34，其余三方法未启动；43,656步checkpoint hash复核通过。
MemAvailable=3035MiB不足3072MiB worker预算（未加余量），本轮未派发恢复或验收。
原截止12:33:19 CST不变，旧v3b进程未干预；详见下方交接报告的本轮补充。

## 2026-10-16 10:33 CST 最新 v4 状态

Direct 至少 47,448 步，34 个已结束回合 Task/Strict 均 0/34，其余三方法未启动；没有收敛或
acceptance 结果。宿主机检查发现实际 UTD=2 与登记1不符，且没有独立3GiB/禁swap硬限。
本轮请求安全停止后整个v4进程树消失，未写出新checkpoint；保留在途失败收据，不冒充正常
回合末退出。已准备独立恢复trainer并验证UTD循环，但可用内存不足，尚未恢复。
详见 [本轮证据、修复和交接](RL_V4_MONITOR_20261016.md)。下文为历史结果，不代表当前进程状态。

最新结果以 [本周三维对比周报](BASELINE_WEEKLY_REPORT_20260923.md) 为准：已完成当前 48D 五方法配对、阻抗积分参考 K300/K900 对照及导纳参考 r2 完整回合。以下 primitive 与 RL pilot 记录保留作前期工程诊断，不与当前配对主表混合。全套检查现为 105 项通过；本轮实验已结束，无后台训练或仿真遗留。

本周先完成 impedance/admittance 的开发矩阵，再建立两类 RL baseline 的文献与本机复现入口：

1. RL 调 VMC/阻抗/导纳参数；
2. RL 直接输出柔顺 action。

当前 GitHub 主线为 `0e9142e9b6c03c22995914e9ef66226cfca27a18`。本记录只引用有 source hash、命令和结果文件的实验。

后续新增公平比较审计：[FAIR_METHOD_COMPARISON_20260923.md](FAIR_METHOD_COMPARISON_20260923.md)。历史 120 条 isolated push 不能冒充 current proposed 的正式对照：完整 provenance 缺失、旧 source/controller 标签不可靠、全部超过当前 0.2 mm 门槛。当前冻结 48D 模型来源见 [CANONICAL_MODEL_PROVENANCE_20260923.md](CANONICAL_MODEL_PROVENANCE_20260923.md)；新配对 panel 矩阵和接口限制见 [PANEL_CLASSICAL_INTEGRATION_20260923.md](PANEL_CLASSICAL_INTEGRATION_20260923.md)。

## 1. 服务器经典 baseline

服务器完成了 24 条隔离运行：

```text
controller × fixture × variant
2 × (ball, push, corner, table_corner) × 3 = 24
```

完整结果：

```text
/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume/FINAL_RESULT.json
```

本机只读保存了同一汇总：

```text
outputs/server_baseline_20260923/FINAL_RESULT.json
```

固定参数开发矩阵的通过情况如下：

| 控制器 | ball | push | corner | table_corner | 总计 |
|---|---:|---:|---:|---:|---:|
| Cartesian impedance | 3/3 | 3/3 | 0/3 | 0/3 | 6/12 |
| Cartesian admittance | 2/3 | 0/3 | 0/3 | 0/3 | 2/12 |

这里的通过数已经同时满足严格的 `penetration <= 0.2 mm`、有效接触、无上游误碰和任务完成条件。完整的逐回合 penetration、端点误差、峰值外力、峰值力矩和失败原因见 [CLASSICAL_BASELINES_20260923.md](CLASSICAL_BASELINES_20260923.md)。

实现边界需要保留：impedance 使用 `J.T @ (K e + D e_dot)`，并经现有 torque feasibility/slew 栈；admittance 使用本体 joint-load 估计 wrench，积分 `M x_dd + D x_d + K x = wrench`，再输出 bounded Cartesian velocity residual。admittance 当前把虚拟 offset 用于内部弹簧反馈，但没有把 offset 变成独立的 WBC reference，因此 nominal WBC 会和虚拟位移产生竞争；这解释了 push/corner/table_corner 的失败，也是下一轮应修正的控制接口问题。

这组数据是 source primitive 的固定参数开发诊断，不是 office blind-test，也不是参数搜索后的论文最终 baseline。当前结果支持的结论是：传统 impedance 在球/棍推 primitive 上有可用工况，但在两个桌角 fixture 上没有通过完整任务 gate；admittance 的固定配置还没有通过持续推压和桌角任务。

复现命令（服务器隔离 source snapshot）：

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/source_resume
/home/arm1/vmc_mujoco_runtime/.venv/bin/python scripts/run_classical_matrix_20260923.py \
  --output /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/baseline_impedance_admittance_20260923/matrix_resume \
  --menagerie /home/arm1/vmc_mujoco_runtime/mujoco_menagerie --workers 8
```

## 2. 2024 年以后“RL 调参数”文献

详细核验见 [RL_PARAMETER_LITERATURE_20260923.md](RL_PARAMETER_LITERATURE_20260923.md)。三篇核心文献是：

| 文献 | venue | 适合本项目的 baseline 解释 |
|---|---|---|
| Da-VIL: Adaptive Dual-Arm Manipulation with Reinforcement Learning and Variable Impedance Control | ICRA 2025，DOI `10.1109/ICRA55743.2025.11127487` | PPO 输出 6 个笛卡尔对角刚度，再由 CVXPY QP 和动力学计算关节力矩；适合映射为 RL 输出 6D VMC stiffness |
| Impedance Primitive-Augmented Hierarchical Reinforcement Learning for Sequential Tasks | ICRA 2025，DOI `10.1109/ICRA55743.2025.11128462` | 高层选择 primitive，参数策略输出阶段相关刚度/任务参数，primitive 内使用自适应刚度；适合做 phase-conditioned parameter baseline |
| Variable Impedance Control Combining Reinforcement Learning and Gaussian Process Regression | IEEE-RAS Humanoids 2024，DOI `10.1109/Humanoids58906.2024.10769856` | RL/FCEM 学 stiffness-damping，GP 建模物体重量变化，momentum observer 提供外力矩估计；公开资料不足以编造完整 obs/action，应先按 paper-spec 补齐 |

这类 baseline 的 action 不是项目的 7D action。公平实现应为：RL 使用允许的本体观测输出 `K/D` 或低维 schedule，解析 VMC/阻抗控制器将参数转换为项目统一的 7D action，再通过同一安全栈。物体姿态、质量、接触 truth、未来事件和障碍物几何必须从 blind student observation 中剔除。

## 3. 2024 年以后“RL 直接输出动作”文献

详细核验见 [RL_ACTION_LITERATURE_20260923.md](RL_ACTION_LITERATURE_20260923.md)。三篇核心文献是：

| 文献 | venue | 动作和迁移限制 |
|---|---|---|
| SERL: A Software Suite for Sample-Efficient Robotic Reinforcement Learning | ICRA 2024，DOI `10.1109/ICRA57147.2024.10610040` | RLPD/SAC 风格，7D 常见形式是 6D pose delta + gripper；可作为 SAC/RLPD-action7 的算法来源 |
| HIL-SERL: Precise and Dexterous Robotic Manipulation via Human-in-the-Loop Reinforcement Learning | Science Robotics 2025，DOI `10.1126/scirobotics.ads5033` | RLPD + demonstration/human intervention；动作为 Cartesian 6D twist/target，夹爪另有离散策略；没有真实 FR3 和纠正数据不能声称忠实复现 |
| AutoMate: Specialist and Generalist Assembly Policies over Diverse Geometries | RSS 2024，[官方论文页](https://roboticsproceedings.org/rss20/p064.html) | PPO 直接输出 6D incremental pose，底层 task-space impedance；actor 使用目标位姿，critic 使用 privileged state，必须改成 48D proprio-only 才能公平比较 |

三篇的动作语义都不同于当前 ESN 的 `[slowdown, yield_6d]`。本项目应实现 interface-matched `PPO-action7` 和 `SAC/RLPD-action7`，把原论文作为算法来源，而不是把原论文 action 维度直接塞进当前环境。

## 4. 本机 RL 工程预实验

本机使用 RTX 5080（CUDA 12.8 PyTorch，`torch 2.11.0+cu128`），运行环境为 `.venv-rl`。仓库 89 个测试仍然通过：

```bash
PYTHONPATH=code/mujoco_6d_vmc_benchmark/scripts \
  .venv-rl/bin/python -m pytest -q code/mujoco_6d_vmc_benchmark/tests
# 89 passed
```

由于本机主内存约 16 GB，训练脚本使用单进程 `DummyVecEnv`、单环境、1--3 个 CPU 核和 6 GB 内存上限。首轮并发 16 worker 曾触发系统 OOM；该故障已定位并停止并发方案。

入口脚本：[run_rl_local_pilot_20260923.py](../tools/run_rl_local_pilot_20260923.py)。它会写入 command、Git/source hash、依赖版本、normalization、checkpoint 和冻结评估；默认只用两条旧 rod development fixture 训练，另两条 fixture 做验证，不使用 office 数据。

### 4.1 PPO 调六维刚度

输出目录：

```text
outputs/rl_pilot_r2_stiffness_ppo/
```

配置：`51D proprioception -> PPO -> 6D stiffness action`，8,192 steps，单进程，约 42 s。零动作和学习策略在 4 个 legacy fixture 上均通过旧版“有效碰撞 + 抓起保持 + 配对 no-rod + 无 hard torque limit”判据：

```json
{"zero_paired_gate": [true, true, true, true],
 "learned_paired_gate": [true, true, true, true],
 "publication_ready": false}
```

这个结果只证明 RL 调参链能运行；零动作也全部通过，不能据此宣称 PPO 改善了 VMC 或优于 ESN。它还没有使用当前 canonical 48D observation、四类正式 teacher split 或 office blind test。

### 4.2 SAC 直接输出动作

输出目录：

```text
outputs/rl_pilot_r2_direct_sac/
```

配置：`32D legacy WBC state -> SAC -> 7D direct residual action`，8,192 steps，单进程，约 69 s。零动作四个 fixture 全通过，而学习策略四个 fixture 全未通过：

```json
{"zero_paired_gate": [true, true, true, true],
 "learned_paired_gate": [false, false, false, false],
 "publication_ready": false}
```

冻结评估显示 learned SAC 在这些短预算、旧 32D 环境中没有建立有效接触和任务完成行为。这是失败的工程预实验，不能解释为“RL 直接动作方法不适合本项目”；它提示后续必须改为当前 48D contract、统一 reward/gate、先用 teacher replay warm-start，再做 SAC/RLPD sweep。

## 5. 当前状态与后续执行顺序

导纳 offset 已接入 WBC 参考，且修复运动学快照时序问题；r2 在三个当前 panel 条件下完成 24 s 全程实验。阻抗已改为积分 WBC twist 的移动平衡点，K300/K900 候选均保留。两者仍未成为可靠通过完整 gate 的最终 baseline，四类 primitive 的修正版全矩阵也尚未重跑。

1. 先为所有方法补齐统一的物理子步速度/实际 actuator torque 记录，并明确状态机参考下的全程与阶段误差口径。
2. 在训练/验证条件上给 impedance/admittance 固定调参预算、验收规则和模型选择规则；冻结后评估新的共同条件，不用这三条开发结果冒充独立测试。
3. 在当前 canonical 48D observation 和 7D action contract 上实现 `PPO-action7` 与 `RL-tune-VMC`；调参方法按单独控制器家族解释。
4. 用 VMC teacher bank 初始化 prior replay，实现 `SAC/RLPD-action7`；训练和 ESN 使用同一 fixture-level split、action hold、normalization 和 gates。
5. 扩大共同物理条件和独立训练 seed，最后执行冻结配置下的 office blind test。全部失败回合保留 failure reason、penetration、contact pair、force/torque 和 trace。

当前已完成的是可复现的 baseline 起点与 RL 工程链路，不是论文最终比较矩阵。
