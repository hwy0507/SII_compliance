"""Fit a pure ESN route/impact dual readout from saved proprio traces."""
import argparse,hashlib,json
from pathlib import Path
import sys
import numpy as np

# The ESN implementation lives in the sibling scripts directory.  Keep this
# generator runnable from the repository root and from a clean subprocess,
# without relying on an ambient PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from esn128_proprio48_action7_20260921 import ESN128Proprio48Action7

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def actions(model,obs):
    model.reset();return np.asarray([model.act(x) for x in obs])
def feat(model,obs):
    model.reset();return np.asarray([model.features(x) for x in obs])
def logits(a):
    y=np.clip(a,-.999,.999);z=np.arctanh(y);p=np.clip(a[:,0],1e-4,1-1e-4);z[:,0]=np.log(p/(1-p));return z
def main():
    p=argparse.ArgumentParser();p.add_argument('--route-model',type=Path,required=True);p.add_argument('--impact-model',type=Path,required=True);p.add_argument('--trace',type=Path,nargs='+',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--impact-scale',type=float,default=.12);p.add_argument('--impact-center',type=float,default=.8);p.add_argument('--impact-width',type=float,default=.2);p.add_argument('--impact-gain',type=float,default=1.0);p.add_argument('--impact-channel-gain',default=None,help='optional seven comma-separated multipliers applied after scalar impact-gain');p.add_argument('--attack-tau',type=float,default=.04);p.add_argument('--release-tau',type=float,default=.16);p.add_argument('--hold-tau',type=float,default=.64);a=p.parse_args()
    if a.impact_gain <= 0:raise ValueError('impact-gain must be positive')
    channel_gain=np.ones(7) if a.impact_channel_gain is None else np.asarray([float(x) for x in a.impact_channel_gain.split(',')],dtype=float)
    if channel_gain.shape!=(7,) or np.any(channel_gain<=0):raise ValueError('impact-channel-gain must contain seven positive values')
    if a.output.exists():raise FileExistsError(a.output)
    with np.load(a.route_model,allow_pickle=False) as z:
        if str(z['contract'])!='proprio48_esn128_action7_v1':raise ValueError('route contract')
        base={k:z[k].copy() for k in z.files if k not in ('metadata','contract')}
    route=ESN128Proprio48Action7.load(a.route_model);impact=ESN128Proprio48Action7.load(a.impact_model)
    obs_chunks=[];route_chunks=[];impact_chunks=[];trans_chunks=[]
    for path in a.trace:
        with np.load(path,allow_pickle=False) as z:obs=z['observation'].astype(float)
        obs_chunks.append(obs);route_chunks.append(actions(route,obs));impact_chunks.append(actions(impact,obs))
        route.reset();q=obs[:,7:14];trans_chunks.append(np.linalg.norm(np.diff(q,axis=0,prepend=q[:1]),axis=1))
    obs=np.concatenate(obs_chunks);route_y=np.concatenate(route_chunks);impact_y=np.concatenate(impact_chunks);trans=np.concatenate(trans_chunks)
    gate=1/(1+np.exp(-np.clip((trans/a.impact_scale-a.impact_center)/a.impact_width,-60,60)))
    # The impact head is fitted to impact policy only when proprioceptive
    # transient evidence is high; otherwise it is regularized toward route.
    target=(1-gate[:,None])*route_y+gate[:,None]*impact_y
    f=feat(route,obs);f=(f-base['fmean'])/base['fstd'];h=np.tanh(f@base['w1'].T+base['b1'])
    d=np.c_[h,np.ones(len(h))];y=logits(target);w=.25+gate*4.;dw=d*w[:,None]
    lhs=d.T@dw+.05*np.eye(d.shape[1]);rhs=dw.T@y+.05*np.vstack((base['w2'].T,base['b2']))
    solved=np.linalg.solve(lhs,rhs);iw,ib=solved[:-1].T*a.impact_gain*channel_gain[:,None],solved[-1]*a.impact_gain*channel_gain
    # Route head is kept exactly from the route checkpoint; impact head is the
    # fitted single-readout response in the same feature space.
    meta=dict(contract='proprio48_esn128_action7_impact_response_v1',method='shared_reservoir_dual_readout',route_sha256=sha(a.route_model),impact_sha256=sha(a.impact_model),trace_sha256=[sha(x) for x in a.trace],forbidden_inputs=['contact truth','ball state','event time','task stage','visual/range','geometry'],impact_scale=a.impact_scale,impact_center=a.impact_center,impact_width=a.impact_width,impact_gain=a.impact_gain,impact_channel_gain=channel_gain.tolist(),attack_tau=a.attack_tau,release_tau=a.release_tau,hold_tau=a.hold_tau,gate_train_fraction=float(np.mean(gate)),route_action_norm=float(np.mean(np.linalg.norm(route_y,axis=1))),impact_action_norm=float(np.mean(np.linalg.norm(impact_y,axis=1))))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(a.output,contract=meta['contract'],metadata=json.dumps(meta),**base,route_w2=base['w2'],route_b2=base['b2'],impact_w2=iw,impact_b2=ib,impact_scale=np.float64(a.impact_scale),impact_center=np.float64(a.impact_center),impact_width=np.float64(a.impact_width),impact_attack_tau=np.float64(a.attack_tau),impact_release_tau=np.float64(a.release_tau),impact_hold_tau=np.float64(a.hold_tau))
    meta['output_sha256']=sha(a.output);a.output.with_suffix('.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
if __name__=='__main__':main()
