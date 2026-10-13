"""Saved-pose rod geometry, separate from authoritative physical contact metrics."""
import json,hashlib
from pathlib import Path
import mujoco
import numpy as np


def main():
    root=Path(__file__).resolve().parents[1]/'outputs/original_esn_rod_opposition_20261013'
    output=root/'ROD_GEOMETRY.json'
    if output.exists():raise FileExistsError(output)
    m=mujoco.MjModel.from_binary_path(str(root/'episode/rollout.mjb'));d=mujoco.MjData(m)
    names=[mujoco.mj_id2name(m,mujoco.mjtObj.mjOBJ_GEOM,i) or '' for i in range(m.ngeom)]
    rod={i for i,n in enumerate(names) if 'office_v5_push_rod' in n}
    assert rod, names
    pairs={}
    with np.load(root/'episode/rollout.npz') as z:
        for t,q,v,c in zip(z['time'],z['qpos'],z['qvel'],z['ctrl']):
            d.qpos[:]=q;d.qvel[:]=v;d.ctrl[:]=c;mujoco.mj_forward(m,d)
            for contact in d.contact:
                a,b=int(contact.geom1),int(contact.geom2)
                if contact.dist>0 or not ({a,b}&rod):continue
                key=names[a]+' / '+names[b]
                record=pairs.setdefault(key,dict(frames=0,first_s=float(t),last_s=float(t),max_penetration_m=0.))
                record['frames']+=1;record['last_s']=float(t)
                record['max_penetration_m']=max(record['max_penetration_m'],-float(contact.dist))
    receipt=dict(rod_geometries=[names[i] for i in sorted(rod)],saved_pose_pairs=pairs,
        trace_sha256=hashlib.sha256((root/'episode/rollout.npz').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        caveat='25Hz saved-pose collision geometry only; neither exact dynamics force nor proof of no between-frame contacts. Event rod in rollout.json measures rod-robot contacts, not all rod-object contacts.')
    output.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__':main()
