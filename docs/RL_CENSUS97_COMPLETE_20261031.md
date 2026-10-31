# 第97轮完整训练、终端诊断与原loss审查

**Goal active，尚未宣称参数RL收敛或最终公平评测完成。** 原97三路有限训练及归档/比较/新终端只读任务已完成；不重启已完成97，不回退96。未自动派发98；后继仍须根据实际结果单独登记并从完整97精确恢复。科学结束仍保留GPU guard。

## 完整97

|方法|完整步数|Task / Strict|回合reward均值|原loss均值 / 最大|原loss末1000均值|
|---|---:|---:|---:|---:|---:|
|impedance|4017762|18 / 16|-4.200142451|0.983269 / 1.776896|1.007540|
|admittance|4021250|15 / 15|-6.807196863|1.040633 / 1.620523|1.033271|
|vmc|4022250|17 / 17|-2.870846981|0.723587 / 1.227645|0.721074|

完整旧回放和历史元数据保持、新reward按原journal逐条重建、实际600万容量与历史marker保留；完整原loss日志/全部NPZ/独立标量复算通过。所有已登记loss、health、全90比较、固定8623终端及新90终端图均实际查看；各PLOT_INSPECTION记录内容与SHA。数值健康判断仍以original_sampled_q_loss为准，不能用条件估计器loss替代。

本轮将上一轮识别的next context证据缺口补齐到全部新97数据：非终端全部52维next与同条件下一current精确，全部current context绑定原日志，30终端/方法的next context符合原终端复制规则；所有新行覆盖，不再有快照尾部未配对项。原线上代码/checkpoint未修改。

## 条件与终端

- impedance: 旧终端masked SSE变化-39.2546%，退化1210行；新97终端masked SSE 14.699449600；Task新增[] / 丢失[]，Strict新增[] / 丢失['active_short_train_0100']。
- admittance: 旧终端masked SSE变化-45.5714%，退化693行；新97终端masked SSE 17.833413025；Task新增['active_short_train_0600'] / 丢失['active_short_train_0900', 'active_long_train_0900']，Strict新增['active_short_train_0600'] / 丢失['active_short_train_0900', 'active_long_train_0900']。
- vmc: 旧终端masked SSE变化-19.5282%，退化1478行；新97终端masked SSE 1.946828270；Task新增[] / 丢失[]，Strict新增['active_short_train_0600'] / 丢失[]。

新增90个终端全部保留，包括失败；8713总终端CPU参考完整保存，旧8623完整97预测逐值复现既有消费者。全部5critic与原mask均保留，learner/Adam/replay/RNG/checkpoint不变。新终端残差、short0600跨96/97任务事件与奖励分项、最大原loss时序均记录；实际采样索引未保存，时序相邻不证明因果。线上每次更新的总终端人口与done累计精确、最终32分层计数已核；线上逐分层tensor内容未记录。

原94–96 A/V reward不稳定及V96 loss尖峰8.7554保留。前瞻97–99规则保持，仍缺完整98、99，不能用本轮完成代替稳定性。Direct33原训练数值验收保留，不因冻结Task/Strict0/0追加34；原28最终内存证明缺口/恢复2证明与指定ESN缺失保持，最终独立公平比较尚待。

## 恢复与保存

98仅静态候选已准备：`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census98_preparation_20261031_v1`，继承原第三容量stage，trainer只改有限预算标签，replay恢复期望与完整97逐值相同。尚未实际恢复、验证native下一更新或启动98；必须先单独登记有限决定及完整恢复/消费者/启动审查。

主机`rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD根`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，Python`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。最新父为`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle97_archive_20261031_v1/{method}/cycle_00097.pt`，完整SHA见`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census_cycle97_review_20261031_v1/REVIEW.json`。完整科学审查`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census97_completion_20261031_v1/COMPLETE97_SCIENTIFIC_REVIEW.json`；新增终端`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census97_new_terminal_diagnosis_20261031_v1`。旧96/原97/有限消费者已完成勿重跑。

原进程有限观察1560.332s/53样本。新增终端binder将总报告passed误用于方法报告，推理前KeyError导致原observer结束；原源码/失败/日志保持。只读修复改为总passed加方法记录逐字一致、state/checkpoint/values哈希核验，随后完成原登记诊断；所有完成标记另行复核，未重跑训练。完整比较图收据与原前5000收据重名被拒绝，已另存FULL97收据，旧记录未覆盖。GPU448采样最低[83, 65, 67, 68]%、低于50次数[0, 0, 0, 0]，末[88, 73, 69, 72]%；含合成guard非科学吞吐，不是每瞬时保证。guard`/tmp/sii_gpu_util_guard_20261031_recovery_v1`继续，勿创建STOP，非重启自启服务。

远端main9a8dcac7/baselinef6e8f8c2已实际query/fetch/read。SSD小证据`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS97_COMPLETE_20261031/SMALL_EVIDENCE.tar.gz`，128成员/8269131字节，SHA256`0c9d5873c31b7b7330b72792bf4cb6d7a3e66da71c8b8a2954a8eb87f8405d87`，逐成员字节/JSON/AST核验。大checkpoint/replay/raw仍SSD，HDD仅既有254-byte LATEST指针，非HDD/arm1全备份。实际发布核验见`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS97_COMPLETE_20261031/PUBLICATION.json`。
