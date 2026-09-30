"""Build a two-expert ESN readout with a nonlinear reservoir-state gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from fit_esn_gated_readout_20260926 import same_shared, sigmoid
from fit_esn_history_adapter_20260925 import hidden_from_head, load_model, sha
from fit_esn_onpolicy_readout_20260925 import features_from_observation


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument('--yield-expert',type=Path,required=True)
    p.add_argument('--clearance-expert',type=Path,required=True)
    p.add_argument('--rollout',type=Path,nargs='+',required=True)
    p.add_argument('--clearance-rollout',type=Path,nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--hidden',type=int,default=16)
    p.add_argument('--steps',type=int,default=6000)
    p.add_argument('--learning-rate',type=float,default=0.01)
    p.add_argument('--l2',type=float,default=1.0e-4)
    p.add_argument('--gate-offset',type=float,default=0.0)
    p.add_argument('--seed',type=int,default=20260926)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    if args.hidden<2 or args.steps<1 or args.learning_rate<=0 or args.l2<=0:raise ValueError('invalid training parameters')
    all_paths={path.resolve() for path in args.rollout};positive_paths={path.resolve() for path in args.clearance_rollout}
    if not positive_paths<=all_paths:raise ValueError('clearance rollouts must be a subset')
    args.output.mkdir(parents=True)
    ymodel=load_model(args.yield_expert);cmodel=load_model(args.clearance_expert);same_shared(ymodel,cmodel)
    fmean=np.asarray(ymodel['fmean'],dtype=np.float64);fstd=np.asarray(ymodel['fstd'],dtype=np.float64)
    w1=np.asarray(ymodel['w1'],dtype=np.float64);b1=np.asarray(ymodel['b1'],dtype=np.float64)
    hs=[];ys=[]
    for path in args.rollout:
        with np.load(path,allow_pickle=False) as data:
            observation=data['observation'].astype(np.float64);stage=data['stage'].astype(np.int64)
        hs.append(hidden_from_head((features_from_observation(ymodel,observation)-fmean)/fstd,w1,b1))
        ys.append(((stage>=3)&(path.resolve() in positive_paths)).astype(np.float64))
    x=np.concatenate(hs);target=np.concatenate(ys);positive=target>0.5
    npos=float(np.sum(positive));nneg=float(len(target)-npos)
    if npos==0 or nneg==0:raise ValueError('gate needs both classes')
    sample_weight=np.where(positive,0.5/npos,0.5/nneg)*len(target)
    rng=np.random.default_rng(args.seed)
    params=[rng.normal(0,0.05,(args.hidden,x.shape[1])),np.zeros(args.hidden),
            rng.normal(0,0.05,args.hidden),np.array(0.0)]
    m=[np.zeros_like(v) for v in params];v=[np.zeros_like(v) for v in params]
    beta1,beta2=0.9,0.999
    history=[]
    for step in range(1,args.steps+1):
        gw1,gb1,gw2,gb2=params
        h=np.tanh(x@gw1.T+gb1);logit=h@gw2+gb2;prob=sigmoid(logit)
        delta=sample_weight*(prob-target)/len(target)
        grads=[(delta[:,None]*gw2*(1-h*h)).T@x+args.l2*gw1,
               np.sum(delta[:,None]*gw2*(1-h*h),axis=0),
               h.T@delta+args.l2*gw2,np.array(np.sum(delta))]
        for i,g in enumerate(grads):
            m[i]=beta1*m[i]+(1-beta1)*g;v[i]=beta2*v[i]+(1-beta2)*g*g
            params[i]-=args.learning_rate*(m[i]/(1-beta1**step))/(np.sqrt(v[i]/(1-beta2**step))+1e-8)
        if step==1 or step%500==0 or step==args.steps:
            loss=np.sum(sample_weight*(np.logaddexp(0.0,logit)-target*logit))/len(target)
            loss+=0.5*args.l2*(np.sum(gw1*gw1)+np.sum(gw2*gw2))
            history.append({'step':step,'loss':float(loss)})
    gw1,gb1,gw2,gb2=params;gb2=np.array(float(gb2+args.gate_offset))
    probability=sigmoid(np.tanh(x@gw1.T+gb1)@gw2+gb2);prediction=probability>=0.5
    metrics={
        'positive_samples':int(npos),'negative_samples':int(nneg),
        'positive_probability_mean':float(np.mean(probability[positive])),
        'positive_probability_p05':float(np.quantile(probability[positive],0.05)),
        'negative_probability_mean':float(np.mean(probability[~positive])),
        'negative_probability_p95':float(np.quantile(probability[~positive],0.95)),
        'true_positive_rate':float(np.mean(prediction[positive])),
        'false_positive_rate':float(np.mean(prediction[~positive])),
    }
    metadata={'method':'reservoir_state_two_expert_mlp_gate','yield_expert_sha256':sha(args.yield_expert),
        'clearance_expert_sha256':sha(args.clearance_expert),'rollout_sha256':[sha(q) for q in args.rollout],
        'clearance_rollout_sha256':[sha(q) for q in args.clearance_rollout],
        'hidden':args.hidden,'steps':args.steps,'learning_rate':args.learning_rate,'l2':args.l2,
        'gate_offset':args.gate_offset,'seed':args.seed,'gate_metrics':metrics,'history':history,
        'deployment_inputs':'unchanged proprio48; gate reads only reservoir-derived hidden state',
        'frozen_components':['48D normalization','heterogeneous-leak reservoir','first readout layer',
                             'expert readouts','action projection','safety filter','task and penetration gates']}
    checkpoint=args.output/'gated_mlp_readout.npz'
    with checkpoint.open('wb') as stream:
        np.savez_compressed(stream,contract='proprio48_esn128_action7_gated_mlp_v1',metadata=json.dumps(metadata),
            seed=np.int64(ymodel['seed']),mean=np.asarray(ymodel['mean']),std=np.asarray(ymodel['std']),
            win=np.asarray(ymodel['win']),w=np.asarray(ymodel['w']),leak=np.asarray(ymodel['leak']),
            input_mask=np.asarray(ymodel['input_mask']),alpha=np.float64(ymodel['alpha']),output_gain=np.float64(ymodel['output_gain']),
            fmean=np.asarray(ymodel['fmean']),fstd=np.asarray(ymodel['fstd']),w1=np.asarray(ymodel['w1']),b1=np.asarray(ymodel['b1']),
            yield_w2=np.asarray(ymodel['w2']),yield_b2=np.asarray(ymodel['b2']),clearance_w2=np.asarray(cmodel['w2']),clearance_b2=np.asarray(cmodel['b2']),
            gate_w1=gw1,gate_b1=gb1,gate_w2=gw2,gate_b2=gb2)
    report={**metadata,'checkpoint_sha256':sha(checkpoint)}
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
