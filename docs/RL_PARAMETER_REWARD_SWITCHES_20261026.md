# 参数27–29奖励波动定位与下一稳定性窗口（2026-10-26）

Goal active，尚未健康收敛。原正式Direct19与参数30持续，本轮没有更改正式物理/MJB/SPT/gate/filter/执行器、网络/优化器/RNG/replay/history或训练设置；无子agent、不推广辅助权重、不重复已完成温度/floor/冻结16等实验。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。当前完整科学基线见RL_PARAMETER30_STABILITY_20261026.md。

## 新保存数据审查

B/runs/parameter27_29_reward_switches_20261026_v1，原2727830已完成。完整27–29结果可见后登记，明确探索性，所有3方法×3轮×30条件保留；576份输入引用在执行前封存并前后hash核对。共371250条保存transition逐项核奖励分项之和、每1375条的episode回报、原完整review已重建reward0误差；270份terminal/rollout的Task/Strict/abort/horizon/MJB标签精确对照。0新物理、神经前向或优化，不是独立重算原始物理子步。

|28→29|整轮平均回报差|成败切换条件的贡献|其余条件贡献|
|---|---:|---:|---:|
|阻抗|+1.806087|short0600 +1.803304|+.002783|
|导纳|−3.303383|short0600与short0900 −3.376112|+.072729|
|VMC|−1.771414|short0600 −1.750606|−.020807|

阻抗净增幅99.8459%来自short0600的Strict假→真，Task保持真；VMC净下降98.8254%来自short0600的Strict真→假，Task保持真。导纳short0600保持Task真但Strict真→假，short0900的Task/Strict都真→假，两者下降被其他条件略微改善抵消，贡献可超过净下降100%。没有丢弃这些条件重算“已收敛”回报。

全部分项均保留；28→29平均terminal项I/A/V为+1.666667/−3.333333/−1.666667，completion_efficiency为+.120606/+.050788/−.075273，penetration为+.019262/−.022525/−.029389，其余分项合并补齐真实均值差。不能把奖励跳变全归为穿透连续惩罚。

|short0600保存的最大外穿透（mm）|27|28|29|
|---|---:|---:|---:|
|阻抗|.200389|.219988|.192556|
|导纳|.200335|.184475|.226281|
|VMC|.224463|.195817|.226764|

这些保存峰值位于原.2mm门槛附近，和上述Strict标签变化一致；本轮未重算原始substep峰值，未放宽判据。在线策略和动作样本同时改变，算术归因不区分学习漂移与动作随机性，也不是单条终端导致loss变化的因果证明。旧25/26终端loss集中度与固定804终端跟踪已完成，本轮没有重跑它们。

另用原episode和math.fsum独立核对均值变化、切换集合、每条件分项和，SAVED_VALUE_REVIEW通过。outcome_switch_contributions.png已目视核验，报告全部条件的剩余贡献与三轮short0600保存峰值。新两个审查源码在code/mujoco_6d_vmc_benchmark/tools；AST和实际执行通过。

## 原训练与第31轮准备

原Direct19 learner1326215/归档1326258/review1326260；参数30 I2344423/A2344425/V2344430/归档2344573/review2344575保持，首1000/1000/2000新增启动审查已在前轮通过。Direct20原准备2086366和原19 CPU调度2086367仍在等待完整19，不重启或自动训练。

新参数31等待2801577，仅完整30 FINISHED/REVIEW后prepare+check-only；新原30 review CPU调度2801579仅三个learner退出后复用CPU13。prepare/launch/monitor精准指定父30与新31、准确父cycle_00030、原2m历史入口23、全部state保持，无自动31训练。该准备不宣称已完成实际恢复；后续需检查原check-only与完整科学结果后正式启动。

本轮采用限定命名/字段替换，逐AST验证真实B根路径、pool30不变、历史23不变与当前30 review适配源码；保留逐文件diff与STATIC_REVIEW，避免前轮宽泛数字替换误改工作目录。所有等待7200秒有界，不自动延长。

## 新30–32完整窗口预登记

B/runs/parameter_capacity30_32_reward_stability_20261026_v1，原等待2830862。登记时30三路均0完成条件，31/32未启动；保存当时进度和30协议hash。固定30/31/32、三类各10、5000条件配对bootstrap、seed2026102632，沿用原5%描述规则/近零保护1。全部完整FINISHED/REVIEW后才封存最终episode/optimizer/health输入并分析。

新增绝对相邻均值变化和三轮均值范围，供接近零时读数；没有添加新的绝对收敛门槛或把近零保护改成通过。该窗口全部完整结果在登记时均属未来；训练策略变化，bootstrap仍只表示条件组成敏感性，不是独立训练seed或冻结策略验证。无自动停训或正式31/32发车；源码AST检查通过，实际分析尚未执行。

## 同步与边界

本轮真实远端查询/fetch/read main dbb1d76ed79177067c48ed49ff9f67f023c704aa和baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d未变；GitHub认证仍待，已问不重复。小证据docs/evidence/rl_parameter_reward_switches_20261026，包含原2727830完成结果、独立保存值检查/图、31准备和新窗口登记/等待记录与实际live快照。大产物SSD，HDD仅小交接/收据，非完整HDD/arm1备份。

GPU沿用已完成纯19/30固定60样本：57.3/67.9833/67.9/69.1333%，本轮未重采或用额外任务补占用；启动审查/恢复空档事实保持。指定ESN仍缺，已问勿重复；健康收敛、最终冻结策略验证和最终比较仍未完成。

本轮科学提交8867d28026d4b5a68c9f0ee6420517b5f78d3c85仅本地，push认证失败。完整小证据包/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER_REWARD_SWITCHES_20261026_231602/FULL_SMALL_EVIDENCE.tar.gz，30成员逐hash/大小核验，755979字节，SHA256 2a0e8588c6cf955e31b04a8590dd08d21f2721874c796e909509e18e8a4c84dd。HDD最新/inspire/hdd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_shutdown_backup_20261026_v1/RL_PARAMETER_REWARD_SWITCHES_STATUS_20261026_231602/HANDOFF.md及收据/LATEST已核验，大产物仍SSD，非HDD/arm1全备份。原19/30和20/31准备、固定30–32等待继续，Goal active。
