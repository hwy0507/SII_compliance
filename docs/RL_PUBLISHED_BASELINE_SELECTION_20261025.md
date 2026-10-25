# 已发表柔顺控制基线筛选与训练集比较接手记录

2026-10-25。本轮来源 main `a1965543edd8302a95521bf71e3fb139c4a07c49`、
baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。

## 当前用户任务与执行状态

用户要求自行搜索近期已发表的 data-driven 柔顺控制方法，优先保留原方法机制、尽量仅
调整任务 objective；训练参数 RL 和直接动作 RL 至有学习改善后的 reward 稳定且优化
诊断正常，再在**训练集**上与指定的现有 ESN 比较。本轮不研究 ESN 本身，也不打开未见组。
这已授权后续适配、奖励设计、测试和训练，覆盖此前本会话只读等待要求。

用户同时明确：本轮 SPT 的 T_ref 使用全部结果中最短完成时间；力矩参考阈值可经验选择
或通过先行数据给出。该新要求优先于旧的预登记 T_ref 规则，但仅在本训练集研究中生效。
持续 Goal 的后续授权已允许必要的方法/接口适配，取消总步数上限，允许在四卡4090上仿真
和训练并由agent自主决策。原 Task/Strict gate、执行器限制及公共 filter 保持共同；新增
算法上下文与接口差异明确登记，不把环境真值加入部署actor。

**状态：正在恢复源码可构建的三类任务运行时，尚无新训练收敛结果。** 历史冻结运行产物
及用户指定 ESN 尚未找到，旧归档网络不通。新环境以独立cohort记录，绝不冒充同一历史MJB；
与ESN的最终配对仍需相同新环境及真正的ESN checkpoint。下面的候选选择不是已完成复现。

## 检索方式与证据等级

检索 Crossref 发表记录、arXiv 原文、作者项目页和公开源码，关键词包括 variable impedance、
compliant manipulation、force control、reinforcement learning，重点覆盖 2023–2026。
通用搜索引擎发生验证或不相关返回，未将这些返回当论文证据。部分 API 限流；不声称穷尽
所有工作，也不凭会议名称、GitHub stars 或发表年份宣称“当前最强”。

完整机制核对：CoRL 2023 Zhang、ICRA 2024 Portela、CHEQ polishing、DA-VIL、C-GMS 的
论文主体；VICES 作者项目/源码说明。IEEE Access 2024 的工作只核对发表记录及后续论文
对其 model-based RL 的描述，不能据此声称已完成全文或官方实现核验。

## 候选矩阵

| 工作 | 发表/来源 | 核心机制 | 与本项目匹配 | “只换 reward”限制 |
|---|---|---|---|---|
| CHEQ-ing the Box | IFAC-PapersOnLine 2025；DOI 10.1016/j.ifacol.2025.10.241 | SAC ensemble、上下文化混合权重、名义控制先验、可变阻抗 | Franka Panda、MuJoCo、物理接触、公开代码；近期优先候选 | 策略含混合权重 context；原动作为位姿增量+刚度+阻尼，原输入含 F/T 与路径前瞻。固定48/现有参数接口下不能宣称仅换reward |
| CHEQ underlying learner | Reinforcement Learning Journal 2, 926–945, 2024 | Contextualized Hybrid Ensemble Q-learning | 通用连续动作学习器，可研究两个接口上的同算法比较 | 移除ensemble、context或混合机制就不再是完整CHEQ |
| Learning Force Control for Legged Manipulation | ICRA 2024；DOI 10.1109/ICRA57147.2024.10611066 | PPO、观测历史、受监督估计器、非对称critic、期望力跟踪 | 有公开实现；直接动作RL的文献候选 | 原为关节位置目标+力命令；action7无力命令，单加history/PPO不算完整方法 |
| Online Admittance Residual Learning | CoRL 2023/PMLR229 | SAC运动及初始导纳+部署时记录力序列并约束优化参数残差 | 单机械臂、MuJoCo、接触操作 | 在线优化和F/T测量不可悄悄删除；只有参数SAC是其部分结构 |
| DA-VIL | ICRA 2025；DOI 10.1109/ICRA55743.2025.11127487 | PPO刚度选择、可微优化/QP、双臂协同 | 使用MuJoCo，操作相关 | 双臂动力学约束和优化层不是换reward即可迁移；不优先 |
| C-GMS | ICRA 2026；DOI 10.1109/ICRA57385.2026.11695701 | DMP+VIC、认证参数流形上的轨迹级采样 | 新近发表，有明确稳定性结构 | 依赖DMP和认证可行集合，保留当前固定参考时适配较大；不能移植稳定性结论 |
| Data-Efficient RL for VIC | IEEE Access 2024；DOI 10.1109/ACCESS.2024.3355311 | model-based VIC学习 | 单臂操作、参数学习 | 不是替换成SAC就算复现；本轮全文/代码未完整核实 |
| VICES | IROS 2019；DOI 10.1109/IROS40897.2019.8968201 | 端执行器可变阻抗动作空间，比较多种直接/参数动作 | Franka、MuJoCo、公开控制器、任务奖励可换 | 非近期论文；原位姿+阻抗动作仍不同于当前受限5/7维接口 |

