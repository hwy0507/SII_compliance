# 直接输出动作的 RL 基线文献与复现建议

更新时间：2026-09-23

适用项目：`mujoco_6d_vmc_benchmark`，当前 student contract 为 `proprio48_action7_6d_v1`。

## 文献筛选结论

下面三篇均发表于 2024 年以后，且有公开论文和官方代码。它们覆盖两类对比问题：SERL/HIL-SERL 是在低层阻抗控制器之上由 RL 直接输出末端动作；AutoMate 是在 GPU 物理仿真中由 PPO 直接输出任务空间增量位姿。三篇都适合作为“动作 RL”相关工作或基线来源，但没有一篇可以在不改接口的情况下直接替换本项目 ESN。

| 文献 | 出版信息 | RL 算法 | policy observation | policy action | 与本项目关系 |
|---|---|---|---|---|---|
| **SERL: A Software Suite for Sample-Efficient Robotic Reinforcement Learning** | ICRA 2024，DOI [`10.1109/ICRA57147.2024.10610040`](https://doi.org/10.1109/ICRA57147.2024.10610040)，论文 [arXiv:2401.16013](https://arxiv.org/abs/2401.16013) | RLPD：SAC 风格的离策略 actor-critic，高 UTD；每个 batch 对半取 prior/demo、对半取 online replay，并使用 layer norm | 论文支持图像+本体；本体可含末端位姿、twist、力、力矩。官方 Franka state 环境还提供 `tcp_pose(7)+tcp_vel(6)+gripper_pose(1)+tcp_force(3)+tcp_torque(3)`，图像可选 | 6D 末端相对位姿增量 + 1D gripper；官方环境 `Box(7)`，位置和旋转增量经过 scale 后交给 1 kHz 低层阻抗控制器。 | 最接近“RL 直接输出 action”，但其 7D 中有夹爪，且没有本项目 `slowdown` 语义；可改为 7D `[slowdown, yield_6d]` 后做严格同观测对比。 |
| **HIL-SERL: Precise and Dexterous Robotic Manipulation via Human-in-the-Loop Reinforcement Learning** | Science Robotics，2025-08-20，DOI [`10.1126/scirobotics.ads5033`](https://doi.org/10.1126/scirobotics.ads5033)，论文 [arXiv:2410.21845](https://arxiv.org/abs/2410.21845) | RLPD + demonstration/human intervention；需要夹爪时另训离散 DQN critic；仍属于 off-policy actor-critic 直接动作策略 | 可含 wrist/side camera、末端 pose/twist、force/torque、gripper status；相对初始末端坐标表达本体，提升扰动和位姿泛化 | 普通接触任务：每个机械臂 6D Cartesian twist target，夹爪为离散 open/close/stay；动态任务可直接输出末端 frame feed-forward wrench | 这是最强的真实机器人动作 RL 参考，但人类纠正、视觉、相对坐标和接触 impedance 设计会引入额外信息/数据来源；公平 baseline 必须去掉这些超出项目 observation contract 的输入。 |
| **AutoMate: Specialist and Generalist Assembly Policies over Diverse Geometries** | Robotics: Science and Systems XX (RSS 2024)，官方页面和论文 [rss20/p064](https://roboticsproceedings.org/rss20/p064.html)，[arXiv:2407.08028](https://arxiv.org/abs/2407.08028) | PPO；specialist policy 使用 assembly-by-disassembly demonstrations、imitation reward 和 trajectory matching；generalist 再做 BC/distillation/RL fine-tuning | actor observation 24D：7 joint angles、当前末端位置/姿态 3+4、目标末端位置/姿态 3+4、相对位置 3；critic privileged state 44D，另含 joint velocity、末端速度、plug pose 等 | 6D incremental pose target（位置 3 + axis-angle rotation 3），送给 task-space impedance；无 slowdown、无夹爪 action（夹爪流程在任务控制中单独处理） | action 维度和 impedance 层次最适合迁移到本项目；但 actor 使用 goal pose，critic 使用 plug pose，均不是项目允许的纯 proprioception-only 输入，必须删去或明确标为 privileged/非公平比较。 |

### 论文中的可核实要点

- SERL 原文将 MDP action 例子定义为 desired end-effector pose，并在实验中使用 6D end-effector delta pose；高层 policy 约 10 Hz，低层 impedance 约 1 kHz。官方 state-only 仿真环境的动作空间是 7 维，前三维为位置增量、后三维为旋转增量、最后一维是 gripper。
- HIL-SERL 原文明确区分连续动作 MDP 和离散夹爪 MDP；普通任务动作是 6D Cartesian twist target，动态任务可以直接输出末端坐标系 feed-forward wrench。它的高成功率依赖 demonstrations、实时 human correction、binary success classifier reward 和接触安全的 impedance reference limiting。
- AutoMate 官方 RSS 页面将其描述为 specialist/generalist assembly framework。论文明确写出 PPO、actor 24D、critic 44D、6D incremental pose target 和 task-space impedance。官方代码当前可以训练 `AutoMateTaskAssemble` specialist；它需要先收集 disassembly paths，首次运行 SDF 生成可能约 30 分钟，而且官方文档提示当前示例一次只支持一个 assembly。

## 官方代码和复现条件

### SERL / HIL-SERL

- SERL 官方代码：[rail-berkeley/serl](https://github.com/rail-berkeley/serl)；HIL-SERL 官方代码：[rail-berkeley/hil-serl](https://github.com/rail-berkeley/hil-serl)。两者采用 actor/learner 异步结构、`agentlace` 数据传输和 JAX policy learner。
- 官方安装文档给出的 GPU 路径是 `jax[cuda12_pip]==0.4.35`，Python 3.10；当前 JAX 文档也提供 CUDA 12/13 wheels。5080 是 Blackwell，建议在本机用项目已经准备好的 PyTorch CUDA 12.8 环境做接口实验，真正运行 SERL/HIL-SERL 时单独建立 JAX CUDA 13 环境并先验证 driver、JAX 和 MuJoCo EGL；不要把 `torch2.11+cu128` 环境直接当作 JAX 复现环境。
- 官方 SERL 仿真 quick start 是 Panda + cube lift，state-only 或 image observation，异步 SAC/RLPD；真实机器人实验需要 Franka 服务器、相机/SpaceMouse 或等价 teleoperation 设备，不能在本项目 MuJoCo fixture 上声称“忠实复现”真实 SERL。
- HIL-SERL 的人类纠正是方法组成部分。若没有真实 Franka 和纠正数据，只能复现其 RLPD policy/action interface，不能复现论文的 HIL 结果。

### AutoMate

- 官方代码：[NVIDIA-Omniverse/IsaacGymEnvs `automate` branch](https://github.com/isaac-sim/IsaacGymEnvs/tree/automate)，官方训练文档：[automate.md](https://github.com/isaac-sim/IsaacGymEnvs/blob/automate/docs/automate.md)。依赖 Isaac Gym Preview 4、Isaac Gym Envs、GPU PhysX、Warp 和 Hydra。
- `AutoMateTaskAssemble.yaml` 给出 `numObservations: 24`、`numStates: 44`、`numActions: 6`。动作在 `automate_task_assemble.py` 中解释为位置和 axis-angle 旋转增量，再由 task-space controller 生成控制信号；配置的 task-space impedance gains 是平移 `[1000,1000,1000]`、旋转 `[50,50,50]`。
- 官方 README 没有声明 Isaac Gym Preview 4 对 Blackwell/5080 的可靠支持。5080 上优先做兼容性 smoke test（headless、单环境、短 horizon）；若 Preview 4 二进制或旧 CUDA 与新驱动不兼容，迁移到服务器 DGX Spark 或改用本项目 MuJoCo PPO 环境，不能把失败归因于 PPO。
- DGX Spark为aarch64平台，不能仅凭GPU强就假定旧Isaac Gym Preview 4及其二进制依赖可用；目前没有验证其原始AutoMate运行栈在该机兼容。也不能把“换到服务器”当作已证实的兼容性解决办法。本机只有16GB RAM，首次SDF生成和高`numEnvs`训练需先限制规模。当前实际验证运行的是MuJoCo+PyTorch的接口适配baseline。

## 与 `proprio48_action7` / ESN 的公平性

本项目 student 的输入是 canonical 48D proprioception，输出固定 7D：

```text
action = [slowdown, yield_vx, yield_vy, yield_vz, yield_wx, yield_wy, yield_wz]
```

teacher action 来自 6D VMC 接触策略。ESN 的优势假设是利用时序状态和 recurrent memory 学习接触阶段切换；RL baseline 应该和它共享以下条件：同一 train/validation/test fixture split、同一 48D observation、同一 7D action contract、同一控制频率与 action hold、同一 reset/任务/release/penetration/force/torque gates、同一 office blind test layouts。

三篇论文原始接口存在这些差异：

| 差异 | 处理方式 |
|---|---|
| SERL/HIL 的第 7 维是夹爪 | 本项目无夹爪动作时删除；不要把夹爪状态或夹爪 reward 偷渡进 observation。若必须保留 7D，重新定义为项目的 `slowdown`，并在方法中说明不是原论文 action。 |
| AutoMate action 是 6D pose delta | 用确定性 adapter 映射成项目的 6D yield；`slowdown` 由 policy 第 1 个输出产生，或固定为 1 做 6D-only 消融。两种设置不能混报。 |
| AutoMate critic 有 privileged 44D state | actor 只能用 48D；critic 可用 simulator state 仅在训练时作为 asymmetric critic，并须单独标注。若比较“student 可部署策略”，建议 actor/critic 都只用 48D。 |
| SERL/HIL 可用图像、success classifier、human correction | 本项目 baseline 只使用 48D 本体和程序化 task reward；视觉、人类纠正、未来状态、接触真值、VMC 参数均禁用。 |
| 原论文多为高层 6D target，底层是 impedance | 在 MuJoCo 中统一使用项目现有低层执行器；RL 输出只改变高层 7D action，不能另换一套更强低层 controller。 |
| 原方法为在线 RL，ESN 为 VMC teacher imitation | 主结果建议区分 `offline action imitation` 和 `online task RL` 两栏；若要求同数据，给 RL 访问同一 teacher transitions 的 offline buffer，并把真实在线交互另列。 |

## 推荐的三个 baseline 版本

### A. `PPO-action7`（最容易审计）

在现有 MuJoCo 环境上使用 PPO，actor 输入 48D，输出 7D squashed action；critic 也用 48D。reward 使用现有任务成功、阶段进度、penetration、force/torque 和 timeout gates 的组合。这个版本借鉴 AutoMate 的 PPO + task-space action 方式，适合作为 ESN 的第一条 RL 对照线。

### B. `SAC/RLPD-action7`（最接近 SERL）

使用 state-only SAC 或 RLPD 风格 replay：continuous 7D action、固定 action scale、相同低层执行器。先用 teacher traces 填充 prior buffer，再以同样的 online transitions 训练；报告 prior-only、online-only 和 50/50 prior-online 三个设置，避免把 demonstration 数量差异误当作算法差异。

### C. `RL-tune-VMC`（调参方向，另列）

RL不直接输出yield，而输出VMC参数残差或低维schedule，例如stiffness/damping参数；底层VMC根据估计wrench计算action7。这个方向是“RL调解析VMC控制器参数”，并非优化ESN/MLP神经网络权重或训练超参数。它与直接action policy的问题定义不同，必须与A/B分开，不应放进direct-action主表。

## 建议的复现顺序（不启动长训练）

1. 先运行环境契约检查：确认 48D finite observation、7D action clipping、action hold、控制频率和 reward/gate 输出；保存 environment/source hash。
2. 在本机 5080 做 PPO `headless=True`、`num_envs` 很小、少量 iterations 的 smoke test，只验证前向、反向、checkpoint 和评估脚本，不产生论文结果。
3. 在 DGX Spark 做完整 PPO/SAC/RLPD sweep；每个 seed 保存 config、normalization、checkpoint、source hash、显存/内存峰值和 rollout manifest。
4. 冻结三个 RL checkpoint 后，统一跑现有 office blind test；同时跑 fixed VMC、impedance/admittance、MLP、linear ESN、nonlinear ESN。
5. 论文主表至少报告 task success、分阶段成功、峰值/P95外力、峰值关节力矩、速度 P95、jerk、penetration、非预期接触和恢复时间。RL 的 episode return 只能作为训练诊断，不能替代合规 gates。

## 复现边界与引用

这三篇论文的官方代码可以帮助复现算法结构和动作接口，但不提供本项目的 VMC fixtures、48D contract 或 office blind test。将它们用于论文时应写清楚：本项目实现的是 **interface-matched PPO/SAC/RLPD baselines inspired by AutoMate/SERL/HIL-SERL**，而不是声称复现原论文的真实机器人成功率。

```bibtex
@inproceedings{luo2024serl,
  title={SERL: A Software Suite for Sample-Efficient Robotic Reinforcement Learning},
  author={Luo, Jianlan and Hu, Zheyuan and Xu, Charles and Tan, You Liang and Berg, Jacob and Sharma, Archit and Schaal, Stefan and Finn, Chelsea and Gupta, Abhishek and Levine, Sergey},
  booktitle={2024 IEEE International Conference on Robotics and Automation (ICRA)},
  year={2024}, doi={10.1109/ICRA57147.2024.10610040}
}

@article{luo2025hilserl,
  title={Precise and Dexterous Robotic Manipulation via Human-in-the-Loop Reinforcement Learning},
  author={Luo, Jianlan and Xu, Charles and Wu, Jeffrey and Levine, Sergey},
  journal={Science Robotics}, year={2025}, doi={10.1126/scirobotics.ads5033}
}

@inproceedings{tang2024automate,
  title={AutoMate: Specialist and Generalist Assembly Policies over Diverse Geometries},
  author={Tang, Bingjie and Akinola, Iretiayo and Xu, Jie and Wen, Bowen and Handa, Ankur and Van Wyk, Karl and Fox, Dieter and Sukhatme, Gaurav S. and Ramos, Fabio and Narang, Yashraj},
  booktitle={Robotics: Science and Systems XX}, year={2024}
}
```
