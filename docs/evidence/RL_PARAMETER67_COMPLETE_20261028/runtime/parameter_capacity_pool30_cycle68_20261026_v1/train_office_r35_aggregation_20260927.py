"""One fixed-budget readout refit on all declared development histories."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def main():
    traces = sorted((ROOT / 'training_traces').glob('*.npz'))
    if len(traces) != 14:
        raise ValueError('Expected five original, six R34 and three reset histories')
    subprocess.run([sys.executable, str(ROOT / 'tools/train_office_vmc_memory_esn_20260927.py'),
                    '--output', str(ROOT / 'r35_training'), '--seed', '20260927',
                    '--axis-separable', '--nonlinear-updates', '3200',
                    '--reservoir-checkpoint', str(ROOT / 'models/r34.npz'), '--development-trace',
                    *map(str, traces)], check=True, cwd=ROOT)
    subprocess.run([sys.executable, str(ROOT / 'tools/make_office_gain_candidate_20260927.py'),
                    '--parent', str(ROOT / 'r35_training/model.npz'),
                    '--output', str(ROOT / 'models/r35/model.npz'), '--gain', '.5'], check=True, cwd=ROOT)
    with np.load(ROOT / 'models/r34.npz') as parent, np.load(ROOT / 'models/r35/model.npz') as child:
        for key in ('win', 'w', 'leak', 'scale', 'output_gain'):
            np.testing.assert_array_equal(parent[key], child[key])
    record = dict(purpose='fixed-budget development-history aggregation, no blind data',
                  reservoir_and_output_gain_unchanged=True, training_updates=3200, seed=20260927,
                  source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  input_trace_sha256={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in traces},
                  parent_sha256=hashlib.sha256((ROOT / 'models/r34.npz').read_bytes()).hexdigest(),
                  checkpoint_sha256=hashlib.sha256((ROOT / 'models/r35/model.npz').read_bytes()).hexdigest(),
                  caveat='Updated readout uses developer-exposed failures and successes. Subsequent six-case runs are development regression, not independent validation.')
    (ROOT / 'r35_training/aggregation_manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    main()
