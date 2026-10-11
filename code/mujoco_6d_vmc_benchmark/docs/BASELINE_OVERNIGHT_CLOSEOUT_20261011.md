# 2026-10-11 过夜结果与启动故障核查

开工核对远端 main `6023800c9632c8de6a043338f6fa6b544481aede`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，fetch并读取两日志与AGENTS。
本轮仅核查与归档，没有新仿真、训练或final条件读取，没有修改算法或环境。

## 经典控制器：90回合完成

原登记54筛选＋36确认全部完成，每类30回合。2026-10-10 22:02 CST收口，
连续监视器为`verified_complete`。10月11日11:53 CST再次独立读取并核对全部90条
轨迹hash、条件/参数/seed/模型/路线以及物理指标、动作与控制器重放审计收据，通过。
原登记SHA `44e1094a88d86130aa7ec2d22dea99acd63d6fab1ad3e6ec6a584f6ccfe7035e`不变。

以下是筛选top2各自的8条件开发确认，未按事后结果只保留较好者。
三项连续指标均为8回合各自指标的算术均值，峰值列不是所有回合的最大值。

| 方法/候选 | Task | Strict | RMSE mm | 回合峰矩均值 Nm | 回合峰速均值 m/s |
|---|---:|---:|---:|---:|---:|
| VMC boundary_00 | 0/8 | 0/8 | 26.904 | 38.590 | 0.3754 |
| VMC boundary_05 | 0/8 | 0/8 | 26.185 | 38.524 | 0.3739 |
| 导纳 boundary_06 | 0/8 | 0/8 | 39.999 | 37.619 | 0.3730 |
| 导纳 boundary_07 | 0/8 | 0/8 | 25.224 | 39.106 | 0.3677 |
| 阻抗 boundary_02 | 0/8 | 0/8 | 24.527 | 35.925 | 0.3795 |
| 阻抗 boundary_01 | 0/8 | 0/8 | 24.861 | 34.834 | 0.3737 |

全部90回合均完整55秒，无物理安全早停；上述48条确认全部停在carry。
六候选各自最坏外部穿透为0.181640、0.186187、0.184915、0.185954、
0.186746、0.180509 mm（顺序同表），均低于0.2 mm。
这是冻结综合环境、正式步长5e-5下的开发调参证据，不是最终保留条件的泛化成功率。
此前clear基础搬运正控制通过；active_only与edge_only归因见经典验收报告。
结果支持所测有限参数范围下的接触停滞，不证明经典控制器普遍不能解决，也不因卡住
而继续无限调参或增加手工恢复机制。最终策略冻结与全方法统一最终评估仍未完成。

## RL：昨晚未启动，新增训练为零

15小时协调器起点为10月10日20:43 CST，截止10月11日11:43 CST。
经典完成后，22:03:01调用RL子进程时，父进程仍持有全局仿真文件锁；
子进程`launch_rl_convergence_20261010.py:154`再次非阻塞获取同一锁，报
`BlockingIOError: [Errno 11] Resource temporarily unavailable`并退出1。
这是我们新增协调器的锁交接实现错误，不是RL学习失败、内存不足或收敛。

外层execution记录`failed_preserved`、`rl_returncode=1`，但外层脚本正常返回，
使systemd显示`Result=success/ExecMainStatus=0`。因此仅查看服务成功状态会误判。
原测试没有覆盖真实父子进程的锁交接及子失败退出码传播，监视缺口导致整夜未及时发现。

新`overnight_15h_20261010`只有REGISTRATION、SOURCE_HASHES和source，
没有execution、训练轨迹或新checkpoint。旧完整已审计direct office_task为108458步、
RL impedance为104500步，各8开发条件Task/Strict均0/8。
其他计划恢复父checkpoint：RL导纳55000、RL VMC55000、direct metric53630、
历史entropy direct54091、历史entropy RL阻抗55000步。
旧中断接续的部分checkpoint另行保留，不能算成本次过夜训练增量。

11:50后检查无运行中的sii服务；窗口已经结束，本轮不重启或延长训练。
待修：锁所有权交接、失败退出码传播、真实进程集成回归与失败监测。
这些修复尚未实施，不能宣称RL baseline已经训练收敛或完成最终公平验收。

## 证据位置

本机benchmark工作集：
`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/`。
原轨迹为`classical_boundary_search_20261010_v1/`，只读复核为
`classical_close_verified_20261011/LATEST.json`，启动失败原收据为
`overnight_baseline_coordinator_20261010/execution.json`。均保留未覆盖。

本轮小包`baseline_closeout_20261011/evidence/`包括原CLOSE、新复核、完整候选选择、
失败execution与当时故障源码；5文件218613字节，manifest SHA
`4215d0701bb622c53039117a6c32b6d3ccb6fdfdb31f93caf8e98187f8703624`。
服务器发布状态收工时写入UPDATE_LOG；本小包不包含90条大型原始轨迹。
