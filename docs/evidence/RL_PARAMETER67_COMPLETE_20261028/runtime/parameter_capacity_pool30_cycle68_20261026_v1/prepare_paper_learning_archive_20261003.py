"""Snapshot every completed/failed student fit and dataset, without selection."""
import argparse
import json
from pathlib import Path
import shutil
from optimize_tool_contact_20261002 import ROOT, sha, write, now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    assert root!=out and root not in out.parents, 'Use a sibling archive staging directory'
    selected=[]
    for path in sorted(root.iterdir()):
        if not path.is_dir():continue
        meta=path/'TRAINING_COMPLETE.json';data=path/'training_data.npz';execution=path/'execution.json'
        state=json.loads(execution.read_text()) if execution.exists() else {}
        failed_fit=state.get('status')=='failed_preserved' and 'train' in str(state.get('argv',[''])[0])
        queue=path.name.endswith('_training') and execution.exists()
        if not (meta.exists() or data.exists() or failed_fit or queue):continue
        assert state.get('status') in ('complete','failed_preserved') or (not execution.exists()), str(path)
        if meta.exists():
            metadata=json.loads(meta.read_text())
            assert sha(path/'checkpoint.npz')==metadata['checkpoint_sha256']
        selected.append(path)
    assert selected
    out.mkdir(parents=True,exist_ok=False);mapping=[]
    for path in selected:
        shutil.copytree(path,out/path.name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
        mapping.append(dict(original=str(path),archive_relative=path.name,
                            execution_sha256=sha(path/'execution.json') if (path/'execution.json').exists() else None))
    for folder in ('scripts','tools','assets'):
        shutil.copytree(ROOT/folder,out/'delivery_source'/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
    write(out/'LEARNING_INDEX.json',dict(created_utc=now(),source_sha256=sha(Path(__file__)),
        original_root=str(root),directories=mapping,
        meaning='All top-level student fits, failed exports, datasets and frozen offline queues. Includes obsolete/unsuccessful variants; does not label every checkpoint valid for deployment. source_overlay and per-fit execution retain actual provenance; delivery_source is a later code snapshot.'))
    print(json.dumps(dict(directories=len(mapping),output=str(out))))


if __name__=='__main__':main()
