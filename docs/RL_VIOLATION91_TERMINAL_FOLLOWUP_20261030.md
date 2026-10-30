# 原91继续；固定87全部终端跟踪91已登记

2026-10-30 UTC，Goal active。前序[91固定前5000审查](RL_VIOLATION91_PREFIX_20261030.md)。本轮在原91运行期间登记完整91后的固定旧终端诊断；没有新训练阶段或物理派发，无自动92/Direct34。完整91 reward和loss健康仍待。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。实际query/fetch/read main `6a0ff6876927768cd6c16df193489677238aed6a` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关科学协议变化。采用sii-research-sync，无子agent。源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation91_terminal_followup_20261030_v1`，诊断run `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation91_fixed87_terminal_followup_20261030_v1`。

固定原87全部7813终端（I2605/A2604/V2604）、all5 critic和原masks；87/88/89/90全部预测及inputs来自已审90跟踪NPZ。全部masked SSE/MSE、all-row SSE和分母精确复算，52维输入逐位绑定原51特征与raw preaction >.0002m位，bit分布 `{'impedance': {'0': 2535, '1': 70}, 'admittance': {'0': 2544, '1': 60}, 'vmc': {'0': 2559, '1': 45}}`。没有新增forward/physics/update，真实缺完整91入口拒绝通过。全部改善和退化保留，不挑表现较好的critic或终端。

原evaluate_violation90只允许90，因此新增本诊断专用validate_architecture91/validate_recovery91，不修改原冻结90 evaluator。准确parent steps取完整90已审记录，I3729700/A3732500/V3733500；继承bit/history原修订floor90/88，双marker、learner/replay52、seed/controller/registration、4m cursor/size、continuation和partial75排除保持。以实际不可变startup91三份checkpoint核验：architecture均通过，完整边界均拒绝，27项错误周期/seed/协议/controller/旧89步数/cursor/capacity/marker/next51负例均拒绝。该检查没有构造未来完整91证据、没有网络forward或训练。

首check91.py在第一路写报告时出现JSON字符串路径.read_text的AttributeError，原源码、PLAN及失败说明保留；check91_v2.py只把读取参数转Path，三路重新完成。原科学作业未重启。LAUNCH_REVIEW绑定实际v2源码hash及VALIDATOR_REVIEW，原PLAN所有source hash仍一致。

唯一等待器PID `1706570`、start `577160264` 已启动，核验原archive689765身份；沿用原91 launch+14400s截止Unix `1793410915.7118208`，不延长训练/归档预算。完整91 REVIEW/FINISHED/health/loss全部到齐且同checkpoint后，才读取准确归档cycle_00091.pt做all5原终端预测，检查learner/replay/RNG/checkpoint不变、独立复算并出六栏图；分析预算1800s，最终实际图检查仍需人工执行。当前没有91终端预测结果。

这是固定已见旧终端拟合/保留诊断，不是策略安全或泛化/收敛门槛；原90 I改善83.45%、A退化9.70%、V退化146.79%的masked SSE证据不覆盖。91新终端由原全回放health诊断负责。完整90 I long0000全局穿透安全中止与外部bit0局限、原失败窗口、partial75、74—76不可判、79安全中止、半std拒绝和所有软件失败保留。Direct原数值验收与冻结33全30 Task/Strict0/0及旧28最终内存证明缺失保持；指定ESN仍缺，不替用其他模型。

原91训练/采样/归档、原冻结90/evaluator/collector/postprocessor、guard及新唯一等待器经过180.075s/19样本/105身份检查，三路steps增加。保存steps `{'impedance': 3745137, 'admittance': 3747935, 'vmc': 3748645}`，冻结90完成 `{'impedance': 4, 'admittance': 4, 'vmc': 4}`/各30。完整91和冻结90全90/raw/88→90配对及最终内存不变仍待。

GPU原97370/97399–97402继续，科学结束仍保载；86样本min[65, 66, 68, 69]%、低于50[0, 0, 0, 0]、末值[72, 91, 92, 96]%；含合成负载、非科研吞吐或每瞬时保证，非重启自启服务。原物理/MJB/Task/Strict/filter/执行器/dt5e−5、actor49/canonical48、52输入/历史/Adam/RNG、4m/terminal128/batch65536/UTD1/原LR/reward/masks保持。

证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION91_TERMINAL_FOLLOWUP_20261030/SMALL_EVIDENCE.tar.gz`，41成员/40191字节/SHA256 `c1ca2d5c06ac468fa24e72a5a80b1c7427d95876549c6b964c80287ded47e4a1`，逐成员及源码AST核验；Git index/commit逐字和正常push/远端确认后写包外PUBLICATION。大产物共享SSD，HDD仅254字节指针，非HDD/arm1全备份。接续保持现有原91与冻结90，完整91后审查loss/health/固定终端和任务标签，再决定后续有限阶段。
