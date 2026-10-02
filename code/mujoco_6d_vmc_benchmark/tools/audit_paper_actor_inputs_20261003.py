"""Check the ten learned final actors use only their declared public fields.

Replays complete development observations and corrupts all other canonical
fields identically for each actor. This checks the actor boundary, not sensor
realism or independence of the shared observer/reference generator.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import ROOT, sha, write, now
from current_student_policy_20260921 import load_current


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--lock',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    lock=json.loads(a.lock.read_text());assert lock['training_closed']
    allowed=np.r_[14:17,20:23,26:29,39:48];unused=np.setdiff1d(np.arange(48),allowed)
    rows=[]
    for candidate in lock['candidates']:
        if not candidate.get('checkpoint'):continue
        path=Path(candidate['checkpoint']);assert sha(path)==candidate['checkpoint_sha256']
        record=next(r for r in lock['development_evidence'] if r['name']==candidate['name'])
        trace=Path(record['development_run'])/'rollout.npz';assert sha(trace)==record['development_trace_sha256']
        with np.load(trace) as z:observations=z['observation'].copy()
        assert observations.shape==(1375,48)
        changed=observations.copy();changed[:,unused]=np.random.default_rng(2026100343).uniform(-1000,1000,(1375,len(unused)))
        original=load_current(path);mutated=load_current(path);original.reset();mutated.reset()
        action_max=0.;state_max=0.;states=0
        for x,y in zip(observations,changed):
            left=original.act(x);right=mutated.act(y)
            np.testing.assert_array_equal(left,right)
            assert left.shape==(7,) and np.isfinite(left).all() and 0<=left[0]<=1 and np.all(abs(left[1:])<=1)
            action_max=max(action_max,float(np.max(abs(left-right))))
            if hasattr(original,'state'):
                np.testing.assert_array_equal(original.state,mutated.state)
                state_max=max(state_max,float(np.max(abs(original.state-mutated.state))));states+=1
        rows.append(dict(name=candidate['name'],checkpoint_sha256=sha(path),development_trace_sha256=sha(trace),
                         samples=len(observations),action_difference_max_abs=action_max,
                         hidden_state_checks=states,hidden_state_difference_max_abs=state_max))
    assert len(rows)==10
    sources=['current_student_policy_20260921.py','office_vmc_memory_esn_20260927.py',
             'office_context_network_20261003.py','office_mlp_rnn_20261002.py']
    write(a.output,dict(created_utc=now(),source_sha256=sha(Path(__file__)),validation_lock_sha256=sha(a.lock),
        actor_source_sha256={f:sha(ROOT/'scripts'/f) for f in sources},allowed_fields=allowed.tolist(),
        perturbed_unused_fields=unused.tolist(),seed=2026100343,rows=rows,
        semantics='Fields 14:17 nominal linear velocity; 20:23 reference-relative position error; 26:29 velocity error; 39:45 estimated wrench; 45:48 nominal path direction. No event time, contact truth, obstacle state, vision or distance is supplied by this interface.',
        limitation='Actor-field invariance on recorded development observations. Public reference inputs are included; this does not prove the shared observer/reference generator is deployable on real hardware. No fitting, tuning or new physical rollout.'))
    print(json.dumps(dict(models=len(rows),observations_each=1375,maximum_action_difference=0.,maximum_state_difference=0.)))


if __name__=='__main__':main()
