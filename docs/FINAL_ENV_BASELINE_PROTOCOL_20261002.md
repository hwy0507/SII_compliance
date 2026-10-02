# Final environment baseline protocol review — 2026-10-02

Source reviewed: main `7cd5f4b7ac0a3056df76ac62bc690ded0724b104`.
This document proposes a final comparison protocol. It does not change the frozen
environment, authorize new WBC edits, or relabel the primitive campaign as office results.

## Decision

Use office-tool-contact-v5 as the fixed composite challenge. Preserve the 1 kg /
60 mm ball, 1.7 m/s launch at 2 s, human 3–10 s, palm rod 12–25.5 s with fixed
10 s hold, unknown edge present from reset, common planned route/rejoin v2,
55 s horizon, actuator limits, pure proprio48 actor input and placement gate.
Another agent owns final WBC changes. Once provided, every method must use the
same WBC source/configuration hash; a changed WBC starts a separately named cohort.

The existing ESN rollout is task=false / strict=false (load_transfer), with
0.653202 mm external penetration at pillar/link7. That alone does not prove the
environment is impossible: it proves this checkpoint fails. First establish a
common no-active-disturbance/no-unknown-edge nominal control. Then distinguish
common execution failures from contact recovery failures. Never remove the pillar,
relax penetration, or select geometry using the relative ranking of methods.

## Test layers

| Layer | Purpose | Outputs beyond shared task/strict |
|---|---|---|
| Public nominal diagnostic | Common grasp/carry/place feasibility | stage progress, placement, completion time |
| Ball only | transient impulse response | actual contact pairs/impulse, peak force, peak displacement, recovery |
| Human only | sustained compliant yielding | force/time, displacement, recovery and task progress |
| Rod only | finite-force pushing and escape while extended | contact duty, recontacts, disengaged hold interval, progress |
| Unknown edge only | unmodeled blockage and reference rejoin | blocking duration, actual crossing/rejoin, placement |
| Exact full v5 | combined primary challenge | full-horizon metrics and stage-specific failure reasons |

Single-event conditions are **new labeled diagnostic interventions**, not identical
MJB comparisons with full v5 unless independently proven. Preserve all failed runs.
The current user request is to review settings; these diagnostic interventions
have not yet been executed or inserted into the environment.

Do not switch events on a controller-dependent task phase, chase the hand with
an obstacle, or reset/teleport an obstacle after launch. The fixed schedule can
produce unequal contact across methods; report exposure on every episode.
No-contact episodes remain in task denominators but are not successful impact
recovery samples. Do not impose legacy “touch every obstacle” as the task gate.

## Controller comparison

Primary: nominal zero, fixed BO-derived admittance/impedance/VMC, and their
respective online parameter RL versions, plus direct RL metric/office_task and
the supplied ESN/MLP. Proposed methods and baselines share scene, common WBC,
observer, nominal references, safety projector, torque/slew limits and evaluation.

One geometric-mean prior per controller is shared across all primitive training
scenes and office transfer. No scene-label prior selection. The prior is transferred
from the older BO bank, not a fresh office-specific BO optimum.
The common WBC generates identical nominal-reference semantics for all methods.
Impedance uses its own wrench-to-torque law with the inherited torque projector
and slew limits; it does not retain the nominal velocity-tracking torque law.
The fixed-prior comparator uses precisely the same implementation as parameter RL
with zero parameter action. This isolates online parameter adaptation.
Classical controllers may contain their intrinsic virtual state; the RL actor still
only receives canonical48 and its saved training normalizer.
Parameter rates 25 Hz, positive bounded parameters and local storage-change
budget remain as registered. This safeguard is not a robot-wide passivity proof.

Separate two scientific questions:
1. **Primary transfer:** train only on registered primitive training split; freeze
   checkpoints/prior before office evaluation. No office fine-tuning.
2. **Optional future adaptation study:** train all learning methods on the same
   separately registered office training distribution and budget. Report separately.
Do not mix a transferred baseline with a proposed method tuned on test episodes
and describe it as equal-data learning; disclose every method's data exposure.

## Metrics and validity

