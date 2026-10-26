# 参数终端误差集中度、第27轮跟踪与28续接（2026-10-26）

Goal active，整体收敛未证明。当前四路原正式训练与冻结16矩阵继续，按完整checkpoint审查接续；物理/MJB/SPT/canonical48/action/critic clock/全部正式网络与优化器/RNG/回放历史不变。无子agent，不导入辅助权重、不回滚重置。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl；R=B/repository/SII_compliance，原HDD仓库为该路径链接。开工实际查询/fetch远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa及baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变。继承已读sii-research-sync；认证失败用户此前已问，不重复问；大产物仍SSD，小交接/收据HDD，不是arm1/HDD全备份。

## 当前已完成的稳定性依据

原交接建议已在B/runs/serl_cycles13_16_reward_stability_20261026_v1及parameter_capacity24_26_reward_stability_20261026_v1落实，原审计已结束勿重跑。Direct回报趋稳，但13→16改善+.134343主要降低穿透/峰矩惩罚、全30仍approach；完整17仍0/30。阻抗24–26回报变化<5%，但均loss涨；导纳26退步且末loss2.1504；VMC26改善但仍波动。回报稳定与任务成功分开，不把短平坦或全state有限当整体健康收敛。详见前交接RL_REWARD_STABILITY_AND_FROZEN16_20261026.md。

## 新只读导纳终端误差集中度

B/runs/admittance25_26_terminal_concentration_20261026_v2，原3292216已完成，0优化/0物理/0replay写入。准确完整25/26冻结checkpoint，只恢复完整agent权重做CPU前向，不恢复或运行优化器；agent权重和前向torch RNG不变、原checkpoint全部hash前后不变。与既有health使用相同float32减法后float64汇总，terminal/inbag MAE逐数完全一致。所有源/runtime/helper和输入hash冻结。

v1原3239960在首次MAE一致性守卫失败，原source/registration/FAILURE保留。原因是先转float64做减法，而旧health先float32减法再float64汇总；25差约1.17e-9、26约2.42e-9。v2复现旧算术，保持原1e-9守卫而未放宽；贡献分析另明确用float64。未改正式精度或数据，失败不能抹去。

对所有终端行计算每个critic的128×mask×(Q−reward)^2，分母取该critic全部保留回放的sum(mask×(1+127×done))，再对5critic求和。终端无bootstrap，故不涉及mean/min目标对或熵采样。它是冻结全回放加权目标中的终端部分，排除普通TD项；不是随机minibatch比值的期望，也不是原在线loss重放。分母/行值NPZ和独立保存算术核验已完成，图已目视核对。

| 完整父 | 终端数 | 终端总体损失贡献 | 最大1行占比 | 前5行 | 前10行 | 当轮新增30终端占比 |
|---|---:|---:|---:|---:|---:|---:|
|25|774|.087947846|14.6604%|37.8925%|52.1599%|13.9389%|
|26|804|.729292495|41.6861%|63.5517%|73.0483%|45.3732%|

该终端部分增长8.292329倍，误差集中；旧终端也贡献显著，不是只有新行。

最大新行是active_short_train_0600的第26轮终端，replay index1103000（全局step1103001），真实终端reward−28.47190094。当前5critic Q为[20.928867,−11.864782,12.112422,−10.202142,−21.627302]，mask[0,1,1,1,1]；第0 critic在该样本留出，不能把它的误差算成该critic拟合失败。其加权总体贡献.304013416，占终端部分41.6861%。同条件旧25终端index1064501 reward+22.7577095，在26权重下Q为[22.833977,22.976887,21.646549,21.918407,17.759348]，mask[1,1,1,1,0]；旧行贡献.000262954。

这对样本存储的50维critic observation L2=.02550284、动作L2=.92116001，并非完全相同输入。25/26各自全部终端中均未发现完全相同critic observation+action但奖励符号相反的配对。近邻距离只是存储归一化坐标下的描述，不是学习度量，也不证明或排除历史信息缺失。当前证据不支持直接增加critic特征/改terminal权重/LR。前时序审计提示该新失败入库附近loss抬升，本次证明其在冻结26终端损失中占比大；仍未重放历史抽样批，不能把时间关联写成在线因果证明。

新保存值独立审查SAVED_VALUE_REVIEW.json复核5critic权重/分母算术、top占比/hash并生成terminal_concentration.png；不重算神经推理或动力学。新源码audit_admittance_terminal_concentration_20261026.py、review_admittance_terminal_concentration_20261026.py，原v1/v2和已完成review均不重复。

## 第27轮固定终端跟踪（完整完成）

B/runs/admittance27_terminal_anchors_20261026_v1，原3440440完成勿重跑。预先固定26全部804终端和重点index1103000；27中原804行observation/action/reward/mask逐值不变，加新30共834。复用26预测，仅27冻结权重CPU前向，0优化/物理/replay写入，agent权重/前向RNG/输入checkpoint hash不变；仅恢复agent权重，不称完整优化器恢复。

固定804条mask加权平方误差5527.899475→683.216563，比例.123594245（下降87.6406%）。27全部终端总体贡献.096164213，其中旧804贡献.086936044、新30贡献.009228168；旧804使用原26分母仍仅.090162038，改善不是分母增长稀释。重点short0600旧失败行masked SSE2303.516289→115.118200（下降95.0025%），27 Q为[19.924397,−27.065901,−18.046534,−26.782530,−27.207344]，mask[0,1,1,1,1]；critic0留出，critic2仍有约10.43误差。实际同一批样本恢复支持继续原设置观察，不修改terminal128/LR/critic特征。终端部分不等于全部在线loss，更不等于整体回报收敛。

