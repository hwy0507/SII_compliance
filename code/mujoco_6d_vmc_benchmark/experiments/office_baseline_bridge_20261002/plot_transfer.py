"""Plot saved office trajectories by method family; never re-run physics."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from summarize import ROOT,SOURCE,build
def plot(output):
    build(output)
    report=json.loads((output/"SUMMARY.json").read_text());rows={r["id"]:r for r in report["rows"]}
    groups={"historical_reference":["zero","source_esn_reference"],"direct_rl":["zero","direct_metric_74001","direct_office_task_74001","direct_metric_74002","direct_office_task_74002"]}
    groups.update({c:["zero","fixed_"+c,"parameter_"+c] for c in ["admittance","impedance","vmc"]})
    written=[]
    for name,ids in groups.items():
        ids=[i for i in ids if i in rows]
        if len(ids)<2:continue
        fig,ax=plt.subplots(2,2,figsize=(12,8),layout="constrained")
        for identity in ids:
            row=rows[identity];prefix=Path(row["source"])/("esn_combined_v4" if identity=="source_esn_reference" else "rollout")
            z=np.load(prefix.with_suffix(".npz"));s=json.loads(prefix.with_suffix(".json").read_text());target=np.asarray(s["placement_destination"]);t=z["time"];xyz=z["object_position"]
            label=identity.replace("source_esn_reference","ESN historical reference").replace("_"," ")
            ax[0,0].plot(xyz[:,0],xyz[:,1],label=label,lw=1.2)
            ax[0,1].plot(t,np.linalg.norm(xyz-target,axis=1)*1000,lw=1.2)
            ax[1,0].plot(t,xyz[:,2],lw=1.2)
            ax[1,1].step(t,z["stage"],where="post",lw=1.2)
        ax[0,0].scatter([target[0]],[target[1]],marker="x",s=90,c="black",label="Placement target")
        ax[0,0].set(xlabel="Payload x (m)",ylabel="Payload y (m)",title="Payload motion")
        ax[0,0].axis("equal")
        ax[0,1].set(xlabel="Physical time (s)",ylabel="Distance (mm)",title="Payload distance to final target")
        ax[1,0].axhline(target[2],c="black",ls=":",lw=1)
        ax[1,0].set(xlabel="Physical time (s)",ylabel="Payload height (m)",title="Lift and placement height")
        ax[1,1].set(xlabel="Physical time (s)",ylabel="Task stage",title="Shared task supervisor progress")
        for a in [ax[0,1],ax[1,0],ax[1,1]]:
            a.axvline(2,color="#a53c3c",ls=":",alpha=.6)
            a.axvspan(3,10,color="#d8ad51",alpha=.1);a.axvspan(12,25.5,color="#69a89d",alpha=.1)
        for a in ax.flat:a.grid(alpha=.2)
        handles,labels=ax[0,0].get_legend_handles_labels()
        fig.legend(handles,labels,loc="outside lower center",ncol=3,fontsize=8)
        fig.suptitle("Exact office v5 / development dt=1e-4 / "+name.replace("_"," ")+"\nSaved trajectories; task outcome and contact exposure remain in SUMMARY.json")
        for ext in ["png","pdf"]:fig.savefig(output/(name+"."+ext),dpi=150)
        plt.close(fig);written.append(name)
    (output/"PLOTS.json").write_text(json.dumps(dict(groups=written,physics_advanced=False,source_summary=str(output/"SUMMARY.json")),indent=2))
    print(json.dumps(dict(plots=written,output=str(output))))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args();plot(a.output)
