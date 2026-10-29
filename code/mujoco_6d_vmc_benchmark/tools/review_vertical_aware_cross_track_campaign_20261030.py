"""Independent complete/prefix review of bounded cross-track development probes.

Verifies per-case saved actor/filter/qualification evidence, fixed prospective
order and matched physical identities. No fitting, integration or test input.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from collect_special_scene_actions_20261028 import ROOT,read,sha,write
from review_v9_paired_scene_closure_20261029 import verify_qualification
from audit_vertical_aware_cross_track_probe_20261030 import expected


def review(root,output,prefix=False):
    assert not output.exists()
    raw=(root/'execution.json').read_bytes();state=json.loads(raw);reg=read(root/'REGISTRATION.json')
    assert sha(root/'REGISTRATION.json')==state['registration_sha256']
    assert sha(root/'teacher.json')==reg['teacher_config_sha256']
    assert [(c['scene'],c['student_steps']) for c in reg['cases']]==[('rod',0),('ball',0),('corner',0),('rod',175),('rod',275)]
    for name,digest in reg['source_sha256'].items():assert sha(ROOT/name)==digest,name
    if not prefix:assert state['status']=='complete_five_probes_pending_independent_campaign_review' and len(state['rows'])==5
    rows=[]
    for item,case in zip(state['rows'],reg['cases']):
        assert item['id']==case['id']
        folder=Path(item['folder']);ref=case['reference'];teacher=Path(ref['folder'])
        assert folder==root/case['id']/case['scene']
        q=verify_qualification(folder,item['qualification_sha256'])
        assert sha(folder/'HANDOFF_REVIEW.json')==item['review_sha256']
        r=read(folder/'HANDOFF_REVIEW.json');h=read(folder/'HANDOFF_EXECUTION.json');e=read(folder/'execution.json')
        assert r['qualified']==item['qualified']==(q['status']=='qualified')
        assert sha(folder/'HANDOFF_EXECUTION.json')==r['handoff_execution_sha256']
        assert sha(folder/'INDEPENDENT_AUDIT.json')==r['independent_audit_sha256']
        for name,digest in h['input_hashes'].items():assert sha(folder/name)==digest
        assert e['status']=='complete' and e['model_sha256']==ref['model_sha256']==sha(folder/'scene.mjb')
        assert e['filter_config']==read(teacher/'execution.json')['filter_config']
        assert sha(folder/'teacher.json')==reg['teacher_config_sha256']
        assert h['student_steps']==case['student_steps'] and h['source_stable'] is True
        assert e['steps']==dict(rod=500,ball=750,corner=325)[case['scene']]
        assert e['substeps']==e['steps']*800
        assert 'oom 0\n' in e['resources']['memory.events'] and e['resources']['memory.swap.current']=='0'
        with np.load(folder/'trajectory.npz') as z:obs=z['observation'].copy();action=z['action'].copy()
        with np.load(teacher/'trajectory.npz') as z:np.testing.assert_array_equal(obs[0],z['observation'][0])
        t,s,behavior,mask=expected(read(folder/'teacher.json'),folder/'student_checkpoint.npz',obs,case['student_steps'])
        np.testing.assert_array_equal(behavior,action)
        with np.load(folder/'handoff_actions.npz') as z:
            np.testing.assert_array_equal(z['teacher'],t);np.testing.assert_array_equal(z['student'],s)
            np.testing.assert_array_equal(z['teacher_loss_mask'],mask)
        rows.append(dict(id=item['id'],qualified=item['qualified'],task_success=q['task_success'],
            safety_valid=q['safety_valid'],scene_behavior_valid=q['scene_contact_valid'],
            peak_torque_nm=max(q['metrics']['peak_torque_nm']),
            max_external_penetration_m=q['metrics']['max_external_penetration_m'],
            rod=(read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json') if case['scene']=='rod' else None),
            qualification_sha256=item['qualification_sha256'],teacher_candidate_label_rows=int(mask.sum()) if item['qualified'] else 0))
    if not prefix:assert (root/'execution.json').read_bytes()==raw
    result=dict(status='verified_incomplete_prefix' if prefix else 'verified_complete_five_development_probes',
        complete_cases=len(rows),qualified_cases=sum(r['qualified'] for r in rows),failed_cases=sum(not r['qualified'] for r in rows),
        rows=rows,registration_sha256=state['registration_sha256'],execution_snapshot_sha256=hashlib.sha256(raw).hexdigest(),
        reviewer_sha256=sha(Path(__file__)),final_test_performed=False,training_performed=False,
        limitations='Five registered development identities only; not unseen success, general recovery proof or final matrix. Qualified executed teacher rows are only candidates for a separately audited shared-data protocol.')
    write(output,result);print({k:v for k,v in result.items() if k!='rows'})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--prefix',action='store_true');a=p.parse_args()
    review(a.root.resolve(),a.output.resolve(),a.prefix)
