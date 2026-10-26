# 参数17与Direct batch65536第13周期交接（2026-10-26）

原Goal active，继续Direct SERL与在线参数RL直到健康收敛。当前未收敛；用户要求不要让GPU长时间空闲。无子agent。本文件覆盖上一份参数16/Direct12运行中快照。

实际计算/大产物根目录 **B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl**。
仓库为B/repository/SII_compliance，用户原HDD路径为链接。大型权重/回放/物理原件仅SSD，未核验arm1副本。HDD配额仍满，仅小交接/收据可写。

## 已完成正式周期与判断

参数16完整审查、健康诊断及图检查已完成。三路各新增41250transition，30完整55秒、无abort；新奖励重建0误差，全旧replay/history/配置/三个marker/MJB保留。末1000条优化日志的均值另有独立来源hash：

| 方法 | steps / updates | Task / Strict（各30） | 平均reward | 末1000 critic loss | terminal MAE | sampled Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| Impedance16 | 698250 / 693251 | 18 / 18 | −0.533626 | 1.869291 | 1.062527 | −8.377526 |
| Admittance16 | 697250 / 692251 | 11 / 9 | −17.182676 | 6.084509 | 0.744909 | +13.612809 |
| VMC16 | 698250 / 693251 | 17 / 17 | −2.825392 | 1.976498 | 0.828596 | +26.576229 |
| Direct12 | 524532 / 4156264 critic | 0 / 0 | −31.019692 | 0.020545 | 0.093513 | −20.592020 |

参数末loss下降不能抵消导纳任务退步与价值移动。CHEQ的mask0行对对应critic刻意留出，不能把全部terminal误差当作拟合发散；例如I in-bag MAE0.260945、out-of-bag4.425543，整体最大104.473。A/V最大分别53.203/55.253。

Direct12也新增41250、30完整55秒、无abort；所有新单步奖励和32步派生目标精确，旧483282行raw/derived/ready顺序/history保留，pending0。390历史terminal×10critic最大误差2.961039、p95 .202016，32步TD MAE .079125。全network/optimizer/RNG在诊断后不变；任务0/30、全部approach，低loss不是任务收敛。

完整审查位置：B/runs/parameter_batch65536_cycle16_review_20261026_v1与serl_multistep_transfer_cycle12_review_20261026_v1。原16三learner4072251/4072252/4072255、Direct12 learner4121413及对应归档/审查已退出，勿重启。

## 当前正式训练：保留原句柄，勿重复派发

参数17 run：B/runs/parameter_batch65536_cycle17_20261026_v1/{impedance,admittance,vmc}/train。

- I1280294、A1280295、V1280296，GPU1/2/3，CPU13–25/26–38/39–51，各12sampler。
- 精确完整16全state接续一个17；batch65536、UTD1、terminal128、target上界projection、I target minimum/A-V target mean、actor minimum、actor LR I/V3e-4/A3e-5均不变。
- 新通用续训driver核验连续父登记链直至原batch13、所有hash与准确当前父review/health；不是无界循环。
- 三check-only完整state/重复恢复/负守卫通过，0更新。实际三路各1000新增，旧prefix/history/markers/MJB/动作/clock/奖励0误差审查通过。
- 归档1328339到parameter_batch65536_cycle17_archive_20261026_v1；完整审查1328342在parameter_batch65536_cycle17_review_20261026_v1。无自动18。

Direct13 run：B/runs/serl_multistep_batch65536_cycle13_20261026_v1/direct。

- learner1280297，GPU0/learnerCPU0，30sampler共享CPU1–12，精确完整12全state接续一个13。
- 唯一学习工作量变更为batch32768→65536，官方8critic:1actor不变（8×8192 critic chunks，actor65536）；10critic/random2 target/no entropy backup/32步/gamma.9995/actor48/零示范纠正/无nominal mixing保持，已有gather和单次batch传输保持。
- 依据：上一纯正式GPU0仅48.43%；原正式11两臂有限probe已完整审查，65536误差接近但更新约2.67倍成本。该历史probe父是11，新正式父是12，登记分别绑定，未导入任何辅助权重。
- check-only全state/replay/下批65536采样/RNG/两种batch构造相等与负守卫通过，0更新。实际1000新增/8000critic审查通过，旧524532全raw/derived前缀保留，145mature+855pending派生精确。
- 归档1328360到serl_multistep_batch65536_cycle13_archive_20261026_v1；完整审查1328362在serl_multistep_batch65536_cycle13_review_20261026_v1，覆盖420历史terminal。无自动14。

