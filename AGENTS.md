# 本仓库的持续工作约定

用户于 2026-09-30 明确授权并要求：**每次对话结束前，将本次文件改动 commit 并 push 到
`https://github.com/hwy0507/SII_compliance` 的 `main`，同时维护根目录 `UPDATE_LOG.md`。**
本约定适用于本仓库后续任务，覆盖旧进度文档中“保持未提交／不发布”的历史要求；用户后续
明确变更指令时，以新指令为准。

## 新用户任务：已发表基线与训练集比较（2026-10-25 后续澄清）

最新接触读取有限对照v1/v2均结束：三类×5状态，编号/顺序/dist/frame及读取前后积分状态精确一致。
v2 CPU计时bulk IDs局部2.33–4.66倍、中位4.55；只测编号提取，不是完整物理/奖励/轨迹等价或GPU提速。
v1 wall共享调度波动，已保留；共30 mj_forward、0 mj_step/更新，正式runtime未改。下一步可在
独立候选验证完整循环/轨迹，不能凭microbenchmark部署。source12原8/9及SAC09继续，13仅准备。
证据PUBLISHED_CONTACT_ACCESS_PROFILE_20261025.json；两probe进程1714191/1749461已退出。

最新只读physical worker采样完成：60s/4895样本/0错误，Direct source12 active-short0600；
observer inclusive53.50%、mj_step叶18.82%，默认排除idle，仅单worker采样分母，不当全局瓶颈或提速。
未改physics/遥测/运行时，无新仿真/辅助更新。证据PUBLISHED_PHYSICAL_WORKER_PROFILE_20261025.json。
四CHEQ12/四SAC09继续更新，原8/9阶段不得提前替换；GPU四卡50%仍无达成证据。

最新后续准备：source_train13 / completed_stage_dispatch_v2已冻结但**未部署或派发**。修复source12
后续factorNone固定要求3e-4的问题，显式登记/核对父LR可原样保留3e-5及完整周期历史，拒绝重复乘.1；
不改plateau/actor/目标/物理合同。5+8共13测试和四个真实低LR准备状态全字段保留检查通过，
0新physics/更新/权重导入，无STOP。证据PUBLISHED_UNCHANGED_LR_PREPARATION_20261025.json；
runs/unchanged_actor_lr_preparation_v1/CANDIDATE_PROTOCOL.json仅结构候选、缺科学review，不是可执行的阶段登记。
当前四CHEQ仍source12运行原8/9、四SAC09继续；必须完成并复核当前阶段，不能提前迁入13。


最新source12在线GPU窗口：60样本/67.60s均值42.22/30.42/31.08/31.48%，min5/9/0/0，无辅助GPU
更新、含固定Direct推理，四卡50%仍未达到。原始ACTOR_LR_ONLINE_GPU_60S_01.json。

**当前实际训练：actor LR新阶段已启动，优先于下方旧快照。** 原critic-reset cycle6/7四路及旧audit/
review全部正常结束并复核：cycle7 Task/Strict0/0、18/17、14/12、17/17，各30，被动全0/10，
四路critic末段loss仍增；不称修复/收敛。新科学review为runs/CRITIC_RESTART_FINAL_SCIENTIFIC_REVIEW_V1.json。
80,000次actor LR有限辅助更新已结束、四辅助进程退出，0physics/无权重导入；小幅数值收益仅支持在线试验。
新runs/actor_lr_online_seed20261025_v1 / source_train12真正更新cycle8，actor LR统一3e-5，
其余权重/critic/alpha/Adam moments/RNG/replay/masks/目标/物理合同保留，不再resetcritic。旧critic_restart
字段仅历史来源。两新完整周期8/9后复核；不是总训练预算或收敛门槛。PIDs Direct919723、Impedance923788、
Admittance927495、VMC932939；coordinator911732正常完成、archive941236（行动前重验）。
source12沿用已证明等价target梯度优化，新完成阶段dispatcher无STOP、必须读完整父归档及科学review。
13测试和真实完整checkpoint/四路状态保留检查通过。不要重启旧source08或live-parent旧迁移器，source11未用。
SAC09四路仍继续。新只读audit969396/reviewer969397等8/9，登记ACTOR_LR_STAGE_AUDIT_V1与
ACTOR_LR_PAIRED_REVIEW_V1；3h仅observer保护，不停训练。证据PUBLISHED_ACTOR_LR_CONTINUATION_20261025.json。
cycle3固定矩阵12/12完成，全部物理/filter/torque审计通过、无机器安全违规，Strict0/2/1/2（各3），
不当完整cohort排名。新cycle7同12条件矩阵已在CPU54运行，coordinator803220、Direct evaluator804667；
冻结source08 cycle7，不是新actorLR策略。nominal75/120，CPU52/53继续。详见PUBLISHED_FIXED_CYCLE03_COMPLETE_20261025.json。


最新边界：Impedance完成cycle7/409721步、Task18/30 Strict17/30、被动0/10，原两轮预算正常退出，
cycle7已归档。勿重启旧981510；其余三路source08仍完成7，四SAC09继续。原auditor900989/reviewer2655393
等待整组；source11继续仅准备，整组科学复核尚未完成。详细证据见PUBLISHED_CONSISTENT_DISCOUNT_AND_PASSIVE_20261025.json。

