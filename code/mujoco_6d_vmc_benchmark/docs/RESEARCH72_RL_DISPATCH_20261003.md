# RL有限轮转续训与预算边界

2026-10-03 20:13:54 UTC登记，尚未开始本轮office RL训练；不依据训练结果调整。
原方案逐个模型先5500步再续至80000步，有限截止下可能让最后的family/seed没有checkpoint。
现将每条队列的5个模型依次跑到累计5500、27500、49500、71500、80000步的边界；
总计仍5种方法×3seed，三条共享槽位队列，单进程单线程/3GiB，最多4个仿真。

每次续训仍恢复原优化器、回放、归一化及RNG，不清空数据，学习率日程始终按80000总步。
每轮只派发预算可容纳的完整回合，实际步数可能小于所列上界，不能把分段累计步再次相加。
模型仍选最后一个完成边界，不读成功率或奖励来决定早停。奖励、网络、输入、动作限制、场景及门槛不变。
开发截止仍10月5日11:30UTC，总截止仍10月6日11:30UTC；不延长用户窗口。

若截止发生在轮转中，只有每个模型都已有有效checkpoint才可将有限队列记为完成；
同时明确`all_requested_segments_dispatched=false`、截止原因、逐模型实际步数。
“队列完成”不等于80000步全部用满、优化收敛或任务成功。缺少任何模型仍阻止最终冻结。
轮转增加最多45次额外训练进程启动，可能增加编译开销，实际耗时须后续计入；不声称等计算量。

## 实际切换及验证

只有经精确PID/命令/执行文件核验、零队列零物理回合的`sii-r72-rl-office-adaptation-v1`
等待器被停止；现有四条learning development物理队列全部保留。
旧`execution.json`保持原`waiting_for_predecessor`字节，其含义由单独supersession收据澄清，
不能看到该历史字段就重复启动旧服务。新`sii-r72-rl-office-adaptation-v2`正常等待同一followup。

本机16项调度、最终模型汇总和冻结回归通过。模拟完整25段的真实队列入口逐段核验parent，
每个模型累计79750、只计新增步；这些是合成工程检查，尚未验证真实物理续跑。
实际服务器新runtime仅改两份调度源文件，trainer和其余tools/scripts/assets逐hash保持原v3内容。
没有新增teacher/ESN拟合，也未登记拟议的context-readout学习预算修订02。

所有路径主机：`arm1@192.168.31.70`。

- 本轮根：`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149/`。
- 活跃登记：本轮根`rl_office_adaptation_v2/`，不是第二套重复训练。
- 新runtime：`/home/arm1/sii_shared/SII_compliance/runs/main/research72_20261003_1149_rl_runtime_v4/`。
- 修订：本轮根`AMENDMENT_RL_ROUND_ROBIN.json`，SHA256 `3ff1ae22f310825de701344df84d8f74c1c18b27e7719c448a5b563c009a7d46`。
- 切换证据：本轮根`rl_dispatch_change_v1/execution.json`，SHA256 `b99f9aa0601b553e67258bfc4529d0b0498856ad9c6653fdd505c34159c5d1ee`。
- 已核验源码overlay包：`/home/arm1/sii_shared/SII_compliance/incoming/sii-r72-rl-dispatch-overlay-20261003-2045.tar.gz`，
  SHA256 `fa888c0e518ac15b2681ba0ebaafc0e3c597a683e5a346acac884af4a8d45509`。
  文件名2045是独立包标识，真实切换时间以收据20:13:54为准；不是干净commit运行，源链为旧v3＋两份hash明确的调度覆盖。

20:15UTC初始学习开发169/264，五个身份各33完整。第五身份ESN4/6task但仅1/6strict：
另外三条已放置轨迹因pillar/link7穿透0.209686、0.279906、0.573083mm失败；
seed303 temporal仍在carry、RMSE250.986mm。原0.2mm门槛保留，不能把4次放置写成4次严格通过。
matchedRNN同4/1，matchedMLP2/2、memoryless1/1、ordinaryMLP1/1、ordinaryRNN3/0。
这些含候选损失版本，不是最终模型泛化率。最终24身份仍封存。
