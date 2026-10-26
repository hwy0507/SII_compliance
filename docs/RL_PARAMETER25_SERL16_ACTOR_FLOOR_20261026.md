# 参数24实际跨界核验、25接续与Direct actor熵下限对照（2026-10-26）

原Goal active，未健康收敛。无子agent。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库B/repository/SII_compliance，HDD原路径是链接。冻结物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward/canonical48/action7，正式优化器/回放/RNG/history不重置，不导入辅助权重。大产物SSD，HDD仅小交接与收据，非HDD/arm1全备份。

本轮重新核验原Direct16、参数24四learner均在运行，未重启。按仓库sii-research-sync实际查询/fetch/read远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变。GitHub认证此前已请求恢复，不重复索要。

## 实际跨过100万条审查完成

B/runs/parameter_capacity_pool30_cycle24_20261026_v1/capacity_boundary/REVIEW.json passed。原跨界检查2362754正常退出，勿重复。
阻抗1001000/996001、导纳1001000/996001、VMC1002000/997001，新增14000/15000/15000；旧987000/986000/987000条所有字段精确保留。capacity2000000/持久marker/cursor=size、历史/优化器超参/30sampler/30MJB/action/clock通过，新增reward重建最大误差0。该审查只读原训练快照，0新增物理/优化，不是新轨迹复模拟。

容量扩展的历史入口绑定完整23父，不在后续25中重写为24。过原1m后仍采样旧数据，分布与原环形覆盖不同；不得称后续整个算法等价。后续必须capacity driver和带标记回放类、pair_class learner，不用默认1m Replay。新2m上限写入/RNG前拒绝覆盖。

## Actor熵下限的实现与有限验证

原完整14梯度诊断发现初始Q/alpha熵梯度norm比80.50，原alpha约.000798；本轮只登记一个0.1下限压力测试，不扫描、不称最优。来源为最新完整15 checkpoint：B/runs/serl_multistep_batch65536_cycle15_archive_20261026_v1/direct/cycle_00015.pt，SHA70c9068b34a7d014f8b093d1c89fb0ed0420af35d07f8ff687e529636a503998。

新helper继承准确官方SACAgent，只把有效actor熵系数变为max(raw_alpha,.1)。原温度参数和不受约束的dual优化器保留，不是等价的约束dual SAC。critic仍无entropy backup、10critic/random2-min bootstrap；actor仍all10mean；32步/8:1/batch65536/原精度保持。没有正式持久marker或部署loader。

B/runs/serl_cycle15_actor_entropy_floor_gate_20261026_v1已完成，原2875668退出。准确下一65536行和RNG精确；完整原learner/replay不变；零下限完整8:1更新state/metrics逐位等同native。六负守卫（负数/NaN/inf/未登记.05/重复转换/entropy backup）通过。官方actor目标差expected .385531425476、actual .385532379150在原容差内。critic-only与temperature-only两臂完整state/metrics精确；actor-only两臂差异仅actor参数和优化器。隔离断言是两臂差异，不声称每个未选择优化器绝对不变。共18critic/4actor/4temperature辅助更新，丢弃；0physics/不保存权重。

## 两臂完整结果与决定

B/runs/serl_cycle15_actor_entropy_floor_probe_20261026_v1已完成，原3020505与结果review3158348退出。两臂各2000outer/16000critic/2000actor/2000temperature，准确同15完整state、同65536采样行与RNG；固定seed2026102622、4096均匀诊断行和480起始/终端。初始网络诊断精确相同，只有有效actor系数按设计不同。最终sample/agent RNG和draw digest匹配，原checkpoint/replay保持；0physics/不存权重/无推广。

| 末点指标 | 原学习alpha | actor下限0.1 |
|---|---:|---:|
| raw学习alpha | .0007456546 | .0001224096 |
| 有效actor系数 | .0007456546 | .1000000015 |
| 起始熵 | -22.421530 | -2.346657 |
| current熵 | -3.584078 | 4.616954 |
| terminal MAE | .047622 | .092180 |
| 32步TD MAE | .051011 | .111292 |
| Q均值 | -20.557819 | -21.366669 |
| 起始public0 mode | .944865 | .929913 |
| 起始残差mode绝对均值 | .498157 | .574491 |
| 末200 critic loss | .015966 | .054182 |

