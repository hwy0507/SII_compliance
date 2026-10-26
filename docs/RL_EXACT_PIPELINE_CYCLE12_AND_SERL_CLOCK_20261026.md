# 2026-10-26 参数11审查、等价执行cycle12与Direct8时钟诊断

原Goal继续active：直接动作SERL与在线调参RL尚未健康收敛，每卡GPU≥50%要求也未达成。
收尾最新：参数12三路、冻结11九回合及Direct clock有限对照均已完成并审查；当前没有正式learner运行，尚未派发参数13/Direct9。完整12数值与checkpoint在文末。
本交接覆盖 `RL_TARGET_PROJECTION_CYCLE11_20261026.md` 的运行状态。不得依据旧PID重启已完作业。
本轮首先核对main a8bf20d3b955018abf95f27f3bf951f98625d148，收尾fetch/read并快进到
35c2f788b0001c8fbb0618ed0bde2472efa899e1；baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d。
另一主机非RL第五条件审查更新已保留，不干预其运行。无子agent。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
实际训练和大型产物在本集群B，未声称已全备份到HDD或arm1；HDD剩余不足300MiB，仅复制小证据。
物理/MJB/执行器/gates/filter/dt5e-5/30条件/SPT reward保持。完整网络、Adam、replay、RNG和历史保留。

## 正式参数11：上界投影改善终端拟合，导纳仍负向漂移

三路均新增41250、30完整55秒、无abort；父replay所有字段、history、optimizer配置、
30terminal/MJB、全部新增reward重建0误差核验通过。这不是全部训练raw-substep物理重放。

| 方法 | steps / updates | Task / Strict，各30 | reward均值 | 终端MAE / in-bag MAE | 抽样Q均值 | 抽样TD MAE | 末1000加权q_loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| 阻抗I | 492000 / 487001 | 18 / 17 | -2.356557 | 1.947651 / 1.080355 | -24.051789 | .546490 | 12.765707 |
| 导纳A | 491000 / 486001 | 15 / 15 | -6.917592 | 1.426678 / .627655 | -217.564331 | 2.206911 | 116.483059 |
| VMC | 492000 / 487001 | 17 / 16 | -4.587388 | 1.806715 / 1.120620 | -67.943657 | 1.587388 | 96.099746 |

抽样Q范围I[-103.877,46.323]、A[-843.555,42.024]、V[-529.137,51.876]。
原巨大正Q被压制，终端拟合改善；A的负偏差未修复，不能称健康收敛。
health的固定pair TD仍是**未投影校准诊断**，不等同于训练的投影目标加权loss。
审查与图 `B/runs/parameter_projection_cycle11_review_20261026_v1` 已完成并目视核对。
旧1110503/1110504/1110505、归档1110506、审查1131662均已完，勿重启。

正式归档 `B/runs/parameter_projection_archive_20261026_v1/{method}/cycle_00011.pt`：

- I `21319adea39dbfaf69dd61952c744f95e432c82d798303cb60d168b68e44963a`
- A `d410b71ca89355e92cb3abb9fb32eabc08775a0f76ef0be7e5d063e9b9916d93`
- V `9a3791e01c1b7198261b72a1c4cec8459629fef935f07bf5b2ca0899aa50d668`

checkpoint必须保留 `terminal_loss_weight=128` 和 `finite_target_projection`：version1、terminal_cap30、
gamma.9995、maximum_actions1375、upper_only true、位置为target critic Q在随机熵项之前。
后续用projected_class或exact_class恢复，原PublishedLearner会静默丢失目标marker，禁止直接替代。

## 等价执行优化：微基准通过，不等于在线提速

先完成 `projection11_live_stack_profile_20261026_v1`：非空Python栈中replay约12–14%、
target update约8–9%、checkpoint约8%、learner update约71%。各分类可能重叠，空栈另列，
这些不是CUDA墙钟占比。独立分母审查完成。

`published_exact_pipeline_20261026.py` 包含两项改动：

