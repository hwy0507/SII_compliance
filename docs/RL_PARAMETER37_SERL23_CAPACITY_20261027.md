# 参数37与Direct23续训、Direct20–22稳定性及容量候选验证

2026-10-27。Goal active；未整体健康收敛，无子agent。最新实际PID/进度以本报告小证据FINAL_LIVE_STATUS.json和原run为准，不凭历史句柄重启。所有旧完成诊断保留，不重跑。

## 参数36完整结果与37接续

三方法各30个原条件、55秒完整、无abort；各新增41250条reward逐条重建误差0，旧replay全字段/history、2m容量marker保持。完整REVIEW/FINISHED、网络只读health、曲线和保存loss算术核验通过。

| 方法 | 总steps / updates | Task / Strict（30） | reward均值 | 末1000 loss | terminal MAE / in-bag MAE |
| --- | --- | --- | --- | --- | --- |
| Impedance | 1523250 / 1518251 | 18 / 17 | -2.410359232 | 2.583627036 | .752927 / .192635 |
| Admittance | 1522250 / 1517251 | 15 / 14 | -8.537313886 | 2.338312689 | .756086 / .362536 |
| VMC | 1523250 / 1518251 | 17 / 17 | -2.841403709 | .670456209 | .535022 / .233794 |

导纳reward较35改善，但末段loss明显上升；阻抗reward下降、loss仍高且有波动；VMC低loss波动。finite不等于健康收敛。原36–38固定窗口尚未完成，不改5%/近零1/配对bootstrap定义。

37三check-only全learner/replay/RNG及next65536精确，PRELAUNCH已读完整36及图；从准确完整36全state续一个有限37，原算法/物理/奖励/输入/动作/30pool/batch/UTD保持。正式I112738/A112739/V112740，启动1793070497.87；startup112742、archive112743、review112744。实际新增I/A1000、V2000的启动审查已通过，旧全部1523250/1522250/1523250行保留，新reward0误差。必须capacity replay+pair learner恢复，历史容量入口23不能改。

38仅恢复准备140023、原37审查释放CPU调度140026，登记runs/parameter38_preparation_registration_20261027_v1；7200秒等待原37 FINISHED/REVIEW后check-only，无自动训练。五入口同时替换、AST、65536保护、准确37父/38目标与历史23守卫通过。实际38恢复尚待，勿重启原准备。

## Direct22完整周期含一次安全早停

准确完整22为935790steps /7446328critic updates，新增40008=29×1375+133；不是预计41250条。30个条件均结束，其中29全55秒，passive_corner_train_0200第133步/5.32秒触发原global_penetration_exceeded_2mm，保存峰穿透2.710379222mm，worst pair为office_v5_corner_training_bridge_connector与66。保留physical_valid=false、Task/Strict失败和全部30分母；没有修改gate/时限或重试该条件。

Task/Strict0/30，reward -31.718349486（21为-30.907792497）；末1000 critic loss .013695120（21为.012554185），全轮均值.014403645，最大.039113179。曲线早期升高后下降；terminal MAE .037416328、32步TD MAE .046476327。完整raw/derived旧895782行、history/RNG保持，新40008目标精确、pending0；网络/优化器/RNG只读诊断通过。低loss不代表任务学会，也不把本次早停删出统计。

完整22父SHA a80f2acd24519be4c99e8002d8cd2707e0eb525d984e76a46874668d2c97d4cd。原23准备1605144完成，check-only全state/nextbatch精确及PRELAUNCH后，正式23 learner257351、startup257405/archive257407/review257409。原官方SERL10critic/random2目标/actor10均值/noentropybackup/8:1、32步行为回报、batch65536、原30pool与物理保持。23最多977040条，仍低于原1m；不凭预计步数替代实际完整checkpoint。实际启动审查结果见补充。

## 原固定20–22稳定性审计已结束

原等待3124904完成，19baseline、20–22窗口；登记时19/20已知，21零完成、22未启动，明确仅部分前瞻。完整30条件/源码/输入hash、保存算术与图核验；没有新物理或优化。

