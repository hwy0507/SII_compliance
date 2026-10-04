# 更新日志

## 2026-10-04 — RL物理奖励输入独立复算与短失败保留

- 05:41UTC实时查询/fetch并读main19a11c21f6aef4be2801a1e3c192146182a23bad、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS，工作区干净；前轮属实质进展，本轮实际PID/服务继续存活。
  main19a完整3284文件核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/19a11c21f6aef4be2801a1e3c192146182a23bad/，tar SHA1f170330481b8121489168602eeefc2e850742edac17cc00fe5ac2c8a30ca431。
- 新research72_reward_intervals从物理/actor时间戳独立划区间，重算dt/error/实际力矩积分与峰值并核对公共过滤action；五家族六完整训练段的62回合82004区间/65603200物理子步通过，4短失败保留。
  时长、峰力矩/误差、动作差值0，积分最大8.33e-17；六项边界/篡改回归通过。Spark1线程/1GiB/CPUQuota100%，约33s完成，无新物理/actor/拟合。
  只补物理日志归约，不独立重算任务potential/初始potential、终止观测或接触真实性，不把这些训练记录当最终策略测试。
- direct_metric301自然完成27336步/22回合/44674更新，5500父前缀及新增21836真实转移核验；新18回合含39.76/1.04/7.64s三个穿透超限短失败。
  新21818奖励精确核验、18首奖励排除；与原五段合计81942已核验奖励/62未知首项，与82004物理区间对应。不补写步数、不丢失败、不称已收敛。
- 两源reward_intervals_source_v1核验，tar SHAfc4fdbb7145ba401f15a7aa479c3641160904d48b289c5d57b503e0190039f37；结果reward_intervals_audit_v1三文件276836字节独立核验，清单SHAddf8c0bea89c62cf4455e01966687002ad7493b178aba07beebe26307477a140。
  共同根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，Git保留物理区间/新奖励/清单同字节；更新原RL奖励报告、状态、进度、周报。
  稳定开发与RL队列继续，未追加搜索/更改环境或gate；全部共同训练边界和38×24最终比较未完成，最终条件封存、目标active。

## 2026-10-04 — 最终RL共同边界的完整账本检查

- 05:26UTC重新实时查询/fetch并读main2000768、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS；承接前轮12文件审计，正常提交/push为9ccabddd8095166c4b535d6b108631327e5af33e。
  完整3284文件已逐内容/大小/模式核验到arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9ccabddd8095166c4b535d6b108631327e5af33e/，tar SHA4afd43694094e5acbfb4ca15e4b3eb230bdb1d3a8049f46a8123abfa31ddcce9。
- 最终38模型汇总原5项回归补至8项：真实final_policy/selected_boundary/main串联15个合成RL模型，包含49336与49500实际步数差异，必须选择登记边界而非后续收尾权重；1375额外步保留计成本。
  缺一个登记阶段不回退，监护关闭证据篡改拒绝，真实新teacher完成与旧相同teacher跳过路径均覆盖。本机8项通过；仅checkpoint字节检查在合成测试中mock，实际13存档另经真实verify_candidates核验。
  无实际最终选择/冻结/开封，无新物理/训练；不修改运行中源码、队列或研究选择规则。
- 只读加载核查：当时13个已完成RL存档964文件/1,836,571,406字节，两遍真实完整校验约1.988/0.914s；550个runtime文件约.030/.030s。
  这是当前存档在现有缓存状态的粗计时，不代表完整15个最终checkpoint冷加载、JAX推理初始化或912回合完成耗时，原预算预测不据此缩减。
- 05:35公开快照：RL151254实际交互/171034更新，旧context26/168、增强网络18/168、新refit3/144；全部120拟合已完成，原作业继续。
  服务器本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，EXPOSURE_SNAPSHOT_20261004_0535.json SHA2809fa0829b508af25ede9c933cbca54b9a804441589cca64ed59c786ebe83a9。
  新refit仍只完成三个开发样本，不做胜负推断；最终24封存，完整912比较、独立最终审计和投稿证据未完成，目标active。

## 2026-10-04 — RL完整续训闭合与五家族奖励缓存核验

- 05:05UTC实时查询/fetch并读main2000768fbd0b4dd2edef709854e6b444b98335a0、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS；工作区原干净，只有root agent。
  main2000768完整3276文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/2000768fbd0b4dd2edef709854e6b444b98335a0/，tar SHA700aa4acb9d6fad89a8464d59e1719718e83daca19fda1427190ca71675ac5fe。
- 导纳301/VMC301自然完成27500步/20回合/45002更新；复用冻结审计工具核对75/74存档文件、44源、原轨迹引用，并验证5500父前缀和新增22000真实转移。
  与旧16500中途快照区分；未逐梯度重算或把训练结束当最终策略成功，15模型49500共同边界继续等待。
- 新research72_reward_replay_audit按原协议SHA加载冻结rewards.py，从保存区间/实际过滤action核验回放奖励，四项边界/篡改回归通过。
  五家族代表段60124奖励逐值一致，包括office_task303原41.72s短失败；其终止task−20、负成本补偿−.2224180869保留。
  因初始potential未保存，44个首奖励明确未核验；未从子步独立重算区间、未重算梯度/终止观测，0物理/actor/学习，不称全15模型审计。
- reward_replay_source_v1两源核验，tar SHA4d304639183d6c490899961a8393ca4e264bd738a0d77ec137ec9c5ae6a6625e。
  rl_completed_continuation_audit_v1五完成结果315828字节逐hash/大小核验，清单SHA33014cf06562a26ac02b4528e9ab6ac45bae1b857b386e70a70f79d78aa3c397；存档/奖励/清单Git同字节，长前缀原件服务器保留。
  共同根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；详见新RESEARCH72_RL_REWARD_AND_CONTINUATION，同步状态/进度/周报。
- 05:19真实成本RL140438交互/154400更新、context25/168、增强网络17/168、新refit2/144；三RL及评估实际PID存活，三memory.events的oom/oom_kill均0。
  新预测保留完整912和2h收尾后理想余量3.632–5.857h，非完成保证；BUDGET_FORECAST_20261004_0520.json SHA7c4709023889cf34387cd711025f2137bc6d492ce65167fe22025b8a123ad795，Git原字节。
  本轮未加训练/物理、未重启稳定队列、未改环境/奖励/gate；最终24仍封存，全部正式比较与论文结论未完成，目标active。

## 2026-10-04 — 新读出实际推理成本和更强RNN对照

- 承接main a09926105598ef04b8f77982fa119d67556088fb，baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；本轮已实时核对分支及AGENTS。
  最新main3275文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a09926105598ef04b8f77982fa119d67556088fb/，tar SHA70a971f64d6d78415cd4bb989657089725ee4fabd6eca648c72738b445f7b563。
- 复用既有inference_profile入口，本机单线程3GiB测量新18模型/同公开1375帧训练序列，固定打乱顺序、每模型3遍，共74250计时；warm导出重放误差0，0物理/拟合/封存读取。
  ESN3780可训练系数，actor中位32.205–32.800μs；普通MLP5504系数/7.847–7.910μs，RNN21888系数/9.885–10.104μs。不称ESN推理更快，不以actor延迟证明端到端实时。
  新matched RNN三个seed选择更新4000/3600/3600、验证MSE均优于ESN父模型；其三seed均值.000230356 vs ESN.000232886。保留更强对照，离线代理不是闭环成功。
- 六文件源码/原始计时/PROFILE已完整核验共享本轮根refit_inference_archive_v1，tar SHAf6f6a71315f7a8146ac0ed1f0b50c78ded5cf451fdad2fab9fd5b371a7277939；PROFILE SHA674c80045d0e22e1962430d8f1e4bfd3deba47780621ea791cad1826adb8ad8b，Git同字节。
  本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；更新READOUT_REFIT_RESULTS、方法定位、联合进度和周报。
- 同时检查Spark空间余2.7TiB，运行目录93GiB；三RL服务正常、swap0，原队列不重启。开发144及旧增强组/RL运行中，最终24封存，目标active。

## 2026-10-04 — 最终选择的真实路径兼容修复与新读出首回合

- 承接已推送main9e7fa92dedd121a79e838a49fa48cd1c27921444，baseline仍ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；本轮前已实时核对两分支和AGENTS，无其他工作区改动。
  main9e完整3274文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9e7fa92dedd121a79e838a49fa48cd1c27921444/，tar SHA49f18477cffb2f15561761f9d96645a90d6dd09a05b9395e8eb09192fd8f80a2。
- 在后续最终学习选择器发现同类JSON路径字符串/hash接口错误，规范化为Path。新增完整72候选合成账本测试，经真实load_phase/main验证18模型输出，全部失败仍入选、teacher证据篡改拒绝、refit缺1回合拒绝。
  本机3项通过、原38模型汇总5项通过；Spark同3项通过，零实际选模/物理/拟合/封存读取。不修改运行中冻结源，真实最终选模必须用本修复后的入口。
  本轮根selection_guard_source_v1两文件内容/大小/模式全核验，tar SHAff30db5889c35883933aef23daf173f181ad957c3ff9ac5c2040ae8547771411。
- 04:51:49UTC新refit首条development000/seed301完整55s结束，worker审计task/strict通过，RMSE30.699mm、峰力矩49.981Nm、峰速度.349058m/s，外穿透.143599mm。
  请求/公共filter/储备池重放误差0；raw trace SHA5c43b9cd6b48c015ff5b9e314d001d23b8b0b5438de23e7139c13766f66ef26c。
  仅单条公共开发、整阶段独立审计未完成，不据它改候选、gate或声称泛化；固定144队列继续。
- 04:52UTC旧context24/168、增强网络15/168、新refit1/144；三RL队列持真实租约、共同边界监护watching。24最终仍封存，目标active。
  共同产物根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/；进度/周报同步，无新搜索或重启。

## 2026-10-04 — 共享新teacher重训完成，纯ESN交互读出进入144条开发比较

- 04:28UTC实时核对/fetch并读main8c1633e5b643b68c26008047c1fb5f4a1cf25010、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS，承接已登记研究的未提交源码/证据。
  main8c完整3259源文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/8c1633e5b643b68c26008047c1fb5f4a1cf25010/，tar SHA5473d1fcee18f0607afce2c56ec94558441a096076b06a48678aec1c689b4ede。
- teacher40/40完整采集完成：task40、strict25；新20训练＋5验证34,375帧，真实请求/过滤重放已核验。验证8配对审计task7→8、strict6→5，合格柱接触0/5，明确不是全面改善。
  validation审计20文件1,056,265字节全核验，清单SHAaedb6501a93be5825b97b8d0bce4fe0e228753f874d05bf4011563a76ada6382，SUMMARY Git同字节。
- 修订02于04:20:58拟合前登记，保留原条件/gate/最终38×24，核验三RL真实租约与容量。纯128ESN新增固定本体×记忆读出，只训练3780线性系数。
  全六模仿家族共享新数据、固定学习率；本机1线程3GiB于04:22–04:26完成18拟合，6固定模型72候选精确重建，18actor共24,750帧隔离/导出重放误差0。
  新数据＋结构不能当单因素机制证明；累计ESN60、无记忆36候选/seed，ordinary+matched MLP/RNN各16，不称等计算。
- 763文件核验共享本轮根local_context_readout_refit_archive_v1，tar SHA07d887b4c98426a3a97441e0d1568a8020b2581b494e9b9268e2c2a9b987034b。
  登记JSON路径字符串错误在写出spec前修复，原拟合未重跑；18模型×8开发全部登记，单队列PID2490149已运行，仍共享四仿真槽。
  修订/登记/储备池/输入审计等Git原字节证据，实际源/seed/hash/限制详见RESEARCH72_READOUT_REFIT_RESULTS，更新状态/进度/周报/英文方法。
- RL导纳301/VMC301各16,500步真实存档保留5500回放前缀精确一致，新增11000转移关联实际8回合；未重算梯度/奖励/终止帧下一观测，不称最终任务审计。
  prefix源两文件核验，tar SHAfd4cf8c6e74e65015a6a28884e1cd7554b464a3ae8b8478ac12a54261763f988；两实际结果Git同字节。
  q1自然得槽在一次性让槽工具之前，真实events=[]，未向研究进程发暂停/恢复信号；工具仅自身一次性测试子进程的信号检查通过，不重复调用。
- 成本工具从登记起计144条、未来optional=0避免重计；新refit_dispatch_source_v1三文件核验，tar SHAccbf38b89d0f15ba9410adeb8fff760e122fa7dcfd563e1b1153bbc1701f91f0。
  04:36:18快照120拟合完成、RL106418交互/102858更新、旧context23/168、增强网络14/168、新refit0/144；含912最终和2h收尾理想余量3.48–5.74h，非完成保证。
  本轮6登记＋8容量＋2曝光＋3回放回归通过；首审计漏systemd工作目录在模型加载前失败，补全后独立审计通过。未改环境/输入/执行器/门槛。
- 上述本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  运行中稳定作业保留，24最终条件仍封存；开发/全RL共同边界/最终冻结/912评估和论文证据仍未完成，目标active。

## 2026-10-04 — 新旧teacher训练示范的配对质量审计

- 03:40UTC实时核对/fetch并读取main6c0cbb6e2edd8fa75a0b1762166ce4bb51f1584f、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志与AGENTS，工作区干净。
  main6c0cbb6完整3256文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/6c0cbb6e2edd8fa75a0b1762166ce4bb51f1584f/，tar SHAd1ddb7352859f63204e34882899ac7be69d7efee458aecf007856c26ecce581d。
- 新research72_teacher_data_comparison只读审计同32训练身份初始/选定teacher共64完整回合、70,400,000已保存子步；使用原v4指标，0物理/拟合/封存读取。
  逐协议/config/MJB/trace/chain/native/telemetry及原三指标核验通过；Spark单线程3GiB服务正常结束。新teacher任务29→32、strict18→20，8改善6退化；柱子合格示范仍只有2条。
  推杆P95力降低，但桌角接触时长4.112→8.583s、力模积分8.169→22.369Ns；不能称全面柔顺改善。人手两身份位移变化单列，负载指标保持，不以均值相同冒充所有字段相同。
- 本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  teacher_data_audit_source_v1单源文件核验，tar SHA83dd9acfc784111c72218cac63b7b179c3993a06e6373d8bfd9f29f005a9bd19；teacher_data_train_comparison_v1共68文件/1,677,577字节全核验，清单SHA3105de87e10c5254b4d2f0e020c095401f36e8d374675e5ed58cd8aaa8f31287。
  SUMMARY SHAd59f26e76abc0e0c69b412edc2130cc2dd270546eea4380671440492ccd41cc3，Git同字节；新增TEACHER_DATA_QUALITY报告，同步状态/联合进度/周报。
- 03:51采集37/40、context18/168、增强网络10/168，原RL/预算监护运行中。等待8验证完整导出；未新拟合/登记修订02/解封24最终条件，目标active。

## 2026-10-04 — 共同边界后的保守成本复算

- 承接已发布7d9fcd8ca3b17bbd0580b0b63e7c7f58c917c3a7；其3255源码文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7d9fcd8ca3b17bbd0580b0b63e7c7f58c917c3a7/，tar SHA dbde88e74d2cd1f1835bc7808465f938a7f411dd7e558b13fdc1f13d2c6ae226。
  本轮main/baseline实时核对如上一条；baseline仍ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，无并行文件修改。
- 容量工具核验登记修订后，计入所有15模型49,500＋最大2750后续收尾步，原80k协议/优化器不改；新增算术回归共7通过。
  03:27实际快照下剩余开发理想21.91–22.94h，最终912物理22.82–23.94h，加2h收尾预计余量7.18–9.32h；额外等待/冷加载仍未计，未登记追加ESN拟合。
- 两源文件已核验共享本轮根budget_forecast_source_v5，tar SHA6e9833187cc81b4601a181bceb0ddce83bb512324dfe129a9cf9b801e06f6940。
  BUDGET_FORECAST_20261004_0327.json SHA8c962f7e502653c3bde882ba6f969b024d3d387563a1bd2f13bf2c351da5b44d，Git同字节；共同根为arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  只做只读成本算术，0物理/拟合；更新状态、容量、联合进度、周报，原训练继续、最终条件封存，目标active。

## 2026-10-04 — 全部RL共同最终边界前瞻登记

- 03:12UTC左右重新实时查询/fetch并读取main271a937444de7577d3432d627d2eeba1cb7efee3、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志/AGENTS，承接三个未提交源文件。
  main271a937的3249文件已核验归档arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/271a937444de7577d3432d627d2eeba1cb7efee3/，tar SHA28cdd9b55ff2c97683593ecbc53872f523f77137b84e7d7e67e11a8889d95bf9。
- 03:24:43UTC在全部模型均未进入49,500阶段时登记统一最终边界：5RL家族×3seed均选该自然完成checkpoint，实际48,126–49,500步；原80k优化器/奖励/runtime保持。
  依据已归档串行队列容量保护完整912回合，不使用奖励或任务成败。不可变队列后续两阶段精确SIGUSR1温和结束，最多2750额外步/模型全部保留/计成本，权重不参与选择。
- 新research72_rl_final_boundary以PID/start ticks/argv/父进程/UID/handler/pidfd核对目标；finalize_selection要求全部15边界与关闭hash证据，无缺失回退。
  本机边界6通过1跳过（缺pidfd），Spark7全通过含真实一次性测试子进程；原finalizer5通过。dry-run三个队列零信号，持续监护服务PID2471052已运行，尚未发训练信号，不创建定时任务。
- 本轮根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  rl_final_boundary_source_v1两文件完整核验，源tar SHAe5903f2beb8dc3460627d391fab404cf5d91c94eeb6292be83497f4ea12cc9a8。
  AMENDMENT SHAe2b74294410aa3a97aa9ded6623f8a621424048101b3b5c7c32fe3159a4a7779；登记/DRY_RUN同字节Git证据，详见RESEARCH72_RL_FINAL_BOUNDARY。
- 更新状态、容量、分析方案、英文方法草稿、联合进度、周报。03:27快照teacher32/40（32训练task全过、20strict）、context16/168、增强网络8/168，RL72418交互/44856更新。
  新teacher尚未用于学生拟合，未登记修订02、未解封最终24条件；ESN泛化/全baseline最终比较/投稿证据仍未完成。稳定作业继续，目标active。

## 2026-10-04 — 真实RL续训首动作验证与队列容量修正

- 02:30UTC实时查询/fetch并读main1066bcad0142c706cd93d2c84382e0c18500885c、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS约定，原工作区干净。
  main1066的3244文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/1066bcad0142c706cd93d2c84382e0c18500885c/，tar SHA c50e57a1f5ac3fbef09cd0284959461be716eaef3783d4be8d465dc4a1a520e8。
- 新research72_rl_resume_audit在原生Spark分别独立加载VMC301/导纳301父checkpoint，以真实续训首观测重放随机动作，精确一致；
  每审计仅1次actor调用、0梯度/物理，保存运行中child execution原字节快照hash、不修改原件。六回归通过，非全段优化器/最终策略核验。
  rl_resume_action_audit_v1三源文件已核验；两结果SHA分别ab492d2cae78ea7721a0b39913de9ad99da4752470a05af17ed8235d06aa9ef7、
  4add155e9f0c35426a247e17499bbe5c692608a3371ed2a099b0cbb188387bda，Git同字节。源tar SHA ff9a4cdc27de1b18d2e225e320d21690977421aecd5dd42a20b9e43167154039。
- 新增VMC303/任务奖励303首段存档核验通过，后者train031因穿透2.560352mm在carry中止，真实5168步/338更新保留，未补成5500。
  rl_saved_state_audit_v3/AUDIT.json SHA a094a55f2627298175f4f0609ecd41aafb23e1595992273c443874427e0d5828，Git同字节；十首段不是全部15模型训练完成。
- 容量预测新增实际串行RL最长队列，6回归通过。02:43实际快照预测全80k开发31.28–32.70h、最终22.82–23.94h，含2h收尾余量+0.67至−1.88h且未计等待；
  不再只用总量除以四。budget_forecast_archive_v4四文件核验，tar SHA bd92cfac326de98edb7abafeae1c3cc4221792bb2d434601c5e893d8b8eb723e，详见CAPACITY_FORECAST。
- 上述产物根均arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  更新状态/联合进度/周报：teacher26/40、context13/168、增强网络4/168，q0/q2真实续训、q1等租约。未改冻结环境/gate、未发停止信号/改预算，24最终封存。
  下一步须据真实稳态明确共同预算边界以保护完整比较；不因某方法失败删回合，目标active。

## 2026-10-04 — 英文方法正文草稿与首任务奖励RL真实存档

- 02:17UTC实时查询/fetch并读main f6d22ffffa74e33e1e28dc8e49695cd22c3a7262、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS，工作区原干净。
  前者3242文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f6d22ffffa74e33e1e28dc8e49695cd22c3a7262/，
  tar SHA6187c1f6b96da35d5f42549a7351d88d6b929468b5c87c402b54cae312a1be36。
- 新RESEARCH72_MANUSCRIPT_METHODS英文稿按实际actor/trainer/evaluator/selection与统计方案逐项核对：给出储备池公式、
  精确task/strict口径、对照差异、912回合计划和推断边界。未选最终变体、未填最终结果或虚构新颖性/ESN优势，不改环境或gate。
  正文SHA b7d2feabb5c2477ce56943f0fd1c83bdabc9f50cec06cdc2576c3313ddd2b5c3；共享methods_draft_v1/docs/，单文件内容/大小/模式核验，
  tar SHA bf66c8495fda765fceeaab3afee10e84c710bb1dd4977375fd6acde1f8d1c41e。
- 新增直接任务奖励302/阻抗303两个首段存档独立复核（75/74文件、7/5维）：各5500步/4回合/1002更新，完整hash/回放/计数/边界/RNG/源核验通过。
  复用v1已归档源码，零动作/更新/物理/封存读取；rl_saved_state_audit_v2/AUDIT.json SHA a23428d103a1f393f98c269f837bffa786a99355185d11b28f7f9406a9b6f53f，
  Git同字节证据，详见RL_MEMORY_PREFLIGHT；不把存档核验当实际续训或任务成功。
- 上述本轮产物根为arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  02:22快照teacher21/40、context10/168、增强网络2/168；RL八首段完成/累计46875交互，q1等租约、OOM0。
  四实际仿真原作业保留，无新搜索/派发/预算修改。更新状态/联合进度/周报；最终公平矩阵、实际续训和最终论文证据仍未完成，目标active。

## 2026-10-04 — 首5D真实RL存档与名义控制完整开发结果

- 01:49UTC实时查询/fetch并读main66c72b90fdbcd7355b2fad2029f482ef24a555b4、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志及AGENTS。
  main66完整3238文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/66c72b90fdbcd7355b2fad2029f482ef24a555b4/，
  tar SHAded8abdba4cea715edc88cd627aa0750e90a34aab932faf3c73a9de774bea152。
- 六模型各5500步/4回合/1002更新已保存，包括5D阻抗302。新增独立零JAX/动作/物理审计核对完整存档、回放维度、
  计数/episode边界/RNG/条件顺序/44源与prior及24条原轨迹hash，全部通过；不是实际续训或最终策略评估。
  本轮服务器根rl_saved_state_audit_v1源/结果已核验，结果SHAbb3120147ee90a4c2e90447b373ad44818a39dcc84015380e4d495514a3b4d35，
  源包SHA717b32450b5902a52426740d1871ccb6302277aee4c1bbef422eecbbdd227261；Git同字节审计及首5D原manifest，详见RL_MEMORY_PREFLIGHT。
- 名义规划＋WBC开发8/8完整与独立审计完成：task/strict0/8，均carry；RMSE26.697mm、峰力矩均值37.532Nm、峰速度均值.36838m/s。
  SUMMARY SHA6c2c6ec9784bcdbedcf0a742e607a46f874873279eef6ed2fce8142806062718，Git同字节；原件additional_development_v1/nominal_development/。
  低误差不抵消任务停滞，非最终留出结果；见CONTROLLER_CONFIRMATION新增名义参考，不混旧64确认分母。
- 实际01:54成本快照：既有剩余开发理想31.569–33.038h，最终22.824–23.942h；不新增回合也只有总余量+1.199至−1.387h（含2h收尾）。
  budget_forecast_archive_v3全4文件核验，tar SHA5a48ce61fa3d6f0c725380dc6ead5c86f0ced0b2483588b3a9f5b3f24f9d909f。
  不绕过开发闭环替换新teacher重训权重，不登记修订02、不减最终baseline；原稳定作业与封存条件保持。
- 上述本轮根为arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/。
  更新状态/联合进度/周报，真实续训、更强学习组、teacher40与最终比较未完成；保持研究目标active。

## 2026-10-04 — 实际物理装置核验与论文结论范围

- 01:30UTC实时查询/fetch并读main58fcf97d6e90d08f6feba94b7740365609815f20、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志和AGENTS，工作区干净。
  main58完整3235文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/58fcf97d6e90d08f6feba94b7740365609815f20/，
  tar SHA9281c6b48f7c11579835f1b4b7724b9b4e6b2ddfb3b22a91c8b29c92df81b163。
- 新零积分只读审计核对公开train000精确MJB、七个实际源码hash、1375帧旧mocap位置：球1kg/r60mm、物块80g自由体，
  无payload weld；实际人/杆为有限质量驱动机构，但模型仍有场外旧mocap。保留审计早期粗假设被拒绝的记录，未修改模型来通过。
  解释14/80N驱动力不等于接触力上限、2s前球被固定、柱为特定低摩擦小几何；不冒充人体安全、广泛环境或硬件验证。
