"""Virtual reference-follower regression; no dynamics and no actor evaluation."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from planned_hand_corner_20261002 import PlannedCornerTask
from office_task_v4_20260917 import PickPlaceTask


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    if a.output.exists():raise FileExistsError(a.output)
    prior=a.run/'esn_combined_v4.plan.json'
    detour=a.run/'INFORMED_DETOUR_EXPANDED_AUDIT.json'
    p=json.loads(prior.read_text())
    d=json.loads(detour.read_text())
    assert d['status']=='geometrically_feasible'
    with tarfile.open(a.run/'source_overlay.tar.gz') as archive:
        old=archive.extractfile('scripts/planned_hand_corner_20261002.py').read()
    namespace={'__name__':'frozen_v1_planner'}
    exec(compile(old,'frozen_v1_planner','exec'),namespace)
    rows=[]
    for version,cls in [('v1',namespace['PlannedCornerTask']),('v2',PlannedCornerTask)]:
        routes={int(k):[(np.array(w['hand']),np.array(w['rotation'])) for w in v] for k,v in p['routes'].items()}
        t=cls(PickPlaceTask(np.array([.54,-.19,.60]),[7,8],[7,8]),routes)
        t.index=4;t.allow_lateral_rejoin=True
        def update(w):
            t.update(np.zeros(9),np.zeros(9),np.array(w['hand']),np.array(w['rotation']),np.zeros(6),np.zeros(6))
        for w in d['plan']['routes']['4']:
            for _ in range(5):update(w)
        for _ in range(100):update(w)
        rows.append(dict(version=version,cursor=t.cursors[4],last_cursor=len(routes[4])-1,stage=t.index))
    assert rows[0]['cursor']<rows[0]['last_cursor']
    assert rows[1]['cursor']==rows[1]['last_cursor'] and rows[1]['stage']==5
    record=dict(purpose=__doc__,physics_stepped=False,used_by_actor=False,
                limitation='Idealized poses on an informed route; this only checks route rejoin logic, not dynamic feasibility or policy success',
                rows=rows,hashes={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (prior,detour,Path(__file__),ROOT/'scripts/planned_hand_corner_20261002.py')},
                legacy_source_sha256=hashlib.sha256(old).hexdigest())
    a.output.write_text(json.dumps(record,indent=2))
    print(json.dumps(rows))


if __name__=='__main__':main()
