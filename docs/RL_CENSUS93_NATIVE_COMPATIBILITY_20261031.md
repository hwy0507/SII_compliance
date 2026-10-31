# 条件终端全量平均：完整原生更新与恢复兼容性（2026-10-31）

三路完整93父状态上的新版估计器已通过完整native训练路径验证，新增actor/target/温度实际更新、增长回放和中途保存恢复的证据。仅隔离副本测试，0正式更新/0物理交互；未登记在线94、未启动Direct34、未推广任何辅助权重。Goal active，reward稳定及原loss健康仍未证明。

## 实现及边界

`census_native.py`只替换原生train的q_losses赋值。先从冻结源重建原数值修复、terminal128、pair reduction和投影，使用相同compile文件名，实际code object marshal字节必须与现行native方法相等；actor/target/温度路径原样保留。新CensusCache继承原ExactCache.sample，原uniform/rejection和所有RNG调用不变；只扫描新追加dones、维护全部终端的五位mask分层。无新终端时不重新gather终端总体，不能把93终端总体冻结后用于新数据。

版本marker绑定模块SHA；完整93迁入仅加marker，保留所有learner/Adam/RNG与既有architecture标记。load后须明确绑定当前cache；新类拒绝缺失/变化marker。原旧loader不会主动拒绝未知marker，严格恢复入口用完整state digest发现规则丢失；不声称旧loader安全。

新训练日志同时返回原抽样`agent_train/original_sampled_q_loss`与条件估计`agent_train/conditional_terminal_q_loss`，原`agent_train/q_loss`在新版指条件估计值。在线健康判断必须另看原抽样口径。条件期望对应原终端SSE/gradient的期望，不代表有限Adam轨迹相同，不使用平方平均残差。

## 实际有限验证

第二版每方法四臂×8完整native更新：原生对照、候选、候选重复、候选4步后保存并重载再4步，共96次。每步追加一条原历史行作为兼容性fixture，交替终端/非终端；不是新物理样本或新训练预算。actor、target、温度均实际更新，初始Adam超参/moments保留。

- 三方法候选/重复/中途恢复的完整state每字段digest、metrics、全部8批indices与RNG均精确；原生对照与候选的抽样序列、RNG及回放相同，但权重轨迹不同。
- 每方法真实65536首批，用独立NumPy分层权重重算全部5critic loss及梯度，最大梯度差均0。
- 每方法9拒绝例覆盖marker、重复迁入/绑定、未绑定更新、旧loader丢标记、截断/替换回放及非法done；额外4loss负例覆盖缺失terminal stratum、零denominator、非法mask/done。
- fresh空缓存、有终端→空/无终端重载、16行增量只扫描16行、无追加refresh不重复扫描、非法restore的测试通过；空终端总体的loss与原nonterminal公式逐元素相等。
- 独立读取三份磁盘restart_fixture.pt与原93：所有旧回放前缀精确，前4新增fixture/action/reward/done以及随机bootstrap mask精确，独立重算4个accepted抽样和replay RNG精确；全部critic/actor/温度Adam计数器分别增加4。完整原始checkpoint哈希未变。

| 方法 | 原终端数→8步fixture后 | 原生对照原抽样loss均值/最大 | 候选原抽样loss均值/最大 | 候选条件估计loss均值/最大 |
|---|---:|---:|---:|---:|
| 阻抗 | 2785→2789 | 1.156355 / 1.262427 | 1.151784 / 1.255414 | 1.464809 / 1.592587 |
| 导纳 | 2784→2788 | 1.124369 / 1.304056 | 1.120002 / 1.304056 | 1.122084 / 1.330342 |
| VMC | 2784→2788 | .761513 / .896025 | .758939 / .894832 | .771292 / .902470 |

这8步只验证实现与恢复，不能证明此前原尖峰消失或线上科学改善。上轮256步对照中I最差原batch13.098仍大于control12.145、I新93改善弱于对照、旧92中止较初始更差、V unmasked退化仍保留。

## 第一版失败及修复

第一版仅运行阻抗32次隔离更新。metrics/RNG/draw一致，但最终state相等断言失败，完整trace保留；没有派发A/V第一版。独立存储检查确认原loader的Adam CPU step与传入state共享：critic50/50、actor8/8、温度1/1；因此重复测试的reset reference会被副本训练写动。第二版在census加载时取得完整learner独立副本，原生对照测试也用独立输入，三组别名均降到0，并通过所有状态/原checkpoint不变检查。该问题不意味正式93存档被改写。

另有独立空回放负例：indices已清空，但旧terminal tensor残留1行；第二版在恢复前清除全部派生终端缓存再重建，空/无终端路径均通过。第一版源码、失败记录、32次更新和未通过结论保留；总隔离更新128，其中通过第二版96。没有通过增加训练预算掩盖失败。

若干辅助只读命令猜测文件路径不存在，已定位实际源；一次概要命令误用系统Python缺NumPy，改用固定env解释器。没有据这些命令失败重启科学任务。

## 下一步及保留事项

下一步单独登记在线94的有限driver、trainer/cache绑定、marker消费者、启动审计和原抽样loss记录；具体接入要求见NEXT_ONLINE_NOTES.md。正式父仍三路完整93，所有本轮restart_fixture权重仅测试用途。每方法拟议一轮≤41250新增仍须正式登记，无自动后续。

原物理/MJB/Task/Strict/canonical48/filter/actuator/dt5e−5、critic52/actor49、clock/history/rawbit、23/47容量marker与append-only4m、LR/reward/masks/terminal128/batch65536/UTD1保持。原90—92窗口失败、92→93reward变化、partial75、不可评74—76、79/90/92中止、冻结90及halfstd拒绝等全保留。Direct33原数值验收和冻结30 Task/Strict0/0、旧28证明不足与恢复2不变结论保持，指定ESN仍缺；最终独立比较未完成。无子agent。


## 来源、GPU与保存

实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮实际query/fetch/read main `27ac709a18db7cae5b4c4e266bd57a77b10fdab6`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，应用仓库sii-research-sync。源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/census93_native_compatibility_20261031_v2`；诊断 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/census93_native_compatibility_20261031_v2`；原完整93归档仍是下一步科学父，未创建正式checkpoint；本轮三份restart_fixture.pt仅用于隔离恢复测试，不能推广权重。来源/有限预算见PLAN与SOURCE_LOCK；三路原生兼容测试、独立保存文件和边界检查已完成。原生测试源码锁定后未改，辅助只读检查另列源码；第一版失败与32更新完整保留。

新主机独立GPU guard继续，科学结束不退出；本次保存采样窗口126样本/637.125秒，最低[76, 77, 76, 70]%、低于50[0, 0, 0, 0]、末值[79, 80, 79, 72]%。含synthetic guard，不等于科学训练吞吐或每瞬时保证；先前主机恢复启动0%记录仍保留于上一交接；不是系统重启服务。

SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS93_NATIVE_COMPATIBILITY_20261031/SMALL_EVIDENCE.tar.gz`，49成员/148888字节，SHA256 `1897580a16941fc62d30d67035f9ed4b70cfc7a6020f1295fe6fe42346b8a9db`，逐成员字节/AST核验。manifest `docs/evidence/RL_CENSUS93_NATIVE_COMPATIBILITY_20261031/MANIFEST.json`，提交字节及实际push核验收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS93_NATIVE_COMPATIBILITY_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原LATEST254字节原地更新回读，非HDD/arm1完整备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