保存值已独立复核masked SSE、每行加权贡献和NPZ SHA，不重新前向或仿真。terminal27_values.npz SHA256 42696e2479624dccf9e3aae2122e36a0ef7fbd75484fe7277e9c309f28cb1583。

## 完整27与正式28

27全部三路30×55秒完成、无abort，全部41250新reward重建误差0，旧replay全字段/history/2m历史marker保持、网络与优化器有限；REVIEW/health/FINISHED及图通过。原I2286139/A2286140/V2286141、归档2286144/review2286145、准备3057098和CPU调度3269264均结束勿重复。

| 方法 | steps / updates | Task / Strict（/30） | reward | 最后1000 q_loss | terminal MAE | inbag MAE |
|---|---|---|---:|---:|---:|---:|
|阻抗|1152000 / 1147001|18 / 17|−2.280261931|1.563277974|.775625757|.224874740|
|导纳|1151000 / 1146001|13 / 13|−10.333074684|1.387413927|.635908391|.221904671|
|VMC|1152000 / 1147001|17 / 16|−4.588803669|1.214168423|.725755373|.371584200|

导纳从26 Strict11回到13但未恢复25的16；VMC17降至16且末loss上升；阻抗回报较稳。A/V抽样Q超过当前必要soft上界比例.00214843755/.0009765625，不能将有限网络或终端恢复称全部优化健康。

准确完整27父位于B/runs/parameter_capacity_pool30_cycle27_archive_20261026_v1/{method}/cycle_00027.pt：
- I SHA72908e7f936f022eaa5c3108f699fcaa15617e14c7010baaba02b27c0b3c7674。
- A SHA4c184c88a05151386247c3ac70f0425cfb108da3a672a1ddf90cb83970466ce1。
- V SHA442ae95946c097ded3fcbf1eba5b6d09429c0156e1b5a0bf9c6214a0909f1b3f。

28三check-only完整learner/原replay/下一65536/RNG精确、继承负守卫通过。2026-10-26 21:51:31 UTC正式28启动：I3733553/A3733556/V3733557，B/runs/parameter_capacity_pool30_cycle28_20261026_v1；startup3733613、归档3733614/完整review3733617。准确最新27全state接续一个周期，保持2m历史入口23、capacity replay+pair learner、原GPU1/2/3、CPU13–51、30pool/batch65536/UTD1/terminal128/projection/Imin+A-Vmean/actor min/原LR。容量超过旧1m后的全保留采样不同于原环形覆盖，不能称整体算法等价。真实首1000检查以startup/REVIEW.json为准；无自动29。

Direct18原2732254、归档2732257/review2732258继续，实际首1000检查已通过，完整父17为730782/5806264、Task/Strict0/30。19 prepare/launch/setup已备，等待3088320只在完整18后check-only，不自动训练；原2732254退出守卫/CPU0，570→600终端、CPU range(1,13)不变。一次review调度3269262等待18退出后用释放CPU0，deadline7200。

冻结Direct16完整30条件原evaluator1749189/1749193、review1749197继续，目前两分片各10条共20/30，未全矩阵完成；固定seed2026102626/55s/最多33000000子步，不变更预算或重复。CPU52推理、53/54物理，GPU0共享推理；不是held-out/多训练seed/确定性mode或指定ESN最终比较。先查原RESULTS/POLICY_UNCHANGED/REVIEW/FAILURE。

## 运行和交接约束

新28启动需要恢复与实际采样，27→28审查和恢复存在GPU1–3空档，不能隐去。旧18/27混合观测30样本31.596516秒均值60.5/69.5333/66.5333/69.2667%仅代表该旧窗口，不外推新18/28。持续核对真实PROGRESS与四GPU占用，不重复已完成实验填负载。

本次重新实际查询/fetch/read main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变；完整冻结参数/环境和另一任务保持。GitHub认证待恢复，不重复询问。最新收据见docs/evidence/rl_parameter28_terminal_concentration_20261026/FINAL_ARCHIVE_RECEIPT.json；大产物仍SSD，仅小交接与收据HDD，不冒称完整HDD/arm1备份。

参数28实际启动检查已通过：I1153000/A1152000/V1154000，分别新增1000/1000/2000，旧I/V1152000、A1151000所有回放字段/history/优化器超参/2m历史marker/30MJB/30sampler/action/clock及新增reward0误差；原3733613已结束勿重复。四正式18/28及归档/完整review继续。

新18/28运行占用窗口30样本/31.663424秒，四GPU均值61.8333/69.4333/68.7667/69.0333%；逐样本四正式及两冻结evaluator均live。它包含冻结16推理，不是纯正式吞吐，也不保证每瞬时≥50%或覆盖先前交接空档；原一次观测已结束勿重复。

本轮科学提交495d577cc1676caf35eac1c2fb609de8eb0de797仅本地；重新fetch远端main dbb1d76/baseline f6e8f8c未变，push仍HTTPS用户名认证失败。完整小证据包/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER28_TERMINAL_20261026_215524/FULL_SMALL_EVIDENCE.tar.gz，94成员逐hash核验、1576516字节，SHA256 5c4ae048b5459ee9f8e886fba680a25caf8cead71b84e0e7110e99b1ee430aec。HDD小交接/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_PARAMETER28_TERMINAL_STATUS_20261026_215524/HANDOFF.md及收据/LATEST已核验，大checkpoint/replay/raw仍SSD，非HDD/arm1全备份。Goal active，原四正式训练与冻结验证继续。
