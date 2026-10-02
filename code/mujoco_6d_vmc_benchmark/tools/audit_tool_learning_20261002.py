"""Independent exported-policy audit; no physical-success inference from MSE."""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from optimize_tool_contact_20261002 import ROOT,sha,write,now
sys.path.insert(0,str(ROOT/'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN
from wbc_velocity_residual_core import VelocityResidualActionFilter,VelocityResidualSafetyConfig

def audit(path):
    metadata=json.loads((path/'TRAINING_COMPLETE.json').read_text())
    assert sha(path/'checkpoint.npz')==metadata['checkpoint_sha256']
    assert sha(path/'training_data.npz')==metadata['training_data_sha256']
    model=OfficeVMCMemoryESN(path/'checkpoint.npz')
    rng=np.random.default_rng(2026100209)
    for _ in range(100):
        o=rng.normal(0,4,48);o[39:45]=0;model.reset()
        np.testing.assert_array_equal(model.act(o),np.zeros(7))
    permitted=set(range(39,45))
    if model.context_inputs:permitted.update([*range(14,17),*range(26,29),*range(45,48)])
    if model.position_context:permitted.update(range(20,23))
    unused=sorted(set(range(48))-permitted)
    twin=OfficeVMCMemoryESN(path/'checkpoint.npz');model.reset();twin.reset()
    for _ in range(200):
        o=rng.normal(0,.2,48);o[39:45]*=20;other=o.copy();other[unused]=rng.normal(0,100,len(unused))
        np.testing.assert_array_equal(model.act(o),twin.act(other))
    with np.load(path/'training_data.npz') as z:
        obs=z['observation'];episodes=z['episode'];target=z['filtered_teacher_action'];stored=z['prediction'];training=z['train']
        predictions=[];executed=[];last=None
        filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32))
        for ep,o in zip(episodes,obs):
            if ep!=last:
                model.reset();filt=VelocityResidualActionFilter(VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32));last=ep
            a=model.act(o);predictions.append(a);f=filt.filter(a,.04)
            executed.append(np.r_[(1-f.wbc_scale)/(1-filt.config.minimum_wbc_scale),f.cartesian_yield_twist/np.r_[np.full(3,.32),np.full(3,filt.config.maximum_angular_yield_radps)]])
        predictions=np.asarray(predictions);executed=np.asarray(executed)
        np.testing.assert_allclose(predictions,stored,rtol=0,atol=1e-12)
        groups={}
        for name,mask in [('synthetic_train',(episodes<48)&training),('synthetic_holdout',~training),('seen_physical_histories',episodes>=48)]:
            groups[name]=dict(samples=int(mask.sum()),raw_output_mse=float(np.mean((predictions[mask]-target[mask])**2)),
                              filtered_execution_mse=float(np.mean((executed[mask]-target[mask])**2)),
                              maximum_action_error=float(np.max(abs(predictions[mask]-target[mask]))))
    report=dict(audited_utc=now(),checkpoint_sha256=sha(path/'checkpoint.npz'),
                exported_replay_max_error=float(np.max(abs(predictions-stored))),
                zero_load_arbitrary_context_pass=True,unused_field_isolation_pass=True,
                canonical_fields_used=sorted(permitted),groups=groups,
                limitation='Replay and synthetic-history validation only; physical success/generalization must be measured separately')
    write(path/'LEARNING_AUDIT.json',report)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directories',type=Path,nargs='+');args=p.parse_args()
    for path in args.directories:
        report=audit(path);print(json.dumps(dict(path=str(path),groups=report['groups'])))
