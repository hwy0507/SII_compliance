# 特化场景 unseen108 正式矩阵最终状态（2026-10-31 18:07 CST）

之前各条“资源阻塞／0/108”记录均为正式启动前的历史快照。当前正式矩阵已经完成，不需要也不得在同一登记目录重复启动：

- 目录：`code/mujoco_6d_vmc_benchmark/outputs/contact_yield_locked_unseen108_20261031_v3/`。108/108 回合完整结束（2026-10-31 07:35:21–09:42:23 UTC）；`execution.json` 保留运行器状态 `complete_pending_independent_review`。独立复核文件状态为 `verified_complete_isolated_unseen_matrix`，重放覆盖108/108，actor/filter最大误差均为0。
- 共同双成功参考 `T_ref=8.92 s`。汇总 ESN：Task35/36、Strict32/36、双成功SPT0.7913、平均峰值力矩42.37Nm、机器合规35/36；MLP：36/36、25/36、0.7548、41.70Nm、31/36；RNN：36/36、32/36、0.7614、42.51Nm、36/36。人舒适度NA（没有人体力/接触通道）。
- MLP棍推Strict仅4/12、机器合规7/12；ESN `corner_unseen_03` seed2026102801为唯一同时Task/Strict/机器失败格，外穿透4.613mm。总计19个至少一项失败的格全部留在原始目录和统计分母。
- 结果报告、逐scene/seed表、SVG图、哈希和失败表：`docs/evidence/contact_yield_final108_20261031/REPORT.md`。旧office/composite108历史结果未改写。此测试是登记的插值条件，不是广义OOD；终态保持基于13个25Hz采样状态/0.48秒，不声称逐物理子步连续保持。
- 紧凑证据和registration/execution/review三份核心收据已在服务器独立目录逐项SHA256核验：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/contact_yield_unseen108_20261031_v3/`。约10.09GB（9.39GiB）的2379个raw文件未传输：自动审批未授权该全量大包；它们仍保留在本机原始输出目录。详见 `docs/evidence/contact_yield_final108_20261031/ARCHIVE_RECEIPT.json`。
- 本地和服务器三份核心来源hash：registration `e4f3b353eb45c4b672fc666154b9a90628bea604964f1e714f3ace4d9e5b88b6`；execution `b45b51cad36c30324e1d9f1e906bc2a7dfbaa8a361435e27c0e8e0c6371e0e5c`；FINAL_REVIEW `bb24b9660364565a5d8ac4bfb4acb256d1a11a0a5cb0a699b5bf42bc67dc2afa`。
- 不要运行旧v1/v2登记，不要重跑v3；当前无在途MuJoCo作业。原始结果完成，现进入文档/Git发布收尾。

---

## 2026-10-31 — 恢复后资源阻塞再次复现

- 预检 v2 收据 `docs/evidence/CONTACT_YIELD_FINAL108_RESOURCE_PREFLIGHT_20261031_v2.json`（SHA256 `f14cc179888c49da76cde97f81ecdfbfae0d3e460d5b3ee44edde654395f8f13`）仍在 `memory.max` 断言处拒绝，`physics_calls=0`。
- final108 仍0/108；当前未有物理进程，服务器无 final108 归档。该资源阻塞在恢复后的连续多轮保持不变。

## 2026-10-31 — final108 静态 readiness

- adapter/evaluator/resource guard 编译与CLI检查通过，静态收据 `docs/evidence/CONTACT_YIELD_FINAL108_STATIC_READINESS_20261031.json`，`run_called=false`、`physics_calls=0`。
- `execution.json`仍不存在；只待合规资源scope，不改变冻结模型、条件或门槛。

## 2026-10-31 — adapter 控制流回归复核

- 零物理控制脚本重新通过：108行有序调度、重复启动拒绝、基础设施失败保留前三条收据、失败重启拒绝、107行复核拒绝；登记 SHA 未漂移。收据 `docs/evidence/CONTACT_YIELD_FINAL108_CONTROL_RECHECK_20261031.json`，`physics_calls=0`。
- 该审计不提供物理指标；资源前置仍不合规，final108仍0/108。

## 2026-10-31 — goal 恢复后当前状态审计

- 新收据 `docs/evidence/CONTACT_YIELD_GOAL_CURRENT_STATE_AUDIT_20261031.json`：登记检查通过，9/9模型来源绑定一致，30/30 teacher qualified。
- final108登记108格但仍无`execution.json`，没有物理指标；资源仍为Chromium scope、affinity/cpuset 0–23、主机swap余236 KiB、user systemd不可用，未启动仿真。

## 2026-10-31 14:59 CST — goal 逐项完成度审计

- 新增逐项权威审计 `docs/evidence/CONTACT_YIELD_GOAL_REQUIREMENTS_AUDIT_20261031.json`，SHA256 `7287f7d851541db2991a7e4cd9174bbd55b7efb7aa27022b9c01c2c1615ac6a7`。
- 已完成项：30条teacher（每场景10条）全部qualified；棍推10条让位—蹭过—回位全部通过；75候选/9锁定模型的公平训练来源与MLP容量审计通过；fixed27开发Task27/27、Strict24/27。
- 未完成项：final108仍无`execution.json`，物理完成度0/108，所有最终矩阵指标缺失；不能用开发闭环或历史综合场景替代冻结unseen108。

## 2026-10-31 14:01 CST — 登记完整性复核

- 重新执行锁定 final108 adapter 的登记检查：9 模型、12 条条件、108 行配对及来源/配置/checkpoint hash 全部通过；登记 SHA256 `e4f3b353eb45c4b672fc666154b9a90628bea604964f1e714f3ace4d9e5b88b6` 保持不变。
- `execution.json` 不存在、`physics_calls=0`。该收据只证明 provenance/dispatch registration 完整，不提供物理 Task/Strict 或指标结果。

## 2026-10-31 服务器归档状态

- 新资源预检 JSON 的服务器归档请求被自动审批拒绝；只读确认 incoming 和最终目标目录均不存在，未写入服务器。既有 rod recheck、binding audit 和 controls v2 归档保持已核验状态。
- 资源预检收据当前仅在本地/GitHub；final108 仍为 0/108，Goal active。

## 2026-10-31 13:50 CST — 登记资源函数零物理预检

- 真实调用冻结资源检查函数 `select_v9_closed_loop_candidates_v3_20261029.py::check_resources()`；在 `memory.max=max` 断言处拒绝，`physics_calls=0`，未调用 final108 `run()`，未生成 `execution.json`。收据为 `docs/evidence/CONTACT_YIELD_FINAL108_RESOURCE_PREFLIGHT_20261031.json`，SHA256 `c4d68bdd045d142e360ead2dd9d7aeef2c38725ae379414e615b3d87f2d6a98b`。
- 当前仍为 Chromium scope、affinity 0–23、user systemd bus 不可用、主机 `SwapFree=8 KiB`，不满足 CPU6/单线程/3 GiB/禁 swap。final108 完成度仍 0/108。

## 2026-10-31 13:39 CST — 资源前置再次核验

- 重新 fetch/read 远端后，`main=414944fe9b270dfa5664de38f2da96952df365e0`、`baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；本地已快进到该 main。RL census94 更新不涉及本专题冻结登记。
- v3 目标目录仍只有 `REGISTRATION.json`，无 `execution.json` 或 episode，final108 完成度 0/108。当前 Chromium scope 的 affinity 为 `0–23`，`memory.max`、`memory.swap.max`、`cpu.max` 不可用，user systemd bus 不可用，主机 `SwapFree=0`；未满足 CPU6/单线程/3 GiB/禁 swap，未启动物理。
- 经批准的服务器只读核验中，rod recheck 与 binding audit 两个既有独立目录的 `SHA256SUMS` 全部通过；controls v2 目录存在并绑定 `abd2fc269f087108160d2edf8ff34a07eb533b1d`。服务器未运行计算，未覆盖旧产物。

