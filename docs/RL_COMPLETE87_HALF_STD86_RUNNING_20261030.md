# 完整87尚未收敛；冻结86方差配对评测实际运行

2026-10-30T14:28:00.386430+00:00。Goal active。原87及全部后续审查、原冻结86全部16回合均已完整结束；不重启这些任务。原85—87稳定性检查三方法全未通过。基于现有seed敏感性证据，已独立登记并启动唯一候选：固定完整86模型、同四组合×同四seed，将pre-tanh Gaussian std乘0.5；最多16回合/22000动作/1760万子步、0更新。新评测仍在途，不提前宣称改善；无自动88/Direct34。GPU科学结束仍保载。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮实际查询/fetch/read main `f47cd2386691ef6bb7e33f46e4359658ea6f2180` 与 baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；收工复查main已到49fb9ae13b5dafc3e2c24e459f05079dffba3f58，实际fetch/read其v7 MLP支持域诊断、恢复拟合审计及报告后快进整合；非RL改动保持，RL冻结runtime不变。按仓库sii-research-sync同步，无子agent。

## 完整87与健康检查

三方法各30原条件×55s、41250新增、无安全中止；完整旧replay逐字段精确保留、新reward重建误差0、网络/optimizer全部有限。原4m append-only、容量历史23/47、terminal128/batch65536/UTD1、原LR/reward/masks/filter/physics/gates保持。

|方法|累计steps|平均reward|Task/Strict /30|critic首→末1000|critic max|actor首→末1000|
|---|---|---|---|---|---|---|
|impedance|3606448|-4.216507780|18/16|2.513269→2.390679|36.255867|21.006076→20.732389|
|admittance|3608750|-8.562139916|15/14|1.253357→1.350164|14.275924|-8.652642→-8.539310|
|vmc|3609750|-4.589780404|17/16|0.816799→1.135634|27.572735|-12.091111→-12.105521|

全loss图含尖峰、health图、V/A终端图均实际查看并保存PLOT_INSPECTION。I首尾均值下降不能掩盖末段从中段回升；V末段loss明显上升，A基本约1.2但末尾尖峰保留。entropy约I−5/A,V−7，alpha有限正值，Q未整体塌缩；不等同loss健康已确认。采样Q超固定alpha全局界比例I0/A0.0001464844/V0.0023925782，诊断而非新验收门。终端in-mask MAE为I0.438088/A0.173765/V0.253886，out-mask为3.436292/2.415404/1.916477。

86→87全187保存rollout标签核验通过。I short0100外穿透0.162323→0.201807mm新Strict失败；short0600原失败仍在。A long0200/0900 Task失败、long0500/short0900 Task恢复，short0600穿透0.188750→0.230166mm新Strict失败。V short0600为0.188604→0.218863mm新Strict失败，原0.2mm gate不变。

- impedance: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_partial75_recovery_cycle87_archive_20261029_v1/impedance/cycle_00087.pt`，SHA256 `2a9e586a7f35c1388deb9a429bbb907a931e3035ac74fa7433ddd5b4d15d8e87`。
- admittance: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_partial75_recovery_cycle87_archive_20261029_v1/admittance/cycle_00087.pt`，SHA256 `819d9c29d202909f7760b38ec1bf2ecd72305c819ee11f87634eb986027c6579`。
- vmc: `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_partial75_recovery_cycle87_archive_20261029_v1/vmc/cycle_00087.pt`，SHA256 `0d996484d92822c78bdddd55a7f4854d2c563dd1c82dc694e43056e61d5ae57f`。

完整审查 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_partial75_recovery_cycle87_review_20261029_v1`；loss/labels/terminal证据见本包同名runs目录。三原learner及全部后续均为已核验终态，不能依据旧PROGRESS再次启动。

## 原85—87窗口与固定终端群体

原PLAN `6d6eebaae137a85a1e715234513b9f6e9799a5e08bdc27b89e832a70c685b51e`，seed2026102858、5000bootstrap、nearzero1、5%、anchor55与原4h截止保持。完整窗口和所有bootstrap抽样标量独立审查通过，但三方法稳定性条件均失败。I reward−0.590930→−2.408941→−4.216508、Strict18→17→16，near-zero保护触发，相对变化不定义；端点差95%区间[−9.027732,0.007020]。A相邻变化22.473%/27.983%，V38.266%/62.095%；A/V端点近似不代表中间稳定。A端点差区间[−4.878116,5.043456]，V[−5.295160,5.331534]，这是条件bootstrap敏感性而非独立训练seed泛化。

同一固定2514旧终端/all5 critic跨84—87的输入/动作/reward/mask一致；前瞻PLAN `7cb97319d8b3cb10e862ebb1ada6dbfe79d97b87cc04035facd3be04d348346d`，保存预测核验/图已完成，0新forward/physics/update。V总SSE9046.061→3556.825→1158.553→2829.904，86→87四critic退化，仅critic4改善；critic2为99.796→1192.429最大退化。A1283.626→3932.823→2110.926→1036.234，四critic改善，critic3为195.430→374.886退化。全部分项保留，不引入新健康阈值或历史抽样因果解释。

另一个原86 anchor2574群体：V1205.453→2959.256，重点2423133为56.484→844.758，2423122为21.174→1.624；A2974.555→1126.414，2752093为56.984→12.016。新87的30终端对完整loss贡献V0.220010/A0.089248。2514与2574分母不同，不混写。

## 原冻结86全部16回合

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter86_frozen_switches_20261030_v1`，原PLAN `42dc5ea17bbcde872335568ca6c02da16f42620500b8a6d31b9021bc43fd8234`。四组合×动作seed2026102633/34/35/36，共16完整55s/22000动作/1760万子步，0optimizer/replay更新。最终全learner/optimizer/RNG/replay不变、native动作重放、原审计和独立raw全子步/全部动作复算通过；reward最大重建误差1.4210854715202004e−14。全16图已实际检查。

