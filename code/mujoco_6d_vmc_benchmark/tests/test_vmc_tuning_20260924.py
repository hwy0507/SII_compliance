import numpy as np
import pytest

from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics


def nominal_options():
    return dict(stiffness_6d=[400.,400.,1200.,10.,8.,12.],
                damping_6d=[28.,28.,55.,2.8,2.4,3.])


def test_zero_parameters_reproduce_original_vmc_over_contact_and_release():
    options = dict(nominal_options(),axis_rotation_rpy=[.1,-.2,.3])
    tuned, reference = Canonical48VMCTuning(options), SixDVirtualDynamics(options)
    rng = np.random.default_rng(240924)
    for i in range(600):
        obs = rng.normal(size=48)
        obs[39:45] = rng.normal(size=6)*([40,35,50,4,4,4] if i<400 else np.zeros(6))
        np.testing.assert_array_equal(tuned.act(obs,np.zeros(6)),reference.act(obs[39:45],.04))
        for name in ('offset','velocity','filtered','k','b'):
            np.testing.assert_array_equal(getattr(tuned.base,name),getattr(reference,name))


def test_rate_bounds_damping_ratio_and_reset_do_not_carry_episode_history():
    tuned = Canonical48VMCTuning(nominal_options())
    observation = np.zeros(48)
    observation[39:45] = [30,20,10,1,2,3]
    ratio = tuned.nominal_d/(2*np.sqrt(tuned.nominal_k*tuned.base.mass))
    before = tuned.log_scale.copy()
    for value in ([1.]*6,)*8+([-1.]*6,)*12:
        tuned.act(observation,value)
        assert np.max(np.abs(tuned.log_scale-before)) <= tuned.log_scale_rate_per_s*.04+1e-15
        assert np.all(tuned.base.k >= .5*tuned.nominal_k-1e-12)
        assert np.all(tuned.base.k <= 2*tuned.nominal_k+1e-12)
        np.testing.assert_allclose(tuned.base.b/(2*np.sqrt(tuned.base.k*tuned.base.mass)),ratio,rtol=1e-14)
        before = tuned.log_scale.copy()
    tuned.reset()
    fresh = Canonical48VMCTuning(nominal_options())
    np.testing.assert_array_equal(tuned.act(observation,np.zeros(6)),fresh.act(observation,np.zeros(6)))


@pytest.mark.parametrize('bad', [np.full(6,np.nan),np.full(6,1.01),np.zeros(7)])
def test_invalid_requests_cannot_mutate_vmc_state(bad):
    tuned = Canonical48VMCTuning(nominal_options())
    with pytest.raises(ValueError):
        tuned.act(np.zeros(48),bad)
    np.testing.assert_array_equal(tuned.log_scale,np.zeros(6))
    np.testing.assert_array_equal(tuned.base.offset,np.zeros(6))


def test_vmc_uses_only_canonical_estimated_wrench_from_observation():
    first,second = Canonical48VMCTuning(nominal_options()),Canonical48VMCTuning(nominal_options())
    rng = np.random.default_rng(53)
    for _ in range(100):
        a,b = rng.normal(size=(2,48))
        b[39:45] = a[39:45]
        parameters = rng.uniform(-1,1,6)
        np.testing.assert_array_equal(first.act(a,parameters),second.act(b,parameters))


def test_missing_core_teacher_gains_are_rejected_instead_of_using_different_defaults():
    for options in ({},dict(stiffness_6d=[200]*6),dict(damping_6d=[20]*6)):
        with pytest.raises(ValueError,match='Explicit nominal'):
            Canonical48VMCTuning(options)


def test_explicit_options_match_real_core_teacher_despite_cli_defaults(monkeypatch):
    import run_vmc_6d_constrained_push_20260918 as core
    from contact_memory_vmc_20260916 import ContactMemoryConfig
    options=nominal_options()
    monkeypatch.setattr(core,'PARAMETERS',options)
    reference=core.CoreTeacher(ContactMemoryConfig(stiffness=200,damping=20))
    tuned=Canonical48VMCTuning(options)
    rng=np.random.default_rng(4824)
    for _ in range(100):
        obs=rng.normal(size=48)
        np.testing.assert_array_equal(tuned.act(obs,np.zeros(6)),
            reference.act(obs[39:45],obs[20:26],obs[26:32],obs[45:48],.04))
