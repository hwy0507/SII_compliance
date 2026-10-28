"""Same-world instrumentation for the baseline branch's exact classical laws.

Keeps impedance's distinct servo torque law. Recorded policy/parameter traces
are consistency checks, not an independent full-physics actor replay.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import numpy as np
import paper_office_worker_20261002 as office

worker = office.worker


def install_policy(parameter_source, controller, config, output, policy_factory=None):
    source = worker.ROOT/'scripts/validate_office_apparatus_v5_20260917.py'
    original = source.read_text()
    replacements = [
        ('def run(a):', 'def run(a, policy_factory=None):'),
        ('    abort_reason=None\n    for step_index',
         '    external_policy=policy_factory(env) if policy_factory else None\n    abort_reason=None\n    for step_index'),
        ('        interval_peak[:]=0.;interval_impulse[:]=0.\n        env.step(applied)',
         "        if external_policy is not None:\n            if esn or teacher or hybrid_teacher:raise ValueError('Exclusive baseline policy required')\n            applied=np.asarray(external_policy.act(observation.copy()),dtype=float)\n            if applied.shape!=(7,) or not np.isfinite(applied).all() or np.max(abs(applied))>1.000001:raise ValueError('Invalid baseline action')\n            signal.update(applied_action=applied.copy(),baseline_action=applied.copy())\n        interval_peak[:]=0.;interval_impulse[:]=0.\n        env.step(applied)"),
        ("    result['metrics']=metrics.save(",
         "    if external_policy is not None:\n        result['controller']=external_policy.label\n        result['baseline_policy']=external_policy.finish(a.output.parent)\n    result['metrics']=metrics.save(")]
    executed = original
    for old, new in replacements:
        assert executed.count(old) == 1, old
        executed = executed.replace(old, new)
    # Use the module namespace so subsequent instrumentation and observation
    # capture are identical to the standard worker's runtime hooks.
    exec(compile(executed, str(source)+'[classical-policy-seam]', 'exec'), worker.evaluator.__dict__)
    run = worker.evaluator.run
    if policy_factory is not None:
        def evaluate_external(args):
            args.teacher = 'none'
            if args.esn_model is not None:
                raise ValueError('External policy cannot mix with learned policy')
            worker.write(output/'external_runtime_settings.json', {k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()})
            return run(args, policy_factory=policy_factory)
        worker.evaluator.run = evaluate_external
        return executed, None, {}
    sys.path.insert(0, str(parameter_source))
    from controllers import ParameterController
    priors = json.loads((parameter_source/'PRIORS.json').read_text())
    prior = copy.deepcopy(priors['methods'][controller])
    if 'parameters' in config:
        theta = np.asarray(config['parameters'], float)
        bounds = np.asarray(prior['bounds'])
        assert theta.shape == (prior['action_dimension'],)
        assert np.isfinite(theta).all() and np.all(theta >= bounds[:, 0]) and np.all(theta <= bounds[:, 1])
        prior['center'] = theta.tolist()
    allowed = {'parameters'}
    if set(config)-allowed:
        raise ValueError('Unsupported baseline config')
    dependencies = {}
    for candidate in (parameter_source/'vendor').glob('*.py'):
        module = sys.modules.get(candidate.stem)
        if module is not None and getattr(module, '__file__', None):
            actual = Path(module.__file__)
            if candidate.stem != 'current_student_policy_20260921':
                assert worker.sha(actual) == worker.sha(candidate), candidate.stem+' baseline law changed'
            dependencies[candidate.stem] = dict(path=str(actual), sha256=worker.sha(actual))
    class Policy:
        label = 'paper fixed '+controller
        def __init__(self, env):
            self.controller = ParameterController(env, controller, prior)
            self.obs, self.actions = [], []
        def act(self, observation):
            self.obs.append(observation.copy())
            action = self.controller.act(observation, np.zeros(prior['action_dimension']))
            self.actions.append(action.copy())
            return action
        def finish(self, out):
            np.savez_compressed(out/'baseline_policy.npz', observation=np.asarray(self.obs), action=np.asarray(self.actions))
            return self.controller.save(out)
    def evaluate(args):
        args.teacher = 'none'
        if args.esn_model is not None:
            raise ValueError('Classical policy cannot mix with learned policy')
        # Worker records settings before invoking the wrapper; retain actual
        # executed settings separately and in rollout.json without falsifying it.
        worker.write(output/'classical_runtime_settings.json', {k:str(v) if isinstance(v,Path) else v for k,v in vars(args).items()})
        return run(args, policy_factory=Policy)
    worker.evaluator.run = evaluate
    return executed, prior, dependencies


def main():
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument('--v6-input', type=Path, required=True)
    p.add_argument('--parameter-source', type=Path, required=True)
    p.add_argument('--controller', choices=('admittance', 'impedance', 'vmc'), required=True)
    p.add_argument('--physics-dt',type=float,default=.0001)
    p.add_argument('--condition-file',type=Path)
    p.add_argument('--condition-id')
    a, rest = p.parse_known_args()
    output = Path(rest[rest.index('--output')+1]).resolve()
    config = json.loads(Path(rest[rest.index('--config')+1]).read_text())
    parameter = a.parameter_source.resolve()
    parameter_hashes = {str(f.relative_to(parameter)):worker.sha(f) for f in parameter.rglob('*')
                        if f.is_file() and f.suffix in ('.py', '.json')}
    evaluator_text, prior, dependencies = install_policy(parameter, a.controller, config, output)
    constructor_text, _ = office.install_binary(a.v6_input.resolve())
    expected,overrides,tier=office.evaluation_settings(a.v6_input.resolve(),a.physics_dt,a.condition_file,a.condition_id)
    worker.EXPECTED_MJB = expected
    worker.RUNTIME_ARGUMENT_OVERRIDES=dict(overrides,teacher='none')
    worker.EXTRA_SOURCE_FILES = [Path(__file__), Path(office.__file__)]
    worker.RUNTIME_PROVENANCE = dict(world='office-validation-v6', **tier,
        upstream_baseline='ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6', parameter_source=str(parameter),
        parameter_source_sha256=parameter_hashes, parameter_prior=prior, imported_dependencies=dependencies,
        executed_evaluator_sha256=hashlib.sha256(evaluator_text.encode()).hexdigest(),
        executed_constructor_sha256=hashlib.sha256(constructor_text.encode()).hexdigest(), wrapper_argv=sys.argv.copy(),
        controller=a.controller, actual_teacher='none', actor_replay='Not performed; policy trace consistency and common action filter independently audited')
    office.instrument(output)
    def audit(run, config, checkpoint, ablation):
        result = worker.audit(run, config, checkpoint, ablation, skip_actor_replay=True)
        with np.load(run/'baseline_policy.npz') as policy, np.load(run/'rollout.npz') as trace:
            np.testing.assert_array_equal(policy['observation'], trace['observation'])
            np.testing.assert_array_equal(policy['action'], trace['applied_action'])
        result.update(policy_trace_consistency_max_abs=0., controller=a.controller,
                      parameter_source_sha256=parameter_hashes)
        worker.write(run/'AUDIT.json', result)
        return result
    worker.AUDIT_FUNCTION = audit
    sys.argv = [sys.argv[0], *rest]
    try:
        worker.main()
    finally:
        if output.exists():
            (output/'executed_evaluator.py.txt').write_text(evaluator_text)
            (output/'executed_fr3_scene.py.txt').write_text(constructor_text)
            target = output/'parameter_source'
            target.mkdir(exist_ok=False)
            for name, digest in parameter_hashes.items():
                assert worker.sha(parameter/name) == digest, 'Baseline source changed'
                destination = target/name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(parameter/name, destination)


if __name__ == '__main__':
    main()
