# R30 full office-v5 result (2026-09-26)

## Result

The frozen R30 checkpoint fails the full historical office-v5 complex scene.
This corrects the earlier over-broad interpretation of its guarded moving-rod
results.

| Gate | Result |
|---|---:|
| Pick/place task | fail (`0/1`) |
| Strict task+safety | fail (`0/1`) |
| Final stage | `approach` |
| Maximum external penetration | `0.177712 mm` (passes `<=0.2 mm`) |
| Ball contact | present |
| Person-hand contact | absent |
| Rod contact | present |
| Cup stable | yes |

The run used seed `2026091751`, variant `0`, `events=all`, 21 s, 50 us
physics, and the original full person/hand + ball + rod + cup + pillar + thick
corner scene.  The canonical observation remained proprio48 and did not add
stage, schedule, geometry, or contact truth.

## Explanation

The reservoir selector fires immediately: its 20-step +z pulse is active from
0.08 to 0.84 s while the task is still in `approach`.  In the guarded-rod
development/validation histories, the same detector fired only after loaded
lift.  This is a concrete closed-loop history-distribution shift, not a
rendering problem.  All 525 office control frames remain at stage 0.

The maximum external penetration remains below the fixed safety limit, but a
safe non-completing trajectory is not task success.  Missing person-hand
contact also fails the predeclared all-events coverage requirement.

## Evidence

- Protocol: `docs/ESN_R30_OFFICE_COMPLEX_PROTOCOL_20260926.md`
- Raw result: `outputs/esn_r30_office_complex_20260926/seed_2026091751_variant_0/rollout.json`
  (`706f106f5c205154c8fc37566de10642a13c55ee4d4cd972ccd1d43f7c46bcfa`)
- Raw trace: `outputs/esn_r30_office_complex_20260926/seed_2026091751_variant_0/rollout.npz`
  (`c40ee0d56aac3eab4ea567692ad3ade324fd92e5f5837e2c11c241402fc0eab1`)
- Offline replay GIF/MP4 and manifest are in the same output directory.
- Rendering uses recorded qpos and does not rerun or modify physics.

## Next valid development step

Treat this historical office condition as exposed. The 2026-09-27 paired
diagnosis (see `ESN_OFFICE_RECOVERY_20260927.md`) shows that pulse-disabled
R30 still fails approach without driven events, while zero residual proceeds
to grasp/carry. Thus an early pulse or ball collision alone is not a proven
cause; base-readout free-space drift also needs correction. The office
development campaign preserves all original failures and requires task
completion and the unchanged 0.2 mm gate before withheld validation.
