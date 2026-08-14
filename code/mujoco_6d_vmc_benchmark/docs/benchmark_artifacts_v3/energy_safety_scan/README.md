# 初始粗扫描记录

本目录保存先前的 8 组独立 validation 扫描原始 JSON/CSV，作为实验追溯记录；其 fixture 设计同样独立于冻结的 V2/V3。

初始结果显示 `low/default/high tank` 与 `low/high recharge` 的外部运动指标相同。随后检查 episode 内部诊断发现所有这些条件的平均 `energy_scale` 都是 1.0，说明该强度下的储能预算没有真正绑定。因此该初扫不能单独支持“能量罐参数已经优化”的说法。

为了检验真实的 budget-limited 情况，后续新增了 `small_tank`、`near_empty_tank` 与 `near_empty_no_recharge`，并对完整的 16-fixture validation set 重新执行全部 controller/configuration；该版本是可用于冻结参数的权威结果，见相邻目录 `../energy_safety_scan_expanded/`。
