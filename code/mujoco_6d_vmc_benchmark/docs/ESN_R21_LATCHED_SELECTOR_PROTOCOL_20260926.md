# ESN sustained-evidence latch protocol R21 (2026-09-26)

R19 exposed a closed-loop distribution shift: on the frozen R15 trajectory,
fixtures 9352 and 9355 have 470 and 529 consecutive positive selector states,
but instantaneous hard switching changes the subsequent trajectory and can
turn the selector off again. The resulting branch chatter does not reproduce
the already verified full-margin response. This diagnosis was completed
before reading any R20 physical result.

R21 fixes one candidate before launch: R18 offset -1.50, threshold 0.5, and
five consecutive positive reservoir decisions (0.20 s) before activation.
Once activated, the margin expert is latched until episode reset. The exposed
R15 negative trajectories have maximum positive runs below five, while 9352
and 9355 exceed the threshold by two orders of magnitude. All weights,
normalization, reservoir dynamics, the existing action filter, downstream
safety filter, physics, task gate, and 0.2 mm penetration gate remain frozen.
Deployment remains proprio48-only; no stage, fixture, geometry, or clock input
is used.

R21 is run only if R20 fails the unchanged eight-condition screen. It must
pass task+strict 8/8 on that screen and 9/9 on the exposed remainder before
the precommitted 9360--9367 blind plan is opened once. All failed rounds and
all three physical metrics are retained.
