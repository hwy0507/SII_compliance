"""Verify completed paired diagnostics; do not mix these into final scores."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from classical_acceptance_20261010 import read, write, sha, now


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--clear',type=Path,required=True)
    p.add_argument('--contact',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    rows=[]; models={}; common_route=None
    for root,expected_count in ((a.clear,4),(a.contact,6)):
        state=read(root/'execution.json')
        assert state['status']=='complete' and len(state['completed'])==expected_count
        assert state['registration_sha256']==sha(root/'REGISTRATION.json')
        for receipt in state['completed']:
            job=receipt['job']; run=root/job['name']
            assert receipt['status']=='complete'
            audit=read(run/'AUDIT.json'); execution=read(run/'execution.json')
            assert execution['status']=='complete'
            assert sha(run/'AUDIT.json')==receipt['audit_sha256']
            assert sha(run/'rollout.npz')==receipt['trace_sha256']==audit['trace_sha256']
            assert sha(run/'rollout.mjb')==audit['model_sha256']
            plan=read(run/'rollout.plan.json')['routes']
            if common_route is None:common_route=plan
            assert plan==common_route, 'Diagnostic routes differ'
            models.setdefault(job['fixture'],set()).add(audit['model_sha256'])
            with np.load(run/'rollout.npz') as z:
                assert z['observation'].shape==(1375,48)
                assert z['applied_action'].shape==(1375,7)
                assert np.isfinite(z['observation']).all() and np.isfinite(z['applied_action']).all()
                assert abs(z['applied_action']).max()<=1.000001
            assert abs(audit['physical_seconds']-55.)<1e-7 and audit['full_horizon']
            result=read(run/'rollout.json')
            events=result['stats']['events']
            row=dict(fixture=job['fixture'],method=job['controller'],task=audit['task_success'],
                strict=audit['strict_success'],final_stage=audit['stage'],
                placement_error_xy_mm=1000*audit['placement_error_xy_m'],rmse_mm=audit['rmse_mm'],
                peak_torque_nm=audit['peak_torque_nm'],peak_speed_mps=audit['peak_speed_mps'],
                external_penetration_mm=audit['penetration_mm'],edge_penetration_mm=audit['edge_penetration_mm'],
                contacts_s={k:events.get(k,{}).get('duration_s',0.) for k in ('ball','person_hand','rod')},
                run=str(run.resolve()),execution_sha256=sha(run/'execution.json'),
                audit_sha256=receipt['audit_sha256'],trace_sha256=receipt['trace_sha256'])
            rows.append(row)
    assert all(len(x)==1 for x in models.values())
    assert set(models)=={'clear','active_only','edge_only'}
    assert len({next(iter(x)) for x in models.values()})==3
    write(a.output,dict(status='verified',created_utc=now(),source_sha256=sha(__file__),rows=rows,
        identical_route_sha256=hashlib.sha256(json.dumps(common_route,sort_keys=True).encode()).hexdigest(),
        model_sha256_by_fixture={k:next(iter(v)) for k,v in models.items()},
        physical_episodes=10,additional_physics_steps=0,final_test_reads=0,
        scope='Ten complete development diagnostic episodes with identical routes and per-fixture models. Common physical metrics/action filter audited by original workers; classical dynamics/shield/native servo independently replayed in separate receipts.',
        interpretation='Clear controls all pass; active-only completion is conditional on actual contact coverage; edge-only isolates one passive obstacle. None are final comprehensive benchmark scores. Single anchor is not a generalization estimate.'))
    print(json.dumps([dict(method=r['method'],fixture=r['fixture'],task=r['task'],strict=r['strict'],
                          xy_mm=r['placement_error_xy_mm']) for r in rows],indent=2))


if __name__=='__main__':main()
