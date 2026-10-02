"""Read-only evaluation of pinned baseline RL checkpoints on their native host.

No training, normalization adaptation or controller replacement. Geometry,
common action filter, metrics and gates match the local paper workers.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace
import numpy as np
import paper_classical_worker_20261002 as classical

office=classical.office
worker=office.worker


def main():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument('--v6-input',type=Path,required=True)
    p.add_argument('--bridge',type=Path,required=True)
    p.add_argument('--case',required=True)
    p.add_argument('--physics-dt',type=float,default=.0001)
    p.add_argument('--condition-file',type=Path)
    p.add_argument('--condition-id')
    a,rest=p.parse_known_args()
    output=Path(rest[rest.index('--output')+1]).resolve()
    v6=a.v6_input.resolve()
    protocol=json.loads((v6/'PROTOCOL.json').read_text())
    case=next(x for x in protocol['cases'] if x['id']==a.case)
    assert case['method'] in ('direct_rl','parameter_rl')
    checkpoint=Path(case['checkpoint'])
    for name,digest in case['checkpoint_hashes'].items():
        assert worker.sha(checkpoint/name)==digest, 'Checkpoint changed'
    spec=importlib.util.spec_from_file_location('paper_upstream_baseline_bridge',a.bridge)
    bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)
    policy_args=SimpleNamespace(method=case['method'],controller=case['controller'],checkpoint=checkpoint)
    policy_root=bridge.PARAMETER if case['method']=='parameter_rl' else bridge.DIRECT
    policy_sources={str(f):worker.sha(f) for f in policy_root.rglob('*') if f.is_file() and f.suffix in ('.py','.json')}
    policies=[]
    class RecordedPolicy(bridge.Policy):
        def __init__(self,env):
            super().__init__(env,policy_args);policies.append(self)
        def finish(self,out):
            result=super().finish(out)
            prediction=np.asarray([self.agent.sample_action(o,training=False) for o in self.obs])
            expected=(np.asarray([r['raw_action'] for r in self.controller.shield.records])
                      if self.controller else np.asarray(self.actions))
            np.testing.assert_array_equal(prediction,expected)
            assert bridge.normalization_hash(self.agent)==self.normalization_before
            result.update(learned_actor_replay_max_abs=0.,parameter_controller_replay_performed=False if self.controller else None)
            return result
    evaluator_text,_,_=classical.install_policy(None,None,{},output,policy_factory=RecordedPolicy)
    constructor_text,_=office.install_binary(v6)
    expected,overrides,tier=office.evaluation_settings(v6,a.physics_dt,a.condition_file,a.condition_id)
    worker.EXPECTED_MJB=expected
    worker.RUNTIME_ARGUMENT_OVERRIDES=dict(overrides,teacher='none')
    worker.EXTRA_SOURCE_FILES=[Path(__file__),Path(classical.__file__),Path(office.__file__)]
    worker.RUNTIME_PROVENANCE=dict(world='office-validation-v6',**tier,
        upstream_baseline='ebb0e1e6a71ddbfe6fb763fd4dabe1278cfa4ac6',case=case,
        bridge_sha256=worker.sha(a.bridge),policy_source_sha256=policy_sources,
        executed_evaluator_sha256=hashlib.sha256(evaluator_text.encode()).hexdigest(),
        executed_constructor_sha256=hashlib.sha256(constructor_text.encode()).hexdigest(),wrapper_argv=sys.argv.copy(),
        actual_teacher='none',training=False)
    office.instrument(output)
    def audit(run,config,unused,ablation):
        result=worker.audit(run,config,None,ablation,skip_actor_replay=True)
        with np.load(run/'baseline_policy.npz') as policy,np.load(run/'rollout.npz') as trace:
            np.testing.assert_array_equal(policy['observation'],trace['observation'])
            np.testing.assert_array_equal(policy['action'],trace['applied_action'])
        result.update(policy_trace_consistency_max_abs=0.,learned_actor_replay_max_abs=0.,case=a.case)
        worker.write(run/'AUDIT.json',result)
        return result
    worker.AUDIT_FUNCTION=audit
    sys.argv=[sys.argv[0],*rest]
    try:
        worker.main()
        assert all(worker.sha(Path(path))==digest for path,digest in policy_sources.items())
    finally:
        if output.exists():
            (output/'executed_evaluator.py.txt').write_text(evaluator_text)
            (output/'executed_fr3_scene.py.txt').write_text(constructor_text)
            shutil.copy2(a.bridge,output/'upstream_bridge.py.txt')
            worker.write(output/'policy_source_manifest.json',policy_sources)


if __name__=='__main__':main()
