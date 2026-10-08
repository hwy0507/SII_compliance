# 经典控制器与 RL：实现及比较充分性审计（2026-10-08）

## 结论

**存在需要处理的问题。当前经典/RL 的 0/24 是这些具体实现和 checkpoint 的真实结果，
不能直接作为“ESN 优于完善的经典控制或充分训练的 RL”的证据。**
已复现 VMC 物理读出与 action 解码的单位不一致；阻抗实现存在参考积分停滞及执行通道
差异；五个选定 RL 模型训练期间没有任何任务成功，且缺少优化器收敛诊断。
本轮没有发现足以判定导纳方程或官方 SimbaV2 核心更新公式写反的证据。

用户本轮要求审查，所以本轮只读取冻结源码、既有轨迹/训练记录并做数值探针。
没有修改任何控制器、模型、环境、gate、checkpoint，没有新机器人仿真或训练。
修正后性能可能提高，也可能超过 ESN，不能以维护 ESN 优势为验收条件。

## 审计对象与来源

- 开工实时核对 main `f135ac021aed4bb2af75d5d118a56d1a374cf555`、
  baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，按 sii-research-sync 核对
  两分支日志、AGENTS 和实际运行产物，未合并 baseline 分支。
- 实际评测主根（以下记作 R）：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/`。
  全 384 个回合及最终报告已完成；两个评测/报告服务均退出，不重启。
- `controllers.py` 的 Git 入口在 baseline 的
  `code/mujoco_6d_vmc_benchmark/experiments/parameter_rl_20261002/controllers.py`。
  实际使用副本保存在 `R/episodes/classical_vmc__office_v7_24_000/parameter_source/`；
  与 Git 及 RL adaptation 的副本 SHA256 相同：
  `a97cd0b142a97519f2ef55d5bc857f445e6140e1ea32df09609dd7aacb76aeb2`。
- 公共代码用 `R/source/`，核对执行收据中的源哈希。RL 身份从各回合
  `ADAPTED_RL_CHECKPOINT.json` 回溯实际 checkpoint、训练协议、三段 execution 和 replay，
  没有拿较早 primitive 模型替代本批 office adaptation。
- 正式结果 `R/report_final/REPORT.json` SHA256：
  `aa84f38750aeafabcf4d5e4586a2f379068b175ccc611535d3cf84d44b5a8203`。
  本轮不更改旧成功率、失败、原始指标或这些文件。

## 1. 已确认：VMC 物理读出归一化与环境解码不一致

代码位置：上述 `controllers.py:82–83,105`；
`scripts/run_vmc_6d_constrained_push_20260918.py:77,104`；
`scripts/vmc_teacher_stable_readout_20260930.py:39–42`。

ParameterController 构造 StableReadoutTeacher 时只传 K/D 和 velocity_weight，
随后更新 M/K/D/readout gain，没有传实际环境的 action units。
VMC 将虚拟物理速度读出除以 `[.16,.16,.20,.60,.60,.60]`；
实际 execution.json 的公共过滤器却乘以 `[.32,.32,.32,.60,.60,.60]`。

因此在没有饱和、没有变化率限制的探针中：

|平移轴|VMC 物理读出 m/s|过滤器解码 m/s|比例|
|---|---:|---:|---:|
|X|0.0062149354|0.0124298707|2.0|
|Y|0.0062149354|0.0124298707|2.0|
|Z|0.0027753587|0.0044405739|1.6|

三旋转轴比例为 1。探针使用实际类、实际执行配置，验证实际 ParameterController 的默认单位，
并核对公共源码 hash；这不是只观察轨迹后猜测。

影响范围至少包括固定 VMC 和 RL 调参 VMC。它改变了原本以物理量解释的柔顺读出及轴间比例，
且饱和/限速后不能简单用一个全局增益等价替换。即使旧搜索在该映射下调过参数，也不能
把当前实现直接解释成其声明的物理读出。该基类被 teacher 路径复用；后续修复必须检查所有
调用者/显式配置，不能假设这是只针对 baseline 的问题，也不能悄悄改历史 teacher 数据。

**已证实的是接口不一致，不是“它单独导致全部 0/24”。**
需要在独立开发条件做保持其它配置不变的单位修正消融，然后重新调参/训练相应 RL。

## 2. 已确认实现特征，因果仍待验证：阻抗参考受限与执行通道差异

代码位置：`controllers.py:84–99,116`；
`scripts/run_panel_impedance_reference_20260923.py:33,68–82,103–130`。

### 参考积分可能在边界冻结

MovingEquilibrium 把位置弹簧误差限制在 4 cm；接近边界时，按一个标量缩小整个参考增量。
这会同时抑制沿边界的切向运动。可复现的代数探针：机器人固定在原点、参考在 `[.04,0,0]`，
给 0.05 m/s 的 Y 向命令、积分 1 s，参考 Y 位移只有 `5.70e-10 m`。
这是限制器结构特征，不是一次物理机器人成功/失败试验。

第一预注册条件 `office_v7_24_000` 的真实轨迹提供相容证据：

|方法|末5秒弹簧误差达到4cm比例|末段名义速度 mm/s|末段实际速度 mm/s|末段目标位置误差 mm|
|---|---:|---:|---:|---:|
|固定阻抗|100%|56.908|0.411|26.126|
|RL 调阻抗|100%|29.399|0.955|12.925|

速度/目标误差是最后 125 个 actor 观测的中位数；弹簧比例来自低层 servo 记录。
它们不是全任务物理子步 RMSE，也不替换之前报告中的均值或另一定义的末段误差。
固定阻抗停在 lift；先前只读接触诊断在其末段未发现外部障碍接触，不能仅归咎于障碍太难。

实际模型物块仅 0.08 kg。模型七关节 frictionloss 为
`[1.137,1.137,1.137,1.137,.763,.44,.248] Nm`；固定阻抗末段 residual torque 中位数约
`[-.025,.699,-.020,1.175,.016,-.072,-.011] Nm`。
部分驱动力矩与干摩擦量级相比很小，值得核查带载跟踪、静差与积分上限。
这些数不能单独证明摩擦是唯一原因，更不能通过擅自删除摩擦来“修好”控制器。

### 共同执行约束不能笼统宣称完全相同

阻抗 torque closure **未读取**传入的 `joint_velocity_command`，而是重新取 nominal WBC twist，
经笛卡尔弹簧/阻尼和 `J.T @ wrench` 生成力矩。它继续使用公共力矩幅值/变化率限制，
但上游已经计算的关节速度/加速度命令限制不进入这条 torque 路径。
AST 读取检查已复现。原生力矩阻抗本身是合法方法；问题是之前不能仅凭公共 action filter
重放通过就声称它与速度残差策略具有完全相同的执行语义/速度保护。

参数阻抗的 action7 始终为零，真正控制量是参数变化后的力矩。这不是 RL 输出未接入，
但训练奖励使用的 `executed_action` 平滑成本对此方法恒为零，不能衡量其参数或力矩抖动。
该方法需要明确报告实际力矩/参数变化，并采用适合原生力矩通道的公共安全验收。

### 现有调参未建立最低功能验收

10月4日八条件开发确认中，两组阻抗共 16 回合均停在 lift；选定配置依据预登记的
strict/task/完整时长/穿透/RMSE/力矩排序。所有候选失败时，低穿透的停滞解仍可能排第一。
4cm 积分保护结构并不在搜索范围内，更多搜索同一受限结构未必能解决问题。
需先在独立无障碍带载运动、方向变化及受阻恢复中验收，再进入复杂任务排名。
详见 `RESEARCH72_CONTROLLER_CONFIRMATION_20261004.md`，旧失败全保留。

## 3. RL：不是没更新网络，但不能视作训练充分的强 baseline

本批五个选定模型均为 seed `2026100301`，从头做 office-v6 训练、未用 teacher 标签，
不是简单把早期 primitive RL 零样本搬过来。登记预算调整后的最终共同 checkpoint 档位为
49,500，不是早期计划中的80,000；直接 RL 因短回合及完整回合预算规则略少。

|方法|实际交互步|梯度更新次数|训练回合|训练 Task/Strict 成功|短回合|
|---|---:|---:|---:|---:|---:|
|RL 调 VMC|49,500|89,002|36|0 / 0|0|
|RL 调导纳|49,500|89,002|36|0 / 0|0|
|RL 调阻抗|49,500|89,002|36|0 / 0|0|
|RL 直接动作 metric|49,336|88,674|38|0 / 0|3|
|RL 直接动作 task|49,182|88,366|38|0 / 0|4|

回溯三段训练执行记录，确认回合身份不重复；步数和 reward_samples 相符，replay 条数和
terminal 数相符，短回合保留。虽然89k更新不算零训练，但36–38个长回合、零次任务成功
不足以证明复杂接触任务中的性能已达平台，更不能和有成功 teacher 数据的模仿学习混称
“训练条件完全一致”。在线交互、teacher 生成/筛选、示范样本、调参计算都应分开披露。

`tools/research72_train_rl_20261003.py:178–195` 的具体问题/边界：

- warmup 前5000步是小幅零均值高斯动作（std=.02），没有成功示范/课程；
  终端成功奖励同时要求 task 和 strict。零成功说明未获得这一奖励，不能断言该设计必然无解。
- `agent.update(...)` 返回的优化诊断被丢弃，训练日志仅保留奖励项和归一化等状态。
  缺少 actor/critic loss、Q、熵/温度等时间序列，无法据此判断收敛、Q失真或探索不足。
- 直接 RL 测试约93%–95%控制步触发动作变化率限制（上一轮轨迹诊断）。应检查请求与实际执行
  差异及学习难度；限速器本身是共同安全机制，不能为提高 RL 成功而移除。

已检查 pinned 官方 SimbaV2（`86899c277cdc697b2b02d827243de1ea93f20a1d`）的
`scale_rl/agents/simbaV2/simbaV2_update.py` 和 normalization wrapper，以及本仓库参数 adapter。
actor 的 `alpha*log_prob-Q`、critic 的终端处理、温度更新未发现明显符号错误；
raw action 入 replay、测试归一化冻结、episode 末 reward consume 的路径也未发现重复处理证据。
这只是有限源码审查，不是完整数学/梯度正确性证明。
已有120条测试回放通过证明模型执行可复现，**不证明训练充分或算法优劣**。

## 4. 导纳：暂未发现明确方程/单位错误

`scripts/run_panel_admittance_reference_20260923.py:41–71` 从实际 env 获取动作单位，
基于本体估计关节负载/雅可比求 wrench，以 M-D-K 状态积分和偏移 WBC 产生残差。
本轮未发现类似 VMC 的单位不一致，未确认符号反向。

实际 office 路径用 `ScaledReferenceWBC`（继承 FixedBasePandaWBC），
在 `scripts/run_contact_transfer_20260916.py` 中替换了构造时的 WBC。
参数导纳记录为 `original BO controller reference mapping`，没有进入
`hasattr(env.fixed_wbc,'waypoints')` 的旧 joint-waypoint 分支。
不能仅看初始构造中的 PaperMPC 字样就把旧分支问题误判为当前 office 失败原因。
导纳的搜索范围、持续受阻时的恢复能力仍需开发验证；当前0/24不代表算法普遍上限。

## 对旧表和下一步的处理

旧384回合表继续作为冻结实现的完整结果，所有失败、低分和指标不删除；标题/说明增加本审计链接。
目前可以说“在同一场景和 gate 下，这些冻结模型取得这些分数”，
不能说“全部方法已充分实现/优化，因此ESN全面优于经典控制与RL”。

建议顺序（本轮未执行修复或重训）：

1. 统一 VMC 物理读出/action 单位，做方向、尺度、零负载及饱和单元验收；检查共享 teacher 调用。
2. 阻抗先通过无障碍带载跟踪、4cm边界切向转向、受阻后恢复验收，明确原生力矩安全语义，
   补齐真实执行量平滑统计。用独立开发身份检验每个改动，不能保证改后一定完成复杂任务。
3. RL 在修复后的接口上登记合理交互/调参预算、多seed、成功曝光策略和全部优化诊断。
   若加入 teacher/BC 或课程，另列该方法及信息/预算，不能伪装成原纯RL。
4. 开发验证完成后冻结新版本，再做全方法一致的独立新条件比较。当前24条件已看过，
   对它们做修复回归可以，但不再称为新一轮完全未见的泛化证据。

## 复现证据及归档

新增审计源码：`tools/audit_baseline_implementation_20261008.py`。
本地代数探针：Python3.11.15/NumPy2.4.6，1线程、2GiB虚拟内存上限。
服务器证据读取：Python3.12.3/NumPy2.2.6，systemd单线程、MemoryMax1GiB、MemorySwapMax0；
仅加载记录和 MJB 参数，未调用物理 step 或梯度更新。

已核验归档主根（以下记作 A）：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/baseline_implementation_audit_20261008/`。