|组合|Task/Strict /4|reward范围|外穿透mm范围|
|---|---|---|---|
|impedance_short0600|4/2|[-34.90051388978959, 19.392583368648918]|[0.18689634349688636, 0.23544876280354185]|
|admittance_short0900|3/3|[-33.26043671333201, 17.784769750108616]|[0.09615643022538727, 0.12185939338872957]|
|admittance_long0200|3/3|[-33.27186966557599, 17.385764204120168]|[0.09342826203400366, 0.09625924526594742]|
|vmc_short0000|4/4|[18.60783074991156, 19.117544701079282]|[0.10546821854464686, 0.13920495500856736]|

I seeds33/34越过0.2mm导致Strict失败，35/36通过，Task全真。A两组合seed35在carry失败，其余三通过；case哈希产生不同RNG流，不推断普遍坏seed。V四次全过不能证明零失败概率。冻结29已建立敏感性，当前86是新的固定模型/条件复核，不是首次发现或历史因果分解。

## 唯一半标准差干预与两次预检失败

运行 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter86_half_std_paired_20261030_v3`，runtime `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/parameter86_half_std_paired_20261030_v3`，PLAN SHA `0d857019e679d3b86c69498cda6a6c39e94264839e771779a69d4a620ada9c89`。相同完整86checkpoint/四组/四seed、同原物理初态与所有gate；仅原actor forward输出的log_std减ln2，同输入mean逐位保持。保留原clock pre-hook、tanh/动作限幅/native CHEQ混合。序列化权重/optimizer/replay/RNG不变，但采样策略行为有意改变，不能写成policy unchanged。高斯pre-tanh熵在同输入减少d·ln2，不等于最终动作std减半或训练target_entropy等价。

v1 PLAN1370af9a：raw forward误收50列而线性层需49；v2 PLANe6c06513：module误收49列，原clock pre-hook期望50列。四组各次check-only均在EVALUATION/physics前失败，退出记录、源码、注册和日志全部保留。v3通过actor(obs50)保留原hook，包装内的cached raw forward接收49；真实native接口随机初始化检查先通过，随后四真实86完整checkpoint恢复、native/external动作一致及56设计/metadata负例全部通过。修正不新增科学预算，不删除失败。

实际LAUNCH四评测PID1280069/1280072/1280075/1280076，start574382314/315/315/315；reviewer1280079/start574382315。启动后全state/replay核验、实际400保存动作/canonical48/MJB/CPU7–10和原physics-action循环AST一致，所有未变native helper hash一致，改动sampler明确分列。新观察7样本/180.012秒，原35+新5身份保持live或已核验完成。快照进度 `{'impedance_short0600': (1, 2026102634, 200), 'admittance_short0900': (0, 2026102633, 1200), 'admittance_long0200': (0, 2026102633, 1200), 'vmc_short0000': (0, 2026102633, 1300)}`；这只是进度，最终16结果/不变证明/paired图仍待。

等待既有reviewer产出FINISHED、REVIEW、PAIRED_REVIEW与PAIRED_SAVED_REVIEW，必须审全部16的Task/Strict增减、reward/穿透/安全中止和实际图，禁止挑seed、搜索因子或自动晋升。任何后续训练修订独立登记，父训练仍完整87，不能从诊断86回退训练。原SAC target_entropy=−dimension未进入PublishedLearner state_dict/load；未来若改训练熵目标，须版本化序列化/恢复/诊断并验证，不能只赋值后声称可恢复。当前未建立任何88或Direct34。

## GPU、恢复与保存

原v7守护supervisor97370/start570509460、workers97399–97402/start570509475仍保持；控制目标70%、阈值50%。本轮363样本min `[74, 63, 63, 63]`%、低于50次数 `[0, 0, 0, 0]`，末值 `[82, 79, 79, 79]`%。用于保活的合成负载不是科研吞吐，科学结束后仍保留。历史v7预热0及v6 GPU0=31/GPU2=33/44低谷不删除；采样不保证每个瞬时，非系统重启自启服务。源码已随包保存。

Direct33数值阶段接受，冻结33全30 Task/Strict0/0、中断28最终内存证明缺失；指定ESN仍不可用，不替换他主机模型、不重复追问。冻结82完整90已于f47cd238发布，不重跑；partial75、原74—76不可判、原所有历史稳定性结论和79真实安全中止保留。科学Goal active。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_COMPLETE87_HALF_STD86_RUNNING_20261030/SMALL_EVIDENCE.tar.gz`，521成员/5928164字节，SHA256 `abd952ef75dd76d84d3d80afd5656fcf190c65511fb1e66de06cec50a7bf9a60`；逐tar成员字节/源码AST已核，Git index/commit核验另存。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份。HDD LATEST只原位更新254字节指针，不能当全备份。运行文件为时间点快照；成功正常push并实际观察远端后才在包外写PUBLICATION.json。

发布验证补充：原始.diff及冻结SAC源码快照保留原字节/空白，未改运行源。git whitespace检查先报告该原SAC快照既有尾空白；仅排除这些原始证据后的新增源码/文档检查通过，全部520项manifest与527个暂存blob逐字核验通过。
