# ESN R16 expert diagnostic (2026-09-26)

Before launch, this diagnostic fixes two already exposed R15 failures (9352
and 9355) and two frozen checkpoints: the R11 weight-2 yield expert and R8
gain-1.5 clearance expert. The resulting four runs distinguish gate
misclassification from expert insufficiency without opening a new condition.

The runner, physics, task gate, 0.2 mm penetration gate, and safety filter are
unchanged. Every rollout is retained. These diagnostic results cannot promote
a checkpoint and cannot be described as blind evaluation.
