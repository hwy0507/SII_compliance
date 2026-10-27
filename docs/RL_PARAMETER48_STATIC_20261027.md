# 参数48扩容静态衔接准备（2026-10-27，Goal active）

最新完整训练结果仍见 [46/28交接](RL_PARAMETER46_SERL28_20261027.md)：参数45与Direct27完整审查通过，原参数43–45未稳定，Direct仍Task0，不宣称健康收敛。本轮推进48准备，原四训练46/28和冻结41继续，无重启或重复训练。

共享SSD B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；源码B/repository/SII_compliance。开工及本轮实际查询远端main0869a04513ae0e586d2b30fd24f1f41d64526811、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，原fetch已完成并读取两日志，无新环境/物理/算法更改。沿用sii-research-sync，无子agent。

## 本轮完成

独立准备目录 `B/runs/parameter48_static_preparation_20261027_v1`，10个运行源码（prepare.py、launch.py、setup_monitors.py、5审查模板、2冻结候选源码）。还没有正式48的run/runtime、waiter或learner；准确47父尚未产生，不执行提前恢复或物理。

- prepare只接准确完整47，验证父review/health、父learner已退出，复制原47不可变runtime并增加两个冻结候选。完整保留原entry23和2m历史marker；新followup固定parent47、4m、实际entry checkpoint/hash/replay digest，绑定既有真实44与异常state准备证据。check-only并行使用已释放13/26/39 CPU、共同900秒时限，超时清理其原子进程，不启动物理或优化。
- dependency_hashes保留原46/47全部键和值，恰新增 `parameter_replay_capacity4m_20261027.py`、`resume_cheq_capacity4m_pool30_20261027.py`；符合已登记46–48固定窗口。候选源码hash与原通过报告一致，没有重跑原4m gate。
- startup/fullreview明确父2m、新4m、双marker、历史entry23及实际47 digest；全旧行保留、reward/动作/optimizer/模型/时钟审查保持。完整review新增 `replay_capacity_followup`、`current_replay_capacity`、实际是否跨2m及超出行数，不假定一定全55秒或一定跨界。两health源码逐字节一致，奖励/映射数值段除周期路径外一致。
- 手动launcher需要CHECK_ONLY与独立PRELAUNCH通过；launcher/setup在任何新派发前校验冻结源码清单。不会自动启动48或修改现有训练。
- AST、准确47→48标签/路径/CPU、两候选hash、三方法原46依赖与审查数值段核对通过。首次静态比较未先规范化startup的cycle_00046→cycle_00048路径而失败；保存INITIAL_STATIC_FAILURE及原检查器，确认差异只有这一周期路径，修正比较后通过。未绕过实际训练守卫。

以上是静态衔接验证，不是准确47全learner恢复、正式48启动或真实200万边界证明。初始生成和检查器是取证记录，不是幂等重跑入口；运行只能使用独立prepare/launch/setup以及SOURCE_MANIFEST中的10个文件。

## 原进程实况

采集UTC 2026-10-27 11:04:40，/proc命令/start_ticks与PROGRESS已核验，完整记录见小证据LIVE_STATUS。冻结列的步数为当前条件actions，非总训练步数。

|运行 / 方法|原PID|当前步数|完整条件|
|---|---:|---:|---:|
|serl_take_cycle28_20261027_v1 / direct|1978250|1132467|0/30|
|parameter_capacity_pool30_cycle46_20261026_v1 / impedance|1829718|1919669|0/30|
|parameter_capacity_pool30_cycle46_20261026_v1 / admittance|1829722|1919873|0/30|
|parameter_capacity_pool30_cycle46_20261026_v1 / vmc|1829726|1921265|0/30|
|parameter41_frozen_full30_20261027_v1 / impedance|316550|200|22/30|
|parameter41_frozen_full30_20261027_v1 / admittance|316551|1300|21/30|
|parameter41_frozen_full30_20261027_v1 / vmc|316552|200|22/30|

47准备1858092、Direct29准备2044155仍仅等待完整父审查后check-only；固定Direct27–29统计336744、参数46–48统计1908379继续。没有重复新建这些作业。

四卡瞬时利用率有低点，不能把单次71/86/0/82或64/0/83/94读数写成稳定≥50%。既有take27固定窗口证据保持，不重复测量或生成GPU假负载。当前四正式都在持续增加步数。

## 下一步与恢复

1. 完整46审查/health后检查实际47恢复和PRELAUNCH，及时接47；保留现有有限准备进程。Direct28同理接现有29准备入口。
2. 实际47启动后再登记48的有界准备等待；准确47完成退出后运行本目录prepare.py，检查全state/RNG/next65536恢复与科学PRELAUNCH，才可运行launch.py。
3. 48需实际startup、真实2m边界保留/采样与reward独立审查、完整review/health；本轮未执行。原46–48与Direct27–29固定统计待完整终点，不选结果重定窗口。
4. 原冻结41继续至90回合完成再独立审查，不重跑已完成冻结32/Direct16。全部reward稳定、loss健康、冻结评测和最终比较未完成，Goal保持active。

小证据：`docs/evidence/RL_PARAMETER48_STATIC_20261027`，21文件逐hash/AST核验。共享SSD小包与提交收据另记。大checkpoint/raw/runtime仍原SSD；HDD配额满，仅更新已有LATEST指针，非HDD或arm1全备份。
