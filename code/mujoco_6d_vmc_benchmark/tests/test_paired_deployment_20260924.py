"""Pure synthetic inference/backend tests: no MuJoCo environment or mj_step."""
import numpy as np
import pytest
import copy
import importlib.util
import json
from pathlib import Path
from canonical48_paired_deployment_20260924 import FrozenActor, PairedExecutionPolicy, frozen_training
from canonical48_vmc_tuning_20260924 import Canonical48VMCTuning

OPTIONS = dict(stiffness_6d=[100,120,140,20,22,24], damping_6d=[11,12,13,4,5,6],
               mass_6d=[.7,.8,.9,.05,.06,.07], filter_tau=.06, axis_rotation_rpy=[.2,0.,-.1])


class RequestActor:
    def __init__(self, action):
        self.action = np.asarray(action)
    def act(self, raw):
        return self.action
    def close(self):
        pass


def observation():
    raw = np.linspace(-.1234567890123,.2345678901234,48)
    raw[39:45] = np.arange(1,7)*1.234567890123
    return raw


def test_actor_float32_cast_precedes_frozen_normalization():
    actor = object.__new__(FrozenActor)
    seen = {}
    class Normalizer:
        def normalize_obs(self, obs):
            seen['raw'] = obs.copy()
            return (obs-3.).astype(np.float32)
    class Model:
        def predict(self, obs, deterministic):
            seen['normalized'] = obs.copy()
            assert deterministic
            return np.linspace(-2,2,6,dtype=np.float32), None
    actor.normalizer, actor.model = Normalizer(), Model()
    actor.low, actor.high = -np.ones(6), np.ones(6)
    raw = observation()
    result = actor.act(raw)
    assert seen['raw'].dtype == np.float32
    assert np.array_equal(seen['raw'][0],raw.astype(np.float32))
    assert np.array_equal(seen['normalized'],raw.astype(np.float32)-3.)
    assert result.dtype == np.float64 and np.max(np.abs(result)) == 1.


def test_backend_raw64_training_options_and_reset(monkeypatch):
    monkeypatch.setenv('CORE_VMC_CONFIG','{"stiffness_6d":[999,999,999,999,999,999]}')
    actor = RequestActor(np.zeros(6))
    policy = PairedExecutionPolicy('parameter6',OPTIONS,actor)
    raw = observation()
    expected = Canonical48VMCTuning(OPTIONS).act(raw,np.zeros(6))
    rounded = Canonical48VMCTuning(OPTIONS).act(raw.astype(np.float32),np.zeros(6))
    assert not np.array_equal(expected,rounded)
    assert np.array_equal(policy.act(raw),expected)
    actor.action = np.ones(6)
    for _ in range(7):
        policy.act(raw)
    assert policy.controller.log_scale.any()
    policy.reset()
    actor.action = np.zeros(6)
    assert np.array_equal(policy.act(raw),expected)
    assert len(policy.log['observation']) == 1


def test_nominal_control_is_zero6_not_zero7():
    policy = PairedExecutionPolicy('nominal_train_vmc',OPTIONS)
    action = policy.act(observation())
    assert action.shape == (7,) and action.any()
    assert not np.any(policy.log['policy_action'])
    assert np.array_equal(policy.controller.base.k,OPTIONS['stiffness_6d'])


def test_direct_control_has_no_vmc_memory_update():
    policy = PairedExecutionPolicy('direct7',OPTIONS,RequestActor(np.array([.2,.3,0,0,0,0,0])))
    for _ in range(3):
        assert np.array_equal(policy.act(observation()),[.2,.3,0,0,0,0,0])
    assert policy.controller.last_parameters is None
    assert not policy.controller.log_scale.any()


@pytest.mark.parametrize('kind',['float32','nan','shape','action'])
def test_invalid_data_rejected_before_state_mutation(kind):
    actor = RequestActor(np.zeros(6))
    policy = PairedExecutionPolicy('parameter6',OPTIONS,actor)
    raw = observation()
    if kind == 'float32': raw = raw.astype(np.float32)
    if kind == 'nan': raw[2] = np.nan
    if kind == 'shape': raw = raw[:-1]
    if kind == 'action': actor.action = np.full(6,np.nan)
    with pytest.raises(ValueError):
        policy.act(raw)
    assert policy.controller.last_parameters is None
    assert not policy.log['observation']


