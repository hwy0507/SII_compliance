"""Compare fixed ball training identities against an audited finite control.

Plots use saved full-physics traces, exact actor replay, same identity/seed/MJB.
No validation traces, fitting, simulated predictions, or new physics.
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from collect_special_scene_actions_20261028 import read, sha, write
from intent_recovery_teacher_20261029 import make_teacher


def compare(collection, controls, output):
    assert not output.exists()
    plan = read(collection/'COLLECTION_PLAN.json')
    reg, review = [read(controls/name) for name in ('REGISTRATION.json', 'REVIEW.json')]
    assert review['execution_sha256'] == sha(controls/'execution.json')
    assert review['registration_sha256'] == sha(controls/'REGISTRATION.json')
    rows = []
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    for ax, identity in zip(axes, ('ball_00', 'ball_01', 'ball_04')):
        entry = next(e for e in plan['episodes'] if e['id'] == identity)
        case = next(c for c in reg['cases'] if c.get('identity') == identity)
        assert entry['split'] == 'train'
        assert entry['seed'] == case['seed'] and entry['scene_parameters'] == case['scene_parameters']
        for label, folder in (('original_v6', Path(entry['folder'])),
                              ('candidate', controls/case['id']/'ball')):
            qualification = read(folder/'DEMONSTRATION_QUALIFICATION.json')
            for name, digest in qualification['input_hashes'].items():
                assert sha(folder/name) == digest
            assert qualification['input_hashes']['scene.mjb'] == case['expected_model_sha256']
            actor = make_teacher(read(folder/'teacher.json'))
            with np.load(folder/'trajectory.npz', allow_pickle=False) as trace, np.load(folder/'legacy.npz', allow_pickle=False) as legacy:
                predictions = []
                for observation in trace['observation']:
                    actor.observe(observation)
                    predictions.append(actor.act(observation[39:45]))
                np.testing.assert_array_equal(predictions, trace['action'])
                time = trace['time']
                np.testing.assert_allclose(np.diff(time), .04, rtol=0, atol=2e-11)
                speed = np.linalg.norm(np.diff(legacy['object_position'], axis=0)/.04, axis=1)
                row = dict(identity=identity, setting=label, qualification=qualification['status'],
                    original_tail_speed_max_mps=float(speed[-9:].max()),
                    last10s_speed_rms_mps=float(np.sqrt(np.mean(speed[-250:]**2))),
                    last10s_speed_max_mps=float(speed[-250:].max()),
                    actor_replay_max_abs=0., folder=str(folder),
                    inputs={name:sha(folder/name) for name in ('DEMONSTRATION_QUALIFICATION.json', 'trajectory.npz', 'legacy.npz', 'teacher.json')})
                rows.append(row)
                ax.plot(time[1:], speed, lw=.9, label=f"{label} ({qualification['status']})")
        ax.axhline(.02, color='red', ls='--', lw=.8)
        ax.axvspan(time[-10], time[-1], color='green', alpha=.13)
        ax.set_title(identity+' (training identity)')
        ax.set_xlim(20, 30); ax.set_ylim(bottom=0); ax.grid(alpha=.2)
        ax.set_ylabel('Object speed (m/s)'); ax.legend(fontsize=8)
    axes[-1].set_xlabel('Saved physical time (s)')
    fig.suptitle('Actual paired physics: last 10 s; green = original end-window qualification\nRed threshold applies to the end window only; teacher controls, not student results', fontsize=11)
    fig.tight_layout()
    output.mkdir(parents=True)
    fig.savefig(output/'paired_ball_speed.png', dpi=160); plt.close(fig)
    result = dict(status='complete', physics_steps=0, rows=rows,
        controls_all_six_qualified=review['all_six_qualified'],
        collection_plan_sha256=sha(collection/'COLLECTION_PLAN.json'),
        control_review_sha256=sha(controls/'REVIEW.json'), source_sha256=sha(Path(__file__)),
        plot_sha256=sha(output/'paired_ball_speed.png'),
        limitation='Fixed original training identities only. No unseen-test, closed-loop stability, student learning or repaired108 claim. End-window gate and whole-tail diagnostics remain distinct.')
    write(output/'REVIEW.json', result)
    print(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('collection', 'controls', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    compare(args.collection.resolve(), args.controls.resolve(), args.output.resolve())
