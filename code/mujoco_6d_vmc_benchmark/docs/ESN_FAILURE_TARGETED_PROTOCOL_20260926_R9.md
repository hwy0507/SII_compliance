# ESN failure-targeted reservoir protocol R9 (2026-09-26)

R8 gain=1.0 completes the task on 9330--9332 and passes the strict gate on
9331--9332, but its global loaded-lift shaping pushes fixture 9330 to 0.2041 mm
penetration. R9 keeps the validated gain and removes shaping from histories
that did not demonstrate the 9332 failure mode.

The base checkpoint is R7 aggregate, SHA256
`a122da8e677867bbc3b6c9c7ddfae7cf80c691ec329a745570b4f63812f18051`.
All 18 cumulative trajectories remain in the fit. Progress shaping with gain
1.0 per metre, deadband 0.012 m, and maximum action 0.30 is applied only to the
four archived 9332 failure trajectories collected under R2, R4, R5, and the
R6 beta=0.50 leader. All other trajectory labels are the unchanged fixed VMC
labels. Every sample is retained.

Only the final readout is fit, with loaded-stage weight 2.0 and proximal ridge
0.01. Normalization, heterogeneous-leak reservoir, first head layer, output
smoothing, action projection, safety filter, runner, task gate, and strict
0.2 mm penetration gate remain frozen. Deployment input remains the original
48-D proprioceptive contract; stage labels, clocks, geometry, and fixture IDs
are not available to the policy.

R9 has one checkpoint and one evaluation on fixtures 9330--9332. Promotion
requires task+strict 3/3. Only then may it run the frozen 9340--9345 cross-
condition evaluation, where all six must pass task and strict gate.