最新：consistent_discount_fresh_cycle06_v1全完成，四路×两arm×5000=40,000有限辅助更新，进程全退出。
同fresh全learner/采样，对cycle6全部30个完整回合的独立副本匹配Bellman与PBRS gamma .99/.9995；
两项测试和真实奖励重建通过。低gamma组Q/终端误差略低，但两组Q仍增、alpha仍适应，且远期成功
信用骤减；不应用到正式训练。0physics/无权重保存或导入，原replay不变。报告图已检查。
只读被动0900对比：cycle3曾37.32s成功，5carry失败，6/7lift失败；相同MJB/规划/fixture，7首align
29.72s。单条件changing-policy证据，不当固定策略成功或因果结论。详见PUBLISHED_CONSISTENT_DISCOUNT_AND_PASSIVE_20261025.json。
混合GPU60样本均值50.28/12.17/36.73/21.85%，仍不达四卡50%，记录辅助退出，不当纯正式吞吐。
正式source08仍cycle7、SAC09继续；source11仅准备，不提前STOP/协调器，等全部7及原审计/review后继续。


最新奖励尺度有限对照reward_units_fresh_cycle06_v1已完成：四路×两尺度×2500=20,000辅助更新，
0physics/无保存或导入权重/父replay与正式训练不变，四辅助进程均退出。两项测试通过、报告和图已核验。
scale1/.04同fresh actor/critic/alpha/RNG，仅sample reward不同；初始alpha相同导致相对熵压力改变。
换回原奖励单位后缩放组Q/终端MAE更大；温度仍在适应，无长期/在线优劣结论，不应用为正式修复。
证据PUBLISHED_REWARD_UNITS_PROBE_20261025.json。最新60样本GPU均值38.97/43.38/27.17/34.73%，
min均0，四卡50%未实现；CYCLE07_POST_PROBE_GPU_60S_01.json。四CHEQ source08仍cycle7、四SAC09
继续；source11仅准备，原cycle6/7完成并复核前不写STOP/启动performance协调器。


最新固定评估：cycle3矩阵9/12，Admittance被动/主动短期失败、主动长期成功；三项审计通过、无机器
安全违规。长期42.88s/49.95Nm/100%对nominal42.48s/54.16Nm/100%，短期低力矩仍失败。CPU54
现评VMC，evaluator3248872（重验）；nominal64/120。与当前reset cycle6明确分开。

最新：四路critic-reset cycle6全部完整归档、进入原登记第二轮7，auditor900989完成cycle6，
reviewer2655393完成5→6，两者等7；0诊断更新/physics，图已检查。Task/Strict1/1、18/17、16/16、17/16
（各30），Direct严格0→1、Admittance13→16、Impedance不变、VMC17→16，被动仍全0/10。
Q133.87/123.41/326.08/1384.20，当前alpha上界超限0/37.95/99.50/0%；VMC critic仍增长。
不是四路收敛或修复成功，继续原两轮试验，source11不提前部署/勿写STOP。详见PUBLISHED_RESTART_CYCLE06_REVIEW_20261025.json。
SAC第二完整周期只读诊断diagnosis_sac_cycle01_all_v1已FINISHED并退出，Task/Strict0/0、17/16、
14/13、18/18（各30），被动全0/10；Q/loss较首轮增长，Direct99.85%超保守上界，不与不同曝光CHEQ排名。
SAC四路source09仍训练，最新全cache GPU窗口均值39.28/32.17/10.87/28.77%，仍未四卡50%；
ALL_SAC_CACHE_GPU_60S_01.json，含CHEQ周期交替与GPU2评估。新证据PUBLISHED_SAC_SECOND_CYCLE_20261025.json。

最新SAC接续完成：四路都在source09真实更新，MIGRATION_FINISHED已落盘，原协调器已结束。
Direct1010728/Impedance1557140/VMC2397784/Admittance2758791，常规archiver2767227（重验）。
不要重启旧SAC进程或迁移；下方Admittance仍排空是本轮稍早快照。

最新完整周期：Impedance已完成critic-reset cycle6，368471保留步/41250新增，Task18/30、Strict17/30，
与父5相同且成功条件名单无增减；reward −2.25857→−2.41005，同17成功条件平均时间16.65→19.38s。
被动仍0/10，首轮无任务收益证据；当前进入原登记第二轮7，其他方法6尚未全部完成，勿提前截短试验。
新只读配对review PID2655393，runs/CRITIC_RESTART_PAIRED_REVIEW_V1.json，冻结runtime/
critic_restart_paired_review_v1；等原auditor900989生成完整6/7报告，自动比较5→6、5→7、6→7，
0physics/0更新、不管训练生命周期。观察失败不等于训练失败。4项测试与实际parent自比较通过。
历史cycle3报告因缺明确网络不变证据被拒，日志保留，不放宽guard。详情PUBLISHED_RESTART_FIRST_CYCLE_20261025.json。
SAC VMC也已迁入source09并更新，新PID2397784；Direct/Impedance同样在09，Admittance仍旧06排空。
原协调器2370128继续，禁止重复迁移。以上PID行动前必须重验。source11仍仅准备，未部署。

最新GPU窗口：辅助退出后60样本/67.64s均值50.48/23.65/31.15/43.10%，min13/0/0/0，
仍未持续四卡50%；RESTART_ONLINE_GPU_60S_02.json，含GPU2固定评估，source11未运行。

最新：target-gradient实际运行时v2验证完成，四接口两顺序4096辅助更新全used-state/非target梯度
精确一致，0physics/无权重导入，所有辅助进程退出；共享负载提速0.972–1.293倍，不保证在线提速。
source10首次接续协议检查因umbrella含CHEQ/SAC而被错误CHEQ-only guard拒绝，未启动，失败保留。
已新冻结source11（不覆盖10），learner/helper与已验证10完全相同，仅trainer改amendment作用域；
8项软件测试和实际协议验证通过。REGISTRATION_CHEQ_TARGET_GRADIENT_PREPARED_V2仅准备，
**没有STOP/协调器/替代训练**。保持source08原critic-reset两轮cycle6/7，完成科学复核后决定是否采用；
不要提前运行performance协调器截短试验。source11优化不再重置critic，全部学习状态保留。
cycle3矩阵6/12，Impedance两主动通过、被动失败；长期20.64s/51.66Nm/37.27%对nominal
20.52s/52.26Nm/24.07%，三个物理/filter/torque审计通过，无机器安全违规；仍非整体或收敛结论。
CPU54现评Admittance，nominal59/120；原四路CHEQ和四路SAC继续，行动前重验真实进程。
详情docs/RL_PUBLISHED_DIAGNOSTICS_20261025.md及PUBLISHED_TARGET_RUNTIME_VALIDATION_20261025.json。

