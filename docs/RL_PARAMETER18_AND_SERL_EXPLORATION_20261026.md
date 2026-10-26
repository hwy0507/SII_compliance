# 参数18接续、Direct探索诊断与调度准备（2026-10-26）

原Goal active，未健康收敛。上轮为实质进展：完成参数16/Direct12审查、正式17/13接续、固定纯正式GPU测量和冻结Direct12随机策略回报验证。本轮继续最新正式state，无子agent，不改冻结物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward。

实际运行与大产物根目录B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库B/repository/SII_compliance由用户HDD原路径链接。大产物仅SSD，无新核验arm1副本；HDD配额仍满。

## 参数17已完整审查，第18周期已启动

三路各新增41250transition，30完整55秒、无abort；所有新奖励重建误差0、旧replay全字段前缀/history/配置/三个marker/MJB与有限网络/优化器检查通过。健康诊断完整，图已目视核验。

| 方法 | steps / updates | Task / Strict（各30） | 平均reward | 末1000 critic loss | terminal MAE | sampled Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| Impedance17 | 739500 / 734501 | 18 / 18 | −0.612733 | 1.452751 | 1.017201 | −6.154024 |
| Admittance17 | 738500 / 733501 | 12 / 12 | −12.190258 | 1.628737 | .624910 | +14.556150 |
| VMC17 | 739500 / 734501 | 17 / 17 | −2.836349 | 1.231426 | .642652 | +26.587584 |

导纳较16的11/9和reward−17.182676恢复，但15→16→17仍为13→9→12个Strict，不能称稳定。I/V任务较16不变；I值仍移动。CHEQ terminal诊断包含刻意留出的out-of-bag行，整体最大误差I56.716/A51.913/V54.486不全是拟合误差，不把低loss或某单项误差作为任务收敛判据。

证据B/runs/parameter_batch65536_cycle17_review_20261026_v1/REVIEW.json、health/DIAGNOSIS.json和FINISHED.json。末1000loss独立来源hash在parameter_cycle17_loss_summary_20261026_v1。旧learner1280294/1280295/1280296、归档1328339/审查1328342均结束，勿重启。

精确父文件均在B/runs/parameter_batch65536_cycle17_archive_20261026_v1/{method}/cycle_00017.pt：

| 方法 | SHA256 |
|---|---|
| impedance | de722c971f0b6a1ec3929f68c11a104a1fa03438614135d33cd73d46dec1572f |
| admittance | cb4dfc9a3f2c48de3cfa5d0a13b4f8d3829eb0280ff7aac1b0ac00befbca1704 |
| vmc | a5cb3decbec21ee003c8c5c584a7e6db5fcdde688bcc806e632d5bb5c986c4fe |

当前正式18 run为B/runs/parameter_batch65536_cycle18_20261026_v1/{method}/train：I2652800/A2652802/V2652804，GPU1/2/3、CPU13–25/26–38/39–51，各12sampler。完整17全state续一个18，batch65536/UTD1/terminal128/上界projection/I target minimum+A-V target mean/actor minimum/原actorLR保持。三check-only完整恢复/重复恢复/负守卫通过；真实各1000新增全旧prefix/history/优化器配置/MJB/动作/clock/reward0误差通过。须pair_class恢复，不丢任何marker或学习状态。

监视器：startup2652910已完成；归档2652915到parameter_batch65536_cycle18_archive_20261026_v1，完整审查2652985在parameter_batch65536_cycle18_review_20261026_v1。无自动19。运行时只能读，不修改冻结源码、不重置或回退权重。

## Direct13仍运行，审查超时兜底已登记

原Direct learner1280297仍运行B/runs/serl_multistep_batch65536_cycle13_20261026_v1/direct，GPU0/CPU0、30sampler共享CPU1–12。batch65536、官方8critic:1actor/10critic/随机2target/noentropy backup/actor48/32步目标/gamma.9995/零示范与纠正/无nominal混合保持。当前完整父仍是正式12；不要把未完整的13当下一父。归档1328360，原完整审查1328362，原只读子进程1328394。

上一固定窗口10.63transition/s意味着本周期约65分钟，超过原只读审查的60分钟等待上限。新增B/runs/serl_multistep_batch65536_cycle13_review_deadline_guard_20261026_v1，PID2542683，保留原训练/归档/审查原句柄，不改运行源码。

兜底只在原审查进程身份已消失、日志明确为原checkpoint等待超时、训练无FAILURE且准确完整13 checkpoint已归档后，运行完全相同的只读review/coordinator/diagnose到serl_multistep_batch65536_cycle13_review_20261026_v2。若原审查成功则不重复；其他失败直接报告，不重启训练。兜底自身观察期限7200秒不构成额外训练预算。后续先查看该guard的FINISHED/REPLACEMENT_LAUNCH，确定最终审查实际位于v1还是v2；不能仅凭一次观察超时宣称训练结束。

## 冻结探索诊断：整回合固定基础噪声

去重实际路径后的正式SERL0–12共390条episode，Task成功0。上轮冻结正式12、每步独立噪声的三个代表也全部approach失败，critic对这些失败轨迹的实际折扣回报预测接近；仅继续压低TD loss不能证明学会任务。

