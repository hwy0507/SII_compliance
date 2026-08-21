# Handoff — Paper-MPC 名义控制器 × 柔顺层支线（paper-mpc-baseline）

> 更新：2026-08-19 晚 · 分支：`paper-mpc-baseline`（与 main 同步，最新提交 `9c5b85f`）
> 服务器：arm1@192.168.31.70（密码 123456），工程在 `/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark`
> 本地仓库：`/Users/hwy/Desktop/个人/科研/SII科研/compliance/0709`，remote = github.com/hwy0507/SII_compliance

> 续接记录：2026-08-21 已为 `run_paper_mpc_benchmark.py` 加入显式 `--eval-seeds` 多种子评估、逐行 `seed` 溯源和 companion summary sidecar；详见 `docs/paper_mpc_benchmark/MULTISEED_PROTOCOL.md`。MuJoCo 长跑尚未在本地执行，待服务器按该协议补齐 5 个评估种子。

> 2026-08-21 服务器结果已补齐：`docs/paper_mpc_benchmark/MULTISEED_RESULTS_20260821.md`。当前 5 个 seed 在固定 fixture 下完全复现（每格 std≈0），所以这是可复现性检查，不是随机物理扰动置信区间。

> 同日完成 `σ=0.01 rad/s` 关节速度观测噪声评测，结果见 `docs/paper_mpc_benchmark/SENSOR_NOISE_RESULTS_20260821.md`：ESN 50/50，MLP 49/50，裸机 25/50，VMC 50/50（沿用无噪声选优配置）。

> 随机化冲击工况也已完成，见 `docs/paper_mpc_benchmark/RANDOMIZED_IMPACT_RESULTS_20260821.md`。ESN-101/202/303 均 50/50；ESN-303 棒/球均值 9.30 mm，接近并略优于 VMC 9.40 mm，但三 seed 平均仍不全面超过 VMC。Proposed 定位应写为跨工况免调参 ESN 柔顺层，而不是“全面击败 VMC”。

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

### 5.1 当前推荐主结果（2026-08-21 服务器）

在五个 seed、匹配的 stroke/height/start 工况扰动下，PaperMPC 裸机为 26/50；ESN-101/202/303 均为 50/50；MLP 为 48/50；VMC 为 50/50。棒/球抓取误差均值分别为：ESN-101 11.04 mm、ESN-202 10.42 mm、ESN-303 9.30 mm、VMC 9.40 mm。这个结果支持 proposed ESN 的跨工况免调参和 reservoir 稳定性，但不支持“ESN 全面击败 VMC”。完整数据见 `docs/paper_mpc_benchmark/RANDOMIZED_IMPACT_RESULTS_20260821.md`。

## 7. 下一步（按优先级）

1. **多评估种子**：当前所有数字基于单一评估种子——跑 5 评估种子取均值±方差（脚本改一行循环）；
2. **TOPP-RA 参考源**（接缝①）：vendored `autolife_planning/trajectory/` 已在服务器
   `/tmp/vendor_traj`，把 smoothstep knots 换成时间最优轨迹重验（速度余量≈0 时柔顺层价值）；
3. **难工况边界扫描 + 力域主指标**：撞击强度/执行器弱化（torque_limit_scale）/多次撞击，
   找裸机成功率跌破 100% 的临界点，柔顺贡献 = 边界外推量；
4. **全接管 vs 残差对照**：`torque_takeover`/`torque_takeover_gc` 模式已埋入 env 未跑；
5. **`compliance.py` Protocol Facade**：给 ESN 套论文系统契约外壳 + SHADOW 模式试跑（集成测试）;
6. 真机 FR3（FCI 力矩流）。

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
