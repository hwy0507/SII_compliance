"""Exercise horizon failure handling and audit the eighteen paired development runs."""
import argparse
import copy
from pathlib import Path

import numpy as np

from audit_special_scene_metrics_v2_20261030 import check_horizon, horizon
from collect_special_scene_actions_20261028 import read, sha, write


def checks():
    t = np.arange(1,4)*.04
    st = np.arange(1,2401)*.00005
    dt = np.full(2400,.00005)
    e = dict(status='complete',steps=3,substeps=2400,physics_dt_s=.00005,physical_seconds=.12)
    assert check_horizon(e,t,st,dt,{},.12)['full_episode_completed']
    short = dict(e,steps=2,substeps=1600,physical_seconds=.08)
    r = check_horizon(short,t[:2],st[:1600],dt[:1600],{},.12)
    assert not r['full_episode_completed'] and r['failure_reasons']==['registered_horizon_not_completed']
    assert not check_horizon(e,t,st,dt,{'invalid_physics':True},.12)['full_episode_completed']
    assert not check_horizon(dict(e,status='failed_preserved'),t,st,dt,{},.12)['full_episode_completed']
    rejected = []
    for name, mutation in (
        ('over_budget',lambda x:x.update(expected_s=.08)),
        ('nonfinite',lambda x:x['substep_time'].__setitem__(8,np.nan)),
        ('missing_substep',lambda x:x.update(substep_time=x['substep_time'][:-1])),
        ('clock_gap',lambda x:x['substep_time'].__setitem__(8,.001)),
        ('wrong_dt',lambda x:x['dt'].__setitem__(8,.0001)),
        ('wrong_manifest_time',lambda x:x['execution'].update(physical_seconds=.08)),
        ('off_grid_budget',lambda x:x.update(expected_s=.13))):
        args = copy.deepcopy(dict(execution=e,trajectory_time=t,substep_time=st,dt=dt,legacy={},expected_s=.12))
        mutation(args)
        try:
            check_horizon(**args)
        except AssertionError:
            rejected.append(name)
        else:
            raise AssertionError('Corruption accepted: '+name)
    return dict(complete_passed=True,short_complete_status_retained_as_failed=True,
                invalid_physics_failed=True,failed_status_failed=True,rejected=rejected)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a = p.parse_args()
    assert not a.output.exists()
    tests = checks()
    registration = read(a.root/'REGISTRATION.json')
    rows = []
    for case in registration['cases']:
        scene = case['scene']
        folder = a.root/case['id']/scene
        expected = {'rod':20.,'ball':30.,'corner':13.}[scene]
        # These durations are the original development dispatch budgets,
        # not estimates from the observed endpoint.
        if scene != 'corner':
            assert read(folder/'recipe.json')['arguments']['duration'] == expected
        else:
            assert read(folder/'legacy.json')['record_duration_s'] == expected
        rows.append(dict(case=case['id'],scene=scene,**horizon(folder,expected)))
    assert len(rows)==18
    write(a.output,dict(status='development_horizon_audit_not_final_matrix',checks=tests,
        registration_sha256=sha(a.root/'REGISTRATION.json'),rows=rows,
        full_episodes=sum(r['full_episode_completed'] for r in rows),
        sources={n:sha(Path(__file__).parent/n) for n in
            ('audit_special_scene_metrics_v2_20261030.py',Path(__file__).name)},
        physics_integration_performed=False))
