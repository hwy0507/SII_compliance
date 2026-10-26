# Direct RL 改用 SERL：论文选择与下次开机交接

日期：2026-10-26。状态：**文献核验与迁移决策；训练、仿真、测试、服务均未启动。原 Goal 继续 paused。**

## 后续澄清：Direct 默认从零训练，零示范

用户随后说明不想再采数据，并询问能否从零训练。静态核验确认 SERL 论文第4.1节明确支持 from scratch，官方 `examples/async_sac_state_sim/async_sac_state_sim.py` 不使用 demo buffer：随机动作采集初始经验、在线 replay 达到启动量后更新 actor/critic。故迁移默认路线为 **SERL-state/SAC from scratch adaptation**：随机初始化、空 replay，仅自主在线交互，不加载已有示范、不加载旧 CHEQ 权重或 replay、不新增人工纠正。本文较早的已有示范方案是历史备选，不再是启动前置条件；若未来改用示范，须另行明确并保留零示范结果。

这保留 SERL 支持的状态输入学习路线，但不包含 RLPD 的先验/在线对半采样，因为当前没有先验数据。不能声称复现了原论文“20条示范”的高成功率结果，也不能保证长时域本项目仅靠稀疏终端成功奖励即可学会。恢复后 reward 适配可保留任务进度引导，终端严格使用原 gate；不得用降低力矩但停滞的平坦 reward 判收敛。采用已有任务/安全反馈不等同增加 actor 的 privileged input。与使用示范的 ESN 比较时，需要分别报告示范量和在线交互量，不宣称两者训练数据预算相等。

## 用户最新约束与路线

- 在线调参的 Impedance / Admittance / VMC 允许继续 CHEQ。
- Direct 不再以 CHEQ 为后续主基线，改为顶会/顶刊已验证的机械臂接触控制方法适配。
- 用户先明确“仅接受已有示范，不新增人工纠正”，随后要求优先从零训练、避免采数据；以顶部零示范路线为当前默认。不得启动人工接管或额外示范采集。
- 本轮选定参考：**SERL: A Software Suite for Sample-Efficient Robotic Reinforcement Learning**，ICRA 2024，pp. 16961–16969，DOI `10.1109/ICRA57147.2024.10610040`。
- 这是 2024 年论文，不是 2025–2026 年论文；选择理由是其训练机制更符合上述数据约束。2025 年顶刊后继 HIL-SERL 需要另行区分，不能借用后继的发表信息给 SERL 标注顶刊。

## 已核实来源

