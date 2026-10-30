# 第91轮固定前5000更新审查；原训练及冻结90继续

2026-10-30 UTC，Goal active。前序[91实际启动](RL_VIOLATION91_ONLINE_20261030.md)。本轮只读取原作业的已保存记录，0新物理步/0新optimizer update/无新阶段派发。原91及完整review/health/loss归档消费者、原冻结90评测/collector/postprocessor、GPU守护继续。未收敛，无自动92/Direct34。

实际主机 `rltest-1025--a6ed2ff39b3c-t55ahnz53q`，共享SSD `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl`，分析源码 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/runtime/violation91_prefix_20261030_v1`，解释器 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/env/bin/python`。按sii-research-sync实际query/fetch/read main `e0842d5fe91c0370061de3408bb003a9b32d758b` 与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；第一次查询TLS失败，重试成功，无相关科学协议变化。无子agent。

在读取91 loss数值前固定每方法最初5000个更新，沿用90同一窗口和算术；三路按准确完整90的实际steps绑定，分别从3729701、3732501、3733501开始。I90安全中止后的实际40752步保持，未假定其完整41250。原optimizer前缀逐字复制且读取后再次核验；全部step连续/update_index0、指标有限且q非负、NPZ逐值相同、math.fsum独立保存均值核验。已实际查看六栏图并记录hash。

| 方法 | critic首1000均值 | critic末1000均值 | critic最大值 | actor首末1000均值 |
|---|---:|---:|---:|---:|
| impedance | 1.764565473 | 1.638681201 | 25.045833588 | 21.815747517 → 21.970616438 |
| admittance | 1.145342035 | 1.161649187 | 3.233340502 | -8.220071655 → -8.217094838 |
| vmc | 0.764069312 | 0.798559343 | 21.450780869 | -11.543272543 → -11.545052965 |

I反复出现约13的尖峰且最大25.05，actor均值继续上移；A critic末段略升，actor近-8.22；V孤立21.45尖峰及4000更新附近波动保留，actor近-11.544。全部有限仅排除本窗口NaN/Inf，不证明loss健康。当前只有部分周期，没有完整91 reward，不能据此前缀宣布reward平稳或整轮收敛。前序90完整loss独立存于REVIEW中的complete90_last1000；同52修订不等于已完成90—92统计窗口。维持原有限91预算和算法，等完整结果再判断后续，不依据早期波动擅改目标/阈值。

原进程实际连续观察180.075秒、19样本、104身份均保持，三路steps增长。保存时steps `{'impedance': 3737955, 'admittance': 3740715, 'vmc': 3741559}`，冻结90完成 `{'impedance': 2, 'admittance': 3, 'vmc': 2}`/各30。最终完整91/health/loss、冻结90全90 raw/88→90配对/最终全state不变仍待。原物理/MJB/Task/Strict/filter/执行器/dt5e−5、actor49/canonical48、critic52/历史/Adam/RNG、回放4m/terminal128/batch65536/UTD1/原LR及失败记录不变。

保留完整90 I long0000全局穿透安全中止、外部bit0未覆盖该失败，固定旧终端A/V退化及旧失败窗口；partial75、74—76不可判、79安全中止、半std拒绝和全部软件失败不删除。Direct原数值验收与冻结33全30 Task/Strict0/0、原28最终内存证明缺失保持；指定ESN仍缺，不替用其他模型。

GPU守护原97370及97399–97402继续，科研结束仍保载；本轮41采样，最低[69, 67, 67, 71]%、低于50次数[0, 0, 0, 0]、末值[73, 92, 93, 89]%。含合成负载，非科研吞吐或每瞬时保证，非重启自启服务。

证据包 `/inspire/ssd/project/long-range-embodied-collaborative-intelligence/ky26288/sii_rl/repository/RL_VIOLATION91_PREFIX_20261030/SMALL_EVIDENCE.tar.gz`，29成员，1392388字节，SHA256 `5322b2e337d99f6705a047e9df5c86a32a2893fd739f64c8e9f2fba1700e2edf`；逐tar成员/源码AST通过。Git index/commit逐字核验及正常push/实际远端确认写包外PUBLICATION。大checkpoint/raw仍共享SSD，HDD仅254字节指针，不是HDD/arm1全备份。
