# 参数56启动校验与未来56–58统计窗口准备（2026-10-28）

Goal active。上一轮完成阻抗53/54终端误差诊断及55固定1645条跟踪，属于实质进展。本轮继续原55训练，准备尚未运行的56启动路径及下一段连续统计窗口；不宣称参数收敛，不改变原reward平稳且loss无异常要求。[前一科学诊断与完整路径](RL_IMPEDANCE54_TERMINALS_20261028.md)。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮fetch/read main `6116208123ca861210d7259b2b3a49c1971f89cd`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`及日志，无新科学约束变化。

## 下一段固定统计窗口

`B/runs/parameter_capacity56_58_reward_stability_20261028_v1`。56/57/58均未启动时登记连续、互不重叠的下一窗口[56,57,58]，不依据未来结果选起止轮次；原53–55窗口及其所有结果仍须完成并保留。原相邻及首尾均值相对变化≤5%、近零保护1、5000次按类别配对bootstrap、全部30条件及真实episode长度不变。bootstrap seed提前固定2026102855，与训练随机状态无关；公式片段与原代码经周期名称替换后逐字一致。

新增anchor_protocol55固定当前三路55注册文件SHA，审计将比较第一轮56与55的科学配置，再继续比较57/58；覆盖conditions/runtime/reference/physics/action/reward/critic clock/batch/UTD/numerical amendments/terminal/projection/pair/capacity/actor LR等原字段及完整dependency hashes。4m与entry23/47历史marker保持；没有更改训练配置的授权。失败/提前结束回合保持30条件分母，optimizer长度必须等于真实episode steps总和。

最终waiter788599/start36203076，固定14400秒观察预算，等待三完整review/health再执行统计，不自动启动训练或停止训练；超时应保留原失败，不以新窗口覆盖。首次源码差异审查发现周期数字替换意外改变诊断CPU54→57，已在任何实际审计和未来训练前停止仅该waiter759408，保留initial源码/plan/LAUNCH/diff，恢复CPU54并更新source SHA后启动当前waiter。统计窗口、seed、公式、阈值和样本分母未变，原55及53–55进程未动。

## 56启动脚本仅准备

`B/runtime/prepare_parameter56_20261028_v1/launch_parameter56.py`及`startup56.py`已从实际验证过的55版本适配，周期与补零路径逆向映射精确回原源码，AST/hash/diff检查通过。启动器要求DECISION56明确parent55/new56、完整parent review/health/loss/paired/check-only证据SHA、图已检查且不宣称收敛，准确恢复退出0/0/0，才派发单个56、归档monitor和实际startup检查。缺DECISION56的真实负向调用已拒绝，未生成56运行目录或任何训练进程。

已有56仅恢复waiter221126/start36101608继续等待完整55。当前实际56恢复未发生、DECISION56不存在、56训练未启动；本准备不代替完整55结果的科学审查。准确父必须55完整归档，不回退54；全部replay/optimizer/RNG/history与原4m/entry23/47保留。若后续进入56，仍需读取实际startup/REVIEW，不能仅凭check-only称启动正确。

## 当前运行与下一步

05:46 UTC原55 I/A/V约2284695/2285535/2286660steps，本轮新增20547/20785/20910，全部仍各30sampler、0个完整条件。三原learner4101991/4101994/4101996（start均36044802）、归档4102000、完整loss45441、原53–55窗口514418、冻结55仅恢复3641528、固定1645条跟踪570510与56仅恢复221126均核PID/ticks live。原GPUv4 supervisor1629438和workers1629439–1629442身份保持，79/94/95/96%含合成负载；科学工作结束后仍保活至STOP/关机，不是跨重启服务或永久瞬时保证。Direct不追加34。

下一步继续等原55完整结果，读原53–55统计、完整loss/health与固定样本诊断；核实际冻结55恢复后执行既定90回合评测，并据完整结果决定是否有限56。下一56–58窗口的存在不是训练授权或收敛证明。

## 保存

小证据`docs/evidence/RL_PARAMETER56_WINDOW_PREP_20261028`含初始CPU纠正记录、最终plan/source/diff/hash、56负向启动验证及状态。原大checkpoint/replay/raw仍共享SSD，非HDD或arm1全备份；HDD LATEST仅保存入口。

共享SSD包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER56_WINDOW_PREP_20261028_054602/SMALL_EVIDENCE.tar.gz`，15321字节、21来源成员，SHA256 `f7d470c0b36e3f32f63bc99de087c5c97590e1540c3cb4abb9d41ed6333aaea1`，逐成员内容核验通过。
