# v10 首两条 VMC 合格搜索轨迹：只读复核

复核对象为 `teacher_bank_three_domains_20260930_v10/search/active_short/vmc/c00/{337,671}`。两条均为训练搜索 anchor，**sphere anchor 0 仍失败；参数银行尚未锁定；正式 collection 数量仍为 0**。不能据此宣称整个 active_short 场景、三类场景或 ESN 泛化已成功。

共享原始 run：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10`。本次复核从本地对应目录只读完成，没有运行仿真、修改原 audit 或 gate。
新增review、脚本和本报告归档根为
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0603/evidence/`，
根下保留outputs/tools/docs相对路径，逐文件SHA核验后发布；本地同名checkpoint的archive_receipt.json记录核验路径。

| 指标 | anchor 337 | anchor 671 |
|---|---:|---:|
| 撞击物 | ellipsoid | capsule |
| task / strict / eligible | 全通过 | 全通过 |
| 物理子步 RMSE (m) | 0.0335686474 | 0.0333544288 |
| 峰值执行器力矩 (Nm) | 48.8491211 | 48.5033646 |
| 峰值末端线速度 (m/s) | 0.0616024432 | 0.0869868469 |
| 外部穿透 (mm) | 0.125381883 | 0.115965218 |
| 力矩幅值比 | 0.561484151 | 0.557509938 |
| 变化率比 | 0.999999791 | 1.000000164 |
| 首次撞击时刻 (s，evaluator 时间) | 11.2774 | 9.3313 |
| 碰撞时任务阶段 | load_transfer | load_transfer |
| 接触累计时长 (ms) | 0.8 | 1.2 |
| 碰撞合力峰值 (N) | 1368.311984 | 1350.488071 |
| 碰撞冲量 (Ns) | 0.454328051 | 0.716925497 |
| retreat 开始 (s；完成时间代理) | 23.76 | 23.16 |

碰撞力峰值是物理子步记录的短时接触合力，不能与关节力矩混为同一指标；约 1.35 kN 峰值必须保留报告，不能因为执行器力矩合规就将其描述为低接触力。没有因此增删 gate。变化率比 1.000000164 属原审计允许的 float32 重算容差（1e-3），未放宽约束。
当前门槛通过也不证明真实部署安全：冲击峰值对接触模型和物理步长的敏感性尚未验证，且执行器力矩不等同于外部冲击造成的全部结构载荷。这里保留开发分辨率的实际记录，不更改碰撞物、接触参数或门槛来降低报告峰值。

## 独立计算与复用审计的边界

1. **独立文件与指标检查**：逐个重算原 audit 清单中的原始文件 SHA，全部匹配；使用独立 NumPy 公式从 550000 个物理子步的 `dt/error/qfrc_actuator/twist` 重算三项指标。与原 audit 的最大差为 RMSE `6.94e-18 m`，力矩与速度均 0。两条均完整 55 s、1375 个 actor 动作、13750 个 exposure bucket。
2. **复用冻结 v10 runner 做重放复核**：VMC 内部 offset/velocity/滤后估计力、原始请求 action、shared filter 输出、filtered action 标签及再次执行标签的重放误差分别为 `3.47e-18`、`1.39e-17`。这属于同实现重放，不冒充独立控制器实现验证。所有输出写到新目录，原 audit SHA 前后未变。
3. **时间/观测对齐**：25 Hz 时间、q 与 pre-action neuron_qpos、连续 q/dq 与前一帧 post-state 检查最大差为 0；550000 子步完整单调，曝光桶区间/时长与物理轨迹绑定通过。未独立重建第一帧 dq、运动学或估计 wrench。
4. **接触/反弹证据**：保存的连续接触段峰值与 evaluator ball event 峰值一致；已有 contact 条件通过。额外从 `rollout_ball_detail.npz` 的碰后 0.12 s 内非接触速度样本独立找到反向速度，沿 fixture axis 最小值分别 `-0.268837792`、`-0.248685875 m/s`，每条有 109 个窗口内样本。入射投影 `1.201566937`、`1.627997531 m/s` 来自保存的 evaluator incoming metadata；没有伪称由完整的接触前物理速度重新求得。

首次接触时间在 exposure 和 evaluator 之间有一个物理子步的时间戳约定差（0.1 ms），碰撞阶段统一由 `task_events` 时间区间确定。两个成功 anchor 在 load_transfer 才受撞；sphere anchor 0 的失败不能据这两条消除，撞击阶段差异也必须在后续分层分析保留。

## 复算入口与 hash

脚本：`tools/teacher_bank_search_success_audit_20260930.py`；独立指标 helper：`tools/teacher_bank_pilot_failure_causes_20260930.py`。使用原运行 Python 环境，输出目录必须全新且在原 run 外：

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python \
  tools/teacher_bank_search_success_audit_20260930.py \
  --run outputs/teacher_bank_three_domains_20260930_v10 \
  --output outputs/teacher_bank_v10_first_success_review_recomputed
```

产物：`outputs/teacher_bank_v10_first_success_review_20260930_v2/review.json`、`337_replay_audit.json`、`671_replay_audit.json`。初次普通 Python 运行缺少 scipy，未进入审计，仅留下空的无 v2 后缀目录；使用原 campaign 环境复跑成功，未覆盖失败目录。

| 文件 | SHA256 |
|---|---|
| 复核脚本 | `1087b6535393fa1b0f19104fd7959bb1c957c24500844371c8eefd68ac54bebf` |
| 独立 helper | `83efc650f94f66e1e8af2f8f484f09faa26835f75ed47a8640664daa85a3d74e` |
| review.json | `c5bfae656205ec7b99a393eb3bcd537a8fef6e000ace475643111a7e6b91f2db` |
| anchor 337 原 audit.json | `24b04a60dd1b702972926ab6eb4614232aa96ad7f9169c52eb5b0a5afd106033` |
| anchor 671 原 audit.json | `1e054a26aa14ab06e998171b76d502d9405d451b84491bc916a03bf66c428bc6` |

完整原始文件、request、seed、模型、冻结 runner 与 source hash 清单均在 review.json。此结果只证明两条开发分辨率训练搜索轨迹满足当前门槛且保存证据可复算；不是正式 dt=5e-5 复验、未见条件测试或锁定参数银行的比较结果。