最新补充：SAC Direct和Impedance均已迁入source09并真实更新，其余两路仍排空。nominal57/120。
四路critic-reset启动后的60样本/66.81s GPU均值57.17/47.87/28.50/33.22%，min2/0/0/0，
辅助更新和profiler已结束，含GPU1固定评估；SAC Impedance启动时间与窗口关系另存证据，不称稳态
独占测量，四卡持续50%仍未实现。原始RESTART_ONLINE_GPU_60S_01.json。

- **最新实际状态：critic-reset四路全部交接成功，原协调器已正常结束。** 当前run仍为
  `runs/critic_reset_online_seed20261025_v1` / source_train08；新Direct1471404、Impedance981510、
  Admittance1373289、VMC1099359已产生真实新steps/updates（行动前重验PID身份）。常规archiver1477077。
  early归档已正常退出无遗漏，父cycle5四个checkpoint全部归档，父进程正常结束；不要恢复旧STOP或重启协调器。
  当前cycle6，仍按登记运行两个新完整周期6/7；两轮结束需自主复核/继续Goal，不把阶段结束当收敛。
- 父cycle5四路Task/Strict为0/0、18/17、13/13、17/17（各30），无健康收敛。新只读阶段审计器
  PID900989，`runs/critic_restart_stage_audit_v1`（冻结runtime/critic_restart_audit_v1）已完成父cycle5
  全报告/图，正等新cycle6/7精确归档；0更新/0physics，三小时仅是observer派发保护，不停训练。
  父Q均值10913.10/6996.29/122751.82/68614.76，末1000更新critic loss约8.18万/13.22万/9008万/1225万。
  网络不变和回合奖励核验通过，图已目视检查。不要把巨额Q解释为高任务回报。
- `runs/critic_restart_early_health_v1`已经结束：当时仅Impedance/VMC有新checkpoint，分别新增
  6000/4000transition、12000/8000更新，Q均值32.07/447.27，当前alpha上界120.64/4709.82，样本
  无超界；in-bag终端MAE32.30/440.51，全来自父replay且当时无新完整回合。图已检查，VMC仍有Q
  增长/loss回升，不是收敛或成功证明。诊断新增父/新终端分栏、精确reward源码上界合同和网络不变检查。
- 60s live py-spy剖析完成：14995样本/0错误，11996空Python栈，2999可识别栈中更新60.32%、
  等仿真25.21%、replay6.27%、checkpoint3.20%、actor3.00%；不能把空栈当GPU空闲或声称全卡提速。
  profiler装在独立tools/py_spy_0_4_1，正式Python环境未改，profiler已退出。
- 新候选 `published_target_gradients_20261025.py` 仅抑制unused target参数梯度，保留actor通过动作输入
  的梯度；**未部署到正式runtime**。`runs/target_gradient_validation_v1`两顺序×四接口×256/arm，
  4096辅助更新结束，完整learner/optimizer/alpha/RNG及所有非target梯度精确一致，只有unused target
  梯度按设计不同。父状态不变、权重丢弃，进程都退出；两顺序提速1.009–1.197倍但共享负载/顺序波动，
  不当在线提速或GPU50%证明。当前critic-reset科学试验的learner源码和其他设置保持。
- cycle3固定中期矩阵3/12已审计：Direct三回合均55s失败于carry、无机器安全违规，physical/filter/
  torque审计通过；active-long接触6.7698s、阈值比例100%，不能替代成功。当前CPU54评Impedance，
  evaluator847406/协调器3686420（重验）。nominal本次55/120。SAC Direct已迁入source09新run并真实
  更新，其他三个仍在原cache协调器2370128排空；不要重复派发。详情见最新诊断文档及
  `PUBLISHED_RESTART_HEALTH_AND_PROFILE_20261025.json`。目标仍未完成，指定ESN仍缺。


- **最新科学修复派发（优先于下方历史快照）**：`runs/critic_reset_online_seed20261025_v1`，
  `REGISTRATION_CHEQ_CRITIC_RESTART_V1.json`，协调器PID429389（行动前重验）。父CHEQ performance v3
  正在cycle5，STOP_REQUESTED是完整周期边界交接；勿恢复父进程或重复启动协调器。新阶段不是精确性能
  接续：仅重置critic/target/critic Adam，保留actor/alpha/它们的optimizer、RNG、replay/masks、reward、
  gamma、batch16384/UTD2和全部physics/control合同。新seed2026102528，每路两个新完整30条件周期后复核。
  不导入辅助权重；critic变化会改变CHEQ uncertainty/mixing输出，规则未改。新阶段cycle history清空，
  父history和checkpoint保留在restart receipt，不能跨reset拼接收敛曲线。初始仅排空，须读MIGRATION/
  LAUNCH/PROGRESS确认实际更新。source_train08未改，准备/协调器冻结runtime/critic_restart_dispatch_v1。
  三种真实接口网络的软件回归和实际Direct完整checkpoint准备通过；这不是已证明的优化修复。
- CHEQ第五完整轮cycle4四路Task/Strict为0/0、17/16、15/14、17/17（各30），平均reward
  −32.889049/−4.035049/−8.756420/−2.836609；全部归档无遗漏。Direct由6/30退化至0/30，
  四路passive仍0/10，不称学习收敛。正式SAC仍由原cache协调器排空，禁止另开迁移。
