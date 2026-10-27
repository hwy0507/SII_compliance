# Direct26冻结全30前瞻登记与容量恢复入口验证

2026-10-27 UTC。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl，实际集群SSD执行；仓库B/repository/SII_compliance。原Direct25和参数41继续。Goal active，训练整体健康收敛尚未证明，无子agent。

## 固定评估问题和预算

在26尚未启动、完整26父不存在时，固定选择原Direct24–26奖励稳定性窗口的终点26。评估其冻结随机策略在原全部30训练条件上的表现，并与已完成冻结16作描述性比较；不选择最高reward检查点/有利条件或种子，不重跑16。

- run：B/runs/serl_cycle26_frozen_full30_20261027_v1；runtime同名位于B/runtime。
- PLAN SHA256：72882a42d0a32a3414363e8f8163f1d7169bb92f10ec8254ffe59e3dd65bf896。
- 原30条件及顺序，外部动作seed2026102626、独立逐动作随机噪声；与冻结16一致，原物理fixture seed不改。
- 30×55秒，最多41250动作/33000000物理子步；两固定交错分片各15条，GPU0推理/CPU52，物理CPU53和54。
- 0优化/正式replay写入，不导入诊断权重；原physics/MJB/gate/filter/执行器/dt5e-5/canonical48/native actor映射保持。
- 这是单训练seed、单动作seed、全训练条件冻结验证，非held-out/多seed泛化、最终ESN/SPT对比或收敛证明。16→26期间包含1m→2m容量变化，不能作无干预因果比较。

原准备waiter3528782存活，10800秒等待完整26原FINISHED/REVIEW，然后绑定准确26归档与训练登记，执行一次600秒上限的真实26恢复check-only。准备不自动派发物理评估或训练。实际26恢复仍待。

物理launcher还要求PRELAUNCH科学审查，以及参数冻结41的原三evaluator和根review已结束且review通过，以避免CPU53/54物理重叠。评估后的root review最长21600秒，超时不自动重启或扩预算。正式训练CPU0–51保持。

## 新容量入口的实际验证

旧冻结16入口只恢复完整learner；新入口增加当前2m容量replay的严格恢复与不可变性核验，使用原已验证capacity driver/helper，不迁移、不采样或写replay。

新 `evaluate_serl_capacity_frozen_20261027.py` 检查准确cycle/登记、历史entry23/容量marker和完整source manifest；恢复完整learner（网络/Adam/RNG）及raw+derived replay/RNG，独立记录实际checkpoint `cycles` 历史摘要。原外部动作种子gate保持；评估结束再次检查全部learner/replay/history不变。check-only返回前不进入物理loop。物理评估入口只接受预定26；已完整24仅用于新入口恢复验证。

B/runs/serl26_frozen_capacity_validation_20261027_v1/restore24_v4实际通过，原3422452已退出：

- 准确完整24 SHA112eda44c8cda14c5f3b4b3ce934dab7882fa254ac516e1ca4e1b5e24fe852e4。
- replay size1018290、capacity2000000，历史容量入口23；完整replay digest41e050124e45f5f47b9c3956ba777ed6881ac9413960acdb07a11a027b8c5ae9。
- 完整learner摘要8f3b58df0921a11233eff3b9856e3a9a1927cc707b00cfb16626e5069232e047，精确等于原state；历史摘要80707c379d08ebc959116bca358a6cb3e91903e64bd3fd82e666d89ab4d76768。
- 外部相同key动作精确、不同seed改变动作、时间采样与learner/RNG不变gate通过。0optimizer/physics/replay writes；未重跑24回合。

保留前期环境失败：v1隐藏CUDA但JAX仍要求CUDA后端；v2显式CPU后端又触发原SERL适配器“exactly one visible GPU”限制；v3错误暴露4卡，若仍运行则停止该辅助组；v4仅可见物理GPU0、native CUDA后端通过。所有失败/更正/日志和原源码保留，原四正式未停止。另将候选初版对不存在history字段的摘要更正为真实cycles字段；实际成功v4使用更正后的代码。没有修改适配器以放宽原GPU要求。

## 审查与代码一致性

新root reviewer固定26/全30/同seed，核验两分片相同learner/replay/history摘要、200万容量、entry23及准确checkpoint；沿用已完成16的原始子步、filter、torque审查，PID身份绑定实际start ticks。原物理helper不变。实际物理26审查尚未执行。

源码AST/CLI --help、真实24完整恢复、完整26引用/预算与固定条件/seed检查通过。CURRENT25_HELPER_REVIEW确认18个相关共同文件与实际正式25逐字节一致，包括source adapter、多步/gather、capacity与物理审计helper。所有冻结16继承文件逐原manifest验证，新的完整source_hashes写入PLAN。capacity helper SHA c39abba32814bc713c58945eb3405f33118e1881b76fb60622c87a010132dd27；validated driver SHA 0ca9b613fb0e2e0f360769ca3ec9ae9f1674ef7b295f4de25986a3ba054b9e81，不改正式优化或采样逻辑。

## 训练衔接准备

原Direct25 learner2350595及review2350599、参数41 I2369246/A2369249/V2369250及review2369308持续推进；26/42仅恢复准备、原Direct24–26/参数39–41稳定性窗口、冻结41准备1833369、导纳固定1224跟踪41原2937574保持。

新参数41→42衔接observer3568920，B/runs/parameter41_42_transition_20261027_v1，CPU54每2秒/1800秒，只读原三PID身份/退出和42 LAUNCH；无自动训练/GPU负载，实际衔接尚待。保存值review_parameter41_saved_results_20261027.py已按40→41/39→40上下文同时替换、AST通过；待完整41原review/health后执行，不提前写passed。原纯25/41GPU窗口不重采；个别瞬时0%后恢复且步数持续更新，不据单样本重启。

## 证据与同步

小证据docs/evidence/RL_SERL26_FROZEN_REGISTRATION_20261027：41文件220162字节逐大小/hash复制，含候选失败/更正/成功恢复、PLAN/静态审查与源码、仅准备登记及衔接observer初始快照；大snapshot留SSD。新HANDOFF/归档SSD，既有HDD LATEST回读；不称HDD/arm1全量备份。

开工真实查询/fetch/read main7d69ac57974888d32f98d208f0097e7ec8f64426、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，远端97/108仍为另一主机非RL，未变。常规commit/push及后续实际41/42结果另记。下一优先完整41科学审查、原39–41统计、导纳跟踪和冻结41恢复，再接续有限训练；不得将本静态登记当实际26评估完成。
