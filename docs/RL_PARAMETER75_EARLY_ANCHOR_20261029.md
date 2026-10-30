# 第75轮早期loss、全2244终端锚点及76仅恢复准备

2026-10-29 02:58:46 UTC，Goal active。承接[完整74及准确有限75](RL_PARAMETER74_COMPLETE_20261029.md)。上一goal轮完成全74审查/实际75接续，属progress；本轮完成新审查及后续部署，仍属progress。第75轮原三路继续，整体收敛尚未证明；Direct33原训练条件数值结论及Task/Strict0/0保持，不启动34。

实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器env/bin/python。I/A/V steps 3096507/3097205/3098191，原PID/start ticks均live、各30sampler，无失败。原30×55秒/41250新增、4m append、markers23/47、terminal128、batch65536、UTD1及LR/masks/reward/物理/gate不变。

|当前任务|PID / start ticks|登记SHA前缀|
|---|---|---|
|75 impedance|2586717 / 43778555|原启动|
|75 admittance|2586718 / 43778555|原启动|
|75 vmc|2586719 / 43778556|原启动|
|loss75|2601754 / 43782327|1b8a46a75688|
|window74_76|541941 / 43375839|d8c243d979f4|
|labels75|2869685 / 43830521|7bb69fb1e613|
|vmc75|2945058 / 43844232|770015f00227|
|admittance75|2945059 / 43844233|7b57d627fe03|
|restore_only76|2869587 / 43830505|ebe5af576e90|

前5000原日志前缀逐字节、连续步号、全数值有限、独立算术及实际图已审。登记发生于前缀可用后，不称前瞻注册；完整75及74–76结论仍待。

|路|critic首→末1000|critic最大值|actor首→末1000|
|---|---|---:|---|
|impedance|3.094763606→3.169439045|30.453176498|25.637870655→25.701041788|
|admittance|1.272399852→1.315833383|6.308498859|-9.130793980→-9.150968040|
|vmc|0.924675461→0.791802929|11.191431999|-13.024445431→-13.045283516|

实际六面板图：I critic均值约3并保留连续尖峰，actor缓升；A critic略升、actor略降；V critic均值下降但有孤立尖峰，actor略降。前缀不能证明全轮loss健康或reward平稳，不能抹去完整74及原71–73失败结论。

全74的2244×57 features/indices/reward/mask/Q逐元素核验、独立标量SSE通过；Q来自已核验74结果，0新网络前向/物理/优化更新。此锚点包含74新增30条，不能与74对旧2214条的SSE1031.376087/2953.887562混用。

|路|全2244 masked SSE|anchor74.npz SHA256|
|---|---:|---|
|vmc|1044.718845252995|ad4f1ae363fcb907cd8278556deba3831b54978bbd3714d8ee9cd5cf5f424b22|
|admittance|4229.352469843741|2bce674fbf710a8b5ff22ea3985109038d853a63ad799cb4fa93546083cd2ff2|

完整75比较全部2244旧终端及新30（预计总2274），保留旧/新分母与原V五focus[2050526,2299142,2046571,2423133,2423122]及A原66short0600/index2752093。两终端等待器已部署，source/inputs/PLAN hash和AST消费focus已独立静态审查。

VMC首次只读review_anchor统一session23118以143退出、无输出且无审查收据；终止来源未确定，不能声称OOM或数据失败。退出记录保留在ANCHOR_REVIEW_FIRST_EXIT.json。确认终态后只重跑该只读复核，session27281自然exit0且2244数组/独立SSE通过；原训练和guard未重启。导纳锚点与独立复核亦通过。

全标签通用审计器与74逐字节相同。真实不完整75调用拒绝且未生成COMPLETE74_75；等待器已部署。完整后执行runtime/parameter_task_label_audit75_20261028_v1/review_labels75.py，要求全75 loss SAVED_REVIEW，并核全180标签/90reward对。

76仅恢复等待器位于runtime/prepare_parameter76_20261029_v1；wait_prepare.py与原75逐字节相同。仅完整75归档审查且原三learner退出后执行全state/replay/下一65536 check-only。真实缺DECISION76调用被拒绝，无76训练目录/训练。launcher保留原68–70及原71–73完整审查、独立算术/实际图与PLAN，保持原74–76准确PLAN，不提前要求未来74–76完整结果。76实际恢复、续训决定和全loss准备均尚待。

原71–73 PLAN c160b5d6032abaea7ea81c1fb0a2a8151f4fd929d81044a830740343fc572bdf及完整不稳定结论保留；原74–76 PLAN d8c243d979f43520e34036b5ce7dfb1b5f5712b5e4091dc09f4dacfdb5061703/waiter541941/start43375839保持。原5%/近零1/seed2026102855/5000/anchor55及全部历史结论不变；近零保护不是将reward推离零的新目标。

从上次完整交接快照起66个guard样本，四卡最低80/68/69/63%，低于50计数[0, 0, 0, 0]，最大间隔5.274106秒。原v5五进程身份保持，STOP/FAILURE不存在；科研完成后继续保载，含合成负载，非纯科学吞吐/每瞬时保证/跨重启服务。

开工实际fetch/read main3b159dcf491ce65fa93ff54d0411fb6f1d2585f2/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d；保存源码基线3b159dcf491ce65fa93ff54d0411fb6f1d2585f2。遵循sii-research-sync，保留并行非RL工作，无子agent。

共享SSD包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER75_EARLY_ANCHOR_20261029_030046/SMALL_EVIDENCE.tar.gz`，112成员/1976600字节，SHA `59afb93b054635fd01a813599ee2c258c810cef80f7dc0dc2999f38476ac8664`，逐成员字节/Python AST已核。[收据](RL_PARAMETER75_EARLY_ANCHOR_20261029_SAVE.json)。大checkpoint/replay/raw仍原共享SSD，非HDD/arm1全备份；既有HDD入口更新回读。

下一步保持原75与六等待器和guard，准备76全loss；待完整75 loss/标签/health/终端全审、实际看图与准确恢复后再决定有限76。原74–76窗口继续，不因观察时限重启科学。Goal active。
