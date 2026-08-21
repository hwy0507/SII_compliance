# Handoff — Paper-MPC 名义控制器 × 柔顺层支线（paper-mpc-baseline）

> 更新：2026-08-21 · 分支：`paper-mpc-baseline`（最新提交见 `git log --oneline -1`）
> 服务器：arm1@192.168.31.70（密码 123456），工程在 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`
> 本地仓库：`/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709`，remote = github.com/hwy0507/SII_compliance

> 续接记录：2026-08-21 已为 `run_paper_mpc_benchmark.py` 加入显式 `--eval-seeds` 多种子评估、逐行 `seed` 溯源和 companion summary sidecar；详见 `docs/paper_mpc_benchmark/MULTISEED_PROTOCOL.md`。MuJoCo 长跑尚未在本地执行，待服务器按该协议补齐 5 个评估种子。

> 2026-08-21 服务器结果已补齐：`docs/paper_mpc_benchmark/MULTISEED_RESULTS_20260821.md`。当前 5 个 seed 在固定 fixture 下完全复现（每格 std≈0），所以这是可复现性检查，不是随机物理扰动置信区间。

> 同日完成 `σ=0.01 rad/s` 关节速度观测噪声评测，结果见 `docs/paper_mpc_benchmark/SENSOR_NOISE_RESULTS_20260821.md`：ESN 50/50，MLP 49/50，裸机 25/50，VMC 50/50（沿用无噪声选优配置）。

> 随机化冲击工况也已完成，见 `docs/paper_mpc_benchmark/RANDOMIZED_IMPACT_RESULTS_20260821.md`。ESN-101/202/303 均 50/50；ESN-303 棒/球均值 9.30 mm，接近并略优于 VMC 9.40 mm，但三 seed 平均仍不全面超过 VMC。Proposed 定位应写为跨工况免调参 ESN 柔顺层，而不是“全面击败 VMC”。

> 随机化教师蒸馏消融也已完成，见 `docs/paper_mpc_benchmark/RANDOMIZED_BC_RESULTS_20260821.md`：12 条 rod/ball 随机教师轨迹没有带来一致的误差提升，故正式 proposed 暂保留 stable-reference coverage BC；随机化 BC 作为负结果/消融，不替换主 checkpoint。

> **最新且应优先引用的公平结论（2026-08-21）：**已完成 ESN/VMC 共享预算候选、仅在 validation
> 选择配置、一次性 held-out test 的协议，完整记录见
> `docs/paper_mpc_benchmark/FAIR_BUDGET_SELECTION_RESULTS_20260821.md`。两者均为 50/50；
> ESN-303/3% 的总体误差 `9.229 mm`，VMC k=1.5/3% 为 `9.357 mm`，但五 seed 配对 95% 区间跨
> 零，故**不得声称 ESN 总体战胜 VMC**。它在 ball/board 更低、在 rod 更高，且木板接触力更高。
> 3% 是对称 validation 选择的结果，不是事先强制固定的预算。

> **后续算法改进的最新结论（2026-08-21）：**在单独的 finite-mass contact-apparatus
> 协议中，BC 初始化 ESN 通过 train-only MuJoCo CEM 优化其七个有界 readout gain 后，在新的
> validation 中选出 CEM ESN-303/5%，VMC 独立选出 k=2.2/5%。二者在 20 个全新 held-out
> realization 上均 20/20 成功；ESN `8.887 mm`、VMC `9.634 mm`，ESN−VMC 配对差
> `−0.747 mm`，fixture- 与 seed-level 95% CI 均不跨零。这个结论只适用于声明的
> MuJoCo 物理包络和“BC + train-only policy improvement”方法，完整协议/限制见
> `docs/paper_mpc_benchmark/ESN_CEM_POLICY_IMPROVEMENT_{PROTOCOL,RESULTS}_20260821.md`。

> **跨接触条件验证的边界结果（2026-08-21）：**将上述 CEM-ESN 完全冻结，迁移到新的
> `positive_y` 反向滑台 + finite-mass ellipsoidal hand-proxy 接触；VMC 只在新 validation
> 上重新选择。held-out 中 frozen ESN `0/20`，validation-selected VMC k=1.0/2% 为 `14/20`；
> ESN/VMC at-grasp error `35.951/20.182 mm`。因此上一轮优势不具备自动跨接触不变性，
> 当前主张必须限定在已声明接触条件内。完整记录见
> `docs/paper_mpc_benchmark/CROSS_CONTACT_GENERALIZATION_{PROTOCOL,RESULTS}_20260821.md`。

本文档完整记录这条支线的**动机 → 方法 → 实验 → 当前结果 → 遗留事项**。接手前请通读；
术语定义在 §1，架构在 §2，所有代码入口在 §3，实验结论在 §5-§7，坑清单在 §8（重要！）。

---

## 1. 项目背景与这条支线的位置

### 1.1 大图景

最终目标系统是 NUS 的 **Visibility-Aware Mobile Grasping**（论文 arXiv 2605.02487，
本地代码 `code/whole-body-motion-control/`，包名 `grasp_anywhere`）。它的架构：

```
规划器（πg 子目标/πv 注视/πr 全身规划, VAMP+重规划）
   → MPC 控制器（maniskill_env_mpc.py: 一步二次型速度控制, 20Hz, 输出 10 维关节速度）
   → 机器人底层
   → Fetch（论文原机）/ FR3（我们的真机平台, FCI 1kHz 力矩流）