- 本机1线程/3GiB成功审计.219s；全部3文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/apparatus_audit_v1/，
  结果SHAcb30b726a8acc310d2607bd38a44785730aae02e6b5c527c9f01d23f10e38648、tar SHAd5c178a5316e26436f16f5672569df115ada885a19db4b1a9e41fe4eda568321；
  与服务器原execution/model/trace再次关联，Git同字节小证据。详见RESEARCH72_APPARATUS_SCOPE，更新方法定位/状态/联合进度/周报。
- 01:44UTC新teacher14/40、名义7/8、context7/168；四RL模型首段各5500/1002，后续两模型4750步；第三队列等租约。
  两queue memory.max事件447/685、OOM0，稳定作业不重启。无新候选、环境/gate/预算修改或封存读取；最终公平矩阵仍未完成。

## 2026-10-04 — 纯ESN固定矩阵独立重建与实际归档关联

- 01:10UTC实时查询/fetch并读取main5b50c0cd87fab8cb711979ef1d15069ecf2fd762、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6日志，工作区干净。
  main5b50完整3233文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/5b50c0cd87fab8cb711979ef1d15069ecf2fd762/，
  tar SHAa6f923d6d9b9a864c02470c6aad5b1018db0438a26ba1dc9e977a171457d5409。
- 新零训练/零推理/零物理审计从seed独立重建12个ESN＋6个无记忆拟合的全部216保留候选固定矩阵、时间尺度、gate及字段合同，
  全部精确一致；每拟合两项内存负对照拒绝修改循环矩阵/额外隐藏层。原权重不改，MLP/RNN不纳入固定矩阵断言。
  本机1线程/3GiB完成1.183s，再与Spark模型/metadata/候选逐hash关联通过；不证明稳定、泛化或ESN优势。
- 全2文件（实际源/结果）已核验到arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/fixed_reservoir_audit_v1/，
  tar SHA2b6ea4ba8a0db3bdde62b10dffea7f2ebb0257b46bcf2288b12d525fe11717bd；结果SHAb01441975949630d46b0b579b36e25bf40fdc52fd043390810c6155af3d4fdcc。
  Git同字节结果，完整方法/源码hash见RESEARCH72_INPUT_AND_MEDIA_AUDIT，更新方法定位/状态/联合进度/周报。
- RL第二模型梯度开始后两queue峰触及3GiB、max事件169/148，OOM仍0，anon约1.83/1.87GB、file约1.25/1.26GB；
  保留页缓存回收的真实观察，不沿用旧max0断言，不增加限制或重启作业。实际新ESN开发和teacher采集继续，最终24未开封。

## 2026-10-04 — 首批真实RL存档通过与最终评估容量复核

- 延续实时核验main759ba7b1d847b660af201ddb51e528ebf9b465b9、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  main759完整3231文件已核验归档arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/759ba7b1d847b660af201ddb51e528ebf9b465b9/，
  tar SHAc2d498bb33101a0bef38f966f80061135f27ef8897e7ab2bb938fdd475971b60。
- 00:56UTC导纳301/VMC301各5500真实交互、4完整回合、1002梯度更新并保存。独立零积分/零更新检查每个75存档文件、
  原始manifest、回放形状/终止计数、runner/agent/奖励计数、RNG可加载、源/prior不变，通过；未将其当真实续训或最终成功。
  两queue累计峰2.67/2.66GiB，max/oom事件0；已轮转下一模型，第三RL等租约，不重启稳定作业。
  Git含两个同字节初始manifest，权重/回放位于本轮根rl_office_adaptation_v2，hash/精确路径见RESEARCH72_RL_MEMORY_PREFLIGHT。
- 00:44UTC新的公开成本快照：既有剩余开发理想32.697–34.220h，最终912回合理想22.824–23.942h；
  再追加144开发会相对总窗口欠2.370–5.186h（含2h收尾假设）。暂不登记修订02，保持全部baseline和最终分母；真实并行/启动成本仍须核对。
  本机零物理预测与源/测试全4文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/budget_forecast_archive_v2/，
  tar SHA8412d5cc484555c83d09365e5bb48bf5f8cdb32d2a21f7b4938d8765dfe93cf6；详见RESEARCH72_CAPACITY_FORECAST。
- 本轮只有核验/文档/小证据更新，未改训练或环境；最终24封存，未完成最终公平矩阵，不宣称RL收敛或ESN最终优势。

## 2026-10-04 — Teacher完整确认、数值敏感性与真实RL启动

- 00:32UTC实时查询/fetch并读main `92d1ea1290dc4b146520224fd86cce90777a9ffb`、baseline `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`日志及AGENTS；无新协作改动。
  main92完整3226文件已共享核验到arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/92d1ea1290dc4b146520224fd86cce90777a9ffb/，
  tar SHA53195da043f6dc2919af8112d8ebff88b7395f7a11afa61515c053770331133c。
- 64/64 teacher/经典开发确认及四队列独立审计完成。预登记选择teacher09、adm03、imp02、vmc11；teacher8task/7strict，
  相同原teacher8/4；development006柱子/link6外穿透.313866810mm失败保留。所有经典确认0/8task，有限搜索不能解释为其普遍上限。
  新报告RESEARCH72_CONTROLLER_CONFIRMATION_20261004给出全部候选与hash，Git同字节选择/汇总；不是ESN/最终保留集结果。
- 三步长3秒球撞诊断完成：50→25μs峰力−10.437%、力模积分+.504%；50μs前缀精确重放。正式步长不改，峰力仍有数值敏感性。
  已知teacher通过最终入口55s逐值重放及独立审计；不代表真实24条件或全部38方法通过。
- 00:35UTC四物理进程：teacher采集、名义WBC、两个真实RL训练；第三RL等租约，新context队列已接续。
  两RL实际子服务峰1.93/1.94GiB、OOM/max事件0；首回合完整，warm-up更新0，真实梯度/保存峰值仍待查。稳定作业不重启。
- 官方SimbaV2 HEAD86899c277cdc697b2b02d827243de1ea93f20a1d完整225文件源码归档并与live逐hash匹配；
  上游归档不包括运行库/权重。独立RL报告额外核对每回合checkpoint manifest，并展示失败阶段、恢复删失；14项相关合成测试通过。
- 本轮产物共享根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/，
  对应followup_v1、controller_confirmation_v1、public_numerical_probe_v1、final_rehearsal_v1、upstream_simbav2_source_v1；精确hash见专题报告/Git证据。
  更新精简RESEARCH_STATUS、联合进度及周报；最终24仍封存，学习修订02未登记，尚无最终ESN优势或可投稿结论。

## 2026-10-03 — 独立RL actor回放准备与缺失证据保留

- 实时核验/fetch main c5343841a29987bc1468c9143ecfcfda4ce48399、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6并读两日志。
  main c534完整3223文件已核验共享arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/c5343841a29987bc1468c9143ecfcfda4ce48399/，
  tar SHA0d249b49abe926daa5dace405429578a06ed8e40dc18b1ff27dbf182649aeca3。
- 新独立进程从冻结官方RL权重重算raw actor，核对canonical48、normalizer/计数、checkpoint/训练源；覆盖失败/短回合，0新物理/拟合。
  汇总器显式记录回放覆盖；缺失不删物理结果。1线程/3GiB下14项合成测试通过，真实RL尚未运行此审计，不混称baseline完成。
- 源码核对RL奖励metadata未拼入actor；调参7/5/7维语义保留。现有物理/过滤器审计继续覆盖本入口未重建的控制律与伺服。
- 共享根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_actor_replay_engineering_v1/evidence/，
  5文件/52,258字节，manifest SHA f4db3b3e57967170bcc97f12419e5546eda59817b61c176f87a9fda52d816472，
  tar SHA a6a4251a6ffe93842e9074d1cf070bfbca237c63771f007b80620d23423a261d，已逐hash核验；完整说明见RESEARCH72_RL_ACTOR_REPLAY_20261004。
- 23:47UTC确认42/64，四稳定仿真未改；增强组/RL/teacher新采集待前序。24最终仍封存，学习修订02未登记，尚无最终优势结论。

## 2026-10-03 — 全方法与五类接触图导出工程核验

- 23:27UTC实时核验并fetch main4b72e83c422d9fbd42896b208e8f8028ae88d3b7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，读取两日志和AGENTS；无新远端改动。
- 最终图入口只消费已有审计统计，不选模型/重算CI；16方法固定顺序，保留缺失、seed、无配对NA、全部五类接触。
  成功子集的P95/力模积分仅条件诊断，图注不作总体/因果优势；三项合成测试及三图目视检查通过，0物理/拟合/封存读取。
- 已核验arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/figure_engineering_archive_v4/evidence/
  10文件/2,056,068字节，manifest SHA7fce50cef55ca5a05c2f1c8132746af0726a996dcbdde54ffe999e6f9613754f，
  tar SHAf4ee52a04dbeb355b4df1bdd606bea4f0767f9a8215fdc628ff5ab377f4bf479；源/合成输入/六图hash见RESEARCH72_FIGURE_EXPORT。
- Git保留v2和v4真实合成manifest，说明仅版式数据；v3本地试排未伪作服务器归档。teacher/经典确认继续，RL等前序；最终比较未完成。

## 2026-10-03 — RAL机器人储备池作者稿及近年先例核对

- 延续实时核验main4b72e83c422d9fbd42896b208e8f8028ae88d3b7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  main4b源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/4b72e83c422d9fbd42896b208e8f8028ae88d3b7/
  全3218文件核验，tar SHAaf0f17eeba547949e5b5ec11eba394b3bc426062fd8c446d15dcf6aefea98018。
- 阅读Shen等arXiv2409.06961v2的完整HTML正文/公式/表/参考文献，对应DOI10.1109/LRA.2024.3523229；图未独立渲染、未复现实验。
  其ESN/物理储备池、T-S分组读出和200Hz软体硬件控制已有明确先例；人工抗扰施于计算储备池，不当本项目机械臂避让证据。
  补查ICRA2025 RC+FORCE及2026 SSRN纯运动学ESN力估计，前者仅元数据/摘要、后者是预印本且未读全文；不夸大阅读范围或方法首次性。
- 更新RESEARCH72_METHOD_POSITIONING及进度/周报：论文贡献仍须靠同数据机制消融与公平闭环结果，未引入新baseline/预算或改环境/gate。
  23:06UTC参数确认16/64、四稳定仿真，其余等前序，真正24最终未开。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/related_work_review_v2/全8文件核验；
  tar SHA2e68435b5e3ea6ca8f79efb0e698b8782d7c05cb500506b1e2477cd1f9cb3406；HTML SHA61f4a5baada4835aabbddaf505d83c19c16e3e648e212e5ae8fa25790dbf9a46；
  阅读记录SHA84f7682a953d784ee260e6c846f815b25f9747904846ce4404b3d82db165b77b。保留广搜不相关命中，OpenAlex两次429未伪作已读文献。

## 2026-10-03 — RL组合内存有限预检与RMSE解释

- 本轮延续核验main558947de4d9aef526768f6af86c0f94dd331b3a0、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  main558源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/558947de4d9aef526768f6af86c0f94dd331b3a0/
  全3215文件核验；tar SHA484d74b444652d2053523998cc09f63e4514bc436efd04ef0da62eae926b5a13。
- 22:53:57–22:55:16UTC实际learner依赖＋80k Replay＋1,086,394,368B物理队列等量压力，CUDA单线程3GiB/无swap，
  4周期/8工程更新峰值2,844,037,120B，余359.715MiB，oom/max事件0。原工程7D73文件集合/hash不变；8更新丢弃，不计训练或候选。
  这是零物理静态压力，不是三learner+真实仿真/存档峰值保证。真实5500步仍须核验，不改运行资源与训练源码。
- 共享根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_memory_probe_v1/execution.json
  SHA26885a47d096fd3bcce484544bbb86ca7812b746524d540538d7dc7b83193297；相邻rl_memory_probe_source_v1实际脚本
  SHA9be4dc23c1ae0e0fc8a880d08ea241eb249e570509abd9cc67aa77aef36b2593，两端核验。Git含同字节原执行记录，语法/有限真实运行通过。
- 核对EpisodeMetrics.sample：RMSE是物理子步末端到当前任务阶段goal距离，各控制器切换时间不同。
  最终报告明确Stage-goal RMSE与解释边界；不改任何计算、排序或gate，不把低误差但停滞称柔顺优势。
- 更新分析方案、联合进度、周报、RESEARCH_STATUS及RESEARCH72_RL_MEMORY_PREFLIGHT。teacher/经典确认运行中，
  新组/RL等待，24最终仍封存，修订02未登记，无ESN最终优势结论。

## 2026-10-03 — 初始264回合完成与全部候选的描述报告

- 开工实时核验main94fdf073be3c03c437d88b656ea5e6903f3c0796、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，fetch并读两日志/AGENTS。
  既有main94源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/94fdf073be3c03c437d88b656ea5e6903f3c0796/
  3211文件已核验，tar SHA a9004df3d23c08d85e126e2726f2834f118c5d2fd0bf6d69228a0d948eee1e3f。
- 22:40:59UTC初始33模型×8条件264回合及四队列独立审计完成：261完整/3短回合，105task/51strict是全部候选账本，不作最终方法率。
  ESN点版19/24task、9/24strict，积分11/24、4/24；六matchedRNN均selected_update0继承ESN，不能据此宣称充分优化RNN不如ESN。
- 新零物理报告逐hash关联264独立审计/接触指标和33训练记录；保留各seed/variant、短失败、暴露NA/恢复删失。
  点版ESN推杆P95均值21.432N较无记忆24.303低，但力模积分36.733Ns较33.242高，暴露集合不同，不作全面优势结论。
  原事件指标为v2，最终须用v4独立复算；没有改门槛/指标、拟合或开封最终条件。
- 服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/public_initial_report_v2/REPORT.json
  SHA adb7ff8e71117d09a612796e6a56ca02b17b430054ca707f51832112194d7b4d；报告脚本SHA8c78f2f0b78228b89e790826c38dda11fd1de02ea350e1b17a07b37cecca8d32，
  selector依赖SHA6b1785c55c183982c7040293276987c3a9e87ef70914934bf598b649db530354均两端核验。Git含279518字节同字节报告。
  v1只读汇总因str/Path类型失败，源保留；v2在独立目录修复后141ms完成，无仿真重跑。3聚合边界检查及真实全批对接通过。
- 更新RESEARCH_STATUS、联合进度、周报和RESEARCH72_INITIAL_DEVELOPMENT。64回合teacher/经典确认开始、四仿真内；
  新teacher采集/增强网络与ESN/RL适配仍待前序。24最终封存，修订02未登记；不以初始开发结果声称可投稿或ESN独占优势。

## 2026-10-03 — 首撞短步长诊断登记与诊断成本分母

- 本轮延续实时核验main f40b1ad05d43373c380d71b06807b7ee9785a8b7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；稳定仿真保留。
  f40源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f40b1ad05d43373c380d71b06807b7ee9785a8b7/
  已核验3206文件，tar SHA4139bca72fd41b21393b8294f016e3028958ae69402c8dc7bc4c9abd565f3844。
- 22:02:45UTC登记原teacher/train_000三条3s前缀，dt100/50/25μs，最多9模拟秒/210000子步。
  只改诊断MJB timestep并验证还原整个二进制hash；50μs前缀须与已有轨迹精确重放。正式55s/50μs/原gate及输入不变。
  独立runtime的525旧文件与f40逐hash一致，仅新增诊断和测试；未对运行源热改。
- 有限服务sii-r72-numerical-probe-v1/PID2403221，1线程/3GiB/CPUQuota100%，等followup完成后取一共享租约。
  当前waiting_for_predecessor/0派发；worker拒绝无存活租约owner的启动。无定时任务、无新增模型或学习预算修订02。
- 原生最终版本3模型/角色测试、本地4预算＋2账本检查通过；均0积分。诊断attempted/completed/耗时保留，
  但已知重放成功和短探针false不混任务成功/失败分母；预测对新增短探针保守计完整回合成本。
- 服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下public_numerical_probe_v1/SPECIFICATION.json
  SHA234712686ed7ee00571a0ec3886c3f134ae33c91631d87024111cdb67ca892a2；Git同字节证据。
  相邻_numerical_runtime_v1实际脚本SHA86a8d8907b93464d9a2c42ef46431534f1cd2697e486e1a04951f8a91b445a36；
  incoming/research72-numerical-overlay-v2.tar.gz SHAc722b43ba619c67d5588a4f8df33f837850e56c980028f7f8058a5a13c567e60两端核验。
- 22:05UTC初始246/264，第七完整身份ESN/matchedRNN各4/6task、1/6strict；matchedMLP2/6strict、memoryless1/3、普通MLP1/6、RNN0/6。
  全264整阶段审计/teacher确认/增强组/RL尚未完成，24最终仍封存。诊断边界及准确共享路径见RESEARCH72_NUMERICAL_DIAGNOSTIC。

## 2026-10-03 — 全102学习actor字段审计与本地完整三机位工程验证

- 延续核对main c84a7cd8aea0ab1874d7c3682773e772445c2cc5、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；运行快照不改。
  c84源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/c84a7cd8aea0ab1874d7c3682773e772445c2cc5/
  核验3201文件，tar SHA20595252d883a0ff09b4c084544561ad45416e0f6eab6b9664d497a9752d253b。
- 本机21:23:55–21:24:06UTC对全部102模型回放train_000：140250时刻请求与导出最大差0，扰动未声明30字段动作逐值不变，
  82500状态检查不变。只读输入、有限幅值和checkpoint身份通过；3负对照涵盖隐藏状态偷用字段/输入原位改写。
  是声明18字段的序列边界检查，不证明上游传感器真实、不覆盖RL、不是任务通过；0拟合/0物理。
- 21:30:42–21:31:02UTC本地已知teacher完整55s三视角：18.771s渲染＋1.692s全帧解码，1375帧/25fps，峰值691216384B。
  输入状态/模型不变，仅mj_forward；6时刻三视图拼图目视核对。不是ESN或新最终成功，最终38模型仍按固定首条件全展示。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  actor_field_audit_archive_v1全3文件核验，结果SHA7aaba52990beb7423b707ae243434c8420f4f38ef51723d52a3ebb4dec9fc5d6；Git含同字节全102行。
  media_rehearsal_archive_v1/evidence全10文件/18244126字节核验；execution SHA464dbe742f17fa3e65c247cbf30fe8d9f4f637b323a9ec72f6b14266ad113f5f；
  MP4 SHA d6a009c7240eeb8877f4ce853331044c349787083fe4227a9c1b68d07ed11b0b；tar SHA2a8e5a140687976644095e88c189a544b0610f5afa7c63215ddbf8131366659d。
  实际本地路径/命令保留，脚本混合源及边界见RESEARCH72_INPUT_AND_MEDIA_AUDIT。
- 最新物理检查220/264，四队列稳定；24最终封存，修订02未登记，不因媒体变快削减审计预留。teacher/增强组/RL与最终比较未完成。

## 2026-10-03 — 第六开发条件失败与剩余容量核算

- 本轮实时核对main792316711f11e43a12e06bfeb389f87b015fe040、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，读取两日志/AGENTS。
  main792源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/792316711f11e43a12e06bfeb389f87b015fe040/
  核验3198文件，tar SHAdfae85ee383bb48c1044cfa6c22b3afbe4ef98b26543e07532cc27a4ee2fdb55。
- 21:09:42UTC只读成本快照209/264，206个完整回合中位351.820s/P90378.758s。完整失败计时保留，短回合计成本但不压低完整预测。
  15RL全80k上限＋已有待执行组理想还需35.253–37.829h；新增144回合加3.518–3.788h会挤占最终912回合。
  当前不登记修订02/不新拟合。理想容量不是实际排队保证，2h收尾只是规划假设；真实RL争用/物理续跑待验证。
- 第六开发身份33候选完整：ESN/matchedRNN各4task/0strict（n6）；matchedMLP2/2、memoryless1/1、ordinaryMLP2/1、ordinaryRNN2/0。
  ESN已放置四条柱子/link7穿透0.223096–0.593794mm；303temporal RMSE247.992mm停carry。未改gate/未删失败，阶段独立复核待全264结束。
- 新纯标准库预测工具3项检查通过：累计RL去重、缺失阶段拒绝、短回合不压低全程耗时。本机0物理/拟合，源与预测共3文件已hash核验共享。
  服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  EXPOSURE_SNAPSHOT_20261003_2120.json SHA97c4dfbba35b60a1f606bc83490106c0e28539a8f27ebe9d7bd157fe5d0cdd55；
  budget_forecast_archive_v1/research72-budget-20261003-2120.json SHAeaa9c54e7f9cab6fdd40fc3e9fc04e2994c27189b2e1e1b9e31eed8fd1b802d5。
  文件名2120不是实际生成时间；完整口径/命令/源hash见RESEARCH72_CAPACITY_FORECAST。
- 四稳定物理队列保留；teacher确认/再采集、增强组及RL仍等前序，24最终封存，尚无完整投稿结论。

## 2026-10-03 — 官方RL GPU有限吞吐与剩余预算依据

- 延续核验main788d6814d0ed3ac2cc5bb5a7cacafa367a66e539、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  788源码arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/788d6814d0ed3ac2cc5bb5a7cacafa367a66e539/
  已核验3195文件，tar SHA04457028dd9328893be595a922833daa507e552e65666416df1d6a0f292d7b53。
- GPU0空闲/96GiB可用后进行有限吞吐探针：官方actor128/critic512、batch256、UTD2、同80k计划；
  每维度1冷＋8预热＋32计时共82更新，总164工程更新，0物理/0候选，权重全部丢弃。同步等待JAX参数树完成。
  5D动作0.773ms＋两更新17.449ms；7D0.839＋18.568ms；冷周期71.160/16.000s，同进程缓存复用，不作速度胜者比较。
  20:47:22–20:49:03UTC，单线程3GiB，峰值2,220,003,328B。组合物理内存和3learner争用仍未验证。
- 原工程检查点5D/7D各74/73文件在实际探针后经独立递归hash核对完整集合/字节精确不变；
  语法检查及实际有限运行通过。不能把这些工程更新给baseline计入真实训练步或宣称已收敛。
  实際执行脚本SHA0ed30caf396db249c1b304767344a84ae546979a9bfe39f576bade140a9293c9；
  本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/rl_throughput_probe_v1/execution.json
  SHA687fdaf8d61f842bdd3c7572891e2064ab11e364d1895cc8cc3b9a38153a9861，已两端核验，Git保存小型同字节证据。
- 两条件teacher筛选中领先09/07均不同于原配置，需要为40条实际采集留预算；八条件确认前不选teacher。
  可选共享ESN交互读出再拟合若数据改变须144开发回合，目前修订02仍未登记。
  20:56UTC初始198/264、第六条件32/33，四仿真持续；RL v2/teacher确认/新组仍等待，24最终条件未读。

## 2026-10-03 — 170公开轨迹首撞时序核对与柔顺性归因边界

- 延续实时核验main be473ca6d6c38a71182032504b8d5194ce235ac7、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  be473ca源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/be473ca6d6c38a71182032504b8d5194ce235ac7/
  核验3189文件，tar SHA f0306577208e5612ff08a225fe9b850ba444f5215892eb65d538b05c1bf07312。
- 前五完整开发身份33初始学习候选＋原teacher共170条全部纳入，4时序回归通过。只读Spark原生20:29:31–20:30:04UTC，
  单线程3GiB、CPU23.299s，无新物理或拟合。球首段接触0.45–0.50ms，至下次真实actor计算9.20–32.20ms；
  170/170球窗峰值和首段接触结束都先于那次计算，已保守考虑50μs采样余量。
- 峰值5485.92–7407.39N不能当已标定人体安全受力，也不能证明25Hz策略已即时抑制首次碰撞。
  碰前姿态/动作、公共4ms WBC和被动物理仍有作用。所有峰值继续报告，不改gate/actor时钟；结合后续恢复/持续接触解释柔顺性。
  此为公开开发事后诊断，不是最终盲测、ESN胜者或RL已验证。全部失败/短回合均保留。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下：
  public_impact_timing_v1/IMPACT_TIMING.json SHA cd8a9ec1f707fdb1be008eceb5331d83ce17e2a4f1ee7d9a929616aa141686e8；
  SPECIFICATION SHA166648074e86fc909ddbed9dd1bc183878f36c6cace5035025eef0c04f1ffe33；
  EXECUTION_RECEIPT SHAa1c9d99d50f02a6cae2f075308954314b81f41cf76f45e311e698a9a612c0eea明确是基于日志补写的事后说明。
  实际诊断脚本SHA2a7db52731480f3dae1bed9c0c47df4c62cbb8c7352898a5a86523e179a19fa5；精确入口见RESEARCH72_IMPACT_TIMING。
- 本地单线程3GiB绘图已目视核验；服务器impact_timing_plot_archive_v1全4文件核验，tar SHA
  fc1c842de54cac4a87d1f25ccd076f9b09db3ebb9feed393cb1dddf6d632bfd3；PNG SHA c9cab76a261e3f6b567776da6a5e1efd8b63ac2f8e8c78f3b44e2c291eb94a8a。
  Git含小型全部结果和图；不改历史路径。初始20:37UTC184/264、4稳定仿真，teacher确认/新组/RL v2仍等待。
  最终24封存；学习预算修订02尚未登记，无最终可投稿结果。

## 2026-10-03 — RL首次开训前轮转登记、第五共同条件与统计区间解释

- 19:55UTC实时核对main2da38895ce8a91eb9cc7b47d94a72e53ff615166、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  读取两日志、同步skill和AGENTS，四稳定仿真保留，未读真正24封存条件。
- 初始20:15UTC169/264，五身份各33完整。第五身份ESN/matchedRNN各4/6task、1/6strict；
  matchedMLP2/2、memoryless1/1、ordinaryMLP1/1、ordinaryRNN3/0。三条已放置ESN因pillar/link7
  穿透0.209686/0.279906/0.573083mm失败，303temporal RMSE250.986mm仍carry。原gate不改、失败保留。
