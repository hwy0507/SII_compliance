# SPT 方向的 RL 训练交接：先预检，再四接口同目标训练

2026-10-25。用户要求把下一轮 RL 脚本与 reward 设计发布，供其他 agent 接手。
本次交付实现训练入口与奖励，没有启动新训练，也没有生成新的学习结果。
先读根 `AGENTS.md`、`EVALUATION_STANDARD_SPT_20261025.md` 和本文件。
本方案是可执行的 **SPT 导向训练代理目标**，不是已实现/已验证的正式 SPT benchmark。
服务器 agent 从 [项目背景与四卡并行入口](RL_SERVER_START_20261025.md) 开始；用户已授权
4张4090/55核服务器计算，旧“服务器仅归档”限制不再适用于这轮新run。

## 1. 本轮科学问题和范围

主问题：同样的真实交互预算下，四种接口能否从训练中改善回报并稳定，冻结后在未见条件上
兼顾 Task/Strict、完成效率和接触负载？不预设 RL 或 ESN 必须胜出。
Direct 输出原 action7；阻抗/导纳/VMC 每 40 ms 输出原在线参数（维度由冻结 PRIORS 给定）。
统一 canonical48、公共 filter、执行器限制、物理/MJB、dt=5e-5、55 s 审计窗口。
不更改最终 gate，不给 actor 添加接触真值、物块位置、时间或任务阶段。
真值只进入训练奖励和审计；所有接口使用同一个奖励公式。

从头使用 pinned 官方 SimbaV2，**不用旧 checkpoint、旧 replay、teacher 示范或 BC**。
旧任务奖励已变，不能直接继承旧 reward normalizer/critic。现有 `teacher.json` 在此只是公共
场景/执行配置，worker 的运行时 teacher 为 none；不是读取 teacher action 标签。
经典参数 priors 保留并披露，不把参数控制器的结构性先验隐去。

## 2. 可运行文件

相对于 `code/mujoco_6d_vmc_benchmark/`：

- `tools/prepare_rl_spt_campaign_20261025.py`：prepare/check/run；冻结源码、配置和参数适配器，
  生成明确命令；每个run用 systemd 硬资源限制。本机单路；服务器模式使用GPU/CPU/并发槽租约。
- `tools/prepare_rl_spt_campaign_20261025.py matrix` 与 `tools/run_spt_server_parallel_20261025.py`：
  服务器四方法×三seed准备和四卡有限队列，详见服务器入口。
- `tools/spt_rl_reward_20261025.py`：唯一 reward CONFIG、人体接触物理子步归约、reward reducer，
  以及需要真实完成时间的纯 SPT 数学函数。
- `tools/train_v4_recovery_rl_20261016.py --reward-variant spt_v1`：实际在线 learner/worker 接入。
- `tools/baseline_repair_online_worker_20261008.py`：独立 reward telemetry，包括初始物块 potential。
- `tools/audit_spt_reward_20261025.py`：含首项的全部已闭合奖励逐项重放；**不替代独立物理审计**。
- `configs/rl_spt_training_20261025.json`：训练规划与正式评估缺口。

GitHub 不含大模型和全部 runtime。当前本机 Python 为 workspace 下的
`.venv-sii-local-rl/bin/python`；父协议/条件/参数源为
`outputs/rl_tuned_20261015_v4/`，公共 runtime 为
`outputs/baseline_local_rl_20261009/runtime/`（需要 v6 二进制、menagerie、SimbaV2、rewards）。
没有这些产物的机器先按原 provenance 获取并校验；不能重新编译不同 MJB 冒充原模型。
prepare 会拒绝缺失的关键输入；upstream adapter 也会核对其 pinned Git commit。

## 3. 奖励定义与初始数值

`h=55 s`，`gamma=0.9995`，`dt_a=0.04 s`。令 `b(x)=max(0,x)/(1+max(0,x))`。
物块进度 `Phi` 复用已实现的 `payload_reward_potential_20261014.py`：手到物块接近、
物块抬升、物块到最终放置目标接近三项等权，范围 [0,1]；不使用会跳变的局部 waypoint 误差。
这只是连续任务代理，不能用 Phi=1 代替抓取/释放/保持等正式 Task 判定。