20/21/22回报均值-30.912665906/-30.907792497/-31.718349486；相邻变化.0157651%/2.6225004%，首尾2.6063219%，**通过原5%描述检查**。不能因Task0或这次早停事后发明新门槛否定这个算术结论，也不能把它升级为整个目标已完成。

19→22配对均值差-.136359804，18条件改善/12变差；原5000次分类配对bootstrap的95%条件组成敏感区间[-1.061864142,.543151240]；20–22均值斜率-.402841790/轮、敏感区间[-.805858850,-.098335806]。这是条件组成敏感性，不是独立训练seed或冻结策略置信区间。完整22安全失败及loss升高另行保留，参数稳定/原冻结矩阵仍待。

## Direct回放扩容：仅候选验证通过，未部署

新工具serl_replay_capacity_20261027.py和validate_serl_replay_capacity_20261027.py；隔离runtime/serl_replay_capacity_candidate_20261027_v1，结果runs/serl_replay_capacity_validation_20261027_v1。原唯一执行35329（timeout600秒、CPU52、CUDA不可见）已完成；AST/--help/真实验证/保存证据核验通过，0物理/learner更新/权重保存。

当前冻结multistep replay在1m处拒绝写入而不是环形覆盖；23可完成，但原预算下24会跨1m，需提前准备。候选扩大到2m、append不覆盖、只均匀采样mature rows；精确保留原32步target与ready/pending顺序/RNG。仅允许准确登记legacy digest导入，扩展恢复必须严格marker，2m满后写入前拒绝；不声称跨旧边界后与假想ring buffer学习等价。

真实输入是Direct22不可变startup，896782行=895918mature+864pending；原容量与候选下一批1/32/256/65536逐值及RNG精确、输入不变。三交错轨迹4/35/66共105行，迁移时4mature+38pending，继续与中途恢复逐步精确、独立32步折扣目标精确；16负守卫通过。有效合成999999前缀跨1m旧行不变；1999999前缀填满2m最后一格后拒绝覆盖。合成数据不推广。

真实startup不是完整23迁移父。**正式24尚未登记/准备/启动；下一步必须做capacity driver及marker lineage、准确完整23全state恢复/nextbatch、启动/完整周期/跨容量监控验证。** 不把本次replay-only验证当全learner更新等价或部署批准，不改正在运行的23。不能直接沿用原1m driver进入24。

## 仍运行的原任务与资源

冻结参数32原I2466385/A2466386/V2466387、根2466388继续原90×55秒/seed2026102638，0优化或正式replay写入；不要重启已完成回合，根REVIEW未完成前不称全矩阵通过。原固定参数36–38等待2889814继续。新混合23/37/冻结32 GPU固定60样本observer272271，结果见补充；之前换轮GPU0/1/2/3存在空档，不能以新窗口抹去。禁止人工占用或重复实验维持利用率。

本轮重新fetch/read远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变。每轮提交/推送按原授权执行，认证结果另记；不重复索取凭据或缺失指定ESN。HDD配额满，新小证据包/HANDOFF/收据放SSD，只覆写现有HDD LATEST指针并回读；大型checkpoint/replay/raw仍SSD，不称HDD/arm1全量备份。

实际启动补充：Direct23原startup257405已完成，新增1000至936790steps/7454328critic，旧935790 raw/derived/history/optimizer/clock保留，新143mature+857pending精确、30MJB/sampler/action/新reward0误差。原check-only与actual startup是两项不同核验，均已通过。四正式23/37持续，旧22/36及准备/启动审查已结束的不重启。

新23/37/冻结32混合原observer272271已完成，60样本/65.789744秒，GPU0–3均值[60.15, 73.8, 72.98333333333333, 66.31666666666666]%，逐样本7原PID身份保持，保存均值独立核验通过。非纯正式吞吐、不是每瞬时50%保证，不抹去已发生换轮空档；勿重采。
