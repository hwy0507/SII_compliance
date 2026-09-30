import sys
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from teacher_bank_design_20260930 import CATEGORIES,decode,design,propose,warm_points
from teacher_bank_rollout_20260930 import adapted_run,training_xml


def test_fixture_counts_split_identity_and_determinism(tmp_path):
    reference=tmp_path/'reference.npz'
    np.savez(reference,time=np.array([0.,55.]),hand=np.array([[.54,-.19,.6],[.58,-.30,.65]]))
    a=design(reference);b=design(reference)
    assert a==b
    for category in CATEGORIES:
        rows=[r for r in a if r['category']==category]
        assert sum(r['split']=='train' for r in rows)==1000
        assert sum(r['split']=='validation' for r in rows)==100
    assert len({r['physical_config_sha256'] for r in a})==3300
    assert len({r['seed'] for r in a})==3300
    assert all(r['start_s']>=2 for r in a)


def test_bounded_positive_controller_and_known_reference():
    cfg=decode(warm_points(1)[0])
    np.testing.assert_allclose(cfg['options']['stiffness_6d'],[800,800,2400,20,16,24])
    assert cfg['velocity_weight']==pytest.approx(.25)
    for point in np.random.default_rng(1).uniform(size=(100,7)):
        for key in ('stiffness_6d','damping_6d'):
            assert np.all(np.asarray(decode(point)['options'][key])>0)
    with pytest.raises(ValueError):decode([2]*7)


def test_bo_feasibility_and_objective_modes():
    history=[dict(x=x,constraint=1.,score=3.) for x in warm_points(2)]
    first=propose(history,11)
    history[0]['constraint']=-1.;history[1]['constraint']=-1.
    second=propose(history,12)
    for point in (first,second):assert np.isfinite(point).all() and all(0<=x<=1 for x in point)


def test_office_adapter_preserves_shared_source():
    from types import SimpleNamespace
    sys.path.insert(0,str(ROOT/'scripts'))
    import validate_office_apparatus_v5_20260917 as evaluator
    source=Path(evaluator.__file__).read_bytes()
    isolated=SimpleNamespace(run=evaluator.run,__file__=evaluator.__file__)
    adapted_run(isolated)
    assert Path(evaluator.__file__).read_bytes()==source
    assert 'TRAIN_CONFIGS' in isolated.run.__code__.co_names
    assert 'TRAIN_BALL_VELOCITY' in isolated.run.__code__.co_names
