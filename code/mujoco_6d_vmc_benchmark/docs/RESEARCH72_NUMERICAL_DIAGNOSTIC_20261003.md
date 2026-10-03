# 首次球撞的有限数值步长诊断登记

2026-10-03 22:02:45UTC已登记并启动有限等待进程，**当前没有新数值诊断结果**。
动机是此前170公开轨迹的首段球接触仅0.45–0.50ms；需要分开报告物理接触模型和采样步长对尖峰的影响。
不根据这项检查重新选择控制器、放宽gate或修改正式对比步长。

固定使用已公开train_000与原始teacher，读取原teacher配置hash，禁止使用新选teacher或封存身份。
执行三条各3秒的前缀：dt=1e-4、5e-5、2.5e-5；最多9模拟秒、210000物理子步。
保留原55s任务定义，利用已有`physics_probe_s`提前结束，故探针永不具备task/strict成功资格；
也不能把探针记作完整任务失败，更不能作为新增示范。正式统一比较仍为55s、dt=5e-5。

二进制模型只改变`opt.timestep`：更改后计算hash，再恢复原dt并要求整个MJB字节hash精确相同。
几何、接触材质、actor周期、4ms servo、动作过滤、执行器限制、teacher参数和扰动身份不变。
对5e-5探针，还要求time/qpos/qvel/ctrl/observation/action与既有完整train_000相应前缀逐值相同。
失败/中断原样保存，不自动重试。计划报告球接触峰值、力模积分、接触时长、首次接触时间、外穿透和力矩/速度。
力模积分不称有符号净冲量；单个已知条件的短前缀也不证明全程收敛、跨方法优势或人体安全。

服务`sii-r72-numerical-probe-v1`，登记时PID2403221，MemoryMax3221225472、CPUQuota100%、库线程1。
等待`followup_v1`全部未使用租约的旧队列结束后，再取得四个共享租约之一；worker同时要求存活的租约owner。
不会与现有四仿真叠加成第五个。截止为原开发截止10-05 11:30UTC，不创建定时任务。

已完成工程验证：原生Spark/本地各通过3项模型序列化与角色检查；最后版本同样通过。
另4项预算及2项成本账本检查通过。新账本对诊断保留attempted/completed/墙钟成本，
但不将已知重放成功或短探针false算进任务成功/失败分母。预测器对已登记短探针保守按3个完整回合收费，
避免遗漏启动/排队成本。这些工程测试不包含物理积分或接触效果。

22:05UTC初始开发246/264，第七身份已完整：ESN/matchedRNN各4/6task、1/6strict；
matchedMLP2/6strict、memoryless1/3、普通MLP1/6、普通RNN0/6。仍为初始候选开发计数；全阶段独立审计未完成。
原四队列稳定，teacher确认、增强学习组、RL及新诊断都等前序，最终24身份仍封存。

主机`arm1@192.168.31.70`：

- 协议：`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/public_numerical_probe_v1/SPECIFICATION.json`，
  SHA256 `234712686ed7ee00571a0ec3886c3f134ae33c91631d87024111cdb67ca892a2`，Git证据为同字节副本。
- 执行状态：同目录`execution.json`，目前`waiting_for_predecessor`、rows为空。不能将active服务当作已完成物理工作。
- 实际runtime：`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149_numerical_runtime_v1/`，
  base main f40b1ad05d43373c380d71b06807b7ee9785a8b7的525个scripts/tools/assets文件逐hash一致，仅添加诊断和测试。
  实际脚本SHA`86a8d8907b93464d9a2c42ef46431534f1cd2697e486e1a04951f8a91b445a36`。
  属于base＋已记录overlay，不能称干净commit执行；旧训练runtime未改。
- 最终overlay：`/home/arm1/sii_shared/SII_compliance/incoming/research72-numerical-overlay-v2.tar.gz`，
  SHA`c722b43ba619c67d5588a4f8df33f837850e56c980028f7f8058a5a13c567e60`，两端一致。
  先前v1仅做零积分工程检查；在任何诊断派发前加入存活租约owner校验，实际登记的是v2脚本hash。
- f40b1ad完整源码已在`/home/arm1/sii_shared/SII_compliance/source/f40b1ad05d43373c380d71b06807b7ee9785a8b7/`
  核验3206文件，tar SHA`4139bca72fd41b21393b8294f016e3028958ae69402c8dc7bc4c9abd565f3844`。

数值检查未增加学习候选cap；可选ESN读出修订02仍未登记，不能借该诊断名义训练新模型。
