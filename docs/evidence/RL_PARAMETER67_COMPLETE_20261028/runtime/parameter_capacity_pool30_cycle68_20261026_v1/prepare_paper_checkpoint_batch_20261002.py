"""Freeze explicitly named learned checkpoints into a sequential manifest."""
import argparse
import json
from pathlib import Path
from optimize_tool_contact_20261002 import sha, write, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--names', nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--memory-ablation',choices=('none','reset_each_observation'),default='none')
    a = p.parse_args()
    if a.output.exists(): raise FileExistsError(a.output)
    rows=[]
    for name in a.names:
        assert Path(name).name == name and name not in ('.', '..')
        root = (a.root/name).resolve()
        metadata = json.loads((root/'TRAINING_COMPLETE.json').read_text())
        checkpoint = root/'checkpoint.npz'
        assert sha(checkpoint) == metadata['checkpoint_sha256']
        rows.append(dict(name=name, category='mlp_rnn_development' if name.startswith('paired_') else 'esn_development',
                         checkpoint=str(checkpoint), checkpoint_sha256=sha(checkpoint)))
        if a.memory_ablation!='none':
            assert not name.startswith('paired_')
            rows[-1].update(name=name+'_reset_each_observation',memory_ablation=a.memory_ablation)
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),candidates=rows))


if __name__ == '__main__': main()
