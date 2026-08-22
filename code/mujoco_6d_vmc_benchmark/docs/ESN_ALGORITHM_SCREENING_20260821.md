# ESN 算法筛选与四方法确认实验（2026-08-21）

## 结论先行

在 MuJoCo FR3 斜木板抬升任务上，ESN 的 reservoir 算法筛选没有得到超过 VMC 的结果。正式的 held-out 测试中，ESN 与 VMC 都是 20/20 成功，但 ESN 的接触冲量和接触后峰值误差明显更高；ESN 仅在峰值力矩上更低。因此当前不能汇报“ESN 全面优于 VMC”，更严谨的结论是：在相同 32-D 可部署观测和 2% 残差预算下，ESN 可以保持任务成功并降低峰值力矩，但其冲击吸收与恢复性能仍落后于 VMC。

## 公平性与 MuJoCo 协议

- 服务器：`arm1@192.168.31.70`，工程 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`。
- MuJoCo 后端：`MUJOCO_GL=osmesa`；Python 为 `/home/arm1/vmc_mujoco_runtime/.venv/bin/python`。
- 四种方法：原 paper 方法（PaperMPC）、VMC、同数据 MLP、ESN。
- 学生观测固定为 32-D：`q(7), qdot(7), nominal_twist(6), wbc_pose_error(6), wbc_twist_error(6)`。
- 学生没有接收 board yaw、板位姿、接触法向、接触力、接触时刻、障碍物身份或未来信息。
- 残差预算统一为 2%；训练 teacher traces、测试场景、随机 seed 和几何门控保持一致。
- 木板是 MuJoCo 中的实体斜板；yaw 只作为场景配置，接触量只在离线统计中使用。

## ESN 筛选过程

训练数据使用同一批成功 teacher traces：tilt=35/40°，yaw=0/30°，以及 tilt=40°、yaw=60° 的成功轨迹和 neutral trace。tilt=35°、yaw=60° 的失败 teacher 保留在 manifest 中，但没有进入训练。

开发筛选在未参与训练的 tilt=37.5°、yaw=75/105°、4 个 rollout 上进行。选择规则预先固定为：先最大化成功率，成功率打平时最小化峰值力、冲量和接触后误差相对于固定 VMC 的等权比值。

最优可行配置为：240 units，spectral radius=0.90，input scale=0.45，快/慢时间常数=0.04/0.16 s，fast fraction=0.5，ridge=1e-4，部署端 yielding 输出平滑系数 α=0.5。它在筛选集的综合物理损失约为 VMC 的 1.17 倍，仍未超过 VMC。

其它失败或未改善的尝试也已保留：

- 单时间尺度 0.04/0.08/0.16 s：冲量约 63--65 N·s，高于 VMC 约 40 N·s。
- 双尺度 0.04/0.12 s、0.06/0.16 s：没有改善；0.06/0.16 s 更差。
- target-lead=1/2 的因果动作目标移位：冲量和恢复误差上升，说明不是简单的标签延迟问题。
- derivative matching / smoothness regularization：只有很小改善。
- 基于部署可测 WBC 位姿误差的 error-aligned yielding：冲量降到约 14 N·s，但 4/4 任务失败，物块保持性为零，因此不能采用。
- 320/480 units 和另外两个 reservoir seed：没有超过 240-unit 主配置。

## 正式 held-out 四方法结果

测试角度为训练未使用的 yaw=90°、120°；tilt=35°、40°；5 个 seed；每个方法 20 次 rollout。

| 方法 | 成功率 | 平均峰值接触力 (N) | 平均接触冲量 (N·s) | 平均接触后峰值误差 (mm) | 平均峰值力矩 (N·m) |
|---|---:|---:|---:|---:|---:|
| PaperMPC | 20/20 (100%) | 126.17 | 91.35 | 279.28 | 41.21 |
| VMC | 20/20 (100%) | 123.68 | **25.29** | **193.29** | 39.80 |
| MLP | 20/20 (100%) | **119.06** | 29.94 | 193.32 | 39.24 |
| ESN（40/160 ms + α=0.5） | 20/20 (100%) | 121.64 | 45.36 | 220.87 | **38.27** |

相对于 VMC，ESN 的平均冲量约高 79.3%，接触后峰值误差约高 14.3%，峰值力矩约低 3.8%。所有方法 geometry-valid postgrasp rate 均为 100%。

## 可复现实验产物

- 最终四方法 JSON：[four_method_confirmatory_yaw90_120.json](../outputs/inclined_lift_esn_screen_20260821/four_method_confirmatory_yaw90_120.json)
- 第一轮 reservoir 筛选：[screen.json](../outputs/inclined_lift_esn_screen_20260821/screen.json)
- 第二轮 target-lead / derivative：[screen_round2.json](../outputs/inclined_lift_esn_screen_20260821/screen_round2.json)
- 第三轮结构化后处理：[screen_round3.json](../outputs/inclined_lift_esn_screen_20260821/screen_round3.json)
- 第四轮容量和 reservoir seed：[screen_round4.json](../outputs/inclined_lift_esn_screen_20260821/screen_round4.json)
- 服务器完整输出目录：`/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_esn_screen_20260821/`

## 当前建议

这个场景可以作为一个诚实的 demo：ESN 能够在未知 yaw 上完成柔顺避障，并将峰值力矩压低；但在当前 teacher、观测和 2% 预算协议下，VMC 仍是更好的冲击恢复基线。若要继续研究，应优先改变任务/训练目标本身（例如对接触后恢复和冲量进行明确的多目标监督或在线闭环学习），而不是继续无止境地堆 reservoir 超参数。

## Overnight 搜索任务

服务器后台任务已启动，PID 文件为 `/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_overnight_20260821/pid`。搜索器会在约 14.2 小时预算内分阶段运行：约 2000 个便宜候选、128 个跨角度复筛、32 个宽应力网格测试和 16 个最终确认候选；每个阶段逐项写入 `overnight_manifest.json`，支持 `--resume` 断点恢复。完整日志位于 `/home/arm1/vmc_mujoco_runtime/outputs/inclined_lift_overnight_20260821/overnight.log`。

### Overnight 已完成结果（2026-08-22）

任务实际运行约 5.20 小时后完成全部计划阶段：2000 个 stage-1 候选、128 个 stage-2 候选、32 个 stage-3 候选和 16 个 final 候选。搜索器中发现了一批“低力/低冲量但没有真正接触木板”的伪优候选；这些候选的 `geometry_valid_rate` 为 0 或低于 1，不能作为算法胜出证据。最终只采用 geometry-valid=1 的候选进行解释。

当前最值得继续验证的候选为 `e467090c86b6`：

- 320 reservoir units；spectral radius 0.90；input scale 0.80；ridge `3e-5`；reservoir seed `20263050`；
- 双时间尺度 0.04/0.16 s；yield smoothing α=0.7；mirror gate 开启；target-lead=1；smoothness weight=0.01；
- 仍然只使用 32-D deployable observation，预算为 2%；没有输入 yaw、接触力、法向或接触时刻。

最终测试为 tilt=35/40°、yaw=90/120°、5 个 seed，共 20 次 rollout：

| 方法 | 成功率 | geometry-valid | 峰值接触力 (N) | 接触冲量 (N·s) | 接触后峰值误差 (mm) | 峰值力矩 (N·m) |
|---|---:|---:|---:|---:|---:|---:|
| ESN `e467090c86b6` | 20/20 | 20/20 | 117.49 | **12.56** | **166.16** | **37.27** |
| 同预算 VMC | 20/20 | 20/20 | 121.63 | 25.90 | 192.84 | 40.03 |

相对 VMC，ESN 的峰值接触力下降 3.4%，接触冲量下降 51.5%，接触后峰值误差下降 13.8%，峰值力矩下降 6.9%。这组结果是目前第一个在保留真实接触的前提下，ESN 在该斜木板任务上同时优于 VMC 的候选。

但仍需注意：这是一组从 2000 个候选中筛选后在新的 20 次测试上的确认结果，不应直接替代完整四方法最终表。下一步应固定 `e467090c86b6`，再与 PaperMPC 和同数据 MLP 在完全相同的 20 个 rollout 上重新跑一次，并增加独立随机 seed，避免把候选选择收益误认为普适性。

### 同一 20 个 rollout 的四方法确认

已完成完全相同的 tilt/yaw/seed 四方法重跑（每个方法 20 次，所有方法 geometry-valid=20/20）：

| 方法 | 成功率 | 峰值接触力 (N) | 接触冲量 (N·s) | 接触后峰值误差 (mm) | 峰值力矩 (N·m) |
|---|---:|---:|---:|---:|---:|
| PaperMPC | 20/20 | 127.37 | 90.84 | 278.05 | 41.20 |
| VMC | 20/20 | 121.63 | 25.90 | 192.84 | 40.03 |
| MLP | 20/20 | 119.70 | 29.99 | 192.39 | 39.44 |
| ESN `e467090c86b6` | 20/20 | **117.49** | **12.56** | **166.16** | **37.27** |

因此，在这组严格对齐的 held-out 斜木板实验上，当前 ESN 候选同时优于 VMC、MLP 和 PaperMPC 的四项核心物理指标，且成功率相同。相对 VMC，冲量下降 51.5%，接触后峰值误差下降 13.8%，峰值力矩下降 6.9%。该结果可以作为当前最强的可汇报结果，但仍应在更多完全独立 seed 和不同接触条件上做最终确认。

四方法确认文件：[four_method_e467_confirmatory.json](../outputs/inclined_lift_overnight_20260821/four_method_e467_confirmatory.json)。