VICES 是历史方法来源，2025 polishing 论文仍将其作为控制结构依据。不能把VICES写成
2025新算法，也不能把SAC/PPO优化器本身称为一套已复现的柔顺控制方法。

## 筛选结论与最小适配界限

优先保留 **2025 polishing/CHEQ 作者实现**作为进一步接入候选，原因是任务平台相近、
参数控制链明确、源码可核查。参数RL与直接动作RL若采用同一作者SAC学习核心，可减少
自行搭建弱learner的风险；但必须分别标为“作者SAC核心的FR3接口适配”，不能改名为
完整CHEQ或复现论文全部结果。完整CHEQ需保留context、Q ensemble、adaptive mixing、
其replay中的raw action和context语义，不能只搬两层网络。

没有找到能在**canonical48、action7/现有5/7维参数接口均不动**的条件下，诚实称为
“近期专用柔顺控制完整方法、只改reward”的即插即用实现。这是接口与方法身份的实际
冲突，不能靠重命名解决。换目标也不自动等于公平：信息权限、训练曝光、控制先验、
在线优化和示范数据必须同时披露。允许平台相关适配与最少改变核心机制是可操作目标。

ICRA 2024 方法暂不作为最小改动首选；其公开实现的估计器和真实力命令机制应保留在
后续方法核对表内，不将“history PPO”误标为该论文的完整控制器。

## 已核对的公开代码

