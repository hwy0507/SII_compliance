# 当前原VMC与历史accepted teacher的差异边界

本记录仅分析既有trace、配置与源码，没有新增仿真，没有修改正在训练的8192步PPO。

同一归档rod fixture，当前本机原VMC24s结果task=false，而历史source结果task=true。现有证据**不能把差异归因于VMC参数抄错或已改变的observer/WBC/safety core，也不能断言硬件是唯一根因**。最早的差异在第一个动作之前，随后接触动力学与控制反馈放大。

## 配置和源码来源

证据目录：`outputs/canonical48_ppo_diagnosis_20260923_r1/`。复查工具：`tools/audit_canonical48_teacher_lineage_20260923.py`，输出 `LINEAGE_AUDIT.json`。

归档来自DGX服务器 `arm1`（aarch64），本轮VMC在RTX5080本机（x86）运行。当前本机MuJoCo3.11.0；没有完备的历史NumPy/SciPy/BLAS与软件环境记录，不能将今日服务器版本当作历史版本。

旧结果来自 `outputs/vmc_auto_search_20260920/trials/r0000_rod_04/rollout.{json,npz}`。服务器搜索发现其 `outputs/vmc_auto_search_20260920/source/` 仍存在，已只读取回到诊断目录 `historical_source/`，同时取回 `source_manifest.json`。9个受历史搜索监测的源码文件逐一匹配历史manifest hash。

| 文件/配置 | 历史 vs 当前 |
|---|---|
| 完整CORE_VMC_CONFIG | 相同 |
| force source / teacher profile | estimated / memory，相同 |
| scene参数、rod_height=0.65m、面板几何 | 相同 |
| haptic_vmc_teacher（observer/estimated wrench） | 源码字节相同 |
| fixed_panda_wbc | 源码字节相同 |
| audited_velocity_env | 源码字节相同 |
| wbc_velocity_residual_core（safety） | 源码字节相同 |
| CoreTeacher / workstation / primitive scene | 源码字节相同 |
| primitive runner | student loader及新增upstream成功gate等差异 |
| panel runner | unified48、多scene、默认rod高度、存档/审计等差异 |

当前primitive新增upstream gate并不是本次失败原因，因为此次upstream=false。历史和当前仍都要求lift>0.10m、末端误差<0.015m、末物体速度<0.02m。panel新增默认高度已恢复至归档0.65m；原VMC分支不调用student loader；48D观测增加的力矩分量不会改变原VMC输入，因为历史teacher_force本就为6维。

这9个文件并不覆盖所有传递依赖、底层数值库和编译模型，因此“关键模块字节相同”不是完整运行时等价证明。

## 首次差异与逐步放大

旧trace有45D observation、6D teacher_force；审计按canonical数据转换顺序插入teacher_force后三维，得到可对比48D observation。没有将45D输入错误填充或重新估计力矩。

第一条action之前，初始q最大差 `3.9380457e−8`，初始nominal twist最大差 `6.5245329e−12`；初始action完全相同。第一步post-step torque最大差约 `4.75e−8`。

| 通道 | 首次差值>1e−8的时间 | 后续较大差异 |
|---|---:|---|
| estimated wrench / teacher_force | actor输入0.52s | 1.04s差0.002156；1.28s差0.01461 |
| action | actor输入0.80s | 1.04s差0.000551；1.36s差0.02387 |
| hand position | post-step1.04s | post-step3.52s差0.01064m |

表中action/wrench属于动作执行前，position属于执行后；JSON同时保存step_start_s和step_end_s以避免40ms错位。旧和新trace时间轴完全相同。微小初值差先于action差出现，随后在接触期间逐渐放大；这与对数值/接触分支敏感的系统相符，但尚未做“同编译模型、同完整初始物理状态、同软件版本”的因果对照，因此不将其写成硬件已被证明是根因。

本机当前VMC抬起0.206m但末端误差52.39mm而失败；历史末端误差5.64mm而成功。当前随机PPO训练轨迹曾抬起0.253m、末端误差7.15mm，只因末端物体速度30.88mm/s超过20mm/s而失败。因此，当前VMC失败**不能证明RL目标不可学**。

## 对最终比较的要求

本机PPO开发结果不得直接拼接DGX上的ESN/MLP/经典控制指标。部署评估应在同一平台、同一固定MJB或严格一致fixture生成条件、同一WBC与审计下运行PPO和zero/VMC参考，再与冻结ESN/MLP比较。本次跨平台历史差异不否定现有同平台审计采样与原始trace不变性证据，也不否定离线teacher动作重放的准确性。
