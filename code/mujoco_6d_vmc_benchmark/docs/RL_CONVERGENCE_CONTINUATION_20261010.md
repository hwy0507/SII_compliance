# 仅本机 RL 接续：开发曲线、稳定成功与失败平台分开记录

用户2026-10-10再次明确要求：继续把RL跑到收敛，再看效果，只用本机算力。
这是旧15小时窗口结束后的新接续授权；不再因旧窗口已收口而只做只读监视。

## 当前执行

13:14 CST，连续服务 `sii-convergence-20261010-v2.service` 已在 airpig 启动。
两路正在重评已有 direct office_task 108458 步和 RL impedance 104500 步 checkpoint，
各使用相同8个 development 条件。完成这一轮后自动接续训练到165k，之后220k/330k/499125；
499125是按完整回合保留的约500k节点，不是“收敛”的替代定义。

七配置全部列入有限队列：direct office_task、RL调阻抗、RL调导纳、RL调VMC、direct metric，
以及直接task/调阻抗的两个历史熵对照。前两项从已完成110k段恢复；其余五项从已完成55k段
恢复，在lane空闲后补到165k。后续比较使用共同节点，不把不同曝光混成同预算算法消融。

旧 coordinator、checkpoint、协议和失败收据保持原样。新运行根目录（本地实际执行来源）：

`/home/airpig/桌面/hwy/compliance_control/SII_compliance/code/mujoco_6d_vmc_benchmark/outputs/baseline_local_rl_20261009/continuation_v2_20261010/`

关键入口：`REGISTRATION.json`、`SOURCE_HASHES.json`、`execution.json`、各训练目录内的
`execution.json`、逐回合原始轨迹及 `*.development_audit.json`。注册SHA256：
`56542a1a43c30d6a1cbc7e1fda6d003e45740eda94536c4f53397aee91a433bc`。
续训冻结源码、登记与测试已核验归档至
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/rl_convergence_v2_setup_20261010/evidence/`。
589文件、5192187字节，manifest SHA256
`15d66fbf101fd50303e79c3eae4aef181778d541c2e1f0e96c4667a0be868486`。
归档包含启动时报告快照；后续进展以GitHub新提交和实际运行收据为准，未包括正在生成的物理回合。

## 如何判断收敛

- 每个评估节点使用同8个development身份、固定模型推理，保存全部失败；训练中的6/40或2/40
  不作为开发成功率。
- 沿用此前登记的操作性筛查：连续3个节点、跨度至少22000交互，每个Task≥7/8且Strict≥6/8，
  Strict计数波动≤1，才标记稳定可用候选。随后还需独立训练seed和完整学习曲线确认；
  本轮单seed不能自动宣称统计收敛或直接用于最终ESN优势论证。
- 三个≥110k节点均Task=0时，标记学习失败平台并转学习机制复查；不称成功收敛，
  也不为追求数字继续无信息增益地空跑。新reward/n-step候选仍需独立登记和闭环验证。
- 达到步数上限、安全截止、磁盘不足或启动错误只表示本段结束/中断；不表示研究目标完成。

## 资源、身份与复现

计算仅在airpig；服务器只读/传输/归档，显示配置不动。最多两路，每路一个模拟器，
MemoryMax=3GiB、MemorySwapMax=0、数值线程1、CPU affinity分别1,6和2,7。
协调器单独1GiB，不运行物理；入场要求可用内存≥7GiB。
使用原全局 `.local-rl-compute.lock` 防重，检查真实宿主机systemd，不能把沙箱内的ps当作全机视图。

登记72小时派发安全边界，至2026-10-13 13:13:46 CST。这是agent选定的有限运行保护，
不是用户新增的小时预算、旧15小时限制或收敛标准；到界仍未解决应依据本次持续授权审查接续。
保留40GiB磁盘余量，派发前另预留当前并行段所需空间，训练每回合边界检查磁盘。

保持原正式MJB（SHA `d4c28e40950d6c8414e7e3b667b0a7070be8d816b71483b88df8b373ee7778e3`）、
dt=5e-5、32训练/8开发身份、Task/Strict、canonical48本体输入、执行器限幅/变化率和公共filter。
不使用teacher/BC，不读final。原reward、n-step=1和500k优化器日程保持；完整恢复
actor/critic/target/temperature/normalizer/optimizer/replay/RNG。

新trainer增加显式 `--continuation-registration`，仅变更已登记接续的派发期限和资源边界，
核验原协议hash、主机、seed、job、上限与输出目录；不修改旧协议使其hash变化而破坏精确恢复。
新source快照保留旧worker/物理源，仅叠加入口与审计工具，保存逐文件hash。

各开发回合执行后独立复算RMSE/峰值力矩/峰值速度的物理子步，核验48D观测、原始请求、
公共过滤/执行链、actor重放、冻结归一化、模型/条件/checkpoint哈希；参数RL另做参数递推审计。
五个新停止条件回归、原七个接续回归、语法和diff检查通过。实际完整新开发结果与梯度接续
尚在等待，不能以启动服务成功替代训练成功。

## 同步状态

本轮已实查远端main `6e31e394617b92ad067aab798e3037b930a6bfe9`、baseline
`f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`并读取两个UPDATE_LOG，不合并baseline。
此前GitHub/SSH失败来自沙箱网络限制；本轮宿主机访问均正常，并非已证实的远端故障。

13:28 CST补充：两方法各完成前2条开发回合，均为完整55秒、Task/Strict 0/2、
worker动作重放误差0；其余6条正在依次运行。部分开发结果不能替代完整8条件结论。
历史55k阻抗的8条真实开发轨迹已通过新审计入口复算，审计SHA
`a07f3653c93901bc4666195beb4fd8ef0f90e9840f067e761e0c2e7c9eff955b`，新增物理步0。

此前两110k完整训练段另作大型归档：3096文件、13504141567字节，manifest SHA
`f91bab36baf92a82eff7f0d08532a204d740386172a1ecca4306568286021588`。
目前仍传输至`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/incoming/rl_closed110k_20261010/`，
**未核验发布**；新一次性本机服务`sii-rl-archive-finish-20261010`等待当前rsync的精确进程身份消失，
再进行远端全文件校验，成功后才发布为独立run。结果以本地新运行根的
`CLOSED110K_ARCHIVE_TRANSFER.json`为准；失败保留暂存与原始文件，不重启或打断训练。
