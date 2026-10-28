"""Read-only model comparison; never steps or recompiles either model."""
import argparse
import hashlib
import json
from pathlib import Path

import mujoco
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("old", type=Path)
    parser.add_argument("new", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    loaded, load_errors = [], {}
    for p in (args.old, args.new):
        try:
            loaded.append(mujoco.MjModel.from_binary_path(str(p)))
        except ValueError as exc:
            loaded.append(None)
            load_errors[str(p)] = str(exc)
    a, b = loaded
    differences, checked = {}, []
    groups = [] if load_errors else [("model", a, b), ("option", a.opt, b.opt)]
    for group, x, y in groups:
        for key in dir(x):
            if key.startswith("_"):
                continue
            v, w = getattr(x, key), getattr(y, key)
            if isinstance(v, np.ndarray):
                checked.append(f"{group}.{key}")
                if not np.array_equal(v, w, equal_nan=True):
                    differences[f"{group}.{key}"] = {
                        "shape_old": list(v.shape), "shape_new": list(w.shape),
                        "max_abs": float(np.max(np.abs(v.astype(float)-w.astype(float)))) if v.shape == w.shape and v.size else None,
                    }
            elif isinstance(v, (str, bytes, int, float)):
                checked.append(f"{group}.{key}")
                if v != w:
                    differences[f"{group}.{key}"] = {"old": repr(v), "new": repr(w)}
    report = {
        "runtime_mujoco_version": mujoco.__version__,
        "files": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in (args.old, args.new)],
        "checked": checked, "differences": differences,
        "load_errors": load_errors,
        "comparison_completed": not bool(load_errors),
        "scope": "Python-exposed scalar/array model fields and physics options; not all binary internals or original runtime identity.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"version": mujoco.__version__, "fields_checked": len(checked), "differences": differences, "load_errors": load_errors}))


if __name__ == "__main__":
    main()
