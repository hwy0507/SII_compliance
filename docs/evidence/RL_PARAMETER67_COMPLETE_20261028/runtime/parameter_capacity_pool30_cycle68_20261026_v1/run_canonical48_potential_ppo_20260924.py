"""Independent reward experiment reusing the frozen 48D PPO training workflow."""
import hashlib
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from canonical48_potential_reward_20260924 import environment_class, protocol


def main():
    source = ROOT/'tools/run_canonical48_ppo_20260923.py'
    spec = importlib.util.spec_from_file_location('potential_ppo_base_workflow',source)
    workflow = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(workflow)
    workflow.Canonical48Env = environment_class(workflow.Canonical48Env)
    original_save = workflow.save_json
    def save_json(path, value):
        if Path(path).name == 'manifest.json':
            value = dict(value, reward=protocol(),
                scope='Independent PPO8192 development-gate potential-reward experiment; not replacement of dense-reward results',
                experiment_entrypoint_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                base_workflow_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        elif Path(path).name == 'COMPLETE.json':
            value = dict(value, reward_version='push4_gate_potential_v1')
        original_save(path,value)
    workflow.save_json = save_json
    workflow.main()


if __name__ == '__main__':
    main()
