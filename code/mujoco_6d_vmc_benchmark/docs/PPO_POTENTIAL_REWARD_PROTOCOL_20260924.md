# PPO潜势奖励变体：运行前冻结协议

日期2026-09-24。依据仅来自PPO8192原训练集的奖励审计：唯一task成功回合的折扣return在13个完整训练回合中排最后。此实验检验更直接对齐验收的训练目标是否改善学习，不把旧失败模型替换成有利结果，不据940x或front验证成绩调系数。

## 唯一实验变化与数学边界

保留48D actor/critic输入、action7、原场景/动力学/任务/安全链，PPO优化器参数、seed20260923、8192互动步数、从零初始化、最后checkpoint选择、原train rod/validation front不变。改变奖励目标：取消旧逐步位置/转角/估计力/动作/动作差惩罚和固定阶段+0.5，改为以下有限时域目标及潜势差。

基础奖励：仅终端开发gate通过给+5，invalid physics或upstream contact给−5，其余0。开发gate保持已有RL评估定义：task成功、正确focus接触、无invalid/upstream、所有外部穿透≤0.2mm；front无rod，不误套rod释放门。它不等于office gate，也不是三维指标最优的奖励函数。

潜势：`Φ=(stage−min(||position_error||/0.30,1))/3`，仅适用原4阶段push，所有终端状态Φ=0。奖励 `r=base+0.995*Φ(next)−Φ(current)`；阶段和终端标签仅供reward，未加入actor/value输入。

对任意完整回合，折扣潜势项之和恒等于`−Φ(initial)`。因此在固定初态、固定600步终点下，额外的阶段切换/等待不能凭潜势奖励改变成功与失败的基础回报排序。它保持的是上述新稀疏目标的理论排序，**并不保持旧密集reward的目标**，更不保证PPO优化、有限样本或神经网络能学好。64步rollout仍可bootstrap，终端没有bootstrap。预算中断partial不伪装成终端成功或失败。

0.30m位置尺度只是固定归一化覆盖当前抬升距离，未扫描；gamma仍.995。本轮不再更改奖励系数。对相同完整600步轨迹，gate通过的基础折扣优势为`5*.995^599≈.2483`；这个信用分配难点仍在，不声称已解决全部长时域问题。

## 代码与验证

- 独立模块 `scripts/canonical48_potential_reward_20260924.py`，没有改原bridge/runner或已冻结源码。
- 独立入口 `tools/run_canonical48_potential_ppo_20260924.py`，复用原工作流并只替换Gym reward、对应manifest描述。
- 11项测试验证多种时长/成功失败的潜势望远镜恒等式、终端无需private final obs、非法stage及提前标签拒绝。
- 原工作流运行前执行6.4s direct-zero/Gym-zero的27数组一致性检查，需通过后才训练。它验证控制行为不变，不验证奖励目标相同。
- 所有源码复制入新的只读snapshot；本机单MuJoCo环境、线程1、affinity2核、RSS≤7GiB/系统可用≥2.5GiB保护、GPU15%、45分钟timeout。每2048步保存更新后checkpoint，最终选择固定8192步模型。

完整评估为同train/validation各zero和冻结PPO一条24s，保留失败。运行结束再与旧8192按task、gate、轨迹误差和物理指标对照；本机不同版本可以配对，但本机数值不拼DGX基线表。后续若部署DGX必须重复最终模型推理parity和同MJB核验。

## 状态

协议在启动前写入。计划输出 `outputs/canonical48_ppo_potential_8192_20260924_r1`，源码 `outputs/canonical48_ppo_potential_source_20260924_r1`。实际启动、PID与状态以持续入口及该目录progress/COMPLETE/FAILED为准。未运行完成前不声称reward修正改善了任务。
