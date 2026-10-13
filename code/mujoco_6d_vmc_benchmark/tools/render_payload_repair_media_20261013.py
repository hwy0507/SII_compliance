"""Render both valid bridge comparisons in full; never rerun simulation."""
import json,os,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/original_esn_payload_bridge_20261013'

def main():
    for arm,label in [('path_only','Frozen ESN | payload-aware planned path'),
                      ('path_bridge_v2','Frozen ESN | planned path + servo bridge'),
                      ('path_bridge_friction_probe','Frozen ESN | path + bridge + model friction FF')]:
        execution=json.loads((OUT/arm/'episode/execution.json').read_text())
        assert execution['status']=='complete'
        subprocess.run([sys.executable,'tools/render_office_threeview_20260929.py',
            '--rollout',str(OUT/arm/'episode/rollout'),'--output',str(OUT/arm/'media'),
            '--label',label,'--scene-label','Old cup-pillar office',
            '--stride','1','--fps','25','--gif-stride','5'],
            cwd=ROOT,env=dict(os.environ,MUJOCO_GL='egl'),check=True)

if __name__=='__main__':main()
