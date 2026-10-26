# 参数21 / Direct15接续与起始探索完整审查（2026-10-26）

原Goal active，未健康收敛。继续用户授权的Direct SERL及三路在线调参RL，尽量缩短周期交接空闲；不使用重复探针或无意义负载填GPU。无子agent。物理/MJB/gate/filter/actuator/dt5e-5/30条件/SPT reward全部冻结；正式网络、优化器、计数器、replay、RNG、history和marker完整保留。

运行根B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；仓库B/repository/SII_compliance，用户HDD仓库路径为链接。大产物与完整小证据主副本在SSD；HDD仅小交接/收据，非arm1或HDD全备份。

## 参数20完整结果与21

| 方法 | steps / updates | Task / Strict（每路30） | reward均值 | 末1000 q_loss | terminal MAE | sampled Q均值 |
|---|---:|---:|---:|---:|---:|---:|
| impedance | 863250 / 858251 | 18 / 17 | -2.275413 | 1.110917 | 0.799493 | -4.886264 |
| admittance | 862250 / 857251 | 12 / 12 | -12.060595 | 1.238914 | 0.842150 | 11.673435 |
| vmc | 863250 / 858251 | 17 / 16 | -4.589517 | 1.221390 | 0.704427 | 22.622589 |

三路各新增41250交互，全部30完整55秒、无abort；全旧replay字段前缀/history/优化器超参/markers保持，新reward从原物理interval journal重建误差0，finite检查通过。完整health不改变网络，图已目视检查。训练q_loss为当前实际投影目标；health中fixed-pair未投影TD不是A/V实际mean目标。CHEQ mask0刻意留出，混合terminal MAE不是纯训练误差。

相对19，阻抗Strict18→17、VMC17→16，两路均在active_short_train_0600任务完成但physical_valid=false；导纳新增short0000/0200成功、丢long0500成功，Strict11→12。全30配对记录在B/runs/parameter19_to20_paired_review_20261026_v1/REVIEW.json，仅原终端记录描述性比对，非独立物理重演/因果证明。图中VMC局部loss/entropy波动与I/V失败保留，不能称健康收敛。

完整review B/runs/parameter_pool30_cycle20_review_20261026_v1，REVIEW/health/DIAGNOSIS/FINISHED均完成。父checkpoint位于parameter_pool30_cycle20_archive_20261026_v1/{method}/cycle_00020.pt：

- impedance：f19cdeb8c8551a6cfcf5fa99526d951d2b8be8061f4e1bc69389939c70b10e1a。
- admittance：7b9b7f945e7eec133024311e9d465f682914be6798127501376ca24b993e1b8c。
- vmc：a5013a75f66ca4b4e80d89cff4315ed3f0643bd532750c6358b48f74e02e3b3b。

正式参数21 PID I/A/V=2558774/2558776/2558777，B/runs/parameter_pool30_cycle21_20261026_v1/{method}/train；GPU1/2/3，learnerCPU13/26/39，30sampler共享CPU14–25/27–38/40–51。batch65536/UTD1/terminal128/upper projection/I target min+A-V mean/actor min/LR I,V3e-4,A3e-5保持。准确20全state接续一个21，历史sampler_pool/shared_sampler_stage保持原18→19迁移来源，不能改写为本轮迁移。三check-only完整state/重复恢复/负守卫通过；实际首各1000条交互全prefix/history/marker/MJB/action/clock/reward误差0与30sampler集合通过。参数恢复必须用pair_class。

归档2558780到parameter_pool30_cycle21_archive_20261026_v1；完整审查2558781到parameter_pool30_cycle21_review_20261026_v1。原20训练/归档/审查已完勿重启。没有自动22。

## Direct14完整结果与15

完整14 steps 607032 / critic updates 4816264，Task/Strict 0/0（30例），reward -31.033155；全部30完整55秒，无abort。新增41250单步reward及32步派生目标精确，保留旧565782全部raw/derived前缀、成熟顺序/history，pending0；网络/优化器/RNG完整恢复与诊断不变。checkpoint SHA d47def4626a3cdb8e783403d2a0152c916593e36ef30675e353e699ff35bf410，B/runs/serl_multistep_batch65536_cycle14_archive_20261026_v1/direct/cycle_00014.pt。完整review/DIAGNOSIS/FINISHED和图已核验，terminal MAE .059095、max2.096615、32步TD .057409、Q均−20.542431，完整数值诊断见证据中DIAGNOSIS.json。Direct截至完整14仍0成功，低loss不是收敛。

