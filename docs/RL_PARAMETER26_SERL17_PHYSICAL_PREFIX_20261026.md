# 参数26接续准备与Direct熵下限的短物理前缀验证（2026-10-26）

原Goal active，未健康收敛。上一轮完整审查Direct16/参数24并接续17/25、完成actor熵下限离线对照，属于实质进展。本轮重新核验原四learner与归档/review均live且持续增加steps，未重启。无子agent。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；R=B/repository/SII_compliance，HDD原目录为链接。冻结物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward/canonical48/action7，正式网络/优化器/replay/RNG/history保持。不回退、不重置，不加示范或nominal混合，不导入辅助权重。大产物SSD，HDD仅小交接收据，不冒称HDD/arm1全备份。

已按sii-research-sync实际查询/fetch/read main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变。GitHub认证此前已请求恢复，不重复索要；不影响训练。

## 新问题与独立有限预算

已完成完整15两臂2000outer离线压力测试：floor0.1提高起始熵，同时终端/TD误差变大；该实验没有物理轨迹，不能由误差上升推断探索必然有害，也不能只由熵上升推断任务收益。旧probe3020505/reviewer3158348均退出，不重复、延长或恢复旧15实验。

新B/runs/serl_cycle16_actor_floor_physical_prefix_20261026_v1从最新完整16父出发，两个臂各仅200outer/1600critic/200actor/200temperature，batch65536、同完整state、同实际采样行和RNG、原默认精度；共3200critic/400actor/400temperature。两臂更新后在内存冻结策略，分别做三个原条件×8外部配对种子×2.56秒短轨迹，共48条、最多3072动作/2457600物理子步。只回答“是否离开初始approach”，不是完整55秒任务成功或全30泛化。无按结果选种子或自动扩展，不保存/推广辅助权重，不写正式replay。

条件固定passive_corner_train_0000、active_short_train_0000、active_long_train_0000。外部action seed起点2026102623，case_action_seed对条件和seed派生；两臂同条件同seed初始观测精确一致，之后状态可以因不同策略分化。诊断seed2026102624、4096均匀行及510初始/终端；两臂初始网络诊断相同，仅有效actor温度按设计不同。

准确父B/runs/serl_multistep_batch65536_cycle16_archive_20261026_v1/direct/cycle_00016.pt，SHAd2ee183f0ebbafa44dabb8dc318cc2091dfc031145a2192bd9a313f989067c5b。原16完整review/health/FINISHED通过。复用已验证的actor-floor helper，引用完整15实现gate及原离线结果，不把旧gate冒称在新16重新完成。新16完整learner/replay恢复和真实下一65536批/RNG在本实验校验。

原dual温度优化器保留，仅actor使用max(raw_alpha,.1)，不声称约束dual的等价实现。critic保持noentropy backup/10critic/random2-min bootstrap、actor all10mean，32步/8:1保持。最新正式17不部署该候选。

## 执行与审查范围

新probe400736、原结果等待review400737。GPU0共享正式17；协调器CPU52，两个独立MuJoCo解释器固定CPU53/54，所有数值线程1。主程序核验完整冻结SOURCE_HASHES、所有登记源码/父/plan/fixture/MJB hash，沿用既有物理审计适配器，仅以已有probe-seconds接口截断到2.56s，未改环境或gate。

每臂物理评估前后learner/optimizer/RNG digest须不变；在丢弃该臂内存权重前，逐已记录观测重新采样并核验全部public动作完全相同、外部action RNG相同。随后独立review读取原物理日志复核filter/torque/采样数/终止状态，校验两臂完整预算/初始state/draw与RNG/原checkpoint；不重训或重跑物理。因为辅助权重不保存，独立review不能再次重算训练后神经推理，该项是原evaluator断言，不能夸大审查范围。

## 正式接续准备

Direct17原4158035/归档4158038/完整review4158039保持，B/runs/serl_multistep_batch65536_cycle17_20261026_v1/direct；准确16全state，实际1000新增已通过。无自动18。
参数25原I3775564/A3775566/V3775568、归档3775663/review3775665继续，实际1000新增与固定前5000 loss审计此前完成勿重跑。最新完整父24，不能提前拿部分25恢复。
参数26prepare/launch/setup及生成审查源码AST/cycle/capacity已核验；等待准备243874只在原25完整FINISHED/REVIEW后执行恢复check-only，不自动训练。必须2m capacity marker、历史入口23与pair learner；25→26不扩容、不重写历史迁移父。
新纯正式17/26 profile454710，B/runs/batch17_parameter26_gpu_profile_20261026_v1，预登记180样本，等新26 startup和原物理前缀实验FINISHED且GPU PID集合恰四正式后记录。当前辅助共享GPU0的读数不称纯正式；不重复选窗。

完整结果与后续接续待原进程完成后追加。

## 短物理前缀完整结果

原probe400736与review400737已完成退出，勿重启。两臂完整200outer/1600critic预算、同初始learner/replay/采样行与最终训练RNG精确；原完整16 checkpoint/replay保持。各24条×64动作×51200子步，合计48条/3072动作/2457600子步，全部2.56秒、无abort/机器违规。三个条件分别都是原alpha0/8、floor0.1为0/8离开初始approach；24个配对均00。

原evaluator在丢弃内存权重前逐动作重放完全相同，物理评估前后网络/优化器/RNG digest精确。独立物理/filter/torque审查通过，源码/模型/plan/fixture/父hash及完整预算通过；图已目视。独立review没有重算训练后的神经推理或重新仿真，范围按上节如实区分。

