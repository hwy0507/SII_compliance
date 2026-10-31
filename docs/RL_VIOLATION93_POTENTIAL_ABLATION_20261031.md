# 完整93全回放因果进展信号与隔离信息消融（2026-10-31）

本轮实际核验全部11566262条保留回放，重建原日志可得的动作前payload potential及短时历史；全部6列保存结果又用独立算法逐行精确复算。随后完成三方法×三方案×256次固定终端拟合以及9次首步重复，共2313次仅隔离副本的更新。结果不足以部署候选特征：阻抗较同预算对照略好，但较初始完整93仍显著退化，导纳/VMC较对照更差。没有推广辅助权重或启动94/Direct34；Goal active，仍未收敛。

## 全历史可用性与因果性

原complete85已核验谱系加86—93实际登记链，共每方法89个日志根。完整93 checkpoint精确校验双history/rawbit架构marker、边界、4m容量及历史23/47标记；读取全部原transition/journal并绑定hash，按原全局step映射，保留部分回合和全部失败。每条current canonical48/context/clock、混合动作、reward/done、next canonical48/clock与原回放精确一致；current/next reward potential与原journal/TERMINAL精确一致。原观察的history/rawbit及masks没有重写；全部8353终端的原52维、动作、reward和masks另与checkpoint精确绑定，旧8263终端与此前固定92输入逐元素一致。

| 方法 | 完整93保留行 | 回合群 | 终端 | 保留partial群 | 缺完整raw但本次信号可得的行 |
|---|---:|---:|---:|---:|---:|
|阻抗|3852762|2820|2785|35|27936|
|导纳|3856250|2820|2784|36|28250|
|VMC|3857250|2820|2784|36|29250|

提取三个候选量：当前动作前P、(P−上一动作前P)/.04、当前及最多前13个P的max−min（最长.52秒跨度）。初始差分按定义0，窗口在回合开始处截短，未填补未知物理状态。prefix扰动/截短测试验证未来P不能影响此前特征。终端next候选列按预登记复制current，匹配原终端next canonical观察复制语义；实际terminal potential仅参与独立reward一致性核验，不用于current特征。无Task/Strict、未来状态、最终hold或cycle/condition输入特征；actor输入不变。

保存每方法全行current3/next3 float64 sidecar，共555180960字节，仅共享SSD。第二实现从原transition的reward potential重算，通过单调双端队列实现过去窗口极值，逐行核验全部6列，与首次journal/滑动窗口实现相互独立；全部行恰写一次/恰审一次。全部原checkpoint文件hash保持。这里证明信号可得与对齐，不证明其包含缺失接触状态或足以修复尖峰。

## 固定隔离消融

每方法从完整93恢复全learner/Adam/replay/RNG，克隆原五critic及原Adam状态。三方案均在第一线性输出、原LayerNorm/激活前增加同形状的零初始化三列线性分支：baseline三列均0；potential仅第一列非0；potential_history三列均非0。旧52维+动作的权重、偏置和Adam逐项保留；新分支使用原optimizer默认设置。所有方案初始全终端预测精确等于原critic；每方案第一步在独立克隆上精确重复，参数/Adam更新结果相同。

仅cycle≤85的原终端参与拟合，I2545/A2544/V2544；86—93各240条只用于辅助拟合之外的检查。**原完整93本来已见过这些检查行**，所以不是独立泛化测试。feature均值/std仅由拟合集计算，固定后应用于检查集；std≤1e−8按1，均保留保存值。三方案各固定256次完整终端batch、原五critic masks和sum masked MSE；纯终端中terminal128相消。没有actor/target/temperature更新，不是原生65536混合batch、历史训练重放或未来在线序列。

保存0/1/16/64/128/256全部终端预测及256条loss，未选最佳epoch。独立复核保存输入、scaling、所有指定点masked/unmasked SSE、与相应pre-update loss以及全部最终统计；实际九栏图检查通过。主副本全learner、Adam、replay、RNG及参数grad与checkpoint保持不变；三方法GPU1/2/3、CPU10/11/12，单线程，9个提取/审查/消融进程均结束。辅助网络不推广。

## 结果：候选不足以部署

固定256步时，辅助检查集原masked SSE如下（越低越好；各240条，所有mask保留）：

| 方法 | 初始完整93 | 同预算baseline | +当前P | +P及历史 |
|---|---:|---:|---:|---:|
|阻抗|7856.226|10557.360|10214.522|10095.772|
|导纳|98.360|84.376|86.489|91.932|
|VMC|165.060|81.307|85.424|87.872|

相对同预算baseline，阻抗两候选−3.247%/−4.372%，导纳+2.504%/+8.955%，VMC+5.063%/+8.074%。阻抗候选仅缓和“只拟合旧终端”的退化，并未优于原完整93。拟合集相对baseline有所改善（I−12.14%/−17.45%，A−.87%/−1.93%，V−.39%/−1.18%），不能据此替代较新数据上的结果。

