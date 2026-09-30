"""Reject incomparable physical worlds even when fixture identifiers match."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from teacher_bank_campaign_20260930 import METHODS,check_paired_models


def test_paired_world_identity_and_partial_group(tmp_path):
    rows=[dict(fixture_id='train_0',method=method,model_sha256='same') for method in METHODS]
    assert check_paired_models(tmp_path,'full',rows)[0]['complete']
    assert not check_paired_models(tmp_path,'partial',rows[:2])[0]['complete']
    rows[-1]['model_sha256']='different'
    with pytest.raises(RuntimeError,match='different worlds'):
        check_paired_models(tmp_path,'corrupt',rows)
    assert not (tmp_path/'paired_model_checks/corrupt.json').exists()


def test_duplicate_method_cannot_fill_pair(tmp_path):
    row=dict(fixture_id='train_0',method='vmc',model_sha256='same')
    with pytest.raises(RuntimeError,match='Duplicate method'):
        check_paired_models(tmp_path,'duplicate',[row,row])
