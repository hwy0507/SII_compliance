# SimbaV2 训练目标与探索审计（2026-10-01）

本文记录只读审计结果，以及由此提出的受控修复。它不是最终性能报告，不能据此宣称 SimbaV2 本身不适合柔顺控制，也不能把旧训练失败作为一个已经充分调优的强基线结论。

## 1. 输入与范围

- 当前代码仓库：`/home/arm1/SII_compliance_baseline`，工作分支 `baseline`。
- 被审计 pilot：`/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/exploration_pilot_01`。
- pilot 冻结代码：`/home/arm1/vmc_mujoco_runtime/behavior_baseline_20261001/frozen_pilot_01/code/mujoco_6d_vmc_benchmark`。
- 官方 SimbaV2：`/home/arm1/vmc_mujoco_runtime/SimbaV2`，提交 `86899c277cdc697b2b02d827243de1ea93f20a1d`。
- checkpoint 读取环境：`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu`；加载前 source 仓库 `code/mujoco_6d_vmc_benchmark/experiments/simba_reward_20260930/gpu_env.sh`。
- 本审计没有修改训练状态、环境、checkpoint 或 pilot 日志，没有启动新训练；唯一新增文件为本文。

四个 run 是 `office_task_standard_entropy`、`office_task_low_entropy`、`metric_standard_entropy`、`metric_low_entropy`。每组 seed=51001、实际 10,000 transitions、warmup 5,000、warmup Gaussian std=0.02、gamma=0.9995、UTD=2、学习率预算 200,000 transitions。standard/low 的 target entropy coefficient 分别为 -0.5/-2。初始温度均 0.01。这里 office_task 是办公室任务适配奖励，不能称为 SimbaV2 原论文专门针对 Office 的奖励。

主要输入：各 run 下的 `PROTOCOL.json`、`progress.json`、`episode_summaries.jsonl`、`control_audit.jsonl`、`checkpoint_step_0005000`、`checkpoint_step_0010000`。所有 checkpoint 均仅在独立读取进程中加载。

## 2. 首要问题：任务成功与接触覆盖混为一个训练终止目标

四组记录中，episode 1 和 2（分别结束于 step 2750、4125）均同时满足：

| 字段 | 实际值 |
|---|---|
| task_success | true |
| placement_complete | true |
| physical_valid | true |
| strict_success | false |
| reward_terms.task | -20.0 |

它们已经完成有效放置，但旧严格验收还要求完整接触覆盖；训练代码直接使用 result.strict_success 决定成功奖励，所以这些成功任务仍被赋予失败代价。

冻结代码 `experiments/simba_reward_20260930/train.py` 第 158 行是 `success=bool(result["strict_success"]) if done else False`。该版本协议的 success_gate 也明确写为 result.strict_success。因此这不是日志展示差异，而是真正进入 replay 的目标定义问题。

“是否稳定放置且物理有效”和“是否触碰了本次协议指定的所有障碍物”应独立报告。把没有发生预设碰撞的成功避让也训练成失败，会让任务奖励与完成抓放目标冲突。不能通过刻意制造碰撞来获得奖励，也不能靠去掉物理验收获得成功。

建议新版本加入显式 `terminal_objective=task_physical`：终止成功由真实 task_success AND physical_valid 决定；保留 placement_complete 和原 strict_success、接触覆盖统计。旧 strict 模式只用于重放旧实验，不覆盖历史结果。真实 task_success 必须来自稳定放置判据，不能由 retreat/release 等阶段名称推断。

最小回归测试：

1. task_success、placement_complete、physical_valid 为 true，但 strict_success/coverage 为 false：新目标任务奖励 +20。
2. 同样放置结果但 physical_valid=false：负终止奖励。
3. final_stage=retreat 而 task_success=false：不能判成功。
4. 原 strict 模式对第 1 项继续给负奖励，保证历史可复现。
5. episode summary 同时保存“原协议 strict_success”和“训练 terminal objective success”，不能用后一字段覆盖前一字段而含混其含义。

