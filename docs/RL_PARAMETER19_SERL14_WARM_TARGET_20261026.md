# 参数共享采样池19、Direct14与暖启动目标对照（2026-10-26）

原 Goal active，尚未健康收敛。最新完整父为参数18和Direct13；两者均完成完整科学审查、健康诊断和目视验图。本轮从这些准确正式父的全部网络、优化器、计数器、回放、RNG与历史继续，没有回退或推广辅助权重。无子agent；物理/MJB/gates/filter/actuators/dt5e-5/30条件/SPT奖励全部冻结。

实际计算和大产物根 B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，仓库 B/repository/SII_compliance，用户HDD仓库路径为链接。SSD是当前主副本，未新核验arm1共享或HDD全量备份。

## 最新完整结果

| 完整周期 | steps / updates | Task / Strict（每路30） | mean reward | 末1000 critic loss | terminal MAE | sampled Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| Impedance18 | 780750 / 775751 | 18 / 18 | −0.578868 | 1.369145 | .918849 | −5.257600 |
| Admittance18 | 779750 / 774751 | 14 / 13 | −10.470471 | 1.165164 | .694976 | +14.146098 |
| VMC18 | 780750 / 775751 | 17 / 17 | −2.820549 | .935907 | .605278 | +25.605375 |
| Direct13 | 565782 / 4486264 critic | 0 / 0 | −31.066473 | 约.018–.020（500更新均值曲线） | .078464 | −20.615009 |

参数三路及Direct各新增41250条交互，全部30完整55秒，无abort；旧回放所有字段前缀、历史、配置与持久marker保留，所有新奖励从冻结interval journal重建误差0。Direct所有新32步目标精确、pending0。诊断不改变完整学习状态，优化器与网络有限；图已目视检查。奖励审查是基于物理interval journal，不声称重新独立仿真全部raw substeps。

参数terminal MAE混合了刻意留出的CHEQ mask0行：I/A/V in-bag .251326/.272468/.256753，held-out 3.717785/2.470758/1.990158；不可将全部held-out误差当作训练发散。导纳Strict15→16→17→18为13→9→12→13，仍不稳定；I/V成功数稳定但存在大量carry失败，Q仍移动。Direct13单步/32步TD MAE .093721/.061994，terminal最大误差13.515680；任务仍零成功，低loss不等于健康任务收敛。

完整父checkpoint及SHA256：

- I：B/runs/parameter_batch65536_cycle18_archive_20261026_v1/impedance/cycle_00018.pt，32c3a2042495dfb9b30beb0ed2bee52679039fcdadef284ac123ba502a043c7c。
- A：同archive/admittance/cycle_00018.pt，2fd40a46fceb6d2e516db2edfa1d36d45405bed4feea2fb8bf602e04c6385a2b。
- V：同archive/vmc/cycle_00018.pt，73ca969942f0583e1973f149f123a876300b7757e4c54d706245cbc6625b6b9d。
- Direct：B/runs/serl_multistep_batch65536_cycle13_archive_20261026_v1/direct/cycle_00013.pt，a03e2d6e859d4299115dad8d59011914db1a40aef984b1bcb595528c72e659b0。

参数完整审查在parameter_batch65536_cycle18_review_20261026_v1。Direct13原review_v1明确等待超时，前轮已登记guard在精确完整13归档后运行相同只读审查，成功版本是serl_multistep_batch65536_cycle13_review_20261026_v2，REVIEW/DIAGNOSIS/FINISHED齐全。保留原超时，不把观察器超时归为训练失败。原18/13 learner及归档/审查已结束，勿重复启动。

## 当前四路正式训练

| 方法 | 周期 | learner PID | GPU | learner CPU | 30sampler共享CPU |
|---|---:|---:|---:|---:|---|
| Direct | 14 | 3955892 | 0 | 0 | 1–12 |
| Impedance | 19 | 3955897 | 1 | 13 | 14–25 |
| Admittance | 19 | 3955898 | 2 | 26 | 27–38 |
| VMC | 19 | 3955899 | 3 | 39 | 40–51 |

Direct run为B/runs/serl_multistep_batch65536_cycle14_20261026_v1/direct，准确完整13全state接续一个不改设置的14：batch65536、官方10critic/random2/noentropy/8critic:1actor、32步、gather+transfer、canonical48/action7不变。新通用driver严格验证连续注册链、原11 batch probe/原12迁移/原10 transfer证据，历史batch_size_stage原样保留，不能伪装成本轮新实验。check-only完整learner/replay/下一65536采样/两batch构造/RNG和负守卫通过；首1000新增/8000critic全旧565782前缀、139mature+861pending、新action/clock/reward0误差、30MJB与真实CPU亲和性通过。

参数run为B/runs/parameter_pool30_cycle19_20261026_v1/{method}/train，准确完整18全state接续一个19，仅改采样调度12→30进程共享原12物理CPU，learner仍独占原核。batch65536/UTD1/terminal128/上界projection/I target min+A/V target mean/actor min/原LR不变。历史17只用于前轮pool状态准备，在线父始终为18，不回退17。三check-only完整state、重复恢复、负守卫通过；真实启动I新增3000/A4000/V4000的全旧前缀、history/markers/MJB/动作参数与clock/reward0误差通过。

