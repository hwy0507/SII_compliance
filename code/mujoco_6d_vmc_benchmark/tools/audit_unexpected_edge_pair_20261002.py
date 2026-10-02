"""Cross-row provenance, final tracking and media checks; retain every failure."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import re
import imageio_ffmpeg
from PIL import Image
import numpy as np


def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return h.hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--legacy',type=Path,required=True)
    a=parser.parse_args();rows=[];plans=[];blocked=[]
    output=a.root/'CROSS_ROW_AUDIT.json'
    if output.exists():raise FileExistsError(output)
    for name in ('nominal_clear','nominal_blocked','esn_blocked','mlp_blocked'):
        r=a.root/name;kind='mlp' if name=='mlp_blocked' else 'esn'
        prefix=r/f'{kind}_combined_v4'
        execution=json.loads((r/'execution.json').read_text())
        summary=json.loads(prefix.with_suffix('.json').read_text())
        audit=json.loads((r/'AUDIT.json').read_text())
        assert execution['status']=='complete'
        assert sha(prefix.with_suffix('.plan.json'))==execution['plan_sha256']
        assert sha(prefix.with_suffix('.mjb'))==execution['model_sha256']
        assert execution['arguments']['teacher']=='none' and not execution['arguments'].get('hybrid_vmc_blend',0)
        assert summary['full_task_horizon_completed'] and audit['substeps']==550000
        plans.append(execution['plan_sha256'])
        if name!='nominal_clear':blocked.append(execution['model_sha256'])
        with np.load(prefix.with_suffix('.npz')) as z, np.load(a.legacy/name/f'{kind}_combined_v4.npz') as old:
            same={k:bool(np.array_equal(z[k],old[k])) for k in ('qpos','qvel','applied_action','stage')}
            final={k:dict(min=float(z[k][-125:].min()),max=float(z[k][-125:].max())) for k in ('task_position_error_m','task_rotation_error_rad','task_speed_mps')}
        media=json.loads((r/'media/manifest.json').read_text())
        for extension in ('.mp4','.gif'):
            assert sha(r/'media'/('replay_threeview'+extension))==media['output_sha256'][extension]
        assert media['input_sha256']['.npz']==sha(prefix.with_suffix('.npz'))
        counts={}
        for extension,expected in (('.mp4',1375),('.gif',275)):
            path=r/'media'/('replay_threeview'+extension)
            if extension=='.gif':
                with Image.open(path) as im:count=im.n_frames
            else:
                result=subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-threads','1','-i',str(path),'-map','0:v:0','-f','null','-'],capture_output=True,text=True,check=True)
                count=int(re.findall(r'frame=\s*(\d+)',result.stderr)[-1])
            assert count==expected
            counts[extension]=count
        policy=audit.get('policy_audit')
        if policy:
            assert policy['action_replay_max_abs']==0
            assert policy['reservoir_state_replay_max_abs'] in (None,0)
            assert policy['checkpoint_and_mjb_metadata_hash_match']
        rows.append(dict(name=name,metrics=audit,final_five_seconds=final,exact_arrays_equal_to_v1=same,
                         media_frame_counts=counts,source_overlay_sha256=sha(r/'source_overlay.tar.gz'),
                         execution_sha256=sha(r/'execution.json')))
    assert len(set(plans))==1 and len(set(blocked))==1
    record=dict(rows=rows,plan_sha256=plans[0],blocked_model_sha256=blocked[0],
                formal=False,dt_s=.0001,independent_physical_metric_recompute='Per-row AUDIT.json from original 550000 substeps',
                limitation='One fixed pair of old checkpoints, not a seed sweep; no new-obstacle contact for a policy means its contact recovery was not tested')
    output.write_text(json.dumps(record,indent=2))
    print(json.dumps(dict(plan_sha256=plans[0],rows=[dict(name=r['name'],task=r['metrics']['task_success'],strict=r['metrics']['strict_success'],same_as_v1=r['exact_arrays_equal_to_v1']) for r in rows]),indent=2))


if __name__=='__main__':main()
