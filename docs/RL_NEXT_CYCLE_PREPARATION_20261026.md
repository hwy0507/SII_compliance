# 参数30与Direct20接续准备（2026-10-26）

Goal active；尚未宣称健康收敛。先核对原进程后建立下一有限周期的准备，保留现有物理/MJB/SPT、全部网络/优化器/计数/replay/RNG/history。无子agent，不重复已完成温度、actor floor、冻结16或GPU观测。

B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。完整科学状态见 RL_SERL19_POLICY_DRIFT_20261026.md；其科学提交e07903b及47成员小证据包已逐项核验，收据提交375ba00，HDD最新入口已同步Direct19/参数29。

## 参数第30轮

已从29准备脚本生成30 prepare/launch/monitor，准确父为完整29而非旧28。等待2031399仅在原29 FINISHED/REVIEW通过、三个原learner946578/946579/946580退出后执行prepare+check-only。保留2m replay、历史容量入口23和原pair learner；不修改任何历史登记。准备检查完整state、旧replay、下一65536采样及RNG；此时尚未实际完成，不能把AST检查当恢复通过。

原29 review946584的CPU调度2031400仅在三learner退出后复用CPU13，记录原进程身份、所有亲和性改变；不会另启审查或改精度。固定27–29原稳定性等待4175982保持，须检查其完整结果再决定正式30；等待程序不自动训练。

## Direct第20轮

准确父为未来完整19；等待2086366仅在原19 FINISHED/REVIEW通过且1326215退出后prepare+check-only。CPU调度2086367把届时原1326260审查及子进程移到释放CPU0；不提前争用learner。正式算法保持官方10critic/random2-min bootstrap、actor全10均值、noentropy、8:1、32步、batch65536与gather/transfer。20预期630历史终端，CPU1–12 sampler范围不改；温度/floor候选均未推广。

## 验证与边界

14份源码/启动记录及STATIC_REVIEW在docs/evidence/rl_next_cycle_preparation_20261026。所有新源码AST通过；用新adapt函数变换当前19/29 review和startup源码后再次AST检查，旧cycle路径清除、20终端630通过。此验证不产生神经更新或物理仿真，不替代后续实际恢复与启动检查。两个等待及两个调度均7200秒有界，不自动延长/启动正式20或30；先查这些原PID和结果，避免重复。

重新查询/fetch/read真实main dbb1d76ed79177067c48ed49ff9f67f023c704aa和baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，未变。GitHub认证问题已问勿重复；本集群SSD产物不冒称arm1或完整HDD备份。

后续覆盖：参数30原等待2031399根路径替换错误，已停止并保留失败源；修正后实际prepare2313197通过并正式30启动。以RL_PARAMETER30_STABILITY_20261026.md为准，不重启原等待。Direct20两原等待继续。
