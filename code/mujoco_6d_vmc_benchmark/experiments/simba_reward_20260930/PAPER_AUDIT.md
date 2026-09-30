# SimbaV2 原论文、官方实现与 Office 适配核查

日期：2026-09-30。此报告是源码/论文审计，不是新实验性能结果。

## 结论

SimbaV2 没有一套通用的机械臂 Office reward。论文提出的核心是用于 SAC 的超球面归一化网络、分布式 critic 以及 reward bounding/scaling。实验沿用 MuJoCo、DMControl、MyoSuite、HumanoidBench 各自的 task reward。我们能够复现的是算法结构与奖励处理方法，再明确给出新 Office 任务的奖励定义，不能把 Office 自定义 reward 称作论文原始 reward。

本次建议的两个主组：
1. SimbaV2 + Office task reward（office_task）：严格成功/失败 + 全局势函数进度 + 时间成本，采用原论文奖励处理方式。
2. SimbaV2 + metric reward：保留第一组任务奖励，并加入用户指定的全子步累计误差、实际峰值力矩增量与弱动作平滑代价。
稀疏 task_only 仅作为可选消融，不作为主基线，以免无必要地降低任务学习信号；以上均明确是 Office 适配奖励，不冒称原论文通用 reward。
两组共享 actor 输入、action 接口、物理协议、网络、normalizers、discount、UTD、训练数据预算、训练分布及 checkpoint 选择规则。

## 可核验来源与服务器路径

- 原论文：Hojoon Lee et al., *Hyperspherical Normalization for Scalable Deep Reinforcement Learning*, ICML 2025。https://arxiv.org/abs/2502.15280
- 官方仓库：https://github.com/DAVIAN-Robotics/SimbaV2
- 固定官方 commit：`86899c277cdc697b2b02d827243de1ea93f20a1d`
- 官方服务器 checkout：`/home/arm1/vmc_mujoco_runtime/SimbaV2`
- 论文原始 PDF：`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/paper_sources/SimbaV2_2502.15280.pdf`
- 论文全文提取：`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/paper_sources/SimbaV2_2502.15280.txt`
- 本报告：`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/PAPER_AUDIT.md`
- 新封装：`/home/arm1/vmc_mujoco_runtime/reward_study_20260930/src/official_agent.py`
- 官方 `configs/agent/simbaV2.yaml`：normalization、网络、critic 支持区间。
- 官方 `configs/online_rl.yaml`：discount heuristic、update ratio、随机采集。
- 官方 `configs/buffer/numpy_uniform.yaml`：replay、batch、warmup。
- 官方 `scale_rl/agents/wrappers/normalization.py`：归一化更新与存档。
- 官方 `scale_rl/agents/simbaV2/simbaV2_update.py`：SAC 与 categorical TD loss。
- 官方 `scale_rl/agents/__init__.py`：正确的 wrapper 接线。
- 旧 Office runner：`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts/train_official_simba_v2_office_resume_20260929.py`
- 旧 Office 配置：同目录 `train_official_simba_v2_office_20260927.py`
- 旧 Office reward：同目录 `train_simba_v2_office_20260927.py`

## 论文奖励处理与实现

论文 §4.3（PDF 第5页）Eq.17–19 对运行折扣回报进行统计：
`G_t = gamma * G_(t-1) + r_t`；
奖励只除以尺度，不做均值中心化：
`r_scaled = r / max(sqrt(var(G)+1e-8), max_abs_G / 5)`。
论文明确指出：episodic task 中 reward 的平移可能改变最优策略，故不中心化。
critic 是 101 个 return atoms，支持区间 [-5, 5]，TD 分布目标超出支持区间会被截断。

官方实际 RewardNormalizer 在 sample_actions(training=True) 时以完整上一 transition 更新统计，update 时才缩放 replay 的原始 reward。其 done=terminated OR truncated，实际统计递推为
`G = gamma * (1-done) * G + reward`，
并记录历史 max(abs(G))。新封装严格复用这一官方递推，没有暗改归一化定义。

奖励缩放是算法的组成部分，固定乘 0.04 不能宣称等价：固定缩放不能针对实际 return 分布自适应防止有限 categorical support 饱和。

## 核心标准配置与论文/代码分歧

| 项目 | 官方代码 / 论文证据 | 新封装 |
|---|---|---|
| Backbone | SAC，非 PPO | 官方 SAC |
| Actor | 1 HyperLERP block，宽128，tanh Gaussian | 相同 |
| Critic | 2 blocks，宽512，101 atoms | 相同 |
| CDQ | 对有失败终止的任务启用 | True |
| BC 权重 | 在线为0 | 0 |
| Observation | running mean / variance normalization | 官方 wrapper，原始48维 |
| Reward | bounding/scaling，g_max=5 | 官方统计与缩放 |
| Gamma | TD-MPC2 heuristic，截在[.95,.995] | 55秒、25Hz给出 .995 |
| Replay | 1M容量，uniform | runner 必须实现 |
| Batch | 256 | 常量256 |
| Warmup | 官方buffer min_length=5000 | 常量5000，runner负责 |
| UTD | 论文附录C Table3为2；代码由action_repeat驱动 | 两组统一2 |
| Target tau | .005 | .005 |
| 初始温度 | .01 | .01 |
| 熵目标 | 代码 temp_target_entropy_coef=-.5 | 相同 |
| Learning rate | 代码1e-4至5e-5；论文表末值写3e-4 | 以固定官方代码5e-5为准 |
| Optimizer | Adam，无weight decay | 官方实现 |
| n-step | 1 | 1 |

