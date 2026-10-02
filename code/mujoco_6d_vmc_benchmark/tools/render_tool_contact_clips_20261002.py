"""Render genuine 200Hz archived poses; ball at quarter speed, rod at real time."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import numpy as np


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True)
    a=p.parse_args();src=a.run/'esn_combined_v4'
    record=json.loads(src.with_suffix('.json').read_text())
    trace_path=a.run/'esn_combined_v4_apparatus_trace.npz'
    with np.load(trace_path) as z:trace={k:z[k] for k in z.files}
    for name,start,end,stride,speed in [('ball',1.9,2.7,1,'0.25x'),('rod',12.5,23.4,4,'1x')]:
        folder=a.run/('clip_'+name);folder.mkdir(exist_ok=False)
        prefix=folder/'trajectory';selected=(trace['time']>=start)&(trace['time']<=end)
        np.savez_compressed(prefix.with_suffix('.npz'),**{k:v[selected] for k,v in trace.items()})
        info=dict(record,clip=dict(source=str(trace_path.resolve()),source_sha256=hashlib.sha256(trace_path.read_bytes()).hexdigest(),range_s=[start,end],playback=speed,physics_rerun=False))
        prefix.with_suffix('.json').write_text(json.dumps(info,indent=2))
        os.link(src.with_suffix('.mjb'),prefix.with_suffix('.mjb'))
        subprocess.run([sys.executable,str(Path(__file__).with_name('render_office_threeview_20260929.py')),
            '--rollout',str(prefix),'--output',str(folder/'media'),'--label',f'ESN | physical {name} contact | {speed}',
            '--stride',str(stride),'--fps','50','--gif-stride','5','--contact-closeup'],check=True)


if __name__=='__main__':main()