```

该系统**没有机械臂遇到障碍物后的柔顺控制**——这正是本研究要填的格子。系统里甚至
预留了柔顺层槽位：`grasp_anywhere/control/compliance.py`（ComplianceController
Protocol，DISABLED/SHADOW/ACTIVE 三模式，前任实现是残差 PPO）。

### 1.2 本研究的方法主张（一句话）

**上层只管发速度（名义控制器），底层柔顺层吃速度、出力矩：**
```
名义控制器（发布 q̇） → 速度伺服 τ = τ_grav + K_v(q̇_cmd − q̇)
                      → + 残差力矩 τ_res = π(x)·Δτ_budget   ← 我们的研究本体
```
- 阻抗式柔顺（力域），不是导纳式（只挪参考）
- 残差预算 = 硬件限位的百分比（主实验统一 3%）→ 最坏情况有解析上界，真机可部署
- π 的三个实例：**ESN（核心算法）、VMC（解析基线）、MLP（无记忆基线）**
- ESN 骨架严格 Fan Ye 式：固定随机储备池（160 神经元，ρ<1）+ 漏积分 +
  岭回归线性读出（唯一可训练部分）；导数匹配正则作为可消融扩展保留

### 1.3 本支线做了什么（动机）

之前所有实验（v0-v2 时代）用的是**自写的 FixedWBC**（`fixed_panda_wbc.py`，121 行
教科书伪逆）。组会质疑"你这个 WBC 是自己写的玩具"后，本支线把名义控制器换成
**论文系统 MPC 的忠实复刻**（`paper_mpc_wbc.py`），验证柔顺层在"真"名义控制器上
依然有效。这就是分支名 `paper-mpc-baseline` 的含义。

---

## 2. 架构与代码地图（全部在 `code/mujoco_6d_vmc_benchmark/scripts/`）

| 文件 | 角色 |
|---|---|
| `paper_mpc_wbc.py` | **本支线核心新增**：论文 MPC 复刻（见 §2.1） |
| `wbc_velocity_residual_env.py` | 主环境；`wbc_backend` ∈ {fixed, pink, **paper_mpc**}；木板场景参数 `lift_board_tilt_deg` |
| `fr3_scene.py` | FR3+Panda Hand 场景；倾斜木板 geom（v2b 几何，见 §8.4） |
| `run_paper_mpc_benchmark.py` | 本支线主评测脚本（10 格 × 方法矩阵；预算显式必填，有防呆） |
| `record_paper_mpc_expert_traces.py` | 教师轨迹录制器（npz 含 budget 溯源字段） |
| `bootstrap_direct_esn_multifixture.py` | ESN 蒸馏（吃轨迹 npz，输出检查点） |
| `train_mlp_baseline.py` | MLP 基线训练（同数据同契约） |
| `vmc_torque_baseline.py` / `vmc_compliance_baseline.py` | VMC 弹簧-小车力矩版（终版：纯弹簧 J^T，无显式阻尼——原作者 ζ≈0.04 惯例，见主仓库文档） |
| `direct_esn_compliance.py` | ESN 控制器本体 |
| `pink_wbc_adapter.py` + `vendor_autolife/` | （另一支线）原仓库 Pink IK vendored，本支线不用但保留 |

### 2.1 PaperMPC 复刻要点（`paper_mpc_wbc.py` 文件头有完整文档）

对照 `grasp_anywhere/envs/maniskill/maniskill_env_mpc.py` 逐行复刻：
- 一步二次型求解 `(BᵀQB+R)u = BᵀQ(x_ref−x)`，臂块 B=I₇ → `u = gain·Q/(Q+R)·(q_wp−q)`
- 参数取自他们源码：Q_arm=12, R_arm=1, gain=2.5, lookahead=2, 限速 7 rad/s
- waypoint 队列 + 最近点选择（他们的参考消费方式）

**三处文档化的平台适配**（都有数学/机制依据，不是乱调）：
1. waypoint 间距取 `1/(gain_eff·lookahead)=0.217s`——前瞻恰好抵消一步解稳态滞后
   （他们的系统里间距是隐含前馈）；
2. 时间锚定搜索窗 ±3 waypoint——我们的参考在关节空间**回折**（下探/上抬同线），
   纯最近点搜索会跳到回折段；
3. 前瞻不跨 hold 段边界——他们行为树按状态触发抓取，我们固定时刻抓取，
   前瞻跨 hold 会提前起抬、抓空。

### 2.2 三种撞击场景

| 场景 | 实现 | 备注 |
|---|---|---|
| 棒击 rod | rail impactor，4 档强度（fx0-3，fx3 held-out） | 继承自主基准 |
| 球击 ball | 同 fixture 换 `impactor_type="ball"`（球 0.16kg，力 88-123N） | |
| 木板 board | 静态 40° 倾斜板条（0.18×0.05×0.008m, 摩擦 0.25）横在上抬弧中段 | **j1 侧弧**定制参考（knots[3][0]/[4][0] += 0.40）；两段式场景构建自动算板位（75/25 混合 + y+0.09）；rod_start=99 停棒 |

木板场景的本质：臂抓起方块上抬时撞板，须贴板面滑动（y: 0→100→274mm）从板边逃逸。
**这是全项目踩坑最多的场景，见 §8.3-8.4。**

### 2.3 训练管线（coverage BC）

教师 = 调好的 VMC（力矩版）；统一 3% 预算下录：棒 3 条（k2.2）+ 球 3 条（k1.5）+
木板 4 条（k2.2）+ no-rod 1 条 → bootstrap 拟合 ESN（3 种子 101/202/303）或 MLP。
观测 32 维纯本体感受 `[q, q̇, ξ_nom, e_pose, ė]`，动作 7 维（预算单位）。

---

## 3. 怎么跑（接手者第一件事照这个走一遍）

```bash
# 服务器
cd /home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/scripts
source /home/arm1/vmc_mujoco_runtime/.venv/bin/activate
export MUJOCO_GL=osmesa
MEN=/home/arm1/vmc_mujoco_runtime/mujoco_menagerie
OUT=/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_bench   # 所有产物在这