Main outcome: complete 55 s, lift >0.1 m, released payload supported on target for
final 0.5 s; XY <25 mm, Z <15 mm, linear speed <15 mm/s, angular speed <0.15 rad/s,
finger sum >75 mm, no robot support. Strict adds the inherited physical gate and
external/edge/payload penetration <=0.2 mm. Reuse code; do not redefine gates here.
Report task and strict separately, actual contact exposure, full-horizon RMSE,
actual generalized actuator peak torque, hand linear peak speed, penetration,
duration and abort reasons. Contact windows additionally report force/impulse,
yield displacement and recovery/recontact measurements.

Low RMSE from a stalled or aborted task is not success. Compare matched durations
and give both all-episode outcomes and full-horizon conditional metric summaries.
For reference tracking, include path progress so a controller cannot look good by
holding still. Recovery should use a predeclared error/speed band and continuous
hold duration; derive thresholds from task tolerances before inspecting rankings.
Show full videos at true 1x and native-state contact clips at explicitly labeled
0.25x, all methods using the same three cameras.

## Numerical and statistical limits

Development uses dt=1e-4; formal requires dt=5e-5, same 4 ms servo / 40 ms actor.
The audited all-event nominal ball report gives 7883.55 N peak, 3.2 ms aggregate robot contact, and 2.57116 Ns impulse; the historical ESN has a different pre-impact state.
Inspect timestep convergence of impulse, ball momentum, hand response and
penetration, not only a highly step-sensitive force maximum. Preserve the
development failure regardless of formal outcome. No formal result exists yet.

One fixed composite condition cannot establish generalization. After the common
WBC is fixed, predeclare a paired held-out condition list using physically feasible
initial-pose, impact and force perturbations; freeze it before model comparison.
Select ranges from physical feasibility and the training distribution, not from
which method wins. Record out-of-distribution axes explicitly. Do not invent a
large success-rate claim from the present single training seed / small test set.

## Server inputs

Host: arm1@192.168.31.70.
- Source: /home/arm1/sii_shared/SII_compliance/source/7cd5f4b7ac0a3056df76ac62bc690ded0724b104/
- Full reference: /home/arm1/sii_shared/SII_compliance/runs/main/tool_contact_review_20261002/evidence/tool_contact_20261002/v5_esn_full/
- Model SHA256: b092662aa1d6fba12357cd0a6271d309abeb047ad09f20a0a646d48415b637a1
- Primitive baseline study: /home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/
- Source and artifact histories remain separate from WBC development.

## Executed feasibility evidence at 2026-10-02 10:24 UTC

The exact archived composite MJB has now run under the nominal (zero extra action)
controller for all 55 s / 550,000 substeps. It lifts 0.128606 m but remains in
carry and never establishes the final placement hold: task=false, strict=false.
Its limited physical gate passes, with maximum external penetration 0.158694 mm.
RMSE is 27.5569 mm, actual peak generalized actuator torque 36.9007 Nm and peak
hand speed 0.398633 m/s. Independent raw-substep recomputation agrees within
float32 logging tolerances. This is all-event zero, **not** the no-disturbance
feasibility control proposed above.

Ball, human and rod contact the hand. Ball peak force is 7883.55 N and impulse
2.57116 Ns; aggregate robot contact is 3.2 ms. Do not infer contact stiffness or
hardware safety from the rendered frames. Unknown-edge aggregate statistics
include payload contact from 11.8843 s; specifically recorded robot-finger
contacts begin 33.7344 s and persist to the end. Distinguish those definitions
rather than calling the earlier payload contact a robot-arm collision.

The main source ESN reference is also a complete failed episode, with 49.4283 mm
RMSE, 45.8801 Nm peak torque, 0.370425 m/s peak speed and 0.653202 mm external
penetration. This comparison motivates progress/contact diagnostics; it does not
prove the learned method is inferior at equal training exposure. A fixed composite
fixture with two failed controllers is not sufficient to establish either
impossibility or useful statistical discrimination among methods.

Published zero replay: http://192.168.31.70:8765/primitive_baselines_20261002/office/
Full replay is 55 s at 1x; ball closeup is explicitly 0.25x. Evidence is under
/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002/office_bridge/transfer01/zero/.
The original rollout, source patch, MJB hash, independent OFFICE_AUDIT.json,
render manifests and contact-clip TIMING_AUDIT.json are retained.