- RL原逐模型80k顺序存在晚排方法零checkpoint风险。首次office训练前登记累计边界5500/27500/49500/71500/80000的轮转，
  同15任务、80k总计划、奖励/模型/训练身份/截止/3租约；完整恢复优化器/回放/RNG。先保证所有组有初段。
  有限队列完成不冒充全80k或收敛，实际步数/截止另存最终候选；更多启动可能增加编译成本。
- 16调度/模型汇总/冻结工程回归通过，包含真实队列入口25个模拟分段父checkpoint和新增步核算；实际物理续跑未验证。
  精确核验旧等待器PID2332615、零队列后仅停止该等待器，旧execution字节不变；新v2 PID2384702等待同followup。
  独立runtime_v4仅两调度文件不同，trainer及其余源逐hash一致，无物理中断。主动选择器/成本快照识别登记的活跃v2。
- 主机arm1@192.168.31.70，本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  AMENDMENT_RL_ROUND_ROBIN.json SHA3ff1ae22f310825de701344df84d8f74c1c18b27e7719c448a5b563c009a7d46；
  rl_dispatch_change_v1/execution.json SHAb99f9aa0601b553e67258bfc4529d0b0498856ad9c6653fdd505c34159c5d1ee；
  活跃rl_office_adaptation_v2，旧v1仅历史登记。相邻research72_20261003_1149_rl_runtime_v4保存真实混合源链。
  incoming/sii-r72-rl-dispatch-overlay-20261003-2045.tar.gz已两端核验SHAfa888c0e518ac15b2681ba0ebaafc0e3c597a683e5a346acac884af4a8d45509；
  文件名2045是标识，实际20:13:54执行。完整报告RESEARCH72_RL_DISPATCH_20261003.md。
- 统计报告区分观测恒定/重抽恒定/点区间，避免将[1,1]当新条件的确定保证；原10000重抽和数值区间不变，18项回归通过。
  本轮无新ESN拟合、无学习预算修订02；teacher确认和新组仍未完成，尚无最终投稿结论。

## 2026-10-03 — 本机99轨迹覆盖诊断与第四共同条件完整

- 延续main a5ed961ef2216033e2311f964ba4617dc80f0de5、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6实时核验。
  main a5ed源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a5ed961ef2216033e2311f964ba4617dc80f0de5/核验3178文件，
  tar SHAd3bcddf8c1b8756a8daf64f7461cb690cae7594dfef0ec42f570cd96f8ea5eaa；未改运行快照。
- 新本体覆盖诊断固定前三完整开发身份全部33候选共99轨迹；18D已有actor字段、固定物理尺度与clip。
  校准排除整个自身teacher训练身份，18身份24750帧的近邻P95=0.308898；不用验证/开发校准，不含储备池状态。
  ESN303temporal/condition001超参照72.7%、RMSE124.44mm；302temporal成功仍46.9%、95.20mm。
  clip约0–0.3%，不能只改裁剪或把距离当失败原因/校准OOD概率。所有失败和短回合保存，图无胜者筛选。
- 本机airpig/NumPy2.4.6/SciPy1.17.1，单线程3GiB，4.163秒；2合成检查通过；Spark只读提取核验所有trace/AUDIT/model。
  0新物理、0拟合。诊断说明RESEARCH72_PROPRIO_SUPPORT及Git内174KiB图，PNG SHA c7d4a4f4397148972371da7c91a435749f478a8e6acdda77754097e10c9d20ea。
  初图标签拥挤仅修排版后目视核验v2，未改数据；代码/数据注册时钟与真实执行命令记录在EXECUTION_RECEIPT。
- 本轮服务器根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下：
  public_proprio_export_v1；proprio_support_archive_v1核验5文件/tar SHAdc07c9d45036ecda010dd2124208f1d421ff6628f04d3490211eaa608363f6b4；
  proprio_support_plot_archive_v2核验4文件/tar SHA78f681f29e7f14bfb46810f484a2ef45057e7dc2a9d4a72297cbefa1bc931fad。
- 19:37UTC143/264，第四共同身份ESN/matchedRNN各5/6task、4/6strict；matchedMLP2/6strict、memoryless1/3、
  ordinaryMLP1/6、ordinaryRNN0/6。初始候选不是最终方法统计；RL/新组/teacher确认等待，4仿真稳定，无其他活跃agent。
  真正24条件封存，修订02未登记；当前没有完整投稿结论。

## 2026-10-03 — 选定teacher共享读出再拟合入口准备，尚未启动新预算

- 延续实时核对main ad957af96444b418c0bceb8063bd0e72031bd8fc与baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；重读AGENTS收尾。
  ad957af源码已在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/ad957af96444b418c0bceb8063bd0e72031bd8fc/核验3175文件，
  tar SHA58f3b23608d8c012db9159c0284fcef932aa24567964138134a3cbbb6b795dca。
- 新refit-data-receipt要求teacher选择/执行/config/数据hash和合格账本一致，未完成采集、标签非真实或最终已开封均拒绝。
  同teacher验证0新采集；不同teacher要求40真实身份导出。只用train/imitation_validation，保留拒绝账本。
- 可选context-readout-refit沿用12组ESN ridge和128储备池，加已验证固定G交互，只训练读出；同特征MLP/RNN获得相同特征。
  网络沿用此前跨3seed验证选好的point学习率/4000更新。数据相同则不重复训练/评估普通网络，新增12模型；数据变则18模型。
  服务器权重引用保留真实路径，不能在本机伪造挂载；登记时在服务器核验复用权重，最后模型选择支持声明的不同数据谱系。
- 14项合成登记/数据来源/跨seed选择/全38模型入口回归通过；没有实际拟合或物理重放。
  RESEARCH72_READOUT_REFIT_PREPARATION明确拟议cap60、额外96或144回合及成本，但AMENDMENT_02尚不存在，当前有效cap仍48。
  必须等teacher确认和剩余预算核定后才能正式登记/拟合；不让额外ESN搜索挤掉已登记baseline或最后24小时评估。
- 19:19UTC初始131/264，第四条件32/33；4稳定仿真、无新增物理；真正24条件仍封存。
  已完成工程，未完成新结构学习/完整跨条件比较/投稿证据。新代码将在本提交对应source目录核验，不改运行快照。

## 2026-10-03 — 补齐放置阶段接触负载、保留原事件统计及全失败安全审计

- 18:53UTC实时核对main2bd499594f45fce1888e34128bdaa67d260dc23a、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；读取AGENTS和两日志。
  main2bd源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/2bd499594f45fce1888e34128bdaa67d260dc23a/核验3173文件，
  tar SHA966cc1894a3c16e39ea745d1e0ea8a9b88bda61a31cec823e23c52332030f8f8。
- development_001的全6ESN与teacher曲线暴露晚期人体接触。新增metrics v4全实际时长/原事件窗外负载，
  保留原窗口、恢复与所有gate；补充属公开开发观察后、最终开封前登记，不宣称最初预注册。
  final report将短失败、完整失败、缺字段和无接触分开；安全表包含短回合外穿透/edge及执行器幅值/变化率审计。
  external不含payload而edge含robot或payload，不把重叠列相加；补充表不作配对优越性推断。
- 本地14项测试通过；初次入口缺PYTHONPATH导入失败已纠正。Spark原生7条完整55s只读回归：所有旧数值/结果精确不变，
  ESN302point窗外人体力模积分1.430966Ns/接触0.29505s，原teacher0.167416Ns/0.02675s；不是安全/优越性结论。
  0新物理、0拟合。服务器本轮根/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/下
  supplemental_contact_regression_v1/results/REGRESSION.json SHA29ee8fff3ccd85bc50746341814d8278f64fd526aae9c92e099220ef29075c04，7产物hash核验。
  public_condition1_esn_curves_v1/保留全6候选+teacher图；精确源/图hash见RESEARCH72_SUPPLEMENTAL_CONTACT_20261003.md。
- 18:59UTC初始学习开发115/264，前三条件各33完整；第三条件总11task/5strict，ESN/matchedRNN各3/6task、1/6strict，
  matchedMLP2/6strict、memoryless1/3strict、ordinaryMLP/RNN0strict。含损失候选，非最终模型统计。
  4稳定物理队列未重启，RL/确认teacher/新组等待；真正最终24封存。尚无最终胜者或可投稿结论。

## 2026-10-03 — 38模型冻结前汇总、相同teacher无重复采集与方法定位

- 本阶段基于已实时核对main9d996dde19adf4bb816cc403b51bc5025f527f32及baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；收尾重读AGENTS。
  main9d源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9d996dde19adf4bb816cc403b51bc5025f527f32/
  核验3170文件，tar SHA586c79474bf49dd7d05cca9d679b130014472e4374956fa11f6cdbf4f48d4bee。
- 新research72_finalize_selection仅汇总公开选择：6学习族×3seed、5RL族×3seed、teacher/三经典/nominal共5确定性方法，合计38。
  缺任何family/seed或混用跨seed variant则阻止冻结，不以开发成功资格筛模型。RL按最新完成训练边界选checkpoint，
  不读reward/任务结果来挑权重；保留实际累计步和stop_reason，共同cap不冒充每族步数严格相同。
- 发现再采集在teacher相同时记录complete_skipped_identical_teacher，而最终锁只接受complete工作收据：
  新汇总器核验原teacher/config/选择hash完全相同且新增物理0，再写明确的零操作closure；不改原执行状态或伪造40条新示范。
  五项合成检查通过，包含38模型全失败仍保留、缺失seed/族、混variant拒绝及真实文件/manifest衔接的skip分支。
  checkpoint字节仍由已有final-lock验证；本次并未执行真实最终模型汇总、锁定或开封。
- 文献原始元数据4篇已核验；已读Gauthier等(2021)NG-RC出版商HTML正文Introduction至Methods，未读补充材料。
  新RESEARCH72_METHOD_POSITIONING说明固定非线性特征+线性读出及leaky ESN不是本项目首创，
  本体信息调制记忆的有效性仍待同数据消融与完整闭环结果；状态有界不当echo-state收缩、无源或机器人安全证明。
  其余3篇仅核验元数据，不声称完成系统综述或忠实复现；一次429和首次303页面未冒充有效全文。
- 已核验共享归档主机arm1@192.168.31.70，本轮根
  /home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/related_work_review_v1/：
  5文件，tar SHA3c7b08994ab1e09d1daf0efed5f845843482a63d7f59ff0e98f9586fbfad961c，
  HTML SHAb03455ff17545082d796162b922d3741a79df55b438e6c62160c20d84fcc8231。
  初始4元数据归档related_work_metadata_archive_v1独立保留，tar SHA5ea2cfc9dd0888f0bb50e25c4b5e54ed645ac99fe359708b81fc5f0e063c7347。
- 18:36UTC初始开发100/264（33/33/32/2分布），仍4稳定物理队列；第三条件尚未齐备，不提前汇总其胜负。
  本机约10.6GiB可用；没有活跃subagent或新增仿真。teacher确认、RL与再采集仍等待前序，真正24条件封存。
  无新拟合、无预算修订02、无最终结论；下一轮学生拟合必须等真实数据与可用预算核定。

## 2026-10-03 — 最终矩阵/媒体入口、工程中断保留与第二条件完整结果

- 延续本轮实时核对main e4366a7a941da64b443db1278ce36af4eae72ebb与baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，AGENTS已重读。
  e436源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/e4366a7a941da64b443db1278ce36af4eae72ebb/核验3165文件，
  tar SHA068bec9321ced62a1b3fa8780a8e68d6bd18b1dbb535306d686ca257a1eddd88。
- 第二共同开发身份development_001全部33候选：ESN6回合3task/3strict，matchedRNN同3/3；ordinaryMLP1/1、
  ordinaryRNN1/0、matchedMLP0/0（分母均6），memoryless0/0（分母3）；总8task/7strict。
  分母都是真实已跑次数，不是未评估。含损失候选，不是最后模型的泛化成功率；增强baseline仍待执行。
- ESN303点版XY13.192mm、外穿透0.149mm，但直到53.44s才load_transfer、54.76s才release，任务仍失败；
  积分版XY7.520mm、外穿透0.187mm，54.24s才load_transfer，亦失败。原55s任务要求不修改。
  两者RMSE102.724/124.436mm；需要改善恢复推进而非单看末端XY。另seed301积分版柱子穿透0.687mm失败。
- 全33模型只读诊断主机arm1@192.168.31.70，本轮根
  /home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/public_contact_diagnostics_condition1_v1/，
  DIAGNOSTICS SHA5c90db239476de8dff03d8382f8af903f047d48afa0f0cb85e881ffac773cb26，
  source SHA9afb61d840dc0c93b32f93d0262c188a48d2178a7e94c4521e58b660fa04cc9a。零新物理回合或拟合，反事实查询不当训练标签。
- 新research72_comparison_report汇总全部锁定方法/seed/24计划身份，验证原始audit/独立复算/metrics/锁关联，
  未审计保持缺失及分母上下界；短回合单列、无接触NA、恢复右删失，严格成功为主、接触条件子集明确披露。
  输出Markdown与逐回合JSON和交叉bootstrap，不排序制造ESN第一；8项合成回归含证据链接入/篡改拒绝通过。
- 修复未来最终batch一队列报错会跳过全部peer独立审计的问题：先保存完整PLANNED，保留失败且继续审计已完成peer；
  audit_paper_phase新增显式allow-partial，审计完成不等于物理全完成。2项合成队列故障测试通过，无自动重试。
  当前运行runtime没有热改；最终入口预演只覆盖worker，完整多队列真实最终链路仍未执行。
- 新最终媒体入口避免沿用旧12小时硬编码截止；选择首个共同最终ID、全部锁定方法/seed，三机位25fps全程，
  失败不剔除、短回合不补帧、缺失不冒充0成功。选择回归通过；未制作或读取最终视频/条件。
- 已完成工程和第二条件诊断；运行仍为初始4队列；RL、确认teacher再采集等仍等待前序。
  真正最终24身份封存；最终矩阵/媒体及新结构训练均未完成，不宣称RAL可投稿或ESN领先。

## 2026-10-03 — 当前本体调制读出工程验证与最终入口预演登记

- 17:42UTC实时核对main65b3dd64868010d9579c565842abeb9a04ac9ca4、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，读取两分支日志和AGENTS。
  65b源码在arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/65b3dd64868010d9579c565842abeb9a04ac9ca4/核验3158文件；
  tar SHA f646a5b44ada140f03712fb0e7d0a74087df108d61cf09804065a9458d6a4bb3。
- 公开完整首条件诊断v3保留全部33模型。ESN积分303在41.72s的z请求+0.3368中，当前signed load项-0.4708，
  signed state项+1.4374，另有absolute state等抵消。是相关特征的代数分解，不是隔离因果结论或实际teacher执行标签。
  DIAGNOSTICS SHA66b833eb6d2ce68f35156ffe16c5fbf5d3926bd21087a24ad8752f64e8394d38；真实执行脚本SHA89c57a43ed28a29e8b6767b957c39fde49525946093c0621af88dd2d3949966e。
- 新可选固定交互特征r*tanh(G*c)，仍128储备池、相同本体输入，只训练线性读出；没有混合teacher。
  扩展特征后不是单独对r/c线性和，训练系数2884→3780，固定G另1536系数，不能称等参数/FLOP。
  给同特征MLP/RNN同一固定变换；未拟合任何新候选，原ESN48/seed cap仍用满，无修订02。
- 本地单线程3GiB，4随机系数组合NumPy/Torch最大差5.61e-15，真实loader导出精确；
  零状态零负载平衡、禁用字段隔离、固定G无梯度通过。旧102模型在已知train_000完整1375帧动作重放全部误差0。
  ENGINEERING_ONLY权重不列候选，不是物理结果。原运行runtime保持不变。
- 本轮共享根arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  public_contact_diagnostics_v3/；context_readout_engineering_archive_v1/已核验14文件，
  tar SHA ff52bdeb2fecdafc2ebc9f3791f152b0b86491f7e60524b5c7d29f22e1926c82。
  PARITY SHAfa1bef3e4193bfc188b9307b138aee2391438762bd7ea47dc2a62aa69e674b3e，
  backward PROFILE SHA3b7d7c7491783de56853edf256e8da570bc7b343b504f3d45e9889d707b047fb。
- 最终入口预演服务已登记，等待followup完成后使用1受管理槽位重放已知train_000的原teacher。
  独立合成协议/锁/receipt不读写真正封存区或FINAL_UNSEAL_RECEIPT。spec SHA92dc8c61a5e41e63bf5a29b4ed5d154583322cd92b563263b9bd4fd47a37f712。
  相邻research72_20261003_1149_final_rehearsal_runtime_v1核验499文件，tar SHA1179c10aaf2631970fdf261ff9811df37a5096f4329c7dc4fc9e800f337ac8d2。
  最终batch拒绝预演活动时启动，曝光账本将预演单列；预演尚未物理执行，不能宣称最终链路全部验证。
- 17:46UTC初始开发60/264完成，4队列稳定；RL/teacher再采集/预演等待前序。真正最终24条件仍封存。
  已完成工程验证，尚未完成新结构学习、全部baseline适配或最终统计；不宣称ESN优化有效或论文可投稿。

## 2026-10-03 — 首开发条件完整对照与柱子失败动作诊断

- 继续核对main415501369e4b26ecdca60f65a9a6761115ffb6e8、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  4155源码已在server source/<完整SHA>/核验3157文件，tar SHA1efd2cb93ccd463121bf6811ba67a902330e6714b689ac52cc9196a450a22d5a。
- 首个公开development_000的33模型全部完成：14任务/10严格；ESN6回合4任务/3严格，
  matchedRNN6回合4/3、matchedMLP6回合2/2、memoryless3回合1/1、ordinaryMLP6回合1/1、ordinaryRNN6回合2/0。
  这些含两个损失版本，不是选定方法跨条件成功率；后续学习率/机制复核仍未运行，不以欠优化网络宣称ESN领先。
- 扩展现有teacher接触诊断工具，要求同一公开身份全部登记模型齐备且完成才诊断；拒绝封存角色，检查协议/公开身份hash。
  所有33回合一同分析，没有选掉失败；truth仅用于离线诊断，不进入actor/训练标签。
- seed303点/积分ESN最差穿透均为柱子-link7。点版首次接触41.4745s，最差41.8659s，延后0.3914s；
  积分版首次25.75275s，最差41.729s，延后15.97625s。不应一概归咎于首次碰撞太快或25Hz来不及反应。
- 在完整真实学生观测上重放原teacher内部状态作反事实查询：积分版41.72s学生z请求+0.3368，
  原teacher建议-0.2049；点版41.84s分别+0.1298/-0.0036。是同观测历史下动作偏差，不能证明换teacher就物理成功。
  请求、实际过滤动作和查询均分开保留，明确actual_execution=false、used_as_training_labels=false。
  未用这些开发历史重新拟合学生或扩充示范，现有ESN48候选cap未再扩展。
- 已核验共享产物主机arm1@192.168.31.70，本轮根public_contact_diagnostics_v1/和v2/：
  v2 DIAGNOSTICS SHA6dc2185a2ba9d2134f0fab897b2a76b62cba4936ccfe83e2a3020cbd6e9933a7，
  实际脚本副本SHA1fb72edb429a314ed8941b3b578b2e8caaa004bbde44609a49b0dc486926574f。
  两次均为单线程3GiB离线分析、0新物理回合，原v1保留；Git同步v2小证据。
- 17:08UTC开发37/264完成，实际均值343s/回合；912最终回合按4并发仅物理约21.72小时，还需预留审计/工程开销。
  不再盲目堆叠开发候选。优先完成当前整批与选定teacher真实再采集，之后若有新拟合须先登记共享数据/预算且保证最终时间。
  最终24条件仍封存，RL等待前序，没有提前结束持续任务或宣布论文完成。

## 2026-10-03 — 成对统计、短回合删失修正与实际推理成本

- 继续已核对的main9855fa8a78c9ea87bd3cf0a63f0fbd345483a296/baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  9855源码tar SHA ed40d4b2980729b8f4eef998e76fcced5636448cd5e401f9b4281902df733719已在server source/<完整SHA>/核验3151文件。
- 新成对统计模块按条件与训练seed交叉bootstrap，确定性经典对照不伪造3seed；缺失回合保留分母上下界，
  无接触/短回合/失败不进入“双方严格成功且接触”的条件子集；该子集不取代完整成功率。8项合成回归通过，
  包含首seed失败不能抹掉后续seed与确定性对照的有效配对。尚未处理最终24身份。
- 模型锁加入所有AMENDMENT文件内容与集合，7项保护回归通过。完整冻结前后预算修订必须一致，真实封存仍未打开。
- 修复paper_metrics早停回合恢复观察窗可能超过实际最后采样时间的问题；v3增加计划截止并保留右删失。
  3项完整提取器合成回归通过；一个真实55s ESN回合全部数值与v2精确相同，只增加计划截止及变更版本/源时间。
  原runtime和历史v2证据不覆盖；主机arm1@192.168.31.70，本轮根metrics_censor_regression_v1/full_esn_point.json
  SHA7aece33d1cc89609f3dac3a1571433901327eab5e80ae9e6608dc4d909194d65，Git含同一小证据。
- 按服务器PRIORS与controllers重新核对，纠正文档“全部参数RL5D”：导纳7参数、阻抗5、VMC7。
  阻抗公共残余动作虽记录为7D零，真实执行仍是其独立底层力矩律。实际训练代码一直使用各prior维度，未更改控制律。
- 本地1线程3GiB零仿真核验全部102已保存拟合，已知train_000完整1375帧动作重放误差全0；
  每模型3次序列推理、保留原始ns。ESN/memoryless2884可训练系数；ordinaryMLP5504、RNN21888；
  matchedMLP22852、RNN39236。各模型中位数再取族中位数：ESN32.15us、普通MLP7.98us、普通RNN10.00us。
  ESN系数少不意味着推理更快，固定特征有开销；actor-only耗时不当整个控制器实时保证。
- 服务器本轮根inference_profile_archive_v1/inference_profile_v1/完整6文件逐内容/大小/模式核验，
  tar SHA4f826b6a90e2ce22925b223d6b6ddbdb99693202c6f70c0842ef72ee64912eaa，PROFILE SHA91431277af003439608cb5677a53cdd1fd6328bfcc737272f02712d29f60ffa2。
  Git INFERENCE_PROFILE_RECEIPT.json含精确命令、成本、归档与局限；初次systemd缺工作目录退出2、脚本未打开，修正工作目录后完成，不是物理重试。
- 16:50UTC公开开发24/264完成。首条件ESN全部3seed×2损失已齐：3/6 strict；
  seed303点/积分外穿透0.551/0.476mm超过0.2mm，点版任务成功仍strict失败；积分版任务也失败。
  待完整开发审计，不从单条件选择模型或改gate。后续RL/teacher再采集等仍等待前序，未重复启动。

## 2026-10-03 — 控制器筛选完成、真实teacher再采集入口与首轮学习闭环

- 16:27UTC重新核对main 8bdade7fbd15f76f725c985514bde6e0c94a0253、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6并读取两分支日志/AGENTS；无远端新变更。
  main8bd源码在服务器source/<完整SHA>/核验3144文件，tar SHA ead3221294e2cfd2565679acaa8b71713381afd64a84217700f6a8fe0919b612。
- 参数筛选96/96完整55s并独立审计：增强teacher21task/13strict（24回合），导纳/阻抗/VMC各0/24。
  这只是12候选×2开发条件；按原规则各取2个继续8条件确认，尚未确定最终参数。
- 初始33模型×8开发条件正在实跑。第一个条件development_000/seed2026100301：
  ESN点版task/strict均通过，RMSE29.399mm、峰矩50.386Nm、峰速0.373926m/s、放置XY24.774mm，距离25mm门槛很近；
  ESN积分版XY26.381mm而失败。无记忆及初始matchedMLP均成功，RMSE37.050mm、XY20.283mm。不是最终盲测或跨条件结论。
- 首4回合离线接触诊断：ESN点版推杆P95力14.313N、力模积分43.724Ns、接触4.945s、保持期最大脱离仅0.0013s；
  无记忆分别25.297N、28.817Ns、2.666s、2.191s。低P95与低RMSE并未同时带来更快脱离和更低累计负载。
  ESN未触柱子，该项显示NA；无记忆有柱子接触。球接触峰力约5.9–6.8kN，属于刚性碰撞仿真瞬态，不能称人体安全力或25Hz策略反应。
  全部恢复诊断右删失，不能写成0秒恢复；完整队列独立审计仍待完成。
- 新增有限refined-teacher服务：等待8条件选择后，在原32train/8validation身份真实执行选中teacher；若配置相同则跳过。
  原48轨迹不覆盖，无开发历史作标签。只采集/审计/导出，不偷偷增加学生训练；任何新拟合须先登记预算。
  导出器默认路径原生回归仍得到相同24示范/33000帧和同一数据SHA b97acf4c61d9d3ba4d5fcb4817ac449b460e65a4821be632c5f61a5a1bba67c6。
- 新学习选择器只接受完整独立审计的三组开发结果，跨全部3seed/8条件统一选variant，失败族也保留；3项合成回归通过。
  54合格权重来自75实跑权重；未对尚未完成的真实数据执行选择。最终入口补充等待refined-teacher，成本账本纳入再采集。
  分析方案注明参数动作与公共7D接口不同；16:45核对原prior后更正为导纳7D/阻抗5D/VMC7D，阻抗另有底层力矩律；
  独立选出的ESN/memoryless不同loss/gate不冒充隔离记忆消融。