# 1) 录教师轨迹
python record_paper_mpc_expert_traces.py --menagerie $MEN --out-dir $OUT/traces --k 2.2 --budget 0.03
#    （board 轨迹在 run_stage8.sh 里有专门段落：fixture rod_start=99 + lift_board=True）

# 2) 蒸馏 ESN / MLP
python bootstrap_direct_esn_multifixture.py --expert-traces <rod...> <ball...> <board...> \
  --no-rod-expert-trace $OUT/traces/no_rod.npz \
  --output-model $OUT/esn_X.npz --output-summary $OUT/esn_X.json \
  --reservoir-seed 101 --spectral-radius 0.90 --time-constant 0.12 \
  --input-scale 0.45 --ridge-lambda 1e-4 --derivative-match

# 3) 评测（注意 --student-budget 必填，防呆）
python run_paper_mpc_benchmark.py --menagerie $MEN \
  --esn $OUT/esn_final_101.npz --mlp $OUT/mlp_h128_s2.npz \
  --student-budget 0.03 --phase students --out $OUT/results_X.json
```

GIF 生成参考服务器 `/tmp/run_gifs3.sh`（board）/`run_gifs2.sh`（ball）的模式。

---

## 4. 实验演进史（四个版本，两个被撤回的结论）

| 版本 | 内容 | 结果 | 结论修正 |
|---|---|---|---|
| v1 | PaperMPC 复刻 + 三场景 + 旧 ESN 零迁移 + VMC 扫描 | ESN 球 1/4，板全灭 | 发现预算错配 bug（§8.1） |
| v2 | 统一 3% + 棒球混合教师重蒸馏 | ESN 8/8（棒+球） | 当时以为板是"重规划领地" |
| v3 | 木板 j1 侧弧修复 + 3% 板教师 + 全混合 | ESN 10/10×3 种子 | 曾报"超单一 VMC"——**欠调基线，撤回** |
| **v4（当前）** | 基线公平调参（VMC k×5、MLP 配置×6） | 见 §5 | **终版结论** |

---

## 5. 当前结果（v4 公平终版，统一 3% 预算，10 格 = 棒4+球4+板2）

> 下表是 2026-08-19 的单一固定 fixture 结果，保留作为历史 v4 记录；当前应优先引用本节末尾的 2026-08-21 五 seed + 随机化结果。尤其不要再把“ESN 独占精度轴”当作当前结论：服务器复评显示 VMC 仍是很强的绝对误差基线。

| 方法 | 总分 | at-grasp 均值/最差 (8格) | 板接触力 | 达 10/10 配置比例 |
|---|---|---|---|---|
| PaperMPC 裸机 | 5/10 | 24.9 / 29.4 mm | 63.0N | — |
| **ESN（零调参）** | **10/10 ×3 种子** | **9.5-10.9 / ≤16.2 mm** | 22.9-56.3N | **3/3 (100%)** |
| MLP（最优 h128s2） | 10/10 | 21.1 / 30.0 mm | 27.6N | 5/6 (83%) |
| VMC（最优 k1.5） | 10/10 | 20.5 / 24.0 mm | 96.3N | 1/5 k 值 (20%) |

数据文件（全在 `docs/paper_mpc_benchmark/` 与服务器 `$OUT`）：
- `results_final_v3.json` — ESN×3/MLP/裸机/VMC统一 的 10 格明细
- `results_vmc_unified_sweep.json` — VMC k 扫描
- `results_mlp_sweep.json` — MLP 容量/种子扫描
- `results_mixed_students.json` / `results_esn_at5pct.json` — v2 存档
- 检查点：`esn_final_{101,202,303}.npz`、`mlp_h{64,128,256}_s{1,2}.npz`
- GIF（9 张，桌面也有）：`gifs/{rod,ball,board}_{1_none,2_esn,3_vmc}.gif`

## 6. 可汇报的四句话结论（v4）

1. **论文系统的 MPC 裸机扛不住撞击**：棒 3/4、球 0/4（球击 at-grasp 28-29mm 全关空）——柔顺层是必需品；
2. **成功率饱和后 ESN 独占精度轴**：at-grasp 比调优后的 MLP/VMC 紧 2 倍，最差种子仍优于两者均值；
3. **免调参稳定性**：ESN 3/3 种子零调参全过；VMC 1/5 k 值（选错一个 k 丢一格）；MLP 5/6；
4. **板场景力域**：ESN 23N ≈ MLP 28N < 裸机 63N < VMC 96N（其最优成功配置反而最用力——软弹簧滑得慢）。

诚实边界：以上均为 FR3 MuJoCo 仿真、单次评估种子（20260819）+ ESN 3 种子；
零迁移失败证明柔顺学生必须在目标名义控制器上蒸馏（耦合性证据）。

### 5.1 随机化工况补充结果（2026-08-21 服务器，非最终公平选参）

在五个 seed、匹配的 stroke/height/start 工况扰动下，PaperMPC 裸机为 26/50；ESN-101/202/303 均为 50/50；MLP 为 48/50；VMC 为 50/50。棒/球抓取误差均值分别为：ESN-101 11.04 mm、ESN-202 10.42 mm、ESN-303 9.30 mm、VMC 9.40 mm。该轮 VMC 使用无噪声阶段选优配置，因而只作为跨工况补充，不能代替后续的公平预算选择测试。完整数据见 `docs/paper_mpc_benchmark/RANDOMIZED_IMPACT_RESULTS_20260821.md`。

## 7. 下一步（按优先级）

### 7.0 2026-08-21 物理接触装置难工况已完成

已完成一轮独立的、面向真机接触装置的 MuJoCo confirmatory protocol：有限质量 rod + 阻尼滑轨 + 受力上限 position servo + MuJoCo 接触柔软度，双次 press–hold–retract。协议与物理参数见 `docs/paper_mpc_benchmark/CONTACT_APPARATUS_PROTOCOL_20260821.md`，结果见 `docs/paper_mpc_benchmark/CONTACT_APPARATUS_RESULTS_20260821.md`。

服务器原始输出：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_contact_apparatus_fair_20260821/fair_results.json`。validation 选择 ESN-303/5% 与 VMC k=2.2/5%；held-out test 两者均 20/20 成功，ESN 10.387 mm、VMC 10.257 mm，匹配差 +0.131 mm，95% CI 跨零。因此该困难工况仍只能汇报“ESN 与 VMC 相当、未证明超越”，不能声称 ESN 击败 VMC。测试 seeds `20260926–20260930` 已消耗，禁止据此继续调参。

