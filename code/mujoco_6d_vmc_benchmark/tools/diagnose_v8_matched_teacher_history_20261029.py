"""Diagnose nine locked actors on one successful, previously inspected history.

No training, checkpoint selection, physical integration or new labels for fitting.
Teacher-history prediction errors do not certify the resulting closed loop.
"""
import argparse
from datetime import datetime, timezone
import inspect
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np

RUNTIME = Path(__file__).resolve().parents[1]/'outputs/special_scene_frozen108_20261029_v8/source'
sys.path.insert(0,str(RUNTIME/'scripts'))

from collect_special_scene_actions_20261028 import ROOT, read, sha, write
from review_repaired_student_closures_20261029 import error_stats, teacher_replay
from prepare_special_frozen_test_20261028 import manifest


def frozen_actor(model):
    filename,classname = ('office_vmc_memory_esn_20260927.py','OfficeVMCMemoryESN') if model['family']=='esn_ridge' else ('office_mlp_rnn_20261002.py','OfficeMLPRNN')
    name = 'v8_frozen_'+classname
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name,RUNTIME/'scripts'/filename)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return getattr(sys.modules[name],classname)(model['checkpoint'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    assert not output.exists()
    teacher_root = ROOT/'outputs/special_teacher_vertical_damping_20261029_v1'
    teacher_run = teacher_root/'vertical_damping_office000'
    matrix = ROOT/'outputs/special_scene_frozen108_20261029_v8'
    preparation = ROOT/'outputs/special_scene_frozen108_preparation_20261029_v8'
    assert manifest(RUNTIME) == read(preparation/'REGISTRATION.json')['physics_source_sha256']
    training = ROOT/'outputs/special_scene_retrain_20261029_v8'
    lock = read(training/'MODEL_LOCK.json')
    assert sha(training/'MODEL_LOCK.json') == sha(matrix/'INPUT_MODEL_LOCK.json')
    teacher_execution = read(teacher_run/'execution.json')
    teacher_audit = read(teacher_run/'AUDIT.json')
    assert teacher_execution['status'] == 'complete'
    assert teacher_audit['task_success'] and teacher_audit['strict_success']
    for name,key in [('rollout.npz','trace_sha256'),('execution_chain.npz','chain_sha256'),
                     ('rollout.mjb','model_sha256'),('rollout_metrics/substep_metrics.npz','metrics_sha256')]:
        assert sha(teacher_run/name) == teacher_audit[key]
    for name,h in teacher_execution['source_sha256'].items():
        assert sha(teacher_root/'source'/name) == h
    config = teacher_root/'teacher_vertical_damping.json'
    collection = ROOT/'outputs/special_scene_vmc_collection_20261029_v8'
    collection_config = Path(read(collection/'COLLECTION_PLAN.json')['teacher_config'])
    assert sha(config) == sha(collection_config)
    with np.load(teacher_run/'rollout.npz',allow_pickle=False) as z:
        obs,time,stage = [z[k].copy() for k in ('observation','time','stage')]
    with np.load(teacher_run/'execution_chain.npz',allow_pickle=False) as z:
        target = z['requested_action'].copy()
    actual,_ = teacher_replay(read(config),obs)
    np.testing.assert_array_equal(actual,target)
    assert obs.shape == (1375,48) and target.shape == (1375,7)
    state = read(matrix/'execution.json')
    completed = {r['method']:r for r in state['results'] if r['condition'].endswith('_000')}
    # The first-step equality check is before any model-induced trajectory divergence.
    provenance_fields = ('model_sha256','physics_dt_s','research_condition','research_protocol_sha256',
                         'condition_file_sha256','executed_constructor_sha256')
    early = np.arange(len(time)) < 4
    assert np.all(stage[early] == 0) and np.count_nonzero(target[early]) == 0
    results, arrays, source_hashes = [], dict(observation=obs,time=time,stage=stage,teacher_action=target), {}
    for model in lock['models']:
        checkpoint = Path(model['checkpoint'])
        assert sha(checkpoint) == model['checkpoint_sha256']
        actor = frozen_actor(model)
        module = Path(inspect.getfile(type(actor)))
        source_hashes[str(module)] = sha(module)
        relative = module.relative_to(RUNTIME)
        assert sha(matrix/'source'/relative) == sha(module)
        actor.reset()
        prediction = np.asarray([actor.act(o) for o in obs])
        arrays[model['name']] = prediction
        # Scalar verification is independent of the vectorized error reduction.
        scalar_mse = sum((float(p)-float(t))**2 for p,t in zip(prediction.flat,target.flat))/target.size
        stats = error_stats(prediction,target)
        assert np.isclose(scalar_mse,stats['mse'],rtol=1e-12,atol=1e-15)
        row = dict(name=model['name'],family=model['family'],seed=model['seed'],
            checkpoint_sha256=sha(checkpoint),teacher_history_error=stats,
            first4=error_stats(prediction[early],target[early]),
            first_prediction=prediction[0].tolist(),
            stages=[dict(stage=int(s),**error_stats(prediction[stage==s],target[stage==s]))
                    for s in sorted(set(stage.tolist()))])
        probes = []
        for axis in range(3):
            for sign in (-1,1):
                probe = np.zeros(48)
                probe[45+axis] = sign
                actor.reset()
                requested = actor.act(probe)
                teacher_requested,_ = teacher_replay(read(config),probe[None,:])
                np.testing.assert_array_equal(teacher_requested[0],np.zeros(7))
                probes.append(dict(axis=axis,sign=sign,student_action=requested.tolist(),
                                   teacher_action=teacher_requested[0].tolist()))
        row['synthetic_zero_load_direction_probes'] = probes
        if model['name'] in completed:
            run = Path(completed[model['name']]['run'])
            execution = read(run/'execution.json')
            for k in provenance_fields:
                assert execution['runtime_provenance'][k] == teacher_execution['runtime_provenance'][k], k
            with np.load(run/'rollout.npz',allow_pickle=False) as z:
                student_obs = z['observation'].copy()
            with np.load(run/'execution_chain.npz',allow_pickle=False) as z:
                student_actions = z['requested_action'].copy()
            np.testing.assert_array_equal(student_obs[0],obs[0])
            np.testing.assert_array_equal(student_actions[0],prediction[0])
            actor.reset()
            np.testing.assert_array_equal(np.asarray([actor.act(o) for o in student_obs]),student_actions)
            counterfactual,_ = teacher_replay(read(config),student_obs)
            row['completed_student'] = dict(run=str(run), trace_sha256=sha(run/'rollout.npz'),
                execution_sha256=sha(run/'execution.json'),chain_sha256=sha(run/'execution_chain.npz'),
                first_observation_exactly_equal=True,first_action_exactly_reproduced=True,
                actor_replay_exact=True,counterfactual_error=error_stats(student_actions,counterfactual))
        results.append(row)
    inputs = {str(p):sha(p) for p in (config,collection_config,preparation/'REGISTRATION.json',teacher_run/'execution.json',
        teacher_run/'AUDIT.json',teacher_run/'rollout.npz',teacher_run/'execution_chain.npz',
        training/'MODEL_LOCK.json',collection/'COLLECTION_PLAN.json')}
    output.mkdir(parents=True)
    np.savez_compressed(output/'PREDICTIONS.npz',**arrays)
    with np.load(output/'PREDICTIONS.npz',allow_pickle=False) as z:
        assert set(z.files) == set(arrays)
        for k,v in arrays.items(): np.testing.assert_array_equal(z[k],v)
    write(output/'REVIEW.json',dict(status='matched_successful_teacher_history_diagnostic',
        created_utc=datetime.now(timezone.utc).isoformat(),rows=results,input_hashes=inputs,
        teacher_replay_exact=True,source_hashes=source_hashes,diagnostic_source_sha256=sha(Path(__file__)),
        prediction_sha256=sha(output/'PREDICTIONS.npz'),frames=len(obs),
        limitation='Already inspected condition000; nine frozen models, no selection or fitting. '
        'First observation comparison precedes trajectory divergence for completed student rows. '
        'Later teacher-on-student-history predictions are counterfactual, not executed dynamics. '
        'Six reset/zero-load/unit-direction probes are synthetic network checks, not demonstrations or fitting labels. '
        'The diagnostic does not uniquely establish the failure cause or certify success.'))
    print(json.dumps(dict(status='matched_successful_teacher_history_diagnostic',models=len(results))))


if __name__ == '__main__':
    main()
