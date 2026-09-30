# active_short VMC c05：冻结搜索的只读训练诊断

本报告解释同一训练环境下 c05 的退化，不修改采样器、controller、环境、gate、预算或银行选择。没有运行 MuJoCo dynamics，没有读取 validation，也没有重新调参。所有结果为 dt=1e-4 开发设置，不能当作正式 dt=5e-5 通过。

## 证据和复现

- 已有原始运行归档：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10/`。本报告实际读取本地同名缓存；新诊断JSON及工具已逐文件核验共享至 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_1124/evidence/`，其中保留归档时报告版本；本句为核验后补充，不改原诊断结果。
- 本地审计：`outputs/teacher_bank_bo_candidate_audit_20260930_v1/review_v2.json`，SHA256 `8c665ea44fa9378eac3ccc1771cb0532840dedf7a2574ad626f25bc5f60cc43e`。原始第一版 `review.json` 保留，v2 补齐完整 frozen source manifest 核验和指标来源声明。
- 复现工具：`tools/teacher_bank_bo_candidate_audit_20260930.py`；运行时 Python 3.11.15、NumPy 2.4.6、SciPy 1.17.1。单线程、RLIMIT_AS=1 GiB，峰值 RSS 105156 KiB。
- 核验源清单全部 hash，以及 9 回合原始文件 SHA；同一 anchor 的场景 physical hash、seed、编译模型 hash 在 c03/c04/c05 间一致。JSON 保存完整 hash、参数、事件与阶段轨迹统计。
- RMSE、峰值力矩、峰值速度来自既有 frozen audit/rollout 的物理子步汇总，本报告验证其原始文件 hash，**没有在本报告重算这三项指标**。本报告独立计算 acquisition、动作和阶段统计。

复现命令（在 benchmark 根目录，输出必须为尚不存在的新文件）：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
 /home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python -B \
 tools/teacher_bank_bo_candidate_audit_20260930.py \
 --run outputs/teacher_bank_three_domains_20260930_v10 \
 --output outputs/teacher_bank_bo_candidate_audit_20260930_reproduction/review.json
```

## c05 为什么被提出

严格使用当时的 history 前 5 项，没有用 c05 的失败结果回填 surrogate。seed=20261035，512 个 Latin-hypercube 候选中 index 464 精确重现原 decision（包括全部 7 个坐标）。当时仅 c03/c04 两个可行 objective 观测。

| acquisition 分量 | c05 |
|---|---:|
| constraint posterior mean / std | 0.97395 / 1.66825 |
| 预测可行概率 | 0.27967 |
| objective mean / std | 0.89160 / 0.05596 |
| EI | 0.0206915 |
| 显式探索项 0.01×std | 0.0005596 |
| 总 acquisition | 0.00594332 |
| 距离 c03 / c04，7D unit cube 欧氏距离 | 1.51541 / 1.49077 |

全池预测可行概率范围为 0.03463–0.58133。c05 是可行概率与不确定 objective 改进共同作用下的探索点，不能把它描述成 BO 已确认安全的候选。EI 本身包含不确定性；其值远大于显式探索项，不应把选择简单归因于额外的 0.01×std。constraint 是失败 anchor 数和失败标签数构成的类别代理，并非真实物理违约幅度。一次探索失败不能推出 BO 整体失败。

## 参数和闭环表现

| 参数 | c03 | c04 | c05 |
|---|---:|---:|---:|
| 平移 Kxy / Kz | 1188.68 / 2325.21 | 1474.38 / 1582.76 | 265.97 / 701.02 |
| 平移 Dxy / Dz | 57.73 / 91.57 | 67.02 / 78.74 | 12.66 / 23.32 |
| velocity readout weight | 0.15346 | 0.15694 | 0.49825 |
| offset gain | 1.54161 | 1.21233 | 1.86742 |
| 三个训练 anchor 合格数 | 3/3 | 3/3 | 0/3 |

下表次序为 anchor 0 / 337 / 671：

| 候选 | RMSE (mm) | 峰值力矩 (Nm) | 峰值速度 (m/s) | 原始 action 步间差 RMS |
|---|---|---|---|---|
| c03 | 37.66 / 33.35 / 33.02 | 45.00 / 44.76 / 44.82 | .0996 / .0616 / .0850 | .00993 / .00807 / .00831 |
| c04 | 36.59 / 33.13 / 32.90 | 44.91 / 44.87 / 44.51 | .0917 / .0616 / .0875 | .00922 / .00783 / .00777 |
| c05 | 40.57 / 36.64 / 34.59 | 49.78 / 52.34 / 54.38 | .1061 / .0645 / .1128 | .18644 / .18060 / .12586 |

c05 同时改变多个参数。低平移 K/D、更高速度读出权重和更大动作步间变化的共现是**关联证据**，不是某一个参数导致失败的因果证明。原始 action 的大变化也不等于真实电机输出越限；共享过滤器、执行器幅值/变化率约束仍照常运行。

三个 c05 回合均触发要求的球接触，完整运行 55s、没有 physical abort；外部穿透分别 .18838 / .06245 / .17363 mm，均不超过 .2 mm。其失败标签均为 task_failed / evaluator_strict_failed，而非没有碰球或外部穿透失败。

## 两类明确不同的任务失败

1. **anchor 0 和 337：无法完成 load_transfer。** 最终仍处于该阶段。该阶段保存的所有位置误差都不小于 12 mm，ready 累计时间始终为 0；位置误差中位数 18.78 / 17.62 mm。多数时刻的速度和姿态门槛满足，因此不能把失败简单说成“被球撞后立即失控”。末尾 10s 原始 action 步间差 RMS 仍为 .20679 / .17330，WBC scale 分别约 .892–.911 / .906–.927，显示持续残差调节与未消除的位置偏差。
2. **anchor 671：退让完成，但 release_supported=false。** 31.56s 进入 release，32.68s 进入 retreat；最终末端距 retreat 目标仅 3.52 mm，物块 xy 距离目标 13.44 mm。它不是一直卡在 load_transfer，也不是末端未回位。严格成功条件要求释放切换瞬间的支撑真值为真，保存的 release_supported=false 已足以使 placement_complete=false。代码允许本体估计 load-change 支路触发释放，因此进入 release 并不保证那一刻真实受支撑；本次仅确认保存事件和判据，没有独立重算接触支撑或证明误触发的单因素原因。

阶段统计有采样边界限制：stage/post-state 在物理步后保存，而 task error/ready 来自步前。特别是阶段切换样本不能作为逐样本 gate 的独立重放；对于 anchor 0/337 长时间停留、ready 始终为零的结论不依赖切换样本。

## 对冻结选择规则的含义

当前规则先比较失败 anchor 数，再比较最大失败标签数代理，再比较原 score。原 score 为 `RMSE/.05 + .3*torque_ratio + .1*retreat_time_proxy/55`；action delta RMS 仅报告，不参与 score。因此 score 优化不等价于动作平滑优化。

c04 的原平均 score .88825 优于 c03 的 .89678，两者均 3/3；c05 为 0/3，不应替换已合格候选。本报告不改变该规则或冻结 teacher_bank。潜在的更平滑 readout、不同先验或采样机制只能作为以后独立注册的新研究，不从本次三个训练 anchor 推出跨条件泛化或成功数据规模。
