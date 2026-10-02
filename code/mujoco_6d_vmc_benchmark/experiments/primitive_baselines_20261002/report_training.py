"""Development training diagnostics, with recovery segments explicitly separated."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
def lines(p):
    if not p.exists():return []
    out=[]
    for line in p.read_text().splitlines():
        try:out.append(json.loads(line))
        except json.JSONDecodeError:pass # trailing write can be incomplete in a live snapshot
    return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(exist_ok=True,parents=True)
    groups=[('Direct metric A (recovered)',ROOT/'campaign02/metric_seed74001'),('Direct office A (recovered)',ROOT/'campaign02/office_task_seed74001'),('Direct metric B',ROOT/'campaign02/metric_seed74002'),('Direct office B',ROOT/'campaign02/office_task_seed74002')]
    groups += [('Parameter '+c,ROOT/'parameter_rl/campaign01'/f'{c}_seed75001') for c in ['admittance','impedance','vmc']]
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    report=[]
    for name,d in groups:
        episodes=lines(d/'episodes.jsonl');train=lines(d/'training.jsonl')
        if not episodes:continue
        x=np.array([r['step'] for r in episodes]);win=8
        rate=np.array([np.mean([r.get('task_success',False) for r in episodes[max(0,i-win+1):i+1]]) for i in range(len(episodes))])
        axes[0,0].plot(x,rate,label=name)
        for ax,key,scale in [(axes[0,1],'rmse_m',1000),(axes[1,0],'peak_torque_nm',1),(axes[1,1],'peak_speed_mps',1)]:
            ys=np.array([r[key]*scale for r in episodes])
            smooth=np.array([np.median(ys[max(0,i-win+1):i+1]) for i in range(len(ys))])
            ax.plot(x,smooth,label=name)
        report.append(dict(label=name,path=str(d),completed_episodes=len(episodes),latest_completed_step=int(x[-1]),training_successes=sum(bool(r.get('task_success')) for r in episodes),training_contact=sum(bool(r.get('contact_exposed')) for r in episodes),scene_counts={s:sum(r['scene']==s for r in episodes) for s in ['ball','push','corner','table_corner']},complete=(d/'COMPLETE.json').exists(),latest_training_record=train[-1] if train else None))
    for ax,title in zip(axes.flat,['Training task rate (last 8 episodes)','Training position RMSE median (mm)','Training peak torque median (Nm)','Training peak speed median (m/s)']):
        ax.set_title(title);ax.set_xlabel('Saved interaction counter');ax.grid(alpha=.2)
    axes[0,0].set_ylim(-.03,1.03);handles,labels=axes[0,0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=3,fontsize=8)
    fig.suptitle('Training diagnostics: mixed scenes, not held-out performance')
    fig.savefig(a.output/'training_diagnostics.png',dpi=150);fig.savefig(a.output/'training_diagnostics.pdf');plt.close(fig)
    result=dict(runs=report,notes=['Recovered A runs show continuation episodes only; original episodes and failed tail remain in campaign01.','Rolling mixed-scene training metrics are diagnostics, not comparison scores or convergence proof.','Saved interaction counter omits discarded post-checkpoint interactions from the old failed run.','Scene durations and success semantics differ; evaluate on paired held-out fixtures.'])
    (a.output/'TRAINING_STATUS.json').write_text(json.dumps(result,indent=2))
    print(json.dumps([dict(label=r['label'],step=r['latest_completed_step'],episodes=r['completed_episodes']) for r in report]))
if __name__=='__main__':main()