1. binary bootstrap mask抽样时，先看原抽样indices的前32行；若每critic已有正mask，则原完整batch必然可接受，否则回退原全量检查。NumPy抽样/拒绝顺序/RNG不变，refresh强制mask二值。
2. 原50个target参数逐张量Polyak更新改用foreach乘加；公式、顺序、batch、UTD、actor更新时机和学习目标不改。

有限验证 `B/runs/projection11_exact_pipeline_probe_20261026_v1`：
三方法各original/cache_only/cache+foreach，正反两个顺序，每次16预热+256计时，
总4896辅助更新、0物理、不保存或推广权重。使用已独立审查的cycle11启动1000步快照，
不冒称以完整11为微基准起点；其父与正式11一致。每方法六个最终完整state digest一致、
sample RNG一致、第一batch逐项相同、父replay不变，四种对抗mask情况通过。

| 方法 | 原实现 updates/s | cache+foreach updates/s | 微基准提升 |
|---|---:|---:|---:|
| I | 34.88365 | 37.05050 | 6.21% |
| A | 39.58593 | 45.03184 | 13.76% |
| V | 38.81001 | 44.26599 | 14.06% |

这是共享GPU上的有限更新微基准，不能据此宣称在线吞吐已提高或GPU达标。旧probe全部完成，勿重跑填占用。

## 正式参数12：从完整11续一个有限周期

`B/runs/parameter_exact_pipeline_cycle12_20261026_v1/{method}/train`：
I2261725/GPU1/CPU13–25，A2261728/GPU2/CPU26–38，V2261730/GPU3/CPU39–51，各12sampler。
保留原权重/Adam/replay/RNG/history、terminal128、投影、pair2、batch32768、UTD1、
actorLR I/V3e-4、A3e-5；只使用上述已验证执行优化。无辅助权重导入，无自动13。
冻结源码 `B/runtime/parameter_exact_pipeline_cycle12_20261026_v1`，三check-only全state不变、
正负守卫和来源hash通过。真实各1000新transition启动审查：父完整prefix/history/配置、marker、
12MJB/实际亲和性、参数输入/clock/nextstate/reward重建0误差通过。

归档2261734：view `parameter_exact_pipeline_archive_view_20261026_v1`，
output `parameter_exact_pipeline_archive_20261026_v1`。
只读审查2261752：`parameter_exact_pipeline_cycle12_review_20261026_v1`，三路health显式包含，等精确完整边界。
准备/启动/进度收据随小证据归档；核实当前PID身份，不按本快照重复派发。

正式12约64.49秒观察 `exact_pipeline12_gpu_profile_20261026_v1/PROFILE.json`：
GPU均值 **0.0 / 40.1333 / 38.6667 / 40.1667%**。GPU0正式Direct已结束，clock入口失败阶段无优化更新；
GPU1–3为正式12加低优先级冻结11推理，未运行辅助optimizer。
I/A/V约29.384/30.376/26.360 transitions/s，learner约.682/.685/.613核，物理worker约10.015/9.693/10.085核。
原正式PID全窗口存活。**未证明在线提速，持续每卡50%没有满足**；不以微基准或有限辅助占用替代此结果。

## 参数11新冻结评估

`B/runs/parameter_projection11_fixed_20261026_v1/{method}`，准确完整11，各三预指定代表：
passive_corner_train_0000、active_short_train_0000、active_long_train_0000。
确定性、0optimizer，最多9×55秒/990万物理子步，未新跑nominal。
协调器I2337200/A2337206/V2337210，evaluator2337542/2337577/2337573，CPU52/53/54、nice19、GPU1/2/3推理。
只读review检查准确checkpoint、完整learner state前后不变、raw-substep物理指标/filter/torque、
每步参数policy/mixing/clock重放1e-7、MJB与完整时长或合法abort；全部通过才写FINISHED。
运行中RESULTS只是已完成子集，不当完整三条件结果；收尾状态见本报告后续快照。

## Direct8：任务仍失败且比7退步