正式15 learner2870244，B/runs/serl_multistep_batch65536_cycle15_20261026_v1/direct，GPU0/learnerCPU0/30sampler共享1–12；准确14全state续一个15，官方SERL commit1fa2af7496be042e43d36120a7c8d1b71f1bfb59、10critic/random2/noentropy backup/8critic:1actor、batch65536/32步/canonical48/action7/gather+transfer保持。check-only全state/replay/下批/RNG检查及实际首批1000真实交互检查通过。归档2870381到serl_multistep_batch65536_cycle15_archive_20261026_v1，完整审查2870384到serl_multistep_batch65536_cycle15_review_20261026_v1。原14 learner3955892/归档3955895/审查3955896已完勿重启；没有自动16。

public0=(raw0+1)/2，0为nominal、更大减慢WBC；禁止反转解释。32步bootstrap保存gamma^(k−1)mask，learner再乘gamma得到gamma^k，正确勿改。既有暖1步与半批early回放候选均未支持部署，勿重复、不导入辅助权重。

## 固定128对起始噪声实验

B/runs/serl_cycle13_initial_noise_gate_20261026_v1，从准确完整13冻结全state，单原条件passive_corner_train_0000、外部种子起点2026102616，共128对、256条，每条6动作/.24秒；独立基础高斯噪声与回合固定基础高斯噪声配对，仍每步state-dependent策略。两臂每对首observation/action精确相同。原55秒任务配置/物理/门/滤波/执行器不改，仅记录器截断诊断；不是完整任务评测。

- independent：离开初始approach 0/128，Wilson95%区间 [0.0000%, 2.9137%]，abort 0、机器违规 0。
- episode_constant：离开初始approach 0/128，Wilson95%区间 [0.0000%, 2.9137%]，abort 0、机器违规 0。

全部实际物理子步1228800，不超过1228800登记预算；全动作精确重放误差0.0，原物理/滤波/力矩记录复算通过，全learner/optimizer/RNG和原父SHA不变。REVIEW/INDEPENDENT_REVIEW/FINISHED、256条PREFIX_REVIEW与图已完成，图已目视检查；这是原始记录复算与动作重放，非独立动力学重模拟。无完整回合延长、无按结果挑种子追加、无replay注入/优化/权重保存/示范或nominal mixing。

128个首动作的public0均值.844914/样本SD.010351，dy .993328/.000960、rx−.975489/.002079；初始状态的动作分布很窄、部分残差接近边界。全局平均entropy不能代表这个具体起始状态的覆盖；这也不证明全局策略坍缩或任务失败的因果原因。原图和FINAL_SCIENTIFIC_REVIEW保留七通道完整分布。

这项有限实验未显示constant noise改善初始门通过率，因此不部署。区间只针对该冻结策略/单条件/.24秒前缀，不能推断全30条件或所有未来策略必失败，也不能把prefix exit当task success。原probe2176229及审查2286328/其子进程均已结束，勿重跑。FINAL_SCIENTIFIC_REVIEW.json记录决定。物理原件仍SSD保留。

## GPU、证据与发布

B/runs/batch15_parameter21_gpu_profile_20261026_v1，预登记180样本，等正式15/21启动检查及prefix GPU审查退出后采样，每样本GPU PID集合恰为四正式原learner。窗口207.974339秒，四GPU均值57.6111/73.8056/73.1556/74.1833%，D/I/A/V吞吐10.6455/24.3924/25.0848/25.1329steps/s；全部原learner全样本live。均值只代表此固定窗口，不保证每瞬时或永久≥50%；周期边界等待与尾部低占用不隐去。观察2673023结束不重采。

本轮开始及收尾fetch实际main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d并读取日志，无远端更新。起点641965d，GitHub凭据待恢复，用户此前已被询问不重复索要。新源码3份AST与运行验证通过；完整小证据docs/evidence/rl_parameter21_serl15_prefix_20261026/SOURCES.json和LIVE_STATUS.json记录原路径/hash及当前进度。提交/推送与归档最终状态在下方收尾记录，不把本地提交写成远端发布。

下一步先核对原15/21及完整review；最新完整周期通过后接续，不重复已完成探针。Goal保持active；成功稳定、奖励稳定和数值健康均仍待，不能以稳定失败代替任务学习。

收尾科学提交1dd86077f2bd9b7a3d83da3b51add7dfc8c0fe2f仅本地；push仍HTTPS用户名认证失败。完整89成员小证据SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER21_SERL15_PREFIX_20261026_180832/FULL_SMALL_EVIDENCE.tar.gz，逐成员hash已核验，1510906字节，SHA256 f203453494eff627c112643334d8be39eb384092f63da08f9630dba649b78fce。HDD小交接/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_PARAMETER21_SERL15_PREFIX_STATUS_20261026_180832/HANDOFF.md与收据及LATEST入口已核验；大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。FINAL_LIVE_STATUS记录四原15/21仍在推进及归档/审查live。
