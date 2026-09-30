# VMC c05 首个长期人手训练回合：独立原始证据审计

`active_long_train_0000` 中，c05 的一个连续 press/hold 受力段满足原门槛：
**1.2643 s 内沿推力方向位移 14.3532 mm**，且任务、strict、放置和释放支撑
标志均为 true。c00 在完全相同的 fixture/seed/MJB 上最大同段位移为 9.09595 mm，
未满足 10 mm。两者均为完整 55 s 的训练搜索回合，开发物理步长 `1e-4 s`。
这不是独立 validation、跨条件泛化、正式 `5e-5 s` 认证或 ESN 成果。

## 已核验的原始证据

使用冻结 v10 源码及本机已完成原始记录，逐文件重算原 audit 声明的 SHA256，
核对 request、plan、fixture 配置、seed、候选 decision、`decode(x)` 与 teacher 参数。
两回合 MJB SHA256 均为
`84f487efd64da42c593459ccc1da4f83e532e1b81acd35c20b3fb4415891425c`。
seed 为 `20460930`，没有修改环境、参数、门槛或历史文件。

独立 NumPy 重算 550000 个物理子步的 stage-waypoint tracking RMSE、实际广义
执行器力矩峰值、末端线速度峰值与 55 s 时长。重放 VMC 原请求、内部状态和共享
action filter；最大数值误差 c00 为 `1.38778e-17`，c05 为 `2.16840e-19`。
原请求与过滤 action、实际执行力矩分别核验，不混用 action7 和电机力矩。
完整动力学、估计负载观测器和 FK/WBC 未重新求解。

person schema2 原始记录逐物理步与物理轨迹时间/步长对齐。独立向量分段算法以
`force > 0.05 N` 且整个子步位于 `[start, start+press+hold]` 为条件，从每个连续段
的首个受力位置重新建立原点，沿 `-fixture.axis` 投影。任意不满足条件的样本立即
断段；没有跨 gap 累计，也没有使用 withdraw 位移。独立分段结果与保存的全部
`person_window_runs` 在 `1e-10` 绝对容差内一致，唯一通过段为索引 83。

## 结果与代价一并保留

| 指标 | c00 初始候选 | c05 候选 |
|---|---:|---:|
| 原 audit 录取 | 否 | 是 |
| stage-waypoint RMSE (mm) | 40.0931 | 56.0386 |
| 实际执行器峰值力矩 (Nm) | 48.3783 | 45.0859 |
| 末端峰值线速度 (m/s) | 0.0616024 | 0.0616024 |
| 同段最大有符号位移 (mm) | 9.09595 | 14.3532 |
| 最长 press/hold 连续受力段 (s) | 1.2516 | 1.2643 |
| 整回合人手接触峰力 (N) | 112.778 | 184.671 |
| 整回合人手接触冲量 (Ns) | 42.4428 | 32.0391 |
| press/hold 接触冲量 (Ns) | 39.0137 | 30.0804 |
| 外部最大穿透，保存元数据 (mm) | 0.0225861 | 0.0327918 |
| release 阶段开始 (s) | 35.92 | 42.12 |
| retreat 阶段开始 (s) | 36.44 | 42.64 |
| 整回合力阈值接触段数量 | 1412 | 7891 |
| press/hold 力阈值接触段数量 | 928 | 6998 |

c05 合格段的物理区间为 **11.0004–12.2647 s**，共 12643 个子步，距 retract
开始 16.79585 s 尚有余量。该段最小力 4.12695 N、最大力 10.3395 N，冲量
8.85807 Ns；相比原门槛，时长余量 0.8643 s、位移余量 4.3532 mm、最小力余量
4.07695 N。这里只报告余量，不据此放宽门槛或宣称扰动后仍可靠。

图只显示两个候选各自最长的一个连续受力段；它们同时是本例最大的同段让位段。
图中的段内最大力不能替代上表整回合峰力，尤其 c05 的整回合峰值 184.671 N。

## 结论边界

- 同段受力时的有符号位移是运动学证据，不能证明相对 nominal 动作的因果让位；
  本次没有无推力反事实对照。
- c05 整回合仍有很多碎接触段。存在一个 1.2643 s 合格段，不等于整段人手交互
  持续平顺，更不等于真实人机交互安全认证。
- c05 改善了同段位移、录取结果和电机峰值力矩，但跟踪 RMSE、接触峰力和完成
  时间均变差。不能只呈现成功标志或较低电机力矩。
- 接触力从已有每物理子步 force 记录独立聚合，不是重新求解接触动力学。
  最大穿透仅核对 hash 绑定的 evaluator/audit 元数据；现有原始轨迹没有完整逐
  子步 contact distance，不能称为独立穿透重算。

## 复用与产物

原始服务器主目录按 campaign 归档约定为
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v10/`。
本次子审计只读本地缓存；随后主agent已逐文件核验共享审计JSON/分段NPZ、图/PDF/完整点、
源码和测试至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_1138/evidence/`。
该检查点共49文件，另含全部27项BO前缀审计与历史辅助证据。图已再次视觉检查。
归档保留当时报告版本；本段是核验完成后的地址补充，不改审计数据。

本地研究根目录：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/`

- 工具：`tools/teacher_bank_person_success_audit_20260930.py`；命令参数为
  `--run <v10目录> --output <全新目录>`。
- JSON 与全部独立分段 NPZ：`outputs/teacher_bank_person_c05_success_review_20260930/`。
  `review.json` SHA256：
  `dab55a4eba144668891332ff6c9a4dbd4415ae8a2c21e7cce7e3acb5725ba2a7`。
- 图与完整绘图点：`outputs/teacher_bank_person_c05_contact_plot_20260930_v2/`。
  PNG SHA256：`f72a50036b5195789304926d0db440f971a3f84a9c876882e011fd69f4cec78d`。
- 3 项针对断段、withdraw、方向和严格力阈值的单测通过；实际双回合审计完成。
  单线程、RLIMIT_AS=1 GiB，峰 RSS 239628 KiB。所有动态积分入口均拒绝调用。
