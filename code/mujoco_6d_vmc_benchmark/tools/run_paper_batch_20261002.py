"""Frozen-source, sequential, deadline-bounded batches for the 12-hour study."""
import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from optimize_tool_contact_20261002 import ROOT, sha, write, now

AUTHORIZED_END = datetime(2026, 10, 3, 2, 11, 36, tzinfo=timezone.utc)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--v6-input', type=Path, required=True)
    p.add_argument('--parameter-source', type=Path)
    p.add_argument('--rl-bridge', type=Path)
    p.add_argument('--menagerie', type=Path, default=ROOT/'outputs/canonical_rl_assets_20260923/menagerie')
    p.add_argument('--dispatch-until', default='2026-10-02T22:11:36+00:00')
    p.add_argument('--start-index', type=int, default=0)
    p.add_argument('--count', type=int)
    p.add_argument('--physics-dt',type=float,default=.0001)
    p.add_argument('--condition-file',type=Path)
    p.add_argument('--condition-id')
    p.add_argument('--validation-lock',type=Path)
    a = p.parse_args()
    deadline = datetime.fromisoformat(a.dispatch_until)
    assert deadline.tzinfo is not None and deadline <= AUTHORIZED_END
    v6 = a.v6_input.resolve()
    reference = v6/'esn_original_v2/rollout.json'
    manifest = json.loads(a.manifest.read_text())
    assert len(manifest['candidates']) <= 48
    assert 0<=a.start_index<len(manifest['candidates']) and (a.count is None or a.count>0)
    candidates=manifest['candidates'][a.start_index:None if a.count is None else a.start_index+a.count]
    if a.condition_id is not None or a.physics_dt!=.0001:
        if a.validation_lock is None:raise ValueError('Freeze model list before heldout/formal evaluation')
        locked=json.loads(a.validation_lock.read_text())
        assert locked['status']=='models_frozen_before_final_evaluation'
        locked_candidates={c['name']:c for c in locked['candidates']}
        assert all(locked_candidates.get(c['name'])==c for c in candidates), 'Final model differs from lock'
    (ROOT/'outputs').mkdir(exist_ok=True)
    with (ROOT/'outputs/tool_teacher_four_hour_20261002.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        run = a.output.resolve(); run.mkdir(parents=True, exist_ok=False)
        runtime = run/'source'; runtime.mkdir()
        for folder in ('scripts', 'assets', 'tools'):
            shutil.copytree(ROOT/folder, runtime/folder,
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'outputs'))
        shutil.copy2(a.manifest, run/'manifest.json')
        os.environ['MUJOCO_MENAGERIE_PATH'] = str(a.menagerie.resolve())
        assert Path(os.environ['MUJOCO_MENAGERIE_PATH']).is_dir()
        state = dict(status='running', started_utc=now(), authorized_end=AUTHORIZED_END.isoformat(),
                     dispatch_until=deadline.isoformat(), manifest_sha256=sha(run/'manifest.json'), argv=sys.argv,
                     sources={str(f.relative_to(runtime)): sha(f) for f in runtime.rglob('*') if f.is_file()}, rows=[])
        state['selected_candidate_names']=[c['name'] for c in candidates]
        state['manifest_slice']=dict(start_index=a.start_index,count=len(candidates),total_registered=len(manifest['candidates']))
        state['validation_lock_sha256']=sha(a.validation_lock) if a.validation_lock else None
        write(run/'execution.json', state)
        try:
            for candidate in candidates:
                if (deadline-datetime.now(timezone.utc)).total_seconds() < 180:
                    state['status'] = 'deadline_no_new_dispatch'; break
                name = candidate['name']
                assert Path(name).name == name and name not in ('.', '..')
                config = run/(name+'.config.json'); write(config, candidate.get('config', {}))
                out = run/name
                script = ('paper_rl_worker_20261002.py' if candidate.get('rl_case') else
                          'paper_classical_worker_20261002.py' if candidate.get('controller')
                          else 'paper_office_worker_20261002.py')
                command = [sys.executable, str(runtime/'tools'/script),
                           '--v6-input', str(v6), '--reference', str(reference), '--config', str(config),
                           '--output', str(out), '--contact-audit']
                command += ['--physics-dt',str(a.physics_dt)]
                if a.condition_id is not None:
                    assert a.condition_file is not None
                    command += ['--condition-file',str(a.condition_file.resolve()),'--condition-id',a.condition_id]
                if candidate.get('controller'):
                    assert a.parameter_source is not None and not candidate.get('checkpoint')
                    command += ['--controller', candidate['controller'], '--parameter-source', str(a.parameter_source.resolve())]
                if candidate.get('rl_case'):
                    assert a.rl_bridge is not None and not candidate.get('checkpoint') and not candidate.get('controller')
                    command += ['--case',candidate['rl_case'],'--bridge',str(a.rl_bridge.resolve())]
                if candidate.get('checkpoint'):
                    checkpoint = Path(candidate['checkpoint']).resolve()
                    assert sha(checkpoint) == candidate['checkpoint_sha256']
                    command += ['--checkpoint', str(checkpoint)]
                if candidate.get('memory_ablation'):
                    assert candidate.get('checkpoint') and candidate['memory_ablation']=='reset_each_observation'
                    command += ['--memory-ablation', candidate['memory_ablation']]
                row = dict(name=name, started_utc=now(), command=command, category=candidate['category'])
                state['rows'].append(row); write(run/'execution.json', state)
                with (run/(name+'.log')).open('x') as log:
                    result = subprocess.run(command, cwd=runtime, stdout=log, stderr=subprocess.STDOUT)
                row.update(returncode=result.returncode, ended_utc=now())
                if (out/'AUDIT.json').is_file():
                    row['audit'] = json.loads((out/'AUDIT.json').read_text())
                write(run/'execution.json', state)
                if result.returncode:
                    raise RuntimeError(name+' failed; retained without automatic retry')
                print(json.dumps(dict(name=name, audit=row['audit'])), flush=True)
            else:
                state['status'] = 'complete'
        except BaseException as exc:
            state.update(status='failed_preserved', error=repr(exc)); raise
        finally:
            state['ended_utc'] = now(); write(run/'execution.json', state)


if __name__ == '__main__':
    main()
