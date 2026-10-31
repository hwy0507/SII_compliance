# 已更新90违规位冻结接口通过；首5000 loss检查

2026-10-30 UTC，Goal active。上一轮[有限90实际启动](RL_VIOLATION90_ONLINE_20261030.md)是progress。本轮核验真实更新后的52维模型能否完整恢复、保持RNG并执行冻结评测接口；原90训练和原88冻结继续，没有重启、加训练预算或自动91/Direct34。使用sii-research-sync，无子agent。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。开工及发布前实际query/fetch/read main `cb2631f0afc589a0b38e752471632e15ba74ce16`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未发现新相关科学协议变化。

## 真实已学违规位的冻结接口

源 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_frozen_preparation_20261030_v1`；预登记 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1/PRE_REGISTRATION.json`。读取原90启动时保存的准确快照：I新增1000、A1000、V2000；不是完整90 checkpoint。逐SHA绑定原startup报告及训练登记，恢复全部learner/Adam/alpha/RNG和全4m容量replay。两架构marker和23/47历史容量marker保持；原51历史已学状态不重置。

`evaluate_violation90.py`从原88完整评测器适配为52维，保留原物理/filter/torque/reward审计、0更新、30条件和外部随机种子；新增history与bit双绑定、实际90 continuation与步数/维度检查。完整90恢复入口真实拒绝当前partial90；不调用只允许原完整89元数据的迁移准备validator。正式物理入口还要求单独的LAUNCH_AUTHORIZATION绑定三路最终registration SHA，目前不存在，未派发。

实际三份更新后快照各执行同原89 short0600的1375条记录输入，连续native和每动作外部RNG切换的全部观测/raw/mixed/context精确相同，terminal clock/history/raw bit精确。实际bit0/1计数 `{'impedance': [95, 1280], 'admittance': [96, 1279], 'vmc': [96, 1279]}`，覆盖真实阈值切换。全1375 actor49隔离检查通过；全部learner、replay、全局/局部RNG与原checkpoint hash不变。每方法10个已学bit online/target列、5个在线Adam一/二阶矩非零，所有native动作总8271，耗时150.874秒；0新物理/0更新/0回放写入。这里只证明软件接口，记录输入来自89，不能当新90闭环结果。

预登记未来完整90三方法×全部30条件、原seed2026102638、最多123750动作/99000000物理子步/0更新。无需开发成功才能比较，所有失败保留；最终派发必须先有完整90 archive、full review、health、完整loss及实际图检查，再执行真正完整父check-only和单独launch。`register_complete90.py`对当前缺完整结果真实拒绝，三个最终registration尚未创建。原冻结88仍按原截止继续，新90评测未占用它的物理CPU。

## 固定前5000次更新的实际loss

源 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_progress_20261030_v1/prefix90.py`，结果 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_progress_20261030_v1/prefix5000`。三方法都取原始optimizer日志前5000个完整行，选择规则先登记；保存原字节、NPZ并独立标量复算全部统计，源prefix回读精确，六栏PNG已实际查看。critic首1000→末1000均值：

- I：1.990384→2.029705，最大34.852695；尾均值略升，3000与4500附近有抬升，尖峰保留。
- A：1.367704→1.220512，最大9.057354；早期尖峰保留。
- V：1.013427→0.812925，最大8.107876；局部尖峰保留。

全部记录值有限，但I actor loss仍有上漂，不能从actor loss正负或A/V早期下降推出任务成功/健康收敛。旧完整89尾段仅单列作上下文，51→52架构边界不能混合做同修订稳定统计；原88—90 A/V失败、I窗口不完整及其他历史失败不变。完整90 reward、loss与90—92新窗口尚未完成。

## 原进程、GPU与接续

训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle90_20261030_v1`，三原PID1096445/1096447/1096449及archive1096452保持。新检查期间180.063秒/19样本/104个原训练/90sampler/冻结88/guard身份保持，三路steps均增加。保存时 `{'impedance': 3699865, 'admittance': 3702178, 'vmc': 3703149}`；仍是部分90。

原冻结88 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1`，保存已完成条件 `{'impedance': 27, 'admittance': 26, 'vmc': 26}`，全90回合、最后全state不变、raw复算及82→88配对仍待；保留原21600s截止，不因观察窗口结束而重启。Direct33已接受数值阶段但冻结Task/Strict0/0，Direct28最终内存证明缺失仍披露；指定ESN缺失不替代，partial75/74—76不可判/79安全abort/所有失败窗口与halfstd拒绝均保留。

原v7 GPU守护继续；用户要求科研全部完成后仍保载，阈值50%/目标70%，不创建STOP。本轮59采样最低[78, 66, 71, 69]%，低于50样本[0, 0, 0, 0]，末值[80, 95, 96, 94]%；含合成守护，不代表科研吞吐或每瞬时保证，旧预热及历史低谷保留。守护不等于重启服务。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION90_FROZEN_READY_20261030/SMALL_EVIDENCE.tar.gz`，78成员/1510538字节/SHA256 `c772c15fd8f051bf6c94c688811b6e6b8c2987d1fc8914d6dba0f6ea83701449`，tar全部成员和Python AST已核；Git index/commit逐字核验、正常push和实际远端确认另记包外PUBLICATION。大快照/轨迹仍共享SSD，HDD仅原位254字节指针，非HDD/arm1全备份。