1. 正式发表：[IEEE DOI](https://doi.org/10.1109/ICRA57147.2024.10610040)。Crossref 与作者项目页均确认 ICRA 2024。
2. [论文全文](https://arxiv.org/html/2401.16013)、[作者项目页](https://serl-robot.github.io/)。本轮阅读公开 arXiv v4（2025-03-20）；后续实现应区分版本，不把 v4 日期当成会议年份。
3. [官方代码](https://github.com/rail-berkeley/serl)，本轮读取 main SHA `1fa2af7496be042e43d36120a7c8d1b71f1bfb59`。这是当前读取源码的固定引用，不声称是会议发表时的原始版本。
4. 官方 README 已标记仓库正在弃用、推荐 HIL-SERL，并推荐可选在线 intervention；这不等于本任务授权在线纠正。必须显式禁用这条路径，保留仅已有示范协议。
5. 后继 [HIL-SERL](https://doi.org/10.1126/scirobotics.ads5033)：*Precise and dexterous robotic manipulation via human-in-the-loop reinforcement learning*，Science Robotics 10(105)，2025-08-20。其在线纠正是重要组成部分，本轮不把删去纠正的版本冒称忠实 HIL-SERL。

## 原论文真正完成了什么

- 真实机械臂 PCB 插入、线缆卡入、物体搬运；每项用 20 条初始遥操作示范，再自主进行在线 RL。物体搬运包含 forward/backward 两个策略。
- 论文第 5 节报告三项任务各 100 次评测中成功率 100%。这是作者任务与测试条件下的结果，不是本项目的结果，不证明人机舒适性或本项目 Strict gate。
- 核心是 RLPD（SAC 系 off-policy actor–critic），含先验数据与在线 replay 的对半采样、高更新/数据比、LayerNorm、target critic 和熵正则。
- RL 输出运动目标，由下层实时控制器执行；接触任务的下层为带 reference limiting 的阻抗控制器。这里的 Direct 指学习动作目标，**不是直接输出全部关节力矩，也不是学习刚度参数**。
- 原论文强调控制器实现对接触任务的重要性：限制参考与实际末端姿态间的偏差，防止目标持续顶入障碍引起过大作用力。不能删除该贡献却声称全部原系统复现。

## 只读代码核验

固定 SHA 下的 `serl_launcher/serl_launcher/utils/launcher.py::make_sac_agent` 支持纯状态输入；配置包括 256×256 actor/critic、LayerNorm、10 critic、target 随机子采样 2、`backup_entropy=False`，并使用可调 temperature。不能简单套用另一版 SAC 的含熵 TD target 并称原实现。

`examples/async_pcb_insert_drq/async_drq_randomized.py::learner` 分别从 demo 与在线 replay 采样半批，再拼接；包含多次 critic 更新配一次 actor 更新。`examples/async_sac_state_sim/async_sac_state_sim.py` 是状态输入的仿真示例。本轮只读这些文件，未执行任何示例或安装 SERL 依赖。

以上是来源证据，不是已经冻结的本项目超参数或训练预算。

## GPU 利用率目标（用户 2026-10-26 补充）

用户要求：**恢复正式训练后，GPU 利用率最好不要低于 50%，尽量充分利用已分配算力。** 这是资源效率目标，不是收敛或任务成功判据，也不是当前恢复计算的指令。

- 对参与训练的每张 GPU 记录利用率，优先看稳定训练阶段的连续 60 秒窗口均值，同时记录整体均值；区分启动、回合/周期收尾、评估和保存 checkpoint 的短暂低谷。
- 若持续低于 50%，优先排查 CPU/MuJoCo 采样、经验传输、同步等待和 learner 更新瓶颈，在已登记预算内优化并发、批处理与数据管线。改变 batch size、UTD 等学习设置时另行记录，不能仅为提高占用而静默改变算法。
- 正式训练和有研究用途的辅助任务分别报告；混合占用达到 50% 不等于正式训练达到 50%。不重复已完成任务或无界追加计算来制造占用；未达目标时如实记录实测值和瓶颈。
- 当前 Goal 仍 paused。以上要求在用户明确恢复后执行，本次不启动训练、仿真、测试、服务或辅助 GPU 任务。

## 下次恢复后的适配范围

1. **当前从空 replay 开始，不等待示范。**以下仅为将来明确启用已有数据时的审计要求：核对训练身份、机器人/physics、dt、观测与动作定义、时间顺序、next observation、termination/truncation 和 reward 可重算字段。仅有 `(observation, teacher_action)` 的行为克隆样本不自动等同 RL transition；动作若不是实际执行动作，不能搭配该轨迹的 next observation 冒充 transition。不得读取验证/未见条件充当先验经验；不得静默补采示范。
2. 使用 SERL 状态输入的 SAC 系学习机制，当前所有批次来自自主在线 replay，无示范对半采样，无在线人工纠正；不让 CHEQ 名义策略混合继续充当新的 Direct 输出层。
3. 优先使用现有 canonical48 的部署可得信息与公共执行动作接口。旧 CHEQ actor 的额外 mixing context 不属于 SERL 原接口；其移除、旧 critic 时钟是否保留、normalizer 与动作头均须在独立适配协议中说明，**本轮未修改**。
4. 原论文视觉输入换成本项目本体状态，是明确的 observation adaptation；代码存在 state-only 路径支持这种实现，但不能称视觉原系统逐项复现。
5. 公共 physics/MJB、Task/Strict gate、filter、执行器限制和 dt 保持冻结。SERL 的原生阻抗 reference limiting 与本项目执行层不自动等价；恢复后先写接口映射与差异表。如必须改底层合同，应先明确变更，不静默替换。新版本宜称 **SERL/RLPD-based Direct adaptation**。
6. 任务 reward 改为本项目成功、时间效率、力矩/接触合规的已登记目标；真实 gate 可用于 reward/evaluation，不因此加入 actor。奖励与最终指标分开。正式评价继续 Task/Strict、统一 `SPT_empirical`、峰值广义力矩、实际人接触期间阈下比例和机器违规率；无接触为 NA，失败保留分母。沿用用户对共同事后 T_ref 的最新授权并披露其事后性质。
7. 独立新 Direct run、训练初始化与配置，不把 CHEQ actor/critic/optimizer 状态直接当成 SERL 的继续训练。旧 Direct 的全部 checkpoint/replay/诊断保留；旧 replay 只有通过动作、奖励、转移和数据许可审计后才可能作为独立登记的先验数据，不能默默导入。
8. 三类参数 CHEQ 保留已有学习状态，按关机交接审查部分 cycle、optimizer/replay/RNG 恢复。新 Direct 的算法切换不构成参数路线清零重训的理由。
9. 与 ESN 对齐可用部署信息、动作权限、任务条件、先验数据身份与选择规则；明确 RL 额外在线交互量。该比较是不同学习/控制方案比较，不能把差异全部归因于“直接动作与调参”或“ESN 网络结构”。
10. 收敛证据需要 reward 从学习改善进入稳定区、优化诊断及独立冻结策略任务成功验证。平坦失败 reward 或数值较小的 critic loss 均不足以宣布完成。

尚未确认：最终比较的 ESN checkpoint、公共执行层与论文控制器之间的适配细节、训练预算及资源计划。已有示范清单不是当前零示范路线的前置条件。当前不设新步数、不选新 checkpoint、不运行预检；待用户开机明确恢复后处理。

## 仓库与备份状态

工作副本 `/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/SII_compliance`。本轮同步读取远端 main `c1175326a607159cfa4966560ef9b4119909a326`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。main 新变化是另一主机的非 RL 新30条拟合与验证动作重放；不代表本集群 RL 恢复，也不能冒充已指定最终 ESN。

本地原 HEAD `16351ad9adc2beef8201ec4cd007f8f6b11cd15f` 含未发布的历史工作。此次仅修改文档，不合并远端源码或改冻结运行时。正常 push 若受认证/分支分叉阻止，应明确保留本地提交和独立 HDD 文档副本，不 force push、不索要凭据。

## 给下次会话的提示词

> 请继续原柔顺控制 RL Goal。先读取 AGENTS.md、docs/RL_SHUTDOWN_RECOVERY_20261026.md 以及 docs/RL_DIRECT_SERL_SELECTION_20261026.md。本次最新路线是：Impedance/Admittance/VMC 在线调参继续 CHEQ；Direct 改用 SERL（ICRA 2024）支持的纯状态 SAC 从零训练路线，不再以 CHEQ 为主方案。随机初始化、空 replay、零示范，不加载旧 CHEQ 权重或 replay，不新增人工纠正或示范采集。保留全部旧 checkpoint 和失败证据，不把旧 CHEQ 权重冒称 SERL。先核验零示范启动、接口映射与公平性，再登记新 Direct 适配阶段；参数 CHEQ 按原学习状态与部分 cycle 语义恢复。正式训练期间GPU利用率尽量不低于50%，按各卡稳定窗口监测并区分正式/辅助占用。最终按相同条件比较 ESN，报告 Task/Strict、SPT_empirical、峰矩、接触期阈下比例和机器违规。除非我在新消息中明确要求恢复计算，Goal 保持 paused，禁止训练、仿真、测试与辅助 GPU 占用任务。
