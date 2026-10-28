"""Investigate full-collection failures without dropping or relabeling them.

Use the next already-tested teacher setting (0.5, no averaging) on every
failed training identity. Also complete the missing two cells of the existing
office readout factorial; this is an inspected regression condition, not an
unseen test or a source of training examples. No automatic fitting follows.
"""
import argparse
import copy
from pathlib import Path
import subprocess

import numpy as np

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now, run


def prepare(root, collection):
    if root.exists():
        raise FileExistsError(root)
    progress=read(collection/'COLLECTION_PROGRESS.json')
    plan=read(collection/'COLLECTION_PLAN.json')
    assert progress['status']=='finished_with_nonqualified_demonstrations'
    assert len(progress['episodes'])==len(plan['episodes'])==30
    assert progress['plan_sha256']==sha(collection/'COLLECTION_PLAN.json')
    status=subprocess.check_output(['systemctl','--user','show',
        'sii-special-collection-v6-20261028.service','-p','MainPID','-p','ActiveState'],text=True)
    assert dict(x.split('=',1) for x in status.splitlines())==dict(MainPID='0',ActiveState='inactive')
    reference=ROOT/'outputs/special_scene_regression_controls_20261028_v2'
    factors=ROOT/'outputs/special_teacher_factor_controls_20261028_v1'
    original=read(reference/'REGISTRATION.json')
    factor_state=read(factors/'execution.json')
    assert factor_state['status']=='complete_pending_review' and len(factor_state['episodes'])==9
    for scene in ('rod','ball','corner'):
        q=next(r['qualification'] for r in factor_state['episodes'] if r['id']=='v0.5_avg0_'+scene)
        assert q['status']=='qualified'
    cases=[]
    reviewed=[]
    for entry,row in zip(plan['episodes'],progress['episodes']):
        assert entry['id']==row['id']
        folder=Path(entry['folder']);q=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        for name,h in q['input_hashes'].items():
            assert sha(folder/name)==h,name
        evidence=dict(id=entry['id'],split=entry['split'],scene=entry['scene'],status=q['status'],
                      qualification_sha256=sha(folder/'DEMONSTRATION_QUALIFICATION.json'))
        assert q['status']==row['status']
        if entry['scene']=='ball':
            with np.load(folder/'legacy.npz',allow_pickle=False) as z:
                positions=z['object_position'][-10:].copy()
            evidence['tail_object_speed_max_mps']=float(np.max(np.linalg.norm(np.diff(positions,axis=0)/.04,axis=1)))
            evidence['original_motion_threshold_mps']=.02
            evidence['legacy_npz_sha256']=sha(folder/'legacy.npz')
            legacy=read(folder/'legacy.json')
            assert legacy['grasp_lift_success']==bool(legacy['lift_m']>.10 and evidence['tail_object_speed_max_mps']<.02)
        reviewed.append(evidence)
        if q['status']!='qualified' and entry['split']=='train':
            # Validation failures remain in full30_review, but do not become
            # teacher-tuning cases. The next candidate was fixed by the
            # preceding training-identity factorial, not these held-out rows.
            cases.append(dict(id=entry['id']+'_v05_avg0',kind='scene',scene=entry['scene'],
                identity=entry['id'],seed=entry['seed'],scene_parameters=entry['scene_parameters'],
                expected_model_sha256=read(folder/'execution.json')['model_sha256'],baseline=str(folder),
                baseline_execution_sha256=sha(folder/'execution.json'),
                config=str(factors/'v0.5_avg0.json'),model=None))
    assert cases, 'Expected at least one actual failed training identity'
    office=original['cases'][0]
    for label in ('v0.5_avg0','v1_avg1'):
        cases.append(dict(id='office_'+label,kind='office',config=str(factors/(label+'.json')),
                          command=office['command'][:]))
    root.mkdir(parents=True)
    reg=copy.deepcopy(original)
    reg.update(schema='sii-full-collection-teacher-tail-probe-v1',registered_utc=now(),
        collection=str(collection),collection_plan_sha256=sha(collection/'COLLECTION_PLAN.json'),
        collection_progress_sha256=sha(collection/'COLLECTION_PROGRESS.json'),
        factor_registration_sha256=sha(factors/'REGISTRATION.json'),
        factor_execution_sha256=sha(factors/'execution.json'),full30_review=reviewed,
        maximum_episodes=len(cases),cases=cases,
        config_sha256={c['config']:sha(Path(c['config'])) for c in cases},
        interpretation=__doc__,
        next_step='Review full failed conditions, all paired receipts and office causal contrasts; no automatic data relabeling, recollection, fitting or final test dispatch.')
    reg['source_sha256']={name:sha(ROOT/name) for name in original['source_sha256']}
    reg['source_sha256'][str(Path(__file__).relative_to(ROOT))]=sha(Path(__file__))
    write(root/'REGISTRATION.json',reg)
    print(root,sha(root/'REGISTRATION.json'),len(cases),
          [(r['id'],r.get('tail_object_speed_max_mps')) for r in reviewed if r['status']!='qualified'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--collection',type=Path)
    p.add_argument('--run',action='store_true')
    a=p.parse_args()
    if a.run:
        run(a.root.resolve())
    else:
        prepare(a.root.resolve(),a.collection.resolve())
