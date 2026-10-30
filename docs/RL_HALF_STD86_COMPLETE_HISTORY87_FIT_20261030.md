# 半标准差全16已审；完整87历史接续与配对critic拟合完成

2026-10-30，Goal active。固定86半标准差试验全部16回合完成并独立审计，改善与退化并存，不推广统一降熵训练。完整87三路历史sidecar已准确接续；新增唯一匹配预算的terminal critic拟合诊断已完成。所有科学子任务正常结束，GPU守护继续保载；没有88/Direct34训练，不宣称收敛。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮实际ls-remote/fetch/read main `80de539b27bc629b1aa0a73869dd3bed55d97843`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，收工main新增a62ddb87bcfeb2dc42766f652e8815e5c770eba1的非RL共同观测动作/高负载诊断，实际fetch/read日志及报告后快进保留，RL runtime不改；按sii-research-sync发布，无子agent。前轮熵状态软件准备是实质进展，但不等于科学方案已选定。

## 固定86半标准差全部配对结果

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter86_half_std_paired_20261030_v3`，原PLAN0d857019，四组×seed2026102633/34/35/36，全部16×55s、22000动作/1760万子步、0optimizer/replay更新、无abort。最终全learner/optimizer/RNG/replay不变、native动作重放、原物理/filter/torque审查、全raw独立复算均通过，reward重建最大误差2.1316282072803006e−14。序列化state不变但采样分布有意改变，不写成unchanged policy。

|组合|Task原→半std /4|Strict原→半std /4|平均reward差(半std−原)|
|---|---|---|---|
|impedance_short0600|4→4|2→0|-26.961714299|
|admittance_short0900|3→2|3→2|-13.287299083|
|admittance_long0200|3→4|3→4|12.412997544|
|vmc_short0000|4→4|4→4|0.222927040|

I四次外穿透0.203194–0.222372mm均超过原0.2mm，seed35/36新失Strict；A short0900 seed34新在lift失败，seed35原carry失败保留；A long0200 seed35恢复；V全部4通过但连续指标仍有增减。两张实际结果图已查看并保存hash/解释收据。完整16原始数据与配对报告交叉对齐，无挑seed/改阈值/新因子搜索。结论：不支持统一降低采样方差，且该推理干预本来就不等价训练target_entropy。前轮持久化adapter保留为软件准备，未部署为训练修订。

## 准确完整87因果历史接续

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery87_history_extension_20261030_v1`，PLAN SHA `b5e9fd0b37c0d6e1b800cda60d2c425c6bd10e9e8ede089f8eee31571e50795d`，登记CPU53/torch1/900秒、0physics/forward/update/replay写入。实际主审164.373秒。逐方法加载原完整85与87，全部旧replay数组前缀按shape/dtype/原字节hash精确相同；复制已审85历史sidecar，不改变原partial75/截断cohort。

新增完整86/87每方法82500、合计247500 transition逐journal核验current50、next50、混合动作、reward/done与global step，交错episode索引恰覆盖一次。preaction历史只用本动作前已完成区间的累计外穿透；next使用下一条journal，terminal仅用于最后done行的next，不把末峰值倒灌。独立保存审查重新标量读取原日志/journal及全部追加值，旧sidecar前缀逐位一致。该字段不是79中止时global穿透，不删除79原异常；也不是独立物理子步重建或部分可观测性必然成立的证明。

- impedance: 3523948+82500=3606448 rows，终端2605；sidecar `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery87_history_extension_20261030_v1/impedance_causal_history.npy`，SHA `2ee30dd5bd7555ed5cb9654de314056a11cefc220121d044e0958cef494d94be`。
- admittance: 3526250+82500=3608750 rows，终端2604；sidecar `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery87_history_extension_20261030_v1/admittance_causal_history.npy`，SHA `8c1bd3f9c9c6760e6993f50df14aa16ec29f54cfb41a4fea957b54922b900a80`。
- vmc: 3527250+82500=3609750 rows，终端2604；sidecar `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery87_history_extension_20261030_v1/vmc_causal_history.npy`，SHA `de66eb4e7e84aaacc8c6c772519dacf9d46d431cc315673f65d41d391121566d`。

