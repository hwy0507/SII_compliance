"""Train-only mechanical sensitivity and optimizer diagnostics, no new rollouts.

These probes identify candidate learning difficulties, not causal evidence that
the task is impossible or that a controller cannot succeed.
"""
import argparse
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import json
import numpy as np
from rl_reward_diagnosis_audit_20261014 import read,write,sha,basic


def inspect(census,parameter_source):
    rows=census['episodes'];result=[]
    for method in sorted({r['method'] for r in rows}):
        latest=max((r for r in rows if r['method']==method),key=lambda r:r['step_after'])
        run=Path(latest['run']);segment=run.parent;spec=read(segment/'PROTOCOL.json')
        optimizer=segment/'optimizer.jsonl';tail=deque(maxlen=5000)
        with optimizer.open() as f:
            for line in f:
                if line.endswith('\n'):tail.append(json.loads(line))
        metrics=[r['metrics'] for r in tail]
        # Pinned upstream update_actor uses -alpha*entropy - mean(min Q).
        # update_temperature logs the same pre-update alpha. actor_bc_alpha=0.
        assert spec['agent_config']['actor_bc_alpha']==0
        q=[-m['actor/loss']-m['temperature/value']*m['actor/entropy'] for m in metrics]
        item=dict(method=method,episode=latest['episode'],run=str(run),steps=latest['step_after'],
            selection='latest complete training episode and last <=5000 optimizer updates, all historical methods',
            optimizer=dict(updates=len(tail),derived_actor_sample_soft_q=basic(q),
                entropy=basic([m['actor/entropy'] for m in metrics]),
                temperature=basic([m['temperature/value'] for m in metrics]),
                critic_cross_entropy=basic([m['critic/loss'] for m in metrics]),
                note='Q is minibatch entropy-regularized action value, not observed return or success. Positive Q alone does not prove overestimation; critic cross entropy need not converge to zero.'),
            optimizer_sha256=sha(optimizer),training_protocol_sha256=sha(segment/'PROTOCOL.json'))
        if spec['controller']:
            # Check the exact prior in this historical segment before probing.
            source=Path(spec['parameter_source']);assert sha(source/'PRIORS.json')==spec['prior_file_sha256']
            prior=read(source/'PRIORS.json')['methods'][spec['controller']]
            assert prior==read(parameter_source/'PRIORS.json')['methods'][spec['controller']]
            trace=read(run/'parameter_trace.json');center=np.asarray(prior['center']);bounds=np.asarray(prior['bounds'])
            raw=np.asarray([r['raw_action'] for r in trace]);old=np.asarray([r['previous_parameters'] for r in trace])
            expected=np.asarray([r['requested_parameters'] for r in trace])
            limit=prior['max_log_rate_per_s']*.04
            def mapping(action):
                span=np.where(action>=0,np.log(bounds[:,1]/center),np.log(center/bounds[:,0]))
                requested=center*np.exp(action*span)
                return np.clip(np.log(requested/old),-limit,limit)
            np.testing.assert_allclose(old*np.exp(mapping(raw)),expected,rtol=1e-12,atol=1e-12)
            flat=np.abs(mapping(np.clip(raw+.01,-1,1))-mapping(np.clip(raw-.01,-1,1)))<1e-10
            item['parameter_local_sensitivity']=dict(normalized_perturbation=.01,ticks=len(trace),
                all_dimensions_flat_fraction=float(flat.all(axis=1).mean()),
                per_dimension_flat_fraction=flat.mean(axis=0).tolist(),keys=prior['keys'],
                exact_rate_mapping_replay_passed=True,trace_sha256=sha(run/'parameter_trace.json'),
                interpretation='For a locally flat dimension, these nearby requests yield exactly the same next rate-limited parameter for the same previous state. This is not proof of zero multi-step authority or a reason to remove safety limits.',
                observation_caveat='Feedforward actor sees canonical48, not explicit previous parameters/energy/virtual offset. This is control-state dependence, not a demonstrated pair of indistinguishable reachable observations.')
        result.append(item)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--census',type=Path,required=True)
    p.add_argument('--parameter-source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    rows=inspect(read(a.census),a.parameter_source)
    write(a.output,dict(status='complete',created_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(__file__),census_sha256=sha(a.census),new_physics_steps=0,new_gradient_updates=0,
        methods=rows,causal_root_cause_established=False))
    for row in rows:print(row['method'],row['optimizer']['derived_actor_sample_soft_q']['mean'],row.get('parameter_local_sensitivity',{}).get('all_dimensions_flat_fraction'))
