# 物理接触装置难工况结果（2026-08-21）

## 结论

在预先固定的“validation 选配置、held-out test 只跑一次”协议下，ESN 没有超过 VMC。两者在新的两次物理接触装置难工况中都取得 20/20 成功；ESN 的测试抓取误差为 `10.387 ± 1.057 mm`，VMC 为 `10.257 ± 1.039 mm`（均值 ± rollout 样本标准差）。ESN−VMC 的匹配 realization 均值差为 `+0.131 mm`，20 个 realization 的 95% t 区间 `[-0.150, +0.411] mm`；按 5 个 seed 先聚合后的区间为 `[-0.067, +0.328] mm`。区间跨零，故结论是总体不可分辨，而不是 VMC 显著胜出。

## 选择结果

| 家族 | validation 选中配置 | success | at-grasp error | peak force | contact bouts |
|---|---|---:|---:|---:|---:|
| ESN | ESN-303, budget 5% | 20/20 | 10.074 mm | 40.580 N | 4.20 |
| VMC | k=2.2, budget 5% | 20/20 | 9.768 mm | 40.999 N | 3.70 |

选择只使用 validation；上述数值不作为 held-out 性能声明。

## 独立测试结果

| 方法 | success | at-grasp error | peak contact force | contact bouts | peak torque | hard limit |
|---|---:|---:|---:|---:|---:|---:|
| ESN-303, 5% | 20/20 | 10.387 ± 1.057 mm | 47.202 ± 19.476 N | 3.30 ± 1.95 | 33.586 ± 0.251 N·m | 0/20 |
| VMC k=2.2, 5% | 20/20 | 10.257 ± 1.039 mm | 47.760 ± 19.454 N | 3.00 ± 1.62 | 33.364 ± 0.241 N·m | 0/20 |

匹配差（ESN−VMC）为：

- at-grasp error：`+0.131 mm`，SD `0.600 mm`，20-realization 95% t CI `[-0.150, +0.411] mm`；
- peak force：`−0.557 N`，即 ESN 略低，但不构成主要算法优越性证据；
- peak torque：`+0.222 N·m`；两者均无 hard torque limit；
- contact bouts：`+0.30`，说明 ESN 在该测试中平均发生略多的接触/再接触事件。

按 seed 的 ESN−VMC 误差差为 `+0.132, +0.299, −0.026, +0.279, −0.030 mm`，平均 `+0.131 mm`，seed-level 95% t CI `[-0.067, +0.328] mm`。ESN 在 20 个匹配 realization 中有 16 个误差高于 VMC，但差异很小且仍跨零。

## 解读与限制

这个结果不支持“ESN 在困难接触装置中战胜解析 VMC”。它支持更克制的表述：domain-randomized proprioceptive ESN 在已声明物理包络内达到与 VMC 相当的成功率和 tracking error，同时保持略低的平均峰值接触力；但 VMC 的点估计误差仍略低，ESN 没有统计可分辨的总体优势。

该 ESN 是由 VMC teacher 蒸馏得到的，因此不应预期仅靠 behavior cloning 自动超过 teacher。训练看到的是物理范围的 train distribution，但没有看到 validation/test realization；controller 输入没有接触力、装置质量/阻尼/伺服增益、pulse count/timing、障碍物位姿或未来释放时刻。

development-only calibration 和 repeated-impact pilot 不能与本 confirmatory result 混用。所有结果来自服务器 MuJoCo：

```text
/home/arm1/vmc_mujoco_runtime/outputs/paper_mpc_contact_apparatus_fair_20260821/fair_results.json
```

原始 JSON 包含全部 21 个 validation candidates、20 个 ESN test rows、20 个 VMC test rows 及每个 fixture 的物理参数。测试 seed 已消耗；后续若研究 direct RL/readout fine-tuning，必须新建独立 train/validation/test split，不能使用本测试集调参。

## 可汇报表述

> Under a physical contact-apparatus envelope and a configuration-selection rule fixed before held-out testing, the domain-randomized ESN and analytic VMC both achieved 100% success on 20 held-out MuJoCo realizations. Their grasping errors were statistically indistinguishable (10.387 versus 10.257 mm), with no hard torque-limit events. The ESN therefore matches, but does not establish superiority over, the analytic baseline in this difficult contact setting.