起始pre-tanh std七通道从对照约.018–.079变为候选.351–.508；探索确实增大。但终端误差1.936倍、TD误差2.182倍，残差mode更大；public0仍约.93（0是nominal，越大越减慢WBC）。原dual面对更高熵继续降低raw alpha，实际actor系数被固定下限覆盖。该压力测试揭示探索/价值误差的权衡，不能当任务收益或健康收敛。

独立保存结果review校验预算/源hash/父hash/digest/有限数及初始等式，并生成9面板图，已目视检查。它未重算神经推理/梯度/抽样/物理；这些属于原probe断言。FINAL_SCIENTIFIC_REVIEW记录：不部署0.1、不重跑或延长、不保存或推广辅助权重。正式16保持原设置。

## 接续准备与当前训练

第25轮prepare/launch/setup脚本在B/runtime，已AST及生成监视源码检查。原等待准备3177341已正常完成，三路check-only全部通过；新25保留历史容量入口23及全部状态。六轮19–24汇总3315162也已完成并目视看图，只读完整审查，不重新训练或推理。正式启动与完整24结果见下方。

Direct16原1387783、归档1387835、review1387837继续，B/runs/serl_multistep_batch65536_cycle16_20261026_v1/direct。最新完整15仍648282/5146264，0/30、reward−31.004831，未健康收敛。17的prepare/launch/setup已准备并检查生成源码；等待准备3805535只在原16完整审查完成后做check-only，不自动训练，当前尚未执行恢复预检。必须最新完整16审查后接续。gamma^(k−1)mask由learner再乘一次gamma正确，不改。

上一纯正式16/24固定180样本/208.235546s GPU均值58.6278/73.5111/71.7167/73.2222%，四原learner逐样本在运行、没有辅助；不重采或将本轮probe混合占用冒称纯正式。瞬时/轮次尾部/恢复检查可低于50%，不保证每秒达标。

## 参数24完整结果与正式25

完整24 review/health/FINISHED与图通过。三路各41250新增/全部30完整55秒/无abort，全部旧回放prefix/history/优化器/marker/finite与新reward重建误差0。旧learner2362748/2362749/2362750、归档2362755/审查2362756已退出勿重启。

| 方法 | steps / updates | Task / Strict | reward均值 | 末1000 q_loss | terminal MAE | inbag terminal MAE | Q均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| impedance | 1028250 / 1023251 | 18 / 17 | -2.269965 | 1.604333 | .719666 | .163308 | -4.765216 |
| admittance | 1027250 / 1022251 | 15 / 15 | -6.918517 | 1.311808 | .759298 | .359104 | 10.864180 |
| vmc | 1028250 / 1023251 | 17 / 15 | -6.375837 | .876321 | .651733 | .318103 | 17.875956 |

参数19–24六轮汇总B/runs/parameter_cycles19_24_summary_20261026_v1，保存报告/逐条件算术核验和图完成。导纳新增active_long0200/0300、active_short0600双成功；VMC的active_short0000/0600仍完成任务但丢失Strict。VMC中后段有熵下降和loss尖峰，末段回落但仍高于23，不能只看末均值宣称稳定。阻抗Strict17–18、导纳11–15、VMC15–17；连续周期相关，非独立多seed；24容量分布改变也不能当不变算法的因果比较。

准确完整父B/runs/parameter_capacity_pool30_cycle24_archive_20261026_v1/{method}/cycle_00024.pt：I99902499314225000e2d7ec84c0913fee89fce6563dbad8de8709ce9b11182f7；Adbe8d29d0f54426791f5fa7bd4315382529ff50d4e9cd5ee883a4773863aa906；V48e5488b43fa6ee40291e9e6f54c4c43b9909a7eee186ed232dd58f2e3a5ed19。

20:09 UTC正式25已启动：I3775564/A3775566/V3775568，B/runs/parameter_capacity_pool30_cycle25_20261026_v1/{method}/train。准确最新24全state接续一个周期，原GPU1/2/3/learnerCPU13/26/39、30sampler共享各12CPU/batch65536/UTD1/terminal128/upper projection/I target min+A/Vmean/actor min/LR不变；capacity保持2m及历史23入口，不再扩容。三check-only完整learner/重复恢复/旧replay/下批65536/RNG精确与负守卫通过，0辅助优化。实际启动检查3775661、归档3775663、完整review3775665；无自动26。

新纯正式16/25 profile3524318，B/runs/batch16_parameter25_gpu_profile_20261026_v1，预登记180样本，只等25启动检查通过且四正式GPU PID集合准确后记录。原actor-floor probe和review已退出。结果未出前不声称新窗口达标。

