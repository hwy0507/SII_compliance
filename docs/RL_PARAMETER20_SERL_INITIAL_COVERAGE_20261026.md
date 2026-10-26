# 参数20接续与Direct起始阶段覆盖诊断（2026-10-26）

原Goal active，未健康收敛。上轮完成参数18/Direct13完整审查、正式19/14接续、纯GPU窗口和暖目标对照，为实质进展。本轮继续原Direct14，完成参数19完整审查后从准确父启动20，所有正式网络/优化器/回放/RNG/计数器/历史保持。无子agent；物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward冻结。

运行根B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，仓库B/repository/SII_compliance，HDD用户路径为链接。当前大产物与完整证据主副本在SSD，未新核验arm1或HDD全备份。

## 参数19完整结果与20正式接续

| 方法 | 完整19 steps / updates | Task / Strict（每路30） | 平均reward | 末1000 loss | terminal MAE | sampled Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| Impedance | 822000 / 817001 | 18 / 18 | −.551137 | 1.232886 | .786093 | −5.194953 |
| Admittance | 821000 / 816001 | 11 / 11 | −13.804757 | 1.019088 | .708058 | +13.318574 |
| VMC | 822000 / 817001 | 17 / 17 | −2.832320 | .692171 | .540398 | +23.347702 |

每路各41250新增交互、30完整55秒、无abort；旧回放全部字段前缀/history/优化器超参/三个marker/MJB保持、新reward重建误差0。完整健康诊断不改变网络状态，图已目视检查。CHEQ mask0为刻意留出，terminal总体误差不等于全部是训练拟合误差。导纳Strict18→19为13→11，reward也下降；I/V成功数不变、V值继续移动，不称健康收敛或pool30因果改善。

完整审查B/runs/parameter_pool30_cycle19_review_20261026_v1下REVIEW/health/DIAGNOSIS/FINISHED齐全；旧learner3955897/3955898/3955899、归档3955903/审查3955904均结束勿重启。准确父在B/runs/parameter_pool30_cycle19_archive_20261026_v1/{method}/cycle_00019.pt：

- impedance：926431df324e94bea73a0319e0719a891da9d2fec423efbcd5d2df1d421ad32d。
- admittance：0a41c4a45fa6c30df36e3490bbf9e10a05a943daa1613c278ea2d09b5d20407b。
- vmc：2a0125569ef53853e47386cf104176e84721fe06c8af97e7fa9267b81347bd08。

正式20在B/runs/parameter_pool30_cycle20_20261026_v1/{method}/train，I1127927/A1127928/V1127929；GPU1/2/3、learnerCPU13/26/39，30sampler分别共享14–25/27–38/40–51。一个有限20，batch65536/UTD1/terminal128/上界projection/I target min+A/V target mean/actor min/原LR与全部正式state不变。

新resume_cheq_pool30_reviewed_continuation_20261026.py将pool19入口推广为连续完整周期接续；严格验证最新父、连续注册链、历史13 batch probe、原18→19的pool迁移与正式17准备来源。sampler_pool/shared_sampler_stage原样继承，不能将旧准备伪装成本轮实验或回退17。三check-only完整state/重复恢复/负守卫通过，实际三路各1000新增的全部旧前缀/history/markers/MJB/参数动作/clock/reward0误差与30sampler亲和性通过。CPU集合比较沿用已修复frozenset，无重复旧startup错误。

归档1127932到parameter_pool30_cycle20_archive_20261026_v1，完整只读1127933在parameter_pool30_cycle20_review_20261026_v1，startup1127931完成。没有自动21，必须在最新完整周期审查后接续；参数必须pair_class恢复全部marker。

## Direct14原进程继续

原PID3955892在B/runs/serl_multistep_batch65536_cycle14_20261026_v1/direct，GPU0/learnerCPU0/30sampler共享1–12；归档3955895、完整审查3955896仍待原14完整结束。设置保持官方10critics/random2/noentropy/8critic:1actor、batch65536、32步、canonical48/action7、gather+transfer，不重启、不回退、不导入辅助权重。最新完整Direct父仍为13；不能把未完整14当父。

前轮暖目标对照完整32步vs1步已经结束，terminalMAE.056348/.363541、mean|gradQ|.027682/.005896；单步候选未部署、不重跑。完整source/review可追溯到serl_cycle13_warm_horizon_probe_20261026_v1。

## 已有轨迹：Direct离开初始就绪区域

新增audit_direct_approach_coverage_20261026.py，B/runs/serl_cycle13_approach_coverage_20261026_v1。只读准确完整Direct13全部30条及参数18三路各30条，共120完整轨迹；0新物理/优化/权重，无示范注入或纠正。源、物理journal、NPZ和TERMINAL全部hash记录，REVIEW/FINAL_SCIENTIFIC_REVIEW与首秒图完成并目视核验。

Direct30条全部1375采样行均为approach，参数18每条只有最初4个记录行处于approach（原状态机约0.2秒保持后前进）。Direct初始位置误差约3.8e-8米、旋转误差约1.5e-6rad，随后速度/位置误差上升；首秒图显示约.08s速度越过.025m/s、约.16–.20s位置越过.012m、约.44s旋转越过.12rad。现有采样记录三阈值同时满足的最长连续段为2行，尚不能独立重放原状态机保持门。

