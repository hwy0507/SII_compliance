# 参数33接续、第32轮全30冻结验证与固定终端跟踪

## Direct20完整审查通过，21已接续

此条覆盖下文Direct20运行快照。完整20为854532步/6796264 critic更新，30完整无abort，Task/Strict0/30、reward−30.912666（19为−31.581990）；保留813282旧raw/derived/history、新41250reward和32步目标精确、pending0。末1000 critic loss .0130094，整轮均值.0133141、最大.0259253；630终端×10critic MAE.0448714，32步TD MAE.0393848，Qmean−20.501648，alpha.000503776。完整REVIEW/DIAGNOSIS/FINISHED、网络/优化器/RNG不变及图通过；低loss不替代任务表现，原17–19描述稳定结论保留，不新增Task门槛。
准确完整20父SHA c16481af41006b8bea48f734f1b3387bcf1a462c099719b74a4167bf926e099c。21check-only通过，PRELAUNCH科学审查后正式learner **2826774**，startup **2826820**、archive **2826823**、review **2826824**。原配置/全state接续一个有限周期，实际新增启动审查另见原startup/REVIEW，禁止把check-only当实际通过。
22准备等待 **2851849**、原21审查CPU调度 **2851880**，7200秒，只完整21后check-only，不自动训练。限定同时替换/AST/准确父21与目标22/预期690终端守卫通过，实际恢复尚待。原20 learner46632/归档46745/review46750与21准备87882/调度87883均已完成，勿重启。正式21路径B/runs/serl_multistep_batch65536_cycle21_20261026_v1，22准备B/runs/serl22_preparation_registration_20261027_v1。

2026-10-27 UTC，服务器 rltest-1025--a6ed2ff39b3c-2d5lfqki2m。Goal active；无子agent。当前结果尚不支持reward平稳且loss无异常的整体收敛结论。

## 完整32结果与30–32窗口

完整32三方法均30×55秒，无abort；全部旧replay字段精确保留，每方法新增41250条reward重建误差0，网络/优化器数值有限。2m append-without-overwrite容量、历史入口23和所有正式设置保持。完整REVIEW/health/FINISHED及健康图已核对。

|方法|steps / updates|Task / Strict|平均reward|末1000 q_loss|terminal MAE / in-bag MAE|
|---|---|---|---|---|---|
|阻抗|1358250 / 1353251|18 / 17|−2.415532|1.757422|.920626 / .355329|
|导纳|1357250 / 1352251|13 / 13|−10.231849|1.450707|.699927 / .299422|
|VMC|1358250 / 1353251|17 / 17|−2.869316|.659962|.584216 / .240568|

A/V必要soft-Q上界超出比例仍为.0006347656/.0017089844，不能将finite等同健康。完整30–32预登记审计已结束，原2830862勿重启。I/A/V相邻reward相对变化为76.90%/41.78%、15.69%/13.64%、.869%/37.69%，三者原5%描述检查均不通过。30→32配对均值差−.070347/+.009744/+1.696225，条件组成bootstrap95%区间分别[−5.4351,+5.3081]、[−4.9990,+5.0508]、[−.0905,+5.2246]。该区间不是独立训练seed不确定性。图已查看，5%仅原描述性建议，不新增成功率或策略恒定门槛。

## 正式33与下一轮准备

00:46:07 UTC从准确完整32全state启动有限一轮33，三check-only及PRELAUNCH_SCIENTIFIC_REVIEW通过。I/A/V learner **2463296 / 2463297 / 2463300**；startup2463353已完成，archive2463355、review2463357继续。实际启动审查I/A新增1000、V新增2000；全部旧1358250/1357250/1358250 replay、history、优化器配置、2m marker、30MJB/sampler与新增reward0误差通过。不是只凭启动PID宣称训练成功。

准确父SHA256：
- I d83a4796e5d87b40af40bfe4916ba7053aba4f4e8c235ba3abf958982aaaddff
- A aed47c2a80ba7bda6cef411adfad7749137708ab07576037a01c8084871b5c6e
- V 2e192b1360bcc47d58407d97fddea255f7ef005423a833d53a661bb50ef1507f

新34准备等待 **2501606**，原33审查CPU调度 **2501611**，7200秒，只完整33 FINISHED/REVIEW后check-only，无自动34训练。源码使用同时替换并核对准确父33/目标34/历史入口23、monitor适配；实际34恢复尚待。旧33准备1007211、调度1007212已完成；不要重复启动。

新非重叠33–35稳定性窗口等待 **2585589**：33三方法0完成条件、34/35未启动时登记，原5%/近零1/5000分类配对bootstrap，seed2026102735，7200秒。只完整三轮后只读分析，不自动训练/停止，仍待结果。

