# 本机旧奖励与潜势奖励PPO8192：最终模型同平台对照

两轮均使用固定8192步最终模型，未选择中间checkpoint；同train/validation fixture、PPO训练参数和软件版本。此处不拼接DGX实验指标。

| 条件 | 原模型task/gate | 潜势模型task/gate | 原→潜势终点误差mm | 原→潜势外部单对象合力峰值N |
|---|---|---|---|---|
| train/zero | False/False | False/False | 187.87→187.87 | 219.22→219.22 |
| train/ppo | False/False | False/False | 294.15→15.74 | 976.29→206.49 |
| validation/zero | True/True | True/True | 7.07→7.07 | 87.70→87.70 |
| validation/ppo | False/False | False/False | 94.43→15.49 | 1138.24→373.28 |

两种zero对照原始数组完全一致：train=True（27数组），validation=True（27数组）。这核对同平台reward变化未改变zero动作物理对照，不证明跨平台动力学一致。

共同使用的9项bridge/控制核心源hash一致，fixture完整规格一致，133项模型资产hash相同且已复核当前文件。其他共享源变化明细在JSON。

终点误差沿用最后10帧到当前任务目标的平均值，未到最终阶段时较小数值不代表完成了抬升；完整phase、task、gate记录在JSON。合力峰值来自既有物理子步逐对象接触审计；没有把25Hz速度/力矩指标改称全物理子步峰值。

两个reward定义不同，不比较episode_reward大小来宣称改善。最终解释须同时看task/gate、阶段和力峰值；仅一次训练seed和两条fixture，不能作显著性或论文级泛化结论。

潜势最终checkpoint：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/canonical48_ppo_potential_8192_20260924_r1/ppo_final.zip`，SHA256 `5f07bf8bac134c8464dd5daa8d8c4b46aa547525004ad37d0173d6cf0f3b1609`。

冻结normalizer：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/canonical48_ppo_potential_8192_20260924_r1/vecnormalize_train_only.pkl`，SHA256 `944f583cce8b73df5f0328a9f981e47f96cb986e7eb35384be26742e922d9f9a`。

最终模型timesteps=8192，优化updates=384。DGX部署前仍需推理parity和同MJB物理条件核对。
