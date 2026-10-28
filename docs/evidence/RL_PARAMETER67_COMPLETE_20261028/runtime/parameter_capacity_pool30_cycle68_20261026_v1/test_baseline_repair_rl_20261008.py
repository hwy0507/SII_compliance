"""Synthetic official-agent gradient/logging/checkpoint contracts; no simulation.

This test is not training exposure, a performance score, or a convergence claim.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import numpy as np
from baseline_repair_rl_diagnostics_20261008 import flatten_metrics


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parameter-source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--action-dimension',type=int,choices=(5,7),default=7)
    a=p.parse_args();sys.path.insert(0,str(a.parameter_source))
    from official_parameter_agent import OfficialParameterAgent
    import jax
    def digest(tree):
        return hashlib.sha256(b''.join(np.asarray(x).tobytes() for x in jax.tree_util.tree_leaves(tree))).hexdigest()
    agent=OfficialParameterAgent(seed=2026100811,total_steps=200000,utd=2,gamma=.9995,
        entropy_coef=-2.,initial_temperature=.0001,action_dimension=a.action_dimension)
    rng=np.random.default_rng(119);observations=rng.normal(0,.1,(256,48)).astype(np.float32)
    actions=[]
    for index,obs in enumerate(observations):
        actions.append(agent.sample_action(obs,training=True))
        agent.consume_transition(float(index%3)*.001,index==255)
    batch=dict(observation=observations,action=np.asarray(actions),reward=rng.normal(0,.01,256).astype(np.float32),
        terminated=np.r_[np.zeros(255),1.].astype(np.float32),truncated=np.zeros(256,np.float32),
        next_observation=np.roll(observations,-1,axis=0))
    snapshots={k:v.copy() for k,v in batch.items()}
    before=digest(agent.raw_agent._actor.params);reports=[]
    for _ in range(3):
        info=agent.update(batch)
        info=flatten_metrics(info)
        assert all(np.isfinite(v) for v in info.values())
        reports.append(info)
    assert before!=digest(agent.raw_agent._actor.params), 'Actor parameters did not update'
    for k,v in snapshots.items():np.testing.assert_array_equal(v,batch[k])
    predicted=agent.sample_action(observations[0],training=False)
    diagnostics=agent.diagnostics()
    with tempfile.TemporaryDirectory(prefix='sii-rl-repair-contract-') as t:
        cp=Path(t)/'checkpoint';agent.save(cp)
        restored=OfficialParameterAgent(seed=2026100811,total_steps=200000,utd=2,gamma=.9995,
            entropy_coef=-2.,initial_temperature=.0001,action_dimension=a.action_dimension)
        restored.load(cp)
        np.testing.assert_array_equal(restored.sample_action(observations[0],training=False),predicted)
        assert restored.diagnostics()==diagnostics
    result=dict(status='passed',synthetic_updates=3,physics_steps=0,actor_updated=True,action_dimension=a.action_dimension,
        replay_inputs_immutable=True,checkpoint_prediction_exact=True,normalization_counters_exact=True,
        actual_optimizer_metrics=reports,scope='Synthetic contract only; not successful physics or RL convergence')
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(result))


if __name__=='__main__':main()
