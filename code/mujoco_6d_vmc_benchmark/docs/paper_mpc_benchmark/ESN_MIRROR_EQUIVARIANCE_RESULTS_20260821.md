# ESN 镜像等变读出结果（2026-08-21）

## 结论先行

简单的 pose-error mirror-equivariant output gate 没有解决上一轮 CEM-ESN 的跨接触失败，反而在 validation 上更差，因此没有被选为最终模型。该方向应作为已完成的负消融保留，不应作为 proposed ESN 的默认机制。

在新的 `positive_y + finite-mass ellipsoidal hand_proxy` 条件下，ESN 两个候选都固定 5% residual budget，validation 选择规则为先最大化 success、再最小化 at-grasp error：

| ESN 候选 | Validation success | Validation error | Peak force | Peak torque | Contact bouts |
|---|---:|---:|---:|---:|---:|
| Frozen original CEM ESN | 0/20 | 37.399 mm | 95.052 N | 36.261 N·m | 2.35 |
| Mirror-equivariant gate | 0/20 | 44.007 mm | 94.926 N | 35.655 N·m | 3.45 |

因此 validation 选择 frozen original ESN。VMC 在同一 validation realization 上独立选择 `k=1.0, 2%`。

held-out test 的最终比较为：

| 方法 | Success | At-grasp error | Peak force | Peak torque | Contact bouts | Hard limit |
|---|---:|---:|---:|---:|---:|---:|
| Selected original ESN, 5% | 0/20 | 36.445 mm | 100.449 N | 36.319 N·m | 2.50 | 0/20 |
| Selected VMC, k=1.0, 2% | 16/20 | 18.852 mm | 100.361 N | 32.868 N·m | 2.10 | 0/20 |

匹配 `(seed, fixture_index)` 的 ESN−VMC 差异为：

- at-grasp error：`+17.593 mm`，fixture-level 95% t CI `[+15.695, +19.491] mm`；
- peak force：`+0.088 N`，差异可视为相当；
- peak torque：约 `+3.451 N·m`，ESN 更高；
- contact bouts：`+0.400`，ESN 更多重复接触。

## 协议

父模型、reservoir、readout 和 deployment observation 均冻结。镜像变体只对已有的 `yield_vy` 和 `yield_wz` 输出通道施加由 deployable `pose_error` 计算的 soft-sign 符号变换；没有加入接触力、装置参数、障碍物状态、接触方向标签、pulse timing/count 或 future release 信息。完整的预先声明协议见 [ESN_MIRROR_EQUIVARIANCE_PROTOCOL_20260821.md](ESN_MIRROR_EQUIVARIANCE_PROTOCOL_20260821.md)。

- validation：`20261211–20261215`，每个 seed 4 个 fixture；
- held-out test：`20261216–20261220`，每个 seed 4 个全新 fixture；
- VMC 候选：`k={1.0,1.5,2.2,3.2}` × budget `{2%,3%,5%}`；
- test seed 在结果生成后视为已消耗，不得据此继续调 epsilon、gate channel、ESN checkpoint 或 VMC 参数。

## 科研解释

失败并不说明“ESN 记忆机制没有价值”，而是说明对输出符号做局部镜像约束不足以恢复接触动力学的映射。该 gate 没有改变 reservoir 的时序状态、训练分布或 nominal-controller coupling；在反向掌形接触中，ESN 仍无法从有限本体感知观测中可靠识别所需的恢复方向。后续若研究跨接触泛化，应建立覆盖方向/几何的独立训练协议或受约束在线适应，不能把本轮 test 结果用于反调 gate。

原始服务器结果：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_esn_mirror_equivariance_20260821/fair_results.json`。
