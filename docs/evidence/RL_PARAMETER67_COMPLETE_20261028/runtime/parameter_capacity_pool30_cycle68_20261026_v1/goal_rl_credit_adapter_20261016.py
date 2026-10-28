"""Explicit n-step-only checkpoint migration; retain raw one-step replay."""
import json
from pathlib import Path
from multistep_official_adapter_20261009 import make_adapter


def check_credit_migration(saved, current):
    if saved.get('n_step') != 1 or current.get('n_step') != 25:
        raise ValueError('Only registered 1 -> 25 credit-horizon migration is allowed')
    if {k: v for k, v in saved.items() if k != 'n_step'} != {
            k: v for k, v in current.items() if k != 'n_step'}:
        raise ValueError('Migration may not change any other agent configuration')


def migrated_replay_metadata(metadata, step, gamma):
    if 'n_step' in metadata:
        raise ValueError('Expected original raw one-step replay metadata')
    if metadata['count'] != step or step <= 0:
        raise ValueError('Replay count mismatch')
    # MultiStepReplay.restore verifies that the actual last raw transition is
    # terminal and that no truncation occurred. Raw rewards remain unchanged.
    return dict(metadata, n_step=25, gamma=gamma, last_terminal=step - 1)


def make_goal_adapter(base_path, migration_checkpoint):
    base = make_adapter(base_path, n_step=25)
    allowed = Path(migration_checkpoint).resolve()

    class GoalAgent(base):
        def load(self, path):
            saved = json.loads((Path(path) / 'official_agent_state.json').read_text())
            if saved['config'] == self.config:
                return super().load(path)
            if Path(path).resolve() != allowed:
                raise ValueError('Checkpoint migration was not registered for this path')
            check_credit_migration(saved['config'], self.config)
            current = self.config
            # The network/optimizer architecture is identical. Temporarily
            # present the saved config to the strict loader, without changing
            # the actual upstream critic's newly constructed n_step=25 config.
            self.config = saved['config']
            try:
                super().load(path)
            finally:
                self.config = current
            assert self.raw_agent._cfg.n_step == self.config['n_step'] == 25
    return GoalAgent