|文件|SHA256|
|---|---|
|`A/v2/audit_baseline_implementation_20261008.py`|`555d94a89c9a3a110411197b75b4f1826fd7303260cd659f3ff00ddc318f33cc`|
|`A/v2/IMPLEMENTATION_AUDIT_V2.json`|`39ec3c982408ec9c3e6c9410c244f7986497094c8e59234cb4031093f84c6d65`|
|`A/v2/LOCAL_CONTRACT_PROBES_V2.json`|`5c43a72054979e84993fb1bc6b241d225633359775b89f7f3c050d8c3fa9abc3`|

V1保留，V2补充实际 execution 配置断言、源码匹配及统计口径，不修改原始结果。
Git 小型证据在 `outputs/baseline_implementation_audit_20261008/` 的两个 V2 JSON。
重放命令（输出须用不存在的新路径）：

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
/home/arm1/vmc_mujoco_runtime/reward_study_20260930/venv_gpu/bin/python \
/home/arm1/sii_shared/SII_compliance/runs/main/baseline_implementation_audit_20261008/v2/audit_baseline_implementation_20261008.py \
--root /home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008 \
--source-root /home/arm1/sii_shared/SII_compliance/runs/main/office_v7_uniform24_20261008/source \
--output /tmp/sii_baseline_implementation_audit_new.json
```

已完成：源码身份核对、两项数值复现、阻抗首条件轨迹核查、五模型训练链核查、审计归档。
运行中：无本轮训练/仿真。
未完成：修正后控制器验证、因果闭环消融、RL收敛验证及新的公平性能矩阵。
