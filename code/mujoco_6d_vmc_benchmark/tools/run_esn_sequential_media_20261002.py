"""One fixed-checkpoint sequential-r12 rollout, audit and full-speed replay."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import mujoco
import validate_office_apparatus_v5_20260917 as evaluator
from audit_temporal_narrow_screen_20261001 import audit


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run = args.output.resolve()
    run.mkdir(parents=True, exist_ok=False)
    reference = ROOT / 'outputs/temporal_s52_latent_dropout_20261001_v1/p010_eval'
    config_path = ROOT / 'configs/office_combined_v4_sequential_r12_20261002.json'
    config = json.loads(config_path.read_text())
    original = json.loads((reference / 'esn_combined_v4.json').read_text())
    checkpoint = reference / 'esn_temporal.npz'
    assert sha(checkpoint) == '9f4b5a8168142595873ff1c8fdcaa3b2186b7a1d1edab916d2bbd38fe5988023'
    assert mujoco.__version__ == config['runtime']['mujoco']
    cgroup = Path('/sys/fs/cgroup') / Path('/proc/self/cgroup').read_text().strip().split('::', 1)[1].lstrip('/')
    memory = (cgroup / 'memory.max').read_text().strip()
    assert memory != 'max' and int(memory) <= 3 * 1024**3
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        assert os.environ.get(name) == '1'
    for name, digest in original['source_sha256'].items():
        if name != Path(evaluator.__file__).name:
            assert sha(ROOT / 'scripts' / name) == digest, name
    shutil.copy2(checkpoint, run / 'esn_temporal.npz')
    shutil.copy2(reference / 'TRAINING_COMPLETE.json', run / 'TRAINING_COMPLETE.json')
    shutil.copy2(config_path, run / config_path.name)
    shutil.copy2(__file__, run / Path(__file__).name)
    a = dict(original['arguments'], output=run / 'esn_combined_v4',
             esn_model=run / 'esn_temporal.npz', rod_start=12.,
             interaction_schedule='sequential-r12-v1')
    assert a['physics_probe_s'] is None and a['duration'] == 55. and a['dt'] == .0001
    record = dict(status='running', started_utc=now(), host=socket.gethostname(),
                  python=sys.executable, mujoco=mujoco.__version__, memory_max=memory,
                  threads=1, argv=sys.argv, scene_id=config['scene_id'], training_performed=False,
                  reused_training_record=str(reference / 'TRAINING_COMPLETE.json'),
                  checkpoint_sha256=sha(checkpoint), config_sha256=sha(config_path),
                  source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  wrapper_sha256=sha(__file__),
                  source_sha256={name: sha(ROOT / 'scripts' / name) for name in original['source_sha256']},
                  arguments={k: str(v) if isinstance(v, Path) else v for k, v in a.items()})
    state = run / 'execution.json'
    state.write_text(json.dumps(record, indent=2))
    save_model = mujoco.mj_saveModel

    def checked_save(model, filename, buffer):
        result = save_model(model, filename, buffer)
        assert sha(filename) == config['development_mjb_sha256'], 'Frozen geometry mismatch'
        return result

    mujoco.mj_saveModel = checked_save
    try:
        with (run / 'esn.log').open('w') as log, contextlib.redirect_stdout(log):
            evaluator.run(SimpleNamespace(**a))
        result = audit(run, 'esn')
        (run / 'AUDIT.json').write_text(json.dumps(result, indent=2))
        record.update(status='rendering', audit=result)
        state.write_text(json.dumps(record, indent=2))
        command = [sys.executable, str(ROOT / 'tools/render_office_threeview_20260929.py'),
                   '--rollout', str(run / 'esn_combined_v4'), '--output', str(run / 'media'),
                   '--label', 'Pure ESN | rod starts 12s | full replay 1x | development',
                   '--stride', '1', '--fps', '25', '--gif-stride', '5']
        record['render_command'] = command
        with (run / 'render.log').open('w') as log:
            subprocess.run(command, check=True, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        assert sha(checkpoint) == sha(run / 'esn_temporal.npz') == record['checkpoint_sha256']
        record.update(status='complete', media_manifest_sha256=sha(run / 'media/manifest.json'))
    except BaseException as exc:
        record.update(status='failed', error=repr(exc))
        raise
    finally:
        mujoco.mj_saveModel = save_model
        record['ended_utc'] = now()
        state.write_text(json.dumps(record, indent=2))
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
