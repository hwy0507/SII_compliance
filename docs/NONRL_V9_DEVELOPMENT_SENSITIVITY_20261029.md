# v9 训练/验证 teacher 历史上的单步输入敏感性检查

本轮是定位证据，不是闭环修复或最终方法排名。没有拟合、仿真积分、模型选择或读取测试轨迹。Goal 仍 active，主矩阵尚未修复。

## 方法与复现

仅读取 v9 数据（SHA256 `120173888964ee0545393cd0d2685c794f7aa261626463fa7c10fc981b9c6407`）中 rod/ball/corner 的 train00、validation08，共六条 teacher 历史；九个冻结模型均检查。每十帧固定采样，对位置误差通道20–22逐坐标 ±1mm、估计力通道39–41逐坐标 ±0.1N，使用同一未扰动历史状态的独立actor副本，各自只推进一个策略步。扰动状态不进入下一帧。三方法使用同一帧、同一扰动；全54组副本与原actor的无扰动输出逐数组精确一致，数据及checkpoint前后hash不变。

结果度量是公共filter之前的归一化requested残差动作（六通道）最大绝对变化，**不是Nm、跟踪误差或成功率**。此坐标扰动并非动力学自洽状态。只测teacher附近的单步敏感性，不能证明闭环稳定性，也不能将方法差异认定为唯一根因。饱和率包含原有饱和，不称新增饱和。

| split | 输入扰动 | ESN最大动作变化 | RNN最大动作变化 | MLP最大动作变化 |
|---|---|---:|---:|---:|
| train | ±1 mm位置误差 | 0.023375 | 0.004541 | 0.008866 |
| train | ±0.1 N估计力 | 0.089976 | 0.023382 | 0.040781 |
| validation | ±1 mm位置误差 | 0.010033 | 0.003683 | 0.007836 |
| validation | ±0.1 N估计力 | 0.095906 | 0.021299 | 0.042393 |

ESN对这组输入扰动的最坏单步响应较大，与既有读出外推风险线索一致，但**尚未完成参数干预后的闭环验证**，不能说已经找全bug或修好。逐组样本数、median/p95/max、饱和率及全部源hash见 `docs/evidence/nonrl_v9_development_sensitivity_20261029/SENSITIVITY.json`。没有利用这些数值挑选新参数。

执行：本机低优先级独立服务 `sii-v9-development-sensitivity-20261029`，CPU6/单数值线程/CPUQuota25%/Nice19/MemoryMax512MiB/禁swap；自然exit0，wall2.141s、CPU2.110s。不新建模拟器，不使用服务器计算。入口 `code/mujoco_6d_vmc_benchmark/tools/diagnose_v9_development_sensitivity_20261029.py`，PYTHONPATH=scripts:tools，--training outputs/special_scene_direction_retrain_20261029_v9，--output 指向上述JSON。

## 当前运行与后续

原108为已曝光的组合扰动迁移压力测试，不能作为三个分离特化场景最终主矩阵。七次30秒间隔的宿主只读观察完成，当前ESN在途回合实际时间17.04→44.04s，scope进程身份保持，memory.events OOM/kill/max均0，实验swap0；随后完成数48→49，Task5、Strict/BOTH0、SPT NA。两个科学单元Invocation保持，后继PID1636845只等待，不重复启动；1103登记源码hash仍一致。完整观察收据见 `docs/evidence/nonrl_v9_verified_wait_20261029_v1/WAIT.json`。

下一步仍按已登记顺序：完成原108且scope退出→唯一v3执行18条同场景train/val配对→审查同身份teacher与学生首次偏离→在训练/验证侧登记有限强ridge/有界特征或覆盖修复并真实验证。新增数据共享三方法，最终另冻结未见三特化测试。不得用已曝光组合测试选新参数，不放宽物理、Task/Strict或安全阈值。

开工核验 main `fc7fcda23251db552f44be63ae4f211f2eb88ea2`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；baseline仍为10/08接触指标探索。归档状态由相邻SHARED_RECEIPT.json记录；无在途108归档。