- 服务器根 arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/：
  controller_screen_v1/SUMMARY.json、early_learning_metrics_v1/、teacher_export_regression_v1/、teacher_refinement_v1/SPECIFICATION.json。
  context21权重原生1375帧重放最大误差1.66e-14；CONTEXT_GATE_NATIVE_REPLAY.json与以上小证据已纳入Git。
  新采集实际源码相邻research72_20261003_1149_teacher_refinement_runtime_v1，tar SHA4bb4d0bbb27b4a95fa8406bd8b4ce6c0f8b7c75acb829a84a4e51a8e56fbfb51（8bd加本批修改）。
- 已完成：筛选/初步诊断/导出回归/选择器工程；运行：四学习仿真；等待：参数确认、RL适配、同机制/小LR评估、新teacher采集。
  24最终身份仍封存。未取得ESN最优或RAL投稿完成结论。

## 2026-10-03 — 记忆表达缺口诊断、预算修订01与同机制ESN/MLP/RNN

- 延续本轮核对main e32f02ddc16e1b65511b5a9f9cfbd316042b43ef、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  e32源码归档SHA8f007a3f8333ee5fff0da721b0a36f8456dac01d4d98093621fd440433e2edf0在服务器source/<该SHA>/全3133文件核验。
- 代码和零仿真输入干预发现：原ESN的context只乘当前load，直接context读出被约束为0；load归零后，
  相同历史无法区分后续卡住/前进/意图消失。3seed两loss的10秒合成探针状态仅保留约0.78%，
  卡住时teacher恢复记忆仍0.99976、z动作约0.37491；该人工输入序列不保证物理可实现，不当任务失败证据。
- 真实18训练＋6验证完整teacher动作复现最大误差1.11e-16；估计线性负载<0.5N且恢复记忆>0.5的片段
  分别3.24秒/16身份、1.08秒/6身份。<0.05N的验证片段为0；真实覆盖远少于人工10秒探针，不能过度解释机制。
- 15:23UTC在新拟合前将AMENDMENT_01_CONTEXT_MEMORY.json归档服务器，SHA5b6e9c22751b0045e7da980f24480338ab03164c6cd7fc29a05fbab68ac27a6a。
  各学习族每seed上限显式24→48；实际ESN48、memoryless24、普通+同特征MLP/RNN各14。72h/48h截止、数据、环境/gate/actor/执行器均不变。
- 使用既有固定随机本体context→leak调制（0.05..2），仍128固定储备池、受约束线性读出、无运行teacher；
  相同固定gate提供给重训memoryless及matchedMLP/RNN，后者沿之前3seed平均验证选定LR，各4000更新，全部原组保留。
  NumPy/Torch含gate及无gate最大差3.83e-15，零平衡/禁用字段隔离通过，gate不是可训练参数。
- 本地单CPU/3GiB完成21模型（另108ridge和48000梯度更新），完整动作导出回放与输入审计通过。
  gate打破合成输入不可区分性，但未获得teacher长时间保持；ESN点/积分验证误差普遍高于原版，未宣称机制或任务改进。
  全21模型登记同8开发身份168回合，四仿真既有筛选74/96正常；新有限服务等待原followup，之后每回合共享释放槽位。
- 服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `local_context_gate_archive_v1/`包SHA c206c4e98102bff46d0dc97a8915e5018ddfbb9369914f08ce5b2e5b1c0b2ea6，21模型元数据/权重/原拟合源全核验。
  `memory_mechanism_archive_v1/`原探针/一致性包SHA2bdd45803e510475fdc40221ca0a7c30c6c2cb3fe377e852390911e921ed96d8，两端及解包数组hash一致。
  `CONTEXT_GATE_DEVELOPMENT_SPECIFICATION.json` SHA19347931867d439ca2951a934c5b9bde636681fe785eed1c934db920993b6cbf。
  有限服务`sii-r72-context-gate-development-v1`已核验仅等待；相邻`research72_20261003_1149_context_runtime_v1/`源码tar
  SHA516ed7e308b8911c355b6397217db32d963d5de6306888fd2e083ae8d293d641，base e32＋本批修改，旧runtime不改。
- 完成：工程/机制/拟合/归档；运行：开发筛选；等待：全部学习闭环和RL。最终24身份仍封存，新的物理改进与投稿证据未完成。

## 2026-10-03 — 最终评估冻结保护与训练成本账本

- 15:00UTC实时核对远端main389e9e53bc016a03a250fe5f053a5a6513331023、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6，
  两分支无新修改；读取AGENTS/同步skill。389源码包SHA77790e550cdfd516b2ef69701ae2a5339222bede0ea8addc28933ab164a33219
  已在`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/389e9e53bc016a03a250fe5f053a5a6513331023/`核验3126文件。
- 新增最终模型锁、独立最终worker和有限4槽队列。锁要求全部16类别、全部3seed与开发证据，
  不按strict资格删方法；checkpoint/RL嵌套文件、精确源码及资产集合核验。直接调用子队列也必须先有同锁/同输出开封收据。
  6项合成数据回归通过，含改权重、加源码、改资产、改收据/条件hash、缺收据拒绝；未读真实封存条件，未启动最终评估。
  真实端到端最终执行仍未验证。新增代码本批提交前仅本地，不热改已有稳定runtime。
- 新只读曝光账本分开统计teacher失败、ridge候选、神经梯度、开发仿真和RL累计新交互；恢复段不重复累加继承步数。
  15:08UTC快照teacher48完整44task/28strict；筛选56/96完成17task/11strict，其余仍在运行，非最终结果。
  初始33模型108ridge/96000梯度更新，复核48模型192000梯度更新；RL等待前序，当前新交互0。
- 本轮服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `EXPOSURE_SNAPSHOT_20261003_1520.json`（实际时间见created_utc）SHA579bf27e5ee931f9c00d036b59c35a911e8583e83072eb49d181f3d48e5cd369，
  已下载逐SHA核对并保留Git证据。实际脚本在服务器incoming/research72_exposure_ledger_20261003_1520.py，
  SHA2812aaf433ef13005e9f7f966781ea6f7c1f16418cde2036af6c721aa317c85e两端一致；后续已提交源码以source/<commit>为准。
- 新分析方案先登记成对条件/seed交叉bootstrap、接触覆盖与双方成功子集局限、恢复删失和成本披露；
  不把72回合视为72独立环境，不把无接触当柔顺零力，不以多指标事后加权制造赢家。环境/gate/actor/执行器均未改变。
  四仿真稳定运行；33+21学习模型闭环、RL适配、最终24条件及投稿证据仍未完成。

## 2026-10-03 — 加强神经baseline与累计动作偏差诊断

- 开工沿用已核验main d08dc8f23a0b5e9bbff2bed66e489620333d9052、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  d08完整Git归档SHA03945be24408f486f792d36d460a05f4de434c5ca69467906f41ded057f56cf2已传Spark，source/<SHA>/3117文件内容/大小/模式核验。
- 原同特征网络验证均选初始化，不能据此断言ESN结构优势。先登记再本地运行48个小学习率拟合（单CPU/3GiB）：
  matched取1e-6/1e-5，ordinary取1e-4/3e-4；每个4千更新，数据/宽度/损失和3seed不变。
  原始＋新增合计每普通/同特征子族每seed6候选，合并MLP/RNN仍仅12≤cap24；ESN候选预算未扩大。
- 按跨3seed平均整身份验证动作MSE择一个共同学习率，保留全部seed，不看闭环/最终条件。
  ordinary MLP点/积分误差下降23.91%/24.59%，ordinary RNN下降36.42%/27.41%；matched RNN下降1.62%/.94%。
  matched MLP积分组继续用原学习率；其余7组共21新模型登记8开发身份168回合，未把这些离线改进当任务成功。
- 新独立回放诊断完整重现教师动作filter和实际记录，覆盖33模型×6验证身份。ESN点/积分版本的
  残余速度差累积末值范数均值约98.0/87.8mm；是固定teacher观测下的开放回放代理，不是真实位置误差或物理结果。
  当前仍须等待闭环结果再确定下一步ESN机制，不把该代理当论文主结果。
- 新增零让位参考接口：相同规划/反馈WBC、7D零动作、同世界与gate；不是开环机械臂。已编译，尚待物理执行。
  `sii-r72-additional-development-v1`等待原统一开发/经典确认结束，然后8个名义参考＋168个神经复核回合。
  与3条RL训练共享4个flock槽位；评估每回合释放，允许ESN后续开发插入。原稳定四队列未修改或重启。
- 服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `local_neural_refinement_archive_v1/`含全部48拟合/源码及`replay_drift_v1`；包两端SHA
  97a39b953bfbe4b90f7aab28d82b4f98c14b4f8934c0827c5d3846d2f84c04fa，逐权重/训练记录/实际源码/数据hash核验。
  选择文件`NEURAL_LR_SELECTION.json` SHA dc5af909d1918f41a9b60e98dd39d0f3c0a26ac30cbd3ec9d9e46827359bcd34。
  后续源码相邻`research72_20261003_1149_development_runtime_v4/`，RLruntime_v3加新overlay
  1399f47d891ef90b2d6e777e4119fe8c0a5fc9319b8106a2c014a296c18d7b5d两端一致；base d08dc8f＋本批改动。
- 新增初始SOURCE标签澄清：teacher队列ENV继承了旧282433d标签，与协议base33f4380不同；
  实际源以已核验runtime tar及每回合source hashes为准，四独立审计已通过。澄清同时存Git和本轮根，未篡改原日志。
- 全部新脚本编译/diff检查通过；本轮拟合和离线诊断完成，闭环队列运行/等待中。24最终条件仍封存，未获得新最终优越性结论。

## 2026-10-03 — RL嵌套checkpoint修复、边界续跑与有限训练登记

- main45662c03ca40269f08e183fa6e814a900f026aca已推送核对，baseline仍ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
  已提交源码在`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/45662c03ca40269f08e183fa6e814a900f026aca/`，
  Git归档SHA b8eed5e8612ddfdf1e0569c9b71080d929aff11e6d724a6c6918276b33ef44d2，3111文件内容/大小/模式核验通过。
- 新RL适配开训前发现hash清单遗漏嵌套模型/优化器文件；修为递归完整清单，拒绝缺组件和symlink，评估要求精确文件集合。
  原生Spark无物理回归通过：5D与7D分别比较112个状态数组，保存/恢复后三次动作及优化更新逐值一致，
  replay内容/采样RNG一致。每模型71个原agent文件均覆盖；不将该工程权重当训练baseline，0新增物理步。
- 新增显式完整回合边界续跑，恢复优化器/归一化/actor RNG、replay/RNG、探索RNG、条件顺序与累计计数。
  只恢复已完整结束的段到新目录，不自动覆盖或重试中断回合。实际物理分段端到端验证尚待首个训练段。
- 登记15模型（RL导纳/阻抗/VMC、direct metric/office_task，各3seed），各最多80000累计步。
  初始5500步段不改变总学习率计划；续跑不清回放、不重复计曝光。参数中心沿事先规则从经典开发确认中选择，方程/范围不变。
  `sii-r72-rl-office-adaptation-v1`正在等待统一开发与经典确认，未开始RL物理训练，不创建定时任务。
- 新共享4槽位flock，6个竞争进程工程验证峰值4且全部释放；新RL限3队列、每队列3GiB/CPUQuota100%，
  为ESN后续开发留容量。检测到未使用锁的旧仿真时等待，不终止或热改稳定作业。现有筛选20/96完成（非最终统计）。
- 本轮根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`：
  `rl_checkpoint_probe_v2/`、`rl_office_adaptation_v1/SPECIFICATION.json`及对应Git小证据可核验。
  源在相邻`research72_20261003_1149_rl_runtime_v3/`，由已归档development_v3加三层overlay组成，
  SHA依次a7b674ba3e640aa512e59bb618efcb02ceb79204bc96559c7d18981c460b753b、
  c5b697572199b6895a80e07b5c3422ebcdcafbed8d3706776d50250824a70f42、
  685ad0d2bae2f002f56646ef013b2d36a0104c5ec27088107107e421e60ae0a1，两端均核验；base45662c0＋未提交改动，非干净commit运行。
- 编译/diff检查通过。24最终条件仍封存；RL学习效果、全部模型闭环对比、最终审计和投稿结果仍未完成。

## 2026-10-03 — 真实数据与33模型拟合完成，启动统一开发比较

- 本轮开工实时核对main fb484272f42e2e89fc54bfbec839f9d1b7d50900、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  短暂GitHub延迟后再次fetch/ls-remote成功，无新分支更新。原72小时协议和最终封存不变。
- 48个teacher全部完成并独立审计，44 task/28 strict；训练32为29/18，离线验证8为7/6，开发8为8/4。
  导出18训练＋6验证实际示范、33000帧，记录请求/过滤/执行量及原始source/seed/hash。全部失败在账本中。
- 训练身份诊断发现18个strict示范仅2个柱接触；12个穿透失败的最差对是pillar/link7。
  这是数据覆盖和接触速度关联，未证明失败不可避免；不将接触真值送actor或伪造示范。
- 本地1线程/3GiB完成33模型：3seed，128宽度纯ESN点/积分读出、重训无记忆、普通/同特征MLP/RNN两损失。
  同特征网络均选择初始权重，验证未获梯度收益；保留此结果继续诊断。离线误差不当闭环成功。
  全部模型登记8开发条件264回合，不按拟合优劣筛掉方法；按跨seed汇总选择损失，禁止择幸运seed。
- RL在线接口已知train_000完整1375步/55秒重放：观测/状态/动作/全部物理子步数组和task/strict/三指标精确相同。
  这是接口工程核验，未开始新RL训练。新增RL prior文件与训练配置hash核对，调参控制律不改；新增先验路径尚待训练验证。
- 增强teacher、导纳、阻抗、VMC各12候选于13:44UTC启动96回合筛选；采样与排序事先登记。
  有限串行服务等待此批完成，依次执行264学习回合及8候选×8条件确认；最多4仿真，各1线程3GiB。
  未创建定时任务；不重启稳定作业，不改环境/gate/执行器/actor契约，最终24条件未读取。
- 服务器根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
  模型归档 `local_learning_archive_v1/learning_v1/`：tar两端SHA 197bc0a5f7c363832a78ddb93dbd73cad7ff793c625eb2e6e19054795360f95d，
  全33权重/训练记录/实际source/数据谱系核验。保留真实本地计算路径，不冒充服务器训练。
  运行源在相邻`research72_20261003_1149_development_runtime_v2/`及`..._v3/`，base fb48427＋本批overlay；
  v2包SHA 850606455d85b9265c518f9408d88d3b02ce8764435410f0d56691f4798a4752，v3新增脚本包SHA
  7cbaaf0da92f23180e8e2e9de5be094c55ceb2e5ef83083a978eeaf5e6254f75，两端一致；不是干净commit执行。
- 新增登记/选择/训练接触诊断/有限后续脚本；编译、diff检查和实际登记核验通过。小证据在
  `code/mujoco_6d_vmc_benchmark/docs/evidence/research72_20261003/`。已完成数据/拟合/接口；运行中开发；未完成新RL、留出、最终论文比较。

## 2026-10-03 — 同真实数据学习机制与办公RL适配接口准备

- 72小时窗口继续，最近已核验teacher28/48完整，25 task、15 strict。四稳定队列保持运行，
  不按中间结果重采样；最终封存24条件未读取。main已发布659672d，baseline仍ebb0e1e，未合并分支。
- 新增真实示范导出器：逐身份原task/strict/55s资格、完整失败账本、训练/离线验证分割，
  逐项核验请求/过滤/执行action链及source/trace。开发与最终历史不能进入训练数据。
  修正旧训练脚本把episode<48一律叫合成轨迹的统计假设，新增显式physical_execution掩码，旧默认兼容。
- 纯ESN新增受约束线性读出的误差差分/16步积分目标，保持固定储备池、零负载平衡和相同本体字段。
  MLP/RNN同时获得积分损失选择；新增覆盖3seed、合计33模型的顺序训练计划（含记忆清空重新训练、普通与同特征网络），
  宽度128但实际参数/成本不同明确披露。尚未在新数据开训，不把离线fit当任务成功。
- 本地单线程3GiB旧训练数据工程回归完成，12个新读出候选/导出回放/输入隔离/零平衡通过；
  该回归只验证实现，非新闭环实验或新盲测。checkpoint SHA dd040d112eb1b53663546aa0bca602264ef54a64710ae5640118d627d8f01936。
  原生执行本机airpig，归档到本轮服务器根`engineering_local_v1/outputs/research72_engineering_20261003/temporal_readout/`；
  tar两端SHA 1c68737d7eb98afdd4b231cc17e8f0c8eb03b0343f231ceeaaf95694bce3df77，解包checkpoint hash一致。
- 已实现同v6原生RL IPC、原官方SimbaV2办公从零训练、冻结归一化评估、有限开发队列和依赖准备服务。
  baseline奖励原公式沿用，平滑项显式改用共同filter之后action；训练专用potential不进入actor。
  这些新增物理接口尚待实际完全重放验证；不宣称RL已开训或通过。
- 新准备源在 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149_learning_runtime_v2/`，
  base659672d＋本轮overlay；tar两端SHA deb7e5c546cab79d0776d1102e9205d1ff2f2c39b4df6889c9e6d881dca5e7d3。
  `sii-r72-prepare-learning-20261003-v2`等待collector完成后导出数据和单回合RL重放，不提前增加仿真并发。
  v1仅空闲等待器因原生环境无torch而替换；不安装额外框架、不动稳定物理作业，保留版本与替换记录。
- 上次已提交完整源码source/659672d9b463b98b3290d461f7bfe6b8901ea572逐文件核验3085项通过。
  本批编译/diff检查、33任务依赖顺序检查通过；最终学习/公平比较/新留出/论文证据仍未完成。

## 2026-10-03 — 新72小时研究登记与真实teacher采集启动

- 用户授权假期3–4天持续自主研究，保守窗口10-03 11:30至10-06 11:30UTC，含准备时间；
  不沿用旧截止、不建定时任务。新增固定GitHub入口 `RESEARCH_STATUS.md`，root README链接。
  开工实时核对main `33f438075649508ceb8f84479880d5d622f4eb4f`、baseline
  `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`；工作树干净、无活动仿真，历史停止作业未动。
- 新协议先登记32训练/8离线验证/8开发身份，同原扰动范围、同v6几何与gate、正式dt5e-5；
  另生成24最终身份并封存，仅记录hash。旧最终条件不作为新盲测或训练轨迹。
  新增3脚本：protocol/role-aware worker/可恢复teacher队列，源码编译与diff检查通过。
- 11:49UTC实际启动48回合增强35mm VMC采集：4顺序队列、各1线程/MemoryMax3GiB/Swap0。
  原worker执行和审计不改；保存角色、协议hash、action全链、原始物理与失败。
  所有完整task/strict合格历史供ESN/MLP/RNN共享；失败留在采集账本，不冒充示范。
- 服务器原生共享根 `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`；
  实际源在相邻`research72_20261003_1149_runtime/`，base33f4380＋3新脚本，运行时各queue另存hash清单。
  初始源tar两端SHA一致 `0c43441298a6a68dac2d25f1578d3ee87ebd49c2c88cd0282a033e78aea4353d`；
  协议SHA `5457d85726e2a88067e153464b7e50dbc9fcd173b89a9fc5da2da096c0891732`，公开副本在
  `code/mujoco_6d_vmc_benchmark/docs/evidence/research72_20261003/`，未下载封存条件。
- 已完成协议/启动核验；运行中真实teacher；未完成新学习、经典/RL适配、新留出与论文证据。
  预算上限和逐阶段登记不等于已执行或各方法成本相同；不预设ESN获胜，不承诺真机/录用。

## 2026-10-03 — 26模型同一正式测试场景全部实际重跑完成

- 用户质疑0/0与是否统一测试后，新授权有限26模型×1固定v6锚点、正式dt5e-5实际重跑；
  旧0/0仅为两个成功计数（各分母4），不是未测试。原12小时预算/结果不改，新协议于10:48:23UTC登记。
  开工核对main c2bbc79de083564b6107fbe200ab2ecf10bb3207、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6。
- 26/26完整55秒，无重训、无换权重、无环境/gate更改、无开发资格筛选、无自动重试。
  5模型task/strict均通过：增强VMC teacher、普通RNN两seed、同特征RNN seed1、无记忆重训。
  两ESN均失败：seed1掉块；seed2最终XY28.19mm超原25mm。三RL调参停carry、四RL action停approach。
  21失败末态13 carry/4 approach/4 retreat；不能把阶段名当放置成功。明确任务/严格两列是/否。
- 各queue独立子步三指标、执行器、action/filter、源/权重审计及共同世界/初态核验通过；
  26条最终放置独立重建、全任务接触覆盖和失败征象汇总完成。7条旧formal重测的轨迹hash与三指标完全相同。
  每模型1条已知锚点，不是成功率/泛化估计；RL训练曝光不同，失败不推广为RL算法族不适用。
- 新增有限执行/报告脚本 `tools/run_all_methods_formal_20261003.py`、`tools/report_all_methods_formal_20261003.py`；
  归档校验工具允许显式指定研究目录名，默认原研究不变。源码编译、diff检查和实际全量执行审计通过。
  入口 `code/mujoco_6d_vmc_benchmark/docs/evidence/all_methods_formal_20261003/report/MATRIX.md`，
  同目录JSON含全26回合；上级有协议、共同配置、4批审计、放置审计与双遍核验收据。
- 服务器原生执行/共享根：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/all_methods_formal_20261003_104728/`。
  基础源码c2bbc79＋两个新脚本快照在相邻`all_methods_formal_20261003_104728_runtime/`及各queue/source。
  最多4并发、1线程、各3GiB/Swap0。11:28:35UTC双遍核验2787文件/3826668265字节；
  清单在相邻`all_methods_formal_20261003_104728_integrity/NATIVE_INTEGRITY.json`，SHA
  `e0869790eb167394cb88a7ba5bc2953d5c830a6fe012141e3b37ef1ae8adaa7f`；174下载证据逐项hash一致。
  本轮无运行中仿真；不修改旧数据，不把新增结果混入原四条件或随机组。
- 用户随后授权约3–4天自主持续研究、定期GitHub更新，目标公平RAL级证据；按72小时新窗口规划，
  先解决ESN放置稳定性并补强同训练条件baseline，另设新模型冻结和留出验证，不预设ESN必胜。

## 2026-10-03 — 全部26方法统一柔顺性矩阵（含RL调参与RL action）

- 应用户要求，对既有冻结v6四条件104个完整55秒回合统一制表；未重训、重跑、改环境或gate。
  开工实时核对main `965be4b04f157eeece21f182ce2fab62fe0ef128`、baseline
  `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`及双方日志/AGENTS；三个原研究协调服务inactive。
- 26行包括2纯ESN、teacher、全部MLP/RNN/无记忆、3个RL调参、4个RL action、7经典及zero。
  全回合（包括失败）中位数统一列RMSE/峰矩/峰速、球峰力、人手/杆/桌角P95力；补充积分、时长、
  恢复观察/删失、全任务再接触。显式接触分母，无接触NA；JSON保存范围和全部104条来源/失败记录。
- ESN主组task为1/4、3/4，strict1/4、2/4；七RL均task0/4。ESN并非各项力最低：RL调导纳
  人手/杆P95为14.5/7.2N，ESN为22.1/19.2及18.7/22.4N。RL与ESN无共同strict回合，
  不能将全回合描述性差异解释成同等完成任务时的柔顺优势；历史训练曝光不等。正式步长ESN失败仍保留。
- 新增标准库复算脚本 `code/mujoco_6d_vmc_benchmark/tools/build_unified_compliance_matrix_20261003.py`；
  入口 `code/mujoco_6d_vmc_benchmark/docs/evidence/unified_compliance_20261003/MATRIX.md`，
  同目录MATRIX.json与服务器核验收据。核对原报告/锁/窗口hash、26方法×4条件全覆盖、trace/接触字段，
  独立检查中位数与成功计数；编译/diff检查通过。本轮只做本地后处理，无运行中实验或新增训练。
- 已核验服务器共享根：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/unified_compliance_20261003_1034/`，
  内含tools脚本及docs/evidence同路径矩阵；3文件内容/大小/权限核验通过，归档SHA256
  `2eda7f13b25e409eae53900c353fea1e65abb6aedc36cb357831a91b4e397a09`。
  MATRIX.json SHA `de918f795f65f9d06a254fb00303faa948186f78c92534e47792a5480f8251f0`。
  原物理归档不变；已提交源码按最终commit另存服务器source/<commit>，不覆盖运行快照。

## 2026-10-03 — 十二小时预算内同场景研究收尾：局部ESN优势，未证明全面最好

- 授权窗口2026-10-02 14:11:36至次日02:11:36UTC，连续任务，无定时任务。22:24UTC前实验、
  独立审计、媒体及服务器整体核验已完成；不为空耗剩余预算重新训练。采用baseline事前发布的
  office-validation-v6与其原生Spark运行库；几何/目标/gate/本体输入/执行器不变，未将旧v5混排。
- 26锁定模型×4条件104回合、7合格模型×8随机条件56回合、7 formal dt5e-5均完整55秒。
  主比较ESN两seed task/strict为1/1和3/2（分母4）；同特征RNN3/2、4/2，普通RNN4/2、2/1，
  同特征MLP2/2、无记忆3/2、增强teacher3/2。七经典及七冻结RL各task0/4，但历史训练曝光不等。
