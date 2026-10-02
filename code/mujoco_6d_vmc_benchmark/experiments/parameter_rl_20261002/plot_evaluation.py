"""Plot the four registered anchor trajectories; never select by test scores."""
import argparse, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT=Path("/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002")

def plot(controller, output):
    root=ROOT/"final_reference01"
    prior_doc=json.loads((Path(__file__).parent/"PRIORS.json").read_text())["methods"][controller]
    center=np.asarray(prior_doc["center"]);keys=prior_doc["keys"]
    scenes=["ball","push","corner","table_corner"]
    fig,axes=plt.subplots(4,2,figsize=(14,12),layout="constrained")
    rows=[]
    for index,scene in enumerate(scenes):
        learned=root/("parameter_"+controller)/(scene+"_reference")
        fixed=root/("fixed_"+controller)/(scene+"_reference")
        if not (learned/"result.json").exists():
            for ax in axes[index]:ax.text(.5,.5,"Registered anchor not finished",ha="center",va="center",transform=ax.transAxes)
            rows.append(dict(scene=scene,status="not_finished"));continue
        rz=json.loads((learned/"result.json").read_text())
        fz=json.loads((fixed/"result.json").read_text())
        assert rz["model_sha256"]==fz["model_sha256"]
        with np.load(learned/"parameter_actions.npz") as params, np.load(learned/"control.npz") as control:
            t=control["time"]
            assert len(t)==len(params["parameters"])
            ratios=params["parameters"]/center
            for i,key in enumerate(keys):
                axes[index,0].plot(t,ratios[:,i],label=key,lw=.9)
            row=dict(scene=scene,status="complete",learned=str(learned),fixed=str(fixed),
                task_fixed=fz["task_success"],task_rl=rz["task_success"],
                strict_fixed=fz["strict_success"],strict_rl=rz["strict_success"],
                minimum_ratio=ratios.min(axis=0).tolist(),maximum_ratio=ratios.max(axis=0).tolist(),
                minimum_tank_j=float(params["tank"].min()),
                limited_updates=int(np.sum(params["energy_scale"]<.999999)))
        axes[index,0].axhline(1,color="0.3",ls="--",lw=.7)
        axes[index,0].set_ylabel(scene+"\nparameter / prior")
        axes[index,0].legend(fontsize=6.5,ncol=3,loc="upper right")
        for path,label,color in [(fixed,"Fixed prior","#7a7e82"),(learned,"Parameter RL","#26708c")]:
            with np.load(path/"control.npz") as control:
                error=np.linalg.norm(control["position"]-control["target"],axis=1)*1000
                axes[index,1].plot(control["time"],error,label=label,color=color,lw=1.1)
        axes[index,1].set_ylabel("Saved 25 Hz position error (mm)")
        axes[index,1].set_title(f"Task fixed/RL: {fz['task_success']}/{rz['task_success']} | strict: {fz['strict_success']}/{rz['strict_success']}",fontsize=10)
        axes[index,1].legend(fontsize=8)
        rows.append(row)
    for ax in axes.flat:ax.set_xlabel("Physical time (s)");ax.grid(alpha=.18)
    fig.suptitle(controller+" | registered display anchors, separate from held-out scores\nLegacy ball launch follows actual hand at launch; curves are not identical-input causal responses",fontsize=12)
    output.mkdir(parents=True,exist_ok=True)
    fig.savefig(output/(controller+".png"),dpi=155);fig.savefig(output/(controller+".pdf"));plt.close(fig)
    (output/(controller+".json")).write_text(json.dumps(dict(controller=controller,keys=keys,rows=rows,
        caveats=["Four preregistered original-video anchors, not selected successes.",
            "The 25 Hz error curve does not capture native peak velocity/force; native metrics are reported separately.",
            "Local energy budget is not a global robot passivity guarantee.",
            "Parameter ratios describe applied actions, not evidence of effective learning."]),indent=2,allow_nan=False))
    print(json.dumps(dict(controller=controller,completed=sum(r["status"]=="complete" for r in rows))))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--controller",choices=["admittance","impedance","vmc"],required=True)
    parser.add_argument("--output",type=Path,default=ROOT/"parameter_rl/final_diagnostics01")
    args=parser.parse_args();plot(args.controller,args.output)
