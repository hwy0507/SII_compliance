# ESN hierarchical hard-selector protocol R19 (2026-09-26)

R18 showed that a soft second-level selector transfers margin-expert action to
negative conditions even below probability 0.5, while positive conditions do
not receive the full margin response. R19 changes only that blend operation:
selector probability below 0.5 uses the complete frozen R15 base logits;
probability at least 0.5 uses the complete frozen 1.10 margin-expert logits.
The existing checkpoint action filter remains active, so commanded action is
still temporally smoothed.

Before launch, R19 fixes two variants: hard conversions of R18 offsets -1.50
and -1.75. They are the two calibration endpoints with the useful TPR/FPR
tradeoff: -1.50 has TPR 0.9791/FPR 0.00775, while -1.75 has TPR 0.9659/FPR
0.00676. No weights are retrained and all offline admission gates remain
satisfied. Offset -1.25 is not carried forward because it has the highest
admitted FPR (0.00943) and no compensating expert or task-capability change.

Both candidates run the unchanged eight-condition exposed screen. A candidate
must achieve task+strict 8/8, then task+strict 9/9 on the exposed remainder,
before the frozen 9360--9367 blind plan may run once. Physics, environment,
safety filter, task gate, and 0.2 mm penetration gate remain unchanged.
