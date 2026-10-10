"""Summarize four offline credit cells without held-out reads."""
import argparse
from pathlib import Path
from office_v7_uniform24_20261008 import read,write,sha,now

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();cells=[];registration=read(a.root/'REGISTRATION.json')
    for path in sorted(a.root.glob('n*/direct_office_task_segment011k')):
        state=read(path/'execution.json');assert state['status']=='complete' and state['steps']==11000 and state['updates']==12002
        spec=read(path/'PROTOCOL.json');cp=path/'checkpoint_0011000'
        cells.append(dict(cell=path.parent.name,reward_variant=spec['reward_variant'],n_step=spec['agent_config']['n_step'],
            steps=state['steps'],updates=state['updates'],new_physics_steps=0,development_reads=0,
            checkpoint_sha256=sha(cp/'official_agent_state.json'),replay_sha256=sha(cp/'office_replay.npz'),
            original_parent_checkpoint_sha256=next(j for j in registration['jobs'] if j['root']==str(path.parent.resolve()))['protocol_sha256'],
            task_or_strict_success=None,interpretation='Offline pure-RL ablation; no closed-loop score'))
    assert len(cells)==4
    write(a.output,dict(created_utc=now(),source_sha256=sha(__file__),cells=cells,
        unchanged=['frozen physics/gates/actor48/actuator limits','no teacher or BC','no heldout/final reads'],
        limitations=['off-policy data reuse','single seed','11k retained prefix only','no policy development evaluation'],
        result='All four cells completed 12002 updates with zero new physics; not a usable baseline or final comparison.'))
    print([(c['cell'],c['n_step'],c['reward_variant'],c['updates']) for c in cells])
if __name__=='__main__':main()
