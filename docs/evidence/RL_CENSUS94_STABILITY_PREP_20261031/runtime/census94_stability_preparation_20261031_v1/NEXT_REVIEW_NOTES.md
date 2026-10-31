# 固定94–96统计程序准备后的继续

原94训练PID1081267/1081271/1081275与archive1081280 start196529848保持，原guard96425–96429保持，科研结束继续保活不建STOP。全8353终端等待1895688/start196656130；全90比较等待2051280/start196679638。首先核真实PID/start和PROGRESS，不因观察器有限退出或工具句柄到期重启原任务。

固定94–96统计准备目录：
/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_census94_96_reward_stability_20261031_v1
含PLAN、SOURCE_LOCK、audit.py、review_saved.py、binding_rules.py、bind_inputs.py。绑定原在线94的STABILITY_WINDOW_INTENT，准确时点为94启动后首完整回合前；本轮只是后来源码准备，不冒充启动前登记。5%/nearzero1/5000bootstrap/seed2026102861固定。统计kernel除输出键名外等同原90–92，实际历史270回合全部结果精确复现、标量bootstrap区间复核通过；I/A原失败、V reward-only通过保持，非新94–96结果。

三真实94协议通过、33损坏配置拒绝；未来九组实际完整输入绑定未完成。没有REGISTRATION.json或REVIEW.json，没有95/96训练登记/自动派发。完整95和96各需独立有限科学审查。

完整94完成后先做原全回放/动作/reward/health/loss以及两个等待器产物的实际图/保存算术，再运行：
/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python /inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census94_comparison_20261031_v1/check_terminal_population.py --complete
需要真实新终端增长，不用首5000全非终端代替；在线每分层tensor未日志化不声称观察到。原health4096未投影fixed-min-pair仅诊断。所有原抽样loss用agent_train/original_sampled_q_loss，不用新条件q_loss宣布尖峰修复。

未来三轮全部完整并已实际看图后，建立显式input map九组method:cycle。每组protocol/review/health/finished/episodes/optimizer/loss_plot/health_plot/loss_review/plot_inspection/checkpoint均为{path,sha256}；bind_inputs.py --input-map <实际map>校验全部源/父链/实际checkpoint再以x模式写REGISTRATION/BINDING_REVIEW。此后运行audit.py --root <上述目录>、review_saved.py，再查看reward_stability.png。任何缺项或改变census版本/科学参数必须拒绝，不能伪造未来完成或替换窗口。5%与有限loss不能独自宣布联合健康收敛。

中断保全最新94 partial权重/Adam/RNG/replay/journal，另登记census-aware恢复；不回退完整93或重跑94，物理state未保存。全部历史失败、Direct33原数值验收/冻结0/0/旧28未全证不变性、指定ESN缺失保持。Goal active，无子agent。
