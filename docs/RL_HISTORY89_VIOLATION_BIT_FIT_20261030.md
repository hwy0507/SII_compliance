# 完整89因果穿透违规位：匹配离线拟合结果

2026-10-30 UTC，Goal active。上一轮完整89/固定87终端跟踪发现阻抗critic3对刚超过穿透阈值的旧终端明显退化；本轮完成单独登记的有限配对拟合。全部三方法和五critic保留，正式89 checkpoint、actor/alpha/target与物理没有更新，拟合权重未保存推广。原冻结88与四卡GPU保持程序继续，未启动90/Direct34。

主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`；共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。运行/源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/history89_violation_bit_paired_fit_20261030_v1`，后续决定 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/history89_violation_bit_review_20261030_v1/SCIENTIFIC_DECISION.json`。前序完整证据见[完整89交接](RL_COMPLETE89_BOUNDARY_DIAGNOSIS_20261030.md)。

## 事前登记与实际匹配

PLAN SHA256 `94aad5f5d2054a31dfe5499544880f6a638f30196b578771aaeecaa5fe171a30`，源、完整89 checkpoint/registration、原87 sidecar、原完整审查及全部端点值均绑定。CPU11/GPU1，拟合阶段900秒预算，每方法每臂固定500步，总3000个clone Q优化器步；完整运行耗时131.778秒。先完成三方法0更新的实际恢复预检，再启动独立有限supervisor2839122、fit2839166与observer2839124，三者正常完成后不可重启。

两臂都将critic输入51→52，保留已学连续history列50，在观测索引51插入零权重列，动作权重列右移；全部旧Adam矩/step/group保持，新列矩0。对照新增输入恒0，实验新增输入`float(raw动作前累计外穿透>.0002)`。两臂同参数量、初始模型/optimizer逐位相同，三方法实际初始Q与原51模型/保存89预测误差全部0；完整learner及Python/NumPy/local/Torch/CUDA RNG前后保持。

原87固定全部终端I2605/A2604/V2604；违规位非零70/60/45行。原observations51/actions/rewards/masks及indices与完整89 replay逐位核验；因果raw sidecar和原连续feature精确对齐。只优化五critic之原mask终端MSE之和，fullbatch每步，全部为terminal故terminal128系数约掉；无bootstrap、actor/alpha/target更新。固定500终点为主，不选择中间最好步数。

| 方法 | 初始masked loss | 对照500步 | 违规位500步 | 违规位−对照 |
|---|---:|---:|---:|---:|
| impedance | 9.694299070 | 0.472334636 | 0.220097768 | -0.252236868 |
| admittance | 0.673561269 | 0.035577437 | 0.035281208 | -0.000296228 |
| vmc | 0.333048580 | 0.028822943 | 0.028384353 | -0.000438590 |

五critic最终masked SSE差（违规位−对照，负为更低）：

- impedance: `[1.6402960774721578, -0.6963044799340423, -0.3081800510517496, -528.8739071995915, -0.21022148197153]`。
- admittance: `[-0.22992000164595083, 0.26712085949111497, -0.38608007233051467, -0.13508102170817438, -0.14013154191707144]`。
- vmc: `[-0.12426301331652212, -0.3673975420824718, -0.18335565170491464, -0.05683170228439849, -0.1862835303436441]`。

保存预测由独立逐标量math.fsum重算全部初末SSE和masked loss，与训练日志在登记的浮点容差内一致；各501点曲线、全部行/all5保留。六栏图已实际查看，记录：三方法六栏全部查看。I违规位曲线约30步后逐渐低于对照，终点主要为critic3 SSE790→261，critic0略差；A/V两臂早期均有明显尖峰/振荡后下降，终点两曲线几乎重叠，微小改善不能扩大解释。Acritic1略差，V五critic均略改善。所有固定500终点和失败保留，仅已见终端拟合。

## 科学判断及后续

固定500步三方法总masked loss均较同容量零输入对照低：I约53.4%、A约0.83%、V约1.52%。I主要改善critic3，但Icritic0及Acritic1略退化，V五critic均小幅改善。两臂仅新增输入取值不同，支持在这些已见终端和该优化轨迹上显式违规位具有拟合收益，不能证明原在线退化的唯一原因或未来稳定性。A/V早期继承Adam后的大尖峰两臂均存在；本实验目标是fullbatch终端拟合，与原混合Bellman在线目标不同，不能直接外推loss轨迹。

据完整89退化和本轮匹配结果，选择进入因果违规位critic52的持久化/回放迁移准备；从准确完整89原权重/Adam新增零列，不使用本轮拟合权重。先重建并核验完整89全部旧行的动作前/后raw累计穿透及因果位，精确保留现有51维特征/动作/reward/masks与原history标记；再验证actor49隔离、clock投影、10critic/Adam扩展、序列化/原生更新/冻结恢复接口。接口与全量输入证据通过后，单独决定和登记有限在线90及新修订统计窗口；目前没有52维正式实现/迁移快照或90训练登记/派发。旧88—90失败窗口保持。

这是已在训练中使用过的原87终端上的离线拟合，不能证明在线reward改善、未见样本泛化、失败因果或整体收敛。没有改变物理MJB、Task/Strict/未知边缘门、canonical48 actor信息、filter、执行器、dt5e-5、正式LR或reward。原88—90 A/V相邻5%窗口失败仍成立；不存在全三轮bootstrap结果，不能以此诊断替代稳定性证据。

## 仍运行的评测与GPU

原冻结88 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runs/parameter88_history_frozen_full30_20261030_v1` 保存完成数 `{'impedance': 13, 'admittance': 14, 'vmc': 13}`；原evaluator2675653/2675660/2675662、collector2675665、postprocessor2713409与五个guard身份持续。观察140.168秒/15样本，诊断正常完成，冻结物理继续。原21600秒截止不延长，最终全90/全state不变/raw审计/82→88配对仍待，无重复派发。

