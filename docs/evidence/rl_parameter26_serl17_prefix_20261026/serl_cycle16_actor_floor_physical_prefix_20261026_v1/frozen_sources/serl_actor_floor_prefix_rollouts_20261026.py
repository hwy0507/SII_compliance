"""Fixed short physical prefixes from an in-memory, frozen auxiliary learner."""
from pathlib import Path
import hashlib
import json
import os
import selectors
import subprocess
import time


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def run_prefixes(learner, registration, output, arm):
    import numpy as np
    from evaluate_serl_seeded_multistep_20261026 import seeded_action, case_action_seed
    from validate_serl_state_20261026 import digest
    reg = registration
    protocol = json.loads(Path(reg['training_registration']['path']).read_text())
    assert reg['prefix_seconds'] == 2.56 and reg['actions_per_trial'] == 64
    assert reg['seeds_per_condition'] == 8 and reg['physics_cpus'] == [53, 54]
    assert reg['action_seed_start'] == 2026102623
    conditions = {c['id']: c for c in protocol['conditions']}
    assert len(set(reg['case_ids'])) == 3
    tasks = [(case, i) for case in reg['case_ids'] for i in range(8)]
    before = digest(learner.state_dict())
    env = dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1', MUJOCO_GL='disable')
    rows = []
    arm_root = output/arm
    arm_root.mkdir()
    # Two separate frozen MuJoCo interpreters, each pinned to one spare CPU.
    for offset in range(0, len(tasks), 2):
        selector = selectors.DefaultSelector()
        active = {}
        for cpu, (case, seed_index) in zip(reg['physics_cpus'], tasks[offset:offset+2]):
            condition = conditions[case]
            assert sha(condition['path']) == condition['sha256']
            seed = case_action_seed(reg['action_seed_start']+seed_index, case)
            folder = arm_root/f'{case}_seed{seed_index:02d}'
            command = ['taskset', '-c', str(cpu), reg['sampler_python'], reg['episode_adapter'],
                '--runtime', protocol['runtime'], '--output', str(folder), '--fixture', condition['path'],
                '--reference-plan', protocol['reference_plan'], '--controller', 'direct', '--ipc',
                '--probe-seconds', '2.56']
            log = (arm_root/(folder.name+'.stderr.log')).open('x')
            child = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=log, text=True, bufsize=1, env=env)
            item = dict(child=child, log=log, folder=folder, case=case, seed_index=seed_index,
                condition=condition, seed=seed, key=learner.jax.random.PRNGKey(seed), actions=0)
            active[child.pid] = item
            selector.register(child.stdout, selectors.EVENT_READ, item)
            (arm_root/(folder.name+'_LAUNCH.json')).write_text(json.dumps(dict(
                pid=child.pid, time=time.time(), command=command, seed=seed))+'\n')
        try:
            while active:
                events = selector.select(timeout=300)
                if not events:
                    raise TimeoutError('Original prefix child silent for300s; no repeat')
                for selected, _ in events:
                    item = selected.data
                    child = item['child']
                    line = child.stdout.readline()
                    if not line:
                        raise RuntimeError('Prefix child exited before terminal')
                    event = json.loads(line)
                    if event['kind'] == 'error':
                        raise RuntimeError(event['error'])
                    if event['kind'] == 'observation':
                        index = item['actions']
                        assert index < 64
                        if index == 0:
                            assert sha(item['folder']/'rollout.mjb') == item['condition']['model_sha256']
                        action, item['key'] = seeded_action(learner, event['observation'], index, item['key'])
                        child.stdin.write(json.dumps(dict(action=action.tolist()))+'\n')
                        child.stdin.flush()
                        item['actions'] += 1
                    elif event['kind'] == 'terminal':
                        assert child.wait(timeout=60) == 0
                        assert event['model_sha256'] == item['condition']['model_sha256']
                        assert not event['result']['full_task_horizon_completed']
                        journal = [json.loads(v) for v in (item['folder']/'actor_intervals.jsonl').read_text().splitlines()]
                        assert len(journal) == item['actions'] and 0 < len(journal) <= 64
                        # Replay actions before discarding this auxiliary learner.
                        key = learner.jax.random.PRNGKey(item['seed'])
                        for index, entry in enumerate(journal):
                            action, key = seeded_action(learner, entry['observation'], index, key)
                            np.testing.assert_array_equal(action, np.asarray(entry['action']))
                            np.testing.assert_array_equal(action, np.asarray(entry['executed_action']))
                        assert np.array_equal(np.asarray(key), np.asarray(item['key']))
                        record = dict(arm=arm, case=item['case'], seed_index=item['seed_index'],
                            seed=item['seed'], folder=str(item['folder']), actions=item['actions'],
                            first_observation=journal[0]['observation'], terminal=event,
                            action_replay_exact=True, journal_sha256=sha(item['folder']/'actor_intervals.jsonl'),
                            left_initial_approach=event['result']['final_task_stage'] != 'approach')
                        rows.append(record)
                        selector.unregister(child.stdout)
                        child.stdin.close()
                        child.stdout.close()
                        item['log'].close()
                        del active[child.pid]
                    else:
                        raise ValueError('Unknown prefix IPC event')
            (output/(arm+'_PREFIX_PROGRESS.json')).write_text(json.dumps(dict(episodes=rows), indent=2)+'\n')
            print(arm, 'physical prefixes', len(rows), 'left approach', sum(r['left_initial_approach'] for r in rows), flush=True)
        finally:
            for item in active.values():
                child = item['child']
                child.stdin.close()
                try:
                    child.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    child.terminate()
                    child.wait(timeout=20)
                item['log'].close()
            selector.close()
    assert len(rows) == 24 and digest(learner.state_dict()) == before
    return dict(episodes=rows, frozen_learner_digest_before=before,
        frozen_learner_digest_after=digest(learner.state_dict()), learner_optimizer_rng_unchanged=True,
        replay_writes=0, weights_saved=False, maximum_physical_substeps=1228800)