# 特化场景模型 final108 一次性比较进度

## v2 启动控制复核

新增零物理控制脚本 `code/mujoco_6d_vmc_benchmark/experiments/check_contact_yield_unseen108_v2_controls_20261031.py`，执行收据位于 `code/mujoco_6d_vmc_benchmark/outputs/contact_yield_unseen108_v2_controls_20261031_v1/CONTROL_AUDIT.json`。控制脚本对真实登记和 v2 adapter 执行合成worker验证：108格按登记顺序完整调度；重复启动被拒；第4格注入基础设施错误后状态为 `failed_preserved`、前三格收据保留且同目录重跑被拒；107格review未生成结果。物理调用为0。审计绑定登记SHA256 `e4f3b353eb45c4b672fc666154b9a90628bea604964f1e714f3ace4d9e5b88b6` 与测试源码SHA256 `4de8f7c048c7718d866a687ea2cc1705747c42f4be1581d4dbe7b851bf804f36`。这只验证协调器控制流，不验证受限资源scope、物理执行或科学结果。

## 已锁定结果

本轮复用用户批准的 v7 公平重训，不重复执行已经完成的 75 个候选：40 条轨迹、21,500 帧，75/75 候选完成，FIT_AUDIT 通过，九个 checkpoint 已锁定。MLP 后续按相同六条 validation 和预算完成宽度容量诊断；三个 seed 均依既有 validation 规则选中宽度 384。拟合误差下降不作为闭环成功证据。

