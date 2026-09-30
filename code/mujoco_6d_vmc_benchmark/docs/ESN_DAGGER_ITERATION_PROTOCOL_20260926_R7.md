# ESN cumulative-reservoir DAgger protocol R7 (2026-09-26)

R6 did not promote a checkpoint. Its beta=0.50 diagnostic leader achieved
task success on 9330 and 9331 and strict success on 9331, while 9332 remained
a task failure. R7 adds exactly the three beta=0.50 closed-loop trajectories
to the cumulative DAgger set.

The fit uses all 18 complete trajectories accumulated through R6. The base is
the R6 beta=0.50 checkpoint, SHA256
`2163bd2f862c65dd87930cc5d0a4c90a973129153fcf7da4640ddd698e7a206c`.
Every sample is retained. Stage 3 weight is 2.0 and proximal ridge is 0.01.
Only the final readout is refit; normalization, heterogeneous-leak reservoir,
first head layer, action projection, safety filter, physics runner, task gate,
and strict 0.2 mm penetration gate remain frozen.

The fixed candidate budget is the unchanged R6 beta=0.50 base, interpolation
coefficients 0.25, 0.50, and 0.75 toward the new aggregate fit, and the new
aggregate fit. The already audited base result may be reused without rerunning
it; the four new candidates are evaluated once on 9330--9332 on the same Spark
snapshot. No coefficient is added after observing results.

Feasibility and selection are unchanged from R6: all three fixtures must pass
both task and strict gate. Among feasible candidates minimize mean physical-
substep RMSE, then peak torque, then peak speed. If none is feasible, no model
is promoted and the diagnostic leader is ranked only for a subsequent DAgger
collection by task count, strict count, and mean endpoint error.

Only a feasible candidate may run the frozen 9340--9345 cross-condition plan.
All six must pass task and strict gate for a simulation robustness result.
