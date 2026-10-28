"""Paired public teacher-data audit, never a student fit or final evaluation.

An unfinished collector may be read only if every identity in the explicitly
requested public role is already complete. No partial-role success denominator.
Recompute recorded substep metrics with the predeclared v4 implementation.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import statistics
import sys

import numpy as np
from paper_metrics_20261002 import measure


def read(path): return json.loads(Path(path).read_text())
def sha(path):
    result=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):result.update(block)
    return result.hexdigest()
def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def avg(values):return statistics.mean(values) if values else None


def summarize(rows):
    accepted=[r for r in rows if r['metrics']['strict_success'] and r['metrics']['full_horizon']]
    result=dict(attempts=len(rows),task=sum(r['metrics']['task_success'] for r in rows),
        strict=sum(r['metrics']['strict_success'] for r in rows),qualifying_demonstrations=len(accepted),
        failure_pairs=dict(Counter('/'.join(r['worst_pair']) for r in rows if not r['metrics']['strict_success'])),
        metrics_all={key:dict(mean=avg([r['metrics'][key] for r in rows]),
                              maximum=max(r['metrics'][key] for r in rows))
                     for key in ('rmse_mm','peak_torque_nm','peak_speed_mps','placement_error_xy_mm')})
    for scope,subset in [('all_attempts',rows),('qualifying_only',accepted)]:
        result[scope]={}
        for event in ('ball','human','rod','pillar','unknown_edge'):
            exposed=[r for r in subset if r['metrics']['contact'][event]['exposure']]
            result[scope][event]=dict(exposed=len(exposed),denominator=len(subset),
                identities=[r['condition_id'] for r in exposed],
                contact_p95_mean_n=avg([r['metrics']['contact'][event]['contact_p95_force_n'] for r in exposed]),
                force_magnitude_integral_mean_ns=avg([r['metrics']['contact'][event]['impulse_ns'] for r in exposed]))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--role',choices=('train','imitation_validation'),required=True)
    a=p.parse_args();root=a.root.resolve();out=a.output.resolve()
    cgroup=Path('/sys/fs/cgroup')/Path('/proc/self/cgroup').read_text().strip().split('::',1)[1].lstrip('/')
    memory=(cgroup/'memory.max').read_text().strip()
    assert memory!='max' and int(memory)<=3*1024**3
    assert all(os.environ.get(k)=='1' for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'))
    assert not out.exists() and not (root/'FINAL_UNSEAL_RECEIPT.json').exists()
    protocol=read(root/'PROTOCOL.json');pdigest=sha(root/'PROTOCOL.json')
    assert sha(root/'CONDITIONS.json')==protocol['condition_file_sha256']
    conditions={c['id']:c for c in read(root/'CONDITIONS.json')['conditions'] if c['role']==a.role}
    assert len(conditions)==(32 if a.role=='train' else 8)
    banks={'initial':root/'teacher_bank','selected':root/'teacher_refinement_v1/collection'}
    source=Path(__file__).resolve();metric_source=Path(measure.__code__.co_filename).resolve()
    choice=read(root/'followup_v1/CONTROLLER_CHOICE.json')
    selection=read(banks['selected']/'TEACHER_SELECTION.json')
    assert selection['choice_sha256']==sha(root/'followup_v1/CONTROLLER_CHOICE.json')
    assert selection['candidate']==next(c for c in choice['candidates'] if c['category']=='enhanced_teacher')
    out.mkdir()
    state=dict(status='running',started_utc=datetime.now(timezone.utc).isoformat(),
        argv=sys.argv,host=platform.node(),python=sys.executable,numpy=np.__version__,memory_max=memory,
        protocol_sha256=pdigest,source_sha256=sha(source),metric_source_sha256=sha(metric_source),
        role=a.role,physics_steps=0,fits=0,sealed_reads=0)
    write(out/'START.json',state)
    rows={};receipts={}
    try:
        for label,bank in banks.items():
            mapping={};receipts[label]=[]
            for path in sorted(bank.glob('queue_[0-3]/execution.json')):
                data=path.read_bytes();queue=json.loads(data)
                receipts[label].append(dict(path=str(path),snapshot_sha256=hashlib.sha256(data).hexdigest(),
                    snapshot=queue))
                for row in queue['rows']:
                    if row['name'] not in conditions:continue
                    assert row['name'] not in mapping and row.get('returncode')==0 and 'audit_sha256' in row
                    mapping[row['name']]=(path.parent/row['name'],row)
            assert set(mapping)==set(conditions),'Requested public role not fully completed'
            result=[]
            expected_config=protocol['teacher_config_sha256'] if label=='initial' else selection['teacher_config_sha256']
            for cid in sorted(mapping):
                run,original=mapping[cid];execution=read(run/'execution.json');audit=read(run/'AUDIT.json')
                assert execution['status']=='complete' and execution['runtime_provenance']['research_condition']==conditions[cid]
                assert execution['runtime_provenance']['research_protocol_sha256']==pdigest
                assert sha(run/'config.json')==expected_config
                assert sha(run/'AUDIT.json')==original['audit_sha256']
                metrics=measure(run)
                assert metrics['model_sha256']==protocol['formal_model_sha256']
                assert metrics['trace_sha256']==original['trace_sha256']==audit['trace_sha256']
                assert metrics['native_metrics_sha256']==audit['metrics_sha256']
                assert sha(run/'execution_chain.npz')==audit['chain_sha256']
                for key in ('task_success','strict_success'):assert metrics[key]==audit[key]
                np.testing.assert_allclose([metrics[k] for k in ('rmse_mm','peak_torque_nm','peak_speed_mps')],
                    [audit[k] for k in ('rmse_mm','peak_torque_nm','peak_speed_mps')],rtol=1e-7,atol=1e-9)
                row=dict(condition_id=cid,run=str(run),audit_sha256=sha(run/'AUDIT.json'),
                    worst_pair=audit['worst_pair'],penetration_mm=audit['penetration_mm'],
                    edge_penetration_mm=audit['edge_penetration_mm'],metrics=metrics)
                write(out/(label+'_'+cid+'.json'),row);result.append(row)
            rows[label]=result
        paired=[]
        for old,new in zip(rows['initial'],rows['selected']):
            assert old['condition_id']==new['condition_id']
            paired.append(dict(condition_id=old['condition_id'],initial_strict=old['metrics']['strict_success'],
                selected_strict=new['metrics']['strict_success'],initial_task=old['metrics']['task_success'],
                selected_task=new['metrics']['task_success'],
                selected_minus_initial={k:new['metrics'][k]-old['metrics'][k]
                    for k in ('rmse_mm','peak_torque_nm','peak_speed_mps','placement_error_xy_mm')}))
        write(out/'INPUT_RECEIPTS.json',receipts)
        write(out/'SUMMARY.json',dict(role=a.role,protocol_sha256=pdigest,
            source_sha256=sha(source),metric_source_sha256=sha(metric_source),
            input_receipts_sha256=sha(out/'INPUT_RECEIPTS.json'),summaries={k:summarize(v) for k,v in rows.items()},
            paired=paired,qualification_rule_unchanged=True,
            limitations=['Public teacher training/validation diagnostic, not heldout performance or student success.',
                'All role identities retained; successful-only demonstration subset is explicit.',
                'Predeclared event windows and threshold0.05N; absent exposure is NA, not zero-force compliance.',
                'Same conditions but different executed contact paths: force differences do not identify intrinsic compliance.',
                'Metrics independently recomputed from saved substeps; no new physical integration or fitting.']))
        state.update(status='complete',summary_sha256=sha(out/'SUMMARY.json'),completed_runs=sum(len(v) for v in rows.values()))
    except BaseException as exc:state.update(status='failed_preserved',error=repr(exc));raise
    finally:
        state['ended_utc']=datetime.now(timezone.utc).isoformat();write(out/'execution.json',state)
    print(json.dumps(dict(status=state['status'],summary_sha256=state['summary_sha256'])))


if __name__=='__main__':main()