本轮B/runs/serl_cycle12_constant_noise_representatives_20261026_v1：协调2427730、evaluator2427731，精确正式12 checkpoint SHA f9169a23466a8d9d6146182144def813dbe046447005235efa763f6f4052bba5，原三个代表、原外部seed2026102612、CPU52/nice19/GPU0推理，最多3×55秒/330万子步，0优化/不写回放/不保存推广权重、不部署训练。

新评估器选项noise_schedule=episode_constant，每回合重复使用同一个JAX sample key，策略仍每步依当前canonical48输出动作；保持的是基础高斯样本，**不是固定公共动作**。首步observation/action与已完成独立噪声对照精确匹配；后续访问状态可以不同。未添加名义动作、示范或人工纠正，不改变公共映射（public0=0为nominal，越大越减慢WBC）。原独立噪声评估的冻结runtime保持不变。

实际入口gate通过：同seed精确、不同seed有差异、同一固定state下跨步动作相同、完整网络/优化器/RNG不变。最终独立审查已完成：三完整55秒、4125actions/330万子步，所有动作重放误差0、首步observation/action与原独立噪声对照精确相同，物理/filter/torque/MJB/完整state不变通过，图已目视检查。FINAL_SCIENTIFIC_REVIEW与FINISHED齐全，原2427730/2427731及只读review均结束勿重跑。三条Task/Strict仍0/3，均approach，无abort/机器违规/人接触（合规NA）。

| 代表 | 独立噪声reward | 固定噪声reward | 独立噪声峰矩(Nm) | 固定噪声峰矩(Nm) |
|---|---:|---:|---:|---:|
| 被动 | −30.973016 | −30.937580 | 56.4681 | 40.2308 |
| 主动短期 | −30.986507 | −30.992191 | 59.6400 | 69.8504 |
| 主动长期 | −30.963434 | −30.917285 | 54.7156 | 54.9506 |

固定噪声在这三个预选代表没有带来任务成功，短期峰矩反而增加；本轮不将它部署到正式13或据此认定探索问题已解决。

固定噪声改变行为策略的时间相关性，因此原critic预测与这条实际回报之差**不再是原策略校准误差**。每条件一条轨迹也不能证明成功率改善，不因单次结果选seed重跑或自动部署。

## 参数30路共享CPU候选：已通过有限准备检查，未部署

原12sampler运行30条件，尾部只能剩6个物理worker；本轮17尾部确实出现低于50%的瞬时GPU利用率，不能拿前一高利用率窗口掩盖。优先检查保持学习设置的调度改进。

新增parameter_shared_sampler_pool_20261026.py，仅变更冻结trainer的worker数量守卫和taskset CPU字符串两处；30条件共享各方法原12个物理CPU，learner仍独占原CPU，不跨方法借核，不改更新比例、动作/奖励/物理或网络。保持全30条件顺序，不选择容易条件。

B/runs/parameter_pool30_preparation_20261026_v1/REVIEW.json已通过，原检查2872195结束：准确正式17三父各两次全state恢复，每次65交错动作，合计390；验证30个独立mixing对象/各流clock与context隔离、raw action×context映射、重复恢复动作与全state相等、恢复后原state精确，以及每方法9个错误worker/CPU/slot负守卫。0optimizer/0physics、无权重保存；仅CPU推理与状态恢复，非在线性能或reward等价证明。

该候选**未部署到18**，也没有完成新pool的正式续训driver/登记/实际启动审查。若采用，必须先完成18或更晚正式周期的review/health，用最新父全state登记后续有限周期；不能回退到本次准备所用17父。原runtime与在线18未修改。

## GPU测量与交付

上轮纯正式180样本四卡均值58.45/75.71/74.89/74.27%属实；参数17尾部和完整周期交接期间会下降，不宣称所有瞬时均达标。三18正式已及时接续，最新进度见带时间LIVE_STATUS，原Direct13不间断。

新固定180样本观察B/runs/batch13_parameter18_gpu_profile_20261026_v1，PID2680231，等待18各>1000新transition且固定噪声评估/审查完整结束、相关GPU进程退出后开始；逐样本核验GPU PID只属于四正式。原测量现已完成，2680231结束，未重采。180样本/206.622929秒，GPU0–3均值54.9444/70.5722/69.7444/68.5833%，D/I/A/V吞吐10.0473/23.1533/23.5550/23.5550transition/s，Direct80.3783critic updates/s。四原learner全样本live，每个样本GPU PID集合恰为这四个正式PID，无辅助推理。该固定窗口四卡均值≥50%，仍非所有瞬时或未来保证。

开工fetch/read真实main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，本地起点307a37a。GitHub HTTPS认证请求此前已问用户，未恢复前勿宣称push，不反复索要密码/token；训练不因此停下。

本轮小证据来源/hash、最后进度、发布/备份结果见docs/evidence/rl_parameter18_exploration_20261026与UPDATE_LOG。Goal仍active：Direct成功行为与健康收敛、参数稳定性、最终冻结全矩阵/指定ESN/SPT尚未完成。继续核对原句柄，完成审查后衔接最新完整正式state，避免重复作业和长时间空闲。
