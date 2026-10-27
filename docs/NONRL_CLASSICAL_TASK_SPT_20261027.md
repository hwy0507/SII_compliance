# Task成功条件SPT与传统控制器同条件补测

2026-10-27用户要求只在Task成功回合计算SPT，并将历史传统控制器加入最新ESN/RNN/MLP
闭环比较。原108回合已经完成，不重新训练或重跑；新run为
`nonrl_classical_task_spt_20261027_v1`，固定6套传统参数×原12条件，新增72回合，最终共180。
本研究不含RL，另一会话的RL训练与冻结评价协议不变。

## 新指标及已经可以确认的结果

`SPT_task_conditional = mean(T_ref / max(T_i,T_ref) | Task_i=true)`。
Task失败回合该项为NA、不进入分母；没有Task成功的模型为NA。Task成功但Strict失败也纳入。
Task/Strict成功率、力矩和机器安全统计仍保留全部回合。共同后验T_ref取完整登记矩阵
所有Task成功回合的最短完成时间，保持一个全局参考，不分方法/条件。

仅对已完成108回合重聚合，T_ref=34.360000000578864秒。原39.40秒只来自双通过回合；
参考变化来自新纳入的Task成功/Strict失败回合，不是改变轨迹、gate或算法。

| 方法 | Task | Task且Strict | 条件SPT | 成功平均完成时间(s) |
|---|---:|---:|---:|---:|
| ESN | 28/36 | 20/36 | 0.755738 | 45.774286 |
| RNN | 26/36 | 12/36 | 0.744141 | 46.720000 |
| MLP | 3/36 | 3/36 | 0.669989 | 51.333333 |

这是三个训练seed的回合池均值，每模型明细另存；不是36个独立训练seed。
新条件效率下ESN/RNN差距明显小于旧“失败填零”的SPT差距。MLP只有3次成功，不能仅按
成功条件效率解释其整体水平。最终180矩阵将重算共同参考；此表仅代表完整108子矩阵。
原报告SHA256 `da9d4fb55ccea6b7eaa4ffa99ccfafaf6e9fe76d94e26b0a2f9f961bc201c7d0`，未改写。

## 传统控制器来源与公平性范围

沿用2026-10-10有限模型式参数搜索、2026-10-13模型锁中每类的两套finalists；不根据本次
测试结果重新选参数，也不只展示其中赢家。具体数值、历史audit hash及依赖源码清单已锁在新run。

| 控制类别 | 固定配置 | 执行方式 |
|---|---|---|
| 导纳 | admittance_boundary_06、07 | 力/力矩驱动的虚拟动力学，经原公共动作接口执行 |
| 阻抗 | impedance_boundary_01、02 | 原生笛卡尔弹簧阻尼力矩、投影平衡参考、原有摩擦前馈与姿态项；保留公共限幅/限速 |
| VMC | vmc_boundary_00、05 | 原虚拟机械柔顺控制律、物理量纲动作适配 |

传统控制器不从30条示范模仿学习；其历史有限调参预算不同。它们是固定系统基线，不能称为
与ESN/RNN/MLP相同数据、相同优化器或相同训练预算的学习算法。每个固定配置只跑12条件，
不将完全相同的确定性重复伪装成三个训练seed。两套配置单列，不作为随机seed求方差。

12条件与原108矩阵逐字节相同；复用原冻结物理源码和MJB，MuJoCo3.11.0、dt5e-5、55秒、
原Task/Strict gate和执行器限制。历史参数选择早于这些条件；研究者已经看过学习组结果，
这次是事后扩展比较，不把既有测试曝光称为重新预注册的完全盲测。

## 执行与审计

本机airpig：单模拟器、单线程、CPU1、MemoryMax3GiB、MemorySwapMax0；全局仿真锁避免
与其他本机作业重复。服务 `sii-nonrl-classical-task-spt-20261027-v1.service`。
计算目录：`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/nonrl_classical_task_spt_20261027_v1/`。
入口 `tools/run_nonrl_classical_extension_20261027.py`，启动后执行run内冻结coordinator副本。
`execution.json`、每回合`rollout.progress.json`和`PROGRESS.md`是真实进度；先查服务/PID再操作。
`--run`拒绝已运行/失败/完成状态，失败原件保留；`STOP_REQUESTED`只在完整回合边界停止。

各回合保留policy trace一致性、公共filter独立重放、原始物理子步指标、穿透/峰矩/速度/RMSE、
源码/参数/config/MJB/轨迹hash及任务失败。**经典worker没有完整独立控制器actor重放**，
尤其阻抗的完整平衡参考/Jacobian原生力矩链不能用action7一致性代替；新报告明确标注这一限制。
学习组已有的完整actor/filter审计不因此降级或改写。

comfort保持原经验阈值 `[43.5,43.5,43.5,43.5,6,6,6]Nm`，只在人机实际接触力>0.05N
的物理子步按dt计分，无接触为NA，不宣称人体舒适认证。机器安全另列，包括穿透>0.2mm。

新聚合器四项测试通过：Task/Strict分离、排除失败且共同参考、无成功NA、异常时间与重复回合拒绝。
准备前核验6套依赖与历史audit全hash一致，以及旧108报告、锁模和冻结源码未改。
服务已启动并确认物理时间推进。72回合尚未完成，完整传统组结果、共同参考与最终归档待完成。
小型登记/108新口径证据先发布，运行中不把局部成绩称最终排名。

首回合已完整完成55秒及审计，用时369.42秒，协调器自动接续第二套导纳；启动链有效，
不是只有systemd active。按首回合粗估72回合约7.4小时，阻抗耗时可能不同，最终以实际进度为准。
首回合未完成Task（carry结束），原始失败保留，不作全组排名；OOM事件0、worker swap0。

## 归档

服务器只用于本轮归档，不计算。已核验登记包：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/nonrl_classical_task_spt_20261027_v1_registration/REGISTRATION_BUNDLE.tar.gz`。
大小2,001,510字节，SHA256 `dc4f40656985e1fced46077ebab0d81e97380dc1070d6dfe1136ca79977c148b`，
含冻结coordinator/物理/经典控制器源码、参数/协议/条件及108新旧聚合报告。收据见
`docs/evidence/nonrl_classical_task_spt_20261027/REGISTRATION_ARCHIVE.json`。
未完成回合不复制为完整证据。全量最终原始产物在72回合结束和核验后另行归档。
