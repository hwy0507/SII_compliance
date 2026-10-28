"""Copy frozen candidates and exact source to a fresh server-addressed bundle.

The resulting paths are intended destinations, not a claim of upload. Publish
and verify with archive_paper_phase before launching any server evaluation.
"""
import argparse,json,shutil
from pathlib import Path
from optimize_tool_contact_20261002 import ROOT,sha,write,now

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifests',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--server-root',type=Path,required=True)
    a=p.parse_args()
    assert str(a.server_root).startswith('/home/arm1/sii_shared/SII_compliance/runs/main/paper_esn_12h_')
    out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    rows=[];mapping=[]
    for manifest in a.manifests:
        for original in json.loads(manifest.read_text())['candidates']:
            row=dict(original);name=row['name']
            assert Path(name).name==name and name not in ('.','..') and name not in [r['name'] for r in rows]
            if row.get('checkpoint'):
                checkpoint=Path(row['checkpoint']);assert sha(checkpoint)==row['checkpoint_sha256']
                target=out/'models'/name;target.mkdir(parents=True)
                shutil.copy2(checkpoint,target/'checkpoint.npz')
                metadata=checkpoint.parent/'TRAINING_COMPLETE.json'
                if metadata.exists():shutil.copy2(metadata,target/'TRAINING_COMPLETE.json')
                row['checkpoint']=str(a.server_root/'models'/name/'checkpoint.npz')
                mapping.append(dict(name=name,local_checkpoint=str(checkpoint.resolve()),server_checkpoint=row['checkpoint'],sha256=row['checkpoint_sha256']))
            rows.append(row)
    assert len(rows)<=48
    for folder in ('scripts','tools','assets'):
        shutil.copytree(ROOT/folder,out/'source'/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
    write(out/'manifest.json',dict(created_utc=now(),candidates=rows,
        upstream_manifests=[dict(path=str(p.resolve()),sha256=sha(p)) for p in a.manifests]))
    write(out/'execution.json',dict(status='complete',completed_utc=now(),preparation_source_sha256=sha(Path(__file__)),
        server_upload_verified=False,intended_server_root=str(a.server_root),mapping=mapping,
        purpose='Frozen development candidates; not final heldout model lock. Archive receipt is separate.'))
    print(json.dumps(dict(candidates=len(rows),bundle=str(out))))

if __name__=='__main__':main()
