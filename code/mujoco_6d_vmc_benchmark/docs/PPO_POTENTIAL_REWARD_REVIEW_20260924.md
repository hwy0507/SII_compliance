# Potential PPO终止语义与可复算性只读审查

结论：在已经冻结的24s有限任务定义下，未发现需要中断运行的terminated/truncated或terminal potential实现错误。当前源码和已完成训练序列支持势函数折扣恒等式；不能据此证明PPO已改善任务。检查期间未改运行snapshot、未中断作业、未启动仿真。

## 终止、截断和bootstrap

- `scripts/canonical48_rl_env_20260923.py:343` 将runner的terminal事件设为done，358行返回`terminated=done,truncated=False`。自然24s终点被定义为真正有限任务终点；严重穿透导致runner提前结束也经terminal处理。这与本实验协议一致，而不是把无限任务的任意TimeLimit误当真实终止。
- `scripts/canonical48_potential_reward_20260924.py:33` 终端强制`Φ(next)=0`。bridge终端返回最后actor observation的占位行为不会进入terminal potential。reset的58–59行重新保存初始obs/phase，不跨episode延续旧势。
- SB3 2.9.0的`common/vec_env/dummy_vec_env.py:62` 将`TimeLimit.truncated=truncated and not terminated`。`common/on_policy_algorithm.py:236` 只对该标志为真的terminal observation加`gamma*V`。本实验终端该标志为False，不触发timeout bootstrap。
- `common/buffers.py:428` 的GAE递推在episode边界用`next_non_terminal=0`，屏蔽终端后的value；即使VecEnv自动reset并返回新episode初态，也不会把它当作上一episode末value。普通64步rollout结束仍以当前非terminal next observation进行bootstrap。
- 8192互动预算结束处是未完成episode的截断采集，close取消worker，但不会再向PPO塞一个假的terminal transition。最后一段正常64步rollout已经按非terminal next observation估value、更新完毕；partial仅保留为partial，不当任务失败或成功。

源码位置以冻结snapshot中相同文件为准，已核对manifest的156项源hash，以及独立入口/base workflow的hash。固定gamma=.995、VecNormalize的norm_reward=False，未发现reward折扣与优化器gamma不一致。

## 两个影响审计范围的记录缺口

1. **没有持久化Gym实际reward、reward_terms或SB3 rollout values/advantages。** 新wrapper在73行把terms放入info，但原训练工作流没有将该info数组写盘。因此现有记录可按冻结源码和真实obs/phase重建应有reward，不能直接逐项比对PPO当时实际消费的buffer内容，也不能复算实测GAE/loss。DummyVecEnv会把reward存为float32；审计单列float32模拟回报，不能把float64望远镜误差当作优化器实际数值误差。
2. **budget partial缺最后一个next observation。** QueuePolicy在bridge第136行先发布当前observation，等待action；第138–139行遇到close发送的None就提前中断，第147行才是保存observation。故N步partial的actor_trace只有N个pre-action observation，没有最后动作后的第N+1个边界观测。它只能精确重建前N−1项新势函数reward；最后一项及最后的critic bootstrap值不可由当前trace精确恢复。完整自然终止episode不受这个缺口影响，因为最后势按协议固定为0。

这些是证据可追溯性的限制，当前没有证据说明运行时实际reward算错。下一次独立实验可在Gym reward计算后记录transition reward/terms/terminated/truncated和next actor observation，再通过只读callback记录必要bootstrap/value；先验证行为不变，不为此次已经运行的snapshot临时加钩子。

## 已实现并运行的独立离线审计

工具 `tools/audit_ppo_potential_reward_20260924.py` 只读train轨迹，直接按势函数表达式独立计算，再与冻结奖励模块逐项核对；原evaluation纯函数从冻结bridge AST提取，不导入或实例化仿真环境，不调用旧reward。

运行中初次证据：`docs/PPO_POTENTIAL_REWARD_AUDIT_20260924_RUNNING.md`及同名JSON。审计时已落盘4个完整600步episode、共2400步，第5条pending。四条task/gate均False，基础终端奖励0；每条完整折扣return约.06666666，等于`−Φ(initial)`，最大折扣shaping残差`5.27e-16`。这些失败回合没有因阶段进展从潜势项额外获得完整回合回报；不据中间结果改模型或奖励。

工具能在运行中保留pending/正在写入/partial状态，不要求所有8192步已经落盘。若run COMPLETE存在则额外核对持久化动作总数等于声明预算。对已保存partial，检验非terminal前缀恒等式`−Φ(initial)+γ^K Φ(last_recorded)`，明确缺失末项，不强制Φ=0。最终应以新输出文件重跑一次，不覆盖中途审计记录。

验证：新增7项审计边界测试，加上原11项奖励测试，共18项通过。没有修改周报或持续入口。

```text
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tools/audit_ppo_potential_reward_20260924.py \
  --run outputs/canonical48_ppo_potential_8192_20260924_r1 \
  --output docs/PPO_POTENTIAL_REWARD_AUDIT_20260924_FINAL.md
```

理论边界：势函数折扣和在完整有限episode上的恒等式是逐轨迹代数性质；它保持新稀疏终端目标的排序，不保持旧密集reward目标。当前48D观测没有显式剩余时间，完整Markov充分性也未证明；这可能影响critic近似与有限rollout优化，但不破坏本次逐轨迹恒等式，更不能由此单独归因训练失败。
