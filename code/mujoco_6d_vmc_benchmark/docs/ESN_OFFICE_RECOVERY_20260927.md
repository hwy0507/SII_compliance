# Office-v5 ESN recovery — 2026-09-27

**最新完成状态**：R34六条件任务6/6、严格综合3/6。全部结果与原始数据已归档，
独立动作/储备池重放与子步指标复算通过。两例接触不足和一例强球撞越限仍
保留为失败；未运行保留布局，当前无运行中队列。见
[R34六条件最终报告](ESN_OFFICE_R34_FINAL_20260927.md)。以下为之前轮次记录。

**后续补充**：使用对所有方法相同、经收敛检查的首撞精细积分后，冻结 R33
已通过原办公室以及提前/加长推杆两种压力条件的完整任务、安全和覆盖门槛。
新增五条 ESN 回合任务 4/5、严格综合 3/5；强球撞仍越限，第9秒推杆仍有
卸载失败。详见 [首撞与压力边界报告](ESN_FIRST_IMPACT_BOUNDARY_20260927.md)。
下文三场景 50us 的原始结果保留，不能用后续数字覆盖它们。

## 本轮可汇报结论

同一个 R33 ESN 已在三个预先声明的复杂办公室**开发场景**完成真实接触
抓取、抬升、搬运、桌面稳定放置、松爪和撤离：任务 **3/3**。这包括原始
有人手推压的 office-v5，未用 guarded-rod 场景替代。三例杯子均保持稳定，
放置时均有真实桌面支撑，最终物体距目标 XY 约 1.6–1.7 mm。

**严格综合验收仍为 0/3，不是安全门槛和盲测均已通过。** 原始与较强球撞
场景的 50 us 原始结果超过 0.2 mm，三例推杆接触覆盖均不足预定 0.4 s，
其中较强扰动场景未发生推杆接触。所有失败门槛保留，不因为绕开推杆而
把 coverage 改成通过。三个保留场景尚未运行。

| R33 场景 | 设置变化 | 任务 | 目标 RMSE (mm) | 峰值力矩 (Nm) | 峰值速度 (m/s) | 最大外部穿透 (mm, 50 us) |
|---|---|---:|---:|---:|---:|---:|
| 原始办公室 | 球 1.70 m/s；人 .20 m；杆 .235 m | 成功 | 152.523 | 39.808 | .14589 | .200284 |
| 障碍 +36 mm | 球 1.45 m/s；人 .18 m；杆 .225 m | 成功 | 145.576 | 38.132 | .11185 | .153605 |
| 障碍 −36 mm | 球 1.85 m/s；人 .22 m；杆 .24 m | 成功 | 135.643 | 42.336 | .11249 | .215214 |

RMSE 是对当前阶段目标计算的全物理子步位置误差；搬运目标切换会产生
约 .42 m 的瞬时目标误差。它不是完成后的落点误差，也不能把卡在早期阶段
的小 RMSE 与完成整条任务的 RMSE 直接排名。

同原始办公室的零残差 WBC 和六维 VMC 教师也已完成任务。因此，本轮不能
支持“其他方法均失败、只有 ESN 成功”的论文结论。它支持的是：此前失败的
ESN，经可解释修正后完成三种复杂开发条件的任务；安全与保留验证仍待完成。

原始场景回放：
`outputs/esn_office_recovery_20260927/r33_original_replay/replay.gif` / `.mp4`。
动画直接读取存档 MJB 和状态，不重新仿真；5.04 s 人手接触与 55 s 最终帧
已目视核查。所有 30 个已发现回合（含短诊断、失败、物理探针）在
`outputs/esn_office_recovery_20260927/all_results.md` / `.json` 中汇总。

This campaign targets the actual person/hand + ball + separate rod + cup +
pillar + thick-corner office pick/place task. Guarded-rod R30 success is not
office success. Real-robot readiness is not established.

## Frozen scope

`configs/esn_office_development_protocol_20260927.json` declares three
development layouts and three withheld layouts. The withheld layouts have
not been run. Complete episodes use the historical common 55 s horizon;
the 21 s historical failure remains archived. All office task gates and the
external penetration <=0.2 mm gate remain unchanged. A safe failed task is
still a failure; contact coverage, cup stability and rebound are retained.

## Evaluator corrections

- Fixed target-geometry variable shadowing by the world-side rod command.
  External contact now excludes the payload body, consistent with canonical
  metrics. Global penetration is still reported with its legacy gate.
- Added explicit abort reason, finite-state checks, execution completeness,
  canonical48 assembly test, stage readiness/error diagnostics, qvel/ctrl/
  mocap, saved MJB/XML, and physical-substep metrics on scratch kinematics.
