"""Independent saved-state actor/filter audit; no new physics or mutation of raw runs."""
import argparse
from dataclasses import fields
import json
from pathlib import Path
import numpy as np
from run_video_reference_vmc_20261028 import sha, write, verify_actor
from optimize_tool_contact_20261002 import ParameterTeacher
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    a=p.parse_args();f=a.folder
    verify_actor()
    record=json.loads((f/'execution.json').read_text())
    with np.load(f/'trajectory.npz') as z:
        obs=z['observation'];actions=z['action'];time=z['time']
    with np.load(f/'filter.npz') as z:
        chain={k:z[k] for k in z.files}
    n=len(actions)
    assert len(obs)==n and n==record['steps']
    cfg=json.loads((f/'teacher.json').read_text());actor=ParameterTeacher(cfg)
    pred=[]
    for o in obs:actor.observe(o);pred.append(actor.act(o[39:45],.04))
    np.testing.assert_array_equal(pred,actions)
    np.testing.assert_array_equal(chain['request'][:n],actions)
    extra=len(chain['request'])-n
    if extra:
        # Original verifier used the capture hook while iterating the captured
        # list. The first N rows are physical; the suffix is verifier output.
        # Keep raw evidence and explicitly bind every suffix request to it.
        assert record['status']=='failed_preserved'
        assert extra==n+1
        np.testing.assert_array_equal(chain['request'][n:2*n],actions)
        np.testing.assert_array_equal(chain['request'][-1],actions[0])
    raw_cfg=record['filter_config']
    for k,v in raw_cfg.items():
        if isinstance(v,list):raw_cfg[k]=np.asarray(v)
    filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(**raw_cfg))
    for i in range(n):
        result=filt.filter(actions[i],float(chain['dt'][i]))
        np.testing.assert_array_equal(result.cartesian_yield_twist,chain['twist'][i])
        np.testing.assert_array_equal(result.raw_action_clipped,chain['clipped'][i])
        assert result.wbc_scale==chain['scale'][i]
    np.testing.assert_allclose(np.diff(time),.04,atol=1e-8,rtol=0)
    write(f/'INDEPENDENT_AUDIT.json',dict(status='passed',physical_action_rows=n,
        audit_only_suffix_rows=extra,original_execution_status=record['status'],
        source_sha256=sha(Path(__file__)),actor_replay_max_abs=0.,filter_replay_max_abs=0.,
        input_hashes={name:sha(f/name) for name in ('trajectory.npz','filter.npz','execution.json','teacher.json')},
        limitation='This validates provenance/execution replay, not Task/Strict success or physical safety.'))


if __name__=='__main__':main()
