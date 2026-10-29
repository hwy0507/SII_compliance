# 第73轮早期loss、全2184终端基准与74仅恢复准备

2026-10-29 00:47:35 UTC，Goal active。承接[完整72与准确73接续](RL_PARAMETER72_COMPLETE_20261029.md)。原73三路训练继续，当前尚未整体收敛。Direct33原训练条件数值结论保持、Task/Strict0/0，不启动34。

实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器env/bin/python。三路I/A/V steps 3015631/3016227/3017251，原PID/start ticks身份均live，各30sampler，无失败。固定30×55秒/41250新增/4m append/markers23/47/terminal128/batch65536/UTD1及原LR/masks/reward/物理/gate保持。

|任务|PID / start ticks|登记SHA前缀|
|---|---|---|
|73 impedance|2714363 / 42979895|原启动|
|73 admittance|2714364 / 42979895|原启动|
|73 vmc|2714365 / 42979895|原启动|
|loss73|2718561 / 42981213|ade5d745bac7|
|window71_73|2909145 / 42204920|c160b5d6032a|
|labels73|3073648 / 43045432|086de4b6432f|
|vmc73|3137325 / 43057175|045b7b04e4b3|
|admittance73|3137336 / 43057177|dbee80a3effb|
|restore_only74|3096807 / 43049834|af2e44e64dc1|
|73归档|2714366 / 42979896|原监视器|

前5000原字节前缀、连续步号、全数值有限、独立算术与实际loss图已审。登记发生在前缀可用之后，非前瞻注册。

|路|critic首→末1000|critic最大值|actor首→末1000|
|---|---|---:|---|
|impedance|2.572366198→2.395603449|16.821136475|26.025016790→26.078288826|
|admittance|2.417615840→1.874659584|41.378467560|-8.549950490→-8.598799252|
|vmc|1.217785537→1.046712781|20.496379852|-12.557226699→-12.573892234|

三路critic前缀末均值较低，但有限尖峰仍在，I actor略升、A/V略降。不能用前缀替代完整73 loss或原71–73窗口，也不覆盖72末段异常。独立算术收据保留当时plot_inspected=false，实际图审另见PLOT_INSPECTION.json。

全72的V/A全部2184×57终端features/indices/reward/mask/Q精确提取，独立数组及标量SSE通过，0新网络前向/物理/优化更新。此基准包括72新增30条，不能与完整72报告只比较旧2154条的SSE1328.573581/6731.893154混用。

|路|全2184 masked SSE|anchor72.npz SHA256|
|---|---:|---|
|vmc|8916.873139807378|8f87a3b2069fcc12b7cdf2154560ade1b227ed55b43658ea47c62e23865c30a7|
|admittance|24329.209051277710|02d6a8eda9a3b23a8ebe5d370f00185207c94618d3ab9dd13ded6cbee69fa8c4|

73完成后比较全部2184旧终端和新增30（总2214），保留旧/新分母。原V五focus[2050526,2299142,2046571,2423133,2423122]及A原66short0600/index2752093保持。五源码/hash/逆映射/AST/输入hash均审查；独立静态检查核对PLAN与AST读取focus，两个CPU53/7200秒等待器绑定实际73原进程，不自动训练。

全标签通用审计器保持原字节。真实不完整73调用被拒绝且未生成COMPLETE72_73输出；等待器已部署。完整后仍需运行review_labels73，核180标签/90reward对，并要求完整73 loss SAVED_REVIEW。

第74轮仅恢复等待器已部署：原wait_prepare.py逐字节不变，只在完整73审查且原learner退出后执行全state/replay/下一65536 check-only。实际缺DECISION74调用拒绝，没有74训练目录或训练。launcher继续绑定原68–70完整审查及原71–73 PLAN；因为73结束后原窗口应齐全，有限74启动还必须绑定原71–73完整REVIEW、独立算术和实际图审。这是兑现原窗口审查要求，没有改变原科学阈值。当前74恢复尚未执行，74全loss准备也尚未创建。

原71–73 PLAN c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf、waiter2909145/start42204920保持，5%/近零1/seed2026102855/5000/anchor55及全部历史结论不变。近零保护是相对统计解释限制，不是把reward推离零的新目标。

自上次完整交接快照至本次共82个guard样本，四卡最低79/66/66/62%，低于50计数[0, 0, 0, 0]，最大间隔5.234436秒。原v5 supervisor3256866及四workers身份保持，STOP/FAILURE不存在。含合成负载，非纯科学吞吐或每瞬时保证；科研完成后也保载，非跨重启服务。

开工实际fetch/read main24a17b0b89cc664e0aac960b610c8eced4417d53/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，保存前再次核验未变。遵循sii-research-sync，保留并行非RL工作，无子agent。

[证据manifest](evidence/RL_PARAMETER73_EARLY_ANCHOR_20261029/MANIFEST.json)。共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER73_EARLY_ANCHOR_20261029_005010/SMALL_EVIDENCE.tar.gz`，107成员/1944387字节，SHA `b614acc7f76158c81059082a375b6c2c42dbaa2fb5504710229bec32b51f315d`，逐成员字节/Python AST核验。[保存收据](RL_PARAMETER73_EARLY_ANCHOR_20261029_SAVE.json)。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份；HDD满只重写既有入口。

下一步保持原73与guard，收齐完整73 loss/标签/health/终端和原71–73窗口，独立复算并实际看图，再决定是否需要有限74。不得因观察结束重启原科学任务。
