# ESN reservoir-evidence debounce protocol R20 (2026-09-26)

R19 showed that a binary margin selector can still transfer risk when an
isolated false-positive state triggers the full margin expert. A fixed
run-length audit on all exposed R15 trajectories found, for R18 offset -1.50,
maximum negative positive-runs of two control steps on 9330, four on 9342,
and one on 9344. In contrast, target conditions 9352 and 9355 contain
continuous positive runs of 470 and 529 steps.

Before physical launch, R20 fixes one candidate: R18 offset -1.50 with binary
threshold 0.5 and five consecutive positive reservoir-state decisions before
activating the margin expert. Five 25 Hz steps equal 0.20 s. A negative
decision immediately returns to the complete frozen R15 base policy; both
branches still pass through the existing action filter. Offset -1.50 is used
because it has the highest TPR among candidates whose observed negative runs
are shorter than five. No weights, experts, physics, gates, or safety limits
are changed.

R20 must pass task+strict 8/8 on the unchanged exposed screen, then 9/9 on the
exposed remainder, before the hash-frozen 9360--9367 blind plan runs once.
Deployment remains proprio48-only, and all failed rounds remain reported.
