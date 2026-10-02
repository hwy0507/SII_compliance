"""Explicit sequential evaluation jobs within the current five-hour session."""
import argparse,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path('/home/arm1/vmc_mujoco_runtime/primitive_baselines_20261002')
DEADLINE=1790944591.0
LABELS={'zero':'Zero / nominal','grid_admittance':'Classical admittance grid','grid_impedance':'Classical impedance grid'}
for c in ['admittance','impedance','vmc']:
    LABELS['fixed_'+c]='BO-derived fixed '+c
    LABELS['parameter_'+c]='Parameter RL '+c
for reward in ['metric','office_task']:
    for seed in [74001,74002]:LABELS[f'direct_{reward}_{seed}']=f'Direct RL {reward}, seed {seed}'
def arguments(identity,phase,parameter_step=None):
    checkpoint=None;controller=None;selection=None
    if identity=='zero':kind='zero'
    elif identity.startswith('grid_'):
        kind=identity[5:];selection=ROOT/'campaign01/classical/SELECTION.json'
    elif identity.startswith('fixed_'):kind='parameter_fixed';controller=identity[6:]
    elif identity.startswith('parameter_'):
        if parameter_step is None:raise ValueError('Require locked common parameter checkpoint step')
        kind='parameter_rl';controller=identity[10:];checkpoint=ROOT/'parameter_rl/campaign01'/f'{controller}_seed75001'/f'checkpoint_{parameter_step:07d}'
    elif identity.startswith('direct_'):
        kind='direct_rl';rest=identity[7:];reward,seed=rest.rsplit('_',1);checkpoint=ROOT/'campaign02'/f'{reward}_seed{seed}'/'checkpoint_0060000'
    else:raise ValueError(identity)
    output=ROOT/('office_bridge/transfer01' if phase=='office' else 'final_evaluation01' if phase=='test' else 'final_reference01')/identity
    if phase=='office':
        if selection:raise ValueError('Legacy grid implementation is not included in office transfer')
        worker=ROOT/'office_bridge/frozen03/evaluate.py'
        command=[sys.executable,str(worker),'--method','nominal' if kind=='zero' else kind,'--output',str(output)]
    else:
        worker=ROOT/('parameter_rl/frozen_evaluation03/evaluate.py' if controller else 'frozen_evaluation03/evaluate.py')
        method='rl' if kind in ('parameter_rl','direct_rl') else kind
        command=[sys.executable,str(worker),'--method',method,'--output',str(output),'--split',phase]
        if phase=='test':command+=['--indices','0','1','2']
        if not controller:command+=['--detailed-contact']
    if controller:command+=['--controller',controller]
    if checkpoint:command+=['--checkpoint',str(checkpoint)]
    if selection:command+=['--selection',str(selection)]
    return command,output,checkpoint
def main():
    p=argparse.ArgumentParser();p.add_argument('--ids',nargs='+',choices=list(LABELS),required=True);p.add_argument('--phase',choices=['test','reference','office'],required=True);p.add_argument('--parameter-step',type=int);p.add_argument('--run-id',required=True);p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    jobs=[(identity,*arguments(identity,a.phase,a.parameter_step)) for identity in a.ids]
    if a.dry_run:
        print(json.dumps([dict(id=i,command=c,checkpoint_exists=cp.exists() if cp else None) for i,c,o,cp in jobs],indent=2));return
    logdir=ROOT/'dispatch'/a.run_id;logdir.mkdir(parents=True,exist_ok=False)
    rows=[]
    for identity,command,output,checkpoint in jobs:
        if checkpoint and not (checkpoint/'official_agent_state.json').is_file():raise FileNotFoundError(checkpoint)
        if output.exists():raise FileExistsError(output)
        remaining=DEADLINE-time.time()
        minimum={'test':1200,'reference':360,'office':240}[a.phase]
        if remaining<minimum:
            rows.append(dict(id=identity,status='not_started_budget',remaining_s=remaining));break
        item=dict(id=identity,label=LABELS[identity],phase=a.phase,command=command,output=str(output),started_epoch=time.time(),parameter_step=a.parameter_step)
        (logdir/(identity+'_command.json')).write_text(json.dumps(item,indent=2))
        with (logdir/(identity+'.log')).open('w') as log:
            proc=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            try:rc=proc.wait(timeout=max(1,DEADLINE-time.time()-60))
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid,signal.SIGTERM)
                try:proc.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
                rc=124
        item.update(returncode=rc,finished_epoch=time.time(),status='complete' if rc==0 else 'failed');rows.append(item)
        (logdir/'STATE.json').write_text(json.dumps(rows,indent=2));print(json.dumps(dict(id=identity,phase=a.phase,status=item['status'],output=str(output))),flush=True)
        if rc:raise RuntimeError('Evaluation failure preserved: '+identity)
    (logdir/'STATE.json').write_text(json.dumps(rows,indent=2))
    (logdir/'COMPLETE.json').write_text(json.dumps(dict(dispatched=len(rows),finished_epoch=time.time()),indent=2))
if __name__=='__main__':main()
