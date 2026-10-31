# 第93轮候选审查后的新主机恢复（2026-10-31）

当前主机为 rltest-1025--a6ed2ff39b3c-cn2p6rygmr。发现原主机t55ahnz53q已被替换、原工具句柄失效、原guard五进程不存在，四卡实际利用率0%。没有据旧句柄或旧PID重启科学任务；先查全/proc确认无其他guard，再恢复相同已存档保活算法。未推断容器更换的精确时间或原因，不能声称切换期间一直高于阈值。

## 保活已恢复

新目录 /tmp/sii_gpu_util_guard_20261031_recovery_v1；supervisor PID96425/start196287191，workers96426/96427/96428 start196287194、96429 start196287195。CPU4—6、原floor50/target70/min duty.70逻辑保持，源码与SSD存档SHA5600eb0cfe76c2eb2f88d2341a77878b8021b70de0efaaadb2094cd7382a8db0逐字相等。新主机上科学任务完成后guard继续，不是重启服务；不要创建STOP。

完整恢复窗口79样本/399.133秒，最低全部0%，各卡2次低于50，均保留。首次四卡均达50后77样本最低73%/81%/77%/83%，无低于50；末值78%/90%/79%/88%。另保留启动前人工查询四卡0%的记录。切换间隔无连续测量，未补造利用率。含synthetic guard，不等于科学吞吐。

## 冷恢复验证

新主机逐hash核验Direct33存档及843项源依赖；三路完整93恢复校验双架构marker、正式边界、回放容量和历史标记。全部8353终端的五critic预测、每方法首个原生65536批次预测与旧主机保存值逐元素相等。完整learner/Adam/replay/RNG与checkpoint不变，0optimizer/physics；不是重跑评测或新的收敛证据。冷恢复进程正常退出0。

| 方法 | 完整93步数 | 终端数 | 新主机比对 |
|---|---:|---:|---|
|阻抗|3852762|2785|全部终端与首批预测精确|
|导纳|3856250|2784|全部终端与首批预测精确|
|VMC|3857250|2784|全部终端与首批预测精确|

Direct33仅本轮追加存档hash确认：783eaa7f7b03226915539e41cce313a5faeb4d49a15ae25626bb9762a9f47849，没有新Direct恢复/冻结运行或34。原数值验收和冻结30 Task/Strict0/0、旧28内存证明缺失及恢复2全state不变结论继续保留。

新环境Python3.11.17、NumPy2.2.6、Torch2.8.0+cu128、CUDA12.8、MuJoCo3.11.0；四张RTX4090，driver595.71.05。实际GPU UUID记录在COLD_RESTORE_REVIEW，不能沿用旧主机设备身份。

## 中断的发布已完成

上一轮科学提交4575eddaedf26da5682729e6802e156e37e0e38f及45文件提交字节核验在主机切换前已完成，原工具句柄9445失效后通过实际git和GIT_BYTES_REVIEW确认，没有重复运行科学工作。

远端并行更新到397bc1f0，属于非RL final108零物理控制审计。安全merge时唯一冲突是UPDATE_LOG顶部；验证双方均以同一9bd8d0d8版本为完整后缀，保留双方新增前缀及原共同内容。其他非RL文件原样合并。merge571b05a0e3d5d3876cc4239efac617a61cc1fa83已正常push、实际远端确认，两条祖先均保留，全部38项科学evidence字节在merge提交中重新验证。旧科学包39成员/SHA8a6c838194a2bafa5736cfc8bbc7a55ae5ee617f7862ed3b51ad2e1d6583751c，未覆盖。

原发布收据在 repository/RL_VIOLATION93_TERMINAL_CENSUS_ABLATION_20261031/PUBLICATION.json，明确记录科学主机与发布主机不同、旧guard消失及新guard恢复，未把新恢复冒充原连续进程。

## 科学下一步未改变

条件终端全量平均的隔离对照有利：全终端masked SSE相对对照I−31.67%/A−88.59%/V−86.67%，原抽样loss均值−7.46%/−7.17%/−5.16%。但I最差原始batch13.098仍高于对照12.145、I新93改善弱于对照、92中止较初始更差、V unmasked退化保留。仅critic更新且目标冻结，尚非完整在线证据。

下一步独立准备完整native actor/target更新、增量终端缓存、持久规则及恢复兼容验证，具体已读代码接入点见NATIVE_NEXT_NOTES.md。没有实现或执行这些未来验证，没有在线94登记，没有辅助权重推广。正式父仍完整93；原reward稳定/loss健康未证，Goal active。

原physics/MJB/Task/Strict/canonical48/filter/actuator/dt、critic52/actor49、clock/history/rawbit双marker、append-only4m及23/47、原LR/reward/masks/terminal128/batch65536/UTD1保持。全部历史失败、中止、partial75、不可评74—76、halfstd拒绝及软件失败保留。原93/冻结90完成勿重启；指定ESN仍缺，最终独立比较待。没有子agent。


## 来源、GPU与保存

实际主机 `rltest-1025--a6ed2ff39b3c-cn2p6rygmr`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮实际query/fetch/read main `64e2b60508a581a8706a97b89bd8d42fc2f203ab`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，应用仓库sii-research-sync。源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/host_recovery_census93_20261031_v1`；诊断 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/host_recovery_census93_20261031_v1`；原完整93归档仍是下一步科学父，未创建新checkpoint。恢复依赖及边界见RECOVERY_PLAN/COLD_RESTORE_REVIEW，全部冷恢复检查已完成。远端新增非RL归档v1/v2日志已读并快进保留；未运行非RL实验。

新主机独立GPU guard继续，科学结束不退出；本次保存采样窗口129样本/653.502秒，最低[0, 0, 0, 0]%、低于50[2, 2, 2, 2]、末值[78, 88, 80, 88]%。含synthetic guard，不等于科学训练吞吐或每瞬时保证；启动0%样本完整保留，不是系统重启服务。

SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS93_HOST_RECOVERY_20261031/SMALL_EVIDENCE.tar.gz`，23成员/86427字节，SHA256 `3730994366581d1cec2c90bbf5c5310f0195ed4d1a6fcd67cf743b4d0ad3ade4`，逐成员字节/AST核验。manifest `docs/evidence/RL_CENSUS93_HOST_RECOVERY_20261031/MANIFEST.json`，提交字节及实际push核验收据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_CENSUS93_HOST_RECOVERY_20261031/GIT_BYTES_REVIEW.json`、`PUBLICATION.json`。HDD配额满，仅原LATEST254字节原地更新回读，非HDD/arm1完整备份。主恢复入口 `docs/RL_RECOVERY75_PARTIAL_TO76_20261029.md`。
