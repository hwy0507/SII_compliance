# 原68连续观测、完整67终端误差排名与69 loss部署准备

2026-10-28，Goal active。实际主机 `rltest-1025--a6ed2ff39b3c-hsje5ateny`，共享SSD根
`B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `B/env/bin/python`。
本补充承接[原68交接](RL_PARAMETER68_EARLY_ANCHOR_20261028.md)，原68的三learner、归档、全loss、
全标签、V/A全部2034固定终端、69仅恢复与原68–70窗口保持原进程。没有69训练或新科学停止门。

## 完整67保存终端值的事后排名

目录 `B/runs/vmc67_ranked_terminal_diagnosis_20261028_v1`。
本次在完整67结果可见之后、68仍运行时登记PLAN，使用已经独立复核的完整67 `values.npz`，
无新网络前向、物理积分、优化器更新或replay写入。按masked SSE降序、replay index打破同值排名，
完整保留2034行和原五focus，不改变原68锚点或另建前向等待器。

全2034终端SSE为4748.245926947702；固定旧2004从4313.479085101947升至4729.287149395173，
新增30为18.958777552529。旧2004中858改善、1146退化、0不变；不能从总和或改善个数单独推断训练收敛。

|事后排名/样本|完整66 SSE|完整67 SSE|占完整67全2034 SSE|
|---|---:|---:|---:|
|1 / index2423133|14.767521258|1826.420822661|38.465169%|
|2 / index2299142|2.062169132|351.402853641|7.400688%|
|前2合计|||45.865857%|
|前5合计|||62.361607%|
|前10合计|||75.945255%|

前两行增加2160.993985912778，剩余2002旧行合计下降1745.185921619552，故全部旧2004净增加415.808064293226。
这描述已保存末端误差的集中程度，不证明历史minibatch梯度因果、表征混叠或泛化。
原五focus2050526/2299142/2046571/2423133/2423122的当前排名分别20/2/57/1/25，全体与旧失败保持。
没有把事后前两行重新包装为预登记focus，也没有新增零终端误差或尖峰阈值。

`REVIEW.json`、`SAVED_REVIEW.json`完成；独立标量实现逐2034行、每head误差、分母贡献、全体统计和原五focus复算通过。
实际 `ranked_terminals.png` 已目视检查，两图分别显示全2034累积误差比例和全2004旧值变化；完整可读、原五点圈出。
保存 `PLOT_INSPECTION.json`。数值来源SHA `8de734907f53bc96cd62851db8c5a779de07d18b579360369a08c0998d688d49`，
新PLAN SHA `5e5870ad08e2776abba2da1c6402ef1dffdaddd43c2f0b2f96075db68ba8907c`。

## 69完整loss的受检查部署入口

`B/runtime/parameter69_loss_preparation_20261028_v1/deploy.py` 静态准备完成，SHA256
`146e3b2792b61ad0c3cf9762ff7a8a6b72c4a7da907304de5e94cbd7a6310576`。
原四份69 loss审查脚本hash保持；精确上下文同时替换、覆盖计数、额外要求加入前的逆变换和最终AST检查通过。

入口要求真实 `DECISION69.json`、完整68 loss/paired/独立复算/实际图、180全标签及独立复算、
完整68 review/health/实际图、V/A完整固定终端三项审查、准确69恢复与实际69三learner PID/start均有效。
逐个核对决定所绑定的全部证据hash；历史65–67三项记录保持，原68–70只要求原PLAN，
不错误地要求尚依赖69/70的未来窗口结果完成。重复或部分69 loss部署目录不允许覆盖。

实际缺DECISION69的调用已经非零拒绝，`DEPLOY_REJECTION.json`保存原始异常，69loss目录没有创建，
没有启动69训练或loss waiter。未来成功路径尚未实际运行，不能把静态/拒绝验证称实际部署成功。
完整68审查后若仍需继续，先绑定实际证据、决定一个有限69并实际启动，再执行此入口。

## 后续与边界

原68预计最终steps2841648/2842250/2843250，以实际FINISHED/归档为准。完整后先运行全68 loss保存复核并查看图，
审完整health及图、全部标签及 `prepare_parameter69_20261028_v1/review_labels68.py`、V/A全部2034固定终端及图，
确认69 exact restore；再决定69。原68–70端点保持，没有自动69/70训练。
新排名只能辅助检查已有68全体保存值，不能替代原五focus、完整loss或完整reward窗口。

Direct33仅原训练队列经验数值收敛，Task/Strict0/0；Direct34false保持。
原65–67 I/A失败、V仅描述性reward通过，旧失败与历史通过保持，整体收敛尚未证实。
原奖励/gate/物理/LR/masks/4m replay/terminal128/batch65536/UTD1和历史23/47 markers未改。
科学全部完成也保持v5合成GPU保载；含保载利用率不能冒充纯科学吞吐，当前不是跨重启服务。
旧v4 STOP仍在共享SSD，v5控制在/tmp，禁止因此恢复旧v4或误停v5。

开工实际查询/fetch/read main `9d13fbb923574e3104cbfd69001a88b843d72319` 与 baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`。已读取另一主机非RL offset六项通过、新30采集/公平学习接续的
日志和报告，fast-forward保留其全部代码/证据，没有本机冻结RL源变动。无子agent。
大checkpoint/replay/raw仍共享SSD；HDD配额满只原地重写既有精简LATEST，不称HDD或arm1全量备份。

## 19:49 UTC 连续观测与归档

`B/runtime/parameter68_verified_wait_1940_20261028_v1` 在19:39:14–19:49:14完成600秒/21观测，
原三learner、归档及六项等待器与五guard逐样本身份/live保持，三路steps
2821391/2822221/2823325→2829004/2829951/2830977严格增加，没有完整/失败标记。
observer2036021/start41207030自然结束，非科学失败，无重启。原68继续，完整结果待。

同期117条guard采样，GPU0–3最低77/67/70/68%、均值78.914530/89.256410/89.803419/89.367521%、
低于50均0，最大采样间隔5.279396秒。包含合成保载，只支持采样窗口结论，非每瞬时保证。
REVIEW/GUARD_REVIEW独立复核通过；科学全部完成后也保持v5。

共享SSD小证据包 `B/repository/RL_PARAMETER68_WAIT_RANKED67_20261028_194932/SMALL_EVIDENCE.tar.gz`，
40成员/426100字节，SHA256 `b2727e4a42dd50600f31c9d16d31e578ea4d32aca5d806e6f939458afe85a451`，
逐成员字节/hash、Python AST和tar回读核验通过。只收本轮完成的小证据及明确依赖，
[保存收据](RL_PARAMETER68_WAIT_RANKED67_20261028_SAVE.json)，
[清单](evidence/RL_PARAMETER68_WAIT_RANKED67_20261028/MANIFEST.json)。不是大模型/轨迹、HDD或arm1全备份。

收尾实际再次fetch/read main `6820a1c6`（完整SHA见Git），baseline仍f6e8f8c。
另一主机非RL v7七条采集/18与108静态准备/覆盖审计工具和归档新日志及报告已读，fast-forward保留全部内容，
没有改变本机冻结RL源。原68、原68–70窗口与全部等待器继续，69仍未启动，Goal active。
