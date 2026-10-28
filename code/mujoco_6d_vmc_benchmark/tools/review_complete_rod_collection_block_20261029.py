"""Review all ten completed rod identities without touching an active collector.

Bind saved qualification/geometry audits and independently check the required
event order, release-time arithmetic, and persistence duration. This does not
reintegrate physics or promote a partial30 collection to a complete dataset.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import math
from pathlib import Path

from collect_special_scene_actions_20261028 import ROOT,read,sha,validate,write


def review(collection,output):
    assert not output.exists()
    plan_path=collection/'COLLECTION_PLAN.json';plan=validate(plan_path)
    state=read(collection/'COLLECTION_PROGRESS.json')
    assert state['plan_sha256']==sha(plan_path)
    entries=[e for e in plan['episodes'] if e['scene']=='rod']
    assert len(entries)==10 and Counter(e['split'] for e in entries)==Counter(train=8,validation=2)
    receipts={r['id']:r for r in state['episodes']}
    assert all(e['id'] in receipts for e in entries), 'All ten rod identities must finish first'
    rows=[]
    for entry in entries:
        folder=Path(entry['folder']);execution=read(folder/'execution.json')
        qualification=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        audit=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
        assert execution['status']=='complete' and receipts[entry['id']]['returncode']==0
        assert qualification['status']==receipts[entry['id']]['status']
        for name,h in qualification['input_hashes'].items(): assert sha(folder/name)==h,name
        for name,h in audit['hashes'].items():
            source=ROOT/'tools'/name if name.endswith('.py') else folder/name
            assert sha(source)==h,name
        assert execution['collection_identity']==entry['id'] and execution['collection_split']==entry['split']
        assert execution['collection_plan_sha256']==sha(plan_path)
        assert execution['collection_scene_parameters']==entry['scene_parameters']
        assert execution['teacher_config_sha256']==plan['teacher_config_sha256']
        env=execution['experiment_environment']
        assert env['VMC_SCENE_SEED']==str(entry['seed'])
        assert all(env[k]==str(v) for k,v in entry['scene_parameters'].items())
        recipe=read(folder/'recipe.json')['arguments'];legacy=read(folder/'legacy.json')
        retract=legacy['fixture_trigger_time_s']+recipe['push_press']+recipe['push_hold']
        assert abs(retract-audit['retract_start_s'])<1e-12
        events=[v for k,v in execution['contacts']['push_rod_geom']['per_body'].items() if k in audit['hand_bodies']]
        first=min((v['first_s'] for v in events),default=None)
        assert first==audit['hand_contact_first_s']
        timing=[audit[k] for k in ('hand_contact_first_s','yield_start_s','pass_s','rejoin_start_s','rejoin_confirmed_s')]+[retract]
        finite=all(v is not None and math.isfinite(v) for v in timing)
        sequence=finite and all(x<=y+1e-9 for x,y in zip(timing[:-2],timing[1:-1])) and timing[-2]<timing[-1]
        persistent=finite and timing[-2]-timing[-3]>=.08-1e-9
        assert audit['criteria']['hold_s']==.08 and audit['criteria']['gap_m']==.002
        assert audit['criteria']['yield_m']==.004 and audit['criteria']['rejoin_tube_m']==.005
        checks=dict(original_qualification=qualification['status']=='qualified',
            original_behavior_checks=all(audit['checks'].values()),
            contact_yield_pass_rejoin_before_retract=sequence,persistent_hold_duration=persistent)
        rows.append(dict(id=entry['id'],split=entry['split'],checks=checks,
            status='passed' if all(checks.values()) else 'failed_preserved',
            timings=dict(zip(('contact_s','yield_s','pass_s','rejoin_start_s','rejoin_confirmed_s','retract_start_s'),timing)),
            rejoin_before_retract_margin_s=retract-timing[-2] if finite else None,
            peak_torque_nm=max(qualification['metrics']['peak_torque_nm']),
            max_external_penetration_mm=1000*qualification['metrics']['max_external_penetration_m'],
            hashes={n:sha(folder/n) for n in ('DEMONSTRATION_QUALIFICATION.json','ROD_YIELD_REJOIN_AUDIT_V3.json',
                     'execution.json','trajectory.npz','scene.mjb','recipe.json','teacher.json')}))
    result=dict(schema='sii-complete-rod-block-review-v1',reviewed_utc=datetime.now(timezone.utc).isoformat(),
        status='all10_passed' if all(r['status']=='passed' for r in rows) else 'completed_with_failures',
        collection=str(collection),plan_sha256=sha(plan_path),rows=rows,source_sha256=sha(Path(__file__)),
        scope='All10 registered rod identities, 8train/2validation, fixed teacher and original checks. No validation tuning.',
        limitation='Saved geometry/physical audit bindings plus independently checked event ordering. No new dynamics. Not full30 qualification, office Task/Strict or student performance.')
    output.parent.mkdir(parents=True,exist_ok=True);write(output,result)
    print(result['status'])
    for row in rows: print(row['id'],row['status'],row['timings'],row['rejoin_before_retract_margin_s'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--collection',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args();review(a.collection.resolve(),a.output.resolve())
