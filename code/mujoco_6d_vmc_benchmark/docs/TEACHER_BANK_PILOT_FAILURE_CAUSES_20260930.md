# v8 三类训练 pilot：失败归因与证据边界

本报告只读复查 `teacher_bank_three_domains_20260930_v8` 的九条完整训练轨迹，不启动 MuJoCo、不改冻结源码、不修改任何录取 gate。每类只有 `train_0000` 一个环境，每个方法一次；它们不是跨条件泛化结果，也不是正式 `dt=5e-5` 验证。九条均为开发 `dt=1e-4`、55 s、25 Hz actor、550000 个物理子步，MuJoCo 3.11.0。长时场景为 **person，不是 rod**。

主归档位置（由已有归档回执记录，本次离线分析没有重新连接服务器验证）：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v8`

下面所有 `pilot/<category>/<method>/` 均相对此目录。冻结源在 `source/`。精确 fixture、seed、控制器参数保存在各 case 的 `request.json`，实际 MuJoCo 配置在 `rollout.xml` / `rollout.mjb`。本报告不把训练 fixture 的参数搜索当作固定测试成绩。

## 1. 可复算入口与原始文件核验

脚本：`tools/teacher_bank_pilot_failure_causes_20260930.py`。只依赖 Python、NumPy、已保存文件；不导入仿真器。它逐个重算九条轨迹的物理子步 RMSE、力矩峰值、速度峰值，校验 `audit.json` 中列出的所有文件哈希，并保存原 metadata、事件、采样时刻、接触统计、几何属性和完整 hash 清单。

仓库 benchmark 目录中运行，输出必须在原 run 之外且不得覆盖：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python tools/teacher_bank_pilot_failure_causes_20260930.py \
  --run outputs/teacher_bank_three_domains_20260930_v8 \
  --output outputs/teacher_bank_pilot_failure_causes_20260930/recomputed.json
```