- `runs/value_bound_cycle03_v1`完成0更新/0physics：120回合奖励/势能望远镜及replay对齐通过，
  四路固定alpha的保守global soft-Q上界3404.05/3654.93/15888.00/18637.88；5critic×4096样本
  超界99.49/51.05/57.64/62.79%。说明该固定policy/alpha价值未校准，不定位某个bug。hidden-clock
  阈值仅作上下文诊断；无时钟critic的terminal MAE也可能含观测混叠误差，不能要求其必然归零。
- `runs/policy_feedback_cycle03_v1`三arm×四接口×1000更新全部结束：冻结actor/alpha显著减弱
  Direct/VMC的短窗增长，但Impedance/Admittance仍增长。固定alpha单独无效，非长期因果证明。
  `runs/fresh_critic_evaluation_cycle03_v2`两batch×四接口×3000=24000辅助更新也全部结束；冷critic
  Q转负且无正global超界，但仍移动、终端误差未消除，不能说恢复收敛或batch256更优。等更新不等采样。
  两批辅助权重丢弃，不作常驻GPU负载。fresh v1因CPU/CUDA不变性比较错误在0更新/0physics退出，
  v2修复比较设备，保留失败；新在线仅reset一因素，未改变batch或引入新的奖励/信息。
- cycle1固定中期矩阵已FINISHED，12/12审计完成：四路passive失败，Direct两个active也失败，
  三参数方法两个active通过；无机器安全违规，不是完整30条件最终比较。新cycle3同12条件/同nominal
  矩阵 `runs/interim_cheq_cycle03_representatives_v1` 正在CPU54，协调器3686420、Direct evaluator3686874
  （重验）；标签前缀改为cheq_cycle03_，无重复cycle1评估。nominal本次47/120，继续CPU52/53。
  没有最终共同SPT参考、指定ESN或完成比较；GPU持续四卡50%仍未证明。

最新补充：critic-reset early archiver PID500618；协调器已写四路边界交接STOP，尚无替代learner，
无MIGRATION_FAILURE。nominal后续49/120。辅助更新结束后的60样本/66.75s GPU均值
34.43/38.67/34.88/39.22%，各卡有瞬时0，仍未达持续50%。原始SOURCE08_ONLINE_GPU_60S_02.json。

以下条目保留此前阶段证据；发生状态冲突时以上方最新条目和真实进程/收据为准。

- **最新GPU replay缓存接续：CHEQ已完成，SAC仍排空，勿重复启动。** CHEQ从performance v2/source_train07迁入
  `runs/cheq_performance_seed20261025_v3` / source_train08；SAC从performance v1/source_train06迁往
  `runs/sac_performance_seed20261025_v2` / source_train09。CHEQ协调器正常完成，SAC协调器PID2370128（重验）。
  四路CHEQ已在新run实际更新cycle4；SAC尚无新learner，旧Direct在cycle2，其余cycle1。旧run的
  STOP_REQUESTED是迁移请求，不可恢复。CHEQ第四轮全部归档无遗漏，新常规archiver PID2660326。
  首次启动因误指向父runtime未包含的协调器文件而退出，未创建STOP/子作业；失败收据保留，
  已用独立冻结runtime/device_replay_dispatch_v1修复。先查MIGRATION_PROGRESS/FAILURE和真实句柄。
- source_train08/09各只改变trainer和新增device cache；分别保留07/06的原learner、算法、physics、
  actor/filter/gate/dt。CPU replay/RNG/checkpoint仍权威，GPU只同步缓存/gather，多占约0.40–0.42GiB。
  两轮反转顺序验证共6144辅助更新全部state/optimizer/target/alpha/RNG/replay/gradient精确一致；
  辅助权重丢弃、进程已结束。9项协议/replay/归档软件测试通过，不把微基准加速当GPU50%达标。
- 新run各有early_cycle_archive迁移期监视器，跟随逐步增加的learner列表，待协调器启动常规
  cycle_archive后自行退出，避免先迁入learner完成周期时漏存；不是另一套训练。旧archiver继续保存父周期。
- CHEQ第四轮四路Task/Strict为6/6、18/17、13/13、17/17（各30），均值−22.61414/−2.24736/
  −10.43662/−2.81063。Direct首次1个passive严格成功，另5个active-short；参数三路passive仍0/10。
  缓存接续后60样本GPU均值40.90/33.22/40.12/32.10%，仍未达50%；所有辅助更新进程已结束。
  `runs/diagnosis_cheq_cycle03_v1`完整只读诊断/图已结束：四路in-bag终端MAE358.05/1063.08/
  21892.57/8474.15，Q均值4607.57/3691.79/32102.17/18220.59，critic继续恶化；下一步重点是价值
  学习稳定性，不能因Direct成功数增加就称收敛。未选定新的科学修复或改奖励/discount/critic信息。
  SAC Direct第二轮0/30，均值−35.57527，全部
  失败于approach，2个原2mm穿透abort，40978新增步。只读诊断Q均值3401.98、终端MAE329.77，
  最近1000更新q_loss624.17，仍恶化；不是健康收敛。runs/diagnosis_sac_direct_cycle01_v1已结束。
- 最新中期固定cycle1矩阵6/12审计完成：Direct三失败；Impedance passive失败于carry，两个active
  Task/Strict通过。active-long完成52.40s对nominal20.52s，接触阈值比例74.48%对24.07%，峰矩
  51.54对52.26Nm，是单条件效率/舒适折衷，非总体改善。CPU54现评估Admittance；nominal31/120。
- `runs/action_value_cycle12_v1`已完成0更新/0physics只读诊断，进程已退出，不作常驻GPU负载。
  cycle1/2同1024状态×12相同候选动作，replay prefix/网络不变；cycle2跨critic分歧中动作均值偏置
  仅解释12.24/32.72/17.83/28.74%，去偏置后所有候选uncertainty仍>.2。不能把问题仅归于共享
  价值偏移，也不能把Q偏好当真实动作改进。正式reward/gamma/mixing阈值未改，无替代修复被选定。
