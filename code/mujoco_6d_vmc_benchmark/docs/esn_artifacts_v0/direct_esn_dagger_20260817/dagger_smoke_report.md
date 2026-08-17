# Direct ESN DAgger smoke report — August 17, 2026

## Scope

This is the first closed-loop Direct ESN DAgger smoke on the Panda fixed-WBC
rod-impact task. It is not a final benchmark, a transfer result, or a claim of
superiority over VMC/impedance/rigid baselines.

The deployed student receives only joint position, joint velocity, nominal WBC
twist, WBC pose error, and WBC twist error. Contact force, contact normal,
penetration/signed distance, impactor data, and contact duration are recorded
only after the student rollout to create offline teacher labels.

## What DAgger fixed

Before DAgger, the imitation-only student could produce a small residual in a
no-rod episode, create its own tracking error, and then amplify that error in a
closed-loop positive feedback loop.

One DAgger iteration collected 155 student-visited states each for rod and
matched no-rod. The no-rod archive was relabeled with exactly zero teacher
action. The first DAgger model reduced matched no-rod behavior to:

| Metric | Imitation-only student | DAgger iteration 1 |
|---|---:|---:|
| Task success | false | true |
| Mean WBC slowdown | 0.1564 | 0.000029 |
| Mean yielding-twist norm | 0.1449 | 0.000069 |
| Hard torque limit | false | false |

This is the desired nominal-neutrality correction: the ESN no longer changes a
normal WBC grasp appreciably when there is no collision.

## What remains unsolved

The same DAgger model remains too conservative under rod contact. It succeeds
and observes an effective collision without a hard torque limit, but its mean
yielding-twist norm is only `0.0010`, i.e., close to fixed WBC. In the matched
single-fixture smoke, it did not improve post-release trajectory performance:

| Metric | Fixed WBC | DAgger iteration 1 |
|---|---:|---:|
| Post-release position RMSE | 5.53 mm | 5.66 mm |
| Peak position deviation | 12.37 mm | 13.16 mm |
| Rejoin latency (5 mm criterion) | 505 ms | 545 ms |

The weighted DAgger pilot (`neutral_repeat=3`, `rod_repeat=4`) preserved
no-rod task success and increased rod action slightly, but the rod action was
still too small for a valid compliance-improvement claim.

## Research decision

DAgger is retained because it solves the critical nominal-neutrality failure.
The next method iteration must improve *teacher quality*, not remove the
student-visited-state data:

1. label a nonzero contact-window yield with a counterfactual one-step safety
   rollout rather than a simple force-normal template;
2. score candidate actions by force/impulse, trajectory error, torque, and
   secondary-contact cost;
3. retain a separate no-rod zero-action teacher stream;
4. run DAgger over several rod fixtures before any ball/hand-palm transfer.

Artifacts copied from the server are the JSON files in this folder.