| 项 | 默认定义 | 目的/边界 |
|---|---|---|
| potential shaping | `5*(gamma*Phi_next - Phi)`；终端 Phi_next=0 | 给局部 TD 指导；正确折扣求和仍抵消，不能独自解决稀疏成功 |
| 剩余进度成本 | `-4*(1-Phi_next)*dt_a/h` | 显式改变训练目标，鼓励更早推进；不是纯 shaping |
| 时间成本 | `-dt_a/h` | 记录时间代价；固定完整55s时总和为常数，不能谎称它已直接优化 SPT |
| 人体接触力矩代理 | `-2/h * integral(I_human * b(max_j(abs(tau_j)/(.5*tau_limit_j))-1) dt)` | 仅同一物理子步发生人体接触时计费 |
| 人体接触力代理 | `-1/h * integral(I_human * b(F_human/15N-1) dt)` | 有界超尺度成本；F 为接触力模之和，不是净合力 |
| 外部穿透 | `-8*delta(running_max b(penetration/.0002m))` | 全外部接触，峰值增量避免重复收费 |
| 执行器峰矩 | `-delta(running_max b(max_j(abs(tau_j)/tau_limit_j)))` | 全回合机器负载代理；保留原始峰值和违规 |
| 执行力矩变化 | `-.25*min(existing_servo_slew_cost, dt_a/h)` | 同一物理执行尺度，覆盖阻抗的原生力矩通道 |
| 终奖 | Task AND Strict：+25；否则 -25 | 超时/早退失败均保留，Task-only 另报但不算成功 |

人体接触定义：`research_channels.json` 的 `human_robot_sum`（列2），力模之和 >0.05 N。
不是 `external_robot_sum`；球、杆、柱、桌边不能冒充人体接触。分母按实际接触秒数积分。
无人体接触：舒适代理比例 `null/NA`，不输出 100%；同时报告接触覆盖与任务失败。
`0.5*执行器限幅`、`15 N` 是 **初始工程训练尺度**，没有人体舒适标定证据，不能当成“让人舒服”
或人身安全认证阈值。原安全 gate 不因此改变。

不加按原始动作变化的惩罚：不同参数接口动作维度和含义不同，使用相同的实际力矩 slew。
所有密集成本按时间归一、有界；提前失败在终端加上剩余密集成本的折扣上界，峰值成本补足
剩余预算，防止提前中止逃避惩罚。安全违规原值仍完整记录，有界训练损失不是忽略极端失败。
初始 potential、每步 interval、全部 reward 分项与总和写日志；reward 不与旧配方混画或直接排名。

## 4. 本机备用启动命令（服务器首选按专门入口执行）

先按 sync skill 更新远端日志、检查服务和 execution，确认没有并行旧作业。
在仓库根进入 benchmark 后执行；变量只是方便处理含空格的本地路径：

```bash
cd code/mujoco_6d_vmc_benchmark
SII_PY='/home/airpig/桌面/hwy/compliance_control/.venv-sii-local-rl/bin/python'
SPT_RUN="$PWD/outputs/rl_spt_20261025_v1"
"$SII_PY" tools/prepare_rl_spt_campaign_20261025.py prepare \
  --root "$SPT_RUN" --parent outputs/rl_tuned_20261015_v4 \
  --parameter-source outputs/rl_tuned_20261015_v4/parameter_fullrange \
  --runtime outputs/baseline_local_rl_20261009/runtime \
  --seed 20261025 --steps 1000000 --dispatch-hours 72 --cpu 1
"$SII_PY" tools/prepare_rl_spt_campaign_20261025.py check --root "$SPT_RUN"
"$SII_PY" tools/prepare_rl_spt_campaign_20261025.py run \
  --root "$SPT_RUN" --family direct --stop-at-step 1375 --dry-run
```

确认命令和输入后去掉 `--dry-run`，先跑一个完整回合（1375步，仍是探索预热，未学习）。
四方法各做一次 1375 步预检，同一时刻一路；family 为 `direct/impedance/admittance/vmc`。
检查运行者真实 steps、checkpoint/hash、canonical48、原始动作/公共 filter、物理 gate、
无 OOM/swap，并对新 telemetry 做原始物理子步复算及开关前后同动作物理一致性检查。
这次发布没有做该 MuJoCo 预检；不能把 dry-run 写成它已通过。

已闭合片段的奖励重放命令（必须用 run 内源码）：

```bash
"$SII_PY" "$SPT_RUN/source/tools/audit_spt_reward_20261025.py" \
  --segment "$SPT_RUN/direct/segment_0001375" \
  --output "$SPT_RUN/direct/reward_audit_0001375.json"
```

预检通过后，按同一协议从每路已登记的完整 checkpoint 分段续训，例如 Direct：

```bash
"$SII_PY" tools/prepare_rl_spt_campaign_20261025.py run \
  --root "$SPT_RUN" --family direct --stop-at-step 11000 \
  --resume-checkpoint "$SPT_RUN/direct/segment_0001375/checkpoint_0001375"
```