- 随机补充ESN6/4、5/4（分母8），同特征RNN6/1、3/2；teacher7/5、无记忆5/5、调参原VMC0/0。
  非合格方法未测，不能计失败。formal两个ESN均放置失败，teacher/无记忆/RNN seed1通过。
  同seed共同strict仅三个条件：ESN较快完成，但杆p95力均更高；不能换权重宣称柔顺全面最好。
- 全部193选定记录（包含26开发）独立复算接触覆盖；192完整回合末态重建通过，1条开发abort
  保留16.36秒。10学习模型53500输入精确回放、1375帧输入边界干预差0；全子步/动作/filter/
  幅值与变化率/source/config/checkpoint检查通过。新增七对步长分叉、失败征象及20ms完成时间
  插值勘误审计，不改变物理/门槛/成功标签。47完整三机位MP4/GIF＋2上下对比视频解码/hash通过。
- 开发本机82＋原生112回合，另7跨库兼容诊断，新增最终167回合；全部原始失败保留。
  主35mm数据只有2实际teacher历史、2反事实学生历史和48合成负载序列，不宣称3000成功场景。
  128宽度不等于相同容量/训练预算；无记忆成功不支持记忆必要性。持续杆推主动滑脱仍未证明。
- 新增纯固定储备池/受约束读出训练、同特征MLP/RNN控制、固定模型/候选队列、统一物理接触指标、
  原生复现、配置/动作/状态/末态审计、完整媒体和归档工具；保留默认旧契约行为。
  编译、diff检查与实际全量审计通过。结果/方法/协议、联合进度、周报、两处README和小型证据已更新。
- 开工及22:29UTC收尾核对远端main `282433d339feef66b0334f223f82a6eea96b040b`、baseline
  `ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6`，均未前进；按sii-research-sync/AGENTS执行，
  未合并baseline分支，未动历史暂停进程。本任务无运行中训练/仿真/后处理；未实现稳定泛化/正式步长ESN。
- 已核验服务器主根：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_rl_20261002_141136/`。
  双遍hash **40094项/32802129515字节**，清单位于同父目录
  `paper_esn_12h_native_integrity_20261003_final/NATIVE_INTEGRITY.json`，SHA256
  `f2bd06e2a7a1b4e26c85eaaa0a6e96061da88b729232c8775a2a58317579b3e8`。本机606份下载/报告/视频
  对该清单复核，24份独立审计报告hash与终版汇总一致；大文件不提交Git。
  实际物理源在各批次source及overlay，后处理在`final_delivery_runtime/`；已提交整理源码
  另按完整提交SHA归档服务器`/home/arm1/sii_shared/SII_compliance/source/`，不覆盖历史run。
- 验收入口：`code/mujoco_6d_vmc_benchmark/docs/PAPER_ESN_12H_RESULTS_20261003.md`；
  小型完整结果、图表、视频索引、核验收据在相邻`docs/evidence/paper_esn_12h_20261003/`。

## 2026-10-03 — 十二小时同场景研究过程记录（最终状态以上节为准）

- 21:41UTC：104四设计条件和7 formal已全部完成、独立审计及同配置核验通过。ESN两seed
  主比较strict1/4、2/4，RNN/MLP/无记忆也有2/4，不支持ESN全面最好。formal两个ESN任务失败，
  teacher/无记忆/同特征RNN seed1通过；不改变门槛、模型或既定随机资格。56随机回合已开始。
  新结果报告记录真实释放/掉落失败与数值敏感性；其余设计条件14条完整三机位视频和一个短abort视频已核验。

- 21:09UTC：主验证81/104条已完成，稳定队列不重启。新增整批最终放置重建、接触覆盖审计与
  完整三机位交付流水线，等待已启动验证结束，不派发新训练/仿真。固定展示h1全部26模型与formal全部7模型，
  abort保持真实时长。开发图发现指令窗口后的人体系再接触，补充全任务/窗口外统计，原指标与gate不改。
  准确注明放置13个25Hz有效样本计.52s、时间戳跨度.48s，不冒称连续子步稳定证明。
  10模型各1375帧输入边界干预的动作/隐藏状态最大差0；原生112条开发全量目录已完成（另列本机82条及7条库兼容诊断）。
  源快照final_delivery_source_20261003_0505.tar.gz SHA 2d7ecfc244d0449722a1ba928900492d7487f7eca326580956ce22ba93738c21；
  已核验于主执行根。一次未完成源码传输的失败解包被单独保留，未用于运行；替代小型源码包先完成传输/hash核验再解包。
  20:29UTC复查远端main 282433d339feef66b0334f223f82a6eea96b040b、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6未变。

- 20:09UTC：38原生经典候选与独立审计完成，26最终模型正式锁定，lock SHA
  755974da1d4d5a3fb1aa24aa779cf91ede2e83768de2b9dd21089de863166701；四条件104回合开始。
  7个开发strict合格模型另做formal；在最终回合前登记8随机条件补充验证，不重训，不按最终结果改资格。
  10模型学习回放各53500输入精确一致；本机82回合审计索引、6完整开发视频和537项baseline依赖已核验共享。
  仍运行中，最终结果未定；服务器详细路径、manifest与源hash见联合进度20:09记录。

- 19:27UTC：同特征RNN两seed独立审计后均开发strict成功，原VMC04亦strict成功，不能宣称ESN独占。
  新训练已结束，新增最终选型规格/冻结工具及一次性连续验证协调器；先完成38条经典候选审计，
  再锁26模型×4共同条件，开发strict合格者另做正式步长。未根据测试结果调参，尚未启动最终条件。
  新增完整表格/锁定配置复核/成功矩阵报告工具及三机位全程媒体队列。学习证据69组/3710文件
  已共享核验至服务器runs/main/paper_esn_12h_learning_complete_20261002_141136/evidence，manifest
  f0229abc25df6042a339035671f6a65cf5e069974ba88b432a028b0e72645e90；经典本机剩余29条亦已归档。
  19:08UTC远端main/baseline SHA与开工相同，无合并baseline代码或改环境。

- 18:45UTC：35mm teacher组两个固定ESN seed均在原生v6锚点task/strict通过；普通MLP/RNN各0/2，
  无记忆重新训练亦成功，不能声称记忆必要。新增共享DAgger、长反传RNN、同特征MLP/RNN机制对照；
  DAgger ESN与长RNN的放置/穿透失败均保留。已完成成功回合真实松爪/桌面支撑重建与两段55秒
  三机位媒体核验。经典38候选全量原生复评中；最后四条件未解封，终版/正式步长与最终结论未完成。
  新增显式argv冻结离线队列，修正数据追加的context契约继承和视频场景标签，训练支持float64及
  可登记长反传，旧默认行为不变。完整学习证据服务器paper_esn_12h_learning_evidence_1815_20261002_141136/evidence
  已核验639文件/100781194字节，manifest f6a56266094c5fb7c89ff6adec32b10bad100ff82ef087ea1cd77a078f799b48。

- 17:56UTC进展：原baseline统一环境首条纯128固定储备池/线性读出ESN task/strict成功，
  41.476mm/50.136Nm/.357187m/s、外穿透.125753mm、终点XY7.929mm；目前只属开发单回合。
  同组条件漏率失败、可训练漏率放置成功但穿透超限，均保留。14历史方法逐数组精确复现与15条
  共同运行环境核验通过；恢复VMC六条中三条成功。新35mm数据组/同宽MLP/RNN继续。
  成功run在服务器paper_esn_12h_rl_20261002_141136/recovery05_learned_native/recovery05_esn_fixed；
  末态/完整接触审计、终版锁定及四条件仍未完成，不能宣称ESN最优。17:50UTC复核两远端SHA未变。

- 开工实时核对main282433d339feef66b0334f223f82a6eea96b040b、baseline ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6；
  按sii-research-sync读取两分支日志/AGENTS。授权2026-10-02 14:11:36至次日02:11:36UTC，无定时任务。
- 锁定baseline既有office-validation-v6，原始VMC本机单条task/strict成功；128单元纯ESN积分训练版
  末帧放置到XY12.557mm，但保持仅.04s不足.5s，仍失败。新增统一接触/恢复/动作与原生子步审计，
  不改场景/gate/actor输入/执行器，不挑失败，不预设ESN最好。MLP/RNN同数据学习对照和经典固定预算继续。
- 纠正RL运行解释器：原GPU环境七条复跑与历史结果一致；先前不同JAX环境七条另存兼容性诊断。
  所有原生RL均失败；非RL锚点正在同解释器核验。首次新源码缺少outputs锁目录的预启动失败保留，
  只补运行目录后恢复，批处理代码增加目录创建。源码快照独立保存，无热改稳定作业。
- 已核验新增经典九条782文件/973560594字节：
  arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_classical_slice1_20261002_141136/evidence/，
  manifest SHA b04f3ec8db8e16e470a98e540c4d77d87c1ec1e7176f7326d943393613577d66。
  先前initial/phase2/paired_learned亦已归档；最新学习产物仍有仅本地待同步部分。
- 进行中：teacher恢复/平滑、学生读出学习、原环境统一锚点。未完成：最终模型锁定、正式步长、四条件
  配对泛化、最终媒体与完整共享审计。详细协议/状态见benchmark docs/PAPER_ESN_12H_PROTOCOL_20261002.md
  和ESN_VMC_JOINT_PROGRESS_20260927.md；收尾再更新最终结论并提交推送main。

## 2026-10-02 — 固定teacher数据下纯MLP/可训练RNN替换ESN

- 按用户新授权，完成两套既有teacher数据×MLP/Elman RNN×两个seed，共8模型、8条55秒开发
  回合；全部task/strict失败，未修改tool-contact-v5环境、b092662a模型、规划/WBC/gate/执行器。
  本轮是独立8模型协议，不延长已结束四小时预算，无定时任务。
- 原VMC组MLP/RNN两seed平均RMSE39.060/29.307mm、峰矩38.470/38.933Nm、峰速.404145/.386349m/s，
  均卡carry；原VMC MLP seed2外穿透.205319mm超限。恢复41组未显示稳定优势：RNN seed1最终
  XY101.545mm，seed2全程approach，较低RMSE/峰矩不能当作进步；MLP seed2最终XY59.899mm仍未放置。
- 新增office_mlp_rnn_20261002 actor、训练/固定8回合runner/独立模型审计；loader添加契约、
  evaluator仅允许RNN类型。128隐藏宽度、2400更新、同data/seed/序列曝光，RNN学习循环矩阵。
  四对RNN离线拟合更好但闭环均失败；参数量不相等，旧ESN另有128非线性读出，不声称结构优势。
- 8条550000子步指标、动作/filter、4条RNN状态、8份独立接触sidecar、执行器幅值/4ms变化率及
  source/data/config/checkpoint/trace hash审计通过；4组训练曝光完全一致。导出Torch/NumPy最大差≤3.76e-7。
  原始teacher失败标签/trace hash复核；两条55秒/1375帧/25fps三机位视频完整解码并目视检查。
- 初次资产路径缺失在物理启动前失败，记录保留、原MLP checkpoint核验复用，没有重训或丢弃回合。
  报告工具增加显式物理batch选择，避免把归档预启动协调记录当待完成物理回合；初次诊断仍保留。
  编译与diff检查通过。专题报告/协议、联合进度、周报、两处README和小型审计收据同步。
- 按sii-research-sync开工核对main `14820fac7141fa8779aa56b5ae0ba595ee2ee0a5`、baseline
  `133a0b4306f70dd703629bf1227961899d6abcfd`；收工main未前进，baseline更新至
  `d00b995711c68a2e42a2ffd4ec2813758849aff3`，历史ESN/RL对照更新已读，未合并分支或干预独立作业。
- 已核验680项、747,693,072字节证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/mlp_rnn_replacement_20261002_131535/evidence/`。
  manifest SHA256 `8a5209a9432138459175202d7a6452125bfc1c1bd7082aca0943256e5743931d`。
  运行源码在该根目录`evaluations/source/`、后处理源码`postprocess_source/`；本轮Git源码另外
  按完整发布commit SHA归档服务器`/home/arm1/sii_shared/SII_compliance/source/`。
  小型证据入口`code/mujoco_6d_vmc_benchmark/docs/evidence/mlp_rnn_replacement_20261002/`。
- 完整结果和视频索引：`code/mujoco_6d_vmc_benchmark/docs/MLP_RNN_REPLACEMENT_REPORT_20261002.md`。
  已完成本轮比较/审计/共享，无运行中实验；未完成成功teacher、放置/strict、formal步长与跨条件泛化。

## 2026-10-02 — 四小时固定环境teacher/纯ESN联合优化及完整失败审计

- 授权09:01:55–13:01:55UTC，连续前台任务，无定时任务。预登记48条teacher/名义候选、
  24条纯ESN回合均完成55秒，task/strict均0；额度用完后收尾，不为耗满时间空转。
  环境tool-contact-v5、MJB b092662a、规划/WBC/gate/公共输入与执行器限制均未改。
- 优化teacher弹簧/读出、负载耦合与相对参考恢复记忆；纯ESN增加多时间尺度、负载×运动/
  误差派生输入、context调制leak、失败学生历史反事实重标注及积分动作损失。
  仍无新成功teacher数据。原VMC蒸馏ESN30.058mm/39.210Nm/.370185m/s、穿透.111707mm，
  但卡carry；推进最远学生integral41为76.718mm/38.129Nm/.398990m/s、XY76.918mm，仍失败。
- teacher47最终XY49.157mm，但没有接触未知凸边，后段卡柱子，推杆连续受力8.8172秒，
  不能把更近的终点当作滑脱成功。DAgger漂移损失配对RMSE153.759→125.970mm、峰矩/峰速
  略升且均失败；零初态平衡不足以保证已有历史卸载，离线干预与物理清空记忆结果分别保存。
- 13个有效学习模型及1个拒绝部署的旧标签模型、8组读出和最后3条gain/记忆干预全部保留。
  本模型128储备池另加128非线性读出；没有MLP新实验，不声称严格参数/FLOP匹配或ESN优势。
  全72条三指标、动作/状态、公共filter、幅值/4ms指令变化率及源/配置/hash审计通过；
  33条独立接触sidecar复算一致，6条穿透超限保留，5组配对数据/seed/预算一致性核验通过。
- 新工具包括冻结批次runner、teacher worker、学习/物理/配对/记忆/视频审计和归档发布；
  teacher与学生checkpoint重放验证、编译与diff检查通过。三机位编码固定单线程，
  两条完整55秒1375帧MP4/GIF已生成并验证，视频明确标为失败。
- 按sii-research-sync开工读取main `7cd5f4b7ac0a3056df76ac62bc690ded0724b104`及baseline
  `e564e09a691293802ec76c237d717b202d592e85`；收工main未前进，baseline更新至
  `a788be958486b5b24bc546737d44f690763521ba`并已读日志。未改baseline作业/分支或独立FLASK环境。
- 已核验5050项、5,951,412,066字节原始数据及运行源码：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_esn_four_hour_20261002_090155/evidence/`。
  manifest SHA256 `20731dc23f9924cf2247a2c7d62db12a7f75602ddae8d8e7ae3a059f5f6de98f`。
  代码在其中各批次`source/`及逐回合/训练overlay，例如`final_intent/source/`与
  `esn_dagger_pair/source/`；base commit不冒充干净源码。本次发布源码另按完整commit SHA
  归档同一服务器`/home/arm1/sii_shared/SII_compliance/source/`，不覆盖旧运行。
- 完整结果/限制/媒体入口：`code/mujoco_6d_vmc_benchmark/docs/VMC_ESN_FOUR_HOUR_REPORT_20261002.md`；
  原预登记协议、联合进度、周报、两处README及小型归档收据已同步。
  已完成本轮预算内实验和审计共享，无运行中任务；未完成稳定放置/strict、成功teacher数据、
  formal dt=5e-5及跨条件泛化。

## 2026-10-02 — 当前环境及三机位完整交接，补充跨机器复跑入口

- 用户认可当前交互展示，要求先同步供其他agent接续；本轮未启动仿真/训练，未改变环境、
  机位、gate或权重。按sii-research-sync开工及收工核对远端main
  `03809257e72b612bdc760ada3113e8ddba32c098`、baseline
  `e564e09a691293802ec76c237d717b202d592e85`，未改baseline分支/独立作业。
- 新增`code/mujoco_6d_vmc_benchmark/docs/OFFICE_TOOL_CONTACT_HANDOFF_20261002.md`，
  固定office-tool-contact-v5的坐标/尺寸/时序、公共规划/成功定义/本体输入限制、三机位
  lookat/距离/方位/俯角、25fps原速完整视频和慢放区别、重渲染/复跑命令、共享资产与hash。
  README、接触修正报告、联合进度和周报均加入入口。
- `run_tool_contact_20261002.py`新增`--reference-dir`，可直接使用共享完整回合中的
  summary/checkpoint/TRAINING_COMPLETE；验证完整时长和权重hash，拒绝短探针参考。
  无仿真验证：共享参考与原p010权重及所有非覆盖参数一致，短球对照被拒绝。
- 已核验原物理源码：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/03809257e72b612bdc760ada3113e8ddba32c098/`。
  已核验原证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/`，
  manifest SHA256 `936b6af1988b65bfce16dcf6c4fa44b2b1bf8460913b59aff2accb6496c6221f`。
  本次提交源码另按完整SHA归档到同一服务器source目录，不覆盖历史产物。
- 已完成：环境与拍摄交接、可移植参考入口。运行中：本任务无新增作业。
  未完成：完整放置/strict、正式步长和跨条件验证；全程仍49.428mm/45.880Nm/.370425m/s、
  最大穿透.653202mm、task/strict=false，不把画面认可当成功。VMC新采集/ESN新学习待后续推进。

## 2026-10-02 — 球撞响应与棍推掌部修正；保持期滑脱已观察，整场仍失败

- 用户要求先修物理交互，暂缓ESN算法修复。本轮未重训、未改WBC/actor输入/权重/执行器限制。
  开工/收工核对main `b75ef8e177a6bd149786b74279704ea8caaa0b92`、baseline
  `e564e09a691293802ec76c237d717b202d592e85`；不影响baseline四特化场景运行。
- 独立tool-contact-v5：1kg/半径60mm球正撞掌部；棍升到.64m、改从对侧推掌部、缩短杆身，
  固定保持到23.5秒，消除新杆身与人体/物块接触。旧默认环境不变，新旧分数不得混算。
- 球零入射速度反事实确认13.845mm额外手部偏移。棍仅接触hand，在仍伸出时15.1201–19.1801秒
  已无受力接触；随后回碰，最长连续接触.1061秒，不能宣称平滑永久滑脱。前28秒穿透.111485mm。
- 55秒开发回合仍task/strict=false，后段原柱子/link7穿透.653202mm；
  RMSE49.428mm、峰矩45.880Nm、峰速.370425m/s。不移柱子/放宽门槛去掩盖失败。
  源码新增延迟球撞日志修复、逐子步接触对象/受力统计、200Hz状态、原速/慢放近景。
  ESN动作/储备池重放误差0；补日志前后28秒状态/动作逐元素一致，公共路径回归检查通过。
- 保留1条入口相交拒绝、3条候选诊断失败、完整v5、28秒遥测复核、3秒球对照。无运行中仿真。
  已核验142项服务器证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/`；
  manifest SHA256 `936b6af1988b65bfce16dcf6c4fa44b2b1bf8460913b59aff2accb6496c6221f`。
  接入/参数/全部失败和媒体见`code/mujoco_6d_vmc_benchmark/docs/TOOL_CONTACT_REPAIR_20261002.md`，
  README/联合进度/周报同步。未完成平滑不回碰、全场安全和最终放置。

## 2026-10-02 — 未建图凸边阻塞任务；统一修复路径接回，旧ESN/MLP尚未解决

- 按用户桌角视频新增独立物理凸边（20×90×70mm），从reset存在、只在先验地图中遗漏，
  不给actor增加感知。保持靠手桌角目标、放置门槛、顺序扰动与执行器限制。
  开工及收工前核对main `f3437ade3a44e52db4a118d5c112e6cabbb48d41`、baseline
  `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`，baseline分支未改。
- 发现并修复公共接回逻辑误把纵向前进计入80mm横向容差。相同虚拟绕行旧版卡14/27，
  修复后27/27并进入下一阶段，终点到达约束保留；几何/IK绕路审计不冒充物理成功。
- v1/v2共8条55秒开发回合完成，每组对应状态/动作数组重跑完全一致。
  名义无新凸边task/strict成功；名义有凸边11.3937–55秒持续接触并失败。
  原ESN/MLP仍在触及新凸边前停carry，均task/strict失败；三指标分别
  26.496mm/37.763Nm/.084326m/s、24.843mm/36.977Nm/.061384m/s。
  无重训；不能声称“加柔顺即可成功”、ESN优势或正式步长通过。
- 子步指标、动作/ESN状态重放、共同规划/阻塞MJB、55秒1375帧MP4/275帧GIF已核验。
  无运行中仿真。未完成：新参考下学生正常推进、接触恢复放置、多条件/正式验证。
- 已逐文件SHA256核验189项共享证据，含实际执行源码快照、权重、轨迹、审计和媒体：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/unexpected_edge_contact_review_20261002_v2/evidence/`。
  `archive_manifest.json` hash：`91dc23cc9d20d8ab4815a2c07164db41d135521d5995774a5441ff9d45bb1544`。
  新报告`code/mujoco_6d_vmc_benchmark/docs/UNEXPECTED_EDGE_CONTACT_TASK_20261002.md`记录
  场景尺寸、命令/权重、成功定义、失败和baseline接入；README/进度/周报同步。

## 2026-10-02 — 靠手桌角新任务与静态路径规划；名义成功，旧ESN仍失败

- 用户授权新目标/成功定义：物块放到靠手桌角并松手稳定即task成功，接触覆盖改为诊断。
  新协议planned-hand-corner-v1，目标[.690,-.310,.545]m；旧协议/结果保留。
  开工main7674ed9、baseline699e317，baseline未改。新增静态A*扫掠规划与IK姿态搜索，
  原竖直姿态不可达，选择-35度；不向ESN加入环境真值，模型几何和执行器限制不改。
- 两条完整55秒/单线程3GiB开发验证完成：同一规划文件hash50f32f7e，零动作名义执行
  成功放置，XY误差10.797mm；原ESN仍停carry，不能把名义成功说成ESN成功。
  ESN三指标43.370mm/38.515Nm/.094228m/s，名义22.767mm/42.020Nm/.068210m/s。
  动作/状态/子步和独立末端放置审计通过；规划绕障与松手边界检查通过，完整GIF/MP4已保存。
- 已核验服务器独立归档：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/planned_hand_corner_pair_20261002_v1/`；
  evidence.tar.gz SHA256=`7b37f3512c95b3f3d5cd0dd0e8546171727e9faec5f8977ef7a8f88f62b4e73e`。
  新协议、旧strict区分、baseline复用与失败分析见
  `code/mujoco_6d_vmc_benchmark/docs/PLANNED_HAND_CORNER_TASK_20261002.md`。
  未完成：新参考下ESN可靠放置；本轮无重训/其他baseline/正式步长，所有作业结束。

## 2026-10-02 — 原ESN权重完成12秒推杆时序评估与全程媒体

- 按用户请求复用上次动图的p=.1 ESN（checkpoint9f4b5a81），只改变推杆时序，未训练。
  开工核对maind43f050、baseline699e317。本机单线程/3GiB、MuJoCo3.11.0完成55秒开发
  评估；task/strict仍false，停load_transfer；RMSE38.708mm、峰矩48.463Nm、峰速
  .094228m/s、外部穿透.122975mm。人手接触4.2813–8.8977秒；推杆/柱子未记录有效接触，
  不把时序分离或低指标冒充成功。动作/储备池重放误差0，550000子步物理指标独立复算通过。
- 全景/末端/柱桌角三视角GIF及MP4完整55秒原速，实测帧数275/1375，已目视核验。
  新单回合启动器保存原参数/源/模型/权重hash、执行和审计；所有作业完成，无新增campaign。
- 已核验服务器归档：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_sequential_r12_media_20261002_v1/`。
  evidence.tar.gz SHA256=`c6938228a27aeb7a6b08d33245d96325fb4ec0cd2274582cfb89cc9a268c1e31`。
  详细结果及源码/媒体地址见`code/mujoco_6d_vmc_benchmark/docs/ESN_SEQUENTIAL_R12_REPLAY_20261002.md`。

## 2026-10-02 — 顺序扰动修复：人手撤回后2秒启动推杆

- 用户授权将combined-v4推杆起点7→12秒，登记独立`sequential-r12-v1`；人手3–10秒、
  推杆12–21.5秒，球2秒及其他物理/任务/gate/actor/执行器设置不变。旧配置与结果保留。
  新共享配置和验证器启动检查拒绝误带旧时序。已有ESN/MLP/baseline权重和参数不需重训。
- 开工实时核对main5dc538b、baseline699e317；未改baseline分支、未重启旧campaign。
  3GiB/单线程的两个80ms检查成功：新旧MJB5eaee4aa及所有轨迹数组一致，权重hash未变；
  全55秒指令检查无重叠。新55秒实际接触/任务/strict尚未评估，不能报告效果改善。
- 已核验共享源码/配置/执行证据：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/office_sequential_r12_check_20261002_v1/`。
  evidence.tar.gz SHA256=`b2d10aa5d0f2d271c3bd514ebad3ad8e46f92d364b50ea744a0aa04811b0008b`。
  接入与未完成项见`code/mujoco_6d_vmc_benchmark/docs/OFFICE_SEQUENTIAL_R12_HANDOFF_20261002.md`。

## 2026-10-02 — current frozen combined-v4 full three-view media

- 按用户请求展示当前最终测试环境，开工核对main38d40c1、baseline699e317；场景未变。
  以最新p=.1 ESN已保存轨迹和MuJoCo3.11.0归档MJB生成全景/末端/柱桌角三视角，
  不重跑物理或训练。仍标注task=false/strict=false及load_transfer停滞，不伪装成功。
