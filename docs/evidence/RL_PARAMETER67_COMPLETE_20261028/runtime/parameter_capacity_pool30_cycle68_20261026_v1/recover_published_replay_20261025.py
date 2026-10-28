"""Recover audited nonterminal replay from the first interrupted CHEQ attempt.

This deliberately supports cycle zero with zero nominal actions only. It does
not recover optimizer state or claim bit-exact original raw actions: division
of recorded mixed float32 actions is verified by reconstruction. Terminal and
incomplete tails are excluded rather than inventing next observations/context.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from published_compliance_learner_20261025 import OBSERVATION_SCALE
from spt_rl_reward_20261025 import SPTReward


def recover(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    receipts = {}
    for method in ('direct', 'impedance', 'admittance', 'vmc'):
        groups, hashes = {}, {}

        def read_rows(path):
            raw = path.read_bytes()
            hashes[str(path.relative_to(source))] = hashlib.sha256(raw).hexdigest()
            return [json.loads(line) for line in raw.splitlines()]

        for row in read_rows(source/method/'transitions.jsonl'):
            if row['cycle'] != 0:
                raise ValueError('Recovery supports only the first interrupted cycle')
            groups.setdefault(row['condition'], []).append(row)
        rows, max_reward_error, max_action_error = [], 0., 0.
        for condition, transitions in groups.items():
            actions = read_rows(source/method/'cycle_00000'/condition/'actor_intervals.jsonl')
            reward = SPTReward()
            for index in range(min(len(actions)-1, len(transitions)-1)):
                current, following = actions[index:index+2]
                transition, next_transition = transitions[index:index+2]
                if transition['done']:
                    raise ValueError('Terminal recovery requires a separate explicit protocol')
                value, _ = reward(current_potential=current['payload_potential'],
                    next_potential=following['payload_potential'], interval=following['interval'],
                    terminated=False, task_success=False, strict_success=False)
                error = abs(value-transition['reward'])
                if not np.isfinite(error) or error > 1e-10:
                    raise ValueError('Reward cannot be reconstructed from physical telemetry')
                max_reward_error = max(max_reward_error, error)
                weight, next_weight = float(transition['context']), float(next_transition['context'])
                if not .2 <= weight <= 1 or not .2 <= next_weight <= 1:
                    raise ValueError('Unsupported recorded CHEQ mixing weight')
                mixed = np.asarray(current['action'], np.float32)
                raw_action = mixed/np.float32(weight)
                action_error = float(np.max(abs(raw_action*np.float32(weight)-mixed)))
                if not np.isfinite(raw_action).all() or np.max(abs(raw_action)) > 1.000001 or action_error > 1e-7:
                    raise ValueError('Cannot reconstruct bounded raw action from zero-nominal mixing')
                max_action_error = max(max_action_error, action_error)
                row = dict(observations=np.r_[np.asarray(current['observation'], np.float32)/OBSERVATION_SCALE, weight],
                    next_observations=np.r_[np.asarray(following['observation'], np.float32)/OBSERVATION_SCALE, next_weight],
                    actions=raw_action, rewards=[value], dones=[0.])
                if not all(np.isfinite(v).all() for v in row.values()):
                    raise ValueError('Nonfinite recovered transition')
                rows.append(row)
        if not rows:
            raise ValueError('No complete recoverable transitions for '+method)
        path = output/(method+'.npz')
        np.savez_compressed(path, **{key: np.asarray([row[key] for row in rows], np.float32) for key in rows[0]})
        receipts[method] = dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            transitions=len(rows), source_failed_attempt=str(source/method), source_sha256=hashes,
            reward_reduction_max_abs_error=max_reward_error,
            recovered_mixing_action_float32_max_abs_error=max_action_error,
            optimizer_recovered=False, recovery='completed nonterminal pairs; raw actions reconstructed with float32 rounding; incomplete tails excluded')
    (output/'RECOVERY.json').write_text(json.dumps(receipts, indent=2)+'\n')
    return receipts


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    result = recover(arguments.source, arguments.output)
    print(json.dumps({method: record['transitions'] for method, record in result.items()}))