本次机器可读结果为 `outputs/teacher_bank_pilot_failure_causes_20260930/analysis_v2.json`（第一版 `analysis.json` 也保留，v2 增补 XML 几何和掉落时段采样）。脚本、本报告和JSON共享根为：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`

根下保留 `tools/`、`docs/` 和 `outputs/` 相对路径，逐文件SHA核验后发布；对应本地checkpoint的 `archive_receipt.json` 记录已核验路径。

| 文件 | SHA256 |
|---|---|
| 本次复算脚本 | `83efc650f94f66e1e8af2f8f484f09faa26835f75ed47a8640664daa85a3d74e` |
| analysis_v2.json | `c6d3469bea9113edf7416697d31950921b7d2fbf44da3f5016c2c74d6d020986` |
| v8 plan.json | `671d5ada576fa14cc27fdcea842afd041a6b03cbaa4268c2bb4cd1a13107fea4` |
| v8 fixtures.json | `e05155a835d59f235b75a95a106194bd0e6dab618c0d772fa3e0ad97a079693f` |

九条原 audit 指向的所有文件 SHA 均匹配。由 raw float32 子步向量重算三项指标，与原 audit 的差：力矩和速度全为零，RMSE 最大绝对差 `6.94e-18 m`。这验证保存指标可复算；不代表每项任务/接触定义都有足够原始字段可追溯到更严格的新 schema。

## 2. 九条结果

“录取”是该冻结 v8 的训练接触谓词、task、strict 等共同判定；impedance 即使录取也属于 baseline 证据，不是 VMC action7 蒸馏标签。三个类别种子分别为 `20260930 / 20360930 / 20460930`。

| 场景/方法 | task / strict / 录取 | RMSE (m) | 峰值力矩 (Nm) | 峰值速度 (m/s) | 外部穿透 (mm) | 直接拒绝原因 |
|---|---|---:|---:|---:|---:|---|
| corner / VMC | 是 / 是 / 否 | 0.036140 | 48.160 | 0.061602 | 0.009486 | 接触中上抬 86.6 µm，小于 100 µm |
| corner / admittance | 否 / 否 / 否 | 0.039900 | 50.927 | 0.061602 | 0.011124 | 接触谓词通过，任务停于 load_transfer |
| corner / impedance | 是 / 是 / 是 | 0.047988 | 45.612 | 0.153140 | 0.060992 | 唯一录取 pilot，仍是 baseline 证据 |
| ball / VMC | 否 / 否 / 否 | 0.064667 | 47.935 | 0.087333 | 0.117442 | 放开后物块滑落，接触/反弹已通过 |
| ball / admittance | 否 / 否 / 否 | 0.046278 | 48.659 | 0.097070 | 0.138606 | 放置位置偏差，未进入 release |
| ball / impedance | 否 / 否 / 否 | 0.032666 | 41.637 | 0.085114 | 0.166234 | carry 收敛慢，55 s 内未放置 |
| person / VMC | 是 / 是 / 否 | 0.040093 | 48.378 | 0.061602 | 0.022586 | 单次连续接触最大位移 9.744 mm < 10 mm |
| person / admittance | 否 / 否 / 否 | 0.046350 | 49.701 | 0.061602 | 0.035704 | 接触分段谓词失败，任务也未完成 |
| person / impedance | 是 / 是 / 否 | 0.031941 | 44.866 | 0.120995 | 0.050618 | 接触高度分段，连续让位谓词失败 |

九条均完整执行，无 `abort_reason`，外部穿透都小于 0.2 mm；力矩幅值比小于 1，变化率比最大约 1.000000164（float32 重算误差，在审计 1e-3 容差内）。因此不能将 ball 三次任务失败解释为安全中止。

## 3. Ball：失败发生在哪个环节

同一球的 launch 为 5.885468 s，但不同控制器的任务阶段不同。以保存的 `task_events` 判断碰撞所在区间，不能直接用最近的 rollout 后采样行阶段替代。

| 方法 | 第一次球接触 (s) | 接触时阶段 | 后续状态 |
|---|---:|---|---|
| VMC | 5.9759 | carry（5.9600 开始） | 24.48 load_transfer；42.32 release；42.84 retreat；物块滑落 |
| admittance | 5.9783 | lift（7.16 才进入 carry） | 12.08 load_transfer，此后一直未释放 |
| impedance | 5.9626 | carry（5.12 开始） | 53.88 才进入 load_transfer，剩余 1.12 s 不足以完成 |

三者都发生真实接触并反弹，接触总时长依次 1.3、1.2、1.0 ms，每条均有三段微接触。没有证据表明碰撞瞬间物块被直接打掉：碰撞附近物块与手距离没有跳变；随后 0.5 s 物块 z 范围依次为 0.54355–0.54758、0.53787–0.54185、0.55015–0.55351 m。

**VMC 的直接失败为晚期放置支撑不足。** 42.32 s 释放时物块中心 `[0.566905, -0.306054, 0.546160]` m，XY 目的地偏差 15.630 mm；`release_supported=true` 仅说明当时有支撑接触。XML 中桌角台面 x 范围 `[0.57, 0.73]` m、顶面 z=0.52 m、物块半宽 0.025 m：物块中心已在左边缘外侧约 3.095 mm，虽仍部分覆盖台面。42.84 s 物块降至 z=0.431602 m；43.48 s 起落在下方桌面，最终目的地 XY 偏差 74.933 mm。该几何/轨迹支持“边缘部分支撑，释放后不稳定”的机制，但没有同参数无球对照，不能声称碰撞是唯一原因。

VMC 约 6 s 的位置误差陡增主要对应 lift→carry 的 waypoint 切换：目标从 `[0.54,-0.19,0.665]` 转到 `[0.560,-0.330,0.670]` m，目标跳变约 141.5 mm。误差由约 9.8 mm 跳到约 145 mm，**不能解读为球把末端瞬间推走 145 mm**。这是完整任务 RMSE 中含阶段参考跳变的语义问题，不是修改 RMSE 或移除该段数据的理由。

**Admittance 是持续放置偏差。** 15–55 s 的最小 task 位置误差 18.868 mm，始终高于共享 release readiness 的 12 mm；15/25/40/55 s 误差约 19.671/27.816/32.789/45.737 mm。物块随持物末端逐渐偏移，直到 55 s 仍未进入 release。可确认位置条件已经阻塞释放；没有充分证据将具体原因归结为某个观测器偏差或 M/D/K 参数，也不能把未释放时物块变低直接说成已脱手。

**Impedance 是慢收敛导致任务超时。** carry 持续 48.76 s，误差在 15/25/40 s 约 21.415/18.356/14.692 mm，直到 53.88 s 才切换 load_transfer。其 action7 为零是该 baseline 使用 Cartesian 力矩后端的架构约定，不是控制器未工作；实际力矩有完整记录。

## 4. Person：有宏观让位，但不满足冻结的连续接触录取条件

人手开始 9.205159 s，press 2.176730 s，hold 5.413959 s，16.795848 s 开始回撤。fixture axis 为 `[0.955489,0.295028,0]`；该人体装置的实际推向为 **负 axis**，不可按 rod 的正 axis 判断。

| 方法 | 首次接触 (s) / 阶段 | 全程接触时长 (s) / 段数 | 最长连续段 (s) | 单连续段最大位移 (mm) | 回撤前宏观有向让位 (mm) |
|---|---|---|---:|---:|---:|
| VMC | 10.6808 / load_transfer | 6.5556 / 1412 | 1.2516 | 9.744 | 27.780 |
| admittance | 10.7047 / load_transfer | 6.4092 / 2774 | 0.1838 | 1.797 | 27.313 |
| impedance | 10.8162 / carry | 6.3343 / 3976 | 0.0074 | 0.0369 | 5.492 |

宏观让位用 4 ms hand 样本计算：取首次接触前最后一帧为原点，直到回撤开始，求 `dot(hand-origin, -axis)` 最大值。VMC 和 admittance 有明确的约 2.7 cm 同向运动，不能写“完全不会让位”。它横跨多个接触片段，也没有无推力对照，不能单独证明全部位移由外推导致，更不能追认连续接触录取通过。

接触分段确实非常密集：press/hold 窗口内完整段间隙中位数，三个方法均约 0.1 ms；90 分位依次为 0.4/0.2/0.1 ms；间隙≤1 ms 的比例为 93.63%/98.85%/99.97%。这里“间隙”指 **force>0.05 N 谓词未成立**，不能等同于肉眼可见脱离，也不能仅据此断言是数值假象。

恢复方面，VMC 于 35.92 s 释放、36.44 s retreat，任务成功；impedance 于 46.20 s 释放、46.80 s retreat，任务成功；admittance 到 55 s 仍处 load_transfer，位置误差 25.958 mm > 12 mm，故它不仅是接触统计不通过，也确有任务未恢复完成。

原研究目标是“受到长期外推时让位并恢复任务”，并不是要求无限时长不间断接触。但注册的训练接触谓词仍须原样记录；本报告不修改 v8 结果，更不修改 v10 gate。v8 只保存 schema1 连续接触摘要和 4 ms 位置，缺少 schema2 所需每个物理子步的定向轨迹；**4 ms 宏观让位不能追溯认证 schema2 的连续、同向、同一次接触让位**。新日志版本解决的是可验证性，不可将旧失败挑掉或改成成功。

## 5. Corner 与后续可检验假设

VMC 虽任务成功，但符合接触的上抬最大仅 86.600 µm，未满足注册的 100 µm 门槛；不宜写为完整展示了“蹭厚桌角”。Impedance 是唯一录取 pilot，但其 12.8117 s 总接触分成 18840 段，只有一段约 5 ms / 上抬 0.231003 mm 满足条件。这足以说明原谓词通过，却不足以宣称宏观连续、平顺的攀边表现。

本轮明确了三个可继续测试的控制器假设：VMC 放置需要改善释放前对中/稳态；admittance 需要避免让位后的长期静差和漂移；impedance 需要提高持物 carry 的收敛效率。它们是待固定预算验证的假设，不是已证明的唯一病因。Ball 的早期冲击响应、person 的宏观让位与最终恢复应分开分析；单次碰撞后的最终失败不能替代中间机理诊断。没有对 rod、其他 fixture、ESN/MLP 优劣或泛化能力作结论。

## 6. 冻结源与证据 SHA256

| v8 source 下文件 | SHA256 |
|---|---|
| tools/teacher_bank_rollout_20260930.py | `8a5f9be532e88287b0acf27b83e92c4645c484e627b6c508dbd6be62c12456a2` |
| tools/teacher_bank_exposure_20260930.py | `8140ac7682802575e469a6afb0881b06a39eeffd225719172a5d8b6046375a52` |
| tools/teacher_bank_classical_20260930.py | `b218373fb7f6ba1d0b85820554fe4b77a883d114e0f7cc1a15f46b3099d47be3` |
| scripts/validate_office_apparatus_v5_20260917.py | `9450355dad81ba983e09d3d8b601a4cb69b08ca8a7c2ac590819e702f4ffe7a0` |
| scripts/physics_substep_metrics_20260923.py | `2932ba97724c476c80b8f93041de3b1f0107fa24c07e1fc2f9030e96ffa4f598` |
| scripts/office_task_v4_20260917.py | `255ce3443ecfb46d4e88797f3b5bb78a864c089e395c097aa86e203533852d0f` |

下面 `audit.json` 哈希锁定其 `files_sha256` 原始文件清单；本次 JSON 同时保存逐个重新计算的完整清单（含 request、rollout NPZ/XML/MJB、execution_chain、teacher_internal、exposure、substep_metrics）。

| pilot case | audit.json SHA256 |
|---|---|
| passive_corner/vmc | `ddb6d90617668207e7516d5b15ee1e91f2916c07ecc1aaee5b7ee2190e50ff20` |
| passive_corner/admittance | `48cbd326e962988097ee7a33373896461a5300c3b29017ef73d7876848d15ae4` |
| passive_corner/impedance | `7537ae3058126eb36b45a71500037c762168a0cfa3d8a8c1400d22a30cf22bc6` |
| active_short/vmc | `8e0a96cfa69ee3d44a9b8755a061c04f0cf1414ef6ed4aab8769045844f149e1` |
| active_short/admittance | `3d9affc68e366f9c67e6ac01b2e39083e911527c3c7f341ef4152c936542f499` |
| active_short/impedance | `bb0dccfd6f1b845bda33d1c497a780c1df9a81636735673801d4cce7212164b6` |
| active_long/vmc | `1dd55ca4d6d777b99e681a021a66d743d24358469f5e5b8f2cace07ae31efcb7` |
| active_long/admittance | `7dcbc60ddaf8ad1ced9269f990ab4c67a651beb84d6cb4572e3a10ef3b499e85` |
| active_long/impedance | `ae0cc2bd19da57b54bb366cb3c159b7557ed69f90ec813020ced776bc0ac210f` |
