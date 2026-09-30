"""Offline final-auditor checks with real SB3 artifacts from a synthetic backend."""
import copy
import importlib.util
import json
from pathlib import Path
import pickle
import sys
import zipfile

import numpy as np
import pytest
import torch
from stable_baselines3 import SAC
from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, str(ROOT/'tests'))
from canonical48_sac_audit_20260925 import AuditedReplayBuffer, OnlineEvidenceEnv, SACProgress, owned
from test_sac_audit_20260925 import SyntheticJournalEnv

spec = importlib.util.spec_from_file_location('independent_sac_final_audit', ROOT/'tools/audit_canonical48_sac_final_20260925.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class CapturedSynthetic(SyntheticJournalEnv):
    def __init__(self):
        super().__init__()
        self.completed_rows = []
        self.completed_directories = []

    def step(self, action):
        result = super().step(action)
        self.completed_rows.append(owned(self.journal.rows[-1]))
        self.completed_directories.append(self.journal.directory)
        return result


@pytest.fixture(scope='module')
def evidence(tmp_path_factory):
    output = tmp_path_factory.mktemp('sac-independent-final')
    torch.set_num_threads(1)
    env = CapturedSynthetic()
    normalized = VecNormalize(DummyVecEnv([lambda: OnlineEvidenceEnv(env)]), norm_reward=False, clip_obs=12.)
    initial = audit.normalizer_state(normalized)
    model = SAC('MlpPolicy', normalized, gamma=.995, seed=20260923, device='cpu',
                policy_kwargs=dict(net_arch=[256, 256]), replay_buffer_class=AuditedReplayBuffer,
                replay_buffer_kwargs=dict(audit_directory=output/'audit'))
    model.replay_buffer.start_audit()
    callback = SACProgress(output, checkpoint_every=0)
    model.save(output/'initial.zip')
    try:
        model.learn(105, callback=callback)
        model.save(output/'final.zip')
        model.replay_buffer.export_valid(output/'valid.npz')
        with np.load(output/'valid.npz') as archive:
            replay = {key: archive[key] for key in archive.files}
        result = dict(output=output, rows=env.completed_rows, directories=env.completed_directories,
                      initial=initial, final=audit.normalizer_state(normalized), old_obs=normalized.old_obs.copy(),
                      replay=replay, insertions=audit.lines(output/'audit/replay_insertions.jsonl'),
                      samples=audit.lines(output/'audit/replay_samples.jsonl'),
                      optimizer=audit.lines(output/'optimizer_steps.jsonl'))
    finally:
        callback.close_logs()
        model.replay_buffer.close_logs()
        normalized.close()
    return result


def test_independent_reconstruction_matches_actual_online_rms_slots_samples_and_adam(evidence):
    state, fallback = audit.reconstruct_statistics(evidence['rows'], evidence['initial'], evidence['old_obs'])
    assert not fallback and len(state) == 105
    audit.same_stats(state[-1], evidence['final'], 'real final')
    inserted = audit.audit_insertions(evidence['replay'], evidence['insertions'], evidence['rows'], evidence['directories'], state)
    assert inserted['online'] == 105 and inserted['online_terminal_placeholders'] == 52
    assert inserted['partial_final_next_valid']
    sampled = audit.audit_samples(evidence['samples'], evidence['replay'], state, 0)
    assert sampled['calls'] == 5 and sampled['sampled_online'] == 5*256
    assert audit.audit_optimizer_logs(evidence['optimizer'], 5) == dict(actor=5, critic=5, entropy=5)
    assert audit.checkpoint(evidence['output']/'initial.zip', 0, 0)['steps'] == 0
    assert audit.checkpoint(evidence['output']/'final.zip', 105, 5)['updates'] == 5


def test_budget_terminal_autoreset_uses_saved_raw_reset_not_terminal_placeholder(evidence):
    # At step104 the synthetic task terminates; the subsequent raw row is the
    # auto-reset observation, exactly what final saved old_obs would contain.
    states, fallback = audit.reconstruct_statistics(evidence['rows'][:104], evidence['initial'], evidence['rows'][104]['observation'])
    assert fallback
    audit.same_stats(states[-1], evidence['samples'][3]['normalization'], 'terminal budget sample state')


def test_real_terminal_budget_has_empty_new_journal_and_saved_reset_observation(tmp_path):
    env = CapturedSynthetic()
    normalized = VecNormalize(DummyVecEnv([lambda: OnlineEvidenceEnv(env)]), norm_reward=False, clip_obs=12.)
    initial = audit.normalizer_state(normalized)
    model = SAC('MlpPolicy', normalized, gamma=.995, seed=20260923, device='cpu', buffer_size=256,
                policy_kwargs=dict(net_arch=[8, 8]), replay_buffer_class=AuditedReplayBuffer,
                replay_buffer_kwargs=dict(audit_directory=tmp_path/'audit'))
    model.replay_buffer.start_audit()
    callback = SACProgress(tmp_path, checkpoint_every=0)
    try:
        model.learn(104, callback=callback)
        assert env.calls == 104 and model._n_updates == 4
        assert env.completed_rows[-1]['terminated'] and env.journal.rows == []
        normalized.save(tmp_path/'final-normalizer.pkl')
        with (tmp_path/'final-normalizer.pkl').open('rb') as stream:
            saved = pickle.load(stream)
        assert not np.array_equal(saved.old_obs[0], np.asarray(env.completed_rows[-1]['next_observation'], np.float32))
        states, fallback = audit.reconstruct_statistics(env.completed_rows, initial, saved.old_obs)
        assert fallback and len(states) == 104
        audit.same_stats(states[-1], audit.normalizer_state(saved), 'real terminal saved RMS')
        with pytest.raises(ValueError):
            false_states, _ = audit.reconstruct_statistics(env.completed_rows, initial, env.completed_rows[-1]['next_observation'])
            audit.same_stats(false_states[-1], audit.normalizer_state(saved), 'terminal placeholder is not reset')
    finally:
        callback.close_logs()
        model.replay_buffer.close_logs()
        normalized.close()


def test_original_reward_auditor_accepts_empty_cancelled_reset_episode(tmp_path):
    original_spec = importlib.util.spec_from_file_location('empty_episode_auditor', ROOT/'tools/audit_paired_transitions_20260924.py')
    original = importlib.util.module_from_spec(original_spec)
    original_spec.loader.exec_module(original)
    manifest = dict(mode='direct7', nominal_options={}, reward={},
                    source_hashes={'scripts/canonical48_rl_env_20260923.py': 'a'*64},
                    fixture_specs={'train': {'command': {'environment': {'CORE_VMC_CONFIG': '{}'}}}})
    contract = dict(mode='direct7', base_bridge_sha256='a'*64, adapter_train_nominal_options={}, reward={}, runtime_core_config={})
    (tmp_path/'transition_contract.json').write_text(json.dumps(contract))
    (tmp_path/'transitions.jsonl').write_text('')
    (tmp_path/'transition_summary.json').write_text(json.dumps(dict(transitions=0, completed=False)))
    np.savez_compressed(tmp_path/'transitions.npz', **{key: np.asarray([]) for key in original.FIELDS})
    np.savez_compressed(tmp_path/'actor_trace.npz', observation=np.asarray([]), action=np.asarray([]), phase_reward_metadata=np.asarray([]))
    result = original.audit_episode(tmp_path, manifest, {}, 'train')
    assert result['transitions'] == 0 and result['empty_reset'] and not result['complete']


@pytest.mark.parametrize('mutation', ['postadd_action', 'terminal_bootstrap', 'false_partial_next', 'source_action'])
def test_independent_journal_and_actual_replay_cannot_disagree(evidence, mutation):
    replay = {key: value.copy() for key, value in evidence['replay'].items()}
    insertions = copy.deepcopy(evidence['insertions'])
    if mutation == 'postadd_action':
        replay['actions'][0, 0, 1] += .01
    elif mutation == 'terminal_bootstrap':
        replay['dones'][1, 0] = 0
    elif mutation == 'false_partial_next':
        replay['next_observations'][-1, 0, 0] += .2
        insertions[-1]['stored']['next_observations'] = replay['next_observations'][-1].tolist()
    else:
        insertions[0]['evidence']['environment_action'][0] += .2
    states, _ = audit.reconstruct_statistics(evidence['rows'], evidence['initial'], evidence['old_obs'])
    with pytest.raises(ValueError):
        audit.audit_insertions(replay, insertions, evidence['rows'], evidence['directories'], states)


@pytest.mark.parametrize('mutation', ['future_transition', 'fitted_demo_statistics', 'wrong_source_count', 'missing_actual_check'])
def test_sample_evidence_must_bind_available_data_and_exact_online_only_statistics(evidence, mutation):
    samples = copy.deepcopy(evidence['samples'])
    if mutation == 'future_transition':
        samples[0]['indices'][0] = 101  # first update only contains indices0..100
    elif mutation == 'fitted_demo_statistics':
        samples[0]['normalization']['mean'][0] += .001
    elif mutation == 'wrong_source_count':
        samples[0]['demo_count'] = 1
    else:
        samples[0]['actual_sample_arrays_verified'] = False
    states, _ = audit.reconstruct_statistics(evidence['rows'], evidence['initial'], evidence['old_obs'])
    with pytest.raises(ValueError):
        audit.audit_samples(samples, evidence['replay'], states, 0)


def test_actual_optimizer_order_and_saved_update_boundary_are_required(evidence):
    rows = copy.deepcopy(evidence['optimizer'])
    rows[0], rows[1] = rows[1], rows[0]
    with pytest.raises(ValueError):
        audit.audit_optimizer_logs(rows, 5)
    with pytest.raises(ValueError):
        audit.checkpoint(evidence['output']/'final.zip', 105, 4)


def test_final_checkpoint_cannot_default_missing_seed_from_manifest(evidence, tmp_path):
    target = tmp_path/'missing-seed.zip'
    with zipfile.ZipFile(evidence['output']/'final.zip') as source, zipfile.ZipFile(target, 'w') as out:
        for name in source.namelist():
            data = source.read(name)
            if name == 'data':
                value = json.loads(data)
                del value['seed']
                data = json.dumps(value).encode()
            out.writestr(name, data)
    with pytest.raises(ValueError, match='seed'):
        audit.checkpoint(target, 105, 5)
