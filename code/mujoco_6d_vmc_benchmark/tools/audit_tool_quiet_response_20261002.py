"""Offline memory/load interventions on recorded observations, not physics."""
import argparse
from pathlib import Path
import shutil
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, a.output/Path(__file__).name)
    checkpoint = a.run/'checkpoint.npz'
    models = [OfficeVMCMemoryESN(checkpoint) for _ in range(3)]
    with np.load(a.run/'rollout.npz') as z:
        observations, time, original = [z[k] for k in ('observation', 'time', 'applied_action')]
    predictions = []
    for o, t in zip(observations, time):
        models[1].reset()
        zeroed = o.copy()
        if t >= 40:
            zeroed[39:45] = 0.
        predictions.append([models[0].act(o), models[1].act(o), models[2].act(zeroed)])
    predictions = np.asarray(predictions)
    np.testing.assert_array_equal(predictions[:, 0], original)
    late = time >= 40
    np.savez_compressed(a.output/'offline_interventions.npz', time=time, prediction=predictions)
    names = ['recorded_history_exact_replay', 'reset_before_each_observation', 'wrench_zero_after_40s']
    write(a.output/'QUIET_RESPONSE_AUDIT.json', dict(
        created_utc=now(), checkpoint_sha256=sha(checkpoint), trace_sha256=sha(a.run/'rollout.npz'),
        source_sha256=sha(Path(__file__)), evidence_sha256=sha(a.output/'offline_interventions.npz'),
        late_wrench_median=np.median(observations[late, 39:45], axis=0).tolist(),
        late_action_median={name: np.median(predictions[late, i], axis=0).tolist() for i, name in enumerate(names)},
        final_action={name: predictions[-1, i].tolist() for i, name in enumerate(names)},
        limitation='Offline actions on the same recorded observations; altered actions are not executed and do not imply closed-loop improvement. Time selects only an analysis intervention, never an actor input.'))
    print(str(a.output/'QUIET_RESPONSE_AUDIT.json'))


if __name__ == '__main__':
    main()
