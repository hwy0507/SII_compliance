"""Eight preregistered, sequential pure MLP/RNN fits and frozen-world episodes."""
import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from optimize_tool_contact_20261002 import ROOT, sha, write, now


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--recover-asset-setup', type=Path,
                   help='Retain a pre-physics missing-assets failure and reuse its verified first trained model')
    a = p.parse_args()
    with (ROOT/'outputs/tool_teacher_four_hour_20261002.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = a.output.resolve()
        run.mkdir(parents=True, exist_ok=False)
        assets = ROOT/'outputs/canonical_rl_assets_20260923/menagerie'
        if not assets.is_dir():
            raise FileNotFoundError(assets)
        os.environ['MUJOCO_MENAGERIE_PATH'] = str(assets)
        recovered_training = None
        if a.recover_asset_setup:
            old = a.recover_asset_setup.resolve()
            old_state = json.loads((old/'execution.json').read_text())
            failure = old/'evaluations/original_mlp_2026100201'
            failure_state = json.loads((failure/'execution.json').read_text())
            assert old_state['status'] == 'failed_preserved' and len(old_state['rows']) == 1
            assert 'MuJoCo Menagerie not found' in failure_state['error']
            assert not (failure/'rollout.mjb').exists() and not (failure/'rollout.npz').exists()
            shutil.copytree(old, run/'setup_failures/attempt1', ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            recovered_training = old/'train_original_mlp_2026100201'
        runtime = run/'evaluations/source'
        runtime.mkdir(parents=True)
        for name in ('scripts', 'assets'):
            shutil.copytree(ROOT/name, runtime/name,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs'))
        (runtime/'tools').mkdir()
        for name in ('optimize_tool_contact_20261002.py', 'train_office_mlp_rnn_20261002.py',
                     'run_office_mlp_rnn_20261002.py'):
            shutil.copy2(ROOT/'tools'/name, runtime/'tools'/name)
        shutil.copy2(ROOT/'docs/MLP_RNN_REPLACEMENT_PROTOCOL_20261002.md', run/'protocol.md')
        reference = run/'reference.json'
        shutil.copy2(ROOT/'outputs/tool_contact_20261002/v5_esn_full/esn_combined_v4.json', reference)
        config = run/'student_config.json'
        write(config, {})
        for dataset, directory in [('original', 'esn_original_system_id_v2'), ('recovery41', 'esn_integral41')]:
            dest = run/'data'/dataset
            dest.mkdir(parents=True)
            for name in ('training_data.npz', 'TRAINING_COMPLETE.json'):
                shutil.copy2(ROOT/'outputs/tool_teacher_four_hour_20261002'/directory/name, dest/name)
            assert sha(dest/'training_data.npz') == json.loads((dest/'TRAINING_COMPLETE.json').read_text())['training_data_sha256']
        state = dict(status='running', started_utc=now(), protocol_sha256=sha(run/'protocol.md'),
                     argv=sys.argv, runner_sha256=sha(Path(__file__)), menagerie_path=str(assets),
                     retained_setup_failure=str(a.recover_asset_setup) if a.recover_asset_setup else None,
                     authorization='New user request to replace ESN with MLP/RNN; eight models, eight episodes; not extension of previous expired budget',
                     source={str(f.relative_to(runtime)): sha(f) for f in runtime.rglob('*') if f.is_file()}, rows=[])
        write(run/'execution.json', state)
        try:
            for dataset in ('original', 'recovery41'):
                for seed in (2026100201, 2026100202):
                    for kind in ('mlp', 'rnn'):
                        name = f'{dataset}_{kind}_{seed}'
                        training = run/('train_'+name)
                        evaluation = run/'evaluations'/name
                        data = run/'data'/dataset
                        train_cmd = [sys.executable, str(runtime/'tools/train_office_mlp_rnn_20261002.py'),
                                     '--data', str(data/'training_data.npz'), '--metadata', str(data/'TRAINING_COMPLETE.json'),
                                     '--kind', kind, '--seed', str(seed), '--output', str(training), '--updates', '2400']
                        eval_cmd = [sys.executable, str(runtime/'tools/optimize_tool_contact_20261002.py'),
                                    '--reference', str(reference), '--config', str(config), '--output', str(evaluation),
                                    '--checkpoint', str(training/'checkpoint.npz'), '--contact-audit']
                        row = dict(name=name, dataset=dataset, kind=kind, seed=seed, started_utc=now(),
                                   training_command=train_cmd, evaluation_command=eval_cmd)
                        state['rows'].append(row)
                        write(run/'execution.json', state)
                        for stage, command in [('training', train_cmd), ('evaluation', eval_cmd)]:
                            if stage == 'training' and recovered_training and name == 'original_mlp_2026100201':
                                receipt = json.loads((recovered_training/'TRAINING_COMPLETE.json').read_text())
                                assert receipt['kind'] == kind and receipt['seed'] == seed and receipt['updates'] == 2400
                                assert receipt['data_sha256'] == sha(data/'training_data.npz')
                                assert receipt['checkpoint_sha256'] == sha(recovered_training/'checkpoint.npz')
                                shutil.copytree(recovered_training, training)
                                row.update(training_reused_from=str(recovered_training), training_returncode=0,
                                           training_command_executed_here=False)
                                continue
                            with (run/(name+'_'+stage+'.log')).open('x') as log:
                                result = subprocess.run(command, cwd=runtime, stdout=log, stderr=subprocess.STDOUT)
                            row[stage+'_returncode'] = result.returncode
                            write(run/'execution.json', state)
                            if result.returncode:
                                raise RuntimeError(f'{name} {stage} failed; retained without retry')
                        row.update(ended_utc=now(), audit=json.loads((evaluation/'AUDIT.json').read_text()))
                        write(run/'execution.json', state)
                        print(json.dumps(dict(name=name, audit=row['audit'])), flush=True)
            state['status'] = 'complete'
        except BaseException as exc:
            state.update(status='failed_preserved', error=repr(exc))
            raise
        finally:
            state['ended_utc'] = now()
            write(run/'execution.json', state)


if __name__ == '__main__':
    main()