- 渲染工具支持显式fps与GIF抽帧，MP4保留1375帧/25fps/55秒原速，GIF275帧/5fps/55秒；
  GIF缩至960×280以限制内存。实测视频/GIF时长与帧数一致，已目视核验终帧。
  本地渲染使用3GiB服务和单线程。短碰撞应优先看25fps MP4，GIF不代表高频物理采样。
- 媒体和输入输出hash已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/current_office_v4_esn_media_20261002_v1/`。
  GIF SHA256=`0c8a370ac63a4d0011df0f646128db93b5be7d89c4c9f81f4b5c67e33a1e7067`；
  MP4=`e92115da80566fb5a3ed6984a1490caa8168c5760ea9b18c4fb0ec40e9227f49`；
  manifest=`9c98c016c435423fab0ee0b59f5373c78c535e286118e681069b1469207fbfdc`。
  对应原始输入仍为temporal_s52_latent_dropout_20261001_v1/p010_eval/esn_combined_v4，
  MJB5eaee4aa未改。自动研究任务保持暂停；本次仅完成媒体展示。

## 2026-10-01 — memory/dropout diagnostics audited; budget conflict closed out

- 开工实时核对main e0c963b、baseline699e317，未修改baseline。固定权重ESN逐次清空历史
  回合完成：task/strict=false，停align，25.213mm/34.820Nm/.076344m/s；没有抓起物块，
  不能把低指标解释成改善。动作与状态按实际reset语义独立重放，最大误差0。
- 同teacher九轨迹、7/2split、seed152/153、160epochs/1120更新与128+128单元预算下，
  完成p=0/.1整段128维特征dropout对照。ESN从lift到load_transfer但仍失败，
  三指标48.971mm/43.600Nm/.116950m/s→44.666mm/47.458Nm/.094228m/s；
  MLP两组task=true，p=.1为46.587mm/44.587Nm/.073259m/s；五条strict均false。
- 五条55s/550000子步/dt1e-4独立审计通过：checkpoint/MJB绑定、有限值、物理指标重算、
  动作/储备池精确重放。p=0权重及原始轨迹与原冻结参考逐字节一致。两dropout组教师身份、
  原始数据hash、seed/epoch/归一化/储备池不变；相同dropout概率不等于相同表征语义。
  全部使用冻结MuJoCo3.11.0/MJB5eaee4aa、真实cgroup3GiB/单线程，无新环境/gate。
- 纠正预算处理：自动化创建05:48:54.070UTC，按创建+8小时保守推算13:48:54.070，
  但前几轮误用唤醒日程16:20作派发授权。未找到独立起点证明延期，晚期诊断不得写作
  原八小时内完成。识别冲突后没有新campaign；已启动末回合15:40:30结束并审计。
  heartbeat已PAUSED、仿真为0；AGENTS新增预算依据规则，原配置/执行记录保持真实，
  新增明确标为事后的BUDGET_RECONCILIATION.json。继续实验需新的明确预算。
- 已核验归档：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_memory_dropout_20261001_v1/evidence.tar.gz`，
  232570508bytes，SHA256 `4ed503552bea79609578040aa4cff344a790bf75051313a183764b8e53820bf5`。
  运行前源码分别为服务器共享根下
  `source/078446e00aa5470ad1bb68caaa1932d35d802c00/repository.tar`（SHA
  `50b0a55ad2a8d2264f88e23733679e3f43101bf685445fc1a3ab72fe1557c84c`）及
  `source/f4422c9b56ef97d1889b774c8d843a1526d4905d/repository.tar`（SHA
  `10e042986438cddf1df85fd1d5679c70d72a9dbb567177a755f4761e1abccc3d`）。
- 完整报告 `code/mujoco_6d_vmc_benchmark/docs/ESN_MEMORY_DROPOUT_DIAGNOSTIC_20261001.md`，
  联合进度/周报/小证据同步。完成了诊断和归档，未完成ESN任务/strict、跨条件泛化和formal；
  不因阶段推进或回放MSE宣称ESN优势。

## 2026-10-01 — register paired sequence-consistent latent dropout

- seed52固定权重清空记忆回合已完成，task/strict=false，停align，未证明清空历史能修复；
  原始失败与精确动作/状态审计保留，结果报告稍后归档。
- 预提交固定p=0与p=.1两组：每组ESN/MLP均160epochs、1120优化步、相同7/2身份留出、
  seed152/153及锁定九条teacher。ESN的128维储备池特征与MLP第一隐藏层128维特征施加
  同概率、整段序列一致的inverted dropout，推理关闭；保留128+128神经元、原输入/gate。
  表征不同，因此不是严格等价结构消融，也不从测试回合挑概率。
- 新训练/评估监督器串行两组，MuJoCo3.11.0、真实3GiB/单线程；每阶段记录执行与hash，
  16:20UTC后不派发新阶段。补全teacher原始文件hash校验、训练运行时/config元数据；
  eval支持显式新checkpoint来源。当前仅注册，未声称已启动或提升。

## 2026-10-01 — register seed52 closed-loop memory intervention

- 开工实时读取main e0c963b与baseline699e317日志；本机/Spark同类评估均空闲。
- 注册一条固定ESN checkpoint的reset_each_observation闭环因果对照，权重、actor输入、
  冻结3.11.0/MJB、scene/gate/执行器限制、seed/55s/dt1e-4保持不变。复用刚完成的
  同条件ESN/MLP作为参考，不重复启动MLP。配置temporal_s52_memory_ablation_20261001.json。
- 守护启动器增加显式方法/记忆消融选项；独立审计按真实记录的记忆语义重放动作和状态。
  本条先提交再运行；这是诊断，不是部署时混合控制、已改进学习或任务成功结论。

## 2026-10-01 — frozen-runtime seed52 pair completed and audited

- 本轮开工核对main d29e504、baseline699e317；运行前注册提交5572a73后，本机服务
  sii-temporal-runtime-s52-20261001于15:12:17–15:15:39UTC串行完成两条，均rc0，
  真实cgroup memory.max=3221225472/单线程。当前无仿真运行，未改baseline或启动训练。
- 同seed52 checkpoint回到冻结MuJoCo3.11.0，两MJB精确匹配5eaee4aa。
  ESN task/strict=false，lift，RMSE/峰矩/峰速/穿透
  48.971mm/43.600Nm/.116950m/s/.131457mm；MLP task=true/strict=false，retreat，
  46.908mm/45.907Nm/.070165m/s/.151728mm。全部55s/550000子步/dt1e-4。
  ESN相对原3.14.0的RMSE降低23.252mm，但失败未解决，不能宣称算法提升。
- 新旧四条独立审计动作/储备池replay最大误差0，三指标复算、模型/checkpoint绑定、
  原参数和源码hash核对通过。错误运行时启动测试在建目录/仿真前拒绝3.14.0。
  初次报告工具Path类型错误已修正，仅重跑只读报告，没有重跑回合。
- ESN末10秒误差中位28.920mm、速度.000860m/s、ready=0；该窗口无输入>12截断、
  无储备池abs>.95饱和。相同输入离线重置历史改变动作RMS .157981，属于读出依赖诊断，
  不是闭环记忆消融成功。下一步聚焦历史状态与持续残差，不改gate或解锁formal。
- 证据已核验：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_frozen_runtime_s52_20261001_v1/evidence.tar.gz`，
  92494783bytes，SHA256 `0b51f23b479282e35343515918ede84e090fde4951259f77e5ac137af36e7c75`。
  运行源码快照：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/5572a733a2fbc97b78201ee586cba188c49d43a3/repository.tar`，
  SHA256 `f5ddd6459b3589404996eb55773a6b2b794d6df37639e378c9890b23d323d87a`。
- 报告 `code/mujoco_6d_vmc_benchmark/docs/ESN_MLP_FROZEN_RUNTIME_PAIR_20261001.md`，
  联合进度/周报/小证据同步。已完成运行时复核与归档；未完成ESN任务/strict稳健成功、
  跨条件泛化和正式步长验证，不把单checkpoint对照当泛化率。

## 2026-10-01 — register frozen-runtime seed52 verification

- 实时查询核对 main d29e504、baseline 699e317并读取对应日志；baseline暂停事项保持不动。
  当前本机/Spark没有运行中的同类评估，未启动重复作业。
- 注册两条串行复核：固定seed52 ESN/MLP checkpoint和原55s/dt1e-4参数，仅恢复冻结
  MuJoCo 3.11.0。启动器检查真实cgroup MemoryMax≤3GiB、单线程、manifest/checkpoint/
  源码hash，并在保存MJB之后、回合执行之前核对5eaee4aa模型hash，失败保留且不重试。
- 配置 temporal_frozen_runtime_diagnostic_20261001.json；工具
  verify_temporal_frozen_runtime_20261001.py。每条保存独立execution/原始轨迹/三指标及
  action/储备池审计；不训练、不改环境/gate/actor/限制，不解锁formal。此条提交在运行前，
  尚无新性能结论；运行记录和服务器归档地址在完成后补充。

## 2026-10-01 — temporal evidence integrity, runtime drift and synchronization repair

- 实时核对 main `ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、baseline
  `699e3171cc5e87e946a79f23f6a49d5e5ba1c1b0`；授权外部网络下 GitHub/Spark 均可达，
  先前失败至少部分为沙箱限制，不能继续称服务器不可达。未合并或操作 baseline 作业。
- 最新六条回合补强审计通过：checkpoint/模型元数据绑定、actor/状态/物理数值有限、
  550000 子步与三指标复算、精确 action/reservoir replay。ESN task 0/3、MLP 3/3，
  strict 各0/3；这些是不同开发配置，不是独立泛化成功率。没有新仿真或正式评估。
- 定位运行时偏移：旧冻结 MJB 仅被现有 MuJoCo 3.11.0 加载，近期 MJB 仅被3.14.0加载。
  最新六条模型hash一致；同版本两模型618个公开字段一致。禁止把跨版本结果作仅算法
  变化排名。后续冻结评估恢复 .venv-canonical-rl/3.11.0，先记录真实执行元数据和限制。
- seed42配置恢复到62f8c65原字节；seed52另存
  `configs/esn_mlp_temporal_consistency_narrow_rep_seed52_20261001.json`，历史命令不改。
  更正窄屏/seed52的“预提交注册”、独立execution.json及历史MemoryMax过强描述。
  本轮只读审计确实使用systemd MemoryMax=3G/单线程；不能反推历史已遵守。
- 原始temporal七组成对回合、训练记录、checkpoint、MJB/XML与新旧审计已核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_integrity_20261001T1450Z/evidence.tar.gz`：
  652346695 bytes，SHA256 `0d30662ae0479b5594f8240eb4f019f7e2f9ee7b76ad974b80b8fdd6216bd460`。
  运行源码快照：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/434e46fbedfc88df11d7ff8c44f2b3d064ebd217/repository.tar`，
  SHA256 `d23b4c74298ff87b5079002f4e3bb246582f4db6447a97613eab7da1e88479b2`。
- 报告 `code/mujoco_6d_vmc_benchmark/docs/ESN_MLP_TEMPORAL_INTEGRITY_20261001.md`；
  同步联合进度、周报和小型JSON证据。已完成配置/审计/归档修复，当前无新实验运行；
  未完成同checkpoint冻结运行时复核、ESN任务/strict稳健成功及formal步长验证。

## 2026-10-01 — temporal-consistency delta=0.25 replication completed locally

- 开工再次核对缓存 `origin/main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、
  `origin/baseline=4dad929b6550b167943becd271836f0c74a21a38`；`git ls-remote` 仍因网络不可达
  失败，未把缓存当作最新远端，未修改 baseline；本机无运行中的 evaluator/training 进程。
- 预注册配置 `configs/esn_mlp_temporal_consistency_replication_20261001.json`，锁定 manifest
  SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、7/2 split、
  canonical48D/action7、宽度128、combined-v4、原 gate、禁止输入和执行器限制；只复现
  `delta_weight=0.25`，ESN seed=`2026100152`、MLP seed=`2026100153`。
- ESN task/strict=`0/1`,`0/1`，停在 lift，指标 `72.223 mm / 44.403 Nm / 0.125044 m/s /
  0.131457 mm`；MLP task/strict=`1/1`,`0/1`，完成 retreat，指标
  `46.980 mm / 45.918 Nm / 0.070165 m/s / 0.151728 mm`。两条均为开发 `dt=1e-4`、55 s、
  550000 子步，失败回合完整保留。
- 独立审计 action replay 最大误差为0、ESN reservoir replay 最大误差为0，三项物理指标
  重算一致。新增报告 `docs/ESN_MLP_TEMPORAL_CONSISTENCY_REPLICATION_20261001.md`；
  结果否定首轮 `delta=0.25` ESN 的稳健改善，formal `dt=5e-5` 继续锁定。大产物仅本地，
  arm1/GitHub 网络仍不可达。

## 2026-10-01 — temporal-consistency narrow follow-up completed locally

- 开工核对缓存 `origin/main=ba84ed8a39ed743f603aa5d60e901bdf87090e1d`、
  `origin/baseline=4dad929b6550b167943becd271836f0c74a21a38`；本轮
  `git ls-remote` 因网络不可达失败，未把缓存 SHA 当作最新远端，也未修改 baseline。
- 预注册配置 `code/mujoco_6d_vmc_benchmark/configs/esn_mlp_temporal_consistency_narrow_20261001.json`
  （SHA256 `4e6fd694756b73fd964f9f1fe1ab6e71eee98f4da165c06f5f79d48851eac886`），
  固定 manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、
  7/2 split、canonical48D/action7、宽度128、combined-v4、原 gate、禁止输入和执行器限制；
  只测试 temporal delta loss `0.25/0.75`。
- 四条开发闭环均 55 s/550000 子步。ESN task/strict=`0/2`,`0/2`，MLP
  task/strict=`2/2`,`0/2`。`delta=0.25` ESN 到 retreat、RMSE `52.502 mm`、峰矩
  `45.556 Nm`、峰速 `0.117007 m/s`、穿透 `0.146245 mm`、推杆最长接触 `0.7673 s`，
  但未完成 placement；`delta=0.75` ESN 停 carry。MLP 两条均 placement 完成，一条缺
  required contact coverage，另一条球反弹失败，均 strict=false。
- 新增独立审计脚本 `tools/audit_temporal_narrow_screen_20261001.py`（SHA256
  `c9639aecdcb26cce9bcfa394e471a1e2c953224456b77ab44dfec5c582e82c3f`），四条 action replay
  最大误差为0，ESN reservoir replay 最大误差为0，物理子步指标独立重算通过。新增专题报告
  `docs/ESN_MLP_TEMPORAL_CONSISTENCY_NARROW_20261001.md`；大产物和 raw rollout 仅本地，
  arm1/GitHub 网络仍不可达，待恢复后同步。formal `dt=5e-5` 继续锁定。

## 2026-10-01 — temporal-consistency candidate seed replication completed locally

- 对首轮 `delta_weight=1.0` ESN 候选预注册第二 seed `2026100142`（MLP `2026100143`），manifest、7/2 split、canonical48D/action7、combined-v4、gate、禁止输入和执行器限制均未变。
- 复现 ESN 在 carry 停止，task/strict=false，RMSE/峰矩/峰速/穿透=`257.986 mm/44.770 Nm/0.1423 m/s/0.1774 mm`；MLP task=true、strict=false，指标=`58.208/45.395/0.1178/0.1317`。两条均完成550000子步，独立 action/储备池/物理审计通过。
- 复现否定首轮 `delta_weight=1.0` ESN 的稳健泛化结论；formal `dt=5e-5` 仍锁定。复现原始证据保留在 `outputs/esn_mlp_temporal_consistency_20261001_rep_seed42/`，大产物仅本地待同步。

## 2026-10-01 — temporal-consistency ESN/MLP screen completed locally

- 注册并完成纯 ESN/MLP action-delta loss 屏幕，候选 `delta_weight=0/0.5/1.0`。锁定 manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、7/2 identity split、canonical48D/action7、128 宽度、combined-v4、原 gate、禁止输入和执行器限制；只改变训练目标中的相邻 action 增量损失。
- 六条均为开发 `dt=1e-4`、55 s、550000 子步。ESN task/strict=`0/3`,`0/3`，最终阶段 carry/carry/load_transfer；`delta_weight=1.0` ESN 最接近完成但仍未放置。MLP 的 `0.5/1.0` 完成 task，strict=`0/3`，required contact coverage 仍失败。六条指标和 checkpoint hash 见 `docs/ESN_MLP_TEMPORAL_CONSISTENCY_SCREEN_20261001.md`。
- 六条独立 action/储备池/物理子步审计通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP 无 reservoir，均为550000物理子步。没有 strict 候选，formal `dt=5e-5` 继续锁定；结果不支持 ESN 优势。
- 新增配置、训练器和专题报告。原始 rollout、checkpoint、MJB 和失败回合仅保留本地待同步；本轮 GitHub 与 arm1 网络仍不可达。

## 2026-10-01 — low-scale ESN/MLP weight-decay screen completed locally

- 完成预注册 `weight_decay=1e-5/1e-4/1e-3` 屏幕。锁定 teacher manifest SHA256=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`，固定 7/2 identity split、canonical48D/action7、ESN/MLP 宽度128、`input_scale=0.25`、combined-v4、原 gate、纯本体输入和执行器限制；仅改变 AdamW weight decay。
- 三组均为开发 `dt=1e-4`、55 s、550000 物理子步。ESN 三组 task/strict 均为 false，全部在 lift 停滞；MLP 三组 task=true、strict=false，均因 combined contact coverage（含柱子等要求）不足而失败。ESN 的 RMSE/峰矩/峰速/外部穿透分别为 `77.173/42.170/0.1106/0.1635`、`75.485/42.723/0.1078/0.0997`、`73.093/41.235/0.1134/0.0919`；MLP 分别为 `48.442/44.781/0.0662/0.1106`、`60.176/45.249/0.1172/0.1323`、`47.831/44.426/0.0702/0.1666`。
- 六条独立审计通过：action replay 最大误差为0，ESN reservoir replay 最大误差为0，MLP 无 reservoir，物理子步与55 s时长一致。两次仿真前 setup failure（hash变量错误、teacher root错误）保留并不计实验回合。结果不支持 ESN 优势，formal `dt=5e-5` 仍锁定。
- 新增报告 `docs/ESN_MLP_LOW_SCALE_WEIGHT_DECAY_20261001.md`、配置和训练器；修复审计器以支持无 reservoir 的 MLP。专题输出和 checkpoint 目前仅本地、待 arm1/GitHub 网络恢复，未声称远端归档；详见专题报告与联合进度。

## 2026-10-01 — low-input-scale pure ESN output-gain screen completed locally

- 在已登记的 `input_scale=0.25` ESN checkpoint 上只改变 `output_gain=0.80/0.90/0.95`；
  base SHA256=`99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`，配置
  `configs/esn_low_scale_gain_screen_20261001.json` SHA256=
  `3e7a79e32cf17ebbd7fc6a81ae9703d27f5c09ed8a69746ce82a5c5fb34fde67`。
- 固定 teacher manifest、7/2 split、canonical48D/action7、combined-v4、原 gate、禁止
  输入与执行器限制；三条均为开发 `dt=1e-4`、55 s/550000 子步，task/strict=`0/3`、`0/3`。
  `.80/.90/.95` 最终 lift/carry/lift，指标分别为
  `60.590/37.618/.1031/.1257`、`144.782/37.867/.1395/.1705`、
  `73.919/37.051/.1019/.1150`（RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm）；柱子
  覆盖全部失败。
- 三条独立审计均通过：action/reservoir replay 最大误差为0，物理子步均550000；失败 raw
  rollout、MJB、checkpoint 和审计保留在 `outputs/esn_low_scale_gain_screen_20261001_v1/`。
  结果只说明增益单因素没有恢复严格任务，不支持 ESN 泛化或相对 MLP 优势。
- formal `dt=5e-5` 继续锁定；arm1 与 GitHub 网络不可达，产物仍仅本地待同步。

## 2026-10-01 — low-input-scale pure ESN alpha screen completed locally

- 开工读取了缓存 main `ba84ed8a39ed743f603aa5d60e901bdf87090e1d` 与 baseline
  `4dad929b6550b167943becd271836f0c74a21a38` 的更新日志；本轮 fetch/SSH 在当前网络下
  失败，未把缓存冒充最新远端，也未修改 baseline。
- 在先前唯一一次 `input_scale=0.25` task-success 的 ESN checkpoint 上预注册并物化
  action-readout `alpha=0.25/0.50/0.75`。base checkpoint SHA256=
  `99e0a169025e3ac9643b2021958a92c668172b5745725f28050d530f2a585651`，配置
  `configs/esn_low_scale_alpha_screen_20261001.json` SHA256=
  `2f286923b0f1a701f42e463553b2f0399fc2b3eba797321536e247a408604f79`。
- 固定 teacher manifest、7/2 identity split、canonical48D/action7、128 ESN、combined-v4
  环境、原 gate、禁止输入和执行器限制；三条均为本地 `.venv-rl`、单线程、开发
  `dt=1e-4`、55 s/550000 子步。结果 task/strict 均 `0/3`：alpha .25 停 lift，
  `.50` 停 carry，`.75` 停 lift；柱子接触覆盖均失败。三项指标分别为
  `68.485/35.127/.1010/.1423`、`138.424/39.585/.1275/.1373`、
  `59.341/37.282/.1041/.1101`（RMSE mm / 峰矩 Nm / 峰速 m/s / 外部穿透 mm）。
  `.50` 推杆最长连续接触 `.6642 s`，但没有转化为任务成功；`.75` 球反弹失败。
- 三个独立审计均通过：action replay 与 reservoir replay 最大误差均为 `0`，物理子步为
  `550000`，最长单回合 RSS 约 `667 MiB`。所有失败 raw rollout、MJB、checkpoint 和审计
  保留于 `code/mujoco_6d_vmc_benchmark/outputs/esn_low_scale_alpha_screen_20261001_v1/`。
  详细结果见 `docs/ESN_LOW_SCALE_ALPHA_SCREEN_20261001.md` 和联合进度文档。
- 本轮无 strict 候选，formal `dt=5e-5` 继续锁定。arm1 归档尝试因 SSH 不可达未完成，
  产物明确标记为本地待同步；GitHub push 待网络恢复。

## 2026-10-01 — fixed-reservoir ESN readout-seed decomposition completed locally

- 固定 input-scale=`0.25` 和 reservoir seed=`2026100101`，仅改变 readout seeds `2026100121/22/23`，预注册配置 SHA=`c5f31edb3263fa16702229bfd14d74f7f6b584d0f9a8136f5c51d521385e4828`，训练脚本 SHA=`9e30fd12ed056bedcdafe80a32deb67786aa20e6f22b4612b8ebfecdccea5d2f`。
- ESN task/strict=`0/3`、`0/3`，停在 lift/carry/carry；MLP task/strict=`3/3`、`0/3`。所有回合 550000 子步，动作和 ESN 储备池 replay 最大误差为 0，物理审计通过。
- 独立 audit SHA=`d82652a366c6f2d5cd6b3562c9b483ae298563f5a130955cf41aad3a8f6a2cb3`，73 文件收据 SHA=`eda963478fa3362d7ed4078bb6d6e9eb1bd500126310670eed8b83bfcbe54af6`。固定 reservoir 仍未消除 ESN 对 readout seed 的敏感性，也没有 strict 候选。
- 未完成：formal `dt=5e-5`、arm1 归档和 GitHub push；网络仍不可达，产物标记为本地待同步。

## 2026-10-01 — pure ESN input-scale screen and replication completed locally

- 在冻结 teacher manifest、office-v5 combined-v4、gate、canonical48D/action7、禁止输入和执行器限制下，预注册输入权重尺度 `0.25/0.45/0.80` 屏幕；配置 SHA=`1197d1739ae0e2f1af9671cf4dbabbd1350bb4ab589ef7b951708fd5bd87deff`，训练器 SHA=`881d670a56f1723576534020ef4baebddd0ed29e5e0f7bb2f7a4ffc9e0db77c6`。
- `input_scale=0.25` 的单个 ESN seed 完成 task、strict=false，RMSE/峰矩/峰速/穿透=`68.471 mm / 48.004 Nm / 0.1164 m/s / 0.1499 mm`；0.45/0.80 ESN 分别在 carry/load_transfer 停止。MLP 对照全部 task=true、strict=false。
- 对唯一 task=true 候选预注册复现 seeds `2026100118/19/20`，ESN task/strict=`0/3`、`0/3`；复现 audit 与 73 文件收据 SHA=`688ae6b3556023d64eb1c68ba2d84cde0b6ca461892240cbe9f8a83666b484f2`。屏幕收据 SHA=`0fe9e346533fb27ba4ba306b49d9bc128dbe2bf584b1a168d1ae8dba934e42a2`。因此单 seed 成功不能称 ESN 泛化或优势。
- 所有回合均为开发 `dt=1e-4`/550000 子步，严格 gate 无一通过，未解锁 formal `dt=5e-5`。GitHub/arm1 仍不可达，产物仅本地待同步。

## 2026-10-01 — pure ESN spectral-radius screen completed locally

- 在同一 teacher manifest、场景、gate、actor 输入和执行器限制上完成预注册 spectral-radius 屏幕；只改变 128 单元 ESN reservoir 谱半径 `0.60/0.90/1.10`，每组配同宽度 MLP。配置 SHA=`e96a9880d607d77390b062542e25dab677880587a2483aeb3dcfc4e9b48f0c17`，训练脚本 SHA=`9381becd58ce6c750672e6184f4a452004990bec5e98dd989ba8eab97fab5e5c`。
- 三组 ESN task/strict 均失败：0.60 在 lift，0.90 在 lift 且外部穿透 `1.5602 mm`，1.10 在 carry。MLP 对照仅 0.90 完成 task、strict=false；所有行都是 55 s、`dt=1e-4`、550000 子步开发结果。
- 独立审计 `outputs/esn_mlp_spectral_screen_20261001/INDEPENDENT_AUDIT.json` 通过，六条动作 replay 最大误差为 0，ESN 储备池 replay 最大误差为 0。73 文件收据 SHA=`6505943bf8a8711fb03a2e48a86545cc1937e77b8f1e64c5e9459179a182ae0`。完整结果和失败原因见 `docs/ESN_SPECTRAL_SCREEN_20261001.md`。
- 未完成：ESN strict 泛化、formal `dt=5e-5`、arm1 归档与 GitHub push。网络仍不可达，产物明确标记为本地待同步。

## 2026-10-01 — pure ESN reservoir leak-time screen completed locally

- 开工核对 main 缓存 `ba84ed8a39ed743f603aa5d60e901bdf87090e1d` 与 baseline 缓存 `4dad929b6550b167943becd271836f0c74a21a38`；再次 fetch 和 GitHub/arm1 SSH 均因网络限制失败，未把缓存当作最新远端，未修改 baseline。
- 预注册 `configs/esn_tau_screen_20261001.json`（SHA256=`cd21c44d4b0aa494f464d9aa450c9ff70b6d002361f924e19ae5c7a378d9a9d4`）并新增 `tools/train_esn_mlp_tau_screen_20261001.py`（SHA256=`510fd962ebcf96051f064e5a51bab6fa14a16af5afa9650babd52dd71be4fa09`）。只改变 128 单元 ESN 的 reservoir leak 时间尺度，保持 teacher manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、canonical48D/action7、7/2 identity split、估计负载训练权重、环境/gate/actor 输入/执行器限制不变；每个 profile 都训练同宽度 MLP 对照。
- fast/baseline/slow 三组均已完成 55 s、`dt=1e-4`、550000 子步闭环。ESN 依次在 lift/carry/lift 停止，task/strict 均为 false；MLP fast/baseline 为 task=true、strict=false，slow 为 task/strict=false。ESN 最佳 baseline 行的 RMSE/峰矩/峰速/穿透为 `86.080 mm / 40.585 Nm / 0.0862 m/s / 0.1540 mm`，但未完成 placement。
- 独立审计 `outputs/esn_mlp_tau_screen_20261001/INDEPENDENT_AUDIT.json` 通过；六条物理子步均为 550000，动作回放最大误差为 0，ESN 储备池回放最大误差为 0。汇总 70 文件收据 SHA=`361116939aee2ef4b6bedbcba828b215a516de3158434c00161e7e9c4694eea0`。完整结果和失败原因见 `docs/ESN_TAU_SCREEN_20261001.md` 与 `docs/ESN_VMC_JOINT_PROGRESS_20260927.md`。
- 未完成：strict 泛化成功、formal `dt=5e-5`、arm1 归档与远端 push。由于服务器不可达，本轮大产物仍标记为“本地、待同步”，没有声称服务器已核验。

## 2026-10-01 — paired ESN/MLP seed screen completed

- 完成预注册配置 `configs/esn_mlp_seed_screen_20261001.json` 的 seed
  `2026100106/07/08` 成对训练。三组均使用 manifest SHA256
  `6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`、固定 7/2
  identity split、估计负载训练权重、canonical48D/action7 和 128 宽度；环境、gate、
  actor 输入与执行器限制保持不变。
- 冻结 combined-v4 开发闭环均为 55 s、550000 子步、`dt=1e-4`。MLP 三组 task=true、
  strict=false；ESN 三组 task=false，seed106/107/108 分别停在 lift/load_transfer/lift。
  ESN/MLP 的 `RMSE mm / 峰矩 Nm / 峰速 m/s / 穿透 mm` 为：
  `874.772/55.664/0.1639/0.1089` vs `52.402/44.708/0.0730/0.1772`；
  `187.222/47.666/0.1601/0.1612` vs `33.860/44.542/0.0707/0.1530`；
  `37.743/38.843/0.0721/0.1714` vs `43.083/45.083/0.0724/0.1843`。
- 六条学生回合独立 action/状态/物理子步审计通过，ESN action/储备池 replay 与 MLP action
  replay 最大误差均为0；没有 strict 通过，未解锁 formal `dt=5e-5`。seed108 的 ESN
  数值指标接近成功但 placement gate 未完成，不能写成 task success或ESN优势。
- 训练峰值 RSS 约 832 MiB；初次错误的 `ulimit -v` 导致 PyTorch 库映射失败，相关失败日志
  保留并不计为实验回合。完整 output、checkpoint、raw rollout 和 audit 已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_mlp_seed_screen_20261001_v1/`；
  evidence tar SHA256=`12ebe6d9529df5dd0bc967a45ed7a5ac77d1d0e4774d8fe10203ac5f158e5aa8`。