def test_plan_is_exact18_original_fixtures_and_never_changes_fixture_core(tmp_path):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('prepare_plan',root/'tools/prepare_paired_six_fixture_deployment_20260924.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = []
    for seed in range(9400,9406):
        rows.append(dict(fixture=dict(seed=seed),command=['python','wrapper','--','--output','old','--seed',str(seed)],
            environment={'CORE_VMC_CONFIG':'unchanged_fixture_core'},model_mjb_sha256='fixture_model_'+str(seed),
            result='original_result',result_sha256='original_hash'))
    before = copy.deepcopy(rows)
    jobs = module.build_jobs(rows,dict(parameter6=tmp_path/'param',direct7=tmp_path/'direct'),
                             dict(parameter6='cuda',direct7='cuda'),tmp_path/'jobs')
    assert rows == before and len(jobs) == 18
    assert {(j['method'],j['fixture']['seed']) for j in jobs} == {(m,s) for m in ('parameter6','direct7','nominal_train_vmc') for s in range(9400,9406)}
    assert all(j['environment']['CORE_VMC_CONFIG']=='unchanged_fixture_core' for j in jobs)
    assert not list(tmp_path.iterdir())  # Plan construction does not start/write jobs.


def tool_module(name):
    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(name,root/'tools'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_never_overrides_failed(tmp_path):
    for name in ('COMPLETE.json','FAILED.json','manifest.json'):
        (tmp_path/name).write_text('{}')
    with pytest.raises(ValueError,match='FAILED'):
        frozen_training(tmp_path,'parameter6')


def test_audit_paths_map_unique_original_run_suffix_and_reject_escape(tmp_path):
    module = tool_module('prepare_paired_six_fixture_deployment_20260924')
    origin = '/remote/project/output/training_parameter6'
    target = tmp_path/'train/episode_00000'
    assert module.audit_directory(origin+'/train/episode_00000',origin,tmp_path)==target
    assert module.audit_directory('project/output/training_parameter6/train/episode_00000',origin,tmp_path)==target
    with pytest.raises(ValueError):
        module.audit_directory('different_run/train/episode_00000',origin,tmp_path)
    with pytest.raises(ValueError):
        module.audit_directory(origin+'/train/../outside',origin,tmp_path)


def write_synthetic_terminal(directory,count,invalid):
    directory.mkdir(parents=True,exist_ok=True)
    obs = np.repeat(observation()[None],count,axis=0)
    terminal = np.arange(count)==count-1
    actions = np.zeros((count,7))
    np.savez_compressed(directory/'transitions.npz',observation=obs,next_observation=obs.copy(),
        execution_action=actions,terminated=terminal,truncated=np.zeros(count,dtype=bool),next_observation_valid=~terminal)
    np.savez_compressed(directory/'actor_trace.npz',observation=obs,action=actions)
    (directory/'transition_contract.json').write_text('{}')
    (directory/'rollout.json').write_text(json.dumps(dict(duration_s=.04*count,invalid_physics=invalid)))
    (directory/'rollout.mjb').write_bytes(b'synthetic offline fixture, never loaded')


def test_safety_short_prefix_retained_but_unexplained_partial_rejected(tmp_path):
    module = tool_module('audit_paired_deployment_replay_20260924')
    write_synthetic_terminal(tmp_path/'safety',3,True)
    data,_,result = module.read_episode(tmp_path/'safety',{})
    assert len(data['observation'])==3 and result['invalid_physics']
    write_synthetic_terminal(tmp_path/'bad',3,False)
    with pytest.raises(ValueError,match='genuine archived safety'):
        module.read_episode(tmp_path/'bad',{})


def test_offline600_dual_path_and_reset_without_physics():
    module = tool_module('audit_paired_deployment_replay_20260924')
    request = np.array([.1,-.2,.3,-.4,.5,-.6])
    actor = RequestActor(request)
    policy = PairedExecutionPolicy('parameter6',OPTIONS,actor)
    raw = np.repeat(observation()[None],600,axis=0)
    raw[:,39] += np.linspace(0,2,600)
    report = module.replay(policy,lambda _:request.copy(),raw,
        dict(nominal_options=OPTIONS,device='cpu',trained_device='cpu'))
    assert report['samples']==600 and report['end_to_end_exact']
    assert report['checks']['reset_replay_execution_action']['exact']
