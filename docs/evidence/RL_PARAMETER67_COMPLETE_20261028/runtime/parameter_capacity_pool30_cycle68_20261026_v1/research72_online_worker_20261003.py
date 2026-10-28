"""One native-v6 RL training episode with an isolated observation/action pipe.

Actor receives only canonical48. Reward-only interval physics/potential travels
in separate IPC fields; the agent runner must never concatenate it to observation.
The shared evaluator, world, failure gates and complete-horizon rule stay intact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import paper_classical_worker_20261002 as classical

office=classical.office
worker=office.worker


def main():
    p=argparse.ArgumentParser(add_help=False)
    p.add_argument('--v6-input',type=Path,required=True)
    p.add_argument('--physics-dt',type=float,default=.00005)
    p.add_argument('--parameter-source',type=Path,required=True)
    p.add_argument('--controller',choices=('admittance','impedance','vmc'))
    a,rest=p.parse_known_args()
    out=Path(rest[rest.index('--output')+1]).resolve();channel=sys.stdout
    raw_observation=worker.evaluator.canonical_observation
    shared={};policies=[]
    def send(value):
        print(json.dumps(value,allow_nan=False,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item()),file=channel,flush=True)
    sys.path.insert(0,str(a.parameter_source))
    from controllers import ParameterController
    priors=json.loads((a.parameter_source/'PRIORS.json').read_text())
    prior=priors['methods'][a.controller] if a.controller else None
    dimension=prior['action_dimension'] if prior else 7
    def potential(env):
        task=env.reference
        error=float(np.linalg.norm(env.data.xpos[env._hand_id]-task.goals[task.index]))
        return float((task.index+1/(1+error/.04))/len(task.goals))
    def interval():
        metrics=shared['metrics'];begin=shared.get('previous_count',0);end=metrics.count
        shared['previous_count']=end
        if begin==end:return None
        arrays=metrics.arrays;dt=arrays['dt'][begin:end].astype(float)
        error=arrays['error'][begin:end].astype(float);e2=np.sum(error**2,axis=1)
        tau=np.abs(arrays['qfrc_actuator'][begin:end].astype(float))
        limits=np.asarray(metrics.env.torque_limits)[:7]
        return dict(elapsed_s=float(dt.sum()),error_integral=float(dt@e2),
            bounded_error_integral=float(dt@(e2/(.12**2+e2))),peak_torque_ratio=float(np.max(tau/limits)),
            peak_torque_nm_per_joint=tau.max(0),max_position_error_m=float(np.sqrt(e2.max())),substeps=end-begin,
            executed_action=shared['last_filtered'].copy(),potential=potential(metrics.env))
    class Policy:
        label='office-trained parameter '+a.controller if a.controller else 'office-trained direct RL'
        def __init__(self,env):
            self.env=env;self.controller=ParameterController(env,a.controller,prior) if prior else None
            self.observations=[];self.actions=[];self.raw=[];self.intervals=[];policies.append(self)
        def act(self,observation):
            iv=interval();self.intervals.append(iv)
            send(dict(kind='observation',observation=observation,interval=iv,potential=potential(self.env)))
            line=sys.stdin.readline()
            if not line:raise RuntimeError('Training action pipe closed; incomplete episode retained')
            action=np.asarray(json.loads(line)['action'],float)
            if action.shape!=(dimension,) or not np.isfinite(action).all() or np.max(np.abs(action))>1.000001:
                raise ValueError('Invalid direct/parameter action contract')
            executed=self.controller.act(observation,action) if self.controller else action
            self.observations.append(observation.copy());self.raw.append(action.copy());self.actions.append(executed.copy())
            return executed
        def finish(self,output):
            env=self.env;d=env.data;m=env.model;e=worker.evaluator
            command=env._wbc_command(0.);rotation=d.xmat[env._hand_id].reshape(3,3)
            error=np.r_[command.target_position_m-d.xpos[env._hand_id],e.so3_log(command.target_rotation@rotation.T)]
            # Save before the unchanged evaluator closes model/data. Last
            # estimated load is explicitly approximate at the finite terminal;
            # the terminal value is never bootstrapped by the learner.
            load=np.asarray(self.observations[-1][32:39])
            wrench=e.equivalent_tool_wrench(e.body_jacobian(m,d,env._hand_id),load)
            shared['terminal_observation']=raw_observation(d.qpos,d.qvel,command.task_twist_world,error,
                e.body_twist(m,d,env._hand_id),load,wrench,env.reference.path_direction)
            shared['terminal_interval']=interval();self.intervals.append(shared['terminal_interval'])
            worker.write(output/'RL_INTERVALS.json',self.intervals)
            np.savez_compressed(output/'baseline_policy.npz',observation=np.asarray(self.observations),
                action=np.asarray(self.actions),raw_action=np.asarray(self.raw))
            return dict(training=True,actor_input='canonical48 only',actor_observes_reward_metadata=False,
                parameters=self.controller.save(output) if self.controller else None)
    executed_evaluator,_,_=classical.install_policy(None,None,{},out,policy_factory=Policy)
    executed_constructor,_=office.install_binary(a.v6_input)
    expected,overrides,provenance=office.evaluation_settings(a.v6_input,a.physics_dt)
    assert provenance['data_role']=='train', 'Online updates only on registered train identities'
    worker.EXPECTED_MJB=expected;worker.RUNTIME_ARGUMENT_OVERRIDES=dict(overrides,teacher='none')
    worker.EXTRA_SOURCE_FILES=[Path(__file__),Path(classical.__file__),Path(office.__file__)]
    dependencies={str(p):worker.sha(p) for p in a.parameter_source.rglob('*') if p.is_file() and p.suffix in ('.py','.json')}
    worker.RUNTIME_PROVENANCE=dict(world='office-validation-v6',**provenance,online_training=True,
        controller=a.controller,parameter_sources=dependencies,actor_input='canonical48 only',
        executed_evaluator_sha256=hashlib.sha256(executed_evaluator.encode()).hexdigest(),
        executed_constructor_sha256=hashlib.sha256(executed_constructor.encode()).hexdigest())
    office.instrument(out)
    parent=worker.evaluator.EpisodeMetrics
    class Metrics(parent):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);shared['metrics']=self
    worker.evaluator.EpisodeMetrics=Metrics
    original_filter=worker.VelocityResidualActionFilter.filter
    def remember_filter(self,action,dt):
        result=original_filter(self,action,dt)
        shared['last_filtered']=np.r_[(1-result.wbc_scale)/(1-self.config.minimum_wbc_scale),
            result.cartesian_yield_twist/np.r_[np.full(3,self.config.maximum_linear_yield_mps),np.full(3,self.config.maximum_angular_yield_radps)]]
        return result
    worker.VelocityResidualActionFilter.filter=remember_filter
    def audit(run,config,unused,ablation):
        result=worker.audit(run,config,None,ablation,skip_actor_replay=True)
        with np.load(run/'baseline_policy.npz') as policy,np.load(run/'rollout.npz') as trace:
            np.testing.assert_array_equal(policy['observation'],trace['observation'])
            np.testing.assert_array_equal(policy['action'],trace['applied_action'])
        result.update(training_policy_trace_consistency_max_abs=0.,training=True)
        worker.write(run/'AUDIT.json',result);return result
    worker.AUDIT_FUNCTION=audit;sys.argv=[sys.argv[0],*rest]
    try:
        worker.main()
        assert all(worker.sha(Path(k))==h for k,h in dependencies.items())
        result=json.loads((out/'rollout.json').read_text())
        send(dict(kind='terminal',observation=shared['terminal_observation'],interval=shared['terminal_interval'],
            result={k:result[k] for k in ('task_success','strict_success','full_task_horizon_completed','physical_valid','abort_reason') if k in result},
            terminal_observer='last available estimate; finite-horizon terminal has no value bootstrap'))
    except BaseException as exc:
        send(dict(kind='error',error=repr(exc)));raise
    finally:
        worker.VelocityResidualActionFilter.filter=original_filter
        if out.exists():
            (out/'executed_evaluator.py.txt').write_text(executed_evaluator)
            (out/'executed_fr3_scene.py.txt').write_text(executed_constructor)


if __name__=='__main__':main()