参数原startup只读检查错误地将无序CPU集合转成tuple后比较，导纳27–38集合排序不同导致假拒绝；实际所有30worker均在准确登记CPU集合内。保留startup_review.py和原失败日志/快照，新startup_review_v2.py改为frozenset比较，在startup_v2保存重新审查；startup/REVIEW.json首次写入成功结果并记录v2来源。训练从未重启或修改；不是放宽允许CPU集合。

监视器：Direct归档3955895、完整审查3955896；参数归档3955903、完整审查3955904。新审查等待上限7200秒。Direct完整14审查在serl_multistep_batch65536_cycle14_review_20261026_v1，参数19在parameter_pool30_cycle19_review_20261026_v1。没有自动15/20；后续必须先核对原句柄和完整周期审查，再由最新完整父衔接。恢复Direct必须保留clock/multistep/ready/pending，参数必须pair_class保留全部marker。

## 固定纯正式GPU窗口

B/runs/batch14_parameter19_gpu_profile_20261026_v1，原观察4032685完成后勿重复。预登记180次1秒间隔（含查询实际208.835874秒），等待四路启动审查通过，逐样本核对GPU进程集合只属于四个正式learner。GPU0–3均值55.2222/73.0222/72.6556/72.8611%，D/I/A/V吞吐10.1371/24.3349/25.0915/24.9047 transitions/s，四原learner全部样本live。这一固定窗口各卡均值≥50%；不保证每瞬时或末尾始终达标，不据此宣称调度严格因果提速。

交接初四卡确有周期边界空档；已及时执行准备检查并于16:48:38–39 UTC启动四路。新窗口没有辅助GPU计算，后续warm probe共享GPU0的负载单列，不能替代纯正式证据。

## Direct暖启动目标对照

B/runs/serl_cycle13_warm_horizon_probe_20261026_v1；协调3598、只读结果审查59003。登记等待上述纯正式profile结束后启动。准确正式13父与完整review/health绑定，两臂horizon32→1各2000outer（各16000critic+2000actor）、相同65536批量与全部回放row draws，0物理，不保存权重，不推广辅助state。比较在32步已拟合失败回报之后恢复官方单步目标，是否改善价值误差和动作价值梯度；不是重复旧formal9坏critic起点对照。

两臂恢复完整网络/optimizer/RNG，采样ready顺序和初始RNG保持；control第一整批与真实部署sampler及采样RNG逐字段相同，终端1/32批精确相同后才开始。单步mask=1−done，32步保存gamma^(k−1)×terminal_mask，learner内部再乘gamma一次得到gamma^k，不更改这项正确约定。保留历史multistep marker的完整内存state但由显式注册目标构造batch；不生成可误用的checkpoint。

固定4096状态检查单步与32步TD、terminal误差/Q/temperature，固定前1024状态检查七通道mode Q梯度与public0；更大梯度未必是正确方向，不是物理任务改善。public0=0对应nominal，数值越大越减慢WBC。正式14设置不变。最终REVIEW、FINISHED、INDEPENDENT_REVIEW及FINAL_SCIENTIFIC_REVIEW均已完成，图已目视检查，原协调3598/evaluator94562/只读59003已退出勿重跑。独立审查核验receipt一致性/预算/有限性，没有重复数值训练。

| 完整对照末值 | 32步基线 | 单步候选 |
|---|---:|---:|
| terminal MAE | .056348 | .363541 |
| terminal max | 2.517700 | 10.242189 |
| 单步TD MAE | .081214 | .039469 |
| 32步TD MAE | .065922 | .102989 |
| 末100 critic loss | .018510 | .004198 |
| mode Q梯度七通道均绝对值 | .027682 | .005896 |
| mode public0均值 | .435496 | .421097 |

两臂各2000outer、相同131072000个采样行及完整rowdraw摘要相同，共32000critic+4000actor辅助更新；全正式源checkpoint/replay/state保持，0新物理，未保存权重。单步TD/loss更低，但terminal误差更高、动作梯度变弱，不支持本次拟议的细粒度梯度改善；**不部署单步候选**。梯度大小不代表方向正确，基线也尚未学会任务。不同诊断seed的初始TD不需等同先前health固定状态值。禁止重复已完成探针填占用。

## 发布与接续

开工实际查询、fetch/read main dbb1d76ed79177067c48ed49ff9f67f023c704aa 与 baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，无新远端更改。本轮源码与小证据见docs/evidence/rl_parameter19_serl14_20261026；来源大小/hash、最新带时间LIVE_STATUS、纯GPU摘要及观察器失败来源全部保留。GitHub HTTPS认证仍待恢复，前轮已询问用户，不重复索要token或密码；本地提交与远端推送分开报告。

下一步先查看当前14/19与暖目标probe原句柄/终态，完成审查后继续最新正式父。不得以失败稳定或低loss宣布成功收敛。最终冻结比较/ESN/SPT与完整目标仍未完成；Goal保持active。HDD仅可放小交接/收据，完整小证据和大state/raw产物在SSD，不宣称HDD/arm1全备份。