- Added a pulse-off diagnostic without changing checkpoint weights.
- Verified office and canonical primitive runners use the same direct-ESN
  twist action, 0.32 m/s yield limit, WBC gains and proprio48 order; the office
  task gate is different from the guarded-rod approach-plane gate and remains
  unchanged. Office nominal speed is fixed at 0.06 m/s.

The first diagnostic snapshot is archived locally under
`outputs/esn_office_recovery_20260927/source_snapshot/` and on Spark under
`/home/arm1/vmc_mujoco_runtime/esn_office_recovery_20260927/`.
Its transmitted tar SHA256 is
`4957a95fbe378fb12878d119e403e8ddf201d8d5084cf0c540259500a4394d29`.
The separate full-task teacher snapshot tar SHA256 is
`ea5f49f42826e36bfb51f819ad64d6edb445c6eabbb970f9725025d9989dee6b`.
No ongoing or prior campaign source was overwritten.

## Completed 6.2 s paired diagnosis

Same seed, physical layout, period, initial state and gates; only actor and
driven-event selection change. `settle` retains physical objects and gravity.

| Actor | Events | Final stage | Lift (m) | Max external penetration (mm) | RMSE (mm) |
|---|---|---|---:|---:|---:|
| R30 | settle | approach | 0 | 0.032775 | 191.20 |
| R30 pulse off | settle | approach | 0 | 0.028213 | 130.14 |
| zero residual | settle | carry | 0.124 | 0 | 191.49 |
| R30 | ball | approach | 0 | 0.177699 | 201.02 |
| R30 pulse off | ball | approach | 0 | 0.186982 | 138.37 |
| zero residual | ball | carry | 0.124 | 0.200284 | 175.11 |
| R30 | all | approach | 0 | 0.177699 | 201.02 |
| R30 pulse off | all | approach | 0 | 0.186982 | 138.37 |
| zero residual | all | lift | 0.121 | 0.200284 | 62.58 |

These short episodes are diagnostic, not complete-task success trials. RMSE
against the current stage target cannot be ranked alone when controllers
reach different stages. All nine failed full-task completion within 6.2 s.

The claim that a ball strike alone caused R30 failure is disproved as a
necessary-cause explanation: R30 and pulse-off R30 fail approach even without
a driven event, whereas zero residual progresses. The R30 base readout itself
produces persistent free-space drift at the office posture. The pulse worsens
drift but disabling it does not repair task execution.

Ball contact in the zero-residual run occurs at 0.05925–0.05960 s; first
post-contact 25 Hz actor observation is at 0.08 s. Its peak penetration is
0.200284 mm and force 2181.35 N. This is an impulsive event between actor
updates, so subsequent recovery cannot undo the recorded peak. Do not relax
the gate or advertise the large impulse as safe human interaction. A physical
timestep convergence check is needed before interpreting the 0.284 micrometre
excess, and may not be selected just to obtain a passing number.

Raw nine-case results and traces are under
`outputs/esn_office_recovery_20260927/diagnostics/`. Historical local smoke is
preserved under `historical_smoke/` in the same campaign directory.

## R31 experimental change

A fresh 128-unit multiscale ESN is distilled from causal six-dimensional VMC
on synthetic wrench histories, using 80 training and 16 independent validation
episodes. It reads only the six encoder-estimated wrench fields of canonical48;
no clock, task stage, geometry, fixture or contact truth enters it. A bias-free
reservoir/readout gives exactly zero action at zero wrench and zero history,
independent of robot posture. Signed and absolute reservoir features permit
both signed yield and nonnegative slowdown. Reservoir time constants are
0.04, 0.16, 0.64 and 2.56 s. This is an experimental replacement, not a renamed
R30 success or evidence of ESN superiority.

Checkpoint SHA256:
`0d70152a72c3e22d4973eae66b85138a89f272284b8e9cdf72864f017ae0a7e8`.
Training histories, labels, predictions and metadata are preserved under
`outputs/esn_office_recovery_20260927/r31_vmc_memory/`.
Synthetic held-out per-channel action RMSE is
`[0.06868, 0.10479, 0.10127, 0.03536, 0.03482, 0.05360, 0.03889]`;
this is not a closed-loop success score. Seven targeted audit/ESN tests pass.

## Completed R31–R33 development sequence

- R31 linear readout: task 0/3. Original stopped at load transfer; shifted-plus
  stopped at lift; shifted-minus at carry. All are preserved.
- R32 nonlinear bias-free readout plus causal relabelling of exposed histories:
  task 1/3, the shifted-plus layout. Other cases reached load transfer but did
  not release. One training attempt hit its 5 GiB virtual-address cap before
  saving a model; it was preserved, duplicate arrays were released, and retry
  used an 8 GiB address cap / one CPU thread. There was no system OOM.
