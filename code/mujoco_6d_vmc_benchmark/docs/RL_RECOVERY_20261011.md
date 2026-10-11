# RL启动故障修复与本机恢复

12:10 CST实证更新：两路各完成1条完整55秒新训练回合，并进入下一回合；
直接动作累计110000步/210002更新（本次已记录3084条优化器更新），调阻抗106000步/
202002更新（本次3000条）。两条各1100000物理子步独立复算三指标、模型/原始轨迹/
执行链hash、训练动作记录与filter一致性通过；Task/Strict均失败照常保留。
这验证恢复后的训练与落盘链路，不是固定策略开发成绩；尚未到新10k checkpoint保存节点。
本次审计未新增物理步、梯度或final读取。工具为`audit_rl_recovery_episodes_20261011.py`。

用户2026-10-11在确认昨夜未训练后，重新授权立即继续运行并监视。开工读取远端
main `8a4be097ad861c54d20efbbc7fbc35f1292b119a`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`日志与AGENTS；未合并baseline。
服务器仅存储，原经典90回合、失败过夜run和所有历史checkpoint不覆盖。

## 修复

- 父协调器只在预检/准备时持仿真锁，调用子协调器前显式释放。子协调器重新核验并独占
  仿真锁；交接期间若有其他作业抢先获取，安全失败，不并行越限。
- 外层使用独立协调器锁并拒绝已有execution，所有预检/准备/子进程异常落盘且向上抛出。
  子进程非零退出不会再被systemd报告成外层成功。
- 可显式登记新run名、当前授权与有限安全窗口；原失败收据和原源码保留。
- 复用旧评估前，核对父checkpoint、审计hash，并重新从16条原始轨迹独立复算物理子步
  指标、检查动作/身份/模型/归一化证据；新审计与原rows完全一致后才允许省去重复物理评估。
- 一路失败时创建本run独立STOP_REQUESTED，另一训练路在回合边界保存checkpoint后停止；
  不向整个进程组发信号。原奖励、观测、控制律、模型、门槛和执行器约束没有变化。
- 新一次性连续监视器每30秒记录实际steps/updates/episodes/checkpoint、worker服务状态和
  评估进度。实验失败优先于systemd的success字样；20分钟无记录进展写ALERT并非零退出。
  该监视器不自动重启、不派发仿真、不发送外部消息；它也不等于agent永远在线。

15项检查通过：6项协调器（包括真实父子进程锁交接、真实子退出23传播、过期不派发），
6项接续/判据（含禁止替换父checkpoint），3项监视（含误报成功、停滞与退出无终态）。
真实旧16条开发证据已重验通过，零新增物理步；这是复用依据，不是新的开发成绩。

## 当前运行与预算

12:01:50 CST，`sii-recovery-20261011-v1.service`启动；12:01:55两路训练派发。
仅airpig本机，两路各一个模拟器/数值线程1/MemoryMax3GiB/MemorySwapMax0，
CPU亲和1,6与2,7；初始可用内存超过7GiB，40GiB磁盘保留。
父协调器2GiB用于准备与原轨迹重审，监视器256MiB，无服务器实验。

首节点为直接动作office_task从108458步、调阻抗从104500步接续到165k预算，
然后同8个development条件独立评估与审计；其余5个已登记配置按空闲lane接续。
保留原165k/220k/330k/499125节点与失败平台停止规则，不把零成功叫收敛，不无限追加预算。
原actor为canonical48，纯RL不使用teacher标签；没有新奖励或算法机制变更。

本次agent设置24小时派发安全上限，至2026-10-12 12:01:50 CST；依据是本次继续授权，
不是把昨夜已结束15小时窗口重新计算，也不是用户承诺的训练时长或收敛标准。
trainer在截止后的回合边界保存退出；未完成节点不得当作完整结果。

12:04 CST直接动作108750步/207502更新，调阻抗104750步/199502更新，
两路训练实质增长，首新回合尚未结束；无ALERT。峰值内存限制已实查生效。
首回合及后续checkpoint状态以追加进度和实时收据为准。

本机运行根：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/recovery_20261011_v1/`。
外层收据在同outputs下`rl_recovery_coordinator_20261011_v1/execution.json`，
实时监视在`rl_recovery_monitor_20261011_v1/LATEST.json`和`events.jsonl`。
这三者与真实服务/worker一起判断进度，不能只看任一running字样。

## 已核验共享

`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_recovery_setup_20261011/evidence/`
含冻结执行源码source、外层/监视源码tools、测试、登记、source hashes和两份重审。
594文件5251685字节，manifest SHA
`30434c95ad548ad349877b380f882402eb1a99d986ddb968ca94b849b113f05f`。
这是设置与审计包，不包含新生成的训练轨迹或未来checkpoint；新训练产物当前仅本地。

首新回合审计与12:10附近监视快照另存：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_recovery_first_episodes_20261011/evidence/`，
3文件13813字节，manifest SHA
`bb75e8ae1e2542d4e184010f23e7131122a7476435da2981b27fb37d73f3e4f6`。
它是明确时间点的运行快照，不代表后续节点已完成，不含两条大轨迹。
