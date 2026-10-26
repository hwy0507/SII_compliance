# Direct19接续、16–18策略变化与17→18奖励退步（2026-10-26）

Goal active，整体健康收敛仍未证明。完整Direct18已审查，19已接续并通过实际首1000步检查；三路参数29继续。新有限诊断只读完整16/17/18和保存日志，未改变物理/MJB/SPT/gate/canonical48/action7、正式网络/优化器/RNG/replay/history，不导入辅助权重，无子agent。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，R=B/repository/SII_compliance；大产物SSD，原HDD仓库是该路径链接。

## 完整18与正式19

Direct18完整772032steps/6136264critic更新，30×55秒无abort，Task/Strict0/30，reward−32.239452388，相较17的−30.984683957退步。新41250单步reward与32步派生目标精确、旧730782 raw/derived/history/ready保持，pending0；完整网络/优化器有限。570终端×10critic MAE.048109151/max1.021331787，32步TD MAE.064622529（17为.045479108），Qmean−20.565374374、alpha.000588874449。REVIEW/DIAGNOSIS/FINISHED及图审查通过；低且有限的日志loss不单独构成整体健康收敛。

准确18父B/runs/serl_multistep_batch65536_cycle18_archive_20261026_v1/direct/cycle_00018.pt，SHA256 f5cc09541af8f61a136687a86f81143e17274a33b5cadd14528ab499902d5a85。原2732254/归档2732257/review2732258，以及等待准备3088320/CPU调度3269262均退出勿重跑。

19恢复check-only全learner/旧replay/下一65536/RNG精确、负守卫通过；PRELAUNCH_SCIENTIFIC_REVIEW记录因18回报和TD退步继续一个有限原设置周期，同时检查策略变化/奖励归因。正式19 learner1326215，B/runs/serl_multistep_batch65536_cycle19_20261026_v1/direct；GPU0/CPU0、30sampler共享CPU1–12，官方10critic、random2/min bootstrap、actor all10mean、noentropy backup、8:1、batch65536、32步/gather+transfer保持。没有推广温度或actor floor候选，无自动20。

实际首1000新增启动审查通过：773032steps/6144264critic，全部旧772032 raw/derived/history/优化器/marker保持，147新mature+853pending精确，30MJB/30sampler、canonical48/clock/action映射及reward0误差通过。原startup1326256已完成；归档1326258/完整review1326260继续。

## 新17→18奖励分项归因

B/runs/serl17_18_reward_terms_20261026_v1，原1439233完成勿重跑。两轮各41250、共82500条保存的reward_terms逐项汇总，核每条分项和reward一致、每条件1375条与完整episode reward一致，所有输入hash前后不变。0新物理/优化，依据完整review已从物理interval journal重建的reward，不是重新执行子步动力学。

17→18平均reward差−1.254768431，其中penetration−1.229066994、peak_torque−.026572407、progress−.001198246，occupancy+.001394621、torque_slew+.000674595，terminal/time/comfort/contact/efficiency等差0。穿透项占净下降97.9517%。26条件退步、4改善；最差active_short0200为−3.419466，short0500−3.318625、short0900−3.299824；passive0500改善+1.099717。仍全30approach，任务并未推进；这是精确保存分项归因，不是动作变化导致穿透的因果证明。

## 固定输入上的16–18策略变化

B/runs/serl_cycles16_18_policy_drift_20261026_v1，原1439232完成勿重跑。在完整18退步可见后登记，探索性固定窗口16/17/18、seed2026102630。使用完整16全部510初始行及不放回uniform4096行，确认它们在17/18原回放所有字段逐值保留；每个checkpoint全网络/优化器/计数/动作与本地RNG恢复精确，推理前后完整learner和replay digest一致，原checkpoint/source hash不变。GPU0只读前向/default正式精度、同外部随机draw；0优化/新物理/replay写入，不保存推广权重。

初始510行实际只有**1个唯一canonical48输入**，不能当510个独立条件；uniform4096包含4094个唯一输入。保存49维观测和actor48维去clock后的唯一数都已核对相同。重复初始行只提供同一输入上的外部噪声采样，不证明输入设计有错或需要增加特征。

