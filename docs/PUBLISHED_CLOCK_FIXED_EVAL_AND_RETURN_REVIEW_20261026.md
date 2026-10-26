# 固定回报诊断完成与时钟策略独立复测

2026-10-26。上一Goal轮为实质进展：完成首周期/旧固定矩阵审查并实际执行有限辅助拟合。
本轮fetch main `6dc2b241215d1898f8e07916153f3e0754dfb3db`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，没有新远端提交。
目标仍为已发表基线适配、充分健康收敛与最终冻结策略/指定ESN公平比较，未达成；不以完成有限阶段替代收敛。

## 有限辅助拟合全部完成并复核

`runs/clock_cycle00_return_capacity_v1`四原进程已正常结束，不重复启动或自动延长。
四方法×parent/fresh两种初始化×20000更新=160000辅助梯度更新；0actor更新、0新physics、不推广权重。
独立以scipy.signal.lfilter从按condition恢复的完整轨迹重建discounted returns；全部目标hash与原递推结果精确一致。
四checkpoint/冻结transition副本hash、33k/8.25k拟合划分、每类两条件留出、八臂328个诊断点与完成收据核验。
图`return_capacity.png`已目视检查。终点MAE如下：

|方法|parent拟合|parent留出|fresh拟合|fresh留出|
|---|---:|---:|---:|---:|
|direct|0.1623|0.3003|0.1116|0.3491|
|impedance|3.1362|12.4380|2.5073|12.6097|
|admittance|1.0915|3.4616|0.5357|4.0734|
|vmc|1.3978|9.1487|0.6249|9.9790|

Direct固定标签可拟合，Impedance/VMC存在较明显的拟合—留出差距；不能把该结果当作在线critic修复。
标签不含SAC熵，且来自变化中的行为策略；它们不是当前actor的soft Q真值。父在线actor/critic已见过留出条件。
本次改用全头固定标签监督，不是原Bernoulli mask Bellman训练。故不能将新低MAE与在线terminal Q MAE直接比较或宣称架构瓶颈已排除。
完成曲线和actor未改由worker记录/自检，辅助权重按协议未保存，因此没有独立最终函数重放或held-out-policy声明。
科学决策：继续原在线阶段，不据这次拟合更换live奖励/优化器，不创建重复辅助循环。

## 首个已训练时钟checkpoint的冻结策略矩阵

新`runs/clock_cycle00_fixed_representatives_v1`，协调PID2960898、首Direct评估2961606，CPU54串行；原在线CPU0–51/四GPU配置未动。
冻结四cycle0 checkpoint（各41250steps），使用与旧代表矩阵相同的passive_corner/active_short/active_long_train_0000。
12×55s、最多1320万新物理子步；确定性、0优化器更新，复用同接口已审计12条nominal，保留所有失败。
不选择最终Tref，不替代完整30条件或指定ESN比较，不构成收敛证据。
独立工具runtime/clock_cycle00_fixed_representatives_v1；复制旧审计套件，评估入口采用source_train17_clock中已支持critic_clock的版本。
已核对完整source/parameter/upstream/assets清单和实际文件，checkpoint/fixture/plan/nominal物理收据；未覆盖旧runtime。
新登记SHA256 `b1c3f1d250de5f621a4c6db743d8f4d91fdcf2f711ff3736058fe1f47c2b25eb`。

首Direct被动回合165-action前缀独立确定性重放误差0：raw48/actor49/critic50/common7、逐action已知时钟、模型/fixture/plan/dt核验。
该检查仅覆盖启动前缀，完整55s和物理/filter/torque audit尚未完成；按原协调运行，不因观察超时重启。

## 原在线阶段继续

报告时真实进度如下（后续持续变化）：

|方法|steps|updates|cycle index|
|---|---:|---:|---:|
|direct|84139|79140|2|
|impedance|67609|62610|1|
|admittance|66833|61834|1|
|vmc|66112|61113|1|

原四learner1729888/1729892/1729893/1729897、归档1729901和审计1729905均核对live。审计按原计划等完整cycle1，未重复派发。
辅助结束后的GPU利用率不能沿用上一轮混合窗口68.6/52.2/33.3/35.8%；正式50%要求尚未解决。
不改physics/MJB、Task/Strict gate、actor输入、公共filter、执行器限制、dt及live learner设置。
最终指定ESN仍未获得，不用历史ESN或另一8条件矩阵替代本30条件比较。

所有原始产物在本集群`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`。
同名JSON记录证据地址/hash、启动核验和登记摘要；Git不包含checkpoint/原始轨迹。上一提交b836477的HTTPS push因非交互认证失败，未发布。

收尾Direct完整cycle1复核：82500steps/77501updates，30完整55s Task/Strict0/0、平均reward−32.920646（cycle0−32.788830，无改善）；失败approach24/align6。全82500 replay reward/done/current-next clock、30终端/模型/fixture/plan/dt核验，通过已保存回放证据而非raw-substep复审。原learner已进入cycle2，不重启。证据runs/clock_direct_cycle01_terminal_review_v1/REVIEW.json，未选新算法或奖励。
