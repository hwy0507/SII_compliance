# 2026-10-26 参数10完整审查、目标Q上界投影与cycle11续训

Goal继续active，尚未健康收敛。最新已核验结果：参数10终端拟合较9改善，但非终端Q/loss仍异常；
新的有限投影诊断显著降低I/V过高Q和三路总体终端误差，已从正式10全state续一个在线cycle11。
Direct6完整审查与三固定代表冻结评估完成，仍0成功；原Direct继续登记7/8。不是最终比较或收敛证明。

开工与恢复核对远端main `5170ce75a9467012d31f5a227bc7c9ba6c2fbdda`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，读取日志、AGENTS及同步skill；另一主机非RL工作不动。
无子agent。B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
物理/MJB/gates/filter/执行器/dt5e-5/30条件/SPT reward保持；大产物仍本集群SSD，非HDD全备份或arm1归档。

## 参数cycle10：终端加权不是整体修复

| 方法 | steps / updates | Task / Strict，各30 | reward均值 | 全终端Q MAE | in-bag终端MAE | 末1000加权q_loss均值 |
|---|---:|---:|---:|---:|---:|---:|
| 阻抗I | 450750 / 445751 | 18 / 16 | −4.163368 | 7.241849 | 2.801344 | 95.344098 |
| 导纳A | 449750 / 444751 | 11 / 10 | −15.491328 | 2.692166 | 1.504965 | 742.014820 |
| VMC | 450750 / 445751 | 17 / 16 | −4.539727 | 47.789203 | 23.946345 | 7760.742444 |

三路每路新增41250，30/30完整55秒，无abort。全父replay前缀、完整cycle history、optimizer配置、
新增reward/done、30terminal/MJB和逐interval reward重建通过，误差0；这不是所有训练回合raw-substep重放。
原训练3818446/3818448/3818450、归档3818454和审查3965208已完成，勿重启。
正式checkpoint在 `B/runs/parameter_terminal128_archive_20261026_v3/{method}/cycle_00010.pt`：

- I `7ed5d338a8c1157f8363a702c4db51a9bdc80682a8aa8aff291f020f796b913c`
- A `95cb6544f08690887140fe875e6db3030791e0d74b83c59387a5e24f006163d8`
- V `17001598bd584121237f29823263c6b66d221ebd263dcf7c6973531baaa683ce`

Q抽样均值I83.100/A−136.002/V976.012；最大1533.589/6210.406/4603.153。
导纳负向漂移和任务回报下降，VMC正向漂移及加权loss升高，不能把终端误差改善当作整体恢复。
新加权loss与历史uniform loss不是同一目标，不直接据绝对数值比较。

审查缺口如实保留：原10 `REVIEW.json`覆盖三路，但其health脚本继承了仅I/A的method列表，
因此FINISHED不意味着VMC健康诊断完成。本轮只补遗漏VMC到
`B/runs/parameter_terminal128_cycle10_vmc_health_20261026_v1`，0训练/物理，图已看；原文件不覆盖。
合并健康索引在新probe的 `PARENT_HEALTH.json`，含两份来源hash，明确三路齐全。

## Direct6完整训练与冻结物理评估

训练cycle6：285867steps / 2246944critic updates，新增41024；Task/Strict0/30，reward−31.388793。
29完整55秒，`active_long_train_0000` 第1149动作global穿透>2mm提前终止，失败保留在分母。
全父244843前缀、官方8critic:1actor增量、30terminal/MJB、每条新动作映射/观测/nextstate/reward重建通过。
210历史terminal×10critic MAE1.738057、p95=1.601644、max37.8680；抽样Q均值11.83683、
TD MAE.029963、alpha.0008884。完整learner/optimizer/RNG诊断不变，图已看，0额外更新。
归档 `B/runs/serl_pool30_archive_20261026_v2/direct/cycle_00006.pt`，SHA
`f5cdc408d52420d395b7537646f38ad449c2c481574d966d431515961fee42c1`。