正式25实际启动检查已完成：三路各新增1000，旧I/V1028250、A1027250条所有字段完整保留；2m容量/历史marker/history/优化器超参/30MJB/30sampler/action/clock及新reward0误差通过。原startup3775661已退出，勿重跑。

新25固定前5000条optimizer日志只读审计已完成（first5000_loss_audit/REVIEW.json），步号连续且均有限；该固定前缀末1000 q_loss为I1.517167/A1.275529/V.726304。相较完整24末段略低，仅新轮早期诊断，不代表稳定、任务收益或收敛；全部尖峰保留。

新纯正式16/25窗口已完成：180样本/207.870721s，GPU均值58.0778/72.3389/71.8056/73.2500%，D/I/A/V吞吐10.6172/23.8898/24.4383/24.5345steps/s。逐样本GPU PID集合恰四正式、原learner全部live，无辅助GPU；3524318完成勿重采。仅此固定窗口均值≥50%，不保证每瞬时，不隐去轮次尾部及恢复检查空闲。

收尾科学提交77b28bcb979ba9d3b59c214c6d161098ab4eef9d仅本地；push仍GitHub认证失败，远端main dbb1d76/baseline f6e8f8c重新fetch未变。完整119成员小证据SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_ACTOR_FLOOR_PARAMETER25_20261026_201558/FULL_SMALL_EVIDENCE.tar.gz，逐成员hash核验，1612910字节，SHA256 5948b7a9484e67b826537089941d6b88d08b70d31c9dfc4e1de0c4689cf7e445。HDD小交接/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_ACTOR_FLOOR_PARAMETER25_STATUS_20261026_201558/HANDOFF.md及收据/LATEST入口已核验，大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。FINAL_LIVE_STATUS记录原16/新25与监视进程；Direct16完整review=False，17check-only=False，先核原3805535，不重复准备。Goal active。

## 收尾接续：Direct16完整完成，正式17已启动

本节覆盖本文前面的Direct16在运行/17尚未执行快照。Direct16完整689532/5476264，Task/Strict0/30、reward−30.932129，全部30完整55s、无abort。新增41250单步/32步派生目标精确，旧648282全部raw/derived/history/ready保持，pending0。510终端×10critic MAE.051144/max4.309624，32步TD.048439，Qmean−20.577059，alpha.000670934620；完整review/DIAGNOSIS/FINISHED及图通过，网络/优化器/RNG只读不变，仍未健康收敛。
准确完整16父B/runs/serl_multistep_batch65536_cycle16_archive_20261026_v1/direct/cycle_00016.pt，SHAd2ee183f0ebbafa44dabb8dc318cc2091dfc031145a2192bd9a313f989067c5b。原1387783、1387835、1387837已退出勿重启。
等待准备3805535已正常完成，17check-only完整learner/重复恢复/原replay/下一65536/RNG精确、继承负守卫通过。正式17 learner4158035已启动，B/runs/serl_multistep_batch65536_cycle17_20261026_v1/direct；准确最新完整16全state接续一个周期，GPU0/CPU0/30sampler共享CPU1–12/batch65536/32步/gather+transfer/官方10critic、random2 bootstrap、actor all10mean/noentropy/8:1保持。原历史batch/gather证据链未重标，未部署actor floor或温度候选。启动4158037、归档4158038、完整review4158039；无自动18。
当前参数25 I3775564/A3775566/V3775568继续，无自动26；旧16/25纯正式GPU窗口是此前固定观测，不冒称新17/25窗口。

Direct17实际首1000新增检查通过：690532/5484264，全部旧689532 raw/derived/history/优化器/marker保持，135新mature+865pending精确，30MJB/30sampler/action/clock/reward0误差通过。原4158037 startup已退出；四正式17/25和归档/完整review均live，最新FINAL_LIVE_STATUS已更新。无自动18/26。

最终17/25科学提交50aabc40be6e8d40567e5c4db29a9a33426ce671；更新后的完整小证据包/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_ACTOR_FLOOR_PARAMETER25_20261026_202151/FULL_SMALL_EVIDENCE.tar.gz，142成员逐hash核验、1876872字节、SHA256 670902a81be9467e40a66ad6ff0d8c286533ab3c0fad2043fa070c256041bfcc。最新HDD入口/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_ACTOR_FLOOR_PARAMETER25_STATUS_20261026_202151/HANDOFF.md与收据/LATEST已验证，覆盖前一20:15的16/25交接快照；大产物仍SSD。GitHub认证失败，未发布；Goal active。
