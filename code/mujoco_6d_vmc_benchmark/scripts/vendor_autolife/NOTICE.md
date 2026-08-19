# Vendored `autolife_planning` (unmodified subset)

Provenance:
- Upstream: https://github.com/AdaCompNUS/Autolife-Planning (AdaComp NUS)
- Consumed via: `autolife-planning==0.3.4` wheel from PyPI (also the dependency
  of https://github.com/AdaCompNUS/Prepose-Sampler, `>=0.3.2,<0.4`)
- Extracted files: `kinematics/{pink_ik_solver,ik_solver_base,collision_model,pinocchio_fk,__init__}.py`,
  `types/*.py`, `utils/{rot_utils,__init__}.py`, `autolife.py`, `__init__.py`
- NO modifications of any kind. The only omission is modules not needed for the
  Pink differential-IK WBC (`planning/`, `trajectory/`, `envs/`, compiled
  `toppra` bindings, which are also x86_64-only).

Why vendored: the published wheels are x86_64-only while our compute server is
aarch64; the WBC modules used here are pure Python on top of `pin`/`pin-pink`,
which are multi-arch on PyPI.

License: the wheel ships no top-level license file (only
`licenses/third_party/toppra/LICENSE`). Upstream repo and wheel are public on
PyPI/GitHub. Kept for research use with this attribution notice.
