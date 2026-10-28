# 冻结参数55全30条件预登记与4m恢复验证（2026-10-28）

Goal active。三参数54原训练继续，Direct的[数值收敛阶段决定](RL_DIRECT33_ASSESSMENT_20261028.md)保持，不追加34。GPU守护v4继续。**本轮完成的是冻结55方案、4m入口验证和等待准备；实际55训练、实际55恢复和冻结物理评测均尚未开始。**

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮实际查询/fetch/read main `9e5a0aa41c0ccb91a47c7f82bc792475e7a247c2`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，没有新RL约束变化。遵循已应用的sii-research-sync，无子agent。

## 55评测方案在55训练开始前固定

`B/runs/parameter55_frozen_full30_20261028_v1/PLAN.json`

SHA256 `906bb31f23a3c63b49edc5e298407c284c81af173cd3d5f816581c4325fac986`。

原53–55稳定窗口的终点55作为预定冻结checkpoint，无论以后结果好坏都不换轮次/条件/seed。注册时54三原learner身份均live，正式55 LAUNCH和完整55 archive不存在；REGISTRATION_REVIEW再次验证55未启动。固定三方法×原30条件=90回合、每回合最多55秒，总上限123750动作/99000000物理子步。沿用冻结41/32的外部action seed2026102638及相同30个fixture/MJB。原gate/reward/filter/torque/SPT/物理与随机策略调用方式不变，0优化、0正式replay写入。

预定与已完成冻结41配对比较。41使用2m replay，55使用4m且原entry23/新entry47保持；COMPARISON_LIMITATIONS单独披露容量与训练曝光差异，不把两checkpoint比较当容量单因素因果实验。单训练seed、单动作seed、训练条件上的冻结结果，不替代held-out泛化或指定ESN/最终SPT交付，也不另加训练收敛门槛。

## 4m入口与准确53只读验证

新runtime：`B/runtime/parameter55_frozen_full30_20261028_v1`。继承冻结41的21个helper原字节，20个可与当前54 runtime对应的公共模块hash一致；新增当前正式使用的`parameter_replay_capacity4m_20261027.py`。新evaluator只调整55元数据与4m恢复约束、验证53仅check-only入口；从`results=[]`起完整物理loop与41逐字节一致。保留原2m历史marker，新增校验4m followup/entry47/源hash/entry checkpoint，完整replay digest精确，不进行容量迁移。

已用三份真实完整53 archive执行新版入口，原validator3567562及三子进程均完成，退出码0/0/0：

- 完整learner（含优化器/RNG）与全部4m容量replay恢复digest精确，检查前后learner/replay不变。
- 各方法原生随机动作与外部seed流的前三次动作逐值一致，同seed一致、不同seed改变动作，两个非法seed被拒绝。
- 原53 checkpoint SHA分别56653f09…、93330d32…、88807530…；完整hash见validation53/REVIEW与REGISTRATION。
- 0新物理/0优化更新；这是53真实恢复验证，**不是55真实恢复或55评测通过**。

`--validation-cycle 53`只有搭配`--check-only`才可用；误请求53物理在读取checkpoint/创建EVALUATION之前拒绝，预期失败及收据保留。未获得55实际恢复时调用物理launcher也按预期拒绝，没有启动任何物理进程。新evaluator及rootreview源已逐字节复制到仓库tools；所有冻结源和执行入口另有manifest。

## 后台准备与实际物理入口

冻结55准备PID3641528/start35932846，固定14400秒。它等待正式55出现时绑定第一次LAUNCH的hash与全部原learner身份；完整55退出、archive/review/health通过后才生成准确55注册并运行check-only。它不会启动物理或正式训练。check-only观察上限600秒，若超时保留原子进程身份、不自动终止或重启；需检查同一原进程。实际准备结果看`CHECK_ONLY_COMPLETE.json`，当前尚不存在。

后续手动`launch55.py`需要准确55 check-only与单独科学PRELAUNCH记录；固定90回合不自动扩预算，rootreview等待上限21600秒。使用已释放CPU0/1/2分别给I/A/V、CPU3根审查，三模型均用GPU0，CUDA可见集合保持0,1,2,3以恢复保存的CUDA RNG。每方法推理与一个串行物理worker共享其指定CPU。当前正式训练仍CPU13–51/GPU1–3，每路30sampler，未改其资源亲和或学习设置。

注意两个55等待任务不同：原`B/runtime/prepare_parameter55_20261028_v1` PID2450050负责**训练54→55恢复**；本轮3641528负责**完整55→冻结55恢复**。不可互换或重复启动。原53–55 reward waiter514418继续，未改5%/nearzero1/bootstrap/seed。

## 当前训练与保存

05:03 UTC身份核对：参数54 I/A/V PID2116858/2116859/2116860，steps2259471/2259487/2260731，完整条件18/17/19，原归档2116861继续；无失败。GPU守护supervisor1629438及四worker继续，当前即时四卡70/90/70/98%，含合成负载、不代表每瞬时永久保证。Direct33已完整保存，GPU0保活保持。

小证据`docs/evidence/RL_FROZEN55_REGISTRATION_20261028`；共享SSD包包含全部27个runtime源码、预登记/准确53恢复/拒绝误启动及进程证据，48来源成员逐大小/hash核验：

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_FROZEN55_REGISTRATION_20261028_050310/SMALL_EVIDENCE.tar.gz`

50890字节；SHA256 `837c7f2fb441ca494722cf53ec86077241f71dad8a96ec5183df6001c99b4a86`。

大checkpoint/raw留共享SSD，HDD仅更新LATEST入口，非HDD/arm1全备份。下一步读取完整54 loss/reward/health、准确55训练恢复并作有限55决定；冻结55等待同时保留，不把当前准备写成实际评测完成。