| 200更新后诊断 | 原alpha | actor下限0.1 |
|---|---:|---:|
| raw alpha | .0006798274 | .0004990007 |
| 有效actor系数 | .0006798274 | .1000000015 |
| 起始熵 | -22.407059 | 1.472282 |
| 起始pre-tanh std范围 | .0200–.0653 | .6383–.7450 |
| terminal MAE | .053164 | .078361 |
| 32步TD MAE | .072936 | .094357 |
| Q均值 | -20.613331 | -20.861347 |
| initial public0 mode | .927937 | .908898 |
| 初始残差mode绝对均值 | .470285 | .468046 |

实际短轨迹上的平均public0，三个条件原alpha .503480/.531502/.558036，对应candidate .484453/.485306/.508199；实际残差动作绝对均值原 .460452/.442967/.450865，对应candidate .528469/.530841/.529946。注意这些是各策略自身演化状态上的随机动作，不等于固定初始状态的mode。public0=0 nominal、越大越减慢WBC，不反写方向。

FINAL_SCIENTIFIC_REVIEW结论：探索确实增大，但本有限试验未观察到起始阶段收益；不部署floor0.1、不增加这些种子/时长、不保存或推广辅助权重、轨迹不进入正式replay。每条件只有8seed且三条件初始几何相关，不能由0退出推断真实概率为零或所有30条件/完整55秒必然失败。正式17原设置继续。

## 完整参数25与正式26启动

三路25完整review/health/FINISHED及图已通过。各41250新增、全部30完整55秒无abort，全部旧I/V1028250/A1027250回放行、历史/优化器/markers保持，新增reward重建误差0，网络/优化器有限。原25 I3775564/A3775566/V3775568、归档3775663/review3775665与准备243874已退出勿重启。

| 方法 | steps / updates | Task / Strict | reward均值 | 末1000 q_loss | terminal MAE | inbag terminal MAE | Q均值 |
|---|---:|---:|---:|---:|---:|---:|---:|
| impedance | 1069500 / 1064501 | 18 / 17 | -2.318779 | 1.856296 | .838634 | .291147 | -4.916550 |
| admittance | 1068500 / 1063501 | 16 / 16 | -5.344773 | 1.199879 | .625643 | .221800 | 11.099812 |
| vmc | 1069500 / 1064501 | 17 / 16 | -4.615704 | 1.629220 | .692525 | .382382 | 18.714698 |

导纳严格成功15→16、reward和loss改善；VMC严格成功15→16但末loss.876→1.629，inbag误差.318→.382、Q均值17.876→18.715，不能由成功数单独判稳定；阻抗末loss1.604→1.856也仍波动。全部失败保留，未健康收敛。
准确父B/runs/parameter_capacity_pool30_cycle25_archive_20261026_v1/{method}/cycle_00025.pt，I30442e0f9eeaf539c5aca2e39b540fddfa2ba55560e7be4507b291ae5a2daf9f；A0b67e111ef772e8b7f60dbefd29f1f10dffe30066e3b0f829e612ba8430f5650；V7d29d24ea5d757674a89ad82936df5550b9e2c6f63900c2671666995bd906ea4。

20:42 UTC正式26 I904989/A904991/V904993，B/runs/parameter_capacity_pool30_cycle26_20261026_v1/{method}/train，准确最新完整25全state接续一个周期。三check-only已通过，原learner/重复恢复/replay/下一65536/RNG精确和继承负守卫保持。原GPU1/2/3/CPU组各30sampler共享12CPU/batch65536/UTD1/terminal128/upperprojection/Imin+A-Vmean/actor min/LR保持；2m容量和历史入口23保持，无重新迁移。实际startup905056、归档905057、完整review905060；无自动27。
Direct17原4158035及归档4158038/review4158039继续，最新完整父16，无自动18。所有辅助物理实验已结束，454710纯正式17/26观察等待新26 startup后开始。

正式26实际各1000新增startup通过：I/V1070500、A1069500，旧I/V1069500、A1068500所有回放字段/history/优化器/2m marker/30MJB/30sampler/action/clock及新reward0误差通过。原905056已退出，勿重跑；四正式17/26及归档/完整review继续。

纯正式17/26窗口已完成：180样本/208.441719s，四GPU均值56.5278/72.6278/71.0000/71.6111%，D/I/A/V吞吐10.4969/23.9395/24.4625/24.4769steps/s。逐样本GPU PID集合恰四正式且原learner全live、无辅助GPU；454710已退出勿重采，仅此固定窗口均值≥50%，不保证每瞬时，不隐去回合尾部与检查恢复等待。

## 下一步判据核对

本轮复读原RL_SPT_TRAINING_HANDOFF_20261025.md第5节与关机交接：要求同身份配对回报改善、末3轮均值变化≤5%及斜率/不确定区间、无新增数值/温度异常，并有冻结策略验证；完全无改善的平坦只能叫停滞。任务成功率与回报稳定必须分开，不要求baseline任务成功才算回报稳定。原32条件建议应按当前正式30条件登记落实，不能偷偷改分母或把建议写成已执行。后续优先量化Direct完整同协议周期的配对改善和稳定性，而不是仅凭0/30无限否决；参数扩容24后应等待至少3个完整同容量轮次，26尚未完整，I/V loss上升尚待诊断。原指定ESN仍未获得，前次已询问，不重复追问或拿旧ESN替代。
