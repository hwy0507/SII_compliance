# ESN hierarchical selector calibration R18 (2026-09-26)

R17's fixed offsets bracketed the offline admission boundary but none passed
all four gates. Offset -1 had TPR 0.9907 and positive p05 0.7277 but FPR
0.01190; offset -2 had FPR 0.00508 but TPR 0.9469 and positive p05 0.4957.
No R17 checkpoint entered a physical screen.

R18 is a fixed-budget threshold calibration, not a weight refit. Before
computing results, selector offsets -1.25, -1.50, and -1.75 are fixed. Each is
derived from the exact R17 zero-offset checkpoint; every weight, both experts,
both gate networks, reservoir, normalization, and action filtering remain
bitwise unchanged. Offline admission remains TPR >= 0.95, FPR <= 0.01,
positive p05 > 0.5, and negative p95 < 0.5.

Every admitted candidate runs the unchanged R17 eight-condition screen.
Feasibility requires task+strict 8/8. Any winner must then pass the remaining
nine exposed conditions before the hash-frozen 9360--9367 blind plan can run
once. Physics, task gate, and the 0.2 mm penetration gate are unchanged.
