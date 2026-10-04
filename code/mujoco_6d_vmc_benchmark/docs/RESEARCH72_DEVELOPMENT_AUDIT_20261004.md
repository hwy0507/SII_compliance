# research72 开发回合 worker 指标汇总（2026-10-04）

范围更正：本报告重新汇总 worker 已保存的指标，没有从原始物理子步独立复算。
旧版本的“独立审计”和“完整回合”措辞过强；程序 `complete` 也可能对应物理提前终止。
后续阶段独立物理审计与此处的指标汇总必须分开。

本报告保存 2026-10-04 约 07:50 UTC 在 arm1 上对已完成开发回合的独立汇总。它服务于最终模型选择前的失败诊断，不是正式留出评估，也不改变 gate、候选资格或封存条件。

服务器根目录：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`

汇总方法是只读递归加载三个开发目录中的 `execution.json`，统计包含 `audit` 对象的回合，包括短回合；直接使用保存的 `task_success`、`strict_success`、`rmse_mm`、`peak_torque_nm`、`peak_speed_mps` 和 `penetration_mm` 字段，不把动作重放误差当任务成功，也不删除失败或超限回合。当时队列登记状态为 neural-LR 26/168、context gate 32/168、context readout refit 12/144；RL 和最终衔接仍在运行。

## 当前已完成回合

| 开发组 | 已汇总 | task 成功 | strict 成功 | RMSE 均值 (mm) | 峰值力矩均值 (Nm) | 峰值速度均值 (m/s) | 最大外穿透 (mm) |
|---|---:|---:|---:|---:|---:|---:|---:|
| neural-LR | 26 | 9 | 7 |  |  |  | 0.9309 |
| context gate | 32 | 17 | 9 |  |  |  | 2.4684 |
| context readout refit | 12 | 4 | 2 |  |  |  | 0.5069 |

均值不在本表填入，因为各候选的已完成条件数不平衡；将不完整候选压成一个方法均值会掩盖身份和条件差异。最终报告应使用固定模型、完整 24 条件和失败保留分母的成对统计。

## 已看到的机制信号

- readout refit ESN 的当前两条开发回合均完成任务，但只有 1/2 strict；两条的 RMSE 为 30.699 和 32.111 mm，峰值力矩约 49.98 Nm，峰值速度为 0.3491 和 0.3823 m/s，第二条外穿透为 0.5069 mm。因此不能将这两条写成安全通过。
- context gate 中 `gated_esn_2026100301_point` 当前 2/2 task、2/2 strict，RMSE 均值约 28.859 mm；但其它 seed/损失分支出现 0.2743、0.5097、0.741 和 0.7817 mm 的外穿透，说明尚无跨条件稳健性。
- neural-LR 中 matched RNN 与 MLP 的早期回合成功/失败混合；部分 temporal RNN 回合 RMSE 达到 161.772 和 269.748 mm，外穿透最高 0.9309 mm。该结果只能作为失败原因线索，不能替代完整 RNN 对照。

这些数字来自不平衡的开发曝光，不能用于宣布 ESN 胜过 MLP、RNN、RL 或经典控制器。最终衔接仍必须等待所有前置收据闭合，然后按已登记的 38 模型 × 24 条件运行正式评估。

## 复现与限制

后续可复核账本：`EXPOSURE_SNAPSHOT_20261004_0850.json`，内部真实时间
`2026-10-04T08:45:42.794542+00:00`，文件名0850仅运行标识。
SHA256 `c708837a1b011d7b623ffbf88c8fd7aac346e72eb88c115727902c24f477df67`。
它使用已归档的 `research72_exposure_ledger_20261003.py`，逐条核对队列引用的 `AUDIT.json` hash；
保留回合身份、trace hash、stage、abort_reason和full_horizon。它仍不重新计算物理子步。
新快照含neural-LR29条（task10/strict8/短回合1）、context34条（18/10/1）、refit16条（5/3/0）。
新旧快照各自保留，不把不同时点的分母混用。上述文件在服务器根和Git evidence目录同字节保存。

本次汇总没有读取封存条件、模型锁或最终输出，也没有启动 MuJoCo、训练、选择或修改服务器文件。复核时应重新读取上述服务器根目录的原始 `execution.json`、各回合 `AUDIT.json`、trace/config/checkpoint hash，并以正式评估的物理子步审计为准。当前 `final_evaluation_v1`、`MODEL_LOCK.json` 和开封收据均不存在。
