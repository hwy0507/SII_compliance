# 冻结88全90完成；原90训练继续

2026-10-30 UTC，Goal active。主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。本轮实际query/fetch/read main `dd5481407b72d6cf8ef0942f0d0f4eb0a76384f3` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，未发现新相关协议变化。采用仓库sii-research-sync，无子agent。

原冻结88三方法各30个原训练条件、固定动作seed2026102638已全部完成，共123750动作/99000000物理子步。原evaluator、collector、postprocessor正常结束，均未重启；全部final full learner/replay状态不变，初末digest一致、0优化器更新。完整评测的成功标签与实现审计通过分开陈述。

| 方法 | Task82→88（/30） | Strict82→88（/30） | 88平均reward | 配对平均变化 | 88机器违规数 |
|---|---:|---:|---:|---:|---:|
| impedance | 18 → 18 | 17 → 17 | -2.373435766 | 0.007398742 | 1 |
| admittance | 14 → 16 | 14 → 15 | -6.869404988 | 1.614865006 | 1 |
| vmc | 17 → 17 | 17 → 17 | -2.871570445 | -0.065277316 | 0 |

两项机器违规均为`active_short_train_0600`：I峰穿透0.2434523239mm、A0.2053474959mm，超过原0.20mm。I总Strict未变，但short0100获成功、short0600失成功；A新增short0900和long0500双成功，同时short0600丢Strict。V成功集合不变、mean reward略降。各方法最初10条passive条件均失败，低穿透不能替代任务完成。

完整逐条件结果、获失成功、失败条件、力矩/实际接触时间及按接触分母汇总见 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/frozen88_completion_review_20261030_v1/REVIEW.json`。原始90回合reward、物理dt/子步、穿透、逐关节峰力矩、机器违规、实际接触舒适比例均经独立raw审计和保存回读核验；no-contact保持NA。原审计 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_saved_audit_20261030_v1`，所有82→88配对 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1/comparison82_88`，完整原评测 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1`。实际查看六栏结果图并另存PLOT_INSPECTION，不把文件存在当目视核验。

该比较仍是原训练集合/单外部动作seed；82→88包含额外在线训练与history critic修订，不能单独归因修订、声称保留集泛化或证明reward稳定。所有失败保留，非最终SPT/指定ESN比较。Direct原数值验收保持，冻结33全30 Task/Strict0/0、原28最终内存证明缺失仍保留；不启动Direct34。指定ESN仍缺，不替换其他主机模型。

原有限90三路PID1096445/1096447/1096449与archive1096452、固定87终端等待器2283008仍保持原身份。保存总steps `{'impedance': 3720281, 'admittance': 3722579, 'vmc': 3723505}`，各30sampler继续。完整90/health/loss/固定终端90预测仍待，尚未收敛；不自动91/92。90–92统计预登记不代表训练授权或完成窗口；旧失败窗口、partial75、74–76不可判、79安全abort、半std拒绝及软件失败保持。第90轮首5000中I critic尖峰/actor漂移的限制不被本次冻结88结果消除。

物理/MJB/Task/Strict/filter/执行器/dt5e−5、canonical48/actor49、30×55s/41250新transition、4m append和23/47 markers、terminal128/batch65536/UTD1/原LR/reward/masks保持。训练90当前critic/replay52、clock49/history50/rawbit51和已学history/Adam/双marker保持；无离线拟合权重晋升。

GPU原guard97370及97399–97402继续，科研完成后也保载；本轮176个样本/892.4秒，最低[75, 68, 67, 66]%，低于50计数[0, 0, 0, 0]，末值[80, 92, 97, 95]%。含合成负载，非科研吞吐，不保证每个瞬时；旧v7 warmup0/v6低谷保留。没有创建STOP，guard非重启服务。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_FROZEN88_COMPLETE_20261030/SMALL_EVIDENCE.tar.gz`，164成员/369459字节/SHA256 `e709de07846bf99dff4ab7dba4da1790b5bdfdf09fada4264d2ec126dac65c85`；逐tar成员与Python AST已核验，Git index/commit逐字核验和正常push/实际远端确认记录在包外PUBLICATION。大checkpoint/raw仍共享SSD；HDD仅原位更新254字节指针，非HDD/arm1全备份。

接续：原90完整结束后收齐archive/review/health/loss及固定87终端跟踪90图，实际查看再作有限下一步科学决定；完整90冻结方案已准备，但仍需完整门槛、实际check-only、最终登记及独立派发。本轮完成88原评测后处理，不重复物理回合。