恢复必须保留完整权重、优化器/counter、replay/RNG/history。参数使用pair_class保留三marker；Direct使用SerlMultistepLearner/replay_class与优化wrapper保留clock/multistep marker、成熟顺序与pending。旧loader不可替代。bootstrap存储为gamma^(k−1)×terminal_mask，learner再乘一次gamma得到gamma^k，不要误改。

准确父文件：

| 方法 | B/runs下相对路径 | SHA256 |
|---|---|---|
| I16 | parameter_batch65536_cycle16_archive_20261026_v1/impedance/cycle_00016.pt | c7db56e9a144489f9480f37b53c7e7a3761f4399815be49e9edfbc17a44b1a36 |
| A16 | parameter_batch65536_cycle16_archive_20261026_v1/admittance/cycle_00016.pt | de642b75d7f5320d6b6ba2a58a55df35ab1e845152fbc3abd917e50c5c49a994 |
| V16 | parameter_batch65536_cycle16_archive_20261026_v1/vmc/cycle_00016.pt | 0ee63071402a99f815dc43ea6433bc3927c66c8e7410df9c29906a90d9f172c0 |
| D12 | serl_multistep_transfer_cycle12_archive_20261026_v1/direct/cycle_00012.pt | f9169a23466a8d9d6146182144def813dbe046447005235efa763f6f4052bba5 |

## 固定纯正式GPU测量已完成

B/runs/batch13_parameter17_gpu_profile_20261026_v1/PROFILE.json，预登记180样本、193.548779秒；等待所有冻结15评估退出，且新四正式各>1000transition后开始。四原learner全窗口存活，测量期间无辅助GPU任务。原测量1364508已结束，不重采挑好窗口。

| GPU / 方法 | 平均利用率 | transition/s | critic update/s |
|---|---:|---:|---:|
| 0 Direct13 | 58.45% | 10.627812 | 85.022495 |
| 1 Impedance17 | 75.7111% | 24.779283 | 24.779283 |
| 2 Admittance17 | 74.8889% | 25.347615 | 25.347615 |
| 3 VMC17 | 74.2667% | 25.213282 | 25.213282 |

该固定窗口四卡均值均≥50%，不是每个瞬时样本或未来持续保证。Direct相比前窗口23.416steps/s降低约54.6%，较大batch以吞吐代价提高利用率，不能宣称在线提速或学习改善。后续冻结推理与正式混合占用另计。

## 冻结参数15：九条已全部审查

B/runs/parameter_pair15_fixed_20261026_v1/{method}/REVIEW.json与FINISHED.json均完成。原协调354445/354448/354759与evaluator354447/354805/544452均退出，勿重跑。每路3×55秒/4125actions/330万子步、0优化；全参数动作重放误差0、clock/MJB/物理/filter/torque与全learner state不变通过。

| 方法 | Task / Strict（各3） | 被动结果 | 主动短期完成(s) | 主动长期完成(s) | 长期人接触(s) | 长期接触合规率 |
|---|---:|---|---:|---:|---:|---:|
| I15 | 2 / 2 | carry失败 | 12.84 | 53.08 | 7.76725 | 14.957% |
| A15 | 2 / 2 | carry失败 | 46.04 | 38.08 | 5.14780 | 100% |
| V15 | 2 / 2 | carry失败 | 27.16 | 31.48 | 6.67145 | 100% |

九条都完整55秒、无abort/机器安全违规。被动/短期无人接触，合规率为NA不能填100%。上述为原预选三个训练代表的冻结诊断，不是全30最终排名，也不据此计算最终Tref/SPT。

## 行为配对与新Direct冻结随机诊断

B/runs/cycle16_parameter_and_direct12_behavior_audit_20261026_v1/REVIEW.json已完成，原1462229退出，0物理/优化。参数15→16：

