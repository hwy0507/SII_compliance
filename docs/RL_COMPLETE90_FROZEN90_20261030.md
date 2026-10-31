# 完整90已审；冻结90全90实际运行

2026-10-30 UTC，Goal active。原三路有限90训练及archive/full review/固定87终端跟踪正常结束，不重启。新冻结90已完成最终登记、三份实际完整checkpoint check-only恢复、实际有限派发和90秒启动检查；最终全90/raw/88→90配对仍待。未收敛，无91或Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。实际query/fetch/read main `d8f15b893483506853ecbcb87f352d315a3e2fdf`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关协议变化；使用sii-research-sync，无子agent。前序[冻结88全部完成](RL_FROZEN88_COMPLETE_20261030.md)。本轮源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_completion_20261030_v1`，训练 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle90_20261030_v1`，完整审查 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle90_review_20261030_v1`，完整checkpoint `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter_violation_cycle90_archive_20261030_v1/<method>/cycle_00090.pt`。

| 方法 | 新transition/update | Task /30 | Strict /30 | mean reward | checkpoint SHA256 |
|---|---:|---:|---:|---:|---|
| impedance | 40752 | 17 | 16 | -4.293254231594 | `787dd97c18faea183731e632c843b4716ceed8f26621b9fe189b0c1b8352e657` |
| admittance | 41250 | 14 | 14 | -8.519996007453 | `884f97f79aa9d90c65a44ec97c2ff2a1380a61315fd27ed6c31afdd0f68c0bd2` |
| vmc | 41250 | 17 | 17 | -2.861059666986 | `b57bec92b59b1985e303f001321da91a47bc6b4df2b0c8ac5a7a443f16ae5511` |

全部旧回放精确保留、新current/next52和raw→mixed动作精确、全部新reward复算误差0，learner/optimizer有限。保持critic/replay52、actor49/canonical48、clock49/history50/rawbit51、已学history与Adam/双marker、4m append及23/47标记、terminal128/batch65536/UTD1/原LR/reward/masks及物理/MJB/gates/filter/执行器/dt5e−5；没有离线拟合权重晋升。

阻抗`active_long_train_0000`在877动作/35.0800000006s安全中止，原因`global_penetration_exceeded_2mm`；原30分母保留，29条完整55s、1条中止，不补跑。全局峰穿透97.9125891mm，最深接触为office_v5_corner_top与target_object_geom；外部穿透仅0.04698594mm，最后current和terminal外部违规bit仍为0。上一轮同条件Task/Strict均成功、无abort。新增bit不是完整Task/Strict或全局安全状态，不能用它覆盖这类失败。`ABORT_REVIEW.json`绑定保存rollout/terminal/journal/transition/hash；非独立物理重跑或因果归因，不改物理门槛。

完整loss（首1000→末1000均值，全部原始点保存）：

- impedance: critic 1.990383955→1.507037844，max 34.852695465；actor 21.225090832→21.786679888。
- admittance: critic 1.367703821→1.116086297，max 9.057353973；actor -8.314841652→-8.217304933。
- vmc: critic 1.013427361→0.764621418，max 12.107591629；actor -11.802638280→-11.546806437。

末段critic均值改善但I后段尖峰重现、三路actor上移；不能把有限值或单轮下降写成loss健康收敛。health、完整loss、训练逐条件变化、固定终端四图均已实际查看并绑定hash。

impedance：89→90 mean变化-1.932852616；Task新增[]、丢失['active_long_train_0000']；Strict新增[]、丢失['active_long_train_0000']。

admittance：89→90 mean变化+3.469811383；Task新增['active_short_train_0300', 'active_long_train_0200', 'active_long_train_0900']、丢失['active_long_train_0300', 'active_long_train_0500']；Strict新增['active_short_train_0300', 'active_short_train_0600', 'active_long_train_0200', 'active_long_train_0900']、丢失['active_long_train_0300', 'active_long_train_0500']。

vmc：89→90 mean变化+1.740470104；Task新增[]、丢失[]；Strict新增['active_short_train_0600']、丢失[]。

全部90条件及reward分项保留，保存回读/独立端点和核验通过；跨history51→violation52与额外在线训练，不做同修订稳定性或bit单独因果归因。首解释脚本在JSON path string调用Path.open时失败，尚未写结果、0新物理/更新；原脚本/PLAN/log保留，v2仅转换Path和绑定新源，重新执行通过。

固定原87全部终端impedance：总masked SSE89→90 20325.764156→3362.887087（-83.455%）；逐critic差[692.9297526302817, 54.47162519117319, -342.9930824199482, -14705.857985472305, -2661.4273782155815]。

固定原87全部终端admittance：总masked SSE89→90 1413.062950→1550.062353（+9.695%）；逐critic差[-100.93586190860879, -103.99891262279198, -307.4501242385777, 643.8248937328244, 5.5594087587196555]。

固定原87全部终端vmc：总masked SSE89→90 698.039432→1722.701171（+146.791%）；逐critic差[256.0923393504054, 275.46279684392357, 352.528615440875, 252.23054797029545, -111.65256072818738]。

全部I2605/A2604/V2604旧终端/all5/原masks保留，完整learner/replay/RNG不变；I c0/1、A c3/4、V c0..3退化均保留。All-row SSE下降也不能替代in-bag拟合、策略安全或整体收敛。原88—90失败窗口不改，90—92统计方案当前只有完整90，不跑缺91/92的窗口，不自动训练91/92。

新冻结90 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_full30_20261030_v1`：沿原预登记完整90、30原条件×三方法、seed2026102638、最多123750动作/99m子步、0更新。实际三份完整父恢复全learner/replay/digest/checkpoint精确，已绑定最终registration和实际图检；显式LAUNCH_AUTHORIZATION后才派发。启动观察90.019s/10样本通过，原evaluator/collector/postprocessor身份及物理CPU亲和性/动作进度保持。当前进度 `{'impedance': {'seed': 2026102638, 'actions': 200, 'completed_conditions': 0, 'condition': 'passive_corner_train_0000', 'physics_pid': 300921, 'time': 1793395856.1979475}, 'admittance': {'seed': 2026102638, 'actions': 300, 'completed_conditions': 0, 'condition': 'passive_corner_train_0000', 'physics_pid': 301393, 'time': 1793395886.3694854}, 'vmc': {'seed': 2026102638, 'actions': 200, 'completed_conditions': 0, 'condition': 'passive_corner_train_0000', 'physics_pid': 300922, 'time': 1793395852.89332}}`。最终全90结果、final fullstate invariance、raw审计与88→90配对尚待，原collector21600s截止不扩展。

