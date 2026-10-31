# 完整93混合回放的条件终端全量平均对照（2026-10-31）

本轮完成三方法、两方案、固定256步的隔离critic对照。条件终端全量平均使全部终端原masked SSE相对同预算对照下降I31.67%/A88.59%/V86.67%，原始抽样混合loss均值下降7.46%/7.17%/5.16%。不是仅把loss换成平滑估计值：原始loss和逐条误差另行复算。但I最差原始batch仍13.098且高于对照12.145，I新93误差改善弱于对照，V unmasked误差略退化；仍未收敛，未启动94或推广辅助权重。

## 数学定义与预检

原batch65536，critic j原分母D_j仍为Σ mask_ij×(1+127 done_i)。保留实际非终端样本、mask、冻结TD target及其误差。终端按完整五位mask组合s分层：全回放终端群大小N_s，当前原batch抽中c_s条。终端分子改为128×Σ_s(c_s/N_s)×Σ_{i∈s}mask_ij×(Q_ij−reward_i)^2，再除原D_j。

这是固定参数/回放、给定原batch的done和完整mask模式及非终端样本/目标后，对终端身份取条件期望；终端target本来就是reward，独立于pair和策略抽样。完整mask组合保留接受条件及分母，不能只按单critic随意合并。使用平方误差的平均，不是平均残差再平方；terminal128、奖励和目标不改。

32种可穷举终端抽样组合的float64预检：原loss均值和候选均为2419.24530514，五梯度期望一致；原条件内方差3566.62752而候选0。非二值mask/done、样本组合缺失于总体、零分母四反例拒绝。该枚举配合代数定义，不替代实际训练验证；期望损失/梯度关系不意味着相同有限采样值、相同Adam轨迹或相同actor结果。

## 实际范围与验证

精确恢复完整93全learner/Adam/replay/RNG和双架构marker。使用此前审计的原生64×65536批次，原均匀采样/接受规则、pair、策略及投影生成的target冻结。192批实际初始五critic预测与原raw逐元素一致，原loss复算通过；8353终端观察52/action/reward/mask与checkpoint及上一轮数据精确绑定。

两个副本克隆原五critic及原Adam/defaults，不改网络或LR。相同64批原顺序重复四遍、固定256次critic更新；每方案首步另用独立克隆精确重复，参数及Adam一致。1536次主辅助更新+6次重复=1542，正式更新0、physics0。actor/target/temperature不更新，目标冻结，因此不是完整native learner在线重放或独立泛化评测。

候选每步在原65536行前向外额外评估全部I2785/A2784/V2784终端，约4.25%更多critic行。相同optimizer步数不等于相同计算量；正式batch/UTD协议没有修改。原分母和mask数量保留；未额外提升新93、历史失败或任一行的期望权重。

保存0/64/128/256全终端预测、全部256步实际使用的估计loss；最终两个方案各64批完整q另存384数组，503365632字节仅SSD。独立审查原192 batch raw和384新q数组，复算原loss、条件loss、每critic/行贡献及完整mask组合。全部masked/unmasked误差和已知失败保留，九栏图已实际查看。三主进程完成，原learner、Adam、replay、RNG、grad及checkpoint hash不变。

## 原始误差，而非仅平滑估计值

固定256步后全部终端原masked SSE（I2785/A2784/V2784条）：

| 方法 | 初始完整93 | 原抽样对照 | 条件终端全量平均 | 候选相对对照 |
|---|---:|---:|---:|---:|
|阻抗|12060.416|12524.789|8558.503|−31.667%|
|导纳|1234.932|1809.006|206.385|−88.591%|
|VMC|964.600|950.111|126.660|−86.669%|

候选相对初始下降29.04%/83.29%/86.87%。旧≤85、86—92、93三组masked SSE（对照→候选）：I5921.195→1576.774、1482.145→1463.185、5121.449→5518.544；A1434.800→175.086、334.268→21.418、39.938→9.880；V906.706→109.787、26.528→9.769、16.877→7.104。I新93比对照差但低于初始6332.251，取舍保留。

固定64批，用原始抽样loss公式重算（均值/最大值）：

| 方法 | 初始完整93 | 原抽样对照256 | 候选256 |
|---|---:|---:|---:|
|阻抗|1.776825 /14.490334|1.693994 /12.145131|1.567660 /13.098103|
|导纳|1.138398 /1.516609|1.134561 /1.886037|1.053171 /1.417627|
|VMC|.798607 /1.241993|.777485 /1.287197|.737328 /1.006928|