- 上次finite-check接续已全部迁入 `runs/cheq_performance_seed20261025_v2` / `runtime/source_train07`，
  四路已产生真实steps/updates，正在cycle3（第四整轮）。v1正常结束，cycle1/2全部归档无遗漏；
  新归档器继续。迁移保留全部learner/optimizer/RNG/replay/masks/history，只优化finite检查。
- 第三整轮cycle2的Task/Strict分别3/3、17/16、12/11、17/17（各30）；平均reward约
  -27.8272/-4.2768/-13.7767/-2.8037。Direct首次成功但其他改善不一致；所有方法passive仍0/10。
  Impedance active_long0000触发原2mm穿透abort，581步，完整周期新增40456步，其余41250；保留失败。
  `runs/diagnosis_cheq_cycle02_v1`已完成只读诊断/图，Q和critic loss仍明显增大，不称健康收敛。
- SAC四路也已全部完成旧cycle0并迁入 `runs/sac_performance_seed20261025_v1` / source_train06，
  真正更新，正在cycle1；原cycle0严格成功0/16/12/15（各30），每路82500更新。
  `runs/diagnosis_sac_cycle00_v1`已完成。它与CHEQ第三周期不是相同曝光，不能据当前数值排算法优劣。
  **这两套较早的finite-check迁移已完成；最新cache迁移状态看本节顶部，禁止重复派发。**
- `runs/discount_sensitivity_cycle01_v1`四接口×两gamma×2000更新全部完成，总16000辅助更新。
  深复制完整恢复且父状态不变；.99降低Q但终端误差仍大，且1374步终奖折扣约1e-6，.9995约.503。
  只改辅助Bellman gamma，stored reward仍含.9995 shaping；不是完整替代objective，不能选为正式修复。
  正式gamma/reward/uncertainty阈值未变，辅助权重不得进入比较，所有辅助进程已结束。
- Direct固定cycle1的3个中期回合均完整55s失败于lift，physical/filter/torque审计已通过；
  active_short/long的nominal成功，不能用RL低峰矩/高接触比例替代完成。CPU54现评估Admittance，
  整体6/12已审计；nominal矩阵本次31/120，继续CPU52/53。未选最终T_ref。
- source07迁移后无辅助训练窗口GPU均值38.33/30.98/30.08/32.22%，50%目标仍未实现；
  不能把finite-check微基准加速或已结束辅助作业写成在线达标。原始记录SOURCE07_ONLINE_GPU_60S_01.json。
- `runs/soft_target_mixing_cycle01_v1`只读诊断已结束，0更新/0physics；cycle1样本四路CHEQ几乎
  全部映射到最低混合权重0.2，近期每路1000真实transition也全部context0.2。熵项平均为负，
  不可把巨大的正Q解释成该样本的正熵奖励。绝对uncertainty阈值的奖励尺度适配仍需验证，未修改。
- `runs/learner_profile_cycle01_v1`有限64更新剖析已完成且不保存权重；finite检查约占27.9%、
  replay采样约14.6%调用时间。最新66.5s GPU均值42.13/47.35/37.87/39.71%，未达50%。
- `runs/concatenated_finite_check_validation_v1`因验证脚本反复恢复时共享CPU optimizer step tensor
  而未通过全状态等价；失败保留。v2 deep-copy每个恢复并检查父状态不可变，四路全部通过。
  旧terminal/batch辅助工具也缺同样防御复制，源码已修复；旧结果不再称optimizer完全一致的对照，
  未重写旧runtime/结果，也没有把辅助权重放进正式训练。source_train07只变finite helper。

- 历史主训练 `runs/cheq_performance_seed20261025_v1` / `runtime/source_train06` 已在cycle2结束并迁出；
  完整cycle0/1/2历史保留。source_train06只减少有限值检查同步，不改学习更新。
  性能迁移保留network/optimizer/target/alpha/RNG/replay/masks/history，区别于早期LayerNorm重启。
- 第二完整周期（cycle1）严格成功0/17/13/16（各30），上一周期0/18/12/16；平均return约
  -33.0687/-2.2419/-10.4761/-4.6481。改善不一致，不能宣称充分学习/收敛。critic loss和Q仍增长。
  `runs/diagnosis_cycle01_dispatch_v1`已完成，结果在 `runs/diagnosis_cheq_performance_cycle01`，
  四路cycle1精确checkpoint已归档、无遗漏，不重复执行该监视器。
- SAC四路已由原协调器迁入 `runs/sac_performance_seed20261025_v1` / source_train06，
  正在cycle1。原 `runs/sac_layernorm_seed20261025_v2` 四路均正常结束，checkpoint和父收据保留。
  **旧run的STOP_REQUESTED是协调迁移，不是取消Goal；先查原进程、LAUNCH/MIGRATION收据，禁止重复派发。**
- 正式训练占52核；CPU52/53继续执行 `runs/nominal_four_interfaces_cohort30_v1` 的120回合固定矩阵，
  不是空闲资源。逐回合physics/contact/filter/reward审计和失败保留，未完成矩阵不选最终T_ref。
  CPU54为只读诊断、轻量协调和有限辅助GPU作业共享。
- `runs/terminal_fitting_replication_v2`两个seed2026102511/12、四接口、两采样variant均已完成，
  SUMMARY.json已落盘，所有辅助dispatcher正常结束。terminal10%降低in-bag误差，out-of-bag基本不变，
  普通误差略升；这是固定标签拟合，不是策略改善。权重不得混入正式比较，不再当常驻GPU负载。