派发源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_frozen_dispatch_20261030_v1`；后处理 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_frozen_postprocess_20261030_v1`，raw审计 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter90_violation_frozen_saved_audit_20261030_v1`；三者源/hash及真实缺完整90拒绝证据均保存。比较原88和新90的物理、reward、条件、action seed逐项一致，显式允许violation52修订；所有成功/失败与无接触NA保留。不得重复派发已结束的原冻结88或训练90。

GPU原guard97370及97399–97402持续，科研结束后也保载。本轮315采样/1600.3s，min[77, 67, 67, 65]%、低于50[0, 0, 0, 0]，末值[81, 69, 72, 71]%；含合成负载、非科研吞吐或每瞬时保证。旧v7 warmup0/v6低谷仍保留，非重启服务。

Direct原数值阶段已接受；冻结33全30 Task/Strict0/0、原28最终内存证明缺失仍保留，不新增成功要求、不为占用启动34。指定ESN缺失不替换，最终比较待。partial75、74—76不可判、79安全abort、90新abort、所有旧失败窗口/半std拒绝/软件失败保持。下一步依据完整90和固定终端分歧、阻抗安全退化，准备有记录的有限后续决定及全state恢复验证，不能用预登记统计自动派发91；原冻结90继续。

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_COMPLETE90_FROZEN90_20261030/SMALL_EVIDENCE.tar.gz`，144成员/7487569字节/SHA256 `d26d47a2b2c25a3cfc035c072211627df1c31fa42fc724e46b946fba56fe2341`，tar成员/AST已核验；index/commit逐字核验及正常push/实际远端确认另存包外PUBLICATION。大checkpoint/raw仍原共享SSD，HDD仅原位254字节指针，非HDD/arm1全备份。
