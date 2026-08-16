# Independent ESN-v2 algorithm protocol

## Motivation

The first independent WBC residual experiment established a small, repeatable
balanced-profile recovery advantage for Fan Ye ESN over a matched current-state
MLP.  Its effect is not yet large enough for a paper claim.  An important
architectural limitation was identified: the residual authority gate used the
measured WBC tracking departure, but the actor received only joint position,
joint velocity, and nominal WBC twist.  It therefore had to infer the magnitude
and direction of the task departure indirectly from proprioception.

ESN-v2 makes that state-estimation problem explicit without introducing any
collision truth.  The control pathway remains independent from the VMC baseline:

```text
fixed Panda WBC
  -> current deployable state plus WBC tracking errors
  -> fixed Fan Ye fast/slow reservoir memory
  -> PPO residual action [slowdown, 6-D yield twist]
  -> shared safety adapter
  -> Panda torque backend
```

## Information contract

All compared actors receive the same current 32-D feature:

`q(7), qdot(7), fixed WBC task twist(6), measured WBC pose error(6), measured WBC twist error(6)`.

The pose error is computed as target-minus-measured translation and rotation
log; the twist error is target-minus-measured end-effector twist.  These are
available from the WBC command and robot proprioception at the controller time
step.  They do not depend on rod contact, contact force, obstacle pose or
geometry, fixture ID, or a future release signal.

The modes are:

| Mode | Online feature | Purpose |
|---|---|---|
| `current_mlp` | current 32-D feature | matched no-memory baseline |
| `fan_ye_esn` | current 32-D feature + frozen v1 64-D Fan Ye state | isolate the effect of legacy reservoir memory after removing missing error state |
| `fan_ye_multiscale_esn` | current 32-D feature + 64-D fast state + 64-D slow state | ESN-v2 proposed algorithm |

The v2 reservoirs are fixed random leaky reservoirs.  They use the existing
Fan Ye-selected spectral-radius/connection family as a **pre-registered initial
candidate**, with distinct causal time constants: 0.040 s for collision loading
and 0.206 s for release/rejoin.  The prior CR/ESPI evidence was computed on the
legacy 20-D input and is not claimed to validate the new 32-D input.  A fresh
32-D CR/ESPI screen is therefore required before any final multi-seed selection.
The reservoirs are not trained, do not receive action feedback, and are reset at
every episode boundary.  The PPO actor is the only learned component.

## Validation sequence

1. Deterministic MuJoCo neutral-action smoke must match fixed WBC exactly for
   all three observation modes.
2. A 32-D input-only CR/ESPI screen selects or rejects the pre-registered
   fast/slow reservoir candidate without using PPO return or validation reward.
3. A paired 100k-step smoke compares `current_mlp` and ESN-v2 on the isolated
   post-V4 development train/validation manifest.
4. Promotion requires full task success, matched no-rod success, at least
   eight effective collisions out of nine validation fixtures, and zero hard
   torque limits in both lanes.
5. Only a promoted setting receives a multi-seed run.  Report task and safety
   gates before recovery RMSE, rejoin latency, contact impulse, jerk, or torque.

The frozen V4 final holdout is excluded from all v2 training, tuning, and model
selection.  The protocol does not claim hardware validation, passivity proof,
or continuous 3-D obstacle coverage.