## Separate post-contact capability from early task incompatibility

The first completed 60k metric-RL held-out ball episodes include no intended ball
contact and task failure, while the paired nominal models have actual contact.
These are retained failures, not measurements of good impact recovery. This
observation does not change the registered test set or motivate obstacle chasing.

For the final WBC cohort, include a separately registered **common loaded-state
contact benchmark** alongside the full pick/carry/place pipeline. Establish a
physically valid, stable grasp with the common nominal prefix, archive the full
MuJoCo integration state, task-supervisor state, nominal-reference/planner state,
and common prefix records, then branch all controllers from that same pre-impact
condition. Preserve the shared lift/history when scoring the full task; a reset
that discards it must be labeled as a different remaining-task diagnostic. A
deterministic shared-prefix replay with verified state equality is an alternative
to restoring all simulator/internal controller fields. Specify controller-state
initialization/burn-in before evaluating; ESN memory and classical virtual state
must not receive a selected favorable history. Verify initial-state equality,
contact-free settling and actual support/load before releasing an impactor.
The actor still receives only canonical48; no contact/scene truth or new time
feature is added. Model hashes, physics settings, finite-force impactor drives,
actuator limits and physical/task gates remain paired within this new cohort.

A fixed shared handover time and predeclared impactor state are allowed experiment
conditions; a controller-dependent trigger or chasing the hand is not. Some
policies may still avoid later contact through their motion. Report the complete
condition denominator, exposure rate, and contact-conditioned response separately.
Avoiding a collision can be legitimate task behavior; it cannot establish a
successful post-impact response when no impact occurred.

This is a proposed final-environment diagnostic cohort, **not** a change applied
to the current primitive training/testing or exact office-v5 transfer. A fresh
cohort needs shared reset/burn-in validation and its own training/exposure ledger.

## Match each event to the controller's response timescale

The audited nominal office ball has 3.2 ms aggregate robot contact, while actor/
parameter updates are every 40 ms and the common servo is 4 ms. The first impact
peak therefore depends strongly on incoming momentum, contact material and
pre-impact mechanical/controller state. A 25 Hz policy cannot be credited with
reacting within a sub-40ms impact merely because its first peak is smaller.
Keep peak force/impulse and penetration as diagnostics, and assess subsequent
hand/payload displacement, oscillation, rejoin and task completion explicitly.
The next human event begins at 3 s, so recovery measured in the full composite
condition becomes confounded after that time; mark unfinished recovery as censored
or use the separately labeled ball-only diagnostic. Do not pretend a later human
response is a pure ball recovery curve.

Rod hold lasts 10 s (250 policy updates), making sustained yielding, contact duty,
sliding/disengagement and subsequent recovery informative for online adaptation.
Human push tests compliance during a finite disturbance and recovery after
withdrawal. The fixed unknown edge tests blockage escape, path rejoin and actual
placement, for which a small global tracking RMSE can coexist with stagnation.
These complementary outcomes should remain visible instead of being reduced to
one reward-selected ranking.

## Legacy primitive launch audit (separate from the fixed office-v5 schedule)

Inspection of frozen source_scene_20260918/scripts/run_primitive_teacher_v7_20260917.py
shows that the old ball scene computes its launch position/velocity from the
actual hand position at a stage-triggered launch, then releases a free ball. It
also holds task-phase advancement until actual contact and a 0.6 s post-contact
interval. These are shared legacy scene/supervisor rules, not privileged actor
inputs, but they make old primitive scores different from a fixed exogenous
impact experiment. Matching initial MJB and sampled parameters certifies the
same scene rule; it does **not** certify identical incoming ball states.

Preserve this protocol for the registered video-derived campaign. Do not silently
change its launch rule after seeing results. Record each executed launch state
and its difference across methods. The fixed-world office-v5 transfer remains
a separate cohort, with fixed 2 s launch and common initial ball state.
The no-chasing/shared-loaded-state recommendations above concern final comparison
design, not a claim that the old primitive launcher already meets them.

