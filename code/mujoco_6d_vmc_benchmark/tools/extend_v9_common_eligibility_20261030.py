"""Common, finite full-grid eligibility extension after the original top-three.

No fitting or test access. All families/seeds inspect at most their same 12
already-trained candidates. Exact completed cases from either ancestor are
reused; null is preserved if none qualifies. One physics worker at a time.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time

import select_v9_closed_loop_candidates_v3_20261029 as base
from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from diagnose_special_scene_regression_20261028 import now
from review_v9_common_eligibility_20261030 import review
from review_v9_paired_scene_closure_20261029 import verify_qualification

PREVIOUS=ROOT/'outputs/nonrl_v9_common_eligibility_20261029_v3'
PREVIOUS_UNIT='sii-v9-common-eligibility-v3-20261029.service'


def previous_review():
    state=read(PREVIOUS/'execution.json')
    assert state['status'] in ('selection_complete_pending_independent_audit','eligibility_exhausted_preserved')
    assert base.properties(PREVIOUS_UNIT)['ActiveState']=='inactive'
    output=PREVIOUS/'FINAL_REVIEW.json'
    if not output.exists():review(PREVIOUS,output)
    report=read(output)
    assert report['status']=='verified_complete_development_selection'
    assert report['execution_snapshot_sha256']==sha(PREVIOUS/'execution.json')
    assert report['registration_sha256']==sha(PREVIOUS/'REGISTRATION.json')
    assert report['reviewer_sha256']==sha(ROOT/'tools/review_v9_common_eligibility_20261030.py')
    return state


def register(root):
    previous=previous_review()
    base.require_parent_review()
    reg=read(PREVIOUS/'REGISTRATION.json')
    reg.update(schema='sii-v9-common-full-grid-eligibility-v1',registered_utc=now(),
        candidate_limit_per_family_seed=12,maximum_candidates=108,maximum_candidate_case_checks=972,
        previous_selection=str(PREVIOUS),previous_execution_sha256=sha(PREVIOUS/'execution.json'),
        previous_registration_sha256=sha(PREVIOUS/'REGISTRATION.json'),
        previous_review_sha256=sha(PREVIOUS/'FINAL_REVIEW.json'),
        previous_selection_status=previous['status'],
        selection='Same existing 12-candidate validation-MSE rank order for every family/seed. Select first candidate qualified on all nine shared train00/validation08/09 closures. Stop a candidate at first complete failure. Reuse exact source-bound complete cases from paired18 or original top-three phase. If all12 fail, selected=null; never fallback or dispatch tests.',
        selection_scope='Prospective common eligibility cap extended from three to all12 already-trained candidates; same total fitting budgets and data. Earlier failures and rankings unchanged. No unseen test input or outcome is read.',
        source_sha256={str(p.relative_to(ROOT)):sha(p) for folder in ('scripts','tools') for p in (ROOT/folder).glob('*.py')})
    assert not (root/'REGISTRATION.json').exists()
    write(root/'REGISTRATION.json',reg)


def check_sources(reg):
    base.check_sources(reg)
    assert sha(PREVIOUS/'execution.json')==reg['previous_execution_sha256']
    assert sha(PREVIOUS/'REGISTRATION.json')==reg['previous_registration_sha256']
    assert sha(PREVIOUS/'FINAL_REVIEW.json')==reg['previous_review_sha256']


def cache(reg):
    result=base.parent_cache(reg)
    state=read(PREVIOUS/'execution.json')
    for group in state['groups']:
        for trial in group['trials']:
            for case in trial['cases']:
                folder=Path(case['folder'])
                verify_qualification(folder,case['qualification_sha256'])
                key=(trial['candidate']['checkpoint_sha256'],case['identity'])
                if key in result:assert result[key]==(folder,case['qualification_sha256'])
                else:result[key]=(folder,case['qualification_sha256'])
    return result


def run(root):
    base.check_resources()
    reg=read(root/'REGISTRATION.json');check_sources(reg)
    reused=cache(reg)
    assert not (root/'execution.json').exists()
    state=dict(status='running_development_eligibility',started_utc=now(),
        registration_sha256=sha(root/'REGISTRATION.json'),groups=[],selected_models=[])
    write(root/'execution.json',state)
    try:
        for group in reg['catalogue']['groups']:
            row=dict(family=group['family'],seed=group['seed'],trials=[],selected=None)
            state['groups'].append(row)
            for candidate in group['ordered_candidates'][:12]:
                trial=dict(candidate=candidate,cases=[],status='running');row['trials'].append(trial)
                write(root/'execution.json',state)
                for reference in reg['references']:
                    assert sha(root/'REGISTRATION.json')==state['registration_sha256']
                    check_sources(reg)
                    state['current']=dict(candidate=candidate['id'],identity=reference['identity'])
                    write(root/'execution.json',state)
                    receipt=base.evaluate(root,reg,candidate,reference,reused)
                    if receipt['reused_parent_episode']:
                        # Compatibility field means either fully audited ancestor,
                        # never a newly executed or partially written episode.
                        folder=Path(receipt['folder'])
                        receipt['reused_origin_run']=str(base.PARENT if base.PARENT in folder.parents else PREVIOUS)
                    check_sources(reg)
                    assert sha(root/'REGISTRATION.json')==state['registration_sha256']
                    trial['cases'].append(receipt);write(root/'execution.json',state)
                    if not receipt['development_qualified']:
                        trial['status']='failed_eligibility_full_episode_preserved';break
                else:
                    assert len(trial['cases'])==9
                    trial['status']='development_qualified_all_nine';row['selected']=candidate
                    state['selected_models'].append(dict(name='special_'+candidate['family']+'_s'+str(candidate['seed']),
                        family=candidate['family'],seed=candidate['seed'],validation_mse=candidate['validation_mse'],
                        selected_trial=candidate['id'],checkpoint=candidate['checkpoint'],checkpoint_sha256=candidate['checkpoint_sha256'],
                        metadata=candidate['metadata'],metadata_sha256=candidate['metadata_sha256'],worker_kind='office',config={}))
                    write(root/'execution.json',state);break
            row['status']='selected_development_qualified' if row['selected'] else 'candidate_budget_exhausted_preserved'
            write(root/'execution.json',state)
        state.update(status='selection_complete_pending_independent_audit' if len(state['selected_models'])==9 else 'eligibility_exhausted_preserved',ended_utc=now())
        write(root/'DEVELOPMENT_SELECTION.json',dict(status=state['status'],models=state['selected_models'],registration_sha256=state['registration_sha256'],final_test_performed=False))
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc),ended_utc=now());raise
    finally:write(root/'execution.json',state)


def wait_and_run(root):
    assert not root.exists(),'Never duplicate or silently restart'
    root.mkdir(parents=True)
    with (ROOT/'outputs/.v9-full-grid-eligibility-coordinator.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        overlay={str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),ROOT/'tools/review_v9_common_eligibility_20261030.py',ROOT/'tools/review_v9_full_grid_eligibility_20261030.py']}
        handoff=dict(status='waiting_for_original_three_rank_phase',started_utc=now(),previous=str(PREVIOUS),
            previous_unit=PREVIOUS_UNIT,maximum_wait_s=21600,pending_source_sha256=overlay)
        write(root/'HANDOFF.json',handoff)
        try:
            deadline=time.monotonic()+21600
            while time.monotonic()<deadline:
                assert all(sha(ROOT/p)==h for p,h in overlay.items())
                state=read(PREVIOUS/'execution.json')
                if state['status']=='failed_preserved':raise RuntimeError('Parent infrastructure failure requires explicit repair')
                if state['status'] in ('selection_complete_pending_independent_audit','eligibility_exhausted_preserved') and base.properties(PREVIOUS_UNIT)['ActiveState']=='inactive':break
                time.sleep(20)
            else:raise TimeoutError('Finite wait expired; no dispatch')
            assert all(sha(ROOT/p)==h for p,h in overlay.items())
            register(root)
            handoff.update(status='running_registered_full_grid_eligibility',dispatched_utc=now());write(root/'HANDOFF.json',handoff)
            run(root)
            handoff.update(status='finished_pending_independent_review',ended_utc=now())
        except BaseException as exc:
            handoff.update(status='failed_preserved',error=repr(exc),ended_utc=now());raise
        finally:write(root/'HANDOFF.json',handoff)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();wait_and_run(args.root.resolve())
