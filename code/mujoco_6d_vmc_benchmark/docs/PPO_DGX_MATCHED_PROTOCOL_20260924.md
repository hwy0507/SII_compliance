# PPO8192最终模型：DGX同平台12回合冻结验证

本协议在物理回合启动前写入。模型固定为本机8192步训练最后checkpoint，不选择中间checkpoint，不因为本机验证失败更换模型。该PPO仅用一个rod训练fixture、8192步interaction、一个seed；ESN/MLP使用多场景teacher imitation数据，因此此次只能比较**相同部署条件**，不能声称训练数据/预算完全公平。

最终模型SHA256：`611323476636c3a398bc465b11c4bf51c0dc6fab280fe9067c7babc66901f16e`；normalizer SHA256：`55fe4881e585d5f48dff32cf467a07ba29c2576a48654bf33516990866366b56`。DGX离线推理先验检查已通过：600帧训练场景48D输入，DGX CPU动作对本机原GPU动作最大误差2.3841858e−7，低于1e−6；normalizer mean/var/count冻结，clip±12。

## 全部预声明job

每个fixture各运行PPO8192和zero，共12条，时长24s，其他参数逐项复制原固定预算验证VMC的command/environment。

| seed | push angle rad | rod height m | payload mass kg | methods |
|---:|---:|---:|---:|---|
| 9400 | −0.125 | 0.5775 | 0.0925 | PPO8192、zero |
| 9401 | −0.125 | 0.5825 | 0.1075 | PPO8192、zero |
| 9402 | 0 | 0.5775 | 0.1075 | PPO8192、zero |
| 9403 | 0 | 0.5825 | 0.0925 | PPO8192、zero |
| 9404 | 0.075 | 0.5775 | 0.0925 | PPO8192、zero |
| 9405 | 0.075 | 0.5825 | 0.1075 | PPO8192、zero |

原source：服务器 `outputs/baseline_impedance_admittance_20260923/source_fixed_budget/`。原结果：`measured_campaign/fixed_budget/validation/FINAL_RESULT.json`。将整份source复制为新独立snapshot，只新增PPO/zero loader包装器与driver，不改原physics/WBC/task/observer/safety/metrics文件；driver启动前逐一检查原source的全部Python文件hash与新snapshot相同，结束后再检查snapshot未变。

## 控制与物理契约

- Actor接口仅48D因果proprioception→7D action，normalizer及网络冻结，deterministic=True，CPU单线程推理。无sim对象、接触oracle、阶段标签或未来信息进入actor。
- 零动作通过相同policy loader输出全0 action7；**不使用settle_only**，原task与gripper照常运行。
- 所有runner使用原同一panel48、原24s任务、原WBC/safety、原50μs物理步进、原6D估计wrench；model参数只是换actor。
- 相同 `run_with_substep_metrics_20260923.py` 和 `physics_substep_metrics_20260923.py` 记录每个物理步的error/twist/真实actuator torque。
- Strict gate完全沿用已有验证 `accepted_panel_demo AND no external upstream contact`；不能用前述rod/front开发pilot的较宽开发gate替代。
- 首先单独执行PPO9400、zero9400，要求两条与原9400 **MJB SHA256完全相同**，并比较scene、controller_6d_config、experiment_contract、dt；通过后剩10条最多4worker并行。
- 每条的MJB必须与对应原fixture hash相同，输出保留原rollout、MJB、contact、physics、substep metrics、命令、模型来源和失败。
- 若原runner因invalid_physics提前停止，保留partial且计失败，不能当完整24s平均；若执行异常，保留execution_error，不删除或补换有利结果。

输出根目录预定：服务器 `outputs/ppo_matched_validation_20260924_r1/`，内含独立source及运行 `evaluation/`；driver为 `scripts/run_ppo_matched_validation_20260924.py`。协议/模型/hash和所有12job完整命令将在 `evaluation/protocol.json` 实际启动前写入。前两条结构检查失败时不启动其余10条，不改变模型来通过。

已有VMC/MLP/ESN/经典控制六条件结果直接使用同平台原结果，并按同fixture/hash匹配。禁止将本机rod/front评估的三指标直接拼进DGX表。完成后的数字与状态写持续入口，不提前声称PPO优于任何方法。

## 执行与验收结果

实际driver PID448695、timeout448694已正常结束；12条共564.29s，PPO和zero各task0/6、strict gate0/6。全部回合完成24s，无执行错误或安全提前终止。163个原baseline Python文件逐hash匹配；每个fixture MJB与原六条件验证精确相同，结束时source snapshot未变。

全12原始文件已归档到本机 `outputs/ppo_dgx_matched_archive_20260924_r1/evaluation/`（约782MB）。独立工具 `tools/report_ppo_matched_validation_20260924.py` 复核每条MJB/result hash、从float32物理数据复算RMSE/峰速/峰矩（容差atol2e−5、rtol2e−6针对原float64累加器），并核对50μs时间轴、样本数、有限值；全部通过。十二条首动作前48D输入与各自原VMC完全相等，排除本轮初始状态差异。

完整七方法同平台表：[PPO_DGX_MATCHED_RESULTS_20260924.md](PPO_DGX_MATCHED_RESULTS_20260924.md)。PPO子步误差低于zero仍未完成任务，峰速与峰矩更高；不代表RL方法已充分训练，也不能用作等预算训练结论。最终失败模型和所有轨迹保留，没有选择中间checkpoint覆盖失败。