`B/runs/serl_pool30_cycle08_review_20261026_v1` 已完整审查并看图。
366962steps / 2895704critic更新，新增39845；Task/Strict0/30，reward均值 **-33.247895**（7为-31.158703）。
25完整55秒；5次global penetration>2mm abort保留在分母：
long0671第1207、passive0337第1208、passive0000第1215、passive0300第1216、short0400第624动作。
全父327117前缀、全部新action/obs/nextstate/reward重建0误差、30terminal/MJB通过。
270历史terminal×10critic MAE2.165311、p952.619545、max42.603771；抽样Q均值16.526279、
max18.378033、TD MAE.064937、alpha.00115346；诊断完整learner/Adam/RNG不变。
低TDloss与任务失败并存，不能当收敛。原438669/438672/855998全部完成，勿重启。

正式8 `B/runs/serl_pool30_cycle07_08_archive_20261026_v1/direct/cycle_00008.pt`，
SHA `f3399b01b550d8c3f4cac6b32f8cd49ca57f53beb68275aebbf3fe4d5a1d5b90`。
尚未派发正式Direct9。仍固定官方SERL commit1fa2af7496be042e43d36120a7c8d1b71f1bfb59，
零示范/纠正/旧CHEQ状态/nominal混合，10critic、随机2target、不备份熵、8critic:1actor、canonical48 actor/action7。
public第一通道=(raw_a0+1)/2，public0是nominal，增加该值减慢WBC。

## Direct critic clock：两次入口失败保留，第三版有限对照完成

共同历史时钟 `B/runs/serl_cycle08_clock_probe_20261026_v1/replay_clock.npy` 与CLOCK_REPLAY_REVIEW.json：
从五个正式journal精确重建366962行×2；每步覆盖一次、reward/done精确、270episode各一个done、≤1375动作。
动作j的当前clock=(1375-j)/1375，next=(1374-j)/1375，早abort同公式，未用未来奖励标签。
v2/v3复用该只读数组，不重新构建。

- v1扩展第一层旧kernel及Adam数组55→56输入；旧state可严格恢复，但Q入口1/2560差异.00020885超过原容差rtol2e-6/atol1e-4，失败。0optimizer更新，未写通过gate。
- v2保留原55输入GEMM，增零clock分支；Q入口通过，但actor精确检查1790/1792不一致，最大.00435504，失败。0optimizer更新。49维切片布局/JIT是当时假设，不写成已证明根因。
- v3将观测传为独立state48和clock叶，actor直接使用原连续48缓冲，critic经零clock分支进入首hidden。保留全部旧参数名/形状/Adam/counter/RNG，只添加online/target/六组moment共8个零叶。入口Q最大差异0，确定性及固定seed随机actor逐项相同，actor不受clock影响，剥离新叶后完整旧agent state精确恢复。

v3 `B/runs/serl_cycle08_clock_probe_20261026_v3`、原2791400已完成。
两个臂均从正式8全state开始、同NumPy抽样流，各2000outer×8，共32000critic+4000actor辅助更新；
0新物理，不保存或推广任何辅助权重，未部署正式clock adapter。20记录/臂、初始诊断一致、
来源/checkpoint/review/clock hash、抽样RNG/预算/有限值/父不变审查通过；COMPARISON.png已看。
固定270terminal及4096非终端样本，TD固定pair7/3是校准诊断。

| 指标 | 原设置对照 | critic clock |
|---|---:|---:|
| 终端MAE | 1.170832 | .985366 |
| 终端p95 | .853906 | 1.188293 |
| 终端最大误差 | 43.357594 | 43.271576 |
| 抽样Q均值 | 16.966883 | 16.990986 |
| 抽样TD MAE | .034698 | .032585 |
| 温度 | .001016716 | .000884714 |

平均终端误差局部改善，但p95更差、最大误差和正Q偏差依然存在；两臂Q均值均从16.579升高。
不能称缺clock已被证实为唯一原因，不能据此宣称在线任务改善或正式恢复。
两个失败版本/日志/源码均保留，不放松原入口判据，不重复有限probe填GPU占用。
新增read-only `review_serl_critic_clock_20261026.py` 可复核完成记录，不执行训练或物理。

