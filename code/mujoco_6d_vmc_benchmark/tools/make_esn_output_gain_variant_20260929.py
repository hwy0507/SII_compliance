"""Create a pure canonical48 ESN output-gain ablation.

The reservoir, readout weights, observation contract and action limits remain
unchanged.  Only the already-supported scalar output gain is frozen to a
declared value; deployment always uses hybrid-vmc-blend=0.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--gain', type=float, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise FileExistsError(a.output)
    if not np.isfinite(a.gain) or not 0.0 < a.gain <= 1.0:
        raise ValueError('gain must be in (0,1]')
    with np.load(a.base, allow_pickle=False) as z:
        if str(z['contract']) != 'proprio48_esn128_action7_v1':
            raise ValueError('canonical pure ESN contract required')
        ck = {k: z[k].copy() for k in z.files}
    ck['output_gain'] = np.float64(a.gain)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(a.output, **ck)
    meta = {
        'method': 'frozen_pure_esn_output_gain_ablation',
        'base': str(a.base), 'base_sha256': sha(a.base), 'gain': a.gain,
        'deployment_contract': 'pure ESN; hybrid_vmc_blend=0',
        'forbidden_inputs': ['contact truth', 'ball state', 'event time',
                             'task stage', 'visual/range', 'geometry'],
        'output_sha256': sha(a.output),
    }
    a.output.with_suffix('.json').write_text(json.dumps(meta, indent=2) + '\n')
    print(json.dumps(meta, indent=2))


if __name__ == '__main__':
    main()
