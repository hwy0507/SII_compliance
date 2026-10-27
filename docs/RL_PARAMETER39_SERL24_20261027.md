# 参数38完整审查、36–38稳定性与正式39/Direct24

2026-10-27 UTC。Goal active，无子agent。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。上一轮修复24启动入口/准备25属于实际进展，本轮接收原38/23完整结果并启动39/24；未重跑旧辅助验证或冻结回合。

## 参数38完整结果

三路各30条件×55秒、41250新交互、无abort。全部旧回放字段/history/2m marker保留，新reward重建误差0，完整REVIEW/FINISHED、health网络不变及两张诊断图核对通过。SAVED_RESULTS_REVIEW使用独立stdlib scalar算术核验日志与37→38全30条件配对，0模型推理/优化/物理。

| 方法 | steps / updates | Task / Strict（30） | reward均值 | 首1000 / 末1000 loss | terminal MAE / inbag MAE |
| --- | --- | --- | --- | --- | --- | --- |
| impedance | 1605750 / 1600751 | 18 / 17 | -2.337858148 | 2.491048 / 2.351629 | 0.738056 / 0.180607 |
| admittance | 1604750 / 1599751 | 12 / 11 | -13.723332249 | 2.926592 / 2.070690 | 0.790137 / 0.333172 |
| vmc | 1605750 / 1600751 | 17 / 16 | -4.576257441 | 0.760637 / 1.613083 | 0.587500 / 0.301742 |

I/A/V整轮loss均值2.579313/1.815535/.759219，最大34.112003/33.634403/36.808697。阻抗整体均值略降、终端校准改善；导纳先下降后末段反弹；VMC最后阶段loss与temperature明显升高，末1000 loss1.613083较37的.805686约翻倍，inbag终端误差.204816→.301742。三温度为正、熵大致围绕原目标，VMC末段熵下降；数值有限不等于已健康稳定。

37→38配对：阻抗均值+.020684、无Task/Strict切换；导纳short0000 Task/Strict真→假贡献−1.738218，short0100 Task仍真/Strict假→真贡献+1.766420，净均值仍−.235548；VMC short0600 Task仍真/Strict真→假贡献−1.745955，净均值−1.724022。保存值算术不证明这些切换造成在线loss变化。不得因均值接近而隐藏成败互换。

完整38 SHA：I50bb762d6c1f03e3ae7f5df165e62213e5e79e5a67504078dd0a735790eb86f1；Ab70aeaa2451b6c979b36ba555fff027e7394540d8daa54fd6122e3455d32cbf0；Vafc59fdff00a5e81de110f65237865ba8f55c3ec394a54f5a36c6543ff919384。

## 原固定36–38审计已完成

原2889814完成，不重跑。全部输入/source hash、保存全30配对均值/百分比/斜率/原5%判据与图独立核验，5000分类bootstrap原结果保留，不重复抽样。三方法均未触发近零1保护。

| 方法 | 三轮reward均值 | 相邻变化百分比 | 首尾变化 | 原5%检查 |
| --- | --- | --- | --- | --- |
| I | −2.410359 / −2.358542 / −2.337858 | 2.1498% / .8770% | 3.0079% | 通过 |
| A | −8.537314 / −13.487784 / −13.723332 | 57.9863% / 1.7464% | 60.7453% | 未通过 |
| V | −2.841404 / −2.852236 / −4.576257 | .3812% / 60.4446% | 61.0562% | 未通过 |

36→38配对delta均值I+.072501/A−5.186018/V−1.734854；条件组成敏感区间95%分别[−5.341458,5.495763]、[−10.490177,−.112774]、[−5.245265,.069860]。I原描述稳定结果明确保留，不能凭bootstrap很宽否认已通过的算术判据；三路整体仍未稳定，VMC末段loss反弹也需继续诊断。这些区间不是独立训练seed或冻结策略置信区间，不增加Task或policy-invariance阈值。

## 正式参数39与后续准备

三39 check-only全learner/replay/RNG/next65536精确，原完整38 REVIEW/health/图、保存值和36–38窗口均读取后写PRELAUNCH。04:20:13 UTC正式I3314522/A3314523/V3314524；startup3314527、archive3314528/review3314529。最新完整38全state续一个有限39，原设置不变，检验末段变化是否持续；capacity replay与pair learner、原CPU/GPU/30pool、物理/MJB/gates/filter/dt/输入/奖励/历史entry23均保持。actual startup已通过首1000/1000/2000，旧1605750/1604750/1605750行和history/marker/action/clock精确，新reward误差0。

40仅准备3416298/原39审查CPU调度3416302，7200秒、无自动训练，登记runs/parameter40_preparation_registration_20261027_v1。五入口AST/准确39父与40目标/CPU39/历史entry23检查通过。初版静态检查错误要求脚本含65536字面量，实际batch从父登记继承；该检查先失败且未启动任何40进程，保留STATIC_CHECK_CORRECTION.json，改为核对三父登记batch65536并确认无覆盖赋值后才登记/启动等待。不是训练失败或更改batch。

