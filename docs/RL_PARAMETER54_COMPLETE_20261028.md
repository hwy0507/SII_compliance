# 参数54完整结果与参数55续训交接（2026-10-28）

Goal active。Direct33已满足原训练条件下的经验数值标准，不启动34；Task/Strict仍0/0，不能称任务成功。参数RL仍未满足reward稳定且loss无异常的整体要求。用户要求全部工作结束后仍保留GPU负载，独立GPU守护v4继续运行；合成计算不计为科学进度。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；计算主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮重新查询、fetch并读取main `076b86aa549dfb1fd723e3c24f057c1f76071c04`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`日志，科学约束未变。训练解释器仍`B/env/bin/python`和冻结runtime；没有更换环境。

## 完整54结果

完整checkpoint位于`B/runs/parameter_capacity_pool30_cycle54_archive_20261026_v1/{impedance,admittance,vmc}/cycle_00054.pt`。完整review和health已结束，原monitor2116861退出。全部旧replay/history保持，新增reward重建误差0，网络和优化器有限；保留4m容量及历史entry23/47双marker。health只读，网络状态不变。已查看loss图和health图，不是独立重跑全部物理。

| 方法 | steps / updates | 新增transition | reward均值 | Task / Strict（分母30） | 完整55秒 | critic首→末1000 | critic最大 |
|---|---|---:|---:|---|---|---|---:|
| 阻抗 | 2264148 / 2259149 | 40468 | −6.094248680 | 17 / 15 | 29/30 | 2.838518→3.795605 | 44.500523 |
| 导纳 | 2264750 / 2259751 | 41250 | −15.300869421 | 11 / 10 | 30/30 | 1.417623→1.521901 | 23.370565 |
| VMC | 2265750 / 2260751 | 41250 | −4.581375944 | 17 / 16 | 30/30 | 0.900831→1.062000 | 43.223648 |

阻抗/VMC末段loss抬升和峰值均保留；导纳53→54平均reward下降6.775965640。有限数值并不等于无异常或收敛。terminal in-bag MAE分别.448091/.334767/.321057；固定pair未投影TD MAE .268986/.230001/.174995，此诊断不等于A/V实际mean和投影训练目标。A/V采样Q超当前alpha必要上界比例.0010742188/.0011230469，非零如实保留，不作Q校准结论。

checkpoint SHA256：

- I `419314b88864ed089984d59887ed2ddfe89830f3d3ff3b78072f2157fa78f5da`
- A `ab923e8db59bf691e69465f8beec8efe09478064fa482cb1d6262d4201ec240c`
- V `26ce20535667e85735ff8823950a823fb504be86e69d36d762338b1fc99f5da2`

## 阻抗提前终止与审计修复

`active_long_train_0000`在593动作、23.7200000002秒、总step2252692发生`global_penetration_exceeded_2mm`。保存的最坏碰撞对为`office_v5_corner_top`/`target_object_geom`，全局穿透98.36443964mm；外部机器人穿透仅.056510901mm是另一指标，不能抵消全局终止。Task/Strict/physical_valid均false，reward−40.60509754。相同53条件完整1375动作/noabort，global .162902mm，同MJB与执行evaluator哈希。所有失败保留在30条件分母，没有填补缺少的782步。

终止step附近前后1000 loss为2.333296/2.410468；时间接近不能证明该样本导致后续loss尖峰。short0100 Task仍成功，但外部穿透.183592→.215793mm跨原.2mm Strict门槛。保存配对gate审查覆盖Strict或abort变化，包含Strict false→false的本次终止；没有更改门槛或独立重放动力学。

完整loss脚本原来错误假定每路41250条，因此初次失败。保留`FAILURE.json`、原脚本、日志及diff，仅将长度断言改为实际30回合steps总和，确认唯一条件、连续step、全部有限、均值和峰值独立复算。配对脚本只扩展记录范围到abort变化。恢复审查`RECOVERY_FINISHED.json`及`SAVED_REVIEW.json`通过，不能掩盖最初失败。

## 55正式运行与后续

训练恢复waiter2450050完成并退出。三路准确54全learner state、全部replay/下一65536和RNG check-only通过，退出0/0/0。`B/runtime/prepare_parameter55_20261028_v1/DECISION55.json`在启动前固定完整54/health/loss/paired/abort/check-only哈希，明确承认上述问题，只批准一个有限55完成原前瞻53–55窗口，无自动56；不改LR、reward、gate、physics、batch65536、UTD1、terminal128、pair规则或容量，不导入辅助权重。

正式目录`B/runs/parameter_capacity_pool30_cycle55_20261026_v1`：I/A/V PID4101991/4101994/4101996，start ticks均36044802，分别GPU1/2/3与原CPU13–25/26–38/39–51，每路30sampler。archive/review PID4102000和startup PID4102002启动信息在相应LAUNCH文件。进程行动前必须同时核PID与start ticks；观察超时不能据此重启。

原53–55稳定性waiter514418/start35382586保持，脚本已经使用`len(optimizer)==new_transitions==sum(episode.steps)`并核实际full_horizon，适配54真实40468，无需改代码。原53–55窗口、seed2026102852、5000bootstrap、5%和nearzero1全部保留；超时失败若发生也必须保留，不能换结果选择窗口。

冻结55在训练前已登记三方法×原30条件、同41外部seed2026102638，总90回合。原仅恢复waiter3641528/start35932846继续，先等待55完整归档/审查并退出再check-only；没有自动物理派发。随后仍需实际55恢复与PRELAUNCH审查，不能把已完成53验证算成55验证。参考[冻结55登记](RL_FROZEN55_REGISTRATION_20261028.md)。

GPU守护v4 supervisor1629438/start35566457、workers1629439–1629442（start35566468/35566468/35566469/35566469）保持，无STOP。后台运行至显式停止或系统关机，即使正式训练/评测退出也继续；不是跨重启服务。原固定60样本全部≥50%证据保持，本轮恢复即时79/70/74/72%，包含合成负载，不保证所有未来瞬时采样。

## 保存与下一次续接

完整诊断源在`B/runs/parameter54_loss_20261028_v1`、`B/runs/parameter_capacity_pool30_cycle54_review_20261026_v1`；小证据副本在`docs/evidence/RL_PARAMETER54_COMPLETE_20261028`，含原失败、修复diff、两图、55决策和恢复/启动信息。大型checkpoint/replay/raw仍在共享SSD，未宣称HDD或arm1完整备份。HDD既有LATEST仅作入口。小包及核验收据见同目录`SAVE_RECEIPT.json`。

下一步先查55真实startup结果和进度，保留原进程；随后完成55归档/health/完整loss、原53–55统计和实际冻结55恢复/评测。整体Goal保持active。

新完整55保存审查waiter45441/start36069767已启动，`B/runs/parameter55_loss_20261028_v1`，固定7200秒，绑定55原PID/ticks、完整结束后才运行loss及54→55配对gate。继承已修复实际episode长度断言，保留所有30条件/abort；这是55启动后登记的描述性审查，不冒充启动前预登记，不替代原53–55统计，无自动续训。

55实际startup已通过：I/A/V首批新增1000/1000/2000，旧2264148/2264750/2265750行replay全部字段精确保留，history/优化器配置/4m双marker/30MJB及每路30sampler核验通过；动作和clock映射与新reward重算误差0。证据`stage55/ACTUAL_STARTUP_REVIEW.json`，此启动前缀没有终端，不能代替完整55审查。

共享SSD核验小包：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER54_COMPLETE_20261028_052418/SMALL_EVIDENCE.tar.gz`，718764字节、66来源成员，SHA256 `d2a24fe2ef86ed38b273f665e4c7dfba4c178d6eef8ae2ac043bf7c0cfa86b5b`；全部归档成员逐字节比对通过。收据在小证据目录，收据自身不在此包内。
