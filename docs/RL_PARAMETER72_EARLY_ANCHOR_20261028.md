# 参数72早期检查、全2154终端基准与73仅恢复准备

2026-10-28 23:40:14 UTC。Goal active，原72训练继续。承接[完整71与准确72启动](RL_PARAMETER71_COMPLETE_20261028.md)。Direct33原训练条件数值收敛判断保留、TaskStrict0/0，不启动34；当前参数RL尚未整体收敛。

## 当前运行

实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，env/bin/python。快照三路I/A/V steps 2972715/2973494/2974569，原身份均live，各30sampler，无完整或失败；没有73训练。固定30×55/41250新增/4m append replay/markers23/47/terminal128/batch65536/UTD1及原LR/masks/reward/物理/gate保持。

|任务|PID / start ticks|登记SHA前缀|
|---|---|---|
|72 impedance|704014 / 42588230|原实际启动|
|72 admittance|704016 / 42588231|原实际启动|
|72 vmc|704019 / 42588231|原实际启动|
|loss72|708626 / 42589386|e16219702910|
|window71_73|2909145 / 42204920|c160b5d6032a|
|labels72|978935 / 42638063|dd768c7a1515|
|vmc72|1062827 / 42653053|e8cbd9b40ddf|
|admittance72|1062828 / 42653054|46c8cb0771d9|
|restore_only73|997695 / 42641371|479a93e21f0c|
|72归档|704024 / 42588231|原监视器|

完整命令/hash/source差异与核验见[证据manifest](evidence/RL_PARAMETER72_EARLY_ANCHOR_20261028/MANIFEST.json)。行动前核验实际身份与输出，勿据旧PID重复启动。

## 前5000更新

原始前缀逐字节一致、步号连续、全数值有限、独立标量均值/极值复核通过；实际loss.png已查看。登记发生在前缀可用之后，非前瞻注册。

|路|critic首→末1000|critic最大值|actor首→末1000|
|---|---|---:|---|
|impedance|2.425788165→2.465292879|22.762973785|26.268914503→26.281934900|
|admittance|1.182205396→1.174083075|6.922300816|-8.701363166→-8.702684762|
|vmc|0.783420539→0.908690600|9.490621567|-12.779944201→-12.770906830|

I critic在约2.4附近波动、末段略升且有限尖峰较多；A critic/actor近似平坦；V中段和末段critic上升，actor稍升。早期前缀不代表完整72或收敛。算术收据plot_inspected=false保留当时事实，后续图审见PLOT_INSPECTION.json。

## 全2154基准与完成后审查

从已核完整71保存值提取V/A全部2154×57 features，以及indices/reward/mask/Q；独立数组与SSE复算通过，0新网络前向/物理/优化更新。基准包括71新增30，不能与上一报告的旧2124 SSE混用。

|路|全2154 masked SSE|anchor71.npz SHA256|
|---|---:|---|
|vmc|761.227960064590|a6988ce1c27d5aead33504e74e16e45e2a4995328f37f9c78a2c2a0ae95dd87d|
|admittance|1258.445655483098|ea5ab9191b486ffbfa490439d3dad4e2b6a5738d005025d17197b2b31f1521da|

72完成后需比较全部2154旧终端及新增30（总2184），保留两个分母。原V五focus[2050526,2299142,2046571,2423133,2423122]及A原66short0600/index2752093与历史背景不变。五源周期/数量映射、完整hash文字保护、逆变换/AST/diff/输入hash通过；capture只更新已核完整71 checkpoint身份。两个CPU53/7200秒等待器已绑定实际72 jobs/归档/source/input，不自动训练。

补充独立静态复核已通过：全部输入/source hash、实际72路径、2154/2184数量及原focus均精确。首次临时检查误把focus当源码字面量，触发AssertionError；实际track从PLAN读取索引，改查PLAN与AST读取方式后通过。检查假设问题已记录，未改变科学源码、PLAN、训练或等待器。

全标签通用audit_labels.py SHA77e985c2保持原字节，wait72/review_labels72映射核验通过。实际不完整72调用以Incomplete cycle 72非零拒绝，无COMPLETE71_72输出；等待器已部署。完整后仍需独立review_labels72核180标签/90reward对，依赖完整72 loss SAVED_REVIEW，不提前pass。

## 73仅恢复

runtime/prepare_parameter73_20261028_v1四源从原72同时周期映射，保护原68–70、原71–73路径及[71,72,73]列表/完整hash；逆变换/AST/diff通过。wait_prepare.py SHA c4617a04逐字节保持。launcher仍绑定原68–70完整审查与原71–73准确PLAN，不要求未来73结果才能启动73，也不新增科学阈值。

实际缺DECISION73启动已拒绝，未创建73训练目录；CPU53/14400秒等待器只在完整72审查、原learner退出后执行全state/replay/下一65536的check-only。当前未执行该恢复、更没有73训练。73 full-loss准备尚未创建。

原71–73 PLAN c160b5d6与waiter2909145/start42204920保持，5%/近零1/seed2026102855/5000/anchor55不变；原68–70及独立bootstrap补充和全部历史结论保留。近零保护是统计解释限制，不是把reward推离零的训练目标。

## GPU与保存

用户要求科研完成后也保留GPU负载。原v5 supervisor3256866及四workers身份保持，STOP/FAILURE不存在；约5秒采样，低于65%增保载。自上次完整交接快照至本次共67样本，最低83/69/70/64%，低于50计数[0, 0, 0, 0]，最大间隔5.227937秒。含合成负载，非科学吞吐或每瞬时保证，非跨重启服务。

开工main9e4d6c5701d23f462b75da5c47e45c51c5d74fc3/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d实际fetch/read，保留并行非RL工作，遵循sii-research-sync，无子agent。

共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER72_EARLY_ANCHOR_20261028_234202/SMALL_EVIDENCE.tar.gz`，93成员/1913440字节，SHA `c0cb38f953fe178463fe4083d2059b374e740bf07aca095807350dd0e105bde6`，逐成员字节/Python AST核验。[保存收据](RL_PARAMETER72_EARLY_ANCHOR_20261028_SAVE.json)。大checkpoint/replay/raw留原共享SSD，非HDD/arm1全备份；HDD满只重写既有入口。

下一步保持原72及guard，完成全72 loss/标签/health/终端数组/实际图审查，准确恢复后再决定有限73；不因观察超时重启科学。Goal active。

补充核验证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER72_EARLY_ANCHOR_20261028_234202/DEPLOYMENT_REVIEW_SUPPLEMENT.tar.gz`，3成员/1834字节，SHA `1b70c1be955d68ad6b80d24991202dd52bea3ce2b649014c5c4a5af5562efeb6`，逐成员/AST核验；原93成员归档保持。见保存收据deployment_review_supplement字段。
