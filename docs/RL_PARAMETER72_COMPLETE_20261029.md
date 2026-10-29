# 完整第72轮审查与准确有限第73轮接续

2026-10-29 00:40:40 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器env/bin/python。本轮完整审查72、独立核验、实际看图后决定准确接续有限73，非整体收敛声明。Direct33原训练条件数值收敛判断保持、TaskStrict0/0，不启动34。

## 完整72与原协议

三路原learner均自然完成30×55秒、41250新交互、noabort；全部旧71 replay字段/history保持，新reward按原冻结日志重建最大误差0，网络/optimizer有限。固定4m append、markers23/47、terminal128、batch65536、UTD1、原LR/masks/reward/物理/gates不变。未独立重积分全部原始物理。

|方法|最终steps|平均reward|Task/Strict（各30）|critic首→末1000|critic最大值|actor首→末1000|
|---|---:|---:|---|---|---:|---|
|impedance|3006648|-2.407331681|18/17|2.425788→2.401702|22.762974|26.268915→26.010672|
|admittance|3007250|-11.985219053|14/12|1.182205→2.166154|60.530479|-8.701363→-8.549468|
|vmc|3008250|-4.602758827|17/16|0.783421→1.164355|55.003189|-12.779944→-12.558400|

全41250 optimizer连续/全字段有限，独立保存算术、全180标签/90reward对复核通过。实际loss和health图已查看；有限值不能单独证明收敛。完整标签变化如下（保留Task-only变化）：

- impedance：physical-valid71→72 30→29（各30）；active_long_train_0000 task,strict，Task False→True、Strict False→True，穿透0.079543921→0.092703569mm；active_short_train_0600 strict,physical_valid，Task True→True、Strict True→False，穿透0.188544219→0.207759706mm；
- admittance：physical-valid71→72 30→28（各30）；active_long_train_0200 task,strict，Task False→True、Strict False→True，穿透0.100807496→0.090795801mm；active_short_train_0000 strict,physical_valid，Task True→True、Strict True→False，穿透0.112104343→0.233869207mm；active_short_train_0600 strict,physical_valid，Task True→True、Strict True→False，穿透0.197431139→0.200074958mm；
- vmc：physical-valid71→72 30→29（各30）；active_short_train_0600 strict,physical_valid，Task True→True、Strict True→False，穿透0.178658694→0.224663717mm；

## 全2154旧终端对比

从完整71提取的全部2154条固定终端输入与本轮新30分别报告，总2184，不与旧2124口径混用。独立保存数组/标量和实际图已核验；原V五focus及A原66short0600保持。

|路|旧2154 SSE前→后|变化|旧贡献（新总分母）|旧贡献（旧分母）|新30贡献|
|---|---|---:|---:|---:|---:|
|vmc|761.227960→1328.573581|74.5303%|0.064687530|0.065593115|0.369446650|
|admittance|1258.445655→6731.893154|434.9371%|0.327691701|0.332260964|0.856940200|

具体focus变化及图观察：

- vmc：index2050526 SSE20.070067→5.129325；index2299142 SSE2.952555→0.640952；index2046571 SSE1.093221→0.610078；index2423133 SSE186.596290→11.512801；index2423122 SSE1.995045→0.326813。
- admittance：index2752093 SSE18.461078→71.308625。

不作历史梯度因果判断，不把零终端误差新增为训练门槛。

## 续训决定与当前73

