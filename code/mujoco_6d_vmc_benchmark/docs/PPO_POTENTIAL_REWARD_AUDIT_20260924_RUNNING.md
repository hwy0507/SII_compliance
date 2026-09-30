# Potential PPO训练奖励独立审计

运行完成：False；已持久化动作：2400/8192；完整训练回合：4。仅统计已落盘序列，不把partial或正在写入的轨迹当终端。

| episode | 状态 | 动作/可复算reward数 | task/gate | 基础终端奖励 | 完整折扣return | 潜势恒等式残差 |
|---|---|---|---|---|---|---|
| episode_00000 | complete | 600/600 | False/False | 0.0 | 0.06666666 | 1.3877787807814457e-16 |
| episode_00001 | complete | 600/600 | False/False | 0.0 | 0.06666666 | 3.7470027081099033e-16 |
| episode_00002 | complete | 600/600 | False/False | 0.0 | 0.06666666 | -2.7755575615628914e-16 |
| episode_00003 | complete | 600/600 | False/False | 0.0 | 0.06666666 | 5.273559366969494e-16 |
| episode_00004 | pending_trace | None/None | None/None | None | — | None |

冻结源码156项、入口/base workflow以及gamma/reward manifest一致。完整回合按真实obs/phase和冻结evaluation重算；新势函数奖励未调用旧密集reward。

完整回合discounted shaping = −Φ(initial)，基础奖励仅在终端加入；本工具同时计算float32奖励折扣回报以反映VecEnv存储精度。partial已知前缀使用−Φ(initial)+γ^KΦ(last recorded)，不把末尾势设为零。

审计限制：没有保存Gym实际reward/terms或SB3 buffer，不能逐项核验当时被PPO消费的值；partial最后一个next observation未保存，最后一项reward及critic bootstrap不可精确恢复。源码和真实序列足以完整复算自然终止回合。运行中的缺失trace标pending，训练完成前不把样本数不足当失败。
