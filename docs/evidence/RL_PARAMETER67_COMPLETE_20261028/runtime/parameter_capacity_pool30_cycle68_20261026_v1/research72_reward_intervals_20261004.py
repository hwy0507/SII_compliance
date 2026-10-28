"""Recompute saved RL reward inputs from immutable raw physical-substep logs.

No actor/learner, simulator steps, policy selection, or condition-file reads.
Partition by physical/actor timestamps, not the interval's claimed row count.
Potential and initial potential are explicitly outside this reduction audit.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

import numpy as np


def read(path): return json.loads(Path(path).read_text())
def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def check_intervals(physical, actor_start, actor_end, filtered, intervals, torque_limits):
    t = physical['time']; dt = physical['dt']; error = physical['error']; tau = physical['qfrc_actuator']
    n = len(t); count = len(actor_end)
    assert n and count and len(intervals)==count+1 and intervals[0] is None
    assert dt.shape==t.shape==(n,) and error.shape==(n,3) and tau.shape==(n,7)
    assert actor_start.shape==(count,) and filtered.shape==(count,7)
    assert torque_limits.shape==(7,) and np.all(torque_limits>0)
    assert all(np.isfinite(v).all() for v in (t,dt,error,tau,actor_start,actor_end,filtered,torque_limits))
    assert np.all(np.diff(t)>0) and np.all(dt>0) and np.all(np.diff(actor_end)>0)
    np.testing.assert_allclose(t-np.r_[0.,t[:-1]],dt,rtol=0,atol=1e-10)
    np.testing.assert_allclose(actor_start,np.r_[0.,actor_end[:-1]],rtol=0,atol=1e-10)
    assert actor_end[-1]==t[-1], 'Missing terminal physical samples'
    ends = np.searchsorted(t,actor_end,side='right')
    assert np.all(ends>0) and np.all(np.diff(ends)>0) and ends[-1]==n
    np.testing.assert_array_equal(t[ends-1],actor_end)
    begin = 0; max_error = {}; elapsed = 0.
    for index,(end,record) in enumerate(zip(ends,intervals[1:])):
        assert record['substeps']==end-begin, 'Interval count differs from timestamps'
        weights = dt[begin:end].astype(np.float64)
        squared = np.sum(error[begin:end].astype(np.float64)**2,axis=1)
        effort = np.abs(tau[begin:end].astype(np.float64))
        actual = dict(elapsed_s=float(np.sum(weights)),
            error_integral=float(np.sum(weights*squared)),
            bounded_error_integral=float(np.sum(weights*squared/(.12**2+squared))),
            peak_torque_ratio=float(np.max(effort/torque_limits)),
            peak_torque_nm_per_joint=effort.max(axis=0),
            max_position_error_m=float(np.sqrt(squared.max())))
        for key,value in actual.items():
            expected=np.asarray(record[key],dtype=float)
            assert np.isfinite(expected).all()
            np.testing.assert_allclose(value,expected,rtol=1e-12,atol=1e-13,
                err_msg=f'Interval {index}, {key}')
            max_error[key]=max(max_error.get(key,0.),float(np.max(np.abs(value-expected))))
        np.testing.assert_array_equal(filtered[index],record['executed_action'])
        elapsed += actual['elapsed_s']; begin=int(end)
    return dict(intervals_checked=count,substeps_checked=n,elapsed_s=elapsed,
        timestamp_partition_verified=True,filtered_action_max_abs=0.,max_absolute_error=max_error,
        numerical_comparison=dict(rtol=1e-12,atol=1e-13),potential_checked=False)


def audit_run(run, original, expected_model):
    import mujoco  # Load the archived MJB; never create MjData or call mj_step.
    names=('execution.json','AUDIT.json','rollout.json','rollout.npz','rollout.mjb',
           'execution_chain.npz','rollout_metrics/substep_metrics.npz','RL_INTERVALS.json')
    hashes={name:sha(run/name) for name in names}
    assert hashes['AUDIT.json']==original['audit_sha256']
    assert hashes['rollout.npz']==original['trace_sha256']
    assert hashes['rollout.mjb']==expected_model
    execution=read(run/'execution.json'); audit=read(run/'AUDIT.json'); summary=read(run/'rollout.json')
    assert execution['status']=='complete' and audit['training']
    assert hashes['execution_chain.npz']==audit['chain_sha256']
    assert hashes['rollout_metrics/substep_metrics.npz']==audit['metrics_sha256']
    assert summary['physics_resolution']['base_dt_s']==.00005
    assert not summary['physics_resolution']['initial_refinement_dt_s']
    model=mujoco.MjModel.from_binary_path(str(run/'rollout.mjb'))
    limits=model.actuator_ctrlrange[:7,1].copy()
    np.testing.assert_array_equal(model.actuator_ctrlrange[:7,0],-limits)
    np.testing.assert_array_equal(limits,[87,87,87,87,12,12,12])
    del model
    with np.load(run/'rollout.npz',allow_pickle=False) as z:
        start=z['neuron_time'].copy();end=z['time'].copy();requested=z['applied_action'].copy()
    with np.load(run/'execution_chain.npz',allow_pickle=False) as z:
        np.testing.assert_array_equal(requested,z['requested_action'])
        filtered=z['filtered_action'].copy()
        cfg=execution['action_filter_config']
        reconstructed=np.column_stack(((1-z['wbc_scale'])/(1-cfg['minimum_wbc_scale']),
            z['yield_twist']/np.r_[np.full(3,cfg['maximum_linear_yield_mps']),
                                 np.full(3,cfg['maximum_angular_yield_radps'])]))
        np.testing.assert_array_equal(filtered,reconstructed)
    with np.load(run/'rollout_metrics/substep_metrics.npz',allow_pickle=False) as z:
        raw={key:z[key] for key in ('time','dt','error','qfrc_actuator')}
    np.testing.assert_array_equal(raw['dt'],np.full(len(raw['dt']),.00005))
    result=check_intervals(raw,start,end,filtered,read(run/'RL_INTERVALS.json'),limits)
    assert result['intervals_checked']==original['steps']
    assert result['substeps_checked']==summary['metrics']['samples']
    assert all(sha(run/name)==value for name,value in hashes.items())
    return dict(run=str(run),evidence_sha256=hashes,
        torque_ratio_denominator_source='Archived MJB first seven symmetric actuator control ranges, equal to frozen default effort limits',
        torque_limits=limits.tolist(),full_horizon=summary['full_task_horizon_completed'],
        abort_reason=summary['abort_reason'],task_success=summary['task_success'],
        strict_success=summary['strict_success'],**result)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',type=Path,action='append',required=True)
    p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    assert not args.output.exists() and len(set(args.manifest))==len(args.manifest)
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=int((cg/'memory.max').read_text());assert memory<=3*1024**3
    state=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=sha(__file__),host=platform.node(),python=sys.executable,numpy=np.__version__,
        argv=sys.argv,memory_max=memory,physics_steps=0,actor_calls=0,gradient_updates=0,sealed_reads=0,rows=[],
        limits=['Reduces recorded physical error/effort samples; does not re-simulate dynamics or establish contact realism.',
            'Task potential/initial potential and terminal next observation are not independently reconstructed.',
            'Filtered actions checked against execution chain, not a new actor or full servo replay.',
            'All episodes in each supplied completed segment included, including failures; not all fifteen final models.'])
    def save():
        temporary=args.output.with_suffix('.tmp')
        temporary.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');temporary.replace(args.output)
    save()
    try:
        for path in args.manifest:
            digest=sha(path);manifest=read(path);protocol=Path(manifest['training_protocol'])
            assert sha(protocol)==manifest['training_protocol_sha256']
            training=read(protocol)
            execution=Path(manifest['checkpoint']).parent/'execution.json';execution_digest=sha(execution)
            record=read(execution);assert record['status']=='complete'
            rows=[]
            for original in record['rows']:
                run=Path(original['run']);run_state=read(run/'execution.json')
                provenance=run_state['runtime_provenance']
                command=original['command'];research=Path(command[command.index('--research-protocol')+1])
                assert sha(research)==training['protocol_sha256']==provenance['research_protocol_sha256']
                rows.append(audit_run(run,original,read(research)['formal_model_sha256']))
            assert sum(row['intervals_checked'] for row in rows)==record['new_segment_steps']
            assert sha(path)==digest and sha(execution)==execution_digest
            state['rows'].append(dict(manifest=str(path.resolve()),manifest_sha256=digest,
                training_protocol_sha256=sha(protocol),execution_sha256=execution_digest,
                family=manifest['family'],seed=manifest['seed'],episodes=rows))
            save()
        state['status']='complete'
    except BaseException as exc:
        state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=datetime.now(timezone.utc).isoformat();save()
    episodes=[r for group in state['rows'] for r in group['episodes']]
    print(json.dumps(dict(status=state['status'],sha256=sha(args.output),episodes=len(episodes),
        intervals=sum(r['intervals_checked'] for r in episodes),substeps=sum(r['substeps_checked'] for r in episodes))))


if __name__=='__main__':main()