- 提交 `9888f6cc361004a70a24851e7915062ca5962a5f` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/9888f6cc361004a70a24851e7915062ca5962a5f/repository.tar`，
  SHA256=`36563d9b960253ba1ec4a71ac3a4a1fea3966aa9afbdfe4727ad271e5ee9c589`。

## 2026-10-01 — pre-registered paired ESN/MLP seed screen

- 增加 `configs/esn_mlp_seed_screen_20261001.json`，预注册在锁定的 9 条 teacher manifest
  上使用 seed `2026100106/07/08` 成对训练 weighted ESN 与 MLP；仍为 canonical48D/action7、
  128 宽度、固定 7/2 身份留出和训练期估计负载权重。环境、gate、actor 输入和执行器限制不变。
- 先固定配置并提交，再按同一 combined-v4 冻结命令运行闭环；所有 seed、checkpoint、trace
  hash、失败原因和独立物理子步审计均保留。未运行前不解读结果。

## 2026-10-01 — pure ESN output-gain screen completed

- 完成预注册的纯 ESN `output_gain=0.80/0.90/0.95` 屏幕；只改变 v4 checkpoint 输出增益，
  不改 office-v5、gate、canonical48D actor 输入、执行器限制或 MLP。三条回合均为
  seed `2026091751`、55 s、550000 子步、开发 `dt=1e-4`。
- 结果：0.80 停在 carry，task/strict=false，RMSE/峰矩/峰速 `520.286 mm/41.950 Nm/
  0.1879 m/s`，穿透 `0.1688 mm`；0.90 停在 lift，`407.785/46.242/0.2134`，
  `0.1350 mm`；0.95 停在 lift，`454.745/44.605/0.2160`，`0.1243 mm`。三条均未完成放置，
  失败回合全部保留，没有候选解锁 formal `dt=5e-5`。
- 独立 audit `outputs/esn_gain_screen_20261001_v1/gain_{080,090,095}_audit.json` 全部通过：
  action replay 与储备池状态 replay 最大误差为 0，物理子步为 550000。配置 SHA256 为
  `1d0e8cb73db0a8effa142a3fcdbc2dd026edf70eaa4517231b72815895ce5c90`，基准 checkpoint
  SHA256 为 `bb0bd4df0f9467932c15999853f67fe662aaf5f34c06b79855d4d1ab9a4cf1b0`。
- 结果和审计保留在本地 `outputs/esn_gain_screen_20261001_v1/`，并已逐项核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_gain_screen_20261001_v1/`；
  文件收据 SHA256=`6ed5e73204de983d481200bcf5082a50e1259fbd55a281934aa33e7460dcff74`。
  预注册源码提交为 `9e9580a`，结果记录为 `0a611d4`，最终同步提交为 `7fa6a6e`。
- 对应 `7fa6a6e39459cf846f21400c7f5fa5d4301da1ca` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7fa6a6e39459cf846f21400c7f5fa5d4301da1ca/repository.tar`，
  SHA256=`1a79dd2583859e38ce785d2cd96bfb5efd1b0a2af436c4565224123c92277015`。
- GitHub `main` 已成功推送至 `7fa6a6e`；服务器归档与源码快照逐项核验通过。
- 已完成：三组闭环、三项物理指标重算、动作/状态重放审计和文档更新。未完成：服务器归档、
  formal `dt=5e-5`（门槛未满足）及 ESN 跨条件成功。

## 2026-10-01 — pre-registered ESN output-gain screen

- 注册第二个纯 ESN 算法屏幕，只改变 v4 checkpoint 的 `output_gain=0.80/0.90/0.95`；不
  组合 alpha、不改环境、gate、actor 输入、执行器限制或 MLP。计划见
  `configs/esn_gain_screen_20261001.json`，物化工具为
  `tools/materialize_esn_gain_screen_20261001.py`。
- 先提交预注册和固定 hash，再逐一运行 55 s/550000 子步开发闭环；未运行前不解读结果。

## 2026-10-01 — pre-registered ESN output-smoothing screen

- 在不修改 office-v5、gate、actor 输入、执行器限制或 MLP 的前提下，注册纯 ESN action
  readout `alpha` 屏幕，候选固定为 `0.25/0.50/0.75`；基准 checkpoint 为 v4 无权重
  ESN，完整命令和选择规则见 `configs/esn_alpha_screen_20261001.json`。
- 新增 `tools/materialize_esn_alpha_screen_20261001.py`，生成变体前固定 base/config
  hash；尚未运行闭环，结果不得提前解读。该预注册先提交，随后按单 MuJoCo/1线程/3GiB
  约束逐一运行，所有失败回合保留。

## 2026-10-01 — pure ESN alpha screen completed

- 按已推送的预注册计划，只改变 v4 ESN checkpoint 的 action-readout smoothing
  `alpha=0.25/0.50/0.75`；场景、gate、canonical48D 输入、执行器限制、MLP 和评测命令均不变。
- 三条开发回合均为 55 s/550000 子步、`dt=1e-4`，task/strict 全部 false：alpha 0.25
  停在 lift，RMSE/峰矩/峰速 `367.725 mm/50.319 Nm/0.2420 m/s`，穿透 `0.6467 mm`；
  alpha 0.50 为 `411.708/36.347/0.2306`，穿透 `0.1787 mm`；alpha 0.75 停在 carry，
  `95.040/41.629/0.0848`，穿透 `0.1276 mm`。alpha 0.25 推杆接触最长2.2952s，0.50为
  0.5018s，0.75为0.0038s；不能把接触时长换写成任务成功。
- 三条动作与储备池状态重放均为0，独立物理子步审计通过；未有候选解锁 formal `dt=5e-5`。
  原始回合、失败和审计保留在 `outputs/esn_alpha_screen_20261001_v1/`，并已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/esn_alpha_screen_20261001_v1/`；
  38 文件收据 `FILE_SHA256_REL.txt` SHA256=`45dcf2d710a8ea12cd0f6ba0277669da76deb6af889347e6ec1f9e01575fbffa`，
  远端逐项校验通过。
- 最终提交 `afba210d2eb554b2e3fd7ca5c91363549cbacf2b` 的源码快照已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/afba210d2eb554b2e3fd7ca5c91363549cbacf2b/repository.tar`；
  本地/远端 SHA256=`61b0284f613a13677b5c969be7c5dfca965b491c591efd34806cfb055dc9cb54`。

## 2026-10-01 — v3 teacher-label correction and frozen ESN/MLP rerun

- 开工按 `sii-research-sync` 核对本地 `origin/main` 缓存起点
  `3336864707c1e59a1015568a0aea1891e18b8980`；本轮网络受限，无法重新连接 GitHub 或
  `arm1@192.168.31.70`，因此未把缓存 SHA 冒充最新远端状态。远端没有可读的 `baseline`
  分支／更新日志；baseline 工作区未修改。
- 修正 `tools/train_vmc_teacher_esn_mlp_20261001.py` 和 weighted trainer：训练目标绑定
  `execution_chain.npz/filtered_action`，保留 raw `rollout.npz/applied_action`，逐条校验两者
  shape 与 rollout/chain hash；metadata 增加 execution-chain、ESN/MLP 推理源码 hash，并
  更正 trainable 参数量为 ESN 23,559、MLP 23,687。新增
  `tests/test_student_distillation_20261001.py` 的标签出口回归测试。
- 在冻结 manifest、combined-v4、canonical48D/action7、gate、actor 输入与执行器限制下，
  使用本地 `.venv-canonical-rl`、单线程完成 v3 训练（seed `2026100104`）与无初始细步的
  55 s/550000 子步开发闭环。结果：VMC teacher task/strict=true/false，ESN=false/false
  （carry，RMSE 406.806 mm，43.246 Nm，0.2404 m/s，穿透 0.1929 mm），MLP=true/false
  （retreat，43.333 mm，44.405 Nm，0.0753 m/s，穿透 0.1012 mm）。动作重放均为 0，ESN
  储备池重放为 0，独立物理子步审计通过；strict 未通过，不解锁 formal `dt=5e-5`。
- v3 输出、首轮带细步诊断及失败回合保留在
  `code/mujoco_6d_vmc_benchmark/outputs/vmc_teacher_esn_mlp_weighted_20261001_v3/`；详见
  `docs/VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md`、联合进度与周报。checkpoint：ESN
  `a5560ca073c3afed6d553c1ee7a37ac32d537f1245aa6369feabeb022dff40b4`，MLP
  `e27c4ed63cd5f604c5338c90aa87b09e61a90f401a2d92f674c1e69a501e45f0`。v3/v4 随后同步到
  新的 arm1 归档目录（见末项），已有 v1 归档未覆盖。
- 验证：`pytest -q tests/test_student_distillation_20261001.py tests/test_esn_compliance.py
  tests/test_direct_esn_env_contract.py tests/test_office_memory_esn_20260927.py` → 14 passed；
  `git diff --check` 与两训练脚本 `py_compile` 通过。已完成：标签修复、v3 训练、闭环和
  独立审计。运行中：无本机仿真。未完成：arm1 归档、正式 `dt=5e-5`（门槛未满足）及
  strict 泛化成功。
- 追加预注册无负载权重控制 v4（seed `2026100105`, emphasis=0）：ESN task/strict=false/false、
  lift、RMSE 526.818 mm、峰矩44.416 Nm、峰速0.2204 m/s、穿透0.1323 mm；MLP=true/false、
  retreat、RMSE38.832 mm、峰矩44.286 Nm、峰速0.0807 m/s、穿透0.1527 mm。仍为
  55 s/550000 子步开发回合；动作/储备池重放及独立审计通过。v3/v4 均未过 strict，
  不解锁 formal dt=5e-5；v4 也已进入同一新的 arm1 归档目录。
- 随后将 v3/v4 完整输出（68个文件，含 checkpoint、55 s 原始 rollout、MJB、日志和两份
  独立审计）归档到已核验的新目录
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v3_v4/`。
  相对路径收据 `FILE_SHA256_REL.txt` SHA256=`ce2046f058475edcada19bf264a5f0e3406197b8f34a448f1485d3820e34aff5`，
  远端逐项 `sha256sum -c` 全部通过；未覆盖已有 v1 归档。
- 已将本轮提交 `a2a926b5b4deee3dea9476e1eaefd5dcf211f09a` 的源码快照归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/a2a926b5b4deee3dea9476e1eaefd5dcf211f09a/repository.tar`，
  本地/远端 SHA256 均为 `4e6fd79dbf6281217fa7dc718d5b9719be6a667be6fcf13930d35e26d9c7dd70`。

本文件记录每次对话交付的文件修改、验证和结果边界；最新记录在前。对应提交号由 Git 历史
查询：`git log --oneline -- UPDATE_LOG.md`。持续提交约定见 [AGENTS.md](AGENTS.md)。

## 2026-10-01 — VMC teacher 标签上的 ESN/MLP 加权读出续实验

- 开工核对 origin：`main=3336864707c1e59a1015568a0aea1891e18b8980`，随后复核远端
  `baseline=4dad929b6550b167943becd271836f0c74a21a38`；baseline 正在独立运行奖励主批次，
  本轮未合并、停止或改写其冻结源/作业。
- 新增 `tools/train_vmc_teacher_esn_mlp_weighted_20261001.py`，在冻结
  canonical48D/action7、相同 128 单元预算下，只对估计力/负载本体通道采用训练期平滑
  权重；actor、环境、gate、执行器限制均未变。新增报告
  `docs/VMC_TEACHER_ESN_MLP_WEIGHTED_20261001.md`，并同步联合进度、周报和 README。
- 新 weighted ESN/MLP checkpoint SHA 分别为
  `2723e218b474e4414bbbf199eeda0099eae5dfae6af9fbd3e40cbe6b389483c9`、
  `992a6dcd99685f278687fcf4cf25e1e6d61171dc4dde650489c679f082497cdc`。
  同一 combined-v4 开发场景：ESN task=false、lift停滞，RMSE 688.378 mm、峰矩
  62.020 Nm、峰速 0.1800 m/s；MLP task=true、placement complete、strict=false，
  RMSE 50.381 mm、峰矩 46.634 Nm、峰速 0.0823 m/s、柱最长接触 0.6056 s。
- `tools/audit_vmc_teacher_esn_mlp_20261001.py` 独立审计通过：三行均 55 s/550000
  子步，动作/储备池重放和 RMSE/力矩/速度复算通过。两学生 strict 均 false，未解锁
  formal `dt=5e-5`；失败回合保留。运行中仿真 0，服务器归档待 SSH 恢复。
- 验证：加权模型训练与闭环均在本地 `.venv-canonical-rl` 单线程运行；10项 ESN/环境
  合约测试通过，`git diff --check` 通过。完整 campaign 已归档到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v1/`；
  远端 file-list receipt SHA=`5dc78c054067e88e3b34922023d3bbe476e251008e01941bfa0bd43525a34d96`，
  checkpoint hash 与本地一致。大型 rollout/checkpoint 未提交 Git。
- 首次代码/文档提交为 `48358e8af6c2563209d52e8f8eeeb852d9be9dae`；对应完整 source tar
  已归档到服务器 `source/48358e8af6c2563209d52e8f8eeeb852d9be9dae/repository.tar`，
  SHA256=`951556d584689f520f13d64d3ad0a9130641c067aa02185602835e31e4c9411e`。

## 2026-09-30 — 十小时窗口收尾：215条记录、9个唯一teacher条件与公平经典对照

- 13:29 UTC读取实际远端日志，13:55/13:57复核fetch：main=
  `cd38ad943b1cf16442ca181e44eae64579720986`、baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，未合并baseline、未干扰其旧暂停作业。
- 10小时派发截止13:48:16；最后派发13:46:18.620425、动态结束13:48:22.954650、
  归档结束13:48:50，continuation v2 rc0退出，截止后派发0。终态162搜索＋27验证记账
  （24动态/3初态拒绝）＋26collection，共212完整动态/3初态失败；缺失最后long0002
  阻抗配对明确保留，未补跑。定义3300不等于已执行/合法示范。
- 验证有效8fixture：VMC/导纳/阻抗task7/8、0/8、7/8；strict4/8、0/8、6/8；
  全要求录取3/8、0/8、4/8。每方法另1个预注册初态无效条件。类别分别锁参，不称统一策略
  或VMC全面优势。追加采集共同8训练fixture录取5/8、0/8、5/8，失败参与指标汇总。
- 新collection独立审计26/26通过，全55s/550000子步，动作重放最大5.55e-17；9重复对
  57NPZ/612数组完全相同、不增样本。严格train-only锁参VMC清单9唯一（厚角4/短撞4/持续1），
  205排除/1隔离：隔离因部分配对缺模型绑定且原本接触失败，不是证明模型矛盾；不回写追认。
  validation全排除，无新ESN。每类1000合格、持续推碰可靠teacher和正式综合泛化未完成。
- 新collection审计入口/测试、shared validation helper显式phase/split绑定、完整验证及
  十小时报告；README、联合进度、周报、三类记录同步。65相关测试通过、diff check通过。
  原冻结v10源207项hash保持一致，环境/gate/actor/执行器限制未改，全部为开发dt=1e-4。
- 2120文件最终证据已逐项核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_final/evidence/`，
  含`tools/`审计代码、`outputs/teacher_bank_v10_terminal_review_20260930_1349/`完整metadata、
  `outputs/teacher_bank_v10_final_comparison_20260930_1350/`及raw/duplicate/strict manifest。
  终态review SHA=`6414365111679e1712ed169bc83c3022c7b8b6cf68b56fd7f27a4517b7b0deea`；
  manifest SHA=`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`。
  逐条raw及动态源码仍在相邻`teacher_bank_three_domains_20260930_v10/`，215份凭据完整。
  归档后的文档地址补充以本提交为准，不冒称已在较早快照中。运行中仿真0，teacher-10已暂停。
- 汇报入口：[十小时结果](code/mujoco_6d_vmc_benchmark/docs/TEACHER_BANK_TEN_HOUR_REPORT_20260930.md)。
  限时工作已完成，数据数量和研究目标未完成；不能以少量合格轨迹宣称泛化或真实部署安全。

## 2026-09-30 — 严格训练标签出口、初态拒绝诊断与不改场景接续

- 12:21及12:49 UTC核对并读取main=`d39aed3f4800223e1aa1584f1dbcc9d45c13e13f`、baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，无上游新变化，未合并baseline。
- 新训练标签出口绑定原train manifest、锁参、源、实际MJB/NPZ/hash和服务器凭据；
  历史validation标签即使true也拒绝。1144快照仅6个唯一训练fixture（厚角2/短撞3/持续1），
  158排除、0隔离。重复不增样本，矛盾结果/模型隔离；未来runner标签增加train条件，
  冻结v10保留。旧collector/status已另筛train，没有证据表明实际训练数据混用。
- 12:27原作业在21完整validation后因棍推0001初态交叉最大60.09884mm退出；
  独立源码/堆栈/空曝光核查表明动态前拒绝，不能说控制器运动失败。三方法该场景均原样
  保留，无替换。新独立continuation复用全部已完成数据、原冻结attempt与截止，未知异常停机。
  v1资源检查未派发即失败（cpu.max未委派）；v2记录quota_enforced=false并强制单sim/1线程/
  MemoryMax3GiB/Swap0，12:46:27启动，最后验证运行中。此前CPUQuota配置请求不等于实际生效。
- 新增去重原始数组对比、严格标签出口、验证图、接续工具与初态诊断；独立验证审计支持
  无效初态单列null指标。五组相关70测试通过；未修改gate/环境/参数、未做新ESN或正式dt验证。
- 已逐文件核验共享至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_1209/evidence/`厚角raw审计与source发布凭据；
  `_1237/evidence/`1791文件（完整名称前缀同上teacher_bank_review_checkpoint_20260930）；
  `_1242/evidence/`45文件初态核查/v1协议；`_1245/evidence/`41文件v2协议/源和首次启动失败。
  v2 driver SHA=`9215b66fefbd7a91082ddbf7c205c777122a59777f5827502d0042a06ed93077`。
  运行中state及本次补充文档未冒称已在此前快照中。原截止13:48:16 UTC不延长，继续验证/采集。

## 2026-09-30 — 162搜索锁参、首个人推独立通过与完整决策审计

- 11:52 UTC重新fetch并读main=`0a1e7972750114d2e0e1f5c1626004e1ed449d7a`及baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`，上游无新增变化，未合并baseline。
- 11:42搜索162/162完成，27录取/135未录取；九组候选/排名、源与配对模型独立核对通过。
  bank SHA=`1cafd43556f754df0595027c6aa1a358520038bbd5a3f742b9ef3b2a2f287945`。
  锁定参数训练录取厚角VMC/导纳/阻抗2/3、0/3、2/3；短撞3/3、1/3、2/3；持续1/3、0/3、0/3。
  task/strict与曝光/录取分开，持续阻抗task/strict仍2/3；不称VMC三指标全面优势。
  27预注册验证运行，collection/新ESN未开始，仍只有2/3/1个唯一合格VMC训练fixture。
- 新增定义覆盖工具，3300定义在剔除未消费字段后仍全部唯一、train/val精确重合0，未宣称
  全量动态有效。全部27BO决策用当时训练前缀同实现精确重放，误差0，不当作收敛证明。
  短撞c05退化诊断区分两类任务失败，不调原score。首个人推c05原始550000子步/动作与
  独立连续段重算通过：1.2643s同段14.3532mm；但RMSE/峰力增加且仍碎接触，不称真实安全。
- 新增validation离线审计、human分段与图工具、相关专属报告，10项针对性测试通过。
  全162点图显示所有失败并修正长期图标签含paddle，已视觉核验。README/主记录/进度/周报同步。
- 均已逐项核验到服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_1124/evidence/`56文件定义覆盖、短撞诊断及工具；
  `teacher_bank_review_checkpoint_20260930_1138/evidence/`49文件独立人推/图与全部BO审计；
  `teacher_bank_review_checkpoint_20260930_1150/evidence/`1609文件锁定元数据、公平表和162点图。
  锁定review SHA=`a2708301bdf41874c01dca8a31611c6a5fc1a09081fb50e6c41ea6c8afd32169`；
  人推review SHA=`dab55a4eba144668891332ff6c9a4dbd4415ae8a2c21e7cce7e3acb5725ba2a7`。
  归档后文档地址补充以本Git提交为准，不冒称已在旧快照中。稳定v10未重启，10小时任务继续。

## 2026-09-30 — 135回合检查点、完整资产复现更正与公平展示

- 11:10 UTC重新fetch并读取main=`2581451cc9c471b19c67286457bea8d3b8a4b2b7`及baseline=
  `c9185489dfbb8d969525a253493592cbbbcd06d2`日志。baseline奖励主实验和独立40k诊断均已收尾，
  仍存在无grasp的探索瓶颈；不合并、不混同其综合场景和本次训练域，也不声称算法本质失败。