## 3. 探索阶段覆盖良好，开始学习后覆盖消失

四组在 warmup 的控制阶段计数完全相同：

| 阶段编号 | 控制步数 |
|---|---:|
| 0 approach | 12 |
| 1 align | 163 |
| 2 grasp | 37 |
| 3 lift | 629 |
| 4 carry | 550 |
| 5 load_transfer | 2911 |
| 6 release | 26 |
| 7 retreat | 672 |

step >= 5000 的 5,000 个控制步，四组均为 approach 4500、release 422、load_transfer 78。后两项是从 warmup 延续过来的回合尾部；新启动的 episode 4、5、6 都停在 approach，未进入 grasp。

因此不能用“所有已结束回合的抓取率”选择 entropy 超参数；该数值会被共享 warmup 主导。应只用 episode 起点 >=5000 的完整回合，区分 warmup、跨边界回合、纯学习后回合。这个 pilot 的两种 entropy 设置在该口径下均没有恢复抓取覆盖。

该观察也说明环境和名义任务控制并非完全不可达；窄分布的随机残差曾完成放置。但它不证明已学习策略能完成任务。

## 4. 动作方差在 warmup 之后迅速增大

从 control_audit.jsonl 提取 requested_action，按 step 区间逐维计算均值、标准差，并统计 abs(action)>0.95 的比例：

- warmup：七维 std 均约 0.020，均值接近 0，无饱和动作。
- 5000–5099：std 约 0.29–0.39。
- 5500–5999：std 约 0.55–0.58。
- 9000–9999：std 约 0.57–0.59，约 2.9%–3.2% 的元素 abs(action)>0.95。

这不是主要由饱和边界造成的失败，而是大幅随机动作不断打断接近/抓取阶段的低速稳定条件。场景原要求接近目标约 12 mm、速度低于 0.025 m/s 并保持 0.2 s；线速度残差通道全量程为约 0.32 m/s。随机残差的量级足以阻止稳定进入该门槛。

## 5. checkpoint 的条件分布与统计量

方法：每个 checkpoint 从其 replay 读取第 0 条原始 observation，使用该 checkpoint 自己保存的 observation normalizer 标准化；直接调用官方 actor，读取 tanh 之前 Gaussian 的 mean/std。无动作执行或统计更新。

- step 5000：四组该状态的 pre-tanh std 约 0.016–0.051，温度约 0.010002。
- step 10000，office_task standard：std 约 0.703–0.822；low：0.743–0.862。
- step 10000，metric standard：std 约 0.517–1.033；low：0.394–0.960。
- 10000 的温度：standard 约 0.004039/0.004037；low 约 0.003979/0.003978。
- 该固定原始 observation 的标准化绝对最大分量从约 2.26 变为约 1.07–1.18；未观察到这个诊断状态出现归一化爆炸。
- 所有组 10000 的 replay-batch actor entropy 约 4.0–4.14，仍然很高。

因此仅把 target entropy 从 -3.5 改为 -14，没有在这段预算内迅速改变实际温度/探索幅度。它不等价于已经实现了一个低噪声策略。

## 6. critic 边界与熵项诊断

在 standard 两组 step10000 checkpoint 中，从 replay 的索引 0..9999 等间距取 256 个状态。分别评估 replay action、独立 PRNGKey(123) 采样的 policy action、全零 action。查看双 critic 的 Q 和 categorical log_prob 转换后的概率。

| 奖励组 | replay动作 Q均值 | policy动作 Q均值 | 零动作 Q均值 | 最上 +5 桶平均概率 | 最后10桶总概率 |
|---|---:|---:|---:|---:|---:|
| office_task standard | 1.27743 | 1.28031 | 1.27738 | 0.13318 | 0.22401 |
| metric standard | 1.23334 | 1.23599 | 1.23338 | 0.12662 | 0.21806 |