I原batch31/32尖峰仍明显；不能以候选实际更新估计loss最大1.708掩盖原loss仍13.098。对照256步loss最大16.665/2.228/1.489，候选1.708/1.485/1.082；两种训练曲线统计量不同，单独保留。固定64批有限均值不必等于条件估计均值；期望关系不要求这64批恰好实现总体均值。

I新尖峰3851694 masked SSE：初始5893.163，对照4837.352，候选5329.678。旧90中止3726050为1252.204→1081.017/1201.826；92中止3804982为138.393→183.966/182.359，候选仍比初始差。旧51大退化2129963为1365.933→1282.790/193.352；71行2959115为229.280→54.257/.219970。所有已知行和三个中止均保留。

全部五critic unmasked总SSE对照→候选：I49137.385→44785.664；A49879.574→48522.249；V73425.849→74170.497。V旧≤85及86—92两组unmasked也更差，masked改善不证明全部critic健康。

## 下一步与保留状态

证据支持进入独立的完整native actor/target更新、增量终端缓存及checkpoint恢复兼容验证；尚无在线94登记。需证明原采样/RNG/目标/actor代码路径保留、终端集合随append-only增长准确、重载不会丢失估计器规则，继续报告原抽样loss及全部终端误差。通过后另行登记有限在线；不推广本轮隔离权重，正式父仍完整93。

原完整93 reward相邻变化8.803%/16.873%/62.877%、I/V峰32.685/17.469、原90—92窗口及固定92退化保持，未收敛。P/history未部署；hold.24对几何上界6.76及缺接触力记录结论保持。Direct33原数值验收和冻结全30 Task/Strict0/0、旧28内存证明缺失及恢复2全state不变保持，不添加Task成功为数值验收条件。冻结90完成勿重跑；指定ESN仍缺，最终独立比较待。

正式critic52、actor49/canonical48、clock49/history50/rawbit51、双marker/已学权重/Adam/RNG、append-only4m及历史23/47标记、terminal128/batch65536/UTD1/原LR reward masks、冻结physics/MJB/Task/Strict/filter/执行器/dt5e−5不变。partial75、不可评74—76、全部中止/失败窗口/halfstd拒绝/软件失败保留，无子agent。

少数后续源码读取使用旧runtime路径未找到文件，已改为实际continuation目录。首次写报告的工具调用发生JavaScript解析错误，整个调用未执行，改为独立命令重写；均未改变科学结果。本轮科学任务和独立复核全部通过。



## 来源、GPU与保存

实际主机 rltest-1025--a6ed2ff39b3c-t55ahnz53q，共享SSD /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，解释器 /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python。本轮实际query/fetch/read main 9bd8d0d8ce202f1a147e5aa5736fcf88e74bb96d、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，应用仓库sii-research-sync。源码 /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_terminal_census_ablation_20261031_v1；产物 /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation93_terminal_census_ablation_20261031_v1；PLAN/SOURCE_LOCK/LAUNCH绑定预算、解释器、设备、完整93父checkpoint与原批次来源。所有新作业结束，无新在线checkpoint。

原GPU guard继续，科学结束不退出；保存窗口120样本/602.717秒，最低[77, 64, 67, 67]%、低于50[0, 0, 0, 0]、末值[81, 77, 72, 71]%。含synthetic guard，不等于科研吞吐或每瞬时保证，不是重启服务。

SSD证据包 /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION93_TERMINAL_CENSUS_ABLATION_20261031/SMALL_EVIDENCE.tar.gz，39成员/3931989字节，SHA256 8a6c838194a2bafa5736cfc8bbc7a55ae5ee617f7862ed3b51ad2e1d6583751c，全部成员字节/AST核验。384个final q数组503365632字节仅SSD、逐hash核验见LARGE_STORAGE_REVIEW；原192 raw仍在先前SSD目录，不重复进Git证据包。manifest docs/evidence/RL_VIOLATION93_TERMINAL_CENSUS_ABLATION_20261031/MANIFEST.json；提交字节和实际push收据 /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION93_TERMINAL_CENSUS_ABLATION_20261031/GIT_BYTES_REVIEW.json、PUBLICATION.json。HDD配额满，仅原LATEST254字节原地更新回读，非HDD/arm1完整备份；主恢复入口 docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md。