## 下一步与证据

收正式12完整边界和三路冻结11独立审查，再针对A负Q、Direct终端大残差/approach失败判断下一步。
若采用Direct critic clock，必须另做持久marker、旧replay时钟迁移、正式8全state恢复和正负守卫，
通过后另登记有限在线9；当前只有辅助候选，不能用原SERL loader静默装入clock状态，也不能导入probe权重。
未选择未经证明的Q下界、没有任意重置或修改物理reward。正式采样/尾部调度与GPU持续利用问题仍待解决。
健康收敛、最终冻结比较与完整ESN/SPT均未完成。小证据索引：
`docs/evidence/rl_exact_pipeline12_20261026/SOURCES.json`；所有大型checkpoint/轨迹仍在B。

## 收尾：参数11九条冻结评估全部完成

三协调器及evaluator均已正常结束，三份FINISHED/REVIEW/FROZEN_STATE_REVIEW齐全。
每方法4125动作/330万子步，总12375动作/990万子步，9条均完整55秒、无abort。
每方法Task/Strict均2/3：被动0000失败、短/长主动0000双通过。全部完整learner state前后不变；
参数动作重放最大误差0，clock、MJB、filter、torque、raw-substep指标审查通过。
审查自身new_physics=0仅指只读审查未新增物理；本轮评估实际新增9回合，不能漏计。

| 方法 | 短主动完成时间(s) | 长主动完成时间(s) | 长主动人体接触(s) | 接触期间舒适比 |
|---|---:|---:|---:|---:|
| I | 12.76 | 20.12 | 7.97265 | 60.8305% |
| A | 46.48 | 37.88 | 4.97540 | 100% |
| V | 27.32 | 31.52 | 6.66435 | 100% |

被动及短主动均无人体接触，舒适比NA。I长主动虽Task/Strict通过，接触舒适比仅60.83%，
这些是不同判据，不把Strict通过替代舒适通过。所有失败保留，未做新的nominal配对或最终排名。

## 收尾：正式12完整审查，当前无下一正式阶段

三路各新增41250、30完整55秒、无abort；全父prefix/history/optimizer配置/marker、新reward重建0误差、30terminal/MJB通过。三路health和图均完成，诊断网络状态不变。原2261725/2261728/2261730、归档2261734和审查2261752均结束，勿重启。尚未登记参数13或Direct9。

| 方法 | steps / updates | Task / Strict，各30 | reward均值 | 终端MAE | Q均值 | TD MAE | 末1000 q_loss |
|---|---:|---:|---:|---:|---:|---:|---:|
| I | 533250 / 528251 | 18 / 17 | -2.213914 | 1.952962 | -20.614117 | 0.436833 | 5.475644 |
| A | 532250 / 527251 | 17 / 17 | -3.543742 | 1.021287 | -232.570078 | 2.186240 | 115.199278 |
| V | 533250 / 528251 | 17 / 17 | -2.841737 | 1.282832 | -77.636435 | 1.553613 | 98.974934 |

I终端最大误差94.267（11为55.792），平均拟合改善不能掩盖尾部。A/V的Q均值继续负移，A末loss仍约115、V约99；任务reward改善不证明价值网络健康。Goal保持active，下一步须从下列完整12继续，不导入辅助权重。

归档 `B/runs/parameter_exact_pipeline_archive_20261026_v1/{method}/cycle_00012.pt`：

- impedance: `6dfbe710b5e664bd4b385123f8b3ae0bce3a08d7dd879703f1e7eb6fbddac71c`
- admittance: `c1e7dd71f1a1b62c2278a1d3850af9fa4d1c66c846213ab0d1c42068d15ac0e1`
- vmc: `4c48707ef4b39dcdb77dd4b4ed67f9412e01e35e60887f68a4861622f9ba558a`

最新续接重点：参数12负Q与I终端尾部；Direct仍以正式8为父，clock仅有限候选；每卡GPU50%仍未达。当前正式learner均结束，这不是用户暂停Goal或达到收敛。
