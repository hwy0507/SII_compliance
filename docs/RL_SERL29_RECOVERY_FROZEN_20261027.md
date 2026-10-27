# Direct29恢复感知冻结入口与真实27恢复验证（2026-10-27）

Goal active。上一轮完成参数46审查/正式47启动，属于实质进展。本轮在原四正式47/Direct28和冻结41持续运行期间，完成Direct29冻结评测入口、实际恢复验证和有界准备等待，没有重跑原冻结16或已完成训练。

共享SSD B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，源码B/repository/SII_compliance。开工实际查询/fetch/read远端main31765d168aab8ba078602798bbfb641350e18344、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d；沿用sii-research-sync，无子agent。原环境/物理/MJB/gate/filter/actuator/dt5e-5/canonical48、正式learner设置未变。

## 已固定的评测目标不变

上一轮在28运行、29未启动/完整29不存在时固定的PLAN仍原SHA `0bcdf58d087370c424801b7f1037131638ee20a56c1c0305f43101163397b7dd`。全30条件/顺序、同冻结16外部独立动作seed2026102626、最多41250动作/33000000子步、0优化与replay写入；两交错15条件分片，CPU52推理/GPU0、物理53/54。须先等原参数冻结41三evaluator和rootreview完成且通过。此次没有改变选择、条件、随机种子或预算。

## 新评测入口

新增 `evaluate_serl_recovery_frozen_20261027.py` 和 `review_serl29_recovery_frozen_matrix_20261027.py`。独立冻结runtime `B/runtime/serl_recovery_frozen_preparation_20261027_v1`，703个文件有完整hash清单，源自原实际28 runtime并增加新候选；原正式runtime不变。

- 使用原已验证恢复/接续validator逐层检查原26→27及后续连续完整周期，原partial25不改成完整25；验证历史2m/entry23、原恢复语义、网络/Adam/RNG/完整raw+derived replay/history。
- 读取hash绑定的原中断25快照，对比全部930 pending队列、相应raw字段和派生目标；要求endpoint仍−1且不在ready集合。保留原完整历史前缀和连续完整26..当前；恢复后和评测后完整状态摘要不变。
- 正式物理只接受准确完整29；27及以后可用于check-only恢复验证。原外部seeded-action函数和整个物理loop逐字节一致；原物理子步/filter/torque四helper与旧冻结入口逐字节一致，未重新仿真或改控制。
- 新root reviewer检查两分片相同learner/replay/history摘要、准确29/checkpoint/登记/源码、930隔离状态和完整26..29历史；沿用全部30原始子步、filter、torque审查。AST及CLI帮助入口检查通过。

错误周期守卫实际通过：请求27物理评测被拒绝，未创建输出目录。该预期非零退出有独立收据，0物理/优化；不把它当成正式评测失败后重试。

## 真实完整27恢复：已通过

`B/runs/serl_recovery_frozen_preparation_20261027_v1/restore27_v1`。原supervisor3577385/worker3577387已完成退出，600秒上限内实际291.2秒。只做完整恢复/外部动作RNG gate，0物理、0优化、0replay写入，无权重更新；不是新冻结27回合，也不是实际29恢复。

- checkpoint SHA `e85376716ba6bcd1b6b89e3b365c289d0e7261de726f4b5ec201e081a2adad1d`，size1121790/capacity2000000/历史entry23。
- learner digest `d99c61586e59abfc8bd1fc2540389c660b4deb066586d069a1dcd4aa33d6da86`。
- replay digest `6ad1e9ae2ed435a2158c14a6d84577886252040b97980386cd10ef49e9520d23`。
- history digest `b5809e74c68465f8cbb4078a556b2ae0a02aeb31cef7bca4b76ede7035ec022f`；完整恢复后历史为原前缀加26/27，没有完整25。
- 930原隔离队列及raw/derived精确一致，未成熟/未可采样；pending digest `5ac5de4e9b26722a728c7ee2e85970b8c99e5bb8bcbeb29e68f0b229e502ee0f`。
- 同外部key动作精确、不同seed动作变化、时间采样gate通过，全部learner状态不变。

独立SAVED_REVIEW将上述learner/replay/history/checkpoint摘要与原实际28恢复时的CHECK_ONLY_REVIEW交叉核对，全部一致；REFERENCE_BINDING_REVIEW又核对其原PRELAUNCH_REVIEW包含相同完整checks及hash。最初定位到空check_only.log与不存在的PRELAUNCH_SCIENTIFIC_REVIEW，随后按原启动脚本找到正确JSON收据；没有重跑恢复或伪造空日志内容。全部703冻结源hash复验保持。

## 实际29准备与尚未完成

`B/runs/serl_take29_frozen_full30_20261027_v1` 新增SOURCE_FREEZE、prepare.py、launch.py与PREPARATION_STATIC_REVIEW。源码冻结收据绑定原PLAN、上述真实27恢复/外部RNG与静态验证。原PLAN的“source未准备”描述是登记时状态，未覆盖原文件；新收据记录当前准备进展。

新**仅准备进程3802347**，最多等10800秒；准确完整29原review/health/FINISHED后，绑定实际29归档与登记，执行600秒check-only。无自动物理评测/训练/扩预算。手动launcher还要求PRELAUNCH_REVIEW、源码/全部输入hash一致和冻结41原进程/rootreview已结束且通过；新root review仍21600秒有界。

实际29完整父、恢复检查、PRELAUNCH及全30物理评测尚未执行。原29训练准备2044155与此3802347职责不同，勿重复派发。16→29包含容量变化、partial25曝光/中断恢复/隔离及take等价gather边界；未来结果仍是单训练seed、单动作seed、训练条件上的描述性冻结比较，不是held-out/多seed泛化、最终ESN/SPT或整体收敛证明。

## 当前任务与证据

原正式47 I3184892/A3184893/V3184894与Direct28 1978250持续增长；冻结41 316550/316551/316552继续。原48仅恢复3192792、Direct29训练恢复2044155、两固定窗口1908379/336744保持。开工四GPU瞬时65/79/81/81仅快照，不证明持续≥50%；本轮验证结束退出，无GPU假负载。当前PID/start_ticks/进度见LIVE_STATUS，行动前重验。

小证据 `docs/evidence/RL_SERL29_RECOVERY_FROZEN_20261027`，27文件逐大小/hash与AST核验。大型验证快照、正式checkpoint/raw/runtime仍共享SSD；HDD配额满只更新已有LATEST指针。本轮小包/提交/push收据另记，非HDD/arm1全备份。下一优先完整28→29与47→48接续、真实2m边界、冻结41最终90审查及已登记固定统计；Goal保持active。