### 7.1 2026-08-21 ESN CEM 读出策略改进已完成

针对“ESN 只是单一 VMC teacher 的 BC，未必能超过独立调优 VMC”的诊断，新增了冻结 reservoir/观测契约、只优化七个有界输出读出增益的 CEM policy-improvement 算法。它在 train-only seeds `20261001–20261004` 上完成优化，随后用全新的 validation seeds `20261011–20261015` 在 BC parent/CEM ESN 与 VMC `k×budget` 候选中各自选一次，最后只在全新 held-out seeds `20261016–20261020` 上测试。协议见 `docs/paper_mpc_benchmark/ESN_CEM_POLICY_IMPROVEMENT_PROTOCOL_20260821.md`，结果见 `docs/paper_mpc_benchmark/ESN_CEM_POLICY_IMPROVEMENT_RESULTS_20260821.md`。

本轮选择了 CEM ESN-303/5% 与 VMC k=2.2/5%。二者测试均 20/20 成功、hard torque-limit 均 0/20；ESN at-grasp error `8.887 ± 1.206 mm`，VMC `9.634 ± 0.887 mm`，配对差 ESN−VMC `−0.747 mm`，fixture-level 95% CI `[-1.220,-0.274]` mm，seed-level 95% CI `[-1.440,-0.054]` mm。该结果支持在声明的 MuJoCo 物理接触装置包络内，经过 train-only 仿真读出策略改进的 ESN 本轮超过 VMC；不得外推为普遍或 sim-to-real 优势。ESN 平均峰值力略高 `0.149 N`，contact bouts 多 `0.20`，但峰值 torque 低 `0.476 N·m`，这些安全维度需如实并列报告。

