# Direct29完整审查、27–29稳定平台、冻结29与有限30

2026-10-27，Goal active；主机 `rltest-1025--a6ed2ff39b3c-z3ntpmmalx`，共享SSD根B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，代码B/repository/SII_compliance。实际查询远端main `ecc0425a72029af28e21802e49cca10c3409426b`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，沿用本轮已fetch/read的未变日志；保留并行非RL。遵循sii-research-sync，无子agent。

## 完整29与原固定窗口

Direct29已完成30×55秒/41250新转换、无abort；累计1204290steps/9594328critic，Task/Strict均0/30，平均reward−30.909745861。原完整review/health、独立保存算术及hash通过，两张诊断/稳定性图已目视检查。旧1163040 raw/derived/history保留，全部新41250已成熟且32步目标精确，原930隔离pending未改变且不可采样，reward重建0误差；完整optimizer/network有限，诊断未改网络/优化器/RNG。未伪造完整25。

准确checkpoint `B/runs/serl_take_cycle29_archive_20261027_v1/direct/cycle_00029.pt`，SHA `ac54df0cb175ca64a0ba5956042cacd1391047b9f61179f103fd723e59daf2af`。

原固定27–29 reward−30.908317531/−30.909500493/−30.909745861，通过原5%检查；首尾变化0.004621185%，均值斜率−.000714165/周期，近零保护未触发。基线26已知、27零完整时登记的原窗口未改，5000bootstrap/seed2026102746保持；独立保存复核不重跑bootstrap，条件敏感性不确定区间不等于多训练seed。

29首/末1000 critic loss .010189882/.009746882，末值.009020314、整轮最大.022699149；27/28末1000 .010699524/.010136176，持续平缓下降。terminal MAE .025088271（870终端×10critics），32步TD MAE .027284449/max2.035084，Qmean−20.409403，temperature .000295965。单步TD MAE .052892972/max22.098869须与真实32步目标分开，不将单步尾部误当原优化loss。温度仍缓慢变化，图中无新增loss发散；这些结果支持本固定窗口reward平稳、loss未见异常，**不等同任务成功或冻结/泛化验证完成**。

从29保存checkpoint读取完整历史0..24、26..29：cycle0 mean−34.223282408，29为−30.909745861，描述差+3.313536547。各历史算法/基础设施阶段发生过变化，不能当单因素因果或冻结策略配对证据。保留partial25真实曝光而不编造完整25。Task0不作为额外收敛门槛，也不因此否认原稳定性检查通过。

## 固定29冻结评测已实际启动

原计划/seed2026102626/30条件/最大41250动作、33000000子步、0优化/回放写入保持。准确完整29 recovery-aware check-only通过：完整learner/replay恢复精确、外部动作RNG验证通过、930原pending raw/derived保持且不可采样，完整恢复后cycles26..29，历史partial25 SHA不变。原冻结41三路与root均已退出。

13:03:19 UTC原手动launch执行：evaluator2559665/2559670，各15case，CPU52推理/GPU0、physics53/54；rootreview2559674。目录 `B/runs/serl_take29_frozen_full30_20261027_v1`。两路已经进入第一条真实物理评测，尚未完整30；冻结16→29同条件/同seed比较仍待全量结果，不能提前宣称成功或优劣。原runtime703源码hash保持，不复用旧26评测计划。

## 第30轮有限确认与原结果的关系

完整29 fullstate/三65536批/RNG/再次恢复/全部history检查通过，原2m/entry23/930隔离保持。已经阅读27–29稳定结果、完整29health和两图后，决定继续**一个有限30**，观察已出现平台在温度继续缓慢变化时能否维持，同时其他参数方法仍在训练；这是额外确认，不增加新的强制收敛门槛，也不要求Task成功才承认reward稳定。固定冻结29使用独立29 checkpoint，不随30更新。没有自动31。

13:05:52 UTC learner2640251，CPU0–12/GPU0、30sampler；startup2640255/archive2640257/fullreview2640259。原10critic/random2-min/noentropy/8:1/batch65536/32步行为目标及全状态保留。目录 `B/runs/serl_take_cycle30_20261027_v1`。实际startup状态：已通过：1205290steps/9602328critic，完整旧1204290保留，新1000=149成熟+851pending，930旧隔离保持，30MJB/sampler及动作/clock/reward0误差。首1000无终端，完整30终端仍待。

原transition observer1132161已完整结束：Direct29进程退出→30spawn界395.229359–397.232218秒（约6.6分钟），期间包括全审查/恢复/科学检查与冻结启动，**不是GPU精确idle**。参数48→49界保留原记录。冻结启动和训练切换期有GPU0低利用，不能把此前29/48固定均值或单次瞬时数当本混合工作负载均值；待30真实更新稳定后再测一次有限窗口，不制造假负载。

参数49原I1717020/A1717023/V1717024继续；50仅恢复1864402，原49–51窗口2064574。新增参数49保存复核2350662，有限7200秒/CPU54nice15，原48复核只换cycle49、等原完整review，不新增训练/物理。参数48+49诊断见前报告RL_PARAMETER49_PROGRESS_20261027。

小证据 `docs/evidence/RL_SERL29_COMPLETE_20261027` 共88文件，逐大小/hash及AST核验。大raw/checkpoint/runtime/冻结轨迹继续共享SSD；HDD满只更新既有LATEST，不是HDD/arm1全量备份。接下来优先实际30startup、参数49完整审查/50决策以及原冻结29全30；Goal active。

补充：实际30startup通过，原2640255已退出。混合GPU观察2728080已完成，60样本/128.860044秒，各卡均值{'0': 63.6, '1': 60.05, '2': 65.9, '3': 59.666666666666664}%，每样本准确四正式learner+两冻结evaluator PID身份/GPU进程集合保持，独立保存均值复算通过。仅此窗口，非每瞬时50%保证，也不覆盖先前约6.6分钟进程切换。收尾fetch发现远端6bb57e5非RL54/72，第九组原始物理包归档；已读其日志和专题新增，保留并行成果后安全合并。