- [polishing-cheq](https://github.com/Data-Science-in-Mechanical-Engineering/polishing-cheq)，
  `1a3c1fee3332848068afdb127c4fa33eee420418`，MIT。读取README、SAC/ensemble配置、
  hybrid_agent_cheq、actor/trainer的context传递、policy结构。
  默认ensemble 5、网络256×256、自动temperature；普通SAC也在同仓库。
  `async_actor.py` 显式向观测注入mixing weight，因此原方法actor不能称为原封不动canonical48。
  原repo依赖W&B及自己的异步采集，迁移时本地日志和完整resume需单独审计。
- [learning-compliance](https://github.com/Improbable-AI/learning-compliance)，
  `c760e1d74ad165d3c069d4f57ab5d066f6a41eb6`。核对actor/critic、PPO、train配置。
  actor使用history+估计状态，critic使用history+训练真值；原代码与论文历史长度等默认值
  不同，复现需固定版本。未运行该项目的Isaac Gym或训练脚本。
- [VICES控制器分支](https://github.com/StanfordVL/robosuite/tree/vices_iros19)，
  `ce81aba2f1896ae6582f796d3ba98c8f75f14a3d`。明确包含直接动作及阻抗控制器。
  原依赖较旧，不把旧MuJoCo环境带入冻结FR3运行时。

论文：

- <https://arxiv.org/abs/2501.07985>（polishing）
- <https://arxiv.org/abs/2406.19768>（CHEQ learner）
- <https://arxiv.org/abs/2405.01402>（Portela）
- <https://proceedings.mlr.press/v229/zhang23e.html>（Zhang）
- <https://arxiv.org/abs/2410.19712>（DA-VIL）
- <https://arxiv.org/abs/2511.16330>（C-GMS）
- <https://doi.org/10.1109/ACCESS.2024.3355311>（Anand）
- <https://stanfordvl.github.io/vices/>（VICES）

## 本轮指标与奖励

定义独立scope `training_set_empirical_v1`，旧实验和正式预登记参考标准不重写。

1. Task和Strict分别报告；主SPT用Task AND Strict。失败仍在分母，严格成功数为零时
   T_ref=NA、SPT=0。快但不安全的失败不能设定成功参考时间。
2. 按用户“所有结果里面最短”的要求，全部登记方法、条件、seed的严格成功回合中取
   **一个全局最短完成时间**作T_ref。称为 `SPT_empirical`，明确是本轮集合的事后归一化，
   不是预先冻结参考轨迹得到的正式SPT；增减比较集合会改变分数。
3. T必须是实际任务完成时刻，不能直接用55秒审计长度。拟定义为最终连续有效放置段内
   首次满足0.5秒稳定条件及抬升条件的时刻；其后若有效性中断，旧完成记录撤销，从最后
   有效段重新认证。仍跑满55秒并按原gate判Task/Strict。这需要真实runner记录对齐后才能
   接入，不从RMSE或reward猜T。
4. 力矩报告每关节峰值、全关节最大值、物理P95；机器违规单列。先用运行时各关节
   执行器限制的0.5倍作为工程参考阈值，保留现有spt_v1尺度；这不是经过标定的人体舒适值。
   独立预检后若发现重力支撑占据主要阈值预算，可登记校准修订并从头建立新reward cohort，
   不能只针对某个方法改阈值。报告也可显示多个预定阈值下的完整曲线。
5. 主比例采用**真实人机接触时间内，所有7关节同时低于各自阈值的时间比例**；按dt加权，
   不能按不等采样帧数或含无接触阶段计算。无接触返回NA；全时域峰矩仍包含无接触时刻。
   应另保留逐关节比例、超阈值时间/积分、人接触力和冲量，不能将力矩比例当人身安全认证。

奖励继续围绕Task/Strict、完成效率和物理成本，不将事后T_ref动态塞入训练目标。
现有spt_v1已有payload progress/occupancy、人体接触负载、峰矩/穿透/slew、±25终奖。
独立helper补充严格成功时的 `5*(1-T/55)` 完成效率项，失败为0；它对T单调，
**不是精确SPT奖励，也不保证与SPT的期望排名等价**。只有完成时间记录接通且经物理核验后
才可登记新reward variant并用于fresh replay；本轮没有改变现有trainer的运行目标。

### 独立指标工具

`code/mujoco_6d_vmc_benchmark/tools/training_comparison_metrics_20261025.py`：

- `contact_torque_summary`：从有时间权重的实际样本计算接触比例及全时域峰矩；
- `completion_bonus`：上述独立奖励效率项；尚未接入trainer；
- `summarize`/CLI：聚合完整登记矩阵，缺失/重复回合报错，不丢弃失败，不按方法各选T_ref；
- 输出写入新文件且附输入SHA；标记 `physical_evidence_verified=false`，不冒充物理独立审计。

输入schema为`sii-training-comparison-empirical-v1`，顶层包含`methods`、`case_ids`、
`horizon_s`、`torque_thresholds_nm`、`records`。case_id编码训练条件及配对评估seed/重复号；
每个method×case均必须有记录。记录字段见测试fixture，包含Task/Strict、full_horizon、
elapsed_s、completion_time_s及定义标识、machine_safety_violation、逐关节峰矩、共同阈值、
人接触和低于阈值的持续时间。现有rollout不会自动转换为该schema；需真实产物适配器。

本工具尚不计算物理P95、完成时刻或验证原始hash链；这些必须由物理日志适配/审计提供。
数值测试只使用明确标注的synthetic fixture，不是训练/仿真结果。

## 收敛与训练集比较规则

用户要求的“reward上升到趋平、loss正常”作为经验训练停止依据，不声称全局最优。
比较条件需要固定或按条件配对，不能把容易条件增多造成的reward上涨当学习改善。

- 初始预热与实际梯度更新分开，先保存未训练/初期学习的参考性能。
- 观察至少多个完整训练条件周期；32条件时每周期完整上限44,000 transitions。
  最近三个完整周期以及前期同条件窗口用于趋势判断，包含物理提前失败。
- 检查相对早期是否有实质提升、相邻周期均值与斜率是否进入登记容差、条件内方差是否稳定；
  不把第一回合开始就平坦的坏策略称为“学习后收敛”。具体数值容差在最终reward冻结后登记。
- SAC actor loss不要求趋零或单调；critic loss结合TD误差、Q值尺度、temperature、entropy、
  梯度/参数有限性和回报解释。PPO需另看KL、clip fraction及value诊断，不能同阈值硬比。
- 保存训练失败、异常、全部seed及完整曲线。最新授权取消百万步上限；按回合边界保存并
  持续检查学习改善和稳定性，不把百万步或阶段结束当自动收敛证明。异常时保留失败并诊断。
- 最终确定性评估在同一训练条件集合、相同初态/扰动seed上进行，单独记录评估曝光；与
  用户指定ESN的冻结checkpoint比较，不用探索期训练回报替代评估。结论仅适用于训练集。

## 接手时的本机依赖缺口及恢复路线

本机可见4张空闲RTX4090；实际进程CPU affinity为128，不把它当55核资源授权外扩。
原hdd工作盘约剩11GB，低于现有20GiB磁盘保护；同用户hdd2/ssd目录空间充足，可另登记run。
PID1是sh，`systemctl --user is-system-running`返回offline，现有systemd启动器不能照搬。
当前Python为`/root/miniconda3/bin/python`，未发现MuJoCo/Gymnasium/Torch/JAX/Flax/OmegaConf。
没有通过修改系统服务、显示配置或全局Python来绕过这些问题。

在当前checkout、/tmp、/root及同用户hdd2/ssd目录的已搜索文件中，未发现运行必需的
冻结MJB、当前PRIORS或指定ESN模型。文档旧归档`192.168.31.70:22`连接超时，本机无既有
`/root/.ssh`目录。没有索要凭据，也没有把Git中的旧条件文件冒充当前运行产物。

需要的实际输入：

- 历史`rl_tuned_20261015_v4`父目录：PROTOCOL、CONDITIONS、teacher.json；
- 其`parameter_fullrange`完整参数/adapter来源；
- runtime：冻结v6 MJB及参考rollout、menagerie、pinned learner与reward源码、版本记录；
- **用户所指当前ESN**的模型、配置、输入/输出合同、checkpoint/hash与训练条件来源。

MJB预期源SHA为`173e404bed4531cd193afc299f7c2243c276ce75797a169d8ea7c49d0bda8d11`；
正式dt模型SHA为`d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`。
这些是文档登记值，本机尚无对应二进制可重新核验。

用户已授权自主恢复Github源码中的任务。运行环境置于本机同用户SSD的`sii_rl`独立目录，
Python3.11/MuJoCo3.11.0/PyTorch2.8.0；模型资产取公开Menagerie且固定commit/完整文件hash。
新增prepare工具可从固定baseline SHA恢复参数源码，套用main现有单位/阻抗修复，复制
官方CHEQ实现并生成源码/依赖清单。新逐回合接口只插入actor与奖励遥测接点，保留原evaluator。
恢复工作不依赖用户再次授权训练；历史checkpoint缺失仍如实列为最终ESN比较缺口。
