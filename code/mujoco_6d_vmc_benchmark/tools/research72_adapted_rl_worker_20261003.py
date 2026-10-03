"""Frozen evaluation of the new office-trained official SimbaV2 cohort."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import paper_classical_worker_20261002 as classical

office=classical.office;worker=office.worker


def normalization_hash(agent):
    h=hashlib.sha256()
    for prefix,norm in [('obs',agent.observation_normalizer.obs_rms),('reward',agent.reward_normalizer.G_rms)]:
        for key in ('mean','var','count'):
            value=np.asarray(getattr(norm,key));h.update((prefix+key+str(value.shape)+str(value.dtype)).encode());h.update(value.tobytes())
    for key in ('G','G_r_max'):
        value=np.asarray(getattr(agent.reward_normalizer,key));h.update((key+str(value.shape)+str(value.dtype)).encode());h.update(value.tobytes())
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument('--v6-input',type=Path,required=True);p.add_argument('--physics-dt',type=float,default=.00005)
    p.add_argument('--agent-checkpoint',type=Path,required=True);p.add_argument('--checkpoint-manifest',type=Path,required=True)
    p.add_argument('--parameter-source',type=Path,required=True);p.add_argument('--controller',choices=('admittance','impedance','vmc'))
    a,rest=p.parse_known_args();out=Path(rest[rest.index('--output')+1]).resolve()
    expected=json.loads(a.checkpoint_manifest.read_text())
    assert expected['checkpoint']==str(a.agent_checkpoint.resolve())
    assert expected['controller']==a.controller
    assert expected['hashes'] and 'official_agent_state.json' in expected['hashes']
    for name,h in expected['hashes'].items():assert worker.sha(a.agent_checkpoint/name)==h
    cp=json.loads((a.agent_checkpoint/'official_agent_state.json').read_text());cfg=cp['config'];utd=cp['utd']
    sys.path.insert(0,str(a.parameter_source))
    from official_parameter_agent import OfficialParameterAgent
    from controllers import ParameterController
    priors=json.loads((a.parameter_source/'PRIORS.json').read_text())
    prior=priors['methods'][a.controller] if a.controller else None
    assert cfg['action_dimension']==(prior['action_dimension'] if prior else 7)
    agent=OfficialParameterAgent(seed=cfg['seed'],total_steps=int(cfg['learning_rate_decay_step'])//utd,utd=utd,
        gamma=cfg['gamma'],entropy_coef=cfg['temp_target_entropy_coef'],initial_temperature=cfg['temp_initial_value'],action_dimension=cfg['action_dimension'])
    agent.load(a.agent_checkpoint);before=agent.diagnostics();norm_before=normalization_hash(agent)
    class Policy:
        label='office-adapted official SimbaV2 '+(a.controller or 'direct')
        def __init__(self,env):
            self.controller=ParameterController(env,a.controller,prior) if prior else None;self.obs=[];self.raw=[];self.actions=[]
        def act(self,obs):
            raw=agent.sample_action(obs,training=False);action=self.controller.act(obs,raw) if self.controller else raw
            self.obs.append(obs.copy());self.raw.append(raw.copy());self.actions.append(action.copy());return action
        def finish(self,output):
            predictions=np.asarray([agent.sample_action(o,training=False) for o in self.obs])
            np.testing.assert_array_equal(predictions,self.raw)
            assert before==agent.diagnostics() and norm_before==normalization_hash(agent)
            np.savez_compressed(output/'baseline_policy.npz',observation=np.asarray(self.obs),action=np.asarray(self.actions),raw_action=np.asarray(self.raw))
            return dict(training=False,normalization_unchanged=True,raw_actor_replay_max_abs=0.,
                parameters=self.controller.save(output) if self.controller else None)
    evaluator,_,_=classical.install_policy(None,None,{},out,policy_factory=Policy)
    constructor,_=office.install_binary(a.v6_input)
    model,overrides,provenance=office.evaluation_settings(a.v6_input,a.physics_dt)
    worker.EXPECTED_MJB=model;worker.RUNTIME_ARGUMENT_OVERRIDES=dict(overrides,teacher='none')
    worker.EXTRA_SOURCE_FILES=[Path(__file__),Path(classical.__file__),Path(office.__file__)]
    sources={str(f):worker.sha(f) for f in a.parameter_source.rglob('*') if f.is_file() and f.suffix in ('.py','.json')}
    worker.RUNTIME_PROVENANCE=dict(world='office-validation-v6',**provenance,adapted_rl_checkpoint=expected,
        checkpoint_manifest_sha256=worker.sha(a.checkpoint_manifest),agent_source_sha256=sources,normalization_sha256=norm_before,
        executed_evaluator_sha256=hashlib.sha256(evaluator.encode()).hexdigest(),
        executed_constructor_sha256=hashlib.sha256(constructor.encode()).hexdigest(),training=False)
    office.instrument(out)
    def audit(run,config,unused,ablation):
        result=worker.audit(run,config,None,ablation,skip_actor_replay=True)
        with np.load(run/'baseline_policy.npz') as policy,np.load(run/'rollout.npz') as trace:
            np.testing.assert_array_equal(policy['observation'],trace['observation']);np.testing.assert_array_equal(policy['action'],trace['applied_action'])
        result.update(raw_actor_replay_max_abs=0.,normalization_unchanged=True,adapted_rl=True)
        worker.write(run/'AUDIT.json',result);return result
    worker.AUDIT_FUNCTION=audit;sys.argv=[sys.argv[0],*rest]
    try:
        worker.main()
        assert all(worker.sha(Path(k))==h for k,h in sources.items())
        assert all(worker.sha(a.agent_checkpoint/k)==h for k,h in expected['hashes'].items())
    finally:
        if out.exists():
            (out/'executed_evaluator.py.txt').write_text(evaluator);(out/'executed_fr3_scene.py.txt').write_text(constructor)
            worker.write(out/'ADAPTED_RL_CHECKPOINT.json',expected)


if __name__=='__main__':main()
