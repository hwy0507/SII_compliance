# 参数44恢复准备、43–45固定稳定窗口与Direct27审查入口

上一轮确实完成参数42完整审查、启动43、通过Direct读取等价gate并成功推送dc35b32，不是无进展或重启。当前Goal active。共享SSD B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；源码B/repository/SII_compliance，当前小证据docs/evidence/RL_PARAMETER44_STABILITY43_45_20261027。

## 当前原任务与新准备

Direct恢复26 learner645388、参数43 I1732692/A1732693/V1732694、冻结41 I316550/A316551/V316552均重新核验/proc身份、实际PROGRESS增长；没有重启。09:08 UTC快照D1065394steps；I/A/V1796480/1796737/1797902，仍各30sampler。Direct新27恢复准备1705859继续，未见FINISHED/FAILURE；只等待完整26后真实check-only，不自动训练。43原完整review1732698/归档1732697继续。

参数44新有界恢复准备2190593：B/runs/parameter44_preparation_20261027_v1。四入口在B/runtime/*parameter_capacity44*，继承原driver/helper，等待完整43review/health/learner退出后，只准备准确完整43→44三路全state/check-only，7200秒等待。每方法新阶段预算最多41250动作，原batch65536/UTD1/terminal128/target Imin+A-Vmean/actor min/LR/2m history entry23不变；没有44正式LAUNCH，更没有自动45。原43仍运行，不为GPU空档跳过审查。

## 43–45固定稳定性窗口

B/runs/parameter_capacity43_45_reward_stability_20261027_v1，新waiter2190600，登记时43三路均0完成、44/45未启动，保存当时真实progress和43三注册hash。固定43/44/45，bootstrap seed2026102745、5000次分类配对抽样，原相邻/首尾5%判据、nearzero1保持；43–45尚未完整，不能提前给出稳定结论。42已完成且单独报告，不将其事后纳入新的前瞻窗口；原39–41结果不改。

源继承39–41修正版的真实episode长度检查，保留abort失败及30条件分母。CPU54、7200秒等待、0物理/优化，无自动训练/停止。source diff核验统计公式不变，数字替换还使图像dpi140→144，该无关显示差异保留并显式记入SOURCE_REVIEW，不影响估计值。近零仍禁止百分比解释；bootstrap为条件组成敏感性，不是独立训练seed，不单独解锁最终测试/收敛。

## Direct27完整审查及启动入口准备

原B/runs/serl_recovery27_preparation_20261027_v1/prepare.py和原1705859保持，不重启、不更改运行中的26driver。新增templates目录：startup_review.py、review.py、diagnose.py、coordinator.py及audit_serl_recovery27_replay_20261027.py；5份AST、准确26→27/完整父/原pending守卫和source diff核验通过。

保留原reward重算、canonical48/critic49 clock、raw7/public7映射、30MJB/CPU affinity、完整历史raw/derived/ready和新32步目标审查。父是完整恢复26，原partial25仍不完整；930旧pending隔离保留，新流30–59在26完整flush后复用。完整27预计810终端（完整26为780，新27加30），不是旧协议把partial25当完成后的840。health仅从成熟集合采样，避免隔离pending endpoint=-1；保留有限诊断pair与off-policy局限。

新增手动launch.py已AST解析，只有原26真实完整review/health、27 check-only/PRELAUNCH及已绑定模板manifest通过才可调用。launcher保存准确pid/start_ticks并派发startup/archive/fullreview，无自动下一周期。当前这些是准备，不是实际27启动或实际27完整审查。待26完整先读实际产物，再科学审查27恢复和PRELAUNCH，不能仅依据模板静态通过派发。

## 41→42保存结果解释

B/runs/parameter41_42_saved_outcomes_20261027_v1，独立只读保存结果配对核验完成，30条件、各注册/模型、review均值与所有小输入hash前后一致，0新物理/优化，不重复旧诊断。

- 阻抗平均回报变化−1.789031759；short0600一例Strict真→假贡献−1.804008786，其他29例合计+0.014977027。该例Task保持真、完成时间保持12.800000001s；外部穿透峰0.192750266→0.222583631mm，越过原0.2mm门。原执行evaluator的physical_valid和Strict reducer、MJB hash核验，原阈值不改。峰motor torque48.037586→47.957941Nm；这是保存统计核对，不是重新计算物理子步或证明学习/随机性因果。
- 导纳平均+3.540855181；short0600 Strict假→真及short0300 Task/Strict假→真合计+3.463714512，其他28例+0.077140669。
- VMC无Task/Strict切换，平均+0.008430436。

当前回报变动可主要由少数原门槛状态切换解释，不能由局部loss较小推导健康收敛。保留原失败、门槛与学习设置，等待固定窗口和冻结评估。最终充分收敛/全范围比较/泛化/指定ESN仍未完成，不缩小Goal。

## 同步与接续

本轮开工真实查询/fetch main dc35b325982d12b5634501be534a5bd75876cc42、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，远端未新增时沿用已读最新日志。运行中的冻结源未修改。小证据30文件约145KB，全部source path/size/hash与10原live身份保存，日志/大checkpoint不进Git。GPU0最近已完成稳定窗口42.7333%仍不足50，未再重复采样，也不制造假负载；等真实27部署后再评估读取优化的端到端效果。

接手优先：查原43完整review及44准备、原Direct26完整review和27准备；核验实际完整父/check-only，完成各PRELAUNCH后启动对应单有限后继，随后查实际startup。43–45审计等待原进程，不重复启动；45仍需另登记。冻结41原全90尚未完成。新小归档与Git提交收据另附；大数据保留共享SSD、HDD配额满，不声称arm1或HDD全备份。无子agent。

本轮科学提交0d70aa6，SSD准备补充包/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER44_PREPARATION_20261027_091248/PREPARATION_SUPPLEMENT.tar.gz，35成员/559987字节，SHA256 509d0d1adfee7e92e15e226b57f83e1a126bf90e33b2bcdd0c9208eb77450d7e，全部成员大小/hash核验。新交接与完整收据仅SSD，既有HDD LATEST已更新回读；依赖前轮重启完整小包，大checkpoint/runtime仍SSD，非HDD/arm1全备份。Goal active。
