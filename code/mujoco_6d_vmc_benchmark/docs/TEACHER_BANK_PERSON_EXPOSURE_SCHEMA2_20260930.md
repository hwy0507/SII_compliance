# Training person-exposure correction — schema 2

This corrects the **source-domain training exposure audit**, uniformly for VMC,
admittance and impedance. It does not change the frozen office task, formal
evaluation gate, geometry, actor inputs, actuator limits or sealed conditions.
Existing v6/v8 snapshots, raw data and historical audit files remain unchanged.
The next campaign snapshot must record the new source hash and schema explicitly.

## Confirmed defect and corrected meaning

Schema 1 treated any end-effector displacement of at least 1 cm during continuous
person contact as yielding. Array-only counterexamples showed that movement
towards the person and purely tangential nominal motion both passed. Contact
starting after the person had begun retracting could also pass.

The generated fixture stores `axis = [cos(yaw), sin(yaw), 0]`. The person root
slide has local axis `-x`, so its positive-stroke world direction is **`-axis`**.
The rod uses local `+x` and therefore pushes along **`+axis`**. Reversing the
person direction by simply using positive `dot(displacement, axis)` would reward
approaching the pusher. The rod's tangential norm is invariant to this sign;
its slide-and-separate predicate is unchanged.

For person acceptance, schema 2 requires both:

- More than 0.4 s of uninterrupted force-bearing contact inside the scheduled
  press/hold interval `[start, start + press + hold]`.
- At least 1 cm of maximum signed end-effector displacement along `-axis` in
  that same continuous interval.

The position origin is the first contact pose inside the allowed interval.
Only full recorded physics intervals contained within the press/hold window are
included. At most two boundary substeps are conservatively excluded; motion
before contact or after retraction cannot contribute. Any substep without
force-bearing contact breaks continuity, even if a 4 ms display bucket hides it.

The original unrestricted displacement norm, tangential displacement and complete
contact runs remain diagnostic fields. They no longer certify person yielding.
The new measure demonstrates **signed kinematic displacement under contact**;
it does not by itself prove the controller caused a deviation from its nominal
motion. Such a causal claim needs a separate matched counterfactual study.

## Recorded evidence and exact re-audit

Schema 2 `exposure.npz` retains the existing `contact_runs`, 4 ms aggregates and
fixture metadata, and adds:

| Field | Meaning |
|---|---|
| `person_physics` | Every physical sample: time, dt, force magnitude, hand x/y/z |
| `person_physics_fields` | Explicit names for the six raw columns |
| `person_window_runs` | Press/hold contact-run fields plus `max_signed_push_m` |
| `person_window_run_fields` | Explicit names for the eight run columns |

The raw person array is recorded only for person scenarios; other scenarios carry
empty arrays. Its uncompressed size for a 55 s, dt=1e-4 episode is about 26.4 MB.
It is accumulated in a compact numeric buffer rather than per-substep Python
dictionaries. This is evaluator-only evidence; none of it is fed to an actor.

`audit_saved()` recomputes person-window runs from these raw samples and compares
them with the saved runs. It checks raw continuity, finiteness, force values,
horizon, and agreement with the existing 4 ms aggregates. It then applies the
directional predicate. Run indices in person acceptance refer explicitly to
`person_window_runs`, not to the original unrestricted `contact_runs`.

The observer retains the existing MuJoCo timestamp caveat: live hand kinematics
and forces originate from the completed step's dynamics evaluation. They are not
advertised as a freshly recomputed, perfectly synchronous post-integration state.

## Legacy v6/v8 compatibility

Schema 1 remains readable. Rod, ball and passive-corner predicates are unchanged.
For person records, the new reader reports `directional_yield_unverified` and
`passed=False`, retaining original norm/timing diagnostics. This means **missing
evidence for the new predicate**, not a retrospective claim that the robot
physically failed.

Legacy full contact runs can establish overlap with the press/hold time window.
Their norm-only maxima cannot reconstruct signed motion. The existing 4 ms hand
poses may support an approximate diagnostic but cannot recover the exact
physical-substep directional maximum, so they must not promote a legacy record
to schema-2 acceptance. Do not rewrite its original `audit.json` or schema field.
If additional legacy analysis is saved, use a new report containing original
artifact/source hashes and clearly separate historical acceptance from current
verification. Exact new acceptance requires a fresh episode under the registered
new snapshot, with the same declared method/configuration and new evidence.

## Validation and scope

Array-only tests cover along-push success, towards-pusher and tangential rejection,
retraction-only contact rejection, post-retraction displacement exclusion, rotated
world axes, submillisecond contact breaks, saved replay, corrupted raw evidence,
and schema-1 non-promotion. No MuJoCo rollout or held-out condition was opened for
this correction. Broader physical performance remains a campaign result, not a
consequence of passing these tests.

At authoring, these edits are a local working copy awaiting the parent campaign's
commit/snapshot/archive step. No unverified server path is presented as available.
