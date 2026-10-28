"""Physical contact targets, geometric rod departure and paired ball response."""
import argparse
import hashlib
import json
from pathlib import Path
import mujoco
import numpy as np


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--ball-off',type=Path,required=True)
    a=parser.parse_args();prefix=a.run/'esn_combined_v4';off=a.ball_off/'esn_combined_v4'
    out=a.run/'CONTACT_REPAIR_AUDIT.json'
    if out.exists():raise FileExistsError(out)
    s=json.loads(prefix.with_suffix('.json').read_text())
    m=mujoco.MjModel.from_binary_path(str(prefix.with_suffix('.mjb')));d=mujoco.MjData(m)
    assert sha(prefix.with_suffix('.mjb'))==sha(off.with_suffix('.mjb'))
    with np.load(a.run/'esn_combined_v4_apparatus_trace.npz') as z:
        trace={k:z[k] for k in z.files}
    with np.load(a.ball_off/'esn_combined_v4_apparatus_trace.npz') as z:
        n=min(len(trace['time']),len(z['time']))
        np.testing.assert_allclose(trace['time'][:n],z['time'][:n],atol=1e-9,rtol=0)
        pre=trace['time'][:n]<2.
        assert np.array_equal(trace['hand'][:n][pre],z['hand'][:n][pre])
        window=(trace['time'][:n]>=2.)&(trace['time'][:n]<2.7)
        delta=trace['hand'][:n]-z['hand'][:n]
        ball=dict(causal_hand_displacement_peak_mm=float(np.linalg.norm(delta[window],axis=1).max()*1000),
                  matched_before_launch=True,window_s=[2.,2.7],counterfactual='same model and policy, incoming ball speed zero')
    pairs=s['apparatus_contact_pairs']
    meaningful={k:v for k,v in pairs.items() if v['duration_s']>0}
    rod=s['stats']['events'].get('rod')
    rod_audit=dict(contact=rod,longest_uninterrupted=s['stats']['contact_diagnostics']['rod_longest_run'])
    rg=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'office_v5_push_rod_geom')
    hg=mujoco.mj_name2id(m,mujoco.mjtObj.mjOBJ_GEOM,'hand_collision')
    separation=[];streak=[];departures=[]
    if rod:
        first=rod['first_s'];end=23.5
        indices=np.flatnonzero((trace['time']>=first)&(trace['time']<end))
        start=trace['hand'][indices[0]]
        delta=trace['hand'][indices]-start
        rod_audit.update(hand_max_push_direction_mm=float((-delta[:,0]).max()*1000),
                         hand_max_tangent_yz_mm=float(np.linalg.norm(delta[:,1:],axis=1).max()*1000))
        for i in indices:
            d.qpos[:]=trace['qpos'][i];mujoco.mj_forward(m,d)
            gap=float(mujoco.mj_geomDistance(m,d,rg,hg,.5,None))
            separation.append([float(trace['time'][i]),gap,float(trace['rod_travel'][i])])
            # For this mesh mj_geomDistance can report hull overlap when the
            # actual collision detector has no contact. Do not use that as a
            # clearance certificate: require zero force-bearing contact at
            # ALL physical substeps in each recorded interval instead.
            free=trace['rod_contact_interval_s'][i]==0 and trace['rod_travel'][i]>.225
            if free:streak.append(i)
            if (not free or i==indices[-1]) and streak:
                if trace['time'][streak[-1]]-trace['time'][streak[0]]>=.5:
                    departures.append(dict(first_s=float(trace['time'][streak[0]]),last_s=float(trace['time'][streak[-1]])))
                streak=[]
    rod_audit.update(pre_retraction_departures=departures,
                     criterion='actual rod travel>225mm and no palm force>0.05N at any physical substep continuously>=0.5s before fixed retract start23.5s; contact audit, no altered success gate',
                     gap_diagnostic_only='mj_geomDistance hull distance disagrees with actual mesh collision detection; not a clearance certificate')
    record=dict(ball=ball,rod=rod_audit,contact_pairs=meaningful,
                payload_contacts=[k for k,v in meaningful.items() if 'target_object' in k],
                rod_human_contacts=[k for k in meaningful if 'push_rod' in k and ('human' in k or 'person' in k or 'arm_geom' in k)],
                physical_valid=s['physical_valid'],task_success=s['task_success'],strict_success=s['strict_success'],
                data_sha256={p.name:sha(p) for p in (prefix.with_suffix('.mjb'),prefix.with_suffix('.npz'),a.run/'esn_combined_v4_apparatus_trace.npz')})
    np.savez_compressed(a.run/'rod_surface_gap_audit.npz',time_gap_travel=np.array(separation))
    out.write_text(json.dumps(record,indent=2))
    print(json.dumps({k:v for k,v in record.items() if k not in ('contact_pairs','data_sha256')},indent=2))


if __name__=='__main__':main()
