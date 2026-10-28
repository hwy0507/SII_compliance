"""Plot complete fixed-condition task/contact traces without new simulation.

Displays 10 ms maxima to preserve short peaks; quantitative statistics remain
the independent full-substep results. No frame or failed tail is excluded.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from optimize_tool_contact_20261002 import sha, write, now


def envelope(time, values, dt):
    width=max(1,round(.01/dt));start=np.arange(0,len(time),width)
    return time[start],np.maximum.reduceat(values,start)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runs',type=Path,nargs='+',required=True);p.add_argument('--labels',nargs='+',required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert len(a.runs)==len(a.labels);out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(3,2,figsize=(14,11),sharex=True);axes=axes.ravel();entries=[];reference=None
    colors=plt.get_cmap('tab10').colors
    for index,(run,label) in enumerate(zip(a.runs,a.labels)):
        s=json.loads((run/'rollout.json').read_text());assert json.loads((run/'execution.json').read_text())['status']=='complete'
        args=s['arguments'];signature={k:args[k] for k in ('duration','dt','seed','ball_speed','person_start','person_stroke','rod_start','rod_stroke','rod_hold')}
        signature['model_sha256']=s['model_sha256']
        if reference is None:reference=signature
        assert reference==signature and sha(run/'rollout.mjb')==s['model_sha256']
        with np.load(run/'rollout_metrics/substep_metrics.npz') as z:
            time=z['time'].astype(float);dt=z['dt'].astype(float)
            np.testing.assert_allclose(dt,dt[0],rtol=0,atol=1e-12)
            signals=[np.linalg.norm(z['error'].astype(float),axis=1)*1000,
                     np.max(abs(z['qfrc_actuator'].astype(float)),axis=1),
                     np.linalg.norm(z['twist'][:,:3].astype(float),axis=1)]
        channels=json.loads((run/'research_channels.json').read_text());assert sha(run/'research_substeps.npz')==channels['telemetry_sha256']
        with np.load(run/'research_substeps.npz') as z:
            assert len(z['contact_force_sum'])==len(time)
            signals.extend([z['contact_force_sum'][:,i].astype(float) for i in (2,3,4)])
        verdict='strict' if s['strict_success'] else 'task only' if s['task_success'] else 'failed'
        for ax,values in zip(axes,signals):
            t,y=envelope(time,values,float(dt[0]));ax.plot(t,y,label=label+' ('+verdict+')',lw=1.05,color=colors[index%len(colors)],alpha=.85)
        entries.append(dict(run=str(run.resolve()),label=label,task_success=s['task_success'],strict_success=s['strict_success'],
            full_horizon=s['full_task_horizon_completed'],duration_s=float(dt.sum()),abort_reason=s['abort_reason'],
            trace_sha256=sha(run/'rollout.npz'),metrics_sha256=sha(run/'rollout_metrics/substep_metrics.npz'),
            research_sha256=channels['telemetry_sha256']))
    for ax,title,unit in zip(axes,('Tracking position error','Maximum absolute joint actuator torque',
                                'End-effector linear speed','Human / robot contact load','Rod / robot contact load','Unknown-edge contact load'),
                            ('mm','Nm','m/s','N','N','N')):
        ax.set_title(title,fontsize=11);ax.set_ylabel(unit);ax.grid(alpha=.2);ax.set_xlim(0,reference['duration'])
        ax.axvline(2,color='gray',ls=':',lw=.8)
        ax.axvspan(reference['person_start'],reference['person_start']+7,color='blue',alpha=.025)
        ax.axvspan(reference['rod_start'],reference['rod_start']+1.5+reference['rod_hold']+2,color='orange',alpha=.045)
    axes[4].set_xlabel('Time (s)');axes[5].set_xlabel('Time (s)')
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=2,fontsize=9)
    fig.suptitle('Frozen office-validation-v6: complete traces, 10 ms peak envelopes\nContact is summed force magnitude; failure tails retained. Shading = commanded hand / rod intervals.',fontsize=12)
    fig.tight_layout(rect=(0,.085,1,.94));fig.savefig(out/'trajectories.png',dpi=160);fig.savefig(out/'trajectories.pdf');plt.close(fig)
    write(out/'MANIFEST.json',dict(created_utc=now(),source_sha256=sha(Path(__file__)),entries=entries,common=reference,
        display='Nonoverlapping 10ms maximum envelopes; all observed time retained. Not an integral or average. Separate source records provide full-substep statistics.',
        output_sha256={n:sha(out/n) for n in ('trajectories.png','trajectories.pdf')}))
    print(json.dumps(dict(episodes=len(entries),output=str(out))))


if __name__=='__main__':main()