| 完整父 | 同一初始输入public0 mode | 初始残差mode平均绝对值 | 初始采样熵 | uniform采样熵 |
|---|---:|---:|---:|---:|
|16|.935059488|.463110358|−22.248177|−3.932148|
|17|.982342124|.526844442|−22.869190|−3.950916|
|18|.999162972|.590679169|−29.320381|−4.202475|

public0=(raw0+1)/2，0为nominal、越大越减慢WBC。mode为官方API tanh(location)确定性输出，只是离线前向，不是新的确定性物理评测。均值和熵来自固定样本/外部draw，非独立训练seed。

| 固定输入策略比较 | 初始7通道平均绝对mode差 | uniform平均绝对mode差 | 初始latent KL旧→新 | uniform latent KL均值 |
|---|---:|---:|---:|---:|
|16→17|.185168584|.112004568|556.686951|27.707902|
|17→18|.221484980|.141227357|3900.930331|38.537423|
|16→18|.291087417|.185281080|6609.434505|83.271525|

小latent std会使KL很大；这些指标描述固定输入上的分布变化，不是任务效应、因果估计或新增收敛硬阈值。当前证据不支持把先前reward平台等同于策略不再变化，也不能把critic终端拟合好等同于任务成功。没有据此直接改LR、温度、状态特征或奖励。历史14温度next32覆盖差异和raw-next1有限候选已完成、不支持部署；本轮不是重新发现或重跑该候选，亦不重复/延长已完成floor探针。

保存值review_serl16_18_policy_drift_20261026.py独立用另一等价表达式重算latent KL、mode/耦合采样差值、30条件分项和输入hash，SAVED_VALUE_REVIEW通过；只检查保存值，不重算前向或动力学。policy_drift_and_reward.png已目视核对。原REVIEW及NPZ/图和source均入小证据。

## 当前其他原任务与下一步

参数29原I946578/A946579/V946580、归档946583/完整review946584继续，最新完整父28及启动审查见RL_FROZEN16_FULL30_PARAMETER29_20261026.md。固定参数27–29稳定性原4175982仍待完整29，原5%/近零1/三类5000配对bootstrap及已封存27输入不变；无自动30。该报告将决定后续参数训练的科学动作，不能提前称稳定。

冻结Direct16全30原1749189/1749193/review1749197已完成退出，不重跑；Task/Strict0/30、全部approach，无abort/机器违规/人体接触，舒适NA，完整物理/filter/torque与state不变通过。它仍非held-out、多独立训练seed、指定ESN或最终SPT比较。指定ESN尚缺，已问不重复、不替代。

新一次纯正式19/29 GPU观测B/runs/batch19_parameter29_gpu_profile_20261026_v1，原1785987，预登记60样本、严格每样本四原GPU learner，等上述两个诊断结束后运行；无新增GPU负载、不按利用率重采，先查原结果。

本轮查询/fetch/read真实main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变。按已读sii-research-sync提交与归档，GitHub认证仍失败，不重复问用户。小证据docs/evidence/rl_serl19_policy_drift_20261026；HDD小交接/收据、checkpoint/replay/raw仍SSD，非HDD/arm1全备份。

纯正式19/29资源窗口已完成：60样本/68.572054秒，四GPU均值58.1500/75.3500/66.5167/69.1667%，逐样本GPU PID恰四正式且原learner身份/live保持，无辅助GPU。仅本窗口均值，不保证每瞬时或过渡期；原1785987已退出勿重采。

本轮科学提交e07903bc8f73600ab41af1c97aae95595ebe423e仅本地，push认证失败。完整小证据包/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_SERL19_POLICY_DRIFT_20261026_225138/FULL_SMALL_EVIDENCE.tar.gz，47成员逐hash/大小核验，3022648字节，SHA256 1e330da1d73176fdd4f94f57aa5dfa90289eef648ec347a669e53b55b1cdda1c。HDD最新/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_SERL19_POLICY_DRIFT_STATUS_20261026_225138/HANDOFF.md及收据/LATEST已核验；大产物仍SSD，非HDD/arm1全备份。新增30准备等待2031399与原29审查CPU调度2031400，不自动训练；原19/29和固定稳定性审计继续。Goal active。
