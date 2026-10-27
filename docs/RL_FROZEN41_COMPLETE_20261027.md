# 参数第41轮冻结全90完成及32→41配对对照

2026-10-27，Goal active。四正式训练48/29持续，冻结41原90预算已完整结束，不重复物理评估。此完成是冻结评测里程碑，不是四方法训练收敛或最终比较完成。执行主机 `rltest-1025--a6ed2ff39b3c-z3ntpmmalx`，共享SSD根B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，源码B/repository/SII_compliance。

本轮实际查询/fetch/read main `1db94305e7772f9de226607dbdae78759283395c`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新环境/算法/物理改动；沿用sii-research-sync，无子agent。上一轮48/29实际接续及启动审查属于实质进展。

## 完整90冻结评测

`B/runs/parameter41_frozen_full30_20261027_v1`：原I316550/A316551/V316552及rootreview316553均完成退出。每方法固定30原训练条件、同外部动作seed2026102638、每回合55秒。实际123750动作/99000000物理子步，90全horizon，无abort。全部原生随机参数动作重放、原公共filter/torque和物理审计、source/checkpoint hash及完整learner/replay前后不变通过，0优化/replay写入。原root REVIEW SHA `efcfae5cb59c6a77348cb2a77ab2f600f07488085079bd26a38c837bbcae6c72`，总览图已目视检查。

逐方法最终Task/Strict为I18/18、A14/13、V17/17。导纳 `active_short_train_0600` Task真但Strict假，最大外部穿透.212086833mm超原.2mm，原机器安全违规标签保留（1/30）；I/V各0/30。无abort不代表没有安全违规。

## 预先指定的冻结32→41对照

原41 PLAN在训练41开始之前绑定完整32 REVIEW，固定相同30条件与seed。新 `B/runs/parameter32_41_frozen_comparison_20261027_v1` 已完成：核验PLAN绑定、全部条件/fixtures/MJB、21共同执行审计模块hash相同、6个checkpoint/hash、保存90+90结果与原review/FINISHED一致、learner/replay不变。只读保存算术，0新物理/优化/神经前向，无额外bootstrap或seed。

|方法|Task/Strict（32→41，各30）|平均reward（32→41）|配对平均差41−32|机器安全违规数（32→41）|
|---|---:|---:|---:|---:|
|impedance|18/18 → 18/18|-0.471887622 → -0.528457769|-0.056570148|0 → 0|
|admittance|13/12 → 14/13|-11.918260986 → -10.422220086|+1.496040900|1 → 1|
|vmc|17/17 → 17/17|-2.792317951 → -2.909769682|-0.117451731|0 → 0|

I/V所有成功标签保持，回报略降。A新获short0900/long0900的Task与Strict，同时丢short0200：新增2、丢1，净增1。三处成功变化贡献+1.619876791，其他27条件−.123835891，合计+1.496040900。short0200外部穿透未超门槛（.123560→.135819mm），本次丢Task；不是把所有失败归咎于穿透或loss。配对图和完整CSV/JSON保留全部30条件，已目视检查。

|方法|全30最大关节力矩Nm（32→41）|实际人体接触总秒数（32→41）|接触时长加权力矩合规比例（32→41）|
|---|---:|---:|---:|
|impedance|59.948186 → 58.545183|130.907800 → 131.601600|17.7727% → 15.5980%|
|admittance|51.681614 → 54.537169|73.975550 → 61.085000|70.4870% → 80.3453%|
|vmc|47.945283 → 47.982026|96.156400 → 96.231950|67.2804% → 68.4389%|

每方法每轮有8个实际人体接触回合；合规比例使用原经验阈值/原审计结果，以真实接触时长加权，无接触回合不进入分母，非所有回合比例简单平均。这不是人体舒适标定或安全认证，也不能用该比例覆盖Task/Strict失败。导纳该比例改善伴随峰值力矩增加，不能宣称全面占优。SPT共同参考和最终指定ESN公平比较仍待完整最终协议/矩阵，未在这个局部对照中冒充完成。

两轮是同一训练seed、一个外部动作seed、原训练条件上的描述性冻结比较。它显示导纳部分改善与持续失败，不证明训练收敛、独立训练seed稳健性、held-out泛化或学习的因果份额；没有挑换checkpoint/条件/seed，失败保留。

## 后续状态

Direct29 learner241542、参数48 I359275/A359279/V359281持续推进，actual startup已在前轮核验；当前进度见LIVE_STATUS。参数真实跨2m审计401313仍等≥2001000快照，尚未声称通过。49仅恢复401495、Direct30仅恢复464829和固定46–48/27–29 waiter1908379/336744继续，不能跳过完整窗口来称稳定。

冻结41释放的CPU52–54不触发重复派发。Direct29冻结prepare3802347仍等待准确完整29；当前29尚在训练，因此实际29恢复/冻结全30未启动。此前冻结29要求原41完成的依赖现已满足，其余准确29/预启动审查仍待。

本轮小证据 `docs/evidence/RL_FROZEN41_COMPLETE_20261027` 共142文件逐大小/hash与Python AST核验；原始99million子步/raw/checkpoint/runtime保留原共享SSD路径。HDD配额满只更新既有LATEST，非HDD或arm1全量备份。commit/push与本轮SSD小证据包收据另记。

冻结41原三evaluator/rootreview全部退出后，固定纯正式29/48 GPU窗口已完成：60样本/73.962015秒，GPU0–3均值[59.21666666666667, 70.7, 57.583333333333336, 57.583333333333336]%；每个样本GPU进程集合恰四正式PID且身份保持，保存均值独立复算通过。只代表该窗口均值，不保证每瞬时或覆盖早先过渡空档；原observer936980已结束，不重复采样。证据/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl29_parameter48_pure_gpu_20261027_v1/PROFILE.json。
