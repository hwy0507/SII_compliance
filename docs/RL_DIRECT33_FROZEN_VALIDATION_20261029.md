# 最新Direct33冻结验证：登记、准确恢复与实际启动

2026-10-29T08:27:14.086334+00:00，Goal active。上轮[完整77与78续训](RL_RECOVERY77_COMPLETE78_RUNNING_20261029.md)已完成并继续；本轮补齐最新Direct33的冻结验证入口并实际启动全30条件。**当前冻结33完成2/30回合，完整物理审查尚未完成，不预告成功或完整通过。** 参数78原三路继续，steps {'impedance': 3210972, 'admittance': 3212243, 'vmc': 3214623}。

共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，执行主机 `rltest-1025--a6ed2ff39b3c-nvfdwjhzzw`。SERL推理用`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/serl_env/bin/python`，物理及根审查用`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`，沿用原锁定upstream。源码基线 `a010582c201c60fcec75bf005c334b27405ba7b2`；本轮实际fetch/read main b1deda6593c6b4bc76a76b89e30b5a6fc4998178、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d，均未变，非RL新增保留，无子agent。

## 选择和范围

原Direct数值阶段决定保留完整33并禁止额外34，但旧冻结只覆盖29，不能用29认证33。本轮固定最新33 SHA783eaa7f7b03226915539e41cce313a5faeb4d49a15ae25626bb9762a9f47849（1369290steps）；登记明确这是训练结束后的最新checkpoint选择，非新的前瞻收敛窗口或未见测试。

`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/serl_take33_frozen_full30_20261029_v1/PLAN.json` SHA `5d9566ce3c2449db5a9fe8652be5f0c9b3ebef76c9e564dda479d2ab32a380f3` 在任何新33恢复/物理前固定，沿用冻结29全部30条件/顺序、独立动作seed2026102626、independent noise、30×55秒、最多41250动作/33000000子步，0优化/0replay写入。两个交错15条件分片；CPU0推理、CPU1/2物理、CPU3审查、GPU0。先查CPU0–3无其他固定Python任务，原参数78仍CPU13–51/GPU1–3，guard52–54保持。单训练seed和单动作seed/训练条件结果，不替代指定ESN、最终完整比较或held-out泛化。

## 源码与准确恢复

独立runtime `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/serl_take33_frozen_full30_20261029_v1`。原冻结29全部703文件逐字复制并核hash，与当前33恢复依赖逐hash一致；新增evaluator只把允许的物理周期29改33，完整物理loop和外部随机动作函数保持原字节/AST。root reviewer改33元数据、完整26..33历史和CPU3，并显式检查总动作≤41250；原物理/filter/torque三审计不变。错误周期29请求在创建输出/读checkpoint前拒绝，0物理。

真实check-only原PID2567326已完成，完整learner/optimizer/RNG、2m replay及历史摘要精确，原930隔离行及raw/derived字段全部保留、不能采样、不补造完整25。同外部seed动作一致、不同seed动作不同、时间采样规则通过，状态未改变。完整33恢复digest：learner ff4b521adea259a4d3bf248c89e846d1612ceb5ceffd42e3895c6afcb0100b57；replay e74ccbea8fb92d2f79c6c1d06d9669727b1cee29a8813689084f154ccc19c4f7；history2436e4bd667690fef00bd3c43fcedd4eef0a09764b51f66ffd597ab6dc62dfa3。

通过独立PRELAUNCH后，两原evaluator PID2686848/2686852启动，root reviewer2686856；全部启动身份记录在LAUNCH/REVIEW_LAUNCH。实际两分片FULL_STATE_RESTORE与check-only逐字段完全一致，外部RNG gate、checkpoint/登记/模型/公共动作桥和CPU亲和核验通过。**该启动检查不冒充完整30回合的物理/最终状态不变审查。**

初始只读观察器错误地将`executed_evaluator.py.txt`函数hash与audit入口模块hash比较而失败。原源码/log/FAILURE保留，改为对照ADAPTER的函数hash和冻结29同条件执行函数，并单独核入口模块hash，两边均通过。`OBSERVER_FIX_REVIEW.json`与diff记录证据；没有修改科学源码或重启科学进程。修正后的观察器连续5样本/120.004秒，18个原身份全部保持，参数步号{'impedance': 3208730, 'admittance': 3210147, 'vmc': 3212247}→{'impedance': 3210335, 'admittance': 3211438, 'vmc': 3213927}；观察器自然结束，评测/训练继续。

## 完整评测后续

原root reviewer等待两分片最终POLICY_UNCHANGED，再对全部30逐原始子步、滤波和力矩记录核验，校验原learner/optimizer/RNG/replay/history未变、MJB/种子/预算及全部失败分母。固定21600秒观察上限；超时不是科学终止，不自动重启。

`COMPARISON_PLAN.json`在完整33评测前登记29→33描述性配对，保留全部30条件Task/Strict、完整时长、机器违规、各关节峰矩、实际人体接触时长与舒适时长/接触分母、完成时刻/阶段/abort；无接触为NA。比较等待器PID2754155，须完整33审查通过后运行，只读保存JSON/CSV与独立计数/均值/差值核验。不会从这部分比较选最终SPT的Tref，不冒充指定ESN或多独立训练seed比较。

参数78原全loss/标签/2304终端锚点后续、完整归档/health和原前瞻76–78统计均保持；本轮不改变训练LR/reward/masks/physics/gates、batch65536/UTD1/terminal128或4m markers。参数reward稳定与loss健康仍未证明；原Goal完整范围保留。

## GPU与保存

自上次最终保存起guard 171个5秒样本，四卡最低[76, 70, 69, 67]%，低于50次数[0, 0, 0, 0]，最后利用率[80, 95, 71, 94]%。含合成保载，非纯科研吞吐；保活在科学全部完成后仍继续。历史容器停机与v6预热空闲保留，非重启自启服务。

本轮SSD小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_DIRECT33_FROZEN_VALIDATION_20261029/SMALL_EVIDENCE.tar.gz`，86成员/249770字节，SHA `145626a48341d6eef26339345babd5784a959c34a0129e54d10130d21ee14476`，逐成员及Python AST核验。[收据](RL_DIRECT33_FROZEN_VALIDATION_20261029_SAVE.json)。新入口源码也复制至仓库tools，冻结runtime/hash仍为执行依据；703原依赖manifest与共享SSD原件保留，大checkpoint/raw/回放仍SSD，非HDD或arm1全备份。GitHub发布以最终实际push收据为准；既有HTTPS认证缺失。

下一步观察原冻结33到完整30及审计/配对，查看真实结果后报告；持续原参数78，收齐78完整loss/health/终端/labels及76–78统计再作科学判断。不要重复启动33冻结，不追加Direct34，不因观察过期重启科学。

保存补充：首次打包在复制新源码到仓库时发现根目录尚无tools目录，FileNotFoundError原记录和save.py已保留。创建目录后从已保存的同一快照继续打包，未重采科学结果、未重启训练/评测；见SAVE_INITIAL_FAILURE.json、finish_save.py与SAVE_RECOVERY_REVIEW.json。
