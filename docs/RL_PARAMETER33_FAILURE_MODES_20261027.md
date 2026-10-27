# 参数32→33成败切换：安全门与阶段停滞

2026-10-27 UTC。本轮承接已完成的全部30条件reward配对结果，仅检查其中全部四条成败切换条件，共8条已保存轨迹；无新仿真、神经推理、优化或正式设置修改。输入与冻结源码hash前后不变，原始结果/失败保留，图已查看。Goal active。

服务器根B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，原诊断`B/runs/parameter32_33_failure_modes_20261027_v1`。源码`code/mujoco_6d_vmc_benchmark/tools/audit_parameter32_33_failure_modes_20261027.py`，小证据`docs/evidence/RL_PARAMETER33_FAILURE_MODES_20261027/`。

## 记录中的失败原因

原physical_valid要求无abort且external penetration≤0.2mm，门槛未改变。

|方法／条件|32穿透峰值mm|33穿透峰值mm|32→33结果|
|---|---:|---:|---|
|阻抗 short0600|.218649|.198514|Task均成功，Strict失败→成功|
|导纳 long0300|.096766|.045914|Task/Strict成功→失败，物理仍有效|
|导纳 short0600|.183458|.232938|Task均成功，Strict成功→失败|
|VMC short0000|.154151|.218823|Task均成功，Strict成功→失败|

三条短期条件的最坏外部接触分别为球与hand/link6/link7；记录峰值跨越原0.2mm门槛。阻抗33仅低于门槛.001486mm，不将一次通过写成鲁棒安全。所有8回合完整55秒、无abort。这里是原保存峰值与标签核对，不是原始物理子步重演，也不证明随机性或学习漂移的因果份额。

导纳long0300呈现不同问题：32进入lift为2.04s、carry6.32s、load_transfer40.72s、release41.20s、retreat41.72s，完成认证42.04s；33进入lift1.88s、carry20.84s，此后一直carry至55s，没有load_transfer/release。lift阶段持续4.28→18.96s，进入carry推迟14.52s；不能据此声称仅延长时限必然成功，也未改55s预算。

33终点物块位于[.693712,−.309759,.556497]m，但未卸载释放；位置接近目的地不能替代完整Task门。末次保存WBC位置误差.012927m、ready计时0；名义路点位置阈值.012m、姿态.12rad、速度.025m/s及.20s持续就绪要求来自原源码。WBC误差不是完整route cursor/目标选择/ready guard重演，不仅凭这一列认定具体条件分支或产生延迟的动作原因。

## 时间戳核验与证据范围更正

原执行脚本保存在诊断目录`executed_audit_v1.py`，SHA ba7046a455450689143893011c4181254e7779947a4a86bf70e82a70d1acdf2f，与原REVIEW source hash一致。初版REVIEW limitation中“last saved sample precedes terminal time”描述不准确；已另存`TIMESTAMP_CORRECTION_REVIEW.json`明确覆盖这句话，保留原报告和源。

实际`time`是区间末物理时间，最后55.0000000013s；`neuron_time`为区间初控制特征时间，最后54.9600000013s。两轮全部1375行差值均.04s（浮点容差2e−9）。此前快速查看的物理54.96s行误差12.844mm不是最后一行；最后控制记录误差12.927mm。原图、峰值、阶段时序和原REVIEW数值不变。提交的后续脚本加入neuron_time并修正文案，AST及实际保存字段核验通过，未重跑原分析或改变正式源码。

## 原训练和后续

Direct21原2826774；参数34原I3926666/A3926667/V3926668仍运行，归档/完整review保持。Direct22准备2851849/2851880、参数35准备3957991/3958081只完整父审查后check-only，无自动训练。Direct20–22固定审计3124904、参数33–35固定审计2585589继续，不能用本诊断替代稳定性结果。
冻结32原2466385/2466386/2466387与根2466388继续90回合，尚未完成根REVIEW。最新进度和原PID身份见LIVE_STATUS；不重复已完成冻结或终端诊断。完整接续上下文见[参数34交接](RL_PARAMETER34_20261027.md)。
本轮查询/fetch/read远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变；GitHub认证和指定ESN已问，不重复索取。SSD新小证据包和HDD小交接收据另记，大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。
