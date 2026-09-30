"""One physics-equilibrium correction of the frozen ESN linear readout."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from run_vmc_6d_constrained_push_20260918 import SixDVirtualDynamics


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def logits(actor, features):
    return features @ actor.weights + np.tanh((features / actor.feature_scale) @ actor.hidden_w.T) @ actor.output_w.T


def actions(actor, features):
    result = np.tanh(logits(actor, features))
    result[:, 0] = np.linalg.norm(result[:, 1:], axis=1) / np.sqrt(6)
    return result * actor.output_gain


def equilibrium_probes(actor, teacher, plan, split):
    features, targets, inputs, axes, residuals = [], [], [], [], []
    for axis in range(6):
        magnitudes = plan[('force_' if axis < 3 else 'moment_') + split + '_magnitudes']
        for magnitude in magnitudes:
            for sign in ((1,) if magnitude == 0 else (-1, 1)):
                wrench = np.zeros(6)
                wrench[axis] = sign * magnitude
                obs = np.zeros(48)
                obs[39:45] = wrench
                actor.reset()
                for _ in range(plan['fixed_point_steps']):
                    feature = actor.features(obs)
                state = actor.state.copy()
                actor.features(obs)
                residuals.append(float(np.max(np.abs(actor.state - state))))
                # For an unsaturated position at constant load, the teacher's
                # tanh wrench and tanh spring invert exactly. No online teacher
                # or equilibrium table is added to the deployed actor.
                offset = np.sign(wrench) * np.maximum(np.abs(wrench) - teacher.deadband, 0.) / teacher.k
                assert np.all(np.abs(offset) < teacher.xmax)
                action = np.zeros(7)
                action[1:] = np.clip(teacher.offset_gain * offset / teacher.action_limits, -1., 1.)
                action[0] = np.linalg.norm(action[1:]) / np.sqrt(6)
                features.append(feature)
                targets.append(action * actor.output_gain)
                inputs.append(wrench)
                axes.append(axis)
    assert max(residuals) < 1e-10
    return np.asarray(features), np.asarray(targets), np.asarray(inputs), np.asarray(axes), np.asarray(residuals)


def main():
    plan_path = ROOT / 'configs/esn_office_equilibrium_20260927.json'
    plan = json.loads(plan_path.read_text())
    model = ROOT / plan['parent']
    history_path = ROOT / plan['history']
    out = ROOT / 'outputs/esn_office_equilibrium_20260927'
    out.mkdir(exist_ok=False)
    assert digest(model) == plan['parent_sha256']
    parent = OfficeVMCMemoryESN(model)
    candidate = OfficeVMCMemoryESN(model)
    teacher = SixDVirtualDynamics({})
    with np.load(history_path) as history:
        wrench = history['wrench'].copy()
        target = history['teacher_action'].copy() * parent.output_gain
        train = history['train'].copy()
        episode = history['episode'].copy()
    with np.load(model) as checkpoint:
        fields = {key: checkpoint[key].copy() for key in checkpoint.files}
    original = json.loads(str(fields['metadata']))['original_training_metadata']
    starts = set(np.flatnonzero(np.r_[True, episode[1:] != episode[:-1]]).tolist())
    offset = original['episodes'] * original['steps_per_episode']
    for trace in original['development_traces']:
        starts.add(offset)
        offset += trace['samples']
    assert offset == len(wrench)
    features = []
    for index, value in enumerate(wrench):
        if index in starts:
            parent.reset()
        obs = np.zeros(48)
        obs[39:45] = value
        features.append(parent.features(obs))
    features = np.asarray(features)
    eqx, eqy, eqw, eqaxis, eqres = equilibrium_probes(parent, teacher, plan, 'train')
    checkx, checky, checkw, checkaxis, checkres = equilibrium_probes(parent, teacher, plan, 'check')
    # Validate the equilibrium formula against the teacher's actual integrator.
    teacher.reset()
    for _ in range(800):
        converged = teacher.act(np.array([2., -2., 3., .1, -.2, .3]), .04) * parent.output_gain
    eqoffset = np.array([1.8, -1.8, 2.8, .07, -.17, .27]) / teacher.k
    expected = np.r_[0., teacher.offset_gain * eqoffset / teacher.action_limits] * parent.output_gain
    expected[0] = np.linalg.norm(expected[1:]) / np.sqrt(6)
    np.testing.assert_allclose(converged, expected, atol=1e-10, rtol=0)
    importance = np.ones(len(features))
    importance[original['episodes'] * original['steps_per_episode']:] = plan['history_development_importance']
    importance = importance[train]
    importance /= importance.sum()
    target_logits = np.arctanh(np.clip(eqy / parent.output_gain, -.98, .98))
    base_logits = logits(parent, eqx)
    corrections = []
    for axis, reservoir_indices in enumerate(np.array_split(np.arange(128), 6)):
        indices = np.r_[axis, 6 + reservoir_indices]
        normalization = parent.feature_scale[indices]
        dynamic = features[train][:, indices] / normalization
        static = eqx[eqaxis == axis][:, indices] / normalization
        desired = (target_logits - base_logits)[eqaxis == axis, axis + 1]
        weight = plan['equilibrium_weight'] / len(static)
        matrix = dynamic.T @ (importance[:, None] * dynamic) + weight * static.T @ static
        matrix += plan['ridge'] * np.eye(len(indices))
        delta = np.linalg.solve(matrix, weight * static.T @ desired)
        candidate.weights[indices, axis + 1] += delta / normalization
        corrections.append(delta)
    before = actions(parent, features)
    after = actions(candidate, features)
    eq_before, eq_after = actions(parent, eqx), actions(candidate, eqx)
    check_before, check_after = actions(parent, checkx), actions(candidate, checkx)
    def rmse(x, y):
        return float(np.sqrt(np.mean((x - y) ** 2)))
    validation_before, validation_after = rmse(before[~train], target[~train]), rmse(after[~train], target[~train])
    stationary_before, stationary_after = rmse(check_before, checky), rmse(check_after, checky)
    accepted = bool(stationary_after < stationary_before and validation_after <= 1.1 * validation_before)
    candidate.reset()
    np.testing.assert_array_equal(candidate.act(np.zeros(48)), np.zeros(7))
    for axis in range(6):
        candidate.reset()
        obs = np.zeros(48)
        obs[39 + axis] = 1.
        action = candidate.act(obs)
        np.testing.assert_array_equal(np.delete(action[1:], axis), np.zeros(5))
    summary = dict(candidate='R36_equilibrium_linear_correction', seed=plan['seed'],
                   offline_criteria_passed=accepted, promoted=False, simulations_run=0,
                   parent_sha256=digest(model), history_sha256=digest(history_path),
                   plan_sha256=digest(plan_path), source_sha256=digest(Path(__file__)),
                   validation_teacher_rmse_before=validation_before, validation_teacher_rmse_after=validation_after,
                   dynamic_prediction_change_rmse=rmse(before, after),
                   equilibrium_train_rmse_before=rmse(eq_before, eqy), equilibrium_train_rmse_after=rmse(eq_after, eqy),
                   equilibrium_interpolation_rmse_before=stationary_before, equilibrium_interpolation_rmse_after=stationary_after,
                   equilibrium_wrong_sign_before=int(np.sum(check_before[:, 1:] * checkw < -1e-12)),
                   equilibrium_wrong_sign_after=int(np.sum(check_after[:, 1:] * checkw < -1e-12)),
                   exact_zero_and_axis_isolation=True, max_fixed_point_residual=float(max(eqres.max(), checkres.max())),
                   caveats=['Development-only interpolation is not blind validation.',
                            'Constant-force errors do not establish the cause of any closed-loop task failure.',
                            'No contact-before-observation benefit is possible from this force-only readout correction.',
                            'Frozen reservoir and nonlinear readout; only signed-axis linear readout changed.'])
    fields['weights'] = candidate.weights
    fields['metadata'] = np.array(json.dumps(summary))
    np.savez_compressed(out / 'model.npz', **fields)
    reloaded = OfficeVMCMemoryESN(out / 'model.npz')
    for key in ('win', 'w', 'leak', 'scale', 'hidden_w', 'output_w', 'feature_scale'):
        np.testing.assert_array_equal(getattr(parent, key), getattr(reloaded, key))
    assert reloaded.output_gain == parent.output_gain
    np.testing.assert_allclose(actions(reloaded, checkx), check_after, atol=1e-14, rtol=0)
    np.savez_compressed(out / 'offline_probes.npz',
                        equilibrium_wrench=eqw, equilibrium_features=eqx, equilibrium_target=eqy,
                        equilibrium_before=eq_before, equilibrium_after=eq_after,
                        check_wrench=checkw, check_features=checkx, check_target=checky,
                        check_before=check_before, check_after=check_after,
                        dynamic_before=before, dynamic_after=after, dynamic_target=target, train=train)
    summary['candidate_sha256'] = digest(out / 'model.npz')
    summary['raw_probe_sha256'] = digest(out / 'offline_probes.npz')
    (out / 'FIT_REPORT.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