Direct每条件位置误差中位数的30条件均值.582197m、旋转.135790rad、速度.060072m/s；位置/旋转/速度阈值采样占比均值.003539/.401745/.148121，同时满足.001455。全程public0均值.467365，平移/旋转残差绝对均值.440479/.350415。参数初始公共输出为零是既有运行的描述性比较，**没有将其作为Direct示范或混合动作**。不同策略/周期/状态分布不是因果对照。

日志误差是在task.update之后针对当前waypoint记录，route切换行不等于更新前gate输入；因此不能把采样阈值占比冒充独立gate/dwell重演。没有更改原12mm/.12rad/.025m/s/.2s规则，也没有放宽成功定义。

Direct13折扣奖励逐项重建，全部总reward与原episode一致，PBRS恒等式误差<1e-10。平均折扣项：progress−.560239、occupancy−2.690276、time−.723280、slew−.041999、penetration−.073318、peak torque−.359722、terminal−12.574916；无人体接触成本。初始phi .112048、每条件最大phi的均值.112049、终止phi .068898，说明这些轨迹几乎没有增加接近/搬运势。

完整失败轨迹的折扣PBRS确实telescopes为−5phi_initial，但occupancy仍依赖phi；不能说整个奖励恒定或无approach信号。奖励实现保持冻结，接下来的研究方向是已有早期交互的学习覆盖。

## 有限早期回放候选：复用已完成对照，不重跑基线

新增probe_serl_early_replay_20261026.py和review_serl_early_replay_20261026.py，B/runs/serl_cycle13_early_replay_probe_20261026_v1。协调1191698、只读review1231275，等待新的纯正式GPU窗口完成后运行。

从准确完整Direct13网络/optimizer/RNG/replay开始，候选仅一个2000outer（16000critic+2000actor）预算，batch65536/32步/官方8:1不变。每批先按原ready顺序和原RNG采样65536行，再用独立登记seed2026102615从已存各episode前32步等概率采样32768行，替换每个奇数位置；交错安排避免8个critic小批中只有后半有早期行。早期行由已存critic clock≥1344/1375识别，不把clock新增给actor。原replay不写回，0新物理、无新奖励或示范/nominal mixing、不保存或推广权重。

均匀基线直接复用前轮serl_cycle13_warm_horizon_probe_20261026_v1/horizon32_RESULT.json，准确相同正式13全state、同2000更新/65536批与诊断seed2026102614。候选必须逐项匹配初始完整state、原始均匀rowdraw摘要和最终原采样RNG；候选实际rowdraw应不同。原control整批与部署sampler精确检查继续保留。不重跑已完成control填占用。

改变抽样分布没有重要性校正，不能声称优化了同一经验分布目标。固定4096状态的旧诊断可与已完成control比较；新增1024早期状态诊断仅有候选前/后，旧control没有保存这项，不能伪造对照值。最终REVIEW/FINISHED/INDEPENDENT_REVIEW/FINAL_SCIENTIFIC_REVIEW齐全，图已目视检查，原协调1191698/evaluator1369467/结果审查1231275均结束勿重跑。全部初始state、原始均匀rowdraw摘要/最终RNG与已完成control匹配，实际候选draw不同；13440早期行，占原565782行约2.38%。候选完成2000outer、16000critic+2000actor，0physics/无保存权重。

| 共同固定状态诊断末值 | 已完成均匀control | 半批early候选 |
|---|---:|---:|
| terminal MAE | .056348 | .074165 |
| 单步TD MAE | .081214 | .089267 |
| 32步TD MAE | .065922 | .071064 |
| Q mean | −20.620266 | −20.672495 |

候选自己的早期状态TD从.137355升至.151933，early mode residual幅度.558644→.591516、public0 .537141→.571652；没有显示拟议的起始阶段改善，因此**不部署early采样**，正式14设置不变。两种采样分布的训练loss不能直接作为同一目标比较，不能仅凭更高loss称发散。此有限诊断不排除其他覆盖比例/策略，但不重复探针填占用，也不声称在线任务改善。

## 利用率与发布

B/runs/batch14_parameter20_gpu_profile_20261026_v1，观察1152868：登记180次采样，等参数20启动审查通过后进行，逐样本检查GPU PID只属于四正式。候选GPU计算必须等该窗口结束，禁止拿混合辅助占用替代正式证据。原窗口已完整结束：180样本207.645494秒，四卡均值56.1611/73.6389/73.5278/73.4611%，D/I/A/V10.2242/24.4262/25.2401/25.0330steps/s；四正式learner全样本live，GPU PID逐样本核验。窗口四卡均值≥50%，非瞬时永久保证；观察1152868已退出不重采。

开工重新fetch/read实际main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，无远端更新。本轮起点0bcbe52；GitHub凭据待恢复，用户已被问过不重复索要。最新小证据及来源hash在docs/evidence/rl_parameter20_initial_coverage_20261026，带时间LIVE_STATUS区分当前正式进度和已完成科学结果。

下一步核对原20/14及early replay探针句柄，完成完整审查后衔接最新正式父。Goal未完成，不能以失败稳定或低loss替代任务学习与健康收敛。HDD仅小交接/收据，完整小证据与大型checkpoint/raw在SSD；不称HDD或arm1完整备份。
