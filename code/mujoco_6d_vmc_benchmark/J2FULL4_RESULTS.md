# J2FULL4 teacher 固定预算机制筛查

6/6 个开发回合已独立审计；不是 ESN 成功或保留集验证。物理、任务和安全门不变。

| 条件 | task | strict | waypoint RMSE mm | 峰矩 Nm | 峰速 m/s | 穿透 mm | 推杆 s | 最终 XY mm |
|---|---|---|---:|---:|---:|---:|---:|---:|
| j2full4_aligned_original | True | True | 156.797 | 38.828 | 0.143303 | 0.196223 | 0.797 | 2.195 |
| j2full4_aligned_rod_start7 | True | True | 132.339 | 41.843 | 0.143303 | 0.196223 | 1.397 | 2.340 |
| j2full4_aligned_rod_start9 | True | False | 135.017 | 42.444 | 0.143303 | 0.196223 | 0.000 | 2.431 |
| j2full4_aligned_rod_hold6 | True | True | 157.844 | 38.828 | 0.143303 | 0.196223 | 0.850 | 2.684 |
| j2full4_aligned_shift_plus | True | False | 140.584 | 38.113 | 0.115232 | 0.176534 | 0.184 | 2.308 |
| j2full4_aligned_hard | True | False | 162.493 | 38.390 | 0.111476 | 0.207370 | 0.951 | 2.286 |

已审计回合各 1375 次动作/teacher 状态重放通过；三个指标从全部物理子步独立复算通过。
已审计同条件候选 MJB hash 完全一致；源、配置、原始数据 hash 见 J2FULL4_AUDIT.json。
waypoint RMSE 包含阶段目标切换，不能作为连续参考曲线跟踪误差。
