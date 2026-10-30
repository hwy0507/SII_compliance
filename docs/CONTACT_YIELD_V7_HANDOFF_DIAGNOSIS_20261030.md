# v7 MLP 棍推 teacher 接管诊断

## 结论

75候选公平重训已经完成：40条训练轨迹、21,500帧；每个方法/seed 12候选，RNN/MLP 32k更新，六条纯teacher validation统一选模。九个模型锁定及九条全数据 actor replay 均通过。固定27开发闭环为 Task 27/27、Strict 25/27；ESN与RNN各9/9，MLP为7/9。MLP seed2026102802和2026102803的棍推失败仍超过冻结0.20 mm外部穿透限值，故开发资格未通过，final108不得派发。

## 接管探针

v1登记保留在`outputs/contact_yield_v7_mlp_rod_handoff_20261030_v1/`。第一次运行绑定`.venv-rl`，其MuJoCo 3.14.0不符合物理worker要求的3.11.0，在任何物理步之前失败。v2另立登记，但user-systemd的`AllowedCPUs=6`没有限制进程的`sched_getaffinity`；运行守卫因此在物理步之前拒绝。v2收据记录`physical_steps=0`，不重用该登记。

v3使用显式`.venv-sii-local-rl/bin/python`（MuJoCo 3.11.0）和`taskset -c 6`，四条完整回合串行完成，各500 actor steps、400,000个物理子步、`dt=5e-5`。同一systemd scope的MemoryMax为3 GiB、MemorySwapMax为0；每条保存的memory peak为756.04、894.46、919.73、1009.19 MiB，OOM/OOM-kill均为0。user cgroup未暴露`cpu.max`，因此不声称测得CPU quota；进程实际affinity为CPU 6。

| 模型seed | teacher接管时间 | 首次超过0.20 mm | 最大外部穿透 | 手接触 | yield / 越杆 / 回位确认 | 撤杆开始 |
|---|---:|---:|---:|---:|---|---:|
| 2026102802 | 4.48 s | 4.78055 s | 0.21599 mm | 5.13885 s | 6.12 / 7.84 / 9.40 s | 12.84 s |
| 2026102802 | 4.60 s | 4.78035 s | 0.22387 mm | 5.20185 s | 6.12 / 7.96 / 9.84 s | 12.84 s |
| 2026102803 | 4.48 s | 4.69895 s | 0.25499 mm | 5.43525 s | 6.28 / 8.88 / 11.60 s | 12.76 s |
| 2026102803 | 4.60 s | 4.69900 s | 0.24257 mm | 4.99070 s | 5.00 / 8.88 / 11.48 s | 12.76 s |

为区分“接管太晚”与“恢复动作本身不足”，同一模型/teacher又在4.20/4.32 s完成四条预登记训练场景对照：

| 模型seed | 接管时间 | 首次超过0.20 mm | 最大外部穿透 | yield / 越杆 / 回位确认 | 撤杆开始 |
|---|---:|---:|---:|---|---:|
| 2026102802 | 4.20 s | 4.78035 s | 0.23565 mm | 5.12 / 7.80 / 9.28 s | 12.84 s |
| 2026102802 | 4.32 s | 4.78010 s | 0.24574 mm | 5.12 / 8.16 / 10.32 s | 12.84 s |
| 2026102803 | 4.20 s | 4.69930 s | 0.24165 mm | 6.56 / 8.36 / 10.56 s | 12.76 s |
| 2026102803 | 4.32 s | 4.69910 s | 0.24904 mm | 5.00 / 8.44 / 10.96 s | 12.76 s |

四条同样为Task成功但Strict/安全资格失败，学生前缀零穿透、actor/filter replay误差0。比4.48/4.60 s接管更早仍未避免越限，且种子对应的首次越限时刻几乎不变；因此“单纯提前接管”不足以修复。

四条的学生前缀均未穿透；每条首次限值越界都发生在teacher后缀期间，且记录到的先接触棍子的是`fr3_link7`，手随后才接触。四条任务均完成，yield、越杆和持续回位顺序均在棍子撤回前达成；但`penetration_within_02mm=false`，因此安全资格/Strict失败，四条失败结果全部保留，不纳入训练集。

