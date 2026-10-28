"""Replay ALL closed SPT-surrogate transitions, including the first reward.

This verifies the recorded interval-to-reward chain, not independent physics,
actor/filter replay, or task success. Run using the campaign source snapshot.
"""
import argparse
import json
from pathlib import Path
import math
from prepare_rl_spt_campaign_20261025 import read, sha
from spt_rl_reward_20261025 import SPTReward, validate_config


def audit(segment):
    spec=read(segment/'PROTOCOL.json');state=read(segment/'execution.json')
    validate_config(spec['spt_reward_spec'])
    if state['status']!='complete':
        raise ValueError('Segment must be closed; partial/failed receipts remain preserved')
    sources=spec['source_sha256']
    reward_path=Path(__file__).with_name('spt_rl_reward_20261025.py').resolve()
    if sources[str(reward_path)]!=sha(reward_path):
        raise ValueError('Run audit from matching frozen source')
    with (segment/'training.jsonl').open() as stream:
        return audit_rows(segment, spec, state, stream)


def audit_rows(segment, spec, state, stream):
    checked=0;returns=[]
    for row in state['rows']:
        run=Path(row['run'])
        entries=[json.loads(next(stream)) for _ in range(row['steps'])]
        if any(e['episode']!=row['episode'] for e in entries):
            raise ValueError('Episode ordering mismatch')
        intervals=read(run/'RL_INTERVALS.json')
        if intervals[0] is not None or len(intervals)!=len(entries)+1 or len(entries)!=row['steps']:
            raise ValueError('Missing/extra intervals')
        reducer=SPTReward(spec['spt_reward_spec'])
        phi=read(run/'RL_REWARD_METADATA.json')['initial_payload_potential'];total=0.
        if phi!=row['initial_payload_potential']:
            raise ValueError('Initial potential mismatch')
        for i,(iv,entry) in enumerate(zip(intervals[1:],entries,strict=True)):
            if entry['step']!=row['step_before']+i+1 or entry['terms']['interval']!=iv:
                raise ValueError('Transition order/telemetry mismatch')
            done=i==len(entries)-1
            value,terms=reducer(current_potential=phi,next_potential=iv['payload_potential'],
                interval=iv,terminated=done,task_success=bool(done and row['result']['task_success']),
                strict_success=bool(done and row['result']['strict_success']),
                failure_reason=row['result'].get('abort_reason') if done else None)
            for key,v in terms.items():
                saved=entry['terms'][key]
                if isinstance(v,float):
                    if not math.isclose(v,saved,rel_tol=1e-12,abs_tol=1e-12):
                        raise ValueError('Reward mismatch: '+key)
                elif v!=saved:raise ValueError('Reward metadata mismatch: '+key)
            total+=value;phi=iv['payload_potential'];checked+=1
        if not math.isclose(total,row['return_value'],rel_tol=1e-12,abs_tol=1e-12):
            raise ValueError('Episode return mismatch')
        returns.append(dict(episode=row['episode'],reward=total,steps=row['steps'],
                            intervals_sha256=sha(run/'RL_INTERVALS.json')))
    if next(stream, None) is not None:
        raise ValueError('Unexpected extra transition logs')
    return dict(status='recorded_reward_replay_passed',transitions=checked,episodes=returns,
                first_rewards_included=True,independent_physics_audit=False,
                actor_filter_replay=False,formal_spt_computed=False,
                protocol_sha256=sha(segment/'PROTOCOL.json'),execution_sha256=sha(segment/'execution.json'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--segment',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    # Exclusive creation preserves prior audits; failures get explicit receipts too.
    with a.output.open('x') as stream:
        try:
            result=audit(a.segment)
        except Exception as exc:
            json.dump(dict(status='failed_preserved',error=repr(exc)),stream,indent=2)
            raise
        json.dump(result,stream,indent=2,allow_nan=False)
    print(json.dumps(dict(status=result['status'],transitions=result['transitions'])))


if __name__=='__main__':main()
