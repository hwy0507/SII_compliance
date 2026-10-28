# 参数55早期loss与56仅恢复准备（2026-10-28）

Goal active。上一轮已完成54完整归档、真实abort诊断、准确55恢复与实际startup审查，属于实质进展。本轮继续同一55原进程，不重启Direct或参数训练。完整54/55启动依据见[前一交接](RL_PARAMETER54_COMPLETE_20261028.md)，Direct数值标准已满足但Task0，不追加34。

B=`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`；主机`rltest-1025--a6ed2ff39b3c-hsje5ateny`。本轮fetch并读取main `3583a6c7298af85776ae0e6a777b521e09624d12`、baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`最新日志，工作区开始干净，无新科学约束变化。使用原冻结环境`B/env/bin/python`，环境版本见上一轮ENVIRONMENT：Python3.11.17/Torch2.8.0/NumPy2.2.6/MuJoCo3.11.0。

## 55前5000保存审查

`B/runs/parameter55_first5000_20261028_v1`：沿用54相同的前5000长度，**在55启动后登记的描述性审查，不是启动前预登记或新收敛门槛**。原53–55全周期统计保持。原审查173021已完成；完整前缀逐字节对照原optimizer文件、连续step、哈希、有限值、均值/峰值用独立Python statistics复算，图已查看。

| 方法 | critic首1000 | critic末1000 | 前5000均值 | 最大 | actor首→末1000 |
|---|---:|---:|---:|---:|---|
| 阻抗 | 3.449113 | 3.722024 | 3.544238 | 32.742645 | 28.915869→29.109037 |
| 导纳 | 1.911840 | 1.568304 | 1.700426 | 45.506172 | −10.138074→−10.201059 |
| VMC | 1.013950 | .951607 | .935060 | 13.191060 | −13.916992→−14.033767 |

全部critic/actor有限，但I保持较高水平，A有45.506峰值，不能宣称loss无异常。I前5000末段仍略升；A在此段内回落，V较54末段减小。

另保存54末5000→55首5000的描述性尾部分布：I均值3.734628→3.544238、中位数2.015368→2.076403、p99 23.812466→19.433113；A均值1.350033→1.700426、中位数1.290069→1.426691、p99 2.085855→11.230866；V均值1.125203→.935060、中位数.801202→.792209、p99 12.082230→5.013010。p95/p99采用nearest-rank，top1%为最大50项占总loss和的比例，精确值及来源hash见SAVED_REVIEW。不以短前缀替代全周期、不作独立seed统计或回放样本因果归因。

## 56仅恢复准备

目录`B/runtime/prepare_parameter56_20261028_v1`，当前waiter **221126/start36101608**，固定14400秒。绑定原55三learner PID/ticks及archive monitor和LAUNCH哈希；必须完整55 archive/review/health完成且原learner退出后才执行准确55→56 check-only。当前没有56运行目录，实际56恢复和训练均未发生；无自动56训练许可，仍须完整55结果审查。

准备脚本来自已验证55准备，最终只改变父/新cycle和对应路径，准确父checkpoint必须`cycle_00055.pt`。逆向映射回原源码逐字一致、AST及hash检查通过，waiter原字节不变。保留两次静态准备纠正记录：首次过宽逆向数字替换误触sha256导致断言失败，未启动waiter；随后diff目检发现补零checkpoint文件名未递增，在任何56实际恢复前按PID/ticks停止仅准备waiter195764，保留源码/注册/收据，修正后启动当前221126。不是因观察超时重启，没有停止或改动55训练。

## 当前运行与保存

05:29 UTC原55 I/A/V约2271993/2272663/2273747steps，三路各30sampler、0个完整条件；完整结果尚待。三learner4101991/4101994/4101996（start均36044802）、归档4102000（36044803）、完整55loss45441（36069767）、原53–55统计514418（35382586）、冻结55仅恢复3641528（35932846）全部核验live。冻结55仍按先前90回合登记，没有开始物理评测。

GPUv4原supervisor1629438（35566457）及workers1629439–1629442保持。即时77/90/92/95%，包含合成保活负载；正式训练或评测结束后仍继续至STOP或关机，不是跨重启服务，也不保证所有未来瞬时采样。不要为了占卡重启已满足数值标准的Direct。

下一步保持原55，读取完整loss/health及53–55统计；随后核真实冻结55恢复再进行既定90回合评测。56仅恢复通过也不代替续训决定。整体Goal未完成，不改变reward平稳和loss无异常的原要求。

小证据`docs/evidence/RL_PARAMETER55_EARLY56_PREP_20261028`；原完整三路前5000 JSONL保留在共享SSD包，Git保存源码/图/报告/来源manifest。大checkpoint/raw仍原共享SSD，不是HDD/arm1全备份。HDD LATEST仅保存入口。

小包`/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_PARAMETER55_EARLY56_PREP_20261028_052942/SMALL_EVIDENCE.tar.gz`，926813字节、29来源成员，SHA256 `9bc7275cff8f6b69033012c415eeec8bf1433ad662604fc6ab2451777162d79f`，逐成员内容核验通过。
