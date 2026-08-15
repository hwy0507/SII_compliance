# Impulse-aware PPO pilot（post-V4 development）

两条训练期冲量惩罚候选均失败，不能进入 multi-seed 或 V4 final。

| 方法 | task / no-rod | effective collision | recovery RMSE (mm) | rejoin (s) | jerk (m/s³) | impulse (N·s) |
|---|---:|---:|---:|---:|---:|---:|
| zero-residual | 9/9 / 9/9 | 8/9 | 1.726 | 0.0322 | 955.87 | 3.177 |
| impulse light (0.03) | 9/9 / 9/9 | 9/9 | 1.734 | 0.0367 | 955.43 | 3.214 |
| impulse medium (0.08) | 9/9 / 9/9 | 9/9 | 1.735 | 0.0367 | 955.20 | 3.217 |

惩罚使 jerk 几乎回到基线，但没有降低 impulse；两个权重反而都使 impulse、rejoin 和 recovery RMSE 变差。该实验表明，在此固定杆轨迹和当前 residual 接口中，接触冲量主要由外部杆的预设动量和接触几何决定，当前 25 Hz residual 对其影响很弱。后续不应盲目继续提高该 reward 权重。