固定 27 条 train00 开发闭环已完成并经 wide-loader 独立复核：Task 27/27、Strict 24/27、actor/filter replay 27/27 精确。ESN 与 RNN 各 9/9 双成功；MLP384 为 6/9。三条失败均为 rod00 MLP384，峰外穿透 0.251768、0.243292、0.222516 mm，均超过原冻结 0.20 mm 门槛。失败 ID、回合和轨迹全部保留。人体舒适度无人体力通道，仍为 NA。

## final108 登记

新增版本化入口 `code/mujoco_6d_vmc_benchmark/experiments/evaluate_contact_yield_unseen108_locked_v2_20261031.py`，当前有效目标目录为 `code/mujoco_6d_vmc_benchmark/outputs/contact_yield_locked_unseen108_20261031_v3/`。它把 fixed27 v4 的原九模型精确绑定到冻结 12 条 unseen 条件，共 108 格；开发失败及其统计写入登记，不再作为派发门槛。该变化只允许比较预先锁定的模型，不替换模型、不改 validation 选择、不用测试结果调参。此前 v1、v2 目录仅有登记文件，因随后加强来源绑定/启动空闲检查而未执行；均保留，禁止运行。

原 final108 物理执行、Task/Strict 与机器 gate、SPT、力矩/速度审计、失败分母、条件配对、source/config/checkpoint hash 和独立复放保持不变。使用已经过 fixed27 验证的 MLP384 loader 包装器和同一物理 worker，以支持新 MLP checkpoint 格式；模型与测试条件均不变。v3 一次性登记已生成，执行 `execution.json` 尚不存在，物理回合尚未派发。启动前代码会确认选择服务和历史 final108 handoff 均 inactive，之后底层 runner仍验证资源并独占全局仿真锁。

固定开发复核结论绑定：27 行，Task 27、Strict 24，失败为三个 `rod_00__special_mlp_scratch_*_w384` 模型；所有 27 行 actor/filter replay 最大误差均为 0。正式 final108 的 SPT 以全部方法双成功的共同最短完成时间作 `T_ref`；只在 Task 与 Strict 同时成功的回合上汇总，失败仍留在成功率分母。人体舒适度仍报告 NA，扰动接触代理单列。

## 执行限制

2026-10-31 本轮容器实际 cgroup 为 `app-org.chromium.Chromium-1534058.scope`：`memory.max=max`、`memory.swap.max=max`、`cpu.max`与有效cpuset不可读，affinity 为 CPU 0–23；读取时cgroup `memory.current=1089753088`、`memory.swap.current=5459968`，主机swap已使用2097112/2097148 KiB。`systemctl --user` 返回 bus `Operation not permitted`，NVIDIA driver不可访问。当前环境不符合登记的 CPU6、单线程、MemoryMax 3 GiB、swap 0 资源约束，故未运行物理 episode，也未生成任何 final108 结果。向自动审批申请建立无仿真的 user-systemd 资源预检 scope 被拒，给出的理由是当前环境显式只读且approval policy=never；按拒绝要求没有改用其他执行通道。需在获准的受限本机执行环境通过资源检查后，才可以对v3登记运行一次；基础设施失败及科学失败都须保留，不得在同一目录自动重试。

