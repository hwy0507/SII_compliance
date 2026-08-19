# Real-WBC (Pink-IK) 部署与「残差 vs 全接管」对照实验

日期：2026-08-19 · 机器人：Franka Research 3 (MuJoCo) · WBC：AdaCompNUS Autolife-Planning Pink 差分 IK（vendored，未改动）

## 1. 交代的溯源链

- 上游：`autolife-planning==0.3.4`（[AdaCompNUS/Autolife-Planning](https://github.com/AdaCompNUS/Autolife-Planning)，也是 [Prepose-Sampler](https://github.com/sally-00/cutting_simulation) 同生态的 WBC/IK 栈）
- 获取方式：PyPI wheel 解包，**源码零改动** vendored 到 `scripts/vendor_autolife/`（wheel 仅发 x86_64，我们服务器是 aarch64；WBC 模块是纯 Python，依赖 `pin`/`pin-pink` 多架构包）
- FR3 平台适配全部在 `scripts/pink_wbc_adapter.py`（链配置指向官方 FR3 URDF；hand→法兰 −45° 常量转换；40ms 在线差分 IK 语义；关闭 Autolife 专属任务：头部相机稳定、CoM、膝踝耦合）

## 2. FK 一致性验证（适配正确性）

pinocchio URDF `fr3_link8` FK 与 MuJoCo 场景 hand 原点在 home 位形完全重合：

```
pinocchio fr3_link8 = [0.5545, 0, 0.6245]
mujoco   hand       = [0.5545, 0, 0.6245]   (0.000 mm)
```

## 3. Pink WBC 基线表现（意外发现：真 WBC 强得多）

双撞击场景（棒击→抓取→二次棒击），同一速度伺服、零残差：

| WBC | 峰值偏差 | 抓取时刻残余 | 任务 |
|---|---:|---:|---|
| 旧 resolved-rate（自写占位） | 39.9 mm | 20.1 mm | ❌ 失败（关爪落空） |
| **Pink 差分 IK（vendored）** | **24.6 mm** | **0.9 mm** | ✅ 成功 |

原因：差分 IK 在 40ms 控制周期的有效带宽 ≈ 1/dt = 25/s，远高于占位 WBC 的 K_p = 3/s；且 QP+LM+姿态正则对冗余 7-DOF 的利用更好。fx0–fx3 全部 18/18 成功（旧占位 WBC 在双撞击下失败）。

**含义**：换上真 WBC 后，"柔顺提升跟踪"的空间被压缩（残差 ESN 仅 −0.2mm），但这让「为什么不让 ESN 全局接管」成为核心问题——正是本实验。

## 4. 实验设计：同数据、同学法、不同部署架构

**教师**（唯一专家源）：Pink WBC + 速度伺服 + 有界残差 ESN（3% 预算，全部任务成功）。
18 条演示（fx0–3 + 双撞击 + 无撞击 × 3 seeds），逐步记录观测 32-D 与力矩分解。

**三个学生**（相同 DirectESN：160 神经元、相同超参、相同数据、各 3 seeds）：

| 架构 | 动作语义 | 部署 |
|---|---|---|
| A 残差 | 残差力矩 / 3% 预算 | 叠加在运行中的伺服上 |
| B 全接管(+GC) | (总力矩−重力)/硬件限位 | 仅重力前馈，无伺服，100% 权限 |
| C 全接管(纯) | 总力矩/硬件限位 | 无任何其他控制器，100% 权限 |

DAgger：B/C 各跑一轮（教师影子通道在学生访问状态上打精确标签——env 内新增非施加的影子伺服计算）。

## 5. 结果（每方法 18 回合：6 场景 × 3 seeds）

| 方法 | 任务成功 | 峰值偏差 | RMSE | 峰值力矩 | 硬限位触发 |
|---|---:|---:|---:|---:|---:|
| Pink WBC + 伺服（名义） | **18/18** | 11.9 mm | 2.9 mm | 33.3 Nm | 0 |
| **A: + ESN 残差 3%** | **18/18** | 11.7 mm | 2.9 mm | 34.3 Nm | 0 |
| B: ESN 全接管(+GC) ×3 seeds | **0/18** | 1139–1417 mm | 661–881 mm | **87.0 Nm 顶死** | 18/18 |
| B + DAgger ×3 seeds | **0/18** | 1371–1417 mm | 827–881 mm | 87.0 顶死 | 18/18 |
| C: ESN 全接管(纯) ×3 seeds | **0/18** | 1216–1457 mm | 776–852 mm | 87.0 顶死 | 18/18 |
| C + DAgger ×3 seeds | **0/18** | 1345–1460 mm | 776–858 mm | 87.0 顶死 | 18/18 |

关键事实：

1. **全接管在无撞击场景也一样崩溃**——不是撞击处理问题，是闭环稳定性问题：BC 学到的映射在自诱导的分布外状态上正反馈发散，机械臂甩出 >1.2 m，力矩从第一步起顶死 87 Nm 硬限位。
2. **重力前馈救不了**（B vs C 无差别）——缺的是速度伺服的阻尼/跟踪项，不是重力。
3. **DAgger 一轮救不回来**——发散态数据反而让训练 MSE 上升（0.00006→0.00134），发散是结构性的（线性读出 + 全权限 × tanh 饱和 = 有限增益但无相位稳定裕度），不是数据量问题。
4. 开环训练 MSE 上全接管反而更低（6e-5 vs 3.3e-4，归一化单位）——**开环模仿误差与闭环稳定性完全脱钩**，这本身就是残差架构安全性的论据。

## 6. 动图（双撞击场景）

| 文件 | 内容 | 结果 |
|---|---|---|
| `1_pink_fw.gif` | Pink WBC + 伺服（无残差） | ✅ 抓取成功 |
| `2_residual_esn.gif` | + ESN 残差 3%（当前系统） | ✅ 抓取成功 |
| `3_takeover_gc.gif` | ESN 全接管（含重力前馈） | ❌ 立即飞出 |
| `4_takeover.gif` | ESN 全接管（纯） | ❌ 立即飞出 |

## 7. 结论（回应"为什么 3% 预算、不让 ESN 全局接管"）

- 残差架构的价值不是"精度调优"，而是**把一个开环不错的函数逼近器（ESN 线性读出）变成闭环可部署的控制器**：伺服提供稳定主干，ESN 只在 3% 权限内做柔顺修正，最坏情况 |τ|≤2.6 Nm。
- 全接管 = 用有限 BC 数据学一个全局非线性控制器（重力+伺服+柔顺），本实验证明在同分布数据 + DAgger 下仍然一步发散——这不是训练不足，是架构性问题。
- 附加发现：真 WBC（Pink 差分 IK）本身足够强，未来柔顺层的主张应转向力矩峰值/瞬态/安全裕度方向，而非跟踪精度。

## 8. 复现

```bash
python scripts/pink_takeover_experiment.py --stage all   # data→train→dagger→eval
# GIF: outputs/pink_takeover/gifs/
# 原始数: outputs/pink_takeover/eval_results.json
```
