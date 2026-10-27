# 阻抗33→34终端误差集中度与固定1045跟踪登记

2026-10-27 UTC。B=/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl。Goal active，无子agent。原四正式参数35/Direct22继续，本轮没有重启或更改训练设置；上轮交接见RL_PARAMETER35_SERL22_20261027.md。

本次问题是阻抗34末1000在线q_loss由33的2.048515升至2.889142，但terminal MAE反而从.822872降至.780232。原只读诊断1995279已经完成：对准确完整33/34全部1015/1045终端×5critic做CPU前向，0优化、0新物理、0replay写入。恢复CPU agent权重、核验前向前后权重和torch RNG不变；完整checkpoint/source/runtime/helper/input hashes前后不变。浮点减法顺序复现原健康报告的all/in-bag MAE后，用float64计算平方误差贡献；此诊断不加载优化器，不声称重演历史GPU批次。

|指标|完整33|完整34|
|---|---:|---:|
|全部终端对冻结全replay加权损失的贡献|.518371005|.471848843|
|最高一行所占比例|44.0883%|45.4811%|
|最高五行所占比例|73.6947%|84.5569%|
|本轮新增30终端所占比例|1.3122%|50.9098%|
|相同1015旧终端masked SSE|4953.164747|2280.246785|

全部终端population贡献下降8.9747%；固定旧1015终端masked SSE下降53.9638%。用33原分母计算34旧行贡献为.238467934，使用34新分母为.231631639，均比33的.518371005低，因此不是仅靠replay分母增长稀释。旧终端的观测/动作、reward、mask和索引逐值相同。

34新增30终端贡献.240217205，其中short0600 replay index1432256贡献.214602043，占全部终端45.4811%。其reward−28.351505，五critic Q为−29.869562/−26.397690/−21.010187/25.750395/16.969294，mask为1/1/1/0/1；critic3的正值未参与该行训练损失，不能把它当作in-bag异常项。原33最大行index1306210到34的贡献下降，但另有旧行1306248贡献仍较大；完整top20和所有值已保存，不仅展示有利样本。

独立保存算术审查重新计算全行贡献、排名、旧行SSE与两种分母结果，源/输入/NPZ hash通过；terminal_concentration.png已目视核对。结论局限：这里只覆盖冻结检查点终端项，排除非终端TD项；随机minibatch分母期望与训练过程中变化的参数也不同。不能把上述比例当在线q_loss因果份额，也不能由此宣称全部loss正常或已经收敛。当前证据支持保留原训练，并继续既定35完整健康/33–35稳定性审计。

新固定1045跟踪35等待2103843：登记时35已经训练中但完整35 checkpoint/health尚不可用，明确不是35训练前预登记。固定全部34终端的观测、动作、标签、mask，以及本次已知最大新行1432256；仅完整35 FINISHED/REVIEW后CPU52前向一次，预期1075终端、其中30新增。等待7200秒、执行600秒，0优化/物理/正式replay写入，复用34已保存预测，不重跑34，不自动训练或参数提升。三个新工具和waiter AST/--help/准确cycle/count/minimum target守卫通过；实际35跟踪与保存值复核仍待。

准确输入父SHA：33为668793677d54efbf38cf9dc0d8583c4ef06cc62969d8312c51337b3dfeb72e62；34为149618c8b54b3945e392df0f4f414e20c2ddf47422efa957b8d9a438f71b2d93。诊断B/runs/impedance33_34_terminal_concentration_20261027_v1；新跟踪B/runs/impedance35_terminal_anchor_followup_20261027_v1。提交源码位于code/mujoco_6d_vmc_benchmark/tools，实际执行副本及hash见REGISTRATION/PLAN。小证据docs/evidence/RL_IMPEDANCE34_TERMINAL_20261027。

远端main dbb1d76ed79177067c48ed49ff9f67f023c704aa、baseline f6e8f8c2711a93f0b5dfc88c608bd82647084d5d本轮重新查询/fetch/read未变。原Github认证缺失/指定ESN缺失不重复索取，当前不是最终比较。大原始数据仍SSD，本轮小证据归档/HDD交接另记，不是HDD/arm1全备份。

本轮科学提交5ddf4d73f2cef52449164a2631af64df0aed59a1仅本地，GitHub push仍HTTPS用户名认证失败。SSD本轮完整小证据包/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_IMPEDANCE34_TERMINAL_20261027_021748/FULL_SMALL_EVIDENCE.tar.gz，21成员逐大小/hash核验、1046873字节，SHA256 93f57b6f7a190fb5cb27b310bbf8d5bd5f82b32a0a001ce2e87fde1e1c8f8b19。HDD新目录因Errno122配额失败；历史档案保留，现有LATEST_RL_HANDOFF.md已成功更新并核验，指向SSD交接/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_IMPEDANCE34_TERMINAL_20261027_021748/HANDOFF.md。本轮新HANDOFF/完整收据仅SSD，不称HDD或arm1备份。原四正式35/22、冻结32、36/23恢复准备、两稳定性及新固定1045跟踪等待2103843继续，Goal active。