- v10完整c00–c04共135回合23录取/112失败，c05继续，未重启。短撞VMC c04单参数3/3、
  c05为0/3；不改规则或丢失败。参数未锁定，validation/collection/新ESN未开始。
- 纠正资产清单遗漏FR3：完整133文件而非85；未来prepare校验两树与引用资源。原冻结
  plan/source/execution保留。本机真实冻结初始化零积分9/9逐字节复现；XML-only0/9因质量
  默认和运行时mask等差异失败。ARM首个source模型22数组有差异，动态补充采集阻断。
  新资产审计/静态复现工具与报告解释范围，不声称跨架构物理等价。
- 新公平展示器分列task/strict/曝光/录取与失败，锁定前不输出策略成绩；三方法指标采用
  同fixture共同完整证据集合，缺失或不匹配一项则共同排除指标聚合但保留任务统计与明细。
  最终11测试通过；资产6/选择6/Spark driver8通过。Spark采集driver仅准备，未启动态作业。
- 已逐文件核验服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_runtime_inputs_complete_20260930/menagerie/`完整133资产，manifest SHA
  `56b0e9d07c2b0e5636f38fb228dbd077980d2ea14c2ea26bc8987be11a304523`；
  `teacher_bank_review_checkpoint_20260930_1104/evidence/`含112文件，本机静态成功和XML失败
  证据、135状态及归档时工具版本；`teacher_bank_spark_static_source_20260930_v1/`为ARM阻断证据。
  归档后的展示器修正及本段文档以本次Git提交为准，未虚称已在1104快照中。
  10小时窗口继续至13:48:16 UTC；3300定义不等于示范，未达到每类1000条。

## 2026-09-30 — 短撞VMC同参数3/3与108回合公平检查点

- 09:42 UTC核对main=`e1d815c390d1221ee0bf80293e2b8179d2e1d3f8`，baseline已前进至
  `e47da59ebb665fb20764131bd56c7b639805f326`，已读新日志。其100k RL主实验已完成但任务失败，
  发现训练覆盖问题后正做独立补充诊断；不把该局限解释为算法本质，不混入本轮特化训练比较，
  未合并baseline或操作其Spark服务。
- 09:40 v10完整c00–c03共108条，17录取/91失败，全部逐条有核验归档凭据；c04运行。
  VMC短撞c03同一参数3/3，初始c00为2/3。六条配对550000子步的三指标独立重算、冻结
  VMC/filter/状态重放与source/参数/model/hash通过；球形RMSE64.667→37.662mm、峰矩
  47.935→45.004Nm，但峰力1793→2221N、穿透0.11744→0.18863mm。穿透仅元数据核验，
  不冒称独立物理重算、全面安全提升或泛化。新增短撞审计工具和报告，更新专题/进度/周报。
- 新终态收尾工具保存原始JSON快照、独立重建选参和锁定、核对后续参数一致性并指出截止
  汇总归档缺口；11项针对性测试通过，live验收正常。它不重新核验所有原始轨迹/远端receipt。
  原稳定仿真未重启，仍固定六候选；持续推碰三方法0/12，validation/collection/新ESN未开始。
- 以下均已逐文件核验至服务器`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_0913/evidence/`含964文件（短撞审计/六份重放、终态
  工具与live验收/JSON快照）；review SHA=`d135e2f4336583528e66be27e03b0e47b66201355fbc5d03b21212c7a1659c50`。
  `teacher_bank_review_checkpoint_20260930_0943/evidence/`含42文件（108回合status/公平图/报告），
  PNG已视觉核验，SHA=`fb7df489d653adfad53c1a2245d5eca8ef7b2aba7019c3c035ec92148d3f9f13`。
  10小时任务继续至原截止，不改gate、环境或执行器，不把3300定义当作已采满示范。

## 2026-09-30 — 初始81回合完成与首个BO决策复核

- 08:57 UTC再次核对main=`b1e14de2dade36eed6cc8d9ce448cd8b4a1565ad`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及日志，无新上游变化；未合并baseline。
- 08:40检查点的初始81回合10录取/71失败，VMC唯一合格fixture厚角2/短撞3/持续推碰0。
  不能把跨参数样本拼成单控制器成功率。实际BO已开始，首个VMC厚角c03录取1/3，低于c01
  的2/3；不称BO已改善。参数未锁定，validation/collection/新ESN未开始，固定预算继续。
- 新增首次BO只读审计及报告：前三候选训练证据独立汇总与history一致；读取九份真实MJB
  哈希，并核对peer audit记录的同模型hash，未冒称重读peer全部模型。冻结源与plan绑定；
  相同优化器实现、seed20260933重放差0。首次是可行性LCB，离散代理不是连续物理超限。
- 初始81条公平三指标图含所有失败，排除另计尚不完整BO尝试，PNG视觉核验通过。
  审计/图/status等44文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0848/evidence/`。
  review SHA=`979ea114c384ba23ced024f37601a35221ed3c27da9f9832ba97d6f14a6dc197`；
  PNG SHA=`31f933a44a09a1fea4eb0189130cc8bfd1ee29191219af9195efc6de8e0a8536`。
  更新三类记录/联合进度/周报。v10未重启，冻结测试、gate和执行器未改；十小时任务继续。

## 2026-09-30 — 54回合检查点与可复算的公平三指标图

- 07:18 UTC核对main=`24c5bac6f26bae935d2367b952ebe0f97bb6fc5b`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，未出现上游变化。稳定v10服务未重启。
- 07:35 UTC前两个初始候选54回合完成：8录取/46失败，全部已核验归档；第三组c02运行。
  VMC合格唯一fixture为厚角2/短撞3/持续推碰0，但短撞3条来自不同候选，不能拼成单策略3/3。
  银行未锁定，BO/独立验证/collection/新ESN尚未完成，截止与预算不变。
- 新增`plot_teacher_bank_search_20260930.py`和测试：只画共同完整候选前缀，核对每条audit SHA、
  fixture/MJB、方法/录取与anchor集合，保留所有失败，partial另计。stage-waypoint RMSE与
  峰矩/峰速分列展示，不当平滑全局路径误差，不挑最佳点，不冒称重新复算物理轨迹。
  5项证据/搬移/不覆盖校验通过；首轮27点PNG视觉检查通过。可选campaign-root映射服务器
  读取根，原执行路径保留，v3旧图不重写。联合进度/周报/主报告同步更新。
- 以下均已逐文件核验至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`：
  `teacher_bank_review_checkpoint_20260930_0717/evidence/`含42文件（首轮PNG/PDF/点JSON/来源status/绘图源）；
  `teacher_bank_review_checkpoint_20260930_0722/evidence/`含36文件（支持服务器映射的新版源码/测试）；
  `teacher_bank_review_checkpoint_20260930_0736/evidence/`含36文件（54回合配对状态）。
  PNG SHA=`bf088ec34ac28340a6c19535654dc1d4f4d80885c63926e22643f2e1c9072824`，完整点JSON的
  SHA=`507cae91f03b65b2335c0c4fde6b08d09295dd46e1b1a1a1816f4f919b514c8e`。未改冻结源码或gate。

## 2026-09-30 — 完整首轮27回合及人手子步独立重建

- 06:26 UTC核对main=`f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`，均无新上游变更。v10相同服务稳定运行，未重启。
- 06:32 UTC第一轮c00三类×三方法×三anchor共27条全部完成，5录取/22失败并逐条归档；
  持续推碰三方法均0/3。status确认三个类别共同完整候选前缀[0]、模型hash与历史一致。
  进入c01；固定6候选搜索未完成、参数未锁定，collection=0、新ESN未启动。
- 新增`teacher_bank_person_anchor_review_20260930.py`及专题报告，原hash全匹配；每条550000
  物理子步独立重建schema2连续段，差≤1.22e-13。VMC1.2516s/9.09595mm，尚差0.90405mm；
  导纳宏观约27mm不能替代连续段要求；阻抗连宏观也不足1cm。力阈值间断不能当几何脱离。
  保留所有失败，不改gate/冻结环境或源。同步联合进度、周报和三类主报告。
- 新脚本/JSON/完整配对汇总38文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0633/evidence/`。
  review SHA=`2f94c7999c3732582e38b69e005c75e257dda84f510b1f190842ac8e145c7835`。
- f3b42f5完整源码2623文件已核验发布到同一服务器
  `/home/arm1/sii_shared/SII_compliance/source/f3b42f55f76c17e54d7c4ec7c55fb4b7cac6f985/`；
  tar SHA=`274e159481c6f9545ce705b0bcfee90455f0c8caf7433aa7b8357d4a0f931b11`。10小时任务仍继续。

## 2026-09-30 — 首两条VMC合格搜索轨迹复核，完整保留接触峰力

- 06:16 UTC核对main=`5ded01a21ed07f57c28786c616507ade46974289`、baseline=
  `5c4844b2d96339f696f6766b4a63cde2514cb547`及两分支日志，未合并baseline；Spark四个新worker运行，
  旧四个进程为T暂停态。本机v10稳定，未重启或新增仿真。
- 06:18 UTC v10完成21条搜索/5条录取/16条失败，另1条运行。共同c00配对：厚角VMC/导纳/阻抗
  0/3、0/3、2/3；短撞2/3、0/3、1/3。VMC持续推碰0/3，其余方法仍在运行；不提前作配对结论。
- 新增`teacher_bank_search_success_audit_20260930.py`及专题报告：VMC短撞337/671原hash与独立
  子步指标重算通过，冻结runner动作/状态重放通过。它们是初始参数搜索样本，不是BO改善，
  不代表独立验证。正式collection=0、参数银行未锁定，各类1000有效示范/新ESN未完成。
- VMC两条合格短撞接触峰力约1368/1350 N，阻抗合格短撞约2077 N；保留冲击风险局限，
  不用电机峰矩合规冒充低碰撞力/真实部署安全。未改变gate、模型或评分。
- status工具新增已完成rollout元数据哈希核验、接触载荷及原失败字段，不冒充独立物理复算。
  19项status测试通过；联合进度、周报及三类记录同步更新。
- 冻结源码输入审计：反馈控制器无直接外部真值字段，但共享task executive使用真实支撑/物块速度
  辅助松爪，并间接改变名义参考。专题文档明确该边界，不将当前系统称为端到端纯本体真实部署；
  本轮不修改共同协议或停止稳定作业。
- 已核验服务器根`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`下：
  `teacher_bank_review_checkpoint_20260930_0603/evidence/`（40文件，首次VMC复核源码/JSON/报告）；
  `teacher_bank_review_checkpoint_20260930_0621/evidence/`（38文件，06:18状态及status源码/测试）。
  原始轨迹继续逐条归档到`teacher_bank_three_domains_20260930_v10/`。10小时任务继续，截止不变。

## 2026-09-30 — 首个公平配对与pilot失败归因，v10继续运行

- 05:36 UTC核对main=`7423d5ef94df05470ba14188a983f92fc51846b1`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`，已读日志，未合并baseline。
- 05:49 UTC，v10厚桌角c00完成三个方法各3个anchor、同模型hash配对，录取VMC0/3、导纳0/3、
  阻抗2/3。统计含失败，不称泛化；参数银行仍暂定，作业继续短撞类别，本机单环境/1线程/3GiB。
  VMC合格新教师仍0，全部搜索、独立验证、各类1000有效轨迹及ESN未完成。
- 新增`tools/teacher_bank_pilot_failure_causes_20260930.py`及同名专题报告（研究目录内）：
  九条v8原始文件hash全部匹配，子步三指标独立重算差≤6.94e-18m，力矩/速度差0。
  球撞VMC主要晚期释放后滑落；导纳放置漂移、阻抗收敛超时。145mm误差跳变主要来自
  waypoint切换，不能当作碰撞末端位移。人推VMC/导纳约27mm宏观位移横跨微接触间断，
  不能说完全不会让位，也不能追认连续接触/schema2成功。原gate/源/失败记录未改。
- 归因JSON SHA=`c6d3469bea9113edf7416697d31950921b7d2fbf44da3f5016c2c74d6d020986`。
  41个新证据文件已核验至
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_checkpoint_20260930_0552/evidence/`；
  内含归因脚本/报告/JSON、当前status源码和v10_0549预算汇总。新增review归档的显式include选项。
- 已提交源码7423d5e的2618文件经SHA/大小/权限及完整文件集合核对，共享到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/7423d5ef94df05470ba14188a983f92fc51846b1/`。
  tar SHA=`47399ebcc9e6463d81f001a3112642ff362e45e9ee46f046efff37229b8cf13e`；初次tar compare
  仅因uid/gid不同而退出，之后独立核验内容通过才发布。新增源码归档核验工具，不改源内容。
- 更新联合进度、周报和三类专题。未重启稳定作业、未新增仿真槽位，10小时原截止不变。

## 2026-09-30 — 三类pilot审计完成，v10公平搜索启动（10小时任务继续）

- 05:19 UTC接续核对main=`8dec129deecf2b769e765c5d91a54a64140a22a7`、
  baseline=`5c4844b2d96339f696f6766b4a63cde2514cb547`并读日志。baseline的SimbaV2
  campaign_03在Spark四路训练，本任务本机单环境/1线程/3GiB，不修改其分支或作业。
- 已完成v6六条主动pilot、v8九条三类别pilot及服务器归档；v8仅阻抗厚桌角fixture0通过，
  RMSE47.988mm/峰矩45.612Nm/峰速0.15314m/s。接触18840段、其中一个5ms段以0.231mm上抬
  通过已注册曝光，不称平顺明显蹭过。VMC同场任务成功但上抬0.0866mm不足0.1mm，保留拒绝。
  当前合格新VMC轨迹为0，不把3300配置定义当成功示范。未启动新ESN。
- 新训练厚边缘移至掌翼上方，避开下降手掌；18项跨类初态预检通过。只改新增训练域，
  冻结综合测试/gate/actor/执行器不变。几何失败、旧corner曝光不足与v5失败全部保留。
- 修复人手曝光方向与施推时窗，schema2保存每个物理子步；旧schema1不追认为新筛选通过。
  修复搜索anchor的物体形状覆盖（0/337/671），独立验证固定0/1/11。候选成功anchor数量
  优先，之后比较失败标签代理及原评分；不把该离散代理称作连续物理超限。
- 每次dispatch核验实际Panda资产85文件，模型hash跨方法/候选/阶段一致；新增曝光-物理
  时间绑定、观察q/dq-前后状态绑定。九条旧pilot关联只读复核全通过，原audit未改写。
  搜索开始前73项测试通过。数值异常停机待分类，不吞异常或伪造BO指标。
- v8于05:23:21 UTC按预定阶段锁在pilot后停止，末尾BlockingIOError是计划内边界停止，
  不算物理失败。v9只准备未运行。v10于05:29:05 UTC实际启动固定6候选×3anchor搜索，
  首回合完成并归档，未通过接触筛选。服务`teacher-bank-search-v10-20260930.service`。
  计算窗口仍截止13:48:16 UTC；heartbeat保留到14:28只做最后归档审计，不扩展计算授权。
- 已核验服务器根：`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/`。
  其下`teacher_bank_three_domains_20260930_v10/`含源码210文件、metadata2文件、输入3文件，
  运行记录逐条发布。`teacher_bank_runtime_inputs_20260930/menagerie/`含实际Panda资产85文件；
  `teacher_bank_reaudit_v5_20260930/impedance/`为旧raw复审及源码；
  `teacher_bank_review_checkpoint_20260930_0527/evidence/`为34份新几何/pilot报告/计划停止证据。
  所有路径均已SHA256核验，未覆盖历史产物。
- 已更新README、联合进度、周报、三类专题及schema2/手掌阻塞诊断；新增独立审计测试和
  review归档工具。未完成：搜索、锁定参数验证、各类1000条合格teacher、ESN与正式泛化。
  `teacher_bank.json`搜索中只是暂定选择；截止partial block须单列，公平比较用共同完整预算。
- 搜索启动后另扩展只读status，独立核验decision/anchors/执行记录和模型hash、reuse/recovery、
  共同完整候选前缀、截止partial，以及完整搜索后才locked。该工具13项测试通过；没有改
  v10冻结源码或运行过程。实时PID核验需宿主上下文，沙箱生成报告可能看不到systemd进程。

## 2026-09-30 — 启动三类 teacher 数据与经典 baseline 的 10 小时任务

- 开工核对 main=`38caf3152282df4963435bb65c11c93a1e4fffa5`、
  baseline=`59342005b11b5892b18301fd9b52c6b07ad87f45`；开工时其日志仅有初始化，
  其工作区 `/home/arm1/SII_compliance_baseline` 不由本任务修改。
  04:15 UTC再次核对baseline已到`5bc21d8d19eaf60691f561f0ad9dd4409749e667`，已读新日志：
  SimbaV2奖励配对训练/GPU验证与布局合法性修正；不合并其分支，不占用Spark仿真槽位。
- 用户新增授权：三类各至少1000训练环境，VMC同时作teacher/model-based baseline，导纳/阻抗
  同场景同预算调参，多agent协作，持续10小时。窗口至2026-09-30 13:48:16 UTC。
- 新增 `tools/teacher_bank_{design,rollout,campaign,classical,exposure}_20260930.py`、相关测试和
  `docs/TEACHER_BANK_THREE_DOMAINS_20260930.md`、独立场景审查报告（路径相对研究目录）。
  生成3000训练+300验证配置，支持冻结源码、约束BO、原始/过滤动作、物理子步与接触曝光审计。
- 已完成34项新测试；动态pilot发现新训练桌角连接件初态与机器人相交，正确拒绝并归档，
  修正为绕手爪连接后42个初态预检通过。v4九条动态pilot已于04:16 UTC启动。
  v4完成一个有效物理回合但没有真实上抬碰face，不可入库；导纳adapter在仿真前失败已修。
  v5于04:30 UTC启动，VMC/导纳前两条均在align被训练face挡住，负结果保留，继续其他配对。
  尚无合格新teacher轨迹；未启动ESN、不改冻结综合测试或保留集。
- 已核验服务器源码/失败路径：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_three_domains_20260930_v2/`。
  v4源码206文件/metadata2文件也已核验归档到同一父目录下
  `teacher_bank_three_domains_20260930_v4/`，动态轨迹完成后逐条归档。
  不覆盖失败记录。详细实时状态和限制见上述专题文档。
- 新增进程身份恢复：仅确认旧PID已退出才另开retry目录，旧文件逐字节保留，基础设施失败
  不进入BO；新增只读状态汇总器。53项测试通过。公共评分移除对力矩阻抗不公平的action7
  平滑罚，补配对MJB一致性和阻抗命令→实际物理力矩审计。
- v5源码209文件、metadata2文件已核验归档到同父目录`teacher_bank_three_domains_20260930_v5/`；
  几何诊断/初态成功及失败的7份JSON已核验到
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/teacher_bank_review_archive_20260930/evidence/`。
- 重要纠正：旧corner task/strict成功不是“上抬碰face成功”证据。新曝光审计把桌面支撑与
  真实上抬碰边分开。十小时按98.3s首回合吞吐无法跑满9000次配对采集；搜索前预注册
  6候选×3anchors/方法/类、每类3个独立验证、之后剩余时间配对采集，3000有效数据目标未完成。
- v5阻抗完整仿真后审计触发3GiB限制，原因是NPZ逐行索引重复解压且保留整列view；已修为
  一次读列＋生成器，54项测试通过。旧raw独立复审4.39s成功，13750servo/550000子步实际力矩
  映射误差0；原failed execution不改写。该复审仅本地、待归档。
  v5现已停止；v6冻结源码的主动短撞/持续推碰六条pilot已启动，仍单环境/1线程/3GiB。

## 2026-09-30 — 协作 skill：双分支开工检查、本地计算与服务器归档

- 新增 `skills/sii-research-sync/SKILL.md` 与 `agents/openai.yaml`，安装至
  `/home/airpig/.codex/skills/sii-research-sync/`，允许自动选择。开工先 fetch/读取远端
  main、baseline 的 `UPDATE_LOG.md`；收工重新读取 `AGENTS.md`，记录并发布本轮进展。
  同步更新根目录 AGENTS 与 README，让未自动加载 skill 的后续 agent 也有入口。
- 本轮远端检查（2026-09-30，Asia/Shanghai）：main=`f098678ad1532f1b87c7e2ac803faa301c4c65ca`；截至本轮查询，
  远端没有 baseline 分支，因此无 baseline 更新日志可读。没有擅自创建分支或合并代码。
- 新默认偏好：尽量本地计算，服务器共享持久文件。共享目录为
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance`，源码按 commit 隔离，
  实验按 branch/run-id 隔离；先同步并校验，再把服务器绝对路径写入更新文档。
  本地缓存和实际执行来源保留，不改历史 execution.json，不覆盖别的 agent 或 runtime。
- 本轮归档的是已发布研究源码，服务器代码位置：
  `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/f098678ad1532f1b87c7e2ac803faa301c4c65ca/code/mujoco_6d_vmc_benchmark/`。
  此路径对应本轮开始时的研究代码；本轮 skill/文档更改以 GitHub 新提交为准。
  未全量迁移历史 outputs、原始大轨迹或 checkpoint，不声称它们已在新共享目录。
- 验证：仓库版与安装版 skill 均通过 skill-creator 的 quick_validate，目录内容一致；
  使用现有 `.venv-canonical-rl` 中的 PyYAML 完成校验，未安装新依赖。文档差异检查通过。
  本轮没有修改算法、环境或启动仿真。
- 已完成：skill 编写安装、双分支状态检查、共享目录创建与研究源码归档。2026-09-30
  03:10:53 UTC 逐文件校验服务器快照：2,592 个文件 SHA256 全部一致，无缺失或额外文件。
  本轮没有运行中的新实验；历史大文件仍在原位置，后续按实际任务逐批归档。

## 2026-09-30 — 积累成果同步与每轮自动提交约定

### 文件更新

- 新增根目录 `AGENTS.md`，落实用户“每次对话结束前 commit、push main、记录更新”的授权。
  新增本日志，README 增加当前状态与入口。此次同步的起点为 `2e37ddc`。
- 纳入 9 月 23 日至今未提交的研究代码、配置、测试、报告与小型证据：统一物理子步指标、
  经典控制器预算实验、canonical48D/action7 及参数动作 RL 对照、ESN 记忆消融、
  VMC＋ESN 联合优化、延迟球撞、综合环境的版本化开发、纯 ESN 与 MLP 比较和动作重放审计。
  各历史实验的冻结配置、失败原因与结论以各自报告为准，不合并为一个“全部成功”的结论。
- 纳入独立 teacher 修正实现 `scripts/vmc_teacher_stable_readout_20260930.py`、
  `tools/teacher_repair_campaign_20260930.py`、`tools/teacher_repair_followup_20260930.py`、
  `tools/audit_teacher_repair_20260930.py`，以及 `docs/TEACHER_REPAIR_20260930.md` 和进度、周报。
  上述路径均相对 `code/mujoco_6d_vmc_benchmark/`。
- 新增 `tools/export_publication_evidence_20260930.py`，导出 teacher 的小型审计 JSON、运行配置、
  源码快照及哈希索引到 `docs/evidence/publication_20260930/`。原始大文件不进入普通 Git：
  `results/` 下 NPZ/MJB、证据目录编译模型，以及原本已忽略的 outputs、视频等仍在原处。
  本次清单覆盖 results 大文件、证据 MJB 和三轮 teacher 输出，不覆盖所有历史 outputs 或服务器。
  小型 docs/evidence NPZ 仍纳入版本管理。没有删除原始数据；需要完整重放时还须取得清单中的本地产物。

### 已有实验结果（与本次发布检查分开）

- teacher 两轮完成 12 条有效 55 s、dt=1e-4 开发回合；动作、内部状态及过滤链独立重放误差为 0，
  每条 550,000 个物理子步复算指标。此前误用 MuJoCo 3.14 的四条诊断保留，不混入有效结果；
  有效实验固定 MuJoCo 3.11，并核对综合模型 SHA256。
- 当前候选 `velocity025_stiff2`：corner-placement 的 task/strict 均通过；综合单柱 v4
  task=true、strict=false（缺少要求的柱接触）。综合 waypoint RMSE 37.406 mm，峰值实际力矩
  48.127 Nm，峰值末端速度 0.070574 m/s，外部穿透 0.144922 mm。
  相对同模型原版，放置阶段动作差分 RMS 0.306187→0.042031，降低约 86.3%。
- 尚未完成：特化场景全协议与跨条件验证、综合 strict、正式 dt=5e-5，以及稳定 teacher 数据上的
  新纯 ESN 蒸馏。此次发布没有新训练，没有改冻结环境或 gate。
- README 中 9/29 的 delayed-ball 正式通过结果和早期 cup/pillar 综合失败属于不同版本；
  不可与当前单柱 teacher 开发回合互相替代，也不能据此声称 ESN 已全面优于 baseline。

### 发布验证

发布内容扫描：814 个 Python 文件（包含归档源码副本）语法通过，1,216 个 JSON 可解析；
已检查的私钥、GitHub token、AWS key 和含密码 URL 模式无命中。相关既有测试
`test_esn_load_gated_20260929`、`test_esn_impact_response_20260929`、
`test_office_canonical_audit_20260927`、`test_physics_substep_metrics_20260923`
共 9 项通过。发布集合约 60 MB，最大单文件约 7.6 MB，无超大单文件。
产物索引含 1,642 项、17,382,062,868 字节（含保留在本地的原始数据和已复制的小型证据）。
本次不重复运行已经完成的长仿真实验。
发布整理同时移除了八份历史 Markdown 的行尾空白或多余末尾空行，不修改实验内容。
`git diff --cached --check` 通过；推送前 fetch 确认远端 main 与此次同步起点一致。
