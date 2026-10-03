"""All-real teacher data with whole-identity splits and an explicit rejection ledger.

Reads only train/imitation-validation histories from the new registered bank.
No synthetic, counterfactual, development or sealed histories enter this data.
Requested actions are the imitation target; filtered and actual execution remain
separately recorded, avoiding accidental double-filtering at deployment.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import numpy as np
from optimize_tool_contact_20261002 import ROOT, sha, write, now, ParameterTeacher
from wbc_velocity_residual_core import VelocityResidualActionFilter, VelocityResidualSafetyConfig

FILTER_CONFIG=VelocityResidualSafetyConfig(maximum_linear_yield_mps=.32)


def filtered_labels(observations,config):
    """Replay the actual teacher/filter without importing a training framework."""
    teacher=ParameterTeacher(config);filt=VelocityResidualActionFilter(FILTER_CONFIG)
    requests=[];labels=[]
    for observation in observations:
        teacher.observe(observation);raw=teacher.act(observation[39:45]);result=filt.filter(raw,.04)
        requests.append(raw)
        labels.append(np.r_[(1-result.wbc_scale)/(1-filt.config.minimum_wbc_scale),
            result.cartesian_yield_twist/np.r_[np.full(3,filt.config.maximum_linear_yield_mps),np.full(3,filt.config.maximum_angular_yield_radps)]])
    return np.asarray(requests),np.asarray(labels)


def read(path):
    return json.loads(path.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    cg=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cg/'memory.max').read_text().strip()
    assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    protocol=read(root/'PROTOCOL.json');protocol_sha=sha(root/'PROTOCOL.json')
    assert protocol['schema']=='sii-research72-v1'
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    assert sha(root/'teacher.json')==protocol['teacher_config_sha256']
    assert read(root/'teacher_bank/execution.json')['status']=='complete'
    summary=read(root/'teacher_bank/SUMMARY.json')
    conditions={c['id']:c for c in read(root/'CONDITIONS.json')['conditions']}
    assert len(summary['rows'])==len(conditions)==48
    assert {r['name'] for r in summary['rows']}==set(conditions)
    out.mkdir(parents=True,exist_ok=False)
    state=dict(status='running',started_utc=now(),argv=sys.argv,host=platform.node(),
        python=sys.executable,numpy=np.__version__,memory_max=memory,protocol_sha256=protocol_sha)
    write(out/'execution.json',state)
    source_files=[Path(__file__),
        ROOT/'tools/optimize_tool_contact_20261002.py',ROOT/'scripts/vmc_teacher_stable_readout_20260930.py',
        ROOT/'scripts/wbc_velocity_residual_core.py']
    hashes={str(p.relative_to(ROOT)):sha(p) for p in source_files}
    for f in source_files:shutil.copy2(f,out/f.name)
    arrays={k:[] for k in ('observation','episode','train','importance','requested_teacher_action',
        'filtered_teacher_action','clipped_teacher_action','executed_yield_twist','executed_wbc_scale','physical_execution')}
    lineage=[];ledger=[]
    try:
        teacher=read(root/'teacher.json')
        for row in summary['rows']:
            c=conditions[row['name']];run=Path(row['run'])
            assert run.parent.parent==root/'teacher_bank' and run.name==c['id']
            record=read(run/'execution.json');audit=read(run/'AUDIT.json')
            assert record['status']=='complete' and sha(run/'AUDIT.json')==row['audit_sha256']
            assert record['runtime_provenance']['research_protocol_sha256']==protocol_sha
            assert record['runtime_provenance']['research_condition']==c
            assert sha(run/'config.json')==protocol['teacher_config_sha256']
            assert sha(run/'rollout.npz')==audit['trace_sha256']==row['trace_sha256']
            assert sha(run/'execution_chain.npz')==audit['chain_sha256']
            assert sha(run/'rollout.mjb')==protocol['formal_model_sha256']
            detail=read(run/'rollout.json')
            qualified=bool(detail['full_task_horizon_completed'] and detail['task_success'] and detail['strict_success'])
            include=qualified and c['role'] in ('train','imitation_validation')
            ledger.append(dict(condition_id=c['id'],role=c['role'],qualified=qualified,included=include,
                task_success=detail['task_success'],strict_success=detail['strict_success'],full_horizon=detail['full_task_horizon_completed'],
                reason='qualifying demonstration' if include else 'development role excluded' if c['role']=='development' else 'original task/strict/full-horizon failed',
                run=str(run),trace_sha256=row['trace_sha256'],audit_sha256=row['audit_sha256']))
            if not include:continue
            with np.load(run/'rollout.npz',allow_pickle=False) as z:
                obs=z['observation'].copy();requested=z['applied_action'].copy()
            with np.load(run/'execution_chain.npz',allow_pickle=False) as z:
                chain={k:z[k].copy() for k in z.files}
            assert obs.shape==(1375,48) and requested.shape==(1375,7)
            assert all(np.isfinite(v).all() for v in (obs,requested,*chain.values()))
            np.testing.assert_array_equal(requested,chain['requested_action'])
            raw,filtered=filtered_labels(obs,teacher)
            np.testing.assert_allclose(raw,requested,rtol=0,atol=1e-10)
            np.testing.assert_allclose(filtered,chain['filtered_action'],rtol=0,atol=1e-12)
            executed=np.c_[(1-chain['wbc_scale'])/(1-FILTER_CONFIG.minimum_wbc_scale),
                chain['yield_twist']/np.r_[np.full(3,FILTER_CONFIG.maximum_linear_yield_mps),np.full(3,FILTER_CONFIG.maximum_angular_yield_radps)]]
            np.testing.assert_array_equal(executed,chain['filtered_action'])
            episode=len(lineage);n=len(obs)
            values=dict(observation=obs,episode=np.full(n,episode,np.int32),train=np.full(n,c['role']=='train',bool),
                importance=np.ones(n),requested_teacher_action=requested,filtered_teacher_action=chain['filtered_action'],
                clipped_teacher_action=chain['clipped_action'],executed_yield_twist=chain['yield_twist'],
                executed_wbc_scale=chain['wbc_scale'],physical_execution=np.ones(n,bool))
            for key,value in values.items():arrays[key].append(value)
            lineage.append(dict(episode=episode,condition_id=c['id'],data_role=c['role'],path=str(run/'rollout.npz'),
                sha256=sha(run/'rollout.npz'),chain_sha256=sha(run/'execution_chain.npz'),actual_execution_labels=True,
                counterfactual_relabel=False,synthetic=False,task_success=True,strict_success=True,
                physics_dt_s=protocol['physics_dt_s'],execution_sha256=sha(run/'execution.json'),
                physical_metrics_path=str(run/'rollout_metrics/substep_metrics.npz'),physical_metrics_sha256=audit['metrics_sha256']))
        write(out/'QUALIFICATION_LEDGER.json',ledger)
        assert sum(x['data_role']=='train' for x in lineage)>=4, 'Too few successful real training identities'
        assert sum(x['data_role']=='imitation_validation' for x in lineage)>=2, 'Too few validation identities; do not substitute development'
        combined={k:np.concatenate(v) for k,v in arrays.items()}
        assert not set(combined['episode'][combined['train']]).intersection(combined['episode'][~combined['train']])
        np.savez_compressed(out/'training_data.npz',**combined)
        result=dict(completed_utc=now(),training_data_sha256=sha(out/'training_data.npz'),lineage=lineage,
            qualification_ledger_sha256=sha(out/'QUALIFICATION_LEDGER.json'),source_sha256=hashes,
            protocol_sha256=protocol_sha,position_error_context=True,all_real_execution=True,
            actual_filter_replay_verified=True,actual_requested_labels_preserved=True,label_replay_atol=1e-10,
            episodes=len(lineage),training_identities=sum(x['data_role']=='train' for x in lineage),
            validation_identities=sum(x['data_role']=='imitation_validation' for x in lineage),frames=len(combined['episode']),
            target_semantics='Learn actual requested actions; common filter applies once during deployment. Filtered/action/actuator data are distinct.',
            selection_split='Whole real physical identities, preassigned imitation_validation; not closed-loop generalization',
            limitations='Positive demonstration qualification disclosed; all collection failures retained. Same frozen geometry and narrow disturbance distribution. No final/closed-loop-development histories or synthetic labels included.')
        assert all(sha(ROOT/k)==h for k,h in hashes.items())
        write(out/'DATA_COMPLETE.json',result);state.update(status='complete',training_data_sha256=result['training_data_sha256'])
        print(json.dumps({k:result[k] for k in ('episodes','training_identities','validation_identities','frames','training_data_sha256')}))
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:state['ended_utc']=now();write(out/'execution.json',state)


if __name__=='__main__':main()
