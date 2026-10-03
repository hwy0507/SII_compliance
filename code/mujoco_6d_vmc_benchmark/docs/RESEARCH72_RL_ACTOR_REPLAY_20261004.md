# 独立冻结RL动作回放入口

准备时间2026-10-03 23:47UTC（本地10月4日）。仅工程检查，真实新RL训练/最终回放尚未完成。

物理执行内的RL worker已经回放raw actor并检查归一化；新的独立进程重新从checkpoint加载官方SimbaV2，
对归档canonical48逐步重算5D/7D原始输出，与 `baseline_policy.npz` 逐值比较，同时验证该文件观测/公共请求
与 `rollout.npz` 相同。直接RL额外要求raw action与公共请求相同；调参RL保留不同的动作语义。
前后核对normalizer、计数器和完整checkpoint文件hash，检查参数/agent实际源码与训练记录一致。

每个模型单独用 `tools/research72_rl_actor_replay_20261004.py`，输入其 `--checkpoint-manifest`、
`--parameter-source`、全部完成评估路径 `--runs` 和新的 `--output`；1线程、MemoryMax3GiB。
不做物理积分、更新、模型选择或读取场景manifest。完整失败和已完成的短回合都必须包括。
这是actor来源检查；参数控制律的内部状态、伺服动作和物理子步仍由原独立审计覆盖，不能把本入口说成完整仿真重跑。

最终报告通过 `--rl-actor-replay` 接收这些收据，逐模型锁、轨迹和文件hash关联，报告独立回放覆盖数。
缺少回放时标记incomplete，同时保留已审计的物理成功/失败，绝不从成功率分母删去。
缺失物理回合仍遵循原缺失上下界；回放覆盖不能替代912回合计划完成情况。
历史初始264报告无新RL，不改写历史报告或运行中的快照。

本机单线程3GiB下14项合成检查通过（4回放＋10报告）：5D/7D、错误动作/形状、输入或归一化原位变更、
短失败保留、文件篡改、真实收据结构对接和缺失回放不删结果。测试没有加载真实新RL权重，不能称真实RL审计通过。
真实动作来源检查待训练/冻结评估完成执行，最终38模型/24条件尚未开封。

5文件源码overlay已在服务器逐hash核验，共52,258字节：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_actor_replay_engineering_v1/evidence/`。
它不是独立完整runtime；最终使用包含依赖的完整Git提交源码快照，并在模型锁中冻结。

| 证据 | SHA256 |
|---|---|
| 独立RL actor回放源 | `40cb2fe3bb3c0449cbca0711f542c18d2825da78d41fa9d57cd5491af449918a` |
| 最终汇总器源 | `88bfcc0684c9c156b1d9e1adf7e39e83ef490b2c8365a600dbba08bc70917155` |
| 归档manifest | `f4db3b3e57967170bcc97f12419e5546eda59817b61c176f87a9fda52d816472` |
| 传输tar | `a6a4251a6ffe93842e9074d1cf070bfbca237c63771f007b80620d23423a261d` |

输入源核对同时确认RL actor只接收canonical48；阶段potential和接触子步指标单独用于奖励，不拼接到actor。
调参RL输出维度导纳7/阻抗5/VMC7，阻抗的7D公共请求为零、参数作用于底层力矩律。
此源码核对不能替代真实传感器、硬件安全或充分收敛证据；不增加学习预算或改变动作范围。