A new inter-step audit complements the existing within-step momentum balance:
exclude only the explicitly recorded first scripted launch, then check velocity
continuity between native steps and implicitfast free-position integration.
The first 28 completed ball trajectories pass with zero nonlaunch velocity resets
and <=1.78e-15 m translation-update residual. Thus those traces contain no extra
post-collision scripted velocity kick; contact-material realism is a separate
question. Evidence: BALL_STATE_CONTINUITY_SUMMARY.json and each episode's
BALL_CONTINUITY_AUDIT.json under the primitive study root.

## Executed numerical sensitivity check

Three preregistered nominal-only probes end at 3 s, before later human/rod contact.
Each uses a derivative of the exact office MJB with only opt.timestep changed;
restoring the original timestep reproduces the original MJB SHA256. The 1e-4 s
probe's saved state/observation/action prefix is exactly equal to the full zero
rollout. No geometry, policy, gate or controller parameter is selected here.

| dt (s) | Ball peak N | Ball impulse Ns | Robot contact ms | Max external penetration mm | Peak hand speed m/s |
|---|---:|---:|---:|---:|---:|
| 1e-4 | 7883.547 | 2.571158 | 3.2 | 0.158694 | 0.398633 |
| 5e-5 | 7367.647 | 2.537813 | 3.5 | 0.185452 | 0.404975 |
| 2.5e-5 | 6457.494 | 2.545698 | 3.9 | 0.171166 | 0.396365 |

Relative to the coarse step, the finest impulse changes -0.99%, hand peak speed
-0.57%, and peak contact force -18.09%. This supports reporting impulse/motion
alongside the sensitive peak, without claiming asymptotic force convergence or
material realism. These are 3 s numerical diagnostics, **not** full-horizon formal
baseline results. Files: office_bridge/numerical01/{REGISTRATION.json,SUMMARY.json,
SUMMARY.csv,timestep_comparison.png} under the study root.

## 建议交给最终环境 / WBC 的具体设置（提案，未在本轮改动环境）

保留当前 v5 综合场景作为固定复合挑战；先补公共任务可行性，再分解接触机制。
不要按哪种方法分数更好来移动物体、改变材质或挑选初态。

| 编号 | 设置 | 要回答的问题 |
|---|---|---|
| N0 | 55 s，原目标、抓放门槛、已知障碍及公共规划不变；球/人/棍处于明确无作用的停放状态，关闭未建图凸边 | 共同名义 WBC 能否正常抓起、搬运、松手和稳定放置 |
| B1 | 与 N0 同一任务，只启用 v5 的 1 kg / 60 mm 球，2 s、+y 1.7 m/s；碰后自由积分 | 冲量、物块是否掉落、碰后偏移/振荡、恢复推进和放置 |
| H1 | 与 N0 同一任务，只启用人手 3–10 s、80 N 驱动上限 | 有限时长推压下的让位和撤力后的恢复 |
| R1 | 与 N0 同一任务，只启用棍，12–13.5 s 推进、保持到 23.5 s、25.5 s 撤完；14 N 上限 | 持续力下的参数适应、滑脱/回碰、接触占空比、撤杆后恢复 |
| E1 | 与 N0 同一任务，只恢复从 reset 存在的未建图凸边，固定原位置/尺寸/材质 | 受阻后的路径推进、脱困、接回与最终放置，防止“站住不动”得到好 RMSE |
| C1 | 完整保留 main 7cd5f4b 的所有事件、凸边、55 s 和成功定义 | 接触影响连续累积时能否完成整场任务 |

N0/B1/H1/R1/E1 都是各自命名的诊断 fixture，模型 hash 必须分别归档；
它们不是对 C1 结果的替代。公共可行性控制应先在公开开发初态完成，失败时定位共同
抓取/规划/WBC/释放链；不利用保留测试结果反复选择环境。当前已完成的 all-event zero
不是 N0，也没有证明新版 N0 成功。

另加共同已抓稳初态的 B1/H1/R1 接触诊断：所有方法从同一物理状态和任务历史接管，
用于排除“还没抓住就失败”造成的混淆。时钟、事件绝对状态及控制器预热方式要预注册；
恢复完整任务时保留 lift 历史，若只测剩余任务则单独命名。无碰撞样本计入完整条件分母，
接触后的恢复统计另外标注有效接触数，不把未碰到球当作柔顺成功。