## 第32轮冻结全矩阵已启动

原PLAN在32启动前选定，SHA fed53352d96604d5aad339b7ad537d042040e2105646e94e1721d0448a120797。原prepare639955完成三check-only，随后本轮PRELAUNCH_REVIEW完成。I/A/V evaluator **2466385 / 2466386 / 2466387**，根review **2466388**。三路实际STARTUP_REVIEW通过完整learner/replay精确、原生3步随机动作逐值一致、同seed一致/不同seed改变及2负守卫，开始真实物理回合；尚未完成90回合或根REVIEW。

固定原30条件×3方法×55s，一个外部动作seed2026102638，最大123750动作/99000000子步；CPU52/53/54、GPU1/2/3、每路一个串行物理子进程。原随机CHEQ/context/mixing、冻结parent step；0优化/replay写入。逐回合物理/filter/torque、原生连续随机动作重放与最终完整state/source/checkpoint digest待最终核验。预算不延长、不排除条件、不补挑seed。这是训练条件上的冻结诊断，不是held-out、多训练seed或指定ESN最终比较。

## VMC固定954终端跟踪32

原1497589完成，保存值独立算术和图亦核对，无重跑推理。相同954行masked SSE **5032.518863→1491.623855**，下降70.36%；采用旧31分母的贡献也降至.165777，非仅新增replay稀释。完整32终端贡献.163869，其中旧954为.160726、新30为.003143。

short0600固定index1304222标签−28.432058、五mask全1，SSE **3525.548360→29.826790**；Q从[−5.34,+7.26,+4.72,−9.69,−12.07]移至[−25.93,−26.75,−24.30,−27.06,−27.09]。固定观测/动作/标签/mask和agent/forward RNG不变。原前向仅CPU权重恢复、不恢复优化器；新保存算术0神经推理/物理/优化。不能将终端端点改善解释为全部历史minibatch loss的因果份额或策略收敛。

## Direct与资源

Direct20原learner46632、archive46745/review46750继续；21准备87882/调度87883仍仅等待完整20后check-only，不自动训练。最后本次快照将在FINAL_LIVE_STATUS记录，勿凭本文旧进度重启。官方SERL10critic、随机2/min bootstrap、actor全10mean、noentropy backup、8:1、batch65536和32步targets保持。

GPU1–3在32结束至33恢复间确有切换空档，保留此事实。新混合20/33/冻结32固定60样本observer2560106，仅报告自身PROFILE结果，不复用旧纯20/32窗口或把冻结推理当纯正式吞吐。大checkpoint/replay/raw继续SSD，HDD仅小交接；不是HDD/arm1全量备份。

## 路径、同步与后续

服务器根：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
- 正式33：`runs/parameter_capacity_pool30_cycle33_20261026_v1`
- 完整32：`runs/parameter_capacity_pool30_cycle32_review_20261026_v1`
- 冻结32：`runs/parameter32_frozen_full30_20261026_v1`
- 固定30–32：`runs/parameter_capacity30_32_reward_stability_20261026_v1`
- VMC跟踪：`runs/vmc32_terminal_anchor_followup_20261027_v1`
- 34准备：`runs/parameter34_preparation_registration_20261027_v1`
- 固定33–35：`runs/parameter_capacity33_35_reward_stability_20261027_v1`

仓库小证据：`docs/evidence/RL_PARAMETER33_FROZEN32_20261027/MANIFEST.json`。开工已fetch/read两远端日志；提交前再次查询/fetch，main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d均未变。GitHub凭据已向用户询问，勿重复索取或找无关token；push成败按实际记录。指定ESN仍缺，勿用旧模型替代或再次提问。

优先检查原Direct20完整审查/21准备并接续；参数33完成后检查health图/完整review，再决定34；冻结32等待原根REVIEW，不重跑已结束条件。Goal保持active。

资源补充：固定60样本/65.5720秒混合20/33/冻结32窗口，GPU均值55.60% / 74.8667% / 72.4333% / 68.2833%，逐样本七个原训练/评估PID身份保持，保存均值另核验。非纯正式窗口、不保证每瞬时、不隐藏32→33切换空档；原observer2560106已结束勿重复。

Direct21实际首1000新增启动审查已通过：855532steps/6804264critic，旧854532 raw/derived/history/optimizer/clock保持，新139 mature+861pending精确，30MJB/sampler与奖励重建0误差。startup2826820已完成，四正式21/33与冻结32继续。最新实际进度和原进程身份见小证据FINAL_LIVE_STATUS.json；原20/32/准备及诊断均已结束的句柄不重启。
