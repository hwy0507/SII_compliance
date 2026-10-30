# 完整89违规位训练恢复、原生更新与消费端接入预检

2026-10-30 UTC，Goal active。上一轮[全回放保存和记录轨迹检查](RL_HISTORY89_VIOLATION_CONSUMERS_20261030.md)属于progress。本轮完成三份准确完整89元数据迁移、生成训练器实际恢复AST执行、真实batch65536原生clone更新重复/恢复，以及完整冻结评测器check-only和原完整health诊断接入。6次辅助clone原生update已丢弃，0正式更新/0新物理步；不是新训练周期、不是收敛认证。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_violation_pipeline_20261030_v1`；登记与结果 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_violation_pipeline_preflight_20261030_v1`；迁移完整快照 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_violation_pipeline_preflight_20261030_v1/archive/<method>/cycle_00089.pt`。所有大快照仅在SSD，未进入Git。

## 完整89边界与生成训练器

每方法派生registration完整保留原科学89 registration，只增加 `violation_critic_amendment`，明确 `migration_preparation_only`/first_cycle90/online_launch false。绑定原89 checkpoint、原87 history marker与上一轮通过的52维full snapshot。迁移checkpoint完整保留原cycles/steps/seed/partial75排除/恢复链/原科学元数据；只替换为精确已核验的52维learner/replay、指向派生registration SHA并添加bit amendment。独立逆还原这两个元数据改变后，所有原89非learner/replay字段digest完全一致；learner/replay与上一轮full snapshot全部精确。实际写盘重载通过。

从各方法真正运行过的89 `trainer_registered.py` 生成准备训练器，仅增加准备阶段启动拒绝、在EXECUTION/checkpoint保存bit amendment，并将简易plateau的修订起点从88改为90；反向删除这些明确变化后源码逐字等于原89。原interval消费、current/next/terminal映射、reward、更新、batch/UTD、sampler和物理代码保持。

从生成训练器AST抽取原样的learner构造至resume校验部分实际执行，包含原torch.load、learner/replay恢复、steps/cycles/start_cycle和initial-state调用；三份真实完整状态均精确恢复，next_cycle为90。该抽取不含sampler/物理步骤，**没有执行完整训练主循环**。准备入口显式拒绝直接online90；不得把AST恢复检查冒充真实新采样startup。

共69个实际拒绝覆盖reward/conditions/batch/UTD/history/capacity变更、scope/更新/物理授权、错误原父周期/边界/步数/seed/controller、缺任一双marker和错51维回放。原始父checkpoint与上一轮full snapshot hash保持。

## 真实原生更新和目标引用

事前PLAN绑定源码/输入，CPU11/cuda:1，整条链1800秒上限。迁移及原生检查实际348.895秒。每方法准确GPU cache取65536，保留原已学history权重、Adam、原masks和terminal128、原LR/reward。一次原生更新后保存全learner状态，再序列化/恢复初始learner、用同一batch重复一次；全部指标及全状态digest精确相同，新增bit列获得非零梯度，原生参数/梯度及指标finite守卫通过。额外验证foreach target参数引用与明确Polyak计算一致，随后恢复全部learner和replay RNG/内容，所有clone变化不推广。

| 方法 | 两次重复更新的Q loss | 迁移快照SHA256 | 拒绝数 |
|---|---:|---|---:|
| impedance | 1.350538611 | `4c811cbdad7f47e1f936a6fb27e5585447359185a48b98938ce44453dca26da2` | 23 |
| admittance | 1.133174181 | `245fac508df7c5ddd32577a1857fb0a373f4c97dd50fc9876708342a56a455bb` | 23 |
| vmc | 0.836339474 | `a3308967b0792385c789f00529f406d3d6a6d341bc5f2c51cfc1c4afbcc23450` | 23 |

这些是单批接口检查值，不是新训练loss曲线、长期健康或reward改善证据。保留上一轮v1 dense CUDA归约失败与v2 split修复；不使用离线拟合权重。

## 实际冻结入口与完整健康诊断

版本化 `evaluate_violation_preparation.py` 以三份真实迁移89运行原完整 evaluator 的check-only路径，核验runtime/全部source/30条件/模型及历史23/47容量链，完整52 replay/learner恢复、原生与外部RNG三动作gate及全state不变通过。其非check-only入口在任何物理派发前拒绝；没有EVALUATION.json或新回合。原运行中的冻结88源码和作业不改。

`health_violation_preparation.py` 完整执行原89 health诊断，只改明确的派生registration/父execution绑定及52维构造，保留只加载网络、不恢复optimizer/host RNG的原方式。其原有unprojected固定minimum-pair TD诊断保持，仍不等同投影Bellman目标或A/V mean estimator。三份原89完整terminal reward、online Q、in/out mask误差及sampled Q/TD保存字段与原89诊断逐项精确一致；全部真实7993终端，0optimizer更新。实际六栏诊断PNG已查看，图来自原89训练日志，不包含本轮6次clone更新；长标题右端沿用原图裁切，数字与曲线可读。保存JSON中的终端/TD残差仍明显，非收敛通过。

## 继续工作与GPU

原冻结88完成数 `{'impedance': 22, 'admittance': 22, 'vmc': 21}`，原evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409身份保持；最终全90/内存不变/raw审计/82→88配对待，原21600秒截止不扩展。整个本轮有界监督575.079秒/115次身份观察，全部辅助子进程正常结束。

GPU guard97370/97399–97402持续，科学任务全部完成也继续。阈值50%、目标70%，本轮137样本min `[69, 75, 65, 76]`%、低于50 `[0, 0, 0, 0]`，末值 `[71, 78, 73, 78]`%；含合成负载，非科研吞吐/每瞬时保证，历史低谷保留，非开机服务。

下一步：结合完整89退化、原88—90 A/V失败与匹配离线bit证据，单独登记有限90的科学决定和真正可派发driver，保持迁移amendment作为历史来源，核验原父/全部合同与原生更新；同时准备90 startup/full archive/review/health/loss消费者及新修订内稳定性登记，再执行真实新采样。当前没有90科学决定或物理启动；本轮只能证明迁移和消费端接入。原88—90失败窗口不得被抹掉，也不能跨不同critic修订池化宣称收敛。

原30×55s、每路41250新transition、append-only4m、terminal128、batch65536/UTD1、LR/reward/masks、physics/MJB/Task/Strict/actor/filter/执行器/dt5e-5保持。Direct33数值接受但冻结30条件Task/Strict0/0，Direct28缺最终内存证明继续披露；指定ESN缺失、不以另一主机模型替换。partial75、不可判74–76、79安全中止、半std拒绝及所有历史失败保留，Goal active。

## 保存与发布

本轮真实query/fetch/read main46772a18及baselinef6e8f8c，保持另一主机非RL工作，使用仓库sii-research-sync，无子agent。共享SSD归档 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY89_VIOLATION_PIPELINE_20261030/SMALL_EVIDENCE.tar.gz`，83成员/616795字节/SHA256 `ea381917d6ee050dfea04ed274e7c741405a72655110bcc5f523e6ae7ab12a01`；tar逐成员与Python AST核验通过。Git index/commit字节核验、正常push与真实ls-remote见包外PUBLICATION。HDD仅254字节LATEST原位更新，大checkpoint/raw仍SSD，非HDD/arm1全备份。

发布检查补充：实际执行的frozen_helpers.py沿用原源EOF空行；原件按登记hash保留。首次whitespace检查对此报错，记录在归档目录WHITESPACE_REVIEW；排除此准确原件及原始diff后复查，其余文件通过。