全部历史总rows10,824,948。动作前已知外穿透>.2mm的行I88075/A76552/V58224，其中86/87新增3720/1279/1279。终端行I2605、A/V2604，保留所有原终端和历史中止，不强行三方法统一删成2604。

## 相同预算的终端critic拟合诊断

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/recovery87_terminal_history_paired_fit_20261030_v1`，PLAN SHA `87121b4a682d0301b23abe7904e82ff48bc31e617352926a7306bfd193d26c58`。完整半std/独立raw/实际图、准确87历史全部审完后，明确登记唯一离线配对：三种方法各原critic clone与history clone各500步，共3000 cloned Q Adam步，CPU53/GPU1/900秒，实际129.883秒。不更新原checkpoint、actor、alpha或target network，不保存/晋升辅助权重；无新物理或88训练。

两臂都使用完整87全部终端、原动作/reward/bootstrap mask、每步相同全batch。loss为各critic mask内MSE之和；全部dones=1所以Bellman不bootstrap，terminal128在每critic分子/分母相消。优化器从同一原Adam states/hyperparameters恢复，旧参数和moment逐位保持；history只在观测索引50插入一个有界因果峰值 `p/(p+0.0002)`，首层新权重和Adam新moment为0。actor canonical48及原正式模型完全不改。

原clone与原模型初始预测逐位相同，增加零列后允许原先登记的1e−4数值容差；全部原参数/moment插入映射检查通过，原checkpoint SHA与完整父learner/RNG最终不变。没有reset优化器或按结果挑step。保存全部501个端点、all5 SSE和所有原终端预测，独立float64/math.fsum重算首末mask分母、SSE/loss、符号错误。

|方法|原终端行|初始原loss|500步原输入loss|500步历史输入loss|历史−原|
|---|---:|---:|---:|---:|---:|
|impedance|2605|14.999322993|5.016654152|4.428005333|-0.588648819|
|admittance|2604|1.588093403|0.054331443|0.047021926|-0.007309517|
|vmc|2604|4.001034273|0.868632134|0.508920872|-0.359711261|

实际六栏图已查看，所有方法/critic/500步全部保留。该比较只说明本次已见终端样本上的拟合表现；不是未见测试、在线reward改善或历史信息唯一因果。checkpoint87已经训练过这些数据，没有假称held-out。不能把离线拟合曲线当正式训练loss健康或收敛。

下一步应据完整配对结果评估是否独立登记因果history critic在线修订。若推进，须统一扩展replay/current-next观测、全state/Adam迁移、actor隔离与CHEQ不确定性接口、checkpoint版本和恢复/health/frozen-eval入口，并验证真实起步；仅凭本次离线收益不能跳过这些。父训练仍完整87，不回退诊断86，不晋升离线权重，也不自动重复原配置88。

## 保存与范围

GPU从history登记起145采样，最低 `[76, 74, 76, 71]`%、低于50次数 `[0, 0, 0, 0]`，末值 `[80, 78, 80, 79]`%。原v7 supervisor97370和四worker身份保持，科学完成后仍合成保载；不以占用冒充科研吞吐，历史低谷保留、不保证采样间每瞬时，非重启自启服务。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HALF_STD86_COMPLETE_HISTORY87_FIT_20261030/SMALL_EVIDENCE.tar.gz`，141成员/3309516字节，SHA `70f854a044e5427e7396e4f647db43bdba3fbf75a19ba901e7f74d5b07aab56b`；tar逐成员/AST核验，Git index/commit另核，成功push和后续实际远端确认后包外PUBLICATION。大型history sidecar/checkpoint/replay/raw在上述原共享SSD，非HDD/arm1全备份。HDD LATEST原位254字节更新，原521/99成员恢复包引用保留。

完整87与85—87稳定性失败及loss末段回升保持；Direct33数值阶段接受但冻结30 Task/Strict0/0，中断28最终内存证明缺失；指定ESN不可用，不替换他主机模型、不重复追问。partial75、74—76不可判和79安全中止及其他历史窗口结论均保留。Goal active，最终仍需四方法收敛、冻结评测和指定比较。
