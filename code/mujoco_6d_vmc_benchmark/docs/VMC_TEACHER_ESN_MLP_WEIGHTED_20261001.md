# VMC teacher → ESN/MLP weighted-readout comparison (2026-10-01)

## v3 corrected-label rerun

The original v2 trainer was retained, but the loader semantics are now explicit and
tested: student targets come from `execution_chain.npz["filtered_action"]`; the
raw `rollout.npz["applied_action"]` is retained only for provenance comparison.
Both files are hash-checked for every manifest entry, and metadata pins the ESN/MLP
inference modules as well as the teacher chain files. This correction changed no
values in the nine frozen traces (maximum raw-versus-filtered difference
`8.9e-16`), but prevents a future active filter from silently changing the label.

The immutable v3 output is `outputs/vmc_teacher_esn_mlp_weighted_20261001_v3/`.
It uses seed `2026100104`, the same weighted loss and the same frozen combined-v4
command with no initial refinement. All rows are development `dt=1e-4`, 55 s and
550000 physical substeps. The independent audit is
`outputs/vmc_teacher_esn_mlp_weighted_20261001_v3/independent_audit_norefine/AUDIT.json`.

| policy | task | strict | final stage | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | penetration (mm) |
|---|---:|---:|---|---:|---:|---:|---:|
| frozen VMC teacher | yes | no | retreat | 43.438 | 50.324 | 0.1008 | 0.1525 |
| v3 ESN | no | no | carry | 406.806 | 43.246 | 0.2404 | 0.1929 |
| v3 MLP | yes | no | retreat | 43.333 | 44.405 | 0.0753 | 0.1012 |

Action replay is exactly zero for both students and ESN reservoir-state replay is zero.
The MLP completes placement but misses the unchanged sustained-contact gate; the ESN
stops in carry. No formal `dt=5e-5` rerun is unlocked, and no environment, gate,
actor input, or actuator limit changed. The first v3 attempt with an initial fine-step
diagnostic is kept separately and is not used in the fair table because it has 676000
physical substeps.

## v4 unweighted control

As a pre-registered control for the loss weighting, v4 used seed `2026100105` and
`emphasis=0` with the same filtered-action loader, frozen world, and 55 s/550000-step
command. It produced ESN task/strict `false/false` (lift, 526.818 mm RMSE,
44.416 Nm, 0.2204 m/s, 0.1323 mm penetration) and MLP `true/false` (retreat,
38.832 mm, 44.286 Nm, 0.0807 m/s, 0.1527 mm). Replay and independent physical
substep checks passed; the audit is
`outputs/vmc_teacher_esn_mlp_weighted_20261001_v4/independent_audit_norefine/AUDIT.json`.
Across v3 and v4, MLP completes the task but misses the unchanged sustained-contact
gate, while ESN remains unstable in the late carry/lift sequence. These are development
results and do not unlock formal `dt=5e-5`. The complete v3/v4 archive (68 files) is
available at `arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v3_v4/`;
its relative-path SHA256 receipt is `ce2046f058475edcada19bf264a5f0e3406197b8f34a448f1485d3820e34aff5`.

This is a development-only continuation of the locked VMC-teacher student
comparison. The MuJoCo world, combined-thick-corner-pillar-v4 fixture, task
gates, actuator limits, canonical48D observation contract, and action filter are
unchanged. Both students use 128-unit trainable hidden/readout width and seven
action outputs. No contact truth, object state, event time, task stage, visual
or range field enters the actor.

The only predeclared change is a training loss weight
`1 + 3*tanh(||estimated_wrench[39:45]||/0.5)`. This is computed only while
fitting the readout from the frozen teacher bank; it is not saved as a runtime
input or gate. The training manifest is
`outputs/teacher_bank_label_manifest_20260930_final_v1/manifest.json`, SHA256
`6e81f03a90a7fc850bd68f19507db0769b517e9f85f9415edefc3433f7fa98f3`, with the
same seven train fixtures and two replay fixtures as v5.

## Results

All closed-loop rows are 55 s, 550,000 physical substeps, development
`dt=1e-4`, and the same combined-v4 development command. The independent audit
is `outputs/vmc_teacher_esn_mlp_weighted_20261001_v1/independent_audit/AUDIT.json`.

| policy | task | strict | placement | RMSE (mm) | peak torque (Nm) | peak speed (m/s) | penetration (mm) | longest rod contact (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| frozen VMC teacher | yes | no | complete | 43.438 | 50.324 | 0.1008 | 0.153 | 0.0670 |
| weighted ESN | no | no | incomplete, lift | 688.378 | 62.020 | 0.1800 | 0.127 | 0.0050 |
| weighted MLP | yes | no | complete | 50.381 | 46.634 | 0.0823 | 0.147 | 0.6056 |

Action replay and the three physical metrics independently recomputed within the
registered tolerances. The weighted MLP greatly improves rod-contact duration
over v5 MLP (`0.6056 s` versus `0.0127 s`) and still completes placement, but
the unchanged sustained-contact gate is not met. The weighted ESN remains a
closed-loop failure at lift despite lower replay error than the original ESN.

Validation action replay MSEs on the two held-out identities were:

| policy | passive corner | active short | passive contact | short contact |
|---|---:|---:|---:|---:|
| original ESN | 4.40e-5 | 6.89e-5 | 7.63e-5 | 1.02e-4 |
| weighted ESN | 3.59e-5 | 4.08e-5 | 4.97e-5 | 4.79e-5 |
| original MLP | 1.45e-5 | 2.87e-5 | 2.25e-5 | 4.57e-5 |
| weighted MLP | 1.23e-5 | 1.53e-5 | 1.95e-5 | 2.19e-5 |

Replay improvement therefore does not imply closed-loop strict success. No
formal `dt=5e-5` rerun is unlocked because neither student passes the unchanged
strict gate. All failed rows and checkpoints remain in the local campaign
directory; no environment or gate was relaxed.

## Reproduction and provenance

Training source:
`tools/train_vmc_teacher_esn_mlp_weighted_20261001.py`, SHA256
`3a64cb9099a74f9e30ad1ac5c2d931db27c298f13cbde5a1c72f164947858a1d`.
Checkpoints:

- `outputs/vmc_teacher_esn_mlp_weighted_20261001_v1/esn_weighted.npz`, SHA256
  `2723e218b474e4414bbbf199eeda0099eae5dfae6af9fbd3e40cbe6b389483c9`.
- `outputs/vmc_teacher_esn_mlp_weighted_20261001_v1/mlp_weighted.npz`, SHA256
  `992a6dcd99685f278687fcf4cf25e1e6d61171dc4dde650489c679f082497cdc`.

The frozen world MJB SHA is
`5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9`.
The independent audit also verified action replay, ESN reservoir replay, 55 s
horizon and 550,000 physical substeps. The complete campaign, v5 reference
metadata, source files and synchronized docs are archived at
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/vmc_teacher_esn_mlp_weighted_20261001_v1/`.
An `ARCHIVE_FILE_LIST.txt` receipt is stored beside the archive, and remote
checkpoint hashes match the values above.
The documentation and tools are committed in Git commit
`48358e8af6c2563209d52e8f8eeeb852d9be9dae`; the corresponding immutable source
snapshot is
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/48358e8af6c2563209d52e8f8eeeb852d9be9dae/repository.tar`.
