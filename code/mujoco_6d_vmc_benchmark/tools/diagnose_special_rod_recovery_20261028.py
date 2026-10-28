"""Read-only diagnosis of all ten registered rod trajectories; no simulation."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--collection',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.collection.resolve();out=a.output.resolve()
    plan=read(root/'COLLECTION_PLAN.json')
    entries=[e for e in plan['episodes'] if e['scene']=='rod']
    assert len(entries)==10
    if out.exists(): raise FileExistsError(out)
    rows=[];curves=[]
    for entry in entries:
        folder=Path(entry['folder']);e=read(folder/'execution.json')
        qualification=read(folder/'DEMONSTRATION_QUALIFICATION.json')
        behavior=read(folder/'ROD_YIELD_REJOIN_AUDIT_V3.json')
        assert e['status']=='complete' and e['collection_plan_sha256']==sha(root/'COLLECTION_PLAN.json')
        for name,digest in qualification['input_hashes'].items():
            if sha(folder/name)!=digest: raise ValueError(f'Stale input: {folder/name}')
        with np.load(folder/'trajectory.npz') as z:
            obs=z['observation'];action=z['action'];time=z['time']-.04
        with np.load(folder/'substeps.npz') as z:
            subtime=z['time'];pen=z['external_penetration_m']
        # Canonical48 records pre-action pose error, command, and twist error.
        # This does not pretend it is the post-step geometry used by v3.
        error_xy=np.linalg.norm(obs[:,20:22],axis=1)
        start=behavior['retract_start_s']
        window=(time>=start-1)&(time<start)
        contacts=e['contacts']['push_rod_geom']
        row=dict(id=entry['id'],split=entry['split'],qualification=qualification['status'],
                 failed_behavior_checks=[k for k,v in behavior['checks'].items() if not v],
                 hand_contact_first_s=behavior['hand_contact_first_s'],
                 last_rod_contact_s=contacts['last_s'],pass_s=behavior['pass_s'],
                 rejoin_confirmed_s=behavior['rejoin_confirmed_s'],retract_start_s=start,
                 max_penetration_mm=float(pen.max()*1000),max_penetration_time_s=float(subtime[np.argmax(pen)]),
                 tail_mean_error_xyz_mm=(obs[window,20:23].mean(0)*1000).tolist(),
                 tail_min_error_xy_mm=float(error_xy[window].min()*1000),
                 tail_mean_nominal_linear_mps=obs[window,14:17].mean(0).tolist(),
                 tail_mean_actual_linear_mps=(obs[window,14:17]-obs[window,26:29]).mean(0).tolist(),
                 tail_mean_action=action[window].mean(0).tolist(),
                 tail_mean_estimated_wrench=obs[window,39:45].mean(0).tolist(),
                 input_hashes={name:sha(folder/name) for name in
                               ['execution.json','trajectory.npz','substeps.npz','ROD_YIELD_REJOIN_AUDIT_V3.json','DEMONSTRATION_QUALIFICATION.json']})
        rows.append(row);curves.append((row,time,error_xy,obs,action))
    out.mkdir(parents=True)
    fig,axes=plt.subplots(2,2,figsize=(13,8),constrained_layout=True)
    for row,time,error_xy,obs,action in curves:
        color='tab:red' if row['qualification']!='qualified' else 'tab:blue'
        style='--' if row['split']=='validation' else '-'
        label=row['id']+' '+row['qualification']
        axes[0,0].plot(time,error_xy*1000,style,color=color,alpha=.65,label=label)
        if row['id'] in ('rod_00','rod_04','rod_05'):
            axes[0,1].plot(time,obs[:,21]*1000,label=row['id'])
            axes[1,0].plot(time,action[:,2],label=row['id'])
            axes[1,1].plot(time,obs[:,15]-obs[:,27],label=row['id']+' actual')
    axes[0,0].axhline(5,color='black',linestyle=':',label='5 mm rejoin tube')
    axes[0,0].set_ylim(0,40);axes[0,0].set_title('All planned rod conditions (dashed = validation)')
    axes[0,0].set_ylabel('Pre-action transverse error (mm)')
    axes[0,1].set_ylabel('Signed y pose error (mm)');axes[0,1].set_title('Training identities: failed00/04 and passed05')
    axes[1,0].set_ylabel('Requested VMC y action (normalized)')
    axes[1,1].set_ylabel('Measured hand y velocity (m/s)')
    for ax in axes.flat:
        ax.set_xlim(4,14);ax.set_xlabel('Simulation time (s)');ax.grid(alpha=.2);ax.legend(fontsize=7)
    fig.savefig(out/'rod_recovery.png',dpi=150);plt.close(fig)
    result=dict(schema='sii-special-rod-recovery-diagnosis-v1',rows=rows,
                collection_plan_sha256=sha(root/'COLLECTION_PLAN.json'),source_sha256=sha(Path(__file__)),
                conclusion='All ten passed geometric crossing; three fail persistent rejoin. Contact has ended well before withdrawal; remaining y error and slow physical recovery are observed. This is not proof of a controller implementation bug or a causal attribution to one parameter.',
                next_probe='Fixed intermediate velocity_weight 0.6 versus 0.3, same pair_average and original recovery; exact failed training identities rod_00/04 plus ball_00 and original qualified corner. No test feedback, no gate/hold/condition narrowing.',
                limitations='40ms pre-action pose signals plus original substep penetration. Not independent physical integration. Validation conditions shown descriptively, not used to choose the two failure probes.')
    (out/'DIAGNOSIS.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(output=str(out),qualified=sum(r['qualification']=='qualified' for r in rows),total=len(rows))))


if __name__=='__main__': main()
