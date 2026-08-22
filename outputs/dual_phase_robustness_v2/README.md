# Independent ESN lift-balanced ablation

v2 在独立 ESN 的 MuJoCo rollout return 中加入 195 mm final-lift 软惩罚，仍从零 readout 训练、不读取 VMC。12 条 expanded held-out 上 v2 ESN 16? 该目录对应 12 条条件的结果：ESN 12/12，VMC 12/12；ESN 平均抬升 194.56 mm，VMC 199.11 mm。ESN 的五指标综合比值相对 VMC 为 0.9731，95% CI `[0.8758, 1.0951]`，跨 1；因此 v2 改善了 v1 的抬升代价，但没有形成统计确定的综合柔顺优势。

- [训练摘要](ars_summary.json)
- [v2 expanded held-out](expanded_heldout_four_method.json)
- [v2 statistics](expanded_heldout_v2_stats.json)
- [v1 same-condition comparison](expanded_heldout_v1_stats.json)