完整72三路各30×55秒/41250新增/noabort，全部旧71 replay/history保留，新reward重建误差0，网络/optimizer有限，全量loss独立算术与实际图审查通过。I/A/V reward−2.407331681/−11.985219053/−4.602758827，相比71−2.252441988/−10.109684327/−2.820382882仍有明显变化；Task/Strict18/17、14/12、17/16。全部180标签/90reward配对复核：I long0000和A long0200恢复TaskStrict，三路short0600及A short0000失去Strict；穿透分别I .207759706、A .200074958/.233869207、V .224663717mm，保留原.2mm阈值。Physical-valid29/28/29，各30，未遗漏Task-only。I critic首末2.425788→2.401702/max22.762974较平但actor下降；A1.182205→2.166154/max60.530479、V.783421→1.164355/max55.003189末段连续尖峰和均值上升，actor仍变，不能称整体loss稳定或收敛。Entropy围绕原−5/−7、temperature正且A末段升；I/A/V小比例当前soft-bound越界保留为诊断。全部2154旧终端V SSE761.227960→1328.573581升74.5303%，尽管原五focus都改善；A1258.445655→6731.893154升434.9371%，原66short0600/index2752093 18.461078→71.308625退化。新30贡献V .369446650/A .856940200高于旧.064687530/.327691701，两分母及完整数组/实际图已核验，不作因果解释，不新增零误差门。准确72全state/replay/next65536恢复三路通过；在原71–73预登记窗口内继续一个有限73，观察末段loss及任务标签变化是否持续。原68–70和bootstrap审查不变，原71–73还缺完整73，近零保护是统计解释限制，不是将reward推离零的目标。保持4m append/markers23/47/terminal128/batch65536/UTD1/原LR/masks/reward/物理/gates，不重置，不导入辅助权重，不自动74，Direct34false。

DECISION73 SHA `fb7759a731c257140ba634c9ed30ea788ef6b43cc14ab47dd0ea4ab647db1b23`，绑定48项证据。准确72全state/replay/下一65536恢复通过，有限73实际启动且startup通过；不重置optimizer/replay/RNG/history、不导入辅助权重，无自动74。

原68–70结果及独立bootstrap补充保持；近零保护限制相对统计解释，不是将reward推离零的新目标。原71–73 PLAN c160b5d6及原waiter保持，当前已有完整71和72，不能提前宣布三轮窗口通过。

|当前任务|PID / start ticks|
|---|---|
|73 impedance|2714363 / 42979895|
|73 admittance|2714364 / 42979895|
|73 vmc|2714365 / 42979895|
|loss73|2718561 / 42981213|
|window71_73|2909145 / 42204920|

00:40:40快照三路steps 3010447/3011131/3012181，新73全loss等待器已部署，原71–73等待器未重启。行动前核验实时PID/start ticks与输出。

## GPU、观察与保存

在途检查曾核验I/A/V各25086/25535/25564条完整日志前缀数值有限、步号连续，最新1000原字节及独立算术通过；该前缀只代表当时，后续完整41250审查已保留A/V末段新增尖峰，不能用早期前缀掩盖它们。

本轮完成边界observer按最多1800秒/30秒登记，实际61样本、1800.928秒，观察结束时全部当前审查就绪标记为False，本报告保存前另行确认全72审查/标签/终端/73仅恢复已实际完成；原71–73未来窗口不被误作本轮必须完成项。观察本身不启动或停止科学进程。

从观察开始到当前快照共516个guard样本，四卡最低74/63/64/60%，低于50计数[0, 0, 0, 0]，最大间隔5.366860秒。原v5五进程身份保持、STOP/FAILURE不存在。含合成占用，非科学吞吐或每瞬时保证；用户要求科研完成后仍保载，继续保持，非跨重启服务。

开工实际fetch/read main9e7e44ce25bef5a7971f1f3abf6b8c147ce811f9、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d。收尾实际fetch/read main8dec2341602b9cacb78c1ac799307bd99907d433、baseline未变，并安全fast-forward保留非RL学习曲线/原108观察/读出诊断，未操作其进程。遵循sii-research-sync，无子agent。

共享SSD归档 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER72_COMPLETE_20261029_004039/SMALL_EVIDENCE.tar.gz`，254成员/3074199字节，SHA `6deafd4669d347d4f7cdf148598a55fd525a12b6060e9edfae60eacad43eaee8`，逐成员字节/Python AST核验。[保存收据](RL_PARAMETER72_COMPLETE_20261029_SAVE.json)。大checkpoint/replay/raw留原共享SSD；HDD满只重写既有入口，非HDD/arm1全备份。

下一步保持原73与guard；准备73完整标签及终端审查、等待原71–73，继续基于完整结果判断reward稳定和loss健康，不因有界观察结束重启科学任务。Goal active。

发布同步补充：首次push因远端并行新增6fe74b6c而非快进拒绝。已读取非RL第二条件审计/八球v4接续保护，安全合并保留双方AGENTS/UPDATE_LOG新增原文与共同历史，冻结RL runtime未改。此同步发生在上述科学小证据包之后。
