"""Read-only progress/checkpoint evidence; never starts, stops or resumes jobs."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def inspect(root,training_subdir=Path('training')):
    report={}
    for mode in ('parameter6','direct7'):
        path=root/training_subdir/mode
        row=dict(mode=mode,progress=json.loads((path/'progress.json').read_text()),checkpoints=[])
        for metadata in sorted((path/'checkpoints').glob('step_*.json')):
            # Metadata is written only after both model and normalizer saves.
            data=json.loads(metadata.read_text());model=metadata.with_suffix('.zip')
            normalizer=metadata.with_name(metadata.stem+'_vecnormalize.pkl')
            digest=sha(model)
            if digest!=data['checkpoint_sha256']:raise ValueError('Checkpoint digest mismatch')
            with zipfile.ZipFile(model) as archive:model_data=json.loads(archive.read('data'))
            if model_data['num_timesteps']!=data['timesteps'] or model_data['_n_updates']!=data['updates']:
                raise ValueError('Checkpoint budget/update mismatch')
            row['checkpoints'].append(dict(timesteps=data['timesteps'],updates=data['updates'],
                model_sha256=digest,normalizer_sha256=sha(normalizer),metadata_sha256=sha(metadata)))
        for name in ('COMPLETE.json','FAILED.json'):
            if (path/name).exists():row[name]=json.loads((path/name).read_text())
        report[mode]=row
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--training-subdir',type=Path,default=Path('training'))
    args=parser.parse_args();print(json.dumps(inspect(args.root,args.training_subdir),indent=2))
