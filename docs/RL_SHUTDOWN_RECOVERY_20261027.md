# 2026-10-27 用户关机暂停：最新 RL 恢复交接

**权威状态：paused。用户要求24小时强制关机前保存，之后重新开机再明确要求继续。未获恢复指令前，不启动训练、物理评估、诊断或等待派发器。** 此状态覆盖本仓库此前所有“Goal active / 继续25或41”的历史记录，也覆盖保持GPU占用的偏好；不是训练目标已完成。

本次通过Goal工具置为paused；四正式learner、采样子进程、归档器、完整审查及后续等待器均已退出。关机前的保存、文件校验和文档整理不属于继续训练。没有操作其他机器的非RL任务。历史PID只作溯源，下次不能据PID判断运行状态。

## 从哪里接手

- 本文：`/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/SII_compliance/docs/RL_SHUTDOWN_RECOVERY_20261027.md`
- HDD固定入口：`/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/LATEST_RL_HANDOFF.md`
- 新独立暂停快照 O：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/user_shutdown_pause_20261027_v1`
- 共享SSD基础目录 B：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。仓库实际B/repository/SII_compliance，原HDD仓库路径为链接；共享文件系统为gpfs_flash。
- 先读O/HANDOFF.md、O/RECOVERY_MANIFEST.json、O/PENDING_WORK.json及本仓库AGENTS.md顶部。

**Direct已经是当前SERL训练，不能按旧2026-10-26文档的“下次从零初始化”再fresh reset。** 当前四路完整optimizer、replay、RNG、历史都必须保留；不重跑完成实验占GPU。

## 已保存的训练状态

|方法|首选快照|周期/边界|真实步数|更新数|
|---|---|---|---:|---:|
|Direct SERL|O/direct/checkpoint_before_interrupt.pt|25，部分周期|1,039,290|8,274,328 critic / 1,034,291 outer|
|Impedance|O/impedance/complete_cycle41.pt|41，完整周期|1,728,680|1,723,681|
|Admittance|O/admittance/complete_cycle41.pt|41，完整周期|1,728,500|1,723,501|
|VMC|O/vmc/complete_cycle41.pt|41，完整周期|1,729,500|1,724,501|

另存完整边界后备：O/direct/last_complete_cycle24.pt（1,018,290步/8,106,328critic updates），以及各参数O/{method}/complete_cycle40.pt。这8份首选/后备文件逐SHA256、torch反序列化、回放容量/长度/游标和raw数组finite核验通过；完整网络/优化器序列化字段保留，不冒称已在新进程GPU恢复测试通过。

主快照SHA256：

- Direct部分25：`f765ef4a5b256097e3c17365ee4305088d943cbdcdb7447a3edbfbeb24eda6ca`
- Direct完整24：`112eda44c8cda14c5f3b4b3ce934dab7882fa254ac516e1ca4e1b5e24fe852e4`
- Impedance41：`5348e1ccec12e1e58ecb28d5c85b2cdc7a965c54e98ca642facc085e9011b307`
- Admittance41：`3678581d424cf26110ab460bda212353e38954334f7724ffa84a8cc5b9e2aef9`
- VMC41：`494a516017696650cdf30661ba0a18a29becb5289147944c921e5fa97f256bea`

源文件仍保留于B/runs/serl_capacity_batch65536_cycle25_20261027_v1/direct以及参数B/runs/parameter_capacity_pool30_cycle41_archive_20261026_v1/{method}/cycle_00041.pt。独立快照是额外副本，未移动或覆盖原件。

## Direct部分周期恢复必须先审查

先从原子发布的checkpoint_latest打开同一inode、复制并fsync首选快照，然后才给learner2350595发送SIGINT。原STOP_REQUESTED只在外层cycle检查，不能及时结束当前30并行回合，因此用原异常处理保存并关闭sampler管道。原FAILURE.json中的KeyboardInterrupt是用户关机中断，不是算法崩溃证据。

原日志最后PROGRESS为1,039,448步；FAILURE为1,039,470步。首选快照止于1,039,290，差180条已执行transition未包含在首选快照内。额外保留O/direct/checkpoint_after_interrupt.pt及DIRECT_POSTINTERRUPT_COPY.json用于对照；它可能处于优化器更新中途，**不得自动替换首选快照**。

首选快照的2m回放中：raw1,039,290条、成熟1,038,360条、930条pending，30个stream各31条。全部原始/派生回放、pending队列、RNG、网络/Adam、历史都保留，但**没有MuJoCo环境状态**；当前25轮0个条件完成，30个均部分进行。

现有 `resume_serl_capacity_reviewed_continuation_20261027.py` 仅允许完整周期父，不能直接拿partial25跑该入口。恢复后必须独立新run、登记首选snapshot hash并实现/审查中断stream恢复语义：不能把新环境起点接在旧pending轨迹后，不能伪造自然终止奖励，不能静默删930条pending或重置优化器/replay；保留原未完成数据及其实际曝光预算。只有恢复语义和完整state核验通过后才续训。完整24是明确后备，不授权自动回退丢弃已经保存的21,000条新增训练数据。

原Direct24–26稳定窗口也受到25中断/重新起环境影响，恢复时须明确审计原窗口是否仍适用，不能把中断前后预算或周期身份假装连续不变。26尚未启动，原25完整审查尚未完成；不能伪造完整25父来解锁26。

## 参数41已完成并有原审查结果

三参数均30×55秒、无abort；原REVIEW/health/FINISHED在暂停收尾时已完成，网络/优化器finite、旧replay保留、新41250奖励重算误差0。没有新启动42。

|方法|Task / Strict（各30）|平均reward|末1000 q_loss|terminal MAE / in-bag|
|---|---|---:|---:|---|
|Impedance41|18 / 18|−0.585221688|2.042269511|0.755266 / 0.240873|
|Admittance41|12 / 11|−13.768370154|1.458500792|0.738283 / 0.285862|
|VMC41|17 / 16|−4.610525251|0.935056174|0.726684 / 0.409143|

这是已保存原审查值；本次关机保存没有继续新的科学诊断、paired结果复算或bootstrap。整体仍未健康收敛。A41终端误差较40下降但任务/回报退步，VMC41末loss较40反升，不能只看一项称恢复。

原完整审查目录：B/runs/parameter_capacity_pool30_cycle41_review_20261026_v1。恢复参数42时必须capacity replay + pair learner、2m append/history entry23、全optimizer/replay/RNG/history；原42准备仅有脚本，实际check-only尚未执行。

## 已完成事项与停止的后续事项

已完成、不要重跑：

- Direct完整24、参数完整40/41的原审查；Direct首次百万边界检查。
- 冻结Direct16全30、参数32全90及其原物理/filter/torque审查。
- 导纳39→40全部终端诊断：固定1194旧行SSE+42.04%，1069变差/125改善，新30占40终端贡献16.4%；见RL_ADMITTANCE40_TERMINAL_20261027.md。
- VMC固定1164跟踪39、阻抗39保存姿态静态碰撞检查；不重复。
- 新Direct容量冻结入口的实际24恢复v4已通过，0优化/物理。CPU/GPU可见性失败与更正均保留；不是实际26物理评估。
- 原纯25/41 GPU窗口60样本/69.37秒均值58.32/59.08/58.72/58.50%，非每瞬时保证；暂停后允许GPU空闲。

已停止，恢复后先查实际产物再登记/接管，不按旧PID盲目重启：

1. 参数39–41固定稳定性审计（原3482651）：原PLAN/seed2026102743/5000/5%/近零1保留，三完整输入现已齐，尚无最终统计REVIEW。
2. 导纳固定1224跟踪41（原2937574）：PLAN固定40全终端及旧分母，完整41现可用，实际跟踪尚未执行。不要重跑39/40诊断。
3. 参数冻结41（原准备1833369）：PLAN全30×3/seed2026102638、最多123750动作/99000000子步；实际41check-only与物理评估均未执行。
4. 参数42准备（原2397589）、Direct26准备（原2397737）与释放CPU调度均停止，无自动训练。
5. Direct24–26稳定性等待（原1470790）停止，25为部分周期，窗口适用性须先审查。
6. Direct26冻结准备（原3528782）停止：全30/seed2026102626、最多41250动作/33000000子步；实际26恢复及物理评估未执行。原计划先等参数冻结41释放CPU53/54；恢复预算/时限需重新记录，不能将过期等待当成实验失败。
7. 参数41→42衔接observer（原3568920）因用户暂停停止；42未启动，不应把关机期间计作普通续训换轮耗时。
8. Direct25完整审查等待（原2350599）停止，无完整25；原归档器已随learner结束退出。

## 环境、冻结约束与存储范围

Direct解释器B/serl_env/bin/python；参数/物理/审查B/env/bin/python。固定runtime B/runtime/source_train17_clock，官方SERL B/runtime/serl_upstream_1fa2af7，commit1fa2af7496be042e43d36120a7c8d1b71f1bfb59。

Direct10critic/随机2min/noentropy backup/8critic:1actor/batch65536/32步behavior目标、2m replay保持；参数CHEQ、terminal128、target Imin/A-Vmean、actor min、2m历史entry23保持。physics/MJB/Task&Strict gate/filter/执行器/dt5e-5/canonical48/原30条件/SPT reward保持。半执行器限值是工程参考，不是人体舒适标定。

O/FROZEN_SOURCES_AND_KEY_RESULTS.tar.gz及DEPENDENCY_ARCHIVE_RECEIPT.json保存冻结runtime/官方source、fixture/MJB、历史登记与计划、当前关键日志和结果，并逐成员大小/hash核验。检查点单独存放，避免归档时误把半写文件当有效副本。原B/runtime、B/runs及两个Python环境必须保留：原始全历史轨迹、全部历史诊断依赖、大型第三方资源及环境并非都额外复制。

HDD配额满，新快照与归档在共享SSD。既有HDD LATEST覆盖回读，指向O/HANDOFF.md；**没有声称这些新大检查点已备份到HDD或arm1**。本地Git提交和独立Git bundle保存未推送源码历史；GitHub仍可能因HTTPS用户名认证不可用而失败，不能以远端代替这份交接。

## 用户明确恢复后执行顺序

1. 读取本文和O清单；检查新机器挂载、文件hash、两Python环境、GPU/CPU及是否有重复任务；真实fetch/read main和baseline日志。只在用户新恢复指令后恢复Goal。
2. 优先审查Direct partial25的pending/环境/优化器边界，保留所有已落盘状态，独立恢复run；不得fresh reset或自动回退24。
3. 读取完整41原review/health；执行尚未完成的保存值复核、原39–41统计及固定1224跟踪，不重算已完成物理回合。
4. 完整41全state恢复check-only后科学判断参数42；为缩短空档，登记有限后续阶段并实测GPU。不能自动无界训练。
5. 按原冻结41、Direct26计划完成实际恢复和有限评测；Direct26依赖完整25/26及中断窗口审查，不能跳过。
6. 继续原目标：reward稳定且loss无异常、冻结验证和最终公平比较。完整学习无改善的平坦曲线应称停滞，不能宣布学会；保留失败，不改物理门或用GPU占用替代收敛。

## 关机保存完成收据

8份主/后备快照及1份中断后取证副本共8929265735字节（8.316GiB）；源码配置/关键结果包819111777字节、5031成员逐大小/hash核验，SHA256 6c0d2294fc32b420dc916fc196a7c8036c0dcef010c5994db84f899246588ebf。独立Git bundle 193419247字节、SHA256 14f2690991e3d90c7154c4f5d019482af87f17c36d48abfa9dfd67a1d674657a，git bundle verify通过、含完整历史及本轮交接提交a0136bb3ddb72261ef103cae685ecdc1778a5e98。GitHub push仍HTTPS用户名认证失败；以本地仓库/独立bundle和共享SSD快照为准。FINAL_STOP_STATUS确认项目任务与GPU计算进程为空，Goal paused。
