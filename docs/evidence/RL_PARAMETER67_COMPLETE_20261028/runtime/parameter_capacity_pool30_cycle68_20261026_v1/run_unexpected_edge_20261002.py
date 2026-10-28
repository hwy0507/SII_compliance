"""Bounded same-world evaluation for a prior-map-omission obstruction."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import mujoco
import numpy as np
import validate_office_apparatus_v5_20260917 as evaluator
from audit_temporal_narrow_screen_20261001 import audit


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--method',choices=('nominal','esn','mlp'),required=True)
    p.add_argument('--clear',action='store_true')
    p.add_argument('--expected-mjb')
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();run=args.output.resolve();run.mkdir(parents=True,exist_ok=False)
    reference=ROOT/'outputs/temporal_s52_latent_dropout_20261001_v1/p010_eval'
    kind='mlp' if args.method=='mlp' else 'esn'
    original=json.loads((reference/f'{kind}_combined_v4.json').read_text())
    config=ROOT/'configs/office_unexpected_edge_20261002.json'
    assert mujoco.__version__=='3.11.0'
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    if args.method!='nominal' and not args.expected_mjb:raise ValueError('Learned evaluation requires the frozen nominal model hash')
    checkpoint=reference/f'{kind}_temporal.npz'
    assert sha(checkpoint)==original['neural_logging']['model_sha256']
    shutil.copy2(checkpoint,run/checkpoint.name)
    shutil.copy2(reference/'TRAINING_COMPLETE.json',run/'TRAINING_COMPLETE.json')
    shutil.copy2(config,run/config.name)
    prefix=run/f'{kind}_combined_v4'
    a=dict(original['arguments'],output=prefix,esn_model=run/checkpoint.name,
           rod_start=12.,interaction_schedule='sequential-r12-v1',planned_hand_corner=True,
           unexpected_edge=not args.clear,allow_lateral_rejoin=True)
    if args.method=='nominal':a.update(esn_model=None,esn_mode='shadow')
    sources={str(f.relative_to(ROOT)):sha(f) for f in (ROOT/'scripts').glob('*.py')}
    sources[str(Path(__file__).relative_to(ROOT))]=sha(__file__)
    renderer=ROOT/'tools/render_office_threeview_20260929.py';sources[str(renderer.relative_to(ROOT))]=sha(renderer)
    subprocess.run(['tar','-czf',str(run/'source_overlay.tar.gz'),*sources, str(config.relative_to(ROOT))],cwd=ROOT,check=True)
    record=dict(status='running',started_utc=now(),method=args.method,clear=args.clear,
                argv=sys.argv,python=sys.executable,mujoco=mujoco.__version__,memory_max=memory,threads=1,
                config_sha256=sha(config),checkpoint_sha256=sha(checkpoint),training_performed=False,
                checkpoint_active=args.method!='nominal',source_sha256=sources,
                source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                arguments={k:str(v) if isinstance(v,Path) else v for k,v in a.items()})
    state=run/'execution.json';state.write_text(json.dumps(record,indent=2))
    save=mujoco.mj_saveModel
    def checked(model,filename,buffer):
        result=save(model,filename,buffer);record['model_sha256']=sha(filename)
        state.write_text(json.dumps(record,indent=2))
        if args.expected_mjb:assert sha(filename)==args.expected_mjb
        return result
    mujoco.mj_saveModel=checked
    try:
        with (run/'rollout.log').open('w') as log,contextlib.redirect_stdout(log):
            evaluator.run(SimpleNamespace(**a))
        summary=json.loads(prefix.with_suffix('.json').read_text())
        with np.load(run/f'{kind}_combined_v4_metrics/substep_metrics.npz') as z:
            dt=z['dt'];e=z['error']
            assert all(np.isfinite(z[k]).all() for k in z.files if np.issubdtype(z[k].dtype,np.number))
            result=dict(method=args.method,task_success=summary['task_success'],strict_success=summary['strict_success'],
                        stage=summary['final_task_stage'],physical_seconds=float(dt.sum()),substeps=len(dt),
                        position_rmse_mm=float(np.sqrt(np.sum(e*e*dt[:,None])/dt.sum())*1000),
                        peak_torque_nm=float(abs(z['qfrc_actuator']).max()),
                        peak_speed_mps=float(np.linalg.norm(z['twist'][:,:3],axis=1).max()),
                        external_penetration_mm=1000*summary['stats']['max_external_penetration_m'],
                        edge=summary['stats'].get('unexpected_edge'),abort_reason=summary['abort_reason'])
        assert abs(result['position_rmse_mm']/1000-summary['metrics']['position_rmse_3d_m'])<1e-5
        assert abs(result['peak_torque_nm']-summary['metrics']['generalized_actuator_torque_peak_nm'])<1e-5
        assert abs(result['peak_speed_mps']-summary['metrics']['linear_speed_peak_mps'])<1e-7
        if args.method=='nominal':
            with np.load(prefix.with_suffix('.npz')) as z:assert np.all(z['applied_action']==0)
        elif summary['full_task_horizon_completed']:
            result['policy_audit']=audit(run,kind)
        (run/'AUDIT.json').write_text(json.dumps(result,indent=2))
        record.update(status='rendering',audit=result);state.write_text(json.dumps(record,indent=2))
        command=[sys.executable,str(renderer),'--rollout',str(prefix),'--output',str(run/'media'),
                 '--label',f'{args.method.upper()} | '+('clear control' if args.clear else 'unknown physical edge')+' | 1x | development',
                 '--stride','1','--fps','25','--gif-stride','5']
        record['render_command']=command
        with (run/'render.log').open('w') as log:subprocess.run(command,cwd=ROOT,check=True,stdout=log,stderr=subprocess.STDOUT)
        assert all(sha(ROOT/name)==digest for name,digest in sources.items()),'Live source changed'
        record.update(status='complete',plan_sha256=sha(prefix.with_suffix('.plan.json')))
    except BaseException as exc:
        record.update(status='failed',error=repr(exc));raise
    finally:
        mujoco.mj_saveModel=save;record['ended_utc']=now();state.write_text(json.dumps(record,indent=2))
    print(json.dumps(record.get('audit',record),indent=2))


if __name__=='__main__':main()