新的冻结评估 `B/runs/serl_cycle06_fixed_representatives_20261026_v1` 使用准确6，
三个预先指定代表passive_corner/active_short/active_long的train_0000，确定性推理、0optimizer更新。
三条均完整55秒，合计330万物理子步/4125动作；独立动作重放误差0，canonical48/public7、MJB、
filter重放、torque幅值/slew/previous-output recurrence/物理执行器链接核验通过，完整learner state不变。
Task/Strict0/3，均停在approach、无abort；人体接触0、舒适比NA。峰关节力矩约40.464Nm。
平均公共slowdown约.5972、最后10秒约.5634；public0才是nominal，增加第一通道意味着减慢WBC。
这些是行为观察，不宣称slowdown是失败的唯一原因。原507630/507861评估已结束勿重跑。
逐子步指标审查自身的filter_verified=False只说明该审查范围不含filter，独立filter审查另已通过。

Direct正式7/8已从准确6全state/history恢复，PID438669、GPU0、learnerCPU0、30sampler共享CPU1–12，
`B/runs/serl_pool30_cycle07_08_20261026_v1/direct`；官方固定SERL十critic、随机2target、不备份熵、
8:1、batch32768不变。仍零示范、无人工纠正/旧CHEQ权重或replay/nominal mixing。
启动核验新增10000/80000，完整285867父prefix、所有新映射与reward重建0误差、30真实亲和性/MJB通过。
归档438672，输出 `serl_pool30_cycle07_08_archive_20261026_v1`；7/8只读审查855997/855998，
对应 `serl_pool30_cycle07_review_20261026_v1`、`serl_pool30_cycle08_review_20261026_v1`。
脚本保留显式30条件，7父6、8父7，不做粗粒度cycle数字替换。有限7/8预算不自动延长。

收尾新增Direct7完整审查：327117steps / 2576944updates，新增41250，30完整55秒、无abort，
Task/Strict0/30、reward−31.158703；全父prefix/所有新增动作/obs/nextstate/reward重建0误差/30MJB通过。
240终端×10critic MAE2.422274、p95=41.245625；抽样Q均值15.854477、TD MAE.032019，正向偏差仍在。
全部learner/optimizer/RNG诊断不变、图已看，7只读855997已结束勿重启；原438669已进入登记8。
归档 `serl_pool30_cycle07_08_archive_20261026_v1/direct/cycle_00007.pt`，SHA
`a460207c21d86513c68c6e0d31a738852611b415458a476b74af4e121aad7c07`。

## 有限目标Q投影：真实收益上界，而非任意裁剪阈值

固定当前policy与alpha时，SPT潜势项望远镜求和为非正贡献，其他running成本≤0，
terminal+completion最多30。动作空间体积V给出最大微分熵log(V)，剩余n步的宽松上界：

`U(n) = 30 + alpha * log(V) * gamma * (1 - gamma**(n-1)) / (1-gamma)`，gamma=.9995。

新逻辑只把target critic pair的min Q向上界投影，然后才减随机采样的alpha*log_pi。
不裁剪整个随机Bellman target；不引入未经证明的下界。使用next observation的clock第49维恢复n，
最多1375动作，终端done仍清零bootstrap。浮点64计算、输出向+inf一ULP，避免float32向下舍入截窄上界。
这明确改变bootstrap学习目标，是CHEQ适配；不是等价性能优化，也不保证历史偏置target立即校准。
当前alpha变化下的诊断不是对未来所有alpha的统一上界。

有限probe：`B/runs/parameter_cycle10_projection_probe_20261026_v1`。
三路从准确正式10完整state/RNG出发，各原终端128对照与终端128+投影两臂，每臂5000、batch32768；
合计30000新辅助更新+入口2更新，0新物理，不保存/推广任何辅助权重。旧cycle9对照不适用于新parent/objective。
32组独立numpy上界比较、舍入/投影identity/终端目标/RNG检查通过；关闭投影时一次完整更新的
全部learner state/optimizer/RNG/metrics与原weighted实现逐项相同。
所有臂初始digest直接匹配正式父；相同实际replay抽样流、每臂20点、全部预算/有限值/父replay不变审查通过，图已看。
三原PID926784/926785/926786及只读957343都已完成，勿重复派发填占用。