对照同一`rod_00`条件、同一MJB的原纯teacher采集：该轨迹通过qualification与棍推次序审计，峰值外部穿透为0.07140 mm，手首次接触4.73175 s，yield/越杆/回位确认4.84/7.16/7.32 s，撤杆12.80 s。因此证据不支持“原teacher在标称状态下一般不安全”。更准确的结论是：MLP前缀产生的轨迹状态与纯teacher状态逐渐分离，当前teacher闭环从这些状态继续运行时不能恢复足够安全裕度。seed03在4.60 s接管时，离线检查的九个robot collision geoms到棍最近间距约25.0 mm，而纯teacher同刻约40.3 mm；这提供状态偏离线索，不能单独解释后续`fr3_link7`碰撞，也不构成因果证明。

四条独立 actor replay 与公共filter replay最大误差均为0，执行器限制检查通过。对已保存的400,000行子步穿透值、torque、速度和dt作了独立数值复算；它复核已保存子步摘要，不是重新积分MuJoCo动力学。额外棍推几何审计从保存状态重建手部/finger collider的越杆和回位，使用40 ms几何采样并参考子步接触摘要，不能替代独立完整动力学重放或final测试。

同一杆推seed的失败MLP与纯teacher轨迹逐帧对齐后，最大关节位置差超过0.01 rad的最早时间为seed02的2.44 s、seed03的3.68 s，早于4.26–4.34 s扰动事件；4.48/4.60 s时最大关节位置差已达0.054–0.065 rad。请求动作在0.04 s即有差异，滤波twist差超过0.005 m/s的最早时间分别为0.12 s和2.24 s。这是轨迹关联诊断，不是因果分解；它说明状态/动作偏差在碰棍前已累积，不能只归因于teacher切换瞬间。

## 诊断与边界

当前证据表明：MLP状态前缀本身在接管时仍安全，但从4.20到4.60 s多种切换时刻都无法避免后续link7先撞棍；可见的附加路径进度逻辑要先观测到接触、再满足yield位移条件，且不提供碰撞几何输入。这是该学生状态下恢复能力不足的强线索；原纯teacher同条件通过说明不能把问题简化为teacher标称动作普遍错误。固定模型/同场景在接管时点改变后碰撞时刻几乎不变，提示还应检查MLP此前的动作和滤波器状态是否将构型推入不可恢复区。任务成功不能抵消穿透失败。

下一轮沿保存轨迹细化关节构型、速度、动作及滤波twist差，定位偏差来源并设计发展期修复；不再重复只改变teacher接管时点的试验。新teacher须先单独通过完整演示和恢复审计，才可重新采集统一训练数据并公平重训ESN、RNN、MLP。物理/MJB、0.20 mm门槛、canonical48、公共action filter、执行器限制和`dt=5e-5`均保持不变；这八条失败后缀不得作为训练标签。最终108未读取或派发。

代码与证据登记入口：

- v1失败：`code/mujoco_6d_vmc_benchmark/outputs/contact_yield_v7_mlp_rod_handoff_20261030_v1/`
- v2零物理步失败：`code/mujoco_6d_vmc_benchmark/outputs/contact_yield_v7_mlp_rod_handoff_20261030_v2/`
- v3完整证据：`code/mujoco_6d_vmc_benchmark/outputs/contact_yield_v7_mlp_rod_handoff_20261030_v3/`
- v4提前接管对照：`code/mujoco_6d_vmc_benchmark/outputs/contact_yield_v7_mlp_rod_handoff_20261030_v4/`
- v3 wrapper：`code/mujoco_6d_vmc_benchmark/experiments/contact_yield_v7_mlp_rod_handoff_20261030_v3.py`
- v4 wrapper：`code/mujoco_6d_vmc_benchmark/experiments/contact_yield_v7_mlp_rod_handoff_20261030_v4.py`

## 归档状态

v1–v4的完整原始回合、失败收据、对应wrapper、诊断报告及三份分析证据已归档到服务器目录：
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/contact_yield_v7_handoff_diagnosis_20261030_v1/`。
归档含226个文件、1,018,511,873字节；从incoming暂存区发布前，使用rsync checksum dry-run逐文件核验无差异。原始本机文件保留。首次GitHub fetch因TLS中断失败，改用HTTP/1.1后获取远端main `271ce4e4d4b58d4375f723a703e0af002e31739d`与baseline `f6e8f8c2711a93f0b5dfc88c608bd82647084d5d`；main的history88 RL进度已保留。v7结果与最新main通过普通merge提交`3218397a43c2a8817481469e1ad1ae5976b9935b`推送成功，并经`ls-remote`核验。对应源码提交及本诊断报告另有`source/<commit SHA>/`快照。