新固定39–41只读等待3482651，runs/parameter_capacity39_41_reward_stability_20261027_v1。39零完成/40–41未启动时登记，原5%/近零1/5000分类配对bootstrap、seed2026102743、7200秒，0训练/无自动延期或启停；source AST/--help/hash/原定义核验。实际统计未运行，不替代36–38已完成结果。

## Direct23完整与容量24正式启动

完整23为977040steps/7776328critic更新，30全55秒/noabort、Task/Strict0/30、reward−30.904079451。全部935790旧raw/derived/history保持、新41250 reward和32步target精确、pending0。首/末1000 critic loss .013692485/.012778872，整轮.013286327、最大.026026407；720终端MAE.044915915、32步TD MAE.060509317、Qmean−20.537884，temperature.000422324。完整REVIEW/FINISHED/health与scalar算术和图通过；loss下降、Q平滑窄幅漂移，不能将零任务成功解释成任务已学会。

完整23 SHA837d596275bf7a0e791aff9e40ecb5ba3765cbb7eadf90cea4eca4d389b87666。原23 learner257351/archive257407/review257409及24准备1003919/调度1003920已结束，勿重启。

真实完整23的24 check-only已通过：全prepared state不变、全部replay/next65536/pytree/RNG与扩展后再次恢复精确，entry_migration=true；不是前轮full22辅助验证的替代声明。容量1m→2m，原validated driver/helper hash与sampler main保持，学习器/targets/reward/physics不改，不推广辅助权重。23的977040+41250=1018290会超过原1m上限，因此需已验证扩容，不能声称与假想环覆盖等价。

04:22:13 UTC正式24 learner3403962、startup3403964、首次1m边界3403965、archive3403966/review3403967，run serl_capacity_batch65536_cycle24_20261027_v1。上轮修正后的setup已实际执行，MONITORS四原句柄存在。actual startup和1,001,000保存边界结果另补，未到边界不可预称通过。原Direct24–26固定窗口1470790继续。

25静态准备沿用[前轮](RL_SERL25_INHERITED_PREPARATION_20261027.md)，现在已根据实际24 LAUNCH/MONITORS登记原等待3448092/CPU调度3448355，7200秒，WAIT_REGISTRATION.json保留旧静态REGISTRATION。只在完整24退出/REVIEW/health后恢复check-only，不自动训练25；旧/新2m，历史entry23、batch历史12保持。正式25需读24完整科学结果及首次边界结果，26入口仍待。

## 资源与继续顺序

新有界原进程退出观察3124153已完成，0 GPU工作，逐PID start_ticks核对；退出到新learner启动的实际间隔范围：D175.45–176.45秒、I218.66–219.66秒、A288.26–289.26秒、V274.23–275.23秒。它含科学审查/check-only，另有启动延迟；冻结推理/只读health期间GPU可有占用，不能当全部GPU空闲时长，也不能省略这些换轮间隔。

新单次混合24/39+冻结32 GPU observer3448359，先等两actual startup，再固定60样本。查原PROFILE，不重复择优；结果另补。原冻结32 2466385/2466386/2466387/根2466388继续原90回合，未改seed/条件/预算，根完整REVIEW仍待。

后续优先核原startup/边界/完整结果、VMC38末段loss反弹和导纳不稳定；准备40/25已在途。保持原冻结32和固定窗口，不凭回报部分稳定声明全目标完成。

本轮真实ls-remote/fetch/read main a3e9e0440506c60eea6c7bcfab9895846706e420、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，开工未变。HDD配额满；新HANDOFF与小证据归档SSD，现有HDD LATEST指针更新回读，大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。提交/push/归档收据另记。

实际24 startup3403964已完成：新增1000至978040steps/7784328critic，旧977040全部raw/derived/history保留，新reward误差0，2m marker、action/clock/MJB/30sampler核验通过。crossed_old_capacity=false，首次1m边界仍待，不将启动检查当边界完成。

原GPU observer3448359已完成，60样本/65.993721秒，四GPU均值[61.61666666666667, 62.71666666666667, 67.06666666666666, 64.68333333333334]%；七原PID身份全程保持，source/hash/保存均值独立核验通过。混合正式24/39与冻结32推理，非纯训练吞吐或每瞬时50%保证，不抹去上文换轮间隔，勿重采。

收尾fetch/read远端main新增d279535d07e862ea656955926eea0d109ae4076e，只更新另一主机非RL90/108进度，不是本机RL或最终指定ESN比较完成。已通过42f4a4d合并，UPDATE_LOG尾部冲突保留完整本地日志并逐字追加远端六行；冻结训练源码未改。baseline仍f6e8f8c。