| 方法 | 原设置→投影：终端MAE | in-bag终端MAE | 非终端absQ p95 | Q超过全局上界比例 |
|---|---:|---:|---:|---:|
| I | 7.2034 → 3.3049 | 2.5130 → 2.5260 | 1027.126 → 65.993 | 16.396% → 0% |
| A | 2.8401 → 2.0362 | 1.6342 → 1.0315 | 316.405 → 312.472 | 1.040% → .00977% |
| V | 56.3555 → 7.2207 | 28.2599 → 5.4278 | 3614.564 → 418.042 | 47.300% → 0% |

I in-bag拟合无改善，整体改善主要含out-of-bag；A的负向偏移仍在，投影后均值−168.767、min−1097.132，
不能称A恢复。V的uncertainty仍大、最小RL authority诊断比例仍100%。上界满足不证明正确return估计。
这些限制进入正式有限在线阶段的登记理由，不隐去负面结果。

## 参数cycle11：已启动、仅一个完整周期

`B/runs/parameter_projection_cycle11_20261026_v1/{impedance,admittance,vmc}/train`：
I1110503/GPU1/CPU13–25，A1110504/GPU2/CPU26–38，V1110505/GPU3/CPU39–51，各12sampler。
从各自正式10继续，所有网络/Adam/replay/RNG/history保留；不加载probe权重。
保留terminal weight128、pair2、batch32768、UTD1及原actor LR I/V3e-4、A3e-5，只加目标Q上界投影。
运行冻结源码 `B/runtime/parameter_projection_cycle11_20261026_v1`，来源hash、prepared commands、
三check-only正负守卫与fullstate严格相等检查齐全；加入marker后除此以外父state逐项相同。

checkpoint现在同时保存 `terminal_loss_weight=128` 和 `finite_target_projection`字典。
后续必须使用projected_class/helper恢复，禁止原PublishedLearner静默丢失两个目标设置。
本轮启动审查三路各1000新增，原replay前缀/history/Adam配置/精确UTD、12真实sampler亲和性/MJB、
clock/input/nextstate/reward全部通过。参数输入与公共运动输出按接口分开检查，未宣称重放A/V内部动态。

归档1110506，view=`parameter_projection_archive_view_20261026_v1`，output=`parameter_projection_archive_20261026_v1`。
11只读协调1131662，`parameter_projection_cycle11_review_20261026_v1`等精确边界，三路health显式齐全。
该health保留未投影fixed-pair TD作为校准诊断，明确不等同新投影目标的训练loss。
有限cycle11结束后必须先审查在线reward、成功率、原始TD/Q与终端拟合，再决定后续；无自动12。

## GPU与下一步

本轮中段旧四正式60样本：56.65/30.83/40.17/43.55%，尾部worker减少，非稳定50%。
有限probe窗口约64.86秒：56.13/57.28/56.75/57.88%，后三路为有限诊断，不能替代正式负载。
新四正式约64.57秒：54.68/41.33/40.87/40.47%，每卡50%仍未达；所有正式原PID在全部样本存活。
D/I/A/V约26.75/28.57/29.66/28.65 transitions/s；参数物理worker各约10核，learner约.75核。
有限诊断都已结束，不重复已完成实验填占用。当前需要继续改善实际物理采样/更新流水线，不能隐瞒GPU要求未满足。

下一步：收Direct8与参数11完整边界、核验注册marker/fullstate；观察目标投影在线是否维持Q校准，
重点处理A负向漂移和三参数passive失败；Direct冻结仍approach失败，不能以低TDloss称收敛。
最终冻结比较、ESN/SPT完整结果以及健康收敛均未完成。收据见
`docs/evidence/rl_projection_cycle11_20261026/SOURCES.json`，仅小证据进入Git/HDD备份，大checkpoint/物理轨迹在B。
