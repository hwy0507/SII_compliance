# 重启接续补充：完整参数42、正式43与Direct读取优化准备

本报告接续 [重启恢复总交接](RL_REBOOT_RESUME_20261027.md)，当前Goal active，用户已明确恢复。B为共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。代码B/repository/SII_compliance；本轮小证据docs/evidence/RL_REBOOT_RESUME_20261027。无子agent，不是收敛完成。

## 参数42完整审查与43

原参数42三learner351462/351463/351465均自然退出。完整归档B/runs/parameter_capacity_pool30_cycle42_archive_20261026_v1，审查B/runs/parameter_capacity_pool30_cycle42_review_20261026_v1。三路全30×55秒，无abort，每方法41250新动作；完整旧replay字段/history/2m历史entry23保留，逐新reward重建误差0，network/optimizer有限。health/FINISHED、保存结果独立算术及诊断图已核验。

| 方法 | 完整steps | Task/Strict | 平均reward | 最后q_loss |
|---|---:|---:|---:|---:|
| Impedance | 1769930 | 18/17 | −2.3742534465 | 3.0750946999 |
| Admittance | 1769750 | 13/13 | −10.2275149728 | 2.0129837990 |
| VMC | 1770750 | 17/16 | −4.6020948150 | 0.7419819236 |

原39–41窗口不通过，本42仍有回报/成败变化及终端残差。有限性与恢复完整允许一轮不改设置续训，不等于loss健康稳定或收敛。I42较41失去一个Strict，A改善一个Task和两个Strict，V成功数相同；这些为计数比较，不能直接归因学习或随机性。

正式43：B/runs/parameter_capacity_pool30_cycle43_20261026_v1，I/A/V1732692/1732693/1732694；2026-10-27 08:46:59 UTC启动，GPU1/2/3、CPU13–51、每路30sampler共享12物理核。原42完整checkpoint各自准确父，三check-only完整learner/replay/next65536均精确，PRELAUNCH_SCIENTIFIC_REVIEW绑定实际42review/health/hash。单有限周期，每路最多41250动作，不改变batch65536、UTD1、terminal128、Imin/A-Vmean、actor min、原LR、2m容量或原物理协议。archive1732697、完整review1732698；实际startup1732696已通过：I/A/V新增1000/1000/2000，旧全replay/history、optimizer设置、30MJB/sampler/clock/action核验、新reward重算误差0。43首次PROGRESS已新增并有30实际sampler，后续无自动44。

42退出至43启动间存在归档、全reward/health审查和真实恢复检查空档；没有连续GPU50%保证。不能用随后的高利用率覆盖这段事实。

## Direct候选等价读取gate通过

B/runs/serl_take_gather_gate_20261027_v1原有限gate已经完成，REVIEW和SAVED_REVIEW都通过。真实首1000新步快照SHA `be68774288b3322c6a036100090284e105bd6eaad5884e1852827ea514f139a4`，三批65536完整字段/RNG相同、完整replay序列化恢复相同、batch pytree相同；两臂各1outer更新，共16critic+2actor，完整更新后network/Adam/RNG/metrics digest相同。两项负守卫通过、930旧pending保留。0物理、不保存或导入辅助权重，不是正式部署。

候选`serl_replay_take_gather_20261027.py` SHA `4d58e85460d197132322822174bbbe5b49b73c2173530487b4adbb2d16206312`。先验证成熟索引和endpoint有效，再np.take，随机draw及字段顺序保持。此前20对CPU读取中位0.191931→0.091872秒，仅为共享CPU上的局部计时；不是端到端2倍加速证明。正式Direct恢复26原645388继续原实现，未热修改或重启。

GPU两个已完成窗口GPU0分别42.5%和42.7333%，未达50%；其他三卡稳定窗口约64.55/68.75/68.4%，含冻结41推理。真实py-spy含保存checkpoint窗口：检查点调用栈约35.53%、数组读取叶帧约19.92%，不能当全程GPU因果份额。不重复采样或创建假负载。

## Direct27独立恢复入口准备

新源码`code/mujoco_6d_vmc_benchmark/tools/resume_serl_recovery26_take27_20261027.py`只接受准确完整恢复26→27。协议保留原interrupted_stream_recovery及完整历史链，新增recovery_continuation_stage，绑定实际26review/health与已通过gather gate；完整25仍不存在。旧0–29共930pending原样隔离，完整26新stream30–59必须全部flush后才复用，新27额外最多41250动作/33000000子步；不改变算法、不丢旧状态。

静态AST、原native trainer patched hash、五项错误边界fixture拒绝通过；与26物理sampler主函数差异仅checkpoint/resume元数据，gather实现另由已完成等价gate验证。静态fixture不是实际26checkpoint恢复。B/runs/serl_recovery27_preparation_20261027_v1/prepare.py等待原26完整review，原进程1705859；7200秒等待上限+900秒一次check-only，完成也不自动训练。若原父/证据失败，保留FAILURE，不回退或重新运行完成实验。未来实际run名称serl_recovery26_take27_20261027_v1，当前尚未创建或启动；后续须先读实际产物。原旧serl_capacity_batch65536_cycle26入口仍禁止使用。

原Direct26、参数43、冻结41三路继续。冻结41原316550/316551/316552、review316553，全90尚未完成；不重跑已完成冻结32/Direct16。最新步骤和/proc身份见小证据LIVE_STATUS.json。后续先查43startup、完整26及27恢复结果，完成冻结41；完整27科学审查/启动、未来稳定性窗口、最终公平比较/泛化/指定ESN仍未完成。不得以当前低Direct loss或平台回报宣告总体收敛。

## 保存与同步

原关机快照、恢复26/参数42全部大checkpoint、轨迹保留在共享SSD；HDD配额满，不声称HDD或arm1全备份。最终小证据MANIFEST覆盖本轮全目录，忽略的.log明确标记，仅本地档案保留，不声称已提交Git。Git提交/push与验证过的SSD归档收据另附。Goal保持active。

收尾真实查询/fetch/read main更新到4c75aa52570930e5bfd7f8fe688c6ea7ec8b8d0d，baseline仍f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。新增是另一主机非RL经典补测12/72与归档服务，不改变当前RL协议或运行源；合并保留双方日志。

本轮科学提交563d974，安全合并远端非RL更新ef2fd49；正常push已成功（4c75aa5→ef2fd49），包括此前重启恢复与gather科学提交。双方UPDATE_LOG逐行顺序保留已核验。无需再索要GitHub凭据。
