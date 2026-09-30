"""Detached, resumable classical v7 source-primitive diagnostic matrix."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--menagerie', type=Path, required=True)
    p.add_argument('--workers', type=int, default=8)
    args = p.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    root = Path(__file__).resolve().parents[1]
    runner = root / 'scripts/run_classical_v7_20260923.py'
    # Explicitly varied source fixtures; seed alone does not randomize v7.
    variants = [dict(seed=20260923, angle=-.08, shift=-.004, mass=.18, friction=.16),
                dict(seed=20260924, angle=0., shift=0., mass=.20, friction=.20),
                dict(seed=20260925, angle=.08, shift=.004, mass=.22, friction=.24)]
    jobs = []
    for method in ('impedance', 'admittance'):
        for scene in ('ball', 'push', 'corner', 'table_corner'):
            for variant in variants:
                jobs.append(dict(method=method, scene=scene, variant=variant))
    manifest = dict(scope='development source-primitive diagnostics; not office test',
                    git_base='0e9142e9b6c03c22995914e9ef66226cfca27a18',
                    source_sha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                                   for p in sorted((root / 'scripts').glob('*.py'))},
                    duration_s=24, jobs=jobs,
                    limitations=['v7 push is not the later raised-hand-rim workstation',
                                 'fixed controller parameters; no claim of optimally tuned baseline',
                                 'v7 ball task phase uses contact audit for its existing shared task gate'])
    (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2))
    started = time.time()

    def run(job):
        method, scene, variant = job['method'], job['scene'], job['variant']
        out = args.output / method / scene / str(variant['seed']) / 'rollout'
        out.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, str(runner), '--classical-controller', method,
                   '--scene', scene, '--seed', str(variant['seed']), '--duration', '24',
                   '--menagerie', str(args.menagerie), '--output', str(out),
                   '--dt', '.0001', '--shift', str(variant['shift']),
                   '--corner-friction', str(variant['friction'])]
        if scene == 'ball':
            command += ['--ball-angle', str(variant['angle']), '--ball-mass', str(variant['mass'])]
        elif scene == 'push':
            command += ['--push-angle', str(variant['angle']), '--push-stroke', '.23']
        elif scene == 'corner':
            command += ['--yaw', str(variant['angle'])]
        if method == 'admittance':
            command += ['--classical-stiffness', '95', '--classical-rot-stiffness', '4',
                        '--classical-mass', '.55', '--classical-inertia', '.065']
        (out.parent/'command.json').write_text(json.dumps(command, indent=2))
        result_path = out.with_suffix('.json')
        if not result_path.exists():
            environment = dict(os.environ, MUJOCO_GL='egl', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
            try:
                with out.with_suffix('.log').open('w') as log:
                    done = subprocess.run(command, cwd=root, env=environment, stdout=log,
                                          stderr=subprocess.STDOUT, timeout=3600)
                if done.returncode or not result_path.exists():
                    return dict(**job, accepted=False, error='runner', returncode=done.returncode,
                                log=str(out.with_suffix('.log')))
            except subprocess.TimeoutExpired:
                return dict(**job, accepted=False, error='timeout', log=str(out.with_suffix('.log')))
        result = json.loads(result_path.read_text())
        return dict(**job, result_path=str(result_path), **{key: result.get(key) for key in
                    ('accepted', 'success', 'failure_reasons', 'real_contact', 'invalid_physics',
                     'upstream_contact', 'endpoint_error_m', 'peak_torque_nm', 'speed_p95_mps',
                     'duration_s', 'contact', 'final_stage', 'impact_metrics', 'push_metrics',
                     'penetration_mm', 'strict_accepted', 'strict_failure_reasons')})

    rows = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for future in as_completed([pool.submit(run, job) for job in jobs]):
            row = future.result(); rows.append(row)
            (args.output/'results.json').write_text(json.dumps(rows, indent=2))
            status = dict(completed=len(rows), total=len(jobs), elapsed_s=time.time()-started)
            (args.output/'status.json').write_text(json.dumps(status, indent=2))
            print(json.dumps(dict(**status, method=row['method'], scene=row['scene'], accepted=row['accepted'])), flush=True)
    summary = dict(completed=len(rows), total=len(jobs), elapsed_s=time.time()-started,
                   by_method={method: dict(accepted=sum(bool(r['accepted']) for r in rows if r['method']==method),
                                           strict_accepted=sum(bool(r.get('strict_accepted')) for r in rows if r['method']==method),
                                           total=sum(r['method']==method for r in rows))
                              for method in ('impedance', 'admittance')}, rows=rows)
    (args.output/'FINAL_RESULT.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}), flush=True)


if __name__ == '__main__':
    main()
