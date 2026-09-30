"""Build a two-expert ESN readout with a reservoir-state logistic gate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from fit_esn_history_adapter_20260925 import hidden_from_head, load_model, sha
from fit_esn_onpolicy_readout_20260925 import features_from_observation


SHARED = ("mean", "std", "win", "w", "leak", "input_mask", "alpha", "output_gain",
          "fmean", "fstd", "w1", "b1")


def same_shared(a: dict, b: dict) -> None:
    for key in SHARED:
        av, bv = np.asarray(a[key]), np.asarray(b[key])
        if av.shape != bv.shape or not np.array_equal(av, bv):
            raise ValueError(f"experts differ in frozen component {key}")


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-np.clip(x, -60.0, 60.0)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--yield-expert", type=Path, required=True)
    parser.add_argument("--clearance-expert", type=Path, required=True)
    parser.add_argument("--rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--clearance-rollout", type=Path, nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--l2", type=float, default=0.1)
    parser.add_argument("--gate-offset", type=float, default=0.0)
    args = parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    all_paths={path.resolve() for path in args.rollout}
    clearance_paths={path.resolve() for path in args.clearance_rollout}
    if not clearance_paths <= all_paths:raise ValueError("clearance rollouts must be a subset")
    if args.l2 <= 0:raise ValueError("l2 must be positive")
    args.output.mkdir(parents=True)

    yield_model=load_model(args.yield_expert)
    clearance_model=load_model(args.clearance_expert)
    same_shared(yield_model,clearance_model)
    hidden_chunks=[];label_chunks=[];episode=[]
    fmean=np.asarray(yield_model["fmean"],dtype=np.float64)
    fstd=np.asarray(yield_model["fstd"],dtype=np.float64)
    w1=np.asarray(yield_model["w1"],dtype=np.float64)
    b1=np.asarray(yield_model["b1"],dtype=np.float64)
    for path in args.rollout:
        with np.load(path,allow_pickle=False) as data:
            observation=data["observation"].astype(np.float64)
            stage=data["stage"].astype(np.int64)
        hidden=hidden_from_head((features_from_observation(yield_model,observation)-fmean)/fstd,w1,b1)
        label=((stage>=3)&(path.resolve() in clearance_paths)).astype(np.float64)
        hidden_chunks.append(hidden);label_chunks.append(label)
        episode.extend([str(path)]*len(label))
    hidden=np.concatenate(hidden_chunks);labels=np.concatenate(label_chunks)
    positives=float(np.sum(labels));negatives=float(len(labels)-positives)
    if positives == 0 or negatives == 0:raise ValueError("gate needs both classes")
    sample_weight=np.where(labels>0.5,0.5/positives,0.5/negatives)*len(labels)
    design=np.c_[hidden,np.ones(len(hidden))]

    def objective(theta: np.ndarray) -> tuple[float,np.ndarray]:
        logits=design@theta
        probability=sigmoid(logits)
        loss=np.sum(sample_weight*(np.logaddexp(0.0,logits)-labels*logits))/len(labels)
        loss+=0.5*args.l2*np.sum(theta[:-1]**2)
        gradient=design.T@(sample_weight*(probability-labels))/len(labels)
        gradient[:-1]+=args.l2*theta[:-1]
        return float(loss),gradient

    theta=np.zeros(design.shape[1],dtype=np.float64)
    previous=np.inf
    iterations=0
    for iterations in range(1,101):
        loss,gradient=objective(theta)
        probability=sigmoid(design@theta)
        curvature=sample_weight*probability*(1.0-probability)/len(labels)
        hessian=design.T@(design*curvature[:,None])
        hessian[:-1,:-1]+=args.l2*np.eye(design.shape[1]-1)
        step=np.linalg.solve(hessian+1.0e-9*np.eye(design.shape[1]),gradient)
        scale=1.0
        while scale>1.0e-6 and objective(theta-scale*step)[0]>=loss:
            scale*=0.5
        theta-=scale*step
        if abs(previous-loss)<1.0e-12 and np.linalg.norm(gradient,np.inf)<1.0e-8:break
        previous=loss
    final_loss,final_gradient=objective(theta)
    if not np.isfinite(final_loss) or np.linalg.norm(final_gradient,np.inf)>1.0e-5:
        raise RuntimeError("gate IRLS did not converge")
    gate_w=theta[:-1];gate_b=float(theta[-1]+args.gate_offset)
    probability=sigmoid(hidden@gate_w+gate_b)
    prediction=probability>=0.5
    positive=labels>0.5
    metrics={
        "positive_samples":int(positives),"negative_samples":int(negatives),
        "positive_probability_mean":float(np.mean(probability[positive])),
        "positive_probability_p05":float(np.quantile(probability[positive],0.05)),
        "negative_probability_mean":float(np.mean(probability[~positive])),
        "negative_probability_p95":float(np.quantile(probability[~positive],0.95)),
        "true_positive_rate":float(np.mean(prediction[positive])),
        "false_positive_rate":float(np.mean(prediction[~positive])),
        "optimizer":"deterministic_numpy_newton_irls",
        "optimizer_loss":float(final_loss),"optimizer_iterations":int(iterations),
    }
    metadata={
        "method":"reservoir_state_two_expert_logistic_gate",
        "yield_expert_sha256":sha(args.yield_expert),
        "clearance_expert_sha256":sha(args.clearance_expert),
        "rollout_sha256":[sha(path) for path in args.rollout],
        "clearance_rollout_sha256":[sha(path) for path in args.clearance_rollout],
        "l2":args.l2,"gate_offset":args.gate_offset,"gate_metrics":metrics,
        "deployment_inputs":"unchanged proprio48; gate reads only reservoir-derived hidden state",
        "frozen_components":["48D normalization","heterogeneous-leak reservoir","first readout layer",
                             "expert readouts","action projection","safety filter","task and penetration gates"],
    }
    checkpoint=args.output/"gated_readout.npz"
    with checkpoint.open("wb") as stream:
        np.savez_compressed(stream,contract="proprio48_esn128_action7_gated_v1",metadata=json.dumps(metadata),
            seed=np.int64(yield_model["seed"]),
            mean=np.asarray(yield_model["mean"]),std=np.asarray(yield_model["std"]),
            win=np.asarray(yield_model["win"]),w=np.asarray(yield_model["w"]),leak=np.asarray(yield_model["leak"]),
            input_mask=np.asarray(yield_model["input_mask"]),alpha=np.float64(yield_model["alpha"]),
            output_gain=np.float64(yield_model["output_gain"]),fmean=np.asarray(yield_model["fmean"]),
            fstd=np.asarray(yield_model["fstd"]),w1=np.asarray(yield_model["w1"]),b1=np.asarray(yield_model["b1"]),
            yield_w2=np.asarray(yield_model["w2"]),yield_b2=np.asarray(yield_model["b2"]),
            clearance_w2=np.asarray(clearance_model["w2"]),clearance_b2=np.asarray(clearance_model["b2"]),
            gate_w=gate_w,gate_b=np.float64(gate_b))
    report={**metadata,"checkpoint_sha256":sha(checkpoint)}
    (args.output/"report.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))


if __name__=="__main__":main()
