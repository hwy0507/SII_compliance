"""Zero-physics checks of finite final-test handoff paths and null guards."""
import argparse
from pathlib import Path
import tempfile
from unittest.mock import patch

import continue_v9_unseen_after_selection_20261030 as h
from collect_special_scene_actions_20261028 import read, sha, write


def check():
    terminal=lambda status,n:dict(status=status,selected_models=[{}]*n)
    cases=[(None,'active','wait'),
        (terminal('running_development_eligibility',5),'active','wait'),
        (terminal('selection_complete_pending_independent_audit',9),'active','wait'),
        (terminal('selection_complete_pending_independent_audit',9),'deactivating','wait'),
        (terminal('failed_preserved',5),'failed','infrastructure_failed_no_dispatch'),
        (terminal('eligibility_exhausted_preserved',8),'inactive','null_selection_requires_development_repair'),
        (terminal('selection_complete_pending_independent_audit',8),'inactive','null_selection_requires_development_repair'),
        (terminal('selection_complete_pending_independent_audit',9),'failed','service_not_inactive_no_dispatch'),
        (terminal('selection_complete_pending_independent_audit',9),'inactive','ready_for_independent_review_and_registration')]
    for state,active,expected in cases:assert h.decision(state,active)==expected
    paths=[]
    with tempfile.TemporaryDirectory(prefix='sii-unseen-handoff-') as temp:
        base=Path(temp);(base/'outputs').mkdir();selection=base/'selection';selection.mkdir()
        # Point SOURCE_NAMES at a separate synthetic root; production sources
        # and actual final output directories are never changed by these tests.
        (base/'tools').mkdir()
        for name in h.SOURCE_NAMES:(base/'tools'/name).write_text('synthetic control source\n')
        conditions=base/'conditions.json';conditions.write_text('{}\n')
        for label,status,n,fail_run in [('ready','selection_complete_pending_independent_audit',9,False),
                ('null','eligibility_exhausted_preserved',8,False),
                ('fault','selection_complete_pending_independent_audit',9,True)]:
            write(selection/'execution.json',terminal(status,n))
            root=base/'outputs'/('handoff_'+label);target=base/'outputs'/('target_'+label)
            calls=[]
            def register(p):
                calls.append('register');p.mkdir();write(p/'REGISTRATION.json',{})
            def run(p):
                calls.append('run')
                if fail_run:raise RuntimeError('synthetic worker fault')
            def review(p,out):calls.append('review');write(out,dict(status='mock_review'))
            with patch.object(h,'ROOT',base),patch.object(h.final,'SELECTION',selection),\
                patch.object(h.final,'CONDITIONS',conditions),patch.object(h.final,'CONDITIONS_SHA',sha(conditions)),\
                patch.object(h.final,'check_resources'),patch.object(h.final,'properties',return_value={'ActiveState':'inactive'}),\
                patch.object(h.final,'register',side_effect=register),patch.object(h.final,'run',side_effect=run),\
                patch.object(h.final,'review',side_effect=review):
                if fail_run:
                    try:h.wait_and_run(root,target,1)
                    except RuntimeError:pass
                    else:raise AssertionError('Worker failure swallowed')
                else:h.wait_and_run(root,target,1)
            receipt=read(root/'HANDOFF.json')
            if label=='ready':
                assert calls==['register','run','review']
                assert receipt['status']=='complete_unseen_test_independently_reviewed_pending_delivery'
            elif label=='null':
                assert calls==[] and not target.exists()
                assert receipt['status']=='null_selection_requires_development_repair'
                assert not receipt['dispatch_attempted']
            else:
                assert calls==['register','run'] and receipt['status']=='failed_preserved'
                assert 'synthetic worker fault' in receipt['error']
            paths.append(dict(label=label,calls=calls,status=receipt['status']))
    return dict(status='passed_zero_physics_handoff_controls',decision_cases=len(cases),paths=paths,
        physics_integrations=0,actual_registration_created=False,
        sources={p.name:sha(p) for p in [Path(__file__),Path(h.__file__)]})


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();write(a.output,check())
