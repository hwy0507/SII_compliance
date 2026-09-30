# R30 office-complex evaluation protocol (2026-09-26)

## Scope

This is the first deployment of the frozen R30 canonical proprio48 policy in
the full `office_complex_scene_v5_20260917.py` environment containing the
desk, thick corner, pillar, free cup, free ball, finite-mass articulated
person/hand, and independent finite-mass rod.  The environment is historical
and exposed, so this run is a final-scene transfer diagnostic, not a new blind
claim and not a human-biomechanics or real-robot safety test.

The earlier R30 9330--9367 result covered the guarded moving-rod fixtures.  It
must not be described as completion of this office-complex environment.

## Frozen policy and inputs

- Checkpoint:
  `outputs/esn_r30_phase3_selector_20260926/floor_065_pulse20/hierarchical_margin_vertical_pulsed.npz`
- Checkpoint SHA256:
  `3f6ed39af0c103ee6af07fada710cd90a781233041fb02c3f850996f22a3aae1`
- Contract: canonical proprio48 plus policy-local reservoir/counter state.
- No stage, event clock, actor schedule, fixture identity, geometry, contact
  truth, or future state enters the policy.
- The office adapter supplies the full estimated 6-D wrench.  This replaces
  the obsolete contact45 loader without changing the checkpoint.

## Fixed first-run condition

- seed `2026091751`, variant `0`;
- task `pick_place`, events `all`;
- duration `21 s`, physics timestep `50 us`, policy period `40 ms`;
- ball speed `1.7 m/s`, person stroke `0.20 m`, rod stroke `0.235 m`;
- person schedule: start/press/hold/retract = `3/2/3/2 s`;
- rod schedule: start/press/hold/retract = `11/1.5/3/2 s`.

The schedules drive world-side finite-mass bodies only and are not policy
inputs.  The run is performed once with raw JSON/NPZ/stdout/source/model hashes
retained.  No result-dependent parameter change is allowed before reporting
this run.

## Gates

Task success requires the existing physical pick/place state machine to lift,
carry, causally confirm support, release, retreat, and hold the placed object.
The strict gate additionally requires:

- maximum robot-versus-external penetration `<= 0.2 mm`, excluding the held
  target object's intended grasp contact;
- required ball, person-hand, and rod contact coverage;
- stable cup and ball rebound checks from the existing office evaluator;
- finite execution without the existing `2 mm` invalid-physics abort.

All failures remain in the report.  A visually plausible GIF cannot override
the numerical gates.

## Frozen source hashes before launch

- evaluator adapter: `60de6ae99374f54569e83edceda718c49170a861caa8e23d0a50d2b2ebbd3540`
- office geometry: `355c4e9a4681f4971318b023fd8da856a819345d66eebacebca67b55a10e75f0`
- office constructor/audit: `99c9b292f47a2b0c0e49e7033e04d13551accbc41d4a4f7dfc26417dc7b28e61`
  (only the stale menagerie path was resolved to the already archived
  canonical asset directory, with an explicit environment override for the
  isolated Spark snapshot; scene geometry and dynamics were not changed)
- current policy loader: `b6d96d3c6434407400bf4ae3631b56521fc12554a106b940cfe8918ae5ddb55a`
