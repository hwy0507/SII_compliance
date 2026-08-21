# 跨接触条件验证结果（2026-08-21）

## 结论

上一轮在 `negative_y` 有限质量圆柱 rod 接触条件下取得优势的 CEM-improved ESN，没有跨越到本协议定义的反向掌形接触条件。ESN checkpoint、reservoir、CEM readout gains 和 5% budget 全部冻结；没有利用本轮 validation/test 重新训练或调参。

在新的 `positive_y`、finite-mass ellipsoidal `hand_proxy` 条件下，validation 中冻结 ESN 已为 `0/20` 成功，而 VMC 在相同 validation realization 上独立选出的配置为 `k=1.0, 2%`，成功率 `15/20`。在完全未见的 held-out test 中：

| 方法 | success | at-grasp error | peak contact force | peak torque | contact bouts | hard limit |
|---|---:|---:|---:|---:|---:|---:|
| Frozen CEM ESN-303, 5% | **0/20** | 35.951 ± 4.829 mm | 104.261 ± 20.757 N | 36.344 ± 0.703 N·m | 2.55 | 0/20 |
| Validation-selected VMC k=1.0, 2% | **14/20** | **20.182 ± 7.849 mm** | 104.434 ± 20.602 N | **32.899 ± 0.354 N·m** | 2.15 | 1/20 |

这里的 `±` 为 rollout 样本标准差。成功率差异为 `0/20` 对 `14/20`，且 14 个 VMC 成功 realization 均为 ESN 失败；不能声称 ESN 在跨接触条件下保持上一轮优势。

## 物理条件与校准

新条件保留真实 MuJoCo 力学接口：有限质量刚体、阻尼 slide joint、受力受限 position servo、MuJoCo `solref` 接触柔度、FR3 原始 torque limits 和 residual safety clamp。相对于上一轮训练/CEM 使用的 `negative_y` cylindrical rod，本轮改变为：

- `positive_y` 反向 slide direction；
- `hand_proxy` finite-mass ellipsoid，作为受控掌形接触探头；
- 仍为两次 press–hold–retract；动态参数继续在既有声明包络内随机化。

仅用于验证物理接触确实发生的 calibration seeds `20261101–20261103` 中，裸 PaperMPC 的峰值接触力分别为 `89.4, 145.7, 121.7 N`，三次均检测到 contact，但 task success 均为 false。校准没有用于 ESN/VMC 选择。

Held-out test fixture 实际范围为：

- impactor mass `0.198–0.492 kg`；slide damping `0.626–3.894 N·s/m`；
- driver kp `2.851–8.661 kN/m`；force limit `151.4–299.4 N`；
- contact time constant `8.91–24.75 ms`；stroke `0.1612–0.1756 m`；
- height `0.5391–0.5418 m`；start time `0.902–1.026 s`；cycle period `0.661–0.719 s`。

## 数据划分与选择

- calibration：`20261101–20261103`，仅做接触存在性检查；
- validation：`20261111–20261115`，20 fixtures；冻结 ESN 只被测量，VMC 搜索 `k={1.0,1.5,2.2,3.2}` × budget `{2%,3%,5%}`；
- held-out test：`20261116–20261120`，20 fixtures，测试前未运行；
- 选择规则：VMC 先最大化 validation success，再以 validation mean at-grasp error 破平局；ESN 的 5% budget 与 checkpoint 继承上一轮并冻结。

Validation 候选中，VMC 选中的 `k=1.0, 2%` 为 `15/20` success、`21.592 mm` mean error。其余较高刚度/预算配置在此接触条件下出现更多失败、较高力矩甚至 hard-limit events；因此不能事后把预算固定为上一轮的 5%。

## 配对统计

在相同 seed/fixture 配对下，ESN−VMC：

- at-grasp error：mean `+15.769 mm`，fixture-level 95% t CI `[+13.753,+17.785] mm`；按 seed 聚合 CI `[+13.421,+18.117] mm`；
- peak contact force：mean `−0.173 N`，fixture-level CI `[-0.640,+0.294] N`；
- peak torque：mean `+3.445 N·m`，fixture-level CI `[+3.147,+3.743] N·m`；
- contact bouts：mean `+0.400`，fixture-level CI `[+0.047,+0.753]`。

ESN 的力峰值与 VMC 接近，但 tracking error、峰值 torque 和接触再发生次数均明显更差。两者都出现了较大的接触力，说明该协议本身是明显比上一轮更困难的接触条件；VMC 也不是无代价地“安全”，在 held-out test 有 1/20 hard-limit event。

## 科研解释

这个负结果是重要边界，而不是实验失败：上一轮 CEM 只优化了 `negative_y` cylindrical-rod 分布上的 readout，且 deployed observation 没有接触方向、接触几何或接触力信息。reservoir 的时间记忆能够帮助其处理训练分布内的冲击瞬态，但不能保证从一个接触几何/方向自动推断另一个接触映射。VMC 的解析 Jacobian/虚拟弹簧结构在这一点上反而具有更强的结构迁移性。

因此当前更严谨的主张是：

> CEM policy improvement can make the proprioceptive ESN outperform VMC within a declared contact-apparatus condition, but the advantage is not automatically cross-contact invariant. Under an unseen opposite-direction ellipsoidal contact, the frozen ESN failed all 20 held-out trials while a freshly selected low-stiffness VMC succeeded on 14/20.

后续若要研究跨接触泛化，必须另立训练协议，例如训练时覆盖方向/几何，或增加受约束的在线 system-identification/adaptation；不能用本轮 test seed 继续调参，也不能把接触方向/力作为未经论证的特权输入偷偷加入 ESN。

原始服务器结果：`/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_cross_contact_generalization_20260821/fair_results.json`；本地/服务器 SHA-256：`11e0ca321c5a98c3cf8faf63417a10559d7a196037cea647712297dda39d61ea`。
