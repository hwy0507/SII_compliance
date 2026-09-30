# 配对PPO固定训练seed复验协议

本协议在新增训练前写入。目的为检验单次初始化和采样的影响，不依据六条件验证选择算法、奖励、参数或checkpoint。已有seed20260923及其全部失败保持原样。新增固定seed20260924、20260925，每个seed都运行parameter6和direct7，不能只扩展表现较好的分支。四个新增run均固定8192真实互动步，全部使用最终模型；总共三训练seed/每分支，但仍只在同一个训练fixture上学习，不称多场景训练。

两分支沿用`RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md`中的全部学习参数：PPO MLP[128,128]、lr3e-4、rollout64、batch64、epochs3、gamma.995、GAE.95、log_std=-2；canonical48 actor/critic，无特权输入；potential_v1奖励不变。parameter6继续用完整训练nominal options、固定K范围和限速、解析状态；direct7继续用原action7。归一化各自只由本run在线训练拟合，评估冻结，不继承之前模型/normalizer。

## 原证明复用和新增入口边界

新增独立入口只参数化训练seed并编排同样的训练和评估。原训练snapshot中163份Python、134份模型资产、旧协议、fixture和运行时逐项保持相同字节/数值。不能修改旧源、原proof或现有快照。复用原两模式完整600步zero证明，但每次启动必须核原proof COMPLETE/PARITY哈希、proof manifest中全部原源是当前执行源子集、资产/runtime/device/fixture/训练名义参数相同。新增入口和本协议另存hash，不能声称整个新源清单与旧proof完全相同。

原完整proof已证明zero控制不依赖训练seed；每个新增run仍执行train/zero及validation/zero并留原轨迹，完成后须按旧冻结比较器核对对应原zero/MJB。训练seed不改变manifest内物理seed800，不增加/改变物理扰动条件。

## 执行、资源与审计

只在DGX运行，每run一个MuJoCo环境、1CPU线程、CUDA与既有paired run相同；进程RSS保护7GiB及系统余量至少2.5GiB保持原实现，每run7200s超时。四项不要求同时启动；先核全服正在执行的命令，整个服务器最多4仿真worker。既有18条部署优先，不中断、不重启稳定进程；新增复验初始最多2worker。所有新输出必须不存在，先冻结源码及预声明四run列表，再启动。

完整记录8192真实transition、Gym float64与SB3 float32奖励、原始观测/末next、参数/动作与终态掩码；2048间隔checkpoint只是留存，永不替代final。最终四项评估固定train/validation × zero/PPO，保留失败和安全短回合；新增run与原seed都纳入结果。执行错误单列，不填零、不把自动重试当新的随机seed。

每个run均须独立8192日志/源/model/资产审计、zero一致性与固定最终模型部署回放后，才能补六条件子步比较。18条初始矩阵与后续多seed矩阵分开归档；不能把六fixture当六独立训练seed。若报告统计，先按每个训练seed聚合六fixture，再描述三训练seed的分布，不把18个相关回合当作18独立训练重复。

新增8192步复验不保证RL充分收敛，也不解决单训练fixture覆盖不足；它回答的是现有固定小预算配方在初始化/采样改变后是否稳定。SAC/RLPD是另一条未完成的算法工作，不以本复验替代。当前只准备执行入口，实际启动及完成状态以持续记录、run manifest和COMPLETE为准。
