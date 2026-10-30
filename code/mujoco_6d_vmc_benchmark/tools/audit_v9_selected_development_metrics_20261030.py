"""Exercise final metric/replay paths on every currently selected development case.

No integration, fitting or test access. Preserve individual audit failures;
no partial SPT reference or final generalization claims are produced.
"""
import argparse
import hashlib
import json
from pathlib import Path

from audit_special_scene_metrics_v2_20261030 import episode
from collect_special_scene_actions_20261028 import read, sha, write
from review_v9_common_eligibility_20261030 import validate_structure as validate_three
from review_v9_full_grid_eligibility_20261030 import validate_structure as validate_twelve
from run_v9_unseen_matrix_20261030 import replay


def audit(root,output):
    assert not output.exists()
    execution_bytes=(root/'execution.json').read_bytes()
    state=json.loads(execution_bytes);reg=read(root/'REGISTRATION.json')
    assert state['registration_sha256']==sha(root/'REGISTRATION.json')
    validator=validate_three if reg['candidate_limit_per_family_seed']==3 else validate_twelve
    selected=validator(reg,state,final=False)
    assert selected
    output.mkdir(parents=True)
    # Freeze the exact observed prefix even if the live coordinator progresses.
    (output/'execution.snapshot.json').write_bytes(execution_bytes)
    write(output/'REGISTRATION.snapshot.json',reg)
    rows=[]
    for group in state['groups']:
        if group['selected'] is None:continue
        candidate=group['selected'];trial=group['trials'][-1]
        assert trial['status']=='development_qualified_all_nine' and len(trial['cases'])==9
        assert sha(Path(candidate['checkpoint']))==candidate['checkpoint_sha256']
        for receipt,reference in zip(trial['cases'],reg['references']):
            folder=Path(receipt['folder'])
            cell=dict(family=group['family'],seed=group['seed'],rank=candidate['validation_rank'],
                identity=receipt['identity'],folder=str(folder))
            assert cell['identity']==reference['identity']
            assert sha(folder/'DEMONSTRATION_QUALIFICATION.json')==receipt['qualification_sha256']
            assert sha(folder/'student_checkpoint.npz')==candidate['checkpoint_sha256']
            try:
                cell['independent_replay']=replay(folder)
                cell['metrics']=episode(folder,group['family']+'_s'+str(group['seed']),
                    reference['identity'],{'rod':20.,'ball':30.,'corner':13.}[reference['scene']])
                assert cell['metrics']['task_success'] and cell['metrics']['strict_success']
                assert cell['metrics']['machine_compliant']
                cell['audit_status']='passed'
            except Exception as exc:
                cell.update(audit_status='failed_preserved',error=repr(exc))
            rows.append(cell)
            write(output/'progress.json',dict(completed=len(rows),expected=len(selected)*9,
                failures=sum(r['audit_status']!='passed' for r in rows)))
    assert len(rows)==len(selected)*9
    assert sha(root/'REGISTRATION.json')==state['registration_sha256']
    result=dict(status='development_metric_preflight_passed' if all(r['audit_status']=='passed' for r in rows)
            else 'development_metric_preflight_failures_preserved',
        selected_groups=len(selected),episodes=len(rows),rows=rows,
        execution_snapshot_sha256=hashlib.sha256(execution_bytes).hexdigest(),
        registration_sha256=state['registration_sha256'],
        source_sha256={p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name(
            'audit_special_scene_metrics_v2_20261030.py'),Path(__file__).with_name('run_v9_unseen_matrix_20261030.py')]},
        physics_integrations=0,final_test_performed=False,spt_computed=False,
        limitations=['Selected development closures only; no final unseen matrix.',
            'No partial T_ref/SPT or model selection from these metric values.',
            'Human comfort NA; disturbance torque proxy not measured human comfort.'])
    write(output/'REVIEW.json',result)
    print({k:v for k,v in result.items() if k not in ('rows','source_sha256','limitations')})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();audit(a.root.resolve(),a.output.resolve())
