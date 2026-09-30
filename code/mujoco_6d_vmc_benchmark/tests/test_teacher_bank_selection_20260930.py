"""Search selection must prioritize successful anchors, not easy low RMSE."""
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from teacher_bank_campaign_20260930 import summarize_candidate, candidate_rank, verify_assets, check_paired_models
from teacher_bank_design_20260930 import propose


def rows(constraints, score):
    return [dict(eligible=value<=0,constraint=value,score=score) for value in constraints]


def test_two_successes_beat_three_low_error_failures_with_same_worst_label_count():
    all_failed=summarize_candidate(rows([1,1,1],.01),[.2]*5,0)
    two_successes=summarize_candidate(rows([-1,-1,1],10.),[.5]*5,1)
    # Previous max-label-count proxy tied and would select all_failed by score.
    assert sorted([all_failed,two_successes],key=candidate_rank)[0] is two_successes
    assert two_successes['constraint']<all_failed['constraint']
    assert (two_successes['eligible_count'],two_successes['total'])==(2,3)


def test_one_extra_failed_anchor_dominates_arbitrarily_large_label_severity():
    one_failed=summarize_candidate(rows([-1,-1,100000],100.),[.3]*5,0)
    two_failed=summarize_candidate(rows([-1,1,1],.01),[.6]*5,1)
    assert candidate_rank(one_failed)<candidate_rank(two_failed)
    assert 1<one_failed['constraint']<1.25<two_failed['constraint']


def test_all_feasible_candidates_rank_by_unchanged_mean_score():
    a=summarize_candidate(rows([-1,-1,-1],.5),[.2]*7,0)
    b=summarize_candidate(rows([-1,-1,-1],.7),[.4]*7,1)
    assert a['constraint']==b['constraint']==-1
    assert candidate_rank(a)<candidate_rank(b)
    with pytest.raises(ValueError,match='Nonfinite'):
        summarize_candidate(rows([-1,-1,-1],np.nan),[.2]*7,2)


def test_new_failure_proxy_is_consumed_by_bo_for_both_controller_dimensions():
    for dimension in (5,7):
        history=[summarize_candidate(rows(constraints,float(i+1)),[.2*(i+1)]*dimension,i)
                 for i,constraints in enumerate(([1,1,1],[-1,-1,2],[-1,1,1]))]
        candidate=np.asarray(propose(history,37))
        assert candidate.shape==(dimension,)
        assert np.isfinite(candidate).all() and np.all((candidate>=0)&(candidate<=1))


def test_actual_asset_contents_and_file_set_must_match_not_only_manifest(tmp_path):
    from teacher_bank_design_20260930 import write, sha
    assets=tmp_path/'assets';robot=assets/'robot';robot.mkdir(parents=True)
    model=robot/'model.xml';model.write_text('<mujoco/>')
    root=tmp_path/'run'
    write(root/'source_inputs/robot_asset_manifest.json',{'robot/model.xml':sha(model)})
    assert verify_assets(root,assets)['files_verified']==1
    # Manifest remains byte-for-byte unchanged; actual runtime input changed.
    model.write_text('<mujoco model="modified"/>')
    with pytest.raises(RuntimeError,match='content differs'):
        verify_assets(root,assets)
    model.write_text('<mujoco/>')
    extra=robot/'unexpected.xml';extra.write_text('<mujoco/>')
    with pytest.raises(RuntimeError,match='file set differs'):
        verify_assets(root,assets)


def test_each_paired_candidate_cannot_silently_use_a_different_shared_model(tmp_path):
    def paired(digest):
        return [dict(fixture_id='fixture1',method=method,model_sha256=digest)
                for method in ('vmc','admittance','impedance')]
    check_paired_models(tmp_path,'search/c00',paired('modelA'))
    check_paired_models(tmp_path,'search/c01',paired('modelA'))
    # All three methods agree WITHIN candidate c02; across-candidate drift fails.
    with pytest.raises(RuntimeError,match='across candidates'):
        check_paired_models(tmp_path,'search/c02',paired('modelB'))
    import json
    retained=json.loads((tmp_path/'fixture_model_identity.json').read_text())
    assert retained['fixture1']['model_sha256']=='modelA'
