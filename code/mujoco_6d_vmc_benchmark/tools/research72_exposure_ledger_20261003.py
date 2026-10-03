"""Snapshot declared public research costs; never traverses sealed conditions.

Running files are atomic snapshots, not a completed-stage receipt. Cumulative RL
segment counters are not added together. Every attempted episode stays visible.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path


def read(path):return json.loads(path.read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def seconds(row):
    if not row.get('ended_utc') or not row.get('started_utc'):return None
    return (datetime.fromisoformat(row['ended_utc'])-datetime.fromisoformat(row['started_utc'])).total_seconds()


def learning(path):
    if not (path/'execution.json').exists():return dict(path=str(path),status='not_started')
    state=read(path/'execution.json');spec=read(path/'SPECIFICATION.json');rows=[]
    jobs={j['name']:j for j in spec['jobs']}
    for row in state['rows']:
        job=jobs[row['name']]
        item=dict(name=row['name'],family=job['family'],seed=job['seed'],wall_seconds=seconds(row),
                  completed=row.get('returncode')==0,returncode=row.get('returncode'))
        if row.get('training_metadata_sha256'):
            metadata=path/row['name']/'TRAINING_COMPLETE.json'
            assert sha(metadata)==row['training_metadata_sha256']
            m=read(metadata)
            assert sha(path/row['name']/'checkpoint.npz')==row['checkpoint_sha256']==m['checkpoint_sha256']
            item.update(metadata_sha256=sha(metadata),checkpoint_sha256=row['checkpoint_sha256'],
                ridge_candidates=len(m.get('candidates',[])),gradient_updates=m.get('updates',0),
                selected_update=m.get('selected_update'),nonpadding_optimizer_observations=m.get('actual_nonpadding_observations'),
                trainable_parameters=m.get('trainable_parameters',m.get('trainable_readout_coefficients')),
                parent_checkpoint_sha256=m.get('parent_checkpoint_sha256'),
                training_data_sha256=m.get('training_data_sha256',m.get('data_sha256')))
        rows.append(item)
    return dict(path=str(path),status=state['status'],specification_sha256=sha(path/'SPECIFICATION.json'),
                registered_models=len(spec['jobs']),rows=rows,
                totals=dict(completed_models=sum(x['completed'] for x in rows),
                    gradient_updates=sum(x.get('gradient_updates',0) for x in rows),
                    ridge_candidates=sum(x.get('ridge_candidates',0) for x in rows),
                    wall_seconds_completed=sum(x['wall_seconds'] or 0 for x in rows if x['completed'])))


def physics(path):
    if not (path/'execution.json').exists():return dict(path=str(path),status='not_started')
    state=read(path/'execution.json');rows=[]
    for q in sorted(path.glob('queue_[0-3]/execution.json')):
        queue=read(q)
        for r in queue['rows']:
            run=q.parent/r['name']
            row=dict(run=str(run),name=r['name'],category=r.get('category','enhanced_teacher'),
                condition_id=r.get('condition_id',r['name']),role=r.get('role','development'),
                wall_seconds=seconds(r),returncode=r.get('returncode'),completed=False)
            if 'audit_sha256' in r:
                assert sha(run/'AUDIT.json')==r['audit_sha256']
                audit=read(run/'AUDIT.json');summary=read(run/'rollout.json')
                row.update(completed=True,task=bool(audit['task_success']),strict=bool(audit['strict_success']),
                    full_horizon=summary['full_task_horizon_completed'],abort_reason=summary['abort_reason'],
                    final_stage=summary['final_task_stage'],audit_sha256=r['audit_sha256'],trace_sha256=r['trace_sha256'])
            rows.append(row)
    totals=dict(attempted=len(rows),completed=sum(r['completed'] for r in rows),
                task=sum(r.get('task',False) for r in rows),strict=sum(r.get('strict',False) for r in rows),
                failed_task=sum(r['completed'] and not r['task'] for r in rows),
                failed_strict=sum(r['completed'] and not r['strict'] for r in rows),
                wall_seconds_completed=sum(r['wall_seconds'] or 0 for r in rows if r['completed']))
    return dict(path=str(path),status=state['status'],totals=totals,rows=rows)


def reinforcement(path):
    if not (path/'execution.json').exists():return dict(path=str(path),status='not_started')
    state=read(path/'execution.json');spec=read(path/'SPECIFICATION.json');rows=[]
    for q in sorted(path.glob('queue_[0-2]/execution.json')):
        for model in read(q)['rows']:
            segments=[]
            for segment in model['segments']:
                execution=q.parent/model['name']/segment['stage']/'execution.json'
                if not execution.exists():continue
                s=read(execution);inherited=s.get('resumed_from',{}).get('inherited_steps',0)
                assert s.get('new_segment_steps',s['steps']-inherited)==s['steps']-inherited
                segments.append(dict(stage=segment['stage'],status=s['status'],cumulative_steps=s['steps'],
                    inherited_steps=inherited,new_steps=s['steps']-inherited,updates=s['updates'],
                    cumulative_episodes=s['episodes'],attempted_new_episodes=len(s['rows']),
                    wall_seconds=seconds(s),execution=str(execution)))
            if segments:
                assert sum(s['new_steps'] for s in segments)==segments[-1]['cumulative_steps']
            rows.append(dict(name=model['name'],family=model['family'],seed=model['seed'],segments=segments,
                cumulative_steps=segments[-1]['cumulative_steps'] if segments else 0,
                cumulative_updates=segments[-1]['updates'] if segments else 0))
    return dict(path=str(path),status=state['status'],registered_models=len(spec['jobs']),rows=rows,
        totals=dict(completed_interaction_steps=sum(r['cumulative_steps'] for r in rows),
                    gradient_updates=sum(r['cumulative_updates'] for r in rows)),
        caveat='Steps count completed actor intervals. An interrupted in-flight interval may have additional physics; its attempted episode remains explicit. Not a substep audit.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();root=a.root.resolve()
    phases=('teacher_bank','controller_screen_v1','learning_development_v1','controller_confirmation_v1',
            'additional_development_v1/nominal_development','additional_development_v1/neural_lr_development',
            'context_gate_development_v1/development','teacher_refinement_v1/collection')
    result=dict(created_utc=datetime.now(timezone.utc).isoformat(),source_sha256=sha(Path(__file__)),
        protocol_sha256=sha(root/'PROTOCOL.json'),snapshot_only=True,sealed_contents_read=False,
        physics=[physics(root/x) for x in phases],
        learning=[learning(root/'local_learning_archive_v1/learning_v1'),
                  learning(root/'local_neural_refinement_archive_v1/neural_lr_refinement_v1'),
                  learning(root/'local_context_gate_archive_v1/context_gate_learning_v1')],
        rl=reinforcement(root/'rl_office_adaptation_v1'),
        accounting=['Do not equate fitted ridge candidates, gradient updates and simulator interactions.',
            'Teacher collection is shared by learned methods; charge all attempts, including failures.',
            'Validation/development physics is separate from demonstration and RL training exposure.',
            'Matched-network parent fit is shared lineage, not free training or duplicate physical data.',
            'Wall time is per-process elapsed time, not CPU time or summed calendar duration.',
            'No final evaluations or historical primitive training are included in this current-cohort snapshot.'])
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(output=str(a.output),sha256=sha(a.output),
        learning=[r.get('totals') for r in result['learning']],physics=[r.get('totals') for r in result['physics']],
        rl=result['rl'].get('totals'))))


if __name__=='__main__':main()
