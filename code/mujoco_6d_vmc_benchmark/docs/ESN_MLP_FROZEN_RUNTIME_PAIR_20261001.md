# Seed52 fixed-checkpoint runtime verification

The frozen MuJoCo 3.11.0 rerun does not repair ESN task failure. MLP still
completes placement; both fail unchanged strict contact coverage. All rows
below are development dt=1e-4, 55 s, 550000 physical substeps, scene seed
2026091751, combined-v4. No scene, gate, actor input or actuator limit changed.

| runtime | method | task | strict | final stage | RMSE mm | peak torque Nm | peak speed m/s | penetration mm |
|---|---|---|---|---|---:|---:|---:|---:|
| prior 3.14.0 model | ESN | false | false | lift | 72.223 | 44.403 | .125044 | .131457 |
| frozen 3.11.0 | ESN | false | false | lift | 48.971 | 43.600 | .116950 | .131457 |
| prior 3.14.0 model | MLP | true | false | retreat | 46.980 | 45.918 | .070165 | .151728 |
| frozen 3.11.0 | MLP | true | false | retreat | 46.908 | 45.907 | .070165 | .151728 |

The paired ESN RMSE changes by -23.252 mm whereas the MLP changes by -0.072 mm.
This shows that runtime drift materially changes the measured ESN trajectory;
it does not explain away failure. One checkpoint pair and one scene cannot
establish generalization. Both current environments report Python 3.11.15 and
NumPy 2.4.6, but the original environment was not fully locked: this comparison
does not isolate every library/build difference to MuJoCo alone.

## Execution and verification

Registered before dispatch in commit 5572a733a2fbc97b78201ee586cba188c49d43a3,
using configs/temporal_frozen_runtime_diagnostic_20261001.json. Local service
sii-temporal-runtime-s52-20261001 ran 15:12:17–15:15:39 UTC, two serial children,
both return code 0. Each child read its actual cgroup memory.max=3221225472
and checked one thread before simulation. Service MemoryCurrent was observed
at 580452352 bytes during ESN; this is a sample, not a peak measurement.

The guard checked the manifest, unchanged checkpoint, original evaluator source
hashes, and saved MJB before the episode. Both new MJBs match the old frozen
SHA256 5eaee4aa1399c6e47c9fcb2c477f0b6392dcb13273ca67f878aca2d05f3239f9.
Execution records include arguments, actual interpreter/version, source commit,
all scripts' hashes, training metadata/config hashes, and start/end times.
Each child performed an independent raw audit after evaluation; the report then
recomputed both old and new rows again. Actor/reservoir replay errors are zero,
physical metrics are finite and consistent, and checkpoint hashes match.

The wrong-runtime guard was tested with the 3.14.0 interpreter: it raised before
creating any run directory or simulator. A report-only Path/string bug was fixed
and the read-only report rerun; neither simulation was restarted. Original
outputs and the first successful comparison report remain intact.

## Failure diagnosis

During ESN's final ten seconds, median position error is 28.920 mm (minimum
26.920 mm), median speed 0.000860 m/s, and ready time stays zero. It is stalled
outside the unchanged 12 mm pose gate. This window has no normalized input
components above magnitude12 and no reservoir units above magnitude.95.
These checks rule out those specific saturation indicators in this window,
not distribution shift or every form of memory instability.

On the same saved late-window inputs, resetting the reservoir for every
observation changes action RMS by .157981; mean channel0 changes from .418324
to .104123 and the other channels also change. Memory therefore materially
affects readout here, but this offline perturbation does not establish that
resetting memory would improve a closed-loop task. The MLP window is in retreat
and is not a matched-phase causal control for the ESN lift window.

Next research priority: audit readout behavior under changed state histories and
training-only bounded history perturbations, with matched-budget MLP controls.
Keep the locked teacher identities and runtime; do not tune gates or claim that
removing memory is the solution. More gain/tau sweeps alone do not address the
observed persistent residual. Formal dt=5e-5 remains locked.

Small evidence: docs/evidence/temporal_runtime_pair_20261001/RUNTIME_COMPARISON_V2.json.
Verified large evidence:
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/runs/main/temporal_frozen_runtime_s52_20261001_v1/evidence.tar.gz`
(92494783 bytes; SHA256
`0b51f23b479282e35343515918ede84e090fde4951259f77e5ac137af36e7c75`).
Registered execution source:
`arm1@192.168.31.70:/home/arm1/sii_shared/SII_compliance/source/5572a733a2fbc97b78201ee586cba188c49d43a3/repository.tar`
(SHA256 `f5ddd6459b3589404996eb55773a6b2b794d6df37639e378c9890b23d323d87a`).
The post-run reporting tool is versioned separately in the result commit.
Local execution cache is outputs/temporal_frozen_runtime_s52_20261001_v1.