每阶段各方法轮流推进；累计边界建议 11k→55k→110k→250k→500k→1M。
`--resume-checkpoint` 必须取 execution 登记的真实末 checkpoint；早退导致步数不整齐时不能
猜文件名。--steps 固定1M对应同一优化器日程，--stop-at-step 只是片段界限。
余量不足一个完整回合时不派发，可能比名义1M少至多1374步，必须报告真实计数。
若 deadline 到期，保存回合末状态，登记新的有限续接协议，不改写已冻结协议、伪造完成或自动延长。
STOP_REQUESTED 是回合边界停止入口；不要 kill 整个进程组。

## 5. 学习设置、故障处理和收敛

初始配置：gamma=.9995、单步TD、UTD=1、batch=256；5000步 AR(1) 探索预热（rho=.9，
std=.10）；entropy coefficient=-.5、initial temperature=.01；pinned SimbaV2 学习率
1e-4→5e-5、actor 128、distributional twin critic 512、normalizer 按原实现。
配置由 parameter adapter 实际 `agent.config` 落盘；n_step 非1时 spt_v1 拒绝启动。
本机备用模式3 GiB hard MemoryMax、禁swap、CPU单核/单线程、单模拟器。
服务器模式默认每路8 GiB、禁swap、GPU learner+CPU物理，最多四路独立作业；实际资源必须登记。
checkpoint 每个回合保存，需监视磁盘并按既有独立归档/hash核验流程安排存储；不自动删除原始失败。
百万步是有限最大预算，不是收敛保证；72小时是派发保护，也不是充分训练声明。

先看真实更新数与参数变化、reward 各项量级、熵/temperature、Q/critic、动作限幅/参数
变化率饱和、控制接口能否实际改善任务。发现实现错误先保留失败，修复后新建独立 run；
不能在正在执行的源码快照内修改文件，不能给旧 replay 静默换 reward。
若无改善，可在训练/dev 上登记有限的单因素候选，例如 temperature 0.003/0.01，或
occupancy 权重2/4/8；当前验证器故意只接受v1，修改要发布新版本并从头训练，不能只改JSON。
测试集不参与任何选择。不要以“让 RL 输给 ESN”为调参目标。

建议训练判据：预热后至少跨过3个完整32条件轮次；看同身份配对的回报改善，再看末3轮
均值变化≤5%、轮均值斜率和不确定区间，无新增数值失败/温度异常。近零均值不能用CV下结论。
完整学习历史仍无改善，即使平坦也标为“停滞”，不能写“已学习收敛”。该建议需在正式训练报告
中登记并按原始日志计算，当前 launcher 不会自动判断收敛或自动解锁 test。
reward 稳定与训练/测试性能分开报告；不要求 baseline 必须任务成功才能算回报稳定。
多seed正式比较建议至少3个独立训练seed，所有seed都报告；prepare默认单seed，服务器matrix默认三seed。

## 6. SPT正式测试前的剩余工作（不得用默认数字绕过）

当前 runner 固定55s，终端才给 Task/Strict。必须提取与最终 Task **全部条件**一致的完成时刻，
含稳定保持和撤回等要求；旧 placement_time 未必覆盖完整 gate。完成后仍保留完整安全审计窗口。
每个条件的 T_ref 由实验前登记的参考生成流程给出，记录可行性与hash。若不能证明最优，只能称
“固定可行参考时间”，不能称理论最优。不能拿被测 RL/ESN 中最快的结果反填 T_ref。

正式 `SPT_i = (Task_i AND Strict_i)*T_ref_i/max(T_i,T_ref_i)`；失败为0，全条件宏平均。
本模块提供公式函数，**没有替调用者生成 T_i/T_ref，也没有完成最终评估集成**。
还需标定并登记人体舒适阈值及其测量量：执行器力矩不是人体接触力矩/力的等价替代。
临时训练代理不可作为最终舒适率。现有旧24测试条件已看过结果，不应再声称从未见过；
新一轮要登记新的保留组，或明确旧组只作历史复测。

最后同一套未见条件比较 ESN、四类RL及经典基线，固定模型后才打开测试；报告 Task/Strict、
SPT、完成时间、逐关节峰矩、接触覆盖/舒适率、人体接触峰力/力模积分、穿透、违规和失败原因。
做独立物理子步、raw actor/public filter replay、source/config/checkpoint hash核验。
正式排名以这些证据为准；训练reward不是最终性能分数。

## 7. 本次验证与交接状态

已完成：奖励/启动契约测试、prepare/check/dry-run；未做：服务器CUDA/四卡实测、新MuJoCo回合、梯度更新、百万步训练、
新物理子步一致性审计、最终SPT/舒适标定、未见组测试。这些都不能因脚本存在而写成已完成。
本次源文件和规范推送 main；没有新增服务器实验产物。
