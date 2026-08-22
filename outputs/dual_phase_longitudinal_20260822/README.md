# Dual-phase longitudinal contact task（2026-08-22）

## 可汇报结论

本实验在 MuJoCo FR3 + Panda Hand 中统一了两个连续、真实接触阶段：

1. 抓取前下探：纵向末端 / link-7 撞到蓝色水平木板的有限边缘，滑开并恢复到物块；
2. 真实手指夹持后上提：末端撞到橙色竖直木板，滑开、保持物块并完成搬运。

Held-out 协议包含 8 个新 seed、2 个未用于训练的 y offset 和 2 个未用于训练的 z offset，共 32 个匹配条件/方法。PaperMPC、VMC、MLP、ESN 均为 32/32 成功，且 32/32 均满足双阶段接触顺序与几何审计。

选中 ESN 相对 VMC 的预声明五指标综合比值为 0.9819（越低越好），按 seed cluster bootstrap 的 95% CI 为 [0.9778, 0.9863]。因此，在本实验范围内可以严谨地说 ESN 的综合柔顺指标优于 VMC；不能说 ESN 在每个单项上都占优，也不能说其综合指标显著优于 MLP。

## 公平性与物理约束

- 四方法使用同一 MuJoCo 模型、同一双板几何、同一 reference、同一 seed、同一 4% residual torque budget 和同一安全限幅。
- MLP 与 ESN 的输入严格相同，均为 32-D：`q(7), qdot(7), nominal_twist(6), WBC pose error(6), WBC twist error(6)`。
- MLP/ESN 不输入板位置、板法向、接触力、碰撞标签、物块状态、未来轨迹或障碍物身份。
- 两块板都是固定 world MuJoCo box geom；episode 内不移动、不 teleport。
- 抓取完全由 Panda 手指—自由物块接触完成；无 weld/equality attach，无物块 qpos 修改。
- `t=0` 板接触采用 hard gate；held-out 128 条方法 rollout 均无初始板接触。
- 所有 held-out rollout 均无物块—板接触；目标板接触对象均为 `hand` 和/或 `fr3_link7` collision geom。
- held-out 最大 penetration：pre-grasp 0.299 mm，post-grasp 0.059 mm，均低于 2 mm 的有效性上限。

## Held-out 全面结果

| 方法 | 成功率 | Pre 峰值力 N | Pre 冲量 N·s | Post 峰值力 N | Post 冲量 N·s | 总板冲量 N·s | 峰值 jerk m/s³ | 最终抬升 mm |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| PaperMPC | 32/32 | 27.766 | **6.159** | 6.992 | 0.600 | **6.759** | 1325.88 | 193.90 |
| VMC | 32/32 | 27.704 | 7.145 | 6.658 | 0.334 | 7.480 | 1351.58 | 196.99 |
| MLP | 32/32 | **27.079** | 7.139 | **6.504** | 0.337 | 7.476 | **1298.23** | 195.67 |
| ESN proposed | 32/32 | 27.651 | 7.157 | 6.517 | **0.319** | 7.476 | 1326.54 | **197.01** |

ESN 相对 VMC：

- pre 峰值力降低 0.19%；
- pre 冲量增加 0.17%（ESN 在该项没有胜出）；
- post 峰值力降低 2.11%；
- post 冲量降低 4.55%；
- peak jerk 降低 1.85%；
- 五指标按匹配条件计算的综合比值 0.9819，95% CI [0.9778, 0.9863]。

ESN 相对 MLP 的五指标综合比值为 0.9937，95% CI [0.9848, 1.0043]，区间跨过 1。ESN 的主要优势在 post-contact impulse 和物块保持；MLP 在 pre-contact force 与 jerk 上更好。因此当前证据不支持“ESN 显著全面优于 MLP”。

PaperMPC 的总冲量最低，主要因为它的 pre-contact impulse 明显较小；但其 post-contact impulse 明显高于 VMC/MLP/ESN。不能把 ESN 描述为所有指标全局最优。

## 模型与训练

- VMC teacher：torque residual，translation stiffness 0.5，共享 4% budget。
- Teacher traces：18/18 双阶段成功；板位/接触数据只写入审计 manifest，不写入 `.npz` observation。
- ESN：160 reservoir units，spectral radius 0.92，input scale 0.45，time constant 0.08 s，ridge 1e-4，deployment smoothing alpha 0.85。
- MLP：128 hidden units；与 ESN 使用同一批 18 条 32-D teacher traces。
- ESN/MLP 超参数只在 development 条件选择；held-out seed/offset 未参与选择。

## GIF

GIF 均为 25 fps，每个 40 ms policy frame 都录制。左侧为全景，右侧为两块板与末端的近景；时间轴覆盖下探、第一次接触、真实抓取、上提、第二次接触和搬运。

- [PaperMPC](gifs/paper_mpc_dual.gif)
- [VMC](gifs/vmc_dual.gif)
- [MLP](gifs/mlp_dual.gif)
- [ESN proposed](gifs/esn_dual.gif)

## 结果文件

- `dual_phase_four_method_heldout_20260822.json`：32 个条件 × 4 方法的逐 rollout 数据和汇总；
- `dual_phase_four_method_heldout_stats_20260822.json`：相对 VMC 的 paired seed-cluster bootstrap；
- `dual_phase_esn_vs_mlp_heldout_stats_20260822.json`：ESN 相对 MLP 的 paired bootstrap；
- `development/screen.json`：12 个 ESN 配置的 development-only 筛选；
- `development/manifest.json`：18 条 VMC teacher trace 的物理审计；
- `models/esn_01.npz`：锁定的 proposed ESN；
- `models/mlp_h128_s20265601.npz`：锁定的 MLP baseline；
- `gifs/manifest.json`：四个 demo rollout 的接触和抓取审计。

## 服务器复现环境

```bash
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts
export MUJOCO_GL=osmesa
export PYTHONPATH=.
```

核心入口：

```text
record_dual_phase_teacher.py
screen_dual_phase_esn.py
evaluate_dual_phase_four_method.py
analyze_dual_phase_heldout.py
render_dual_phase_four_method_gifs.py
```

## 当前局限

- 结果来自 MuJoCo，尚未做真机 system identification、传感延迟、关节摩擦与结构柔性验证。
- 只有一个 FR3 抓取 reference 和一族轻微板位/contact-time 随机化；不能外推到任意障碍物。
- 当前 ESN 对 VMC 的优势幅度小，且对 MLP 的综合 CI 跨 1；论文表述应限定为本 dual-contact protocol。
- 训练 teacher 是 VMC behavioral cloning；下一步若要扩大 ESN 优势，应采用不含特权输入的 trajectory-level residual optimization/DAgger teacher，而不是继续从同一 VMC 标签做近乎精确拟合。
