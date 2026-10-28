# 参数70终端基准、完成后审查与71仅恢复准备

2026-10-28 21:36 UTC。Goal active；本轮是实质准备进展，不是训练收敛结论。承接[完整69与准确70启动](RL_PARAMETER69_COMPLETE_20261028.md)。Direct33已有原训练条件数值收敛判断，但Task/Strict仍0/0；不启动Direct34。

## 当前运行和固定协议

实际计算主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD根 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `env/bin/python`。21:36:27快照中原70 impedance/admittance/vmc steps为2894151/2894940/2895977，每路30sampler、0完成条件、无FAILURE，原learner身份及归档监视器保持。三路固定30×55秒、41250新增、4m append replay、原23/47标记、terminal128、batch65536、UTD1以及LR/mask/reward/物理/gate保持。没有重启原科学作业。

|任务|PID / start ticks|状态|
|---|---|---|
|70 impedance|896042 / 41814808|运行|
|70 admittance|896043 / 41814809|运行|
|70 VMC|896044 / 41814809|运行|
|70 archive/fullreview|896045 / 41814809|等待完整科学输入|
|70 full loss|899342 / 41815619|原等待器保留|
|原68–70稳定性|1085142 / 41039557|原PLAN e3a50567保持|
|70全标签|1235714 / 41876142|已部署，PLAN 37eb5e95|
|70 VMC终端对比|1368498 / 41899909|已部署，PLAN da7e9b37|
|70导纳终端对比|1368511 / 41899910|已部署，PLAN aa1f63b1|
|71仅恢复准备|1393879 / 41904388|等待完整70，REG dc665e2d|

所有PID须结合start ticks及输出核验，不能仅凭本文重复启动。精确命令、完整hash和快照在[小证据](evidence/RL_PARAMETER70_ANCHOR_FOLLOWUPS_20261028/MANIFEST.json)。

## 已完成的输入与源码审查

VMC/导纳从完整69保存值提取全部2094条终端，features2094×57，旧Q、reward、mask、indices精确保持；独立重建标量SSE、保存数组复核通过。提取/复核共0新网络前向、0新物理、0优化更新。

|基准|完整2094条masked SSE|anchor69.npz SHA256|
|---|---:|---|
|VMC|4074.470064641393|1465ab7e6aaaeb64d8287fe7cff686e1cc876ed566b845bb3f4fe717485a902f|
|导纳|1244.9266896226727|eea163f79aa1dd0b9ec67430c06137876f053d37d908c45ade9828a08c00fc1b|

70实际对比须完整archive/review/health通过且原learner退出；届时对全部2094旧终端和新增30（合计2124）计算，保留两个分母。VMC原focus[2050526,2299142,2046571,2423133,2423122]及历史58背景不变；导纳原66short0600/index2752093不变。不以focus替代全体，无梯度/因果声明。

五个终端脚本经同时周期/行数映射、hash文字保护、逆变换、覆盖计数、AST审查；capture唯一额外更新为已核69checkpoint SHA。每项输入/source/helper和实际70启动hash重新核验。新PLAN在70运行、未完整时登记，CPU53/7200秒有界等待；没有自动训练。

全标签通用auditor与69逐字节一致（SHA77e985c2），wait70及review_labels70经同样源码核验。真实不完整70调用以`Incomplete cycle 70`拒绝，非零退出且无COMPLETE69_70输出，原失败收据保留。全70完成后审查180标签/90reward对；独立review_labels70还需完整70的SAVED_REVIEW，不提前宣称通过。

## 71仅恢复准备

`runtime/prepare_parameter71_20261028_v1/`四脚本由原70模板同时69→70/70→71映射，保护日期/owner/hash、逆变换/AST/diff通过。wait_prepare通用源码保持；绑定实际70 jobs/monitor/LAUNCH hash。原70完整归档审查及learner退出后，才可运行三路全state/replay/下一65536的check-only。当前尚未发生准确70恢复验证，更没有71训练。

新71 launcher显式要求原68–70的REVIEW、SAVED_ARITHMETIC_REVIEW、PLOT_INSPECTION作为准确路径/hash绑定证据，独立算术通过且实际图已查看；这是原窗口审查义务，不是增加科学阈值。原5%/近零1/seed2026102855/5000bootstrap/端点保持，不能移动窗口或提前pass。真实缺DECISION71的启动已拒绝且未创建71run；零训练。完整70/全loss/标签/health/两终端对比/原窗口及实际图审查后，才能决定是否需要有限71。

## GPU继续保载

用户再次明确：科学全部完成也保留GPU运行、每卡利用率至少50%。原v5 supervisor3256866/start37410686与workers3256867–3256870身份均保持，STOP/FAILURE不存在。按约5秒监测、低于65%增加保载；科学任务结束不停止保载。该进程独立于本对话，但不是跨重启自启服务。

21:25:43–21:36:24 UTC共126样本，四卡min71/64/64/69%、均值78.0952/88.9921/89.5/89.4048%，低于50计数全部0，最大采样间隔5.272715秒。21:36即时79/93/95/92%。含合成占用，不当作科学吞吐，也不能据离散样本保证每瞬时。原采样字节与独立聚合保留。

## 下一步与保存状态

1. 保持原70与guard运行，观察实际进度及失败文件；任何有限等待结束不构成重启科学授权。
2. 等完整70后核archive/review、full loss及独立保存算术/真实图；执行runtime标签独立review_labels70.py并检查全180/90。
3. 核两终端对比FINISHED/保存数组与真实图；完成原68–70独立算术和真实图。保留65–67 I/A失败与V描述性通过及全部历史失败，不凭短窗口宣布整体收敛。
4. 71恢复完成后仍需单独DECISION71；按完整证据决定继续或已达原数值目标。GPU保载始终继续。

开工实际fetch/read main265859f88f73e9816c4868de3cb1e6886a94f12b/baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d，无冻结RL源变化，保留另一主机非RL工作。遵循仓库sii-research-sync，无子agent。

共享SSD小包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER70_ANCHOR_FOLLOWUPS_20261028_213746/SMALL_EVIDENCE.tar.gz`，78成员/979125字节，SHA256 `f748d285a94c0a66f20f55b0bd3a60555296d6d68eb6f56d91da1cf177c8ecf7`，逐成员字节与Python AST核验。[保存收据](RL_PARAMETER70_ANCHOR_FOLLOWUPS_20261028_SAVE.json)。大checkpoint/replay/raw仍在原共享SSD；HDD配额满，仅重写既有紧凑入口，未做HDD/arm1全备份。

收尾实际fetch获main efe3c46e（新增非RL全24恢复记忆诊断与原学习观察），日志和专题更新已读。合并保留双方AGENTS/UPDATE_LOG新增原字节和共同历史，无冻结RL源改动；baseline仍f6e8f8c。该同步补充晚于小证据包，不冒充包内内容。
