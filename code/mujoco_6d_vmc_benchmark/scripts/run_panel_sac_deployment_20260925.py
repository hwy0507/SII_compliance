"""Explicit SAC deployment entry retaining the original panel/WBC/metrics chain."""
import argparse
import json
import os
from pathlib import Path
import sys
os.environ.update(OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')
import numpy as np


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--sac-branch', choices=('online_only', 'demo_prefill'), required=True)
    parser.add_argument('--training-directory', type=Path, required=True)
    parser.add_argument('--deployment-device', choices=('cuda',), default='cuda')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mixture', type=float, default=0.)
    args, remaining = parser.parse_known_args()
    if args.mixture != 0. or '--model' in remaining or '--settle-only' in remaining:
        raise ValueError('Require unchanged task and pure frozen SAC deployment')
    if os.environ.get('UNIFIED_6D_TEACHER') != '1':
        raise ValueError('Canonical48 observation required')
    from canonical48_sac_deployment_20260925 import load_policy, sha
    import current_student_policy_20260921 as loader
    policy, metadata = load_policy(args.training_directory, args.sac_branch, args.deployment_device)
    metadata['runtime_fixture_CORE_VMC_CONFIG'] = json.loads(os.environ['CORE_VMC_CONFIG'])
    metadata['source_sha256'][Path(__file__).name] = sha(__file__)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.with_suffix('.paired_deployment.json').write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n')
    original = loader.load_current
    token = 'sac_frozen_policy_in_memory'

    def load(path):
        if str(path) != token:
            raise ValueError('Unexpected policy load target')
        policy.reset()
        return policy

    loader.load_current = load
    sys.argv = [sys.argv[0], *remaining, '--output', str(args.output), '--mixture', '0', '--model', token]
    try:
        from run_panel_push_20260920 import main as run
        run()
    finally:
        loader.load_current = original
        try:
            np.savez_compressed(args.output.parent / 'paired_policy_trace.npz', **{k: np.asarray(v) for k, v in policy.log.items()})
        finally:
            policy.close()


if __name__ == '__main__':
    main()
