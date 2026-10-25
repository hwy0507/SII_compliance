"""Freeze a balanced source-defined training cohort before learner dispatch.

Thirty preselected train identities from the original three-category sampler;
no performance selection, held-out opening, ESN refitting, or old-result reuse.
The nominal reference is a separately recorded zero-policy construction run.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys

from teacher_bank_design_20260930 import design
from spt_rl_reward_20261025 import CONFIG


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main(args):
    root, out, ref = args.runtime.resolve(), args.output.resolve(), args.reference.resolve()
    if out.exists():
        raise FileExistsError('Preserve existing cohort attempts')
    result = json.loads((ref/'rollout.json').read_text())
    receipt = json.loads((ref/'ADAPTER.json').read_text())
    if not receipt['nominal_reference_only'] or not result['task_success'] or not result['strict_success']:
        raise ValueError('Require the successful standalone nominal construction reference')
    fixtures = design(ref/'rollout.npz')
    anchors = (0, 100, 200, 300, 337, 400, 500, 600, 671, 900)
    chosen = [f for f in fixtures if f['split'] == 'train' and int(f['id'].rsplit('_', 1)[1]) in anchors]
    assert len(chosen) == 30
    out.mkdir(parents=True)
    shutil.copy2(ref/'rollout.plan.json', out/'REFERENCE_PLAN.json')
    (out/'fixtures').mkdir()
    write(out/'DESIGN.json', dict(anchors=anchors, categories=['passive_corner', 'active_short', 'active_long'],
        identities=chosen, reference=str(ref), reference_trajectory_sha256=sha(ref/'rollout.npz'),
        reference_receipt_sha256=sha(ref/'ADAPTER.json'),
        design_source_sha256=sha(Path(__file__).with_name('teacher_bank_design_20260930.py')),
        scope='new 30-condition training cohort; not the historical 3000-trajectory corpus',
        selection='indices fixed before physical preflight, no outcome-based replacement'))
    for fixture in chosen:
        write(out/'fixtures'/(fixture['id']+'.json'), fixture)

    def check(item):
        i, fixture = item
        path = out/'fixtures'/(fixture['id']+'.json')
        episode = out/'model_preflight'/fixture['id']
        log = out/(fixture['id']+'.preflight.log')
        command = ['taskset', '-c', str(args.cpu_start+i % args.workers), sys.executable,
            str(Path(__file__).with_name('published_compliance_episode_20261025.py')),
            '--runtime', str(root), '--output', str(episode), '--fixture', str(path),
            '--reference-plan', str(out/'REFERENCE_PLAN.json'), '--probe-seconds', '.08']
        with log.open('x') as stream:
            rc = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
                         CUDA_VISIBLE_DEVICES='', MUJOCO_GL='disable')).returncode
        if rc:
            raise RuntimeError('Condition preflight failed and retained: '+fixture['id'])
        terminal = json.loads((episode/'TERMINAL.json').read_text())
        if terminal['result']['abort_reason'] is not None or not terminal['result']['physical_valid']:
            raise ValueError('Invalid initial physical condition: '+fixture['id'])
        return dict(id=fixture['id'], category=fixture['category'], path=str(path), sha256=sha(path),
                    model_sha256=terminal['model_sha256'], preflight=str(episode))

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        conditions = list(pool.map(check, enumerate(chosen)))
    write(out/'REGISTRATION.json', dict(schema='sii-published-compliance-training-v1', status='registered',
        created_utc=datetime.now(timezone.utc).isoformat(), runtime=str(root), runtime_sha256=sha(root/'RUNTIME.json'),
        conditions=conditions, seeds=[20261025, 20261026, 20261027],
        reference_plan=str(out/'REFERENCE_PLAN.json'), reference_plan_sha256=sha(out/'REFERENCE_PLAN.json'),
        planner='same frozen nominal plan in every condition; disturbances are absent from prior map; no condition-specific replanning',
        controllers=['direct', 'impedance', 'admittance', 'vmc'], algorithms=['cheq', 'sac'],
        physics_dt_s=.00005, actor_period_s=.04, horizon_s=55.,
        actor='canonical48 SI fields divided by fixed physical scales; CHEQ appends own mixing weight only',
        primary='CHEQ core FR3 controller-interface adaptations, four interfaces',
        ablation='same authors SAC without context/ensemble/mixing',
        source_identity='IFAC2025 polishing-cheq 1a3c1fee3332848068afdb127c4fa33eee420418',
        changes=['platform observations/actions', 'gamma .99 -> .9995 for 55 s horizon',
                 'bounded uniform warmup then original stochastic Gaussian SAC',
                 'correct next mixing context in replay', 'finite horizon terminal no bootstrap',
                 'complete optimizer/temperature/RNG/replay cycle-boundary resume',
                 'local concurrent collection replaces agentlace services'],
        reward=CONFIG, additional_efficiency_bonus='strict_success * 5 * (1 - completion_time / 55)',
        empirical_spt='posthoc global minimum strict-success completion among all registered evaluation results; not used as moving training reward',
        torque_thresholds_nm=[43.5]*4+[6.]*3, torque_scope='actual human contact only; zero duration NA',
        convergence='minimum six paired condition cycles, improvement >=2 over first two cycle means, last three mean range <=max(.5,.02*abs(mean)); diagnostic candidate only, optimizer and deterministic evaluation review required',
        max_total_steps=None, stop='explicit STOP_REQUESTED drains complete cycle; no claim from dispatch-stage completion',
        comparison='fresh paired evaluations on these training conditions; historical ESN outcomes cannot be copied into table',
        designated_esn_checkpoint_available=False))
    print(json.dumps(dict(registration=str(out/'REGISTRATION.json'), conditions=len(conditions))))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reference', type=Path, required=True)
    p.add_argument('--workers', type=int, default=4)
    p.add_argument('--cpu-start', type=int, default=4)
    main(p.parse_args())
