"""Collect completed local analyses and the verified raw-phase archive map."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
from optimize_tool_contact_20261002 import ROOT,sha,write,now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    assert root!=out and root not in out.parents
    receipts=[json.loads(p.read_text()) for p in sorted((root/'archive_receipts').glob('*.json'))]
    by_original={r['local_execution_root']:r for r in receipts}
    phases=[];counts=Counter()
    for p in sorted(root.glob('*/execution.json')):
        state=json.loads(p.read_text());rows=state.get('rows',[])
        if not rows or not any('audit' in r for r in rows):continue
        assert state['status']=='complete' and all(r.get('returncode')==0 for r in rows)
        receipt=by_original[str(p.parent.resolve())]
        assert sha(p.parent/'archive_manifest.json')==receipt['manifest_sha256']
        counts.update(r['category'] for r in rows)
        phases.append(dict(local_phase=str(p.parent),server_phase=receipt['published_evidence'],
            archive_manifest_sha256=receipt['manifest_sha256'],execution_sha256=sha(p),
            rows=[dict(name=r['name'],category=r['category'],task_success=r['audit']['task_success'],
                       strict_success=r['audit']['strict_success'],trace_sha256=r['audit']['trace_sha256']) for r in rows]))
    out.mkdir(parents=True,exist_ok=False)
    for path in root.iterdir():
        if path.is_file() and path.suffix in ('.json','.py'):
            shutil.copy2(path,out/path.name)
        elif path.is_dir() and (path.name.endswith(('_analysis','_diagnosis','_audits')) or path.name=='archive_receipts'):
            shutil.copytree(path,out/path.name,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
    for folder in ('scripts','tools','assets'):
        shutil.copytree(ROOT/folder,out/'delivery_source'/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc','outputs'))
    write(out/'LOCAL_AUDIT_INDEX.json',dict(created_utc=now(),source_sha256=sha(Path(__file__)),
        local_root=str(root),raw_phases=phases,completed_physical_episodes=sum(len(p['rows']) for p in phases),
        counts_by_registered_category=dict(counts),archive_receipts=receipts,
        limitation='Local development only; do not mix local success with native baseline runtime. Raw phases remain in separately hash-verified server directories. Delivery source is later than historical run-specific source.'))
    print(json.dumps(dict(phases=len(phases),physical_episodes=sum(len(p['rows']) for p in phases))))


if __name__=='__main__':main()