最初一次 GitHub 查询失败；随后恢复只读查询并 fetch，读取到 `main=d9507f2f319856428246018c77922a9fc1425aaf`、`baseline=f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。main 新增的 history89 RL 接口与证据更新未改本专题冻结条件、模型或登记，与本轮无冲突。本轮提交 `72d318a5a3a9cdbc94744da4b3c5964f670d3817` 已推送并从远端核验；登记 JSON 远端 SHA256 为 `e4f3b353eb45c4b672fc666154b9a90628bea604964f1e714f3ace4d9e5b88b6`。baseline 未修改。
## 本轮续接状态

2026-10-31，服务器归档 v1 已完成：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_final108_v2_controls_20261031_v1/`，5个文件与manifest逐项SHA256回读一致。2026-10-31，v2控制审计通过，审计脚本、控制收据与本进度更新已准备并随本轮提交发布。用户已明确批准使用SSH将本轮必要产物归档到共享服务器独立目录并逐文件校验SHA256；只读检查确认共享根存在、目标目录 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_final108_v2_controls_20261031_v1/` 在归档前不存在。SSH访问已恢复。GitHub远端main `9bd8d0d8ce202f1a147e5aa5736fcf88e74bb96d` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d` 已查询，main远端更新已合并；发布和归档需在本轮最终提交后完成。final108仍未派发，测试完成度0/108。

## 2026-10-31 — all10 棍推 teacher 行为收据只读复核

- 对既有独立收据 `docs/evidence/nonrl_v9_candidate_catalogue_20261029/CONTACT_YIELD_ALL10_ROD_INDEPENDENT_REVIEW_20261030.json` 做了逐条只读核验；`rod_00`–`rod_09` 共 10 条均 `qualified=true`，Task、安全、行为、actor replay、filter replay 全部为 true，失败列表为空。
- 十条均满足“撤杆前让位、持杆越过、撤杆前持续回位、穿透≤0.20 mm”。回位确认时间早于撤杆 1.24–5.59 s（中位数 4.36 s）；各条时间与轨迹 SHA 已保存到 `docs/evidence/CONTACT_YIELD_ALL10_ROD_RECHECK_20261031.json`。这验证的是开发 teacher collection，不是冻结 unseen108 的模型性能或最终科学结果。
- final108 v3 目录仍只有 `REGISTRATION.json`，物理完成度 0/108；未生成 `execution.json`、Task/Strict、SPT、峰值力矩、人舒适度或机器合规统计。当前容器仍不满足登记的 CPU6/单线程/3 GiB/零 swap 约束，未启动仿真。
- 已按用户批准的归档授权核验 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/` 存在，并将本轮复核包归档到 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/contact_yield_rod_recheck_20261031_v1/`；4个文件及 `SHA256SUMS` 已逐项回读通过，MANIFEST SHA256 为 `ef3e40bd72b7dac43461092c9be44d64bc9eac1dda2ac28b3abd01d8fa86ec45`。服务器未运行计算。

## 2026-10-31 — final108 登记绑定哈希前置审计

- 只读核对 v3 登记的来源绑定：9/9 checkpoint、9/9 training metadata、1178/1178 源文件、2/2 配置文件 SHA256 全部匹配。完整明细见 `docs/evidence/CONTACT_YIELD_FINAL108_BINDING_AUDIT_20261031.json`。
- 这项审计只证明 provenance/preflight 完整，不提供 Task/Strict、SPT、峰值力矩、人舒适度或机器合规结果；final108 仍为0/108。当前资源隔离条件仍不满足，未启动 episode。
- 审计包已归档到 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/contact_yield_final108_binding_audit_20261031_v1/`；4 个文件和 `SHA256SUMS` 已逐项回读通过，MANIFEST SHA256 为 `dbe9a3273b8c729467d797ecccdb4a850be7ff037445a23b9b82cd99aaae51c5`。
