# 配对训练启动说明：与验收快照保持一致

训练遵循已经冻结的`RL_PARAMETER_ACTION_PAIRED_PROTOCOL_20260924.md`，使用DGX独立只读`outputs/paired_parameter_action_20260924_r1/source`及`assets`。后续新增部署脚本不再同步进入该source，以免使运行前证明与训练源码脱钩。

主agent已给出条件执行授权：parameter6/direct7完整24s Gym proof及独立transition审计均通过、两模式source/asset/runtime完全一致且无其他物理worker后，直接启动各8192步训练。不需再次向用户确认，也不绕过任一失败证据。

验收进程分别固定CPU0/1。只读硬件检查发现它们是2.808GHz小核；CPU5/6是3.9GHz大核，当前allowed_cpu明确为0–19，因此`--cpu-offset 5/6`分别对应实际CPU5/6。训练预先改用这两颗大核，每进程仍单CPU线程、单物理环境，device统一CUDA NVIDIA GB10。只是计算资源选择变化，不变更互动预算、物理配置、奖励或checkpoint选择。

各分支外部timeout7200s，输出计划为`training/parameter6`和`training/direct7`，必须不存在才启动。入口内部同时核对两份proof的mode、fixture、163份执行源文件、完整两套franka资产、runtime/device及冻结总协议hash；模型资产与源文件结束时再次验hash。最多2个simulator worker，线程参数OMP/OpenBLAS/MKL/Torch均为1。

两命令共用以下绝对路径：根`/home/arm1/vmc_mujoco_runtime/mujoco_6d_vmc_benchmark/outputs/paired_parameter_action_20260924_r1`，Python`/home/arm1/vmc_mujoco_runtime/.venv/bin/python`，menagerie`/home/arm1/vmc_mujoco_runtime/mujoco_menagerie`。调用该根下`source/tools/run_canonical48_paired_ppo_20260924.py`，分别传`--mode parameter6/direct7 --output 根/training/模式 --assets 根/assets --menagerie 原menagerie --proof-root 根/proof --device cuda --cpu-offset 5/6`，不传proof-only。

完成后额外复核训练分支的无学习train对照：parameter6的`eval/train/zero/episode_00000`对先前归档nominal VMC；direct7的同路径对`proof/direct7/direct_reference`。复用冻结入口的`compare_episode`检查有限原始轨迹/MJB/JSON语义精确一致。若跨核不同必须保留并诊断，不把差异排除或将不合格对照伪装为相等；训练模型和失败记录仍保留。

实际启动PID、时间、源码/协议hash及状态将以各`training/模式/manifest.json`、`progress.json`、`COMPLETE/FAILED.json`和本说明后续记录为准，本文计划本身不代表训练已开始。

## 实际启动

两份完整proof及独立agent审计全部通过后，已核服务器没有其他物理worker（原WebUI服务保留）、可用内存约119583MiB，按上述条件授权启动。parameter6 timeout472043/Python472046绑定CPU5；direct7 timeout472044/Python472045绑定CPU6。两个manifest、model_architecture和progress已产生，RSS各约2.21GiB；实际命令与本说明一致。日志中的SB3 MLP低GPU利用率提示不是执行失败，也不据此单边改变设备。

首次稳定检查：parameter6 512步/116.14s，direct7 576步/118.50s，CUDA各约64.7MiB、系统可用112.6GiB。实际可训练网络参数分别46477与46607；这由6/7维输出层及log_std差别导致，相同128×128隐藏层不等于参数数目完全相同。后续进度以progress文件为准，此处仅记录启动验收快照。

训练source继续为验收同一只读快照；没有重跑旧8192，也没有提前启动后续18条部署。完成状态只以新训练各自COMPLETE及随后的独立审计为准。
