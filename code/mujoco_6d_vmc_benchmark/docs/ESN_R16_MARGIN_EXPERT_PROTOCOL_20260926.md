# ESN R16 margin-expert protocol (2026-09-26)

The frozen R11 yield and R8 gain-1.5 clearance experts both retain task
success on exposed fixtures 9352 and 9355. Full clearance passes 9355 at
0.196086 mm but misses 9352 at 0.202617 mm; yield misses both at 0.201733 and
0.210417 mm. This shows that R16 needs both better condition separation and a
slightly stronger margin expert.

Before launch, two deterministic margin-expert candidates are fixed. Starting
from the frozen R8 gain-1.5 clearance checkpoint, multiply only final readout
logits for residual channels 1:7 by 1.10 or 1.20. Channel 0, the reservoir,
normalization, first readout layer, temporal filter, safety filter, physics,
task gate, and 0.2 mm penetration gate remain unchanged. Both candidates run
on the already exposed 9352/9355 diagnostic plan. All four results are kept.

A margin expert is feasible only if task+strict is 2/2. Feasible experts may
then be combined with the frozen yield expert using a reservoir-hidden-state
gate trained on exposed trajectories. No result in this protocol is blind or
sufficient for promotion.
