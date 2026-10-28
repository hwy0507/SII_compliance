"""Interleave frozen candidate lists without changing or filtering candidates."""
import argparse
import json
from pathlib import Path
from itertools import zip_longest
from optimize_tool_contact_20261002 import sha,write,now

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--inputs',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    lists=[json.loads(path.read_text())['candidates'] for path in a.inputs]
    rows=[row for group in zip_longest(*lists) for row in group if row is not None]
    assert len({r['name'] for r in rows})==len(rows)
    assert len(rows)<=48
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),
        input_manifests=[dict(path=str(p.resolve()),sha256=sha(p)) for p in a.inputs],candidates=rows))

if __name__=='__main__':main()