- R33 adds six independent reservoir blocks and masked nonlinear readouts,
  exploiting the diagonal VMC teacher's axis symmetry. This prevents a force
  history on one axis from generating a learned residual on another. Total
  reservoir remains 128 units, with causal leak time constants spanning
  .02–1 s in each block. Six signed residuals are learned; slowdown is their
  bounded norm divided by sqrt(6), as in the teacher. No teacher dynamics run
  inside the deployed ESN. Exact zero equilibrium and zero cross-axis leakage
  were checked on the trained checkpoint. Task 3/3; strict 0/3.

R33 used all R31 failed development histories as well as the original VMC and
zero-residual traces for causal teacher relabelling. Thus these three layouts
are **development performance**, not zero-shot or blind generalization.
No test layout, stage, object identity, event clock or contact truth enters
the actor. All inference uses canonical48 encoder-wrench fields 39:45 only.
This deliberate input restriction retains the public action7 contract.

R33 checkpoint SHA256:
`ba5575e4dd48c5773396ebf7b59b9911d3f0320b8a908dc88260b6331061835d`.
R33 source/config/checkpoint tar SHA256:
`57ed12ba8b92bd2a472f5c9cdf1905baa55b112ef80e1477c369bea870a50c6b`.
Original / plus / minus result JSON SHA256:

- `df46fd5ee7ffad512bd88588e9d6f26746817346ce4d4a3e81245cbe9d300933`
- `fffbd5e83002f2bd7f17b8937744a76e6d0e2c395e10f9d0d431cf748824a463`
- `81bd9c57f82d99562f48864ed9a253dc0e4c38b7bcdb2e9fda110f80b6fcfba7`

Training data/labels, checkpoint and hashes are in `r33_axis_memory/`; frozen
runtime source is in `r33_snapshot/`; original raw states/substeps/MJB in
`r33_local_all/`; Spark shifted cases/probes in `r33_screen/` locally and
`/home/arm1/vmc_mujoco_runtime/esn_office_r33_20260927/results/` on Spark.

## Safety numerical audit and remaining boundary

The original and stronger initial ball strikes happen before a 25 Hz policy
can observe the collision. All neutral-before-contact controllers have the
same initial physical trajectory; later recovery cannot change that maximum.
The following probes use zero residual, unchanged ball/body physics and the
same encoder/task state, to isolate integration resolution. They are 0.2 s
physics probes, never full-task successes. The 25 us probe exactly reproduces
the initial maximum in the 6.2 s counterpart.

| Physics dt (us) | Original penetration (mm) | Stronger ball penetration (mm) |
|---:|---:|---:|
| 50 | .200284 | .215214 |
| 25 | .194609 | — |
| 12.5 | .191966 | — |
| 6.25 | .195849 | — |
| 3.125 | .195283 | .206436 |
| 1.5625 | .196223 | .207370 |

The final two estimates differ by <.001 mm in both tested conditions, meeting
the probe plan's numerical tolerance. This does not retroactively turn any
50 us full episode into a pass. The stronger ball remains over the unchanged
.2 mm threshold even at fine resolution. Peak contact force around 2 kN in
the original case is also not evidence of safe real-human interaction.

Next work must address the unresolved first-impact safety limit and ensure
adequate person/rod stress exposure with a frozen evaluation protocol. Merely
more VMC readout fitting cannot undo a peak that occurs before the first
post-contact observation. A justified common physics resolution and a causal
high-rate safety/control architecture need explicit evaluation before any
hardware-readiness or broad safety claim. Keep existing failures and gates;
do not weaken the ball or relabel development as blind to obtain a pass.

Completed: three-layout R33 task screen, seven targeted tests, trained-model
invariant checks, 30-episode failure-inclusive summary and original office
animation. Outstanding: strict safety and sufficient stress exposure across
conditions, withheld validation, and hardware validation. The overall safety
goal remains active; no real-robot-ready or ESN-superiority claim is made.

Final verification: all three R33 episodes' 1,375 recorded actions were
independently replayed from the frozen checkpoint and observations. Maximum
absolute error was 0 locally, 1.50e-15 for plus, and 2.20e-15 for minus.
RMSE, peak torque and peak speed were independently recomputed from all
1,100,000 physical-substep samples per episode and matched within raw float32
precision. Both Spark layout directories, including MJB and full substep
sidecars, are now fully archived locally. Final Spark process check found no
office evaluator running; all seven R33 queue jobs exited 0. There are no
unattended active jobs in this campaign at handoff.
