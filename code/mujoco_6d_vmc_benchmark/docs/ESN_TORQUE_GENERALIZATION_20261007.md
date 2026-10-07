# ESN 读出平滑与泛化开发结果（2026-10-07）

## 目的与冻结边界

本轮只改变固定 128 单元 ESN 的线性 readout 拟合，不改变 office-v6 几何、任务/strict gate、48D/action7 本体输入、执行器幅值/变化率限制、公共 filtering 或正式物理步长。训练数据为
`outputs/research72_20261003_1149/demonstrations_refined_v1/training_data.npz`，固定 20/5 identity split；最终 24 条 sealed 条件未读取。

父 checkpoint SHA256：`acd3b27e37c3e7d7690570df5276f52492d6597951643bf5011ad8ac2aee2ec7`。

训练数据 SHA256：`7bb2f7bad7555cc97ca9cc32d43040e91775ce05cdfd32d109a7afbeb1d7e0a0`。

## 读出机制

- action-increment 正则：惩罚相邻读出特征对应的动作变化；
- action magnitude 正则：抑制动作能量，作为峰值力矩的离线代理；
- 可选本体观测噪声一致性：只在训练拟合中使用，部署仍接收原始 48D 本体字段；
- 禁止接触真值、球/物块状态、事件时间、任务阶段、视觉或距离输入。

网格为 `ridge ∈ {0.01, 0.1, 1.0}`、`smooth_weight ∈ {0, 0.01, 0.05, 0.1}`、`action_weight ∈ {0, 0.001, 0.005}`，共 36 个候选；选择只看 5 个 validation identities 的预注册组合目标。

## 离线 identity-holdout 结果

| 模型 | checkpoint SHA256 | 验证 action MSE | 验证 action delta energy | 验证 action energy | 最大单步 action 跳变 |
|---|---|---:|---:|---:|---:|
| 父 ESN | `acd3b27e…2ec7` | 0.000242 | 0.014357 | 0.012396 | 1.566 |
| 平滑网格候选 | `69ecee9d…46e4` | 0.000612 | 0.009489 | 0.009701 | 1.366 |
| 平滑+噪声候选 | `c327ee61…ab6e` | 0.000548 | 0.010215 | 0.010058 | 1.412 |

相对父 ESN，平滑网格候选的验证 action delta energy 降低约 33.9%，action energy 降低约 21.7%，最大单步跳变降低约 12.7%；代价是 action MSE 增加约 153%。加入小幅本体噪声后 MSE 和平滑度折中，但仍不如纯平滑网格候选的预注册目标分数。完整逐身份结果和数据 hash 见：

本地：`outputs/esn_torque_generalization_20261007_grid/REPLAY_COMPARISON.json`；服务器归档：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_torque_generalization_20261007_fa64f33/REPLAY_COMPARISON.json`

训练网格收据：

`outputs/esn_torque_generalization_20261007_grid/TRAINING_COMPLETE.json`

提交源码快照已核验至：

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/fa64f33b59794a0f88d53f667b8517e87a6737eb/source.tar`

源码 tar SHA256：`871cd8fb426a6171217f84bc0cd5810fd5b295a66fdca172d49aeecc62b544be`。

## 物理闭环状态

本轮没有把新 checkpoint 放入正式 `/24` 矩阵，也没有声称峰值力矩下降或泛化成功。默认解释器确实因缺少 Pillow/SciPy 在首次尝试时失败；随后找到兼容的 `/home/airpig/桌面/hwy/compliance_control/.venv-canonical-rl/bin/python3`（Pillow、SciPy、MuJoCo 3.11.0），但 worker 要求显式 cgroup `MemoryMax≤3G`，本机 `systemd-run --user` 因受限运行容器无法连接 bus，arm1 SSH 也不可达。因此本轮：

- 物理子步数：0；
- task/strict：未测；
- 真实峰值力矩、峰值速度、RMSE、穿透：未测；
- sealed 条件：未读取；
- 失败原因：默认解释器 `ModuleNotFoundError: PIL`；兼容解释器的 cgroup 审计失败（`memory.max` 为 `max`，`systemd-run --user` 为 `Operation not permitted`）。服务器归档已完成，但尚未运行新的物理闭环 worker。

下一步应在依赖完整且资源受限的既有 worker 上，用未参与选择的 8 个 development identities 评估父 ESN、平滑候选和噪声候选；只有闭环 task/strict 与物理峰值结果完成后，才决定是否进入新的冻结模型锁。
