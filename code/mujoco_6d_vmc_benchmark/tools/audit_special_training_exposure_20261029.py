"""Describe saved neural exposure and frame weighting; no fitting or test data.

Checks actual schedule contents, not only equality of schedule hashes. Padding
is excluded. A schedule is a trainer receipt, not an independent optimizer
trace; these checks do not establish gradient equivalence or task success.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def inspect_schedule(schedule, train, batch_size, chunk):
    counts = Counter({e: 0 for e in train})
    previous = None
    seen = set()
    complete_epochs = 0
    padded_slots = 0
    for epoch, group, offset, recorded_mass in schedule:
        assert all(type(v) is int for v in (epoch, offset, recorded_mass))
        assert len(group) == batch_size and len(set(group)) == batch_size
        assert all(type(e) is int and e in train for e in group), 'Validation/unknown identity in fitting schedule'
        length = max(train[e]['frames'] for e in group)
        assert 0 <= offset < length and offset % chunk == 0
        if previous is None:
            assert epoch == offset == 0
        else:
            pe, pg, po, pl = previous
            if offset == 0:
                assert po + chunk >= pl, 'Previous batch truncated before boundary'
                if epoch != pe:
                    assert epoch == pe + 1 and seen == set(train), 'Incomplete/duplicate epoch'
                    complete_epochs += 1
                    seen = set()
                else:
                    assert not seen.intersection(group), 'Repeated identity in epoch'
            else:
                assert epoch == pe and group == pg and offset == po + chunk, 'Sequence gap or mixed histories'
        if offset == 0:
            assert not seen.intersection(group)
            seen.update(group)
        mass = 0
        for e in group:
            actual = max(0, min(chunk, train[e]['frames'] - offset))
            counts[e] += actual
            mass += actual
        assert mass == recorded_mass and mass > 0, 'Padding counted as real exposure'
        padded_slots += batch_size * min(chunk, length - offset) - mass
        previous = (epoch, group, offset, length)
    assert previous is not None
    scene = Counter()
    for e, n in counts.items():
        scene[train[e]['scene']] += n
    total = sum(counts.values())
    return dict(updates=len(schedule), complete_epochs_before_terminal_epoch=complete_epochs,
                terminal_epoch=previous[0], terminal_offset=previous[2],
                real_frame_presentations=total, padded_frame_slots=padded_slots,
                per_episode={str(e): dict(identity=train[e]['id'], frames=train[e]['frames'],
                    presentations=n, equivalent_passes=n/train[e]['frames']) for e, n in counts.items()},
                per_scene_presentations=dict(scene),
                per_scene_presentation_fraction={k:v/total for k,v in scene.items()})


def audit(root):
    state, metadata = read(root/'execution.json'), read(root/'data/DATA_COMPLETE.json')
    assert state['status'] == 'complete'
    assert sha(root/'data/training_data.npz') == state['data_sha256'] == metadata['training_data_sha256']
    lineage = metadata['lineage']
    train = {r['episode']:r for r in lineage if r['split'] == 'train'}
    assert len(lineage) == 30 and len(train) == 24
    assert Counter(r['scene'] for r in train.values()) == dict(rod=8, ball=8, corner=8)
    frame_counts = {}
    for split in ('train', 'validation'):
        counts = Counter()
        for row in lineage:
            if row['split'] == split:
                counts[row['scene']] += row['frames']
        frame_counts[split] = dict(frames=dict(counts), total=sum(counts.values()),
                                  fractions={k:v/sum(counts.values()) for k,v in counts.items()})
    rows, cache, schedules = [], {}, {}
    for fit in state['fits']:
        if fit['family'] not in ('mlp_scratch', 'rnn_scratch'):
            continue
        assert fit['status'] == 'complete'
        out = Path(fit['output'])
        assert sha(out/'TRAINING_COMPLETE.json') == fit['metadata_sha256']
        info = read(out/'TRAINING_COMPLETE.json')
        assert info['data_sha256'] == state['data_sha256']
        assert info['global_loss'] and info['raw_slowdown_loss']
        assert info['updates'] == info['selected_update'] == 32000
        digest = sha(out/'schedule.json')
        assert digest == info['schedule_sha256']
        if digest not in cache:
            cache[digest] = inspect_schedule(read(out/'schedule.json'), train, info['batch_size'], info['tbptt_steps'])
        result = cache[digest]
        assert result['updates'] == info['updates']
        assert result['real_frame_presentations'] == info['actual_nonpadding_observations']
        schedules.setdefault(fit['seed'], set()).add(digest)
        rows.append(dict(name=fit['name'], seed=fit['seed'], family=fit['family'],
                         metadata_sha256=fit['metadata_sha256'], schedule_sha256=digest))
    assert len(rows) == 72 and len(schedules) == 3
    assert all(len(v) == 1 for v in schedules.values()), 'Unequal per-seed neural exposure'
    assert all(Counter(r['family'] for r in rows if r['seed'] == seed)
               == dict(mlp_scratch=12, rnn_scratch=12) for seed in schedules)
    return dict(status='saved_training_exposure_verified', created_utc=datetime.now(timezone.utc).isoformat(),
                training=str(root), dataset_sha256=state['data_sha256'],
                metadata_sha256=sha(root/'data/DATA_COMPLETE.json'), execution_sha256=sha(root/'execution.json'),
                frame_weighting=frame_counts, candidates=rows, schedules=cache,
                seed_schedule={str(k): next(iter(v)) for k,v in schedules.items()},
                auditor_sha256=sha(Path(__file__)),
                limitation='Saved schedule and metadata audit only; no optimizer replay, model selection, fitting or physics. '
                    'Per-frame weights imply unequal scene mass for unequal durations. ESN sees each training frame '
                    'in ridge fitting; neural presentations are repeated TBPTT samples, not an equal-compute claim. '
                    'Terminal epoch can be partial. New collection still requires actual qualification and coverage.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    assert not a.output.exists()
    result = audit(a.root.resolve())
    with a.output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(status=result['status'], frame_weighting=result['frame_weighting'],
                         seed_schedule=result['seed_schedule'])), flush=True)
