# 参数41全30冻结验证预登记

2026-10-27 UTC。Goal active，无子agent。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。

## 科学目的与前瞻选择

参数39–41稳定性窗口已在39阶段登记。现在正式40仍在运行、41尚未启动且完整41检查点不存在，固定窗口终点41用于下一次冻结验证。复用已完成冻结32的全部30条件及同一个外部动作seed2026102638，比较经过后续训练后的冻结策略，而不是依在线回报择优挑检查点、条件或随机种子。

冻结32原90回合已经完整完成，不重跑。其结果作为固定比较输入，SHA绑定在新PLAN。原39–41统计定义、5%门槛和已知36–38结论均不改变；冻结41即使在线结果没有改善也不另选更好检查点。单训练seed、单外部动作seed、原训练条件，不能当成held-out泛化、多独立训练seed、最终指定ESN/SPT或单独证明收敛。

## 固定预算与实际状态

新run B/runs/parameter41_frozen_full30_20261027_v1；runtime B/runtime/parameter41_frozen_full30_20261027_v1。三方法阻抗/导纳/VMC，各30条件、每回合最多55秒，合计90回合/最多123750动作和99000000物理子步；原安全早停继续生效，所有条件及失败保留。外部动作seed2026102638与冻结32完全相同，物理/MJB/原gate/filter/执行器/dt5e−5/canonical48/reward保持。

原准备PID1833369实际存活，等待7200秒，只在完整41的FINISHED/REVIEW通过后生成准确父hash登记并执行三check-only。不会自动执行90回合；随后读取实际恢复和科学结果再决定调用已准备的有限评估launcher。根评估审查最多等待21600秒，无自动延期/种子追加。

当前没有41冻结评估进程、实际父恢复或物理回合，不能把静态通过当作实际部署。prepare/launch两个新入口及evaluate/review两个新脚本已保存。PLAN SHA `a541276ae23af43ac253d0bc0d6a3736fd5a601d8ba6d00307f727e3379df83a`；准确41父protocol/checkpoint SHA要等真实完整父出现后才绑定，不虚构未来hash。

## 保持的恢复与审计约束

新evaluate/review由原冻结32入口作限定的32→41阶段替换，seed、物理预算和helper没有改。AST、CLI --help、准确parent41/cycle41、原30条件、历史capacity入口23、预算守卫通过。全部旧helper字节保持；另与正式40 runtime中20个共同模块逐一比较hash一致，证据CURRENT40_HELPER_REVIEW。没有重复前轮辅助更新/物理验证。

实际恢复必须使用2m capacity replay与pair learner，完整learner/optimizer/replay/RNG digest相等；外部RNG与原生随机动作gate通过后才允许评估。每回合按原物理/filter/torque与native动作重放审查，评估前后完整state不变，0优化/正式回放写入。CPU52/53/54、GPU1/2/3映射沿用原冻结32。原先CPU0–51正式训练保持。

## 与正式训练的衔接

正式Direct24原3403962与参数40 I691539/A691540/V691541继续，原25恢复3448092/调度3448355、41恢复715346/调度715347、两固定窗口1470790/3482651已核验live。完整24/40、下一阶段实际恢复与科学审查仍按原流程。

新进程1739008仅观察原四learner退出区间与未来25/41实际spawn时间，CPU54、每2秒、最多1800秒；不启动训练、不生成GPU负载，超时仅记收据不自动重试。它记录进程衔接间隔，不冒充全GPU空闲时长。原已完成百万容量边界、40startup、冻结32、VMC固定1164和旧GPU窗口不重跑。

开工远端main7d69ac57974888d32f98d208f0097e7ec8f64426、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d实际重新fetch/read未变。远端非RL97/108不是本机RL或最终指定ESN完成。HDD配额满，新产物SSD，已有LATEST入口后续指向核验过的SSD交接。整体目标仍未完成。
