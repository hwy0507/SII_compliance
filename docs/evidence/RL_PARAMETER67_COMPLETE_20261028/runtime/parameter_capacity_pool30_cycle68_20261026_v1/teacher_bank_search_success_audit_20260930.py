"""Read-only v10 first successful VMC search-anchor review. No simulation."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

from teacher_bank_pilot_failure_causes_20260930 import analyze_case, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, output = args.run.resolve(), args.output.resolve()
    if output.exists() or output == root or root in output.parents:
        raise ValueError('Require new output directory outside immutable run')
    output.mkdir(parents=True)
    sys.path.insert(0, str(root/'source/tools'))
    spec = importlib.util.spec_from_file_location('frozen_v10_runner', root/'source/tools/teacher_bank_rollout_20260930.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    results = {}
    for anchor in (337, 671):
        folder = root/f'search/active_short/vmc/c00/{anchor}'
        request = json.loads((folder/'request.json').read_text())
        original_audit_hash = sha(folder/'audit.json')
        repeated = runner.audit(root, request, folder, output_path=output/f'{anchor}_replay_audit.json')
        # Separate NumPy calculation, not a call to runner's metric helper.
        independent = analyze_case(folder)
        meta = json.loads((folder/'rollout.json').read_text())
        axis = np.asarray(request['fixture']['axis'], dtype=float)
        with np.load(folder/'rollout_ball_detail.npz', allow_pickle=False) as detail:
            t, v, touch = detail['time'], detail['velocity'], detail['contact'].astype(bool)
            assert touch.any(), 'No saved impact sample'
            last_touch = float(t[touch].max())
            after = (~touch) & (t > last_touch) & (t < last_touch+.12)
            assert after.any(), 'No saved post-impact sample'
            outgoing = v[after]@axis
            incoming = float(np.asarray(meta['ball_incoming_velocity'])@axis)
            rebound = bool(incoming > .05 and np.any(outgoing < -.05))
            detail_evidence = dict(first_saved_contact_s=float(t[touch].min()),
                last_saved_contact_s=last_touch, post_contact_sample_count=int(after.sum()),
                incoming_projected_mps=incoming,
                min_saved_post_contact_projected_mps=float(outgoing.min()),
                rebound_witness=rebound,
                caveat='Outgoing sampled velocities independently witness reversal; incoming is saved evaluator metadata, not independently recreated preceding physical velocity')
        with np.load(folder/'exposure.npz', allow_pickle=False) as exposure:
            peak = float(exposure['contact_runs'][:, -1].max())
        assert repeated['eligible'] and independent['audit']['eligible'] and rebound
        assert repeated['substeps'] == 550000
        assert original_audit_hash == sha(folder/'audit.json')
        results[str(anchor)] = dict(independent=independent, frozen_runner_replay=repeated,
            rebound_detail=detail_evidence, peak_contact_force_from_saved_runs_n=peak,
            evaluator_ball_event=meta['stats']['events']['ball'], original_audit_unchanged=True)
    result = dict(scope='Two successful VMC search anchors only, not locked bank or formal collection',
        comparison_caveat='sphere anchor 0 failed; bank not locked; formal collection count 0',
        run=str(root), script_sha256=sha(Path(__file__)),
        independent_helper_sha256=sha(Path(__file__).with_name('teacher_bank_pilot_failure_causes_20260930.py')),
        frozen_runner_sha256=sha(root/'source/tools/teacher_bank_rollout_20260930.py'),
        checks=dict(independent='SHA256 and NumPy physical metric recomputation, saved rebound witness',
                    repeated_implementation='Frozen runner audit: full VMC state/action/filter replay, observation-time continuity, physical completeness, exposure binding'),
        cases=results)
    path = output/'review.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(path), sha256=sha(path))))


if __name__ == '__main__':
    main()