原始服务器 JSON：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_contact_apparatus_esn_cem_fair_20260821/fair_results.json`；本地归档 JSON SHA-256：`a088437a9a6cb800f102e0c52610cb92c899b6841f6ec3aeccc317003d8dfaba`。上述 held-out seeds 已消耗，禁止继续用它们调 gain、预算、VMC 刚度、checkpoint 或物理范围。

### 7.2 2026-08-21 跨接触条件验证已完成

新增脚本 `scripts/run_cross_contact_generalization.py`，将上一轮 selected CEM ESN-303/5% 冻结，
改用 `positive_y` 反向进入的 finite-mass `hand_proxy` 椭球探头。校准 seeds `20261101–03`
只验证物理接触存在；validation `20261111–15` 只为 VMC 选择 `k×budget`；held-out
`20261116–20` 只运行冻结 ESN 与选中的 VMC。结果：ESN `0/20`，VMC k=1.0/2% `14/20`；
ESN error `35.951 mm`、VMC `20.182 mm`，误差差 `+15.769 mm`，fixture-level 95% CI
`[+13.753,+17.785] mm`。这轮是明确的负泛化结果：CEM-ESN 在上一轮接触条件有效，但
不能自动迁移到反向掌形接触；不得用这批 test seed 继续调参。协议/结果见
`docs/paper_mpc_benchmark/CROSS_CONTACT_GENERALIZATION_{PROTOCOL,RESULTS}_20260821.md`。

### 7.3 2026-08-21 镜像等变 gate 负结果已完成

为检验能否只靠 ESN 自身的结构约束恢复反向接触，新增了基于 deployable `pose_error` soft-sign
的 `yield_vy/yield_wz` mirror-equivariant output gate。该 gate 不读取力、装置参数、方向标签、
接触时序或 future 信息，但在新 `positive_y + hand_proxy` split 的 validation 上为 `0/20`、
`44.007 mm`，冻结原始 ESN 为 `0/20`、`37.399 mm`，所以 validation 选择原始 ESN。held-out
中原始 ESN 为 `0/20`、`36.445 mm`，VMC k=1.0/2% 为 `16/20`、`18.852 mm`。这条思路已
明确否定，不应继续用同一 test split 调 epsilon、gate channel 或 checkpoint。完整协议/结果见
`docs/paper_mpc_benchmark/ESN_MIRROR_EQUIVARIANCE_{PROTOCOL,RESULTS}_20260821.md`。

### 7.4 2026-08-21 多时间尺度 ESN × 多接触训练已完成

为从 ESN 自身算法下手，建立了 320-unit fast--slow reservoir：相同固定 recurrent matrix、
相同 32-D proprioceptive observation、相同 successful-only mixed-contact BC 数据和 readout
拟合流程，仅将 50% reservoir units 的 leak time constant 设为 0.04 s、其余 50% 设为 0.20 s，
并与单时间尺度 τ=0.12 s 的严格同条件模型比较。不同 teacher budget 的 trace 通过 provenance
换算到统一 5% deployment budget，未增加特权输入。

在 `positive_y + hand_proxy` 的新 validation (`20261311–15`) 中，multi-scale ESN 由 success
优先规则选中：`5/20`, `24.128 mm`，single-scale 为 `3/20`, `25.645 mm`；VMC 独立选中
`k=1.0, 2%`，`17/20`, `18.118 mm`。held-out (`20261316–20`) 中 multi-scale ESN 为
`4/20`, `24.150 ± 2.190 mm`，VMC 为 `18/20`, `18.696 ± 5.262 mm`。匹配 fixture 的
ESN−VMC error 差为 `+5.454 mm`，95% CI `[+2.482,+8.427] mm`；按 seed 聚合 CI 跨零，
但 success 差距为 `4/20` 对 `18/20`。两者 hard torque-limit 均为 `0/20`，ESN 平均 peak
force 与 torque 与 VMC 接近，但 contact bouts 多 `0.60`。因此 multi-scale 只改善了 validation
上的 ESN dynamics，仍未解决跨接触泛化，更不能声称战胜 VMC。完整记录见
`docs/paper_mpc_benchmark/ESN_MULTISCALE_MULTICONTACT_{PROTOCOL,RESULTS}_20260821.md`。

本轮 test seeds `20261316–20` 已消耗，禁止继续据此调 fast/slow time constants、reservoir size、
teacher mix、budget、smoothness、CEM 或 checkpoint。

### 7.5 2026-08-21 多接触 CEM 读出改进：数值优势，但尚需独立复现

针对 §7.4 的“multi-scale BC 仍落后”结果，新建了完全独立的 `positive_y + finite-mass
hand_proxy` protocol。multi-scale ESN 的 reservoir、32-D proprioceptive observation、5% residual
budget 和 FR3 safety envelope 冻结；训练期 CEM 只优化七个 readout row 的有界 log-gain，使用
train-only seeds `20261401–04`。训练期的最佳 checkpoint 为 `8/8` success、`15.712 mm`，但这只
是开发记录，不能作为测试声明。

在全新 validation (`20261411–15`) 中，CEM ESN 为 `16/20`, `17.419 mm`，相比 BC parent 的
`7/20`, `23.625 mm` 被选中；VMC 独立选择 k=1.0/2%，同为 `16/20`, `20.018 mm`。held-out
(`20261416–20`) 结果为 CEM ESN `19/20`, `16.756 ± 1.792 mm`，VMC `17/20`,
`19.979 ± 8.723 mm`。匹配 error 差 ESN−VMC=`−3.223 mm`，但 fixture-level 95% CI
`[-7.534,+1.088] mm`、seed-level CI `[-9.419,+2.973] mm` 都跨零；成功配对为 2 个 ESN-only、
0 个 VMC-only、17 个共成功、1 个共失败。两者都是 `1/20` hard limit；ESN peak torque 高
`1.239 N·m`、contact bouts 多 `0.45`。因此只能称“在本 split 数值领先、至少与 VMC 相当，
但单轮统计不足以断言显著胜出”，不能粉饰为全面安全优势或普遍泛化。完整协议/结果见
`docs/paper_mpc_benchmark/ESN_MULTICONTACT_CEM_{PROTOCOL,RESULTS}_20260821.md`。

本轮 `20261416–20` test seeds 已消耗。若要建立强 superiority claim，下一步必须使用新的独立
replication split（同一预注册候选、无需再改 CEM/VMC 超参数），而不能回看本轮结果调参数。

1. **冻结两轮完成的 held-out 结论，不追测同一 test。**基础 BC 公平预算选择的结论仍是
   “与 VMC 相当”；CEM-ESN 的独立新 split 结论是“在该 physical contact-apparatus envelope
   中优于 validation-selected VMC”。两者均不能再用于挑 ESN seed/gain/budget、VMC 刚度或
   checkpoint。论文必须明确区分 pure BC 与 `BC + train-only policy improvement`。
2. **若需要扩大“ESN 优于 VMC”的适用范围**，另立预注册协议：先固定新的难度轴、候选配置、
   train/validation/test seed 和主要指标，再生成此前完全未见的测试集。可考虑多次冲击或
   torque-limit scaling，但不可从任何已消耗 held-out 结果反推参数或难度。
3. **TOPP-RA 参考源**（接缝①）：vendored `autolife_planning/trajectory/` 已在服务器
   `/tmp/vendor_traj`，把 smoothstep knots 换成时间最优轨迹重验（速度余量≈0 时柔顺层价值）；
4. **难工况边界扫描 + 力域主指标**：撞击强度/执行器弱化（torque_limit_scale）/多次撞击，
   找裸机成功率跌破 100% 的临界点，柔顺贡献 = 边界外推量；
5. **全接管 vs 残差对照**：`torque_takeover`/`torque_takeover_gc` 模式已埋入 env 未跑；
6. **`compliance.py` Protocol Facade**：给 ESN 套论文系统契约外壳 + SHADOW 模式试跑（集成测试）;
7. 真机 FR3（FCI 力矩流）。

## 8. 坑清单（接手者必读，每个都真实踩过）

1. **预算错配**（v1 球击 1/4 的根因）：教师轨迹录制预算 ≠ 学生部署预算 → 动作被静默
   缩放。已加防呆：`run_rollout` 的 `residual_scale` 无默认值必填；CLI
   `--student-budget` 必填；轨迹 npz 存 `residual_budget_fraction`。
   **"部分成功"是最危险的实验状态**——不报错、看起来合理。
2. **scp 部署会静默失败**（expect 脚本 eof 时序）：多次踩到"改了本地没生效、结果对不上"。
   **每次部署后必须 md5 校验**（本地 `md5 -q` vs 服务器 `md5sum`），或用 tar 包 + 校验。
3. **j2 不是侧向关节**（木板 v2 假成功的根因）：该构型下 j2 轴水平，EE 只在 x-z 平面动，
   hand_y 全程 0、板从未被碰。侧向用 **j1（基座偏航）**。教训：**逐帧插桩诊断**
   （hand_y、接触力、q4 随时间）比任何推理都快。
4. **木板几何现值（v2b）**：板 0.18×0.05×0.008、倾角 40°、摩擦 0.25、位置 = 上抬弧
   75/25 混合点 + y0.09。成功带 2-3% 预算。**不要**把板挪近（v3 教训：+0.045 会让张开的
   手指蹭板、毁掉抓取段）。
5. **ESN/MLP 接口差异**：VMC 力矩版的 `act()` 要 `hand_jacobian` kwarg，ESN/MLP 不要——
   分发时按 `hasattr(ctrl, "residual_torque_limits")` 判断。
6. **并行会话会切 git 分支**：本仓库有另一条工作线共用本地仓库。**用户已定规则：
   本支线的所有新工作一律提交在 `paper-mpc-baseline` 上，main 只在结果稳定时合并
   （`git checkout main && git merge paper-mpc-baseline` 或 PR）**。每次提交前
   `git branch --show-current` 确认；发现被切到 main 就先
   `git checkout paper-mpc-baseline` 再提交。工作树里出现的 extraction_*/residual_*/
   whole-body-motion-control 未提交改动属于并行线，不要动也不要顺手提交。
7. **服务器长命令用 nohup + 日志文件**，expect 直连会断（exit 255）。

## 9. 关键文档索引

- `docs/paper_mpc_benchmark/REPORT.md` — 本支线完整报告（v1→v4 演进含撤回记录）
- `docs/RESEARCH_ROADMAP.md` — 全项目历程（FixedWBC→Pink→PaperMPC）与三接缝分析
- `docs/esn_artifacts_v0/direct_esn_fixture23_coverage_20260817/report/FINAL_REPORT.md` —
  主线（FixedWBC 时代）32-seed 报告：ESN −18.2±0.55 vs MLP −9.8±3.57 等
- 主仓库 README / HANDOFF.md — 更早的总体上下文
