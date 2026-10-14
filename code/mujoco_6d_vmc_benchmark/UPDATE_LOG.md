
## 2026-10-14 — 按loss样式重画RL reward图

- 新增 `tools/plot_reward_convergence_loss_style_20261014.py`，输出 `outputs/reward_training_curves_20261013/reward_convergence_loss_style.png/pdf` 及按动作类型分组图。
- 采用与loss图一致的淡色原始曲线+粗线移动平均布局；每个点为完整episode return，横轴为实际累计训练步，平滑窗口为10个episode。另导出 `reward_episode_returns.csv`。
- 未重训、未仿真；仍区分直接动作两种reward标准和参数输出四类方法。该图用于看回报平台趋势，不能把不同reward尺度直接横比，也不能单独证明任务成功。
