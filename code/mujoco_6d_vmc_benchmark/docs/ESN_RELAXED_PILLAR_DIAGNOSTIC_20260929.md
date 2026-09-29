# ESN relaxed-pillar diagnostic - 2026-09-29

This is a development-only diagnostic requested after combined-v4 was blocked by
the pillar. It does not replace the original combined-v4 or formal `dt=5e-5`
condition. The ESN checkpoint, canonical48D/action7 pure-proprioceptive contract,
ball/person/rod disturbances, cup, thick corner, task gates, actuator limits and
hybrid blend remain unchanged.

The opt-in `--relaxed-pillar` flag changes only the combined-v2 pillar: position
`[.585,-.300]` to `[.620,-.100]`, radius `15 mm` to `10 mm`, half-height `25 mm`
to `15 mm`, with lower friction and a more compliant contact material.

The retained `dt=1e-4`, 36 s rollout is
`outputs/esn_relaxed_pillar_combined_v2_20260929/postrelease36`.

| Item | Result |
|---|---:|
| external penetration | `0.117404 mm` |
| peak torque | `48.813 Nm` |
| peak speed | `0.068410 m/s` |
| 3-D position RMSE | `0.055491 m` |
| cup contact | `0.8807 s / 7.279 N` |
| cup shift / tilt | `9.839 mm / 0.849 deg` |
| final stage | `load_transfer` |
| task / strict | fail / fail |

The relaxed pillar removes the original carry blockage and brings penetration
below the unchanged `0.2 mm` gate. The cup remains valid. However, this run has
no pillar contact and the current-source controller remains in `load_transfer`,
so it is not a complete combined-scene success.

An intermediate placement `[.600,-.270]` produced a real pillar window
(`1.739 s / 60.82 N`) but penetrated `0.5255 mm`; it is retained as a failed
diagnostic. The conclusion is that relaxing the pillar removes the carry
collision, but the remaining bottleneck is the release/load-transfer transition.