- `runs/batch_sensitivity_cycle01_v1` 四接口各两variant×2000更新均完成，SUMMARY.json已落盘。
  同cycle1父状态直接切batch256使in-bag终端误差高于16384；是等更新非等采样、继承大batch状态的
  离线敏感性，不能宣称官方小batch较差或在线最优，不改正式batch/reward/replay；辅助进程已结束。
- 当前CPU54运行 `runs/interim_cheq_cycle01_representatives_v1`，冻结四个cycle1 checkpoint，
  每接口在每类首个登记条件（passive_corner/active_short/active_long的0000）评估，共12回合，
  配对固定nominal同条件记录，含physical/filter/torque审计。原训练52核和nominalCPU52/53保留。
  这是中期固定策略诊断，不是完整30条件最终比较，不选择最终T_ref。先查LAUNCH/PROGRESS/FAILURE，
  不把CPU54当空闲或另开重复评估。源码冻结 `runtime/interim_matrix_v1`、audit wrapperv6。
- `runs/interim_impedance_torque_audited_v2` / wrapperv6完整55s透明性验证已通过：原checkpoint、
  原cuda:1、同条件，物理/actor/接触精确一致，1375次filter及13750次公共力矩投影重放误差0，
  与1100000物理子步实际执行器力矩精确对应；幅值/slew/原limits通过。该回合scale<1次数0，
  激活幅值投影分支由单测覆盖。不是native reference/wrench/Jacobian重建，也不是最终策略验收。
  v1仅排队未physics即取消，旧收据保留，不恢复；本次真实审计已结束、释放CPU54。
- `runs/parameter_cycle_audit_v1`此前90回合123750次参数shield精确重放通过，rate限制约
  53.87/70.23/53.32%、energy限制0；参数确实改变。重放保存的storage state不等于全局被动性证明。
- 最近无辅助拟合的周期末尾60s GPU均值22.80/25.18/15.93/14.82%，当时每learner只剩1–3个回合；
  最新完整并发加batch诊断60s均值50.20/50.03/50.92/55.85%，该窗口平均达标但含辅助作业。
  batch辅助结束后最新在线加单次GPU0推理窗口42.67/36.47/37.93/39.87%，仍未达50%。
  需区分完整并发/周期尾部/辅助负载，GPU性能问题未解决。
  指定ESN仍缺；无充分收敛、完整最终矩阵或ESN比较结论。详见执行/诊断文档。
- 持续 Goal 的最新授权优先：用户已将论文选择、必要方法/接口适配、三类任务集上的仿真和
  四卡4090训练决策交给当前 agent，取消总训练步数上限，要求训练至改善后稳定并公平比较。
  不再就上述已授权事项重复询问。仍须保留原始任务/安全判据，记录新模型来源和所有适配，
  不把新编译模型冒充缺失历史MJB，不把短窗口平坦或阶段结束当作收敛。
- 用户已授权搜索并尽量忠实适配已发表data-driven柔顺控制方法、设计任务奖励、训练参数RL/
  直接动作RL至有学习改善后的reward稳定且loss诊断正常，然后与指定现有ESN在训练集比较。
  此授权覆盖本会话早先的只读等待要求；具体接口适配按上述最新授权单独登记。
- 本轮训练集SPT按用户新要求，用全部登记结果中最短严格成功完成时间作共同T_ref，称为
  `SPT_empirical`；明确事后参考及训练集范围，不重写旧实验或冒充预登记规划参考SPT。
  力矩参考阈值可经验登记/先行校准，但不按方法或最终排名反调；无人接触仍记NA。
- 读 `docs/RL_PUBLISHED_BASELINE_SELECTION_20261025.md`：候选来源、官方代码SHA、
  真实依赖缺口及新指标工具。该筛选文档记录的是当时的依赖缺口；现在新source runtime和训练已启动，指定ESN仍未定位；
  不得重新生成不同模型充当归档模型。CHEQ的控制混合上下文属于算法适配，须明确登记；
  不引入障碍物真值等部署不可得actor输入。

## 当前 RL 交接与服务器授权（2026-10-25，优先于历史资源约定）

- 接手 RL 先读 `docs/RL_SERVER_START_20261025.md`（项目介绍、4卡并行、当地启动入口），
  再读 `docs/RL_SPT_TRAINING_HANDOFF_20261025.md`（reward、优化器、收敛和审计）。
- 关于两篇柔顺控制论文的迁移判断，继续读取
  `docs/RL_TWO_PAPERS_TRANSFER_ASSESSMENT_20261025.md`：只采纳参数残差、历史本体输入和
  privileged critic 分栏等设计原则；论文平台的动作、奖励、阈值和结果不能直接当作 FR3 配置。
- 用户更正服务器有 **4张RTX4090、55核CPU**，要求尽量利用算力、多组并行；服务器 agent
  自行确认当地路径/设备并执行，无须向本机 agent 提供地址。**该新授权覆盖下文及旧 skill
  中“本机计算、服务器只归档”的限制。** 不因此修改旧run收据、物理/MJB、gate、actor输入或dt。
- 新入口初始支持四路独立learner、一卡一路、四接口×三seed、每方法每seed最多百万真实步；
  先实测完整回合及真实更新，再扩大并行。服务器逐job登记GPU UUID、CPU集、RAM/显存、
  环境版本与hash；本机3GiB限制只适用本机，服务器新run默认每路8GiB/禁swap，按实际内存准入。
- 本次只发布方案/代码，未启动训练。SPT导向reward是训练代理；正式完成时刻/T_ref和人体
  舒适阈值仍待登记/标定，不得将其写成已有的正式SPT/安全认证结果。

## 当前评估标准（2026-10-25 起）