论文附录C Table3 与代码的 final learning rate 存在差异，不将其悄悄抹平。我们的可复现声明应是“固定官方 commit 的实现、使用论文 UTD=2”。

## 旧 Office 实现的实质性差异

1. 旧 runner 导入裸 SimbaV2Agent，绕过 create_agent，因此 observation/reward wrappers 实际均未使用。
2. 旧 obs 是固定比例 tanh(raw48 / scale)，并非论文 running-statistics normalization。
3. 旧 reward 固定乘1/25，critic仍支持[-5,5]；return 超范围时可能被投影截断。
4. 旧 gamma=.999；官方55s/1375步 heuristic 为.995。折扣目标显著不同。
5. 旧训练每transition更新一次（UTD1），最早256 samples就更新；warmup1375只控制随机action，未阻止提前梯度更新。
6. 旧 replay 是不断增长的Python list，不是上限1M ring buffer。
7. 旧 resume 可恢复优化器，但 replay 清空，不能称为精确断点续训。
8. 旧 observation 首动作映射 bug 已在20260929 resume runner修正：actor tanh第一维只进行一次[-1,1]至[.2,1]仿射转换，replay保存原tanh action。新代码应保留该正确接口。
9. 旧奖励对误差做截断、接触调权，以控制采样端点估计速度/力矩峰值；与用户本轮要求的全物理子步误差和真实执行峰值力矩并不相同。

以上不是既有性能退化的因果证明，需要新实验控制变量后再判断。

## 终止、超时和 actor 信息限制

官方 critic 的 bootstrap mask 只使用 terminated，不使用 truncated。普通 TimeLimit 截断保留bootstrap；真实失败或成功终止关闭bootstrap。
本项目若55秒是明确的任务deadline，超时为任务失败，可以定义terminated=True；若只是采样器收集窗口，则应truncated=True。必须在协议中明确选择，不能混用。

原始 actor仍仅接收允许的48维因果本体观测及任务命令。进度/失败审计可以用训练环境的任务状态，但不得额外加入actor输入。Office task-only组的任务成功也必须由严格placement及physical gates定义。

## 新封装接口与统计保存

`OfficialOfficeAgent(seed, total_steps, utd=2, gamma=.995)`

- `sample_action(raw_obs, previous_transition=None, training=True)`：返回未映射的tanh action7。
- previous_transition只需reward/terminated/truncated，传原始未归一化reward。
- 每个交互只调用一次，包括随机warmup（可丢弃actor动作并执行随机动作）。
- done后先reset，传新的raw_obs以及上一terminal transition；统计复用官方递推。
- `update(raw_batch)`：复制batch后由官方reward/observation wrappers归一化，避免污染replay。
- `consume_transition(reward,terminated,truncated)`：如最后一条transition后不再调用sample_action，用它补齐reward统计；同一transition不能重复消费。
- `save(path)`、`load(path)`：官方actor/critic/target/temperature参数和优化器，两个normalizer统计、JAX RNG以及更新/交互计数。
- replay与环境状态由runner另存。仅该封装checkpoint不能称为整条仿真精确续跑。
- eval使用training=False，统计冻结；评测种子和结果不进入训练normalizer。
- 原始48维不再做旧的固定tanh预处理，两组必须一致。

## 实验解释的边界

1. “无成功”不能自动说明算法本身弱，尤其task-only稀疏reward下探索、训练量与信用分配很重要。
2. gamma=.995时55秒的终点奖励折扣约为 .995^1375 = .001，终点信号传到起点很弱；它是原配置启发式产生的现实限制。可在足够预算后增加预注册配对gamma敏感性分析，但不要只给某一组单独调参。
3. 两组比较时网络、normalizer和gamma同时修正仅能与各自旧版作诊断；新两组彼此的唯一主变量应为reward结构。
4. 论文峰值force/velocity/torque等物理指标必须由原始轨迹计算，不能从normalized reward反推。
5. 要保存完整训练曲线、同预算多seed和冻结布局评测，报告成功率与物理无效率。固定Office开发布局上调参的结果不自动具有未知场景泛化含义。
6. 用户要求的峰值力矩增量仅在未折扣求和时严格望远镜等于终末峰值平方。正常gamma<1需明确此差别。
