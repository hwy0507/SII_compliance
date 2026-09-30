"""Independent finite-value and equality audit of completed zero-parameter parity."""
import argparse
import json
import hashlib
from pathlib import Path
import numpy as np


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--parity',type=Path,required=True)
    args=parser.parse_args();root=args.parity
    primary=root/('COMPLETE.json' if (root/'COMPLETE.json').exists() else 'FAILED.json')
    completed=json.loads(primary.read_text())
    if primary.name=='FAILED.json' and completed['error']!='AssertionError("Result dynamics/audit differ:[\'contact\']")':
        raise ValueError('Unexpected primary failure; requires independent diagnosis')
    finite=[];exact=[]
    for file in sorted(root.rglob('*.npz')):
        with np.load(file,allow_pickle=False) as archive:
            for key in archive.files:
                values=archive[key]
                if values.dtype.kind in 'fciu':
                    passed=bool(np.isfinite(values).all())
                    finite.append(dict(file=str(file.relative_to(root)),key=key,shape=list(values.shape),passed=passed))
                    if not passed:raise ValueError(f'Nonfinite values in{file}:{key}; cannot prove valid interface')
    a_root,b_root=root/'nominal_vmc',root/'zero_parameter'
    for name in ('rollout.npz','physics_states.npz','contact_samples.npz'):
        with np.load(a_root/name,allow_pickle=False) as first,np.load(b_root/name,allow_pickle=False) as second:
            if first.files!=second.files:raise ValueError('Different array fields')
            for key in first.files:
                if name=='rollout.npz' and key=='teacher_action':
                    if not np.array_equal(first[key],second['action']) or np.any(second[key]):
                        raise ValueError('Teacher-action label semantics do not match declared exception')
                    exact.append(dict(file=name,key=key,rule='A.teacher_action=B.action and B.teacher_action=0',passed=True))
                else:
                    passed=bool(np.array_equal(first[key],second[key]))
                    if not passed:raise ValueError(f'Exact finite equality failed{name}:{key}')
                    exact.append(dict(file=name,key=key,rule='A=B',passed=True))
    hashes=[sha(p/'rollout.mjb') for p in (a_root,b_root)]
    if hashes[0]!=hashes[1]:raise ValueError('MJB hash mismatch')
    results=[json.loads((p/'rollout.json').read_text()) for p in (a_root,b_root)]
    first,second=results
    changed_contact=[k for k in first['contact'] if first['contact'][k]!=second['contact'][k]]
    set_fields=('pairs','robot_geoms','robot_bodies','other_contacts')
    if any(k not in set_fields for k in changed_contact):raise ValueError('True contact-value mismatch')
    for result in results:
        for key in set_fields:result['contact'][key]=sorted(result['contact'][key],key=lambda x:json.dumps(x,sort_keys=True))
    if set(first)!=set(second):raise ValueError('Result keys mismatch')
    for key in first:
        if key not in ('controller','teacher_called','arguments') and first[key]!=second[key]:
            raise ValueError(f'Result JSON differs after declared set semantics:{key}')
    if not first['teacher_called'] or second['teacher_called']:raise ValueError('Unexpected teacher branch')
    arg_diff=[k for k in first['arguments'] if first['arguments'][k]!=second['arguments'][k]]
    if set(arg_diff)!={'output','model'}:raise ValueError('Unexpected argument changes')
    protocol=json.loads((root/'protocol.json').read_text())
    snapshot=root.parent/'source'
    source_checks={name:dict(expected=value,actual=sha(snapshot/name)) for name,value in protocol['source_hashes'].items()}
    if any(v['expected']!=v['actual'] for v in source_checks.values()):raise ValueError('Source snapshot changed')
    artifact_hashes={str(f.relative_to(root)):sha(f) for f in root.rglob('*')
        if f.is_file() and (f.suffix in ('.npz','.mjb') or f.name in ('protocol.json','rollout.json','FAILED.json'))}
    nominal=json.loads(protocol['jobs'][0]['environment']['CORE_VMC_CONFIG'])
    with np.load(b_root/'vmc_parameter_trace.npz',allow_pickle=False) as trace,np.load(b_root/'rollout.npz',allow_pickle=False) as rollout:
        if trace['parameter_request'].shape!=(600,6) or np.any(trace['parameter_request']) or np.any(trace['log_scale']):
            raise ValueError('Not zero parameters over full600step episode')
        for field,cfg in [('stiffness','stiffness_6d'),('damping','damping_6d')]:
            if not np.array_equal(trace[field],np.tile(nominal[cfg],(600,1))):raise ValueError('Nominal K/D differ')
        for key in ('action','observation'):
            if not np.array_equal(trace[key],rollout[key]):raise ValueError('Parameter trace differs')
        if rollout['observation'].shape!=(600,48):raise ValueError('Full24s trace not completed')
    report=dict(passed=True,all_numeric_arrays_finite=True,numeric_arrays_checked=len(finite),
        finite_checks=finite,exact_array_checks=exact,model_mjb_sha256=hashes[0],
        source='Independent local audit; primary runner unchanged despite equal_nan implementation',
        learned_policy=False,primary_status=primary.stem,primary_status_sha256=sha(primary),
        primary_failure_preserved=primary.name=='FAILED.json',
        semantic_contact_set_fields=list(set_fields),contact_fields_with_order_only_changes=changed_contact,
        semantic_json_equal=True,parameter_trace_nominal_exact=True,task_success=first['success'],
        source_snapshot_unchanged=True,source_checks=source_checks,artifact_sha256=artifact_hashes,
        accepted_panel_demo=first['accepted_panel_demo'],
        set_semantics_source='run_primitive_teacher_v7_20260917.py:34 clean iterates set; lines232-235 initialize the four set fields',
        scope='Independent finite numeric and semantic-set equivalence; does not retroactively mark primary runner passed')
    (root/'FINITE_EXACT_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('finite_checks','exact_array_checks','source_checks','artifact_sha256')},indent=2))


if __name__=='__main__':main()
