"""Final three predeclared student slots: two gains and a memory intervention."""
import argparse
from pathlib import Path
import shutil
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    a.output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, a.output/Path(__file__).name)
    with np.load(a.parent, allow_pickle=False) as z:
        base = {k: z[k].copy() for k in z.files}
    if float(base.get('output_gain', 1.)) != 1.:
        raise ValueError('Registered parent must use unscaled output')
    batch = dict(protocol='fixed_tool_contact_four_hour_20261002', registered_before_rollouts=True,
                 purpose='Final bounded residual-gain calibration plus causal memory intervention; no new teacher or world changes',
                 parent_checkpoint_sha256=sha(a.parent), registered_utc=now(), contact_audit=True,
                 candidates={}, checkpoint_by_candidate={}, memory_ablation_by_candidate={})
    for name, gain in [('gain075', .75), ('gain050', .5)]:
        path = a.output/name
        path.mkdir()
        model = dict(base, output_gain=np.asarray(gain))
        checkpoint = path/'checkpoint.npz'
        np.savez_compressed(checkpoint, **model)
        teacher = OfficeVMCMemoryESN(a.parent)
        actor = OfficeVMCMemoryESN(checkpoint)
        rng = np.random.default_rng(2026100208)
        for _ in range(100):
            obs = rng.normal(0, .2, 48)
            obs[39:45] *= 20
            np.testing.assert_array_equal(actor.act(obs), teacher.act(obs)*gain)
            np.testing.assert_array_equal(actor.state, teacher.state)
        write(path/'CALIBRATION.json', dict(parent=str(a.parent.resolve()), parent_sha256=sha(a.parent),
              checkpoint_sha256=sha(checkpoint), output_gain=gain, reservoir_unchanged=True,
              source_sha256=sha(Path(__file__)), limitation='Seen-world gain calibration; not physical success or independently held-out tuning'))
        batch['candidates'][name] = {}
        batch['checkpoint_by_candidate'][name] = str(checkpoint.resolve())
    batch['candidates']['reset_each_observation'] = {}
    batch['checkpoint_by_candidate']['reset_each_observation'] = str(a.parent.resolve())
    batch['memory_ablation_by_candidate']['reset_each_observation'] = 'reset_each_observation'
    batch['memory_ablation_limitation'] = 'Same trained weights with state reset before every observation; a causal intervention, not a retrained/matched MLP baseline'
    write(a.output/'batch.json', batch)
    print(str(a.output/'batch.json'))


if __name__ == '__main__':
    main()
