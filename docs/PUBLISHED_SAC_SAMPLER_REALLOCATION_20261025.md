# SAC完整周期边界采样资源调整（2026-10-25）

原CHEQ all5在线10/11阶段和120回合名义矩阵已经完成，释放的CPU可用于原SAC真实物理采样。本次只调整原SAC采样并发，从每接口2个worker增加到9个；保留同一个source_train09、同一个REGISTRATION_SAC_PERFORMANCE_V2.json字节内容和全部科学设置。不是新的学习稳定性干预，也不是收敛或最终比较结果。

## 登记和已执行部分

独立资源协议`runs/SAC_SAMPLER_REALLOCATION_V1.json`与冻结协调工具`runtime/sac_sampler_reallocation_v1`保存于集群SSD根目录：

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`

协调器691298已登记并向四原learner写入STOP_REQUESTED。这些文件表示完成当前完整30条件周期后交接，不表示取消Goal，不能删除后重启旧进程。当前VMC已完成交接；Direct、Impedance、Admittance仍由原进程完成当前周期。请先读COORDINATOR/MIGRATION_PROGRESS/LAUNCH/FAILURE再行动，禁止另开相同队列。

| 接口 | learner CPU | sampler CPU | GPU | 本次快照状态 |
|---|---:|---|---:|---|
| Direct | 10 | 1–9 | 0 | 原1010728完成cycle6后交接 |
| Impedance | 23 | 15–22、24 | 1 | 原1557140完成cycle4后交接 |
| Admittance | 36 | 27–35 | 2 | 原2758791完成cycle3后交接 |
| VMC | 49 | 40–48 | 3 | 原2397784正常结束，新726082实际更新cycle4 |

四个有限折扣probe的CPU0/14/26/39、只读观察CPU13、协调/归档CPU54保留；新分配也不与仍在收尾的其他接口旧CPU重叠。迁移归档器691379在兄弟任务尚未交接时便观察新learner，避免先启动者的完整周期被错过。全部交接后协调器启动正常归档并退出，训练独立继续。

VMC父checkpoint在完整cycle3保存186009真实环境步、330000优化更新；SHA256为`7a62caf02e093c8bf222a67476f1e14d240ffb37a70e67d3c08c815f55f69fef`。原文件、新副本和新EXECUTION的resume hash一致。新进程已超过父steps/updates，首份验收快照为186807/331596；9个真实worker分别绑定CPU40–48。既有load路径保留网络、target、Adam、alpha、learner/replay RNG、replay与cycle history；EXECUTION确认没有fresh optimizer。原registration里的历史restart_reason文字随字节不变保留，本次原因以独立资源登记为准。

并发增加会改变采样到达顺序和后续动作RNG交错，因此不能声称迁移后轨迹逐位等同原双worker运行。所有科学参数、batch16384/UTD2、奖励/折扣、actor输入、公共filter、执行器限制、physics/MJB、gate和dt保持；未部署source16，也没有改变CHEQ下一阶段选择。

## 验证与GPU观测

6个迁移守卫测试通过，覆盖有效配置、保留CPU/新worker冲突、尚未退出兄弟作业冲突、陈旧PID、未知接口、GPU变更、worker计数及不完整/不匹配checkpoint拒绝。初版测试夹具误占保留CPU14，被守卫抓住并在派发前修正；未发生训练失败。

原runtime的777个source、24个parameter、150个上游代码与128个robot资产实际文件哈希全部核验，30条件及参考计划哈希一致。VMC首9个新环境的实际MJB均匹配原登记、55s/dt5e-5、actor48/action7和无truth输入核验；这是启动验收，尚非新cycle4完整物理审计。旧VMC cycle3归档已被原observer3759872识别，其仍等待Admittance3，未重复派发审计。

迁移期间60个GPU样本、66.53s窗口均值为59.65/57.20/58.10/65.35%，最小20/43/12/10%。该窗口包含原/新SAC和四个有限折扣probe，不能称正式训练独立达到50%，也不能声称每时刻高于15%或50%。真实物理吞吐提升幅度须等可比完整周期测量，不从worker数量直接推算。

## 未完成工作

四有限probe仍用原PID361333/361334/361335/361336运行，首个gamma arm各50000更新已完成，第二arm正在推进，完整配对结果尚未科学review。每路总100000、四路总400000辅助更新预算未扩大，不保存/推广辅助权重，无新增physics。不要将不同接口先完成的不同gamma互作配对比较。

剩余三接口交接、新完整周期健康审计、延长折扣诊断的完整配对分析、下一CHEQ在线阶段、充分收敛证据、固定策略全训练集矩阵、共同事后Tref/SPT和指定ESN公平比较均未完成。既有SAC critic诊断不健康；更多采样不是修复结论。指定ESN checkpoint仍未提供，不用历史ESN代替。

本轮fetch/read两分支：main a52dfba、baseline f6e8f8c，远端无新增变化；GitHub发布情况以实际push结果为准。小型证据索引见同名JSON，原始产物保留SSD，不提交轨迹、环境和权重。
