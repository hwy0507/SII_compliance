"""Plot every registered primitive test outcome, including missing and failed cases."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
def plot(catalog,output):
    cat=json.loads(catalog.read_text());entries=cat["models"];fixtures=None
    for e in entries:
        p=Path(e["output"])/"PROTOCOL.json"
        if p.exists():fixtures=json.loads(p.read_text())["fixtures"];break
    if fixtures is None:raise ValueError("No evaluation protocol")
    colors=["#e3e7ea","#737b84","#efc574","#4b9971","#bf625c","#6194bd"]
    matrix=np.zeros((len(entries),len(fixtures)),int);no_contact=[];labels=[]
    for i,e in enumerate(entries):
        d=Path(e["output"]);labels.append(e["label"])
        if not (d/"ROWS.json").exists():continue
        rows=json.loads((d/"ROWS.json").read_text())
        for row in rows:
            j=fixtures.index(row["fixture_id"])
            if row.get("initial_state_rejected"):matrix[i,j]=1;continue
            matrix[i,j]=4 if not row["physical_valid"] else 3 if row["strict_success"] else 5 if row["task_success"] else 2
            if not row["contact_exposed"]:no_contact.append((j,i))
    fig,ax=plt.subplots(figsize=(14,8),layout="constrained")
    ax.imshow(matrix,cmap=ListedColormap(colors),vmin=0,vmax=5,aspect="auto",interpolation="none")
    ax.set_yticks(range(len(labels)),labels,fontsize=9)
    ax.set_xticks(range(len(fixtures)),[str(int(f.rsplit("_",1)[1])) for f in fixtures])
    ax.set_xticks(np.arange(-.5,len(fixtures),1),minor=True);ax.set_yticks(np.arange(-.5,len(labels),1),minor=True)
    ax.grid(which="minor",color="white",lw=1.4);ax.tick_params(which="minor",bottom=False,left=False)
    ax.set_xlabel("Predeclared test index within each scene")
    for x in [2.5,5.5,8.5]:ax.axvline(x,color="#3a4c57",lw=1.5)
    top=ax.secondary_xaxis("top");top.set_xticks([1,4,7,10],["Ball","Rod push","Side corner","Table corner"])
    if no_contact:
        xy=np.asarray(no_contact);ax.scatter(xy[:,0],xy[:,1],s=90,facecolors="none",edgecolors="#162b35",linewidths=1.6)
    names=["Not completed","Initial-state rejected","Task failed; numeric gate passed","Strict success","Numeric/penetration gate failed","Task succeeded; no intended contact"]
    legend=[Patch(facecolor=c,label=n) for c,n in zip(colors,names)]
    fig.legend(handles=legend,loc="outside lower center",ncol=3,fontsize=8)
    fig.suptitle("Primitive development tests: every fixed condition retained\nOutlined circle = no intended robot/obstacle contact; native timesteps differ across scenes",fontsize=12)
    output.mkdir(exist_ok=True,parents=True)
    fig.savefig(output/"outcome_matrix.png",dpi=160);fig.savefig(output/"outcome_matrix.pdf");plt.close(fig)
    (output/"OUTCOME_MATRIX.json").write_text(json.dumps(dict(catalog=str(catalog),fixtures=fixtures,methods=[e["id"] for e in entries],codes=names,values=matrix.tolist(),no_contact_cells=no_contact),indent=2))
    print(json.dumps(dict(completed_cells=int(np.count_nonzero(matrix)),planned_cells=matrix.size,output=str(output))))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--catalog",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args();plot(a.catalog,a.output)
