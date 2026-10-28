"""Explicit sealed evaluation adapter; requires a prior all-model hash lock.

This module is deliberately separate from every training/development wrapper.
It cannot select weights, change gates, or treat a final outcome as a label.
"""
import argparse
import json
from pathlib import Path
import sys
from research72_final_lock_20261003 import authorize_final_read, sha, read
from research72_protocol_20261003 import FIELDS, LOW, HIGH


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--model-lock',type=Path,required=True)
    p.add_argument('--lock-sha256',required=True)
    p.add_argument('--candidate',required=True)
    p.add_argument('--condition',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    source=Path(__file__).resolve().parents[1]
    lock,protocol=authorize_final_read(root,a.model_lock,a.lock_sha256,source,out.parent.parent)
    candidate=next(c for c in lock['candidates'] if c['name']==a.candidate)
    conditions=root/'sealed/HELDOUT.json'
    assert sha(conditions)==protocol['sealed_condition_sha256']
    condition=next(c for c in read(conditions)['conditions'] if c['id']==a.condition)
    assert condition['role']=='heldout'
    values=condition['overrides']
    assert set(values)==set(FIELDS)
    assert all(lo<=values[k]<=hi for k,lo,hi in zip(FIELDS,LOW,HIGH))
    assert values['rod_start']>=values['person_start']+8.
    import paper_office_worker_20261002 as office
    from run_all_methods_formal_20261003 import V6,PARAMETER
    original=office.evaluation_settings
    def settings(v6,dt,condition_file=None,condition_id=None):
        assert condition_file is None and condition_id is None and dt==protocol['physics_dt_s']
        expected,overrides,provenance=original(v6,dt)
        assert expected==protocol['formal_model_sha256']
        overrides.update(values)
        provenance.update(condition_id=condition['id'],data_role='sealed_final',
            research_protocol_sha256=sha(root/'PROTOCOL.json'),research_condition=condition,
            condition_file_sha256=sha(conditions),model_lock_sha256=a.lock_sha256,
            use='Sealed evaluation only; never fitting, selection feedback or demonstration labels')
        return expected,overrides,provenance
    office.evaluation_settings=settings
    config=out.parent/(out.name+'.config.json')
    with config.open('x') as f:
        json.dump(candidate.get('config',{}),f,indent=2,allow_nan=False);f.write('\n')
    args=['--v6-input',str(V6),'--reference',str(V6/'esn_original_v2/rollout.json'),
        '--config',str(config),'--output',str(out),'--physics-dt',str(protocol['physics_dt_s']),'--contact-audit']
    if candidate.get('nominal'):
        import research72_nominal_worker_20261003 as selected
    elif candidate.get('adapted_rl'):
        import research72_adapted_rl_worker_20261003 as selected
        rl=candidate['adapted_rl']
        args+=['--agent-checkpoint',rl['checkpoint'],'--checkpoint-manifest',rl['manifest'],
            '--parameter-source',rl['parameter_source']]
        if rl.get('controller'):args+=['--controller',rl['controller']]
    elif candidate.get('controller'):
        import paper_classical_worker_20261002 as selected
        args+=['--controller',candidate['controller'],'--parameter-source',str(PARAMETER)]
    else:
        selected=office
        if candidate.get('checkpoint'):args+=['--checkpoint',candidate['checkpoint']]
    sys.argv=[sys.argv[0],*args]
    try:
        selected.main()
    finally:
        if out.exists():
            office.worker.write(out/'FINAL_ROLE.json',dict(protocol_sha256=sha(root/'PROTOCOL.json'),
                model_lock_sha256=a.lock_sha256,candidate=a.candidate,condition=condition,
                source_sha256=sha(Path(__file__)),test_only=True))
            (out/'research72_final_worker.py.txt').write_text(Path(__file__).read_text())


if __name__=='__main__':main()
