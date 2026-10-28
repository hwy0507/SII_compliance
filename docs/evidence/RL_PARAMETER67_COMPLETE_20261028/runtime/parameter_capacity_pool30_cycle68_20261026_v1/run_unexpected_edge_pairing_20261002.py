"""Four sequential development rows under one resource-limited service."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    expected=None
    for name,method,clear in [('nominal_clear','nominal',True),('nominal_blocked','nominal',False),('esn_blocked','esn',False),('mlp_blocked','mlp',False)]:
        run=a.output/name
        cmd=[sys.executable,str(ROOT/'tools/run_unexpected_edge_20261002.py'),'--method',method,'--output',str(run)]
        if clear:cmd+=['--clear']
        if method!='nominal':cmd+=['--expected-mjb',expected]
        subprocess.run(cmd,cwd=ROOT,check=True)
        if name=='nominal_blocked':expected=json.loads((run/'execution.json').read_text())['model_sha256']
    states=[json.loads((a.output/n/'execution.json').read_text()) for n in ('nominal_clear','nominal_blocked','esn_blocked','mlp_blocked')]
    assert all(s['status']=='complete' for s in states)
    assert len({s['plan_sha256'] for s in states})==1
    assert len({s['model_sha256'] for s in states[1:]})==1
    (a.output/'COMPARISON.json').write_text(json.dumps(dict(same_plan=True,same_blocked_model=True,rows=[s['audit'] for s in states]),indent=2))


if __name__=='__main__':main()