- I新增active_long_train_0000成功，无丢失；V Task/Strict条件集合不变。
- A丢失Strict的条件为active_short_train_0100、0000、0900与active_long_train_0400；无新增Strict。0100/0900/长期0400从成功变为carry失败；短期0000仍Task成功但physical_valid=false。新Task成功短期0600也physical_valid=false。因此Task13→11、Strict13→9。
- 三参数被动均0/10。主动期间平均authority变化与结果仅描述相关，不是控制变量因果证明。
- Direct11→12全30均approach；前160动作公共channel0均值.451791→.357072，残差饱和9.4306%→5.1076%。公共channel0=0为nominal、越大越减慢WBC。配对时长不等于同状态/同动作RNG。

新B/runs/serl_cycle12_stochastic_representatives_20261026_v1，协调1521445、实际evaluator1535401。等待上述纯正式profile完成后才启动；GPU0低优先级，CPU52，精确正式12冻结权重，原三个代表最多3×55秒/330万子步，0优化。

动作独立外部seed2026102612，每case由SHA256取前4字节little-endian；每动作split独立JAX key，官方sample_actions和原公共映射不变，不改变训练action_rng。实际EXTERNAL_ACTION_RNG_GATE已通过：同seed精确、不同seed有差异、完整state不变。评估与独立最终审查已全部完成；原协调1521445/evaluator1535401及review2105519已退出，勿重跑。

独立review已逐动作重放4125actions（误差0）、重建SPT reward与gamma.9995折扣实际回报，比较实际访问状态/动作的10critic预测；330万子步物理/filter/torque/MJB与完整state不变全部通过。FINAL_SCIENTIFIC_REVIEW和FINISHED齐全，value_vs_realized_return.png已目视检查。三条各完整55秒，Task/Strict0/3，均approach，无abort/机器安全违规，无人接触（合规率NA）。

| 代表 | 初始10critic均值 | 初始实际折扣回报 | 全轨迹均值Q与实际回报MAE | 未折扣reward |
|---|---:|---:|---:|---:|
| 被动 | −17.051441 | −16.983772 | .079748 | −30.973016 |
| 主动短期 | −17.078608 | −16.991653 | .071932 | −30.986507 |
| 主动长期 | −17.050270 | −16.976093 | .089618 | −30.963434 |

这些访问轨迹上的预测接近实际失败回报，未见足以解释任务失败的大幅价值高估。证据提示下一步需关注策略如何探索到成功行为及动作改进信号；不能仅继续降低已很小的TD loss并称任务收敛。每条件仅一条随机轨迹，相关状态不是独立样本；不可当期望回报置信区间或完整校准证明。保留原句柄，不按等待时长重启。

## 发布、证据与接续

开工与恢复上下文后均使用禁交互凭据提示fetch/read真实main与baseline：main dbb1d76ed79177067c48ed49ff9f67f023c704aa，baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。此前本地573d0469/ac6a028未推送，GitHub编辑器认证等待恢复，已问用户勿反复索要；训练不依赖发布。

本轮源码三文件AST与对应恢复/启动/随机入口检查通过。小证据在docs/evidence/rl_parameter17_batch13_20261026，SOURCES.json逐文件hash记录来源；LIVE_STATUS为带时间快照，实时状态以原run为准。末1000loss与冻结15汇总仅重用已完成证据。收尾提交/无提示push结果与SSD包/HDD收据见UPDATE_LOG及最新备份入口。

后续先核对原17/13进程与自动完整审查；新随机评估已完成勿重跑。若某路完成，在完整review/health核验后从其**最新正式全state**衔接下一有限周期，避免空闲；不得跳过未完成审查、回退到16/12、重置学习或导入辅助权重。不改冻结物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT。原Goal保持active，健康收敛/最终全矩阵/指定ESN与最终SPT仍未完成。

收尾科学提交746ad79bbd3d83a27bf56ed577ec67625c1e28b4仅本地；本轮211成员小证据包位于B/repository/RL_PARAMETER17_BATCH13_20261026_155831/FULL_SMALL_EVIDENCE.tar.gz，SHA a2cb7761fd72915391bb307e4e770251f1d9fa900d8da695e12134fc821e6dcf，逐项hash验证通过。HDD最新小交接入口已更新，配额限制下未复制完整包或大产物。
