# 完整第71轮审查与准确有限第72轮接续

2026-10-28 23:34:29 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器env/bin/python。本轮完整审查71、独立核验、实际看图后决定准确接续有限72，非整体收敛声明。Direct33原训练条件数值收敛判断保持、TaskStrict0/0，不启动34。

## 完整71与原协议

三路原learner均自然完成30×55秒、41250新交互、noabort；全部旧70 replay字段/history保持，新reward按原冻结日志重建最大误差0，网络/optimizer有限。固定4m append、markers23/47、terminal128、batch65536、UTD1、原LR/masks/reward/物理/gates不变。未独立重积分全部原始物理。

|方法|最终steps|平均reward|Task/Strict（各30）|critic首→末1000|critic最大值|actor首→末1000|
|---|---:|---:|---|---|---:|---|
|impedance|2965398|-2.252441988|17/17|1.762973→2.328908|38.577110|26.388201→26.257922|
|admittance|2966000|-10.109684327|13/13|1.420316→1.170214|24.514984|-8.770752→-8.708112|
|vmc|2967000|-2.820382882|17/17|1.327331→0.856005|24.339268|-12.943230→-12.790413|

全41250 optimizer连续/全字段有限，独立保存算术、全180标签/90reward对复核通过。实际loss和health图已查看；有限值不能单独证明收敛。完整标签变化如下（保留Task-only变化）：

- impedance：physical-valid70→71 30→30（各30）；active_long_train_0000 task,strict，Task True→False、Strict True→False，穿透0.068076040→0.079543921mm；
- admittance：physical-valid70→71 29→30（各30）；active_long_train_0200 task,strict，Task True→False、Strict True→False，穿透0.095842217→0.100807496mm；active_long_train_0900 task,strict，Task True→False、Strict True→False，穿透0.067587079→0.035868338mm；active_short_train_0600 strict,physical_valid，Task True→True、Strict False→True，穿透0.203332713→0.197431139mm；active_short_train_0900 task,strict，Task True→False、Strict True→False，穿透0.100233855→0.118754656mm；
- vmc：physical-valid70→71 29→30（各30）；active_short_train_0600 strict,physical_valid，Task True→True、Strict False→True，穿透0.223467895→0.178658694mm；

## 全2124旧终端对比

从完整70提取的全部2124条固定终端输入与本轮新30分别报告，总2154，不与旧2094口径混用。独立保存数组/标量和实际图已核验；原V五focus及A原66short0600保持。

|路|旧2124 SSE前→后|变化|旧贡献（新总分母）|旧贡献（旧分母）|新30贡献|
|---|---|---:|---:|---:|---:|
|vmc|10788.124348→732.080520|-93.2140%|0.036153144|0.036666877|0.001439473|
|admittance|8555.136405→1241.855017|-85.4841%|0.061299584|0.062159709|0.000819060|

具体focus变化及图观察：

- vmc：index2050526 SSE22.919670→20.070067；index2299142 SSE2.826301→2.952555；index2046571 SSE1.157100→1.093221；index2423133 SSE4.757417→186.596290；index2423122 SSE12.511053→1.995045。
- admittance：index2752093 SSE69.519956→18.461078。

不作历史梯度因果判断，不把零终端误差新增为训练门槛。

## 续训决定与当前72

完整71的reward相对70仍明显变化：阻抗−0.570129→−2.252442、导纳−6.801951→−10.109684、VMC−4.596285→−2.820383，伴随上述成功标签变化。原71–73窗口尚未完成，不能宣布整体稳定；旧68–70结论和独立bootstrap复核保持。

全量loss和health图显示：阻抗末段critic均值上升且最大值38.577110；导纳和VMC均值下降，但有限尖峰和actor变化仍存在。熵围绕原目标，temperature保持正值但仍在变化。导纳/VMC采样Q超过当前soft bound的比例分别约0.000146484/0.001611328，作为诊断保留；不隐藏这些现象，也不把终端误差必须为零新增为门槛。

在完整标签、全2124终端数组/标量、实际图及准确恢复验证完成后，决定按原配置接续一个有限72。全部历史、markers23/47、4m append、terminal128、batch65536、UTD1、LR、masks、物理和gate保持；不重置状态，不导入辅助权重，无自动73。完整原始决定理由与47项证据绑定保留在DECISION72.json。

DECISION72 SHA `a06b85b02ce49e13d7cabea19d49ae7c6da15735968bf48b6078934d969a84f0`，绑定47项证据。准确71全state/replay/下一65536恢复通过，有限72实际启动且startup通过；不重置optimizer/replay/RNG/history、不导入辅助权重，无自动73。

原68–70结果及独立bootstrap补充保持；近零保护限制相对统计解释，不是将reward推离零的新目标。原71–73 PLAN c160b5d6及原waiter保持，当前只有完整71，不能提前宣布三轮窗口通过。

|当前任务|PID / start ticks|
|---|---|
|72 impedance|704014 / 42588230|
|72 admittance|704016 / 42588231|
|72 vmc|704019 / 42588231|
|loss72|708626 / 42589386|
|window71_73|2909145 / 42204920|

23:34:29快照三路steps 2968395/2969021/2970053，新72全loss等待器已部署，原71–73等待器未重启。行动前核验实时PID/start ticks与输出。

## GPU、观察与保存

本轮完成边界observer按最多1800秒/30秒登记，实际58样本、1710.899秒，在原71完整审查/标签/终端/72仅恢复就绪后自然结束；原71–73未来窗口不被误作本轮必须完成项。观察本身不启动或停止科学进程。

从观察开始到当前快照共399个guard样本，四卡最低79/62/64/63%，低于50计数[0, 0, 0, 0]，最大间隔5.271246秒。原v5五进程身份保持、STOP/FAILURE不存在。含合成占用，非科学吞吐或每瞬时保证；用户要求科研完成后仍保载，继续保持，非跨重启服务。

开工实际fetch/read main72d9239070c982b546c39f17e1424a73d435d60c、baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保留并行非RL工作。收尾再次fetch/read main80efd331并安全fast-forward，保留非RL完整18/108及同教师历史诊断，未操作其进程。遵循sii-research-sync，无子agent。

共享SSD归档 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER71_COMPLETE_20261028_233428/SMALL_EVIDENCE.tar.gz`，240成员/2860976字节，SHA `c877d8024ff7abe72c305418c51b5f7561675ca2e3206f8ae0a038b61926a06b`，逐成员字节/Python AST核验。[保存收据](RL_PARAMETER71_COMPLETE_20261028_SAVE.json)。大checkpoint/replay/raw留原共享SSD；HDD满只重写既有入口，非HDD/arm1全备份。

下一步保持原72与guard；准备72完整标签及终端审查、等待原71–73，继续基于完整结果判断reward稳定和loss健康，不因有界观察结束重启科学任务。Goal active。
