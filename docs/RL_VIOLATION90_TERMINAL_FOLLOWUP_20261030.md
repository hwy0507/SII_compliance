# 原90继续；固定87终端跟踪90已登记

2026-10-30 UTC，Goal active。上一轮[已学90冻结接口与首5000 loss](RL_VIOLATION90_FROZEN_READY_20261030.md)为progress。本轮在原90训练继续期间准备固定旧终端的完整90后续诊断，不重复Direct训练/评测，不增加90预算、不自动91或Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。已实际query/fetch/read main `4b19b5f9f797fecad4bc2a27d9b4b8fab9349aa7`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`，无新相关科学协议变化。采用仓库sii-research-sync，无子agent。

## 固定终端跟踪

来源 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_terminal_followup_20261030_v1`，运行/方案 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/violation90_fixed87_terminal_followup_20261030_v1`。原87全部终端集合不变：I2605、A2604、V2604，共7813条；每条保留全部5 critic和原masks，不挑选后续表现较好的样本。原87/88/89预测、indices、observations51、actions、rewards、masks直接取已审保存NPZ。

新52维终端输入为原51特征附加当前raw preaction严格穿透bit。原完整89 raw sidecar/bit SHA逐一绑定90的violation amendment；原终端历史特征逐位相同，bit逐条与raw >0.0002m独立复算一致。终端bit0/1数量 `{'impedance': {'0': 2535, '1': 70}, 'admittance': {'0': 2544, '1': 60}, 'vmc': {'0': 2559, '1': 45}}`。原87/88/89全部masked SSE/MSE、all-row SSE、mask分母保存值独立标量复算与已有报告精确一致；0新神经forward/0物理/0更新。真实缺完整90审查前置条件拒绝通过，不把partial90当complete。

`compare90.py`在完整90 REVIEW/FINISHED/health/loss通过且绑定同一checkpoint后才运行；使用已验证的52维violation恢复接口，检查实际90完整边界、双marker、原continuation、全旧终端indices/52特征/actions/rewards/masks精确。每方法所有5 critic仅做一次完整旧终端预测，检查完整learner/replay/RNG/hash不变，保存87/88/89/90结果、独立标量统计及六栏图。全部改善和退化保留，不引入零终端误差收敛门槛。

唯一等待器PID `2283008`/start `576631374` 已启动，并实时核验原archive1096452身份。截止沿用原90 launch+14400s（Unix `1793405432.8649602`），没有扩展原训练/归档预算；诊断自身最多1800s。此等待器不启动训练/新物理，完整90当前仍缺、尚未产生新90终端预测。生成图后仍需实际查看。

这是固定已见终端的保留/拟合诊断。90包含新在线训练和51→52修订，不能把差异归因为bit的单独因果收益、泛化、策略性能或整体收敛。它也不覆盖88—90新增终端；完整90的原health仍负责全部回放终端。原88—90失败窗口保留，新90—92统计方案不授权91/92训练。

## Direct范围复核

重新读取原DIRECT_STAGE_DECISION及其7项hash绑定证据，并检查完整冻结33的实际保存审查。Direct原数值阶段已经接受，原27—29窗口及33平稳loss支持此有限范围；不能因Task/Strict0/0另加新的收敛条件或为了GPU占用重新启动34。

最新冻结33仍全30、Task/Strict0/0、机器违规0，原28已保存动作精确重现、新2最终全state不变；原28最终内存证明丢失仍明确保留，额外877中断动作不计入完整分母。没有重跑已有物理、训练或bootstrap，指定ESN与最终比较仍缺，不替换他主机模型。新 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation90_terminal_followup_20261030_v1/DIRECT_SCOPE_REVIEW.json`仅核验现有证据和范围，不覆盖原决定。

## 当前科学与GPU

原90三路训练及90sampler、原冻结88、collector/postprocessor和guard均保持原身份。新180.067秒/19样本/105身份观察通过，三路steps增加。保存总steps `{'impedance': 3706926, 'admittance': 3709226, 'vmc': 3710237}`；原冻结88完成数 `{'impedance': 28, 'admittance': 27, 'vmc': 27}`。完整90与原冻结88最终全90/raw/82→88配对仍待，原21600s冻结截止不延长。

原科学协议保持：30×55s/最多41250新transition、4m append/23与47marker、terminal128、batch65536/UTD1/原LR/reward/masks、actor49/canonical48、clock49/history50/bit51、物理/MJB/gates/filter/执行器限制/dt5e-5。既有partial75、74—76不可判、79安全abort、全部旧失败窗口、半std拒绝及软件失败保留。首5000 loss的I尖峰和actor漂移不能被此准备工作解释为解决。

GPU原v7 supervisor97370/worker97399–97402继续，科学全部结束后仍按用户要求保载，不创建STOP。本轮65采样最低[78, 66, 64, 70]%，低于50样本[0, 0, 0, 0]，末值[82, 72, 73, 71]%；含合成负载，不作科学吞吐或每瞬时保证。历史低谷保留，guard不是重启服务。

## 保存与接续

小证据 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION90_TERMINAL_FOLLOWUP_20261030/SMALL_EVIDENCE.tar.gz`，40成员/90482字节/SHA256 `d075b260520e063ab4e8371bcd27cf438b78151cc5be0e67cd4d2789914053a7`，全部tar成员/AST核验。Git index/commit逐字核验、正常push与真实远端确认后写包外PUBLICATION。大产物仍原共享SSD，HDD只原位更新已有254字节指针，非HDD/arm1全备份。

下一步保持原90、原冻结88与唯一固定87终端等待器；完整结果到齐后收全loss/health/任务标签、终端跟踪和实际图，再决定有限下一步。未有完整90前不发布其性能或reward稳定结论。