上表尾桶数据用 replay action。policy/zero 的尾桶概率非常接近。官方 critic 支持范围为 [-5,5]，101 bins。

尽管 episode 的任务终止奖励全部为负，Q 仍为正并不自动表示损失符号写反：SAC 风格 Q 包含软熵收益。当前 alpha×entropy 约 0.017/step，而日志中的归一化平均即时任务奖励约 -0.001/step；gamma=.9995 对应约 2000 控制步的无限时域尺度，熵收益的粗略持续累积尺度约 34。真实有限时域和状态相关性会改变该数值，不能把它当实际精确回报，但它显示较长 gamma、固定 critic support 与温度之间有明显尺度风险。

尾桶堆积和三类 action 的 Q 几乎无区分，支持“早期 critic 尚未可靠区分动作优劣、熵项主导探索”的诊断；它们不足以单独证明整个训练已经数值发散。需要后续曲线与受控干预验证。

已检查官方 actor loss 为 alpha*logpi - Q，温度损失符号也是官方实现；未发现这两项符号反转。不应在没有证据时将其描述为 SimbaV2 原实现 bug。

## 7. 建议的受控 pilot02

为避免同时修改许多因素，建议四路：两种 reward × temp_initial_value(0.01,0.0001)。全部使用修正后的 task_physical 目标、相同 seed、gamma=.9995、entropy coefficient=-.5、warmup std=.02、动作范围、公共过滤器、环境、预算。

- temp=.01 分支相对 pilot01 standard 仅改变 terminal objective，隔离任务目标修复的影响。
- temp=.0001 分支相对本轮 .01 分支只改变初始温度，测试过强熵探索假设。
- 两种 reward 必须共用最终选择的探索配置；选择只依据训练 pilot 的学习后覆盖，不看正式未知测试结果。
- 不引入 VMC、teacher 或 BC；不修改 actor 可见信息；不放松稳定放置/物理判据。
- 同时报告训练后抓取/放置、均值动作偏置、条件 std、温度、Q 尾桶概率。不要只看训练总 reward。

这是待验证实验建议；本文不宣称 pilot02 已完成，也不宣称此修复必然成功。

## 8. 独立行为验收审查

新 `experiments/simba_behavior_20261001/behavior_evaluate.py` 将局部接触后恢复/进展与最终放置分开，并在缺乏连续证据时返回 unknown，方向正确。

审查提出并由负责 agent 修复的归因漏洞包括：旋转参考突然变化可能制造虚假误差下降；后续同一球独立撞击及重叠其他接触可能污染首次碰撞的恢复归因。新版记录 reference_rotation 并对这些情况截断/标记归因不确定。

持续接触窗口允许最多 0.08 s 的短时接触间隙，应描述为“间歇承载接触窗口”，并报告接触占空比、最大间隙，不应宣称每个物理时刻持续受力。5 s 窗口内局部滑移与实际路线净进展不是完整清障证明，也不是稳定放置证明。

新增球撞后继续推进分支允许先真实重新进入碰撞起点的原目标邻域，再沿真实路线推进；它和低速 settled recovery 必须分列。一次保留 0.2 s 的局部推进不证明此后完全无逆行或振荡。

现有已看过、修改过的办公室布局属于开发验收集。后续正式泛化测试仍需冻结新的未参与调参条件。

## 9. 对旧结果的使用限制

历史成功率为零仍可如实保留，但必须注明旧 terminal objective 混入接触覆盖，且 learned exploration 缺少抓取覆盖。它们可用于修复前诊断，不足以支持“充分训练仍然不行，所以算法先天弱”的结论。

修复前后保持各自冻结源、配置、checkpoint、seed、训练预算与完整失败日志。不得覆盖旧结果、混合口径排名或隐藏失败；新的 task_physical 成功也不能冒充旧 contact-required strict_success。
