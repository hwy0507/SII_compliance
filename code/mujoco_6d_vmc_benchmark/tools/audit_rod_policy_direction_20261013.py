"""Exact frozen readout attribution; diagnostic only, never changes actions."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from office_vmc_memory_esn_20260927 import OfficeVMCMemoryESN


def main():
    source=ROOT/'outputs/original_esn_rod_tick_20261013/same_tick/episode'
    output=ROOT/'outputs/original_esn_rod_opposition_20261013/POLICY_DIRECTION.json'
    if output.exists():raise FileExistsError(output)
    policy=OfficeVMCMemoryESN(source/'checkpoint.npz')
    assert policy.context_inputs and policy.position_context and policy.weights.shape==(552,7)
    assert not policy.nonlinear and not policy.state_delta_readout
    result=json.loads((source/'rollout.json').read_text());rod=result['stats']['events']['rod']
    parts=[]
    with np.load(source/'rollout.npz') as z,np.load(source/'execution_chain.npz') as chain:
        t=z['neuron_time'];obs=z['observation'];actions=z['applied_action']
        for i,o in enumerate(obs):
            f=policy.features(o);weighted=f*policy.weights[:,1]
            raw=f@policy.weights
            action=np.clip(raw,-1,1);action[0]=np.clip(raw[0],0,1)
            np.testing.assert_array_equal(action,actions[i]);np.testing.assert_array_equal(policy.state,z['reservoir_state'][i])
            rows=weighted[268:412].reshape(12,12)
            components=dict(current_fx=float(weighted[0]+weighted[134]+rows[[0,6]].sum()),
                current_fy=float(weighted[1]+weighted[135]+rows[[1,7]].sum()),
                current_fz=float(weighted[2]+weighted[136]+rows[[2,8]].sum()),
                current_moments=float(weighted[3:6].sum()+weighted[137:140].sum()+rows[[3,4,5,9,10,11]].sum()),
                reservoir=float(weighted[6:134].sum()+weighted[140:268].sum()),
                reservoir_context=float(weighted[412:540].sum()),context_alone=float(weighted[540:].sum()))
            np.testing.assert_allclose(sum(components.values()),raw[1],rtol=1e-12,atol=1e-12)
            parts.append(components)
        span=(t>=rod['first_s']-1e-7)&(t<rod['last_s']-1e-7)
        positive=span&(obs[:,39]>0)
        opposite=positive&(actions[:,1]<0)
        rows=[]
        for i in np.flatnonzero(opposite):
            rows.append(dict(time_s=float(t[i]),estimated_wrench=obs[i,39:45].tolist(),
                raw_request_x_mmps=float(actions[i,1]*320),filtered_x_mmps=float(chain['yield_twist'][i,0]*1000),
                nominal_x_mmps=float(obs[i,14]*1000),measured_x_mmps=float((obs[i,14]-obs[i,26])*1000),
                preclip_x_readout_components=parts[i]))
    receipt=dict(source_trace_sha256=hashlib.sha256((source/'rollout.npz').read_bytes()).hexdigest(),
        checkpoint_sha256=hashlib.sha256((source/'checkpoint.npz').read_bytes()).hexdigest(),
        analysis_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        exact_action_and_state_replay=True,policy_or_environment_changed=False,
        rod_span_frames=int(span.sum()),positive_estimated_fx_frames=int(positive.sum()),
        negative_raw_vx_despite_positive_estimated_fx_frames=int(opposite.sum()),examples=rows,
        limitations=['Estimated force is not true rod contact force',
            'Rod span includes contact gaps; positive Fx may coexist with other wrench components',
            'Instantaneous negative force/velocity alignment may reflect memory, recovery or cross-axis response; not a passivity or instability proof',
            'Exact reproduction locates these particular requests in the frozen readout, not an adapter sign reversal; it does not exclude other execution-layer causes'])
    output.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='examples'},indent=2))
    print(json.dumps(rows[:2],indent=2))


if __name__=='__main__':main()
