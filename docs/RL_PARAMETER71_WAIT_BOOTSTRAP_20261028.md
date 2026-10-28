# 第71轮十分钟观察及原68–70不确定区间独立复核

2026-10-28 UTC。Goal active。承接[71观察与72完整loss准备](RL_PARAMETER71_WAIT72_LOSS_PREP_20261028.md)。本轮新增原始样本核验及独立bootstrap证据，没有改动科学训练、停止原进程或宣布收敛。Direct33原训练条件数值结论保留，TaskStrict0/0，不启动34。

## 原71连续运行

22:48:16–22:58:16UTC，600秒/30秒、21次原71三learner、archive、六审查等待器和五guard PID/start ticks均live。三路每次步数严格增加，末次I/A/V 2948239/2949235/2950340。原learner2902207/2902208/2902211同start42203070保持；没有完整71或失败。observer自然结束，科学继续，无重启。固定30×55/41250新增/4m replay/batch65536/UTD1及原LR/masks/reward/物理/gate不变。

观察前后分别保存三路最新1000条完整optimizer原始字节（事后取样非前瞻窗口），记录来源offset/完整前缀hash，源跨度回读精确。步号连续、所有数值有限、独立fsum均值/极值核验通过。

|路|两次最新1000 critic均值|actor均值|temperature均值|
|---|---|---|---|
|impedance|1.870921647→2.119513246|26.438245239→26.418494865|0.001332812→0.001341525|
|admittance|1.223197939→1.211544152|-8.755386204→-8.746767439|0.000402835→0.000385667|
|vmc|0.897551606→0.800234016|-12.929899817→-12.913187546|0.000542042→0.000600043|

仅这两段在途样本，不代替完整71 loss/health或固定reward窗口，也不以有限性单独证明健康收敛。其间未保存的更新仍由原完整审查负责。

## 原68–70 bootstrap独立复核

原REVIEW与SAVED_ARITHMETIC_REVIEW保持原字节，原标量复核的bootstrap_reruns=0仍描述当时事实。本轮在新runtime/parameter68_70_bootstrap_independent_20261028_v1进行事后独立复算：三类各10条件、按condition排序、seed2026102855+方法序号、5000次原分层重采样保持；用独立整数索引构造、math.fsum逐样本均值、手写排序线性分位数，不调用原审核脚本或原np.quantile。新物理/优化更新均0。

|路|68→70回报差的原95%条件构成敏感区间|每轮斜率区间|
|---|---|---|
|I|[-0.037629027,8.709085586]|[-0.018814514,4.354542793]|
|A|[-0.063797918,5.100350875]|[-0.031898959,2.550175438]|
|V|[-0.066808664,0.119972685]|[-0.033404332,0.059986342]|

与原保存区间最大差异I1.77636e−15/A9.15934e−16/V8.88178e−16，通过1e−12数值容差。输入episode/原报告/登记前后hash保持。全部5000×30索引及delta/slope保存原JSON在共享SSD，并无损打包NPZ（613319bytes，SHA49663ddcd5f8fb0f16a4174a810eafb7cbfe6f5241e3df902cc154d1bdf29e06），所有数组精确回读。

三者区间都含0，但“包含0”并不证明等价或稳定；I/A区间宽，原描述性5%/近零判定未改，整体未收敛结论保持。这里只核验条件构成敏感性，不是独立训练seed、冻结策略性能或泛化。原71–73 PLAN/5%/近零1/seed/5000保持，无提前窗口结论。后续必须完整71审查后决定有限72。

## GPU与保存

同期117个guard样本最低76/62/60/63%，低于50计数[0, 0, 0, 0]，含合成占用，非每瞬时保证。v5 supervisor3256866及四workers保持，STOP/FAILURE不存在；科研完成后继续保载，非跨重启服务。

实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，env/bin/python。开工mainf2198d05d521cabb12d5640a9d7dacd9b1608bc3/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d实际fetch/read，保留非RL工作、遵循sii-research-sync，无子agent。[证据manifest](evidence/RL_PARAMETER71_WAIT_BOOTSTRAP_20261028/MANIFEST.json)。

共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER71_WAIT_BOOTSTRAP_20261028_225824/SMALL_EVIDENCE.tar.gz`，29成员/905977字节，SHA `1e8d272f3348411b5bba726eda47c8cb1da4b62bb1c61340829c0c96da0e1e93`，逐成员字节/AST核验。[收据](RL_PARAMETER71_WAIT_BOOTSTRAP_20261028_SAVE.json)。大checkpoint/replay/raw仍共享SSD，非HDD/arm1全备份；HDD满仅重写既有入口。原71科学与71–73等待器继续，72 full-loss准备已就绪但未部署，无72训练。
