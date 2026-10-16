"""Prospective training-only screen; never substitutes for final acceptance.

Follow exact stage lineage, count only each segment's own closed rows, preserve
failed/early/incomplete rows, and never mix reward/config treatments or methods.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics


def read_bound(path):
    data = Path(path).read_bytes()
    return json.loads(data), hashlib.sha256(data).hexdigest()


def screen(rows, conditions, criteria):
    expected = set(conditions)
    window = criteria['window_episodes']
    assert len(expected) == len(conditions) == window
    assert criteria['minimum_completed_episodes'] >= 2*window
    seen = set()
    last_episode = last_step = None
    pending = []
    closed = []
    for row in rows:
        episode = row['episode']
        assert episode not in seen, 'Duplicate episode would double-count exposure'
        seen.add(episode)
        if last_episode is not None:
            assert episode == last_episode+1, 'Missing or unordered episode'
            assert row['step_before'] == last_step, 'Missing or duplicated transition interval'
        assert row['condition_id'] in expected
        assert not pending, 'An unfinished episode cannot be silently skipped'
        if 'ended_utc' not in row:
            pending.append(row)
        else:
            assert math.isfinite(row['return_value'])
            assert row['steps'] > 0 and row['step_after']-row['step_before'] == row['steps']
            for key in ('task_success','strict_success','physical_valid','full_task_horizon_completed'):
                assert type(row['result'][key]) is bool, f'Missing or non-boolean {key}'
            closed.append(row)
            last_step = row['step_after']
        last_episode = episode
    def summarize(group):
        returns = [r['return_value'] for r in group]
        return dict(count=len(group),
            episode_ids=[r['episode'] for r in group],
            return_mean=statistics.fmean(returns) if returns else None,
            return_std=statistics.pstdev(returns) if returns else None,
            task=sum(r['result']['task_success'] for r in group),
            strict=sum(r['result']['strict_success'] for r in group),
            joint=sum(r['result']['task_success'] and r['result']['strict_success'] for r in group),
            physical_valid=sum(r['result']['physical_valid'] for r in group),
            full_horizon=sum(r['result']['full_task_horizon_completed'] for r in group),
            conditions=sorted({r['condition_id'] for r in group}))
    result = dict(closed=summarize(closed),incomplete_episodes=[r['episode'] for r in pending],
        training_candidate=False,acceptance=False,goal_complete=False,reasons=[])
    if len(closed) < criteria['minimum_completed_episodes']:
        result['reasons'].append('insufficient_completed_episodes')
    if len(closed) < 2*window:
        result['reasons'].append('insufficient_two_full_windows')
        return result
    previous = summarize(closed[-2*window:-window])
    latest = summarize(closed[-window:])
    # Definitions fixed in code before a qualifying sample exists. Absolute mean
    # handles negative returns. epsilon only prevents division by zero.
    drift = abs(latest['return_mean']-previous['return_mean'])/max(abs(previous['return_mean']),1e-12)
    cv = latest['return_std']/max(abs(latest['return_mean']),1e-12)
    result.update(previous_window=previous,latest_window=latest,relative_mean_drift=drift,return_cv=cv)
    for name,group in (('previous',previous),('latest',latest)):
        if set(group['conditions']) != expected:
            result['reasons'].append(name+'_condition_coverage_incomplete')
        if group['joint']/window < criteria['required_task_and_strict_rate_each_last_window']:
            result['reasons'].append(name+'_joint_task_strict_rate_low')
    if drift > criteria['adjacent_window_relative_mean_change_max']:
        result['reasons'].append('return_mean_not_stable')
    if cv > criteria['last_window_return_cv_max']:
        result['reasons'].append('return_variation_too_large')
    result['training_candidate'] = not result['reasons']
    return result


def collect(root):
    stages = []
    visited = set()
    cursor = root
    expected_reg = expected_execution = None
    while True:
        assert cursor not in visited, 'Stage lineage cycle'
        visited.add(cursor)
        reg,reg_hash = read_bound(cursor/'REGISTRATION.json')
        assert reg['schema'] == 'sii-rl-persistent-goal-stage-v1'
        assert Path(reg['run_root']) == cursor
        if expected_reg:
            assert reg_hash == expected_reg, 'Parent registration changed'
            parent_state,parent_hash = read_bound(cursor/'execution.json')
            assert parent_hash == expected_execution and parent_state['status'] == 'finite_stage_complete'
        stages.append((reg,reg_hash))
        previous = reg.get('previous_stage')
        if not previous:
            break
        cursor = Path(previous['root']).resolve()
        expected_reg = previous['registration_sha256']
        expected_execution = previous['execution_sha256']
    stages.reverse()
    criteria = stages[-1][0]['training_convergence']
    methods = {}
    for stage_index,(reg,reg_hash) in enumerate(stages):
        assert reg['training_convergence'] == criteria, 'Do not mix convergence criteria'
        assert {j['controller'] for j in reg['jobs']} == {None,'impedance','admittance','vmc'}
        assert len(reg['jobs']) == 4
        for job in reg['jobs']:
            entry = methods.setdefault(job['name'],dict(rows=[],evidence=[],fingerprint=None,
                conditions=None,reported_status='not_started',cumulative_steps=job['inherited_steps']))
            output = Path(job['output'])
            if not (output/'execution.json').exists():
                assert stage_index == len(stages)-1, 'Completed parent method evidence is missing'
                continue
            execution,execution_hash = read_bound(output/'execution.json')
            spec,spec_hash = read_bound(output/'PROTOCOL.json')
            assert spec['goal_registration_sha256'] == reg_hash
            assert spec['controller'] == job['controller'] and spec['seed'] == job['seed']
            fingerprint = {key:spec[key] for key in ('protocol_sha256','seed','controller','agent_config',
                'reward','reward_variant','utd','prior_file_sha256','training_conditions')}
            fingerprint['tracking_guidance'] = spec.get('tracking_guidance')
            if entry['fingerprint'] is not None:
                assert entry['fingerprint'] == fingerprint, 'Do not pool different training treatments'
                assert execution['resumed_from']['inherited_steps'] == entry['cumulative_steps']
                assert execution['resumed_from']['parent_execution_sha256'] == entry['evidence'][-1]['execution_sha256']
            entry['fingerprint'] = fingerprint
            entry['conditions'] = spec['training_conditions']
            rows = execution['rows']
            if rows:
                assert rows[0]['step_before'] == job['inherited_steps']
            entry['rows'].extend(rows)
            entry.update(reported_status=execution['status'],cumulative_steps=execution['steps'])
            entry['evidence'].append(dict(execution_path=str(output/'execution.json'),execution_sha256=execution_hash,
                protocol_sha256=spec_hash,registration_sha256=reg_hash,
                execution_snapshot=execution,protocol_snapshot=spec))
    assert len(methods) == 4, 'Method names changed across stages'
    for entry in methods.values():
        entry['screen'] = screen(entry['rows'],entry['conditions'],criteria) if entry['conditions'] else dict(
            training_candidate=False,reasons=['not_started'],acceptance=False,goal_complete=False)
        # The full snapshots above preserve every failure and incomplete row;
        # inherited historical n1 episodes are deliberately not added.
        entry.pop('rows')
        entry.pop('fingerprint')
    return dict(criteria=criteria,methods=methods,stage_roots=[r['run_root'] for r,_ in stages],
        all_training_candidates=all(m['screen']['training_candidate'] for m in methods.values()),
        acceptance_performed=False,goal_complete=False,
        interpretation='Training-only prospective screen, not final acceptance or a causal treatment comparison. Count this n25 lineage only; all early/failed closed rows remain in denominators. Incomplete episodes remain explicit. Service liveness is checked separately. Final physical/replay/checkpoint audits remain required.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists(), 'Do not overwrite prior evidence'
    result=dict(status='running',observed_utc=datetime.now(timezone.utc).isoformat(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    try:
        result.update(collect(args.root.resolve()),status='screened')
    except BaseException as exc:
        result.update(status='invalid_evidence',error=repr(exc),goal_complete=False)
        raise
    finally:
        with args.output.open('x') as output:
            json.dump(result,output,indent=2,ensure_ascii=False,allow_nan=False)
            output.write('\n')
    print(json.dumps({name:entry['screen'] for name,entry in result['methods'].items()},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
