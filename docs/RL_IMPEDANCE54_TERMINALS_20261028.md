# 阻抗53→54终端误差分布与55固定样本跟踪（2026-10-28）

Goal active。上一轮完成55前5000保存核验与56仅恢复准备，属于实质进展。本轮保持原55训练，完成一次新的冻结终端诊断，定位高loss的样本组成；不修改训练设置，不以局部误差改善宣称整体收敛。上一交接：[55早期与56准备](RL_PARAMETER55_EARLY56_PREP_20261028.md)。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮fetch/read main `9a66ad7d4de3d0fdf4ae6cd4c43362181bbd71a7`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，无新科学约束变化。使用原B/env/bin/python，CPU0单线程；原训练/守护资源保持。

## 已完成的只读诊断

运行`B/runs/impedance53_54_terminal_concentration_20261028_v1`；源码`B/runtime/impedance53_54_terminal_concentration_20261028_v1`，原coordinator458394/start36143672已完成退出。按登记的完整53/54 checkpoint/health/review/transition哈希读取，全终端数1615/1645，4m/双容量marker检查通过。只恢复CPU前向agent权重，**没有恢复或执行优化器训练**；权重digest与前向RNG不变，原checkpoint哈希前后不变，0物理/优化/replay写入。

对每条终端样本求5个critic的贡献之和：128×mask×(Q−terminal_reward)²，分别除以各critic完整replay的sum(mask×(1+127×done))。这个量是冻结、全回放、仅终端部分的加权平方误差，排除了非终端TD项；随机小批次的分母和历史在线网络不同，不能视为日志loss的重放或历史尖峰的因果分解。terminal reward也不是整回合return。

原33/34只读脚本仅适配53/54、计数/CPU/4m校验及已观察abort条件的额外输出，差异留档。CPU终端MAE与已有health的float32误差顺序在原1e−9绝对容差内一致。全部预测/mask/reward/特征/分母/贡献保存NPZ，独立保存值脚本在原1e−14容差复算通过，图已查看。

| 量 | 完整53 | 完整54 |
|---|---:|---:|
| 全终端加权贡献 | 2.036595822 | 1.917637315 |
| 最大单条占比 | 21.6448% | 25.2391% |
| 最大5条占比 | 62.3434% | 75.1867% |
| 本轮新增30条占比 | 45.7120% | 63.3597% |
| 原同一1615条mask平方误差和 | 30929.124336 | 10864.678290 |

同一旧1615条输入/动作/reward/mask逐元素保持，平方误差和比值.351276621，即下降64.8723%。用旧53分母计算54旧样本贡献.715332763，用54分母为.702628164，分别报告，避免把回放增长当拟合改善。54新增30条贡献1.215009151，占63.3597%。全终端贡献比值.941589536（下降5.8410%），但实际在线末1000 loss从3.072625升至3.795605；两者统计对象不同，不能从本诊断断言非终端项或某一采样批是原因。

54最大单条是short0600，贡献.483994436/25.2391%；第二是short0100，.366283934/19.1008%；第三为53保留short0600，.291836513/15.2185%。这不是所有旧样本全面退化，也不能把新误差全部归因于abort。

## 提前终止记录的独立核对

已观察的long0000：53完整1375动作、无abort，回放index2219835，terminal reward−28.132873535，整回合return−32.877704965；54为593动作的global_penetration_exceeded_2mm，index2252691，terminal reward−38.772529602，整回合return−40.605097538。54该条贡献.222324099，占全部终端贡献11.5936%，不是最大贡献。

FOCUS_SAVED_REVIEW再次由NPZ逐critic标量公式复算，并与episodes的total_steps−1、条件、动作数、abort标签核对。不是独立物理重放或历史小批次采样因果证明。保留该真实失败及原30条件分母，不改gate/reward。

## 原55继续，固定1645条跟踪已登记

`B/runs/impedance55_terminal_anchor_followup_20261028_v1`；源码同名runtime，waiter570510/start36164183，固定7200秒。完整55尚不存在时固定54全部1645终端输入/动作/reward/mask及旧分母，包含而不只选abort那一条；将使用完整55权重对相同样本做一次CPU前向，另报告55新增30条。既有54预测直接复用，不重复推理。abort2252691只作为次要固定关注行，不据此筛选优化数据。

登记发生在55训练已运行之后，不冒充训练前预登记。waiter绑定原55 LAUNCH哈希、learners和archive monitor PID/ticks；等待完整archive/review/health及父learner退出，再依次执行推理和独立保存值审查。子进程记录PID/ticks，不因观察超时杀死/重复派发；无训练派发。原53–55稳定性窗口及冻结55全90评测不变。冻结55准备已绑定真实55 LAUNCH，PLAN SHA仍906bb31f23a3c63b49edc5e298407c284c81af173cd3d5f816581c4325fac986。

05:39 UTC原55 I/A/V约2279633/2280393/2281525steps，每路30sampler、尚0个完整条件。三learner4101991/4101994/4101996、归档4102000、完整loss45441、原窗口514418、冻结55仅恢复3641528、56仅恢复221126及新固定样本570510均核验live。Direct已满足经验数值标准，不重启34；参数整体仍未收敛。

GPUv4 supervisor1629438及四worker原PID/ticks保持，当前78/92/93/92%，含合成保活负载。用户要求全部科研工作结束后也继续，保持至STOP或关机；不是跨重启服务，也不承诺每个未来瞬时值。

## 保存与续接

小证据`docs/evidence/RL_IMPEDANCE54_TERMINALS_20261028`含全部NPZ、源/diff、登记、诊断与独立审查及图。大checkpoint/raw仍原共享SSD，不是HDD或arm1全备份。HDD LATEST仅指向本交接。

下一步等待原55完整结束，读取全周期loss/health、原53–55统计和固定1645样本结果；核实际冻结55恢复后进行既定90回合评测，56仅恢复通过仍须完整结果审查再决定训练。原reward平稳且loss无异常要求不变。

共享SSD小包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_IMPEDANCE54_TERMINALS_20261028_053933/SMALL_EVIDENCE.tar.gz`，849871字节/24来源成员，SHA256 `d1c396d43aab6fed6abbea19a5e88cf5e7246e9d43c0ea6d7404c6f9b1a91f95`，全部成员逐字节核验通过。