**难度分层建议先只改变外界激励幅度。** 以现有参数为中档，公开开发中可检验
球速 1.36/1.70/2.04 m/s、人手力上限 64/80/96 N、杆力上限 11.2/14/16.8 N；
球质量/半径和接触材质不随方法变化，时序保持固定。这些 ±20% 是待物理可行性核对的
设计候选，尚未运行、尚未成为冻结测试清单；不是从当前成绩推导出的“最优难度”。
先在训练/开发条件检查初始无相交、有效自由空间、实际驱动和数值稳定性，再一次性锁定
范围及独立条件种子。凸边先保持当前几何，不同时叠加尺寸/位置/摩擦变化。
最终发布按低/中/高强度分别报告，不能只挑 baseline 失败最多的一档。

**指标需按事件定义。** 球保留首次接触峰力、总冲量、最大手/物块偏移及掉落；
恢复计时要对应同一名义轨迹，使用预注册误差/速度带和持续保持时间。
C1 中球恢复到 3 s 仍未完成的样本受人手事件干扰，标记截尾；B1 用于完整恢复曲线。
杆保持期内记录实际接触力/冲量、累计受力时长、最长无接触区间和回碰次数；
撤杆后再评估路径接回，不能把定时撤杆造成的脱离称为主动让位。
桌角同时看路径进度、卡住时长和放置；所有组同时保留 task、strict、RMSE、
实际峰值力矩、手部峰速、最大穿透、接触录取和失败原因。

最终 WBC 更换后，所有控制器使用同一公共规划、参考/观测构造、执行器投影及门槛。
阻抗 baseline 的力矩控制律本身是比较对象，不能因为要求公共接口就把它替换成名义
控制律。每类固定参数和在线调参使用同一实现、同一统一先验；纯 ESN/MLP 采用同一
canonical48 输入。正式条件使用 dt=5e-5，并完成完整时长验证；不能仅凭本轮三秒
步长探针宣布正式通过。

## 接触材质与动作能力的解释边界

归档 MJB 直接读取确认：旧球锚点的显示半径 60 mm、碰撞内核半径 51 mm，
9 mm margin 表示柔性表层，soft solref=[.012,.75]；同位置另有无质量 hard core，
solref=[.0006,1]。office-v5 则为 60 mm、零 margin 的单球碰撞体，
solref=[.0004,.55]。因此两组的反弹时长/峰值不能作为同一种材料响应直接比较。
旧球的 .2 mm 负接触距离门槛限制内核重叠，不代表允许的柔性表层压缩也只有 .2 mm；
渲染球体不真实形变。材质若要按实物校准，需要单独的公开校准和新冻结版本，
所有方法同改；本轮归档结果不回写。solref 不是已测量的杨氏模量。

最新版原球锚点 zero / metric74001 / office_task74001 的机器人接触峰力分别
204.651 / 205.850 / 204.520 N，冲量 1.44754 / 1.45553 / 1.43907 Ns；
各有约20 ms受力。该锚点里首次碰撞相近，RL后续任务仍失败；不能据此否认此前
不同checkpoint/不同条件视频的问题，也不能把新office的数千牛峰值套回旧球。
证据在 BALL_CONTACT_MODEL_INVENTORY.json 及原生子步轨迹。

人手80 N和杆14 N是**驱动力上限**，不保证碰撞接触峰力小于这个数；
实际接触力、冲量仍需按物理子步统计。C1先固定保留，数值或材质校准放入独立开发组。

另外，输入相同不意味着动作表达能力相同。正的对角刚度/阻尼调节只能在既定控制器结构
内改变响应；直接action7残差可以另外产生方向性速度/让位。E1脱困可能同时考验几何
运动能力和柔顺性，而不只是“参数调得好不好”。主比较保留完整任务，但机制分析应
分别报告B1/H1/R1的局部接触响应，以及E1的受阻推进。不要把无法新建绕行路径的
调参策略失败简单归因于RL优化器，也不要给某种方法独占新的规划器。
判断在线调参的增益，首要使用同控制器fixed-prior对照；比较ESN/MLP与调参RL时
明确两者动作空间/控制器结构差别。
