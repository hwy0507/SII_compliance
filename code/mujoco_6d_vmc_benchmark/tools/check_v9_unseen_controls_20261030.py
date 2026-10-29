"""Zero-physics control checks for final dispatch, failure preservation and SPT."""
import copy
from pathlib import Path
import tempfile
from unittest.mock import patch

import run_v9_unseen_matrix_20261030 as runner
from collect_special_scene_actions_20261028 import read, sha, write


def check():
    contract=read(runner.CONDITIONS)
    selected=read(runner.ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3/REGISTRATION.json')
    # Synthetic identities exercise dispatch logic only; not model selections.
    models=[dict(name=f+'_s'+str(s),family=f,seed=s) for f in runner.FAMILIES for s in runner.SEEDS]
    cases=runner.make_cases(models,contract['conditions'])
    assert len(cases)==108
    rejected=[]
    for name,alter in (
        ('missing_model',lambda m,c:m.pop()),
        ('duplicate_seed',lambda m,c:m.__setitem__(1,copy.deepcopy(m[0]))),
        ('duplicate_model_name',lambda m,c:m[1].update(name=m[0]['name'])),
        ('missing_condition',lambda m,c:c.pop()),
        ('duplicate_condition',lambda m,c:c.__setitem__(1,copy.deepcopy(c[0])))):
        m=copy.deepcopy(models);c=copy.deepcopy(contract['conditions']);alter(m,c)
        try:runner.make_cases(m,c)
        except AssertionError:rejected.append(name)
        else:raise AssertionError(name+' accepted')
    physical_calls=[]
    with tempfile.TemporaryDirectory(prefix='sii-unseen-control-') as temp:
        base=Path(temp)
        reg=dict(cases=cases)
        def fake_case(root,case,registration):
            physical_calls.append(case['id'])
            return dict(id=case['id'],pairing=dict(model_sha256=case['condition']['id'],
                        initial_observation=[0.]*48,filter_config={}))
        # Uses the actual coordinator loop, recording calls without a worker.
        with patch.object(runner.fcntl,'flock'),patch.object(runner,'check_resources'),patch.object(runner,'check_registration'),patch.object(runner,'run_case',side_effect=fake_case):
            good=base/'good';good.mkdir();write(good/'REGISTRATION.json',reg)
            runner.run(good)
            state=read(good/'execution.json')
            assert state['status']=='complete_pending_independent_review' and len(state['rows'])==108
            assert physical_calls==[c['id'] for c in cases]
            before=len(physical_calls)
            try:runner.run(good)
            except AssertionError:pass
            else:raise AssertionError('Implicit restart accepted')
            assert len(physical_calls)==before
        failed=base/'failed';failed.mkdir();write(failed/'REGISTRATION.json',reg)
        calls=[]
        def failure(root,case,registration):
            calls.append(case['id'])
            if len(calls)==4:raise RuntimeError('synthetic infrastructure fault')
            return fake_case(root,case,registration)
        with patch.object(runner.fcntl,'flock'),patch.object(runner,'check_resources'),patch.object(runner,'check_registration'),patch.object(runner,'run_case',side_effect=failure):
            try:runner.run(failed)
            except RuntimeError:pass
            else:raise AssertionError('Fault swallowed')
        state=read(failed/'execution.json')
        assert state['status']=='failed_preserved' and len(state['rows'])==3 and len(calls)==4
        assert state['current']==cases[3]['id'] and 'synthetic infrastructure fault' in state['error']
        mismatch=base/'mismatch';mismatch.mkdir();write(mismatch/'REGISTRATION.json',reg)
        def mismatched(root,case,registration):
            result=fake_case(root,case,registration)
            if case['id']==cases[1]['id']:result['pairing']['initial_observation'][0]=1.
            return result
        with patch.object(runner.fcntl,'flock'),patch.object(runner,'check_resources'),patch.object(runner,'check_registration'),patch.object(runner,'run_case',side_effect=mismatched):
            try:runner.run(mismatch)
            except AssertionError:pass
            else:raise AssertionError('Pairing defect accepted')
        assert read(mismatch/'execution.json')['status']=='failed_preserved'
        review_rejected=[]
        for count,status in ((107,'complete_pending_independent_review'),
                             (109,'complete_pending_independent_review'),
                             (108,'running_unseen_test')):
            folder=base/('review_'+str(count)+'_'+status);folder.mkdir()
            write(folder/'REGISTRATION.json',reg)
            receipts=[dict(id=c['id']) for c in cases]
            if count==107:receipts.pop()
            if count==109:receipts.append(copy.deepcopy(receipts[-1]))
            write(folder/'execution.json',dict(status=status,rows=receipts,
                registration_sha256=sha(folder/'REGISTRATION.json')))
            with patch.object(runner,'check_registration'):
                try:runner.review(folder,folder/'REVIEW.json')
                except AssertionError:review_rejected.append([count,status])
                else:raise AssertionError('Incomplete/duplicate/live review accepted')
            assert not (folder/'REVIEW.json').exists()
        # Real active-service guard must reject before any final registration.
        blocked=runner.ROOT/'outputs/nonrl_v9_unseen_guard_probe_20261030'
        assert not blocked.exists()
        try:runner.register(blocked)
        except AssertionError as exc:assert 'Selection still active' in str(exc)
        else:raise AssertionError('Registered while development active')
        assert not blocked.exists()
    rows=[]
    for i,m in enumerate(models):
        rows.append(dict(method=m['name'],condition='synthetic',scene='rod',
            task_success=True,strict_success=i!=8,completion_time_s=2.+i,
            peak_torque_nm=float(i),human_contact_s=None,proxy_contact_s=1.,
            proxy_below_threshold_s=.5,machine_compliant=i!=8))
    groups=runner.grouped(rows,models,1.,('family',))
    # Explicit shared global reference, never each group's local minimum.
    assert abs(groups[0]['spt_both_conditional']-sum(1./v for v in (2.,3.,4.))/3)<1e-12
    mlp=next(g for g in groups if g['family']=='mlp_scratch')
    assert mlp['episodes']==3 and mlp['both_success']==2
    return dict(status='passed_zero_physics_controls',dispatch_108_once=True,
        restart_rejected=True,infrastructure_failure_stopped_after_four_calls=True,
        pairing_mismatch_preserved=True,active_selection_registration_rejected=True,
        invalid_matrix_inputs_rejected=rejected,grouped_global_reference_verified=True,
        incomplete_duplicate_live_reviews_rejected=review_rejected,
        data_sha256=selected['catalogue']['data_sha256'],
        conditions_sha256=sha(runner.CONDITIONS),
        sources={p.name:sha(p) for p in (Path(__file__),Path(runner.__file__))},
        physics_integrations=0,final_registration_created=False)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();write(a.output,check())
