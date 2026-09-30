"""Freeze final completed potential PPO artifacts without inspecting scores."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import zipfile

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True)
    p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    complete=json.loads((args.pilot/'COMPLETE.json').read_text())
    manifest=json.loads((args.pilot/'manifest.json').read_text())
    if complete['status']!='complete' or complete['reward_version']!='push4_gate_potential_v1':raise ValueError('Experiment not complete')
    if manifest['training']['timesteps']!=8192:raise ValueError('Wrong predeclared budget')
    with zipfile.ZipFile(args.pilot/'ppo_final.zip') as archive:
        if json.loads(archive.read('data'))['num_timesteps']!=8192:raise ValueError('Wrong final checkpoint')
    names=('ppo_final.zip','vecnormalize_train_only.pkl','COMPLETE.json','manifest.json','eval/train/ppo/episode_00000/actor_trace.npz')
    files={n:sha(args.pilot/n) for n in names}
    if files['ppo_final.zip']!=complete['checkpoint_sha256']:raise ValueError('Final model differs from COMPLETE')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    report=dict(files=files,pilot=str(args.pilot),frozen_unix=time.time(),training_steps=8192,
        protocol_sha256=sha(args.protocol),selection='Fixed completed final8192; scores not consulted',
        reward_version=complete['reward_version'],planned_jobs=7)
    with args.output.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
