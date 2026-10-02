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
The current ball report gives ~6523 N peak in ~7.3 ms, impulse ~2.633 Ns.
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