原v7 supervisor97370与workers97399–97402继续，科研全部结束也保载，阈值50%、目标70%。本轮59采样min `[71, 76, 67, 76]`%、低于50次数 `[0, 0, 0, 0]`，末值 `[75, 77, 70, 79]`%；含合成负载，非科研吞吐或每瞬时保证；旧v7预热0及v6 31/33/44低谷保留。不是重启自启服务。

## 发布与完整目标

本轮query/fetch/read main8610fd8e864c10e573e5f1a3cd20e42494645219及baselinef6e8f8c2711a93f0b5dfc88c608bd82647084d5d。沿用sii-research-sync，无子agent。共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_HISTORY89_VIOLATION_BIT_FIT_20261030/SMALL_EVIDENCE.tar.gz`，43成员/2638470字节，SHA256 `06ab306ade7f80d5f7d3ce00820004aff94d71da6180320bd3a539183c5a51f3`；tar与AST通过，index/commit逐字核验及成功push/真实远端确认后PUBLICATION见包外收据。

HDD仅原位254字节LATEST，原大checkpoint/raw/sidecar继续共享SSD，非HDD/arm1全备份。Direct33数值接受但冻结30 Task/Strict0/0，28中断缺最终内存不变证明；指定ESN未提供、不替代其他主机模型。partial75、74—76不可判、79安全中止、全部失败窗口、halfstd拒绝及软件失败保留。完整reward稳定、loss健康、最终冻结及原ESN比较未证实，Goal active。

发布前远端main前进到511fbd5f5a671b203f8265636a8bcc143860a264，已fetch/read最新日志、AGENTS和MLP384专题报告：另一主机非RL容量拟合改善但rod00三seed Strict均失败，保留其原作业/失败及wide-loader修复。本机冻结runtime不受这些checkout修改影响；正常整合双方记录，不合并baseline。