阻抗新93尖峰index3851694原masked SSE5893.163，256步baseline8778.845、P8483.616、history8348.267，全部变差。原90中止3726050由1252.204至1389.208/1345.666/1357.347，全部更差；92中止3804982由138.393至157.617/156.541/101.641，history改善。拟合集中的旧79中止及51/71大退化样本被大幅拟合：2129963由1365.933至.635924/.130091/.096578，2959115由229.280至.004596/.004298/.001356。全部有利/不利样本及原masks均保留。这支持继续检查旧、新终端的学习分配，但不是原在线93的梯度冲突因果证明。

未mask的预测误差也保留，不能只看参与loss的critic。固定256时检查集全部五critic unmasked SSE：I14514.844/14138.785/13887.216；A2280.104/2281.649/2274.268；V7166.584/7170.010/7174.425（顺序baseline/P/history）。部分critic未受对应行mask监督，不能把masked改善当作全critic健康。

全部256次辅助loss中，A三方案早期峰约8.979/8.961/8.965，V约7.446/7.766/7.638；原Adam面对终端only分布的瞬态没有隐去。后期loss很低不是原在线loss已健康；上述曲线与真实混合训练不直接等同。

## 后续决策与原约束

本轮不部署P/history，也不把辅助低loss当作收敛。下一步在原生混合回放上有限比较旧、新终端学习分配或梯度稳健性的候选，保持原masked/unmasked SSE和全部失败的独立诊断，区分降低梯度波动与实际减少原预测误差。任何采样/目标/网络协议变化仍需单独登记、原state兼容恢复和实际在线证据，不自动派发94。不得用替代loss数值更小宣称原异常已解决。

完整93各41250新增，92→93 reward相邻变化8.803%/16.873%/62.877%及I/V loss尖峰32.685/17.469、原90—92窗口结论保留。原固定92终端I总SSE+16.95%及所有critic/行退化保持。上一轮hold.24对上界6.76、接触力条件不可重建的结论没有被本轮P可用性推翻。

正式critic52、actor49/canonical48、clock49/history50/rawbit51、双marker/已学权重/Adam/RNG、append-only4m及23/47历史标记、terminal128/batch65536/UTD1/原LR reward masks、冻结physics/MJB/Task/Strict/filter/执行器/dt5e−5均未改。全部partial75、不可评74—76、79/90/92中止、冻结90中止、失败窗口/halfstd拒绝/软件失败仍保留。Direct33原数值验收与冻结全30 Task/Strict0/0、旧28内存证明缺失及恢复2全state不变保持，不将Task成功附加为数值收敛条件。原93和冻结90完成勿重启；指定ESN仍缺，最终独立比较仍待。无子agent。

开工首次fetch遭TLS握手失败，重试fetch成功并重新读取两分支日志；实际远端SHA与记录一致。全部本轮科学任务与独立复核均成功，未重启或覆盖旧作业。


## 来源、GPU与保存

实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮实际query/fetch/read main `8b50530f3209fb6eceb5d1272f1cc55460081208`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，首次TLS fetch失败后重试恢复并重读，应用仓库sii-research-sync。审计源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_potential_audit_20261031_v1`、消融源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation93_potential_ablation_20261031_v1`；产物 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation93_potential_audit_20261031_v1`、`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation93_potential_ablation_20261031_v1`，各自PLAN/SOURCE_LOCK/LAUNCH及逐输入hash绑定预算、解释器、设备、checkpoint与真实源。全部9进程结束，正式完整93仍为科学父，没有新在线checkpoint。

原GPU guard继续，科学结束不退出；本次保存窗口165样本/833.499秒，最低[74, 72, 68, 64]%、低于50[0, 0, 0, 0]、末值[83, 77, 72, 79]%。含synthetic guard，不等于科学训练吞吐或每瞬时保证，不是重启服务。

SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION93_POTENTIAL_ABLATION_20261031/SMALL_EVIDENCE.tar.gz`，69成员/8485976字节，SHA256 `6ac8a0fc1ed1905c3fb5f770b3abdff3de9d5c9a8eca3f2dd0852e552b6dfc96`，全部成员字节/AST核验。全行sidecar总555180960字节仅SSD、逐hash核验见LARGE_STORAGE_REVIEW；它们不进Git证据包。manifest `docs/evidence/RL_VIOLATION93_POTENTIAL_ABLATION_20261031/MANIFEST.json`，提交字节及实际push核验收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION93_POTENTIAL_ABLATION_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原LATEST254字节原地更新回读，非HDD/arm1完整备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
