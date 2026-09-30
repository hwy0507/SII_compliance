# Standard SAC 两分支六fixture部署预声明

固定部署 `online_only` 与 `demo_prefill`，训练seed均为20260923，各自使用 final8192/8092 与自身仅在线训练得到的冻结 VecNormalize，动作48→7。后者额外600条 train-only demo、不作离线更新。不得选周期checkpoint、改reward、调预算、改seed或遇失败自动重试。不称RLPD、顶会方法完整复现或等计算量比较。

## 固定13条执行与对照复用

12条 learned 是两策略各自原9400–9405六fixture，沿旧VMC fixture原命令/环境/资产/MJB/24s/50µs measurement/WBC/任务门执行。独立 `FrozenSACActor` 原样保留 rawfloat64 canonical48→float32→own frozen observation normalizer→SAC deterministic predict→动作Box→原 `PairedExecutionPolicy` direct7。所有姿态、速度、执行器和安全路径仍由原panel运行链实现，不能把推理回放当物理部署。

第13条是唯一额外 direct7 `zero7/9400` parity：固定原zero7执行入口、source、fixture options和动作7维全零，不运行actor，不调用zero6解析VMC。与旧zero7/9400的全部原始rollout、物理状态/接触轨迹和50µs raw逐字段dtype/数值exact、完整MJB、50µs摘要、动力学JSON对齐，仅容许原set型contact字段排序与输出路径差异。通过后复用旧zero7/9400–9405六条，不重复计算成新增性能样本。任一parity失败立即停止新增launch，保留原失败。

通过parity后先执行两branch的9400，二者执行/来源/有限性检查通过后再执行其余10条。任务失败、原0.2mm gate失败、真实安全早停都是结果，继续计入各branch分母6；进程错误、来源漂移、错配或非有限数据阻止新launch，已经开始的peer保留。旧direct7 zero7六条作为动作学习收益主对照；旧nominal仅作旧报告背景，不消耗本轮parity，不能混淆zero7与训练nominal VMC。

## 开跑准入

两训练必须COMPLETE且无FAILED，真实最终zip seed20260923/8192/8092，各actor/critic/entropy8092真实optimizer steps；完整原始8192 Gym/reward/replay slot/sample统计审计、四项最终train/validation×zero/SAC评估均保留。两actual initial policy/alpha/RMS必须匹配预检和彼此；前100 warmup及step101首次更新前transition exact证据必须通过。train/validation零策略须与原seed23 direct7 zero完整600帧raw/MJB精确相等。

同DGX CUDA用新SAC部署adapter对原final eval观测逐帧回放，独立原evaluate表达式与adapter request/execution exact，并核reset后重放和RMS冻结。train/validation实际短episode保留；仅当其真实安全终止时，使用训练argv预绑定的原direct7零proof600观测补充完整600 policy-input replay。核原proof base protocol、source subset、fixture、runtime、nominal、资产、proof文件hash与MJB；不可自由选择好轨迹或推造短episode后续物理。

prepare重新核所有准入报告与原始输入hash、旧报告/归档和原六fixture命令。运行源码从readonly SAC训练201文件快照复制，并仅增加已审阅部署文件；不改在训snapshot。构建新readonly部署快照与独立PLAN，root审阅具体hash/命令/资源并明确launch后才能执行额外物理。旧18条背景报告固定SHA `c417038bcc43c79ed52925cb942a7993b2eeb56595a9b731f92167adaf44b011`；匹配zero7六条及其旧审计报告另以原hash绑定，并完整绑定raw输入后复用。

早期草案曾误写nominal zero6 parity，root在任何新增物理启动前明确覆盖为本版zero7协议。`canonical48_sac_replay_source_20260925_r1`里的旧草案仅伴随learned adapter无物理回放，不是最终13job部署协议；最终快照必须采用本版并绑定其hash。

原25job部署结束后最多2个新worker，各单计算线程；全服物理worker总数不超过4。每job固定1800s timeout。禁止覆盖输出、改旧结果或干预其他进程；记录实际PID、命令、开始/结束、exit及所有失败。

## 报告约定

新增12条完整读取50µs raw重算当前状态机waypoint 3D位置RMSE、实际qfrc_actuator关节峰矩、末端线速度峰，原task/panel/strict门不改。每branch按六fixture报告所有值与均值、task/strict率、阶段、触杆时长、抬升和失败，不以低RMSE独立宣称成功；共同目标 `[0.54,0,0.785]m` 末帧距离与绝对(18,24]s末6秒150帧RMSE分列，真实短回合后者留空。

仅单个SAC训练seed，不提供训练seed标准差，不与三seed PPO的方差混称。demo-prefill在线预算8192、总数据8792明确区分；额外demo与梯度/网络预算差异公开。旧ESN/MLP/经典结果和PPO报告复用hash绑定的已审计结果，不能声称本轮重算了它们全部raw。13条包含12个新性能结果和1个parity，不改变旧六fixture分母。