用户已将本项目的人机柔顺控制评估标准改为：优先保证人身安全、机器安全和任务完成，再比较完成效率。
后续 RL、ESN、经典控制和其他方法的正式对比必须读取并遵守
`docs/EVALUATION_STANDARD_SPT_20261025.md`：主效率指标使用 **SPT（Success-weighted Path Time）**，
不再使用 SPL 作为主效率指标。主结果必须同时报告 Task/Strict success rate、SPT、峰值广义力矩、
人体实际交互期间的舒适力矩合规比例，以及机器安全违规率。不得用 reward、低力矩但未完成任务，
或无接触时段的低力矩比例替代这些指标。SPT 的参考量、舒适力矩阈值、接触分母和安全门必须在
实验开始前登记并冻结，不能根据测试结果回调。

## 每次开工前与存储偏好

- 本仓库任务使用 [sii-research-sync](skills/sii-research-sync/SKILL.md)。先查询远端分支并
  获取、读取 `main` 和 `baseline` 上的 `UPDATE_LOG.md`，记录 SHA 和与本任务有关的更新，
  再开始研究或修改。分支／日志缺失须如实记录，不自建、不使用陈旧引用冒充最新状态。
- 历史本机计算/归档默认如下；本轮服务器训练服从上方2026-10-25新授权。既有文件共享位置为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`。
  源码存 `source/<commit>/`，实验存 `runs/<branch>/<run-id>/`；使用独立目录与 hash 核验，
  不覆盖既有服务器 runtime。允许本地工作副本和缓存，历史数据不自动迁移或删除。
- 新更新文档的代码与产物位置优先指向已核验的服务器绝对路径，同时保留实际计算主机、
  Git SHA、环境版本和源/产物 hash。未上传的文件明确写“仅本地、待同步”；不改写历史执行记录。
- 每次收工重新读取本文件并执行以下流程。若其他 agent 有用户明确指定的 baseline 分支
  工作约定，遵守其授权；不得擅自把 baseline 全分支合并到 main。

## 每次交付前

1. 检查分支、远端、工作区和并行任务，保留他人的改动；通常只提交本次任务的文件。
   本次首次同步另获授权纳入截至 2026-09-30 的已有研究积累。
2. 在 `UPDATE_LOG.md` 顶部增加记录：日期、修改目的和文件、验证、研究结果与局限、未完成项。
   不以任务阶段名或文件名推断成功，不把开发结果写成正式结论。
3. 做与改动相称的验证，检查暂存差异、大文件和敏感内容。仅为答疑且无文件改动时，不必造空提交。
4. 显式暂存目标文件、提交，检查远端 `main` 是否前进，然后正常推送到 `main`。
   不使用 force push，不重置或覆盖其他 agent 的工作；必要时安全整合远端提交。
5. 核对远端包含新提交；最终回复说明提交号和更新日志位置。若认证、网络或冲突阻止发布，
   如实说明本地提交和远端状态，绝不声称未完成的 push 已成功。

## 产物和实验边界

- **2026-10-16用户开启持续Goal**：用户明确要求持续推进四类RL直至有可验证收敛证据，
  遇到问题自主诊断修复。该新授权承接原15小时训练任务；旧run仍按原截止保留真实收据，
  后续使用独立登记的有限阶段预算，不把旧窗口结束或阶段跑完当作Goal完成。允许有记录的
  超参数/训练奖励/训练任务调整，最终物理/MJB、Task/Strict gate、canonical48输入、公共
  filter、执行器限制及dt5e-5保持；本机计算、服务器仅归档。当前stage01登记25步回报、
  UTD1、四方法各新增最多11k交互、24小时派发保护、单模拟器/3GiB/禁swap。后续阶段依据
  证据登记，不自动无界派发；完成仍须训练收敛、四方法完成及最终独立测试/审计。

- **baseline验收目标（用户2026-10-10再次澄清）**：要求实现正确、调参有充分且可审计的
  依据、比较条件公平，不要求baseline在复杂任务中一定成功或解卡。排除实现/调参缺陷后
  仍卡住，应保留为该方法在所测条件下的失败；不得为强行过关持续添加手工恢复机制、改环境
  或无限追加搜索。完成已登记的有限调参并如实报告证据和局限，不能仅凭卡住就断言实现有错，
  也不能跳过实现与调参核查直接宣称proposed优越。

- **历史本地计算限定（2026-10-09；本轮被2026-10-25服务器授权覆盖）**：新的RL baseline修复、训练、仿真和分析
  全部在本机运行，禁止使用Spark算力；这覆盖下方历史批次的服务器计算授权。
  服务器只可做既有文件读取/传输/归档，不启动或恢复旧训练队列。先测本机内存和吞吐，
  再登记有限预算与并发；保留OOM保护和失败，不以占满GPU作为进展。
  本轮`baseline_local_rl_20261009/campaign_v2`在完整单回合预检后登记本机两路并行，
  每路最多一个模拟器/3GiB/禁swap，数值线程1，合计最多6GiB；启动可用内存至少7GiB。
  以其`LOCAL_RESOURCE_AMENDMENT.json`为准，不外推并发，也不与原单路调度器重复启动。
  **2026-10-10经典搜索资源调整**：用户指出本机利用不足后，
  `classical_boundary_search_20261010_v1`允许在原回合及审计结束的安全边界交接至本机2路。
  每路单线程/3GiB/禁swap、分别绑定CPU1/6，首次派发可用内存≥7GiB、已有1路时≥4GiB；
  共最多6GiB worker上限，仍占用同一全局仿真锁。以该run的`DISPATCH_V2.json`为凭据，
  原90回合/参数/条件/seed/worker来源/排序规则不变，不重复已完成回合，不启动服务器计算。

  **2026-10-10过夜15小时baseline接续**：用户授权一次性15小时窗口，
  `sii-overnight-baseline-20261010.service`先等待上述经典90回合自然完成；随后在全局锁释放、
  可用内存≥7GiB且没有活动RL服务时，从已保存的RL checkpoint创建独立
  `outputs/baseline_local_rl_20261009/overnight_15h_20261010/`并接续。协调器不持有仿真锁等待，
  不覆盖旧`running`收据；RL每路仍1线程/3GiB/禁swap、服务器不计算，15小时是有限安全窗口，
  不是收敛或成功条件。经典与RL失败均保留，最终比较需独立审计后再做。

- **2026-10-11恢复防复发**：用户在发现昨夜启动失败后重新授权本机继续RL并监视。
  使用独立新run保留失败；协调器不得持有全局仿真锁调用会再次获取该锁的子进程。
  子失败必须传播非零退出码，实验失败收据优先于systemd的success；启动后核对真实steps/
  updates/完整回合/checkpoint，不能仅凭active宣称推进。停止用独立STOP_REQUESTED在回合
  边界落盘，不向整个进程组发送停止信号。当前两路3GiB/禁swap/1线程限制不变。

- **2026-10-13公平比较加速（用户新授权）**：`fair_comparison_20261013_v2`可按
  `dispatch_v3/REGISTRATION.json`切换为本机最多4路独立回合，CPU1/6/2/7、每路1线程、禁swap。
  先完成当前子作业并保留31个已完成拟合，再交接原全局锁；不改冻结source或39拟合/288回合协议。
  第一个原计划ESN完整回合测内核cgroup峰值（含审计压缩），只有保留≥2倍余量时神经策略
  worker才用1.5/2GiB上限，否则3GiB；经典/RL保持3GiB。派发须满足
  `MemAvailable ≥ 新worker硬上限 + Σ(运行worker硬上限−当前cgroup内存，最低0) + 0.75GiB`。
  上限4路不等于必须开4路；内存不足等待，基础设施失败停止新派发并收完其他在途回合。
  旧STOP_REQUESTED仅按登记hash消费为本次交接，新停止入口DISPATCH_STOP_REQUESTED。
  不重算完成回合、不延长原48小时派发截止、不使用服务器算力，不关闭用户桌面应用。
  **同日实测补充dispatch_v4**：完整55秒ESN的内核峰值1,159,131,136字节，原粗档位会
  将所需2.16GiB向上取整至3GiB，妨碍并行。v4改为1.5–3GiB间每0.25GiB一档，保持
  ≥2倍峰值，神经worker初始2.25GiB。其他类别先3GiB，在该类别完整回合测得峰值后
  按同一规则下调；取已完成完整回合峰值最大值，短回合不降低上限。同样的内存准入/
  总4路上限/固定实验预算；复用39拟合、已完成回合和原pilot。v3的停止文件仅用于登记
  交接，当前停止入口为DISPATCH_V4_STOP_REQUESTED。以dispatch_v4/REGISTRATION.json为准。

- **Spark显示配置保护（用户2026-10-09明确要求）**：保持Xorg自动识别显示器。
  `/etc/X11/xorg.conf`当前不存在，旧强制headless/HDMI配置仅存为
  `/etc/X11/xorg.conf.sii-backup-20261009`，不得为训练、EGL渲染或远程访问恢复它。
  已恢复时实际输出为`USB-C-1`、2560×1440约60Hz；这是观测值，不应硬编码端口/模式。
  研究任务不得修改Xorg、GDM、GRUB、显示驱动、显示分辨率或创建强制虚拟显示配置；
  如确需系统显示变更，必须有用户针对该变更的新授权。计算使用现有离屏运行时。
  详见`code/mujoco_6d_vmc_benchmark/docs/SERVER_DISPLAY_INCIDENT_20261009.md`。

- 不提交凭据、私钥、环境目录、临时锁或运行日志。大型原始轨迹、编译模型和视频保留本地／
  原实验服务器；提交配置、源码、报告、必要的小型证据和产物 SHA256 清单。
  `.gitignore` 不等于删除产物，Git clone 也不等于完整原始数据备份。
- 发布时说明缺失的大文件、绝对路径和运行时依赖；复现实验须按 execution.json 核对解释器、
  MuJoCo 版本、模型及源码 hash。不得用重编译后的不同模型冒充归档模型。
- 当前优先修正 teacher 并验证特化条件，再做纯 ESN。未经用户新授权，不改冻结环境、gate、
  actor 输入、执行器限制，不解封保留条件，不把 dt=1e-4 开发结果当作 dt=5e-5 正式结果。
- 保留失败回合。读取进度、运行服务和 execution.json 后才启动实验，避免重复；本机一个
  MuJoCo 环境、1–2 线程、MemoryMax≤3 GiB，Spark 总仿真并发≤4。
  **本批次例外（2026-10-08）**：用户再次要求加速并充分利用服务器算力后，
  `office_v7_uniform24_20261008` 已在回合边界从 4 路提高到 8 路；每路仍为单线程、
  MemoryMax=3GiB、MemorySwapMax=0，只用高性能核。以该 run 的 `DISPATCH_V2.json`
  为调度补充协议，不恢复旧四路协调器，不修改冻结物理/模型/条件，不擅自外推到其他作业。
- **新批次例外（2026-10-08 21:23 CST）**：用户另授15小时baseline修复/重评并开放本机与
  Spark算力。`baseline_repair_15h_20261008`登记Spark新仿真并发≤10、单线程/每worker3GiB/禁swap，
  本机仍≤1个模拟器；保留四个历史暂停RL进程。以新批次PROTOCOL/后续资源收据为准，
  不把旧四/八路限制误作本批必须等待审批的条件；也不无界增加并发或改环境/gate。
- 用户给出小时预算时，协议必须记录授权起点、派发截止及依据。自动化的 RRULE/UNTIL
  只表示唤醒日程，不构成延长计算预算的授权。若会话、协议与日程时间冲突，先核对来源；
  无法确认剩余预算时停止新派发，保留已启动回合并完成审计，报告冲突后等待新的预算。
