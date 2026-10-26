"""Review saved finite temperature-probe evidence; no neural/dynamics rerun."""
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main(root):
    os.sched_setaffinity(0, {53})
    deadline = time.monotonic()+3600
    while not (root/'REVIEW.json').exists():
        assert not (root/'FAILURE.json').exists(), 'Original probe failed; do not repeat arms'
        assert time.monotonic() < deadline, 'Timed out waiting for original finite probe'
        time.sleep(5)
    reg = json.loads((root/'REGISTRATION.json').read_text())
    report = json.loads((root/'REVIEW.json').read_text())
    assert report['passed'] and report['formal_default_matmul_precision']
    assert report['new_physics'] == 0 and not report['weights_saved'] and not report['formal_deployment']
    assert report['original_checkpoint_and_replay_unchanged']
    for key in ['checkpoint', 'cycle_review', 'health_review', 'training_registration', 'implementation_gate', 'gate_decision']:
        assert sha(reg[key]['path']) == reg[key]['sha256'], key
    for ref in reg['sources'].values():
        assert sha(ref['path']) == ref['sha256']
    gate = json.loads(Path(reg['implementation_gate']['path']).read_text())
    arms = report['results']
    assert [arm['arm'] for arm in arms] == ['derived_next32', 'raw_next1']
    equal_fields = ['initial', 'initial_learner_digest', 'initial_replay_digest', 'sampled_rows_sha256',
        'final_sample_rng_digest', 'final_agent_rng_digest']
    for key in equal_fields:
        assert arms[0][key] == arms[1][key], key
    assert arms[0]['initial_learner_digest'] == gate['initial_learner_digest']
    assert arms[0]['initial_replay_digest'] == gate['replay_digest']
    def finite(value):
        if isinstance(value, dict):
            for v in value.values(): finite(v)
        elif isinstance(value, list):
            for v in value: finite(v)
        elif isinstance(value, float):
            assert math.isfinite(value)
    for arm in arms:
        assert arm == json.loads((root/(arm['arm']+'_RESULT.json')).read_text())
        for key, value in [('outer_updates', 2000), ('critic_updates', 16000), ('actor_updates', 2000), ('temperature_updates', 2000)]:
            assert arm[key] == value
        assert not arm['weights_saved']
        assert [p['outer_updates'] for p in arm['points']] == list(range(200, 2001, 200))
        for point in arm['points']:
            assert point['critic_updates'] == 8*point['outer_updates']
            assert point['temperature'] > 0 and point['terminal_mae'] >= 0 and point['td32_mae'] >= 0
        finite(arm)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 3, figsize=(15, 8), constrained_layout=True)
    keys = ['temperature', 'initial_entropy', 'raw_next1_entropy', 'terminal_mae', 'td32_mae', 'initial_public0_mode_mean']
    for arm in arms:
        points = [dict(arm['initial'], outer_updates=0)]+arm['points']
        for axis, key in zip(axes.flat, keys):
            axis.plot([p['outer_updates'] for p in points], [p[key] for p in points], marker='.', label=arm['arm'])
            axis.set(title=key, xlabel='Offline outer updates'); axis.grid(alpha=.25)
    axes[0, 0].legend()
    fig.suptitle('Same formal14 full state and row draws; no new physics or task-success evaluation')
    plot=root/'temperature_successor_comparison.png'; fig.savefig(plot, dpi=140); plt.close(fig)
    changes = {key:dict(control=arms[0]['points'][-1][key], candidate=arms[1]['points'][-1][key],
        candidate_minus_control=arms[1]['points'][-1][key]-arms[0]['points'][-1][key]) for key in keys}
    write(root/'INDEPENDENT_REVIEW.json', dict(time=time.time(), passed=True, equal_fields=equal_fields,
        checkpoint=reg['checkpoint'], report_sha256=sha(root/'REVIEW.json'), plot_sha256=sha(plot),
        source_sha256=sha(__file__), endpoint_comparison=changes,
        scope='Independent saved-report/full-budget/digest/source-hash and finite-number checks plus plot. Does not recompute neural inference, gradients, draws, or dynamics; these remain original probe assertions. No formal deployment decision.'))
    write(root/'FINISHED.json', dict(time=time.time(), completed=True, convergence_claim=False))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args=parser.parse_args()
    try:
        main(args.run)
    except BaseException as error:
        write(args.run/'INDEPENDENT_REVIEW_FAILURE.json', dict(time=time.time(), error=repr(error)))
        raise
